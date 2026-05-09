import tkinter as tk
import random

class CampoMinado:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Campo Minado")
        self.root.configure(bg="#F3F4F6")
        
        # State variables
        self.rows = 0
        self.cols = 0
        self.total_mines = 0
        self.flags_placed = 0
        self.mines_locations = set()
        self.buttons = {}
        self.first_click = True
        self.game_over = False
        self.cells_revealed = 0
        
        # Timer variables
        self.elapsed_time = 0
        self.timer_id = None
        self.is_paused = False
        self.is_playing = False
        
        self.color_bg = "#F3F4F6"
        self.color_btn = "#FFFFFF"
        self.color_revealed = "#E5E7EB"
        
        self.setup_difficulty_screen()

    def setup_difficulty_screen(self):
        self.root.geometry("400x350")
        
        # Centralizar
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 175
        self.root.geometry(f"+{x}+{y}")
        
        self.diff_frame = tk.Frame(self.root, bg=self.color_bg)
        self.diff_frame.pack(expand=True)
        
        tk.Label(self.diff_frame, text="Campo Minado", font=("Segoe UI", 24, "bold"), bg=self.color_bg, fg="#1F2937").pack(pady=10)
        tk.Label(self.diff_frame, text="Selecione a Dificuldade", font=("Segoe UI", 12), bg=self.color_bg, fg="#4B5563").pack(pady=10)
        
        btn_style = {"font": ("Segoe UI", 12, "bold"), "fg": "#FFFFFF", "relief": "flat", "bd": 0, "cursor": "hand2", "width": 25, "pady": 10}
        
        tk.Button(self.diff_frame, text="Fácil (9x9, 10 minas)", bg="#10B981", activebackground="#059669", command=lambda: self.start_game(9, 9, 10), **btn_style).pack(pady=5)
        tk.Button(self.diff_frame, text="Médio (16x16, 40 minas)", bg="#F59E0B", activebackground="#D97706", command=lambda: self.start_game(16, 16, 40), **btn_style).pack(pady=5)
        tk.Button(self.diff_frame, text="Difícil (16x30, 99 minas)", bg="#EF4444", activebackground="#DC2626", command=lambda: self.start_game(16, 30, 99), **btn_style).pack(pady=5)
        
        # Botão de voltar ao menu
        tk.Button(self.diff_frame, text="Voltar ao Menu", font=("Segoe UI", 10, "bold"), bg="#6B7280", fg="white", relief="flat", bd=0, cursor="hand2", width=20, pady=5, command=self.voltar_menu).pack(pady=15)

    def voltar_menu(self):
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def start_game(self, rows, cols, mines):
        self.rows = rows
        self.cols = cols
        self.total_mines = mines
        self.flags_placed = 0
        self.first_click = True
        self.game_over = False
        self.cells_revealed = 0
        self.mines_locations.clear()
        
        # Limpar tela de dificuldade
        if hasattr(self, 'diff_frame'):
            self.diff_frame.pack_forget()
            
        self.setup_ui()
        
    def setup_ui(self):
        # Ajustar geometria da janela dependendo do grid
        btn_size = 30
        width = max(350, self.cols * btn_size + 40)
        height = self.rows * btn_size + 120
        self.root.geometry(f"{width}x{height}")
        
        # Centralizar na tela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.top_frame = tk.Frame(self.root, bg=self.color_bg)
        self.top_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Info panel
        self.mines_label = tk.Label(self.top_frame, text=f"Minas: {self.total_mines}", font=("Segoe UI", 12, "bold"), bg=self.color_bg, fg="#EF4444")
        self.mines_label.pack(side=tk.LEFT)
        
        self.timer_label = tk.Label(self.top_frame, text="Tempo: 0s", font=("Segoe UI", 12, "bold"), bg=self.color_bg, fg="#3B82F6", width=12)
        self.timer_label.pack(side=tk.LEFT, padx=10)
        
        self.pause_btn = tk.Button(self.top_frame, text="Pausar", font=("Segoe UI", 10, "bold"), bg="#6B7280", fg="white", activebackground="#4B5563", activeforeground="white", relief="flat", bd=0, padx=10, cursor="hand2", command=self.toggle_pause)
        self.pause_btn.pack(side=tk.RIGHT)
        
        self.grid_frame = tk.Frame(self.root, bg="#D1D5DB")
        self.grid_frame.pack(padx=20, pady=(0, 20))
        
        self.pause_label = tk.Label(self.root, text="JOGO PAUSADO", font=("Segoe UI", 24, "bold"), bg=self.color_bg, fg="#1F2937")
        
        self.buttons = {}
        for r in range(self.rows):
            for c in range(self.cols):
                btn = tk.Button(self.grid_frame, width=2, height=1, font=("Segoe UI", 10, "bold"), bg=self.color_btn, activebackground="#E5E7EB", relief="raised", bd=1)
                btn.grid(row=r, column=c, padx=1, pady=1)
                
                # Bindings
                btn.bind("<Button-1>", lambda e, r=r, c=c: self.on_left_click(r, c))
                btn.bind("<Button-3>", lambda e, r=r, c=c: self.on_right_click(r, c))
                self.buttons[(r, c)] = btn

    def place_mines(self, first_r, first_c):
        safe_zone = [(first_r, first_c)]
        # Add adjacent cells to safe zone
        for r in range(max(0, first_r-1), min(self.rows, first_r+2)):
            for c in range(max(0, first_c-1), min(self.cols, first_c+2)):
                safe_zone.append((r, c))
                
        all_positions = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in safe_zone]
        if len(all_positions) < self.total_mines:
            all_positions = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) != (first_r, first_c)]
            
        self.mines_locations = set(random.sample(all_positions, self.total_mines))

    def on_left_click(self, r, c):
        if self.game_over or self.is_paused: return
        btn = self.buttons[(r, c)]
        if btn["state"] == "disabled" or btn["text"] == "🚩": return
        
        if self.first_click:
            self.first_click = False
            self.place_mines(r, c)
            self.start_timer()
            
        if (r, c) in self.mines_locations:
            self.game_over_lose()
        else:
            self.reveal(r, c)
            self.check_win()

    def on_right_click(self, r, c):
        if self.game_over or self.is_paused or self.first_click: return
        btn = self.buttons[(r, c)]
        if btn["state"] == "disabled": return
        
        if btn["text"] == "🚩":
            btn.config(text="", bg=self.color_btn)
            self.flags_placed -= 1
        else:
            if self.flags_placed < self.total_mines:
                btn.config(text="🚩", fg="#EF4444")
                self.flags_placed += 1
                
        self.mines_label.config(text=f"Minas: {self.total_mines - self.flags_placed}")

    def reveal(self, r, c):
        if (r, c) not in self.buttons: return
        btn = self.buttons[(r, c)]
        if btn["state"] == "disabled" or btn["text"] == "🚩": return
        
        count = self.count_adjacent_mines(r, c)
        btn.config(state="disabled", bg=self.color_revealed, relief="flat")
        self.cells_revealed += 1
        
        if count == 0:
            btn.config(text="")
            for nr in range(max(0, r-1), min(self.rows, r+2)):
                for nc in range(max(0, c-1), min(self.cols, c+2)):
                    if (nr, nc) != (r, c):
                        self.reveal(nr, nc)
        else:
            colors = ["", "#3B82F6", "#10B981", "#EF4444", "#8B5CF6", "#F59E0B", "#14B8A6", "#111827", "#6B7280"]
            btn.config(text=str(count), disabledforeground=colors[count])

    def count_adjacent_mines(self, r, c):
        count = 0
        for nr in range(max(0, r-1), min(self.rows, r+2)):
            for nc in range(max(0, c-1), min(self.cols, c+2)):
                if (nr, nc) in self.mines_locations:
                    count += 1
        return count

    def toggle_pause(self):
        if not self.is_playing or self.game_over: return
        
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.config(text="Pausar", bg="#6B7280")
            self.pause_label.pack_forget()
            self.grid_frame.pack(padx=20, pady=(0, 20))
            self.update_timer()
        else:
            self.is_paused = True
            self.pause_btn.config(text="Retomar", bg="#10B981")
            self.grid_frame.pack_forget()
            self.pause_label.pack(expand=True)
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None

    def start_timer(self):
        self.is_playing = True
        self.elapsed_time = 0
        self.update_timer()

    def update_timer(self):
        if self.is_playing and not self.is_paused and not self.game_over:
            self.timer_label.config(text=f"Tempo: {self.elapsed_time}s")
            self.elapsed_time += 1
            self.timer_id = self.root.after(1000, self.update_timer)

    def check_win(self):
        if self.cells_revealed == (self.rows * self.cols - self.total_mines):
            self.game_over = True
            self.is_playing = False
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
            
            # Marcar minas restantes
            for (r, c) in self.mines_locations:
                btn = self.buttons[(r, c)]
                if btn["text"] != "🚩":
                    btn.config(text="🚩", fg="#EF4444", bg=self.color_revealed)
            
            self.root.after(500, lambda: self._show_popup("Você Venceu! 🎉"))

    def game_over_lose(self):
        self.game_over = True
        self.is_playing = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) in self.mines_locations:
                    btn = self.buttons[(r, c)]
                    btn.config(text="💣", bg="#EF4444")
                    
        self.root.after(1000, lambda: self._show_popup("Você Perdeu! 💣"))

    def _show_popup(self, title_text):
        popup = tk.Toplevel(self.root)
        popup.title("Fim de Partida")
        popup.geometry("300x230")
        popup.configure(bg="#F3F4F6")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 115
        popup.geometry(f"+{x}+{y}")
        
        tk.Label(popup, text=title_text, font=("Segoe UI", 16, "bold"), bg="#F3F4F6", fg="#1F2937").pack(pady=(15, 5))
        tk.Label(popup, text=f"Tempo: {self.elapsed_time}s", font=("Segoe UI", 10), bg="#F3F4F6", fg="#4B5563").pack(pady=(0, 10))
        
        def play_again():
            popup.destroy()
            self.cleanup_for_restart()
            self.setup_difficulty_screen()
            
        def change_game():
            popup.destroy()
            if self.on_menu_return:
                self.root.destroy()
                self.on_menu_return()
            else:
                self.root.destroy()
                
        def quit_game():
            popup.destroy()
            self.root.quit()
            
        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "#FFFFFF", "relief": "flat", "bd": 0, "cursor": "hand2", "width": 20, "pady": 5}
        
        tk.Button(popup, text="Jogar Novamente", bg="#3B82F6", activebackground="#2563EB", command=play_again, **btn_style).pack(pady=5)
        tk.Button(popup, text="Trocar de Jogo", bg="#10B981", activebackground="#059669", command=change_game, **btn_style).pack(pady=5)
        tk.Button(popup, text="Sair", bg="#EF4444", activebackground="#DC2626", command=quit_game, **btn_style).pack(pady=5)

    def cleanup_for_restart(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        if hasattr(self, 'top_frame'):
            self.top_frame.destroy()
        if hasattr(self, 'grid_frame'):
            self.grid_frame.destroy()
        if hasattr(self, 'pause_label'):
            self.pause_label.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CampoMinado(root)
    root.mainloop()

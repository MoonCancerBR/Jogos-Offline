import tkinter as tk
import random
import time

class Sudoku:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Sudoku")
        self.root.configure(bg="#F3F4F6")
        
        # State variables
        self.size = 0
        self.block_size = 0
        self.solution = []
        self.puzzle = []
        self.entries = {}
        self.game_over = False
        
        # Timer variables
        self.elapsed_time = 0
        self.timer_id = None
        self.is_paused = False
        self.is_playing = False
        
        self.color_bg = "#F3F4F6"
        self.color_entry_bg = "#FFFFFF"
        self.color_fixed_bg = "#E5E7EB"
        self.color_fixed_fg = "#1F2937"
        self.color_user_fg = "#3B82F6"
        self.color_hint_fg = "#10B981"
        
        self.setup_difficulty_screen()

    def setup_difficulty_screen(self):
        self.root.geometry("400x350")
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 175
        self.root.geometry(f"+{x}+{y}")
        
        self.diff_frame = tk.Frame(self.root, bg=self.color_bg)
        self.diff_frame.pack(expand=True)
        
        tk.Label(self.diff_frame, text="Sudoku", font=("Segoe UI", 24, "bold"), bg=self.color_bg, fg="#1F2937").pack(pady=10)
        tk.Label(self.diff_frame, text="Selecione o Tamanho", font=("Segoe UI", 12), bg=self.color_bg, fg="#4B5563").pack(pady=10)
        
        btn_style = {"font": ("Segoe UI", 12, "bold"), "fg": "#FFFFFF", "relief": "flat", "bd": 0, "cursor": "hand2", "width": 20, "pady": 10}
        
        tk.Button(self.diff_frame, text="Pequeno (4x4)", bg="#10B981", activebackground="#059669", command=lambda: self.start_game(4, 2, 8), **btn_style).pack(pady=5)
        tk.Button(self.diff_frame, text="Clássico (9x9)", bg="#F59E0B", activebackground="#D97706", command=lambda: self.start_game(9, 3, 40), **btn_style).pack(pady=5)
        tk.Button(self.diff_frame, text="Gigante (16x16)", bg="#EF4444", activebackground="#DC2626", command=lambda: self.start_game(16, 4, 120), **btn_style).pack(pady=5)
        
        tk.Button(self.diff_frame, text="Voltar ao Menu", font=("Segoe UI", 10, "bold"), bg="#6B7280", fg="white", relief="flat", bd=0, cursor="hand2", width=20, pady=5, command=self.voltar_menu).pack(pady=15)

    def voltar_menu(self):
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def start_game(self, size, block_size, remove_count):
        self.size = size
        self.block_size = block_size
        self.game_over = False
        
        if hasattr(self, 'diff_frame'):
            self.diff_frame.pack_forget()
            
        self.generate_sudoku(remove_count)
        self.setup_ui()
        self.start_timer()

    def generate_sudoku(self, remove_count):
        n = self.block_size
        N = self.size
        
        # Matemática para base válida
        def pattern(r, c): return (n * (r % n) + r // n + c) % N
        def shuffle(s): return random.sample(s, len(s))
        
        rBase = range(n)
        rows  = [g * n + r for g in shuffle(rBase) for r in shuffle(rBase)]
        cols  = [g * n + c for g in shuffle(rBase) for c in shuffle(rBase)]
        nums  = shuffle(range(1, N + 1))
        
        self.solution = [[nums[pattern(r, c)] for c in cols] for r in rows]
        
        # Remove números para criar o puzzle
        self.puzzle = [row[:] for row in self.solution]
        squares = N * N
        empties = min(squares, remove_count)
        
        for p in random.sample(range(squares), empties):
            self.puzzle[p // N][p % N] = 0

    def setup_ui(self):
        # Geometria dinâmica
        entry_width = 2 if self.size < 16 else 3
        cell_size = 40 if self.size < 16 else 35
        
        width = max(350, self.size * cell_size + 60)
        height = self.size * cell_size + 140
        self.root.geometry(f"{width}x{height}")
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.top_frame = tk.Frame(self.root, bg=self.color_bg)
        self.top_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.timer_label = tk.Label(self.top_frame, text="Tempo: 0s", font=("Segoe UI", 12, "bold"), bg=self.color_bg, fg="#3B82F6", width=12, anchor="w")
        self.timer_label.pack(side=tk.LEFT)
        
        self.hint_btn = tk.Button(self.top_frame, text="Dica", font=("Segoe UI", 10, "bold"), bg="#10B981", fg="white", activebackground="#059669", relief="flat", bd=0, padx=10, cursor="hand2", command=self.give_hint)
        self.hint_btn.pack(side=tk.LEFT, padx=10)
        
        self.pause_btn = tk.Button(self.top_frame, text="Pausar", font=("Segoe UI", 10, "bold"), bg="#6B7280", fg="white", activebackground="#4B5563", relief="flat", bd=0, padx=10, cursor="hand2", command=self.toggle_pause)
        self.pause_btn.pack(side=tk.RIGHT)
        
        self.grid_wrapper = tk.Frame(self.root, bg="#1F2937", bd=2)
        self.grid_wrapper.pack(pady=(0, 20))
        
        self.pause_label = tk.Label(self.root, text="JOGO PAUSADO", font=("Segoe UI", 24, "bold"), bg=self.color_bg, fg="#1F2937")
        
        # Validacao de entrada (somente digitos e limite de tamanho)
        vcmd = (self.root.register(self.validate_input), '%P')
        
        self.entries = {}
        
        # Criar blocos subgrids
        for br in range(self.block_size):
            for bc in range(self.block_size):
                block_frame = tk.Frame(self.grid_wrapper, bd=1, bg="#1F2937")
                block_frame.grid(row=br, column=bc, padx=1, pady=1)
                
                # Preencher entradas do bloco
                for ir in range(self.block_size):
                    for ic in range(self.block_size):
                        r = br * self.block_size + ir
                        c = bc * self.block_size + ic
                        
                        entry = tk.Entry(
                            block_frame, width=entry_width, font=("Segoe UI", 16, "bold"), 
                            justify="center", validate="key", validatecommand=vcmd,
                            relief="flat"
                        )
                        entry.grid(row=ir, column=ic, padx=1, pady=1, ipady=5)
                        
                        val = self.puzzle[r][c]
                        if val != 0:
                            entry.insert(0, str(val))
                            entry.config(state="readonly", readonlybackground=self.color_fixed_bg, fg=self.color_fixed_fg)
                        else:
                            entry.config(bg=self.color_entry_bg, fg=self.color_user_fg)
                            # Bind para checar vitória quando o usuário digitar e sair ou soltar a tecla
                            entry.bind("<KeyRelease>", lambda e, r=r, c=c: self.check_win())
                            
                        self.entries[(r, c)] = entry

    def validate_input(self, P):
        if P == "": return True
        if P.isdigit():
            val = int(P)
            if 1 <= val <= self.size:
                return True
        return False

    def toggle_pause(self):
        if not self.is_playing or self.game_over: return
        
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.config(text="Pausar", bg="#6B7280")
            self.pause_label.pack_forget()
            self.grid_wrapper.pack(pady=(0, 20))
            self.update_timer()
        else:
            self.is_paused = True
            self.pause_btn.config(text="Retomar", bg="#10B981")
            self.grid_wrapper.pack_forget()
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

    def give_hint(self):
        if self.game_over or self.is_paused: return
        
        empty_or_wrong = []
        for r in range(self.size):
            for c in range(self.size):
                entry = self.entries[(r, c)]
                if entry["state"] != "readonly":
                    val = entry.get()
                    if val == "" or (val.isdigit() and int(val) != self.solution[r][c]):
                        empty_or_wrong.append((r, c))
                        
        if empty_or_wrong:
            r, c = random.choice(empty_or_wrong)
            entry = self.entries[(r, c)]
            entry.delete(0, tk.END)
            entry.insert(0, str(self.solution[r][c]))
            entry.config(state="readonly", readonlybackground="#D1FAE5", fg=self.color_hint_fg) # Fundo verdinho para dica
            self.check_win()

    def check_win(self):
        # Chamado após cada alteração (keyrelease) ou dica
        if self.game_over: return
        
        for r in range(self.size):
            for c in range(self.size):
                val = self.entries[(r, c)].get()
                if val == "" or not val.isdigit() or int(val) != self.solution[r][c]:
                    return # Jogo continua
        
        # Se chegou aqui, todos estão preenchidos e certos
        self.game_over = True
        self.is_playing = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            
        self.root.after(500, lambda: self._show_popup("Sudoku Completo! 🎉"))

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
        if hasattr(self, 'grid_wrapper'):
            self.grid_wrapper.destroy()
        if hasattr(self, 'pause_label'):
            self.pause_label.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = Sudoku(root)
    root.mainloop()

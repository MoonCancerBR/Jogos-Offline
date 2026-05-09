import tkinter as tk
from tkinter import messagebox
import random
import winsound
import threading
import time

class QuebraCabeca:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Quebra-Cabeça Deslizante")
        self.root.geometry("400x600")
        self.root.configure(bg="#F3F4F6")
        self.root.resizable(False, False)

        # Configurações de UI
        self.color_bg = "#F3F4F6"
        self.color_grid_bg = "#9CA3AF" # Fundo do tabuleiro
        self.color_tile = "#3B82F6"    # Cor das peças
        self.color_tile_hover = "#2563EB"
        self.color_empty = "#D1D5DB"   # Cor do espaço vazio
        self.color_text = "#FFFFFF"

        self.size = tk.IntVar(value=4) # 4x4 por padrão
        self.board = []
        self.buttons = []
        self.empty_idx = -1
        self.moves = 0
        self.game_active = False

        # Pixel virtual para permitir tamanhos em pixels
        self.pixel_virtual = tk.PhotoImage(width=1, height=1)

        # Título
        self.title_label = tk.Label(
            self.root, text="Quebra-Cabeça", 
            font=("Segoe UI", 24, "bold"), 
            bg=self.color_bg, fg="#1F2937"
        )
        self.title_label.pack(pady=(20, 5))

        # Controles de Modo
        self.mode_frame = tk.Frame(self.root, bg=self.color_bg)
        self.mode_frame.pack(pady=(0, 10))
        tk.Radiobutton(self.mode_frame, text="3x3 (Fácil)", variable=self.size, value=3, 
                       bg=self.color_bg, font=("Segoe UI", 10), command=self.change_mode).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(self.mode_frame, text="4x4 (Clássico)", variable=self.size, value=4, 
                       bg=self.color_bg, font=("Segoe UI", 10), command=self.change_mode).pack(side=tk.LEFT, padx=10)

        # Contador de movimentos
        self.moves_label = tk.Label(
            self.root, text="Movimentos: 0", 
            font=("Segoe UI", 14), 
            bg=self.color_bg, fg="#4B5563"
        )
        self.moves_label.pack(pady=(0, 20))

        # Frame do grid
        self.grid_frame = tk.Frame(self.root, bg=self.color_grid_bg, bd=2)
        self.grid_frame.pack(padx=20, pady=10)

        # Botão de reiniciar
        self.reset_btn = tk.Button(
            self.root, text="Embaralhar / Reiniciar", font=("Segoe UI", 12, "bold"), 
            bg="#10B981", fg="#FFFFFF", activebackground="#059669", activeforeground="#FFFFFF", 
            relief="flat", bd=0, padx=20, pady=10, command=self.start_game, cursor="hand2"
        )
        self.reset_btn.pack(pady=20)
        
        self.reset_btn.bind("<Enter>", lambda e: self.reset_btn.config(bg="#059669"))
        self.reset_btn.bind("<Leave>", lambda e: self.reset_btn.config(bg="#10B981"))

        self.start_game()

    def play_sound(self, sound_type):
        def _play():
            if sound_type == "slide":
                winsound.Beep(600, 50)
            elif sound_type == "win":
                winsound.Beep(400, 150)
                time.sleep(0.05)
                winsound.Beep(600, 200)
                time.sleep(0.05)
                winsound.Beep(800, 300)
        threading.Thread(target=_play, daemon=True).start()

    def change_mode(self):
        self.start_game()

    def start_game(self):
        self.game_active = False
        n = self.size.get()
        
        # Limpar grid anterior
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        self.buttons = []
        self.board = list(range(1, n*n)) + [0] # 0 representa o espaço vazio
        self.empty_idx = n*n - 1
        
        # Cria os botões
        btn_size = 75 if n == 4 else 100
        for i in range(n*n):
            btn = tk.Button(
                self.grid_frame, text="", font=("Segoe UI", 24 if n == 4 else 32, "bold"), 
                width=btn_size, height=btn_size,
                image=self.pixel_virtual, compound="center",
                relief="flat", bd=0, command=lambda idx=i: self.on_click(idx)
            )
            btn.grid(row=i//n, column=i%n, padx=2, pady=2)
            
            btn.bind("<Enter>", lambda e, b=btn, idx=i: self.on_hover_enter(e, b, idx))
            btn.bind("<Leave>", lambda e, b=btn, idx=i: self.on_hover_leave(e, b, idx))
            
            self.buttons.append(btn)

        self.shuffle_board()
        self.moves = 0
        self.update_ui()
        self.game_active = True

    def shuffle_board(self):
        n = self.size.get()
        # Embaralhamento garantidamente solucionável fazendo movimentos aleatórios válidos
        # 300 movimentos para 3x3, 1000 para 4x4
        num_moves = 300 if n == 3 else 1000
        
        for _ in range(num_moves):
            valid_moves = self.get_valid_moves(self.empty_idx)
            move_to = random.choice(valid_moves)
            # Troca
            self.board[self.empty_idx], self.board[move_to] = self.board[move_to], self.board[self.empty_idx]
            self.empty_idx = move_to

    def get_valid_moves(self, idx):
        n = self.size.get()
        moves = []
        row, col = idx // n, idx % n
        if row > 0: moves.append(idx - n) # Cima
        if row < n - 1: moves.append(idx + n) # Baixo
        if col > 0: moves.append(idx - 1) # Esquerda
        if col < n - 1: moves.append(idx + 1) # Direita
        return moves

    def update_ui(self):
        self.moves_label.config(text=f"Movimentos: {self.moves}")
        for i, val in enumerate(self.board):
            btn = self.buttons[i]
            if val == 0:
                btn.config(text="", bg=self.color_empty, cursor="arrow")
            else:
                btn.config(text=str(val), bg=self.color_tile, fg=self.color_text, cursor="hand2")

    def on_hover_enter(self, event, btn, idx):
        if not self.game_active: return
        if self.board[idx] != 0 and self.is_adjacent_to_empty(idx):
            btn.config(bg=self.color_tile_hover)

    def on_hover_leave(self, event, btn, idx):
        if not self.game_active: return
        if self.board[idx] != 0:
            btn.config(bg=self.color_tile)

    def is_adjacent_to_empty(self, idx):
        return idx in self.get_valid_moves(self.empty_idx)

    def on_click(self, idx):
        if not self.game_active or self.board[idx] == 0:
            return

        if self.is_adjacent_to_empty(idx):
            self.play_sound("slide")
            # Animação super rápida (visual)
            self.buttons[idx].config(bg="#93C5FD") # Azul mais claro piscando
            self.root.update_idletasks()
            time.sleep(0.02)
            
            # Troca de posição
            self.board[self.empty_idx], self.board[idx] = self.board[idx], self.board[self.empty_idx]
            self.empty_idx = idx
            self.moves += 1
            
            self.update_ui()
            self.check_win()

    def check_win(self):
        n = self.size.get()
        target = list(range(1, n*n)) + [0]
        if self.board == target:
            self.game_active = False
            self.play_sound("win")
            
            # Destacar todas as peças
            for btn in self.buttons:
                if btn.cget("text") != "":
                    btn.config(bg="#10B981") # Verde
            
            self.root.after(1000, self.show_win_popup)

    def show_win_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Vitória!")
        popup.geometry("300x220")
        popup.configure(bg="#F3F4F6")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 110
        popup.geometry(f"+{x}+{y}")
        
        lbl = tk.Label(popup, text=f"Parabéns!\nVocê resolveu em\n{self.moves} movimentos!", font=("Segoe UI", 12, "bold"), bg="#F3F4F6", fg="#1F2937")
        lbl.pack(pady=15)
        
        def play_again():
            popup.destroy()
            self.start_game()
            
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
        
        tk.Button(popup, text="Jogar Novamente", bg="#3B82F6", activebackground="#2563EB", command=play_again, **btn_style).pack(pady=3)
        tk.Button(popup, text="Trocar de Jogo", bg="#10B981", activebackground="#059669", command=change_game, **btn_style).pack(pady=3)
        tk.Button(popup, text="Sair", bg="#EF4444", activebackground="#DC2626", command=quit_game, **btn_style).pack(pady=3)

if __name__ == "__main__":
    root = tk.Tk()
    app = QuebraCabeca(root)
    root.mainloop()

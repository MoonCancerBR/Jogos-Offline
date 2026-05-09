import tkinter as tk
from tkinter import messagebox
import random
import winsound
import threading
import time

class JogoDaVelha:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Jogo da Velha")
        self.root.geometry("400x600")
        self.root.configure(bg="#F3F4F6")  # Cor de fundo suave (Tailwind gray-100)
        self.root.resizable(False, False)

        self.player = "X"
        self.cpu = "O"
        self.current_turn = self.player
        self.board = [""] * 9
        self.game_active = True
        self.wins_x = 0
        self.wins_o = 0
        self.game_mode = tk.StringVar(value="1x1")

        # Paleta de cores moderna
        self.color_bg = "#F3F4F6"
        self.color_grid = "#D1D5DB"      # Cinza para as bordas do grid
        self.color_btn = "#FFFFFF"       # Fundo branco para os botões
        self.color_x = "#FF6B6B"         # Vermelho pastel vibrante para o X
        self.color_o = "#4ECDC4"         # Turquesa para o O
        self.color_text = "#1F2937"      # Cinza escuro para textos
        self.color_win = "#FEF08A"       # Amarelo suave para destacar a vitória

        # Título
        self.title_label = tk.Label(
            self.root, text="Jogo da Velha", 
            font=("Segoe UI", 26, "bold"), 
            bg=self.color_bg, fg=self.color_text
        )
        self.title_label.pack(pady=(20, 5))

        # Modo de jogo
        self.mode_frame = tk.Frame(self.root, bg=self.color_bg)
        self.mode_frame.pack(pady=(0, 10))
        tk.Radiobutton(self.mode_frame, text="1 vs 1", variable=self.game_mode, value="1x1", 
                       bg=self.color_bg, font=("Segoe UI", 10), command=self.on_mode_change).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(self.mode_frame, text="1 vs CPU", variable=self.game_mode, value="cpu", 
                       bg=self.color_bg, font=("Segoe UI", 10), command=self.on_mode_change).pack(side=tk.LEFT, padx=10)

        # Status
        self.status_label = tk.Label(
            self.root, text="Vez do X", 
            font=("Segoe UI", 14), 
            bg=self.color_bg, fg="#6B7280"
        )
        self.status_label.pack(pady=(0, 20))

        # Placar
        self.score_label = tk.Label(
            self.root, text="Vitórias (X): 0  |  Vitórias (O): 0", 
            font=("Segoe UI", 12, "bold"), 
            bg=self.color_bg, fg=self.color_text
        )
        self.score_label.pack(pady=(0, 10))

        # Frame que atuará como o "grid" (linhas da velha)
        self.frame = tk.Frame(self.root, bg=self.color_grid)
        self.frame.pack(padx=20, pady=10)

        self.buttons = []
        for i in range(9):
            btn = tk.Button(
                self.frame, text="", font=("Segoe UI", 40, "bold"), width=3, height=1,
                bg=self.color_btn, activebackground="#F9FAFB", relief="flat", bd=0,
                command=lambda i=i: self.on_click(i), cursor="hand2"
            )
            # O grid spacing (padx/pady) cria o efeito das linhas do tabuleiro
            btn.grid(row=i//3, column=i%3, padx=2, pady=2)
            
            # Eventos de hover (passar o mouse)
            btn.bind("<Enter>", lambda e, b=btn: self.on_hover_enter(e, b))
            btn.bind("<Leave>", lambda e, b=btn: self.on_hover_leave(e, b))
            
            self.buttons.append(btn)

        # Botão de reiniciar
        self.reset_btn = tk.Button(
            self.root, text="Reiniciar Jogo", font=("Segoe UI", 12, "bold"), 
            bg="#3B82F6", fg="#FFFFFF", activebackground="#2563EB", activeforeground="#FFFFFF", 
            relief="flat", bd=0, padx=20, pady=10, command=self.reset_game, cursor="hand2"
        )
        self.reset_btn.pack(pady=25)

        # Efeito hover no botão reiniciar
        self.reset_btn.bind("<Enter>", lambda e: self.reset_btn.config(bg="#2563EB"))
        self.reset_btn.bind("<Leave>", lambda e: self.reset_btn.config(bg="#3B82F6"))

    def play_sound(self, sound_type):
        def _play():
            if sound_type == "click":
                winsound.Beep(500, 100)
            elif sound_type == "win":
                winsound.Beep(400, 150)
                time.sleep(0.05)
                winsound.Beep(600, 200)
            elif sound_type == "loss":
                winsound.Beep(300, 300)
            elif sound_type == "tie":
                winsound.Beep(400, 200)
                
        threading.Thread(target=_play, daemon=True).start()

    def on_hover_enter(self, event, btn):
        if btn["text"] == "" and self.game_active:
            btn.config(bg="#E5E7EB")  # Cinza claro ao passar o mouse

    def on_hover_leave(self, event, btn):
        if btn["bg"] == "#E5E7EB":
            btn.config(bg=self.color_btn)

    def on_click(self, index):
        if self.board[index] == "" and self.game_active:
            if self.game_mode.get() == "cpu" and self.current_turn != self.player:
                return # Ignora clique se for vez da CPU

            self.play_sound("click")
            
            # Animação de clique visual (pisca levemente escuro)
            btn = self.buttons[index]
            btn.config(bg="#D1D5DB")
            self.root.after(100, lambda: btn.config(bg=self.color_btn) if btn["bg"] not in (self.color_win, "#E5E7EB") else None)
            
            current_symbol = self.current_turn
            self.make_move(index, current_symbol)
            
            if self.game_active:
                if self.game_mode.get() == "cpu":
                    self.current_turn = self.cpu
                    self.status_label.config(text="CPU pensando...", fg="#6B7280")
                    # Um pequeno delay para parecer que a CPU está pensando
                    self.root.after(600, self.cpu_move)
                else:
                    self.current_turn = "O" if current_symbol == "X" else "X"
                    self.status_label.config(text=f"Vez do {self.current_turn}", fg="#6B7280")

    def make_move(self, index, symbol):
        self.board[index] = symbol
        color = self.color_x if symbol == "X" else self.color_o
        self.buttons[index].config(text=symbol, fg=color)
        
        winner, combo = self.check_winner()
        if winner:
            self.game_active = False
            if winner == "Tie":
                self.status_label.config(text="Deu Velha! (Empate)", fg="#D97706")
                self.play_sound("tie")
            else:
                if winner == "X":
                    self.wins_x += 1
                    if self.game_mode.get() == "cpu":
                        text = "Você Venceu! 🎉"
                    else:
                        text = "Jogador X Venceu! 🎉"
                    self.play_sound("win")
                else:
                    self.wins_o += 1
                    if self.game_mode.get() == "cpu":
                        text = "A CPU Venceu! 🤖"
                        self.play_sound("loss")
                    else:
                        text = "Jogador O Venceu! 🎉"
                        self.play_sound("win")
                        
                color_win = self.color_x if winner == "X" else self.color_o
                self.status_label.config(text=text, fg=color_win)
                self.highlight_winner(combo)
            
            self.score_label.config(text=self.get_score_text())
            self.ask_play_again()
        
    def highlight_winner(self, combo):
        if combo:
            for idx in combo:
                self.buttons[idx].config(bg=self.color_win)

    def cpu_move(self):
        if not self.game_active: return

        # 1. Tentar ganhar
        move = self.find_best_move(self.cpu)
        if move is None:
            # 2. Bloquear o jogador
            move = self.find_best_move(self.player)
        
        if move is None:
            # 3. Pegar o centro, se estiver livre
            if self.board[4] == "":
                move = 4
        
        if move is None:
            # 4. Pegar qualquer espaço vazio aleatoriamente
            available = [i for i, x in enumerate(self.board) if x == ""]
            if available:
                move = random.choice(available)
        
        if move is not None:
            self.play_sound("click")
            # Animação de clique da CPU
            btn = self.buttons[move]
            btn.config(bg="#D1D5DB")
            self.root.after(100, lambda: btn.config(bg=self.color_btn) if btn["bg"] not in (self.color_win, "#E5E7EB") else None)

            self.make_move(move, self.cpu)
            if self.game_active:
                self.current_turn = self.player
                self.status_label.config(text="Sua vez (X)", fg="#6B7280")

    def find_best_move(self, symbol):
        win_combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], # linhas
            [0, 3, 6], [1, 4, 7], [2, 5, 8], # colunas
            [0, 4, 8], [2, 4, 6]             # diagonais
        ]
        for combo in win_combos:
            values = [self.board[i] for i in combo]
            if values.count(symbol) == 2 and values.count("") == 1:
                return combo[values.index("")]
        return None

    def get_score_text(self):
        if self.game_mode.get() == "cpu":
            return f"Vitórias: {self.wins_x}  |  Derrotas: {self.wins_o}"
        else:
            return f"Vitórias (X): {self.wins_x}  |  Vitórias (O): {self.wins_o}"

    def on_mode_change(self):
        self.wins_x = 0
        self.wins_o = 0
        self.score_label.config(text=self.get_score_text())
        self.reset_game()

    def check_winner(self):
        win_combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for combo in win_combos:
            if self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] != "":
                return self.board[combo[0]], combo
        
        if "" not in self.board:
            return "Tie", None
            
        return None, None

    def reset_game(self):
        self.board = [""] * 9
        self.game_active = True
        self.current_turn = self.player
        if self.game_mode.get() == "cpu":
            self.status_label.config(text="Sua vez (X)", fg="#6B7280")
        else:
            self.status_label.config(text="Vez do X", fg="#6B7280")
        for btn in self.buttons:
            btn.config(text="", bg=self.color_btn)

    def ask_play_again(self):
        # Pequeno atraso para a tela renderizar a vitória
        self.root.after(500, self._show_popup)

    def _show_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Fim de Partida")
        popup.geometry("300x200")
        popup.configure(bg="#F3F4F6")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        
        # Centralizar a popup sobre a janela do jogo
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")
        
        lbl = tk.Label(popup, text="Fim de jogo!\nO que deseja fazer?", font=("Segoe UI", 12), bg="#F3F4F6", fg="#1F2937")
        lbl.pack(pady=15)
        
        def play_again():
            popup.destroy()
            self.reset_game()
            
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
        
        btn_play = tk.Button(popup, text="Jogar Novamente", bg="#3B82F6", activebackground="#2563EB", command=play_again, **btn_style)
        btn_play.pack(pady=5)
        
        btn_change = tk.Button(popup, text="Trocar de Jogo", bg="#10B981", activebackground="#059669", command=change_game, **btn_style)
        btn_change.pack(pady=5)
        
        btn_quit = tk.Button(popup, text="Sair", bg="#EF4444", activebackground="#DC2626", command=quit_game, **btn_style)
        btn_quit.pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = JogoDaVelha(root)
    root.mainloop()

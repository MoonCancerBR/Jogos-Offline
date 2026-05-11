import tkinter as tk
from tkinter import messagebox

class JogoDama:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Dama 1x1")
        self.root.geometry("600x700")
        self.root.configure(bg="#F3F4F6")
        self.root.resizable(False, False)

        self.color_bg = "#F3F4F6"
        self.color_text = "#1F2937"
        
        self.color_dark = "#D1D5DB" # Gray-300
        self.color_light = "#F9FAFB" # Gray-50
        
        self.color_p1 = "#EF4444" # Red
        self.color_p2 = "#1F2937" # Dark Gray
        self.color_highlight = "#3B82F6"
        self.color_selected = "#10B981"
        self.color_valid = "#6EE7B7"

        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.current_turn = "P1"
        self.selected = None
        self.valid_moves = {} # (r, c) -> jumped_pieces_list
        self.extra_turn = False
        self.continuous_capture_piece = None
        
        self.setup_ui()
        self.reset_game()

    def setup_ui(self):
        self.title_label = tk.Label(
            self.root, text="Dama", 
            font=("Segoe UI", 26, "bold"), 
            bg=self.color_bg, fg=self.color_text
        )
        self.title_label.pack(pady=(15, 5))

        self.status_label = tk.Label(
            self.root, text="Vez do Jogador 1 (Vermelho)", 
            font=("Segoe UI", 14), 
            bg=self.color_bg, fg=self.color_p1
        )
        self.status_label.pack(pady=(0, 10))

        # Canvas for the board
        self.canvas_size = 480
        self.sq_size = self.canvas_size // 8
        self.canvas = tk.Canvas(self.root, width=self.canvas_size, height=self.canvas_size, bg="white", highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

        # Buttons
        btn_frame = tk.Frame(self.root, bg=self.color_bg)
        btn_frame.pack(pady=10)

        self.reset_btn = tk.Button(
            btn_frame, text="Reiniciar Jogo", font=("Segoe UI", 12, "bold"), 
            bg="#3B82F6", fg="#FFFFFF", activebackground="#2563EB", activeforeground="#FFFFFF", 
            relief="flat", bd=0, padx=15, pady=5, command=self.reset_game, cursor="hand2"
        )
        self.reset_btn.grid(row=0, column=0, padx=10)

        if self.on_menu_return:
            self.voltar_btn = tk.Button(
                btn_frame, text="Voltar ao Menu", font=("Segoe UI", 12, "bold"), 
                bg="#6B7280", fg="#FFFFFF", activebackground="#4B5563", activeforeground="#FFFFFF", 
                relief="flat", bd=0, padx=15, pady=5, command=self.voltar_menu, cursor="hand2"
            )
            self.voltar_btn.grid(row=0, column=1, padx=10)

    def voltar_menu(self):
        self.root.destroy()
        if self.on_menu_return:
            self.on_menu_return()

    def reset_game(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        # Setup P2 (Black - Top)
        for r in range(3):
            for c in range(8):
                if (r + c) % 2 == 1:
                    self.board[r][c] = "P2"
        # Setup P1 (Red - Bottom)
        for r in range(5, 8):
            for c in range(8):
                if (r + c) % 2 == 1:
                    self.board[r][c] = "P1"

        self.current_turn = "P1"
        self.selected = None
        self.valid_moves = {}
        self.extra_turn = False
        self.continuous_capture_piece = None
        self.update_status()
        self.draw_board()

    def update_status(self):
        if self.current_turn == "P1":
            self.status_label.config(text="Vez do Jogador 1 (Vermelho)", fg=self.color_p1)
        else:
            self.status_label.config(text="Vez do Jogador 2 (Preto)", fg=self.color_p2)
        if getattr(self, "continuous_capture_piece", None):
            self.status_label.config(text=self.status_label.cget("text") + " - Captura Contínua Disponível!", fg="#D97706")
        elif self.extra_turn:
            self.status_label.config(text=self.status_label.cget("text") + " - Rodada Extra!", fg="#D97706")

    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1 = c * self.sq_size
                y1 = r * self.sq_size
                x2 = x1 + self.sq_size
                y2 = y1 + self.sq_size

                color = self.color_dark if (r + c) % 2 == 1 else self.color_light
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

                # Highlight valid moves
                if (r, c) in self.valid_moves:
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.color_valid, outline="")

                # Highlight continuous capture piece
                if getattr(self, "continuous_capture_piece", None) == (r, c) and self.selected != (r, c):
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FCD34D", outline="") # Amber-300

                # Highlight selected
                if self.selected == (r, c):
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.color_selected, outline="")

                piece = self.board[r][c]
                if piece:
                    p_color = self.color_p1 if "P1" in piece else self.color_p2
                    pad = 8
                    self.canvas.create_oval(x1+pad, y1+pad, x2-pad, y2-pad, fill=p_color, outline="#FFFFFF", width=2)
                    
                    if "K" in piece:
                        # Draw crown or double circle to indicate King
                        self.canvas.create_oval(x1+pad+6, y1+pad+6, x2-pad-6, y2-pad-6, outline="#FFD700", width=3)
                        self.canvas.create_text(x1 + self.sq_size//2, y1 + self.sq_size//2, text="K", fill="#FFD700", font=("Segoe UI", 16, "bold"))

    def get_all_valid_moves(self, r, c):
        piece = self.board[r][c]
        if not piece: return {}
        
        moves = {}
        is_king = "K" in piece
        player = piece[:2]
        
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            if not is_king:
                # Normal move
                if player == "P1" and dr == -1 or player == "P2" and dr == 1:
                    r_new, c_new = r + dr, c + dc
                    if 0 <= r_new < 8 and 0 <= c_new < 8 and self.board[r_new][c_new] is None:
                        moves[(r_new, c_new)] = []
                
                # Capture move (can be any direction for both players based on "voltando" rule)
                r_jump, c_jump = r + dr, c + dc
                r_land, c_land = r + 2*dr, c + 2*dc
                if 0 <= r_land < 8 and 0 <= c_land < 8:
                    jumped = self.board[r_jump][c_jump]
                    if jumped and jumped[:2] != player and self.board[r_land][c_land] is None:
                        moves[(r_land, c_land)] = [(r_jump, c_jump)]
            else:
                # King moves
                curr_r, curr_c = r + dr, c + dc
                jumped_pieces = []
                while 0 <= curr_r < 8 and 0 <= curr_c < 8:
                    p = self.board[curr_r][curr_c]
                    if p:
                        if p[:2] == player:
                            break # Blocked by own piece
                        else:
                            if len(jumped_pieces) == 1:
                                break # Can't jump 2 pieces in same line
                            jumped_pieces.append((curr_r, curr_c))
                    else:
                        moves[(curr_r, curr_c)] = list(jumped_pieces)
                    
                    curr_r += dr
                    curr_c += dc

        return moves

    def on_click(self, event):
        c = event.x // self.sq_size
        r = event.y // self.sq_size
        if not (0 <= r < 8 and 0 <= c < 8): return

        piece = self.board[r][c]

        # If clicking a valid move
        if (r, c) in self.valid_moves:
            self.execute_move(self.selected[0], self.selected[1], r, c)
            return

        # If clicking own piece
        if piece and piece[:2] == self.current_turn:
            self.selected = (r, c)
            self.valid_moves = self.get_all_valid_moves(r, c)
            self.draw_board()
        else:
            self.selected = None
            self.valid_moves = {}
            self.draw_board()

    def execute_move(self, r1, c1, r2, c2):
        piece = self.board[r1][c1]
        jumped = self.valid_moves[(r2, c2)]
        
        self.board[r2][c2] = piece
        self.board[r1][c1] = None
        
        for jr, jc in jumped:
            self.board[jr][jc] = None

        # King promotion
        player = piece[:2]
        if player == "P1" and r2 == 0 and "K" not in piece:
            self.board[r2][c2] = "P1K"
        elif player == "P2" and r2 == 7 and "K" not in piece:
            self.board[r2][c2] = "P2K"

        if len(jumped) > 0:
            all_moves = self.get_all_valid_moves(r2, c2)
            capture_moves = {m: j for m, j in all_moves.items() if len(j) > 0}
            if capture_moves:
                self.extra_turn = True
                self.continuous_capture_piece = (r2, c2)
            else:
                self.extra_turn = False
                self.continuous_capture_piece = None
                self.current_turn = "P2" if self.current_turn == "P1" else "P1"
        else:
            self.extra_turn = False
            self.continuous_capture_piece = None
            self.current_turn = "P2" if self.current_turn == "P1" else "P1"
            
        self.selected = None
        self.valid_moves = {}
        
        self.update_status()
        self.draw_board()
        self.check_winner()

    def check_winner(self):
        p1_count = 0
        p2_count = 0
        p1_moves = 0
        p2_moves = 0
        
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p:
                    if "P1" in p:
                        p1_count += 1
                        p1_moves += len(self.get_all_valid_moves(r, c))
                    else:
                        p2_count += 1
                        p2_moves += len(self.get_all_valid_moves(r, c))

        winner = None
        if p1_count == 0 or (p1_moves == 0 and self.current_turn == "P1"):
            winner = "Jogador 2 (Preto)"
        elif p2_count == 0 or (p2_moves == 0 and self.current_turn == "P2"):
            winner = "Jogador 1 (Vermelho)"

        if winner:
            self.status_label.config(text=f"Vencedor: {winner}!", fg="#D97706")
            self.ask_play_again(winner)

    def ask_play_again(self, winner):
        popup = tk.Toplevel(self.root)
        popup.title("Fim de Jogo")
        popup.geometry("300x200")
        popup.configure(bg="#F3F4F6")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")

        lbl = tk.Label(popup, text=f"{winner} Venceu!\\nO que deseja fazer?", font=("Segoe UI", 12), bg="#F3F4F6", fg="#1F2937")
        lbl.pack(pady=15)

        def play_again():
            popup.destroy()
            self.reset_game()

        def change_game():
            popup.destroy()
            self.voltar_menu()

        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "#FFFFFF", "relief": "flat", "bd": 0, "cursor": "hand2", "width": 20, "pady": 5}

        btn_play = tk.Button(popup, text="Jogar Novamente", bg="#3B82F6", activebackground="#2563EB", command=play_again, **btn_style)
        btn_play.pack(pady=5)

        if self.on_menu_return:
            btn_change = tk.Button(popup, text="Trocar de Jogo", bg="#10B981", activebackground="#059669", command=change_game, **btn_style)
            btn_change.pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = JogoDama(root)
    root.mainloop()

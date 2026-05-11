import tkinter as tk
from tkinter import messagebox
import copy
import time

PIECES_UNICODE = {
    'wK': '♔', 'wQ': '♕', 'wR': '♖', 'wB': '♗', 'wN': '♘', 'wP': '♙',
    'bK': '♚', 'bQ': '♛', 'bR': '♜', 'bB': '♝', 'bN': '♞', 'bP': '♟'
}

PIECES_NAMES = {
    'K': 'Rei', 'Q': 'Rainha', 'R': 'Torre', 'B': 'Bispo', 'N': 'Cavalo', 'P': 'Peão'
}

class JogoXadrez:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Xadrez 1x1")
        self.root.geometry("1280x800")
        self.root.configure(bg="#1E293B")
        self.root.resizable(True, True)

        # Colors
        self.color_bg = "#1E293B" # Main background
        self.color_panel = "#0F172A" # Panels background
        self.color_text = "#F8FAFC"
        
        self.color_dark = "#739552" # Chess green
        self.color_light = "#EBECD0" # Chess white
        self.color_highlight = "#F6F669" # Yellow for selection
        self.color_valid = "#B9CA43" # Greenish for valid move
        self.color_capture = "#EF4444" # Red for capture
        self.color_danger = "#F59E0B" # Amber/Yellow for danger move

        # State Variables
        self.timer_id = None
        self.use_timer = False
        self.initial_time = 0
        self.game_paused = False
        self.game_over = False

        self.setup_ui()
        self.ask_timer_config()

    def ask_timer_config(self):
        # Modal para perguntar sobre cronômetro
        popup = tk.Toplevel(self.root)
        popup.title("Configuração de Jogo")
        popup.geometry("350x250")
        popup.configure(bg="#1F2937")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        # Center popup
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 175
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 125
        popup.geometry(f"+{x}+{y}")

        lbl = tk.Label(popup, text="Deseja jogar com cronômetro?", font=("Segoe UI", 12, "bold"), bg="#1F2937", fg="white")
        lbl.pack(pady=20)

        def start_game(time_mins):
            self.use_timer = time_mins > 0
            self.initial_time = time_mins * 60
            popup.destroy()
            self.reset_game()

        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "white", "relief": "flat", "bd": 0, "cursor": "hand2", "width": 15, "pady": 5}
        
        tk.Button(popup, text="Sem tempo", bg="#6B7280", command=lambda: start_game(0), **btn_style).pack(pady=5)
        
        frame_tempos = tk.Frame(popup, bg="#1F2937")
        frame_tempos.pack(pady=5)
        tk.Button(frame_tempos, text="5 Min", bg="#3B82F6", command=lambda: start_game(5), **btn_style).grid(row=0, column=0, padx=5)
        tk.Button(frame_tempos, text="10 Min", bg="#10B981", command=lambda: start_game(10), **btn_style).grid(row=0, column=1, padx=5)
        tk.Button(frame_tempos, text="30 Min", bg="#8B5CF6", command=lambda: start_game(30), **btn_style).grid(row=1, column=0, columnspan=2, pady=10)

    def setup_ui(self):
        # Top bar
        top_frame = tk.Frame(self.root, bg=self.color_bg)
        top_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(top_frame, text="Vez do Jogador 1 (Brancas)", font=("Segoe UI", 16, "bold"), bg=self.color_bg, fg=self.color_text)
        self.status_label.pack(side=tk.TOP)
        self.lbl_global_time = tk.Label(top_frame, text="Tempo de Partida: 00:00", font=("Segoe UI", 12), bg=self.color_bg, fg="#94A3B8")
        self.lbl_global_time.pack(side=tk.TOP)

        # Main Layout: Left Panel | Center Canvas | Right Panel
        main_frame = tk.Frame(self.root, bg=self.color_bg)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Left Panel ---
        left_panel = tk.Frame(main_frame, bg=self.color_panel, width=200, bd=2, relief="groove")
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Player 2 Timer
        self.lbl_timer_p2 = tk.Label(left_panel, text="P2: --:--", font=("Segoe UI", 24, "bold"), bg=self.color_bg, fg=self.color_text, padx=10, pady=10, relief="flat")
        self.lbl_timer_p2.pack(pady=10, fill=tk.X)

        # Captured pieces P2 (Pieces white captured by P2) -> Wait, P2 is black. Black captures White pieces.
        self.lbl_cap_w = tk.Label(left_panel, text="", font=("Segoe UI", 18), bg=self.color_panel, fg=self.color_text, wraplength=180)
        self.lbl_cap_w.pack(pady=5, fill=tk.X)

        # Controls
        ctrl_frame = tk.Frame(left_panel, bg=self.color_panel)
        ctrl_frame.pack(pady=30, fill=tk.X, padx=10)

        btn_style = {"font": ("Segoe UI", 10, "bold"), "fg": "white", "relief": "flat", "bd": 0, "cursor": "hand2", "pady": 8}
        self.btn_pause = tk.Button(ctrl_frame, text="PAUSAR", bg="#F59E0B", command=self.toggle_pause, **btn_style)
        self.btn_pause.pack(fill=tk.X, pady=5)

        self.btn_undo = tk.Button(ctrl_frame, text="⏪ Desfazer", bg="#6B7280", command=self.undo_move, state=tk.DISABLED, **btn_style)
        self.btn_undo.pack(fill=tk.X, pady=5)
        
        self.btn_redo = tk.Button(ctrl_frame, text="Refazer ⏩", bg="#6B7280", command=self.redo_move, state=tk.DISABLED, **btn_style)
        self.btn_redo.pack(fill=tk.X, pady=5)

        self.btn_reset = tk.Button(ctrl_frame, text="Reiniciar", bg="#EF4444", command=lambda: self.ask_timer_config(), **btn_style)
        self.btn_reset.pack(fill=tk.X, pady=5)
        
        if self.on_menu_return:
            self.btn_voltar = tk.Button(ctrl_frame, text="Sair", bg="#4B5563", command=self.voltar_menu, **btn_style)
            self.btn_voltar.pack(fill=tk.X, pady=5)

        # Captured pieces P1 (Pieces black captured by P1)
        self.lbl_cap_b = tk.Label(left_panel, text="", font=("Segoe UI", 18), bg=self.color_panel, fg=self.color_text, wraplength=180)
        self.lbl_cap_b.pack(side=tk.BOTTOM, pady=5, fill=tk.X)

        # Player 1 Timer
        self.lbl_timer_p1 = tk.Label(left_panel, text="P1: --:--", font=("Segoe UI", 24, "bold"), bg=self.color_bg, fg=self.color_text, bd=2, relief="solid", padx=10, pady=10)
        self.lbl_timer_p1.pack(side=tk.BOTTOM, pady=10, fill=tk.X)

        # --- Center Canvas ---
        self.canvas_size = 640
        self.sq_size = self.canvas_size // 8
        self.canvas = tk.Canvas(main_frame, width=self.canvas_size, height=self.canvas_size, bg=self.color_bg, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, padx=20)
        self.canvas.bind("<Button-1>", self.on_click)

        # --- Right Panel ---
        right_panel = tk.Frame(main_frame, bg=self.color_panel, width=350, bd=2, relief="groove")
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(right_panel, text="Histórico de Lances", font=("Segoe UI", 12, "bold"), bg=self.color_panel, fg=self.color_text).pack(pady=5)
        
        scroll = tk.Scrollbar(right_panel)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.list_history = tk.Listbox(right_panel, font=("Consolas", 10), yscrollcommand=scroll.set, bg=self.color_bg, fg=self.color_text, selectbackground="#334155", highlightthickness=0)
        self.list_history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5,0), pady=(0,5))
        scroll.config(command=self.list_history.yview)
        self.list_history.bind("<<ListboxSelect>>", self.on_history_select)

    def voltar_menu(self):
        self.cancel_timers()
        self.root.destroy()
        if self.on_menu_return:
            self.on_menu_return()

    def cancel_timers(self):
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def create_initial_board(self):
        return [
            ['bR', 'bN', 'bB', 'bQ', 'bK', 'bB', 'bN', 'bR'],
            ['bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP', 'bP'],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, None, None, None, None],
            ['wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP', 'wP'],
            ['wR', 'wN', 'wB', 'wQ', 'wK', 'wB', 'wN', 'wR']
        ]

    def reset_game(self):
        self.cancel_timers()
        self.board = self.create_initial_board()
        self.turn = 'w'
        self.castling = {'wK': True, 'wQ': True, 'bK': True, 'bQ': True}
        self.en_passant_target = None
        self.halfmove_clock = 0
        
        self.time_w = self.initial_time
        self.time_b = self.initial_time
        self.global_time = 0
        
        self.captured = {'w': [], 'b': []} # 'w' means white pieces captured by black
        self.history = []
        self.history_index = -1

        self.selected_sq = None
        self.valid_moves = {} # {(r, c): 'move_type'} move_type can be 'normal', 'capture', 'en_passant', 'castling', 'promotion'
        self.danger_moves = set() # subset of valid_moves that end up in danger

        self.game_paused = False
        self.game_over = False
        self.timer_started = False

        self.update_ui()
        self.save_state("Partida Iniciada")

    def save_state(self, move_desc=""):
        # Se estamos no meio do histórico e fazemos um novo lance, apaga o futuro
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
            self.list_history.delete(self.history_index + 1, tk.END)

        state = {
            'board': copy.deepcopy(self.board),
            'turn': self.turn,
            'castling': copy.deepcopy(self.castling),
            'en_passant_target': self.en_passant_target,
            'halfmove_clock': self.halfmove_clock,
            'time_w': self.time_w,
            'time_b': self.time_b,
            'captured': copy.deepcopy(self.captured),
            'desc': move_desc
        }
        self.history.append(state)
        self.history_index += 1

        if move_desc:
            self.list_history.insert(tk.END, f"{self.history_index}. {move_desc}")
            self.list_history.selection_clear(0, tk.END)
            self.list_history.selection_set(self.history_index)
            self.list_history.see(self.history_index)

    def timer_tick(self):
        if self.game_paused or self.game_over:
            return

        self.global_time += 1
        
        if self.use_timer:
            if self.turn == 'w':
                self.time_w -= 1
                if self.time_w <= 0:
                    self.time_w = 0
                    self.end_game("Tempo esgotado! Jogador 2 (Pretas) Vence.")
            else:
                self.time_b -= 1
                if self.time_b <= 0:
                    self.time_b = 0
                    self.end_game("Tempo esgotado! Jogador 1 (Brancas) Vence.")

        self.update_timer_labels()
        if not self.game_over:
            self.timer_id = self.root.after(1000, self.timer_tick)

    def format_time(self, seconds):
        if seconds < 0: seconds = 0
        m = seconds // 60
        s = seconds % 60
        return f"{m:02d}:{s:02d}"

    def update_timer_labels(self):
        self.lbl_global_time.config(text=f"Tempo de Partida: {self.format_time(self.global_time)}")
        if self.use_timer:
            self.lbl_timer_p1.config(text=f"P1: {self.format_time(self.time_w)}")
            self.lbl_timer_p2.config(text=f"P2: {self.format_time(self.time_b)}")
        else:
            self.lbl_timer_p1.config(text="P1: --:--")
            self.lbl_timer_p2.config(text="P2: --:--")

    def update_buttons_state(self):
        if self.game_paused or not self.use_timer:
            self.btn_undo.config(state=tk.NORMAL, bg="#3B82F6")
            self.btn_redo.config(state=tk.NORMAL, bg="#3B82F6")
        else:
            self.btn_undo.config(state=tk.DISABLED, bg="#6B7280")
            self.btn_redo.config(state=tk.DISABLED, bg="#6B7280")

    def toggle_pause(self, is_promotion_pause=False):
        if self.game_over: return
        
        self.game_paused = not self.game_paused
        
        if self.game_paused:
            self.btn_pause.config(text="RETOMAR", bg="#10B981")
            self.selected_sq = None
            self.valid_moves = {}
            if not is_promotion_pause:
                self.status_label.config(text="JOGO PAUSADO")
        else:
            self.btn_pause.config(text="PAUSAR", bg="#F59E0B")
            self.update_status_label()
            if self.timer_started:
                self.timer_tick()
                
        self.update_buttons_state()
        self.draw_board()

    def on_history_select(self, event):
        if not self.game_paused and self.use_timer:
            return # Must be paused to navigate history if using timer
        
        selection = self.list_history.curselection()
        if selection:
            idx = selection[0]
            if idx != self.history_index:
                self.history_index = idx
                self.load_state(self.history[idx])

    def undo_move(self):
        if self.history_index > 0 and (self.game_paused or not self.use_timer):
            self.history_index -= 1
            self.load_state(self.history[self.history_index])

    def redo_move(self):
        if self.history_index < len(self.history) - 1 and (self.game_paused or not self.use_timer):
            self.history_index += 1
            self.load_state(self.history[self.history_index])

    def load_state(self, state):
        self.board = copy.deepcopy(state['board'])
        self.turn = state['turn']
        self.castling = copy.deepcopy(state['castling'])
        self.en_passant_target = state['en_passant_target']
        self.halfmove_clock = state['halfmove_clock']
        self.time_w = state['time_w']
        self.time_b = state['time_b']
        self.captured = copy.deepcopy(state['captured'])
        
        self.list_history.selection_clear(0, tk.END)
        self.list_history.selection_set(self.history_index)
        self.list_history.see(self.history_index)
        
        self.game_over = False
        self.update_ui()
        if self.game_paused:
            self.status_label.config(text="JOGO PAUSADO")

    def update_status_label(self):
        if self.game_over: return
        if self.turn == 'w':
            self.status_label.config(text="Vez do Jogador 1 (Brancas)", fg=self.color_text)
        else:
            self.status_label.config(text="Vez do Jogador 2 (Pretas)", fg=self.color_text)

    def update_ui(self):
        self.update_timer_labels()
        self.update_status_label()
        self.update_buttons_state()
        
        cap_w_text = "".join([PIECES_UNICODE['w'+p] for p in self.captured['w']])
        cap_b_text = "".join([PIECES_UNICODE['b'+p] for p in self.captured['b']])
        self.lbl_cap_w.config(text=f"Capturas: {cap_w_text}")
        self.lbl_cap_b.config(text=f"Capturas: {cap_b_text}")
        
        self.draw_board()

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
                    move_type = self.valid_moves[(r, c)]
                    hl_color = self.color_valid
                    
                    if (r, c) in self.danger_moves:
                        hl_color = self.color_danger
                    elif move_type == 'capture' or move_type == 'en_passant':
                        hl_color = self.color_capture
                        
                    # Se for perigo sobrepoe a captura ou valido
                    if (r, c) in self.danger_moves:
                        hl_color = self.color_danger

                    # Desenhar circulo ou highlight quadrado
                    pad = self.sq_size // 4
                    if self.board[r][c]: # If there's a piece (capture), draw a border
                        self.canvas.create_rectangle(x1, y1, x2, y2, outline=hl_color, width=4)
                    else: # Draw a circle in empty square
                        self.canvas.create_oval(x1+pad, y1+pad, x2-pad, y2-pad, fill=hl_color, outline="")

                # Highlight selected
                if self.selected_sq == (r, c):
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.color_highlight, outline="")

                # Draw Piece
                piece = self.board[r][c]
                if piece:
                    char = PIECES_UNICODE[piece]
                    color_p = "#000000" if piece[0] == 'b' else "#FFFFFF"
                    # Add subtle shadow for white pieces so they are visible on light squares
                    if piece[0] == 'w':
                        self.canvas.create_text(x1 + self.sq_size//2 + 2, y1 + self.sq_size//2 + 2, text=char, fill="#4B5563", font=("Segoe UI", 36))
                    self.canvas.create_text(x1 + self.sq_size//2, y1 + self.sq_size//2, text=char, fill=color_p, font=("Segoe UI", 36))

                # Draw coordinates
                text_color = self.color_light if (r + c) % 2 == 1 else self.color_dark
                if c == 0:
                    self.canvas.create_text(x1 + 4, y1 + 4, text=str(8-r), fill=text_color, font=("Segoe UI", 10, "bold"), anchor="nw")
                if r == 7:
                    self.canvas.create_text(x2 - 4, y2 - 4, text=chr(97+c), fill=text_color, font=("Segoe UI", 10, "bold"), anchor="se")

        # Overlay se pausado
        if self.game_paused:
            self.canvas.create_rectangle(0, 0, self.canvas_size, self.canvas_size, fill="#0F172A", stipple="gray50")
            self.canvas.create_text(self.canvas_size//2, self.canvas_size//2, text="PAUSADO", font=("Segoe UI", 36, "bold"), fill=self.color_text)

    def pos_to_algebraic(self, r, c):
        return f"{chr(97+c)}{8-r}"

    def on_click(self, event):
        if self.game_paused or self.game_over:
            return

        c = event.x // self.sq_size
        r = event.y // self.sq_size
        if not (0 <= r < 8 and 0 <= c < 8): return

        # If clicked on a valid move destination
        if self.selected_sq and (r, c) in self.valid_moves:
            self.execute_move(self.selected_sq[0], self.selected_sq[1], r, c)
            return

        piece = self.board[r][c]
        if piece and piece[0] == self.turn:
            self.selected_sq = (r, c)
            self.valid_moves = self.get_legal_moves(r, c)
            self.calculate_danger_moves(r, c)
        else:
            self.selected_sq = None
            self.valid_moves = {}
            self.danger_moves = set()
            
        self.draw_board()

    def get_piece_moves(self, board, r, c):
        piece = board[r][c]
        if not piece: return {}
        
        color = piece[0]
        p_type = piece[1]
        moves = {}

        def add_move(nr, nc):
            if 0 <= nr < 8 and 0 <= nc < 8:
                target = board[nr][nc]
                if not target:
                    moves[(nr, nc)] = 'normal'
                    return True # Continue in this direction
                elif target[0] != color:
                    moves[(nr, nc)] = 'capture'
                    return False # Stop in this direction
                return False # Blocked by own piece
            return False # Out of bounds

        def add_line(dr, dc):
            nr, nc = r + dr, c + dc
            while add_move(nr, nc):
                nr += dr
                nc += dc

        if p_type == 'P':
            d = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1
            # Forward 1
            if 0 <= r+d < 8 and board[r+d][c] is None:
                moves[(r+d, c)] = 'normal'
                # Forward 2
                if r == start_row and board[r+2*d][c] is None:
                    moves[(r+2*d, c)] = 'normal'
            # Captures
            for dc in [-1, 1]:
                if 0 <= r+d < 8 and 0 <= c+dc < 8:
                    target = board[r+d][c+dc]
                    if target and target[0] != color:
                        moves[(r+d, c+dc)] = 'capture'
                    elif (r+d, c+dc) == self.en_passant_target:
                        moves[(r+d, c+dc)] = 'en_passant'

        elif p_type == 'N':
            jumps = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
            for dr, dc in jumps:
                add_move(r+dr, c+dc)

        elif p_type == 'B':
            for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                add_line(dr, dc)

        elif p_type == 'R':
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                add_line(dr, dc)

        elif p_type == 'Q':
            for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                add_line(dr, dc)

        elif p_type == 'K':
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    add_move(r+dr, c+dc)
            
            # Castling (only pseudo-legal, check condition later)
            if self.castling.get(f'{color}K'): # Kingside
                if board[r][c+1] is None and board[r][c+2] is None:
                    moves[(r, c+2)] = 'castling'
            if self.castling.get(f'{color}Q'): # Queenside
                if board[r][c-1] is None and board[r][c-2] is None and board[r][c-3] is None:
                    moves[(r, c-2)] = 'castling'

        # Check for promotion notation
        for move_pos, mtype in list(moves.items()):
            if p_type == 'P' and (move_pos[0] == 0 or move_pos[0] == 7):
                moves[move_pos] = 'promotion' # Override

        return moves

    def is_square_attacked(self, board, r, c, attacker_color):
        for ir in range(8):
            for ic in range(8):
                piece = board[ir][ic]
                if piece and piece[0] == attacker_color:
                    # To prevent infinite recursion with Kings, we simulate basic attacks
                    p_type = piece[1]
                    if p_type == 'K':
                        if abs(r-ir) <= 1 and abs(c-ic) <= 1:
                            return True
                    elif p_type == 'P':
                        d = -1 if attacker_color == 'w' else 1
                        if ir+d == r and abs(c-ic) == 1:
                            return True
                    else:
                        moves = self.get_piece_moves(board, ir, ic)
                        if (r, c) in moves:
                            return True
        return False

    def is_in_check(self, board, color):
        kr, kc = -1, -1
        for r in range(8):
            for c in range(8):
                if board[r][c] == f"{color}K":
                    kr, kc = r, c
                    break
        if kr == -1: return False # King captured (should not happen in real game)
        return self.is_square_attacked(board, kr, kc, 'b' if color == 'w' else 'w')

    def simulate_move(self, r1, c1, r2, c2, move_type):
        sim_board = copy.deepcopy(self.board)
        piece = sim_board[r1][c1]
        sim_board[r2][c2] = piece
        sim_board[r1][c1] = None

        if move_type == 'en_passant':
            sim_board[r1][c2] = None
        elif move_type == 'castling':
            if c2 > c1: # Kingside
                sim_board[r2][c2-1] = sim_board[r2][7]
                sim_board[r2][7] = None
            else: # Queenside
                sim_board[r2][c2+1] = sim_board[r2][0]
                sim_board[r2][0] = None
                
        return sim_board

    def get_legal_moves(self, r, c):
        pseudo = self.get_piece_moves(self.board, r, c)
        legal = {}
        color = self.board[r][c][0]
        
        for (nr, nc), mtype in pseudo.items():
            sim_board = self.simulate_move(r, c, nr, nc, mtype)
            if not self.is_in_check(sim_board, color):
                # Extra castling checks: King cannot pass through check
                if mtype == 'castling':
                    if self.is_in_check(self.board, color): continue # Cannot castle out of check
                    dir_c = 1 if nc > c else -1
                    if self.is_square_attacked(self.board, r, c + dir_c, 'b' if color == 'w' else 'w'):
                        continue # Cannot pass through check
                
                legal[(nr, nc)] = mtype
        return legal

    def calculate_danger_moves(self, r, c):
        self.danger_moves = set()
        color = self.board[r][c][0]
        enemy_color = 'b' if color == 'w' else 'w'
        
        for (nr, nc), mtype in self.valid_moves.items():
            sim_board = self.simulate_move(r, c, nr, nc, mtype)
            if self.is_square_attacked(sim_board, nr, nc, enemy_color):
                self.danger_moves.add((nr, nc))

    def has_legal_moves(self, color):
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece and piece[0] == color:
                    if self.get_legal_moves(r, c):
                        return True
        return False

    def is_insufficient_material(self):
        pieces = []
        for r in range(8):
            for c in range(8):
                if self.board[r][c]:
                    pieces.append(self.board[r][c])
        
        if len(pieces) == 2: return True # K vs K
        if len(pieces) == 3:
            types = [p[1] for p in pieces]
            if 'B' in types or 'N' in types: return True # K+B vs K or K+N vs K
        return False

    def execute_move(self, r1, c1, r2, c2):
        if not self.timer_started:
            self.timer_started = True
            self.timer_tick()
            
        move_type = self.valid_moves[(r2, c2)]
        piece = self.board[r1][c1]
        target_piece = self.board[r2][c2]
        
        player = "Player 1" if self.turn == 'w' else "Player 2"
        move_desc = f"{player} moveu {PIECES_NAMES[piece[1]]} de {self.pos_to_algebraic(r1,c1)} -> {self.pos_to_algebraic(r2,c2)}"

        # Handle captures
        captured_something = False
        if target_piece:
            self.captured[target_piece[0]].append(target_piece[1])
            move_desc = f"{player} capturou {PIECES_NAMES[target_piece[1]]} movendo {PIECES_NAMES[piece[1]]} de {self.pos_to_algebraic(r1,c1)} -> {self.pos_to_algebraic(r2,c2)}"
            captured_something = True
        elif move_type == 'en_passant':
            cap_p = self.board[r1][c2]
            self.captured[cap_p[0]].append(cap_p[1])
            self.board[r1][c2] = None
            move_desc = f"{player} capturou Peão (En Passant) de {self.pos_to_algebraic(r1,c1)} -> {self.pos_to_algebraic(r2,c2)}"
            captured_something = True

        # Halfmove clock
        if piece[1] == 'P' or captured_something:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # Move piece
        self.board[r2][c2] = piece
        self.board[r1][c1] = None

        # Castling
        if move_type == 'castling':
            if c2 > c1: # Kingside
                self.board[r2][c2-1] = self.board[r2][7]
                self.board[r2][7] = None
                move_desc = f"{player} fez Roque Curto"
            else: # Queenside
                self.board[r2][c2+1] = self.board[r2][0]
                self.board[r2][0] = None
                move_desc = f"{player} fez Roque Longo"

        # Update Castling Rights
        if piece[1] == 'K':
            self.castling[f"{self.turn}K"] = False
            self.castling[f"{self.turn}Q"] = False
        elif piece[1] == 'R':
            if r1 == 7 and c1 == 7: self.castling['wK'] = False
            if r1 == 7 and c1 == 0: self.castling['wQ'] = False
            if r1 == 0 and c1 == 7: self.castling['bK'] = False
            if r1 == 0 and c1 == 0: self.castling['bQ'] = False

        # En Passant Target setup
        if piece[1] == 'P' and abs(r2 - r1) == 2:
            self.en_passant_target = ((r1 + r2) // 2, c1)
        else:
            self.en_passant_target = None

        # Format times for history
        t_global = self.format_time(self.global_time)
        t_player = self.format_time(self.time_w if self.turn == 'w' else self.time_b)
        time_str = f" [Tempo: {t_global} | P: {t_player}]"
        
        self.selected_sq = None
        self.valid_moves = {}
        self.danger_moves = set()

        if move_type == 'promotion':
            self.ask_promotion(r2, c2, move_desc + time_str)
        else:
            self.finalize_turn(move_desc + time_str)

    def ask_promotion(self, r, c, move_desc):
        self.toggle_pause(is_promotion_pause=True) # Pauses timer
        
        popup = tk.Toplevel(self.root)
        popup.title("Promoção")
        popup.geometry("300x120")
        popup.configure(bg="#1F2937")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 60
        popup.geometry(f"+{x}+{y}")

        lbl = tk.Label(popup, text="Escolha a peça para promoção:", font=("Segoe UI", 12), bg="#1F2937", fg="white")
        lbl.pack(pady=10)

        frame = tk.Frame(popup, bg="#1F2937")
        frame.pack()

        color = self.turn
        pieces = ['Q', 'R', 'B', 'N']
        for p in pieces:
            char = PIECES_UNICODE[f"{color}{p}"]
            btn = tk.Button(frame, text=char, font=("Segoe UI", 24), bg="#374151", fg="white", relief="flat", cursor="hand2",
                            command=lambda p_type=p: self.promote(popup, r, c, p_type, move_desc))
            btn.pack(side=tk.LEFT, padx=5)

    def promote(self, popup, r, c, p_type, move_desc):
        self.board[r][c] = f"{self.turn}{p_type}"
        popup.destroy()
        move_desc = move_desc.replace("moveu Peão", f"promoveu Peão para {PIECES_NAMES[p_type]}")
        self.toggle_pause(is_promotion_pause=True) # Unpause
        self.finalize_turn(move_desc)

    def finalize_turn(self, move_desc):
        enemy_color = 'b' if self.turn == 'w' else 'w'
        
        in_check = self.is_in_check(self.board, enemy_color)
        has_moves = self.has_legal_moves(enemy_color)

        if in_check:
            if not has_moves:
                move_desc += " -> XEQUE-MATE!"
            else:
                move_desc += " -> Xeque no Rei"

        self.turn = enemy_color
        self.save_state(move_desc)
        self.update_ui()

        if in_check and not has_moves:
            self.end_game(f"Xeque-Mate! Jogador {'1 (Brancas)' if self.turn == 'b' else '2 (Pretas)'} Vence!")
        elif not in_check and not has_moves:
            self.end_game("Empate por Afogamento (Stalemate)!")
        elif self.halfmove_clock >= 100:
            self.end_game("Empate pela regra dos 50 movimentos!")
        elif self.is_insufficient_material():
            self.end_game("Empate por Insuficiência de Material!")

    def end_game(self, message):
        self.game_over = True
        self.cancel_timers()
        self.status_label.config(text=message, fg="#D97706")
        self.btn_pause.config(state=tk.DISABLED)
        messagebox.showinfo("Fim de Jogo", message, parent=self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = JogoXadrez(root)
    root.mainloop()

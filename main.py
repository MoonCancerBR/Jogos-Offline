import tkinter as tk
from jogo_da_velha import JogoDaVelha
from campo_minado import CampoMinado
from sudoku import Sudoku
from ping_pong import PingPong
from cobrinha import Cobrinha
from Tetris.main import TetrisGame
from sapo import Sapo
from passarinho import Passarinho
from PuyoPuyo.main import PuyoPuyoGame
from space_invaders import SpaceInvaders
from candy_crush import CandyCrush
from quebra_cabeca import QuebraCabeca
from jogo_1024 import Jogo1024
from dama import JogoDama
from xadrez import JogoXadrez
from labirinto import Labirinto
from Sobrevivencia.main import SobrevivenciaGame

class MiniGamesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Menu de Mini-Games")
        self.root.geometry("660x520")
        self.root.configure(bg="#1E293B")  # Um azul muito escuro para dar um ar moderno
        self.root.resizable(False, False)

        # Centralizar janela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (660 // 2)
        y = (self.root.winfo_screenheight() // 2) - (520 // 2)
        self.root.geometry(f"+{x}+{y}")

        # Título
        self.title_label = tk.Label(
            self.root, text="Arcade de Mini-Games", 
            font=("Segoe UI", 26, "bold"), 
            bg="#1E293B", fg="#F8FAFC"
        )
        self.title_label.pack(pady=(35, 5))

        self.subtitle_label = tk.Label(
            self.root, text="Selecione um jogo na coleção abaixo:", 
            font=("Segoe UI", 12), 
            bg="#1E293B", fg="#94A3B8"
        )
        self.subtitle_label.pack(pady=(0, 30))

        # Pixel virtual para permitir tamanhos exatos em pixels nos botões
        self.pixel_virtual = tk.PhotoImage(width=1, height=1)

        # Frame principal
        self.main_frame = tk.Frame(self.root, bg="#1E293B")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas para rolagem
        self.canvas = tk.Canvas(self.main_frame, bg="#1E293B", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        self.scrollbar = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Frame do Grid dentro do Canvas
        self.grid_frame = tk.Frame(self.canvas, bg="#1E293B")
        self.canvas.create_window((330, 0), window=self.grid_frame, anchor="n")

        # Configurar scroll com mouse wheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Lista de jogos: (Nome, Comando, Cor Base, Cor Hover)
        games = [
            ("Jogo da\nVelha", self.abrir_jogo_da_velha, "#EF4444", "#DC2626"),
            ("Campo\nMinado", self.abrir_campo_minado, "#F59E0B", "#D97706"),
            ("Sudoku", self.abrir_sudoku, "#3B82F6", "#2563EB"),
            ("Tetris", self.abrir_tetris, "#8B5CF6", "#7C3AED"),
            ("Ping Pong", self.abrir_ping_pong, "#10B981", "#059669"),
            ("Cobrinha", self.abrir_cobrinha, "#22C55E", "#16A34A"),
            ("Sapo", self.abrir_sapo, "#06B6D4", "#0891B2"),
            ("Passarinho", self.abrir_passarinho, "#EAB308", "#CA8A04"),
            ("Puyo Puyo", self.abrir_puyo_puyo, "#EC4899", "#BE185D"),
            ("Space\nInvaders", self.abrir_space_invaders, "#A855F7", "#7E22CE"),
            ("Candy\nCrush", self.abrir_candy_crush, "#F472B6", "#DB2777"),
            ("Quebra\nCabeça", self.abrir_quebra_cabeca, "#F97316", "#EA580C"),
            ("1024\nNeon", self.abrir_1024, "#B500FF", "#8A2BE2"),
            ("Dama\n1x1", self.abrir_dama, "#E11D48", "#BE123C"),
            ("Xadrez", self.abrir_xadrez, "#64748B", "#475569"),
            ("Labirinto", self.abrir_labirinto, "#14B8A6", "#0F766E"),
            ("Sobrevi-\nvencia", self.abrir_sobrevivencia, "#0EA5E9", "#0284C7")
        ]

        btn_style = {
            "font": ("Segoe UI", 13, "bold"),
            "fg": "#FFFFFF",
            "activeforeground": "#FFFFFF",
            "relief": "flat",
            "bd": 0,
            "cursor": "hand2",
            "image": self.pixel_virtual,
            "compound": "center",
            "width": 125,
            "height": 125
        }

        # Popula o Grid formatado em matriz (4 colunas)
        for i, (name, cmd, bg_color, hover_color) in enumerate(games):
            btn = tk.Button(
                self.grid_frame, text=name, command=cmd,
                bg=bg_color, activebackground=bg_color,
                **btn_style
            )
            
            # Efeito hover mágico
            btn.bind("<Enter>", lambda e, b=btn, c=hover_color: b.config(bg=c))
            btn.bind("<Leave>", lambda e, b=btn, c=bg_color: b.config(bg=c))
            
            row = i // 4
            col = i % 4
            btn.grid(row=row, column=col, padx=12, pady=12)

    def abrir_jogo_da_velha(self):
        # Esconde o menu principal
        self.root.withdraw()
        
        # Cria uma nova janela para o jogo
        jogo_window = tk.Toplevel(self.root)
        
        # O callback mostra a janela raiz novamente
        def on_return():
            self.root.deiconify()
            
        app = JogoDaVelha(jogo_window, on_menu_return=on_return)

        # Se a janela do jogo for fechada no 'X', voltamos para o menu principal
        def on_close():
            jogo_window.destroy()
            self.root.deiconify()
            
        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_campo_minado(self):
        self.root.withdraw()
        
        jogo_window = tk.Toplevel(self.root)
        
        def on_return():
            self.root.deiconify()
            
        app = CampoMinado(jogo_window, on_menu_return=on_return)

        def on_close():
            jogo_window.destroy()
            self.root.deiconify()
            
        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_sudoku(self):
        self.root.withdraw()
        
        jogo_window = tk.Toplevel(self.root)
        
        def on_return():
            self.root.deiconify()
            
        app = Sudoku(jogo_window, on_menu_return=on_return)

        def on_close():
            jogo_window.destroy()
            self.root.deiconify()
            
        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_tetris(self):
        self.root.withdraw()
        jogo = TetrisGame()
        result = jogo.run()
        if result == "quit":
            self.root.destroy()
        else:
            self.root.deiconify()

    def abrir_ping_pong(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = PingPong(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_loop()
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_cobrinha(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = Cobrinha(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_loop()
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_sapo(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = Sapo(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_loop()
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_passarinho(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = Passarinho(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_loop()
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_puyo_puyo(self):
        self.root.withdraw()
        jogo = PuyoPuyoGame()
        result = jogo.run()
        if result == "quit":
            self.root.destroy()
        else:
            self.root.deiconify()

    def abrir_space_invaders(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = SpaceInvaders(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_loop()
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_candy_crush(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = CandyCrush(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_loop()
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_quebra_cabeca(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = QuebraCabeca(jogo_window, on_menu_return=on_return)

        def on_close():
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_1024(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = Jogo1024(jogo_window, on_menu_return=on_return)

        def on_close():
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_dama(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = JogoDama(jogo_window, on_menu_return=on_return)

        def on_close():
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_xadrez(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = JogoXadrez(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_timers() if hasattr(app, 'cancel_timers') else None
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_labirinto(self):
        self.root.withdraw()

        jogo_window = tk.Toplevel(self.root)

        def on_return():
            self.root.deiconify()

        app = Labirinto(jogo_window, on_menu_return=on_return)

        def on_close():
            app.cancel_loop()
            jogo_window.destroy()
            self.root.deiconify()

        jogo_window.protocol("WM_DELETE_WINDOW", on_close)

    def abrir_sobrevivencia(self):
        self.root.withdraw()
        jogo = SobrevivenciaGame()
        result = jogo.run()
        if result == "quit":
            self.root.destroy()
        else:
            self.root.deiconify()

if __name__ == "__main__":
    root = tk.Tk()
    app = MiniGamesApp(root)
    root.mainloop()

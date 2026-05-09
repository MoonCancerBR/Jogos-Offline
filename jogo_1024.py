import tkinter as tk
from tkinter import messagebox
import random
import winsound
import threading
import time

class Jogo1024:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("1024 - Cyberpunk Edition")
        self.root.geometry("400x600")
        
        # Cores Cyberpunk/Neon
        self.color_bg = "#0D0E15"
        self.color_grid_bg = "#1A1C29"
        self.color_empty = "#24273A"
        self.color_text_dark = "#0D0E15"
        self.color_text_light = "#FFFFFF"

        self.root.configure(bg=self.color_bg)
        self.root.resizable(False, False)

        # Mapeamento de cores Neon para os números
        self.tile_colors = {
            1: ("#FF0055", self.color_text_light),    # Rosa Neon
            2: ("#00FFCC", self.color_text_dark),     # Ciano
            4: ("#B500FF", self.color_text_light),    # Roxo Neon
            8: ("#39FF14", self.color_text_dark),     # Verde Limão
            16: ("#FFEA00", self.color_text_dark),    # Amarelo Neon
            32: ("#FF5E00", self.color_text_light),   # Laranja Neon
            64: ("#FF0099", self.color_text_light),   # Magenta
            128: ("#00B8FF", self.color_text_dark),   # Azul Claro
            256: ("#8A2BE2", self.color_text_light),  # Azul Violeta
            512: ("#FF3366", self.color_text_light),  # Rosa Choque
            1024: ("#00FF00", self.color_text_dark),  # Verde Brilhante
            2048: ("#FFD700", self.color_text_dark),  # Ouro
        }

        self.board = [[0]*4 for _ in range(4)]
        self.score = 0
        self.game_active = False

        # Título
        self.title_label = tk.Label(
            self.root, text="1024", 
            font=("Segoe UI", 32, "bold"), 
            bg=self.color_bg, fg="#00FFCC"
        )
        self.title_label.pack(pady=(20, 5))

        # Pontuação
        self.score_label = tk.Label(
            self.root, text="Score: 0", 
            font=("Segoe UI", 16), 
            bg=self.color_bg, fg="#FF0055"
        )
        self.score_label.pack(pady=(0, 20))

        # Frame do grid
        self.grid_frame = tk.Frame(self.root, bg=self.color_grid_bg, bd=4)
        self.grid_frame.pack(padx=20, pady=10)

        # Labels das células (em vez de botões, usaremos labels)
        self.cells = []
        for i in range(4):
            row = []
            for j in range(4):
                frame = tk.Frame(self.grid_frame, bg=self.color_empty, width=75, height=75)
                frame.grid(row=i, column=j, padx=4, pady=4)
                frame.grid_propagate(False) # Mantém o tamanho fixo
                
                label = tk.Label(frame, text="", bg=self.color_empty, font=("Segoe UI", 24, "bold"))
                label.place(relx=0.5, rely=0.5, anchor="center") # Centraliza o texto
                row.append(label)
            self.cells.append(row)

        # Botões de ação
        btn_frame = tk.Frame(self.root, bg=self.color_bg)
        btn_frame.pack(pady=20)
        
        self.reset_btn = tk.Button(
            btn_frame, text="Reiniciar", font=("Segoe UI", 12, "bold"), 
            bg="#B500FF", fg="#FFFFFF", activebackground="#8A2BE2", activeforeground="#FFFFFF", 
            relief="flat", bd=0, padx=20, pady=8, command=self.start_game, cursor="hand2"
        )
        self.reset_btn.pack(side=tk.LEFT, padx=10)

        # Bind de teclas
        self.root.bind("<Up>", lambda e: self.move("UP"))
        self.root.bind("<Down>", lambda e: self.move("DOWN"))
        self.root.bind("<Left>", lambda e: self.move("LEFT"))
        self.root.bind("<Right>", lambda e: self.move("RIGHT"))

        self.start_game()

    def play_sound(self, sound_type):
        def _play():
            if sound_type == "merge":
                winsound.Beep(800, 50)
            elif sound_type == "move":
                winsound.Beep(400, 30)
            elif sound_type == "game_over":
                winsound.Beep(300, 200)
                time.sleep(0.1)
                winsound.Beep(200, 300)
        threading.Thread(target=_play, daemon=True).start()

    def start_game(self):
        self.board = [[0]*4 for _ in range(4)]
        self.score = 0
        self.game_active = True
        self.spawn_new_tile()
        self.spawn_new_tile()
        self.update_ui()

    def get_max_tile(self):
        return max(max(row) for row in self.board)

    def generate_new_value(self):
        max_tile = self.get_max_tile()
        
        rand = random.random()
        if rand < 0.70:
            return 1
        elif rand < 0.90:
            return 2
        else:
            # 10% de chance de nascer algo maior, baseado no progresso
            if max_tile < 16:
                return 4
            else:
                # Pode nascer até max_tile // 8
                limit = max(4, max_tile // 8)
                possible_values = []
                val = 4
                while val <= limit:
                    possible_values.append(val)
                    val *= 2
                return random.choice(possible_values)

    def spawn_new_tile(self):
        empty_spots = [(i, j) for i in range(4) for j in range(4) if self.board[i][j] == 0]
        if empty_spots:
            i, j = random.choice(empty_spots)
            self.board[i][j] = self.generate_new_value()

    def compress(self, mat):
        changed = False
        new_mat = [[0]*4 for _ in range(4)]
        for i in range(4):
            pos = 0
            for j in range(4):
                if mat[i][j] != 0:
                    new_mat[i][pos] = mat[i][j]
                    if j != pos:
                        changed = True
                    pos += 1
        return new_mat, changed

    def merge(self, mat):
        changed = False
        for i in range(4):
            for j in range(3):
                if mat[i][j] == mat[i][j+1] and mat[i][j] != 0:
                    mat[i][j] *= 2
                    mat[i][j+1] = 0
                    self.score += mat[i][j]
                    changed = True
        return mat, changed

    def reverse(self, mat):
        new_mat = []
        for i in range(4):
            new_mat.append(mat[i][::-1])
        return new_mat

    def transpose(self, mat):
        new_mat = [[0]*4 for _ in range(4)]
        for i in range(4):
            for j in range(4):
                new_mat[i][j] = mat[j][i]
        return new_mat

    def move(self, direction):
        if not self.game_active:
            return

        mat = self.board
        changed1 = changed2 = changed3 = False
        
        if direction == "LEFT":
            mat, changed1 = self.compress(mat)
            mat, changed2 = self.merge(mat)
            mat, changed3 = self.compress(mat)
        elif direction == "RIGHT":
            mat = self.reverse(mat)
            mat, changed1 = self.compress(mat)
            mat, changed2 = self.merge(mat)
            mat, changed3 = self.compress(mat)
            mat = self.reverse(mat)
        elif direction == "UP":
            mat = self.transpose(mat)
            mat, changed1 = self.compress(mat)
            mat, changed2 = self.merge(mat)
            mat, changed3 = self.compress(mat)
            mat = self.transpose(mat)
        elif direction == "DOWN":
            mat = self.transpose(mat)
            mat = self.reverse(mat)
            mat, changed1 = self.compress(mat)
            mat, changed2 = self.merge(mat)
            mat, changed3 = self.compress(mat)
            mat = self.reverse(mat)
            mat = self.transpose(mat)

        changed = changed1 or changed2 or changed3
        self.board = mat

        if changed:
            if changed2:
                self.play_sound("merge")
            else:
                self.play_sound("move")
                
            self.spawn_new_tile()
            self.update_ui()
            
            if self.check_game_over():
                self.game_active = False
                self.play_sound("game_over")
                self.root.after(1000, self.show_game_over_popup)

    def check_game_over(self):
        # Tem espaço vazio?
        for i in range(4):
            for j in range(4):
                if self.board[i][j] == 0:
                    return False
        
        # Dá pra fundir horizontal?
        for i in range(4):
            for j in range(3):
                if self.board[i][j] == self.board[i][j+1]:
                    return False
                    
        # Dá pra fundir vertical?
        for i in range(3):
            for j in range(4):
                if self.board[i][j] == self.board[i+1][j]:
                    return False
                    
        return True

    def update_ui(self):
        self.score_label.config(text=f"Score: {self.score}")
        for i in range(4):
            for j in range(4):
                val = self.board[i][j]
                cell = self.cells[i][j]
                frame = cell.master # O frame pai que segura o fundo
                
                if val == 0:
                    cell.config(text="", bg=self.color_empty)
                    frame.config(bg=self.color_empty)
                else:
                    bg_color, fg_color = self.tile_colors.get(val, ("#FFFFFF", "#0D0E15")) # Fallback pra branco se for muito grande
                    
                    # Ajusta tamanho da fonte para números grandes
                    font_size = 24
                    text_str = str(val)
                    if len(text_str) >= 4:
                        font_size = 18
                    elif len(text_str) >= 5:
                        font_size = 14
                        
                    cell.config(text=text_str, bg=bg_color, fg=fg_color, font=("Segoe UI", font_size, "bold"))
                    frame.config(bg=bg_color)

    def show_game_over_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Game Over")
        popup.geometry("300x220")
        popup.configure(bg=self.color_bg)
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 110
        popup.geometry(f"+{x}+{y}")
        
        lbl = tk.Label(popup, text=f"Game Over!\nSem mais movimentos.\n\nScore Final: {self.score}", 
                       font=("Segoe UI", 12, "bold"), bg=self.color_bg, fg="#FF0055")
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
        
        tk.Button(popup, text="Jogar Novamente", bg="#00FFCC", activebackground="#00B8FF", command=play_again, **btn_style).pack(pady=3)
        tk.Button(popup, text="Trocar de Jogo", bg="#B500FF", activebackground="#8A2BE2", command=change_game, **btn_style).pack(pady=3)
        tk.Button(popup, text="Sair", bg="#FF0055", activebackground="#FF3366", command=quit_game, **btn_style).pack(pady=3)

if __name__ == "__main__":
    root = tk.Tk()
    app = Jogo1024(root)
    root.mainloop()

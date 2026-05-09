import tkinter as tk
import random

class CandyCrush:
    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Candy Crush - Sugar Rush")
        
        self.color_bg = "#111827" # Mais escuro pra neon
        self.root.configure(bg=self.color_bg)
        
        self.rows = 8
        self.cols = 8
        self.cell_size = 60
        self.num_types = 6
        
        self.mode = None
        self.level = 1
        self.score = 0
        self.target_score = 5000
        self.moves = 20
        self.combo_multiplier = 1
        
        self.grid = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        self.selected = None
        self.animating = False
        
        self.hint_timer = None
        self.hint_cells = None
        self.floating_texts = []
        
        # Frames
        self.menu_frame = None
        self.game_frame = None
        self.top_frame = None
        self.canvas = None
        
        self.show_mode_selection()

    def show_mode_selection(self):
        self.root.geometry("400x500")
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 250
        self.root.geometry(f"+{x}+{y}")
        
        if self.game_frame: self.game_frame.destroy()
        if self.top_frame: self.top_frame.destroy()
        
        self.menu_frame = tk.Frame(self.root, bg=self.color_bg)
        self.menu_frame.pack(expand=True)
        
        tk.Label(self.menu_frame, text="CANDY CRUSH", font=("Segoe UI", 28, "bold"), fg="#F472B6", bg=self.color_bg).pack(pady=(0, 5))
        tk.Label(self.menu_frame, text="SUGAR RUSH", font=("Segoe UI", 16, "bold"), fg="#34D399", bg=self.color_bg).pack(pady=(0, 40))
        
        btn_style = {"font": ("Segoe UI", 14, "bold"), "fg": "white", "relief": "flat", "bd": 0, "cursor": "hand2", "width": 15, "pady": 10}
        
        tk.Button(self.menu_frame, text="Modo Casual", bg="#3B82F6", activebackground="#2563EB", command=lambda: self.start_game('casual'), **btn_style).pack(pady=10)
        tk.Label(self.menu_frame, text="Jogue infinito, sem limites", font=("Segoe UI", 10), fg="#9CA3AF", bg=self.color_bg).pack(pady=(0, 20))
        
        tk.Button(self.menu_frame, text="Modo Arcade", bg="#8B5CF6", activebackground="#7C3AED", command=lambda: self.start_game('arcade'), **btn_style).pack(pady=10)
        tk.Label(self.menu_frame, text="Fases, alvos e limite de turnos", font=("Segoe UI", 10), fg="#9CA3AF", bg=self.color_bg).pack(pady=(0, 20))
        
        tk.Button(self.menu_frame, text="Sair", font=("Segoe UI", 12, "bold"), bg="#4B5563", fg="white", activebackground="#374151", relief="flat", bd=0, cursor="hand2", width=15, pady=5, command=self.voltar_menu).pack(pady=20)

    def start_game(self, mode):
        self.mode = mode
        if self.menu_frame:
            self.menu_frame.destroy()
            self.menu_frame = None
            
        self.level = 1
        self.score = 0
        
        self.setup_ui()
        self.init_level()

    def setup_ui(self):
        width = self.cols * self.cell_size + 40
        height = self.rows * self.cell_size + 160
        self.root.geometry(f"{width}x{height}")
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"+{x}+{y}")
        
        self.top_frame = tk.Frame(self.root, bg=self.color_bg)
        self.top_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.score_label = tk.Label(self.top_frame, text="0", font=("Segoe UI", 18, "bold"), bg=self.color_bg, fg="#34D399")
        self.score_label.pack(side=tk.LEFT, padx=10)
        
        if self.mode == 'arcade':
            self.level_label = tk.Label(self.top_frame, text="Level: 1", font=("Segoe UI", 14, "bold"), bg=self.color_bg, fg="#FBBF24")
            self.level_label.pack(side=tk.LEFT, padx=10)
            
            self.moves_label = tk.Label(self.top_frame, text="Moves: 20", font=("Segoe UI", 14, "bold"), bg=self.color_bg, fg="#F87171")
            self.moves_label.pack(side=tk.LEFT, padx=10)
        else:
            tk.Label(self.top_frame, text="Modo Casual", font=("Segoe UI", 14, "bold"), bg=self.color_bg, fg="#60A5FA").pack(side=tk.LEFT, padx=10)
            
        self.btn_voltar = tk.Button(self.top_frame, text="Abandonar", font=("Segoe UI", 10, "bold"), bg="#EF4444", fg="white",
                                    activebackground="#DC2626", relief="flat", bd=0, padx=10, cursor="hand2", command=self.show_mode_selection)
        self.btn_voltar.pack(side=tk.RIGHT)
        
        self.game_frame = tk.Frame(self.root, bg=self.color_bg)
        self.game_frame.pack()
        
        canvas_width = self.cols * self.cell_size
        canvas_height = self.rows * self.cell_size
        self.canvas = tk.Canvas(self.game_frame, width=canvas_width, height=canvas_height, bg="#1F2937", highlightthickness=4, highlightbackground="#374151")
        self.canvas.pack(pady=5)
        self.canvas.bind("<Button-1>", self.on_click)

    def voltar_menu(self):
        self.cancel_hint()
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def cancel_loop(self):
        self.cancel_hint()

    def init_level(self):
        if self.mode == 'arcade':
            self.target_score = 5000 + (self.level - 1) * 2500
            self.moves = 20 + self.level
        self.combo_multiplier = 1
        
        self.update_hud()
        self.init_grid()
        self.draw_grid()
        self.reset_hint_timer()
        self.check_board_state()

    def update_hud(self):
        if self.mode == 'arcade':
            self.level_label.config(text=f"Lvl: {self.level}")
            self.score_label.config(text=f"{self.score} / {self.target_score}")
            self.moves_label.config(text=f"Moves: {self.moves}")
        else:
            self.score_label.config(text=f"Score: {self.score}")

    def init_grid(self):
        for r in range(self.rows):
            for c in range(self.cols):
                while True:
                    color = random.randint(0, self.num_types - 1)
                    self.grid[r][c] = {'color': color, 'type': 'normal'}
                    if self.check_initial_match(r, c):
                        continue
                    break

    def check_initial_match(self, r, c):
        color = self.grid[r][c]['color']
        if c >= 2 and self.grid[r][c-1] and self.grid[r][c-2]:
            if self.grid[r][c-1]['color'] == color and self.grid[r][c-2]['color'] == color:
                return True
        if r >= 2 and self.grid[r-1][c] and self.grid[r-2][c]:
            if self.grid[r-1][c]['color'] == color and self.grid[r-2][c]['color'] == color:
                return True
        if r >= 1 and c >= 1 and self.grid[r-1][c] and self.grid[r][c-1] and self.grid[r-1][c-1]:
            if self.grid[r-1][c]['color'] == color and self.grid[r][c-1]['color'] == color and self.grid[r-1][c-1]['color'] == color:
                return True
        return False

    def reset_hint_timer(self):
        self.cancel_hint()
        self.hint_timer = self.root.after(15000, self.show_hint)

    def cancel_hint(self):
        if self.hint_timer:
            self.root.after_cancel(self.hint_timer)
            self.hint_timer = None
        if self.hint_cells:
            self.hint_cells = None
            if not self.animating:
                self.draw_grid()

    def show_hint(self):
        if self.animating: return
        move = self.find_possible_move()
        if move:
            self.hint_cells = [move[0], move[1]]
            self.draw_grid()

    def find_possible_move(self):
        for r in range(self.rows):
            for c in range(self.cols):
                if c < self.cols - 1:
                    self.grid[r][c], self.grid[r][c+1] = self.grid[r][c+1], self.grid[r][c]
                    m = self.check_matches(virt=True)
                    self.grid[r][c], self.grid[r][c+1] = self.grid[r][c+1], self.grid[r][c]
                    if m or self.is_special_swap(r, c, r, c+1): return ((r, c), (r, c+1))
                if r < self.rows - 1:
                    self.grid[r][c], self.grid[r+1][c] = self.grid[r+1][c], self.grid[r][c]
                    m = self.check_matches(virt=True)
                    self.grid[r][c], self.grid[r+1][c] = self.grid[r+1][c], self.grid[r][c]
                    if m or self.is_special_swap(r, c, r+1, c): return ((r, c), (r+1, c))
        return None

    def shuffle_board(self):
        self.add_floating_text("SHUFFLING!", self.rows//2, self.cols//2, "#F472B6", font_size=28)
        
        items = []
        for r in range(self.rows):
            for c in range(self.cols):
                items.append(self.grid[r][c])
                
        valid = False
        attempts = 0
        while not valid and attempts < 100:
            random.shuffle(items)
            idx = 0
            for r in range(self.rows):
                for c in range(self.cols):
                    self.grid[r][c] = items[idx]
                    idx += 1
            # Checa se nao gerou matches instantaneos e tem jogada
            if not self.check_matches(virt=True) and self.find_possible_move() is not None:
                valid = True
            attempts += 1
            
        if not valid:
            # Fallback extremo: recria
            self.init_grid()
            
        self.draw_grid()
        self.reset_hint_timer()

    def check_board_state(self):
        if not self.animating:
            if not self.find_possible_move():
                self.shuffle_board()

    def add_floating_text(self, text, r, c, color="#FBBF24", font_size=16):
        x = c * self.cell_size + self.cell_size / 2
        y = r * self.cell_size + self.cell_size / 2
        self.floating_texts.append({'text': text, 'x': x, 'y': y, 'life': 20, 'color': color, 'font_size': font_size})
        if len(self.floating_texts) == 1:
            self.update_floating_texts()

    def update_floating_texts(self):
        active = []
        for ft in self.floating_texts:
            ft['life'] -= 1
            ft['y'] -= 2
            if ft['life'] > 0:
                active.append(ft)
        self.floating_texts = active
        self.draw_grid()
        if active:
            self.root.after(40, self.update_floating_texts)

    def draw_grid(self):
        if not self.canvas: return
        self.canvas.delete("all")
        
        for r in range(self.rows):
            for c in range(self.cols):
                x0 = c * self.cell_size
                y0 = r * self.cell_size
                x1 = x0 + self.cell_size
                y1 = y0 + self.cell_size
                
                bg_color = "#1F2937" if (r + c) % 2 == 0 else "#111827"
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=bg_color, outline="", tags="bg")
                
                if self.selected == (r, c):
                    self.canvas.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline="#F472B6", width=4)
                
                if self.hint_cells and (r, c) in self.hint_cells:
                    self.canvas.create_rectangle(x0+2, y0+2, x1-2, y1-2, outline="#34D399", width=4, dash=(4, 4))

                cell = self.grid[r][c]
                if cell is not None:
                    self.draw_candy(c, r, cell)

        for ft in self.floating_texts:
            f = ("Segoe UI", ft['font_size'], "bold")
            # Adiciona shadow pra dar o efeito "Dopamina"
            self.canvas.create_text(ft['x']+2, ft['y']+2, text=ft['text'], font=f, fill="#000000")
            self.canvas.create_text(ft['x'], ft['y'], text=ft['text'], font=f, fill=ft['color'])

    def draw_candy(self, c, r, cell):
        pad = 8
        x0 = c * self.cell_size + pad
        y0 = r * self.cell_size + pad
        x1 = (c + 1) * self.cell_size - pad
        y1 = (r + 1) * self.cell_size - pad
        cx = (x0 + x1) / 2
        cy = (y0 + y1) / 2

        color = cell['color']
        ctype = cell['type']
        
        hex_colors = ["#5D4037", "#FFF9C4", "#E53935", "#FB8C00", "#7CB342", "#039BE5"]
        outlines = ["#3E2723", "#FBC02D", "#B71C1C", "#E65100", "#558B2F", "#01579B"]
        
        fill = hex_colors[color] if color != -1 else "#212121"
        out = outlines[color] if color != -1 else "#000000"

        if color == -1 or ctype == 'color_bomb':
            self.canvas.create_oval(x0, y0, x1, y1, fill="#111827", outline="#F472B6", width=2)
            self.canvas.create_oval(cx-8, cy-8, cx-4, cy-4, fill="#E53935", outline="")
            self.canvas.create_oval(cx+4, cy-8, cx+8, cy-4, fill="#7CB342", outline="")
            self.canvas.create_oval(cx-8, cy+4, cx-4, cy+8, fill="#039BE5", outline="")
            self.canvas.create_oval(cx+4, cy+4, cx+8, cy+8, fill="#FFF9C4", outline="")
            return

        if color == 0:
            self.canvas.create_oval(x0, y0, x1, y1, fill=fill, outline=out, width=2)
        elif color == 1:
            self.canvas.create_oval(x0, y0, x1, y1, fill=fill, outline=out, width=2)
        elif color == 2:
            self.canvas.create_oval(x0, y0+5, x1, y1-5, fill=fill, outline=out, width=2)
        elif color == 3:
            self.canvas.create_rectangle(x0+5, y0+5, x1-5, y1-5, fill=fill, outline=out, width=2)
        elif color == 4:
            self.canvas.create_oval(x0+5, y0, x1-5, y1, fill=fill, outline=out, width=2)
        elif color == 5:
            self.canvas.create_polygon([cx, y0, x1, cy, cx, y1, x0, cy], fill=fill, outline=out, width=2)

        if ctype == 'striped_h':
            self.canvas.create_line(x0, cy, x1, cy, fill="#FFFFFF", width=5)
        elif ctype == 'striped_v':
            self.canvas.create_line(cx, y0, cx, y1, fill="#FFFFFF", width=5)
        elif ctype == 'wrapped':
            self.canvas.create_rectangle(x0-2, y0-2, x1+2, y1+2, outline="#34D399", width=3)
        elif ctype == 'star':
            self.canvas.create_line(cx-12, cy, cx+12, cy, fill="#FBBF24", width=4)
            self.canvas.create_line(cx, cy-12, cx, cy+12, fill="#FBBF24", width=4)

    def on_click(self, event):
        if self.animating: return
        self.reset_hint_timer()
        
        c = event.x // self.cell_size
        r = event.y // self.cell_size
        
        if not (0 <= r < self.rows and 0 <= c < self.cols): return
        
        if self.selected:
            sr, sc = self.selected
            if (abs(sr - r) == 1 and sc == c) or (abs(sc - c) == 1 and sr == r):
                self.selected = None
                self.try_swap(sr, sc, r, c)
            elif (sr, sc) == (r, c):
                self.selected = None
                self.draw_grid()
            else:
                self.selected = (r, c)
                self.draw_grid()
        else:
            self.selected = (r, c)
            self.draw_grid()

    def is_special_swap(self, r1, c1, r2, c2):
        t1 = self.grid[r1][c1]['type'] if self.grid[r1][c1] else None
        t2 = self.grid[r2][c2]['type'] if self.grid[r2][c2] else None
        if t1 == 'color_bomb' or t2 == 'color_bomb': return True
        if t1 and t2 and t1.startswith('striped') and t2.startswith('striped'): return True
        return False

    def try_swap(self, r1, c1, r2, c2):
        self.animating = True
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        self.draw_grid()
        
        if self.is_special_swap(r1, c1, r2, c2):
            if self.mode == 'arcade': self.moves -= 1
            self.combo_multiplier = 1
            self.update_hud()
            self.root.after(200, lambda: self.process_special_swap(r1, c1, r2, c2))
            return

        matches = self.check_matches()
        if not matches:
            self.root.after(300, lambda: self.revert_swap(r1, c1, r2, c2))
        else:
            if self.mode == 'arcade': self.moves -= 1
            self.combo_multiplier = 1
            self.update_hud()
            self.root.after(200, lambda: self.process_matches(matches, (r1, c1), (r2, c2)))

    def revert_swap(self, r1, c1, r2, c2):
        self.grid[r1][c1], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r1][c1]
        self.draw_grid()
        self.animating = False
        self.check_board_state()

    def process_special_swap(self, r1, c1, r2, c2):
        t1 = self.grid[r1][c1]['type']
        t2 = self.grid[r2][c2]['type']
        
        to_destroy = set()
        
        if t1 == 'color_bomb' and t2 == 'color_bomb':
            self.add_floating_text("BIG BANG!", r1, c1, "#FBBF24", 24)
            for r in range(self.rows):
                for c in range(self.cols):
                    to_destroy.add((r, c))
                    
        elif t1 == 'color_bomb' or t2 == 'color_bomb':
            cb_r, cb_c = (r1, c1) if t1 == 'color_bomb' else (r2, c2)
            other_r, other_c = (r2, c2) if t1 == 'color_bomb' else (r1, c1)
            other_type = self.grid[other_r][other_c]['type']
            target_color = self.grid[other_r][other_c]['color']
            to_destroy.add((cb_r, cb_c))
            
            if other_type == 'normal':
                to_destroy.add((other_r, other_c))
                self.add_floating_text("Color Wipe!", cb_r, cb_c, "#34D399", 20)
                for r in range(self.rows):
                    for c in range(self.cols):
                        if self.grid[r][c] and self.grid[r][c]['color'] == target_color:
                            to_destroy.add((r, c))
            else:
                self.add_floating_text("SUPER CLONE!", cb_r, cb_c, "#FBBF24", 24)
                for r in range(self.rows):
                    for c in range(self.cols):
                        if self.grid[r][c] and self.grid[r][c]['color'] == target_color:
                            self.grid[r][c]['type'] = other_type
                            to_destroy.add((r, c))
                            
        elif t1.startswith('striped') and t2.startswith('striped'):
            self.add_floating_text("Cross Striped!", r1, c1, "#60A5FA", 20)
            to_destroy.add((r1, c1))
            to_destroy.add((r2, c2))
            self.combo_multiplier += 1 

            for stype, r, c in [(t1, r1, c1), (t2, r2, c2)]:
                if stype == 'striped_h':
                    for i in range(self.cols): to_destroy.add((r, i))
                elif stype == 'striped_v':
                    for i in range(self.rows): to_destroy.add((i, c))
                        
        self.execute_destruction(to_destroy)

    def check_matches(self, virt=False):
        h_lines = []
        for r in range(self.rows):
            c = 0
            while c < self.cols:
                if not self.grid[r][c]:
                    c += 1
                    continue
                color = self.grid[r][c]['color']
                start = c
                while c < self.cols and self.grid[r][c] and self.grid[r][c]['color'] == color:
                    c += 1
                length = c - start
                if length >= 3: h_lines.append(set((r, i) for i in range(start, c)))
                    
        v_lines = []
        for c in range(self.cols):
            r = 0
            while r < self.rows:
                if not self.grid[r][c]:
                    r += 1
                    continue
                color = self.grid[r][c]['color']
                start = r
                while r < self.rows and self.grid[r][c] and self.grid[r][c]['color'] == color:
                    r += 1
                length = r - start
                if length >= 3: v_lines.append(set((i, c) for i in range(start, r)))

        squares = []
        for r in range(self.rows - 1):
            for c in range(self.cols - 1):
                if not self.grid[r][c]: continue
                color = self.grid[r][c]['color']
                if self.grid[r][c+1] and self.grid[r+1][c] and self.grid[r+1][c+1]:
                    if self.grid[r][c+1]['color'] == color and self.grid[r+1][c]['color'] == color and self.grid[r+1][c+1]['color'] == color:
                        squares.append(set([(r, c), (r, c+1), (r+1, c), (r+1, c+1)]))

        if virt:
            return len(h_lines) > 0 or len(v_lines) > 0 or len(squares) > 0

        groups = []
        for sq in squares: groups.append({'cells': sq, 'type': 'square2x2'})

        all_lines = h_lines + v_lines
        used = [False] * len(all_lines)
        
        for i in range(len(all_lines)):
            if used[i]: continue
            group_cells = set(all_lines[i])
            used[i] = True
            
            changed = True
            while changed:
                changed = False
                for j in range(len(all_lines)):
                    if not used[j] and len(group_cells.intersection(all_lines[j])) > 0:
                        group_cells = group_cells.union(all_lines[j])
                        used[j] = True
                        changed = True
            
            max_h_len = 0
            max_v_len = 0
            for r in range(self.rows):
                in_row = [c for c in range(self.cols) if (r, c) in group_cells]
                if len(in_row) > max_h_len: max_h_len = len(in_row)
            for c in range(self.cols):
                in_col = [r for r in range(self.rows) if (r, c) in group_cells]
                if len(in_col) > max_v_len: max_v_len = len(in_col)

            special = None
            if max_h_len >= 5 or max_v_len >= 5: special = 'color_bomb'
            elif max_h_len >= 3 and max_v_len >= 3:
                if len(group_cells) == 5:
                    is_star = False
                    for (rr, cc) in group_cells:
                        viz = sum(1 for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)] if (rr+dr, cc+dc) in group_cells)
                        if viz == 4:
                            is_star = True
                            break
                    special = 'star' if is_star else 'wrapped'
                else: special = 'wrapped'
            elif max_h_len == 4: special = 'striped_v' 
            elif max_v_len == 4: special = 'striped_h'
            
            groups.append({'cells': group_cells, 'type': special})

        return groups

    def process_matches(self, groups, pos1=None, pos2=None):
        to_destroy = set()
        new_specials = {}
        
        for g in groups:
            cells = g['cells']
            stype = g['type']
            
            if stype == 'square2x2':
                self.add_floating_text("4x4 BOOM!", list(cells)[0][0], list(cells)[0][1], "#F87171", 20)
                min_r = min(r for r, c in cells)
                min_c = min(c for r, c in cells)
                for dr in range(-1, 3):
                    for dc in range(-1, 3):
                        nr, nc = min_r + dr, min_c + dc
                        if 0 <= nr < self.rows and 0 <= nc < self.cols:
                            to_destroy.add((nr, nc))
                continue

            to_destroy.update(cells)
            if stype:
                target_pos = None
                if pos1 in cells: target_pos = pos1
                elif pos2 in cells: target_pos = pos2
                else: target_pos = list(cells)[0]
                    
                if pos1 and pos2:
                    if stype == 'striped_h' or stype == 'striped_v':
                        if pos1[0] == pos2[0]: stype = 'striped_v'
                        else: stype = 'striped_h'
                        
                new_specials[target_pos] = stype

        self.execute_destruction(to_destroy, new_specials)

    def execute_destruction(self, initial_destroy_set, new_specials=None):
        if not new_specials: new_specials = {}
        
        destroy_queue = list(initial_destroy_set)
        destroyed_final = set()
        
        while destroy_queue:
            r, c = destroy_queue.pop(0)
            if (r, c) in destroyed_final: continue
            destroyed_final.add((r, c))
            
            if not self.grid[r][c]: continue
            
            if self.grid[r][c]['type'] != 'normal' and (r, c) not in new_specials:
                ctype = self.grid[r][c]['type']
                self.add_floating_text("Chain Reaction!", r, c, "#F472B6", 14)
                if ctype == 'striped_h':
                    for i in range(self.cols):
                        if (r, i) not in destroyed_final: destroy_queue.append((r, i))
                elif ctype == 'striped_v':
                    for i in range(self.rows):
                        if (i, c) not in destroyed_final: destroy_queue.append((i, c))
                elif ctype == 'wrapped':
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            nr, nc = r+dr, c+dc
                            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                                if (nr, nc) not in destroyed_final: destroy_queue.append((nr, nc))
                elif ctype == 'star':
                    for i in range(self.cols):
                        if (r, i) not in destroyed_final: destroy_queue.append((r, i))
                    for i in range(self.rows):
                        if (i, c) not in destroyed_final: destroy_queue.append((i, c))
                elif ctype == 'color_bomb':
                    target_color = random.randint(0, self.num_types - 1)
                    for rr in range(self.rows):
                        for cc in range(self.cols):
                            if self.grid[rr][cc] and self.grid[rr][cc]['color'] == target_color:
                                if (rr, cc) not in destroyed_final: destroy_queue.append((rr, cc))

        if len(destroyed_final) > 0:
            dopamine_texts = ["AWESOME!", "SWEET!", "UNBELIEVABLE!", "INSANE!", "SUGAR RUSH!"]
            if self.combo_multiplier > 1:
                p = list(destroyed_final)[0]
                idx = min(self.combo_multiplier - 2, len(dopamine_texts) - 1)
                text = f"Combo x{self.combo_multiplier}\n{dopamine_texts[idx]}"
                self.add_floating_text(text, p[0], p[1], "#C084FC", 18)
                
            # BUFF Extremo de Pontuação (Base subiu pra 50, multiplicador agora é quadrático)
            base_points = 50
            multiplier_power = self.combo_multiplier ** 2
            pts = len(destroyed_final) * base_points * multiplier_power
            
            self.score += pts
            self.add_floating_text(f"+{pts}", list(destroyed_final)[0][0], list(destroyed_final)[0][1], "#34D399", 18)
            self.update_hud()
            
            for (r, c) in destroyed_final:
                self.grid[r][c] = None
                
            for (r, c), stype in new_specials.items():
                color = -1 if stype == 'color_bomb' else random.randint(0, self.num_types-1)
                self.grid[r][c] = {'color': color, 'type': stype}
                self.add_floating_text("PowerUp!", r, c, "#FBBF24", 16)
                
            self.draw_grid()
            self.root.after(200, self.apply_gravity)
        else:
            self.end_turn()

    def apply_gravity(self):
        moved = False
        for c in range(self.cols):
            for r in range(self.rows - 1, 0, -1):
                if not self.grid[r][c]:
                    for k in range(r - 1, -1, -1):
                        if self.grid[k][c]:
                            self.grid[r][c] = self.grid[k][c]
                            self.grid[k][c] = None
                            moved = True
                            break
                            
        for c in range(self.cols):
            for r in range(self.rows):
                if not self.grid[r][c]:
                    self.grid[r][c] = {'color': random.randint(0, self.num_types - 1), 'type': 'normal'}
                    moved = True
                    
        self.draw_grid()
        
        if moved:
            self.root.after(300, self.check_chain_reaction)
        else:
            self.end_turn()

    def check_chain_reaction(self):
        self.combo_multiplier += 1
        matches = self.check_matches()
        if matches:
            self.process_matches(matches)
        else:
            self.end_turn()

    def end_turn(self):
        self.animating = False
        self.draw_grid()
        
        if self.mode == 'arcade':
            if self.score >= self.target_score:
                self.level_clear()
            elif self.moves <= 0:
                self.game_over()
            else:
                self.check_board_state()
        else:
            # Modo Casual não tem vitória nem derrota por movimentos
            self.check_board_state()

    def level_clear(self):
        self.animating = True
        self.cancel_hint()
        popup = tk.Toplevel(self.root)
        popup.title("Nível Concluído!")
        popup.geometry("300x150")
        popup.configure(bg="#1E1E2E")
        popup.transient(self.root)
        popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        popup.geometry(f"+{x}+{y}")
        
        tk.Label(popup, text="LEVEL CLEAR!", font=("Segoe UI", 20, "bold"), bg="#1E1E2E", fg="#34D399").pack(pady=20)
        
        def next_level():
            popup.destroy()
            self.level += 1
            self.score = 0
            self.animating = False
            self.init_level()
            
        tk.Button(popup, text="Próximo Nível", font=("Segoe UI", 12, "bold"), bg="#FBBF24", fg="#1E1E2E",
                  activebackground="#F59E0B", command=next_level, relief="flat", padx=10).pack()

    def game_over(self):
        self.animating = True
        self.cancel_hint()
        popup = tk.Toplevel(self.root)
        popup.title("Fim de Jogo")
        popup.geometry("300x200")
        popup.configure(bg="#1E1E2E")
        popup.transient(self.root)
        popup.grab_set()
        
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 100
        popup.geometry(f"+{x}+{y}")
        
        tk.Label(popup, text="GAME OVER", font=("Segoe UI", 20, "bold"), bg="#1E1E2E", fg="#F87171").pack(pady=10)
        tk.Label(popup, text=f"Score: {self.score}", font=("Segoe UI", 12), bg="#1E1E2E", fg="white").pack(pady=5)
        
        def restart():
            popup.destroy()
            self.level = 1
            self.animating = False
            self.init_level()
            
        def sair():
            popup.destroy()
            self.show_mode_selection()
            
        tk.Button(popup, text="Jogar Novamente", font=("Segoe UI", 10, "bold"), bg="#3B82F6", fg="white", command=restart, relief="flat", width=15).pack(pady=5)
        tk.Button(popup, text="Mudar Modo", font=("Segoe UI", 10, "bold"), bg="#6B7280", fg="white", command=sair, relief="flat", width=15).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = CandyCrush(root)
    root.mainloop()

import math
import random
import tkinter as tk


class Labirinto:
    MAZE_COLS = 15
    MAZE_ROWS = 15
    TILE = 20
    GRID_COLS = MAZE_COLS * 2 + 1
    GRID_ROWS = MAZE_ROWS * 2 + 1
    CANVAS_WIDTH = GRID_COLS * TILE
    CANVAS_HEIGHT = GRID_ROWS * TILE
    PLAYER_RADIUS = 7
    EXIT_RADIUS = 9
    KEY_SPEED = 3.8
    PATH_SPEED = 5.4
    FRAME_MS = 16

    WALL = 1
    PATH = 0

    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Labirinto")
        self.root.configure(bg="#101820")
        self.root.resizable(False, False)

        self.loop_id = None
        self.canvas = None
        self.status_label = None
        self.info_label = None
        self.level = 1
        self.invalid_paths = 0

        self.grid = []
        self.start_center = (0, 0)
        self.exit_center = (0, 0)
        self.player_x = 0
        self.player_y = 0
        self.pressed_keys = set()

        self.is_dragging = False
        self.drag_points = []
        self.drag_invalid = False
        self.path_points = []
        self.finished = False
        self.status_text = ""

        self.color_bg = "#101820"
        self.color_panel = "#17212B"
        self.color_board = "#F7FAFC"
        self.color_wall = "#1F2937"
        self.color_wall_edge = "#0F172A"
        self.color_path = "#E2E8F0"
        self.color_text = "#F8FAFC"
        self.color_muted = "#94A3B8"
        self.color_player = "#EF4444"
        self.color_exit = "#22C55E"
        self.color_start = "#38BDF8"

        self.setup_start_screen()

    def center_window(self, width, height):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def cancel_loop(self):
        if self.loop_id is not None:
            try:
                self.root.after_cancel(self.loop_id)
            except tk.TclError:
                pass
            self.loop_id = None

    def clear_window(self):
        self.cancel_loop()
        for child in self.root.winfo_children():
            child.destroy()

    def make_button(self, parent, text, color, command, width=20):
        return tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 11, "bold"),
            bg=color,
            fg="#FFFFFF",
            activebackground=color,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            width=width,
            pady=8,
            cursor="hand2",
            command=command,
        )

    def setup_start_screen(self):
        self.clear_window()
        self.center_window(460, 430)

        frame = tk.Frame(self.root, bg=self.color_bg)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Labirinto",
            font=("Segoe UI", 30, "bold"),
            bg=self.color_bg,
            fg=self.color_text,
        ).pack(pady=(46, 8))

        tk.Label(
            frame,
            text="Leve o ponto vermelho de A ate B.",
            font=("Segoe UI", 12),
            bg=self.color_bg,
            fg=self.color_muted,
        ).pack(pady=(0, 28))

        self.make_button(frame, "Iniciar Jogo", "#22C55E", lambda: self.start_game(reset_level=True)).pack(pady=8)
        self.make_button(frame, "Voltar ao Menu", "#64748B", self.voltar_menu).pack(pady=(18, 0))

        tk.Label(
            frame,
            text="Setas/WASD movem  |  Arraste o ponto para desenhar um trajeto",
            font=("Segoe UI", 9),
            bg=self.color_bg,
            fg="#64748B",
        ).pack(side=tk.BOTTOM, pady=24)

    def voltar_menu(self):
        self.cancel_loop()
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def start_game(self, reset_level=False, advance_level=False):
        self.clear_window()
        if reset_level:
            self.level = 1
            self.invalid_paths = 0
        elif advance_level:
            self.level += 1

        self.finished = False
        self.is_dragging = False
        self.drag_points = []
        self.drag_invalid = False
        self.path_points = []
        self.pressed_keys.clear()
        self.status_text = "Chegue ate a area verde B."

        self.generate_maze()
        self.player_x, self.player_y = self.start_center
        self.build_game_ui()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.focus_set()
        self.render()
        self.game_loop()

    def build_game_ui(self):
        width = self.CANVAS_WIDTH + 60
        height = self.CANVAS_HEIGHT + 142
        self.center_window(width, height)

        top_frame = tk.Frame(self.root, bg=self.color_panel)
        top_frame.pack(fill=tk.X)

        tk.Label(
            top_frame,
            text="Labirinto",
            font=("Segoe UI", 17, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=12,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(20, 8), pady=12)

        self.info_label = tk.Label(
            top_frame,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=32,
            anchor="w",
        )
        self.info_label.pack(side=tk.LEFT, padx=8)

        btn_style = {
            "font": ("Segoe UI", 9, "bold"),
            "fg": "#FFFFFF",
            "relief": "flat",
            "bd": 0,
            "cursor": "hand2",
            "padx": 8,
            "pady": 6,
        }
        tk.Button(top_frame, text="Menu", bg="#0EA5E9", command=self.voltar_menu, **btn_style).pack(side=tk.RIGHT, padx=(4, 20))
        tk.Button(top_frame, text="Novo mapa", bg="#F59E0B", command=lambda: self.start_game(reset_level=False), **btn_style).pack(side=tk.RIGHT, padx=4)
        tk.Button(top_frame, text="Proximo", bg="#22C55E", command=lambda: self.start_game(advance_level=True), **btn_style).pack(side=tk.RIGHT, padx=4)

        self.canvas = tk.Canvas(
            self.root,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg=self.color_board,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(18, 10))
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        self.status_label = tk.Label(
            self.root,
            text="",
            font=("Segoe UI", 10),
            bg=self.color_bg,
            fg=self.color_muted,
        )
        self.status_label.pack(pady=(0, 10))

    def generate_maze(self):
        self.grid = [[self.WALL for _ in range(self.GRID_COLS)] for _ in range(self.GRID_ROWS)]
        visited = [[False for _ in range(self.MAZE_COLS)] for _ in range(self.MAZE_ROWS)]

        def carve(cx, cy):
            visited[cy][cx] = True
            gx = cx * 2 + 1
            gy = cy * 2 + 1
            self.grid[gy][gx] = self.PATH

            directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            random.shuffle(directions)
            for dx, dy in directions:
                nx = cx + dx
                ny = cy + dy
                if 0 <= nx < self.MAZE_COLS and 0 <= ny < self.MAZE_ROWS and not visited[ny][nx]:
                    self.grid[gy + dy][gx + dx] = self.PATH
                    carve(nx, ny)

        carve(0, 0)
        self.start_center = self.cell_center(1, 1)
        self.exit_center = self.cell_center(self.GRID_COLS - 2, self.GRID_ROWS - 2)

    def cell_center(self, grid_x, grid_y):
        return (
            grid_x * self.TILE + self.TILE / 2,
            grid_y * self.TILE + self.TILE / 2,
        )

    def on_key_press(self, event):
        key = event.keysym.lower()
        if key in {"up", "down", "left", "right", "w", "a", "s", "d"}:
            self.pressed_keys.add(key)
        elif key == "r":
            self.start_game(reset_level=False)
        elif key == "n":
            self.start_game(advance_level=True)
        elif key == "escape":
            self.voltar_menu()

    def on_key_release(self, event):
        self.pressed_keys.discard(event.keysym.lower())

    def on_mouse_down(self, event):
        if self.finished or self.path_points:
            return
        if self.distance(event.x, event.y, self.player_x, self.player_y) <= self.PLAYER_RADIUS + 9:
            self.is_dragging = True
            self.drag_invalid = False
            self.drag_points = [(self.player_x, self.player_y)]
            self.status_text = "Desenhe o trajeto e solte para o ponto seguir."
            self.render()

    def on_mouse_drag(self, event):
        if not self.is_dragging:
            return

        last_x, last_y = self.drag_points[-1]
        next_point = (event.x, event.y)
        if self.distance(last_x, last_y, next_point[0], next_point[1]) < 4:
            return

        if not self.segment_is_clear(last_x, last_y, next_point[0], next_point[1]):
            self.drag_invalid = True
            self.status_text = "Trajeto invalido: a linha atravessou uma parede."

        self.drag_points.append(next_point)
        self.render()

    def on_mouse_up(self, _event):
        if not self.is_dragging:
            return

        self.is_dragging = False
        if self.drag_invalid or len(self.drag_points) < 2:
            self.invalid_paths += 1
            self.status_text = "Trajeto descartado. Comece no ponto vermelho e evite as paredes."
            self.drag_points = []
            self.render()
            return

        self.path_points = self.simplify_path(self.drag_points[1:])
        self.drag_points = []
        self.status_text = "Seguindo o trajeto desenhado..."
        self.render()

    def simplify_path(self, points):
        simplified = []
        for point in points:
            if not simplified or self.distance(point[0], point[1], simplified[-1][0], simplified[-1][1]) >= 5:
                simplified.append(point)
        return simplified

    def game_loop(self):
        self.loop_id = None
        if self.finished:
            return

        if self.path_points:
            self.follow_drawn_path()
        else:
            self.move_from_keyboard()

        self.check_victory()
        self.render()

        if not self.finished:
            self.loop_id = self.root.after(self.FRAME_MS, self.game_loop)

    def move_from_keyboard(self):
        dx = 0
        dy = 0
        if "left" in self.pressed_keys or "a" in self.pressed_keys:
            dx -= 1
        if "right" in self.pressed_keys or "d" in self.pressed_keys:
            dx += 1
        if "up" in self.pressed_keys or "w" in self.pressed_keys:
            dy -= 1
        if "down" in self.pressed_keys or "s" in self.pressed_keys:
            dy += 1

        if dx == 0 and dy == 0:
            return

        length = math.hypot(dx, dy)
        step_x = (dx / length) * self.KEY_SPEED
        step_y = (dy / length) * self.KEY_SPEED
        self.try_move(step_x, step_y)

    def follow_drawn_path(self):
        if not self.path_points:
            return

        target_x, target_y = self.path_points[0]
        dx = target_x - self.player_x
        dy = target_y - self.player_y
        distance = math.hypot(dx, dy)

        if distance <= self.PATH_SPEED:
            if self.segment_is_clear(self.player_x, self.player_y, target_x, target_y):
                self.player_x = target_x
                self.player_y = target_y
            else:
                self.path_points = []
                self.status_text = "Movimento bloqueado por uma parede."
                return
            self.path_points.pop(0)
            if not self.path_points:
                self.status_text = "Trajeto concluido. Continue ate B."
            return

        step_x = (dx / distance) * self.PATH_SPEED
        step_y = (dy / distance) * self.PATH_SPEED
        if not self.try_move(step_x, step_y):
            self.path_points = []
            self.status_text = "Movimento bloqueado por uma parede."

    def try_move(self, dx, dy):
        moved = False
        next_x = self.player_x + dx
        next_y = self.player_y
        if not self.circle_hits_wall(next_x, next_y):
            self.player_x = next_x
            moved = True

        next_x = self.player_x
        next_y = self.player_y + dy
        if not self.circle_hits_wall(next_x, next_y):
            self.player_y = next_y
            moved = True

        return moved

    def segment_is_clear(self, x1, y1, x2, y2):
        distance = self.distance(x1, y1, x2, y2)
        steps = max(1, int(distance / 2.5))
        for index in range(steps + 1):
            t = index / steps
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            if self.circle_hits_wall(x, y):
                return False
        return True

    def circle_hits_wall(self, cx, cy):
        radius = self.PLAYER_RADIUS
        min_col = int((cx - radius) // self.TILE)
        max_col = int((cx + radius) // self.TILE)
        min_row = int((cy - radius) // self.TILE)
        max_row = int((cy + radius) // self.TILE)

        if min_col < 0 or min_row < 0 or max_col >= self.GRID_COLS or max_row >= self.GRID_ROWS:
            return True

        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                if self.grid[row][col] == self.WALL and self.circle_intersects_cell(cx, cy, col, row):
                    return True
        return False

    def circle_intersects_cell(self, cx, cy, col, row):
        x1 = col * self.TILE
        y1 = row * self.TILE
        x2 = x1 + self.TILE
        y2 = y1 + self.TILE
        closest_x = min(max(cx, x1), x2)
        closest_y = min(max(cy, y1), y2)
        return self.distance(cx, cy, closest_x, closest_y) <= self.PLAYER_RADIUS

    def check_victory(self):
        if self.distance(self.player_x, self.player_y, self.exit_center[0], self.exit_center[1]) <= self.EXIT_RADIUS + self.PLAYER_RADIUS:
            self.finished = True
            self.path_points = []
            self.drag_points = []
            self.status_text = "Voce venceu! Pressione N ou clique em Proximo para gerar outro nivel."
            self.cancel_loop()

    def render(self):
        if not self.canvas:
            return

        self.canvas.delete("all")
        self.info_label.config(text=f"Nivel: {self.level}  |  Linhas invalidas: {self.invalid_paths}")
        self.status_label.config(text=self.status_text)

        self.draw_maze()
        self.draw_start_and_exit()
        self.draw_drag_path()
        self.draw_player()

        if self.finished:
            self.draw_victory_overlay()

    def draw_maze(self):
        self.canvas.create_rectangle(
            0,
            0,
            self.CANVAS_WIDTH,
            self.CANVAS_HEIGHT,
            fill=self.color_path,
            outline="",
        )
        for row, cells in enumerate(self.grid):
            for col, cell in enumerate(cells):
                if cell == self.WALL:
                    x1 = col * self.TILE
                    y1 = row * self.TILE
                    x2 = x1 + self.TILE
                    y2 = y1 + self.TILE
                    self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.color_wall, outline=self.color_wall_edge)

        self.canvas.create_rectangle(
            1,
            1,
            self.CANVAS_WIDTH - 1,
            self.CANVAS_HEIGHT - 1,
            outline="#0F172A",
            width=3,
        )

    def draw_start_and_exit(self):
        sx, sy = self.start_center
        ex, ey = self.exit_center

        self.canvas.create_oval(
            sx - self.EXIT_RADIUS,
            sy - self.EXIT_RADIUS,
            sx + self.EXIT_RADIUS,
            sy + self.EXIT_RADIUS,
            fill=self.color_start,
            outline="#E0F2FE",
            width=2,
        )
        self.canvas.create_text(sx, sy, text="A", fill="#082F49", font=("Segoe UI", 9, "bold"))

        self.canvas.create_oval(
            ex - self.EXIT_RADIUS,
            ey - self.EXIT_RADIUS,
            ex + self.EXIT_RADIUS,
            ey + self.EXIT_RADIUS,
            fill=self.color_exit,
            outline="#DCFCE7",
            width=2,
        )
        self.canvas.create_text(ex, ey, text="B", fill="#052E16", font=("Segoe UI", 9, "bold"))

    def draw_drag_path(self):
        points = []
        color = "#60A5FA"
        if self.is_dragging and len(self.drag_points) > 1:
            points = self.drag_points
            color = "#EF4444" if self.drag_invalid else "#38BDF8"
        elif self.path_points:
            points = [(self.player_x, self.player_y)] + self.path_points
            color = "#22C55E"

        if len(points) < 2:
            return

        flattened = []
        for x, y in points:
            flattened.extend([x, y])
        self.canvas.create_line(
            *flattened,
            fill=color,
            width=4,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
            smooth=True,
        )

    def draw_player(self):
        x = self.player_x
        y = self.player_y
        r = self.PLAYER_RADIUS
        self.canvas.create_oval(x - r - 3, y - r - 3, x + r + 3, y + r + 3, fill="#FECACA", outline="")
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=self.color_player, outline="#7F1D1D", width=2)

    def draw_victory_overlay(self):
        self.canvas.create_rectangle(
            0,
            0,
            self.CANVAS_WIDTH,
            self.CANVAS_HEIGHT,
            fill="#020617",
            stipple="gray50",
            outline="",
        )
        self.canvas.create_text(
            self.CANVAS_WIDTH // 2,
            self.CANVAS_HEIGHT // 2 - 34,
            text="VOCE VENCEU!",
            fill="#F8FAFC",
            font=("Segoe UI", 30, "bold"),
        )
        self.canvas.create_text(
            self.CANVAS_WIDTH // 2,
            self.CANVAS_HEIGHT // 2 + 12,
            text="Pressione N para gerar um novo labirinto",
            fill="#CBD5E1",
            font=("Segoe UI", 12),
        )
        self.canvas.create_text(
            self.CANVAS_WIDTH // 2,
            self.CANVAS_HEIGHT // 2 + 42,
            text="R reinicia  |  Esc volta ao menu",
            fill="#94A3B8",
            font=("Segoe UI", 10),
        )

    def distance(self, x1, y1, x2, y2):
        return math.hypot(x2 - x1, y2 - y1)


if __name__ == "__main__":
    root = tk.Tk()
    app = Labirinto(root)
    root.mainloop()

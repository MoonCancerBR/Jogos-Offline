import random
import tkinter as tk


class Cobrinha:
    COLS = 24
    ROWS = 24
    CELL = 22
    CANVAS_SIZE = COLS * CELL
    BASE_DELAY = 170
    MIN_DELAY = 80
    FOOD_POINTS = 25
    BOOST_FOOD_POINTS = 70
    SPECIAL_POINTS = 50
    BOOST_DURATION_STEPS = 65
    BOOST_EXTRA_GROWTH = 2
    BOMB_STOP_SCORE = 500
    BOMB_MIN_FREE_CELLS = 120
    BOMB_TTL_STEPS = 42
    SPECIAL_TTL_STEPS = 85

    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Cobrinha")
        self.root.configure(bg="#0F172A")
        self.root.resizable(False, False)

        self.loop_id = None
        self.canvas = None
        self.snake = []
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = (0, 0)
        self.score = 0
        self.high_score = 0
        self.level = 1
        self.foods_eaten = 0
        self.delay = self.BASE_DELAY
        self.pending_growth = 0
        self.bombs = {}
        self.special_food = None
        self.special_ttl = 0
        self.special_cooldown = 0
        self.boost_steps_remaining = 0
        self.is_paused = False
        self.game_over = False
        self.started = False

        self.color_bg = "#0F172A"
        self.color_panel = "#111827"
        self.color_board = "#020617"
        self.color_grid = "#1E293B"
        self.color_text = "#F8FAFC"
        self.color_muted = "#94A3B8"
        self.color_snake = "#22C55E"
        self.color_snake_head = "#86EFAC"
        self.color_food = "#EF4444"
        self.color_special = "#FDE047"
        self.color_bomb = "#111827"

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

    def setup_start_screen(self):
        self.clear_window()
        self.started = False
        self.game_over = False
        self.is_paused = False
        self.center_window(430, 430)

        frame = tk.Frame(self.root, bg=self.color_bg)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Cobrinha",
            font=("Segoe UI", 30, "bold"),
            bg=self.color_bg,
            fg=self.color_text,
        ).pack(pady=(46, 8))

        tk.Label(
            frame,
            text="Coma, cresca e desvie das surpresas.",
            font=("Segoe UI", 12),
            bg=self.color_bg,
            fg=self.color_muted,
        ).pack(pady=(0, 28))

        self.make_button(frame, "Iniciar Jogo", "#22C55E", self.start_game).pack(pady=8)
        self.make_button(frame, "Voltar ao Menu", "#64748B", self.voltar_menu).pack(pady=(18, 0))

        controls = tk.Label(
            frame,
            text="Setas/WASD movem  |  Espaco pausa  |  R reinicia",
            font=("Segoe UI", 9),
            bg=self.color_bg,
            fg="#64748B",
        )
        controls.pack(side=tk.BOTTOM, pady=24)

    def make_button(self, parent, text, color, command):
        return tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 12, "bold"),
            bg=color,
            fg="#FFFFFF",
            activebackground=color,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            width=22,
            pady=9,
            cursor="hand2",
            command=command,
        )

    def start_game(self):
        self.clear_window()
        self.center_window(660, 700)
        self.started = True
        self.is_paused = False
        self.game_over = False
        self.score = 0
        self.level = 1
        self.foods_eaten = 0
        self.delay = self.BASE_DELAY
        self.pending_growth = 0
        self.bombs = {}
        self.special_food = None
        self.special_ttl = 0
        self.special_cooldown = 35
        self.boost_steps_remaining = 0

        center = (self.COLS // 2, self.ROWS // 2)
        self.snake = [
            center,
            (center[0] - 1, center[1]),
            (center[0] - 2, center[1]),
        ]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.spawn_food()

        self.build_game_ui()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_set()
        self.render()
        self.game_loop()

    def build_game_ui(self):
        top_frame = tk.Frame(self.root, bg=self.color_panel)
        top_frame.pack(fill=tk.X)

        tk.Label(
            top_frame,
            text="Cobrinha",
            font=("Segoe UI", 17, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=12,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(20, 8), pady=12)

        self.score_label = tk.Label(
            top_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=34,
            anchor="w",
        )
        self.score_label.pack(side=tk.LEFT, padx=8)

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
        tk.Button(top_frame, text="Pausar", bg="#64748B", command=self.toggle_pause, **btn_style).pack(side=tk.RIGHT, padx=4)
        tk.Button(top_frame, text="Reiniciar", bg="#F59E0B", command=self.start_game, **btn_style).pack(side=tk.RIGHT, padx=4)

        self.canvas = tk.Canvas(
            self.root,
            width=self.CANVAS_SIZE,
            height=self.CANVAS_SIZE,
            bg=self.color_board,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(26, 12))

        hint = tk.Label(
            self.root,
            text="Comida pontua e cresce. Bombas somem sozinhas, mas encerram o jogo. Fruta dourada ativa turbo.",
            font=("Segoe UI", 10),
            bg=self.color_bg,
            fg=self.color_muted,
        )
        hint.pack(pady=(0, 12))

    def voltar_menu(self):
        self.cancel_loop()
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def blocked_cells(self):
        blocked = set(self.snake)
        blocked.add(self.food)
        blocked.update(self.bombs.keys())
        if self.special_food is not None:
            blocked.add(self.special_food)
        return blocked

    def available_cells(self, include_food=False):
        blocked = self.blocked_cells()
        if include_food:
            blocked.discard(self.food)
        return [
            (x, y)
            for y in range(self.ROWS)
            for x in range(self.COLS)
            if (x, y) not in blocked
        ]

    def spawn_food(self):
        available = self.available_cells(include_food=True)
        if not available:
            self.finish_game("VOCE VENCEU", "A cobra ocupou o tabuleiro inteiro.")
            return
        self.food = random.choice(available)

    def boost_active(self):
        return self.boost_steps_remaining > 0

    def activate_boost(self):
        self.boost_steps_remaining = self.BOOST_DURATION_STEPS
        self.special_food = None
        self.special_ttl = 0
        self.special_cooldown = 75

    def bomb_spawns_allowed(self):
        free_cells = (self.COLS * self.ROWS) - len(set(self.snake))
        return (
            self.score < self.BOMB_STOP_SCORE
            and free_cells > self.BOMB_MIN_FREE_CELLS
            and self.foods_eaten >= 2
        )

    def update_dynamic_items(self):
        if self.boost_steps_remaining > 0:
            self.boost_steps_remaining -= 1

        expired_bombs = []
        for cell in list(self.bombs):
            self.bombs[cell] -= 1
            if self.bombs[cell] <= 0:
                expired_bombs.append(cell)
        for cell in expired_bombs:
            self.bombs.pop(cell, None)

        if not self.bomb_spawns_allowed():
            self.bombs.clear()
        elif len(self.bombs) < 3 and random.random() < 0.075:
            self.spawn_bomb()

        if self.special_food is not None:
            self.special_ttl -= 1
            if self.special_ttl <= 0:
                self.special_food = None
                self.special_cooldown = 45
        elif not self.boost_active():
            if self.special_cooldown > 0:
                self.special_cooldown -= 1
            elif self.foods_eaten >= 3 and random.random() < 0.035:
                self.spawn_special_food()

    def spawn_bomb(self):
        available = self.available_cells()
        if available:
            self.bombs[random.choice(available)] = self.BOMB_TTL_STEPS

    def spawn_special_food(self):
        available = self.available_cells()
        if available:
            self.special_food = random.choice(available)
            self.special_ttl = self.SPECIAL_TTL_STEPS

    def on_key_press(self, event):
        key = event.keysym.lower()
        directions = {
            "up": (0, -1),
            "w": (0, -1),
            "down": (0, 1),
            "s": (0, 1),
            "left": (-1, 0),
            "a": (-1, 0),
            "right": (1, 0),
            "d": (1, 0),
        }

        if key in directions:
            self.queue_direction(directions[key])
        elif key == "space":
            self.toggle_pause()
        elif key == "r":
            self.start_game()
        elif key == "escape":
            self.voltar_menu()

    def queue_direction(self, direction):
        if self.game_over:
            return
        opposite = (-self.direction[0], -self.direction[1])
        if direction != opposite:
            self.next_direction = direction

    def toggle_pause(self):
        if not self.started or self.game_over:
            return
        self.is_paused = not self.is_paused
        self.render()
        if not self.is_paused and self.loop_id is None:
            self.game_loop()

    def game_loop(self):
        self.loop_id = None
        if self.started and not self.is_paused and not self.game_over:
            self.step()
            self.render()
            self.loop_id = self.root.after(self.current_delay(), self.game_loop)

    def step(self):
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        if not self.inside_board(new_head):
            self.finish_game("FIM DE JOGO", "Voce bateu na parede.")
            return

        ate_food = new_head == self.food
        ate_special = self.special_food is not None and new_head == self.special_food
        ate_bomb = new_head in self.bombs

        if ate_bomb:
            self.finish_game("FIM DE JOGO", "Voce devorou uma bombinha.")
            return

        will_grow = ate_food or ate_special or self.pending_growth > 0
        body_to_check = self.snake if will_grow else self.snake[:-1]
        if not self.boost_active() and new_head in body_to_check:
            self.finish_game("FIM DE JOGO", "Voce bateu no proprio corpo.")
            return

        self.snake.insert(0, new_head)
        should_pop_tail = not ate_food and not ate_special and self.pending_growth == 0

        if ate_special:
            self.score += self.SPECIAL_POINTS
            self.pending_growth += 1
            self.activate_boost()

        if ate_food:
            if self.boost_active():
                self.score += self.BOOST_FOOD_POINTS
                self.pending_growth += self.BOOST_EXTRA_GROWTH
            else:
                self.score += self.FOOD_POINTS
            self.foods_eaten += 1
            self.update_speed()
            self.spawn_food()

        if should_pop_tail:
            self.snake.pop()
        elif not ate_food and not ate_special and self.pending_growth > 0:
            self.pending_growth -= 1

        self.high_score = max(self.high_score, self.score)
        self.update_dynamic_items()

    def inside_board(self, cell):
        x, y = cell
        return 0 <= x < self.COLS and 0 <= y < self.ROWS

    def update_speed(self):
        self.level = 1 + self.foods_eaten // 5
        self.delay = max(self.MIN_DELAY, self.BASE_DELAY - (self.level - 1) * 7)

    def current_delay(self):
        if self.boost_active():
            return max(48, int(self.delay * 0.62))
        return self.delay

    def finish_game(self, title, subtitle):
        self.game_over = True
        self.high_score = max(self.high_score, self.score)
        self.end_title = title
        self.end_subtitle = subtitle
        self.cancel_loop()
        self.render()

    def render(self):
        if not self.canvas:
            return

        self.canvas.delete("all")
        self.score_label.config(
            text=f"Pontos: {self.score}  |  Nivel: {self.level}  |  Recorde: {self.high_score}"
        )
        self.draw_board()
        self.draw_food()
        self.draw_special_food()
        self.draw_bombs()
        self.draw_snake()
        self.draw_boost_timer()

        if self.is_paused:
            self.draw_overlay("PAUSADO", "Espaco para continuar")
        elif self.game_over:
            self.draw_overlay(self.end_title, f"{self.end_subtitle}  |  R para reiniciar")

    def draw_board(self):
        for x in range(0, self.CANVAS_SIZE + 1, self.CELL):
            self.canvas.create_line(x, 0, x, self.CANVAS_SIZE, fill=self.color_grid)
        for y in range(0, self.CANVAS_SIZE + 1, self.CELL):
            self.canvas.create_line(0, y, self.CANVAS_SIZE, y, fill=self.color_grid)

        self.canvas.create_rectangle(
            1,
            1,
            self.CANVAS_SIZE - 1,
            self.CANVAS_SIZE - 1,
            outline="#334155",
            width=3,
        )

    def draw_food(self):
        x, y = self.food
        pad = 4
        x1 = x * self.CELL + pad
        y1 = y * self.CELL + pad
        x2 = (x + 1) * self.CELL - pad
        y2 = (y + 1) * self.CELL - pad
        self.canvas.create_oval(x1, y1, x2, y2, fill=self.color_food, outline="")
        self.canvas.create_oval(x1 + 5, y1 + 4, x1 + 10, y1 + 9, fill="#FCA5A5", outline="")

    def draw_special_food(self):
        if self.special_food is None:
            return

        x, y = self.special_food
        cx = x * self.CELL + self.CELL // 2
        cy = y * self.CELL + self.CELL // 2
        pulse = 2 if self.special_ttl % 8 < 4 else 0
        r = 8 + pulse
        self.canvas.create_oval(cx - r - 4, cy - r - 4, cx + r + 4, cy + r + 4, fill="#713F12", outline="")
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=self.color_special, outline="#FEF3C7", width=2)
        self.canvas.create_line(cx - 10, cy, cx + 10, cy, fill="#FFF7ED", width=2)
        self.canvas.create_line(cx, cy - 10, cx, cy + 10, fill="#FFF7ED", width=2)

    def draw_bombs(self):
        for (x, y), ttl in self.bombs.items():
            cx = x * self.CELL + self.CELL // 2
            cy = y * self.CELL + self.CELL // 2
            danger = ttl < 12
            fill = "#7F1D1D" if danger and ttl % 4 < 2 else self.color_bomb
            self.canvas.create_oval(cx - 8, cy - 8, cx + 8, cy + 8, fill=fill, outline="#F8FAFC", width=1)
            self.canvas.create_line(cx + 5, cy - 8, cx + 10, cy - 13, fill="#94A3B8", width=2)
            spark = "#FDE047" if ttl % 6 < 3 else "#FB923C"
            self.canvas.create_oval(cx + 8, cy - 15, cx + 13, cy - 10, fill=spark, outline="")

    def draw_snake(self):
        for index, (x, y) in enumerate(reversed(self.snake)):
            real_index = len(self.snake) - 1 - index
            is_head = real_index == 0
            pad = 2 if is_head else 3
            x1 = x * self.CELL + pad
            y1 = y * self.CELL + pad
            x2 = (x + 1) * self.CELL - pad
            y2 = (y + 1) * self.CELL - pad

            color = self.color_snake_head if is_head else self.segment_color(real_index)
            if self.boost_active():
                glow_colors = ["#FDE047", "#67E8F9", "#A7F3D0", "#F0ABFC"]
                glow = glow_colors[(real_index + self.boost_steps_remaining) % len(glow_colors)]
                self.canvas.create_rectangle(
                    x * self.CELL + 1,
                    y * self.CELL + 1,
                    (x + 1) * self.CELL - 1,
                    (y + 1) * self.CELL - 1,
                    fill=glow,
                    outline="",
                )
                color = "#F8FAFC" if is_head else glow
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#064E3B", width=1)

        self.draw_head_eyes()

    def segment_color(self, index):
        shades = ["#22C55E", "#16A34A", "#15803D", "#166534"]
        return shades[index % len(shades)]

    def draw_head_eyes(self):
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        cx = head_x * self.CELL
        cy = head_y * self.CELL

        if dx != 0:
            eye_y_offsets = (7, 14)
            eye_x = 15 if dx > 0 else 6
            positions = [(cx + eye_x, cy + off) for off in eye_y_offsets]
        else:
            eye_x_offsets = (7, 14)
            eye_y = 15 if dy > 0 else 6
            positions = [(cx + off, cy + eye_y) for off in eye_x_offsets]

        for ex, ey in positions:
            self.canvas.create_oval(ex - 2, ey - 2, ex + 2, ey + 2, fill="#052E16", outline="")

    def boost_seconds_remaining(self):
        if not self.boost_active():
            return 0
        return max(1, round((self.boost_steps_remaining * self.current_delay()) / 1000))

    def draw_boost_timer(self):
        if not self.boost_active():
            return

        seconds = self.boost_seconds_remaining()
        text = f"TURBO {seconds}s"
        self.canvas.create_rectangle(12, 12, 128, 44, fill="#422006", outline="#FDE047", width=2)
        self.canvas.create_text(
            70,
            28,
            text=text,
            fill="#FEF3C7",
            font=("Segoe UI", 12, "bold"),
        )

    def draw_overlay(self, title, subtitle):
        self.canvas.create_rectangle(
            0,
            0,
            self.CANVAS_SIZE,
            self.CANVAS_SIZE,
            fill="#020617",
            stipple="gray50",
            outline="",
        )
        self.canvas.create_text(
            self.CANVAS_SIZE // 2,
            self.CANVAS_SIZE // 2 - 28,
            text=title,
            fill="#F8FAFC",
            font=("Segoe UI", 30, "bold"),
        )
        self.canvas.create_text(
            self.CANVAS_SIZE // 2,
            self.CANVAS_SIZE // 2 + 20,
            text=subtitle,
            fill="#CBD5E1",
            font=("Segoe UI", 12),
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = Cobrinha(root)
    root.mainloop()

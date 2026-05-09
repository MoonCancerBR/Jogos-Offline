import math
import random
import tkinter as tk


class PingPong:
    WIDTH = 760
    HEIGHT = 500
    EFFECT_DEFINITIONS = {
        "multiball": {"label": "Multibola", "color": "#67E8F9", "duration": 0, "symbol": "M"},
        "wide": {"label": "Raquete larga", "color": "#38BDF8", "duration": 520, "symbol": "W"},
        "slim": {"label": "Raquete fina", "color": "#FB7185", "duration": 360, "symbol": "S"},
        "turbo": {"label": "Turbo", "color": "#F97316", "duration": 420, "symbol": "T"},
        "slow": {"label": "Camera lenta", "color": "#A78BFA", "duration": 420, "symbol": "L"},
        "gravity": {"label": "Gravidade", "color": "#FDE047", "duration": 420, "symbol": "G"},
        "chaos": {"label": "Caos", "color": "#E879F9", "duration": 300, "symbol": "C"},
        "safety": {"label": "Parede segura", "color": "#22C55E", "duration": 420, "symbol": "P"},
        "color": {"label": "Cores vivas", "color": "#14B8A6", "duration": 420, "symbol": "V"},
        "bonus": {"label": "Bonus", "color": "#FACC15", "duration": 0, "symbol": "+"},
    }

    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Ping Pong")
        self.root.configure(bg="#0F172A")
        self.root.resizable(False, False)

        self.mode = None
        self.canvas = None
        self.loop_id = None
        self.is_paused = False
        self.game_over = False
        self.keys_pressed = set()
        self.mouse_x = self.WIDTH // 2
        self.mouse_y = self.HEIGHT // 2

        self.color_bg = "#0F172A"
        self.color_panel = "#111827"
        self.color_text = "#F8FAFC"
        self.color_muted = "#94A3B8"
        self.color_blue = "#3B82F6"
        self.color_green = "#10B981"
        self.color_red = "#EF4444"
        self.color_yellow = "#F59E0B"

        self.setup_mode_screen()

    def center_window(self, width, height):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def clear_window(self):
        self.cancel_loop()
        for child in self.root.winfo_children():
            child.destroy()

    def cancel_loop(self):
        if self.loop_id is not None:
            try:
                self.root.after_cancel(self.loop_id)
            except tk.TclError:
                pass
            self.loop_id = None

    def setup_mode_screen(self):
        self.clear_window()
        self.mode = None
        self.is_paused = False
        self.game_over = False
        self.center_window(430, 430)

        frame = tk.Frame(self.root, bg=self.color_bg)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Ping Pong",
            font=("Segoe UI", 28, "bold"),
            bg=self.color_bg,
            fg=self.color_text,
        ).pack(pady=(42, 8))

        tk.Label(
            frame,
            text="Escolha o modo de jogo",
            font=("Segoe UI", 12),
            bg=self.color_bg,
            fg=self.color_muted,
        ).pack(pady=(0, 28))

        self.make_menu_button(frame, "Pong 1x1 local", "#3B82F6", lambda: self.start_game("pong")).pack(pady=8)
        self.make_menu_button(frame, "Atari Breakout", "#10B981", lambda: self.start_game("breakout")).pack(pady=8)
        self.make_menu_button(frame, "Voltar ao Menu", "#64748B", self.voltar_menu).pack(pady=(26, 0))

    def make_menu_button(self, parent, text, color, command):
        return tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 13, "bold"),
            bg=color,
            fg="#FFFFFF",
            activebackground=color,
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            width=24,
            pady=10,
            cursor="hand2",
            command=command,
        )

    def start_game(self, mode):
        self.clear_window()
        self.mode = mode
        self.is_paused = False
        self.game_over = False
        self.keys_pressed.clear()
        self.center_window(820, 620)

        top_frame = tk.Frame(self.root, bg=self.color_panel)
        top_frame.pack(fill=tk.X)

        title = "Pong 1x1 local" if mode == "pong" else "Atari Breakout"
        self.title_label = tk.Label(
            top_frame,
            text=title,
            font=("Segoe UI", 16, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=18,
            anchor="w",
        )
        self.title_label.pack(side=tk.LEFT, padx=(20, 10), pady=12)

        self.score_label = tk.Label(
            top_frame,
            text="",
            font=("Segoe UI", 12, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=24,
        )
        self.score_label.pack(side=tk.LEFT, padx=8)

        self.info_label = tk.Label(
            top_frame,
            text="",
            font=("Segoe UI", 10),
            bg=self.color_panel,
            fg=self.color_muted,
            width=28,
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
        tk.Button(top_frame, text="Pausar", bg="#64748B", command=self.toggle_pause, **btn_style).pack(side=tk.RIGHT, padx=(4, 20))
        tk.Button(top_frame, text="Menu", bg="#0EA5E9", command=self.voltar_menu, **btn_style).pack(side=tk.RIGHT, padx=4)
        tk.Button(top_frame, text="Modos", bg="#10B981", command=self.setup_mode_screen, **btn_style).pack(side=tk.RIGHT, padx=4)
        tk.Button(top_frame, text="Reiniciar", bg="#F59E0B", command=lambda: self.start_game(self.mode), **btn_style).pack(side=tk.RIGHT, padx=4)

        self.canvas = tk.Canvas(
            self.root,
            width=self.WIDTH,
            height=self.HEIGHT,
            bg="#020617",
            highlightthickness=0,
        )
        self.canvas.pack(padx=30, pady=24)

        if mode == "breakout":
            self.canvas.bind("<Motion>", self.on_mouse_move)
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.root.focus_set()
        self.canvas.focus_set()

        if mode == "pong":
            self.setup_pong()
        else:
            self.setup_breakout()

        self.game_loop()

    def on_key_press(self, event):
        key = event.keysym.lower()
        self.keys_pressed.add(key)
        if key == "space":
            self.toggle_pause()

    def on_key_release(self, event):
        self.keys_pressed.discard(event.keysym.lower())

    def on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def toggle_pause(self):
        if self.game_over or self.mode is None:
            return
        self.is_paused = not self.is_paused
        self.render_current_game()

    def voltar_menu(self):
        self.cancel_loop()
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def game_loop(self):
        if self.mode and not self.is_paused and not self.game_over:
            if self.mode == "pong":
                self.update_pong()
            else:
                self.update_breakout()

        self.render_current_game()
        if self.mode and not self.game_over:
            self.loop_id = self.root.after(16, self.game_loop)

    def render_current_game(self):
        if not self.canvas:
            return
        if self.mode == "pong":
            self.render_pong()
        elif self.mode == "breakout":
            self.render_breakout()

        if self.is_paused:
            self.draw_center_overlay("PAUSADO", "Espaco para continuar")
        elif self.game_over:
            self.draw_center_overlay(self.end_title, self.end_subtitle)

    def draw_center_overlay(self, title, subtitle):
        self.canvas.create_rectangle(0, 0, self.WIDTH, self.HEIGHT, fill="#020617", stipple="gray50", outline="", tags="overlay")
        self.canvas.create_text(
            self.WIDTH // 2,
            self.HEIGHT // 2 - 20,
            text=title,
            fill="#F8FAFC",
            font=("Segoe UI", 32, "bold"),
            tags="overlay",
        )
        self.canvas.create_text(
            self.WIDTH // 2,
            self.HEIGHT // 2 + 24,
            text=subtitle,
            fill="#CBD5E1",
            font=("Segoe UI", 13),
            tags="overlay",
        )

    # Pong
    def setup_pong(self):
        self.left_score = 0
        self.right_score = 0
        self.paddle_w = 12
        self.paddle_h = 92
        self.left_paddle_x = 42
        self.right_paddle_x = self.WIDTH - 54
        self.left_paddle_y = self.HEIGHT // 2
        self.right_paddle_y = self.HEIGHT // 2
        self.reset_pong_ball()

    def reset_pong_ball(self):
        direction = random.choice([-1, 1])
        angle = random.uniform(-0.55, 0.55)
        speed = 5.8
        self.pong_ball = {
            "x": self.WIDTH / 2,
            "y": self.HEIGHT / 2,
            "dx": direction * speed * math.cos(angle),
            "dy": speed * math.sin(angle),
            "r": 9,
        }

    def update_pong(self):
        left_move = 0
        right_move = 0
        if "w" in self.keys_pressed:
            left_move -= 8
        if "s" in self.keys_pressed:
            left_move += 8
        if "up" in self.keys_pressed:
            right_move -= 8
        if "down" in self.keys_pressed:
            right_move += 8

        self.left_paddle_y += left_move
        self.right_paddle_y += right_move
        self.left_paddle_y = max(self.paddle_h / 2, min(self.HEIGHT - self.paddle_h / 2, self.left_paddle_y))
        self.right_paddle_y = max(self.paddle_h / 2, min(self.HEIGHT - self.paddle_h / 2, self.right_paddle_y))

        ball = self.pong_ball
        ball["x"] += ball["dx"]
        ball["y"] += ball["dy"]

        if ball["y"] - ball["r"] <= 0 or ball["y"] + ball["r"] >= self.HEIGHT:
            ball["dy"] *= -1
            ball["y"] = max(ball["r"], min(self.HEIGHT - ball["r"], ball["y"]))

        self.check_pong_paddle_collision(self.left_paddle_x, self.left_paddle_y, True)
        self.check_pong_paddle_collision(self.right_paddle_x, self.right_paddle_y, False)

        if ball["x"] < -20:
            self.right_score += 1
            self.reset_pong_ball()
        elif ball["x"] > self.WIDTH + 20:
            self.left_score += 1
            self.reset_pong_ball()

        if self.left_score >= 7 or self.right_score >= 7:
            self.game_over = True
            if self.left_score > self.right_score:
                self.end_title = "JOGADOR ESQUERDA VENCEU"
            else:
                self.end_title = "JOGADOR DIREITA VENCEU"
            self.end_subtitle = "Reiniciar, trocar modo ou voltar ao menu"

    def check_pong_paddle_collision(self, paddle_x, paddle_y, is_player):
        ball = self.pong_ball
        r = ball["r"]
        paddle_left = paddle_x
        paddle_right = paddle_x + self.paddle_w
        paddle_top = paddle_y - self.paddle_h / 2
        paddle_bottom = paddle_y + self.paddle_h / 2

        if not (paddle_left <= ball["x"] + r and ball["x"] - r <= paddle_right):
            return
        if not (paddle_top <= ball["y"] <= paddle_bottom):
            return
        if is_player and ball["dx"] >= 0:
            return
        if not is_player and ball["dx"] <= 0:
            return

        impact = (ball["y"] - paddle_y) / (self.paddle_h / 2)
        speed = min(10.5, math.hypot(ball["dx"], ball["dy"]) + 0.28)
        ball["dx"] = speed if is_player else -speed
        ball["dy"] = impact * 5.2
        ball["x"] = paddle_right + r if is_player else paddle_left - r

    def render_pong(self):
        self.canvas.delete("all")
        self.score_label.config(text=f"Esq {self.left_score}  |  Dir {self.right_score}")
        self.info_label.config(text="Esq: W/S  |  Dir: setas")

        for y in range(12, self.HEIGHT, 34):
            self.canvas.create_rectangle(self.WIDTH // 2 - 2, y, self.WIDTH // 2 + 2, y + 18, fill="#334155", outline="")

        self.canvas.create_rectangle(
            self.left_paddle_x,
            self.left_paddle_y - self.paddle_h / 2,
            self.left_paddle_x + self.paddle_w,
            self.left_paddle_y + self.paddle_h / 2,
            fill="#38BDF8",
            outline="",
        )
        self.canvas.create_rectangle(
            self.right_paddle_x,
            self.right_paddle_y - self.paddle_h / 2,
            self.right_paddle_x + self.paddle_w,
            self.right_paddle_y + self.paddle_h / 2,
            fill="#F97316",
            outline="",
        )

        b = self.pong_ball
        self.canvas.create_oval(b["x"] - b["r"], b["y"] - b["r"], b["x"] + b["r"], b["y"] + b["r"], fill="#F8FAFC", outline="")

    # Breakout
    def setup_breakout(self):
        self.breakout_score = 0
        self.breakout_lives = 3
        self.breakout_level = 1
        self.base_paddle_width = 116
        self.paddle_width = self.base_paddle_width
        self.paddle_height = 14
        self.paddle_x = self.WIDTH // 2
        self.breakout_gravity = 0
        self.effect_text = "Quebre blocos e pegue as esferas"
        self.effect_frames = 160
        self.breakout_bg = "#020617"
        self.breakout_balls = [self.make_breakout_ball()]
        self.pending_balls = []
        self.powerups = []
        self.active_effects = {}
        self.chaos_tick = 0
        self.build_bricks()

    def make_breakout_ball(self, x=None, y=None, dx=None, dy=None):
        angle = random.uniform(-0.75, 0.75)
        speed = 5.4 + self.breakout_level * 0.35
        return {
            "x": x if x is not None else self.WIDTH / 2,
            "y": y if y is not None else self.HEIGHT - 82,
            "dx": dx if dx is not None else speed * math.sin(angle),
            "dy": dy if dy is not None else -abs(speed * math.cos(angle)),
            "r": 8,
            "color": random.choice(["#F8FAFC", "#67E8F9", "#FDE68A", "#C4B5FD"]),
        }

    def build_bricks(self):
        self.bricks = []
        cols = 10
        rows = min(7, 4 + self.breakout_level)
        gap = 6
        brick_w = (self.WIDTH - 80 - (cols - 1) * gap) / cols
        brick_h = 24
        palette = ["#38BDF8", "#22C55E", "#F59E0B", "#EF4444", "#A855F7", "#14B8A6", "#F97316"]

        for row in range(rows):
            for col in range(cols):
                x1 = 40 + col * (brick_w + gap)
                y1 = 52 + row * (brick_h + gap)
                hp = 2 if self.breakout_level >= 3 and random.random() < 0.18 else 1
                self.bricks.append({
                    "x1": x1,
                    "y1": y1,
                    "x2": x1 + brick_w,
                    "y2": y1 + brick_h,
                    "hp": hp,
                    "color": palette[row % len(palette)],
                })

    def update_active_effects(self):
        expired = []
        for effect, data in self.active_effects.items():
            data["frames"] -= 1
            if data["frames"] <= 0:
                expired.append(effect)

        for effect in expired:
            self.active_effects.pop(effect, None)

        if "color" not in self.active_effects:
            self.breakout_bg = "#020617"

        if "gravity" in self.active_effects:
            self.breakout_gravity = self.active_effects["gravity"].get("gravity", 0.045)
        else:
            self.breakout_gravity = 0

        if "chaos" in self.active_effects:
            self.chaos_tick += 1
            if self.chaos_tick % 28 == 0:
                self.randomize_ball_angles()
        else:
            self.chaos_tick = 0

        self.recalculate_paddle_width()

    def recalculate_paddle_width(self):
        width = self.base_paddle_width
        if "wide" in self.active_effects:
            width += 46
        if "slim" in self.active_effects:
            width -= 34
        self.paddle_width = max(68, min(190, width))

    def ball_speed_multiplier(self):
        multiplier = 1.0
        if "turbo" in self.active_effects:
            multiplier *= 1.28
        if "slow" in self.active_effects:
            multiplier *= 0.76
        return multiplier

    def update_powerups(self):
        paddle_top = self.HEIGHT - 42
        paddle_left = self.paddle_x - self.paddle_width / 2
        paddle_right = self.paddle_x + self.paddle_width / 2
        remaining = []

        for powerup in self.powerups:
            powerup["y"] += powerup["dy"]
            caught = (
                paddle_left <= powerup["x"] <= paddle_right
                and paddle_top <= powerup["y"] + powerup["r"] <= paddle_top + self.paddle_height + 12
            )
            if caught:
                self.activate_breakout_effect(powerup["effect"])
            elif powerup["y"] - powerup["r"] <= self.HEIGHT:
                remaining.append(powerup)

        self.powerups = remaining

    def spawn_powerup(self, x, y):
        effect = random.choice(list(self.EFFECT_DEFINITIONS.keys()))
        info = self.EFFECT_DEFINITIONS[effect]
        self.powerups.append({
            "x": x,
            "y": y,
            "dy": random.uniform(1.15, 1.85),
            "r": 10,
            "effect": effect,
            "label": info["label"],
            "color": info["color"],
            "symbol": info["symbol"],
        })

    def update_breakout(self):
        self.update_active_effects()

        move = 0
        if "a" in self.keys_pressed or "left" in self.keys_pressed:
            move -= 10
        if "d" in self.keys_pressed or "right" in self.keys_pressed:
            move += 10

        self.paddle_x += move
        if move == 0:
            self.paddle_x += (self.mouse_x - self.paddle_x) * 0.22
        half = self.paddle_width / 2
        self.paddle_x = max(half + 8, min(self.WIDTH - half - 8, self.paddle_x))

        if self.effect_frames > 0:
            self.effect_frames -= 1

        self.pending_balls = []
        self.update_powerups()

        alive_balls = []
        for ball in list(self.breakout_balls):
            self.update_breakout_ball(ball, alive_balls)

        self.breakout_balls = alive_balls + self.pending_balls
        if not self.breakout_balls:
            self.breakout_lives -= 1
            if self.breakout_lives <= 0:
                self.game_over = True
                self.end_title = "FIM DE JOGO"
                self.end_subtitle = "Reiniciar, trocar modo ou voltar ao menu"
                return
            self.breakout_balls = [self.make_breakout_ball()]
            self.effect_text = "Bola nova"
            self.effect_frames = 120

        if not self.bricks:
            self.breakout_level += 1
            self.base_paddle_width = min(150, self.base_paddle_width + 10)
            self.recalculate_paddle_width()
            self.breakout_balls = [self.make_breakout_ball()]
            self.powerups.clear()
            self.build_bricks()
            self.effect_text = f"Nivel {self.breakout_level}"
            self.effect_frames = 150

    def update_breakout_ball(self, ball, alive_balls):
        ball["dy"] += self.breakout_gravity
        speed_multiplier = self.ball_speed_multiplier()
        ball["x"] += ball["dx"] * speed_multiplier
        ball["y"] += ball["dy"] * speed_multiplier

        if ball["x"] - ball["r"] <= 0 or ball["x"] + ball["r"] >= self.WIDTH:
            ball["dx"] *= -1
            ball["x"] = max(ball["r"], min(self.WIDTH - ball["r"], ball["x"]))

        if ball["y"] - ball["r"] <= 0:
            ball["dy"] = abs(ball["dy"])
            ball["y"] = ball["r"]

        paddle_top = self.HEIGHT - 42
        paddle_left = self.paddle_x - self.paddle_width / 2
        paddle_right = self.paddle_x + self.paddle_width / 2
        if (
            paddle_left <= ball["x"] <= paddle_right
            and paddle_top <= ball["y"] + ball["r"] <= paddle_top + 18
            and ball["dy"] > 0
        ):
            impact = (ball["x"] - self.paddle_x) / (self.paddle_width / 2)
            speed = min(12.5, max(5.2, math.hypot(ball["dx"], ball["dy"]) + 0.12))
            ball["dx"] = impact * speed
            ball["dy"] = -abs(speed * (1 - min(0.55, abs(impact) * 0.25)))
            ball["y"] = paddle_top - ball["r"]

        hit_brick = self.find_brick_hit(ball)
        if hit_brick is not None:
            hit_brick["hp"] -= 1
            ball["dy"] *= -1
            self.breakout_score += 10 * self.breakout_level
            if hit_brick["hp"] <= 0:
                brick_center_x = (hit_brick["x1"] + hit_brick["x2"]) / 2
                brick_center_y = (hit_brick["y1"] + hit_brick["y2"]) / 2
                self.bricks.remove(hit_brick)
                self.spawn_powerup(brick_center_x, brick_center_y)
            else:
                hit_brick["color"] = "#F8FAFC"

        if ball["y"] - ball["r"] > self.HEIGHT:
            if "safety" in self.active_effects:
                ball["y"] = self.HEIGHT - ball["r"]
                ball["dy"] = -abs(ball["dy"])
                alive_balls.append(ball)
            return

        alive_balls.append(ball)

    def find_brick_hit(self, ball):
        for brick in self.bricks:
            if (
                brick["x1"] <= ball["x"] + ball["r"]
                and ball["x"] - ball["r"] <= brick["x2"]
                and brick["y1"] <= ball["y"] + ball["r"]
                and ball["y"] - ball["r"] <= brick["y2"]
            ):
                return brick
        return None

    def activate_breakout_effect(self, effect):
        info = self.EFFECT_DEFINITIONS[effect]
        duration = info["duration"]

        if duration > 0:
            self.active_effects[effect] = {
                "label": info["label"],
                "frames": duration,
                "color": info["color"],
            }

        if effect == "multiball" and len(self.breakout_balls) + len(self.pending_balls) < 5:
            source_ball = random.choice(self.breakout_balls) if self.breakout_balls else self.make_breakout_ball()
            self.pending_balls.append(self.make_breakout_ball(
                source_ball["x"],
                source_ball["y"],
                -source_ball["dx"] * random.uniform(0.8, 1.1),
                source_ball["dy"] * random.uniform(0.85, 1.15),
            ))
            self.effect_text = "Multibola"
        elif effect == "wide":
            self.recalculate_paddle_width()
            self.effect_text = "Raquete expandida"
        elif effect == "slim":
            self.recalculate_paddle_width()
            self.effect_text = "Raquete compacta"
        elif effect == "turbo":
            self.effect_text = "Turbo"
        elif effect == "slow":
            self.effect_text = "Camera lenta"
        elif effect == "gravity":
            self.active_effects[effect]["gravity"] = random.choice([-0.045, 0.045])
            self.effect_text = "Gravidade maluca"
        elif effect == "chaos":
            self.randomize_ball_angles()
            self.effect_text = "Angulos caoticos"
        elif effect == "safety":
            self.effect_text = "Parede de seguranca"
        elif effect == "color":
            self.breakout_bg = random.choice(["#06141F", "#120A1F", "#111827", "#1A120B"])
            for brick in self.bricks:
                brick["color"] = random.choice(["#38BDF8", "#22C55E", "#F97316", "#E879F9", "#FDE047"])
            self.effect_text = "Chuva de cores"
        elif effect == "bonus":
            self.breakout_score += 50 * self.breakout_level
            self.effect_text = "Bonus de pontos"

        self.effect_frames = 170

    def scale_balls(self, factor):
        for ball in self.breakout_balls:
            ball["dx"] *= factor
            ball["dy"] *= factor

    def randomize_ball_angles(self):
        for ball in self.breakout_balls:
            speed = max(5.2, min(11, math.hypot(ball["dx"], ball["dy"])))
            angle = random.uniform(-1.05, 1.05)
            ball["dx"] = speed * math.sin(angle)
            ball["dy"] = -abs(speed * math.cos(angle))

    def render_breakout(self):
        self.canvas.delete("all")
        self.canvas.configure(bg=self.breakout_bg)
        self.score_label.config(text=f"Pontos {self.breakout_score}  |  Vidas {self.breakout_lives}")
        self.info_label.config(text="A/D, setas ou mouse")

        for brick in self.bricks:
            self.canvas.create_rectangle(
                brick["x1"],
                brick["y1"],
                brick["x2"],
                brick["y2"],
                fill=brick["color"],
                outline="#0F172A",
                width=2,
            )
            if brick["hp"] > 1:
                self.canvas.create_text(
                    (brick["x1"] + brick["x2"]) / 2,
                    (brick["y1"] + brick["y2"]) / 2,
                    text="2",
                    fill="#0F172A",
                    font=("Segoe UI", 10, "bold"),
                )

        paddle_top = self.HEIGHT - 42
        self.canvas.create_rectangle(
            self.paddle_x - self.paddle_width / 2,
            paddle_top,
            self.paddle_x + self.paddle_width / 2,
            paddle_top + self.paddle_height,
            fill="#38BDF8",
            outline="",
        )

        if "safety" in self.active_effects:
            self.canvas.create_rectangle(0, self.HEIGHT - 6, self.WIDTH, self.HEIGHT, fill="#22C55E", outline="")

        self.draw_powerups()

        for ball in self.breakout_balls:
            self.canvas.create_oval(
                ball["x"] - ball["r"],
                ball["y"] - ball["r"],
                ball["x"] + ball["r"],
                ball["y"] + ball["r"],
                fill=ball["color"],
                outline="",
            )

        self.canvas.create_text(
            14,
            18,
            text=f"Nivel {self.breakout_level}",
            fill="#CBD5E1",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        if self.effect_frames > 0:
            self.canvas.create_text(
                self.WIDTH - 14,
                18,
                text=self.effect_text,
                fill="#FDE68A",
                font=("Segoe UI", 11, "bold"),
                anchor="e",
            )
        self.draw_active_effect_timers()

    def draw_powerups(self):
        for powerup in self.powerups:
            x = powerup["x"]
            y = powerup["y"]
            r = powerup["r"]
            self.canvas.create_oval(x - r - 3, y - r - 3, x + r + 3, y + r + 3, fill="#0F172A", outline=powerup["color"], width=2)
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=powerup["color"], outline="")
            self.canvas.create_text(
                x,
                y,
                text=powerup["symbol"],
                fill="#020617",
                font=("Segoe UI", 9, "bold"),
            )

    def draw_active_effect_timers(self):
        if not self.active_effects:
            return

        effects = sorted(self.active_effects.values(), key=lambda data: data["frames"])
        x = self.WIDTH - 168
        y = 42
        self.canvas.create_text(
            x,
            y - 12,
            text="Efeitos",
            fill="#CBD5E1",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )

        for data in effects:
            seconds = max(1, math.ceil(data["frames"] / 60))
            self.canvas.create_rectangle(x, y, x + 154, y + 24, fill="#111827", outline=data["color"], width=1)
            self.canvas.create_text(
                x + 8,
                y + 12,
                text=f"{data['label']} {seconds}s",
                fill="#F8FAFC",
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            )
            y += 29


if __name__ == "__main__":
    root = tk.Tk()
    app = PingPong(root)
    root.mainloop()

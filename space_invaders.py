import random
import tkinter as tk

class SpaceInvaders:
    CANVAS_WIDTH = 600
    CANVAS_HEIGHT = 700
    FPS = 60
    DELAY = 1000 // FPS

    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Space Invaders")
        self.root.configure(bg="#020617") # Fundo escuro slate-950
        self.root.resizable(False, False)

        self.loop_id = None
        self.canvas = None
        
        # Colors (Neon/Retro)
        self.color_bg = "#020617"
        self.color_panel = "#0F172A"
        self.color_text = "#F8FAFC"
        self.color_muted = "#94A3B8"
        self.color_ship = "#38BDF8"  # Cyan neon
        self.color_player_bullet = "#22C55E" # Green neon
        self.color_alien_bullet = "#EF4444" # Red neon
        self.color_shield = "#10B981" # Emerald neon
        
        self.alien_colors = ["#A855F7", "#EC4899", "#EAB308", "#06B6D4"] # Roxo, Rosa, Amarelo, Ciano

        # Key states
        self.keys = {'Left': False, 'Right': False, 'a': False, 'd': False, 'A': False, 'D': False}

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
        self.center_window(500, 500)

        frame = tk.Frame(self.root, bg=self.color_panel)
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="SPACE INVADERS",
            font=("Segoe UI", 36, "bold"),
            bg=self.color_panel,
            fg="#A855F7",
        ).pack(pady=(60, 8))

        tk.Label(
            frame,
            text="Proteja a Terra da invasão alienígena!",
            font=("Segoe UI", 12),
            bg=self.color_panel,
            fg=self.color_muted,
        ).pack(pady=(0, 30))

        self.make_button(frame, "Iniciar Jogo", "#8B5CF6", self.start_game).pack(pady=10)
        self.make_button(frame, "Voltar ao Menu", "#475569", self.voltar_menu).pack(pady=(15, 0))

        controls = tk.Label(
            frame,
            text="Controles:\nSetas ou A/D para mover\nEspaço para Atirar",
            font=("Segoe UI", 11),
            bg=self.color_panel,
            fg="#94A3B8",
            justify="center"
        )
        controls.pack(side=tk.BOTTOM, pady=30)

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
            pady=10,
            cursor="hand2",
            command=command,
        )

    def start_game(self):
        self.clear_window()
        self.center_window(self.CANVAS_WIDTH, self.CANVAS_HEIGHT + 60)
        self.started = True
        self.game_over = False
        self.victory = False
        
        self.score = 0
        self.high_score = getattr(self, 'high_score', 0)
        self.lives = 3
        
        # Player State
        self.ship_width = 40
        self.ship_height = 20
        self.ship_x = self.CANVAS_WIDTH // 2 - self.ship_width // 2
        self.ship_y = self.CANVAS_HEIGHT - 50
        self.ship_speed = 6.0
        self.shoot_cooldown = 0
        
        # Bullets
        self.bullets = []       # Player bullets
        self.alien_bullets = [] # Alien bullets
        self.bullet_speed = 10
        self.alien_bullet_speed = 5
        
        # Aliens State
        self.aliens = []
        self.alien_width = 30
        self.alien_height = 20
        self.alien_rows = 5
        self.alien_cols = 10
        self.alien_speed_x = 2.0
        self.alien_speed_y = 20
        self.alien_direction = 1 # 1 for right, -1 for left
        self.alien_shoot_timer = 60
        self.init_aliens()

        # Shields State
        self.shields = []
        self.init_shields()

        self.build_game_ui()
        
        # Binds
        self.root.bind("<KeyPress>", self.keydown)
        self.root.bind("<KeyRelease>", self.keyup)
        
        self.root.focus_set()
        
        self.game_loop()

    def init_aliens(self):
        start_x = 50
        start_y = 60
        gap_x = 45
        gap_y = 40
        for r in range(self.alien_rows):
            color = self.alien_colors[r % len(self.alien_colors)]
            for c in range(self.alien_cols):
                self.aliens.append({
                    'x': start_x + c * gap_x,
                    'y': start_y + r * gap_y,
                    'color': color,
                    'row': r,
                    'col': c
                })

    def init_shields(self):
        num_shields = 4
        shield_y = self.CANVAS_HEIGHT - 130
        spacing = self.CANVAS_WIDTH // (num_shields + 1)
        
        # A shield is a collection of small 5x5 blocks
        block_size = 6
        shield_shape = [
            "  XXXXXX  ",
            " XXXXXXXX ",
            "XXXXXXXXXX",
            "XXXXXXXXXX",
            "XXX    XXX",
            "XX      XX"
        ]
        
        for i in range(num_shields):
            base_x = spacing * (i + 1) - (len(shield_shape[0]) * block_size) // 2
            for row_idx, row_str in enumerate(shield_shape):
                for col_idx, char in enumerate(row_str):
                    if char == 'X':
                        self.shields.append({
                            'x': base_x + col_idx * block_size,
                            'y': shield_y + row_idx * block_size,
                            'size': block_size,
                            'hp': 1
                        })

    def build_game_ui(self):
        top_frame = tk.Frame(self.root, bg=self.color_panel, height=60)
        top_frame.pack(fill=tk.X)

        tk.Label(
            top_frame,
            text="Space Invaders",
            font=("Segoe UI", 14, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(20, 8), pady=10)

        self.score_label = tk.Label(
            top_frame,
            text=f"Pontos: 0  |  Vidas: 3  |  Recorde: {self.high_score}",
            font=("Segoe UI", 11, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            anchor="w",
        )
        self.score_label.pack(side=tk.LEFT, padx=15)

        btn_style = {
            "font": ("Segoe UI", 9, "bold"),
            "fg": "#FFFFFF",
            "relief": "flat",
            "bd": 0,
            "cursor": "hand2",
            "padx": 8,
            "pady": 4,
        }
        tk.Button(top_frame, text="Menu", bg="#475569", command=self.voltar_menu, **btn_style).pack(side=tk.RIGHT, padx=(4, 20), pady=10)

        self.canvas = tk.Canvas(
            self.root,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg=self.color_bg,
            highlightthickness=0,
        )
        self.canvas.pack()

    def voltar_menu(self):
        self.cancel_loop()
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def keydown(self, event):
        if self.game_over or self.victory:
            if event.keysym.lower() == 'space':
                self.start_game()
            return

        if event.keysym in self.keys:
            self.keys[event.keysym] = True
            
        if event.keysym.lower() == 'space':
            self.shoot()

    def keyup(self, event):
        if event.keysym in self.keys:
            self.keys[event.keysym] = False

    def shoot(self):
        if self.shoot_cooldown <= 0:
            self.bullets.append({
                'x': self.ship_x + self.ship_width // 2 - 2,
                'y': self.ship_y,
                'width': 4,
                'height': 15
            })
            self.shoot_cooldown = 20 # frames

    def game_loop(self):
        self.loop_id = None
        if self.started and not self.game_over and not self.victory:
            self.update_physics()
            self.check_collisions()
            self.render()
            self.loop_id = self.root.after(self.DELAY, self.game_loop)

    def update_physics(self):
        # Update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # Move Ship
        if self.keys['Left'] or self.keys['a'] or self.keys['A']:
            self.ship_x -= self.ship_speed
        if self.keys['Right'] or self.keys['d'] or self.keys['D']:
            self.ship_x += self.ship_speed
            
        # Clamp ship
        if self.ship_x < 0:
            self.ship_x = 0
        if self.ship_x > self.CANVAS_WIDTH - self.ship_width:
            self.ship_x = self.CANVAS_WIDTH - self.ship_width

        # Move Bullets
        for b in self.bullets:
            b['y'] -= self.bullet_speed
        self.bullets = [b for b in self.bullets if b['y'] > 0]

        for b in self.alien_bullets:
            b['y'] += self.alien_bullet_speed
        self.alien_bullets = [b for b in self.alien_bullets if b['y'] < self.CANVAS_HEIGHT]

        # Move Aliens
        hit_edge = False
        for a in self.aliens:
            a['x'] += self.alien_speed_x * self.alien_direction
            if a['x'] <= 10 or a['x'] >= self.CANVAS_WIDTH - self.alien_width - 10:
                hit_edge = True

        if hit_edge:
            self.alien_direction *= -1
            # Speed up slightly as they drop
            self.alien_speed_x *= 1.05 
            for a in self.aliens:
                a['x'] += self.alien_speed_x * self.alien_direction # Adjust position so they don't get stuck
                a['y'] += self.alien_speed_y
                if a['y'] + self.alien_height >= self.ship_y:
                    self.die(True) # Aliens reached player

        # Alien shooting
        self.alien_shoot_timer -= 1
        if self.alien_shoot_timer <= 0 and len(self.aliens) > 0:
            # Pick a random alien from the lowest in each column
            cols = {}
            for a in self.aliens:
                if a['col'] not in cols or a['y'] > cols[a['col']]['y']:
                    cols[a['col']] = a
            
            shooter = random.choice(list(cols.values()))
            self.alien_bullets.append({
                'x': shooter['x'] + self.alien_width // 2 - 2,
                'y': shooter['y'] + self.alien_height,
                'width': 4,
                'height': 15
            })
            # Timer gets faster as fewer aliens remain
            self.alien_shoot_timer = max(20, int(60 * (len(self.aliens) / (self.alien_rows * self.alien_cols))))

    def check_collisions(self):
        # 1. Player bullets vs Aliens
        for b in self.bullets[:]:
            b_rect = (b['x'], b['y'], b['x'] + b['width'], b['y'] + b['height'])
            hit = False
            for a in self.aliens[:]:
                a_rect = (a['x'], a['y'], a['x'] + self.alien_width, a['y'] + self.alien_height)
                if self.rect_intersect(b_rect, a_rect):
                    self.aliens.remove(a)
                    if b in self.bullets:
                        self.bullets.remove(b)
                    hit = True
                    self.update_score(10)
                    break
            
            if hit: continue
            
            # Player bullet vs Shields
            for s in self.shields[:]:
                s_rect = (s['x'], s['y'], s['x'] + s['size'], s['y'] + s['size'])
                if self.rect_intersect(b_rect, s_rect):
                    self.shields.remove(s)
                    if b in self.bullets:
                        self.bullets.remove(b)
                    break

        # 2. Alien bullets vs Player
        player_rect = (self.ship_x, self.ship_y, self.ship_x + self.ship_width, self.ship_y + self.ship_height)
        for b in self.alien_bullets[:]:
            b_rect = (b['x'], b['y'], b['x'] + b['width'], b['y'] + b['height'])
            if self.rect_intersect(b_rect, player_rect):
                self.alien_bullets.remove(b)
                self.die(False)
                break
                
            # Alien bullet vs Shields
            hit = False
            for s in self.shields[:]:
                s_rect = (s['x'], s['y'], s['x'] + s['size'], s['y'] + s['size'])
                if self.rect_intersect(b_rect, s_rect):
                    self.shields.remove(s)
                    if b in self.alien_bullets:
                        self.alien_bullets.remove(b)
                    break

        # Check win condition
        if len(self.aliens) == 0:
            self.win()

    def rect_intersect(self, r1, r2):
        # r = (x1, y1, x2, y2)
        return not (r2[0] > r1[2] or r2[2] < r1[0] or r2[1] > r1[3] or r2[3] < r1[1])

    def update_score(self, points):
        self.score += points
        if self.score > self.high_score:
            self.high_score = self.score
        self.update_ui()

    def update_ui(self):
        self.score_label.config(text=f"Pontos: {self.score}  |  Vidas: {self.lives}  |  Recorde: {self.high_score}")

    def die(self, instant_game_over):
        if instant_game_over:
            self.lives = 0
        else:
            self.lives -= 1
            
        self.update_ui()
        
        if self.lives <= 0:
            self.game_over = True
            self.cancel_loop()
            self.render()
            self.draw_overlay("GAME OVER", f"Pontuação: {self.score}\nPressione ESPAÇO para reiniciar", "#EF4444")
        else:
            # Reset player position and clear bullets
            self.ship_x = self.CANVAS_WIDTH // 2 - self.ship_width // 2
            self.bullets.clear()
            self.alien_bullets.clear()
            # Pause briefly? For now just continue

    def win(self):
        self.victory = True
        self.cancel_loop()
        self.render()
        self.draw_overlay("VITÓRIA!", f"Você salvou a Terra!\nPontuação Final: {self.score}\nESPAÇO para jogar novamente", "#10B981")

    def render(self):
        if not self.canvas:
            return

        self.canvas.delete("all")

        # Draw stars background
        for _ in range(5):
            sx = random.randint(0, self.CANVAS_WIDTH)
            sy = random.randint(0, self.CANVAS_HEIGHT)
            self.canvas.create_rectangle(sx, sy, sx+2, sy+2, fill="#334155", outline="")

        # Draw Shields
        for s in self.shields:
            self.canvas.create_rectangle(
                s['x'], s['y'], s['x'] + s['size'], s['y'] + s['size'],
                fill=self.color_shield, outline=""
            )

        # Draw Aliens
        for a in self.aliens:
            self.draw_alien(a['x'], a['y'], self.alien_width, self.alien_height, a['color'])

        # Draw Bullets
        for b in self.bullets:
            self.canvas.create_rectangle(b['x'], b['y'], b['x'] + b['width'], b['y'] + b['height'], fill=self.color_player_bullet, outline="")
        for b in self.alien_bullets:
            self.canvas.create_rectangle(b['x'], b['y'], b['x'] + b['width'], b['y'] + b['height'], fill=self.color_alien_bullet, outline="")

        # Draw Player Ship
        if self.lives > 0:
            px = self.ship_x
            py = self.ship_y
            pw = self.ship_width
            ph = self.ship_height
            
            # Base
            self.canvas.create_rectangle(px, py + ph//2, px + pw, py + ph, fill=self.color_ship, outline="")
            # Cannon
            self.canvas.create_rectangle(px + pw//2 - 4, py, px + pw//2 + 4, py + ph//2, fill=self.color_ship, outline="")
            # Wings detail
            self.canvas.create_polygon(px, py + ph//2, px, py + ph, px - 8, py + ph, fill="#0284C7", outline="")
            self.canvas.create_polygon(px + pw, py + ph//2, px + pw, py + ph, px + pw + 8, py + ph, fill="#0284C7", outline="")

    def draw_alien(self, x, y, w, h, color):
        # A simple stylized invader
        # Body
        self.canvas.create_rectangle(x + 4, y, x + w - 4, y + h - 6, fill=color, outline="")
        # Antennae
        self.canvas.create_rectangle(x + 6, y - 4, x + 10, y, fill=color, outline="")
        self.canvas.create_rectangle(x + w - 10, y - 4, x + w - 6, y, fill=color, outline="")
        # Legs
        self.canvas.create_rectangle(x, y + h - 6, x + 6, y + h, fill=color, outline="")
        self.canvas.create_rectangle(x + w - 6, y + h - 6, x + w, y + h, fill=color, outline="")
        # Eyes
        self.canvas.create_rectangle(x + 8, y + 4, x + 12, y + 8, fill=self.color_bg, outline="")
        self.canvas.create_rectangle(x + w - 12, y + 4, x + w - 8, y + 8, fill=self.color_bg, outline="")

    def draw_overlay(self, title, subtitle, color):
        self.canvas.create_rectangle(
            0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT,
            fill="#020617", stipple="gray50", outline=""
        )
        self.canvas.create_text(
            self.CANVAS_WIDTH // 2, self.CANVAS_HEIGHT // 2 - 40,
            text=title, fill=color, font=("Segoe UI", 42, "bold")
        )
        self.canvas.create_text(
            self.CANVAS_WIDTH // 2, self.CANVAS_HEIGHT // 2 + 20,
            text=subtitle, fill="#F8FAFC", font=("Segoe UI", 14), justify="center"
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = SpaceInvaders(root)
    root.mainloop()

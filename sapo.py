import random
import tkinter as tk


class Lane:
    def __init__(self, lane_type, speed, direction, entities, y_index):
        self.type = lane_type  # 'GRASS', 'ROAD', 'RIVER'
        self.speed = speed
        self.direction = direction  # 1 (right) or -1 (left)
        self.entities = entities  # list of dicts: {'x': float, 'w': int, 'color': str}
        self.y_index = y_index

class Sapo:
    COLS = 20
    ROWS = 25
    CELL = 24
    CANVAS_WIDTH = COLS * CELL
    CANVAS_HEIGHT = ROWS * CELL
    FPS = 45
    DELAY = 1000 // FPS

    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Sapo")
        self.root.configure(bg="#0F172A")
        self.root.resizable(False, False)

        self.loop_id = None
        self.canvas = None
        
        # Colors
        self.color_bg = "#0F172A"
        self.color_panel = "#111827"
        self.color_text = "#F8FAFC"
        self.color_muted = "#94A3B8"
        
        self.color_frog = "#22C55E"
        self.color_frog_shield = "#38BDF8"
        
        self.color_grass = "#14532D"
        self.color_road = "#1E293B"
        self.color_river = "#0369A1"
        self.color_log = "#78350F"
        
        self.color_car_types = ["#EF4444", "#F59E0B", "#8B5CF6", "#EC4899", "#F97316"]

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
            text="Sapo Arcade",
            font=("Segoe UI", 30, "bold"),
            bg=self.color_bg,
            fg=self.color_text,
        ).pack(pady=(46, 8))

        tk.Label(
            frame,
            text="Atravesse ruas e rios infinitamente.",
            font=("Segoe UI", 12),
            bg=self.color_bg,
            fg=self.color_muted,
        ).pack(pady=(0, 28))

        self.make_button(frame, "Iniciar Jogo", "#22C55E", self.start_game).pack(pady=8)
        self.make_button(frame, "Voltar ao Menu", "#64748B", self.voltar_menu).pack(pady=(18, 0))

        controls = tk.Label(
            frame,
            text="W/A/S/D ou Setas  |  Espaço pausa  |  R reinicia",
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
        self.center_window(self.CANVAS_WIDTH + 40, self.CANVAS_HEIGHT + 140)
        self.started = True
        self.is_paused = False
        self.game_over = False
        
        self.score = 0
        self.high_score = 0
        self.lives = 3
        
        # State
        self.frog_x = (self.COLS // 2) * self.CELL
        self.frog_y = self.ROWS - 2  # Lane index
        self.frog_moving = False
        
        self.shield_active = False
        self.slow_active_frames = 0
        
        self.lanes = []
        self.power_ups = []  # {'x': float, 'y': int, 'type': 'SHIELD'|'SLOW'|'LIFE'}
        
        # Init base map
        self.generate_initial_map()

        self.build_game_ui()
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.focus_set()
        self.render()
        self.game_loop()

    def generate_initial_map(self):
        self.lanes = []
        for i in range(self.ROWS):
            # Bottom 3 lanes are always grass
            if i >= self.ROWS - 3:
                self.lanes.append(Lane('GRASS', 0, 1, [], i))
            else:
                self.lanes.append(self.create_random_lane(i))

    def create_random_lane(self, y_index):
        # Prevent more than 3 of the same type in a row
        types_history = [l.type for l in self.lanes[-3:]] if len(self.lanes) >= 3 else []
        
        choices = ['GRASS', 'ROAD', 'ROAD', 'RIVER', 'RIVER']
        
        if types_history.count('RIVER') >= 3:
            choices = ['GRASS', 'ROAD']
        elif types_history.count('ROAD') >= 3:
            choices = ['GRASS', 'RIVER']
            
        ltype = random.choice(choices)
        direction = random.choice([1, -1])
        base_speed = random.uniform(1.0, 3.5) + (self.score * 0.02)
        
        entities = []
        if ltype == 'ROAD':
            num_cars = random.randint(1, 3)
            spacing = self.CANVAS_WIDTH / num_cars
            offset = random.uniform(0, spacing)
            for i in range(num_cars):
                w = random.choice([1.5, 2.0, 2.5]) * self.CELL
                entities.append({
                    'x': offset + (i * spacing), 
                    'w': w,
                    'color': random.choice(self.color_car_types)
                })
        elif ltype == 'RIVER':
            num_logs = random.randint(2, 4)
            spacing = self.CANVAS_WIDTH / num_logs
            offset = random.uniform(0, spacing)
            for i in range(num_logs):
                w = random.choice([2.5, 3.0, 4.0]) * self.CELL
                entities.append({
                    'x': offset + (i * spacing), 
                    'w': w,
                    'color': self.color_log
                })
        elif ltype == 'GRASS':
            # 10% chance to spawn a powerup on new grass
            if random.random() < 0.10:
                self.spawn_power_up(y_index)
                
        return Lane(ltype, base_speed, direction, entities, y_index)

    def spawn_power_up(self, y_index):
        x = random.randint(0, self.COLS - 1) * self.CELL
        ptype = random.choices(['SHIELD', 'SLOW', 'LIFE'], weights=[40, 40, 20])[0]
        self.power_ups.append({'x': x, 'y': y_index, 'type': ptype})

    def build_game_ui(self):
        top_frame = tk.Frame(self.root, bg=self.color_panel)
        top_frame.pack(fill=tk.X)

        tk.Label(
            top_frame,
            text="Sapo",
            font=("Segoe UI", 17, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=8,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(20, 8), pady=12)

        self.score_label = tk.Label(
            top_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=40,
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

        self.canvas = tk.Canvas(
            self.root,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg=self.color_bg,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(20, 0))
        
        info = tk.Label(
            self.root,
            text="Chegue o mais longe que puder! Desvie de carros e use troncos nos rios.",
            font=("Segoe UI", 9),
            bg=self.color_bg,
            fg=self.color_muted,
        )
        info.pack(pady=8)

    def voltar_menu(self):
        self.cancel_loop()
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def on_key_press(self, event):
        if self.game_over:
            if event.keysym.lower() == 'r':
                self.start_game()
            return

        key = event.keysym.lower()
        if key == "space":
            self.toggle_pause()
            return
            
        if self.is_paused:
            return

        if key in ["w", "up"]:
            self.move_frog(0, -1)
        elif key in ["s", "down"]:
            self.move_frog(0, 1)
        elif key in ["a", "left"]:
            self.move_frog(-1, 0)
        elif key in ["d", "right"]:
            self.move_frog(1, 0)

    def move_frog(self, dx, dy):
        new_x = self.frog_x + dx * self.CELL
        
        if 0 <= new_x <= self.CANVAS_WIDTH - self.CELL:
            self.frog_x = new_x
            
        if dy != 0:
            new_y = self.frog_y + dy
            # Block moving below screen
            if new_y >= self.ROWS:
                return
                
            self.frog_y = new_y
            if dy < 0:
                # Scored!
                self.score += 1
                if self.score > self.high_score:
                    self.high_score = self.score
                
                # Scroll logic if moving past a certain point
                if self.frog_y < self.ROWS // 2:
                    self.scroll_map_down()

    def scroll_map_down(self):
        self.frog_y += 1
        
        # Move all lanes down
        for lane in self.lanes:
            lane.y_index += 1
            
        # Move power ups down
        for p in self.power_ups:
            p['y'] += 1
            
        # Remove off-screen lanes and powerups
        self.lanes = [l for l in self.lanes if l.y_index < self.ROWS]
        self.power_ups = [p for p in self.power_ups if p['y'] < self.ROWS]
        
        # Insert new lane at top (index 0)
        new_lane = self.create_random_lane(0)
        self.lanes.insert(0, new_lane)

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
            self.update_entities()
            self.check_collisions()
            self.render()
            self.loop_id = self.root.after(self.DELAY, self.game_loop)

    def update_entities(self):
        if self.slow_active_frames > 0:
            self.slow_active_frames -= 1
            
        speed_mult = 0.4 if self.slow_active_frames > 0 else 1.0

        for lane in self.lanes:
            move_amt = lane.speed * lane.direction * speed_mult
            
            for ent in lane.entities:
                ent['x'] += move_amt
                # Wrap around logic
                if lane.direction == 1 and ent['x'] > self.CANVAS_WIDTH:
                    ent['x'] = -ent['w']
                elif lane.direction == -1 and ent['x'] < -ent['w']:
                    ent['x'] = self.CANVAS_WIDTH
                    
        # Move frog if on a log
        current_lane = self.get_lane_at(self.frog_y)
        if current_lane and current_lane.type == 'RIVER':
            move_amt = current_lane.speed * current_lane.direction * speed_mult
            self.frog_x += move_amt
            
            # Check if floating out of bounds
            if self.frog_x < -self.CELL or self.frog_x > self.CANVAS_WIDTH:
                self.die("Você foi levado pela correnteza!")

    def get_lane_at(self, y_index):
        for lane in self.lanes:
            if lane.y_index == y_index:
                return lane
        return None

    def check_collisions(self):
        if self.game_over:
            return

        current_lane = self.get_lane_at(self.frog_y)
        if not current_lane:
            return
            
        frog_rect = [self.frog_x + 4, self.frog_y * self.CELL + 4, 
                     self.frog_x + self.CELL - 4, (self.frog_y + 1) * self.CELL - 4]

        # Power up collisions
        to_remove_pw = []
        for p in self.power_ups:
            if p['y'] == self.frog_y:
                px = p['x']
                if self.frog_x < px + self.CELL and self.frog_x + self.CELL > px:
                    self.apply_power_up(p['type'])
                    to_remove_pw.append(p)
        for p in to_remove_pw:
            if p in self.power_ups:
                self.power_ups.remove(p)

        if current_lane.type == 'ROAD':
            for ent in current_lane.entities:
                ent_rect = [ent['x'], current_lane.y_index * self.CELL, 
                            ent['x'] + ent['w'], (current_lane.y_index + 1) * self.CELL]
                if self.intersect(frog_rect, ent_rect):
                    self.die("Você foi atropelado!")
                    return
                    
        elif current_lane.type == 'RIVER':
            on_log = False
            for ent in current_lane.entities:
                ent_rect = [ent['x'], current_lane.y_index * self.CELL, 
                            ent['x'] + ent['w'], (current_lane.y_index + 1) * self.CELL]
                # Relaxed intersection for logs to be forgiving
                if frog_rect[0] < ent_rect[2] and frog_rect[2] > ent_rect[0]:
                    on_log = True
                    break
                    
            if not on_log:
                self.die("Você se afogou!")
                return

    def intersect(self, r1, r2):
        return not (r1[2] < r2[0] or r1[0] > r2[2] or r1[3] < r2[1] or r1[1] > r2[3])

    def apply_power_up(self, ptype):
        if ptype == 'SHIELD':
            self.shield_active = True
        elif ptype == 'SLOW':
            self.slow_active_frames = self.FPS * 5  # 5 seconds
        elif ptype == 'LIFE':
            self.lives += 1
            
        self.score += 5

    def die(self, reason):
        if self.shield_active:
            self.shield_active = False
            self.frog_y = min(self.ROWS - 1, self.frog_y + 1) # Jump back safely
            # Make the lane below safe temporarily
            safe_lane = self.get_lane_at(self.frog_y)
            if safe_lane:
                safe_lane.type = 'GRASS'
                safe_lane.entities = []
            return

        self.lives -= 1
        if self.lives <= 0:
            self.finish_game("FIM DE JOGO", reason)
        else:
            # Respawn logic
            self.frog_y = self.ROWS - 2
            self.frog_x = (self.COLS // 2) * self.CELL
            # Ensure bottom lanes are safe
            for i in range(self.ROWS - 3, self.ROWS):
                l = self.get_lane_at(i)
                if l:
                    l.type = 'GRASS'
                    l.entities = []

    def finish_game(self, title, subtitle):
        self.game_over = True
        self.cancel_loop()
        self.render()
        self.draw_overlay(title, f"{subtitle}  |  R para reiniciar")

    def render(self):
        if not self.canvas:
            return

        self.canvas.delete("all")
        
        status_txt = f"Pts: {self.score}  |  Vidas: {'❤'*self.lives}  |  Recorde: {self.high_score}"
        if self.shield_active:
            status_txt += "  |  [ESCUDO]"
        if self.slow_active_frames > 0:
            status_txt += f"  |  [LENTO {self.slow_active_frames//self.FPS}s]"
            
        self.score_label.config(text=status_txt)

        self.draw_map()
        self.draw_power_ups()
        self.draw_frog()

        if self.is_paused:
            self.draw_overlay("PAUSADO", "Espaço para continuar")

    def draw_map(self):
        for lane in self.lanes:
            y1 = lane.y_index * self.CELL
            y2 = y1 + self.CELL
            
            bg_color = self.color_bg
            if lane.type == 'GRASS': bg_color = self.color_grass
            elif lane.type == 'ROAD': bg_color = self.color_road
            elif lane.type == 'RIVER': bg_color = self.color_river
            
            self.canvas.create_rectangle(0, y1, self.CANVAS_WIDTH, y2, fill=bg_color, outline="")
            
            # Draw lane decorators (street lines, river waves)
            if lane.type == 'ROAD':
                for x in range(0, self.CANVAS_WIDTH, 40):
                    self.canvas.create_line(x, y1, x+20, y1, fill="#475569", width=2)
            elif lane.type == 'RIVER':
                for x in range(0, self.CANVAS_WIDTH, 60):
                    offset = (self.slow_active_frames % 20) if self.slow_active_frames > 0 else 0
                    self.canvas.create_line(x + offset, y1+12, x+15 + offset, y1+12, fill="#0284C7", width=2)

            # Draw entities
            for ent in lane.entities:
                if lane.type == 'ROAD':
                    # Draw Car
                    self.canvas.create_rectangle(ent['x'], y1 + 4, ent['x'] + ent['w'], y2 - 4, 
                                                fill=ent['color'], outline="#111827", width=2)
                    # Window
                    window_x = ent['x'] + 4 if lane.direction == -1 else ent['x'] + ent['w'] - 12
                    self.canvas.create_rectangle(window_x, y1 + 6, window_x + 8, y2 - 6, fill="#94A3B8", outline="")
                elif lane.type == 'RIVER':
                    # Draw Log
                    self.canvas.create_rectangle(ent['x'], y1 + 2, ent['x'] + ent['w'], y2 - 2, 
                                                fill=ent['color'], outline="#451A03", width=2)
                    self.canvas.create_line(ent['x'] + 10, y1 + 6, ent['x'] + ent['w'] - 10, y1 + 6, fill="#92400E")

    def draw_power_ups(self):
        for p in self.power_ups:
            x = p['x'] + self.CELL//2
            y = p['y'] * self.CELL + self.CELL//2
            
            if p['type'] == 'SHIELD':
                self.canvas.create_oval(x-8, y-8, x+8, y+8, fill="#38BDF8", outline="#E0F2FE", width=2)
                self.canvas.create_text(x, y, text="S", fill="#0C4A6E", font=("Arial", 10, "bold"))
            elif p['type'] == 'SLOW':
                self.canvas.create_oval(x-8, y-8, x+8, y+8, fill="#FDE047", outline="#FEF08A", width=2)
                self.canvas.create_text(x, y, text="T", fill="#713F12", font=("Arial", 10, "bold"))
            elif p['type'] == 'LIFE':
                self.canvas.create_oval(x-8, y-8, x+8, y+8, fill="#EF4444", outline="#FECACA", width=2)
                self.canvas.create_text(x, y, text="❤", fill="#FFFFFF", font=("Arial", 10))

    def draw_frog(self):
        pad = 3
        x1 = self.frog_x + pad
        y1 = self.frog_y * self.CELL + pad
        x2 = self.frog_x + self.CELL - pad
        y2 = (self.frog_y + 1) * self.CELL - pad
        
        color = self.color_frog_shield if self.shield_active else self.color_frog
        
        # Legs
        self.canvas.create_oval(x1-2, y1+4, x1+6, y2-4, fill="#166534", outline="")
        self.canvas.create_oval(x2-6, y1+4, x2+2, y2-4, fill="#166534", outline="")
        
        # Body
        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="#14532D", width=2)
        
        # Eyes
        self.canvas.create_oval(x1+2, y1+2, x1+6, y1+6, fill="#FFFFFF", outline="")
        self.canvas.create_oval(x2-6, y1+2, x2-2, y1+6, fill="#FFFFFF", outline="")
        self.canvas.create_oval(x1+3, y1+3, x1+5, y1+5, fill="#000000", outline="")
        self.canvas.create_oval(x2-5, y1+3, x2-3, y1+5, fill="#000000", outline="")

    def draw_overlay(self, title, subtitle):
        self.canvas.create_rectangle(
            0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT,
            fill="#020617", stipple="gray50", outline=""
        )
        self.canvas.create_text(
            self.CANVAS_WIDTH // 2, self.CANVAS_HEIGHT // 2 - 28,
            text=title, fill="#F8FAFC", font=("Segoe UI", 30, "bold")
        )
        self.canvas.create_text(
            self.CANVAS_WIDTH // 2, self.CANVAS_HEIGHT // 2 + 20,
            text=subtitle, fill="#CBD5E1", font=("Segoe UI", 12)
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = Sapo(root)
    root.mainloop()

import random
import tkinter as tk

class Passarinho:
    CANVAS_WIDTH = 400
    CANVAS_HEIGHT = 600
    FPS = 60
    DELAY = 1000 // FPS

    # Physics Constants
    GRAVITY = 0.5
    JUMP_STRENGTH = -8.5
    PIPE_SPEED = 4.0
    PIPE_WIDTH = 60
    PIPE_GAP = 160

    def __init__(self, root, on_menu_return=None):
        self.root = root
        self.on_menu_return = on_menu_return
        self.root.title("Passarinho")
        self.root.configure(bg="#0F172A")
        self.root.resizable(False, False)

        self.loop_id = None
        self.canvas = None
        
        # Colors (Tailwind inspired)
        self.color_bg = "#38BDF8"  # Sky blue
        self.color_panel = "#111827"
        self.color_text = "#F8FAFC"
        self.color_muted = "#94A3B8"
        self.color_bird = "#FDE047"  # Yellow bird
        self.color_bird_outline = "#CA8A04"
        self.color_pipe = "#22C55E"  # Green pipe
        self.color_pipe_outline = "#166534"
        self.color_ground = "#D97706"  # Dirt/Ground

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
        self.center_window(430, 430)

        # Usando a cor escura pro painel inicial
        frame = tk.Frame(self.root, bg="#0F172A")
        frame.pack(expand=True, fill=tk.BOTH)

        tk.Label(
            frame,
            text="Passarinho",
            font=("Segoe UI", 34, "bold"),
            bg="#0F172A",
            fg=self.color_text,
        ).pack(pady=(46, 8))

        tk.Label(
            frame,
            text="Pule e desvie dos canos!",
            font=("Segoe UI", 12),
            bg="#0F172A",
            fg=self.color_muted,
        ).pack(pady=(0, 28))

        self.make_button(frame, "Iniciar Jogo", "#F59E0B", self.start_game).pack(pady=8)
        self.make_button(frame, "Voltar ao Menu", "#64748B", self.voltar_menu).pack(pady=(18, 0))

        controls = tk.Label(
            frame,
            text="Barra de Espaço ou Clique do Mouse para pular",
            font=("Segoe UI", 10),
            bg="#0F172A",
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
        self.center_window(self.CANVAS_WIDTH + 40, self.CANVAS_HEIGHT + 100)
        self.started = True
        self.game_over = False
        
        self.score = 0
        self.high_score = getattr(self, 'high_score', 0)
        
        # Bird State
        self.bird_x = 100
        self.bird_y = self.CANVAS_HEIGHT // 2
        self.bird_vy = 0.0
        self.bird_radius = 14
        
        # Pipes State
        self.pipes = []
        self.frames_since_last_pipe = 0
        self.spawn_pipe_frames = 85  # frames between pipes

        self.build_game_ui()
        
        # Binds for jumping
        self.root.bind("<space>", self.jump)
        self.root.bind("<Button-1>", self.jump)
        
        self.root.focus_set()
        
        # Initial jump
        self.jump(None)
        self.game_loop()

    def build_game_ui(self):
        top_frame = tk.Frame(self.root, bg=self.color_panel)
        top_frame.pack(fill=tk.X)

        tk.Label(
            top_frame,
            text="Passarinho",
            font=("Segoe UI", 15, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
            width=10,
            anchor="w",
        ).pack(side=tk.LEFT, padx=(20, 8), pady=12)

        self.score_label = tk.Label(
            top_frame,
            text=f"Pontos: 0  |  Recorde: {self.high_score}",
            font=("Segoe UI", 11, "bold"),
            bg=self.color_panel,
            fg=self.color_text,
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

        self.canvas = tk.Canvas(
            self.root,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg=self.color_bg,
            highlightthickness=0,
        )
        self.canvas.pack(pady=(15, 0))

    def voltar_menu(self):
        self.cancel_loop()
        if self.on_menu_return:
            self.root.destroy()
            self.on_menu_return()
        else:
            self.root.quit()

    def jump(self, event):
        if self.game_over:
            if event and hasattr(event, 'keysym') and event.keysym.lower() == 'space':
                self.start_game()
            elif event and hasattr(event, 'num') and event.num == 1:
                self.start_game()
            return
            
        if self.started:
            self.bird_vy = self.JUMP_STRENGTH

    def spawn_pipe(self):
        # min pipe height
        min_h = 50
        max_h = self.CANVAS_HEIGHT - self.PIPE_GAP - min_h
        
        top_h = random.randint(min_h, max_h)
        
        self.pipes.append({
            'x': self.CANVAS_WIDTH,
            'top_h': top_h,
            'bottom_y': top_h + self.PIPE_GAP,
            'passed': False
        })

    def game_loop(self):
        self.loop_id = None
        if self.started and not self.game_over:
            self.update_physics()
            self.check_collisions()
            self.render()
            self.loop_id = self.root.after(self.DELAY, self.game_loop)

    def update_physics(self):
        # Update bird
        self.bird_vy += self.GRAVITY
        self.bird_y += self.bird_vy
        
        # Spawn pipes
        self.frames_since_last_pipe += 1
        if self.frames_since_last_pipe >= self.spawn_pipe_frames:
            self.spawn_pipe()
            self.frames_since_last_pipe = 0
            
        # Update pipes
        for pipe in self.pipes:
            pipe['x'] -= self.PIPE_SPEED
            
            # Check score
            if not pipe['passed'] and pipe['x'] + self.PIPE_WIDTH < self.bird_x:
                pipe['passed'] = True
                self.score += 1
                if self.score > self.high_score:
                    self.high_score = self.score
                self.score_label.config(text=f"Pontos: {self.score}  |  Recorde: {self.high_score}")
                
        # Remove off-screen pipes
        self.pipes = [p for p in self.pipes if p['x'] + self.PIPE_WIDTH > 0]

    def check_collisions(self):
        if self.game_over:
            return

        # Check floor/ceiling
        if self.bird_y + self.bird_radius >= self.CANVAS_HEIGHT or self.bird_y - self.bird_radius <= 0:
            self.die()
            return

        # Check pipes
        bird_left = self.bird_x - self.bird_radius
        bird_right = self.bird_x + self.bird_radius
        bird_top = self.bird_y - self.bird_radius
        bird_bottom = self.bird_y + self.bird_radius

        for pipe in self.pipes:
            pipe_left = pipe['x']
            pipe_right = pipe['x'] + self.PIPE_WIDTH
            
            # Se o pássaro está na zona horizontal do cano
            if bird_right > pipe_left and bird_left < pipe_right:
                # Bateu no cano de cima
                if bird_top < pipe['top_h']:
                    self.die()
                    return
                # Bateu no cano de baixo
                if bird_bottom > pipe['bottom_y']:
                    self.die()
                    return

    def die(self):
        self.game_over = True
        self.cancel_loop()
        self.render()
        self.draw_overlay("FIM DE JOGO", f"Você fez {self.score} pontos! Espaço para reiniciar")

    def render(self):
        if not self.canvas:
            return

        self.canvas.delete("all")

        # Background decorations (clouds)
        self.canvas.create_oval(50, 100, 120, 140, fill="#7DD3FC", outline="")
        self.canvas.create_oval(80, 80, 150, 130, fill="#7DD3FC", outline="")
        self.canvas.create_oval(250, 200, 330, 250, fill="#7DD3FC", outline="")
        self.canvas.create_oval(290, 180, 360, 240, fill="#7DD3FC", outline="")

        self.draw_pipes()
        self.draw_bird()

    def draw_pipes(self):
        for pipe in self.pipes:
            px = pipe['x']
            pw = self.PIPE_WIDTH
            
            # Top pipe
            self.canvas.create_rectangle(
                px, 0, px + pw, pipe['top_h'],
                fill=self.color_pipe, outline=self.color_pipe_outline, width=3
            )
            # Top pipe cap
            self.canvas.create_rectangle(
                px - 4, pipe['top_h'] - 20, px + pw + 4, pipe['top_h'],
                fill=self.color_pipe, outline=self.color_pipe_outline, width=3
            )
            
            # Bottom pipe
            self.canvas.create_rectangle(
                px, pipe['bottom_y'], px + pw, self.CANVAS_HEIGHT,
                fill=self.color_pipe, outline=self.color_pipe_outline, width=3
            )
            # Bottom pipe cap
            self.canvas.create_rectangle(
                px - 4, pipe['bottom_y'], px + pw + 4, pipe['bottom_y'] + 20,
                fill=self.color_pipe, outline=self.color_pipe_outline, width=3
            )

    def draw_bird(self):
        bx = self.bird_x
        by = self.bird_y
        r = self.bird_radius
        
        # Rotation effect based on velocity
        angle_tilt = max(-30, min(self.bird_vy * 4, 90))
        
        # We'll just draw a static simple bird since tkinter doesn't do rotation easily
        # Body
        self.canvas.create_oval(
            bx - r - 4, by - r, bx + r + 4, by + r,
            fill=self.color_bird, outline=self.color_bird_outline, width=2
        )
        
        # Wing
        wing_y_offset = -2 if self.bird_vy < 0 else 2
        self.canvas.create_oval(
            bx - r, by + wing_y_offset, bx - 2, by + r - 2 + wing_y_offset,
            fill="#FEF08A", outline=self.color_bird_outline, width=2
        )
        
        # Eye
        self.canvas.create_oval(bx + 4, by - 6, bx + 10, by, fill="white", outline="black")
        self.canvas.create_oval(bx + 7, by - 4, bx + 9, by - 2, fill="black", outline="")
        
        # Beak
        self.canvas.create_polygon(
            bx + r + 2, by,
            bx + r + 12, by + 4,
            bx + r + 2, by + 8,
            fill="#F97316", outline="black", width=1
        )

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
    app = Passarinho(root)
    root.mainloop()

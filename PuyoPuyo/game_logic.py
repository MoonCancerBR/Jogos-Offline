import pygame

if __package__:
    from .constants import *
    from .piece import PuyoPair, PuyoRandomizer
    from .board import Board
else:
    from constants import *
    from piece import PuyoPair, PuyoRandomizer
    from board import Board

class GameLogic:
    def __init__(self, mode=GAME_MODE_HARDCORE):
        self.mode = mode
        self.board = Board()
        self.randomizer = PuyoRandomizer()
        self.next_queue = [self.randomizer.next_piece() for _ in range(5)]
        self.current_piece = self.randomizer.next_piece()
        self.hold_piece = None
        self.can_hold = True
        
        self.score = 0
        self.level = 1
        self.puyos_cleared_total = 0
        self.combo = 0
        
        self.game_over = False
        self.zone_active = False
        self.zone_energy = 0
        self.zone_timer = 0
        
        self.fall_time = 0
        self.lock_timer = 0
        
        # Animação de lock (cascata)
        self.locking = False
        self.cascade_timer = 0
        self.CASCADE_DELAY = 300 # ms entre etapas de cascata
        
    def get_fall_speed(self):
        if self.mode == GAME_MODE_CASUAL: return 1000
        if self.mode == GAME_MODE_SANDBOX: return 500
        return max(50, 1000 - (self.level - 1) * 80)

    def is_sandbox(self):
        return self.mode == GAME_MODE_SANDBOX

    def spawn_piece(self):
        self.current_piece = self.next_queue.pop(0)
        self.next_queue.append(self.randomizer.next_piece())
        self.can_hold = True
        self.lock_timer = 0
        
        if not self.board.is_valid_move(self.current_piece):
            self.game_over = True

    def hold(self):
        if not self.can_hold or self.locking:
            return
        
        if self.hold_piece is None:
            self.hold_piece = PuyoPair(self.current_piece.color_main, self.current_piece.color_sec)
            self.spawn_piece()
        else:
            temp = self.hold_piece
            self.hold_piece = PuyoPair(self.current_piece.color_main, self.current_piece.color_sec)
            self.current_piece = temp
            self.current_piece.x = 2
            self.current_piece.y = 1
            self.current_piece.rotation = 0
            
        self.can_hold = False

    def move(self, dx, dy):
        if self.locking: return False
        if self.board.is_valid_move(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            if dy == 0:
                self.lock_timer = 0 # reset lock
            return True
        return False

    def rotate(self, clockwise=True):
        if self.locking: return False
        
        old_rot = self.current_piece.rotation
        new_rot = self.current_piece.get_rotated_state(clockwise)
        
        # Tentar rodar na posição atual
        if self.board.is_valid_move(self.current_piece, 0, 0, new_rot):
            self.current_piece.rotation = new_rot
            self.lock_timer = 0
            return True
            
        # Wall kick simples (tentar empurrar o main puyo)
        kicks = [(-1, 0), (1, 0), (0, -1)]
        for dx, dy in kicks:
            if self.board.is_valid_move(self.current_piece, dx, dy, new_rot):
                self.current_piece.x += dx
                self.current_piece.y += dy
                self.current_piece.rotation = new_rot
                self.lock_timer = 0
                return True
                
        return False

    def hard_drop(self):
        if self.locking: return
        drop_dist = 0
        while self.board.is_valid_move(self.current_piece, 0, 1):
            self.current_piece.y += 1
            drop_dist += 1
        self.score += drop_dist * 2
        self.start_lock()

    def start_lock(self):
        self.board.lock_piece(self.current_piece)
        self.locking = True
        self.combo = 0
        self.cascade_timer = 0
        # A primeira etapa é separar os puyos (gravidade)
        self.board.apply_gravity()

    def process_cascade(self):
        """Processa as etapas de match e gravidade periodicamente."""
        matches = self.board.clear_matches()
        if matches > 0:
            self.combo += 1
            self.update_score(matches)
            # Após clear, precisamos aplicar gravidade
            self.board.apply_gravity()
        else:
            # Se não teve match, tenta gravidade de novo caso algo tenha ficado no ar
            if not self.board.apply_gravity():
                # Fim da cascata
                self.locking = False
                self.spawn_piece()

    def update_score(self, puyos_cleared):
        base_points = puyos_cleared * 10
        combo_mult = max(1, self.combo * 2)
        points = base_points * combo_mult * self.level
        
        self.score += points
        self.puyos_cleared_total += puyos_cleared
        self.level = (self.puyos_cleared_total // 20) + 1
        
        self.zone_energy = min(100, self.zone_energy + puyos_cleared * 2)

    def toggle_zone(self):
        if self.zone_energy >= 100 and not self.zone_active:
            self.zone_active = True
            self.zone_timer = ZONE_DURATION
        elif self.zone_active:
            self.end_zone()

    def end_zone(self):
        self.zone_active = False
        self.zone_energy = 0
        self.score += self.puyos_cleared_total * 10 # Bônus

    def get_ghost_y(self):
        ghost_y = self.current_piece.y
        while self.board.is_valid_move(self.current_piece, 0, ghost_y - self.current_piece.y + 1):
            ghost_y += 1
        return ghost_y

    def update(self, dt):
        if self.game_over:
            return

        if self.zone_active:
            self.zone_timer -= dt
            if self.zone_timer <= 0:
                self.end_zone()
            # Zona paralisa a queda automática do Puyo
            return

        if self.locking:
            self.cascade_timer += dt
            if self.cascade_timer >= self.CASCADE_DELAY:
                self.cascade_timer = 0
                self.process_cascade()
            return

        self.fall_time += dt
        if self.fall_time > self.get_fall_speed():
            if not self.move(0, 1):
                self.lock_timer += self.fall_time
                if self.lock_timer >= LOCK_DELAY:
                    self.start_lock()
            else:
                self.lock_timer = 0
            self.fall_time = 0

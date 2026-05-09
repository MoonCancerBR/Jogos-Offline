import pygame

if __package__:
    from .constants import *
    from .piece import Piece, BagRandomizer
    from .board import Board
else:
    from constants import *
    from piece import Piece, BagRandomizer
    from board import Board

class GameLogic:
    def __init__(self, mode=GAME_MODE_HARDCORE):
        self.mode = mode
        self.board = Board()
        self.randomizer = BagRandomizer()
        self.next_queue = [self.randomizer.next_piece() for _ in range(5)]
        self.current_piece = self.randomizer.next_piece()
        self.hold_piece = None
        self.can_hold = True
        
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.combo = -1
        self.back_to_back = False
        
        self.game_over = False
        self.zone_active = False
        self.zone_energy = 0
        self.zone_lines = 0
        self.zone_timer = 0
        self.is_t_spin = False
        self.is_t_spin_mini = False
        
        self.fall_time = 0
        self.lock_timer = 0
        self.lock_resets = 0
        
        # DAS (Delayed Auto Shift)
        self.das_timer = 0
        self.das_direction = 0 # -1 left, 1 right
        
    def get_fall_speed(self):
        if self.mode == GAME_MODE_CASUAL:
            return 1000
        if self.mode == GAME_MODE_SANDBOX:
            speed_step = self.score // 500
            return max(50, 1000 - speed_step * 60)

        return max(50, 1000 - (self.level - 1) * 100)

    def is_sandbox(self):
        return self.mode == GAME_MODE_SANDBOX

    def get_current_piece_cells(self):
        return {
            (self.current_piece.x + px, self.current_piece.y + py)
            for px, py in self.current_piece.current_shape
        }

    def apply_sandbox_gravity(self, include_current_piece=True, clear_lines=False, score_lines=True):
        if not self.is_sandbox():
            return 0

        blocked_cells = self.get_current_piece_cells() if include_current_piece else None
        total_lines = 0

        while True:
            self.board.collapse_columns(blocked_cells)
            if not clear_lines:
                return total_lines

            lines = self.board.clear_lines()
            if lines == 0:
                return total_lines

            total_lines += lines
            if score_lines:
                self.update_score(lines)

    def spawn_piece(self):
        self.current_piece = self.next_queue.pop(0)
        self.next_queue.append(self.randomizer.next_piece())
        self.can_hold = True
        self.lock_resets = 0
        self.lock_timer = 0
        
        if not self.board.is_valid_move(self.current_piece):
            self.game_over = True

    def hold(self):
        if not self.can_hold:
            return
        
        if self.hold_piece is None:
            self.hold_piece = Piece(self.current_piece.name)
            self.spawn_piece()
        else:
            temp_name = self.hold_piece.name
            self.hold_piece = Piece(self.current_piece.name)
            self.current_piece = Piece(temp_name)
            
        self.can_hold = False

    def move(self, dx, dy):
        if self.board.is_valid_move(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            if dy == 0:
                self.reset_lock_delay()
            self.apply_sandbox_gravity()
            return True
        return False

    def rotate(self, clockwise=True):
        if self.current_piece.name == 'O': return False
        old_rotation = self.current_piece.rotation
        new_rotation = self.current_piece.get_rotated_state(clockwise)
        
        kick_type = 'I' if self.current_piece.name == 'I' else 'default'
        kicks = WALL_KICK_DATA[kick_type].get((old_rotation, new_rotation), [(0, 0)])
        
        for i, (dx, dy) in enumerate(kicks):
            if self.board.is_valid_move(self.current_piece, dx, dy, new_rotation):
                self.current_piece.x += dx
                self.current_piece.y += dy
                self.current_piece.rotation = new_rotation
                self.reset_lock_delay()
                
                # T-Spin Detection
                if self.current_piece.name == 'T':
                    self.check_t_spin(i == 4) # i == 4 is the last kick (usually the most extreme)
                else:
                    self.is_t_spin = False
                    self.is_t_spin_mini = False
                self.apply_sandbox_gravity()
                return True
        return False

    def check_t_spin(self, last_kick):
        # T-Spin 3-corner rule
        corners = [(0, 0), (2, 0), (0, 2), (2, 2)]
        occupied = 0
        for cx, cy in corners:
            nx, ny = self.current_piece.x + cx, self.current_piece.y + cy
            if nx < 0 or nx >= BOARD_WIDTH or ny >= BOARD_HEIGHT or (ny >= 0 and self.board.grid[ny][nx] is not None):
                occupied += 1
        
        if occupied >= 3:
            if last_kick: self.is_t_spin_mini = True
            else: self.is_t_spin = True
        else:
            self.is_t_spin = False
            self.is_t_spin_mini = False

    def reset_lock_delay(self):
        if not self.board.is_valid_move(self.current_piece, 0, 1):
            if self.lock_resets < MAX_LOCK_RESETS:
                self.lock_timer = 0
                self.lock_resets += 1

    def hard_drop(self):
        drop_dist = 0
        while self.board.is_valid_move(self.current_piece, 0, 1):
            self.current_piece.y += 1
            drop_dist += 1
        self.score += drop_dist * 2
        self.lock_and_next()

    def count_complete_lines(self):
        return sum(
            1
            for y in range(BOARD_HEIGHT)
            if all(self.board.grid[y][x] is not None for x in range(BOARD_WIDTH))
        )

    def lock_and_next(self):
        self.board.lock_piece(self.current_piece)
        if self.is_sandbox():
            if self.zone_active:
                self.apply_sandbox_gravity(include_current_piece=False, clear_lines=False)
                self.zone_lines += self.count_complete_lines()
                self.spawn_piece()
            else:
                lines = self.apply_sandbox_gravity(include_current_piece=False, clear_lines=True)
                if lines == 0:
                    self.update_score(0)
                self.spawn_piece()
            return

        if self.zone_active:
            # No Zone, as linhas completas não desaparecem imediatamente, elas descem
            # Para simplificar, vamos contar as linhas e mantê-las no grid até o fim do Zone
            lines = 0
            for y in range(BOARD_HEIGHT):
                if all(self.board.grid[y][x] is not None for x in range(BOARD_WIDTH)):
                    lines += 1
            self.zone_lines += lines
            # No Zone real do Tetris Effect, as linhas completas descem para o fundo.
            # Aqui vamos apenas spawnar a próxima peça.
            self.spawn_piece()
        else:
            lines = self.board.clear_lines()
            self.update_score(lines)
            self.spawn_piece()

    def update_score(self, lines):
        if lines == 0:
            if not self.is_t_spin and not self.is_t_spin_mini:
                self.combo = -1
            return
        
        self.combo += 1
        points = 0
        
        if self.is_t_spin:
            t_spin_points = {1: 800, 2: 1200, 3: 1600}
            points = t_spin_points.get(lines, 400) # 400 for T-spin with 0 lines
        elif self.is_t_spin_mini:
            points = 100 * lines if lines > 0 else 100
        else:
            base_points = {1: 100, 2: 300, 3: 500, 4: 800}
            points = base_points.get(lines, 0)

        points *= self.level
        
        if lines == 4 or self.is_t_spin:
            if self.back_to_back:
                points *= 1.5
            self.back_to_back = True
        else:
            self.back_to_back = False
            
        self.score += int(points) + (self.combo * 50 * self.level)
        self.lines_cleared_total += lines
        self.level = (self.lines_cleared_total // 10) + 1
        
        # Zone Energy
        self.zone_energy = min(100, self.zone_energy + lines * 10)

    def toggle_zone(self):
        if self.zone_energy >= 100 and not self.zone_active:
            self.zone_active = True
            self.zone_timer = ZONE_DURATION
            self.zone_lines = 0
        elif self.zone_active:
            self.end_zone()

    def end_zone(self):
        self.zone_active = False
        self.zone_energy = 0
        # Pontuação massiva por linhas no Zone
        self.score += self.zone_lines * 1000 * self.level
        # Limpar todas as linhas completas acumuladas
        self.board.clear_lines()
        self.apply_sandbox_gravity(include_current_piece=True, clear_lines=True)
        self.zone_lines = 0

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
            # No Zone, a gravidade é suspensa (ou muito lenta)
            # O jogador deve mover a peça manualmente para baixo
            return

        self.fall_time += dt
        if self.fall_time > self.get_fall_speed():
            if not self.move(0, 1):
                self.lock_timer += self.fall_time
                if self.lock_timer >= LOCK_DELAY:
                    self.lock_and_next()
            else:
                self.lock_timer = 0
            self.fall_time = 0

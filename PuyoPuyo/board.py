if __package__:
    from .constants import BOARD_WIDTH, BOARD_HEIGHT
else:
    from constants import BOARD_WIDTH, BOARD_HEIGHT

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

    def is_valid_move(self, piece, offset_x=0, offset_y=0, rotation=None):
        mx = piece.x + offset_x
        my = piece.y + offset_y
        sx, sy = piece.get_sec_pos(rotation)
        sx += offset_x
        sy += offset_y
        
        # Check bounds
        if mx < 0 or mx >= BOARD_WIDTH or my >= BOARD_HEIGHT: return False
        if sx < 0 or sx >= BOARD_WIDTH or sy >= BOARD_HEIGHT: return False
        
        # Check collisions
        if my >= 0 and self.grid[my][mx] is not None: return False
        if sy >= 0 and self.grid[sy][sx] is not None: return False
        
        return True

    def lock_piece(self, piece):
        if piece.y >= 0 and piece.y < BOARD_HEIGHT:
            self.grid[piece.y][piece.x] = piece.color_main
            
        sx, sy = piece.get_sec_pos()
        if sy >= 0 and sy < BOARD_HEIGHT:
            self.grid[sy][sx] = piece.color_sec

    def apply_gravity(self):
        """Faz os puyos caírem se houver espaço vazio embaixo. Retorna True se algo caiu."""
        moved = False
        for x in range(BOARD_WIDTH):
            # Analisa de baixo para cima
            empty_y = BOARD_HEIGHT - 1
            for y in range(BOARD_HEIGHT - 1, -1, -1):
                if self.grid[y][x] is not None:
                    if y != empty_y:
                        self.grid[empty_y][x] = self.grid[y][x]
                        self.grid[y][x] = None
                        moved = True
                    empty_y -= 1
        return moved

    def clear_matches(self):
        """Encontra grupos de >= 4 puyos da mesma cor e os remove. Retorna a quantidade removida."""
        visited = set()
        to_remove = set()
        
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                color = self.grid[y][x]
                if color is not None and (x, y) not in visited:
                    group = []
                    queue = [(x, y)]
                    visited.add((x, y))
                    
                    while queue:
                        cx, cy = queue.pop(0)
                        group.append((cx, cy))
                        
                        # Check neighbors
                        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                            nx, ny = cx + dx, cy + dy
                            if 0 <= nx < BOARD_WIDTH and 0 <= ny < BOARD_HEIGHT:
                                if (nx, ny) not in visited and self.grid[ny][nx] == color:
                                    visited.add((nx, ny))
                                    queue.append((nx, ny))
                                    
                    if len(group) >= 4:
                        to_remove.update(group)
                        
        for x, y in to_remove:
            self.grid[y][x] = None
            
        return len(to_remove)

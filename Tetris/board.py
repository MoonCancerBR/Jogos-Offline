if __package__:
    from .constants import BOARD_WIDTH, BOARD_HEIGHT, BLACK
else:
    from constants import BOARD_WIDTH, BOARD_HEIGHT, BLACK

class Board:
    def __init__(self):
        self.grid = [[None for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]

    def is_valid_move(self, piece, offset_x=0, offset_y=0, rotation=None):
        shape = piece.shape_variants[rotation % len(piece.shape_variants)] if rotation is not None else piece.current_shape
        for px, py in shape:
            nx, ny = piece.x + px + offset_x, piece.y + py + offset_y
            if nx < 0 or nx >= BOARD_WIDTH or ny >= BOARD_HEIGHT:
                return False
            if ny >= 0 and self.grid[ny][nx] is not None:
                return False
        return True

    def lock_piece(self, piece):
        for px, py in piece.current_shape:
            nx, ny = piece.x + px, piece.y + py
            if 0 <= ny < BOARD_HEIGHT and 0 <= nx < BOARD_WIDTH:
                self.grid[ny][nx] = piece.color

    def clear_lines(self):
        lines_cleared = 0
        new_grid = [row for row in self.grid if any(cell is None for cell in row)]
        lines_cleared = BOARD_HEIGHT - len(new_grid)
        
        for _ in range(lines_cleared):
            new_grid.insert(0, [None for _ in range(BOARD_WIDTH)])
        
        self.grid = new_grid
        return lines_cleared

    def collapse_columns(self, blocked_cells=None):
        blocked_cells = {
            (x, y)
            for x, y in (blocked_cells or set())
            if 0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT
        }
        old_grid = [row[:] for row in self.grid]

        for x in range(BOARD_WIDTH):
            blocked_rows = sorted(y for cell_x, y in blocked_cells if cell_x == x)
            boundaries = [-1, *blocked_rows, BOARD_HEIGHT]

            for start, end in zip(boundaries, boundaries[1:]):
                top = start + 1
                bottom = end - 1
                if top > bottom:
                    continue

                cells = [
                    self.grid[y][x]
                    for y in range(bottom, top - 1, -1)
                    if self.grid[y][x] is not None
                ]

                for y in range(top, bottom + 1):
                    if (x, y) not in blocked_cells:
                        self.grid[y][x] = None

                for index, color in enumerate(cells):
                    self.grid[bottom - index][x] = color

        return self.grid != old_grid

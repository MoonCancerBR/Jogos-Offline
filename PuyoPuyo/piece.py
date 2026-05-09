import random

if __package__:
    from .constants import COLORS
else:
    from constants import COLORS

class PuyoPair:
    def __init__(self, color1=None, color2=None):
        color_keys = list(COLORS.keys())
        self.color_main = color1 if color1 else COLORS[random.choice(color_keys)]
        self.color_sec = color2 if color2 else COLORS[random.choice(color_keys)]
        
        self.rotation = 0 # 0: Cima, 1: Direita, 2: Baixo, 3: Esquerda
        self.x = 2  # Posição central (grid width 6 -> índice 2 e 3)
        self.y = 1  # O Puyo principal começa na linha 1
        
    def get_sec_pos(self, rot=None):
        if rot is None:
            rot = self.rotation
            
        if rot == 0:
            return (self.x, self.y - 1)
        elif rot == 1:
            return (self.x + 1, self.y)
        elif rot == 2:
            return (self.x, self.y + 1)
        elif rot == 3:
            return (self.x - 1, self.y)

    def get_rotated_state(self, clockwise=True):
        if clockwise:
            return (self.rotation + 1) % 4
        else:
            return (self.rotation - 1) % 4

    def rotate(self, clockwise=True):
        self.rotation = self.get_rotated_state(clockwise)

class PuyoRandomizer:
    def __init__(self):
        self.queue = []
        self.fill_queue()

    def fill_queue(self):
        while len(self.queue) < 5:
            self.queue.append(PuyoPair())

    def next_piece(self):
        p = self.queue.pop(0)
        self.fill_queue()
        return p

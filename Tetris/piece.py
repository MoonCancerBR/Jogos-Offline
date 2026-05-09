import random

if __package__:
    from .constants import SHAPES, COLORS, WALL_KICK_DATA
else:
    from constants import SHAPES, COLORS, WALL_KICK_DATA

class Piece:
    def __init__(self, shape_name):
        self.name = shape_name
        self.shape_variants = SHAPES[shape_name]
        self.color = COLORS[shape_name]
        self.rotation = 0
        self.x = 3  # Posição inicial centralizada
        self.y = 0
        
    @property
    def current_shape(self):
        return self.shape_variants[self.rotation % len(self.shape_variants)]

    def get_rotated_state(self, clockwise=True):
        if clockwise:
            return (self.rotation + 1) % len(self.shape_variants)
        else:
            return (self.rotation - 1) % len(self.shape_variants)

    def rotate(self, clockwise=True):
        self.rotation = self.get_rotated_state(clockwise)

class BagRandomizer:
    def __init__(self):
        self.bag = []
        self.refill()

    def refill(self):
        self.bag = list(SHAPES.keys())
        random.shuffle(self.bag)

    def next_piece(self):
        if not self.bag:
            self.refill()
        return Piece(self.bag.pop())

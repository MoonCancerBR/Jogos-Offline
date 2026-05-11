import math
import random

from pygame.math import Vector2

if __package__:
    from .constants import CHUNK_SIZE, TERRAIN_TYPES, VIEW_PADDING, WORLD_TILE_SIZE
    from .entities import Destructible, RectBody
else:
    from constants import CHUNK_SIZE, TERRAIN_TYPES, VIEW_PADDING, WORLD_TILE_SIZE
    from entities import Destructible, RectBody


def stable_hash(x, y, salt=0):
    value = (x * 374761393 + y * 668265263 + salt * 362437) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    return (value ^ (value >> 16)) & 0xFFFFFFFF


def unit_hash(x, y, salt=0):
    return stable_hash(x, y, salt) / 0xFFFFFFFF


def circle_rect_overlap(cx, cy, radius, rect):
    nearest_x = max(rect.left, min(cx, rect.right))
    nearest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - nearest_x
    dy = cy - nearest_y
    return dx * dx + dy * dy <= radius * radius


class World:
    def __init__(self):
        self.chunks = {}

    def chunk_coords(self, x, y):
        return math.floor(x / CHUNK_SIZE), math.floor(y / CHUNK_SIZE)

    def ensure_chunk(self, cx, cy):
        key = (cx, cy)
        if key not in self.chunks:
            self.chunks[key] = self._generate_chunk(cx, cy)
        return self.chunks[key]

    def ensure_area(self, center, radius=2):
        cx, cy = self.chunk_coords(center.x, center.y)
        for oy in range(-radius, radius + 1):
            for ox in range(-radius, radius + 1):
                self.ensure_chunk(cx + ox, cy + oy)

    def _generate_chunk(self, cx, cy):
        rng = random.Random(stable_hash(cx, cy, 91))
        base_x = cx * CHUNK_SIZE
        base_y = cy * CHUNK_SIZE
        obstacles = []
        destructibles = []

        obstacle_count = 3 + rng.randint(0, 4)
        for index in range(obstacle_count):
            wide = rng.random() < 0.58
            width = rng.randint(96, 210) if wide else rng.randint(44, 86)
            height = rng.randint(42, 90) if wide else rng.randint(90, 190)
            rect = RectBody(
                base_x + rng.randint(44, CHUNK_SIZE - width - 44),
                base_y + rng.randint(44, CHUNK_SIZE - height - 44),
                width,
                height,
            )
            if rect.center.length() < 330:
                continue
            if any(rect.intersects(existing, padding=32) for existing in obstacles):
                continue
            obstacles.append(rect)

        destructible_count = 4 + rng.randint(0, 5)
        for index in range(destructible_count):
            size = rng.randint(28, 42)
            rect = RectBody(
                base_x + rng.randint(35, CHUNK_SIZE - size - 35),
                base_y + rng.randint(35, CHUNK_SIZE - size - 35),
                size,
                size,
            )
            if rect.center.length() < 250:
                continue
            if any(rect.intersects(obstacle, padding=20) for obstacle in obstacles):
                continue
            kind = "cache" if rng.random() < 0.22 else "crate"
            hp = 35 if kind == "cache" else 24
            destructibles.append(
                Destructible(
                    id=f"{cx}:{cy}:{index}",
                    rect=rect,
                    hp=hp,
                    max_hp=hp,
                    kind=kind,
                    chunk=(cx, cy),
                )
            )

        return {"obstacles": obstacles, "destructibles": destructibles}

    def terrain_at(self, x, y):
        tile_x = math.floor(x / WORLD_TILE_SIZE)
        tile_y = math.floor(y / WORLD_TILE_SIZE)
        region_x = math.floor(tile_x / 4)
        region_y = math.floor(tile_y / 4)
        base = unit_hash(region_x, region_y, 11)
        variation = unit_hash(tile_x, tile_y, 23)
        value = (base * 0.78) + (variation * 0.22)

        if value < 0.15:
            return "sand"
        if value < 0.27:
            return "mud"
        if value > 0.86:
            return "stone"
        return "grass"

    def speed_multiplier_at(self, x, y):
        return TERRAIN_TYPES[self.terrain_at(x, y)]["speed"]

    def iter_visible_terrain(self, camera_x, camera_y, width, height):
        start_x = math.floor((camera_x - VIEW_PADDING) / WORLD_TILE_SIZE)
        end_x = math.ceil((camera_x + width + VIEW_PADDING) / WORLD_TILE_SIZE)
        start_y = math.floor((camera_y - VIEW_PADDING) / WORLD_TILE_SIZE)
        end_y = math.ceil((camera_y + height + VIEW_PADDING) / WORLD_TILE_SIZE)

        for ty in range(start_y, end_y):
            for tx in range(start_x, end_x):
                kind = self.terrain_at(tx * WORLD_TILE_SIZE, ty * WORLD_TILE_SIZE)
                yield tx * WORLD_TILE_SIZE, ty * WORLD_TILE_SIZE, WORLD_TILE_SIZE, kind, unit_hash(tx, ty, 41)

    def _chunks_in_rect(self, left, top, right, bottom):
        start_cx = math.floor(left / CHUNK_SIZE)
        end_cx = math.floor(right / CHUNK_SIZE)
        start_cy = math.floor(top / CHUNK_SIZE)
        end_cy = math.floor(bottom / CHUNK_SIZE)
        for cy in range(start_cy, end_cy + 1):
            for cx in range(start_cx, end_cx + 1):
                yield self.ensure_chunk(cx, cy)

    def iter_visible_obstacles(self, camera_x, camera_y, width, height):
        left = camera_x - VIEW_PADDING
        top = camera_y - VIEW_PADDING
        right = camera_x + width + VIEW_PADDING
        bottom = camera_y + height + VIEW_PADDING
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for rect in chunk["obstacles"]:
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    yield rect

    def iter_visible_destructibles(self, camera_x, camera_y, width, height):
        left = camera_x - VIEW_PADDING
        top = camera_y - VIEW_PADDING
        right = camera_x + width + VIEW_PADDING
        bottom = camera_y + height + VIEW_PADDING
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for item in chunk["destructibles"]:
                rect = item.rect
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    yield item

    def nearby_solid_rects(self, x, y, radius, include_destructibles=True):
        left = x - radius - 96
        top = y - radius - 96
        right = x + radius + 96
        bottom = y + radius + 96
        rects = []
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            rects.extend(chunk["obstacles"])
            if include_destructibles:
                rects.extend(item.rect for item in chunk["destructibles"])
        return rects

    def nearby_destructibles(self, x, y, radius):
        left = x - radius
        top = y - radius
        right = x + radius
        bottom = y + radius
        items = []
        for chunk in self._chunks_in_rect(left, top, right, bottom):
            for item in chunk["destructibles"]:
                rect = item.rect
                if not (rect.right < left or rect.left > right or rect.bottom < top or rect.top > bottom):
                    items.append(item)
        return items

    def move_circle(self, pos, radius, delta, include_destructibles=True):
        new_pos = Vector2(pos)
        if delta.x:
            new_pos.x += delta.x
            for rect in self.nearby_solid_rects(new_pos.x, new_pos.y, radius, include_destructibles):
                if not circle_rect_overlap(new_pos.x, new_pos.y, radius, rect):
                    continue
                if delta.x > 0:
                    new_pos.x = rect.left - radius
                else:
                    new_pos.x = rect.right + radius

        if delta.y:
            new_pos.y += delta.y
            for rect in self.nearby_solid_rects(new_pos.x, new_pos.y, radius, include_destructibles):
                if not circle_rect_overlap(new_pos.x, new_pos.y, radius, rect):
                    continue
                if delta.y > 0:
                    new_pos.y = rect.top - radius
                else:
                    new_pos.y = rect.bottom + radius

        return new_pos

    def circle_hits_wall(self, pos, radius):
        return any(circle_rect_overlap(pos.x, pos.y, radius, rect) for rect in self.nearby_solid_rects(pos.x, pos.y, radius))

    def remove_destructible(self, item):
        chunk = self.ensure_chunk(*item.chunk)
        chunk["destructibles"] = [entry for entry in chunk["destructibles"] if entry.id != item.id]


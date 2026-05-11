from dataclasses import dataclass, field

from pygame.math import Vector2

if __package__:
    from .constants import (
        BUFF_DURATION,
        PLAYER_BASE_SPEED,
        PLAYER_MAX_HEALTH,
        PLAYER_RADIUS,
        PROJECTILE_DAMAGE,
        PROJECTILE_LIFE,
        PROJECTILE_RADIUS,
        SHIELD_DURATION,
        SPECIAL_MAX,
        SWORD_ARC,
        SWORD_DAMAGE,
        SWORD_DURATION,
        SWORD_RADIUS,
    )
else:
    from constants import (
        BUFF_DURATION,
        PLAYER_BASE_SPEED,
        PLAYER_MAX_HEALTH,
        PLAYER_RADIUS,
        PROJECTILE_DAMAGE,
        PROJECTILE_LIFE,
        PROJECTILE_RADIUS,
        SHIELD_DURATION,
        SPECIAL_MAX,
        SWORD_ARC,
        SWORD_DAMAGE,
        SWORD_DURATION,
        SWORD_RADIUS,
    )


@dataclass
class RectBody:
    x: float
    y: float
    w: float
    h: float

    @property
    def left(self):
        return self.x

    @property
    def right(self):
        return self.x + self.w

    @property
    def top(self):
        return self.y

    @property
    def bottom(self):
        return self.y + self.h

    @property
    def center(self):
        return Vector2(self.x + self.w * 0.5, self.y + self.h * 0.5)

    def intersects(self, other, padding=0):
        return not (
            self.right + padding < other.left
            or self.left - padding > other.right
            or self.bottom + padding < other.top
            or self.top - padding > other.bottom
        )


@dataclass
class Player:
    pos: Vector2 = field(default_factory=lambda: Vector2(0, 0))
    radius: float = PLAYER_RADIUS
    max_health: float = PLAYER_MAX_HEALTH
    health: float = PLAYER_MAX_HEALTH
    base_speed: float = PLAYER_BASE_SPEED
    mode: str = "projectile"
    level: int = 1
    xp: float = 0
    xp_to_next: float = 55
    coins: int = 0
    kills: int = 0
    score: int = 0
    special: float = 0
    shoot_timer: float = 0
    sword_timer: float = 0
    dash_timer: float = 0
    dash_cooldown: float = 0
    invulnerable_timer: float = 0
    shield_timer: float = 0
    last_move_dir: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    dash_dir: Vector2 = field(default_factory=lambda: Vector2(1, 0))
    buffs: dict = field(default_factory=dict)
    speed_bonus: float = 0
    damage_bonus: float = 0
    attack_rate_bonus: float = 0
    sword_range_bonus: float = 0
    special_gain_bonus: float = 0
    vampirism: float = 0
    ricochet_bounces: int = 0
    poison_level: int = 0
    projectile_count_bonus: int = 0

    def damage_multiplier(self):
        multiplier = 1.0 + self.damage_bonus
        if self.buffs.get("power", 0) > 0:
            multiplier += 0.25
        return multiplier

    def speed_multiplier(self):
        multiplier = 1.0 + self.speed_bonus
        if self.buffs.get("speed", 0) > 0:
            multiplier += 0.45
        if self.shield_timer > 0:
            multiplier += 0.25
        return multiplier

    def attack_rate_multiplier(self):
        return 1.0 + self.attack_rate_bonus

    def projectile_damage(self):
        return PROJECTILE_DAMAGE * self.damage_multiplier()

    def projectile_count(self):
        return 1 + self.projectile_count_bonus

    def sword_damage(self):
        return SWORD_DAMAGE * self.damage_multiplier()

    def sword_radius(self):
        return SWORD_RADIUS * (1.0 + self.sword_range_bonus)

    def add_special(self, amount):
        self.special = min(SPECIAL_MAX, self.special + amount * (1.0 + self.special_gain_bonus))

    def activate_buff(self, name):
        self.buffs[name] = BUFF_DURATION

    def activate_shield(self):
        self.shield_timer = SHIELD_DURATION
        self.invulnerable_timer = max(self.invulnerable_timer, SHIELD_DURATION)


@dataclass
class Enemy:
    id: int
    pos: Vector2
    kind: str
    radius: float
    speed: float
    max_health: float
    health: float
    damage: float
    xp_value: int
    color: str
    special_value: float
    coin_chance: float
    frozen_timer: float = 0
    poison_timer: float = 0
    poison_dps: float = 0
    hit_flash: float = 0
    knockback: Vector2 = field(default_factory=lambda: Vector2(0, 0))


@dataclass
class Projectile:
    pos: Vector2
    vel: Vector2
    damage: float = PROJECTILE_DAMAGE
    radius: float = PROJECTILE_RADIUS
    life: float = PROJECTILE_LIFE
    freeze: bool = False
    poison: bool = False
    poison_dps: float = 0
    bounces_left: int = 0
    hit_ids: set = field(default_factory=set)


@dataclass
class Slash:
    origin: Vector2
    direction: Vector2
    radius: float = SWORD_RADIUS
    arc: float = SWORD_ARC
    damage: float = SWORD_DAMAGE
    duration: float = SWORD_DURATION
    age: float = 0
    hit_ids: set = field(default_factory=set)


@dataclass
class Drop:
    pos: Vector2
    kind: str
    value: float = 1
    radius: float = 10
    ttl: float = 18.0
    bob: float = 0


@dataclass
class Destructible:
    id: str
    rect: RectBody
    hp: float
    max_hp: float
    kind: str
    chunk: tuple
    hit_flash: float = 0


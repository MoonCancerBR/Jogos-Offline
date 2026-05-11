import math


SCREEN_WIDTH = 1100
SCREEN_HEIGHT = 720
FPS = 60

WORLD_TILE_SIZE = 96
CHUNK_SIZE = 768
VIEW_PADDING = 180

PLAYER_RADIUS = 18
PLAYER_MAX_HEALTH = 120
PLAYER_BASE_SPEED = 235.0
PLAYER_CONTACT_GRACE = 0.35

DASH_SPEED = 790.0
DASH_DURATION = 0.17
DASH_COOLDOWN = 1.25

PROJECTILE_SPEED = 720.0
PROJECTILE_RADIUS = 5
PROJECTILE_DAMAGE = 16
PROJECTILE_COOLDOWN = 0.17
PROJECTILE_LIFE = 1.65
MAX_PROJECTILES = 130

SWORD_DAMAGE = 46
SWORD_RADIUS = 92
SWORD_ARC = math.radians(88)
SWORD_COOLDOWN = 0.42
SWORD_DURATION = 0.16

SPECIAL_MAX = 100
SPECIAL_RADIUS = 560
SPECIAL_DAMAGE = 230
SPECIAL_CHARGE_BASIC = 9
SPECIAL_CHARGE_RUNNER = 7
SPECIAL_CHARGE_BRUTE = 16

XP_MAGNET_RADIUS = 150
DROP_PICKUP_RADIUS = 32
DROP_ATTRACT_SPEED = 360.0

SHIELD_DURATION = 7.0
BUFF_DURATION = 8.0
FREEZE_DURATION = 2.4

MAX_ENEMIES = 95
SPAWN_START_DELAY = 1.15
SPAWN_MIN_DELAY = 0.23
SPAWN_DISTANCE_MIN = 560
SPAWN_DISTANCE_MAX = 760
CONTACT_DAMAGE_PER_SECOND = 17.0

CAMERA_SMOOTHING = 9.5
SCREEN_SHAKE_DECAY = 5.5

COLORS = {
    "bg": "#07111E",
    "panel": "#101927",
    "panel_2": "#172033",
    "text": "#F8FAFC",
    "muted": "#94A3B8",
    "muted_2": "#64748B",
    "health": "#EF4444",
    "health_bg": "#44151B",
    "special": "#38BDF8",
    "xp": "#22C55E",
    "coin": "#FACC15",
    "player": "#E2E8F0",
    "player_core": "#38BDF8",
    "projectile": "#67E8F9",
    "projectile_freeze": "#BAE6FD",
    "sword": "#FDE68A",
    "shield": "#60A5FA",
    "danger": "#FB7185",
    "upgrade": "#A78BFA",
}

TERRAIN_TYPES = {
    "grass": {
        "color": "#173B2A",
        "accent": "#1F5138",
        "speed": 1.0,
        "name": "Grama",
    },
    "sand": {
        "color": "#786C3A",
        "accent": "#9A8849",
        "speed": 0.55,
        "name": "Areia",
    },
    "mud": {
        "color": "#46372B",
        "accent": "#5C4938",
        "speed": 0.76,
        "name": "Lama",
    },
    "stone": {
        "color": "#293241",
        "accent": "#384558",
        "speed": 0.92,
        "name": "Pedra",
    },
}

ENEMY_TYPES = {
    "basic": {
        "name": "Errante",
        "radius": 17,
        "speed": 122.0,
        "health": 36,
        "damage": 14.0,
        "xp": 11,
        "color": "#F97316",
        "special": SPECIAL_CHARGE_BASIC,
        "coin_chance": 0.12,
    },
    "runner": {
        "name": "Corredor",
        "radius": 13,
        "speed": 178.0,
        "health": 24,
        "damage": 11.0,
        "xp": 9,
        "color": "#F43F5E",
        "special": SPECIAL_CHARGE_RUNNER,
        "coin_chance": 0.10,
    },
    "brute": {
        "name": "Bruto",
        "radius": 24,
        "speed": 82.0,
        "health": 95,
        "damage": 25.0,
        "xp": 25,
        "color": "#A855F7",
        "special": SPECIAL_CHARGE_BRUTE,
        "coin_chance": 0.28,
    },
}

UPGRADES = {
    "speed": {
        "title": "Passos Leves",
        "description": "+8% velocidade permanente.",
    },
    "damage": {
        "title": "Lamina e Cano",
        "description": "+13% dano em todos os ataques.",
    },
    "max_health": {
        "title": "Pulso Vital",
        "description": "+22 vida maxima e cura parcial.",
    },
    "fire_rate": {
        "title": "Ritmo de Combate",
        "description": "+11% cadencia de tiros e golpes.",
    },
    "sword_range": {
        "title": "Alcance da Espada",
        "description": "+10% alcance do corte.",
    },
    "special_gain": {
        "title": "Nucleo Instavel",
        "description": "+16% carga de especial por abate.",
    },
}


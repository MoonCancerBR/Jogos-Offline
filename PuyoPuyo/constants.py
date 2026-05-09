import pygame

# Configurações da Tela
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
BLOCK_SIZE = 40  # Aumentado para compensar a largura menor do grid
BOARD_WIDTH = 6
BOARD_HEIGHT = 12

# Cores (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)

# Cores dos Puyos
COLORS = {
    'R': (239, 68, 68),   # Vermelho (Tailwind Red 500)
    'G': (34, 197, 94),   # Verde (Tailwind Green 500)
    'B': (59, 130, 246),  # Azul (Tailwind Blue 500)
    'Y': (234, 179, 8),   # Amarelo (Tailwind Yellow 500)
    'P': (168, 85, 247)   # Roxo (Tailwind Purple 500)
}

# Configurações de Tempo e Movimento
DAS_DELAY = 170  # ms
DAS_INTERVAL = 50 # ms
LOCK_DELAY = 500 # ms
ZONE_DURATION = 10000 # ms (10 segundos)

# Game modes
GAME_MODE_HARDCORE = "hardcore"
GAME_MODE_CASUAL = "casual"
GAME_MODE_SANDBOX = "sandbox"
GAME_MODE_LABELS = {
    GAME_MODE_HARDCORE: "Hardcore",
    GAME_MODE_CASUAL: "Casual",
    GAME_MODE_SANDBOX: "Sandbox",
}

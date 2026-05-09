import pygame

if __package__:
    from .constants import *
else:
    from constants import *


COMMAND_ROWS = [
    ("Seta esquerda", "Mover para a esquerda"),
    ("Seta direita", "Mover para a direita"),
    ("Seta baixo", "Descer mais rapido"),
    ("Seta cima", "Girar para a direita"),
    ("Z", "Girar para a esquerda"),
    ("Espaco", "Queda rapida"),
    ("C", "Guardar ou trocar peca"),
    ("Shift", "Ativar ou encerrar Zone"),
    ("Esc", "Pausar ou voltar"),
    ("R", "Reiniciar no Game Over"),
]


class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.button_font = pygame.font.SysFont("Arial", 22, bold=True)
        self.large_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.pause_button_rect = pygame.Rect(SCREEN_WIDTH - 150, SCREEN_HEIGHT - 62, 100, 40)

        self.board_rect = pygame.Rect(
            (SCREEN_WIDTH - BOARD_WIDTH * BLOCK_SIZE) // 2,
            (SCREEN_HEIGHT - BOARD_HEIGHT * BLOCK_SIZE) // 2,
            BOARD_WIDTH * BLOCK_SIZE,
            BOARD_HEIGHT * BLOCK_SIZE,
        )

    def draw_puyo(self, x, y, color, alpha=255, outline=True):
        radius = BLOCK_SIZE // 2 - 2
        center = (int(x + BLOCK_SIZE // 2), int(y + BLOCK_SIZE // 2))
        
        if alpha < 255:
            surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(surface, (*color, alpha), (BLOCK_SIZE // 2, BLOCK_SIZE // 2), radius)
            if outline:
                pygame.draw.circle(surface, (255, 255, 255, alpha), (BLOCK_SIZE // 2, BLOCK_SIZE // 2), radius, 2)
            self.screen.blit(surface, (x, y))
        else:
            pygame.draw.circle(self.screen, color, center, radius)
            # Brilho (highlight)
            pygame.draw.circle(self.screen, (255, 255, 255), (center[0] - radius//3, center[1] - radius//3), radius//4)
            if outline:
                pygame.draw.circle(self.screen, DARK_GRAY, center, radius, 1)

    def draw_board(self, board):
        pygame.draw.rect(self.screen, DARK_GRAY, self.board_rect, 2)
        # Background do board
        pygame.draw.rect(self.screen, (10, 15, 25), self.board_rect)
        
        for y, row in enumerate(board.grid):
            for x, color in enumerate(row):
                if color:
                    self.draw_puyo(
                        self.board_rect.x + x * BLOCK_SIZE,
                        self.board_rect.y + y * BLOCK_SIZE,
                        color,
                    )

    def draw_piece(self, piece, offset_x=0, offset_y=0, alpha=255):
        # Desenhar Main
        self.draw_puyo(
            offset_x + piece.x * BLOCK_SIZE,
            offset_y + piece.y * BLOCK_SIZE,
            piece.color_main,
            alpha,
        )
        # Desenhar Sec
        sx, sy = piece.get_sec_pos()
        self.draw_puyo(
            offset_x + sx * BLOCK_SIZE,
            offset_y + sy * BLOCK_SIZE,
            piece.color_sec,
            alpha,
        )

    def draw_ghost(self, game):
        if game.locking: return
        ghost_y = game.get_ghost_y()
        offset_y = ghost_y - game.current_piece.y
        
        # Ghost Main
        self.draw_puyo(
            self.board_rect.x + game.current_piece.x * BLOCK_SIZE,
            self.board_rect.y + ghost_y * BLOCK_SIZE,
            game.current_piece.color_main,
            alpha=80, outline=False
        )
        # Ghost Sec
        sx, sy = game.current_piece.get_sec_pos()
        self.draw_puyo(
            self.board_rect.x + sx * BLOCK_SIZE,
            self.board_rect.y + (sy + offset_y) * BLOCK_SIZE,
            game.current_piece.color_sec,
            alpha=80, outline=False
        )

    def draw_sidebar(self, game):
        hold_text = self.font.render("HOLD", True, WHITE)
        self.screen.blit(hold_text, (50, 50))
        pygame.draw.rect(self.screen, DARK_GRAY, (50, 80, 120, 150), 2)
        if game.hold_piece:
            self.draw_puyo(50 + 40, 80 + 60, game.hold_piece.color_main)
            sx, sy = game.hold_piece.get_sec_pos()
            dx = sx - game.hold_piece.x
            dy = sy - game.hold_piece.y
            self.draw_puyo(50 + 40 + dx * BLOCK_SIZE, 80 + 60 + dy * BLOCK_SIZE, game.hold_piece.color_sec)

        next_text = self.font.render("NEXT", True, WHITE)
        self.screen.blit(next_text, (SCREEN_WIDTH - 170, 50))
        pygame.draw.rect(self.screen, DARK_GRAY, (SCREEN_WIDTH - 170, 80, 120, 450), 2)
        for i, piece in enumerate(game.next_queue):
            base_x = SCREEN_WIDTH - 170 + 40
            base_y = 80 + 40 + i * 85
            self.draw_puyo(base_x, base_y, piece.color_main)
            self.draw_puyo(base_x, base_y - BLOCK_SIZE, piece.color_sec) # Puyo sec é sempre acima no queue

        score_text = self.font.render(f"Score: {game.score}", True, WHITE)
        level_text = self.font.render(f"Level: {game.level}", True, WHITE)
        lines_text = self.font.render(f"Puyos: {game.puyos_cleared_total}", True, WHITE)
        mode_text = self.font.render(f"Mode: {GAME_MODE_LABELS.get(game.mode, game.mode)}", True, WHITE)
        self.screen.blit(score_text, (50, 250))
        self.screen.blit(level_text, (50, 280))
        self.screen.blit(lines_text, (50, 310))
        self.screen.blit(mode_text, (50, 340))

        zone_text = self.font.render("ZONE", True, WHITE)
        self.screen.blit(zone_text, (50, 390))
        pygame.draw.rect(self.screen, DARK_GRAY, (50, 420, 100, 20), 2)
        energy_width = int(game.zone_energy)
        pygame.draw.rect(self.screen, (244, 114, 182), (50, 420, energy_width, 20)) # Rosa no Puyo Puyo

        if game.zone_active:
            active_text = self.font.render("ZONE ACTIVE!", True, (244, 114, 182))
            self.screen.blit(active_text, (50, 450))

        if game.combo > 1:
            combo_text = self.font.render(f"COMBO {game.combo}", True, (255, 255, 0))
            self.screen.blit(combo_text, (SCREEN_WIDTH // 2 - 50, 80))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        text = self.large_font.render("GAME OVER", True, WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, rect)

        retry_text = self.font.render("Press R to Restart", True, WHITE)
        retry_rect = retry_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 60))
        self.screen.blit(retry_text, retry_rect)

    def draw_game_scene(self, game, show_pause_button=True):
        if game.zone_active:
            self.screen.fill((60, 20, 40))
        else:
            self.screen.fill((20, 20, 30))

        self.draw_board(game.board)
        if not game.game_over:
            self.draw_ghost(game)
            if not game.locking:
                self.draw_piece(game.current_piece, self.board_rect.x, self.board_rect.y)
        
        self.draw_sidebar(game)

        if show_pause_button and not game.game_over:
            self.draw_button(self.pause_button_rect, "Pause", False, False)

        if game.game_over:
            self.draw_game_over()

    def render(self, game):
        self.draw_game_scene(game)
        pygame.display.flip()
        if game.game_over:
            return []
        return [("pause", self.pause_button_rect)]

    def draw_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 185))
        self.screen.blit(overlay, (0, 0))

    def draw_panel(self, rect):
        pygame.draw.rect(self.screen, (18, 24, 38), rect, border_radius=8)
        pygame.draw.rect(self.screen, (71, 85, 105), rect, 2, border_radius=8)

    def draw_centered_text(self, text, font, color, y):
        surface = font.render(text, True, color)
        rect = surface.get_rect(center=(SCREEN_WIDTH // 2, y))
        self.screen.blit(surface, rect)

    def draw_button(self, rect, label, selected=False, hovered=False):
        if selected:
            fill = (236, 72, 153) # Pink 500
            border = (244, 114, 182) # Pink 400
        elif hovered:
            fill = (190, 24, 93) # Pink 700
            border = (219, 39, 119) # Pink 600
        else:
            fill = (30, 41, 59)
            border = (71, 85, 105)

        pygame.draw.rect(self.screen, fill, rect, border_radius=6)
        pygame.draw.rect(self.screen, border, rect, 2, border_radius=6)
        text = self.button_font.render(label, True, WHITE)
        text_rect = text.get_rect(center=rect.center)
        self.screen.blit(text, text_rect)

    def render_mode_select(self, selected_index, mouse_pos):
        self.screen.fill((7, 11, 20))
        self.draw_centered_text("Escolha o modo de jogo", self.large_font, WHITE, 150)

        panel = pygame.Rect(150, 185, 500, 430)
        self.draw_panel(panel)

        options = [
            (GAME_MODE_HARDCORE, "Hardcore", "Velocidade aumenta conforme voce avanca."),
            (GAME_MODE_CASUAL, "Casual", "Velocidade de queda fixa."),
        ]

        buttons = []
        for index, (action, label, description) in enumerate(options):
            rect = pygame.Rect(230, 245 + index * 112, 340, 56)
            hovered = rect.collidepoint(mouse_pos)
            self.draw_button(rect, label, selected_index == index, hovered)
            desc = self.small_font.render(description, True, (203, 213, 225))
            desc_rect = desc.get_rect(center=(SCREEN_WIDTH // 2, rect.bottom + 22))
            self.screen.blit(desc, desc_rect)
            buttons.append((action, rect))

        pygame.display.flip()
        return buttons

    def render_pause_menu(self, game, options, selected_index, mouse_pos):
        self.draw_game_scene(game, show_pause_button=False)
        self.draw_overlay()

        panel = pygame.Rect(190, 85, 420, 530)
        self.draw_panel(panel)
        self.draw_centered_text("Pausado", self.large_font, WHITE, 145)
        mode = GAME_MODE_LABELS.get(game.mode, game.mode)
        self.draw_centered_text(f"Modo: {mode}", self.small_font, (203, 213, 225), 190)

        buttons = []
        for index, (label, action) in enumerate(options):
            rect = pygame.Rect(250, 235 + index * 66, 300, 48)
            hovered = rect.collidepoint(mouse_pos)
            self.draw_button(rect, label, selected_index == index, hovered)
            buttons.append((action, rect))

        pygame.display.flip()
        return buttons

    def render_commands_menu(self, game, mouse_pos):
        self.draw_game_scene(game, show_pause_button=False)
        self.draw_overlay()

        panel = pygame.Rect(135, 55, 530, 590)
        self.draw_panel(panel)
        self.draw_centered_text("Lista de comandos", self.large_font, WHITE, 110)

        y = 165
        for key, action in COMMAND_ROWS:
            key_surface = self.button_font.render(key, True, (147, 197, 253))
            action_surface = self.small_font.render(action, True, (226, 232, 240))
            self.screen.blit(key_surface, (190, y))
            self.screen.blit(action_surface, (375, y + 4))
            y += 38

        back_rect = pygame.Rect(250, 570, 300, 48)
        self.draw_button(back_rect, "Voltar", True, back_rect.collidepoint(mouse_pos))
        pygame.display.flip()
        return [("back_to_pause", back_rect)]

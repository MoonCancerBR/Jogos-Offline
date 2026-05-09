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

    def draw_block(self, x, y, color, alpha=255, outline=True):
        rect = pygame.Rect(x, y, BLOCK_SIZE, BLOCK_SIZE)
        if alpha < 255:
            surface = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
            surface.fill((*color, alpha))
            self.screen.blit(surface, rect)
        else:
            pygame.draw.rect(self.screen, color, rect)

        if outline:
            pygame.draw.rect(self.screen, DARK_GRAY, rect, 1)

    def draw_board(self, board):
        pygame.draw.rect(self.screen, DARK_GRAY, self.board_rect, 2)
        for y, row in enumerate(board.grid):
            for x, color in enumerate(row):
                if color:
                    self.draw_block(
                        self.board_rect.x + x * BLOCK_SIZE,
                        self.board_rect.y + y * BLOCK_SIZE,
                        color,
                    )

    def draw_piece(self, piece, offset_x=0, offset_y=0, alpha=255):
        for px, py in piece.current_shape:
            self.draw_block(
                offset_x + (piece.x + px) * BLOCK_SIZE,
                offset_y + (piece.y + py) * BLOCK_SIZE,
                piece.color,
                alpha,
            )

    def draw_ghost(self, game):
        ghost_y = game.get_ghost_y()
        for px, py in game.current_piece.current_shape:
            rect = pygame.Rect(
                self.board_rect.x + (game.current_piece.x + px) * BLOCK_SIZE,
                self.board_rect.y + (ghost_y + py) * BLOCK_SIZE,
                BLOCK_SIZE,
                BLOCK_SIZE,
            )
            pygame.draw.rect(self.screen, game.current_piece.color, rect, 1)

    def draw_sidebar(self, game):
        hold_text = self.font.render("HOLD", True, WHITE)
        self.screen.blit(hold_text, (50, 50))
        pygame.draw.rect(self.screen, DARK_GRAY, (50, 80, 120, 120), 2)
        if game.hold_piece:
            for px, py in game.hold_piece.current_shape:
                self.draw_block(60 + px * BLOCK_SIZE, 100 + py * BLOCK_SIZE, game.hold_piece.color)

        next_text = self.font.render("NEXT", True, WHITE)
        self.screen.blit(next_text, (SCREEN_WIDTH - 170, 50))
        pygame.draw.rect(self.screen, DARK_GRAY, (SCREEN_WIDTH - 170, 80, 120, 400), 2)
        for i, piece in enumerate(game.next_queue):
            for px, py in piece.current_shape:
                self.draw_block(
                    SCREEN_WIDTH - 160 + px * BLOCK_SIZE,
                    100 + i * 70 + py * BLOCK_SIZE,
                    piece.color,
                )

        score_text = self.font.render(f"Score: {game.score}", True, WHITE)
        level_text = self.font.render(f"Level: {game.level}", True, WHITE)
        lines_text = self.font.render(f"Lines: {game.lines_cleared_total}", True, WHITE)
        mode_text = self.font.render(f"Mode: {GAME_MODE_LABELS.get(game.mode, game.mode)}", True, WHITE)
        self.screen.blit(score_text, (50, 250))
        self.screen.blit(level_text, (50, 280))
        self.screen.blit(lines_text, (50, 310))
        self.screen.blit(mode_text, (50, 340))

        zone_text = self.font.render("ZONE", True, WHITE)
        self.screen.blit(zone_text, (50, 390))
        pygame.draw.rect(self.screen, DARK_GRAY, (50, 420, 100, 20), 2)
        energy_width = int(game.zone_energy)
        pygame.draw.rect(self.screen, (0, 200, 255), (50, 420, energy_width, 20))

        if game.zone_active:
            active_text = self.font.render("ZONE ACTIVE!", True, (0, 255, 255))
            self.screen.blit(active_text, (50, 450))

        if game.is_t_spin:
            tspin_text = self.font.render("T-SPIN!", True, (255, 0, 255))
            self.screen.blit(tspin_text, (SCREEN_WIDTH // 2 - 40, 50))
        elif game.is_t_spin_mini:
            tspin_text = self.font.render("T-SPIN MINI", True, (255, 100, 255))
            self.screen.blit(tspin_text, (SCREEN_WIDTH // 2 - 60, 50))

        if game.combo > 0:
            combo_text = self.font.render(f"COMBO x{game.combo}", True, (255, 255, 0))
            self.screen.blit(combo_text, (SCREEN_WIDTH // 2 - 50, 80))

        if game.back_to_back:
            b2b_text = self.font.render("BACK-TO-BACK", True, (0, 255, 0))
            self.screen.blit(b2b_text, (SCREEN_WIDTH // 2 - 70, 110))

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
            self.screen.fill((0, 20, 40))
        else:
            self.screen.fill(BLACK)

        self.draw_board(game.board)
        self.draw_ghost(game)
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
            fill = (37, 99, 235)
            border = (147, 197, 253)
        elif hovered:
            fill = (51, 65, 85)
            border = (96, 165, 250)
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
            (GAME_MODE_SANDBOX, "Sandbox", "Blocos soltos caem e fecham buracos."),
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

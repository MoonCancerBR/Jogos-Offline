import pygame
import sys

if __package__:
    from .constants import *
    from .game_logic import GameLogic
    from .ui import UI
else:
    from constants import *
    from game_logic import GameLogic
    from ui import UI


MODE_OPTIONS = [GAME_MODE_HARDCORE, GAME_MODE_CASUAL]

PAUSE_OPTIONS = [
    ("Mostrar lista de comandos", "commands"),
    ("Reiniciar", "restart"),
    ("Trocar modo de jogo", "change_mode"),
    ("Trocar de jogo", "menu"),
    ("Fechar", "quit"),
]


class PuyoPuyoGame:
    def __init__(self):
        self.selected_mode = GAME_MODE_HARDCORE

    def run(self):
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Modern Puyo Puyo Python")
        clock = pygame.time.Clock()
        ui = UI(screen)

        game = None
        state = "mode_select"
        return_action = "menu"
        button_rects = []
        mode_selected = 0
        pause_selected = 0
        last_move_time = 0
        move_direction = 0

        def reset_movement():
            nonlocal last_move_time, move_direction
            last_move_time = 0
            move_direction = 0

        def start_game(mode):
            nonlocal game, state, mode_selected
            self.selected_mode = mode
            mode_selected = MODE_OPTIONS.index(mode)
            game = GameLogic(mode)
            state = "playing"
            reset_movement()

        def restart_game():
            nonlocal game, state
            game = GameLogic(self.selected_mode)
            state = "playing"
            reset_movement()

        def handle_pause_action(action):
            nonlocal state, pause_selected, return_action, running

            if action == "commands":
                state = "commands"
            elif action == "restart":
                restart_game()
            elif action == "change_mode":
                state = "mode_select"
                pause_selected = 0
                reset_movement()
            elif action == "menu":
                return_action = "menu"
                running = False
            elif action == "quit":
                return_action = "quit"
                running = False

        running = True
        while running:
            dt = clock.tick(60)
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return_action = "menu"
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for action, rect in button_rects:
                        if not rect.collidepoint(event.pos):
                            continue

                        if state == "mode_select" and action in MODE_OPTIONS:
                            start_game(action)
                        elif state == "playing" and action == "pause":
                            state = "paused"
                            pause_selected = 0
                            reset_movement()
                        elif state == "paused":
                            handle_pause_action(action)
                        elif state == "commands" and action == "back_to_pause":
                            state = "paused"
                        break

                elif event.type == pygame.KEYDOWN:
                    if state == "mode_select":
                        if event.key == pygame.K_ESCAPE:
                            return_action = "menu"
                            running = False
                        elif event.key in (pygame.K_UP, pygame.K_LEFT):
                            mode_selected = (mode_selected - 1) % len(MODE_OPTIONS)
                        elif event.key in (pygame.K_DOWN, pygame.K_RIGHT):
                            mode_selected = (mode_selected + 1) % len(MODE_OPTIONS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            start_game(MODE_OPTIONS[mode_selected])

                    elif state == "paused":
                        if event.key == pygame.K_ESCAPE:
                            state = "playing"
                            reset_movement()
                        elif event.key == pygame.K_UP:
                            pause_selected = (pause_selected - 1) % len(PAUSE_OPTIONS)
                        elif event.key == pygame.K_DOWN:
                            pause_selected = (pause_selected + 1) % len(PAUSE_OPTIONS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            handle_pause_action(PAUSE_OPTIONS[pause_selected][1])

                    elif state == "commands":
                        if event.key in (
                            pygame.K_ESCAPE,
                            pygame.K_BACKSPACE,
                            pygame.K_RETURN,
                            pygame.K_KP_ENTER,
                            pygame.K_SPACE,
                        ):
                            state = "paused"

                    elif state == "playing":
                        if event.key == pygame.K_ESCAPE:
                            state = "paused"
                            pause_selected = 0
                            reset_movement()
                            continue

                        if game.game_over:
                            if event.key == pygame.K_r:
                                restart_game()
                            continue

                        if event.key == pygame.K_LEFT:
                            game.move(-1, 0)
                            move_direction = -1
                            last_move_time = pygame.time.get_ticks() + DAS_DELAY
                        elif event.key == pygame.K_RIGHT:
                            game.move(1, 0)
                            move_direction = 1
                            last_move_time = pygame.time.get_ticks() + DAS_DELAY
                        elif event.key == pygame.K_DOWN:
                            game.move(0, 1)
                        elif event.key == pygame.K_UP:
                            game.rotate(True)
                        elif event.key == pygame.K_z:
                            game.rotate(False)
                        elif event.key == pygame.K_SPACE:
                            game.hard_drop()
                        elif event.key == pygame.K_c:
                            game.hold()
                        elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                            game.toggle_zone()

                elif event.type == pygame.KEYUP and state == "playing":
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        move_direction = 0

            if state == "playing":
                if move_direction != 0 and not game.game_over:
                    now = pygame.time.get_ticks()
                    if now > last_move_time:
                        game.move(move_direction, 0)
                        last_move_time = now + DAS_INTERVAL

                game.update(dt)
                button_rects = ui.render(game)
            elif state == "mode_select":
                button_rects = ui.render_mode_select(mode_selected, mouse_pos)
            elif state == "paused":
                button_rects = ui.render_pause_menu(game, PAUSE_OPTIONS, pause_selected, mouse_pos)
            elif state == "commands":
                button_rects = ui.render_commands_menu(game, mouse_pos)

        pygame.quit()
        return return_action


def main():
    app = PuyoPuyoGame()
    result = app.run()
    if result == "quit":
        sys.exit()


if __name__ == "__main__":
    main()

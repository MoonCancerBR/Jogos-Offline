import pygame
from pygame.math import Vector2

if __package__:
    from .constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
    from .game_logic import GameLogic
    from .ui import UI
else:
    from constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH
    from game_logic import GameLogic
    from ui import UI


PAUSE_OPTIONS = [
    ("Continuar", "resume"),
    ("Comandos", "commands"),
    ("Reiniciar", "restart"),
    ("Voltar ao Menu", "menu"),
    ("Fechar", "quit"),
]


class SobrevivenciaGame:
    def run(self):
        pygame.init()
        pygame.display.set_caption("Sobrevivencia - Top Down Survival")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        clock = pygame.time.Clock()
        ui = UI(screen)
        game = GameLogic()

        state = "start"
        return_action = "menu"
        button_rects = []
        pause_selected = 0
        upgrade_selected = 0
        commands_return_state = "start"
        running = True

        while running:
            dt = clock.tick(FPS) / 1000.0
            mouse_pos = pygame.mouse.get_pos()
            mouse_world = ui.screen_to_world(mouse_pos, game.camera)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return_action = "menu"
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for action, rect in button_rects:
                        if rect.collidepoint(event.pos):
                            if action == "commands":
                                commands_return_state = "paused" if state == "paused" else "start"
                            elif action == "back":
                                state = commands_return_state
                                break
                            state, running, return_action, pause_selected, upgrade_selected = self._handle_action(
                                action,
                                state,
                                game,
                                running,
                                return_action,
                                pause_selected,
                                upgrade_selected,
                            )
                            break

                elif event.type == pygame.KEYDOWN:
                    if state == "start":
                        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            game.restart()
                            state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            return_action = "menu"
                        elif event.key == pygame.K_c:
                            commands_return_state = "start"
                            state = "commands"

                    elif state == "playing":
                        if event.key == pygame.K_ESCAPE:
                            state = "paused"
                            pause_selected = 0
                        elif event.key in (pygame.K_q, pygame.K_LSHIFT, pygame.K_RSHIFT):
                            game.toggle_mode()
                        elif event.key == pygame.K_SPACE:
                            game.try_dash(mouse_world)
                        elif event.key == pygame.K_e:
                            game.try_special()

                    elif state == "paused":
                        if event.key == pygame.K_ESCAPE:
                            state = "playing"
                        elif event.key == pygame.K_UP:
                            pause_selected = (pause_selected - 1) % len(PAUSE_OPTIONS)
                        elif event.key == pygame.K_DOWN:
                            pause_selected = (pause_selected + 1) % len(PAUSE_OPTIONS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action = PAUSE_OPTIONS[pause_selected][1]
                            if action == "commands":
                                commands_return_state = "paused"
                            state, running, return_action, pause_selected, upgrade_selected = self._handle_action(
                                action,
                                state,
                                game,
                                running,
                                return_action,
                                pause_selected,
                                upgrade_selected,
                            )

                    elif state == "commands":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            state = commands_return_state

                    elif state == "upgrade":
                        if event.key == pygame.K_UP:
                            upgrade_selected = (upgrade_selected - 1) % len(game.upgrade_choices)
                        elif event.key == pygame.K_DOWN:
                            upgrade_selected = (upgrade_selected + 1) % len(game.upgrade_choices)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            game.apply_upgrade(game.upgrade_choices[upgrade_selected])
                            upgrade_selected = 0
                            state = "playing"

                    elif state == "game_over":
                        if event.key == pygame.K_r:
                            game.restart()
                            state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            return_action = "menu"

            if state == "playing":
                move = self._movement_vector()
                game.update(dt, move, mouse_world)
                if game.level_up_pending:
                    state = "upgrade"
                    upgrade_selected = 0
                elif game.game_over:
                    state = "game_over"
                ui.render_game(game, mouse_pos)
                button_rects = []
            elif state == "start":
                button_rects = ui.render_start(mouse_pos)
            elif state == "paused":
                button_rects = ui.render_pause(game, PAUSE_OPTIONS, pause_selected, mouse_pos)
            elif state == "commands":
                button_rects = ui.render_commands(mouse_pos)
            elif state == "upgrade":
                button_rects = ui.render_upgrade(game, upgrade_selected, mouse_pos)
            elif state == "game_over":
                button_rects = ui.render_game_over(game, mouse_pos)

        pygame.quit()
        return return_action

    def _movement_vector(self):
        keys = pygame.key.get_pressed()
        x = 0
        y = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            x += 1
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            y += 1
        return Vector2(x, y)

    def _handle_action(self, action, state, game, running, return_action, pause_selected, upgrade_selected):
        if action == "start":
            game.restart()
            state = "playing"
        elif action == "commands":
            state = "commands"
        elif action == "resume":
            state = "playing"
        elif action == "restart":
            game.restart()
            state = "playing"
        elif action == "menu":
            return_action = "menu"
            running = False
        elif action == "quit":
            return_action = "quit"
            running = False
        elif action in game.upgrade_choices:
            game.apply_upgrade(action)
            upgrade_selected = 0
            state = "playing"
        return state, running, return_action, pause_selected, upgrade_selected


def main():
    app = SobrevivenciaGame()
    app.run()


if __name__ == "__main__":
    main()

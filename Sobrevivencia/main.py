import pygame
from pygame.math import Vector2

if __package__:
    from .data.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, CHARACTERS, SPECIAL_COMBO_HOLD_SECONDS
    from .core.game_logic import GameLogic
    from .presentation.ui import UI
else:
    from Sobrevivencia.data.constants import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, CHARACTERS, SPECIAL_COMBO_HOLD_SECONDS
    from Sobrevivencia.core.game_logic import GameLogic
    from Sobrevivencia.presentation.ui import UI


PAUSE_OPTIONS = [
    ("Continuar", "resume"),
    ("Inventario", "inventory"),
    ("Gerenciamento de Skills", "skills"),
    ("Loja de Status", "stat_shop"),
    ("Construcoes", "constructions"),
    ("Comandos", "commands"),
    ("Configuracoes", "settings"),
    ("Trocar Personagem", "change_character"),
    ("Reiniciar", "restart"),
    ("Voltar ao Menu", "menu"),
    ("Fechar", "quit"),
]


START_OPTIONS = [
    ("Iniciar Jogo", "character_select"),
    ("Comandos", "commands"),
    ("Configuracoes", "settings"),
    ("Voltar ao Menu", "menu"),
]


CONTROL_ACTIONS = [
    ("move_up", "Mover para cima"),
    ("move_down", "Mover para baixo"),
    ("move_left", "Mover para esquerda"),
    ("move_right", "Mover para direita"),
    ("dash", "Dash"),
    ("special", "Especial / combo"),
    ("toggle_weapon", "Alternar arma"),
    ("inventory", "Inventario"),
    ("skills", "Skills"),
    ("stat_shop", "Loja de Status"),
    ("pause", "Pausar"),
    ("settings", "Configuracoes"),
    ("fullscreen", "Tela cheia"),
]


BINDING_SLOT_COUNT = 3


DEFAULT_BINDINGS = {
    "move_up": [("key", pygame.K_w), ("key", pygame.K_UP), None],
    "move_down": [("key", pygame.K_s), ("key", pygame.K_DOWN), None],
    "move_left": [("key", pygame.K_a), ("key", pygame.K_LEFT), None],
    "move_right": [("key", pygame.K_d), ("key", pygame.K_RIGHT), None],
    "dash": [("key", pygame.K_SPACE), None, None],
    "special": [("key", pygame.K_e), None, None],
    "toggle_weapon": [("key", pygame.K_q), ("key", pygame.K_LSHIFT), None],
    "inventory": [("key", pygame.K_i), ("key", pygame.K_TAB), None],
    "skills": [("key", pygame.K_k), None, None],
    "stat_shop": [("key", pygame.K_l), None, None],
    "pause": [("key", pygame.K_ESCAPE), None, None],
    "settings": [("key", pygame.K_o), None, None],
    "fullscreen": [("key", pygame.K_F11), None, None],
}


JOYSTICK_DEFAULT_BINDINGS = {
    "move_up": ("joy_axis", 1, -1),
    "move_down": ("joy_axis", 1, 1),
    "move_left": ("joy_axis", 0, -1),
    "move_right": ("joy_axis", 0, 1),
    "dash": ("joy_button", 0),
    "special": ("joy_button", 2),
    "toggle_weapon": ("joy_button", 3),
    "inventory": ("joy_button", 6),
    "skills": ("joy_button", 5),
    "stat_shop": ("joy_button", 4),
    "pause": ("joy_button", 7),
}


JOYSTICK_DEADZONE = 0.55
JOYSTICK_AIM_DEADZONE = 0.28
JOYSTICK_AIM_DISTANCE = 230


class SobrevivenciaGame:
    def run(self):
        pygame.init()
        pygame.joystick.init()
        pygame.display.set_caption("Sobrevivencia - Top Down Survival")
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        clock = pygame.time.Clock()
        ui = UI(screen)
        game = GameLogic()
        controls = self._default_bindings()
        fullscreen = False
        self._event_pressed_bindings = []
        self._event_released_bindings = []
        self._joystick_axis_active = {}
        self._joystick_hat_active = {}
        self._init_joysticks()
        if self._joystick_count():
            self._apply_default_joystick_bindings(controls)

        state = "start"
        return_action = "menu"
        button_rects = []
        start_selected = 0
        pause_selected = 0
        upgrade_selected = 0
        inventory_selected = 0
        construction_selected = 0
        skill_selected = 0
        settings_selected = 0
        settings_slot = 0
        fusion_confirm_selected = 0
        game_over_selected = 0
        stat_shop_selected = 0
        mode_selected = 0
        multiplayer_selected = False
        character_selected = 0
        character_selected_2 = 0
        character_select_player = 0
        character_cancel_state = "start"
        commands_return_state = "start"
        skills_return_state = "paused"
        stat_shop_return_state = "paused"
        settings_return_state = "start"
        capture_binding = None
        special_holding = {0: False, 1: False}
        special_hold_time = {0: 0.0, 1: 0.0}
        special_hold_triggered = {0: False, 1: False}
        special_combo_checked = {0: False, 1: False}
        joystick_aim_dir = Vector2(1, 0)
        aim_mode = "mouse"
        running = True
        
        # Virtual Screen para Smoothscale Fullscreen
        self.virtual_screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        ui.screen = self.virtual_screen
        self.active_device = "keyboard" # "keyboard" ou "joystick"
        self.control_preference = "auto" # "auto", "keyboard", "joystick"

        while running:
            dt = clock.tick(FPS) / 1000.0
            
            final_screen = pygame.display.get_surface()
            raw_mouse_pos = pygame.mouse.get_pos()
            fw, fh = final_screen.get_size()
            vw, vh = self.virtual_screen.get_size()
            if fw != vw or fh != vh:
                mouse_pos = (int(raw_mouse_pos[0] * vw / fw), int(raw_mouse_pos[1] * vh / fh))
            else:
                mouse_pos = raw_mouse_pos
                
            joystick_aim = self._joystick_aim_vector()
            if joystick_aim.length_squared() > 0:
                joystick_aim_dir = joystick_aim.normalize()
                aim_mode = "joystick"
            aim_pos = self._aim_screen_pos(game, joystick_aim_dir) if aim_mode == "joystick" and not game.multiplayer else mouse_pos
            aim_world = ui.screen_to_world(aim_pos, game.camera)
            p2_aim_screen = None
            p2_aim_world = None
            if game.multiplayer and game.player2 is not None:
                p2_aim_screen = self._aim_screen_pos_for(game, game.player2, joystick_aim_dir)
                p2_aim_world = ui.screen_to_world(p2_aim_screen, game.camera)

            for event in self._poll_events(game):
                self._prepare_input_event(event)
                if event.type == pygame.QUIT:
                    return_action = "menu"
                    running = False

                elif event.type == pygame.JOYDEVICEADDED:
                    self._add_joystick(event.device_index)
                    self._apply_default_joystick_bindings(controls)
                    aim_mode = "joystick"
                    game.message = self._joystick_status_message()

                elif event.type == pygame.JOYDEVICEREMOVED:
                    self._remove_joystick(event.instance_id)
                    if not self._joystick_count():
                        aim_mode = "mouse"
                        self.active_device = "keyboard"
                    game.message = self._joystick_status_message()

                # Detecção de Dispositivo Ativo (Apenas se estiver em "auto")
                if self.control_preference == "auto":
                    if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                        self.active_device = "keyboard"
                        aim_mode = "mouse"
                    elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                        self.active_device = "joystick"
                        aim_mode = "joystick"
                else:
                    self.active_device = self.control_preference
                    aim_mode = "joystick" if self.active_device == "joystick" else "mouse"

                # Input Lock Multiplayer no Draft / Level Up
                if game.multiplayer and game.level_up_pending:
                    is_joystick_event = event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION)
                    is_keyboard_event = event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)
                    
                    if game.level_up_player_index == 0: # Turno do P1 (Teclado)
                        if is_joystick_event: continue
                    else: # Turno do P2 (Joystick)
                        if is_keyboard_event: continue
                
                # Trava de Dispositivo Singleplayer (Gameplay)
                if not game.multiplayer and state == "playing":
                    if self.active_device == "joystick" and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                        continue
                    if self.active_device == "keyboard" and event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION):
                        continue

                if state == "settings" and capture_binding:
                    binding = self._binding_from_event(event)
                    if binding is not None:
                        action_key, slot = capture_binding
                        controls[action_key][slot] = binding
                        capture_binding = None
                    continue

                elif event.type == pygame.MOUSEMOTION:
                    aim_mode = "mouse"

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    aim_mode = "mouse"
                    if state == "settings" and capture_binding:
                        action_key, slot = capture_binding
                        controls[action_key][slot] = self._binding_from_event(event)
                        capture_binding = None
                        continue

                    clicked_button = False
                    if event.button == 1:
                        for action, rect in button_rects:
                            if rect.collidepoint(event.pos):
                                clicked_button = True
                                if state == "settings":
                                    if action == "settings_back":
                                        state = settings_return_state
                                        capture_binding = None
                                    elif action == "settings_reset":
                                        controls = self._default_bindings()
                                        if self._joystick_count():
                                            self._apply_default_joystick_bindings(controls)
                                        capture_binding = None
                                    elif action == "settings_fullscreen":
                                        fullscreen = not fullscreen
                                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                                    elif action == "settings_control":
                                        prefs = ["auto", "keyboard", "joystick"]
                                        curr = prefs.index(self.control_preference)
                                        self.control_preference = prefs[(curr + 1) % len(prefs)]
                                        if self.control_preference != "auto":
                                            self.active_device = self.control_preference
                                            aim_mode = "joystick" if self.active_device == "joystick" else "mouse"
                                    elif action.startswith("bind:"):
                                        _, action_key, slot = action.split(":", 2)
                                        settings_selected = self._control_index(action_key)
                                        settings_slot = int(slot)
                                        capture_binding = (action_key, settings_slot)
                                    break
                                if action == "character_select":
                                    state = "mode_select" if self._joystick_count() else "character_select"
                                    character_selected = 0
                                    character_selected_2 = 0
                                    character_select_player = 0
                                    multiplayer_selected = False
                                    character_cancel_state = "start"
                                    break
                                if action in ("single_player", "multiplayer"):
                                    multiplayer_selected = action == "multiplayer"
                                    state = "character_select"
                                    character_selected = 0
                                    character_selected_2 = 0
                                    character_select_player = 0
                                    character_cancel_state = "mode_select"
                                    break
                                if action == "start_game":
                                    if multiplayer_selected and character_select_player == 0:
                                        character_select_player = 1
                                    else:
                                        char_class = list(CHARACTERS.keys())[character_selected]
                                        char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                                        game = GameLogic(char_class, char_class_2, multiplayer_selected)
                                        state = "playing"
                                    break
                                if action == "change_character":
                                    character_selected = self._current_character_index(game)
                                    character_selected_2 = self._current_character_index(game, 1)
                                    character_cancel_state = state
                                    multiplayer_selected = game.multiplayer
                                    character_select_player = 0
                                    state = "character_select"
                                    break
                                if state == "fusion_confirm":
                                    state, inventory_selected = self._handle_fusion_confirm_action(action, game, inventory_selected)
                                    break
                                if action == "toggle_menu_player" and state in ("inventory", "skills"):
                                    game.menu_player_index = 1 - game.menu_player_index
                                    inventory_selected = 0
                                    skill_selected = 0
                                    break
                                if state == "inventory":
                                    state, inventory_selected = self._handle_inventory_action(action, state, game, inventory_selected)
                                    if state == "fusion_confirm":
                                        fusion_confirm_selected = 1
                                    break
                                if state == "stat_shop":
                                    state = self._handle_stat_shop_action(action, game, stat_shop_return_state)
                                    break
                                if state == "constructions":
                                    state, construction_selected = self._handle_construction_action(action, construction_selected)
                                    break
                                if state == "skills":
                                    state, skill_selected = self._handle_skill_action(action, state, game, skill_selected, skills_return_state)
                                    break
                                if action == "commands":
                                    commands_return_state = "paused" if state == "paused" else "start"
                                elif action == "settings":
                                    settings_return_state = "paused" if state == "paused" else "start"
                                    state = "settings"
                                    capture_binding = None
                                    break
                                elif action == "skills":
                                    skills_return_state = "paused"
                                elif action == "stat_shop":
                                    stat_shop_return_state = "paused" if state == "paused" else "playing"
                                elif action == "back":
                                    if state == "mode_select":
                                        state = "start"
                                        break
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

                    if clicked_button:
                        continue

                    if self._action_pressed(event, controls, "fullscreen"):
                        fullscreen = not fullscreen
                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if state == "playing":
                        if self._action_pressed(event, controls, "pause"):
                            state = "paused"
                            pause_selected = 0
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "playing"
                            state = "settings"
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "toggle_weapon"):
                            game.toggle_mode()
                        elif self._action_pressed(event, controls, "dash"):
                            game.try_dash(aim_world)
                        elif self._action_pressed(event, controls, "special"):
                            special_holding[0] = True
                            special_hold_time[0] = 0.0
                            special_hold_triggered[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "inventory"):
                            game.menu_player_index = 0
                            state = "inventory"
                            inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(0).item_list()) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "skills"):
                            game.menu_player_index = 0
                            skills_return_state = "playing"
                            state = "skills"
                            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "stat_shop"):
                            stat_shop_return_state = "playing"
                            state = "stat_shop"
                            stat_shop_selected = 0
                            special_holding[0] = False
                            special_combo_checked[0] = False

                elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                    if not self._event_pressed_bindings:
                        continue
                    if self._action_pressed(event, controls, "fullscreen"):
                        fullscreen = not fullscreen
                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if state == "start":
                        if self._menu_up_pressed():
                            start_selected = (start_selected - 1) % len(START_OPTIONS)
                        elif self._menu_down_pressed():
                            start_selected = (start_selected + 1) % len(START_OPTIONS)
                        elif self._menu_confirm_pressed():
                            action = START_OPTIONS[start_selected][1]
                            if action == "character_select":
                                state = "mode_select" if self._joystick_count() else "character_select"
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                multiplayer_selected = False
                                character_cancel_state = "start"
                            elif action == "commands":
                                commands_return_state = "start"
                                state = "commands"
                            elif action == "settings":
                                settings_return_state = "start"
                                state = "settings"
                            elif action == "menu":
                                running = False
                                return_action = "menu"
                        elif self._menu_back_pressed():
                            running = False
                            return_action = "menu"
                    elif state == "mode_select":
                        if self._menu_up_pressed():
                            mode_selected = (mode_selected - 1) % 3
                        elif self._menu_down_pressed():
                            mode_selected = (mode_selected + 1) % 3
                        elif self._menu_confirm_pressed():
                            if mode_selected == 2:
                                state = "start"
                            else:
                                multiplayer_selected = mode_selected == 1
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                character_cancel_state = "mode_select"
                                state = "character_select"
                        elif self._menu_back_pressed():
                            state = "start"
                    elif state == "character_select":
                        if self._menu_left_pressed():
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 - 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected - 1) % len(CHARACTERS)
                        elif self._menu_right_pressed():
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 + 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected + 1) % len(CHARACTERS)
                        elif self._menu_confirm_pressed():
                            if multiplayer_selected and character_select_player == 0:
                                character_select_player = 1
                            else:
                                char_class = list(CHARACTERS.keys())[character_selected]
                                char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                                game = GameLogic(char_class, char_class_2, multiplayer_selected)
                                state = "playing"
                        elif self._menu_back_pressed():
                            if multiplayer_selected and character_select_player == 1:
                                character_select_player = 0
                            else:
                                state = character_cancel_state
                    elif state == "commands":
                        if self._menu_confirm_pressed() or self._menu_back_pressed():
                            state = commands_return_state
                    elif state == "settings":
                        if self._menu_back_pressed():
                            state = settings_return_state
                            capture_binding = None
                        elif self._menu_up_pressed():
                            settings_selected = (settings_selected - 1) % len(CONTROL_ACTIONS)
                        elif self._menu_down_pressed():
                            settings_selected = (settings_selected + 1) % len(CONTROL_ACTIONS)
                        elif self._menu_left_pressed():
                            settings_slot = (settings_slot - 1) % BINDING_SLOT_COUNT
                        elif self._menu_right_pressed():
                            settings_slot = (settings_slot + 1) % BINDING_SLOT_COUNT
                        elif self._menu_confirm_pressed():
                            action_key = CONTROL_ACTIONS[settings_selected][0]
                            capture_binding = (action_key, settings_slot)
                    elif state == "paused":
                        if self._menu_back_pressed():
                            state = "playing"
                        elif self._menu_up_pressed():
                            pause_selected = (pause_selected - 1) % len(PAUSE_OPTIONS)
                        elif self._menu_down_pressed():
                            pause_selected = (pause_selected + 1) % len(PAUSE_OPTIONS)
                        elif self._menu_confirm_pressed():
                            action = PAUSE_OPTIONS[pause_selected][1]
                            if action == "commands":
                                commands_return_state = "paused"
                            if action == "settings":
                                settings_return_state = "paused"
                                state = "settings"
                                capture_binding = None
                                continue
                            if action == "skills":
                                skills_return_state = "paused"
                                state = "skills"
                                skill_selected = min(skill_selected, max(0, len(game.get_player(game.menu_player_index).passives) - 1))
                                continue
                            if action == "stat_shop":
                                stat_shop_return_state = "paused"
                                state = "stat_shop"
                                stat_shop_selected = 0
                                continue
                            if action == "change_character":
                                character_selected = self._current_character_index(game)
                                character_selected_2 = self._current_character_index(game, 1)
                                multiplayer_selected = game.multiplayer
                                character_select_player = 0
                                character_cancel_state = "paused"
                                state = "character_select"
                                continue
                            state, running, return_action, pause_selected, upgrade_selected = self._handle_action(
                                action,
                                state,
                                game,
                                running,
                                return_action,
                                pause_selected,
                                upgrade_selected,
                            )
                    elif state == "playing":
                        if game.multiplayer:
                            if self._action_pressed(event, controls, "pause"):
                                state = "paused"
                                pause_selected = 0
                            elif self._action_pressed(event, controls, "toggle_weapon"):
                                game.toggle_mode(1)
                            elif self._action_pressed(event, controls, "dash"):
                                game.try_dash(p2_aim_world or aim_world, 1)
                            elif self._action_pressed(event, controls, "special"):
                                game.try_special(p2_aim_world or aim_world, 1)
                            elif self._action_pressed(event, controls, "inventory"):
                                game.menu_player_index = 1
                                state = "inventory"
                                inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(1).item_list()) - 1))
                            elif self._action_pressed(event, controls, "skills"):
                                game.menu_player_index = 1
                                skills_return_state = "playing"
                                state = "skills"
                                skill_selected = min(skill_selected, max(0, len(game.get_player(1).passives) - 1))
                            elif self._action_pressed(event, controls, "stat_shop"):
                                stat_shop_return_state = "playing"
                                state = "stat_shop"
                                stat_shop_selected = 0
                            continue
                        if self._action_pressed(event, controls, "pause"):
                            state = "paused"
                            pause_selected = 0
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "playing"
                            state = "settings"
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "toggle_weapon"):
                            game.toggle_mode()
                        elif self._action_pressed(event, controls, "dash"):
                            game.try_dash(aim_world)
                        elif self._action_pressed(event, controls, "special"):
                            special_holding[0] = True
                            special_hold_time[0] = 0.0
                            special_hold_triggered[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "inventory"):
                            game.menu_player_index = 0
                            state = "inventory"
                            inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(0).item_list()) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "skills"):
                            game.menu_player_index = 0
                            skills_return_state = "playing"
                            state = "skills"
                            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "stat_shop"):
                            stat_shop_return_state = "playing"
                            state = "stat_shop"
                            stat_shop_selected = 0
                            special_holding[0] = False
                            special_combo_checked[0] = False

                    elif state == "upgrade":
                        if self._menu_up_pressed():
                            upgrade_selected = (upgrade_selected - 1) % len(game.upgrade_choices)
                        elif self._menu_down_pressed():
                            upgrade_selected = (upgrade_selected + 1) % len(game.upgrade_choices)
                        elif self._menu_confirm_pressed():
                            game.apply_upgrade(game.upgrade_choices[upgrade_selected], game.level_up_player_index)
                            upgrade_selected = 0
                            state = "playing"

                    elif state == "inventory":
                        inv = game.get_inventory(game.menu_player_index)
                        raw_items = inv.item_list()
                        active_items = [item for item in raw_items if inv.is_active(item.key)]
                        reserve_items = [item for item in raw_items if not inv.is_active(item.key)]
                        items = active_items + reserve_items
                        if self._menu_back_pressed() or self._action_pressed(event, controls, "inventory"):
                            state = "playing"
                        elif game.multiplayer and self._menu_y_pressed():
                            game.menu_player_index = 1 - game.menu_player_index
                            inventory_selected = 0
                        elif items:
                            if self._menu_up_pressed():
                                inventory_selected -= 5
                            elif self._menu_down_pressed():
                                inventory_selected += 5
                            elif self._menu_left_pressed():
                                inventory_selected -= 1
                            elif self._menu_right_pressed():
                                inventory_selected += 1
                            elif self._menu_confirm_pressed():
                                game.toggle_inventory_item(items[inventory_selected].key)
                            elif self._menu_x_pressed():
                                game.upgrade_inventory_item(items[inventory_selected].key)
                            elif self._menu_y_pressed():
                                game.mark_or_fuse_item(items[inventory_selected].key)
                                if game.has_pending_fusion():
                                    state = "fusion_confirm"
                                    fusion_confirm_selected = 1
                            inventory_selected = max(0, min(inventory_selected, len(items) - 1))

                    elif state == "fusion_confirm":
                        if self._menu_back_pressed():
                            state, inventory_selected = self._handle_fusion_confirm_action("fusion_confirm_no", game, inventory_selected)
                        elif self._menu_left_pressed() or self._menu_right_pressed() or self._menu_up_pressed() or self._menu_down_pressed():
                            fusion_confirm_selected = 1 - fusion_confirm_selected
                        elif self._menu_confirm_pressed():
                            action = "fusion_confirm_yes" if fusion_confirm_selected == 0 else "fusion_confirm_no"
                            state, inventory_selected = self._handle_fusion_confirm_action(action, game, inventory_selected)

                    elif state == "stat_shop":
                        if self._menu_back_pressed() or self._action_pressed(event, controls, "stat_shop"):
                            state = stat_shop_return_state
                        elif not game.stat_shop_offers:
                            if (self._menu_confirm_pressed() or self._menu_y_pressed()) and game.stat_shop_unlocked():
                                game.roll_stat_shop()
                        else:
                            stat_shop_selected = min(stat_shop_selected, len(game.stat_shop_offers) - 1)
                            if self._menu_left_pressed():
                                stat_shop_selected = (stat_shop_selected - 1) % len(game.stat_shop_offers)
                            elif self._menu_right_pressed():
                                stat_shop_selected = (stat_shop_selected + 1) % len(game.stat_shop_offers)
                            elif self._menu_confirm_pressed():
                                game.purchase_stat_shop_offer(stat_shop_selected)
                                stat_shop_selected = min(stat_shop_selected, max(0, len(game.stat_shop_offers) - 1))
                            elif self._menu_x_pressed():
                                game.reroll_stat_shop_offer(stat_shop_selected)

                    elif state == "constructions":
                        entry_count = len(ui.construction_catalog())
                        if self._menu_back_pressed():
                            state = "paused"
                        elif self._menu_up_pressed():
                            construction_selected = (construction_selected - 1) % entry_count
                        elif self._menu_down_pressed():
                            construction_selected = (construction_selected + 1) % entry_count

                    elif state == "skills":
                        keys = list(game.get_player(game.menu_player_index).passives.keys())
                        if self._menu_back_pressed() or self._action_pressed(event, controls, "skills"):
                            state = skills_return_state
                        elif game.multiplayer and self._menu_y_pressed():
                            game.menu_player_index = 1 - game.menu_player_index
                            skill_selected = 0
                        elif keys:
                            if self._menu_up_pressed():
                                skill_selected = (skill_selected - 1) % len(keys)
                            elif self._menu_down_pressed():
                                skill_selected = (skill_selected + 1) % len(keys)
                            elif self._menu_confirm_pressed() or self._menu_x_pressed():
                                skill_selected = min(skill_selected, len(keys) - 1)
                                game.upgrade_skill(keys[skill_selected])

                    elif state == "game_over":
                        go_options = [("Reiniciar", "restart"), ("Trocar Personagem", "change_character"), ("Voltar ao Menu", "menu"), ("Fechar", "quit")]
                        if self._menu_up_pressed():
                            game_over_selected = (game_over_selected - 1) % len(go_options)
                        elif self._menu_down_pressed():
                            game_over_selected = (game_over_selected + 1) % len(go_options)
                        elif self._menu_confirm_pressed():
                            go_action = go_options[game_over_selected][1]
                            if go_action == "restart":
                                game.restart()
                                state = "playing"
                            elif go_action == "change_character":
                                character_selected = self._current_character_index(game)
                                character_selected_2 = self._current_character_index(game, 1)
                                multiplayer_selected = game.multiplayer
                                character_select_player = 0
                                character_cancel_state = "game_over"
                                state = "character_select"
                            elif go_action == "menu":
                                running = False
                                return_action = "menu"
                            elif go_action == "quit":
                                running = False
                                return_action = "quit"
                        elif self._menu_back_pressed():
                            running = False
                            return_action = "menu"

                elif event.type in (pygame.KEYUP, pygame.MOUSEBUTTONUP, pygame.JOYBUTTONUP):
                    if self._action_released(event, controls, "special") and special_holding[0]:
                        if state == "playing" and not special_hold_triggered[0]:
                            game.try_special(aim_world)
                        special_holding[0] = False
                        special_hold_time[0] = 0.0
                        special_hold_triggered[0] = False
                        special_combo_checked[0] = False

                elif event.type == pygame.KEYDOWN:
                    if state == "settings":
                        if capture_binding:
                            action_key, slot = capture_binding
                            controls[action_key][slot] = self._binding_from_event(event)
                            capture_binding = None
                            continue
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = settings_return_state
                        elif event.key == pygame.K_UP:
                            settings_selected = (settings_selected - 1) % len(CONTROL_ACTIONS)
                        elif event.key == pygame.K_DOWN:
                            settings_selected = (settings_selected + 1) % len(CONTROL_ACTIONS)
                        elif event.key == pygame.K_LEFT:
                            settings_slot = (settings_slot - 1) % BINDING_SLOT_COUNT
                        elif event.key in (pygame.K_RIGHT, pygame.K_TAB):
                            settings_slot = (settings_slot + 1) % BINDING_SLOT_COUNT
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action_key = CONTROL_ACTIONS[settings_selected][0]
                            capture_binding = (action_key, settings_slot)
                        elif event.key == pygame.K_r:
                            controls = self._default_bindings()
                            if self._joystick_count():
                                self._apply_default_joystick_bindings(controls)
                            capture_binding = None
                        elif self._action_pressed(event, controls, "fullscreen"):
                            fullscreen = not fullscreen
                            screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if self._action_pressed(event, controls, "fullscreen"):
                        fullscreen = not fullscreen
                        screen, fullscreen = self._set_display_mode(fullscreen, ui)
                        continue

                    if state == "start":
                        if event.key == pygame.K_UP:
                            start_selected = (start_selected - 1) % len(START_OPTIONS)
                        elif event.key == pygame.K_DOWN:
                            start_selected = (start_selected + 1) % len(START_OPTIONS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action = START_OPTIONS[start_selected][1]
                            if action == "character_select":
                                state = "mode_select" if self._joystick_count() else "character_select"
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                multiplayer_selected = False
                                character_cancel_state = "start"
                            elif action == "commands":
                                commands_return_state = "start"
                                state = "commands"
                            elif action == "settings":
                                settings_return_state = "start"
                                state = "settings"
                            elif action == "menu":
                                running = False
                                return_action = "menu"
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            return_action = "menu"
                        elif event.key == pygame.K_c:
                            commands_return_state = "start"
                            state = "commands"
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "start"
                            state = "settings"

                    elif state == "mode_select":
                        if event.key == pygame.K_UP:
                            mode_selected = (mode_selected - 1) % 3
                        elif event.key == pygame.K_DOWN:
                            mode_selected = (mode_selected + 1) % 3
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if mode_selected == 2:
                                state = "start"
                            else:
                                multiplayer_selected = mode_selected == 1
                                character_selected = 0
                                character_selected_2 = 0
                                character_select_player = 0
                                character_cancel_state = "mode_select"
                                state = "character_select"
                        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = "start"

                    elif state == "character_select":
                        if event.key == pygame.K_LEFT:
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 - 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected - 1) % len(CHARACTERS)
                        elif event.key == pygame.K_RIGHT:
                            if multiplayer_selected and character_select_player == 1:
                                character_selected_2 = (character_selected_2 + 1) % len(CHARACTERS)
                            else:
                                character_selected = (character_selected + 1) % len(CHARACTERS)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            if multiplayer_selected and character_select_player == 0:
                                character_select_player = 1
                            else:
                                char_class = list(CHARACTERS.keys())[character_selected]
                                char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                                game = GameLogic(char_class, char_class_2, multiplayer_selected)
                                state = "playing"
                        elif event.key == pygame.K_ESCAPE:
                            if multiplayer_selected and character_select_player == 1:
                                character_select_player = 0
                            else:
                                state = character_cancel_state

                    elif state == "playing":
                        if self._action_pressed(event, controls, "pause"):
                            state = "paused"
                            pause_selected = 0
                        elif self._action_pressed(event, controls, "settings"):
                            settings_return_state = "playing"
                            state = "settings"
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "toggle_weapon"):
                            game.toggle_mode()
                        elif self._action_pressed(event, controls, "dash"):
                            game.try_dash(aim_world)
                        elif self._action_pressed(event, controls, "special"):
                            special_holding[0] = True
                            special_hold_time[0] = 0.0
                            special_hold_triggered[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "inventory"):
                            state = "inventory"
                            game.menu_player_index = 0
                            inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(0).item_list()) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "skills"):
                            skills_return_state = "playing"
                            state = "skills"
                            game.menu_player_index = 0
                            skill_selected = min(skill_selected, max(0, len(game.get_player(0).passives) - 1))
                            special_holding[0] = False
                            special_combo_checked[0] = False
                        elif self._action_pressed(event, controls, "stat_shop"):
                            stat_shop_return_state = "playing"
                            state = "stat_shop"
                            stat_shop_selected = 0
                            special_holding[0] = False
                            special_combo_checked[0] = False

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
                            if action == "settings":
                                settings_return_state = "paused"
                                state = "settings"
                                capture_binding = None
                                continue
                            if action == "skills":
                                skills_return_state = "paused"
                                state = "skills"
                                skill_selected = min(skill_selected, max(0, len(game.get_player(game.menu_player_index).passives) - 1))
                                continue
                            if action == "stat_shop":
                                stat_shop_return_state = "paused"
                                state = "stat_shop"
                                stat_shop_selected = 0
                                continue
                            if action == "change_character":
                                character_selected = self._current_character_index(game)
                                character_selected_2 = self._current_character_index(game, 1)
                                multiplayer_selected = game.multiplayer
                                character_select_player = 0
                                character_cancel_state = "paused"
                                state = "character_select"
                                continue
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

                    elif state == "stat_shop":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE) or self._action_pressed(event, controls, "stat_shop"):
                            state = stat_shop_return_state
                        elif event.key == pygame.K_r and game.stat_shop_unlocked() and not game.stat_shop_offers:
                            game.roll_stat_shop()
                        elif event.key in (pygame.K_1, pygame.K_KP1) and game.stat_shop_offers:
                            game.purchase_stat_shop_offer(0)
                        elif event.key in (pygame.K_2, pygame.K_KP2) and len(game.stat_shop_offers) > 1:
                            game.purchase_stat_shop_offer(1)
                        elif event.key in (pygame.K_3, pygame.K_KP3) and len(game.stat_shop_offers) > 2:
                            game.purchase_stat_shop_offer(2)

                    elif state == "constructions":
                        entry_count = len(ui.construction_catalog())
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                            state = "paused"
                        elif event.key == pygame.K_UP:
                            construction_selected = (construction_selected - 1) % entry_count
                        elif event.key == pygame.K_DOWN:
                            construction_selected = (construction_selected + 1) % entry_count
                        elif event.key == pygame.K_PAGEUP:
                            construction_selected = max(0, construction_selected - 5)
                        elif event.key == pygame.K_PAGEDOWN:
                            construction_selected = min(entry_count - 1, construction_selected + 5)
                        elif event.key == pygame.K_HOME:
                            construction_selected = 0
                        elif event.key == pygame.K_END:
                            construction_selected = entry_count - 1

                    elif state == "skills":
                        keys = list(game.get_player(game.menu_player_index).passives.keys())
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_k):
                            state = skills_return_state
                        elif game.multiplayer and event.key == pygame.K_p:
                            game.menu_player_index = 1 - game.menu_player_index
                            skill_selected = 0
                        elif keys:
                            if event.key == pygame.K_UP:
                                skill_selected = (skill_selected - 1) % len(keys)
                            elif event.key == pygame.K_DOWN:
                                skill_selected = (skill_selected + 1) % len(keys)
                            elif event.key == pygame.K_PAGEUP:
                                skill_selected = max(0, skill_selected - 5)
                            elif event.key == pygame.K_PAGEDOWN:
                                skill_selected = min(len(keys) - 1, skill_selected + 5)
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_u):
                                game.upgrade_skill(keys[skill_selected])

                    elif state == "upgrade":
                        if event.key == pygame.K_UP:
                            upgrade_selected = (upgrade_selected - 1) % len(game.upgrade_choices)
                        elif event.key == pygame.K_DOWN:
                            upgrade_selected = (upgrade_selected + 1) % len(game.upgrade_choices)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            game.apply_upgrade(game.upgrade_choices[upgrade_selected], game.level_up_player_index)
                            upgrade_selected = 0
                            state = "playing"

                    elif state == "inventory":
                        inv = game.get_inventory(game.menu_player_index)
                        raw_items = inv.item_list()
                        active_items = [item for item in raw_items if inv.is_active(item.key)]
                        reserve_items = [item for item in raw_items if not inv.is_active(item.key)]
                        items = active_items + reserve_items

                        if event.key in (pygame.K_ESCAPE, pygame.K_i, pygame.K_TAB):
                            state = "playing"
                        elif game.multiplayer and event.key == pygame.K_p:
                            game.menu_player_index = 1 - game.menu_player_index
                            inventory_selected = 0
                        elif items:
                            if event.key == pygame.K_UP:
                                inventory_selected -= 5
                            elif event.key == pygame.K_DOWN:
                                inventory_selected += 5
                            elif event.key == pygame.K_LEFT:
                                inventory_selected -= 1
                            elif event.key == pygame.K_RIGHT:
                                inventory_selected += 1
                            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
                                game.toggle_inventory_item(items[inventory_selected].key)
                            elif event.key == pygame.K_u:
                                game.upgrade_inventory_item(items[inventory_selected].key)
                            elif event.key == pygame.K_f:
                                game.mark_or_fuse_item(items[inventory_selected].key)
                                if game.has_pending_fusion():
                                    state = "fusion_confirm"
                                    fusion_confirm_selected = 1

                            inventory_selected = max(0, min(inventory_selected, len(items) - 1))

                    elif state == "fusion_confirm":
                        if event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_n):
                            state, inventory_selected = self._handle_fusion_confirm_action("fusion_confirm_no", game, inventory_selected)
                        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                            fusion_confirm_selected = 1 - fusion_confirm_selected
                        elif event.key in (pygame.K_y,):
                            state, inventory_selected = self._handle_fusion_confirm_action("fusion_confirm_yes", game, inventory_selected)
                        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                            action = "fusion_confirm_yes" if fusion_confirm_selected == 0 else "fusion_confirm_no"
                            state, inventory_selected = self._handle_fusion_confirm_action(action, game, inventory_selected)

                    elif state == "game_over":
                        if event.key == pygame.K_r:
                            game.restart()
                            state = "playing"
                        elif event.key in (pygame.K_c, pygame.K_t):
                            character_selected = self._current_character_index(game)
                            character_selected_2 = self._current_character_index(game, 1)
                            multiplayer_selected = game.multiplayer
                            character_select_player = 0
                            character_cancel_state = "game_over"
                            state = "character_select"
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                            return_action = "menu"

            if state == "playing":
                if special_holding[0]:
                    if not self._action_currently_active(controls, "special"):
                        if not special_hold_triggered[0]:
                            game.try_special(aim_world, 0)
                        special_holding[0] = False
                        special_hold_time[0] = 0.0
                        special_hold_triggered[0] = False
                        special_combo_checked[0] = False
                    else:
                        special_hold_time[0] += dt
                        if not special_combo_checked[0] and special_hold_time[0] >= SPECIAL_COMBO_HOLD_SECONDS:
                            special_combo_checked[0] = True
                            if game.try_combo_special(aim_world, 0):
                                special_hold_triggered[0] = True
                                special_holding[0] = False
                p1_controls = self._player_one_controls(controls) if game.multiplayer else controls
                move = self._movement_vector(p1_controls)
                move_2 = self._joystick_movement_vector() if game.multiplayer else None
                game.update(dt, move, aim_world, move_2, p2_aim_world)
                if game.level_up_pending:
                    state = "upgrade"
                    upgrade_selected = 0
                elif game.game_over:
                    state = "game_over"
                    game_over_selected = 0
                ui.render_game(game, aim_pos, flip=False, aim_from_joystick=aim_mode == "joystick", p2_aim_pos=p2_aim_screen)
                button_rects = []
            elif state == "start":
                button_rects = ui.render_start(mouse_pos, start_selected)
            elif state == "mode_select":
                button_rects = ui.render_mode_select(mouse_pos, mode_selected, self._joystick_count())
            elif state == "character_select":
                selected_index = character_selected_2 if multiplayer_selected and character_select_player == 1 else character_selected
                char_class = list(CHARACTERS.keys())[selected_index]
                char_class_2 = list(CHARACTERS.keys())[character_selected_2]
                button_rects = ui.render_character_select(
                    char_class,
                    mouse_pos,
                    multiplayer_selected,
                    char_class_2,
                    character_select_player,
                )
            elif state == "paused":
                button_rects = ui.render_pause(game, PAUSE_OPTIONS, pause_selected, mouse_pos)
            elif state == "commands":
                button_rects = ui.render_commands(mouse_pos, self._command_lines(controls))
            elif state == "settings":
                settings_selected = min(settings_selected, len(CONTROL_ACTIONS) - 1)
                button_rects = ui.render_settings(
                    self._control_rows(controls),
                    settings_selected,
                    settings_slot,
                    capture_binding,
                    fullscreen,
                    self.control_preference,
                    self._joystick_count(),
                    mouse_pos,
                )
            elif state == "stat_shop":
                button_rects = ui.render_stat_shop(game, mouse_pos)
            elif state == "constructions":
                construction_selected = min(construction_selected, max(0, len(ui.construction_catalog()) - 1))
                button_rects = ui.render_constructions(game, construction_selected, mouse_pos)
            elif state == "skills":
                skill_selected = min(skill_selected, max(0, len(game.get_player(game.menu_player_index).passives) - 1))
                button_rects = ui.render_skills(game, skill_selected, mouse_pos)
            elif state == "upgrade":
                button_rects = ui.render_upgrade(game, upgrade_selected, mouse_pos)
            elif state == "inventory":
                inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(game.menu_player_index).item_list()) - 1))
                button_rects = ui.render_inventory(game, inventory_selected, mouse_pos)
            elif state == "fusion_confirm":
                inventory_selected = min(inventory_selected, max(0, len(game.get_inventory(game.menu_player_index).item_list()) - 1))
                button_rects = ui.render_fusion_confirm(game, inventory_selected, fusion_confirm_selected, mouse_pos)
            elif state == "game_over":
                button_rects = ui.render_game_over(game, mouse_pos, game_over_selected)

            # Final Smoothscale Render
            if fw != vw or fh != vh:
                pygame.transform.smoothscale(self.virtual_screen, (fw, fh), final_screen)
            else:
                final_screen.blit(self.virtual_screen, (0, 0))
            pygame.display.flip()

        pygame.quit()
        return return_action

    def _default_bindings(self):
        return {action: list(bindings) for action, bindings in DEFAULT_BINDINGS.items()}

    def _poll_events(self, game):
        try:
            return pygame.event.get()
        except (KeyError, SystemError, pygame.error):
            self._recover_joystick_state()
            game.message = "Controle desconectado: entrada reinicializada."
            return []

    def _recover_joystick_state(self):
        self.joysticks = {}
        self._joystick_axis_active = {}
        self._joystick_hat_active = {}
        try:
            pygame.event.clear()
        except (KeyError, SystemError, pygame.error):
            pass
        try:
            pygame.joystick.quit()
        except pygame.error:
            pass
        try:
            pygame.joystick.init()
            self._init_joysticks()
        except pygame.error:
            self.joysticks = {}

    def _init_joysticks(self):
        self.joysticks = {}
        for index in range(pygame.joystick.get_count()):
            self._add_joystick(index)

    def _apply_default_joystick_bindings(self, controls):
        for action, binding in JOYSTICK_DEFAULT_BINDINGS.items():
            bindings = controls.setdefault(action, [])
            while len(bindings) < BINDING_SLOT_COUNT:
                bindings.append(None)
            if binding not in bindings and bindings[BINDING_SLOT_COUNT - 1] is None:
                bindings[BINDING_SLOT_COUNT - 1] = binding

    def _add_joystick(self, device_index):
        try:
            joystick = pygame.joystick.Joystick(device_index)
            joystick.init()
            instance_id = joystick.get_instance_id()
            self.joysticks[instance_id] = joystick
        except pygame.error:
            return

    def _remove_joystick(self, instance_id):
        joystick = self.joysticks.pop(instance_id, None)
        self._joystick_axis_active = {
            key: binding for key, binding in self._joystick_axis_active.items() if key[0] != instance_id
        }
        self._joystick_hat_active = {
            key: bindings for key, bindings in self._joystick_hat_active.items() if key[0] != instance_id
        }
        if joystick is not None:
            try:
                joystick.quit()
            except pygame.error:
                pass

    def _joystick_count(self):
        return len(getattr(self, "joysticks", {}))

    def _joystick_status_message(self):
        count = self._joystick_count()
        if count == 1:
            return "Controle detectado: Single-Player ou Coop Local disponiveis."
        if count > 1:
            return f"{count} controles detectados: Coop Local disponivel."
        return "Controle desconectado."

    def _prepare_input_event(self, event):
        self._event_pressed_bindings = []
        self._event_released_bindings = []

        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN):
            binding = self._binding_from_event(event)
            if binding is not None:
                self._event_pressed_bindings.append(binding)
            return

        if event.type in (pygame.KEYUP, pygame.MOUSEBUTTONUP, pygame.JOYBUTTONUP):
            binding = self._binding_from_event(event)
            if binding is not None:
                self._event_released_bindings.append(binding)
            return

        if event.type == pygame.JOYAXISMOTION:
            device_id = self._joystick_event_device_id(event)
            key = (device_id, event.axis)
            previous = self._joystick_axis_active.get(key)
            current = self._axis_binding(event.axis, event.value)
            if previous != current:
                if previous is not None:
                    self._event_released_bindings.append(previous)
                if current is not None:
                    self._event_pressed_bindings.append(current)
                    self._joystick_axis_active[key] = current
                else:
                    self._joystick_axis_active.pop(key, None)
            return

        if event.type == pygame.JOYHATMOTION:
            device_id = self._joystick_event_device_id(event)
            key = (device_id, event.hat)
            previous = self._joystick_hat_active.get(key, set())
            current = set(self._hat_bindings(event.hat, event.value))
            for binding in previous - current:
                self._event_released_bindings.append(binding)
            for binding in current - previous:
                self._event_pressed_bindings.append(binding)
            if current:
                self._joystick_hat_active[key] = current
            else:
                self._joystick_hat_active.pop(key, None)

    def _joystick_event_device_id(self, event):
        return getattr(event, "instance_id", getattr(event, "joy", 0))

    def _axis_binding(self, axis, value):
        if value <= -JOYSTICK_DEADZONE:
            return ("joy_axis", axis, -1)
        if value >= JOYSTICK_DEADZONE:
            return ("joy_axis", axis, 1)
        return None

    def _hat_bindings(self, hat, value):
        x, y = value
        bindings = []
        if x < 0:
            bindings.append(("joy_hat", hat, -1, 0))
        elif x > 0:
            bindings.append(("joy_hat", hat, 1, 0))
        if y < 0:
            bindings.append(("joy_hat", hat, 0, -1))
        elif y > 0:
            bindings.append(("joy_hat", hat, 0, 1))
        return bindings

    def _pressed_has(self, *bindings):
        return any(binding in self._event_pressed_bindings for binding in bindings)

    def _menu_up_pressed(self):
        return self._pressed_has(("joy_axis", 1, -1), ("joy_hat", 0, 0, 1), ("key", pygame.K_UP), ("key", pygame.K_w))

    def _menu_down_pressed(self):
        return self._pressed_has(("joy_axis", 1, 1), ("joy_hat", 0, 0, -1), ("key", pygame.K_DOWN), ("key", pygame.K_s))

    def _menu_left_pressed(self):
        return self._pressed_has(("joy_axis", 0, -1), ("joy_hat", 0, -1, 0), ("key", pygame.K_LEFT), ("key", pygame.K_a))

    def _menu_right_pressed(self):
        return self._pressed_has(("joy_axis", 0, 1), ("joy_hat", 0, 1, 0), ("key", pygame.K_RIGHT), ("key", pygame.K_d))

    def _menu_confirm_pressed(self):
        return self._pressed_has(("joy_button", 0), ("joy_button", 7), ("key", pygame.K_RETURN), ("key", pygame.K_SPACE))

    def _menu_back_pressed(self):
        return self._pressed_has(("joy_button", 1), ("key", pygame.K_ESCAPE), ("key", pygame.K_BACKSPACE))

    def _menu_x_pressed(self):
        return self._pressed_has(("joy_button", 2), ("key", pygame.K_x), ("key", pygame.K_u))

    def _menu_y_pressed(self):
        return self._pressed_has(("joy_button", 3), ("key", pygame.K_y), ("key", pygame.K_TAB))

    def _joystick_aim_vector(self):
        best = Vector2()
        best_strength = JOYSTICK_AIM_DEADZONE * JOYSTICK_AIM_DEADZONE
        for joystick in getattr(self, "joysticks", {}).values():
            try:
                pair = self._right_stick_axes(joystick)
                if pair is None:
                    continue
                x_axis, y_axis = pair
                vector = Vector2(joystick.get_axis(x_axis), joystick.get_axis(y_axis))
            except (KeyError, IndexError, pygame.error):
                continue
            strength = vector.length_squared()
            if strength > best_strength:
                best = vector
                best_strength = strength
        if best.length_squared() > 1:
            best = best.normalize()
        return best

    def _right_stick_axes(self, joystick):
        try:
            axis_count = joystick.get_numaxes()
        except pygame.error:
            return None
        if axis_count >= 6:
            return 2, 3
        if axis_count >= 5:
            return 3, 4
        if axis_count >= 4:
            return 2, 3
        return None

    def _aim_screen_pos(self, game, direction):
        return self._aim_screen_pos_for(game, game.player, direction)

    def _aim_screen_pos_for(self, game, player, direction):
        if direction.length_squared() <= 0:
            direction = Vector2(player.last_move_dir)
        if direction.length_squared() <= 0:
            direction = Vector2(1, 0)
        player_screen = Vector2(
            player.pos.x - game.camera.x,
            player.pos.y - game.camera.y,
        )
        aim_pos = player_screen + direction.normalize() * JOYSTICK_AIM_DISTANCE
        margin = 18
        aim_pos.x = max(margin, min(SCREEN_WIDTH - margin, aim_pos.x))
        aim_pos.y = max(margin, min(SCREEN_HEIGHT - margin, aim_pos.y))
        return int(aim_pos.x), int(aim_pos.y)

    def _set_display_mode(self, fullscreen, ui):
        attempts = []
        if fullscreen:
            scaled_flag = getattr(pygame, "SCALED", 0)
            if scaled_flag:
                attempts.append((pygame.FULLSCREEN | scaled_flag, True))
            attempts.append((pygame.FULLSCREEN, True))
        else:
            attempts.append((0, False))

        attempts.append((0, False))
        seen = set()
        for flags, applied_fullscreen in attempts:
            if flags in seen:
                continue
            seen.add(flags)
            try:
                if (flags & pygame.FULLSCREEN) and not (flags & getattr(pygame, "SCALED", 0)):
                    screen = pygame.display.set_mode((0, 0), flags)
                else:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
                ui.screen = screen
                return screen, applied_fullscreen
            except pygame.error:
                continue

        return ui.screen, False

    def _binding_from_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            return ("key", event.key)
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return ("mouse", event.button)
        if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            return ("joy_button", event.button)
        if event.type == pygame.JOYAXISMOTION:
            return self._axis_binding(event.axis, event.value)
        if event.type == pygame.JOYHATMOTION:
            bindings = self._hat_bindings(event.hat, event.value)
            return bindings[0] if bindings else None
        return None

    def _action_pressed(self, event, controls, action):
        return any(binding in controls.get(action, []) for binding in self._event_pressed_bindings)

    def _action_released(self, event, controls, action):
        return any(binding in controls.get(action, []) for binding in self._event_released_bindings)

    def _action_currently_active(self, controls, action):
        keys = pygame.key.get_pressed()
        try:
            mouse_buttons = pygame.mouse.get_pressed(5)
        except TypeError:
            mouse_buttons = pygame.mouse.get_pressed()
        return any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get(action, []))

    def _binding_active(self, binding, keys, mouse_buttons):
        if binding is None:
            return False
        source = binding[0]
        code = binding[1] if len(binding) > 1 else None
        if source == "key":
            try:
                return bool(keys[code])
            except (IndexError, KeyError):
                return False
        if source == "mouse":
            index = code - 1
            return 0 <= index < len(mouse_buttons) and bool(mouse_buttons[index])
        if source == "joy_button":
            for joystick in getattr(self, "joysticks", {}).values():
                try:
                    if code < joystick.get_numbuttons() and joystick.get_button(code):
                        return True
                except pygame.error:
                    continue
            return False
        if source == "joy_axis":
            axis, direction = binding[1], binding[2]
            for joystick in getattr(self, "joysticks", {}).values():
                try:
                    if axis >= joystick.get_numaxes():
                        continue
                    value = joystick.get_axis(axis)
                    if direction < 0 and value <= -JOYSTICK_DEADZONE:
                        return True
                    if direction > 0 and value >= JOYSTICK_DEADZONE:
                        return True
                except pygame.error:
                    continue
            return False
        if source == "joy_hat":
            hat, x_dir, y_dir = binding[1], binding[2], binding[3]
            for joystick in getattr(self, "joysticks", {}).values():
                try:
                    if hat >= joystick.get_numhats():
                        continue
                    x, y = joystick.get_hat(hat)
                    if x_dir and x == x_dir:
                        return True
                    if y_dir and y == y_dir:
                        return True
                except pygame.error:
                    continue
            return False
        return False

    def _control_index(self, action):
        for index, (action_key, _label) in enumerate(CONTROL_ACTIONS):
            if action_key == action:
                return index
        return 0

    def _binding_label(self, binding):
        if binding is None:
            return "Nao definido"
        source = binding[0]
        code = binding[1] if len(binding) > 1 else None
        if source == "mouse":
            names = {
                1: "Mouse esquerdo",
                2: "Mouse meio",
                3: "Mouse direito",
                4: "Roda cima",
                5: "Roda baixo",
            }
            return names.get(code, f"Mouse {code}")
        if source == "joy_button":
            xbox_buttons = {
                0: "Controle A",
                1: "Controle B",
                2: "Controle X",
                3: "Controle Y",
                4: "LB",
                5: "RB",
                6: "Back",
                7: "Start",
                8: "L3",
                9: "R3",
                10: "Guide",
            }
            return xbox_buttons.get(code, f"Controle B{code}")
        if source == "joy_axis":
            axis, direction = binding[1], binding[2]
            side = "neg." if direction < 0 else "pos."
            return f"Analogico {axis} {side}"
        if source == "joy_hat":
            hat, x_dir, y_dir = binding[1], binding[2], binding[3]
            if y_dir > 0:
                side = "cima"
            elif y_dir < 0:
                side = "baixo"
            elif x_dir < 0:
                side = "esq."
            else:
                side = "dir."
            return f"D-pad {hat} {side}"

        key_names = {
            pygame.K_ESCAPE: "Esc",
            pygame.K_SPACE: "Espaco",
            pygame.K_TAB: "Tab",
            pygame.K_RETURN: "Enter",
            pygame.K_KP_ENTER: "Enter num.",
            pygame.K_UP: "Seta cima",
            pygame.K_DOWN: "Seta baixo",
            pygame.K_LEFT: "Seta esq.",
            pygame.K_RIGHT: "Seta dir.",
            pygame.K_LSHIFT: "Shift esq.",
            pygame.K_RSHIFT: "Shift dir.",
            pygame.K_BACKSPACE: "Backspace",
            pygame.K_F11: "F11",
        }
        if code in key_names:
            return key_names[code]
        name = pygame.key.name(code)
        return name.upper() if len(name) == 1 else name.title()

    def _binding_combo(self, controls, action):
        labels = [self._binding_label(binding) for binding in controls.get(action, []) if binding is not None]
        return " / ".join(labels) if labels else "Nao definido"

    def _control_rows(self, controls):
        rows = []
        for action, label in CONTROL_ACTIONS:
            bindings = list(controls.get(action, []))
            while len(bindings) < BINDING_SLOT_COUNT:
                bindings.append(None)
            rows.append({
                "action": action,
                "label": label,
                "bindings": [self._binding_label(bindings[slot]) for slot in range(BINDING_SLOT_COUNT)],
            })
        return rows

    def _command_lines(self, controls):
        return [
            f"Mover cima/baixo: {self._binding_combo(controls, 'move_up')} | {self._binding_combo(controls, 'move_down')}",
            f"Mover esquerda/direita: {self._binding_combo(controls, 'move_left')} | {self._binding_combo(controls, 'move_right')}",
            "Mouse: direcao dos tiros e golpes automaticos",
            f"{self._binding_combo(controls, 'toggle_weapon')}: alternar entre projetil e espada",
            f"{self._binding_combo(controls, 'dash')}: dash com recarga e invulnerabilidade curta",
            f"{self._binding_combo(controls, 'special')}: especial; segure para combo com as duas barras cheias",
            f"{self._binding_combo(controls, 'inventory')}: abre inventario de itens passivos",
            f"{self._binding_combo(controls, 'skills')}: abre Gerenciamento de Skills",
            f"{self._binding_combo(controls, 'stat_shop')}: abre Loja de Status",
            f"{self._binding_combo(controls, 'settings')}: configuracoes da sessao",
            f"{self._binding_combo(controls, 'fullscreen')}: alternar tela cheia",
            "Controle Xbox: analogico esquerdo move, A confirma/dash, B volta, LB loja, RB skills, Start pausa.",
            "Joystick: remapeie botoes, eixos e D-pad em Configuracoes.",
            "Armas de distancia usam pente e reserva de municao.",
            "No Game Over, C ou T abre a troca de personagem.",
        ]

    def _movement_vector(self, controls):
        keys = pygame.key.get_pressed()
        try:
            mouse_buttons = pygame.mouse.get_pressed(5)
        except TypeError:
            mouse_buttons = pygame.mouse.get_pressed()
        x = 0
        y = 0
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_left", [])):
            x -= 1
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_right", [])):
            x += 1
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_up", [])):
            y -= 1
        if any(self._binding_active(binding, keys, mouse_buttons) for binding in controls.get("move_down", [])):
            y += 1
        return Vector2(x, y)

    def _player_one_controls(self, controls):
        filtered = {}
        for action, bindings in controls.items():
            filtered[action] = [binding for binding in bindings if binding is None or binding[0] in ("key", "mouse")]
        return filtered

    def _joystick_movement_vector(self):
        x = 0.0
        y = 0.0
        for joystick in getattr(self, "joysticks", {}).values():
            try:
                if joystick.get_numaxes() >= 2:
                    x = joystick.get_axis(0)
                    y = joystick.get_axis(1)
                    break
            except pygame.error:
                continue
        if abs(x) < JOYSTICK_AIM_DEADZONE:
            x = 0
        if abs(y) < JOYSTICK_AIM_DEADZONE:
            y = 0
        return Vector2(x, y)

    def _current_character_index(self, game, player_index=0):
        keys = list(CHARACTERS.keys())
        player = game.get_player(player_index)
        if player.char_class in keys:
            return keys.index(player.char_class)
        return 0

    def _handle_action(self, action, state, game, running, return_action, pause_selected, upgrade_selected):
        if action == "start":
            game.restart()
            state = "playing"
        elif action == "commands":
            state = "commands"
        elif action == "settings":
            state = "settings"
        elif action == "constructions":
            state = "constructions"
        elif action == "skills":
            state = "skills"
        elif action == "stat_shop":
            state = "stat_shop"
        elif action == "change_character":
            state = "character_select"
        elif action == "inventory":
            state = "inventory"
            game.menu_player_index = 0
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
            game.apply_upgrade(action, game.level_up_player_index)
            upgrade_selected = 0
            state = "playing"
        return state, running, return_action, pause_selected, upgrade_selected

    def _handle_inventory_action(self, action, state, game, selected):
        inv = game.get_inventory(game.menu_player_index)
        raw_items = inv.item_list()
        active_items = [item for item in raw_items if inv.is_active(item.key)]
        reserve_items = [item for item in raw_items if not inv.is_active(item.key)]
        items = active_items + reserve_items
        if action == "resume":
            return "playing", selected
        if action.startswith("item_select:"):
            return state, int(action.split(":", 1)[1])
        if not items:
            return state, selected

        selected = min(selected, len(items) - 1)
        key = items[selected].key
        if action == "item_toggle":
            game.toggle_inventory_item(key)
        elif action == "item_upgrade":
            game.upgrade_inventory_item(key)
        elif action == "item_fuse":
            game.mark_or_fuse_item(key)
            if game.has_pending_fusion():
                return "fusion_confirm", selected
            selected = min(selected, max(0, len(inv.item_list()) - 1))
        return state, selected

    def _handle_stat_shop_action(self, action, game, return_state):
        if action == "stat_shop_back":
            return return_state
        if action == "stat_shop_roll":
            game.roll_stat_shop()
            return "stat_shop"
        if action.startswith("stat_shop_buy:"):
            game.purchase_stat_shop_offer(int(action.split(":", 1)[1]))
            return "stat_shop"
        if action.startswith("stat_shop_reroll:"):
            game.reroll_stat_shop_offer(int(action.split(":", 1)[1]))
            return "stat_shop"
        return "stat_shop"

    def _handle_construction_action(self, action, selected):
        if action == "constructions_back":
            return "paused", selected
        if action.startswith("construction_select:"):
            return "constructions", int(action.split(":", 1)[1])
        return "constructions", selected

    def _handle_skill_action(self, action, state, game, selected, return_state):
        keys = list(game.get_player(game.menu_player_index).passives.keys())
        if action == "skills_back":
            return return_state, selected
        if action.startswith("skill_select:"):
            return state, int(action.split(":", 1)[1])
        if action == "skill_upgrade" and keys:
            selected = min(selected, len(keys) - 1)
            game.upgrade_skill(keys[selected])
        return state, selected

    def _handle_fusion_confirm_action(self, action, game, selected):
        inv = game.get_inventory(game.menu_player_index)
        if action == "fusion_confirm_yes":
            game.confirm_pending_fusion()
        elif action == "fusion_confirm_no":
            game.cancel_pending_fusion()
        selected = min(selected, max(0, len(inv.item_list()) - 1))
        return "inventory", selected


def main():
    app = SobrevivenciaGame()
    app.run()


if __name__ == "__main__":
    main()

import pygame
if __package__:
    from ...data.constants import *
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.presentation.ui_utils import hex_color

class SystemMenus:
    def render_start(self, mouse_pos, selected=0):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        self._center_text("SOBREVIVENCIA", self.font_big, 142, COLORS["text"])
        self._center_text("Top-down shooter/slasher infinito", self.font, 190, COLORS["muted"])
        self._center_text("WASD/analogico move  |  Mouse mira  |  A confirma/dash  |  B volta  |  Start pausa", self.font_small, 232, COLORS["muted"])
        buttons = []
        buttons.append(self._button(410, 300, 280, 48, "Iniciar Jogo", "character_select", mouse_pos, COLORS["xp"], selected == 0))
        buttons.append(self._button(410, 362, 280, 48, "Comandos", "commands", mouse_pos, COLORS["special"], selected == 1))
        buttons.append(self._button(410, 424, 280, 48, "Configuracoes", "settings", mouse_pos, COLORS["upgrade"], selected == 2))
        buttons.append(self._button(410, 486, 280, 48, "Voltar ao Menu", "menu", mouse_pos, COLORS["muted_2"], selected == 3))
        # pygame.display.flip()
        return buttons

    def render_mode_select(self, mouse_pos, selected=0, joystick_count=0):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        self._center_text("MODO DE JOGO", self.font_big, 132, COLORS["text"])
        self._center_text(f"{joystick_count} controle(s) detectado(s)", self.font, 188, COLORS["muted"])
        self._center_text("P1 usa teclado e mouse. P2 usa joystick no cooperativo local.", self.font_small, 224, COLORS["muted"])
        buttons = []
        buttons.append(self._button(410, 302, 280, 48, "Single-Player", "single_player", mouse_pos, COLORS["xp"], selected == 0))
        buttons.append(self._button(410, 364, 280, 48, "Multiplayer", "multiplayer", mouse_pos, COLORS["special"], selected == 1))
        buttons.append(self._button(410, 426, 280, 48, "Voltar", "back", mouse_pos, COLORS["muted_2"], selected == 2))
        # pygame.display.flip()
        return buttons

    def render_character_select(self, char_class, mouse_pos, multiplayer=False, char_class_2=None, active_player=0):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        title = "SELECAO COOP" if multiplayer else "SELECIONE SEU PERSONAGEM"
        self._center_text(title, self.font_title, 80, COLORS["text"])
        if multiplayer:
            self._center_text(f"Turno do Jogador {active_player + 1}. Ambos podem escolher o mesmo personagem.", self.font_small, 112, COLORS["muted"])

        data = CHARACTERS[char_class]
        color = hex_color(data["color"])
        core = hex_color(data["core_color"])

        # draw big icon
        center_x, center_y = SCREEN_WIDTH // 2, 200
        pygame.draw.circle(self.screen, color, (center_x, center_y), 45)
        if data["shape"] == "circle_triangle":
            pts = [(center_x + 25, center_y), (center_x - 15, center_y - 20), (center_x - 15, center_y + 20)]
            pygame.draw.polygon(self.screen, core, pts)
        else:
            pygame.draw.circle(self.screen, core, (center_x, center_y), 15)

        self._center_text(data["name"].upper(), self.font_title, 270, COLORS["upgrade"])
        self._center_text(f"Armas: {data['weapon_1']} / {data['weapon_2']}", self.font, 310, COLORS["text"])
        specials = data.get("specials", {})
        special_text = f"Especiais: {specials.get('weapon_1', data['special'])} / {specials.get('weapon_2', data['special'])}"
        self._center_text(special_text, self.font, 340, COLORS["special"])
        self._center_text(f"Combo: {specials.get('combo', 'Ultimate combinada')}", self.font_small, 366, COLORS["upgrade"])

        passives = list(data["passives"].values())
        start_y = 392
        columns = (145, 570)
        for index, p_data in enumerate(passives):
            col = index % 2
            row = index // 2
            x = columns[col]
            y = start_y + row * 36
            category = p_data.get("category", "Kit")
            title_surf, t_rect = self.font_tiny.render(f"{category.upper()} | {p_data['title']}", hex_color(COLORS["text"]))
            desc_surf, d_rect = self.font_tiny.render(p_data["description"][:58], hex_color(COLORS["muted"]))
            self.screen.blit(title_surf, (x, y))
            self.screen.blit(desc_surf, (x, y + 16))

        if multiplayer and char_class_2:
            p1 = CHARACTERS[char_class]["name"]
            p2 = CHARACTERS[char_class_2]["name"]
            self._center_text(f"P1: {p1}    |    P2: {p2}", self.font_small, 584, COLORS["muted_2"])
        else:
            self._center_text("< Esquerda     Direita >", self.font_small, 585, COLORS["muted_2"])

        buttons = []
        label = "Confirmar P1" if multiplayer and active_player == 0 else "Iniciar Coop" if multiplayer else "Confirmar (Enter)"
        buttons.append(self._button(410, 620, 280, 48, label, "start_game", mouse_pos, COLORS["xp"]))
        # pygame.display.flip()
        return buttons

    def render_pause(self, game, options, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        return self._overlay_menu("PAUSADO", options, selected, mouse_pos)

    def render_game_over(self, game, mouse_pos, selected=0):
        self.render_game(game, mouse_pos, flip=False)
        title = "FIM DA SOBREVIVENCIA"
        options = [("Reiniciar", "restart"), ("Trocar Personagem", "change_character"), ("Voltar ao Menu", "menu"), ("Fechar", "quit")]
        buttons = self._overlay_menu(title, options, selected, mouse_pos, extra=f"Tempo {int(game.time_alive)}s  |  Abates {game.player.kills}  |  Pontos {game.player.score}")

        def draw_build_for_player(p, x_start, y_start, label):
            self._center_text(label, self.font_small, y_start, COLORS["muted_2"])
            inv = game.get_inventory(p.player_index)
            active_items = [item for item in inv.item_list() if inv.is_active(item.key)]
            # Itens
            for i in range(5):
                slot_rect = pygame.Rect(x_start + i * 44 - (5 * 44) // 2 + 22, y_start + 24, 38, 38)
                pygame.draw.rect(self.screen, (30, 41, 59), slot_rect, width=1, border_radius=4)
                if i < len(active_items):
                    self._draw_item_icon(active_items[i], slot_rect, game, show_level=True)
            # Passivas
            passives = [(k, v) for k, v in p.passives.items() if v > 0]
            for i in range(10):
                slot_rect = pygame.Rect(x_start + i * 26 - (10 * 26) // 2 + 13, y_start + 70, 22, 22)
                pygame.draw.rect(self.screen, (30, 41, 59), slot_rect, width=1, border_radius=2)
                if i < len(passives):
                    pygame.draw.rect(self.screen, hex_color(COLORS["text"]), slot_rect, border_radius=2)
                    lvl_surf, l_rect = self.font_tiny.render(str(passives[i][1]), hex_color(COLORS["bg"]))
                    self.screen.blit(lvl_surf, (slot_rect.centerx - l_rect.width // 2, slot_rect.centery - l_rect.height // 2))

        if game.multiplayer:
            draw_build_for_player(game.player, SCREEN_WIDTH // 4, 520, f"BUILD J1 ({CHARACTERS[game.player.char_class]['name']})")
            draw_build_for_player(game.player2, (SCREEN_WIDTH // 4) * 3, 520, f"BUILD J2 ({CHARACTERS[game.player2.char_class]['name']})")
        else:
            draw_build_for_player(game.player, SCREEN_WIDTH // 2, 520, f"BUILD FINAL ({CHARACTERS[game.player.char_class]['name']})")

        return buttons

    def render_commands(self, mouse_pos, lines=None):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        self._center_text("COMANDOS", self.font_big, 110, COLORS["text"])
        if lines is None:
            lines = [
                "WASD ou setas: mover pelo mapa infinito",
                "Mouse: direcao dos tiros e golpes automaticos",
                "Q ou Shift: alternar entre projetil e espada",
                "Espaco: dash com recarga e invulnerabilidade curta",
                "E: especial da arma atual; segure E com as duas barras cheias para combo",
                "I ou TAB: abre inventario de itens passivos.",
                "K: abre Gerenciamento de Skills pelo pause/jogo.",
                "L: abre Loja de Status pelo jogo.",
                "Armas de distancia usam pente e reserva de municao.",
                "Ao esvaziar o pente, voce luta corpo a corpo enquanto recarrega.",
                "Colete XP para subir de nivel; a cada 3 niveis vem melhoria grande.",
                "Moedas ativam buffs temporarios; escudos repelem inimigos.",
                "No Game Over, C ou T abre a troca de personagem.",
            ]
        y = 174
        for line in lines:
            self._center_text(line, self.font_small, y, COLORS["muted"])
            y += 28
        buttons = [self._button(410, 620, 280, 48, "Voltar", "back", mouse_pos, COLORS["muted_2"])]
        # pygame.display.flip()
        return buttons

    def render_settings(self, rows, selected, selected_slot, capture_binding, fullscreen, control_pref, joystick_count, mouse_pos):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        self._center_text("CONFIGURACOES", self.font_big, 54, COLORS["text"])
        self._center_text("Clique em um slot ou use setas e Enter. A proxima tecla, mouse ou joystick sera usado nesta sessao.", self.font_small, 104, COLORS["muted"])
        joystick_text = f"Controles detectados: {joystick_count}" if joystick_count else "Nenhum controle detectado."
        self._center_text(joystick_text, self.font_tiny, 122, COLORS["muted"])

        panel = pygame.Rect(86, 132, SCREEN_WIDTH - 172, 462)
        pygame.draw.rect(self.screen, (8, 14, 25), panel, border_radius=8)
        pygame.draw.rect(self.screen, hex_color(COLORS["special"]), panel, width=2, border_radius=8)

        slot_x = [panel.x + 400, panel.x + 558, panel.x + 716]
        slot_w = 142
        self.font_tiny.render_to(self.screen, (panel.x + 22, panel.y + 18), "ACAO", hex_color(COLORS["muted"]))
        self.font_tiny.render_to(self.screen, (slot_x[0] + 30, panel.y + 18), "PRIMARIO", hex_color(COLORS["muted"]))
        self.font_tiny.render_to(self.screen, (slot_x[1] + 56, panel.y + 18), "ALT.", hex_color(COLORS["muted"]))
        self.font_tiny.render_to(self.screen, (slot_x[2] + 36, panel.y + 18), "CONTROLE", hex_color(COLORS["muted"]))

        buttons = []
        y = panel.y + 42
        row_h = 31
        for index, row in enumerate(rows):
            active = index == selected
            row_rect = pygame.Rect(panel.x + 12, y, panel.w - 24, row_h - 3)
            bg = (31, 44, 64) if active else (13, 22, 36)
            if row_rect.collidepoint(mouse_pos):
                bg = (37, 58, 78)
            pygame.draw.rect(self.screen, bg, row_rect, border_radius=5)
            if active:
                pygame.draw.rect(self.screen, hex_color(COLORS["upgrade"]), row_rect, width=1, border_radius=5)

            self.font_small.render_to(self.screen, (row_rect.x + 12, row_rect.y + 5), row["label"], hex_color(COLORS["text"]))

            for slot in range(len(row["bindings"])):
                binding_rect = pygame.Rect(slot_x[slot], row_rect.y + 4, slot_w, 22)
                waiting = capture_binding == (row["action"], slot)
                slot_active = active and selected_slot == slot
                color = COLORS["special"] if waiting else (COLORS["upgrade"] if slot_active else COLORS["panel_2"])
                pygame.draw.rect(self.screen, hex_color(color), binding_rect, border_radius=4)
                pygame.draw.rect(self.screen, (226, 232, 240), binding_rect, width=1 if waiting or slot_active else 0, border_radius=4)
                text = "Pressione..." if waiting else row["bindings"][slot]
                surf, s_rect = self.font_tiny.render(text[:18], hex_color(COLORS["text"]))
                self.screen.blit(surf, (binding_rect.centerx - s_rect.width // 2, binding_rect.y + 4))
                buttons.append((f"bind:{row['action']}:{slot}", binding_rect))
            y += row_h

        status = "Tela cheia: ON" if fullscreen else "Tela cheia: OFF"
        hint = "R restaura padrao  |  Esc volta" if not capture_binding else "Aguardando entrada..."
        self._center_text(hint, self.font_tiny, 608, COLORS["muted"])

        pref_labels = {"auto": "Entrada: AUTO", "keyboard": "Entrada: TECLADO", "joystick": "Entrada: CONTROLE"}
        pref_text = pref_labels.get(control_pref, "Entrada: AUTO")

        buttons.append(self._button(86, 632, 220, 42, status, "settings_fullscreen", mouse_pos, COLORS["special"]))
        buttons.append(self._button(322, 632, 220, 42, pref_text, "settings_control", mouse_pos, COLORS["muted"]))
        buttons.append(self._button(558, 632, 220, 42, "Restaurar padrao", "settings_reset", mouse_pos, COLORS["upgrade"]))
        buttons.append(self._button(794, 632, 220, 42, "Voltar", "settings_back", mouse_pos, COLORS["muted_2"]))
        # pygame.display.flip()
        return buttons

    def _overlay_menu(self, title, options, selected, mouse_pos, extra=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 192))
        self.screen.blit(overlay, (0, 0))
        self._center_text(title, self.font_big, 145, COLORS["text"])
        if extra:
            self._center_text(extra, self.font, 198, COLORS["muted"])
        buttons = []
        compact = len(options) > 7
        button_h = 42 if compact else 48
        spacing = 50 if compact else 62
        start_y = 238 if extra else (220 if compact else 235)
        for index, (label, action) in enumerate(options):
            color = COLORS["upgrade"] if index == selected else COLORS["panel_2"]
            buttons.append(self._button(410, start_y + index * spacing, 280, button_h, label, action, mouse_pos, color))
        # pygame.display.flip()
        return buttons

    def _draw_menu_background(self):
        for x in range(-160, SCREEN_WIDTH + 180, 80):
            pygame.draw.line(self.screen, (15, 36, 52), (x, 0), (x + 250, SCREEN_HEIGHT), 1)
        for y in range(70, SCREEN_HEIGHT, 96):
            pygame.draw.line(self.screen, (21, 48, 57), (0, y), (SCREEN_WIDTH, y - 44), 1)
        for index in range(9):
            x = 110 + index * 110
            y = 510 + (index % 3) * 18
            pygame.draw.rect(self.screen, (31, 41, 55), (x, y, 58, 34), 1, border_radius=4)

    def _center_text(self, text, font, y, color):
        f_rect = font.get_rect(text)
        font.render_to(self.screen, (SCREEN_WIDTH // 2 - f_rect.width // 2, y), text, hex_color(color))

    def _button(self, x, y, w, h, text, action, mouse_pos, color, selected=False):
        rect = pygame.Rect(x, y, w, h)
        hover = rect.collidepoint(mouse_pos)
        base = hex_color(color)
        if hover or selected:
            base = tuple(min(255, channel + 24) for channel in base)
        pygame.draw.rect(self.screen, base, rect, border_radius=7)
        pygame.draw.rect(self.screen, (226, 232, 240), rect, width=3 if selected else 1, border_radius=7)
        txt_color = (7, 17, 30) if color not in (COLORS["panel_2"], COLORS["muted_2"]) else hex_color(COLORS["text"])
        surf, s_rect = self.font.render(text, txt_color)
        self.screen.blit(surf, (x + w // 2 - s_rect.width // 2, y + h // 2 - s_rect.height // 2))
        return action, rect

    def _wrap_text(self, text, max_chars):
        words = text.split()
        if not words:
            return [""]
        lines = []
        current = words[0]
        for word in words[1:]:
            if len(current) + len(word) + 1 <= max_chars:
                current += " " + word
            else:
                lines.append(current[:max_chars])
                current = word
        lines.append(current[:max_chars])
        return lines


import pygame
from itertools import combinations, combinations_with_replacement
if __package__:
    from ...data.constants import *
    from ...data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from Sobrevivencia.presentation.ui_utils import hex_color

class ShopMenus:
    def render_stat_shop(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 224))
        self.screen.blit(overlay, (0, 0))

        buttons = []
        panel = pygame.Rect(58, 48, SCREEN_WIDTH - 116, SCREEN_HEIGHT - 96)
        pygame.draw.rect(self.screen, (8, 14, 25), panel, border_radius=8)
        pygame.draw.rect(self.screen, hex_color(COLORS["xp"]), panel, width=2, border_radius=8)

        self.font_title.render_to(self.screen, (panel.x + 28, panel.y + 18), "LOJA DE STATUS", hex_color(COLORS["text"]))
        points_label = "Pontos disponiveis" if not game.multiplayer else "Pontos da equipe"
        points_text = f"{points_label}: {game.inventory.points}"
        p_surf, p_rect = self.font_small.render(points_text, hex_color(COLORS["xp"]))
        self.screen.blit(p_surf, (panel.right - p_rect.width - 28, panel.y + 22))

        if not game.stat_shop_unlocked():
            current_level = max(player.level for player in game.players)
            needed = max(0, STAT_SHOP_UNLOCK_LEVEL - current_level)
            self._center_text(f"Desbloqueia no nivel {STAT_SHOP_UNLOCK_LEVEL}", self.font_big, 214, COLORS["text"])
            self._center_text(f"Maior nivel atual {current_level}. Faltam {needed} niveis.", self.font, 276, COLORS["muted"])
            self._center_text("Depois de desbloqueada, use pontos de nivel para roletar status permanentes.", self.font_small, 322, COLORS["muted"])
            buttons.append(self._button(panel.centerx - 110, panel.bottom - 56, 220, 40, "Voltar", "stat_shop_back", mouse_pos, COLORS["muted_2"]))
            # pygame.display.flip()
            return buttons

        subtitle_text = f"Roletar abre 3 ofertas por {STAT_SHOP_ROLL_COST} ponto. Jogar novamente uma oferta custa {STAT_SHOP_REROLL_COST} ponto."
        self.font_tiny.render_to(self.screen, (panel.x + 28, panel.y + 52), subtitle_text, hex_color(COLORS["muted"]))

        if not game.stat_shop_offers:
            self._center_text("Role a loja para revelar tres melhorias permanentes.", self.font, 252, COLORS["text"])
            self._center_text("Os custos de compra aumentam conforme a forca e a quantidade de status.", self.font_small, 292, COLORS["muted"])
            color = COLORS["xp"] if game.inventory.points >= STAT_SHOP_ROLL_COST else COLORS["muted_2"]
            buttons.append(self._button(panel.centerx - 130, 366, 260, 48, f"Roletar ({STAT_SHOP_ROLL_COST} pt) - A/Y/Enter", "stat_shop_roll", mouse_pos, color))
            buttons.append(self._button(panel.centerx - 110, panel.bottom - 56, 220, 40, "Voltar - B/Esc", "stat_shop_back", mouse_pos, COLORS["muted_2"]))
            # pygame.display.flip()
            return buttons

        card_w = 292
        card_h = 328
        start_x = panel.x + 38
        gap = 24
        y = 158
        rarity_colors = {
            1: COLORS["panel_2"],
            2: COLORS["special"],
            3: COLORS["xp"],
            4: COLORS["upgrade"],
            5: COLORS["coin"],
        }
        for index, offer in enumerate(game.stat_shop_offers):
            x = start_x + index * (card_w + gap)
            rect = pygame.Rect(x, y, card_w, card_h)
            hover = rect.collidepoint(mouse_pos)
            is_selected = (index == selected)
            rank_color = rarity_colors.get(offer.get("power", 1), COLORS["panel_2"])
            bg = (13, 22, 36) if not (hover or is_selected) else (19, 32, 50)
            pygame.draw.rect(self.screen, bg, rect, border_radius=8)
            
            # Border: Red if selected via joystick/keyboard, rank color otherwise
            border_color = (220, 38, 38) if is_selected else hex_color(rank_color)
            border_width = 4 if is_selected else 2
            pygame.draw.rect(self.screen, border_color, rect, width=border_width, border_radius=8)

            self.font.render_to(self.screen, (rect.x + 18, rect.y + 16), offer["title"].upper(), hex_color(COLORS["text"]))
            tier_text = f"FORCA {offer.get('power', 1)}"
            t_surf, t_rect = self.font_tiny.render(tier_text, hex_color(rank_color))
            self.screen.blit(t_surf, (rect.right - t_rect.width - 18, rect.y + 20))

            line_y = rect.y + 62
            for effect in offer["effects"]:
                self.font_small.render_to(self.screen, (rect.x + 18, line_y), effect["label"], hex_color(COLORS["text"]))
                self.font_small.render_to(self.screen, (rect.x + 18, line_y + 24), effect["display"], hex_color(COLORS["xp"]))
                line_y += 58

            cost = offer["cost"]
            cost_color = COLORS["coin"] if game.inventory.points >= cost else COLORS["danger"]
            self.font_small.render_to(self.screen, (rect.x + 18, rect.bottom - 106), f"Custo de compra: {cost} pts", hex_color(cost_color))

            buy_color = COLORS["xp"] if game.inventory.points >= cost else COLORS["muted_2"]
            buttons.append(self._button(rect.x + 18, rect.bottom - 78, rect.w - 36, 34, f"Comprar ({cost}) - A", f"stat_shop_buy:{index}", mouse_pos, buy_color))
            reroll_color = COLORS["special"] if game.inventory.points >= STAT_SHOP_REROLL_COST else COLORS["muted_2"]
            buttons.append(self._button(rect.x + 18, rect.bottom - 38, rect.w - 36, 30, f"Reroll ({STAT_SHOP_REROLL_COST}) - X", f"stat_shop_reroll:{index}", mouse_pos, reroll_color))

        self._center_text("Teclas 1/2/3 compram as ofertas. Esc volta ao pause. (Joystick: A compra, X reroll)", self.font_tiny, panel.bottom - 74, COLORS["muted"])
        buttons.append(self._button(panel.centerx - 110, panel.bottom - 44, 220, 34, "Voltar - B/Esc", "stat_shop_back", mouse_pos, COLORS["muted_2"]))
        # pygame.display.flip()
        return buttons

    def render_upgrade(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 205))
        self.screen.blit(overlay, (0, 0))
        player_index = game.level_up_player_index
        player = game.get_player(player_index)
        
        # Cor do turno
        turn_color = hex_color(P2_AIM_COLOR if player_index == 1 else P1_AIM_COLOR)
        
        title = "MELHORIA GRANDE" if game.upgrade_is_major else "NOVO NIVEL"
        subtitle = "Escolha um poder permanente raro" if game.upgrade_is_major else "Escolha um upgrade permanente"
        if game.multiplayer:
            subtitle = f"Turno do Jogador {player_index + 1} - " + subtitle
        
        # Brilho de turno
        pulse = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() * 0.006)
        glow_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, 100, 600, 100)
        pygame.draw.rect(self.screen, (*turn_color, int(40 * pulse)), glow_rect, border_radius=20)

        self._center_text(title, self.font_big, 116, COLORS["text"])
        self._center_text(subtitle, self.font, 166, COLORS["muted"])
        
        # Texto de turno destacado
        turn_text = f"VEZ DO JOGADOR {player_index + 1}"
        t_surf, t_rect = self.font_title.render(turn_text, turn_color)
        self.screen.blit(t_surf, (SCREEN_WIDTH // 2 - t_rect.width // 2, 210))

        buttons = []
        y = 254
        for index, key in enumerate(game.upgrade_choices):
            data = UPGRADES.get(key)
            if not data:
                data = OMNI_UPGRADES.get(key)
            if not data:
                data = CHARACTERS[player.char_class]["passives"].get(key)
            if not data: continue
            
            rect = pygame.Rect(260, y, 580, 78)
            active = rect.collidepoint(mouse_pos) or index == selected
            
            bg_color = hex_color(COLORS["upgrade"] if active else COLORS["panel"])
            if active:
                # Se estiver selecionado, usa a cor do jogador
                pygame.draw.rect(self.screen, (*turn_color, 40), rect.inflate(10, 10), border_radius=10)
                bg_color = turn_color

            pygame.draw.rect(self.screen, bg_color, rect, border_radius=7)
            border_color = (226, 232, 240) if active else (51, 65, 85)
            pygame.draw.rect(self.screen, border_color, rect, width=1, border_radius=7)
            
            text_color = (255, 255, 255) if active else hex_color(COLORS["text"])
            self.font_title.render_to(self.screen, (rect.x + 24, rect.y + 12), data["title"], text_color)
            self.font_small.render_to(self.screen, (rect.x + 24, rect.y + 47), data["description"], text_color if active else hex_color(COLORS["muted"]))
            buttons.append((key, rect))
            y += 94
        
        # pygame.display.flip() # Handled by main loop
        return buttons

    def render_skills(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 224))
        self.screen.blit(overlay, (0, 0))

        player = game.get_player(game.menu_player_index)
        inv = game.get_inventory(game.menu_player_index)
        data = CHARACTERS[player.char_class]["passives"]
        keys = list(player.passives.keys())
        selected = max(0, min(selected, len(keys) - 1)) if keys else 0
        selected_key = keys[selected] if keys else None
        buttons = []

        panel = pygame.Rect(58, 48, SCREEN_WIDTH - 116, SCREEN_HEIGHT - 96)
        pygame.draw.rect(self.screen, (8, 14, 25), panel, border_radius=8)
        pygame.draw.rect(self.screen, hex_color(COLORS["special"]), panel, width=2, border_radius=8)

        self.font_title.render_to(self.screen, (panel.x + 28, panel.y + 18), "GERENCIAMENTO DE SKILLS", hex_color(COLORS["text"]))
        switch_hint = "  |  Y/P troca jogador" if game.multiplayer else ""
        subtitle_text = f"Jogador {game.menu_player_index + 1}  |  Pontos de item {inv.points}  |  A/X/U/Enter upa skill{switch_hint}"
        self.font_tiny.render_to(self.screen, (panel.x + 28, panel.y + 50), subtitle_text, hex_color(COLORS["muted"]))
        if game.multiplayer:
            other = 2 if game.menu_player_index == 0 else 1
            buttons.append(self._button(panel.right - 228, panel.y + 18, 190, 34, f"Ver Jogador {other}", "toggle_menu_player", mouse_pos, COLORS["special"]))

        list_rect = pygame.Rect(panel.x + 26, panel.y + 86, 470, panel.h - 150)
        detail_rect = pygame.Rect(list_rect.right + 24, list_rect.y, panel.right - list_rect.right - 50, list_rect.h)
        pygame.draw.rect(self.screen, (13, 22, 36), list_rect, border_radius=6)
        pygame.draw.rect(self.screen, (39, 52, 73), list_rect, width=1, border_radius=6)
        pygame.draw.rect(self.screen, (11, 19, 31), detail_rect, border_radius=6)
        pygame.draw.rect(self.screen, (72, 86, 112), detail_rect, width=1, border_radius=6)

        y = list_rect.y + 12
        for index, key in enumerate(keys):
            skill = data[key]
            level = player.passives[key]
            category = skill.get("category", "Kit")
            rect = pygame.Rect(list_rect.x + 12, y, list_rect.w - 24, 32)
            hover = rect.collidepoint(mouse_pos)
            active = index == selected
            bg = (31, 44, 64) if active else (17, 28, 44)
            if hover:
                bg = (37, 58, 78)
            pygame.draw.rect(self.screen, bg, rect, border_radius=5)
            border_color = self._skill_category_color(category) if active or hover else (45, 60, 82)
            pygame.draw.rect(self.screen, border_color, rect, width=1, border_radius=5)

            state = "ATIVA" if level > 0 else "BLOQUEADA"
            label = f"{skill['short']}  {skill['title']}"
            self.font_tiny.render_to(self.screen, (rect.x + 10, rect.y + 4), label[:42], hex_color(COLORS["text"]))
            self.font_tiny.render_to(self.screen, (rect.x + 10, rect.y + 18), category.upper(), self._skill_category_color(category))
            
            lvl_text = f"NV {level}/10  {state}"
            l_surf, l_rect = self.font_tiny.render(lvl_text, hex_color(COLORS["xp"] if level > 0 else COLORS["muted"]))
            self.screen.blit(l_surf, (rect.right - l_rect.width - 10, rect.y + 9))
            buttons.append((f"skill_select:{index}", rect))
            y += 37

        if selected_key:
            skill = data[selected_key]
            level = player.passives[selected_key]
            category = skill.get("category", "Kit")
            cost = game.skill_upgrade_cost(selected_key)
            rank_color = self._skill_category_color(category)

            self.font_tiny.render_to(self.screen, (detail_rect.x + 22, detail_rect.y + 20), category.upper(), rank_color)
            y = detail_rect.y + 48
            for line in self._wrap_text(skill["title"], 34)[:2]:
                self.font_title.render_to(self.screen, (detail_rect.x + 22, y), line, hex_color(COLORS["text"]))
                y += 30
            y += 8
            state = "Desbloqueada" if level > 0 else "Ainda bloqueada"
            self.font_small.render_to(self.screen, (detail_rect.x + 22, y), f"{state} | Nivel {level}/10", hex_color(COLORS["muted"]))
            y += 34
            for line in self._wrap_text(skill["description"], 58)[:4]:
                self.font_small.render_to(self.screen, (detail_rect.x + 22, y), line, hex_color(COLORS["text"]))
                y += 22

            y += 14
            cost_text = f"Custo do proximo upgrade: {cost} pontos"
            if level >= 10:
                cost_text = "Skill no nivel maximo."
            self.font_small.render_to(self.screen, (detail_rect.x + 22, y), cost_text, rank_color)

            can_upgrade = level < 10 and inv.points >= cost
            button_color = COLORS["xp"] if can_upgrade else COLORS["muted_2"]
            buttons.append(self._button(detail_rect.x + 22, detail_rect.bottom - 62, 220, 40, "Upar Skill", "skill_upgrade", mouse_pos, button_color))

        buttons.append(self._button(panel.centerx - 110, panel.bottom - 52, 220, 38, "Voltar", "skills_back", mouse_pos, COLORS["muted_2"]))
        # pygame.display.flip()
        return buttons

    def _skill_category_color(self, category):
        if category == "Distância":
            return hex_color(COLORS["projectile"])
        if category == "Corpo a corpo":
            return hex_color(COLORS["sword"])
        if category == "Ambas":
            return hex_color(COLORS["xp"])
        if category == "Especial":
            return hex_color(COLORS["upgrade"])
        return hex_color(COLORS["special"])

    def construction_catalog(self):
        entries = []
        for key in BASE_ITEM_KEYS:
            entries.append({
                "tier": 1,
                "key": key,
                "item": InventoryItem(key=key),
            })

        for first, second in combinations_with_replacement(BASE_ITEM_KEYS, 2):
            sources = tuple(sorted((first, second)))
            entries.append({
                "tier": 2,
                "key": "hybrid:" + "+".join(sources),
                "item": InventoryItem(key="hybrid:" + "+".join(sources), hybrid_sources=sources),
            })

        for source_key in RELIC_DEFINITIONS:
            sources = tuple(source_key.split("+"))
            entries.append({
                "tier": 3,
                "key": "relic:" + source_key,
                "item": InventoryItem(key="relic:" + source_key, hybrid_sources=sources),
            })
        return entries

    def render_constructions(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 222))
        self.screen.blit(overlay, (0, 0))

        entries = self.construction_catalog()
        selected = max(0, min(selected, len(entries) - 1))
        selected_entry = entries[selected]
        selected_item = selected_entry["item"]
        buttons = []

        panel = pygame.Rect(58, 48, SCREEN_WIDTH - 116, SCREEN_HEIGHT - 96)
        pygame.draw.rect(self.screen, (8, 14, 25), panel, border_radius=8)
        pygame.draw.rect(self.screen, (179, 147, 74), panel, width=2, border_radius=8)
        pygame.draw.line(self.screen, (64, 52, 34), (panel.left + 22, panel.top + 52), (panel.right - 22, panel.top + 52), 1)

        self.font_title.render_to(self.screen, (panel.x + 28, panel.y + 16), "CONSTRUCOES", hex_color(COLORS["text"]))
        subtitle_text = "Itens separados por tier, com arvore de fusao e resultado final."
        self.font_tiny.render_to(self.screen, (panel.x + 236, panel.y + 26), subtitle_text, hex_color(COLORS["muted"]))

        list_rect = pygame.Rect(panel.x + 26, panel.y + 76, 398, panel.h - 142)
        detail_rect = pygame.Rect(list_rect.right + 24, list_rect.y, panel.right - list_rect.right - 50, list_rect.h)
        pygame.draw.rect(self.screen, (13, 22, 36), list_rect, border_radius=6)
        pygame.draw.rect(self.screen, (39, 52, 73), list_rect, width=1, border_radius=6)
        pygame.draw.rect(self.screen, (11, 19, 31), detail_rect, border_radius=6)
        pygame.draw.rect(self.screen, (72, 86, 112), detail_rect, width=1, border_radius=6)

        y = list_rect.y + 12
        index = 0
        for tier, label in ((1, "TIER 1 - BASE"), (2, "TIER 2 - HIBRIDOS"), (3, "TIER 3 - RELIQUIAS")):
            header_color = self._tier_color(tier)
            self.font_tiny.render_to(self.screen, (list_rect.x + 14, y), label, header_color)
            y += 19
            for entry in [entry for entry in entries if entry["tier"] == tier]:
                rect = pygame.Rect(list_rect.x + 12, y, list_rect.w - 24, 18)
                hover = rect.collidepoint(mouse_pos)
                active = index == selected
                bg = (31, 44, 64) if active else (17, 28, 44)
                if hover:
                    bg = (37, 58, 78)
                pygame.draw.rect(self.screen, bg, rect, border_radius=4)
                if active:
                    pygame.draw.rect(self.screen, header_color, rect, width=1, border_radius=4)

                icon_rect = pygame.Rect(rect.x + 5, rect.y + 3, 12, 12)
                self._draw_item_icon(entry["item"], icon_rect, game, show_level=False)
                name = self._catalog_label(entry["item"])
                color = hex_color(COLORS["text"] if active or hover else COLORS["muted"])
                self.font_tiny.render_to(self.screen, (rect.x + 24, rect.y + 2), name[:45], color)
                buttons.append((f"construction_select:{index}", rect))
                y += 19
                index += 1
            y += 4

        self._draw_construction_detail(game, selected_item, detail_rect)
        buttons.append(self._button(panel.centerx - 110, panel.bottom - 52, 220, 38, "Voltar", "constructions_back", mouse_pos, COLORS["muted_2"]))
        # pygame.display.flip()
        return buttons

    def _draw_construction_detail(self, game, item, rect):
        rank_label, rank_color = self._rank_title(item)
        self.font_tiny.render_to(self.screen, (rect.x + 22, rect.y + 18), rank_label, rank_color)

        y = rect.y + 42
        for line in self._wrap_text(item_display_name(item), 38)[:3]:
            self.font_title.render_to(self.screen, (rect.x + 22, y), line, hex_color(COLORS["text"]))
            y += 30

        y += 4
        for line in self._wrap_text(item_short_description(item), 58)[:3]:
            self.font_small.render_to(self.screen, (rect.x + 24, y), line, hex_color(COLORS["muted"]))
            y += 19

        tree_rect = pygame.Rect(rect.x + 20, rect.y + 172, rect.w - 40, rect.h - 194)
        self._draw_build_tree(game, item, tree_rect)

    def _draw_build_tree(self, game, item, rect):
        pygame.draw.rect(self.screen, (8, 14, 24), rect, border_radius=6)
        pygame.draw.rect(self.screen, (39, 52, 73), rect, width=1, border_radius=6)
        self.font_tiny.render_to(self.screen, (rect.x + 12, rect.y + 10), "ARVORE DE CONSTRUCAO", (179, 147, 74))

        if item.rank == 1:
            node = pygame.Rect(rect.centerx - 96, rect.y + 72, 192, 112)
            self._draw_tree_node(item, node, game, selected=True, show_level=False)
            for index, line in enumerate(self._wrap_text("Item base encontrado em caixas especiais e recompensas.", 56)[:2]):
                s_rect = self.font_tiny.get_rect(line)
                self.font_tiny.render_to(self.screen, (rect.centerx - s_rect.width // 2, node.bottom + 20 + index * 16), line, hex_color(COLORS["muted"]))
            return

        if item.rank == 2:
            top = pygame.Rect(rect.centerx - 106, rect.y + 42, 212, 90)
            left = pygame.Rect(rect.x + 54, rect.bottom - 104, 154, 82)
            right = pygame.Rect(rect.right - 208, rect.bottom - 104, 154, 82)
            self._draw_tree_node(item, top, game, selected=True, show_level=False)
            sources = list(item.hybrid_sources)
            self._draw_tree_edges((left.centerx, left.y - 10), (top.centerx, top.bottom + 8), (right.centerx, right.y - 10))
            self._draw_tree_node(InventoryItem(key=sources[0]), left, game, show_level=False)
            self._draw_tree_node(InventoryItem(key=sources[1]), right, game, show_level=False)
            return

        sources = list(item.hybrid_sources)
        first_pair = tuple(sources[:2])
        second_pair = tuple(sources[2:])
        top = pygame.Rect(rect.centerx - 112, rect.y + 36, 224, 78)
        left_hybrid = pygame.Rect(rect.x + 52, rect.y + 150, 164, 76)
        right_hybrid = pygame.Rect(rect.right - 216, rect.y + 150, 164, 76)
        self._draw_tree_node(item, top, game, selected=True, show_level=False)
        self._draw_tree_edges((left_hybrid.centerx, left_hybrid.y - 8), (top.centerx, top.bottom + 8), (right_hybrid.centerx, right_hybrid.y - 8))

        left_item = self._hybrid_preview_item(first_pair)
        right_item = self._hybrid_preview_item(second_pair)
        self._draw_tree_node(left_item, left_hybrid, game, show_level=False)
        self._draw_tree_node(right_item, right_hybrid, game, show_level=False)

        base_y = rect.bottom - 76
        base_w = 96
        gap = 16
        start_x = rect.centerx - (base_w * 4 + gap * 3) // 2
        base_rects = []
        for index, source_key in enumerate(first_pair + second_pair):
            base_rects.append(pygame.Rect(start_x + index * (base_w + gap), base_y, base_w, 62))
            self._draw_tree_node(InventoryItem(key=source_key), base_rects[-1], game, show_level=False)

        for source_rect in base_rects[:2]:
            pygame.draw.line(self.screen, (179, 147, 74), source_rect.midtop, left_hybrid.midbottom, 1)
        for source_rect in base_rects[2:]:
            pygame.draw.line(self.screen, (179, 147, 74), source_rect.midtop, right_hybrid.midbottom, 1)

    def _draw_tree_edges(self, left_point, top_point, right_point):
        pygame.draw.line(self.screen, (179, 147, 74), top_point, left_point, 2)
        pygame.draw.line(self.screen, (179, 147, 74), top_point, right_point, 2)
        pygame.draw.circle(self.screen, (179, 147, 74), top_point, 3)

    def _draw_tree_node(self, item, rect, game, selected=False, show_level=False):
        rank_label, rank_color = self._rank_title(item)
        bg = (20, 31, 47) if selected else (13, 22, 36)
        pygame.draw.rect(self.screen, bg, rect, border_radius=6)
        pygame.draw.rect(self.screen, rank_color, rect, width=2 if selected else 1, border_radius=6)

        icon_size = max(18, min(38, rect.w - 16, rect.h - 32))
        icon_rect = pygame.Rect(rect.centerx - icon_size // 2, rect.y + 7, icon_size, icon_size)
        self._draw_item_icon(item, icon_rect, game, show_level=show_level)

        label = item_display_name(item) if rect.w >= 150 else self._catalog_label(item)
        max_chars = max(10, rect.w // 8)
        lines = self._wrap_text(label, max_chars)[:2]
        y = icon_rect.bottom + 4
        for line in lines:
            s_rect = self.font_tiny.get_rect(line)
            self.font_tiny.render_to(self.screen, (rect.centerx - s_rect.width // 2, y), line, hex_color(COLORS["text"]))
            y += 14

        if rect.h >= 84:
            self.font_tiny.render_to(self.screen, (rect.x + 6, rect.bottom - 16), rank_label.split(" - ")[0], rank_color)

    def _catalog_label(self, item):
        if item.is_relic:
            relic_key = item.key[len("relic:"):]
            return RELIC_DEFINITIONS.get(relic_key, {}).get("short", item_display_name(item))
        if item.is_hybrid:
            return " + ".join(ITEM_DEFINITIONS[key]["short"] for key in item.hybrid_sources)
        return item_display_name(item)


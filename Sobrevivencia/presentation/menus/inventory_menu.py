import pygame
from pygame.math import Vector2
if __package__:
    from ...data.constants import *
    from ...data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from ..ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description, RELIC_DEFINITIONS
    from Sobrevivencia.presentation.ui_utils import hex_color

class InventoryMenu:
    def render_inventory(self, game, selected, mouse_pos, inventory_tab="items", flip=True):
        self.render_game(game, mouse_pos, flip=False)
        inv = game.get_inventory(game.menu_player_index)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 220))
        self.screen.blit(overlay, (0, 0))

        title = "INVENTARIO" if not game.multiplayer else f"INVENTARIO - JOGADOR {game.menu_player_index + 1}"
        self._center_text(title, self.font_big, 70, COLORS["text"])
        subtitle = f"Slots ativos {len(inv.active_slots)}/{MAX_ACTIVE_ITEMS}   Pontos de item {inv.points}"
        self._center_text(subtitle, self.font, 124, COLORS["muted"])

        raw_items = inv.item_list()
        buttons = []
        if game.multiplayer:
            other = 2 if game.menu_player_index == 0 else 1
            buttons.append(self._button(790, 112, 230, 34, f"Ver Jogador {other}", "toggle_menu_player", mouse_pos, COLORS["special"]))

        if inv.black_market_unlocked:
            tab_color1 = COLORS["xp"] if inventory_tab == "items" else COLORS["muted"]
            tab_color2 = COLORS["special"] if inventory_tab == "shop" else COLORS["muted"]
            self.screen.blit(self.font.render("[L1] Itens", True, hex_color(tab_color1)), (120, 112))
            self.screen.blit(self.font.render("[R1] Loja (Mercado Negro)", True, hex_color(tab_color2)), (300, 112))

        items = []  # Garante que items está sempre definido
        if inventory_tab == "shop":
            shop_keys = list(BASE_ITEM_KEYS)
            selected = max(0, min(selected, len(shop_keys) - 1))
            self.screen.blit(self.font_small.render("Itens Basicos a Venda (Custo: 15 pt)", True, hex_color(COLORS["text"])), (120, 160))
            
            slot_size = 64
            spacing = 16
            for i, key in enumerate(shop_keys):
                rect = pygame.Rect(120 + i * (slot_size + spacing), 184, slot_size, slot_size)
                hover = rect.collidepoint(mouse_pos)
                is_selected = i == selected
                color = COLORS["upgrade"] if is_selected else COLORS["panel_2"]
                if hover: color = COLORS["special"]
                pygame.draw.rect(self.screen, hex_color(color), rect, border_radius=6)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, width=1 if is_selected else 0, border_radius=6)
                
                mock_item = InventoryItem(key=key)
                self._draw_item_icon(mock_item, rect, game, show_level=False)
                buttons.append((f"shop_select:{i}", rect))
                
            panel_x = 780
            panel_y = 190
            selected_key = shop_keys[selected]
            mock_item = InventoryItem(key=selected_key)
            name = item_display_name(mock_item)
            wrapped = [
                name[:28],
                "Nivel base 1. Comprar igual sobe de nivel.",
                item_short_description(mock_item)[:34],
            ]
            for offset, line in enumerate(wrapped):
                self.screen.blit(self.font_small.render(line, True, hex_color(COLORS["text"] if offset == 0 else COLORS["muted"])), (panel_x, panel_y + offset * 28))
                
            can_buy = inv.points >= 15
            buttons.append(self._button(panel_x, panel_y + 112, 230, 42, "Comprar (15 pts) - A", "shop_buy", mouse_pos, COLORS["xp"] if can_buy else COLORS["muted_2"]))

        elif not raw_items:
            self._center_text("Destrua Caixas Especiais para encontrar itens passivos.", self.font, 274, COLORS["muted"])
            items = []
        else:
            active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
            reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
            items = active_items + reserve_items
            selected = max(0, min(selected, len(items) - 1))

            self.screen.blit(self.font_small.render("Ativos", True, hex_color(COLORS["text"])), (120, 160))
            slot_size = 64
            spacing = 16
            for i in range(MAX_ACTIVE_ITEMS):
                rect = pygame.Rect(120 + i * (slot_size + spacing), 184, slot_size, slot_size)
                index = i
                hover = rect.collidepoint(mouse_pos)
                is_selected = index == selected
                color = COLORS["upgrade"] if is_selected else COLORS["panel_2"]
                if hover: color = COLORS["special"]
                pygame.draw.rect(self.screen, hex_color(color), rect, border_radius=6)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, width=1 if is_selected else 0, border_radius=6)

                if i < len(active_items):
                    self._draw_item_icon(active_items[i], rect, game)
                    buttons.append((f"item_select:{index}", rect))

            self.screen.blit(self.font_small.render("Reserva", True, hex_color(COLORS["text"])), (120, 268))
            for r_idx in range(20):
                col = r_idx % 5
                row = r_idx // 5
                rect = pygame.Rect(120 + col * (slot_size + spacing), 292 + row * (slot_size + spacing), slot_size, slot_size)
                index = len(active_items) + r_idx
                hover = rect.collidepoint(mouse_pos)
                is_selected = index == selected
                color = COLORS["upgrade"] if is_selected else COLORS["panel_2"]
                if hover: color = COLORS["special"]
                pygame.draw.rect(self.screen, hex_color(color), rect, border_radius=6)
                pygame.draw.rect(self.screen, (226, 232, 240), rect, width=1 if is_selected else 0, border_radius=6)

                if r_idx < len(reserve_items):
                    self._draw_item_icon(reserve_items[r_idx], rect, game)
                    buttons.append((f"item_select:{index}", rect))

        panel_x = 780
        panel_y = 190
        selected_item = items[selected] if items else None
        if selected_item:
            name = item_display_name(selected_item)
            wrapped = [
                name[:28],
                f"Nivel {selected_item.level}/{MAX_ITEM_LEVEL}",
                item_short_description(selected_item)[:34],
            ]
            for offset, line in enumerate(wrapped):
                self.screen.blit(self.font_small.render(line, True, hex_color(COLORS["text"] if offset == 0 else COLORS["muted"])), (panel_x, panel_y + offset * 28))
            equip_label = "Remover dos ativos" if inv.is_active(selected_item.slot_key) else "Equipar"
            buttons.append(self._button(panel_x, panel_y + 112, 230, 42, equip_label, "item_toggle", mouse_pos, COLORS["special"]))
            if selected_item.is_relic:
                cost = 7
                rank_label = "RELIQUIA (Rank 3)"
                rank_color = (250, 180, 50)
            elif selected_item.is_hybrid:
                cost = 3
                rank_label = "HIBRIDO (Rank 2)"
                rank_color = hex_color(COLORS["upgrade"])
            else:
                cost = 1
                rank_label = "BASICO (Rank 1)"
                rank_color = (205, 127, 50)  # Bronze para Tier 1
            rank_surf = self.font_tiny.render(f"Rank: {rank_label}", True, rank_color)
            self.screen.blit(rank_surf, (panel_x, panel_y + 90))
            
            if selected_item.rank == 1 and selected_item.level >= 10 and inv.black_market_unlocked:
                buttons.append(self._button(panel_x, panel_y + 166, 230, 42, "Transformar (15 pts)", "item_transform", mouse_pos, COLORS["special"]))
            else:
                buttons.append(self._button(panel_x, panel_y + 166, 230, 42, f"Upar ({cost} pts)", "item_upgrade", mouse_pos, COLORS["xp"]))
                
            fuse_label = "Marcar/Fundir" if not selected_item.is_relic else "(Reliquia: sem fusao)"
            buttons.append(self._button(panel_x, panel_y + 220, 230, 42, fuse_label, "item_fuse", mouse_pos, COLORS["upgrade"]))
            
            sell_value = inv.get_sell_value(selected_item.slot_key)
            if not inv.is_active(selected_item.slot_key):
                buttons.append(self._button(panel_x, panel_y + 274, 230, 42, f"Vender ({sell_value} pts)", "item_sell", mouse_pos, "#DC2626")) # Vermelho para venda
            else:
                self.screen.blit(self.font_tiny.render("(Desequipe para vender)", True, COLORS["muted_2"]), (panel_x, panel_y + 286))

        hint = "I/Esc volta  |  Tab/Q troca aba  |  ENTER equipa  |  U upa  |  F fundir  |  S vender"
        if game.multiplayer:
            hint += "  |  P troca jogador"
        self._center_text(hint, self.font_tiny, 640, COLORS["muted"])
        buttons.append(self._button(410, 662, 280, 42, "Voltar ao Jogo", "resume", mouse_pos, COLORS["muted_2"]))
        if flip:
            pass  # pygame.display.flip() handled by main loop
        return buttons

    def render_fusion_confirm(self, game, inventory_selected, choice_selected, mouse_pos):
        self.render_inventory(game, inventory_selected, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 176))
        self.screen.blit(overlay, (0, 0))

        success, preview, message = game.fusion_preview()
        inv = game.get_inventory(game.menu_player_index)
        sources = [inv.get(key) for key in inv.fusion_marks]
        sources = [item for item in sources if item is not None]

        panel = pygame.Rect(248, 112, 604, 468)
        pygame.draw.rect(self.screen, (9, 15, 26), panel, border_radius=8)
        pygame.draw.rect(self.screen, (179, 147, 74), panel, width=2, border_radius=8)
        self._center_text("CONFIRMAR FUSAO", self.font_title, panel.y + 24, COLORS["text"])

        if success and len(sources) == 2:
            name_lines = self._wrap_text(item_display_name(preview), 44)
            y = panel.y + 70
            for line in name_lines[:2]:
                self._center_text(line, self.font_small, y, COLORS["upgrade"] if preview.is_hybrid else COLORS["coin"])
                y += 20
            self._center_text("Os dois itens nivel 10 serao consumidos.", self.font_tiny, y + 4, COLORS["muted"])

            left = pygame.Rect(panel.x + 58, panel.y + 168, 158, 90)
            right = pygame.Rect(panel.right - 216, panel.y + 168, 158, 90)
            result = pygame.Rect(panel.centerx - 92, panel.y + 298, 184, 88)
            self._draw_tree_node(sources[0], left, game, show_level=True)
            self._draw_tree_node(sources[1], right, game, show_level=True)
            plus = self.font_title.render("+", True, (179, 147, 74))
            self.screen.blit(plus, (panel.centerx - plus.get_width() // 2, left.centery - plus.get_height() // 2))
            pygame.draw.line(self.screen, (179, 147, 74), (left.centerx, left.bottom + 8), (result.centerx, result.y - 10), 2)
            pygame.draw.line(self.screen, (179, 147, 74), (right.centerx, right.bottom + 8), (result.centerx, result.y - 10), 2)
            pygame.draw.polygon(self.screen, (179, 147, 74), [(result.centerx, result.y - 2), (result.centerx - 7, result.y - 13), (result.centerx + 7, result.y - 13)])
            self._draw_tree_node(preview, result, game, selected=True, show_level=False)
        else:
            self._center_text(message, self.font, panel.y + 220, COLORS["danger"])

        buttons = []
        actions = [(f"Confirmar ({FUSION_COST} pts)", "fusion_confirm_yes", COLORS["xp"]), ("Cancelar", "fusion_confirm_no", COLORS["muted_2"])]
        for index, (label, action, color) in enumerate(actions):
            button_color = COLORS["upgrade"] if index == choice_selected else color
            buttons.append(self._button(panel.x + 126 + index * 230, panel.bottom - 58, 170, 40, label, action, mouse_pos, button_color))

        # pygame.display.flip()
        return buttons

    def render_point_confirm(self, game, cost, message, selected, mouse_pos):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 176))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 120, 500, 240)
        pygame.draw.rect(self.screen, (9, 15, 26), panel, border_radius=8)
        pygame.draw.rect(self.screen, hex_color(COLORS["xp"]), panel, width=2, border_radius=8)

        self._center_text("CONFIRMAR COMPRA", self.font_title, panel.y + 24, COLORS["text"])

        y = panel.y + 80
        for line in self._wrap_text(message, 44)[:3]:
            self._center_text(line, self.font, y, COLORS["muted"])
            y += 24

        buttons = []
        actions = [(f"Confirmar ({cost} pts)", "point_confirm_yes", COLORS["xp"]), ("Cancelar", "point_confirm_no", COLORS["muted_2"])]
        for index, (label, action, color) in enumerate(actions):
            button_color = COLORS["upgrade"] if index == selected else color
            buttons.append(self._button(panel.x + 60 + index * 200, panel.bottom - 60, 180, 40, label, action, mouse_pos, button_color))

        return buttons

    def _draw_item_icon(self, item, rect, game, show_level=True):
        if item.is_relic:
            # Pulsing gold/purple for relics
            import time
            pulse = 0.5 + 0.5 * math.sin(time.time() * 4)
            r = int(rect.width // 3 + pulse * 4)
            pygame.draw.circle(self.screen, (250, 180, 50), rect.center, r)
            pygame.draw.circle(self.screen, (192, 132, 252), rect.center, int(r * 0.55))
        elif item.is_hybrid:
            pygame.draw.circle(self.screen, hex_color(COLORS["upgrade"]), rect.center, rect.width // 3)
        else:
            if item.key in self.item_icons:
                icon = pygame.transform.scale(self.item_icons[item.key], (rect.width - 8, rect.height - 8))
                self.screen.blit(icon, (rect.x + 4, rect.y + 4))
            else:
                pygame.draw.circle(self.screen, hex_color(COLORS["special"]), rect.center, rect.width // 3)

        # Tier 1 borders (Bronze)
        if not item.is_relic and not item.is_hybrid:
            pygame.draw.rect(self.screen, (205, 127, 50), rect, width=2, border_radius=6)
        # Tier 2 borders (Silver)
        elif item.is_hybrid:
            pygame.draw.rect(self.screen, (192, 192, 192), rect, width=2, border_radius=6)
        # Tier 3 borders (Gold)
        elif item.is_relic:
            pygame.draw.rect(self.screen, (255, 215, 0), rect, width=2, border_radius=6)

        if show_level:
            lvl_surf = self.font_tiny.render(str(item.level), True, hex_color(COLORS["text"]))
            lvl_rect = lvl_surf.get_rect(bottomright=(rect.right - 2, rect.bottom - 2))
            bg_rect = lvl_rect.inflate(4, 2)
            bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
            pygame.draw.rect(bg_surf, (9, 14, 24, 210), bg_surf.get_rect(), border_radius=2)
            self.screen.blit(bg_surf, bg_rect.topleft)
            self.screen.blit(lvl_surf, lvl_rect)

        if game and item.slot_key in game.get_inventory(game.menu_player_index).fusion_marks:
            tag = self.font_tiny.render("F", True, hex_color(COLORS["text"]))
            pygame.draw.rect(self.screen, hex_color(COLORS["health"]), (rect.x + 2, rect.y + 2, tag.get_width() + 4, tag.get_height() + 4), border_radius=3)
            self.screen.blit(tag, (rect.x + 4, rect.y + 4))

    def _hybrid_preview_item(self, sources):
        sources = tuple(sorted(sources))
        return InventoryItem(key="hybrid:" + "+".join(sources), hybrid_sources=sources)

    def _rank_title(self, item):
        if item.is_relic:
            return "TIER 3 - RELIQUIA", (250, 180, 50)
        if item.is_hybrid:
            return "TIER 2 - HIBRIDO", hex_color(COLORS["upgrade"])
        return "TIER 1 - BASE", hex_color(COLORS["special"])

    def _tier_color(self, tier):
        if tier == 3:
            return (250, 180, 50)
        if tier == 2:
            return hex_color(COLORS["upgrade"])
        return hex_color(COLORS["special"])


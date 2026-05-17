import pygame

try:
    import pygame_gui
except ImportError:
    pygame_gui = None

if __package__:
    from ...data.constants import *
    from ...data.items import (
        BASE_ITEM_KEYS,
        InventoryItem,
        MAX_ACTIVE_ITEMS,
        MAX_ITEM_LEVEL,
        item_display_name,
        item_short_description,
    )
    from ..ui_utils import hex_color
    from .ui_components import ObjectID
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import (
        BASE_ITEM_KEYS,
        InventoryItem,
        MAX_ACTIVE_ITEMS,
        MAX_ITEM_LEVEL,
        item_display_name,
        item_short_description,
    )
    from Sobrevivencia.presentation.ui_utils import hex_color
    from Sobrevivencia.presentation.menus.ui_components import ObjectID


class InventoryGUI:
    def init_inventory_gui(self):
        self.inv_window = None
        self.item_buttons = {}
        self.inventory_action_buttons = {}
        self.inventory_tab_buttons = {}
        self._last_inventory_signature = None

    def render_inventory_gui(self, game, selected, mouse_pos=None, inventory_tab="items"):
        self.render_game(game, mouse_pos or (0, 0), flip=False, draw_gui=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 220))
        self.screen.blit(overlay, (0, 0))

        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            return self.render_inventory(game, selected, mouse_pos or (0, 0), inventory_tab)

        inv = game.get_inventory(game.menu_player_index)
        items = inv.item_list()
        signature = (
            game.menu_player_index,
            inventory_tab,
            selected,
            inv.points,
            tuple(inv.active_slots),
            tuple(inv.fusion_marks),
            tuple((item.slot_key, item.key, item.level) for item in items),
            inv.black_market_unlocked,
        )

        if not self.inv_window or not self.inv_window.alive() or self._last_inventory_signature != signature:
            if self.inv_window:
                self.inv_window.kill()
            self._create_inventory_window(game, selected, inventory_tab)
            self._last_inventory_signature = signature

        self.draw_gui_layer()
        if game.multiplayer:
            self.draw_player_window_accent(self.inv_window, game.menu_player_index)
        return []

    def _create_inventory_window(self, game, selected, inventory_tab):
        self.item_buttons = {}
        self.inventory_action_buttons = {}
        self.inventory_tab_buttons = {}
        c = self.components
        inv = game.get_inventory(game.menu_player_index)

        title = f"J{game.menu_player_index + 1} - INVENTARIO" if game.multiplayer else "INVENTARIO"
        self.inv_window = c.window(
            title,
            (940, 600),
            "#inventory_window",
            y=58,
            player_index=game.menu_player_index if game.multiplayer else None,
        )
        if self.inv_window is None:
            return

        subtitle = f"Slots ativos {len(inv.active_slots)}/{MAX_ACTIVE_ITEMS} | Pontos {inv.points}"
        c.label(pygame.Rect((20, 12), (520, 28)), subtitle, container=self.inv_window)

        if game.multiplayer:
            other = 2 if game.menu_player_index == 0 else 1
            self.inventory_action_buttons["toggle_menu_player"] = c.button(
                pygame.Rect((680, 10), (220, 32)),
                f"Ver Jogador {other}",
                container=self.inv_window,
                intent="secondary",
            )

        if inv.black_market_unlocked:
            self.inventory_tab_buttons["inventory_tab:items"] = c.button(
                pygame.Rect((20, 46), (160, 32)),
                "Itens",
                container=self.inv_window,
                intent="selected" if inventory_tab == "items" else "muted",
            )
            self.inventory_tab_buttons["inventory_tab:shop"] = c.button(
                pygame.Rect((190, 46), (220, 32)),
                "Mercado Negro",
                container=self.inv_window,
                intent="selected" if inventory_tab == "shop" else "muted",
            )

        if inventory_tab == "shop":
            self._create_inventory_shop_tab(game, selected)
        else:
            self._create_inventory_items_tab(game, selected)

        self.inventory_action_buttons["resume"] = c.button(
            pygame.Rect((370, 528), (200, 40)),
            "Voltar ao Jogo",
            container=self.inv_window,
            intent="muted",
        )

    def _create_inventory_shop_tab(self, game, selected):
        c = self.components
        inv = game.get_inventory(game.menu_player_index)
        shop_keys = list(BASE_ITEM_KEYS)
        selected = max(0, min(selected, len(shop_keys) - 1)) if shop_keys else 0

        c.label(
            pygame.Rect((30, 98), (520, 24)),
            "Itens basicos a venda | Custo: 15 pts",
            container=self.inv_window,
        )
        grid = c.panel(pygame.Rect((28, 130), (600, 360)), container=self.inv_window)
        details = c.panel(pygame.Rect((650, 90), (250, 400)), container=self.inv_window)

        slot = 82
        gap = 12
        for index, key in enumerate(shop_keys):
            item = InventoryItem(key=key)
            col = index % 5
            row = index // 5
            is_selected = index == selected
            
            panel_rect = pygame.Rect((18 + col * (slot + gap), 18 + row * (slot + gap)), (slot, slot))
            panel_oid = ObjectID(class_id="@selected_upgrade_panel" if is_selected else "#item_button")
            slot_panel = c.panel(panel_rect, container=grid, object_id=panel_oid)
            
            img_surf = self._create_item_surface(item, (slot-8, slot-8), game)
            c.image(pygame.Rect((4, 4), (slot-8, slot-8)), img_surf, container=slot_panel)
            
            btn_oid = ObjectID(class_id="@selected_upgrade_btn" if is_selected else "@upgrade_btn")
            btn = c.button(
                pygame.Rect((0, 0), (slot, slot)),
                "",
                container=slot_panel,
                tooltip=item_short_description(item),
                object_id=btn_oid
            )
            self.item_buttons[btn] = f"shop_select:{index}"

        item = InventoryItem(key=shop_keys[selected]) if shop_keys else None
        if item:
            c.label(pygame.Rect((12, 16), (226, 30)), item_display_name(item), container=details)
            c.text_box(
                pygame.Rect((12, 56), (226, 170)),
                item_short_description(item),
                container=details,
            )
            can_buy = inv.points >= 15
            self.inventory_action_buttons["shop_buy"] = c.button(
                pygame.Rect((12, 250), (226, 42)),
                "Comprar (15 pts)",
                container=details,
                intent="primary" if can_buy else "muted",
            )
            if not can_buy:
                self.inventory_action_buttons["shop_buy"].disable()

    def _create_inventory_items_tab(self, game, selected):
        c = self.components
        inv = game.get_inventory(game.menu_player_index)
        raw_items = inv.item_list()
        active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
        reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
        ordered_items = active_items + reserve_items
        selected = max(0, min(selected, len(ordered_items) - 1)) if ordered_items else 0

        c.label(pygame.Rect((30, 98), (260, 24)), "Ativos", container=self.inv_window)
        active_panel = c.panel(pygame.Rect((28, 130), (600, 105)), container=self.inv_window)
        reserve_panel = c.scroll(pygame.Rect((28, 272), (600, 220)), container=self.inv_window)
        c.label(pygame.Rect((30, 244), (260, 24)), "Reserva", container=self.inv_window)
        details = c.panel(pygame.Rect((650, 90), (250, 400)), container=self.inv_window)

        slot = 76
        gap = 12
        for index in range(MAX_ACTIVE_ITEMS):
            item = active_items[index] if index < len(active_items) else None
            is_selected = index == selected and item
            
            panel_rect = pygame.Rect((16 + index * (slot + gap), 14), (slot, slot))
            panel_oid = ObjectID(class_id="@selected_upgrade_panel" if is_selected else "#item_button")
            slot_panel = c.panel(panel_rect, container=active_panel, object_id=panel_oid)
            
            if item:
                img_surf = self._create_item_surface(item, (slot-8, slot-8), game)
                c.image(pygame.Rect((4, 4), (slot-8, slot-8)), img_surf, container=slot_panel)
                
            btn_oid = ObjectID(class_id="@selected_upgrade_btn" if is_selected else "@upgrade_btn")
            btn = c.button(
                pygame.Rect((0, 0), (slot, slot)),
                "",
                container=slot_panel,
                tooltip=item_short_description(item) if item else None,
                object_id=btn_oid
            )
            if item:
                self.item_buttons[btn] = f"item_select:{index}"

        for reserve_index, item in enumerate(reserve_items):
            index = len(active_items) + reserve_index
            col = reserve_index % 6
            row = reserve_index // 6
            is_selected = index == selected
            
            panel_rect = pygame.Rect((12 + col * (slot + gap), 12 + row * (slot + gap)), (slot, slot))
            panel_oid = ObjectID(class_id="@selected_upgrade_panel" if is_selected else "#item_button")
            slot_panel = c.panel(panel_rect, container=reserve_panel, object_id=panel_oid)
            
            img_surf = self._create_item_surface(item, (slot-8, slot-8), game)
            c.image(pygame.Rect((4, 4), (slot-8, slot-8)), img_surf, container=slot_panel)
            
            btn_oid = ObjectID(class_id="@selected_upgrade_btn" if is_selected else "@upgrade_btn")
            btn = c.button(
                pygame.Rect((0, 0), (slot, slot)),
                "",
                container=slot_panel,
                tooltip=item_short_description(item),
                object_id=btn_oid
            )
            self.item_buttons[btn] = f"item_select:{index}"

        reserve_rows = (len(reserve_items) + 5) // 6
        reserve_content_height = 24 + max(1, reserve_rows) * (slot + gap)
        reserve_panel.set_scrollable_area_dimensions((580, reserve_content_height))
        if selected >= len(active_items) and reserve_items:
            reserve_index = selected - len(active_items)
            row = reserve_index // 6
            item_top = 12 + row * (slot + gap)
            self._scroll_container_to_item(reserve_panel, item_top, slot, 220, reserve_content_height)

        if not ordered_items:
            c.text_box(
                pygame.Rect((12, 16), (226, 90)),
                "Destrua Caixas Especiais para encontrar itens passivos.",
                container=details,
            )
            return

        selected_item = ordered_items[selected]
        name = item_display_name(selected_item)
        c.label(pygame.Rect((12, 14), (226, 30)), name[:30], container=details)
        c.label(
            pygame.Rect((12, 44), (226, 24)),
            f"Nivel {selected_item.level}/{MAX_ITEM_LEVEL} | {self._rank_label(selected_item)}",
            container=details,
        )
        c.text_box(
            pygame.Rect((12, 78), (226, 124)),
            item_short_description(selected_item),
            container=details,
        )

        y = 218
        equip_label = "Remover dos ativos" if inv.is_active(selected_item.slot_key) else "Equipar"
        self.inventory_action_buttons["item_toggle"] = c.button(
            pygame.Rect((12, y), (226, 34)),
            equip_label,
            container=details,
            intent="secondary",
        )
        y += 40

        cost = 7 if selected_item.is_relic else (3 if selected_item.is_hybrid else 1)
        self.inventory_action_buttons["item_upgrade"] = c.button(
            pygame.Rect((12, y), (226, 34)),
            f"Upar ({cost} pts)",
            container=details,
            intent="primary" if inv.points >= cost else "muted",
        )
        if inv.points < cost:
            self.inventory_action_buttons["item_upgrade"].disable()
        y += 40

        fuse_label = "Marcar/Fundir" if not selected_item.is_relic else "Reliquia sem fusao"
        self.inventory_action_buttons["item_fuse"] = c.button(
            pygame.Rect((12, y), (226, 34)),
            fuse_label,
            container=details,
            intent="secondary",
        )
        if selected_item.is_relic:
            self.inventory_action_buttons["item_fuse"].disable()
        y += 40

        if selected_item.rank == 1 and selected_item.level >= MAX_ITEM_LEVEL and inv.black_market_unlocked:
            self.inventory_action_buttons["item_transform"] = c.button(
                pygame.Rect((12, y), (226, 34)),
                "Transformar (15 pts)",
                container=details,
                intent="secondary" if inv.points >= 15 else "muted",
            )
            if inv.points < 15:
                self.inventory_action_buttons["item_transform"].disable()
            y += 40

        if not inv.is_active(selected_item.slot_key):
            value = inv.get_sell_value(selected_item.slot_key)
            self.inventory_action_buttons["item_sell"] = c.button(
                pygame.Rect((12, y), (226, 34)),
                f"Vender ({value} pts)",
                container=details,
                intent="danger",
            )

    def handle_inventory_event(self, event):
        if pygame_gui is None or event.type != pygame_gui.UI_BUTTON_PRESSED:
            return None

        if hasattr(self, 'point_confirm_action_buttons') and event.ui_element in self.point_confirm_action_buttons:
            return self.point_confirm_action_buttons[event.ui_element]

        if hasattr(self, 'fusion_confirm_action_buttons') and event.ui_element in self.fusion_confirm_action_buttons:
            return self.fusion_confirm_action_buttons[event.ui_element]

        if event.ui_element in self.item_buttons:
            return self.item_buttons[event.ui_element]

        for action, button in self.inventory_action_buttons.items():
            if event.ui_element == button:
                return action

        for action, button in self.inventory_tab_buttons.items():
            if event.ui_element == button:
                return action

        return None

    def _create_item_surface(self, item, size, game):
        import math
        surf = pygame.Surface(size, pygame.SRCALPHA)
        rect = pygame.Rect(0, 0, *size)
        if item.is_relic:
            import time
            pulse = 0.5 + 0.5 * math.sin(time.time() * 4)
            r = int(rect.width // 3 + pulse * 4)
            pygame.draw.circle(surf, (250, 180, 50), rect.center, r)
            pygame.draw.circle(surf, (192, 132, 252), rect.center, int(r * 0.55))
        elif item.is_hybrid:
            pygame.draw.circle(surf, hex_color(COLORS["upgrade"]), rect.center, rect.width // 3)
        else:
            if item.key in self.item_icons:
                icon = pygame.transform.scale(self.item_icons[item.key], (rect.width - 8, rect.height - 8))
                surf.blit(icon, (rect.x + 4, rect.y + 4))
            else:
                pygame.draw.circle(surf, hex_color(COLORS["special"]), rect.center, rect.width // 3)

        if not item.is_relic and not item.is_hybrid:
            pygame.draw.rect(surf, (205, 127, 50), rect, width=2, border_radius=6)
        elif item.is_hybrid:
            pygame.draw.rect(surf, (192, 192, 192), rect, width=2, border_radius=6)
        elif item.is_relic:
            pygame.draw.rect(surf, (255, 215, 0), rect, width=2, border_radius=6)

        lvl_surf, l_rect = self.font_tiny.render(str(item.level), hex_color(COLORS["text"]))
        l_rect.bottomright = (rect.right - 2, rect.bottom - 2)
        bg_rect = l_rect.inflate(4, 2)
        bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg_surf, (9, 14, 24, 210), bg_surf.get_rect(), border_radius=2)
        surf.blit(bg_surf, bg_rect.topleft)
        surf.blit(lvl_surf, l_rect)

        if game and item.slot_key in game.get_inventory(game.menu_player_index).fusion_marks:
            tag_surf, t_rect = self.font_tiny.render("F", hex_color(COLORS["text"]))
            pygame.draw.rect(surf, hex_color(COLORS["health"]), (rect.x + 2, rect.y + 2, t_rect.width + 4, t_rect.height + 4), border_radius=3)
            surf.blit(tag_surf, (rect.x + 4, rect.y + 4))
            
        return surf

    def _item_button_label(self, item):
        if item is None:
            return ""
        name = item_display_name(item)
        return f"{name[:7]}\nNv {item.level}"

    def _rank_label(self, item):
        if item.is_relic:
            return "T3 Reliquia"
        if item.is_hybrid:
            return "T2 Hibrido"
        return "T1 Base"

    def render_point_confirm(
        self,
        game,
        cost,
        message,
        selected,
        mouse_pos,
        quantity=1,
        max_quantity=1,
        total_cost=None,
    ):
        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            from .inventory_menu import InventoryMenu
            return InventoryMenu.render_point_confirm(
                self,
                game,
                cost,
                message,
                selected,
                mouse_pos,
                quantity,
                max_quantity,
                total_cost,
            )
            
        c = self.components
        total_cost = cost if total_cost is None else total_cost
        quantity_enabled = max_quantity > 1
        signature = ("point_confirm", cost, message, selected, quantity, max_quantity, total_cost)
        
        if not hasattr(self, 'point_confirm_window') or not self.point_confirm_window or not self.point_confirm_window.alive() or getattr(self, '_last_point_confirm_signature', None) != signature:
            if hasattr(self, 'point_confirm_window') and self.point_confirm_window:
                self.point_confirm_window.kill()
                
            self.point_confirm_window = c.window(
                "CONFIRMAR ACAO",
                (440, 250 if quantity_enabled else 200),
                "#point_confirm",
                y=SCREEN_HEIGHT // 2 - (125 if quantity_enabled else 100),
                close_button=False
            )
            
            c.text_box(pygame.Rect((20, 10), (400, 62)), message, container=self.point_confirm_window)
            
            self.point_confirm_action_buttons = {}

            button_y = 80
            if quantity_enabled:
                c.label(
                    pygame.Rect((20, 76), (400, 24)),
                    f"Quantidade: {quantity}/{max_quantity} | Total: {total_cost} pts",
                    container=self.point_confirm_window,
                )

                btn_dec = c.button(
                    pygame.Rect((72, 108), (70, 36)),
                    "-",
                    container=self.point_confirm_window,
                    intent="secondary",
                )
                if quantity <= 1:
                    btn_dec.disable()
                self.point_confirm_action_buttons[btn_dec] = "point_confirm_decrease"

                c.label(
                    pygame.Rect((160, 111), (120, 30)),
                    f"x{quantity}",
                    container=self.point_confirm_window,
                )

                btn_inc = c.button(
                    pygame.Rect((298, 108), (70, 36)),
                    "+",
                    container=self.point_confirm_window,
                    intent="secondary",
                )
                if quantity >= max_quantity:
                    btn_inc.disable()
                self.point_confirm_action_buttons[btn_inc] = "point_confirm_increase"
                button_y = 158
            
            btn_yes = c.button(
                pygame.Rect((20, button_y), (190, 40)),
                f"Confirmar ({total_cost} pts)",
                container=self.point_confirm_window,
                intent="primary" if selected == 0 else "secondary"
            )
            self.point_confirm_action_buttons[btn_yes] = "point_confirm_yes"
            
            btn_no = c.button(
                pygame.Rect((230, button_y), (190, 40)),
                "Cancelar",
                container=self.point_confirm_window,
                intent="primary" if selected == 1 else "secondary"
            )
            self.point_confirm_action_buttons[btn_no] = "point_confirm_no"
            
            self._last_point_confirm_signature = signature

        self.draw_gui_layer()
        return []

    def render_fusion_confirm(self, game, inventory_selected, choice_selected, mouse_pos):
        self.render_inventory_gui(game, inventory_selected, mouse_pos)
        
        if pygame_gui is None or not getattr(self, "components", None) or not self.components.available:
            from .inventory_menu import InventoryMenu
            return InventoryMenu.render_fusion_confirm(self, game, inventory_selected, choice_selected, mouse_pos)
            
        success, preview, message = game.fusion_preview()
        c = self.components
        signature = ("fusion_confirm", choice_selected, success, message)
        
        if not hasattr(self, 'fusion_confirm_window') or not self.fusion_confirm_window or not self.fusion_confirm_window.alive() or getattr(self, '_last_fusion_confirm_signature', None) != signature:
            if hasattr(self, 'fusion_confirm_window') and self.fusion_confirm_window:
                self.fusion_confirm_window.kill()
                
            self.fusion_confirm_window = c.window(
                "CONFIRMAR FUSAO",
                (520, 320),
                "#fusion_confirm",
                y=SCREEN_HEIGHT // 2 - 160,
                close_button=False
            )
            
            if success:
                from ...data.items import item_display_name
                c.label(pygame.Rect((20, 14), (480, 30)), item_display_name(preview), container=self.fusion_confirm_window)
                c.text_box(
                    pygame.Rect((20, 54), (480, 118)),
                    "Os dois itens nivel 10 serao consumidos.<br><br>Resultado: " + item_display_name(preview),
                    container=self.fusion_confirm_window,
                )
            else:
                c.text_box(
                    pygame.Rect((20, 64), (480, 96)),
                    f"<font color=#E74C3C>{message}</font>",
                    container=self.fusion_confirm_window,
                )

            self.fusion_confirm_action_buttons = {}
            
            btn_yes = c.button(
                pygame.Rect((56, 210), (190, 40)),
                f"Confirmar ({FUSION_COST} pts)",
                container=self.fusion_confirm_window,
                intent="primary" if choice_selected == 0 else "secondary"
            )
            if not success: btn_yes.disable()
            self.fusion_confirm_action_buttons[btn_yes] = "fusion_confirm_yes"
            
            btn_no = c.button(
                pygame.Rect((274, 210), (190, 40)),
                "Cancelar",
                container=self.fusion_confirm_window,
                intent="primary" if choice_selected == 1 else "secondary"
            )
            self.fusion_confirm_action_buttons[btn_no] = "fusion_confirm_no"
            
            self._last_fusion_confirm_signature = signature

        self.draw_gui_layer()
        return []


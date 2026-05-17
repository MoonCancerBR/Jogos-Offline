import pygame
if __package__:
    from ..data.constants import *
    from ..data.items import MAX_ITEM_LEVEL
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import MAX_ITEM_LEVEL

class MenuController:
    def _refresh_point_confirm_quantity(self, game):
        action = getattr(self, "point_confirm_action", None)
        marker = repr(action)
        if getattr(self, "_point_confirm_action_marker", None) != marker:
            self.point_confirm_quantity = 1
            self._point_confirm_action_marker = marker

        max_quantity = self._point_confirm_max_quantity(action, game)
        self.point_confirm_max_quantity = max(1, max_quantity)
        self.point_confirm_quantity = max(
            1,
            min(getattr(self, "point_confirm_quantity", 1), self.point_confirm_max_quantity),
        )
        self.point_confirm_total_cost = self._point_confirm_total_cost(
            action,
            game,
            self.point_confirm_quantity,
        )

    def _point_confirm_max_quantity(self, action, game):
        if not action:
            return 1

        act = action[0]
        if act == "buy_shop_item":
            inv = game.get_inventory(game.menu_player_index)
            return max(1, inv.points // 15)

        if act == "upgrade_inventory":
            inv = game.get_inventory(game.menu_player_index)
            item = inv.get(action[1])
            if item is None or item.level >= MAX_ITEM_LEVEL:
                return 1
            cost = 7 if item.is_relic else (3 if item.is_hybrid else 1)
            return max(1, min(MAX_ITEM_LEVEL - item.level, inv.points // cost))

        if act == "upgrade_skill":
            player = game.get_player(game.menu_player_index)
            inv = game.get_inventory(game.menu_player_index)
            key = action[1]
            level = player.passives.get(key, 0)
            if level >= 10:
                return 1

            points = inv.points
            quantity = 0
            while level + quantity < 10:
                step_cost = self._skill_step_cost(game, key, level + quantity)
                if points < step_cost:
                    break
                points -= step_cost
                quantity += 1
            return max(1, quantity)

        return 1

    def _point_confirm_total_cost(self, action, game, quantity):
        if not action:
            return getattr(self, "point_confirm_cost", 0)

        act = action[0]
        if act in ("buy_shop_item", "upgrade_inventory"):
            return getattr(self, "point_confirm_cost", 0) * quantity

        if act == "upgrade_skill":
            player = game.get_player(game.menu_player_index)
            key = action[1]
            level = player.passives.get(key, 0)
            return sum(self._skill_step_cost(game, key, level + step) for step in range(quantity))

        return getattr(self, "point_confirm_cost", 0)

    def _skill_step_cost(self, game, key, level):
        player = game.get_player(game.menu_player_index)
        data = CHARACTERS[player.char_class]["passives"].get(key, {})
        is_special = data.get("category") == "Especial"
        if level <= 0:
            return SPECIAL_SKILL_UNLOCK_COST if is_special else SKILL_UNLOCK_COST
        return SPECIAL_SKILL_UPGRADE_COST if is_special else SKILL_UPGRADE_COST

    def _point_confirm_has_quantity(self):
        return getattr(self, "point_confirm_max_quantity", 1) > 1

    def _clear_point_confirm_quantity(self):
        self.point_confirm_quantity = 1
        self.point_confirm_max_quantity = 1
        self.point_confirm_total_cost = getattr(self, "point_confirm_cost", 0)
        self._point_confirm_action_marker = None

    def _adjust_point_confirm_quantity(self, delta, game):
        self._refresh_point_confirm_quantity(game)
        if not self._point_confirm_has_quantity():
            return
        self.point_confirm_quantity = max(
            1,
            min(self.point_confirm_quantity + delta, self.point_confirm_max_quantity),
        )
        self.point_confirm_total_cost = self._point_confirm_total_cost(
            self.point_confirm_action,
            game,
            self.point_confirm_quantity,
        )

    def _handle_point_confirm_choice(self, action, game):
        self._refresh_point_confirm_quantity(game)
        if action == "point_confirm_decrease":
            self._adjust_point_confirm_quantity(-1, game)
            return "point_confirm"
        if action == "point_confirm_increase":
            self._adjust_point_confirm_quantity(1, game)
            return "point_confirm"
        if action == "point_confirm_yes":
            return self._handle_point_confirm_action(self.point_confirm_action, game, self.point_confirm_return)
        if action == "point_confirm_no":
            self._clear_point_confirm_quantity()
            return self.point_confirm_return
        return "point_confirm"

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
                return screen, applied_fullscreen
            except pygame.error:
                continue

        return pygame.display.get_surface(), False

    def _handle_point_confirm_action(self, action, game, return_state):
        if not action:
            return return_state
        act = action[0]
        quantity = getattr(self, "point_confirm_quantity", 1)
        if act == "roll_stat_shop":
            game.roll_stat_shop()
        elif act == "purchase_stat_shop":
            game.purchase_stat_shop_offer(action[1])
        elif act == "reroll_stat_shop":
            game.reroll_stat_shop_offer(action[1])
        elif act == "upgrade_skill":
            done = 0
            for _ in range(quantity):
                if not game.upgrade_skill(action[1]):
                    break
                done += 1
            if done > 1:
                game.message = f"Skill aprimorada {done} vezes."
        elif act == "upgrade_inventory":
            done = 0
            for _ in range(quantity):
                if not game.upgrade_inventory_item(action[1]):
                    break
                done += 1
            if done > 1:
                game.message = f"Item aprimorado {done} vezes."
        elif act == "buy_shop_item":
            done = 0
            for _ in range(quantity):
                if not game.buy_shop_item(action[1]):
                    break
                done += 1
            if done > 1:
                game.message = f"Compra realizada {done} vezes."
        elif act == "transform_inventory":
            inv = game.get_inventory(game.menu_player_index)
            success, msg = inv.attempt_transformation(action[1], game.random)
            game.message = msg
        elif act == "sell_inventory":
            inv = game.get_inventory(game.menu_player_index)
            success, msg = inv.sell_item(action[1])
            game.message = msg
        self._clear_point_confirm_quantity()
        return return_state

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
            # "Voltar ao Menu" dentro da partida: retorna ao menu inicial do jogo sem encerrar
            state = "start"
        elif action == "quit":
            # "Fechar": encerra a sessao e retorna ao Arcade
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
        active_items = [item for item in raw_items if inv.is_active(item.slot_key)]
        reserve_items = [item for item in raw_items if not inv.is_active(item.slot_key)]
        items = active_items + reserve_items
        if action == "resume":
            return "playing", selected
        if action.startswith("item_select:"):
            return state, int(action.split(":", 1)[1])
        if not items:
            return state, selected

        selected = min(selected, len(items) - 1)
        slot_key = items[selected].slot_key
        if action == "item_toggle":
            game.toggle_inventory_item(slot_key)
        elif action == "item_upgrade":
            cost = 7 if items[selected].is_relic else (3 if items[selected].is_hybrid else 1)
            if inv.points >= cost:
                self.point_confirm_action = ("upgrade_inventory", slot_key)
                self.point_confirm_cost = cost
                self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar este item?"
                self.point_confirm_return = "inventory"
                self.point_confirm_selected = 1
                return "point_confirm", selected
            else:
                game.message = f"Pontos insuficientes (custa {cost})."
        elif action == "item_fuse":
            game.mark_or_fuse_item(slot_key)
            if game.has_pending_fusion():
                return "fusion_confirm", selected
            selected = min(selected, max(0, len(inv.item_list()) - 1))
        elif action == "item_sell":
            if not inv.is_active(items[selected].slot_key):
                value = inv.get_sell_value(items[selected].slot_key)
                self.point_confirm_action = ("sell_inventory", items[selected].slot_key)
                self.point_confirm_cost = 0 # No cost, we gain points
                self.point_confirm_msg = f"Deseja vender este item por {value} ponto(s)?"
                self.point_confirm_return = "inventory"
                self.point_confirm_selected = 1
                return "point_confirm", selected
            else:
                game.message = "Desequipe o item antes de vende-lo."
        return state, selected

    def _handle_stat_shop_action(self, action, game, return_state):
        if action == "stat_shop_back":
            return return_state
        if action == "stat_shop_roll":
            if game.inventory.points >= STAT_SHOP_ROLL_COST:
                self.point_confirm_action = ("roll_stat_shop",)
                self.point_confirm_cost = STAT_SHOP_ROLL_COST
                self.point_confirm_msg = f"Deseja gastar {STAT_SHOP_ROLL_COST} ponto(s) para abrir a loja?"
                self.point_confirm_return = "stat_shop"
                self.point_confirm_selected = 1
                return "point_confirm"
            else:
                game.message = f"Pontos insuficientes (custa {STAT_SHOP_ROLL_COST})."
                return "stat_shop"
        if action.startswith("stat_shop_buy:"):
            idx = int(action.split(":", 1)[1])
            cost = game.stat_shop_offers[idx]["cost"]
            if game.inventory.points >= cost:
                self.point_confirm_action = ("purchase_stat_shop", idx)
                self.point_confirm_cost = cost
                self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para comprar esta melhoria?"
                self.point_confirm_return = "stat_shop"
                self.point_confirm_selected = 1
                return "point_confirm"
            else:
                game.message = f"Pontos insuficientes (custa {cost})."
                return "stat_shop"
        if action.startswith("stat_shop_reroll:"):
            idx = int(action.split(":", 1)[1])
            if game.inventory.points >= STAT_SHOP_REROLL_COST:
                self.point_confirm_action = ("reroll_stat_shop", idx)
                self.point_confirm_cost = STAT_SHOP_REROLL_COST
                self.point_confirm_msg = f"Deseja gastar {STAT_SHOP_REROLL_COST} ponto(s) para trocar esta oferta?"
                self.point_confirm_return = "stat_shop"
                self.point_confirm_selected = 1
                return "point_confirm"
            else:
                game.message = f"Pontos insuficientes (custa {STAT_SHOP_REROLL_COST})."
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
            key = keys[selected]
            cost = game.skill_upgrade_cost(key)
            level = game.get_player(game.menu_player_index).passives.get(key, 0)
            if level >= 10:
                game.message = "Skill ja esta no nivel maximo."
            elif game.get_inventory(game.menu_player_index).points >= cost:
                self.point_confirm_action = ("upgrade_skill", key)
                self.point_confirm_cost = cost
                self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar esta skill?"
                self.point_confirm_return = "skills"
                self.point_confirm_selected = 1
                return "point_confirm", selected
            else:
                game.message = f"Pontos insuficientes (custa {cost})."
        return state, selected

    def _handle_fusion_confirm_action(self, action, game, selected):
        inv = game.get_inventory(game.menu_player_index)
        if action == "fusion_confirm_yes":
            game.confirm_pending_fusion()
        elif action == "fusion_confirm_no":
            game.cancel_pending_fusion()
        selected = min(selected, max(0, len(inv.item_list()) - 1))
        return "inventory", selected


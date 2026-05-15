import pygame
if __package__:
    from ..data.constants import *
else:
    from Sobrevivencia.data.constants import *

class MenuController:
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
        if act == "roll_stat_shop":
            game.roll_stat_shop()
        elif act == "purchase_stat_shop":
            game.purchase_stat_shop_offer(action[1])
        elif act == "reroll_stat_shop":
            game.reroll_stat_shop_offer(action[1])
        elif act == "upgrade_skill":
            game.upgrade_skill(action[1])
        elif act == "upgrade_inventory":
            game.upgrade_inventory_item(action[1])
        elif act == "buy_shop_item":
            game.buy_shop_item(action[1])
        elif act == "transform_inventory":
            inv = game.get_inventory(game.menu_player_index)
            success, msg = inv.attempt_transformation(action[1], game.random)
            game.message = msg
        elif act == "sell_inventory":
            inv = game.get_inventory(game.menu_player_index)
            success, msg = inv.sell_item(action[1])
            game.message = msg
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
            cost = 7 if items[selected].is_relic else (3 if items[selected].is_hybrid else 1)
            if inv.points >= cost:
                self.point_confirm_action = ("upgrade_inventory", key)
                self.point_confirm_cost = cost
                self.point_confirm_msg = f"Deseja gastar {cost} ponto(s) para aprimorar este item?"
                self.point_confirm_return = "inventory"
                self.point_confirm_selected = 1
                return "point_confirm", selected
            else:
                game.message = f"Pontos insuficientes (custa {cost})."
        elif action == "item_fuse":
            game.mark_or_fuse_item(key)
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


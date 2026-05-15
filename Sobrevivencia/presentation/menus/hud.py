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

class HudMenu:
    def _draw_hud(self, game):
        if game.multiplayer and len(game.players) > 1:
            self._draw_coop_hud(game)
            return
        player = game.player
        pygame.draw.rect(self.screen, hex_color(COLORS["panel"]), (0, 0, SCREEN_WIDTH, 76))
        pygame.draw.line(self.screen, (30, 41, 59), (0, 76), (SCREEN_WIDTH, 76), 2)

        self._bar(24, 18, 250, 16, player.health / player.max_health, COLORS["health"], COLORS["health_bg"], "VIDA")
        self._bar(24, 45, 250, 12, player.xp / player.xp_to_next, COLORS["xp"], "#15361F", f"NV {player.level}")
        self._bar(304, 12, 136, 12, player.special_ranged / SPECIAL_MAX, COLORS["special"], "#0B2C3C", "ESP DIST")
        self._bar(304, 31, 136, 12, player.special_melee / SPECIAL_MAX, COLORS["sword"], "#3A2A08", "ESP MELEE")

        # Aviso pulsante quando ambas as barras estão cheias
        if player.special_ranged >= SPECIAL_MAX and player.special_melee >= SPECIAL_MAX:
            pulse = (pygame.time.get_ticks() // 400) % 2 == 0
            if pulse:
                suprema_surf = self.font_small.render("★ SUPREMA DISPONIVEL ★", True, (250, 204, 21))
                bg_w = suprema_surf.get_width() + 16
                bg_h = suprema_surf.get_height() + 6
                bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                pygame.draw.rect(bg_surf, (20, 10, 0, 200), bg_surf.get_rect(), border_radius=5)
                pygame.draw.rect(bg_surf, (250, 204, 21, 180), bg_surf.get_rect(), width=1, border_radius=5)
                self.screen.blit(bg_surf, (304, 50))
                self.screen.blit(suprema_surf, (312, 53))

        w_name = CHARACTERS[player.char_class][player.mode]
        mode_color = COLORS["sword"] if player.mode == "weapon_2" else COLORS["projectile"]
        self._pill(448, 18, 96, 23, w_name.upper(), mode_color)

        ammo_capacity = max(1, game.magazine_capacity())
        ammo_fill = player.ammo_magazine / ammo_capacity
        ammo_label = f"PNT {player.ammo_magazine}/{ammo_capacity}"
        if player.reload_timer > 0:
            ammo_fill = 1.0 - min(1.0, player.reload_timer / max(0.01, player.reload_duration))
            ammo_label = f"REC {player.reload_timer:.1f}"
        self._mini_cooldown(448, 44, 104, 23, ammo_label, ammo_fill)

        max_reserve = game.max_ammo_reserve_for(player)
        reserve_fill = player.ammo_reserve / max_reserve
        self._mini_cooldown(560, 44, 104, 23, f"RES {player.ammo_reserve}/{max_reserve}", reserve_fill)

        dash_fill = 1.0 - min(1.0, player.dash_cooldown / DASH_COOLDOWN)
        self._mini_cooldown(552, 18, 62, 23, "DASH", dash_fill)

        info = f"Abates {player.kills}   Moedas {player.coins}   Pontos {player.score}"
        self.screen.blit(self.font_small.render(info, True, hex_color(COLORS["text"])), (632, 17))
        passive_w = len(player.passives) * 24 + max(0, len(player.passives) - 1) * 4
        message_limit = max(120, SCREEN_WIDTH - 20 - passive_w - 640)
        message = game.message
        while len(message) > 4 and self.font_tiny.size(message + "...")[0] > message_limit:
            message = message[:-1]
        if message != game.message:
            message += "..."
        self.screen.blit(self.font_tiny.render(message, True, hex_color(COLORS["muted"])), (632, 44))

        self._draw_item_slots(game)
        self._draw_passive_slots(game)
        self._draw_stats_panel(game)
        self._draw_quest_panel(game)
        self._draw_buff_list(player, SCREEN_WIDTH - 24, 324, align_right=True)

    def _draw_coop_hud(self, game):
        pygame.draw.rect(self.screen, hex_color(COLORS["panel"]), (0, 0, SCREEN_WIDTH, 90))
        pygame.draw.line(self.screen, (30, 41, 59), (0, 90), (SCREEN_WIDTH, 90), 2)
        self._draw_player_hud_block(game, game.player, 24, 12, left=True)
        self._draw_player_hud_block(game, game.player2, SCREEN_WIDTH - 418, 12, left=False)

        coins = game.shared_coins
        score = sum(player.score for player in game.players)
        center_info = f"Moedas compartilhadas {coins}   Pontos {score}"
        self._center_text(center_info, self.font_small, 16, COLORS["text"])
        message = game.message
        while len(message) > 4 and self.font_tiny.size(message + "...")[0] > 360:
            message = message[:-1]
        if message != game.message:
            message += "..."
        self._center_text(message, self.font_tiny, 42, COLORS["muted"])
        if game.level_up_pending:
            self._center_text(f"Turno do Jogador {game.level_up_player_index + 1}", self.font_tiny, 64, COLORS["upgrade"])
        self._draw_coop_stats_panels(game)
        self._draw_quest_panel(game)
        self._draw_buff_list(game.player, 14, 410, align_right=False)
        if getattr(game, 'player2', None):
            self._draw_buff_list(game.player2, SCREEN_WIDTH - 14, 410, align_right=True)

    def _draw_player_hud_block(self, game, player, x, y, left=True):
        title = f"J{player.player_index + 1}  {CHARACTERS[player.char_class]['name']}"
        title_color = P2_AIM_COLOR if player.player_index == 1 else P1_AIM_COLOR
        self.screen.blit(self.font_tiny.render(title.upper(), True, hex_color(title_color)), (x, y))
        status = "CAIDO" if player.is_down else f"NV {player.level}"
        self._bar(x, y + 18, 220, 12, player.health / max(1, player.max_health), COLORS["health"], COLORS["health_bg"], f"VIDA {status}")
        self._bar(x, y + 36, 220, 10, player.special_ranged / SPECIAL_MAX, COLORS["special"], "#0B2C3C", "ESP DIST")
        self._bar(x, y + 52, 220, 10, player.special_melee / SPECIAL_MAX, COLORS["sword"], "#3A2A08", "ESP MELEE")
        capacity = max(1, game.magazine_capacity_for(player))
        ammo_fill = player.ammo_magazine / capacity
        ammo_label = f"PNT {player.ammo_magazine}/{capacity}"
        if player.reload_timer > 0:
            ammo_fill = 1.0 - min(1.0, player.reload_timer / max(0.01, player.reload_duration))
            ammo_label = f"REC {player.reload_timer:.1f}"
        self._mini_cooldown(x + 230, y + 18, 78, 22, ammo_label, ammo_fill)
        dash_fill = 1.0 - min(1.0, player.dash_cooldown / DASH_COOLDOWN)
        self._mini_cooldown(x + 230, y + 46, 78, 22, "DASH", dash_fill)

        max_res = game.max_ammo_reserve_for(player)
        res_fill = player.ammo_reserve / max_res
        self._mini_cooldown(x + 316, y + 18, 78, 22, f"RES {player.ammo_reserve}/{max_res}", res_fill)

    def _draw_passive_slots(self, game):
        player = game.player
        char_data = CHARACTERS[player.char_class]["passives"]
        slot_size = 24
        spacing = 4
        total_w = len(player.passives) * slot_size + max(0, len(player.passives) - 1) * spacing
        x = SCREEN_WIDTH - 20 - total_w
        y = 48
        for i, (key, lvl) in enumerate(player.passives.items()):
            rect = pygame.Rect(x + i * (slot_size + spacing), y, slot_size, slot_size)
            pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=16)
            pygame.draw.rect(self.screen, hex_color(COLORS["special"]), rect, width=1, border_radius=16)
            short = char_data[key]["short"]
            surf = self.font_tiny.render(short, True, hex_color(COLORS["text"]))
            self.screen.blit(surf, surf.get_rect(center=rect.center))

            lvl_surf = self.font_tiny.render(f"{lvl}", True, hex_color(COLORS["upgrade"]))
            lvl_rect = lvl_surf.get_rect(bottomright=(rect.right, rect.bottom))
            self.screen.blit(lvl_surf, lvl_rect)

    def _draw_item_slots(self, game):
        slot_size = 32
        spacing = 6
        total_w = MAX_ACTIVE_ITEMS * slot_size + (MAX_ACTIVE_ITEMS - 1) * spacing
        x = SCREEN_WIDTH - 20 - total_w
        y = 12

        active_items = game.inventory.active_items()

        for i in range(MAX_ACTIVE_ITEMS):
            rect = pygame.Rect(x + i * (slot_size + spacing), y, slot_size, slot_size)
            pygame.draw.rect(self.screen, (15, 23, 42), rect, border_radius=4)
            pygame.draw.rect(self.screen, (51, 65, 85), rect, width=1, border_radius=4)

            if i < len(active_items):
                item = active_items[i]
                # Gold border for relics
                if item.is_relic:
                    pygame.draw.rect(self.screen, (250, 180, 50), rect, width=2, border_radius=4)
                elif item.is_hybrid:
                    pygame.draw.rect(self.screen, hex_color(COLORS["upgrade"]), rect, width=1, border_radius=4)
                if item.is_hybrid or item.is_relic:
                    pygame.draw.circle(self.screen, hex_color(COLORS["upgrade"]), rect.center, 10)
                else:
                    if item.key in self.item_icons:
                        self.screen.blit(self.item_icons[item.key], (rect.x, rect.y))
                    else:
                        pygame.draw.circle(self.screen, hex_color(COLORS["special"]), rect.center, 10)

                lvl_surf = self.font_tiny.render(str(item.level), True, hex_color(COLORS["text"]))
                lvl_rect = lvl_surf.get_rect(bottomright=(rect.right - 1, rect.bottom))
                bg_rect = lvl_rect.inflate(4, 2)
                bg_surf = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
                pygame.draw.rect(bg_surf, (9, 14, 24, 210), bg_surf.get_rect(), border_radius=2)
                self.screen.blit(bg_surf, bg_rect.topleft)
                self.screen.blit(lvl_surf, lvl_rect)

    def _draw_buff_list(self, player, start_x, start_y, align_right=False):
        labels = {
            "freeze": "congelante",
            "speed": "velocidade",
            "power": "dano",
        }
        y = start_y
        
        active_buffs = []
        if player.shield_timer > 0:
            active_buffs.append(("escudo", player.shield_timer, COLORS["shield"]))
        for name, timer in player.buffs.items():
            active_buffs.append((labels.get(name, name), timer, COLORS["upgrade"]))
            
        for name, timer, color in active_buffs:
            text = f"{name} {timer:.0f}s"
            width = max(82, self.font_tiny.size(text)[0] + 18)
            x = start_x - width if align_right else start_x
            self._pill(x, y, width, 22, text, color)
            y += 28

    def _draw_coop_stats_panels(self, game):
        if game.player2 is None:
            return
        y = 180
        self._draw_stats_panel_for(game, game.player, game.get_inventory(0), 14, y, "Status J1")
        self._draw_stats_panel_for(game, game.player2, game.get_inventory(1), SCREEN_WIDTH - 214, y, "Status J2")

    def _draw_stats_panel(self, game):
        self._draw_stats_panel_for(game, game.player, game.inventory, SCREEN_WIDTH - 224, 94, "Status do boneco")

    def _draw_stats_panel_for(self, game, player, inv, x, y, title):
        terrain_key = game.world.terrain_at(player.pos.x, player.pos.y)
        terrain = TERRAIN_TYPES[terrain_key]
        max_speed = player.base_speed * game.effective_speed_multiplier_for(player)
        terrain_speed = max_speed * terrain["speed"]
        fire_rate = game.effective_attack_rate_multiplier_for(player, inv) / PROJECTILE_COOLDOWN
        w = 200
        h = 220
        pygame.draw.rect(self.screen, hex_color(COLORS["panel"]), (x, y, w, h), border_radius=6)
        pygame.draw.rect(self.screen, (51, 65, 85), (x, y, w, h), width=1, border_radius=6)
        self.screen.blit(self.font_small.render(title, True, hex_color(COLORS["text"])), (x + 14, y + 10))

        stats = [
            ("Vel max", f"{max_speed:.0f}"),
            (f"Terreno {terrain['name']}", f"{terrain_speed:.0f}"),
            ("Dano tiro", f"{game.projectile_damage_for(player, inv):.0f}"),
            ("Dano espada", f"{game.sword_damage_for(player, inv):.0f}"),
            ("Alcance espada", f"{game.sword_radius_for(player, inv):.0f}"),
            ("Ritmo tiro", f"{fire_rate:.1f}/s"),
            ("Balas/salva", str(1 + player.passives.get("multishot", 0))),
            ("Pente", f"{player.ammo_magazine}/{game.magazine_capacity_for(player)}"),
            ("Reserva", str(player.ammo_reserve)),
            ("Recarga", f"{player.reload_timer:.1f}s" if player.reload_timer > 0 else "pronta"),
        ]

        line_y = y + 38
        for label, value in stats:
            self.screen.blit(self.font_tiny.render(label, True, hex_color(COLORS["muted"])), (x + 14, line_y))
            value_surf = self.font_tiny.render(value, True, hex_color(COLORS["text"]))
            self.screen.blit(value_surf, (x + w - 14 - value_surf.get_width(), line_y))
            line_y += 17

        passive = f"Itens {len(inv.active_slots)}/{MAX_ACTIVE_ITEMS}  Pts {inv.points}"
        self.screen.blit(self.font_tiny.render(passive, True, hex_color(COLORS["poison"])), (x + 14, y + h - 24))

    def _bar(self, x, y, w, h, fill, color, bg, label):
        fill = max(0, min(1, fill))
        pygame.draw.rect(self.screen, hex_color(bg), (x, y, w, h), border_radius=4)
        pygame.draw.rect(self.screen, hex_color(color), (x, y, int(w * fill), h), border_radius=4)
        pygame.draw.rect(self.screen, (15, 23, 42), (x, y, w, h), width=1, border_radius=4)
        self.screen.blit(self.font_tiny.render(label, True, hex_color(COLORS["text"])), (x + 8, y - 1))

    def _pill(self, x, y, w, h, text, color):
        pygame.draw.rect(self.screen, hex_color(color), (x, y, w, h), border_radius=5)
        label = self.font_tiny.render(text, True, (9, 14, 24))
        self.screen.blit(label, (x + w // 2 - label.get_width() // 2, y + h // 2 - label.get_height() // 2))

    def _mini_cooldown(self, x, y, w, h, text, fill):
        pygame.draw.rect(self.screen, (30, 41, 59), (x, y, w, h), border_radius=5)
        pygame.draw.rect(self.screen, (34, 197, 94), (x, y, int(w * fill), h), border_radius=5)
        pygame.draw.rect(self.screen, (15, 23, 42), (x, y, w, h), width=1, border_radius=5)
        label = self.font_tiny.render(text, True, hex_color(COLORS["text"]))
        self.screen.blit(label, (x + w // 2 - label.get_width() // 2, y + h // 2 - label.get_height() // 2))

    def _draw_quest_panel(self, game):
        """Draws the quest panel on the left side, below the HUD."""
        x, y, w = 14, 90, 230
        q = game.quest

        if q is None:
            # Show cooldown until next quest
            wait = max(0, game.next_quest_timer)
            panel_h = 46
            overlay = pygame.Surface((w, panel_h), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (16, 25, 40, 190), overlay.get_rect(), border_radius=6)
            self.screen.blit(overlay, (x, y))
            pygame.draw.rect(self.screen, (30, 41, 59), (x, y, w, panel_h), width=1, border_radius=6)
            self.screen.blit(self.font_tiny.render("MISSAO", True, hex_color(COLORS["muted"])), (x + 10, y + 6))
            self.screen.blit(self.font_tiny.render(f"Proxima em {wait:.0f}s", True, hex_color(COLORS["muted_2"])), (x + 10, y + 24))
            return

        panel_h = 82
        overlay = pygame.Surface((w, panel_h), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (16, 25, 40, 210), overlay.get_rect(), border_radius=6)
        self.screen.blit(overlay, (x, y))
        pygame.draw.rect(self.screen, hex_color(COLORS["upgrade"]), (x, y, w, panel_h), width=1, border_radius=6)

        self.screen.blit(self.font_tiny.render("MISSAO ATIVA", True, hex_color(COLORS["upgrade"])), (x + 10, y + 6))

        # Wrap description
        desc = q["description"]
        line1 = desc[:32]
        line2 = desc[32:64] if len(desc) > 32 else ""
        self.screen.blit(self.font_tiny.render(line1, True, hex_color(COLORS["text"])), (x + 10, y + 22))
        if line2:
            self.screen.blit(self.font_tiny.render(line2, True, hex_color(COLORS["text"])), (x + 10, y + 34))

        # Progress bar
        target = q["target"]
        progress_fill = min(1.0, game.quest_progress / target) if target > 0 else 0
        bar_y = y + 52
        pygame.draw.rect(self.screen, (30, 41, 59), (x + 10, bar_y, w - 20, 8), border_radius=4)
        if progress_fill > 0:
            pygame.draw.rect(self.screen, hex_color(COLORS["xp"]), (x + 10, bar_y, int((w - 20) * progress_fill), 8), border_radius=4)

        # Timer
        timer_left = max(0, q["timer"])
        timer_color = COLORS["danger"] if timer_left < 10 else COLORS["muted"]
        timer_surf = self.font_tiny.render(f"{timer_left:.0f}s  +3 niveis", True, hex_color(timer_color))
        self.screen.blit(timer_surf, (x + 10, y + 64))


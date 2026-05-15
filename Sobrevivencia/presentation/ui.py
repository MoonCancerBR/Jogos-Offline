import math
from itertools import combinations, combinations_with_replacement

import pygame
from pygame.math import Vector2

if __package__:
    from ..data.constants import *
    from ..data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description
    from .ui_utils import hex_color
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description
    from Sobrevivencia.presentation.ui_utils import hex_color


if __package__:
    from .menus.hud import HudMenu
    from .menus.inventory_menu import InventoryMenu
    from .menus.shop_menus import ShopMenus
    from .menus.system_menus import SystemMenus
else:
    from Sobrevivencia.presentation.menus.hud import HudMenu
    from Sobrevivencia.presentation.menus.inventory_menu import InventoryMenu
    from Sobrevivencia.presentation.menus.shop_menus import ShopMenus
    from Sobrevivencia.presentation.menus.system_menus import SystemMenus

class UI(HudMenu, InventoryMenu, ShopMenus, SystemMenus):
    def __init__(self, screen):
        self.screen = screen
        self.font_big = pygame.font.SysFont("Segoe UI", 42, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.font = pygame.font.SysFont("Segoe UI", 18)
        self.font_small = pygame.font.SysFont("Segoe UI", 14)
        self.font_tiny = pygame.font.SysFont("Segoe UI", 12)

        self.item_icons = {}
        import os
        base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "items")
        for key in ["storm_core", "guardian_plate", "magnet_orb", "chrono_boots", "blade_relay"]:
            try:
                img = pygame.image.load(os.path.join(base_path, f"{key}.png")).convert_alpha()
                self.item_icons[key] = pygame.transform.scale(img, (32, 32))
            except Exception:
                pass

    def screen_to_world(self, screen_pos, camera):
        return Vector2(screen_pos[0] + camera.x, screen_pos[1] + camera.y)

    def world_to_screen(self, pos, camera):
        return int(pos.x - camera.x), int(pos.y - camera.y)

    def render_game(self, game, mouse_pos, flip=True, aim_from_joystick=False, p2_aim_pos=None):
        camera = Vector2(game.camera)
        if game.screen_shake > 0:
            shake = math.sin(game.time_alive * 72) * game.screen_shake
            camera.x += shake
            camera.y += math.cos(game.time_alive * 61) * game.screen_shake * 0.6

        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_terrain(game, camera)
        self._draw_hazards(game, camera)
        self._draw_world_objects(game, camera)
        self._draw_drops(game, camera)
        self._draw_projectiles(game, camera)
        self._draw_item_events(game, camera)
        self._draw_enemies(game, camera)
        self._draw_slashes(game, camera)
        self._draw_players(game, camera, mouse_pos, aim_from_joystick, p2_aim_pos)
        self._draw_special_blast(game, camera)
        self._draw_floaters(game, camera)
        self._draw_hud(game)
        if flip:
            pygame.display.flip()

    def _draw_terrain(self, game, camera):
        tile = WORLD_TILE_SIZE
        for x, y, size, kind, variation in game.world.iter_visible_terrain(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            data = TERRAIN_TYPES[kind]
            rect = pygame.Rect(int(x - camera.x), int(y - camera.y), size + 1, size + 1)
            pygame.draw.rect(self.screen, hex_color(data["color"]), rect)
            if variation > 0.62:
                accent = hex_color(data["accent"])
                if kind == "sand":
                    pygame.draw.line(self.screen, accent, (rect.left + 14, rect.top + 30), (rect.right - 16, rect.top + 22), 1)
                    pygame.draw.line(self.screen, accent, (rect.left + 26, rect.bottom - 24), (rect.right - 28, rect.bottom - 34), 1)
                elif kind == "grass":
                    pygame.draw.circle(self.screen, accent, (rect.left + tile // 3, rect.top + tile // 3), 3)
                    pygame.draw.circle(self.screen, accent, (rect.left + tile * 2 // 3, rect.top + tile * 2 // 3), 2)
                elif kind == "mud":
                    pygame.draw.ellipse(self.screen, accent, rect.inflate(-42, -58), 1)
                else:
                    pygame.draw.line(self.screen, accent, (rect.left + 8, rect.top + 8), (rect.right - 8, rect.bottom - 8), 1)

    def _draw_hazards(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for hazard in game.world.iter_visible_hazards(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            rect = hazard.rect
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            pulse = 0.5 + 0.5 * math.sin(game.time_alive * 6 + hazard.pulse)

            if hazard.kind == "fire":
                pygame.draw.rect(overlay, (239, 68, 68, 72), screen_rect, border_radius=8)
                pygame.draw.rect(overlay, (251, 146, 60, 130), screen_rect, width=2, border_radius=8)
                for index in range(5):
                    x = screen_rect.left + 12 + index * max(12, screen_rect.width // 5)
                    y = screen_rect.centery + math.sin(game.time_alive * 5 + index) * 10
                    pygame.draw.line(overlay, (254, 215, 170, 150), (x, y + 14), (x + 8, y - 14), 2)
            elif hazard.kind == "ice":
                pygame.draw.rect(overlay, (125, 211, 252, 64), screen_rect, border_radius=8)
                pygame.draw.rect(overlay, (186, 230, 253, 132), screen_rect, width=2, border_radius=8)
                for index in range(4):
                    y = screen_rect.top + 16 + index * max(12, screen_rect.height // 4)
                    pygame.draw.line(overlay, (224, 242, 254, 125), (screen_rect.left + 12, y), (screen_rect.right - 12, y - 8), 1)
            elif hazard.kind == "mine":
                center = screen_rect.center
                radius = int(13 + pulse * 3)
                pygame.draw.circle(overlay, (127, 29, 29, 210), center, radius)
                pygame.draw.circle(overlay, (248, 113, 113, 210), center, radius + 4, 2)
                pygame.draw.line(overlay, (254, 226, 226, 190), (center[0] - 6, center[1]), (center[0] + 6, center[1]), 2)
                pygame.draw.line(overlay, (254, 226, 226, 190), (center[0], center[1] - 6), (center[0], center[1] + 6), 2)
        self.screen.blit(overlay, (0, 0))

    def _draw_world_objects(self, game, camera):
        for rect in game.world.iter_visible_obstacles(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            pygame.draw.rect(self.screen, (31, 41, 55), screen_rect, border_radius=5)
            pygame.draw.rect(self.screen, (15, 23, 42), screen_rect, width=2, border_radius=5)
            pygame.draw.line(self.screen, (71, 85, 105), screen_rect.topleft, screen_rect.topright, 1)

        for item in game.world.iter_visible_destructibles(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            rect = item.rect
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            if item.kind == "special":
                color = (56, 189, 248)
            elif item.kind == "cache":
                color = (245, 158, 11)
            else:
                color = (146, 64, 14)
            if item.hit_flash > 0:
                color = (253, 230, 138)
            pygame.draw.rect(self.screen, color, screen_rect, border_radius=4)
            pygame.draw.rect(self.screen, (69, 26, 3), screen_rect, width=2, border_radius=4)
            pygame.draw.line(self.screen, (254, 215, 170), screen_rect.topleft, screen_rect.bottomright, 1)

    def _draw_drops(self, game, camera):
        for drop in game.drops:
            x, y = self.world_to_screen(drop.pos + Vector2(0, math.sin(drop.bob) * 3), camera)
            if drop.kind == "xp":
                pygame.draw.circle(self.screen, hex_color(COLORS["xp"]), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (187, 247, 208), (x, y), int(drop.radius * 0.45))
            elif drop.kind == "ammo":
                pygame.draw.rect(self.screen, (103, 232, 249), (x - 7, y - 4, 14, 8), border_radius=3)
                pygame.draw.rect(self.screen, (8, 47, 73), (x - 7, y - 4, 14, 8), 1, border_radius=3)
                pygame.draw.circle(self.screen, (224, 242, 254), (x + 6, y), 3)
            elif drop.kind == "coin":
                pygame.draw.circle(self.screen, hex_color(COLORS["coin"]), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (113, 63, 18), (x, y), int(drop.radius), 2)
            elif drop.kind == "heal":
                pygame.draw.circle(self.screen, hex_color(COLORS["health"]), (x, y), int(drop.radius))
                pygame.draw.line(self.screen, (255, 255, 255), (x - 5, y), (x + 5, y), 2)
                pygame.draw.line(self.screen, (255, 255, 255), (x, y - 5), (x, y + 5), 2)
            elif drop.kind == "shield":
                pygame.draw.circle(self.screen, hex_color(COLORS["shield"]), (x, y), int(drop.radius), 3)
                pygame.draw.circle(self.screen, (191, 219, 254), (x, y), int(drop.radius * 0.45))
            elif drop.kind == "item_box":
                rect = pygame.Rect(x - int(drop.radius), y - int(drop.radius), int(drop.radius * 2), int(drop.radius * 2))
                pygame.draw.rect(self.screen, hex_color(COLORS["special"]), rect, border_radius=4)
                pygame.draw.rect(self.screen, (224, 242, 254), rect, 2, border_radius=4)
                pygame.draw.line(self.screen, (8, 47, 73), (x - 5, y), (x + 5, y), 2)
                pygame.draw.line(self.screen, (8, 47, 73), (x, y - 5), (x, y + 5), 2)

    def _draw_projectiles(self, game, camera):
        for projectile in game.projectiles:
            x, y = self.world_to_screen(projectile.pos, camera)
            if projectile.freeze:
                color = COLORS["projectile_freeze"]
            elif projectile.poison:
                color = COLORS["poison"]
            else:
                color = COLORS["projectile"]
            pygame.draw.circle(self.screen, hex_color(color), (x, y), int(projectile.radius + 2))
            pygame.draw.circle(self.screen, (8, 47, 73), (x, y), int(projectile.radius), 1)

    def _draw_item_events(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for event in game.item_events:
            event_type = event.get("type", "storm")
            if event_type == "arrow_rain":
                alpha = max(0, min(1, event["timer"] * 2))
                pos = event["pos"] - camera
                radius = event["radius"]
                rgba = (255, 100, 100, int(150 * alpha))
                pygame.draw.circle(overlay, rgba, (int(pos.x), int(pos.y)), int(radius), 2)
                for i in range(5):
                    ox = math.sin(game.time_alive * 20 + i) * radius * 0.8
                    oy = math.cos(game.time_alive * 15 + i) * radius * 0.8
                    pygame.draw.line(overlay, rgba, (pos.x + ox, pos.y + oy - 40), (pos.x + ox, pos.y + oy), 2)
            elif event_type == "danger_circle":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                pos = event["pos"] - camera
                radius = event["radius"]
                pulse_radius = radius * (0.86 + 0.14 * math.sin(game.time_alive * 18))
                pygame.draw.circle(overlay, (248, 113, 113, int(56 + 70 * alpha)), (int(pos.x), int(pos.y)), int(pulse_radius))
                pygame.draw.circle(overlay, (254, 226, 226, int(210 * alpha)), (int(pos.x), int(pos.y)), int(radius), 4)
            elif event_type == "danger_line":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                width = int(event.get("width", 42))
                pygame.draw.line(overlay, (248, 113, 113, int(82 + 80 * alpha)), (start.x, start.y), (end.x, end.y), width)
                pygame.draw.line(overlay, (254, 226, 226, int(220 * alpha)), (start.x, start.y), (end.x, end.y), 3)
            elif event_type == "laser":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 0.2))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                width = int(event.get("width", 44))
                pygame.draw.line(overlay, (251, 146, 60, int(210 * alpha)), (start.x, start.y), (end.x, end.y), width)
                pygame.draw.line(overlay, (255, 247, 237, int(245 * alpha)), (start.x, start.y), (end.x, end.y), max(3, width // 5))
            elif event_type == "explosion":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 0.2))
                alpha = max(0, 1 - age / duration)
                pos = event["pos"] - camera
                current_radius = event["radius"] * (1 - alpha**2)
                rgba = (255, 200, 50, int(200 * alpha))
                pygame.draw.circle(overlay, rgba, (int(pos.x), int(pos.y)), int(current_radius))
            elif event_type == "summon_pulse":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 2.0))
                alpha = max(0, 1 - age / duration)
                pulse = 0.5 + 0.5 * math.sin(age * 10)
                pos = event["pos"] - camera
                radius = int(event["radius"] * (0.85 + 0.15 * pulse))
                pygame.draw.circle(overlay, (192, 132, 252, int(110 * alpha)), (int(pos.x), int(pos.y)), radius)
                pygame.draw.circle(overlay, (216, 180, 254, int(200 * alpha)), (int(pos.x), int(pos.y)), radius, 4)
            else:
                if "start" not in event or "end" not in event:
                    continue
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                color = hex_color(event.get("color", "#FFFFFF"))
                rgba = (*color, int(220 * alpha))
                pygame.draw.line(overlay, rgba, (start.x, start.y), (end.x, end.y), 4)
                pygame.draw.circle(overlay, rgba, (int(end.x), int(end.y)), 18, 2)
        self.screen.blit(overlay, (0, 0))

    def _draw_enemies(self, game, camera):
        for enemy in game.enemies:
            x, y = self.world_to_screen(enemy.pos, camera)
            color = (255, 255, 255) if enemy.hit_flash > 0 else hex_color(enemy.color)
            if enemy.kind == "chromatic" and enemy.hit_flash <= 0:
                palette = [
                    (34, 211, 238),
                    (236, 72, 153),
                    (250, 204, 21),
                    (74, 222, 128),
                    (167, 139, 250),
                ]
                color = palette[int(game.time_alive * 14 + enemy.id) % len(palette)]
            if enemy.frozen_timer > 0:
                color = (125, 211, 252)
            pygame.draw.circle(self.screen, color, (x, y), int(enemy.radius))
            if enemy.poison_timer > 0:
                pygame.draw.circle(self.screen, hex_color(COLORS["poison"]), (x, y), int(enemy.radius + 4), 2)
            if getattr(enemy, "bleed_timer", 0) > 0:
                pygame.draw.circle(self.screen, (248, 113, 113), (x, y), int(enemy.radius + 7), 2)
            pygame.draw.circle(self.screen, (25, 25, 35), (x, y), int(enemy.radius), 2)
            if enemy.kind == "miniboss":
                pulse = int(4 + math.sin(game.time_alive * 5) * 2)
                pygame.draw.circle(self.screen, (254, 226, 226), (x, y), int(enemy.radius + pulse), 3)
                pygame.draw.circle(self.screen, (196, 181, 253), (x - 14, y - 10), 5)
                pygame.draw.circle(self.screen, (196, 181, 253), (x + 14, y - 10), 5)
                if enemy.action:
                    pygame.draw.circle(self.screen, hex_color(COLORS["danger"]), (x, y), int(enemy.radius + 12), 2)
            elif enemy.kind == "chromatic":
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), int(enemy.radius + 6), 2)
                if enemy.lifetime > 0:
                    arc_rect = pygame.Rect(x - enemy.radius - 8, y - enemy.radius - 8, int((enemy.radius + 8) * 2), int((enemy.radius + 8) * 2))
                    pygame.draw.arc(self.screen, (226, 232, 240), arc_rect, -math.pi / 2, -math.pi / 2 + math.tau * (enemy.lifetime / CHROMATIC_LIFETIME), 3)
            elif enemy.kind == "brute":
                pygame.draw.circle(self.screen, (254, 226, 226), (x - 7, y - 5), 3)
                pygame.draw.circle(self.screen, (254, 226, 226), (x + 7, y - 5), 3)
            elif enemy.kind == "runner":
                pygame.draw.polygon(self.screen, (255, 228, 230), [(x, y - 7), (x + 8, y + 7), (x - 8, y + 7)])
            elif enemy.kind == "spitter":
                pygame.draw.circle(self.screen, (236, 252, 203), (x + 5, y - 4), 4)
                if enemy.action:
                    pygame.draw.circle(self.screen, (190, 242, 100), (x, y), int(enemy.radius + 8), 2)
            elif enemy.kind == "bulwark":
                pygame.draw.circle(self.screen, (203, 213, 225), (x, y), int(enemy.radius + 8), 2)
                pygame.draw.rect(self.screen, (15, 23, 42), (x - 11, y - 7, 22, 14), 2, border_radius=3)
            elif enemy.kind == "sapper":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 12 + enemy.id)
                pygame.draw.circle(self.screen, (254, 240, 138), (x, y), int(enemy.radius + 5 + pulse * 3), 2)
            elif enemy.kind == "minion":
                glow_r = int(enemy.radius + 5)
                pygame.draw.circle(self.screen, (216, 180, 254), (x, y), glow_r, 2)
                pygame.draw.circle(self.screen, (192, 132, 252), (x, y), int(enemy.radius * 0.45))

            if enemy.health < enemy.max_health:
                bar_w = int(enemy.radius * 2.0)
                bar_rect = pygame.Rect(x - bar_w // 2, y - int(enemy.radius) - 10, bar_w, 4)
                pygame.draw.rect(self.screen, (64, 20, 26), bar_rect)
                bar_rect.width = int(bar_w * max(0, enemy.health / enemy.max_health))
                pygame.draw.rect(self.screen, (248, 113, 113), bar_rect)

    def _draw_slashes(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for slash in game.slashes:
            progress = min(1.0, slash.age / max(0.01, slash.duration))
            origin = slash.origin - camera
            base_angle = math.atan2(slash.direction.y, slash.direction.x)
            start = base_angle - slash.arc * 0.5
            end = base_angle + slash.arc * 0.5
            points = [(origin.x, origin.y)]
            steps = 12
            radius = slash.radius * (0.82 + 0.18 * progress)
            for i in range(steps + 1):
                angle = start + (end - start) * (i / steps)
                points.append((origin.x + math.cos(angle) * radius, origin.y + math.sin(angle) * radius))
            pygame.draw.polygon(overlay, (253, 224, 71, int(120 * (1 - progress * 0.55))), points)
            pygame.draw.lines(overlay, (254, 243, 199, 210), False, points[1:], 4)
        self.screen.blit(overlay, (0, 0))

    def _draw_players(self, game, camera, mouse_pos, aim_from_joystick=False, p2_aim_pos=None):
        aim_positions = {0: mouse_pos}
        aim_modes = {0: aim_from_joystick}
        if p2_aim_pos is not None:
            aim_positions[1] = p2_aim_pos
            aim_modes[1] = True
        for player in game.players:
            self._draw_player(game, camera, player, aim_positions.get(player.player_index, mouse_pos), aim_modes.get(player.player_index, False))

    def _draw_player(self, game, camera, player, mouse_pos, aim_from_joystick=False):
        x, y = self.world_to_screen(player.pos, camera)
        aim = Vector2(mouse_pos) - Vector2(x, y)
        if aim.length_squared() <= 0:
            aim = Vector2(1, 0)
        aim = aim.normalize()
        nose = Vector2(x, y) + aim * (player.radius + 11)
        left = Vector2(x, y) + aim.rotate(132) * (player.radius * 0.86)
        right = Vector2(x, y) + aim.rotate(-132) * (player.radius * 0.86)

        aim_color = hex_color(P2_AIM_COLOR if player.player_index == 1 else P1_AIM_COLOR)
        pygame.draw.line(self.screen, aim_color, (x, y), mouse_pos, 1)
        if aim_from_joystick:
            self._draw_joystick_aim_pointer(mouse_pos, aim, aim_color)
        if player.shield_timer > 0:
            pulse = 5 + int(math.sin(game.time_alive * 12) * 2)
            pygame.draw.circle(self.screen, hex_color(COLORS["shield"]), (x, y), int(player.radius + 12 + pulse), 3)
        elif player.invulnerable_timer > 0:
            pygame.draw.circle(self.screen, (148, 163, 184), (x, y), int(player.radius + 7), 2)

        char_data = CHARACTERS[player.char_class]
        color = hex_color(char_data["color"])
        core = hex_color(char_data["core_color"])

        if player.is_down:
            pygame.draw.circle(self.screen, (71, 85, 105), (x, y), int(player.radius))
            pygame.draw.line(self.screen, aim_color, (x - 16, y - 16), (x + 16, y + 16), 4)
            pygame.draw.line(self.screen, aim_color, (x + 16, y - 16), (x - 16, y + 16), 4)
            progress = player.revive_progress / max(0.01, REVIVE_TIME)
            pygame.draw.circle(self.screen, aim_color, (x, y), int(REVIVE_RADIUS), 2)
            self._bar(x - 36, y - 48, 72, 8, progress, COLORS["xp"], COLORS["panel_2"], f"RESGATE J{player.player_index + 1}")
        else:
            pygame.draw.circle(self.screen, color, (x, y), int(player.radius))
            if char_data["shape"] == "circle_triangle":
                pygame.draw.polygon(self.screen, core, [nose, left, right])
            else:
                pygame.draw.circle(self.screen, core, (x, y), int(player.radius * 0.4))

        pygame.draw.circle(self.screen, (15, 23, 42), (x, y), int(player.radius), 2)

        if not player.is_down and player.ammo_magazine <= 0:
            pulse = (pygame.time.get_ticks() // 250) % 2 == 0
            if pulse:
                msg = "SEM MUNICAO!" if player.ammo_reserve <= 0 else "RECARREGANDO"
                color = hex_color(COLORS["health"]) if player.ammo_reserve <= 0 else hex_color(COLORS["coin"])
                ammo_text = self.font_small.render(msg, True, color)
                text_rect = ammo_text.get_rect(center=(x, y - int(player.radius) - 20))
                
                # Create a semi-transparent background
                bg_surf = pygame.Surface((text_rect.width + 12, text_rect.height + 6), pygame.SRCALPHA)
                pygame.draw.rect(bg_surf, (15, 23, 42, 200), bg_surf.get_rect(), border_radius=4)
                self.screen.blit(bg_surf, (text_rect.x - 6, text_rect.y - 3))
                self.screen.blit(ammo_text, text_rect)

        # Relic aura: two rotating fire circles
        inv = game.get_inventory(player.player_index)
        has_relic = any(item.is_relic for item in inv.active_items())
        if has_relic:
            aura_r = 82
            overlay_aura = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(2):
                angle = game.relic_aura_angle + i * math.pi
                cx2 = int(x + math.cos(angle) * aura_r * 0.72)
                cy2 = int(y + math.sin(angle) * aura_r * 0.72)
                pygame.draw.circle(overlay_aura, (250, 160, 50, 170), (cx2, cy2), 12)
                pygame.draw.circle(overlay_aura, (255, 210, 100, 90), (cx2, cy2), 20)
            pygame.draw.circle(overlay_aura, (167, 139, 250, 40), (x, y), aura_r)
            pygame.draw.circle(overlay_aura, (250, 180, 50, 100), (x, y), aura_r, 2)
            self.screen.blit(overlay_aura, (0, 0))

    def _draw_joystick_aim_pointer(self, mouse_pos, aim, aim_color=(56, 189, 248)):
        cx, cy = int(mouse_pos[0]), int(mouse_pos[1])
        ticks = pygame.time.get_ticks()
        pulse = 0.5 + 0.5 * math.sin(ticks * 0.005)

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)

        # Outer glow ring (pulsing)
        outer_r = int(18 + pulse * 3)
        glow_alpha = int(40 + 30 * pulse)
        pygame.draw.circle(overlay, (*aim_color, glow_alpha), (cx, cy), outer_r + 6)
        pygame.draw.circle(overlay, (*aim_color, int(150 + 60 * pulse)), (cx, cy), outer_r, 2)

        # Cross lines (4 lines radiating from center with a gap)
        gap = 5
        line_len = int(12 + pulse * 2)
        cross_color = (226, 232, 240, 220)
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            x1 = cx + dx * gap
            y1 = cy + dy * gap
            x2 = cx + dx * (gap + line_len)
            y2 = cy + dy * (gap + line_len)
            pygame.draw.line(overlay, cross_color, (x1, y1), (x2, y2), 2)

        # Bright center dot
        pygame.draw.circle(overlay, (255, 255, 255, 240), (cx, cy), 2)

        # Small directional arrow showing aim direction
        arrow_tip = Vector2(cx, cy) + aim * (outer_r + 10 + pulse * 2)
        side = aim.rotate(90)
        arrow_left = arrow_tip - aim * 7 + side * 4
        arrow_right = arrow_tip - aim * 7 - side * 4
        pygame.draw.polygon(overlay, (*aim_color, int(180 + 50 * pulse)),
                            [(int(arrow_tip.x), int(arrow_tip.y)),
                             (int(arrow_left.x), int(arrow_left.y)),
                             (int(arrow_right.x), int(arrow_right.y))])

        self.screen.blit(overlay, (0, 0))

    def _draw_special_blast(self, game, camera):
        if game.special_blast_timer <= 0:
            return
        player = game.player
        progress = 1 - game.special_blast_timer / 0.35
        radius = int(game.special_radius() * progress)
        x, y = self.world_to_screen(player.pos, camera)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (56, 189, 248, int(105 * (1 - progress))), (x, y), radius, 8)
        pygame.draw.circle(overlay, (165, 243, 252, int(60 * (1 - progress))), (x, y), max(1, radius // 2), 0)
        self.screen.blit(overlay, (0, 0))

    def _draw_floaters(self, game, camera):
        for floater in game.floaters:
            alpha = max(0, 1 - floater["age"] / floater["duration"])
            x, y = self.world_to_screen(floater["pos"], camera)
            surf = self.font_tiny.render(floater["text"], True, hex_color(floater["color"]))
            surf.set_alpha(int(255 * alpha))
            self.screen.blit(surf, (x - surf.get_width() // 2, y - 14))












































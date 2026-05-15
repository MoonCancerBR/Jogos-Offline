import math
from itertools import combinations, combinations_with_replacement

import pygame
from pygame.math import Vector2

if __package__:
    from ..data.constants import *
    from ..data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description


def hex_color(value):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


class UI:
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
            title = self.font_tiny.render(f"{category.upper()} | {p_data['title']}", True, hex_color(COLORS["text"]))
            desc = self.font_tiny.render(p_data["description"][:58], True, hex_color(COLORS["muted"]))
            self.screen.blit(title, (x, y))
            self.screen.blit(desc, (x, y + 16))

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
                    lvl_text = self.font_tiny.render(str(passives[i][1]), True, hex_color(COLORS["bg"]))
                    self.screen.blit(lvl_text, (slot_rect.centerx - lvl_text.get_width() // 2, slot_rect.centery - lvl_text.get_height() // 2))

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
        self.screen.blit(self.font_tiny.render("ACAO", True, hex_color(COLORS["muted"])), (panel.x + 22, panel.y + 18))
        self.screen.blit(self.font_tiny.render("PRIMARIO", True, hex_color(COLORS["muted"])), (slot_x[0] + 30, panel.y + 18))
        self.screen.blit(self.font_tiny.render("ALT.", True, hex_color(COLORS["muted"])), (slot_x[1] + 56, panel.y + 18))
        self.screen.blit(self.font_tiny.render("CONTROLE", True, hex_color(COLORS["muted"])), (slot_x[2] + 36, panel.y + 18))

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

            label = self.font_small.render(row["label"], True, hex_color(COLORS["text"]))
            self.screen.blit(label, (row_rect.x + 12, row_rect.y + 5))

            for slot in range(len(row["bindings"])):
                binding_rect = pygame.Rect(slot_x[slot], row_rect.y + 4, slot_w, 22)
                waiting = capture_binding == (row["action"], slot)
                slot_active = active and selected_slot == slot
                color = COLORS["special"] if waiting else (COLORS["upgrade"] if slot_active else COLORS["panel_2"])
                pygame.draw.rect(self.screen, hex_color(color), binding_rect, border_radius=4)
                pygame.draw.rect(self.screen, (226, 232, 240), binding_rect, width=1 if waiting or slot_active else 0, border_radius=4)
                text = "Pressione..." if waiting else row["bindings"][slot]
                surf = self.font_tiny.render(text[:18], True, hex_color(COLORS["text"]))
                self.screen.blit(surf, (binding_rect.centerx - surf.get_width() // 2, binding_rect.y + 4))
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

    def render_stat_shop(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 224))
        self.screen.blit(overlay, (0, 0))

        buttons = []
        panel = pygame.Rect(58, 48, SCREEN_WIDTH - 116, SCREEN_HEIGHT - 96)
        pygame.draw.rect(self.screen, (8, 14, 25), panel, border_radius=8)
        pygame.draw.rect(self.screen, hex_color(COLORS["xp"]), panel, width=2, border_radius=8)

        title = self.font_title.render("LOJA DE STATUS", True, hex_color(COLORS["text"]))
        self.screen.blit(title, (panel.x + 28, panel.y + 18))
        points_label = "Pontos disponiveis" if not game.multiplayer else "Pontos da equipe"
        points = self.font_small.render(f"{points_label}: {game.inventory.points}", True, hex_color(COLORS["xp"]))
        self.screen.blit(points, (panel.right - points.get_width() - 28, panel.y + 22))

        if not game.stat_shop_unlocked():
            current_level = max(player.level for player in game.players)
            needed = max(0, STAT_SHOP_UNLOCK_LEVEL - current_level)
            self._center_text(f"Desbloqueia no nivel {STAT_SHOP_UNLOCK_LEVEL}", self.font_big, 214, COLORS["text"])
            self._center_text(f"Maior nivel atual {current_level}. Faltam {needed} niveis.", self.font, 276, COLORS["muted"])
            self._center_text("Depois de desbloqueada, use pontos de nivel para roletar status permanentes.", self.font_small, 322, COLORS["muted"])
            buttons.append(self._button(panel.centerx - 110, panel.bottom - 56, 220, 40, "Voltar", "stat_shop_back", mouse_pos, COLORS["muted_2"]))
            # pygame.display.flip()
            return buttons

        subtitle = self.font_tiny.render(
            f"Roletar abre 3 ofertas por {STAT_SHOP_ROLL_COST} ponto. Jogar novamente uma oferta custa {STAT_SHOP_REROLL_COST} ponto.",
            True,
            hex_color(COLORS["muted"]),
        )
        self.screen.blit(subtitle, (panel.x + 28, panel.y + 52))

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

            title = self.font.render(offer["title"].upper(), True, hex_color(COLORS["text"]))
            self.screen.blit(title, (rect.x + 18, rect.y + 16))
            tier = self.font_tiny.render(f"FORCA {offer.get('power', 1)}", True, hex_color(rank_color))
            self.screen.blit(tier, (rect.right - tier.get_width() - 18, rect.y + 20))

            line_y = rect.y + 62
            for effect in offer["effects"]:
                label = self.font_small.render(effect["label"], True, hex_color(COLORS["text"]))
                value = self.font_small.render(effect["display"], True, hex_color(COLORS["xp"]))
                self.screen.blit(label, (rect.x + 18, line_y))
                self.screen.blit(value, (rect.x + 18, line_y + 24))
                line_y += 58

            cost = offer["cost"]
            cost_color = COLORS["coin"] if game.inventory.points >= cost else COLORS["danger"]
            cost_surf = self.font_small.render(f"Custo de compra: {cost} pts", True, hex_color(cost_color))
            self.screen.blit(cost_surf, (rect.x + 18, rect.bottom - 106))

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
        turn_surf = self.font_title.render(turn_text, True, turn_color)
        self.screen.blit(turn_surf, (SCREEN_WIDTH // 2 - turn_surf.get_width() // 2, 210))

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
            title_surf = self.font_title.render(data["title"], True, text_color)
            desc_surf = self.font_small.render(data["description"], True, text_color if active else hex_color(COLORS["muted"]))
            
            self.screen.blit(title_surf, (rect.x + 24, rect.y + 12))
            self.screen.blit(desc_surf, (rect.x + 24, rect.y + 47))
            buttons.append((key, rect))
            y += 94
        
        # pygame.display.flip() # Handled by main loop
        return buttons

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

        title = self.font_title.render("GERENCIAMENTO DE SKILLS", True, hex_color(COLORS["text"]))
        self.screen.blit(title, (panel.x + 28, panel.y + 18))
        switch_hint = "  |  Y/P troca jogador" if game.multiplayer else ""
        subtitle = self.font_tiny.render(
            f"Jogador {game.menu_player_index + 1}  |  Pontos de item {inv.points}  |  A/X/U/Enter upa skill{switch_hint}",
            True,
            hex_color(COLORS["muted"]),
        )
        self.screen.blit(subtitle, (panel.x + 28, panel.y + 50))
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
            self.screen.blit(self.font_tiny.render(label[:42], True, hex_color(COLORS["text"])), (rect.x + 10, rect.y + 4))
            self.screen.blit(self.font_tiny.render(category.upper(), True, self._skill_category_color(category)), (rect.x + 10, rect.y + 18))
            lvl = self.font_tiny.render(f"NV {level}/10  {state}", True, hex_color(COLORS["xp"] if level > 0 else COLORS["muted"]))
            self.screen.blit(lvl, (rect.right - lvl.get_width() - 10, rect.y + 9))
            buttons.append((f"skill_select:{index}", rect))
            y += 37

        if selected_key:
            skill = data[selected_key]
            level = player.passives[selected_key]
            category = skill.get("category", "Kit")
            cost = game.skill_upgrade_cost(selected_key)
            rank_color = self._skill_category_color(category)

            self.screen.blit(self.font_tiny.render(category.upper(), True, rank_color), (detail_rect.x + 22, detail_rect.y + 20))
            y = detail_rect.y + 48
            for line in self._wrap_text(skill["title"], 34)[:2]:
                self.screen.blit(self.font_title.render(line, True, hex_color(COLORS["text"])), (detail_rect.x + 22, y))
                y += 30
            y += 8
            state = "Desbloqueada" if level > 0 else "Ainda bloqueada"
            self.screen.blit(self.font_small.render(f"{state} | Nivel {level}/10", True, hex_color(COLORS["muted"])), (detail_rect.x + 22, y))
            y += 34
            for line in self._wrap_text(skill["description"], 58)[:4]:
                self.screen.blit(self.font_small.render(line, True, hex_color(COLORS["text"])), (detail_rect.x + 22, y))
                y += 22

            y += 14
            cost_text = f"Custo do proximo upgrade: {cost} pontos"
            if level >= 10:
                cost_text = "Skill no nivel maximo."
            self.screen.blit(self.font_small.render(cost_text, True, rank_color), (detail_rect.x + 22, y))

            can_upgrade = level < 10 and inv.points >= cost
            button_color = COLORS["xp"] if can_upgrade else COLORS["muted_2"]
            buttons.append(self._button(detail_rect.x + 22, detail_rect.bottom - 62, 220, 40, "Upar Skill", "skill_upgrade", mouse_pos, button_color))

        buttons.append(self._button(panel.centerx - 110, panel.bottom - 52, 220, 38, "Voltar", "skills_back", mouse_pos, COLORS["muted_2"]))
        # pygame.display.flip()
        return buttons

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

        title = self.font_title.render("CONSTRUCOES", True, hex_color(COLORS["text"]))
        self.screen.blit(title, (panel.x + 28, panel.y + 16))
        subtitle = self.font_tiny.render("Itens separados por tier, com arvore de fusao e resultado final.", True, hex_color(COLORS["muted"]))
        self.screen.blit(subtitle, (panel.x + 236, panel.y + 26))

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
            self.screen.blit(self.font_tiny.render(label, True, header_color), (list_rect.x + 14, y))
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
                self.screen.blit(self.font_tiny.render(name[:45], True, color), (rect.x + 24, rect.y + 2))
                buttons.append((f"construction_select:{index}", rect))
                y += 19
                index += 1
            y += 4

        self._draw_construction_detail(game, selected_item, detail_rect)
        buttons.append(self._button(panel.centerx - 110, panel.bottom - 52, 220, 38, "Voltar", "constructions_back", mouse_pos, COLORS["muted_2"]))
        # pygame.display.flip()
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

    def _draw_construction_detail(self, game, item, rect):
        rank_label, rank_color = self._rank_title(item)
        self.screen.blit(self.font_tiny.render(rank_label, True, rank_color), (rect.x + 22, rect.y + 18))

        y = rect.y + 42
        for line in self._wrap_text(item_display_name(item), 38)[:3]:
            self.screen.blit(self.font_title.render(line, True, hex_color(COLORS["text"])), (rect.x + 22, y))
            y += 30

        y += 4
        for line in self._wrap_text(item_short_description(item), 58)[:3]:
            self.screen.blit(self.font_small.render(line, True, hex_color(COLORS["muted"])), (rect.x + 24, y))
            y += 19

        tree_rect = pygame.Rect(rect.x + 20, rect.y + 172, rect.w - 40, rect.h - 194)
        self._draw_build_tree(game, item, tree_rect)

    def _draw_build_tree(self, game, item, rect):
        pygame.draw.rect(self.screen, (8, 14, 24), rect, border_radius=6)
        pygame.draw.rect(self.screen, (39, 52, 73), rect, width=1, border_radius=6)
        self.screen.blit(self.font_tiny.render("ARVORE DE CONSTRUCAO", True, (179, 147, 74)), (rect.x + 12, rect.y + 10))

        if item.rank == 1:
            node = pygame.Rect(rect.centerx - 96, rect.y + 72, 192, 112)
            self._draw_tree_node(item, node, game, selected=True, show_level=False)
            for index, line in enumerate(self._wrap_text("Item base encontrado em caixas especiais e recompensas.", 56)[:2]):
                surf = self.font_tiny.render(line, True, hex_color(COLORS["muted"]))
                self.screen.blit(surf, (rect.centerx - surf.get_width() // 2, node.bottom + 20 + index * 16))
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
            surf = self.font_tiny.render(line, True, hex_color(COLORS["text"]))
            self.screen.blit(surf, (rect.centerx - surf.get_width() // 2, y))
            y += 14

        if rect.h >= 84:
            tier_surf = self.font_tiny.render(rank_label.split(" - ")[0], True, rank_color)
            self.screen.blit(tier_surf, (rect.x + 6, rect.bottom - 16))

    def _hybrid_preview_item(self, sources):
        sources = tuple(sorted(sources))
        return InventoryItem(key="hybrid:" + "+".join(sources), hybrid_sources=sources)

    def _catalog_label(self, item):
        if item.is_relic:
            relic_key = item.key[len("relic:"):]
            return RELIC_DEFINITIONS.get(relic_key, {}).get("short", item_display_name(item))
        if item.is_hybrid:
            return " + ".join(ITEM_DEFINITIONS[key]["short"] for key in item.hybrid_sources)
        return item_display_name(item)

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
        surf = font.render(text, True, hex_color(color))
        self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))

    def _button(self, x, y, w, h, text, action, mouse_pos, color, selected=False):
        rect = pygame.Rect(x, y, w, h)
        hover = rect.collidepoint(mouse_pos)
        base = hex_color(color)
        if hover or selected:
            base = tuple(min(255, channel + 24) for channel in base)
        pygame.draw.rect(self.screen, base, rect, border_radius=7)
        pygame.draw.rect(self.screen, (226, 232, 240), rect, width=3 if selected else 1, border_radius=7)
        surf = self.font.render(text, True, (7, 17, 30) if color not in (COLORS["panel_2"], COLORS["muted_2"]) else hex_color(COLORS["text"]))
        self.screen.blit(surf, (x + w // 2 - surf.get_width() // 2, y + h // 2 - surf.get_height() // 2))
        return action, rect

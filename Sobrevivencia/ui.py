import math

import pygame
from pygame.math import Vector2

if __package__:
    from .constants import *
else:
    from constants import *


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

    def screen_to_world(self, screen_pos, camera):
        return Vector2(screen_pos[0] + camera.x, screen_pos[1] + camera.y)

    def world_to_screen(self, pos, camera):
        return int(pos.x - camera.x), int(pos.y - camera.y)

    def render_game(self, game, mouse_pos, flip=True):
        camera = Vector2(game.camera)
        if game.screen_shake > 0:
            shake = math.sin(game.time_alive * 72) * game.screen_shake
            camera.x += shake
            camera.y += math.cos(game.time_alive * 61) * game.screen_shake * 0.6

        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_terrain(game, camera)
        self._draw_world_objects(game, camera)
        self._draw_drops(game, camera)
        self._draw_projectiles(game, camera)
        self._draw_enemies(game, camera)
        self._draw_slashes(game, camera)
        self._draw_player(game, camera, mouse_pos)
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

    def _draw_world_objects(self, game, camera):
        for rect in game.world.iter_visible_obstacles(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            pygame.draw.rect(self.screen, (31, 41, 55), screen_rect, border_radius=5)
            pygame.draw.rect(self.screen, (15, 23, 42), screen_rect, width=2, border_radius=5)
            pygame.draw.line(self.screen, (71, 85, 105), screen_rect.topleft, screen_rect.topright, 1)

        for item in game.world.iter_visible_destructibles(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            rect = item.rect
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            color = (245, 158, 11) if item.kind == "cache" else (146, 64, 14)
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

    def _draw_enemies(self, game, camera):
        for enemy in game.enemies:
            x, y = self.world_to_screen(enemy.pos, camera)
            color = (255, 255, 255) if enemy.hit_flash > 0 else hex_color(enemy.color)
            if enemy.frozen_timer > 0:
                color = (125, 211, 252)
            pygame.draw.circle(self.screen, color, (x, y), int(enemy.radius))
            if enemy.poison_timer > 0:
                pygame.draw.circle(self.screen, hex_color(COLORS["poison"]), (x, y), int(enemy.radius + 4), 2)
            pygame.draw.circle(self.screen, (25, 25, 35), (x, y), int(enemy.radius), 2)
            if enemy.kind == "brute":
                pygame.draw.circle(self.screen, (254, 226, 226), (x - 7, y - 5), 3)
                pygame.draw.circle(self.screen, (254, 226, 226), (x + 7, y - 5), 3)
            elif enemy.kind == "runner":
                pygame.draw.polygon(self.screen, (255, 228, 230), [(x, y - 7), (x + 8, y + 7), (x - 8, y + 7)])

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

    def _draw_player(self, game, camera, mouse_pos):
        player = game.player
        x, y = self.world_to_screen(player.pos, camera)
        aim = Vector2(mouse_pos) - Vector2(x, y)
        if aim.length_squared() <= 0:
            aim = Vector2(1, 0)
        aim = aim.normalize()
        nose = Vector2(x, y) + aim * (player.radius + 11)
        left = Vector2(x, y) + aim.rotate(132) * (player.radius * 0.86)
        right = Vector2(x, y) + aim.rotate(-132) * (player.radius * 0.86)

        pygame.draw.line(self.screen, (56, 189, 248), (x, y), mouse_pos, 1)
        if player.shield_timer > 0:
            pulse = 5 + int(math.sin(game.time_alive * 12) * 2)
            pygame.draw.circle(self.screen, hex_color(COLORS["shield"]), (x, y), int(player.radius + 12 + pulse), 3)
        elif player.invulnerable_timer > 0:
            pygame.draw.circle(self.screen, (148, 163, 184), (x, y), int(player.radius + 7), 2)

        pygame.draw.circle(self.screen, hex_color(COLORS["player"]), (x, y), int(player.radius))
        pygame.draw.polygon(self.screen, hex_color(COLORS["player_core"]), [nose, left, right])
        pygame.draw.circle(self.screen, (15, 23, 42), (x, y), int(player.radius), 2)

    def _draw_special_blast(self, game, camera):
        if game.special_blast_timer <= 0:
            return
        player = game.player
        progress = 1 - game.special_blast_timer / 0.35
        radius = int(SPECIAL_RADIUS * progress)
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
        player = game.player
        pygame.draw.rect(self.screen, hex_color(COLORS["panel"]), (0, 0, SCREEN_WIDTH, 76))
        pygame.draw.line(self.screen, (30, 41, 59), (0, 76), (SCREEN_WIDTH, 76), 2)

        self._bar(24, 18, 250, 16, player.health / player.max_health, COLORS["health"], COLORS["health_bg"], "VIDA")
        self._bar(24, 45, 250, 12, player.xp / player.xp_to_next, COLORS["xp"], "#15361F", f"NV {player.level}")
        self._bar(304, 18, 220, 16, player.special / SPECIAL_MAX, COLORS["special"], "#0B2C3C", "ESPECIAL")

        mode_color = COLORS["sword"] if player.mode == "sword" else COLORS["projectile"]
        mode_text = "ESPADA" if player.mode == "sword" else "PROJETIL"
        self._pill(304, 44, 110, 23, mode_text, mode_color)

        dash_fill = 1.0 - min(1.0, player.dash_cooldown / DASH_COOLDOWN)
        self._mini_cooldown(432, 44, 92, 23, "DASH", dash_fill)

        info = f"Abates {player.kills}   Moedas {player.coins}   Pontos {player.score}"
        self.screen.blit(self.font_small.render(info, True, hex_color(COLORS["text"])), (560, 17))
        self.screen.blit(self.font_tiny.render(game.message, True, hex_color(COLORS["muted"])), (560, 44))

        self._draw_buff_list(player)
        self._draw_stats_panel(game)

    def _draw_buff_list(self, player):
        labels = {
            "freeze": "congelante",
            "speed": "velocidade",
            "power": "dano",
        }
        x = SCREEN_WIDTH - 190
        y = 44
        if player.shield_timer > 0:
            self._pill(x, y, 78, 22, f"escudo {player.shield_timer:.0f}s", COLORS["shield"])
            x -= 92
        for name, timer in player.buffs.items():
            text = f"{labels.get(name, name)} {timer:.0f}s"
            width = max(82, self.font_tiny.size(text)[0] + 18)
            x -= width + 8
            self._pill(x, y, width, 22, text, COLORS["upgrade"])

    def _draw_stats_panel(self, game):
        player = game.player
        terrain_key = game.world.terrain_at(player.pos.x, player.pos.y)
        terrain = TERRAIN_TYPES[terrain_key]
        max_speed = player.base_speed * player.speed_multiplier()
        terrain_speed = max_speed * terrain["speed"]
        fire_rate = player.attack_rate_multiplier() / PROJECTILE_COOLDOWN
        x = SCREEN_WIDTH - 224
        y = 94
        w = 200
        h = 174
        pygame.draw.rect(self.screen, hex_color(COLORS["panel"]), (x, y, w, h), border_radius=6)
        pygame.draw.rect(self.screen, (51, 65, 85), (x, y, w, h), width=1, border_radius=6)
        self.screen.blit(self.font_small.render("Status do boneco", True, hex_color(COLORS["text"])), (x + 14, y + 10))

        stats = [
            ("Vel max", f"{max_speed:.0f}"),
            (f"Terreno {terrain['name']}", f"{terrain_speed:.0f}"),
            ("Dano tiro", f"{player.projectile_damage():.0f}"),
            ("Dano espada", f"{player.sword_damage():.0f}"),
            ("Alcance espada", f"{player.sword_radius():.0f}"),
            ("Ritmo tiro", f"{fire_rate:.1f}/s"),
            ("Balas/salva", str(player.projectile_count())),
        ]

        line_y = y + 38
        for label, value in stats:
            self.screen.blit(self.font_tiny.render(label, True, hex_color(COLORS["muted"])), (x + 14, line_y))
            value_surf = self.font_tiny.render(value, True, hex_color(COLORS["text"]))
            self.screen.blit(value_surf, (x + w - 14 - value_surf.get_width(), line_y))
            line_y += 17

        passive = f"Ric {player.ricochet_bounces}  Ven {player.poison_level}  Vamp {player.vampirism:.0f}"
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

    def render_start(self, mouse_pos):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        self._center_text("SOBREVIVENCIA", self.font_big, 142, COLORS["text"])
        self._center_text("Top-down shooter/slasher infinito", self.font, 190, COLORS["muted"])
        self._center_text("WASD move  |  Mouse mira  |  Q alterna arma  |  Espaco dash  |  E especial", self.font_small, 232, COLORS["muted"])
        buttons = []
        buttons.append(self._button(410, 300, 280, 48, "Iniciar Jogo", "start", mouse_pos, COLORS["xp"]))
        buttons.append(self._button(410, 362, 280, 48, "Comandos", "commands", mouse_pos, COLORS["special"]))
        buttons.append(self._button(410, 424, 280, 48, "Voltar ao Menu", "menu", mouse_pos, COLORS["muted_2"]))
        pygame.display.flip()
        return buttons

    def render_pause(self, game, options, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        return self._overlay_menu("PAUSADO", options, selected, mouse_pos)

    def render_game_over(self, game, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        title = "FIM DA SOBREVIVENCIA"
        options = [("Reiniciar", "restart"), ("Voltar ao Menu", "menu"), ("Fechar", "quit")]
        return self._overlay_menu(title, options, 0, mouse_pos, extra=f"Tempo {int(game.time_alive)}s  |  Abates {game.player.kills}  |  Pontos {game.player.score}")

    def render_commands(self, mouse_pos):
        self.screen.fill(hex_color(COLORS["bg"]))
        self._draw_menu_background()
        self._center_text("COMANDOS", self.font_big, 110, COLORS["text"])
        lines = [
            "WASD ou setas: mover pelo mapa infinito",
            "Mouse: direcao dos tiros e golpes automaticos",
            "Q ou Shift: alternar entre projetil e espada",
            "Espaco: dash com recarga e invulnerabilidade curta",
            "E: especial quando a barra azul estiver cheia",
            "Colete XP para subir de nivel; a cada 5 niveis vem melhoria grande.",
            "Moedas ativam buffs temporarios; escudos repelem inimigos.",
        ]
        y = 190
        for line in lines:
            self._center_text(line, self.font, y, COLORS["muted"])
            y += 36
        buttons = [self._button(410, 470, 280, 48, "Voltar", "back", mouse_pos, COLORS["muted_2"])]
        pygame.display.flip()
        return buttons

    def render_upgrade(self, game, selected, mouse_pos):
        self.render_game(game, mouse_pos, flip=False)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 205))
        self.screen.blit(overlay, (0, 0))
        title = "MELHORIA GRANDE" if game.upgrade_is_major else "NOVO NIVEL"
        subtitle = "Escolha um poder permanente raro" if game.upgrade_is_major else "Escolha um upgrade permanente"
        self._center_text(title, self.font_big, 116, COLORS["text"])
        self._center_text(subtitle, self.font, 166, COLORS["muted"])
        buttons = []
        y = 244
        for index, key in enumerate(game.upgrade_choices):
            data = UPGRADES.get(key) or MAJOR_UPGRADES[key]
            rect = pygame.Rect(260, y, 580, 78)
            hover = rect.collidepoint(mouse_pos) or index == selected
            color = hex_color(COLORS["upgrade"] if hover else COLORS["panel_2"])
            pygame.draw.rect(self.screen, color, rect, border_radius=7)
            pygame.draw.rect(self.screen, (226, 232, 240), rect, width=1 if hover else 0, border_radius=7)
            title = self.font_title.render(data["title"], True, hex_color(COLORS["text"]))
            desc = self.font_small.render(data["description"], True, hex_color(COLORS["muted"] if not hover else COLORS["text"]))
            self.screen.blit(title, (rect.x + 24, rect.y + 12))
            self.screen.blit(desc, (rect.x + 24, rect.y + 47))
            buttons.append((key, rect))
            y += 94
        pygame.display.flip()
        return buttons

    def _overlay_menu(self, title, options, selected, mouse_pos, extra=None):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 10, 18, 192))
        self.screen.blit(overlay, (0, 0))
        self._center_text(title, self.font_big, 145, COLORS["text"])
        if extra:
            self._center_text(extra, self.font, 198, COLORS["muted"])
        buttons = []
        start_y = 260 if extra else 235
        for index, (label, action) in enumerate(options):
            color = COLORS["upgrade"] if index == selected else COLORS["panel_2"]
            buttons.append(self._button(410, start_y + index * 62, 280, 48, label, action, mouse_pos, color))
        pygame.display.flip()
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
        surf = font.render(text, True, hex_color(color))
        self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))

    def _button(self, x, y, w, h, text, action, mouse_pos, color):
        rect = pygame.Rect(x, y, w, h)
        hover = rect.collidepoint(mouse_pos)
        base = hex_color(color)
        if hover:
            base = tuple(min(255, channel + 24) for channel in base)
        pygame.draw.rect(self.screen, base, rect, border_radius=7)
        pygame.draw.rect(self.screen, (226, 232, 240), rect, width=1, border_radius=7)
        surf = self.font.render(text, True, (7, 17, 30) if color not in (COLORS["panel_2"], COLORS["muted_2"]) else hex_color(COLORS["text"]))
        self.screen.blit(surf, (x + w // 2 - surf.get_width() // 2, y + h // 2 - surf.get_height() // 2))
        return action, rect

import math
from itertools import combinations, combinations_with_replacement

import pygame
import pygame.freetype
from pygame.math import Vector2

if __package__:
    from ..config.runtime import NullGUIManager, TweeningFallback, logger, optional_import
    from ..data.constants import *
    from ..data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description
    from .ui_utils import hex_color
else:
    from Sobrevivencia.config.runtime import NullGUIManager, TweeningFallback, logger, optional_import
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.data.items import BASE_ITEM_KEYS, ITEM_DEFINITIONS, InventoryItem, MAX_ACTIVE_ITEMS, MAX_ITEM_LEVEL, item_display_name, item_short_description
    from Sobrevivencia.presentation.ui_utils import hex_color


if __package__:
    from .menus.hud import HudMenu
    from .menus.inventory_menu import InventoryMenu
    from .menus.inventory_gui import InventoryGUI
    from .menus.shop_menus import ShopMenus
    from .menus.system_menus import SystemMenus
    from .animation_manager import AnimationManager
    from .particle_manager import ParticleManager

else:
    from Sobrevivencia.presentation.menus.hud import HudMenu
    from Sobrevivencia.presentation.menus.inventory_menu import InventoryMenu
    from Sobrevivencia.presentation.menus.inventory_gui import InventoryGUI
    from Sobrevivencia.presentation.menus.shop_menus import ShopMenus
    from Sobrevivencia.presentation.menus.system_menus import SystemMenus
    from Sobrevivencia.presentation.animation_manager import AnimationManager
    from Sobrevivencia.presentation.particle_manager import ParticleManager

moderngl = optional_import("moderngl")
np = optional_import("numpy")
pygame_gui = optional_import("pygame_gui")
pytweening = optional_import("pytweening") or TweeningFallback


class UI(HudMenu, InventoryMenu, InventoryGUI, ShopMenus, SystemMenus):
    def __init__(self, screen):
        self.screen_original = screen
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen = self.game_surface  # Redireciona desenhos legados para a superfície offscreen
        self.ctx = None
        if moderngl is not None and np is not None:
            try:
                self.ctx = moderngl.create_context()
                logger.info(f"Contexto ModernGL criado: {self.ctx.info}")

                # ModernGL Setup
                self.quad_buffer = self.ctx.buffer(np.array([
                    # x, y, u, v
                    -1.0,  1.0, 0.0, 0.0, # TL
                     1.0,  1.0, 1.0, 0.0, # TR
                    -1.0, -1.0, 0.0, 1.0, # BL
                     1.0,  1.0, 1.0, 0.0, # TR
                     1.0, -1.0, 1.0, 1.0, # BR
                    -1.0, -1.0, 0.0, 1.0, # BL
                ], dtype='f4'))

                self.prog = self.ctx.program(
                    vertex_shader='''
                        #version 330
                        in vec2 in_vert;
                        in vec2 in_texcoord;
                        out vec2 v_texcoord;
                        void main() {
                            gl_Position = vec4(in_vert, 0.0, 1.0);
                            v_texcoord = in_texcoord;
                        }
                    ''',
                    fragment_shader='''
                        #version 330
                        uniform sampler2D Texture;
                        in vec2 v_texcoord;
                        out vec4 f_color;

                        void main() {
                            f_color = texture(Texture, v_texcoord);
                            f_color.a = 1.0;
                        }
                    '''
                )
                self.vao = self.ctx.vertex_array(self.prog, [
                    (self.quad_buffer, '2f 2f', 'in_vert', 'in_texcoord')
                ])
                self.tex = self.ctx.texture((SCREEN_WIDTH, SCREEN_HEIGHT), 4)
                self.tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            except Exception as e:
                logger.warning(f"ModernGL indisponivel ({e}). Usando renderizador CPU.")
                self.ctx = None

        pygame.freetype.init()
        # Escala dinamica: base 1100x720, ajusta fontes pela menor dimensao.
        import os
        ui_scale = max(0.85, min(1.25, min(SCREEN_WIDTH / 1100.0, SCREEN_HEIGHT / 720.0)))
        self.font_big   = pygame.freetype.SysFont("Segoe UI", int(42 * ui_scale), bold=True)
        self.font_title = pygame.freetype.SysFont("Segoe UI", int(26 * ui_scale), bold=True)
        self.font       = pygame.freetype.SysFont("Segoe UI", int(18 * ui_scale))
        self.font_small = pygame.freetype.SysFont("Segoe UI", int(16 * ui_scale))
        self.font_tiny  = pygame.freetype.SysFont("Segoe UI", int(13 * ui_scale))
        self.animation_manager = AnimationManager()
        self.particle_manager = ParticleManager()
        _theme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "theme.json")
        if pygame_gui is not None:
            try:
                self.gui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), _theme_path)
            except Exception:
                self.gui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.gui_manager = NullGUIManager()
        self.init_inventory_gui()

        self.item_icons = {}
        _base_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "items")
        for key in ["storm_core", "guardian_plate", "magnet_orb", "chrono_boots", "blade_relay"]:
            try:
                img = pygame.image.load(os.path.join(_base_path, f"{key}.png")).convert_alpha()
                self.item_icons[key] = pygame.transform.scale(img, (32, 32))
            except Exception:
                pass

    def screen_to_world(self, screen_pos, camera):
        return Vector2(screen_pos[0] + camera.x, screen_pos[1] + camera.y)

    def world_to_screen(self, pos, camera):
        return int(pos.x - camera.x), int(pos.y - camera.y)

    def _rgb(self, color):
        return hex_color(color)[:3]

    def _blend(self, color, target, amount):
        base = self._rgb(color)
        target = self._rgb(target)
        return tuple(int(base[i] + (target[i] - base[i]) * amount) for i in range(3))

    def _draw_soft_circle(self, center, radius, color, alpha=80, rings=3):
        radius = max(1, int(radius))
        size = radius * 2 + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        rgb = self._rgb(color)
        for index in range(rings, 0, -1):
            r = max(1, int(radius * index / rings))
            a = max(0, int(alpha * (index / rings) ** 1.8))
            pygame.draw.circle(surf, (*rgb, a), (size // 2, size // 2), r)
        self.screen.blit(surf, (int(center[0] - size // 2), int(center[1] - size // 2)))

    def _draw_shadow(self, center, radius, alpha=92, y_scale=0.36):
        w = max(4, int(radius * 2.25))
        h = max(3, int(radius * y_scale))
        surf = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, alpha), (2, 2, w, h))
        self.screen.blit(surf, (int(center[0] - w / 2), int(center[1] + radius * 0.48)))

    def _draw_star(self, center, outer, inner, color, points=5, angle_offset=-math.pi / 2):
        pts = []
        for i in range(points * 2):
            r = outer if i % 2 == 0 else inner
            ang = angle_offset + i * math.pi / points
            pts.append((center[0] + math.cos(ang) * r, center[1] + math.sin(ang) * r))
        pygame.draw.polygon(self.screen, color, pts)

    def render_game(self, game, mouse_pos, dt=0.016, flip=True, aim_from_joystick=False, p2_aim_pos=None):
        self.animation_manager.update(dt)
        self.particle_manager.update(dt)
        self.gui_manager.update(dt)
        for event in game.particle_events:
            self.particle_manager.emit(event["pos"], count=event.get("count", 10), color=event.get("color", "#FFFFFF"), speed=event.get("speed", 50), lifetime=event.get("lifetime", 0.5), size=event.get("size", 4))
        game.particle_events.clear()

        camera = Vector2(game.camera)
        if game.screen_shake > 0:
            shake = math.sin(game.time_alive * 72) * game.screen_shake
            camera.x += shake
            camera.y += math.cos(game.time_alive * 61) * game.screen_shake * 0.6

        # Draw to offscreen surface
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
        self.particle_manager.render(self.screen, camera)
        self._draw_floaters(game, camera)
        self._draw_hud(game)
        self.gui_manager.draw_ui(self.screen)
        # Present via ModernGL if available, otherwise CPU blit
        if self.ctx:
            try:
                texture_data = pygame.image.tostring(self.game_surface, 'RGBA', False)
                self.tex.write(texture_data)
                self.ctx.viewport = (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
                self.ctx.clear(0.0, 0.0, 0.0)
                self.tex.use(0)
                self.prog['Texture'].value = 0
                self.vao.render(moderngl.TRIANGLES)
            except Exception as e:
                logger.error(f"Erro ModernGL: {e}")
                self.screen_original.blit(self.game_surface, (0, 0))
        else:
            self.screen_original.blit(self.game_surface, (0, 0))
        if flip:
            pygame.display.flip()

    def _draw_terrain(self, game, camera):
        tile = WORLD_TILE_SIZE
        for x, y, size, kind, variation in game.world.iter_visible_terrain(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            data = TERRAIN_TYPES[kind]
            rect = pygame.Rect(int(x - camera.x), int(y - camera.y), size + 1, size + 1)
            base = hex_color(data["color"])
            pygame.draw.rect(self.screen, base, rect)
            if variation < 0.18:
                pygame.draw.rect(self.screen, self._blend(base, "#020617", 0.08), rect)
            if variation > 0.62:
                accent = hex_color(data["accent"])
                if kind == "sand":
                    pygame.draw.circle(self.screen, self._blend(accent, "#FFFFFF", 0.18), (rect.left + tile // 3, rect.top + tile // 2), 2)
                    pygame.draw.line(self.screen, accent, (rect.left + 14, rect.top + 30), (rect.right - 16, rect.top + 22), 1)
                    pygame.draw.line(self.screen, accent, (rect.left + 26, rect.bottom - 24), (rect.right - 28, rect.bottom - 34), 1)
                elif kind == "grass":
                    pygame.draw.circle(self.screen, accent, (rect.left + tile // 3, rect.top + tile // 3), 3)
                    pygame.draw.circle(self.screen, accent, (rect.left + tile * 2 // 3, rect.top + tile * 2 // 3), 2)
                    pygame.draw.line(self.screen, self._blend(accent, "#FFFFFF", 0.08), (rect.left + 18, rect.bottom - 18), (rect.left + 28, rect.bottom - 30), 1)
                elif kind == "mud":
                    pygame.draw.ellipse(self.screen, self._blend(accent, "#020617", 0.25), rect.inflate(-42, -58), 1)
                    pygame.draw.ellipse(self.screen, accent, rect.inflate(-62, -72), 1)
                else:
                    pygame.draw.line(self.screen, accent, (rect.left + 8, rect.top + 8), (rect.right - 8, rect.bottom - 8), 1)
                    pygame.draw.line(self.screen, self._blend(accent, "#FFFFFF", 0.18), (rect.left + 18, rect.top + 58), (rect.right - 24, rect.top + 52), 1)

    def _draw_hazards(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for hazard in game.world.iter_visible_hazards(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            rect = hazard.rect
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            pulse = 0.5 + 0.5 * math.sin(game.time_alive * 6 + hazard.pulse)

            if hazard.kind == "fire":
                pygame.draw.rect(overlay, (127, 29, 29, 58), screen_rect.inflate(8, 8), border_radius=10)
                pygame.draw.rect(overlay, (239, 68, 68, 78), screen_rect, border_radius=8)
                pygame.draw.rect(overlay, (251, 146, 60, 150), screen_rect, width=2, border_radius=8)
                for index in range(5):
                    x = screen_rect.left + 12 + index * max(12, screen_rect.width // 5)
                    y = screen_rect.centery + math.sin(game.time_alive * 5 + index) * 10
                    pygame.draw.line(overlay, (254, 215, 170, 170), (x, y + 14), (x + 8, y - 14), 2)
                    pygame.draw.circle(overlay, (255, 247, 237, 120), (x + 8, int(y - 14)), max(2, int(3 + pulse * 2)))
            elif hazard.kind == "ice":
                pygame.draw.rect(overlay, (8, 47, 73, 64), screen_rect.inflate(6, 6), border_radius=10)
                pygame.draw.rect(overlay, (125, 211, 252, 70), screen_rect, border_radius=8)
                pygame.draw.rect(overlay, (186, 230, 253, 150), screen_rect, width=2, border_radius=8)
                for index in range(4):
                    y = screen_rect.top + 16 + index * max(12, screen_rect.height // 4)
                    pygame.draw.line(overlay, (224, 242, 254, 135), (screen_rect.left + 12, y), (screen_rect.right - 12, y - 8), 1)
                pygame.draw.line(overlay, (240, 249, 255, 95), screen_rect.topleft, screen_rect.bottomright, 1)
            elif hazard.kind == "mine":
                center = screen_rect.center
                radius = int(13 + pulse * 3)
                pygame.draw.circle(overlay, (248, 113, 113, int(34 + 36 * pulse)), center, radius + 13)
                pygame.draw.circle(overlay, (127, 29, 29, 230), center, radius)
                pygame.draw.circle(overlay, (248, 113, 113, 220), center, radius + 4, 2)
                pygame.draw.circle(overlay, (254, 226, 226, 220), center, max(3, radius // 3))
                pygame.draw.line(overlay, (254, 226, 226, 190), (center[0] - 6, center[1]), (center[0] + 6, center[1]), 2)
                pygame.draw.line(overlay, (254, 226, 226, 190), (center[0], center[1] - 6), (center[0], center[1] + 6), 2)
        self.screen.blit(overlay, (0, 0))

    def _draw_world_objects(self, game, camera):
        for rect in game.world.iter_visible_obstacles(camera.x, camera.y, SCREEN_WIDTH, SCREEN_HEIGHT):
            screen_rect = pygame.Rect(int(rect.x - camera.x), int(rect.y - camera.y), int(rect.w), int(rect.h))
            shadow = screen_rect.move(4, 6)
            pygame.draw.rect(self.screen, (6, 10, 18), shadow, border_radius=5)
            pygame.draw.rect(self.screen, (31, 41, 55), screen_rect, border_radius=5)
            pygame.draw.rect(self.screen, (15, 23, 42), screen_rect, width=2, border_radius=5)
            pygame.draw.line(self.screen, (71, 85, 105), screen_rect.topleft, screen_rect.topright, 1)
            pygame.draw.line(self.screen, (8, 13, 24), screen_rect.bottomleft, screen_rect.bottomright, 2)
            if screen_rect.width > 52 and screen_rect.height > 34:
                pygame.draw.line(self.screen, (45, 57, 76), (screen_rect.left + 10, screen_rect.top + 10), (screen_rect.right - 12, screen_rect.bottom - 12), 1)

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
            pygame.draw.rect(self.screen, (69, 26, 3), screen_rect.move(3, 4), border_radius=4)
            pygame.draw.rect(self.screen, color, screen_rect, border_radius=4)
            pygame.draw.rect(self.screen, self._blend(color, "#020617", 0.42), screen_rect, width=2, border_radius=4)
            pygame.draw.line(self.screen, (254, 215, 170), screen_rect.topleft, screen_rect.bottomright, 1)
            pygame.draw.line(self.screen, self._blend(color, "#FFFFFF", 0.35), (screen_rect.left + 4, screen_rect.top + 4), (screen_rect.right - 5, screen_rect.top + 4), 1)
            if item.kind == "special":
                pygame.draw.circle(self.screen, (224, 242, 254), screen_rect.center, max(4, screen_rect.width // 5), 1)

    def _draw_drops(self, game, camera):
        for drop in game.drops:
            x, y = self.world_to_screen(drop.pos + Vector2(0, math.sin(drop.bob) * 3), camera)
            pulse = 0.5 + 0.5 * math.sin(drop.bob * 1.7)
            if drop.kind == "xp":
                self._draw_soft_circle((x, y), drop.radius + 8 + pulse * 3, COLORS["xp"], alpha=45, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["xp"]), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (187, 247, 208), (x, y), int(drop.radius * 0.45))
            elif drop.kind == "ammo":
                self._draw_soft_circle((x, y), drop.radius + 8, COLORS["projectile"], alpha=38, rings=3)
                pygame.draw.rect(self.screen, (103, 232, 249), (x - 7, y - 4, 14, 8), border_radius=3)
                pygame.draw.rect(self.screen, (8, 47, 73), (x - 7, y - 4, 14, 8), 1, border_radius=3)
                pygame.draw.circle(self.screen, (224, 242, 254), (x + 6, y), 3)
            elif drop.kind == "coin":
                self._draw_soft_circle((x, y), drop.radius + 7 + pulse * 2, COLORS["coin"], alpha=48, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["coin"]), (x, y), int(drop.radius))
                pygame.draw.circle(self.screen, (113, 63, 18), (x, y), int(drop.radius), 2)
                pygame.draw.circle(self.screen, (255, 247, 237), (x - 3, y - 3), 2)
            elif drop.kind == "heal":
                self._draw_soft_circle((x, y), drop.radius + 9, COLORS["health"], alpha=48, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["health"]), (x, y), int(drop.radius))
                pygame.draw.line(self.screen, (255, 255, 255), (x - 5, y), (x + 5, y), 2)
                pygame.draw.line(self.screen, (255, 255, 255), (x, y - 5), (x, y + 5), 2)
            elif drop.kind == "shield":
                self._draw_soft_circle((x, y), drop.radius + 10, COLORS["shield"], alpha=42, rings=3)
                pygame.draw.circle(self.screen, hex_color(COLORS["shield"]), (x, y), int(drop.radius), 3)
                pygame.draw.circle(self.screen, (191, 219, 254), (x, y), int(drop.radius * 0.45))
            elif drop.kind == "item_box":
                self._draw_soft_circle((x, y), drop.radius + 12 + pulse * 3, COLORS["special"], alpha=55, rings=3)
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
            rgb = hex_color(color)
            if projectile.vel.length_squared() > 0:
                tail = Vector2(x, y) - projectile.vel.normalize() * (projectile.radius * 3.2)
                pygame.draw.line(self.screen, self._blend(rgb, "#FFFFFF", 0.25), (int(tail.x), int(tail.y)), (x, y), 2)
            self._draw_soft_circle((x, y), projectile.radius + 6, rgb, alpha=44, rings=2)
            pygame.draw.circle(self.screen, rgb, (x, y), int(projectile.radius + 2))
            pygame.draw.circle(self.screen, (8, 47, 73), (x, y), int(projectile.radius), 1)

    def _draw_item_events(self, game, camera):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for event in game.item_events:
            event_type = event.get("type", "storm")
            if event_type == "arrow_rain":
                alpha = max(0, min(1, event["timer"] * 2))
                pos = event["pos"] - camera
                radius = event["radius"]
                rgba = (56, 189, 248, int(120 * alpha))
                pygame.draw.circle(overlay, (14, 165, 233, int(26 * alpha)), (int(pos.x), int(pos.y)), int(radius))
                pygame.draw.circle(overlay, rgba, (int(pos.x), int(pos.y)), int(radius), 2)
                pygame.draw.circle(overlay, (224, 242, 254, int(120 * alpha)), (int(pos.x), int(pos.y)), int(radius * 0.55), 1)
                for i in range(5):
                    ox = math.sin(game.time_alive * 20 + i) * radius * 0.8
                    oy = math.cos(game.time_alive * 15 + i) * radius * 0.8
                    tip = (pos.x + ox, pos.y + oy)
                    pygame.draw.line(overlay, (224, 242, 254, int(190 * alpha)), (tip[0] - 8, tip[1] - 34), tip, 2)
                    pygame.draw.polygon(overlay, (56, 189, 248, int(170 * alpha)), [tip, (tip[0] - 4, tip[1] - 10), (tip[0] + 5, tip[1] - 8)])
            elif event_type == "danger_circle":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                pos = event["pos"] - camera
                radius = event["radius"]
                pulse_radius = radius * (0.86 + 0.14 * math.sin(game.time_alive * 18))
                warn = hex_color(event.get("color", COLORS["danger"]))
                pygame.draw.circle(overlay, (*warn, int(44 + 60 * alpha)), (int(pos.x), int(pos.y)), int(pulse_radius))
                pygame.draw.circle(overlay, (254, 226, 226, int(210 * alpha)), (int(pos.x), int(pos.y)), int(radius), 4)
            elif event_type == "danger_line":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 1))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                width = int(event.get("width", 42))
                warn = hex_color(event.get("color", COLORS["danger"]))
                pygame.draw.line(overlay, (*warn, int(72 + 75 * alpha)), (start.x, start.y), (end.x, end.y), width)
                pygame.draw.line(overlay, (254, 226, 226, int(220 * alpha)), (start.x, start.y), (end.x, end.y), 3)
            elif event_type == "laser":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 0.2))
                alpha = max(0, 1 - age / duration)
                start = event["start"] - camera
                end = event["end"] - camera
                width = int(event.get("width", 44))
                beam = hex_color(event.get("color", "#FB923C"))
                pygame.draw.line(overlay, (*beam, int(210 * alpha)), (start.x, start.y), (end.x, end.y), width)
                pygame.draw.line(overlay, (255, 247, 237, int(245 * alpha)), (start.x, start.y), (end.x, end.y), max(3, width // 5))
            elif event_type == "explosion":
                age = event.get("age", 0)
                duration = max(0.01, event.get("duration", 0.2))
                alpha = max(0, 1 - age / duration)
                pos = event["pos"] - camera
                progress = min(1.0, age / duration)
                current_radius = event["radius"] * (1 - alpha**2)
                core_r = max(4, int(event["radius"] * 0.18 * alpha))
                pygame.draw.circle(overlay, (251, 146, 60, int(80 * alpha)), (int(pos.x), int(pos.y)), int(current_radius))
                pygame.draw.circle(overlay, (254, 240, 138, int(230 * alpha)), (int(pos.x), int(pos.y)), int(current_radius), max(2, int(5 * alpha)))
                pygame.draw.circle(overlay, (255, 247, 237, int(190 * alpha)), (int(pos.x), int(pos.y)), core_r)
                for i in range(6):
                    ang = game.time_alive * 2.0 + i * math.tau / 6
                    inner = Vector2(pos.x, pos.y) + Vector2(math.cos(ang), math.sin(ang)) * current_radius * 0.35
                    outer = Vector2(pos.x, pos.y) + Vector2(math.cos(ang), math.sin(ang)) * current_radius * (0.72 + 0.12 * progress)
                    pygame.draw.line(overlay, (253, 186, 116, int(135 * alpha)), inner, outer, 2)
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
            self._draw_shadow((x, y), enemy.radius, alpha=86)
            if enemy.kind in ("chromatic", "miniboss", "sapper") or enemy.action:
                self._draw_soft_circle((x, y), enemy.radius + 18, color, alpha=44, rings=3)
            pygame.draw.circle(self.screen, color, (x, y), int(enemy.radius))
            pygame.draw.circle(self.screen, self._blend(color, "#FFFFFF", 0.22), (x - int(enemy.radius * 0.25), y - int(enemy.radius * 0.28)), max(2, int(enemy.radius * 0.18)))
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
                pygame.draw.line(self.screen, (49, 46, 129), (x - 18, y + 12), (x + 18, y + 12), 3)
                if enemy.action:
                    pygame.draw.circle(self.screen, hex_color(COLORS["danger"]), (x, y), int(enemy.radius + 12), 2)
            elif enemy.kind == "chromatic":
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), int(enemy.radius + 6), 2)
                self._draw_star((x, y), max(7, int(enemy.radius * 0.55)), max(3, int(enemy.radius * 0.25)), (255, 255, 255), points=4, angle_offset=enemy.phase)
                if enemy.lifetime > 0:
                    arc_rect = pygame.Rect(x - enemy.radius - 8, y - enemy.radius - 8, int((enemy.radius + 8) * 2), int((enemy.radius + 8) * 2))
                    pygame.draw.arc(self.screen, (226, 232, 240), arc_rect, -math.pi / 2, -math.pi / 2 + math.tau * (enemy.lifetime / CHROMATIC_LIFETIME), 3)
            elif enemy.kind == "brute":
                pygame.draw.circle(self.screen, (254, 226, 226), (x - 7, y - 5), 3)
                pygame.draw.circle(self.screen, (254, 226, 226), (x + 7, y - 5), 3)
                pygame.draw.line(self.screen, (127, 29, 29), (x - 13, y + 8), (x + 13, y + 8), 2)
            elif enemy.kind == "runner":
                pygame.draw.polygon(self.screen, (255, 228, 230), [(x, y - 7), (x + 8, y + 7), (x - 8, y + 7)])
                pygame.draw.line(self.screen, (15, 23, 42), (x, y - 12), (x, y + 10), 1)
            elif enemy.kind == "spitter":
                pygame.draw.circle(self.screen, (236, 252, 203), (x + 5, y - 4), 4)
                if enemy.action:
                    pygame.draw.circle(self.screen, (190, 242, 100), (x, y), int(enemy.radius + 8), 2)
                    pygame.draw.circle(self.screen, (236, 252, 203), (x, y), int(enemy.radius * 0.45), 1)
            elif enemy.kind == "bulwark":
                pygame.draw.circle(self.screen, (203, 213, 225), (x, y), int(enemy.radius + 8), 2)
                pygame.draw.rect(self.screen, (15, 23, 42), (x - 11, y - 7, 22, 14), 2, border_radius=3)
                pygame.draw.line(self.screen, (226, 232, 240), (x - 16, y - 13), (x + 16, y - 13), 2)
            elif enemy.kind == "sapper":
                pulse = 0.5 + 0.5 * math.sin(game.time_alive * 12 + enemy.id)
                pygame.draw.circle(self.screen, (254, 240, 138), (x, y), int(enemy.radius + 5 + pulse * 3), 2)
                pygame.draw.line(self.screen, (113, 63, 18), (x - 6, y), (x + 6, y), 2)
                pygame.draw.line(self.screen, (113, 63, 18), (x, y - 6), (x, y + 6), 2)
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
            alpha = int(135 * (1 - progress * 0.55))
            pygame.draw.polygon(overlay, (253, 224, 71, alpha), points)
            pygame.draw.lines(overlay, (254, 243, 199, 225), False, points[1:], 4)
            inner = [(origin.x, origin.y)]
            inner_radius = radius * 0.72
            for i in range(steps + 1):
                angle = start + (end - start) * (i / steps)
                inner.append((origin.x + math.cos(angle) * inner_radius, origin.y + math.sin(angle) * inner_radius))
            pygame.draw.lines(overlay, (251, 146, 60, int(120 * (1 - progress))), False, inner[1:], 2)
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
        self._draw_shadow((x, y), player.radius, alpha=105)
        if player.dash_timer > 0:
            dash_alpha = int(55 + 85 * min(1.0, player.dash_timer / max(0.01, DASH_DURATION)))
            for step in range(1, 4):
                trail = Vector2(x, y) - player.dash_dir * step * player.radius * 0.9
                self._draw_soft_circle((trail.x, trail.y), player.radius * (1.0 - step * 0.12), aim_color, alpha=max(18, dash_alpha // (step + 1)), rings=2)
        if player.shield_timer > 0:
            pulse = 5 + int(math.sin(game.time_alive * 12) * 2)
            self._draw_soft_circle((x, y), player.radius + 24 + pulse, COLORS["shield"], alpha=55, rings=3)
            pygame.draw.circle(self.screen, hex_color(COLORS["shield"]), (x, y), int(player.radius + 12 + pulse), 3)
        elif player.invulnerable_timer > 0:
            self._draw_soft_circle((x, y), player.radius + 14, "#CBD5E1", alpha=38, rings=2)
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
            self._draw_soft_circle((x, y), player.radius + 11, aim_color, alpha=34, rings=2)
            pygame.draw.circle(self.screen, color, (x, y), int(player.radius))
            if char_data["shape"] == "circle_triangle":
                pygame.draw.polygon(self.screen, core, [nose, left, right])
                pygame.draw.line(self.screen, (224, 242, 254), nose, Vector2(x, y) - aim * player.radius * 0.35, 2)
            else:
                self._draw_star((x, y), int(player.radius * 0.62), int(player.radius * 0.28), core, points=5)

        pygame.draw.circle(self.screen, (15, 23, 42), (x, y), int(player.radius), 2)
        pygame.draw.circle(self.screen, self._blend(color, "#FFFFFF", 0.32), (x - int(player.radius * 0.28), y - int(player.radius * 0.32)), max(2, int(player.radius * 0.18)))

        if not player.is_down and player.ammo_magazine <= 0:
            pulse = (pygame.time.get_ticks() // 250) % 2 == 0
            if pulse:
                msg = "SEM MUNICAO!" if player.ammo_reserve <= 0 else "RECARREGANDO"
                color = hex_color(COLORS["health"]) if player.ammo_reserve <= 0 else hex_color(COLORS["coin"])
                ammo_text, text_rect = self.font_small.render(msg, color)
                text_rect.center = (x, y - int(player.radius) - 20)
                
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
        alpha = 1 - progress
        pygame.draw.circle(overlay, (56, 189, 248, int(72 * alpha)), (x, y), radius)
        pygame.draw.circle(overlay, (165, 243, 252, int(135 * alpha)), (x, y), radius, 8)
        pygame.draw.circle(overlay, (255, 255, 255, int(90 * alpha)), (x, y), max(1, radius // 2), 2)
        for i in range(10):
            ang = game.time_alive * 3 + i * math.tau / 10
            p1 = Vector2(x, y) + Vector2(math.cos(ang), math.sin(ang)) * radius * 0.32
            p2 = Vector2(x, y) + Vector2(math.cos(ang), math.sin(ang)) * radius * 0.92
            pygame.draw.line(overlay, (224, 242, 254, int(80 * alpha)), p1, p2, 2)
        self.screen.blit(overlay, (0, 0))

    def _draw_floaters(self, game, camera):
        for floater in game.floaters:
            duration = floater["duration"]
            age = floater["age"]
            progress = min(1.0, age / duration)
            ftype = floater.get("type", "damage")

            if ftype == "alert":
                # Alertas de acao: fonte maior, fundo, borda, sobem mais rapido
                eased_offset = pytweening.easeOutCubic(progress) * 60
                fade_start = 0.4
                fade_progress = max(0.0, (progress - fade_start) / (1.0 - fade_start))
                alpha = int(255 * (1.0 - pytweening.easeInQuad(fade_progress)))
                x, y = self.world_to_screen(floater["pos"], camera)
                color = hex_color(floater["color"])
                surf, rect = self.font_small.render(floater["text"], color)
                pad_x, pad_y = 10, 5
                bg = pygame.Surface((rect.width + pad_x * 2, rect.height + pad_y * 2), pygame.SRCALPHA)
                bg_alpha = min(180, alpha)
                pygame.draw.rect(bg, (10, 5, 5, bg_alpha), bg.get_rect(), border_radius=6)
                pygame.draw.rect(bg, (*color, bg_alpha), bg.get_rect(), width=1, border_radius=6)
                bx = x - rect.width // 2 - pad_x
                by = int(y - 28 - eased_offset) - pad_y
                self.screen.blit(bg, (bx, by))
                surf.set_alpha(alpha)
                self.screen.blit(surf, (bx + pad_x, by + pad_y))
            else:
                # Floaters de dano: comportamento original leve e rapido
                eased_offset = pytweening.easeOutQuad(progress) * 40
                alpha = int(255 * (1.0 - pytweening.easeInQuad(progress)))
                x, y = self.world_to_screen(floater["pos"], camera)
                surf, rect = self.font_tiny.render(floater["text"], hex_color(floater["color"]))
                surf.set_alpha(alpha)
                self.screen.blit(surf, (x - rect.width // 2, y - 14 - eased_offset))












































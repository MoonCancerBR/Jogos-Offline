import math
import random

from pygame.math import Vector2

if __package__:
    from ..data.constants import *
    from .entities import Drop, Enemy, Player, Projectile, Slash
    from ..data.items import Inventory, item_display_name, RELIC_DEFINITIONS
    from .world import World, circle_rect_overlap
else:
    from Sobrevivencia.data.constants import *
    from Sobrevivencia.core.entities import Drop, Enemy, Player, Projectile, Slash
    from Sobrevivencia.data.items import Inventory, item_display_name, RELIC_DEFINITIONS
    from Sobrevivencia.core.world import World, circle_rect_overlap


STAT_SHOP_STATS = [
    {
        "key": "max_health",
        "label": "Vida maxima",
        "base": 10.0,
        "cost": 0.22,
        "kind": "flat",
        "unit": "vida",
    },
    {
        "key": "damage",
        "label": "Dano",
        "base": 0.035,
        "cost": 75.0,
        "kind": "percent",
        "unit": "dano",
    },
    {
        "key": "speed",
        "label": "Velocidade",
        "base": 0.030,
        "cost": 68.0,
        "kind": "percent",
        "unit": "velocidade",
    },
    {
        "key": "attack_rate",
        "label": "Cadencia",
        "base": 0.032,
        "cost": 70.0,
        "kind": "percent",
        "unit": "cadencia",
    },
    {
        "key": "sword_range",
        "label": "Alcance corpo a corpo",
        "base": 0.045,
        "cost": 52.0,
        "kind": "percent",
        "unit": "alcance",
    },
    {
        "key": "special_gain",
        "label": "Carga de especial",
        "base": 0.050,
        "cost": 46.0,
        "kind": "percent",
        "unit": "carga",
    },
    {
        "key": "vampirism",
        "label": "Vampirismo",
        "base": 0.8,
        "cost": 1.35,
        "kind": "decimal",
        "unit": "cura/abate",
    },
    {
        "key": "magazine",
        "label": "Pente",
        "base": 3.0,
        "cost": 0.82,
        "kind": "integer",
        "unit": "municoes",
    },
    {
        "key": "reload_speed",
        "label": "Recarga",
        "base": 0.030,
        "cost": 74.0,
        "kind": "percent",
        "unit": "recarga",
    },
]


class GameLogic:
    def __init__(self, char_class="vanguard", char_class_2="vanguard", multiplayer=False):
        self.char_class = char_class
        self.char_class_2 = char_class_2
        self.multiplayer = multiplayer
        self.world = World()
        self.player = Player(char_class=char_class, player_index=0)
        self.inventory = Inventory()
        if multiplayer:
            self.player2 = Player(char_class=char_class_2, player_index=1)
            self.player2.pos = self.player.pos + Vector2(72, 0)
            self.inventory2 = Inventory()
            self.players = [self.player, self.player2]
            self.inventories = [self.inventory, self.inventory2]
            self.shared_coins = 0
            # XP Compartilhado
            self.shared_level = 1
            self.shared_xp = 0
            self.shared_xp_to_next = int(40 + 25 * 1)
            self.draft_active = False
            self.draft_turn_player = 0  # 0 ou 1
            self.draft_first_picker = 0 # Alterna a cada nível
        else:
            self.player2 = None
            self.inventory2 = None
            self.players = [self.player]
            self.inventories = [self.inventory]
            self.shared_coins = 0
            self.shared_level = 1 # Para compatibilidade
        self.camera = Vector2(
            self.player.pos.x - SCREEN_WIDTH * 0.5,
            self.player.pos.y - SCREEN_HEIGHT * 0.5,
        )
        self.camera_focus_index = 0
        self.enemies = []
        self.projectiles = []
        self.slashes = []
        self.drops = []
        self.floaters = []
        self.stat_shop_offers = []
        self.upgrade_choices = []
        self.upgrade_is_major = False
        self.level_up_pending = False
        self.level_up_player_index = 0
        self.menu_player_index = 0
        self.game_over = False
        self.time_alive = 0.0
        self.spawn_timer = 0.2
        self.enemy_id = 1
        self.screen_shake = 0.0
        self.special_blast_timer = 0.0
        self.special_box_timer = 12.0
        self.item_events = []
        self.message = "Sobreviva o maximo que puder."
        self.random = random.Random()
        self.chromatic_spawn_timer = self.random.uniform(CHROMATIC_SPAWN_MIN, CHROMATIC_SPAWN_MAX)
        self.miniboss_spawn_timer = self.random.uniform(MINIBOSS_SPAWN_MIN, MINIBOSS_SPAWN_MAX)
        self.world.ensure_area(self.player.pos, 2)
        # Quest system
        self.quest = None
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(60.0, 90.0)
        self._player_in_fire = False
        # Game Director
        self.director_minute = 0
        self.director_tick = 0.0
        self.director_health = 1.0
        self.director_damage = 1.0
        self.director_speed = 1.0
        # Relic aura
        self.relic_aura_angle = 0.0
        self.camera_zoom = 1.0

    def restart(self):
        self.__init__(self.char_class, self.char_class_2, self.multiplayer)

    def get_player(self, index=0):
        if index == 1 and self.player2 is not None:
            return self.player2
        return self.player

    def get_inventory(self, index=0):
        if index == 1 and self.inventory2 is not None:
            return self.inventory2
        return self.inventory

    @property
    def camera_focus(self):
        if self.multiplayer and self.player2:
            alive = self.alive_players()
            if len(alive) == 2:
                # Ponto médio
                return (alive[0].pos + alive[1].pos) * 0.5
            elif len(alive) == 1:
                return alive[0].pos
            return self.players[0].pos
        
        p = self.get_player(self.camera_focus_index)
        if p.is_down and self.multiplayer:
            other = self.get_player(1 - self.camera_focus_index)
            if not other.is_down:
                return other.pos
        return p.pos

    def alive_players(self):
        return [p for p in self.players if not p.is_down]

    def toggle_mode(self, player_index=0):
        player = self.get_player(player_index)
        if player.is_down:
            return
        
        if player.mode == "weapon_1": # Mudando para weapon_2 (espada)
            player.mode = "weapon_2"
            player.forced_reload = False
            if player.ammo_magazine < self.magazine_capacity_for(player) and player.reload_timer <= 0:
                self._start_reload_for(player, forced=False, show_message=False)
        else:
            if not self._ranged_weapon_ready_for(player, show_message=True):
                return
            player.mode = "weapon_1"
            player.forced_reload = False
        
        w_name = CHARACTERS[player.char_class][player.mode]
        self.message = f"J{player_index + 1}: modo {w_name}"

    def try_dash(self, aim_world, player_index=0):
        player = self.get_player(player_index)
        if player.dash_cooldown > 0 or player.dash_timer > 0 or self.game_over:
            return
        if player.is_down:
            return
        # Quest hook: fail survive_no_dash
        if self.quest and self.quest["goal_type"] == "survive_no_dash":
            self._fail_quest()
        direction = Vector2(player.last_move_dir)
        if direction.length_squared() < 0.01:
            direction = Vector2(aim_world) - player.pos
        if direction.length_squared() < 0.01:
            direction = Vector2(1, 0)
        player.dash_dir = direction.normalize()
        player.dash_timer = DASH_DURATION
        player.dash_cooldown = self.current_dash_cooldown_for(player)
        player.invulnerable_timer = max(player.invulnerable_timer, DASH_DURATION + 0.08)

    def try_special(self, aim_world, player_index=0):
        if self.game_over:
            return False
        player = self.get_player(player_index)
        if player.is_down:
            return False
        channel = "ranged" if player.mode == "weapon_1" else "melee"
        if self.special_charge(channel, player_index) < SPECIAL_MAX:
            self.message = f"J{player_index + 1}: especial da arma atual ainda nao carregou."
            return False
        self._consume_special(channel, player)
        self._cast_weapon_special(channel, aim_world, player)
        return True

    def try_combo_special(self, aim_world, player_index=0):
        if self.game_over:
            return False
        player = self.get_player(player_index)
        if player.is_down:
            return False
        if player.special_ranged < SPECIAL_MAX or player.special_melee < SPECIAL_MAX:
            self.message = f"J{player_index + 1}: combo exige os dois especiais carregados."
            return False
        player.special_ranged = 0
        player.special_melee = 0
        player.special = 0
        self._cast_combo_special(aim_world, player)
        return True

    def special_charge(self, channel, player_index=0):
        player = self.get_player(player_index)
        return player.special_melee if channel == "melee" else player.special_ranged

    def _consume_special(self, channel, player=None):
        if player is None:
            player = self.player
        if channel == "melee":
            player.special_melee = 0
        else:
            player.special_ranged = 0
        player.special = max(player.special_ranged, player.special_melee)

    def _cast_weapon_special(self, channel, aim_world, player=None):
        if player is None:
            player = self.player
        if player.char_class == "vanguard":
            if channel == "ranged":
                self._cast_vanguard_radial(player=player)
            else:
                self._cast_vanguard_charge(aim_world, player=player)
        else:
            if channel == "ranged":
                self._cast_huntress_arrow_rain(aim_world, player=player)
            else:
                self._cast_huntress_dagger_dance(player=player)

    def _cast_combo_special(self, aim_world, player=None):
        if player is None:
            player = self.player
        if player.char_class == "vanguard":
            self._cast_vanguard_radial(multiplier=1.35, radius_multiplier=1.18, silent=True, player=player)
            self._cast_vanguard_charge(aim_world, multiplier=1.35, silent=True, player=player)
            self.message = "Combo: Protocolo Cerco!"
        else:
            self._cast_huntress_arrow_rain(aim_world, multiplier=1.25, radius_multiplier=1.18, silent=True, player=player)
            self._cast_huntress_dagger_dance(multiplier=1.30, radius_multiplier=1.18, silent=True, player=player)
            self.message = "Combo: Tempestade Predatoria!"
        self.screen_shake = max(self.screen_shake, 18.0)

    def _cast_vanguard_radial(self, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        inv = self.get_inventory(player.player_index)
        special_damage = self.special_damage_for(player) * multiplier
        special_radius = self.special_radius_for(player) * radius_multiplier
        self.special_blast_timer = 0.35
        self.screen_shake = max(self.screen_shake, 16.0)
        if not silent:
            self.message = "Explosao radial liberada!"

        for enemy in list(self.enemies):
            distance = enemy.pos.distance_to(player.pos)
            if distance <= special_radius:
                direction = enemy.pos - player.pos
                if direction.length_squared() > 0:
                    enemy.knockback += direction.normalize() * 520
                self.damage_enemy(enemy, special_damage, source="special", killer_index=player.player_index)

        for item in list(self.world.nearby_destructibles(player.pos.x, player.pos.y, special_radius * 0.75)):
            if item.rect.center.distance_to(player.pos) <= special_radius * 0.75:
                self.destroy_destructible(item)

        reactor = player.passives.get("reactor_blast", 0)
        if reactor > 0:
            restored = min(self.magazine_capacity_for(player) - player.ammo_magazine, 2 + reactor * 2)
            if restored > 0:
                player.ammo_magazine += restored
                player.forced_reload = False
                player.reload_timer = 0
                player.mode = "weapon_1"
                if not silent:
                    self.message = "Explosao radial liberada! Pente reenergizado."

    def _cast_vanguard_charge(self, aim_world, multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        direction = Vector2(aim_world) - player.pos
        if direction.length_squared() <= 0.01:
            direction = player.last_move_dir
        if direction.length_squared() <= 0.01:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        start = Vector2(player.pos)
        end = start + direction * 420
        width = 78
        damage = self.special_damage_for(player) * 0.88 * multiplier
        self._apply_laser_damage(start, end, width, damage, damage_player=False, killer_index=player.player_index)
        player.pos = self.world.move_circle(player.pos, player.radius, direction * 240, include_destructibles=False)
        self.item_events.append({
            "type": "laser",
            "start": start,
            "end": end,
            "width": width,
            "age": 0.0,
            "duration": 0.26,
            "color": COLORS["sword"],
        })
        self.screen_shake = max(self.screen_shake, 12.0)
        if not silent:
            self.message = "Carga Titanica!"

    def _cast_huntress_arrow_rain(self, aim_world, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        storm_eye = player.passives.get("storm_eye", 0)
        duration = (2.0 + storm_eye * 0.12) * (1.0 + (multiplier - 1.0) * 0.5)
        self.item_events.append({
            "type": "arrow_rain",
            "pos": Vector2(aim_world),
            "timer": duration,
            "age": 0.0,
            "duration": duration,
            "damage": self.special_damage_for(player) * (0.18 + storm_eye * 0.006) * multiplier,
            "radius": self.special_radius_for(player) * 0.8 * radius_multiplier,
            "owner": player.player_index,
        })
        if not silent:
            self.message = "Chuva de Flechas!"

    def _cast_huntress_dagger_dance(self, multiplier=1.0, radius_multiplier=1.0, silent=False, player=None):
        if player is None:
            player = self.player
        radius = 260 * radius_multiplier
        damage = self.special_damage_for(player) * 0.72 * multiplier
        for enemy in list(self.enemies):
            if enemy.pos.distance_squared_to(player.pos) <= (radius + enemy.radius) ** 2:
                enemy.bleed_timer = max(enemy.bleed_timer, 4.0)
                enemy.bleed_dps = max(enemy.bleed_dps, 18.0 * multiplier)
                push = enemy.pos - player.pos
                if push.length_squared() > 0:
                    enemy.knockback += push.normalize() * 260
                self.damage_enemy(enemy, damage, source="special", killer_index=player.player_index)
        self.item_events.append({
            "type": "explosion",
            "pos": Vector2(player.pos),
            "radius": radius,
            "damage": 0,
            "age": 0.0,
            "duration": 0.32,
            "owner": player.player_index,
        })
        player.invulnerable_timer = max(player.invulnerable_timer, 0.65)
        self.screen_shake = max(self.screen_shake, 10.0)
        if not silent:
            self.message = "Danca das Adagas!"

    def item_level(self, key):
        return self.inventory.active_effect_level(key)

    def hybrid_level(self):
        return self.inventory.active_hybrid_level()

    def passive_level(self, key):
        return self.player.passives.get(key, 0)

    def magazine_capacity(self):
        level_capacity = BASE_MAGAZINE_CAPACITY + max(0, self.player.level - 1) * MAGAZINE_CAPACITY_PER_LEVEL
        return level_capacity + self.player.magazine_bonus

    def current_reload_duration(self):
        reload_bonus = (
            self.passive_level("combat_drill") * 0.015
            + self.passive_level("predator_focus") * 0.015
            + self.player.reload_speed_bonus
        )
        return max(0.75, RELOAD_DURATION * (1.0 - min(0.35, reload_bonus)))

    def _ranged_weapon_ready(self, show_message=False):
        return self._ranged_weapon_ready_for(self.player, show_message=show_message)

    def _ranged_weapon_ready_for(self, player, show_message=False):
        if player.reload_timer > 0:
            if show_message:
                self.message = f"J{player.player_index + 1} recarregando: {player.reload_timer:.1f}s."
            return False
        if player.ammo_magazine > 0:
            return True
        started = self._start_reload_for(player)
        if show_message and not started:
            self.message = f"J{player.player_index + 1} sem municao: lute corpo a corpo e colete cartuchos."
        elif show_message:
            self.message = f"J{player.player_index + 1}: pente vazio, recarregando."
        return False

    def _start_forced_reload(self, show_message=True):
        player = self.player
        player.mode = "weapon_2"
        player.forced_reload = True
        if player.ammo_reserve <= 0:
            if show_message:
                self.message = "Sem municao: lute corpo a corpo e colete cartuchos."
            return False
        player.reload_duration = self.current_reload_duration()
        player.reload_timer = player.reload_duration
        if show_message:
            self.message = "Pente vazio: arma corpo a corpo ativa enquanto recarrega."
        return True

    def _finish_reload(self):
        player = self.player
        capacity = self.magazine_capacity()
        needed = max(0, capacity - player.ammo_magazine)
        loaded = min(needed, player.ammo_reserve)
        if loaded <= 0:
            player.reload_timer = 0
            player.reload_duration = 0
            player.forced_reload = True
            self.message = "Sem municao na reserva."
            return

        player.ammo_magazine += loaded
        player.ammo_reserve -= loaded
        player.reload_timer = 0
        player.reload_duration = 0
        was_forced = player.forced_reload
        player.forced_reload = False
        if was_forced:
            player.mode = "weapon_1"
            self.message = "Recarga completa: arma de distancia pronta."

    def _consume_ranged_ammo(self):
        player = self.player
        if not self._ranged_weapon_ready(show_message=True):
            return False
        player.ammo_magazine = max(0, player.ammo_magazine - 1)
        if player.ammo_magazine <= 0:
            self._start_forced_reload(show_message=True)
        return True

    def effective_speed_multiplier(self):
        chrono = self.item_level("chrono_boots")
        return self.player.speed_multiplier() * (1.0 + chrono * 0.015)

    def current_dash_cooldown(self):
        chrono = self.item_level("chrono_boots")
        hybrid = self.hybrid_level()
        reduction = min(0.45, chrono * 0.025 + hybrid * 0.015)
        return max(0.55, DASH_COOLDOWN * (1.0 - reduction))

    def current_dash_cooldown_for(self, player):
        inv = self.get_inventory(player.player_index)
        chrono = inv.active_effect_level("chrono_boots")
        hybrid = inv.active_hybrid_level()
        reduction = min(0.45, chrono * 0.025 + hybrid * 0.015)
        return max(0.55, DASH_COOLDOWN * (1.0 - reduction))

    def effective_attack_rate_multiplier(self):
        blade = self.item_level("blade_relay")
        hybrid = self.hybrid_level()
        both_bonus = self.passive_level("combat_drill") * 0.01 + self.passive_level("predator_focus") * 0.012
        return self.player.attack_rate_multiplier() * (1.0 + blade * 0.012 + hybrid * 0.01 + both_bonus)

    def ranged_damage_multiplier(self):
        return (
            1.0
            + self.passive_level("combat_drill") * 0.025
            + self.passive_level("predator_focus") * 0.020
            + self.passive_level("piercing_rounds") * 0.015
        )

    def melee_damage_multiplier(self):
        return (
            1.0
            + self.passive_level("combat_drill") * 0.025
            + self.passive_level("predator_focus") * 0.020
            + self.passive_level("fan_blades") * 0.018
        )

    def projectile_damage(self):
        storm = self.item_level("storm_core")
        return self.player.projectile_damage() * (1.0 + storm * 0.01) * self.ranged_damage_multiplier()

    def sword_damage(self):
        blade = self.item_level("blade_relay")
        return self.player.sword_damage() * (1.0 + blade * 0.012) * self.melee_damage_multiplier()

    def sword_radius(self):
        blade = self.item_level("blade_relay")
        hybrid = self.hybrid_level()
        melee_bonus = self.passive_level("wide_cleave") * 0.030 + self.passive_level("fan_blades") * 0.028
        return self.player.sword_radius() * (1.0 + blade * 0.018 + hybrid * 0.018 + melee_bonus)

    def sword_arc(self):
        return SWORD_ARC + math.radians(self.passive_level("wide_cleave") * 2.4)

    def dagger_arc(self):
        return SWORD_ARC * 0.6 + math.radians(self.passive_level("fan_blades") * 2.8)

    def special_damage(self):
        return SPECIAL_DAMAGE * (
            1.0
            + self.passive_level("reactor_blast") * 0.055
            + self.passive_level("storm_eye") * 0.040
        )

    def special_radius(self):
        return SPECIAL_RADIUS * (
            1.0
            + self.passive_level("reactor_blast") * 0.030
            + self.passive_level("storm_eye") * 0.025
        )

    def special_damage_for(self, player):
        return SPECIAL_DAMAGE * (
            1.0
            + player.passives.get("reactor_blast", 0) * 0.055
            + player.passives.get("storm_eye", 0) * 0.040
        )

    def special_radius_for(self, player):
        return SPECIAL_RADIUS * (
            1.0
            + player.passives.get("reactor_blast", 0) * 0.030
            + player.passives.get("storm_eye", 0) * 0.025
        )

    def incoming_damage_multiplier(self):
        guardian = self.item_level("guardian_plate")
        if guardian <= 0:
            return 1.0
        if self.player.health / self.player.max_health > 0.42:
            return 1.0
        return max(0.52, 1.0 - (0.10 + guardian * 0.022))

    def drop_magnet_radius(self, kind):
        magnet = self.item_level("magnet_orb")
        base = XP_MAGNET_RADIUS if kind == "xp" else XP_MAGNET_RADIUS * 0.72
        if kind == "item_box":
            base = XP_MAGNET_RADIUS * 0.9
        return base + magnet * 9

    def update(self, dt, move_vector, aim_world, move_vector_2=None, aim_world_2=None):
        if self.game_over:
            return

        dt = min(dt, 0.05)
        self.time_alive += dt
        self._player_in_fire = False
        self.world.ensure_area(self.player.pos, 2)
        self._update_director(dt)

        # --- Per-player updates ---
        inputs = [(self.player, move_vector, aim_world)]
        if self.multiplayer and self.player2 is not None:
            mv2 = move_vector_2 if move_vector_2 is not None else Vector2(0, 0)
            aw2 = aim_world_2 if aim_world_2 is not None else self.player2.pos + Vector2(1, 0)
            inputs.append((self.player2, mv2, aw2))

        for player, mv, aw in inputs:
            if player.is_down:
                continue
            self._update_player_timers_for(dt, player)
            self._move_player_for(dt, mv, aw, player)
            self._auto_attack_for(dt, aw, player)

        self._spawn_enemies(dt)
        self._update_world_timers(dt)
        self._update_projectiles(dt)
        self._update_slashes(dt)
        self._update_enemies(dt)
        self._update_hazards(dt)
        self._update_item_system(dt)
        self._update_relic_aura(dt)
        self._update_drops(dt)
        self._update_floaters(dt)
        self._update_quests(dt)
        self._update_camera(dt)
        self.screen_shake = max(0, self.screen_shake - SCREEN_SHAKE_DECAY * 20 * dt)
        self.special_blast_timer = max(0, self.special_blast_timer - dt)

        # --- Multiplayer: tethering and revive ---
        if self.multiplayer and self.player2 is not None:
            self._update_tethering()
            self._update_revive(dt)

        # --- Game over check ---
        for player in self.players:
            if player.health <= 0 and not player.is_down:
                if self.multiplayer:
                    player.is_down = True
                    player.health = 0
                    self.message = f"Jogador {player.player_index + 1} caiu!"
                else:
                    player.health = 0
                    self.game_over = True
        if self.multiplayer and all(p.is_down for p in self.players):
            self.game_over = True

    def _update_player_timers(self, dt):
        self._update_player_timers_for(dt, self.player)

    def _update_player_timers_for(self, dt, player):
        player.shoot_timer = max(0, player.shoot_timer - dt)
        player.sword_timer = max(0, player.sword_timer - dt)
        player.dash_cooldown = max(0, player.dash_cooldown - dt)
        player.dash_timer = max(0, player.dash_timer - dt)
        player.invulnerable_timer = max(0, player.invulnerable_timer - dt)
        player.shield_timer = max(0, player.shield_timer - dt)
        player.full_ammo_msg_timer = max(0, player.full_ammo_msg_timer - dt)
        if player.mode == "weapon_2" and player.ammo_magazine < self.magazine_capacity_for(player) and player.ammo_reserve > 0:
            player.reload_timer = max(0, player.reload_timer - dt)
            player.reload_step_timer -= dt
            
            if player.reload_step_timer <= 0:
                player.ammo_reserve -= 1
                player.ammo_magazine += 1
                
                capacity = self.magazine_capacity_for(player)
                if player.ammo_magazine < capacity and player.ammo_reserve > 0:
                    time_per_bullet = player.reload_duration / capacity
                    player.reload_step_timer += time_per_bullet
                else:
                    player.reload_timer = 0
                    player.reload_step_timer = 0
                    if player.forced_reload:
                        player.mode = "weapon_1"
                        player.forced_reload = False
                        
                        w_name = CHARACTERS[player.char_class][player.mode]
                        self.message = f"J{player.player_index + 1}: modo {w_name}"
        else:
            if player.reload_timer > 0:
                player.reload_timer = 0
                player.reload_step_timer = 0

        expired = []
        for name in player.buffs:
            player.buffs[name] = max(0, player.buffs[name] - dt)
            if player.buffs[name] <= 0:
                expired.append(name)
        for name in expired:
            del player.buffs[name]

    def _move_player(self, dt, move_vector, aim_world):
        self._move_player_for(dt, move_vector, aim_world, self.player)

    def _move_player_for(self, dt, move_vector, aim_world, player):
        if move_vector.length_squared() > 0:
            move_vector = move_vector.normalize()
            player.last_move_dir = Vector2(move_vector)

        if player.dash_timer > 0:
            delta = player.dash_dir * DASH_SPEED * dt
        else:
            terrain_speed = self.world.speed_multiplier_at(player.pos.x, player.pos.y)
            speed = player.base_speed * self.effective_speed_multiplier_for(player) * terrain_speed
            delta = move_vector * speed * dt

        player.pos = self.world.move_circle(player.pos, player.radius, delta)
        if player.shield_timer > 0:
            self._repel_enemies(dt, player)

    def _auto_attack(self, dt, aim_world):
        self._auto_attack_for(dt, aim_world, self.player)

    def _auto_attack_for(self, dt, aim_world, player):
        direction = Vector2(aim_world) - player.pos
        if direction.length_squared() < 0.01:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        pi = player.player_index
        inv = self.get_inventory(pi)

        if player.char_class == "vanguard":
            if player.mode == "weapon_1":
                cooldown = PROJECTILE_COOLDOWN / self.effective_attack_rate_multiplier_for(player, inv)
                if player.shoot_timer <= 0 and len(self.projectiles) < MAX_PROJECTILES:
                    if not self._consume_ranged_ammo_for(player):
                        return
                    # Quest hook: fail melee_only
                    if self.quest and self.quest["goal_type"] == "survive_melee":
                        self._fail_quest()
                    count = 1 + player.passives.get("multishot", 0)
                    side = direction.rotate(90)
                    start_offset = -(count - 1) * 0.5
                    pierce = player.passives.get("piercing_rounds", 0) // 3
                    for index in range(count):
                        if len(self.projectiles) >= MAX_PROJECTILES:
                            break
                        offset = side * ((start_offset + index) * PROJECTILE_PARALLEL_SPACING)
                        self.projectiles.append(
                            Projectile(
                                pos=Vector2(player.pos) + direction * (player.radius + 8) + offset,
                                vel=direction * PROJECTILE_SPEED,
                                damage=self.projectile_damage_for(player, inv),
                                freeze=player.buffs.get("freeze", 0) > 0,
                                poison=player.passives.get("poison", 0) > 0,
                                poison_dps=POISON_BASE_DPS * player.passives.get("poison", 0) * player.damage_multiplier(),
                                bounces_left=player.passives.get("ricochet", 0),
                                pierce=pierce,
                                owner=pi,
                            )
                        )
                    player.shoot_timer = cooldown
            else:
                cooldown = SWORD_COOLDOWN / self.effective_attack_rate_multiplier_for(player, inv)
                if player.sword_timer <= 0:
                    self.slashes.append(
                        Slash(
                            origin=Vector2(player.pos),
                            direction=direction,
                            radius=self.sword_radius_for(player, inv),
                            arc=self.sword_arc_for(player),
                            damage=self.sword_damage_for(player, inv),
                            execute_level=player.passives.get("execution_edge", 0),
                            shockwave_level=player.passives.get("shockwave", 0),
                            owner=pi,
                        )
                    )
                    player.sword_timer = cooldown
        else: # huntress
            if player.mode == "weapon_1":
                cooldown = (PROJECTILE_COOLDOWN * 1.3) / self.effective_attack_rate_multiplier_for(player, inv)
                if player.shoot_timer <= 0 and len(self.projectiles) < MAX_PROJECTILES:
                    if not self._consume_ranged_ammo_for(player):
                        return
                    # Quest hook: fail melee_only
                    if self.quest and self.quest["goal_type"] == "survive_melee":
                        self._fail_quest()
                    split_level = player.passives.get("splinter_arrows", 0)
                    side_pairs = 0 if split_level <= 0 else 1 + split_level // 6
                    angles = [0]
                    for pair in range(1, side_pairs + 1):
                        angles.extend((10 * pair, -10 * pair))
                    for angle in angles:
                        if len(self.projectiles) >= MAX_PROJECTILES:
                            break
                        shot_dir = direction.rotate(angle)
                        extra = angle != 0
                        self.projectiles.append(
                            Projectile(
                                pos=Vector2(player.pos) + shot_dir * (player.radius + 8),
                                vel=shot_dir * PROJECTILE_SPEED * 1.5,
                                damage=self.projectile_damage_for(player, inv) * (1.2 if not extra else 0.58 + split_level * 0.018),
                                freeze=player.buffs.get("freeze", 0) > 0,
                                pierce=2 if not extra else max(0, split_level // 5),
                                explosive_level=player.passives.get("explosive", 0),
                                homing_level=player.passives.get("homing", 0),
                                owner=pi,
                            )
                        )
                    player.shoot_timer = cooldown
            else:
                cooldown = (SWORD_COOLDOWN * 0.45) / self.effective_attack_rate_multiplier_for(player, inv)
                if player.sword_timer <= 0:
                    self.slashes.append(
                        Slash(
                            origin=Vector2(player.pos),
                            direction=direction,
                            radius=self.sword_radius_for(player, inv) * 0.65,
                            arc=self.dagger_arc_for(player),
                            damage=self.sword_damage_for(player, inv) * 0.45,
                            duration=SWORD_DURATION * 0.5,
                            prey_mark_level=player.passives.get("prey_mark", 0),
                            bleed_level=player.passives.get("bleeding_blades", 0),
                            shadow_lunge_level=player.passives.get("shadow_lunge", 0),
                            owner=pi,
                        )
                    )
                    player.sword_timer = cooldown

    # ------------------------------------------------------------------ #
    # PER-PLAYER STAT HELPERS                                              #
    # ------------------------------------------------------------------ #

    def effective_speed_multiplier_for(self, player):
        inv = self.get_inventory(player.player_index)
        chrono = inv.active_effect_level("chrono_boots")
        return player.speed_multiplier() * (1.0 + chrono * 0.015)

    def effective_attack_rate_multiplier_for(self, player, inv):
        blade = inv.active_effect_level("blade_relay")
        hybrid = inv.active_hybrid_level()
        both_bonus = player.passives.get("combat_drill", 0) * 0.01 + player.passives.get("predator_focus", 0) * 0.012
        return player.attack_rate_multiplier() * (1.0 + blade * 0.012 + hybrid * 0.01 + both_bonus)

    def projectile_damage_for(self, player, inv):
        storm = inv.active_effect_level("storm_core")
        ranged_mult = (
            1.0
            + player.passives.get("combat_drill", 0) * 0.025
            + player.passives.get("predator_focus", 0) * 0.020
            + player.passives.get("piercing_rounds", 0) * 0.015
        )
        return player.projectile_damage() * (1.0 + storm * 0.01) * ranged_mult

    def sword_damage_for(self, player, inv):
        blade = inv.active_effect_level("blade_relay")
        melee_mult = (
            1.0
            + player.passives.get("combat_drill", 0) * 0.025
            + player.passives.get("predator_focus", 0) * 0.020
            + player.passives.get("fan_blades", 0) * 0.018
        )
        return player.sword_damage() * (1.0 + blade * 0.012) * melee_mult

    def sword_radius_for(self, player, inv):
        blade = inv.active_effect_level("blade_relay")
        hybrid = inv.active_hybrid_level()
        melee_bonus = player.passives.get("wide_cleave", 0) * 0.030 + player.passives.get("fan_blades", 0) * 0.028
        return player.sword_radius() * (1.0 + blade * 0.018 + hybrid * 0.018 + melee_bonus)

    def sword_arc_for(self, player):
        return SWORD_ARC + math.radians(player.passives.get("wide_cleave", 0) * 2.4)

    def dagger_arc_for(self, player):
        return SWORD_ARC * 0.6 + math.radians(player.passives.get("fan_blades", 0) * 2.8)

    def magazine_capacity_for(self, player):
        level_capacity = BASE_MAGAZINE_CAPACITY + max(0, player.level - 1) * MAGAZINE_CAPACITY_PER_LEVEL
        return level_capacity + player.magazine_bonus

    def max_ammo_reserve_for(self, player):
        return STARTING_AMMO_RESERVE + max(0, player.level - 1) * 20

    def _consume_ranged_ammo_for(self, player):
        if player.reload_timer > 0:
            return False
        if player.ammo_magazine > 0:
            player.ammo_magazine = max(0, player.ammo_magazine - 1)
            if player.ammo_magazine <= 0:
                self._start_reload_for(player)
            return True
        self._start_reload_for(player)
        return False

    def _start_reload_for(self, player, forced=True, show_message=True):
        player.mode = "weapon_2"
        if forced:
            player.forced_reload = True
        
        capacity = self.magazine_capacity_for(player)
        if player.ammo_magazine >= capacity or player.ammo_reserve <= 0:
            if forced and show_message:
                self.message = f"J{player.player_index + 1} sem municao: lute corpo a corpo e colete cartuchos."
            return False

        reload_bonus = (
            player.passives.get("combat_drill", 0) * 0.015
            + player.passives.get("predator_focus", 0) * 0.015
            + player.reload_speed_bonus
        )
        player.reload_duration = max(0.75, RELOAD_DURATION * (1.0 - min(0.35, reload_bonus)))
        
        needed = capacity - player.ammo_magazine
        loaded = min(needed, player.ammo_reserve)
        time_per_bullet = player.reload_duration / capacity
        
        player.reload_timer = time_per_bullet * loaded
        player.reload_step_timer = time_per_bullet
        
        if forced and show_message:
            self.message = f"J{player.player_index + 1}: pente vazio: arma corpo a corpo ativa enquanto recarrega."
        return True



    # ------------------------------------------------------------------ #
    # MULTIPLAYER: TETHERING & REVIVE                                      #
    # ------------------------------------------------------------------ #

    def _update_tethering(self):
        if not self.multiplayer or not self.player2:
            return
        
        alive = self.alive_players()
        if len(alive) < 2:
            return

        p1, p2 = alive[0], alive[1]
        dist = p1.pos.distance_to(p2.pos)
        if dist > TETHER_MAX_DISTANCE:
            # Teleporta ambos para ficarem no limite permitido em relação ao ponto médio
            mid = (p1.pos + p2.pos) * 0.5
            diff = (p1.pos - p2.pos).normalize()
            limit = TETHER_MAX_DISTANCE * 0.48
            p1.pos = mid + diff * limit
            p2.pos = mid - diff * limit
            
            # Garante que não atravessam paredes no teleporte
            p1.pos = self.world.move_circle(p1.pos, p1.radius, Vector2(0, 0))
            p2.pos = self.world.move_circle(p2.pos, p2.radius, Vector2(0, 0))
            
            self.add_floater(mid, "Fiquem Juntos!", COLORS["special"])

    def _update_revive(self, dt):
        alive = [p for p in self.players if not p.is_down]
        down = [p for p in self.players if p.is_down]
        for downed in down:
            reviving = False
            for helper in alive:
                if helper.pos.distance_to(downed.pos) <= REVIVE_RADIUS:
                    downed.revive_progress += dt
                    reviving = True
                    if downed.revive_progress >= REVIVE_TIME:
                        downed.is_down = False
                        downed.health = downed.max_health * REVIVE_HP_PERCENT
                        downed.invulnerable_timer = 2.0
                        downed.revive_progress = 0.0
                        self.message = f"Jogador {downed.player_index + 1} revivido!"
                        self.add_floater(downed.pos, "REVIVIDO!", COLORS["xp"])
                    break
            if not reviving:
                downed.revive_progress = max(0, downed.revive_progress - dt * 0.5)

    def _spawn_enemies(self, dt):
        difficulty = 1.0 + self.time_alive / 85.0 + (self.player.level - 1) * 0.09
        self._update_special_spawns(dt, difficulty)

        if len(self.enemies) >= MAX_ENEMIES:
            return

        delay = max(SPAWN_MIN_DELAY, SPAWN_START_DELAY / difficulty)
        self.spawn_timer -= dt
        if self.spawn_timer > 0:
            return

        self.spawn_timer = delay
        amount = 1
        if self.time_alive > 80 and self.random.random() < 0.28:
            amount += 1
        if self.time_alive > 170 and self.random.random() < 0.18:
            amount += 1
        for _ in range(amount):
            self._spawn_one_enemy(difficulty)

    def _update_special_spawns(self, dt, difficulty):
        self.chromatic_spawn_timer -= dt
        if self.chromatic_spawn_timer <= 0:
            if len(self.enemies) < MAX_ENEMIES:
                self._spawn_special_enemy("chromatic", difficulty)
            self.chromatic_spawn_timer = self.random.uniform(CHROMATIC_SPAWN_MIN, CHROMATIC_SPAWN_MAX)

        self.miniboss_spawn_timer -= dt
        has_miniboss = any(enemy.kind == "miniboss" for enemy in self.enemies)
        if self.miniboss_spawn_timer <= 0:
            if self.time_alive > 45 and not has_miniboss and len(self.enemies) < MAX_ENEMIES:
                self._spawn_special_enemy("miniboss", difficulty)
            self.miniboss_spawn_timer = self.random.uniform(MINIBOSS_SPAWN_MIN, MINIBOSS_SPAWN_MAX)

    def _spawn_special_enemy(self, kind, difficulty):
        angle = self.random.random() * math.tau
        if kind == "chromatic":
            distance = self.random.uniform(420, 610)
            health_scale = min(2.2, 1.0 + (difficulty - 1.0) * 0.16)
            speed_scale = min(1.45, 1.0 + (difficulty - 1.0) * 0.06)
            lifetime = CHROMATIC_LIFETIME
            message = "Um Erratico Cromatico apareceu perto da tela."
        else:
            distance = self.random.uniform(650, 820)
            health_scale = min(2.4, 1.0 + (difficulty - 1.0) * 0.20)
            speed_scale = 1.0
            lifetime = -1
            message = "Mini-boss avistado: fique longe dos avisos vermelhos."

        pos = self.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance
        data = ENEMY_TYPES[kind]
        enemy = Enemy(
            id=self.enemy_id,
            pos=pos,
            kind=kind,
            radius=data["radius"],
            speed=data["speed"] * speed_scale * self.director_speed,
            max_health=data["health"] * health_scale * self.director_health,
            health=data["health"] * health_scale * self.director_health,
            damage=data["damage"] * self.director_damage,
            xp_value=data["xp"],
            color=data["color"],
            special_value=data["special"],
            coin_chance=data["coin_chance"],
            lifetime=lifetime,
            phase=self.random.random() * math.tau,
            special_timer=self.random.uniform(2.2, 4.0),
        )
        self.enemy_id += 1

        if not self.world.circle_hits_wall(enemy.pos, enemy.radius):
            self.enemies.append(enemy)
            self.message = message

    def _spawn_one_enemy(self, difficulty):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(SPAWN_DISTANCE_MIN, SPAWN_DISTANCE_MAX)
        pos = self.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance

        roll = self.random.random()
        if self.time_alive > 190 and roll < 0.10:
            kind = "sapper"
        elif self.time_alive > 150 and roll < 0.22:
            kind = "bulwark"
        elif self.time_alive > 95 and roll < 0.29: # Reduzido de 0.34 (12% -> 7%)
            kind = "spitter"
        elif self.time_alive > 75 and roll < 0.48:
            kind = "brute"
        elif self.time_alive > 25 and roll < 0.72:
            kind = "runner"
        else:
            kind = "basic"

        data = ENEMY_TYPES[kind]
        enemy = Enemy(
            id=self.enemy_id,
            pos=pos,
            kind=kind,
            radius=data["radius"],
            speed=data["speed"] * min(1.75, 1.0 + (difficulty - 1.0) * 0.08) * self.director_speed,
            max_health=data["health"] * min(2.6, 1.0 + (difficulty - 1.0) * 0.18) * self.director_health,
            health=data["health"] * min(2.6, 1.0 + (difficulty - 1.0) * 0.18) * self.director_health,
            damage=data["damage"] * self.director_damage,
            xp_value=data["xp"],
            color=data["color"],
            special_value=data["special"],
            coin_chance=data["coin_chance"],
        )
        self.enemy_id += 1

        if not self.world.circle_hits_wall(enemy.pos, enemy.radius):
            self.enemies.append(enemy)

    def _update_projectiles(self, dt):
        alive = []
        for projectile in self.projectiles:
            if projectile.homing_level > 0 and projectile.life > 0:
                best_target = None
                best_dist = 400**2
                for enemy in self.enemies:
                    if enemy.id in projectile.hit_ids: continue
                    d = projectile.pos.distance_squared_to(enemy.pos)
                    if d < best_dist:
                        best_dist = d
                        best_target = enemy
                if best_target:
                    direction = (best_target.pos - projectile.pos).normalize()
                    speed = projectile.vel.length()
                    new_dir = (projectile.vel.normalize() * 0.9 + direction * 0.1 * projectile.homing_level).normalize()
                    projectile.vel = new_dir * speed

            projectile.life -= dt
            projectile.pos += projectile.vel * dt
            if projectile.life <= 0 or self.world.circle_hits_wall(projectile.pos, projectile.radius, include_destructibles=False):
                if projectile.explosive_level > 0:
                    self.item_events.append({
                        "type": "explosion",
                        "pos": Vector2(projectile.pos),
                        "radius": 40 + projectile.explosive_level * 12,
                        "damage": projectile.damage * (0.5 + projectile.explosive_level * 0.15),
                        "age": 0,
                        "duration": 0.2
                    })
                continue

            hit = False
            min_damage_required = (SWORD_DAMAGE // 10) * 10 - 5
            for item in self.world.nearby_destructibles(projectile.pos.x, projectile.pos.y, projectile.radius + 24):
                if item.id in projectile.hit_ids:
                    continue
                if circle_rect_overlap(projectile.pos.x, projectile.pos.y, projectile.radius, item.rect):
                    projectile.hit_ids.add(item.id)
                    hit = True
                    if projectile.damage >= min_damage_required:
                        self.damage_destructible(item, projectile.damage)
                    break
            if hit:
                if projectile.explosive_level > 0:
                    self.item_events.append({
                        "type": "explosion",
                        "pos": Vector2(projectile.pos),
                        "radius": 40 + projectile.explosive_level * 12,
                        "damage": projectile.damage * (0.5 + projectile.explosive_level * 0.15),
                        "age": 0,
                        "duration": 0.2
                    })
                if projectile.pierce > 0:
                    projectile.pierce -= 1
                    alive.append(projectile)
                elif self._try_ricochet(projectile):
                    alive.append(projectile)
                continue

            for enemy in list(self.enemies):
                if enemy.id in projectile.hit_ids:
                    continue
                if projectile.pos.distance_squared_to(enemy.pos) <= (projectile.radius + enemy.radius) ** 2:
                    projectile.hit_ids.add(enemy.id)
                    if projectile.freeze:
                        enemy.frozen_timer = max(enemy.frozen_timer, FREEZE_DURATION)
                    if projectile.poison:
                        enemy.poison_timer = max(enemy.poison_timer, POISON_DURATION)
                        enemy.poison_dps = max(enemy.poison_dps, projectile.poison_dps)
                    self.damage_enemy(enemy, projectile.damage, source="projectile")

                    if projectile.pierce > 0:
                        projectile.pierce -= 1
                        alive.append(projectile)
                    elif self._try_ricochet(projectile):
                        alive.append(projectile)
                    else:
                        if projectile.explosive_level > 0:
                            self.item_events.append({
                                "type": "explosion",
                                "pos": Vector2(projectile.pos),
                                "radius": 40 + projectile.explosive_level * 12,
                                "damage": projectile.damage * (0.5 + projectile.explosive_level * 0.15),
                                "age": 0,
                                "duration": 0.2
                            })
                    hit = True
                    break

            if not hit:
                alive.append(projectile)

        self.projectiles = alive

    def _try_ricochet(self, projectile):
        if projectile.bounces_left <= 0:
            return False

        target = None
        target_distance = RICOCHET_RANGE * RICOCHET_RANGE
        for enemy in self.enemies:
            if enemy.id in projectile.hit_ids:
                continue
            distance_sq = projectile.pos.distance_squared_to(enemy.pos)
            if distance_sq < target_distance:
                target = enemy
                target_distance = distance_sq

        if target is None:
            return False

        direction = target.pos - projectile.pos
        if direction.length_squared() <= 0:
            return False

        direction = direction.normalize()
        projectile.vel = direction * PROJECTILE_SPEED
        projectile.pos += direction * (projectile.radius + 8)
        projectile.damage *= RICOCHET_DAMAGE_MULTIPLIER
        projectile.bounces_left -= 1
        projectile.life = max(projectile.life, 0.28)
        return True

    def _update_world_timers(self, dt):
        for chunk in self.world.chunks.values():
            for item in chunk["destructibles"]:
                item.hit_flash = max(0, item.hit_flash - dt)

    def _update_slashes(self, dt):
        alive = []
        for slash in self.slashes:
            slash.age += dt
            self._apply_slash_hits(slash)
            if slash.age < slash.duration:
                alive.append(slash)
        self.slashes = alive

    def _apply_slash_hits(self, slash):
        owner = self.get_player(slash.owner)
        origin = owner.pos
        slash.origin = Vector2(origin)
        for enemy in list(self.enemies):
            if enemy.id in slash.hit_ids:
                continue
            to_enemy = enemy.pos - origin
            distance_sq = to_enemy.length_squared()
            if distance_sq > (slash.radius + enemy.radius) ** 2 or distance_sq <= 0:
                continue
            if slash.direction.angle_to(to_enemy) ** 2 <= math.degrees(slash.arc * 0.5) ** 2:
                slash.hit_ids.add(enemy.id)
                hit_pos = Vector2(enemy.pos)
                enemy.knockback += to_enemy.normalize() * 330
                damage = slash.damage
                if slash.prey_mark_level > 0:
                    enemy.speed *= max(0.4, 1.0 - 0.05 * slash.prey_mark_level)
                    damage *= 1.0 + 0.1 * slash.prey_mark_level
                if slash.execute_level > 0 and enemy.health <= enemy.max_health * 0.42:
                    damage *= 1.0 + 0.08 * slash.execute_level
                if slash.bleed_level > 0:
                    enemy.bleed_timer = max(enemy.bleed_timer, 2.2 + slash.bleed_level * 0.12)
                    enemy.bleed_dps = max(enemy.bleed_dps, 4.0 + slash.bleed_level * 2.2)
                if slash.shadow_lunge_level > 0:
                    owner.dash_cooldown = max(0, owner.dash_cooldown - 0.035 * slash.shadow_lunge_level)
                    owner.invulnerable_timer = max(owner.invulnerable_timer, 0.02 * slash.shadow_lunge_level)
                self.damage_enemy(enemy, damage, source="sword", killer_index=slash.owner)
                if slash.shockwave_level > 0:
                    self._apply_slash_shockwave(hit_pos, slash.shockwave_level, slash.damage, slash.hit_ids)

        for item in list(self.world.nearby_destructibles(origin.x, origin.y, slash.radius + 64)):
            marker = f"item:{item.id}"
            if marker in slash.hit_ids:
                continue
            center = item.rect.center
            to_item = center - origin
            if to_item.length_squared() > (slash.radius + 36) ** 2 or to_item.length_squared() <= 0:
                continue
            if slash.direction.angle_to(to_item) ** 2 <= math.degrees(slash.arc * 0.5) ** 2:
                slash.hit_ids.add(marker)
                self.damage_destructible(item, slash.damage)

    def _apply_slash_shockwave(self, center, level, base_damage, hit_ids):
        radius = 52 + level * 7
        damage = base_damage * (0.14 + level * 0.035)
        for other in list(self.enemies):
            if other.id in hit_ids:
                continue
            if other.pos.distance_squared_to(center) > (radius + other.radius) ** 2:
                continue
            hit_ids.add(other.id)
            push = other.pos - center
            if push.length_squared() > 0:
                other.knockback += push.normalize() * (95 + level * 8)
            self.damage_enemy(other, damage, source="sword")

    def _nearest_alive_player(self, pos):
        best = self.player
        best_dist = pos.distance_squared_to(self.player.pos) if not self.player.is_down else 999999999
        if self.multiplayer and self.player2 is not None and not self.player2.is_down:
            d2 = pos.distance_squared_to(self.player2.pos)
            if d2 < best_dist:
                best = self.player2
        return best

    def _update_enemies(self, dt):
        alive_list = []
        for enemy in list(self.enemies):
            enemy.phase += dt
            enemy.frozen_timer = max(0, enemy.frozen_timer - dt)
            enemy.hit_flash = max(0, enemy.hit_flash - dt)
            if enemy.lifetime > 0:
                enemy.lifetime -= dt
                if enemy.lifetime <= 0 and enemy.kind == "chromatic":
                    self.add_floater(enemy.pos, "escapou", COLORS["muted"])
                    continue
            if enemy.poison_timer > 0:
                enemy.poison_timer = max(0, enemy.poison_timer - dt)
                self.damage_enemy(enemy, enemy.poison_dps * dt, source="poison")
                if enemy.health <= 0:
                    continue
            if enemy.bleed_timer > 0:
                enemy.bleed_timer = max(0, enemy.bleed_timer - dt)
                self.damage_enemy(enemy, enemy.bleed_dps * dt, source="bleed")
                if enemy.health <= 0:
                    continue

            target = self._nearest_alive_player(enemy.pos)
            to_player = target.pos - enemy.pos
            if to_player.length_squared() > 0:
                direction = to_player.normalize()
            else:
                direction = Vector2(1, 0)

            slow = 0.28 if enemy.frozen_timer > 0 else 1.0
            chase_speed = enemy.speed * slow * self.world.hazard_speed_multiplier_at(enemy.pos.x, enemy.pos.y)
            if enemy.kind == "chromatic":
                velocity = self._chromatic_velocity(enemy, chase_speed)
            elif enemy.kind == "miniboss":
                velocity = self._miniboss_velocity(enemy, direction, chase_speed, dt)
            elif enemy.kind == "spitter":
                velocity = self._spitter_velocity(enemy, direction, chase_speed, dt)
            else:
                velocity = direction * chase_speed
            if enemy.knockback.length_squared() > 1:
                velocity += enemy.knockback
                enemy.knockback *= max(0, 1.0 - 7.0 * dt)

            enemy.pos = self._move_enemy(enemy, direction, chase_speed, velocity, dt)

            # Contact damage: check all alive players
            sapper_detonated = False
            for player in self.alive_players():
                distance_sq = enemy.pos.distance_squared_to(player.pos)
                if enemy.kind == "sapper" and distance_sq <= (enemy.radius + player.radius + 38) ** 2:
                    self._detonate_sapper(enemy)
                    sapper_detonated = True
                    break
                contact_radius = enemy.radius + player.radius
                if distance_sq <= contact_radius * contact_radius:
                    if player.shield_timer > 0:
                        push = enemy.pos - player.pos
                        if push.length_squared() > 0:
                            enemy.knockback += push.normalize() * 460
                        self.damage_enemy(enemy, 22 * dt, source="shield")
                    elif player.invulnerable_timer <= 0:
                        self._damage_player_direct(player, enemy.damage * dt)
            if sapper_detonated:
                continue

            if enemy.health > 0:
                alive_list.append(enemy)
        self.enemies = alive_list

    def _chromatic_velocity(self, enemy, chase_speed):
        target = self._nearest_alive_player(enemy.pos)
        offset = enemy.pos - target.pos
        if offset.length_squared() <= 0.001:
            offset = Vector2(1, 0)
        distance = offset.length()
        away = offset.normalize()
        tangent = away.rotate(90 if math.sin(enemy.phase * 2.7 + enemy.id) >= 0 else -90)
        jitter = Vector2(math.cos(enemy.phase * 5.3 + enemy.id), math.sin(enemy.phase * 4.7))

        if distance < 330:
            desired = away * 1.55 + tangent * 0.9 + jitter * 0.35
        elif distance > 620:
            desired = away * -1.15 + tangent * 0.75 + jitter * 0.25
        else:
            desired = away * 0.45 + tangent * 1.15 + jitter * 0.35

        if desired.length_squared() <= 0.001:
            desired = away
        return desired.normalize() * chase_speed

    def _spitter_velocity(self, enemy, direction, chase_speed, dt):
        target = self._nearest_alive_player(enemy.pos)
        if enemy.action:
            enemy.action_timer -= dt
            if enemy.action_timer <= 0:
                if enemy.action == "spit_warn":
                    start = Vector2(enemy.pos)
                    end = Vector2(enemy.target_pos)
                    self._apply_laser_damage(start, end, 32, 26, ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "laser",
                        "start": start,
                        "end": end,
                        "width": 32,
                        "age": 0.0,
                        "duration": 0.18,
                        "color": "#84CC16",
                    })
                enemy.action = ""
                enemy.special_timer = self.random.uniform(2.8, 4.2)
            return Vector2(0, 0)

        enemy.special_timer -= dt
        offset = enemy.pos - target.pos
        distance = offset.length() if offset.length_squared() > 0 else 1.0
        
        # Menor frequência de disparos
        if enemy.special_timer <= 0 and 280 < distance < 650:
            self._start_spitter_shot(enemy)
            return Vector2(0, 0)

        away = offset.normalize() if offset.length_squared() > 0 else Vector2(1, 0)
        tangent = away.rotate(90 if math.sin(enemy.phase * 2.0 + enemy.id) > 0 else -90)
        
        # Ajuste de distâncias de fuga e perseguição
        if distance < 380: # Aumentado de 340
            desired = away * 1.1 + tangent * 0.3 # Velocidade de fuga levemente reduzida
        elif distance > 550: # Reduzido de 590
            desired = -away + tangent * 0.25
        else:
            desired = tangent * 0.65
        return desired.normalize() * chase_speed

    def _start_spitter_shot(self, enemy):
        target = self._nearest_alive_player(enemy.pos)
        direction = target.pos - enemy.pos
        if direction.length_squared() <= 0.001:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        start = Vector2(enemy.pos)
        end = start + direction * 620
        enemy.target_pos = end
        enemy.action = "spit_warn"
        enemy.action_timer = 0.62
        self.item_events.append({
            "type": "danger_line",
            "start": start,
            "end": end,
            "width": 32,
            "age": 0.0,
            "duration": 0.62,
            "color": "#84CC16",
        })

    def _detonate_sapper(self, enemy):
        center = Vector2(enemy.pos)
        self._apply_area_damage(center, 118, 42, "sapper", ignore_enemy=enemy)
        self.item_events.append({
            "type": "explosion",
            "pos": center,
            "radius": 118,
            "damage": 0,
            "age": 0.0,
            "duration": 0.28,
        })
        self.screen_shake = max(self.screen_shake, 9.0)
        self.add_floater(center, "BOOM", COLORS["coin"])

    def _miniboss_velocity(self, enemy, direction, chase_speed, dt):
        enemy.summon_cooldown = max(0.0, enemy.summon_cooldown - dt)
        if enemy.action:
            enemy.action_timer -= dt
            if enemy.action_timer <= 0:
                if enemy.action == "leap_warn":
                    landing = Vector2(enemy.target_pos)
                    enemy.pos = self.world.move_circle(landing, enemy.radius, Vector2(0, 0), include_destructibles=False)
                    self._apply_area_damage(landing, MINIBOSS_LEAP_RADIUS, MINIBOSS_LEAP_DAMAGE, "miniboss", ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "explosion",
                        "pos": landing,
                        "radius": MINIBOSS_LEAP_RADIUS,
                        "damage": 0,
                        "age": 0.0,
                        "duration": 0.28,
                    })
                    self.screen_shake = max(self.screen_shake, 13.0)
                elif enemy.action == "laser_warn":
                    start = Vector2(enemy.pos)
                    end = Vector2(enemy.target_pos)
                    self._apply_laser_damage(start, end, MINIBOSS_LASER_WIDTH, MINIBOSS_LASER_DAMAGE, ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "laser",
                        "start": start,
                        "end": end,
                        "width": MINIBOSS_LASER_WIDTH,
                        "age": 0.0,
                        "duration": 0.22,
                        "color": "#F97316",
                    })
                    self.screen_shake = max(self.screen_shake, 8.0)
                elif enemy.action == "shockwave_warn":
                    center = Vector2(enemy.pos)
                    self._apply_area_damage(center, 220, 36, "miniboss", ignore_enemy=enemy)
                    self.item_events.append({
                        "type": "explosion",
                        "pos": center,
                        "radius": 220,
                        "damage": 0,
                        "age": 0.0,
                        "duration": 0.34,
                    })
                    self.screen_shake = max(self.screen_shake, 12.0)
                # summon action ends silently — minions were spawned at start

                enemy.action = ""
                enemy.special_timer = self.random.uniform(3.2, 5.2)
            return Vector2(0, 0)

        enemy.special_timer -= dt
        target_mb = self._nearest_alive_player(enemy.pos)
        if enemy.special_timer <= 0 and enemy.pos.distance_squared_to(target_mb.pos) < (900 * 900):
            roll = self.random.random()
            if not enemy.enraged and enemy.health <= enemy.max_health * 0.45:
                enemy.enraged = True
                enemy.speed *= 1.22
                enemy.damage *= 1.18
                self.message = "Mini-boss enfurecido!"
            if roll < 0.26 and enemy.summon_cooldown <= 0:
                self._start_miniboss_summon(enemy)
            elif roll < 0.52:
                self._start_miniboss_leap(enemy)
            elif roll < 0.78:
                self._start_miniboss_laser(enemy)
            else:
                self._start_miniboss_shockwave(enemy)
            return Vector2(0, 0)

        return direction * chase_speed

    def _start_miniboss_leap(self, enemy):
        leap_target = self._nearest_alive_player(enemy.pos)
        target = Vector2(leap_target.pos) + self.random_offset(70)
        enemy.target_pos = target
        enemy.action = "leap_warn"
        enemy.action_timer = MINIBOSS_LEAP_WARNING
        self.item_events.append({
            "type": "danger_circle",
            "pos": target,
            "radius": MINIBOSS_LEAP_RADIUS,
            "age": 0.0,
            "duration": MINIBOSS_LEAP_WARNING,
            "color": COLORS["danger"],
        })
        self.message = "Salto do mini-boss: saia do circulo vermelho."

    def _start_miniboss_laser(self, enemy):
        laser_target = self._nearest_alive_player(enemy.pos)
        direction = laser_target.pos - enemy.pos
        if direction.length_squared() <= 0.001:
            direction = Vector2(1, 0)
        direction = direction.normalize()
        start = Vector2(enemy.pos)
        end = start + direction * MINIBOSS_LASER_RANGE
        enemy.target_pos = end
        enemy.action = "laser_warn"
        enemy.action_timer = MINIBOSS_LASER_WARNING
        self.item_events.append({
            "type": "danger_line",
            "start": start,
            "end": end,
            "width": MINIBOSS_LASER_WIDTH,
            "age": 0.0,
            "duration": MINIBOSS_LASER_WARNING,
            "color": COLORS["danger"],
        })
        self.message = "Laser do mini-boss: fuja da faixa vermelha."

    def _start_miniboss_shockwave(self, enemy):
        enemy.action = "shockwave_warn"
        enemy.action_timer = 0.78
        self.item_events.append({
            "type": "danger_circle",
            "pos": Vector2(enemy.pos),
            "radius": 220,
            "age": 0.0,
            "duration": 0.78,
            "color": COLORS["danger"],
        })
        self.message = "Pulso do mini-boss: afaste-se."

    def _move_enemy(self, enemy, direction, chase_speed, velocity, dt):
        old_pos = Vector2(enemy.pos)
        intended = velocity * dt
        candidate = self.world.move_circle(old_pos, enemy.radius, intended, include_destructibles=False)
        if intended.length_squared() <= 1:
            return candidate

        moved_sq = candidate.distance_squared_to(old_pos)
        blocked = moved_sq < intended.length_squared() * 0.08
        if not blocked:
            return candidate

        best_pos = candidate
        best_score = -999999.0
        for angle in (90, -90, 45, -45, 135, -135):
            detour = direction.rotate(angle)
            test_pos = self.world.move_circle(
                old_pos,
                enemy.radius,
                detour * chase_speed * dt,
                include_destructibles=False,
            )
            progress = old_pos.distance_to(self.player.pos) - test_pos.distance_to(self.player.pos)
            movement = test_pos.distance_squared_to(old_pos)
            score = progress * 12 + movement
            if score > best_score:
                best_score = score
                best_pos = test_pos
        return best_pos

    def _damage_player(self, amount, source="hit"):
        if amount <= 0 or self.player.shield_timer > 0 or self.player.invulnerable_timer > 0:
            return False
        self.player.health -= amount * self.incoming_damage_multiplier()
        if amount >= 1:
            self.add_floater(self.player.pos, f"-{int(amount)}", COLORS["danger"])
        return True

    def _damage_player_direct(self, player, amount, source="hit"):
        if amount <= 0 or player.shield_timer > 0 or player.invulnerable_timer > 0:
            return False
        inv = self.get_inventory(player.player_index)
        guardian = inv.active_effect_level("guardian_plate")
        mult = 1.0
        if guardian > 0 and player.health / player.max_health <= 0.42:
            mult = max(0.52, 1.0 - (0.10 + guardian * 0.022))
        player.health -= amount * mult
        if amount >= 1:
            self.add_floater(player.pos, f"-{int(amount)}", COLORS["danger"])
        return True

    def _apply_area_damage(self, center, radius, damage, source, ignore_enemy=None):
        center = Vector2(center)
        for player in self.alive_players():
            if player.pos.distance_squared_to(center) <= (radius + player.radius) ** 2:
                self._damage_player_direct(player, damage, source=source)

        for enemy in list(self.enemies):
            if enemy is ignore_enemy:
                continue
            if enemy.pos.distance_squared_to(center) <= (radius + enemy.radius) ** 2:
                push = enemy.pos - center
                if push.length_squared() > 0:
                    enemy.knockback += push.normalize() * 360
                self.damage_enemy(enemy, damage, source=source)

    def _apply_laser_damage(self, start, end, width, damage, ignore_enemy=None, damage_player=True, killer_index=0):
        if damage_player:
            for player in self.alive_players():
                radius_sq = (width * 0.5 + player.radius) ** 2
                if self._point_segment_distance_sq(player.pos, start, end) <= radius_sq:
                    self._damage_player_direct(player, damage, source="laser")

        for enemy in list(self.enemies):
            if enemy is ignore_enemy:
                continue
            enemy_radius_sq = (width * 0.5 + enemy.radius) ** 2
            if self._point_segment_distance_sq(enemy.pos, start, end) <= enemy_radius_sq:
                self.damage_enemy(enemy, damage, source="laser", killer_index=killer_index)

    def _point_segment_distance_sq(self, point, start, end):
        segment = end - start
        length_sq = segment.length_squared()
        if length_sq <= 0.001:
            return point.distance_squared_to(start)
        t = max(0.0, min(1.0, (point - start).dot(segment) / length_sq))
        closest = start + segment * t
        return point.distance_squared_to(closest)

    def _repel_enemies(self, dt, player=None):
        if player is None:
            player = self.player
        for enemy in self.enemies:
            distance = enemy.pos.distance_to(player.pos)
            if 0 < distance < 130:
                direction = (enemy.pos - player.pos).normalize()
                enemy.pos = self.world.move_circle(
                    enemy.pos,
                    enemy.radius,
                    direction * 280 * dt,
                    include_destructibles=False,
                )
                enemy.knockback += direction * 180 * dt

    def _update_hazards(self, dt):
        focus = self.camera_focus  # já é um Vector2
        for hazard in list(self.world.nearby_hazards(focus.x, focus.y, 980)):
            hazard.pulse += dt
            if hazard.kind == "mine":
                trigger_pos = None
                for player in self.alive_players():
                    if circle_rect_overlap(player.pos.x, player.pos.y, player.radius + MINE_TRIGGER_RADIUS, hazard.rect):
                        trigger_pos = Vector2(player.pos)
                        break
                if trigger_pos is None:
                    for enemy in list(self.enemies):
                        if circle_rect_overlap(enemy.pos.x, enemy.pos.y, enemy.radius + MINE_TRIGGER_RADIUS, hazard.rect):
                            trigger_pos = Vector2(enemy.pos)
                            break
                if trigger_pos is not None:
                    self._detonate_mine(hazard, trigger_pos)

            elif hazard.kind == "fire":
                for player in self.alive_players():
                    if circle_rect_overlap(player.pos.x, player.pos.y, player.radius, hazard.rect):
                        self._damage_player_direct(player, FIRE_DAMAGE_PER_SECOND * dt, source="fire")
                        self._player_in_fire = True
                for enemy in list(self.enemies):
                    if circle_rect_overlap(enemy.pos.x, enemy.pos.y, enemy.radius, hazard.rect):
                        self.damage_enemy(enemy, FIRE_DAMAGE_PER_SECOND * 0.72 * dt, source="fire")

    def _detonate_mine(self, hazard, trigger_pos):
        self.world.remove_hazard(hazard)
        self._apply_area_damage(trigger_pos, MINE_EXPLOSION_RADIUS, MINE_DAMAGE, "mine")
        self.item_events.append({
            "type": "explosion",
            "pos": Vector2(trigger_pos),
            "radius": MINE_EXPLOSION_RADIUS,
            "damage": 0,
            "age": 0.0,
            "duration": 0.32,
        })
        self.screen_shake = max(self.screen_shake, 12.0)
        self.message = "Mina terrestre detonada."

    def _update_item_system(self, dt):
        self.special_box_timer -= dt
        if self.special_box_timer <= 0:
            self.spawn_drop("item_box", self.player.pos + self.random_offset(320), 1)
            self.special_box_timer = self.random.uniform(32.0, 44.0)
            self.message = "Uma Caixa Especial surgiu por perto."

        for item in self.inventory.active_items():
            if "storm_core" in item.effect_keys():
                item.timers["storm"] = item.timers.get("storm", 1.0) - dt
                if item.timers["storm"] <= 0:
                    self._trigger_storm_item(item)

        alive_events = []
        for event in self.item_events:
            if event.get("type") == "arrow_rain":
                event["timer"] -= dt
                event["age"] = event.get("age", 0.0) + dt
                if event["timer"] > 0:
                    alive_events.append(event)
                    if self.random.random() < dt * 15:
                        for enemy in list(self.enemies):
                            if enemy.pos.distance_squared_to(event["pos"]) <= event["radius"]**2:
                                self.damage_enemy(enemy, event["damage"], source="special")
            else:
                if event.get("type") == "explosion" and event.get("age", 0) == 0 and event.get("damage", 0) > 0:
                    for enemy in list(self.enemies):
                        if enemy.pos.distance_squared_to(event["pos"]) <= event["radius"]**2:
                            self.damage_enemy(enemy, event.get("damage", 0), source="projectile")
                            enemy.knockback += (enemy.pos - event["pos"]).normalize() * 150 if enemy.pos != event["pos"] else Vector2(1, 0)

                event["age"] = event.get("age", 0.0) + dt
                if event["age"] < event.get("duration", 1.0):
                    alive_events.append(event)
        self.item_events = alive_events[-24:]

    def _trigger_storm_item(self, item):
        target = self._nearest_enemy(self.player.pos, 520 + item.level * 18)
        cooldown = max(1.8, 5.2 - item.level * 0.18 - self.hybrid_level() * 0.08)
        item.timers["storm"] = cooldown
        if target is None:
            return

        damage = 22 + item.level * 8
        self.damage_enemy(target, damage, source="storm")
        self.item_events.append(
            {
                "start": Vector2(self.player.pos),
                "end": Vector2(target.pos),
                "age": 0.0,
                "duration": 0.18,
                "color": COLORS["special"],
            }
        )

    def _nearest_enemy(self, pos, radius):
        best = None
        best_distance = radius * radius
        for enemy in self.enemies:
            distance = enemy.pos.distance_squared_to(pos)
            if distance < best_distance:
                best = enemy
                best_distance = distance
        return best

    def _update_drops(self, dt):
        alive = []
        for drop in self.drops:
            drop.ttl -= dt
            drop.bob += dt * 6
            # Find nearest alive player for attraction/pickup
            nearest = self.player
            nearest_dist = 999999
            for player in self.alive_players():
                d = player.pos.distance_to(drop.pos)
                if d < nearest_dist:
                    nearest = player
                    nearest_dist = d
            to_player = nearest.pos - drop.pos
            distance = to_player.length()

            magnet_radius = self.drop_magnet_radius(drop.kind)
            if 0 < distance < magnet_radius:
                drop.pos += to_player.normalize() * DROP_ATTRACT_SPEED * dt

            if distance <= DROP_PICKUP_RADIUS + drop.radius:
                if self.collect_drop(drop, nearest):
                    continue
            if drop.ttl > 0:
                alive.append(drop)
        self.drops = alive

    def _update_floaters(self, dt):
        alive = []
        for floater in self.floaters:
            floater["age"] += dt
            floater["pos"].y -= 24 * dt
            if floater["age"] < floater["duration"]:
                alive.append(floater)
        self.floaters = alive[-35:]

    def _update_camera(self, dt):
        focus_pos = self.camera_focus
        target = Vector2(
            focus_pos.x - SCREEN_WIDTH * 0.5,
            focus_pos.y - SCREEN_HEIGHT * 0.5,
        )
        
        # Zoom dinâmico no multiplayer
        if self.multiplayer and self.player2:
            alive = self.alive_players()
            if len(alive) == 2:
                dist = alive[0].pos.distance_to(alive[1].pos)
                scale = 1.0
                if dist > 300:
                    t = min(1.0, (dist - 300) / (CAMERA_ZOOM_MAX_DISTANCE - 300))
                    scale = 1.0 - t * (1.0 - CAMERA_ZOOM_MIN_SCALE)
                self.camera_zoom += (scale - self.camera_zoom) * dt * 2.0
            else:
                self.camera_zoom += (1.0 - self.camera_zoom) * dt * 2.0
        else:
            self.camera_zoom = 1.0

        self.camera += (target - self.camera) * min(1.0, CAMERA_SMOOTHING * dt)

    def damage_enemy(self, enemy, amount, source="hit", killer_index=0):
        if enemy.kind != "bulwark" and source not in ("fire", "mine", "special"):
            for protector in self.enemies:
                if protector.kind == "bulwark" and protector.health > 0:
                    if protector.pos.distance_squared_to(enemy.pos) <= 220 * 220:
                        amount *= 0.72
                        break
        enemy.health -= amount
        enemy.hit_flash = 0.08
        if amount >= 1:
            self.add_floater(enemy.pos, str(int(amount)), "#FDE68A" if source == "sword" else "#BAE6FD")
        if enemy.health <= 0 and enemy in self.enemies:
            self.kill_enemy(enemy, source=source, killer_index=killer_index)

    def kill_enemy(self, enemy, source="hit", killer_index=0):
        self.enemies.remove(enemy)
        killer = self.get_player(killer_index)
        killer.kills += 1
        killer.score += int(enemy.xp_value * 10 + self.time_alive)

        # Quest hooks (team-based)
        if self.quest:
            gt = self.quest["goal_type"]
            if gt == "kill_count":
                self.quest_progress += 1
            elif gt == "kill_brutes" and enemy.kind == "brute":
                self.quest_progress += 1

        if source != "special":
            self._add_special_from_source(enemy.special_value, source, killer)
        if killer.vampirism > 0 and killer.health < killer.max_health:
            heal = min(killer.vampirism, killer.max_health - killer.health)
            killer.health += heal
            if heal > 0:
                self.add_floater(killer.pos, f"+{heal:.0f}", COLORS["health"])
        self._apply_kill_resource_passives(enemy, source, killer)

        if enemy.kind == "miniboss":
            self._grant_miniboss_reward(enemy.pos, killer_index)
            return

        self.spawn_drop("xp", enemy.pos, enemy.xp_value)
        ammo_amount = self._ammo_drop_amount(enemy)
        if ammo_amount > 0:
            self.spawn_drop("ammo", enemy.pos + self.random_offset(20), ammo_amount)
        if self.random.random() < enemy.coin_chance:
            self.spawn_drop("coin", enemy.pos + self.random_offset(18), 1)
        if self.random.random() < 0.035:
            self.spawn_drop("heal", enemy.pos + self.random_offset(22), 22)
        if self.random.random() < 0.018:
            self.spawn_drop("shield", enemy.pos + self.random_offset(22), 1)
        if enemy.kind == "chromatic":
            self._grant_random_reward(enemy.pos, strong=False, player_index=killer_index)

    def _add_special_from_source(self, amount, source, player=None):
        if player is None:
            player = self.player
        if source in ("sword", "bleed", "shield", "relic"):
            player.add_special(amount, "melee")
        elif source in ("projectile", "poison", "storm"):
            player.add_special(amount, "ranged")

    def _ammo_drop_amount(self, enemy):
        chances = {
            "basic": 0.18,
            "runner": 0.16,
            "brute": 0.42,
            "chromatic": 0.70,
            "spitter": 0.26,
            "bulwark": 0.46,
            "sapper": 0.22,
            "minion": 0.08,
        }
        if self.random.random() >= chances.get(enemy.kind, 0.0):
            return 0
        if enemy.kind == "brute":
            return self.random.randint(10, 18)
        if enemy.kind == "chromatic":
            return self.random.randint(18, 30)
        if enemy.kind == "bulwark":
            return self.random.randint(14, 24)
        if enemy.kind == "sapper":
            return self.random.randint(6, 14)
        if enemy.kind == "minion":
            return self.random.randint(2, 5)
        return self.random.randint(AMMO_DROP_PICKUP_MIN, AMMO_DROP_PICKUP_MAX)

    def _apply_kill_resource_passives(self, enemy, source, player=None):
        if player is None:
            player = self.player
        salvage = player.passives.get("field_salvage", 0)
        if salvage > 0 and self.random.random() < min(0.45, 0.035 * salvage):
            gained = 2 + salvage // 2
            player.ammo_reserve += gained
            self.add_floater(player.pos, f"+{gained} mun", COLORS["projectile"])
            if player.ammo_magazine <= 0 and player.reload_timer <= 0:
                self._start_reload_for(player)

        siphon = player.passives.get("ammo_siphon", 0)
        if siphon > 0 and source != "special" and self.random.random() < min(0.40, 0.030 * siphon):
            gained = 2 + siphon // 3
            player.ammo_reserve += gained
            player.add_special(1.5 + siphon * 0.35, "ranged" if source in ("projectile", "poison", "storm") else "melee")
            self.add_floater(player.pos, f"+{gained} mun", COLORS["projectile"])
            if player.ammo_magazine <= 0 and player.reload_timer <= 0:
                self._start_reload_for(player)

    def damage_destructible(self, item, amount):
        item.hp -= amount
        item.hit_flash = 0.08
        if item.hp <= 0:
            self.destroy_destructible(item)

    def destroy_destructible(self, item):
        center = item.rect.center
        self.world.remove_destructible(item)
        if item.kind == "special":
            self.spawn_drop("item_box", center + self.random_offset(16), 1)
            self.spawn_drop("coin", center + self.random_offset(20), 1)
            return

        self.spawn_drop("coin", center + self.random_offset(18), 1)
        roll = self.random.random()
        if roll < 0.18:
            self.spawn_drop("heal", center + self.random_offset(22), 20)
        elif roll < 0.28:
            self.spawn_drop("shield", center + self.random_offset(22), 1)
        elif roll < 0.45:
            self.spawn_drop("xp", center + self.random_offset(22), 8)
        elif item.kind == "cache" and roll < 0.58:
            self.spawn_drop("item_box", center + self.random_offset(22), 1)

    def collect_drop(self, drop, player=None):
        if player is None:
            player = self.player
        if drop.kind == "xp":
            self.add_xp(drop.value, player)
        elif drop.kind == "ammo":
            max_res = self.max_ammo_reserve_for(player)
            if player.ammo_reserve >= max_res:
                if player.full_ammo_msg_timer <= 0:
                    self.add_floater(player.pos, "Cheio!", COLORS["muted"])
                    player.full_ammo_msg_timer = 2.0
                return False
                
            amount = int(drop.value)
            added = min(amount, max_res - player.ammo_reserve)
            player.ammo_reserve += added
            self.add_floater(player.pos, f"+{added} mun", COLORS["projectile"])
            if player.ammo_magazine <= 0 and player.reload_timer <= 0:
                self._start_reload_for(player)
        elif drop.kind == "coin":
            if self.multiplayer:
                self.shared_coins += 1
            else:
                player.coins += 1
            player.score += 25
            total_coins = self.shared_coins if self.multiplayer else player.coins
            if total_coins % 5 == 0:
                self.activate_random_coin_buff(player)
        elif drop.kind == "heal":
            player.health = min(player.max_health, player.health + drop.value)
            self.add_floater(player.pos, f"+{int(drop.value)}", COLORS["health"])
        elif drop.kind == "shield":
            player.activate_shield()
            self.message = "Escudo ativo: invulneravel, rapido e repelente."
        elif drop.kind == "item_box":
            self.grant_random_item(player.player_index)
        return True

    def grant_random_item(self, player_index=0):
        inv = self.get_inventory(player_index)
        # 0.5% chance of pre-defined relic drop
        if self.random.random() < 0.005:
            relic_source_key = self.random.choice(list(RELIC_DEFINITIONS.keys()))
            result, item = inv.add_relic(relic_source_key)
            if item is not None and result in ("new", "level_up"):
                name = item_display_name(item)
                self.message = f"RELIQUIA LENDARIA encontrada: {name}!"
                self.screen_shake = max(self.screen_shake, 14.0)
                return

        result, item = inv.add_random_item(self.random)
        if item is None:
            inv.points += 1
            self.message = "Sem itens disponiveis. +1 ponto de item."
            return

        name = item_display_name(item)
        if result == "new":
            self.message = f"Novo item: {name}."
        elif result == "level_up":
            self.message = f"{name} subiu para o nivel {item.level}."
        else:
            inv.points += 1
            self.message = f"{name} ja esta no maximo. +1 ponto de item."

    def _grant_random_reward(self, pos, strong=False, player_index=0):
        pos = Vector2(pos)
        player = self.get_player(player_index)
        inv = self.get_inventory(player_index)
        rewards = ["item", "coins", "xp", "heal", "shield", "points"]
        if strong:
            rewards.extend(["item", "coins", "points"])
        reward = self.random.choice(rewards)

        if reward == "item":
            self.grant_random_item(player_index)
        elif reward == "coins":
            amount = 10 if strong else 5
            for _ in range(amount):
                self.spawn_drop("coin", pos + self.random_offset(56), 1)
            self.message = "Recompensa: chuva de moedas."
        elif reward == "xp":
            amount = 150 if strong else 55
            self.add_xp(amount, player)
            self.message = "Recompensa: experiencia extra."
        elif reward == "heal":
            amount = player.max_health if strong else 38
            player.health = min(player.max_health, player.health + amount)
            self.add_floater(player.pos, f"+{int(amount)}", COLORS["health"])
            self.message = "Recompensa: cura imediata."
        elif reward == "shield":
            player.activate_shield()
            self.message = "Recompensa: escudo ativado."
        else:
            amount = 1600 if strong else 420
            player.score += amount
            inv.points += 2 if strong else 1
            self.message = "Recompensa: pontos e carga de itens."

    def _grant_miniboss_reward(self, pos, killer_index=0):
        killer = self.get_player(killer_index)
        inv = self.get_inventory(killer_index)
        killer.health = killer.max_health
        killer.ammo_reserve += 80
        killer.score += 5200 + int(self.time_alive * 35)
        inv.points += 3
        self._grant_bonus_levels(3, killer_index)
        for _ in range(14):
            self.spawn_drop("coin", Vector2(pos) + self.random_offset(88), 1)
        self._grant_random_reward(pos, strong=True, player_index=killer_index)
        self.message = "Mini-boss derrotado: vida cheia, +3 niveis e recompensa."

    def _grant_bonus_levels(self, amount, player_index=0):
        if self.multiplayer:
            major = False
            for _ in range(amount):
                self.shared_level += 1
                for p in self.players:
                    p.level = self.shared_level
                    self._apply_level_up_stats(p)
                for inv in self.inventories:
                    inv.points += 1
                if self.shared_level % 3 == 0:
                    major = True
                    for inv in self.inventories:
                        inv.points += 2
                    for p in self.players:
                        if not p.is_down:
                            self.spawn_drop("item_box", p.pos + self.random_offset(130), 1)
            self.shared_xp = 0
            self.shared_xp_to_next = int(40 + 25 * self.shared_level)
            self.level_up_pending = True
            self.upgrade_is_major = major
            if major:
                self.level_up_player_index = 0
                self.draft_active = False
                self.upgrade_choices = self.generate_upgrade_choices(True, 0)
            else:
                self.draft_active = True
                self.draft_turn_player = self.draft_first_picker
                if len(self.players) > 1 and self.players[self.draft_turn_player].is_down:
                    other_player = 1 - self.draft_turn_player
                    if not self.players[other_player].is_down:
                        self.draft_turn_player = other_player
                self.level_up_player_index = self.draft_turn_player
                self.upgrade_choices = self.generate_upgrade_choices(False, self.draft_turn_player)
                self.draft_first_picker = 1 - self.draft_first_picker
            return

        player = self.get_player(player_index)
        inv = self.get_inventory(player_index)
        major = False
        for _ in range(amount):
            player.level += 1
            self._apply_level_up_stats(player)
            inv.points += 1
            if player.level % 3 == 0:
                major = True
                inv.points += 2
                self.spawn_drop("item_box", player.pos + self.random_offset(130), 1)
        player.xp = 0
        player.xp_to_next = int(40 + 25 * player.level)
        self.level_up_pending = True
        self.level_up_player_index = player_index
        self.upgrade_is_major = major
        self.upgrade_choices = self.generate_upgrade_choices(major, player_index)

    def stat_shop_unlocked(self):
        return any(p.level >= STAT_SHOP_UNLOCK_LEVEL for p in self.players)

    def roll_stat_shop(self):
        if not self.stat_shop_unlocked():
            self.message = f"Loja de Status libera no nivel {STAT_SHOP_UNLOCK_LEVEL}."
            return False
        inv = self.get_inventory(0)  # shared stat shop uses P1 inventory points
        if inv.points < STAT_SHOP_ROLL_COST:
            self.message = f"Roletar custa {STAT_SHOP_ROLL_COST} ponto."
            return False
        inv.points -= STAT_SHOP_ROLL_COST
        self.stat_shop_offers = [self._generate_stat_offer() for _ in range(3)]
        self.message = "Loja de Status: escolha uma melhoria ou role uma carta novamente."
        return True

    def reroll_stat_shop_offer(self, index):
        if not self.stat_shop_unlocked():
            self.message = f"Loja de Status libera no nivel {STAT_SHOP_UNLOCK_LEVEL}."
            return False
        if index < 0 or index >= len(self.stat_shop_offers):
            self.message = "Oferta invalida."
            return False
        inv = self.get_inventory(0)
        if inv.points < STAT_SHOP_REROLL_COST:
            self.message = f"Jogar novamente custa {STAT_SHOP_REROLL_COST} ponto."
            return False
        inv.points -= STAT_SHOP_REROLL_COST
        previous_power = self.stat_shop_offers[index].get("power", 1)
        self.stat_shop_offers[index] = self._generate_stat_offer(self._reroll_stat_power(previous_power))
        self.message = "Oferta rolada novamente."
        return True

    def purchase_stat_shop_offer(self, index):
        if index < 0 or index >= len(self.stat_shop_offers):
            self.message = "Oferta invalida."
            return False
        offer = self.stat_shop_offers[index]
        cost = offer.get("cost", 0)
        inv = self.get_inventory(0)
        if inv.points < cost:
            self.message = f"Pontos insuficientes para comprar esta melhoria (custa {cost})."
            return False
        inv.points -= cost
        # Shared: apply to all players
        for effect in offer["effects"]:
            for player in self.players:
                self._apply_stat_shop_effect(effect["key"], effect["value"], player)
        self.stat_shop_offers = []
        self.message = f"Melhoria comprada: {offer['title']}."
        return True

    def _generate_stat_offer(self, power=None):
        if power is None:
            power = 2 if self.random.random() < 0.20 else 1
        power = max(1, min(5, int(power)))
        if power >= 4:
            effect_count = self.random.choices([1, 2, 3], weights=[20, 50, 30], k=1)[0]
        elif power >= 2:
            effect_count = self.random.choices([1, 2], weights=[55, 45], k=1)[0]
        else:
            effect_count = self.random.choices([1, 2], weights=[75, 25], k=1)[0]

        definitions = self.random.sample(STAT_SHOP_STATS, min(effect_count, len(STAT_SHOP_STATS)))
        effects = []
        total_cost = 0.0
        for definition in definitions:
            value = self._roll_stat_value(definition, power)
            effects.append({
                "key": definition["key"],
                "label": definition["label"],
                "value": value,
                "display": self._stat_effect_display(definition, value),
            })
            total_cost += value * definition["cost"]

        rarity = ["", "Comum", "Refinada", "Rara", "Epica", "Lendaria"][power]
        cost = max(2, math.ceil(total_cost + power * 0.8 + max(0, len(effects) - 1) * 1.2))
        return {
            "title": f"Melhoria {rarity}",
            "power": power,
            "cost": cost,
            "effects": effects,
        }

    def _reroll_stat_power(self, previous_power):
        roll = self.random.random()
        if roll < 0.55:
            gain = 0
        elif roll < 0.87:
            gain = 1
        elif roll < 0.98:
            gain = 2
        else:
            gain = 3
        return min(5, previous_power + gain)

    def _roll_stat_value(self, definition, power):
        scale = 1.0 + (power - 1) * 0.55
        raw = definition["base"] * scale * self.random.uniform(0.84, 1.22)
        if definition["kind"] == "integer":
            return max(1, int(round(raw)))
        if definition["kind"] == "flat":
            return max(1, int(round(raw)))
        if definition["kind"] == "decimal":
            return round(max(0.1, raw), 1)
        return round(max(0.005, raw), 3)

    def _stat_effect_display(self, definition, value):
        if definition["kind"] == "percent":
            return f"+{int(round(value * 100))}% {definition['unit']}"
        if definition["kind"] == "decimal":
            return f"+{value:.1f} {definition['unit']}"
        return f"+{int(value)} {definition['unit']}"

    def _apply_stat_shop_effect(self, key, value, player=None):
        if player is None:
            player = self.player
        if key == "max_health":
            player.max_health += value
            player.health = min(player.max_health, player.health + value)
        elif key == "damage":
            player.damage_bonus += value
        elif key == "speed":
            player.speed_bonus += value
        elif key == "attack_rate":
            player.attack_rate_bonus += value
        elif key == "sword_range":
            player.sword_range_bonus += value
        elif key == "special_gain":
            player.special_gain_bonus += value
        elif key == "vampirism":
            player.vampirism += value
        elif key == "magazine":
            player.magazine_bonus += int(value)
            player.ammo_magazine = min(self.magazine_capacity(), player.ammo_magazine + int(value))
        elif key == "reload_speed":
            player.reload_speed_bonus += value

    def toggle_inventory_item(self, key):
        inv = self.get_inventory(self.menu_player_index)
        success, message = inv.toggle_active(key)
        self.message = message
        return success

    def upgrade_inventory_item(self, key):
        inv = self.get_inventory(self.menu_player_index)
        success, message = inv.upgrade_with_point(key)
        self.message = message
        return success

    def buy_shop_item(self, item_key):
        inv = self.get_inventory(self.menu_player_index)
        cost = 15
        if inv.points < cost:
            self.message = f"Pontos insuficientes para comprar (custa {cost})."
            return False
            
        inv.points -= cost
        status, item = inv.add_item(item_key)
        self.message = f"Item {item.key} adquirido no Mercado Negro!"
        return True

    def skill_upgrade_cost(self, key):
        player = self.get_player(self.menu_player_index)
        data = CHARACTERS[player.char_class]["passives"].get(key, {})
        level = player.passives.get(key, 0)
        is_special = data.get("category") == "Especial"
        if level == 0:
            return SPECIAL_SKILL_UNLOCK_COST if is_special else SKILL_UNLOCK_COST
        return SPECIAL_SKILL_UPGRADE_COST if is_special else SKILL_UPGRADE_COST

    def upgrade_skill(self, key):
        player = self.get_player(self.menu_player_index)
        inv = self.get_inventory(self.menu_player_index)
        if key not in player.passives:
            self.message = "Skill nao encontrada."
            return False
        if player.passives[key] >= 10:
            self.message = "Skill ja esta no nivel maximo."
            return False
        cost = self.skill_upgrade_cost(key)
        if inv.points < cost:
            self.message = f"Pontos insuficientes para upar skill (custa {cost})."
            return False
        inv.points -= cost
        player.passives[key] += 1
        data = CHARACTERS[player.char_class]["passives"][key]
        state = "desbloqueada" if player.passives[key] == 1 else "aprimorada"
        self.message = f"Skill {state}: {data['title']}."
        return True

    def mark_or_fuse_item(self, key):
        inv = self.get_inventory(self.menu_player_index)
        success, message = inv.mark_for_fusion(key)
        self.message = message
        return success

    def fusion_preview(self):
        inv = self.get_inventory(self.menu_player_index)
        success, preview, message = inv.preview_marked_fusion()
        return success, preview, message

    def has_pending_fusion(self):
        success, _, _ = self.fusion_preview()
        return success

    def confirm_pending_fusion(self):
        inv = self.get_inventory(self.menu_player_index)
        if inv.points < FUSION_COST:
            self.message = f"Pontos insuficientes para fusao (custa {FUSION_COST})."
            return False
        success, message = inv.fuse_marked_items()
        if success:
            inv.points -= FUSION_COST
        self.message = message
        return success

    def cancel_pending_fusion(self):
        inv = self.get_inventory(self.menu_player_index)
        inv.clear_fusion_marks()
        self.message = "Fusao cancelada."

    def _apply_level_up_stats(self, player):
        for stat in STAT_SHOP_STATS:
            val = 0.01 if stat["kind"] == "percent" else 1.0
            self._apply_stat_shop_effect(stat["key"], val, player)

    def add_xp(self, amount, player=None):
        if player is None:
            player = self.player
        
        # XP Compartilhado no Multiplayer
        if self.multiplayer:
            self.shared_xp += amount
            for p in self.players:
                p.score += int(amount * 3) # Score dividido
            
            while self.shared_xp >= self.shared_xp_to_next:
                self.shared_xp -= self.shared_xp_to_next
                self.shared_level += 1
                for p in self.players:
                    p.level = self.shared_level # Sincroniza níveis
                    self._apply_level_up_stats(p)
                
                # Pontos de inventário ainda são individuais para cada nível
                for inv in self.inventories:
                    inv.points += 1
                
                self.shared_xp_to_next = int(40 + 25 * self.shared_level)
                self.level_up_pending = True
                
                # Lógica de Draft
                major = self.shared_level % 3 == 0
                self.upgrade_is_major = major
                
                if major:
                    # Recompensas do nível especial para o time
                    for inv in self.inventories:
                        inv.points += 2
                    for p in self.players:
                        if not p.is_down:
                            self.spawn_drop("item_box", p.pos + self.random_offset(120), 1)
                    
                    # Upgrades grandes são individuais (um após o outro)
                    self.level_up_player_index = 0
                    self.draft_active = False
                    self.upgrade_choices = self.generate_upgrade_choices(True, self.level_up_player_index)
                else:
                    # Upgrades comuns são via DRAFT
                    self.draft_active = True
                    self.draft_turn_player = self.draft_first_picker
                    
                    # Se o jogador da vez estiver morto e o outro não, passa a vez pro vivo
                    if len(self.players) > 1 and self.players[self.draft_turn_player].is_down:
                        other_player = 1 - self.draft_turn_player
                        if not self.players[other_player].is_down:
                            self.draft_turn_player = other_player
                            
                    self.level_up_player_index = self.draft_turn_player
                    self.upgrade_choices = self.generate_upgrade_choices(False, self.draft_turn_player)
                    # O draft alterna quem começa a cada nível
                    self.draft_first_picker = 1 - self.draft_first_picker
                
                self.message = "DRAFT: escolha um upgrade!" if self.draft_active else "Evolução de Classe!"
                break
            return

        pi = player.player_index
        inv = self.get_inventory(pi)
        player.xp += amount
        player.score += int(amount * 6)
        while player.xp >= player.xp_to_next:
            player.xp -= player.xp_to_next
            player.level += 1
            self._apply_level_up_stats(player)
            inv.points += 1
            player.xp_to_next = int(40 + 25 * player.level)
            self.level_up_pending = True
            self.level_up_player_index = pi
            self.upgrade_is_major = player.level % 3 == 0
            if self.upgrade_is_major:
                inv.points += 2
                self.spawn_drop("item_box", player.pos + self.random_offset(120), 1)
            self.upgrade_choices = self.generate_upgrade_choices(self.upgrade_is_major, pi)
            self.message = "Escolha uma melhoria grande." if self.upgrade_is_major else "Escolha um upgrade."
            break

    def activate_random_coin_buff(self, player=None):
        if player is None:
            player = self.player
        buff = self.random.choice(["freeze", "speed", "power"])
        player.activate_buff(buff)
        labels = {
            "freeze": "Tiro congelante ativado.",
            "speed": "Aumento de velocidade ativado.",
            "power": "Dano energizado ativado.",
        }
        self.message = labels[buff]

    def generate_upgrade_choices(self, major=False, player_index=0):
        player = self.get_player(player_index)
        if major:
            passives = player.passives
            available = [k for k, v in passives.items() if v < 10]
            if not available:
                keys = list(OMNI_UPGRADES.keys())
                return self.random.sample(keys, min(3, len(keys)))
            return self.random.sample(available, min(3, len(available)))
        else:
            keys = list(UPGRADES.keys())
            return self.random.sample(keys, 3)

    def apply_upgrade(self, upgrade_key, player_index=0):
        player = self.get_player(player_index)
        if upgrade_key == "speed":
            player.speed_bonus += 0.08
        elif upgrade_key == "damage":
            player.damage_bonus += 0.13
        elif upgrade_key == "max_health":
            player.max_health += 22
            player.health = min(player.max_health, player.health + 42)
        elif upgrade_key == "fire_rate":
            player.attack_rate_bonus += 0.11
        elif upgrade_key == "sword_range":
            player.sword_range_bonus += 0.10
        elif upgrade_key == "special_gain":
            player.special_gain_bonus += 0.16
        elif upgrade_key == "vampirism":
            player.vampirism += 2.5
        elif upgrade_key in player.passives:
            player.passives[upgrade_key] += 1
        elif upgrade_key == "omni_power":
            player.damage_bonus += 0.25
            player.attack_rate_bonus += 0.25
            player.sword_range_bonus += 0.25
        elif upgrade_key == "omni_survival":
            player.max_health += 45
            player.health += 45
            player.speed_bonus += 0.45
            player.vampirism += 5.0
        elif upgrade_key == "omni_special":
            player.special_gain_bonus += 1.0
            player.sword_range_bonus += 0.35
            player.attack_rate_bonus += 0.15

        data = UPGRADES.get(upgrade_key)
        if not data:
            data = OMNI_UPGRADES.get(upgrade_key)
        if not data:
            data = CHARACTERS[player.char_class]["passives"].get(upgrade_key)

        title = data["title"] if data else upgrade_key
        self.message = f"J{player_index + 1} escolheu: {title}"

        # Lógica de Draft Multiplayer
        if self.multiplayer and self.draft_active:
            if player_index == self.draft_turn_player: # Jogador da vez
                # Remove a escolha da lista
                if upgrade_key in self.upgrade_choices:
                    self.upgrade_choices.remove(upgrade_key)
                
                # Se ainda houver um segundo turno no draft
                if len(self.upgrade_choices) > 1: # Tinha 3, sobrou 2
                    self.draft_turn_player = 1 - self.draft_turn_player
                    self.level_up_player_index = self.draft_turn_player
                    # Mantém o level_up_pending = True para o próximo jogador
                    return
                else:
                    # Fim do draft: limpa tudo
                    self.draft_active = False
                    self.level_up_pending = False
                    self.upgrade_choices = []
            return

        # Lógica de Upgrades Grandes Multiplayer (sequencial)
        if self.multiplayer and self.upgrade_is_major and player_index == 0:
            # P1 terminou, agora vez do P2
            self.level_up_player_index = 1
            self.upgrade_choices = self.generate_upgrade_choices(True, 1)
            return

        self.level_up_pending = False
        self.upgrade_is_major = False
        self.upgrade_choices = []

    def spawn_drop(self, kind, pos, value=1):
        radius = 8
        if kind == "xp":
            radius = 7
        elif kind == "ammo":
            radius = 8
        elif kind == "heal":
            radius = 10
        elif kind == "shield":
            radius = 12
        elif kind == "item_box":
            radius = 13
        self.drops.append(Drop(pos=Vector2(pos), kind=kind, value=value, radius=radius))

    def random_offset(self, amount):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(0, amount)
        return Vector2(math.cos(angle), math.sin(angle)) * distance

    def add_floater(self, pos, text, color):
        self.floaters.append(
            {
                "pos": Vector2(pos),
                "text": text,
                "color": color,
                "age": 0.0,
                "duration": 0.55,
            }
        )

    # ------------------------------------------------------------------ #
    # MINIBOSS SUMMON                                                       #
    # ------------------------------------------------------------------ #

    def _start_miniboss_summon(self, enemy):
        enemy.action = "summon"
        enemy.action_timer = MINIBOSS_SUMMON_DURATION
        enemy.summon_cooldown = self.random.uniform(MINIBOSS_SUMMON_COOLDOWN_MIN, MINIBOSS_SUMMON_COOLDOWN_MAX)
        count = self.random.randint(MINIBOSS_SUMMON_COUNT_MIN, MINIBOSS_SUMMON_COUNT_MAX)
        spawned = 0
        for _ in range(count * 4):
            if spawned >= count:
                break
            angle = self.random.random() * math.tau
            dist = self.random.uniform(60, 130)
            pos = enemy.pos + Vector2(math.cos(angle), math.sin(angle)) * dist
            if not self.world.circle_hits_wall(pos, 11):
                self._spawn_minion(pos)
                spawned += 1
        self.item_events.append({
            "type": "summon_pulse",
            "pos": Vector2(enemy.pos),
            "radius": 140,
            "age": 0.0,
            "duration": MINIBOSS_SUMMON_DURATION,
        })
        self.message = "Mini-boss invocou reforcos!"

    def _spawn_minion(self, pos):
        data = ENEMY_TYPES["minion"]
        minion = Enemy(
            id=self.enemy_id,
            pos=Vector2(pos),
            kind="minion",
            radius=data["radius"],
            speed=data["speed"] * self.director_speed,
            max_health=data["health"] * self.director_health,
            health=data["health"] * self.director_health,
            damage=data["damage"] * self.director_damage,
            xp_value=data["xp"],
            color=data["color"],
            special_value=data["special"],
            coin_chance=data["coin_chance"],
        )
        self.enemy_id += 1
        self.enemies.append(minion)

    # ------------------------------------------------------------------ #
    # GAME DIRECTOR                                                         #
    # ------------------------------------------------------------------ #

    def _update_director(self, dt):
        self.director_tick += dt
        if self.director_tick >= 60.0:
            self.director_tick -= 60.0
            self.director_minute += 1
            self.director_health = 1.0 + min(1.0, self.director_minute * 0.05)
            self.director_damage = 1.0 + min(0.40, self.director_minute * 0.02)
            self.director_speed = 1.0 + min(0.30, self.director_minute * 0.02)
            bonus_enemies = min(45, self.director_minute * 5)
            self.message = (
                f"Minuto {self.director_minute}: inimigos mais fortes!"
            )
            # Dynamically raise the enemy cap
            global MAX_ENEMIES
            MAX_ENEMIES = 95 + bonus_enemies

    # ------------------------------------------------------------------ #
    # QUEST SYSTEM                                                          #
    # ------------------------------------------------------------------ #

    def _update_quests(self, dt):
        if self.quest is None:
            self.next_quest_timer -= dt
            if self.next_quest_timer <= 0:
                self._start_quest()
            return

        q = self.quest
        gt = q["goal_type"]
        q["timer"] -= dt

        # Accumulate time-based progress
        if gt == "survive_melee":
            self.quest_progress += dt
        elif gt == "stand_fire" and self._player_in_fire:
            self.quest_progress += dt
        elif gt == "survive_no_dash":
            self.quest_progress += dt

        # Check completion
        if self.quest_progress >= q["target"]:
            self._grant_quest_reward()
            return

        # Check timeout
        if q["timer"] <= 0:
            self._fail_quest()

    def _start_quest(self):
        chosen = self.random.choice(QUEST_DEFINITIONS)
        self.quest = dict(chosen)
        self.quest["timer"] = chosen["time_limit"]
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(90.0, 150.0)
        self.message = f"Nova missao: {chosen['description']}"

    def _fail_quest(self):
        desc = self.quest["description"] if self.quest else ""
        self.quest = None
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(60.0, 100.0)
        self.message = f"Missao falhou: {desc}"

    def _grant_quest_reward(self):
        desc = self.quest["description"] if self.quest else ""
        self.quest = None
        self.quest_progress = 0.0
        self.next_quest_timer = self.random.uniform(90.0, 150.0)
        self._grant_bonus_levels(3)
        self.message = f"Missao concluida: {desc} | +3 niveis!"
        self.screen_shake = max(self.screen_shake, 10.0)

    # ------------------------------------------------------------------ #
    # RELIC AURA                                                            #
    # ------------------------------------------------------------------ #

    def _update_relic_aura(self, dt):
        self.relic_aura_angle = (self.relic_aura_angle + dt * 1.8) % math.tau
        aura_radius = 82
        for player in self.alive_players():
            inv = self.get_inventory(player.player_index)
            if not any(item.is_relic for item in inv.active_items()):
                continue
            for enemy in list(self.enemies):
                if enemy.pos.distance_to(player.pos) <= aura_radius + enemy.radius:
                    self.damage_enemy(enemy, 8.0 * dt, source="relic", killer_index=player.player_index)

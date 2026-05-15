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






from .managers.combat_manager import CombatManager
from .managers.enemy_manager import EnemyManager
from .managers.item_manager import ItemManager
from .managers.quest_manager import QuestManager

class GameLogic(CombatManager, EnemyManager, ItemManager, QuestManager):
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







    def _update_world_timers(self, dt):
        for chunk in self.world.chunks.values():
            for item in chunk["destructibles"]:
                item.hit_flash = max(0, item.hit_flash - dt)





















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




    def _nearest_enemy(self, pos, radius):
        best = None
        best_distance = radius * radius
        for enemy in self.enemies:
            distance = enemy.pos.distance_squared_to(pos)
            if distance < best_distance:
                best = enemy
                best_distance = distance
        return best



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






































    def random_offset(self, amount):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(0, amount)
        return Vector2(math.cos(angle), math.sin(angle)) * distance


    # ------------------------------------------------------------------ #
    # MINIBOSS SUMMON                                                       #
    # ------------------------------------------------------------------ #



    # ------------------------------------------------------------------ #
    # GAME DIRECTOR                                                         #
    # ------------------------------------------------------------------ #


    # ------------------------------------------------------------------ #
    # QUEST SYSTEM                                                          #
    # ------------------------------------------------------------------ #





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

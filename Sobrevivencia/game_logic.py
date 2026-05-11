import math
import random

from pygame.math import Vector2

if __package__:
    from .constants import *
    from .entities import Drop, Enemy, Player, Projectile, Slash
    from .world import World, circle_rect_overlap
else:
    from constants import *
    from entities import Drop, Enemy, Player, Projectile, Slash
    from world import World, circle_rect_overlap


class GameLogic:
    def __init__(self):
        self.world = World()
        self.player = Player()
        self.camera = Vector2(
            self.player.pos.x - SCREEN_WIDTH * 0.5,
            self.player.pos.y - SCREEN_HEIGHT * 0.5,
        )
        self.enemies = []
        self.projectiles = []
        self.slashes = []
        self.drops = []
        self.floaters = []
        self.upgrade_choices = []
        self.level_up_pending = False
        self.game_over = False
        self.time_alive = 0.0
        self.spawn_timer = 0.2
        self.enemy_id = 1
        self.screen_shake = 0.0
        self.special_blast_timer = 0.0
        self.message = "Sobreviva o maximo que puder."
        self.random = random.Random()
        self.world.ensure_area(self.player.pos, 2)

    def restart(self):
        self.__init__()

    def toggle_mode(self):
        self.player.mode = "sword" if self.player.mode == "projectile" else "projectile"
        self.message = "Modo espada" if self.player.mode == "sword" else "Modo projetil"

    def try_dash(self, aim_world):
        player = self.player
        if player.dash_cooldown > 0 or player.dash_timer > 0 or self.game_over:
            return

        direction = Vector2(player.last_move_dir)
        if direction.length_squared() < 0.01:
            direction = Vector2(aim_world) - player.pos
        if direction.length_squared() < 0.01:
            direction = Vector2(1, 0)
        player.dash_dir = direction.normalize()
        player.dash_timer = DASH_DURATION
        player.dash_cooldown = DASH_COOLDOWN
        player.invulnerable_timer = max(player.invulnerable_timer, DASH_DURATION + 0.08)

    def try_special(self):
        player = self.player
        if player.special < SPECIAL_MAX or self.game_over:
            return

        player.special = 0
        self.special_blast_timer = 0.35
        self.screen_shake = max(self.screen_shake, 16.0)
        self.message = "Explosao radial liberada!"

        for enemy in list(self.enemies):
            distance = enemy.pos.distance_to(player.pos)
            if distance <= SPECIAL_RADIUS:
                direction = enemy.pos - player.pos
                if direction.length_squared() > 0:
                    enemy.knockback += direction.normalize() * 520
                self.damage_enemy(enemy, SPECIAL_DAMAGE, source="special")

        for item in list(self.world.nearby_destructibles(player.pos.x, player.pos.y, SPECIAL_RADIUS * 0.75)):
            if item.rect.center.distance_to(player.pos) <= SPECIAL_RADIUS * 0.75:
                self.destroy_destructible(item)

    def update(self, dt, move_vector, aim_world):
        if self.game_over:
            return

        dt = min(dt, 0.05)
        self.time_alive += dt
        self.world.ensure_area(self.player.pos, 2)
        self._update_player_timers(dt)
        self._move_player(dt, move_vector, aim_world)
        self._auto_attack(dt, aim_world)
        self._spawn_enemies(dt)
        self._update_world_timers(dt)
        self._update_projectiles(dt)
        self._update_slashes(dt)
        self._update_enemies(dt)
        self._update_drops(dt)
        self._update_floaters(dt)
        self._update_camera(dt)
        self.screen_shake = max(0, self.screen_shake - SCREEN_SHAKE_DECAY * 20 * dt)
        self.special_blast_timer = max(0, self.special_blast_timer - dt)

        if self.player.health <= 0:
            self.player.health = 0
            self.game_over = True

    def _update_player_timers(self, dt):
        player = self.player
        player.shoot_timer = max(0, player.shoot_timer - dt)
        player.sword_timer = max(0, player.sword_timer - dt)
        player.dash_cooldown = max(0, player.dash_cooldown - dt)
        player.dash_timer = max(0, player.dash_timer - dt)
        player.invulnerable_timer = max(0, player.invulnerable_timer - dt)
        player.shield_timer = max(0, player.shield_timer - dt)

        expired = []
        for name in player.buffs:
            player.buffs[name] = max(0, player.buffs[name] - dt)
            if player.buffs[name] <= 0:
                expired.append(name)
        for name in expired:
            del player.buffs[name]

    def _move_player(self, dt, move_vector, aim_world):
        player = self.player
        if move_vector.length_squared() > 0:
            move_vector = move_vector.normalize()
            player.last_move_dir = Vector2(move_vector)

        if player.dash_timer > 0:
            delta = player.dash_dir * DASH_SPEED * dt
        else:
            terrain_speed = self.world.speed_multiplier_at(player.pos.x, player.pos.y)
            speed = player.base_speed * player.speed_multiplier() * terrain_speed
            delta = move_vector * speed * dt

        player.pos = self.world.move_circle(player.pos, player.radius, delta)
        if player.shield_timer > 0:
            self._repel_enemies(dt)

    def _auto_attack(self, dt, aim_world):
        player = self.player
        direction = Vector2(aim_world) - player.pos
        if direction.length_squared() < 0.01:
            direction = Vector2(1, 0)
        direction = direction.normalize()

        if player.mode == "projectile":
            cooldown = PROJECTILE_COOLDOWN / player.attack_rate_multiplier()
            if player.shoot_timer <= 0 and len(self.projectiles) < MAX_PROJECTILES:
                self.projectiles.append(
                    Projectile(
                        pos=Vector2(player.pos) + direction * (player.radius + 8),
                        vel=direction * PROJECTILE_SPEED,
                        damage=player.projectile_damage(),
                        freeze=player.buffs.get("freeze", 0) > 0,
                    )
                )
                player.shoot_timer = cooldown
        else:
            cooldown = SWORD_COOLDOWN / player.attack_rate_multiplier()
            if player.sword_timer <= 0:
                self.slashes.append(
                    Slash(
                        origin=Vector2(player.pos),
                        direction=direction,
                        radius=player.sword_radius(),
                        damage=player.sword_damage(),
                    )
                )
                player.sword_timer = cooldown

    def _spawn_enemies(self, dt):
        if len(self.enemies) >= MAX_ENEMIES:
            return

        difficulty = 1.0 + self.time_alive / 85.0 + (self.player.level - 1) * 0.09
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

    def _spawn_one_enemy(self, difficulty):
        angle = self.random.random() * math.tau
        distance = self.random.uniform(SPAWN_DISTANCE_MIN, SPAWN_DISTANCE_MAX)
        pos = self.player.pos + Vector2(math.cos(angle), math.sin(angle)) * distance

        roll = self.random.random()
        if self.time_alive > 75 and roll < 0.16:
            kind = "brute"
        elif self.time_alive > 25 and roll < 0.42:
            kind = "runner"
        else:
            kind = "basic"

        data = ENEMY_TYPES[kind]
        enemy = Enemy(
            id=self.enemy_id,
            pos=pos,
            kind=kind,
            radius=data["radius"],
            speed=data["speed"] * min(1.75, 1.0 + (difficulty - 1.0) * 0.08),
            max_health=data["health"] * min(2.6, 1.0 + (difficulty - 1.0) * 0.18),
            health=data["health"] * min(2.6, 1.0 + (difficulty - 1.0) * 0.18),
            damage=data["damage"],
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
            projectile.life -= dt
            projectile.pos += projectile.vel * dt
            if projectile.life <= 0 or self.world.circle_hits_wall(projectile.pos, projectile.radius):
                continue

            hit = False
            for item in self.world.nearby_destructibles(projectile.pos.x, projectile.pos.y, projectile.radius + 24):
                if circle_rect_overlap(projectile.pos.x, projectile.pos.y, projectile.radius, item.rect):
                    self.damage_destructible(item, projectile.damage)
                    hit = True
                    break
            if hit:
                continue

            for enemy in list(self.enemies):
                if projectile.pos.distance_squared_to(enemy.pos) <= (projectile.radius + enemy.radius) ** 2:
                    if projectile.freeze:
                        enemy.frozen_timer = max(enemy.frozen_timer, FREEZE_DURATION)
                    self.damage_enemy(enemy, projectile.damage, source="projectile")
                    hit = True
                    break

            if not hit:
                alive.append(projectile)

        self.projectiles = alive

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
        origin = self.player.pos
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
                enemy.knockback += to_enemy.normalize() * 330
                self.damage_enemy(enemy, slash.damage, source="sword")

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

    def _update_enemies(self, dt):
        player = self.player
        alive = []
        for enemy in list(self.enemies):
            enemy.frozen_timer = max(0, enemy.frozen_timer - dt)
            enemy.hit_flash = max(0, enemy.hit_flash - dt)

            to_player = player.pos - enemy.pos
            if to_player.length_squared() > 0:
                direction = to_player.normalize()
            else:
                direction = Vector2(1, 0)

            slow = 0.28 if enemy.frozen_timer > 0 else 1.0
            velocity = direction * enemy.speed * slow
            if enemy.knockback.length_squared() > 1:
                velocity += enemy.knockback
                enemy.knockback *= max(0, 1.0 - 7.0 * dt)

            enemy.pos = self.world.move_circle(enemy.pos, enemy.radius, velocity * dt, include_destructibles=False)

            distance_sq = enemy.pos.distance_squared_to(player.pos)
            contact_radius = enemy.radius + player.radius
            if distance_sq <= contact_radius * contact_radius:
                if player.shield_timer > 0:
                    push = enemy.pos - player.pos
                    if push.length_squared() > 0:
                        enemy.knockback += push.normalize() * 460
                    self.damage_enemy(enemy, 22 * dt, source="shield")
                elif player.invulnerable_timer <= 0:
                    player.health -= enemy.damage * dt

            if enemy.health > 0:
                alive.append(enemy)
        self.enemies = alive

    def _repel_enemies(self, dt):
        for enemy in self.enemies:
            distance = enemy.pos.distance_to(self.player.pos)
            if 0 < distance < 130:
                direction = (enemy.pos - self.player.pos).normalize()
                enemy.pos += direction * 280 * dt
                enemy.knockback += direction * 180 * dt

    def _update_drops(self, dt):
        player = self.player
        alive = []
        for drop in self.drops:
            drop.ttl -= dt
            drop.bob += dt * 6
            to_player = player.pos - drop.pos
            distance = to_player.length()

            magnet_radius = XP_MAGNET_RADIUS if drop.kind == "xp" else XP_MAGNET_RADIUS * 0.72
            if 0 < distance < magnet_radius:
                drop.pos += to_player.normalize() * DROP_ATTRACT_SPEED * dt

            if distance <= DROP_PICKUP_RADIUS + drop.radius:
                self.collect_drop(drop)
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
        target = Vector2(
            self.player.pos.x - SCREEN_WIDTH * 0.5,
            self.player.pos.y - SCREEN_HEIGHT * 0.5,
        )
        self.camera += (target - self.camera) * min(1.0, CAMERA_SMOOTHING * dt)

    def damage_enemy(self, enemy, amount, source="hit"):
        enemy.health -= amount
        enemy.hit_flash = 0.08
        if amount >= 1:
            self.add_floater(enemy.pos, str(int(amount)), "#FDE68A" if source == "sword" else "#BAE6FD")
        if enemy.health <= 0 and enemy in self.enemies:
            self.kill_enemy(enemy)

    def kill_enemy(self, enemy):
        self.enemies.remove(enemy)
        self.player.kills += 1
        self.player.score += int(enemy.xp_value * 10 + self.time_alive)
        self.player.add_special(enemy.special_value)
        self.spawn_drop("xp", enemy.pos, enemy.xp_value)
        if self.random.random() < enemy.coin_chance:
            self.spawn_drop("coin", enemy.pos + self.random_offset(18), 1)
        if self.random.random() < 0.035:
            self.spawn_drop("heal", enemy.pos + self.random_offset(22), 22)
        if self.random.random() < 0.018:
            self.spawn_drop("shield", enemy.pos + self.random_offset(22), 1)

    def damage_destructible(self, item, amount):
        item.hp -= amount
        item.hit_flash = 0.08
        if item.hp <= 0:
            self.destroy_destructible(item)

    def destroy_destructible(self, item):
        center = item.rect.center
        self.world.remove_destructible(item)
        self.spawn_drop("coin", center + self.random_offset(18), 1)
        roll = self.random.random()
        if roll < 0.18:
            self.spawn_drop("heal", center + self.random_offset(22), 20)
        elif roll < 0.28:
            self.spawn_drop("shield", center + self.random_offset(22), 1)
        elif roll < 0.45:
            self.spawn_drop("xp", center + self.random_offset(22), 8)

    def collect_drop(self, drop):
        player = self.player
        if drop.kind == "xp":
            self.add_xp(drop.value)
        elif drop.kind == "coin":
            player.coins += 1
            player.score += 25
            if player.coins % 5 == 0:
                self.activate_random_coin_buff()
        elif drop.kind == "heal":
            player.health = min(player.max_health, player.health + drop.value)
            self.add_floater(player.pos, f"+{int(drop.value)}", COLORS["health"])
        elif drop.kind == "shield":
            player.activate_shield()
            self.message = "Escudo ativo: invulneravel, rapido e repelente."

    def add_xp(self, amount):
        player = self.player
        player.xp += amount
        player.score += int(amount * 6)
        while player.xp >= player.xp_to_next:
            player.xp -= player.xp_to_next
            player.level += 1
            player.xp_to_next = int(player.xp_to_next * 1.26 + 22)
            self.level_up_pending = True
            self.upgrade_choices = self.generate_upgrade_choices()
            self.message = "Escolha um upgrade."
            break

    def activate_random_coin_buff(self):
        buff = self.random.choice(["freeze", "speed", "power"])
        self.player.activate_buff(buff)
        labels = {
            "freeze": "Tiro congelante ativado.",
            "speed": "Aumento de velocidade ativado.",
            "power": "Dano energizado ativado.",
        }
        self.message = labels[buff]

    def generate_upgrade_choices(self):
        keys = list(UPGRADES.keys())
        return self.random.sample(keys, 3)

    def apply_upgrade(self, upgrade_key):
        player = self.player
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

        self.level_up_pending = False
        self.upgrade_choices = []
        self.message = f"Upgrade aplicado: {UPGRADES[upgrade_key]['title']}"

    def spawn_drop(self, kind, pos, value=1):
        radius = 8
        if kind == "xp":
            radius = 7
        elif kind == "heal":
            radius = 10
        elif kind == "shield":
            radius = 12
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

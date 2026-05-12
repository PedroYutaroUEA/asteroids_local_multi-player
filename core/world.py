import math
from random import uniform
from typing import Dict, List
import pygame as pg

from core import config as C
from core.collisions import CollisionManager
from core.commands import PlayerCommand
from core.entities import Asteroid, Ship, UFO
from core.utils import Vec, rand_edge_pos


class World:
    def __init__(self, player_ids: List[C.PlayerId]) -> None:
        self.active_player_ids = player_ids  # Armazena para facilitar o reset
        self.tethers: list[tuple[C.PlayerId, C.PlayerId]] = []
        self.game_over = False
        self.ufo_timer = float(C.UFO_SPAWN_EVERY)
        self.wave_cool = float(C.WAVE_DELAY)

        self._init_state()

    def _init_state(self) -> None:
        """Inicializa (ou reinicia) todo o estado mutável da simulação."""
        self.ships: Dict[C.PlayerId, Ship] = {}
        self.scores: Dict[C.PlayerId, int] = {pid: 0 for pid in self.active_player_ids}
        self.lives: Dict[C.PlayerId, int] = {
            pid: C.START_LIVES for pid in self.active_player_ids
        }
        self.power_use_count = 0
        self.shots_fired = 0

        self.bullets = pg.sprite.Group()
        self.time_bombs = pg.sprite.Group()
        self.asteroids = pg.sprite.Group()
        self.ufos = pg.sprite.Group()
        self.all_sprites = pg.sprite.Group()

        self.wave = 0
        self.wave_cool = float(C.WAVE_DELAY)
        self.ufo_timer = float(C.UFO_SPAWN_EVERY)
        self.events: list[str] = []
        self._collision_mgr = CollisionManager()
        self.game_over = False

        for pid in self.active_player_ids:
            self.spawn_player(pid)

    def reset(self) -> None:
        """Reinicia o mundo in-place, mantendo os mesmos jogadores do lobby."""
        self._init_state()

    def spawn_player(self, player_id: C.PlayerId) -> None:
        # Posições de spawn distintas para evitar colisões no nascimento
        offsets = {1: (-100, -100), 2: (100, -100), 3: (-100, 100), 4: (100, 100)}
        ox, oy = offsets.get(player_id, (0, 0))
        pos = Vec(C.WIDTH / 2 + ox, C.HEIGHT / 2 + oy)

        ship = Ship(player_id, pos)
        ship.invuln = float(C.SAFE_SPAWN_TIME)
        self.ships[player_id] = ship
        self.all_sprites.add(ship)

    def update(self, dt: float, commands: Dict[C.PlayerId, PlayerCommand]) -> None:
        if self.game_over:
            return
        self.events.clear()

        self._apply_players_commands(dt, commands)
        self._update_tethers(dt, commands)
        self.all_sprites.update(dt)
        self._update_ufos(dt)
        self._update_timers(dt)
        self._handle_collisions()
        self._maybe_start_next_wave(dt)

    def _apply_players_commands(
        self, dt: float, commands: Dict[C.PlayerId, PlayerCommand]
    ):
        for pid, cmd in commands.items():
            ship = self.ships.get(pid)
            if not ship or not ship.alive():
                continue

            # Lógica de poderes e contagem
            if cmd.hyperspace:
                ship.hyperspace()
                self.power_use_count += 1
                self.scores[pid] = max(0, self.scores[pid] - C.HYPERSPACE_COST)

            ship.apply_command(cmd, dt)

            if cmd.shoot:
                bullet = ship.try_fire(self.bullets)
                if bullet:
                    self.bullets.add(bullet)
                    self.all_sprites.add(bullet)
                    self.shots_fired += 1
                    self.events.append("player_shoot")

            if cmd.time_bomb:
                time_bomb = ship.try_time_bomb(self.time_bombs)
                if time_bomb:
                    self.time_bombs.add(time_bomb)
                    self.all_sprites.add(time_bomb)
                    self.events.append("player_time_bomb")

    def _update_tethers(
        self, dt: float, commands: Dict[C.PlayerId, PlayerCommand]
    ) -> None:
        pressing_special = []
        for pid, cmd in commands.items():
            ship = self.ships.get(pid)
            if ship and ship.alive() and cmd.special:
                pressing_special.append(pid)

        for i, p1 in enumerate(pressing_special):
            for j in range(i + 1, len(pressing_special)):
                p2 = pressing_special[j]
                already_tethered = any(
                    (t[0] == p1 and t[1] == p2) or (t[0] == p2 and t[1] == p1)
                    for t in self.tethers
                )
                if not already_tethered:
                    if (
                        self.ships[p1].pos - self.ships[p2].pos
                    ).length() <= C.TETHER_MAX_DIST:
                        self.tethers.append((p1, p2))

        active_tethers = []
        for p1, p2 in self.tethers:
            s1, s2 = self.ships.get(p1), self.ships.get(p2)
            if s1 and s2 and s1.alive() and s2.alive():
                cmd1, cmd2 = commands.get(p1), commands.get(p2)
                if cmd1 and cmd2 and cmd1.special and cmd2.special:
                    if (s1.pos - s2.pos).length() <= C.TETHER_MAX_DIST:
                        active_tethers.append((p1, p2))
                        # cost is applied as an integer chunk every so often or directly subtracting and flooring
                        # Note: float cost accumulation isn't supported without adding float fields to scores.
                        # Let's subtract a probabilistic cost or keep score as integer.
                        if uniform(0, 1) < dt:
                            cost = int(C.TETHER_SCORE_COST_PER_SEC)
                            self.scores[p1] = max(0, self.scores[p1] - cost)
                            self.scores[p2] = max(0, self.scores[p2] - cost)

        self.tethers = active_tethers

    def _handle_collisions(self) -> None:
        result = self._collision_mgr.resolve(
            self.ships,
            self.bullets,
            self.asteroids,
            self.ufos,
            self.time_bombs,
            self.tethers,
        )
        self.events.extend(result.events)

        # Aplica ganhos de pontos (incluindo abates PVP)
        for player_id, delta in result.score_deltas.items():
            if player_id in self.scores:
                self.scores[player_id] += delta

        # spawn de asteroids fragmentados
        for pos, vel, size in result.asteroids_to_spawn:
            self.spawn_asteroid(pos, vel, size)

        # Processa mortes (usa set para não matar a mesma nave duas vezes no mesmo frame)
        for player_id in set(result.ship_deaths):
            ship = self.ships.get(player_id)
            if ship:
                self._ship_die(ship)

    def _ship_die(self, ship: Ship) -> None:
        pid = ship.player_id
        self.lives[pid] -= 1

        if self.lives[pid] > 0:
            ship.pos.xy = (C.WIDTH / 2, C.HEIGHT / 2)
            ship.vel.xy = (0, 0)
            ship.angle = -90.0
            ship.invuln = float(C.SAFE_SPAWN_TIME)
        else:
            # Jogador eliminado da partida atual
            ship.kill()
            if pid in self.ships:
                # Mantemos a referência no dict para o Score aparecer na HUD,
                # mas a entidade física sumiu.
                pass

        if all(life <= 0 for life in self.lives.values()):
            self.game_over = True

    # Métodos _update_ufos, _update_timers, etc permanecem como os enviados
    def _update_timers(self, dt: float) -> None:
        self.ufo_timer -= dt
        if self.ufo_timer <= 0.0:
            self.spawn_ufo()

        for ship in self.ships.values():
            ship.update_time_bomb_cooldown(dt)
        for time_bomb in self.time_bombs:
            time_bomb.check_explode(dt)

    def _maybe_start_next_wave(self, dt: float) -> None:
        if self.asteroids:
            return
        self.wave_cool -= dt
        if self.wave_cool <= 0.0:
            self.start_wave()

    def _get_nearest_ship_pos(self, from_pos: Vec) -> Vec | None:
        nearest = None
        min_dist = float("inf")
        for ship in self.ships.values():
            if not ship.alive():
                continue
            d = (ship.pos - from_pos).length()
            if d < min_dist:
                min_dist = d
                nearest = ship
        return nearest.pos if nearest else None

    def _update_ufos(self, dt: float) -> None:
        for ufo in list(self.ufos):
            ufo.target_pos = self._get_nearest_ship_pos(ufo.pos)
            ufo.update(dt)
            bullet = ufo.try_fire()
            if bullet:
                self.bullets.add(bullet)
                self.all_sprites.add(bullet)
                self.events.append("ufo_shoot")
            if not ufo.alive():
                self.ufos.remove(ufo)

    def spawn_asteroid(self, pos: Vec, vel: Vec, size: str) -> None:
        ast = Asteroid(pos, vel, size)
        self.asteroids.add(ast)
        self.all_sprites.add(ast)

    def spawn_ufo(self) -> None:
        pos = rand_edge_pos()
        target = self._get_nearest_ship_pos(pos)
        ufo = UFO(pos, uniform(0, 1) < 0.5, target_pos=target)
        self.ufos.add(ufo)
        self.all_sprites.add(ufo)

    def start_wave(self) -> None:
        self.wave += 1
        count = C.WAVE_BASE_COUNT + self.wave
        ship_positions = [s.pos for s in self.ships.values() if s.alive()]
        for _ in range(count):
            pos = rand_edge_pos()
            while any(
                (pos - sp).length() < C.AST_MIN_SPAWN_DIST for sp in ship_positions
            ):
                pos = rand_edge_pos()
            ang = uniform(0, math.tau)
            vel = Vec(math.cos(ang), math.sin(ang)) * uniform(
                C.AST_VEL_MIN, C.AST_VEL_MAX
            )
            self.spawn_asteroid(pos, vel, "L")

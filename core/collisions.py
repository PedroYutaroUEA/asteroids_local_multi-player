"""Collision detection and resolution."""

from dataclasses import dataclass, field
from random import uniform

import pygame as pg

from core import config as C
from core.entities import Asteroid, Ship, UFO_BULLET_OWNER
from core.utils import Vec, circles_collide, rand_unit_vec


@dataclass
class CollisionResult:
    """Outcome of a single collision resolution pass."""

    events: list[str] = field(default_factory=list)
    score_deltas: dict[C.PlayerId, int] = field(default_factory=dict)
    ship_deaths: list[C.PlayerId] = field(default_factory=list)
    ship_time_delayed: list[C.PlayerId] = field(default_factory=list)
    asteroids_to_spawn: list[tuple[Vec, Vec, str]] = field(default_factory=list)
    powerups_to_spawn: list[Vec] = field(default_factory=list)
    collected_powerups: dict[C.PlayerId, str] = field(default_factory=dict)


class CollisionManager:
    """Resolves all collisions between game entities."""

    def resolve(
        self,
        ships: dict[C.PlayerId, Ship],
        bullets: pg.sprite.Group,
        asteroids: pg.sprite.Group,
        ufos: pg.sprite.Group,
        time_bombs: pg.sprite.Group,
        tethers: list[tuple[C.PlayerId, C.PlayerId]] = None,
        powerups: pg.sprite.Group = None,
    ) -> CollisionResult:
        result = CollisionResult()
        tethers = tethers or []
        powerups = powerups or pg.sprite.Group()
        # Bullet X Objects
        self._bullets_vs_asteroids(bullets, asteroids, result)
        self._bullets_vs_time_bombs(bullets, time_bombs, result)

        # 2. Balas vs Entidades Ativas (UFO e Jogadores)
        self._bullets_vs_ufos(bullets, ufos, result)  # Unificado: Player e UFO bullets
        self._bullets_vs_ships(bullets, ships, result)  #

        # Physics Interactions
        self._ufo_vs_asteroids(ufos, asteroids, result)
        self._ship_vs_asteroids(ships, asteroids, result)
        self._ship_vs_ship(ships, result)
        self._ship_vs_powerups(ships, powerups, result)

        # 4. Mecânicas Especiais
        self._tether_vs_asteroids(tethers, ships, asteroids, result)
        self._tether_vs_ufos(tethers, ships, ufos, result)
        self._ship_vs_time_bombs(ships, time_bombs, result)
        self._ufo_vs_time_bombs(ufos, time_bombs, result)
        self._asteroid_vs_time_bombs(asteroids, time_bombs, result)

        return result

    def _ship_vs_powerups(
        self,
        ships: dict[C.PlayerId, Ship],
        powerups: pg.sprite.Group,
        result: CollisionResult,
    ):
        for ship in ships.values():
            if not ship.alive():
                continue
            for pu in list(powerups):
                if (ship.pos - pu.pos).length() < (ship.r + pu.r):
                    result.collected_powerups[ship.player_id] = pu.kind
                    result.events.append("powerup_collect")
                    pu.kill()

    def _tether_vs_asteroids(
        self,
        tethers: list[tuple[C.PlayerId, C.PlayerId]],
        ships: dict[C.PlayerId, Ship],
        asteroids: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        for p1, p2 in tethers:
            s1, s2 = ships.get(p1), ships.get(p2)
            if not s1 or not s2 or not s1.alive() or not s2.alive():
                continue
            for ast in list(asteroids):
                if self._line_intersects_circle(s1.pos, s2.pos, ast.pos, ast.r):
                    # Ambos dividem os pontos, atribuimos ao p1 para simplificar, ou ambos
                    self._split_asteroid(ast, result=result, scorer_id=p1)
                    # p2 also gets points
                    result.score_deltas[p2] = (
                        result.score_deltas.get(p2, 0) + C.AST_SIZES[ast.size]["score"]
                    )

    def _tether_vs_ufos(
        self,
        tethers: list[tuple[C.PlayerId, C.PlayerId]],
        ships: dict[C.PlayerId, Ship],
        ufos: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        for p1, p2 in tethers:
            s1, s2 = ships.get(p1), ships.get(p2)
            if not s1 or not s2 or not s1.alive() or not s2.alive():
                continue
            for ufo in list(ufos):
                if self._line_intersects_circle(s1.pos, s2.pos, ufo.pos, ufo.r):
                    score = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    result.score_deltas[p1] = result.score_deltas.get(p1, 0) + score
                    result.score_deltas[p2] = result.score_deltas.get(p2, 0) + score
                    ufo.kill()
                    result.events.append("ship_explosion")

    def _line_intersects_circle(self, p1: Vec, p2: Vec, center: Vec, r: float) -> bool:
        line_vec = p2 - p1
        line_len = line_vec.length()
        if line_len == 0:
            return (center - p1).length() <= r

        line_unit = line_vec / line_len
        point_to_center = center - p1
        proj_length = point_to_center.dot(line_unit)

        if proj_length < 0:
            closest_point = p1
        elif proj_length > line_len:
            closest_point = p2
        else:
            closest_point = p1 + line_unit * proj_length

        return (center - closest_point).length() <= r

    def _ship_vs_time_bombs(
        self,
        ships: dict[C.PlayerId, Ship],
        time_bombs: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        """Lógica de PVP: Jogador atingido por bomba-relógio de outro jogador."""
        for ship in list(ships.values()):
            if ship.invuln > 0.0 or not ship.alive():
                continue

            for bomb in list(time_bombs):
                # Ignora bombas-relógio lançadas pela própria nave
                if bomb.owner_id == ship.player_id:
                    continue

                if (bomb.pos - ship.pos).length() < (bomb.r + ship.r) and bomb.exploded:
                    ship.vel *= 0.8  # Reduz a velocidade da nave atingida
                    result.events.append("ship_time_delayed")
                elif (bomb.pos - ship.pos).length() < (
                    bomb.r + ship.r
                ) and not bomb.exploded:
                    bomb.early_explosion = (
                        True  # Detona a bomba mais rápido se atingida por uma nave
                    )

    def _ship_vs_ship(
        self, ships: dict[C.PlayerId, Ship], result: CollisionResult
    ) -> None:
        """Colisão física entre duas naves."""
        pids = list(ships.keys())
        for i, pid1 in enumerate(pids):
            for pid2 in pids[i + 1 :]:
                s1, s2 = ships[pid1], ships[pid2]
                if not s1.alive() or not s2.alive():
                    continue
                if s1.invuln > 0 or s2.invuln > 0:
                    continue

                if (s1.pos - s2.pos).length() < (s1.r + s2.r):
                    result.ship_deaths.append(pid1)
                    result.ship_deaths.append(pid2)
                    result.events.append("ship_explosion")

    def _reflect_bullet(self, bullet, target):
        """Calcula a reflexão física da bala contra um objeto circular."""
        if (
            not getattr(bullet, "can_ricochet", False)
            or bullet.bounces >= bullet.max_bounces
        ):
            return False
        # 1. Calcula o vetor normal (do centro do alvo para a bala)
        diff = bullet.pos - target.pos
        dist = diff.length()
        if dist == 0:
            return False
        normal = diff / dist  # Vetor unitário normal
        # 2. Reflete o vetor velocidade: v' = v - 2 * (v . n) * n
        dot_product = bullet.vel.dot(normal)

        bullet.vel = bullet.vel - (normal * (2 * dot_product))
        # 3. Reposicionamento (Push-out) para evitar colisão no próximo frame
        # Coloca a bala exatamente na borda do alvo + um pequeno padding
        bullet.pos = target.pos + (normal * (target.r + bullet.r + 2))

        bullet.bounces += 1
        return True

    def _bullets_vs_asteroids(
        self,
        bullets: pg.sprite.Group,
        asteroids: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        for bullet in list(bullets):
            for ast in list(asteroids):
                if circles_collide(bullet.pos, bullet.r, ast.pos, ast.r):
                    # Tenta refletir. Se falhar (acabou bounces), mata a bala.
                    is_ufo_bullet = bullet.owner_id == UFO_BULLET_OWNER

                    if not is_ufo_bullet:
                        if not self._reflect_bullet(bullet, ast):
                            bullet.kill()
                    else:
                        bullet.kill()  # Balas de UFO nunca ricocheteiam

                    # O asteroide sempre quebra, mesmo com ricochete
                    scorer = bullet.owner_id if not is_ufo_bullet else None
                    self._split_asteroid(ast, result, scorer_id=scorer)
                    break

    def _bullets_vs_time_bombs(
        self,
        bullets: pg.sprite.Group,
        time_bombs: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        """Lógica de PVP: Jogador atingido por bomba-relógio de outro jogador."""
        for bullet in list(bullets):
            for bomb in list(time_bombs):
                if bullet.owner_id != bomb.owner_id:
                    if (bomb.pos - bullet.pos).length() < (
                        bomb.r + bullet.r
                    ) and bomb.exploded:
                        bullet.vel *= 0.8  # Reduz a velocidade do projétil atingido
                        result.events.append("bullet_time_delayed")
                    elif (bomb.pos - bullet.pos).length() < (
                        bomb.r + bullet.r
                    ) and not bomb.exploded:
                        bomb.early_explosion = (
                            True  # Detona a bomba mais rápido se atingida por um tiro
                        )
                else:
                    continue

    def _asteroid_vs_time_bombs(
        self,
        asteroids: pg.sprite.Group,
        time_bombs: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        """Lógica de PVP: Jogador atingido por bomba-relógio de outro jogador."""
        for ast in list(asteroids):
            for bomb in list(time_bombs):
                if (bomb.pos - ast.pos).length() < (bomb.r + ast.r) and bomb.exploded:
                    ast.vel *= 0.8  # Reduz a velocidade do asteroide atingido
                    result.events.append("asteroid_time_delayed")
                elif (bomb.pos - ast.pos).length() < (
                    bomb.r + ast.r
                ) and not bomb.exploded:
                    bomb.early_explosion = (
                        True  # Detona a bomba mais rápido se atingida por um asteroide
                    )

    def _bullets_vs_ufos(
        self, bullets: pg.sprite.Group, ufos: pg.sprite.Group, result: CollisionResult
    ):
        """Trata balas atingindo o UFO (Pode ser bala de player ou fogo amigo de outro UFO)."""
        for bullet in list(bullets):
            if bullet.owner_id == UFO_BULLET_OWNER:
                continue
            for ufo in list(ufos):
                if (bullet.pos - ufo.pos).length() < (bullet.r + ufo.r):
                    # UFO morre
                    ufo.kill()

                    # Se foi um player que atirou, ele ganha pontos
                    if bullet.owner_id > 0:
                        score = (
                            C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                        )
                        result.score_deltas[bullet.owner_id] = (
                            result.score_deltas.get(bullet.owner_id, 0) + score
                        )

                    # Balas que não ricocheteiam morrem ao impacto
                    if not getattr(bullet, "can_ricochet", False):
                        bullet.kill()

                    result.events.append("ship_explosion")
                    break

    def _ufo_vs_time_bombs(
        self,
        ufos: pg.sprite.Group,
        time_bombs: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        """Lógica de PVP: Jogador atingido por bomba-relógio de outro jogador."""
        for ufo in list(ufos):
            for bomb in list(time_bombs):
                if (bomb.pos - ufo.pos).length() < (bomb.r + ufo.r) and bomb.exploded:
                    ufo.vel *= 0.8  # Reduz a velocidade da nave atingida
                    result.events.append("ufo_time_delayed")
                elif (bomb.pos - ufo.pos).length() < (
                    bomb.r + ufo.r
                ) and not bomb.exploded:
                    bomb.early_explosion = (
                        True  # Detona a bomba mais rápido se atingida por uma nave
                    )

    def _ufo_vs_asteroids(
        self,
        ufos: pg.sprite.Group,
        asteroids: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        """UFO collided with asteroid.

        - UFO is destroyed.
        - Asteroid splits as if it were hit by a bullet, but
          without adding score.
        """
        for ufo in list(ufos):
            for ast in list(asteroids):
                if (ufo.pos - ast.pos).length() < (ufo.r + ast.r):
                    ufo.kill()
                    if ufo in ufos:
                        ufos.remove(ufo)

                    result.events.append("ship_explosion")
                    self._split_asteroid(ast, result=result)
                    break

    def _ship_vs_asteroids(
        self,
        ships: dict[C.PlayerId, Ship],
        asteroids: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        for ship in ships.values():
            if ship.invuln > 0.0 or not ship.alive():
                continue
            for ast in asteroids:
                if (ast.pos - ship.pos).length() < (ast.r + ship.r):
                    result.ship_deaths.append(ship.player_id)
                    result.events.append("ship_explosion")
                    break

    def _bullets_vs_ships(
        self, bullets: pg.sprite.Group, ships: dict[int, Ship], result: CollisionResult
    ):
        """Trata balas (de players ou UFOs) atingindo naves de jogadores."""
        for bullet in list(bullets):
            for ship in ships.values():
                if (
                    not ship.alive()
                    or ship.invuln > 0
                    or (bullet.owner_id == ship.player_id)
                ):
                    continue

                if circles_collide(bullet.pos, bullet.r, ship.pos, ship.r):
                    # Se for bala de outro player (PVP)
                    if bullet.owner_id > 0:
                        result.score_deltas[bullet.owner_id] = (
                            result.score_deltas.get(bullet.owner_id, 0) + 500
                        )

                    # Se a bala não for de ricochete, ela morre
                    if not getattr(bullet, "can_ricochet", False):
                        bullet.kill()

                    result.ship_deaths.append(ship.player_id)
                    result.events.append("ship_explosion")
                    break

    def _split_asteroid(
        self,
        ast: Asteroid,
        result: CollisionResult,
        scorer_id: C.PlayerId | None = None,
    ) -> None:
        """Split or destroy an asteroid.

        scorer_id=None means no score is awarded (e.g. UFO-asteroid collision).
        """
        if scorer_id is not None:
            result.score_deltas[scorer_id] = (
                result.score_deltas.get(scorer_id, 0) + C.AST_SIZES[ast.size]["score"]
            )

        # LÓGICA DE DROP (0.12 chance)
        if uniform(0, 1) < C.POWERUP_DROP_CHANCE:
            result.powerups_to_spawn.append(Vec(ast.pos))

        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)
        ast.kill()

        result.events.append("asteroid_explosion")

        for new_size in split:
            dirv = rand_unit_vec()
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * C.AST_SPLIT_SPEED_MULT
            result.asteroids_to_spawn.append((pos, dirv * speed, new_size))

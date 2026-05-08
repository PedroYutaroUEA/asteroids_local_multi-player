"""Collision detection and resolution."""

from dataclasses import dataclass, field
from random import uniform

import pygame as pg

from core import config as C
from core.entities import Asteroid, Ship, UFO_BULLET_OWNER
from core.utils import Vec, rand_unit_vec


@dataclass
class CollisionResult:
    """Outcome of a single collision resolution pass."""

    events: list[str] = field(default_factory=list)
    score_deltas: dict[C.PlayerId, int] = field(default_factory=dict)
    ship_deaths: list[C.PlayerId] = field(default_factory=list)
    asteroids_to_spawn: list[tuple[Vec, Vec, str]] = field(default_factory=list)


class CollisionManager:
    """Resolves all collisions between game entities."""

    def resolve(
        self,
        ships: dict[C.PlayerId, Ship],
        bullets: pg.sprite.Group,
        asteroids: pg.sprite.Group,
        ufos: pg.sprite.Group,
    ) -> CollisionResult:
        result = CollisionResult()
        # Enviroment Interactions
        self._bullets_vs_asteroids(bullets, asteroids, result)
        self._ufo_vs_player_bullets(ufos, bullets, result)
        self._ufo_vs_asteroids(ufos, asteroids, result)
        # Players Interactions
        self._ship_vs_asteroids(ships, asteroids, result)
        self._ship_vs_ufo_bullets(ships, bullets, result)
        self._ship_vs_player_bullets(ships, bullets, result)
        self._ship_vs_ship(ships, result)
        return result

    def _ship_vs_player_bullets(
        self,
        ships: dict[C.PlayerId, Ship],
        bullets: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        """Lógica de PVP: Jogador atirando em outro jogador."""
        for ship in list(ships.values()):
            if ship.invuln > 0.0 or not ship.alive():
                continue

            for bullet in list(bullets):
                # Ignora tiros de UFO (tratados em outro método) e fogo amigo da própria nave
                if bullet.owner_id <= 0 or bullet.owner_id == ship.player_id:
                    continue

                if (bullet.pos - ship.pos).length() < (bullet.r + ship.r):
                    # O atirador ganha pontos por abater um oponente
                    result.score_deltas[bullet.owner_id] = (
                        result.score_deltas.get(bullet.owner_id, 0) + 500  # Score PVP
                    )
                    bullet.kill()
                    result.ship_deaths.append(ship.player_id)
                    result.events.append("ship_explosion")

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

    def _bullets_vs_asteroids(
        self,
        bullets: pg.sprite.Group,
        asteroids: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        hits = pg.sprite.groupcollide(
            asteroids,
            bullets,
            False,
            True,
            collided=lambda a, b: (a.pos - b.pos).length() < a.r,
        )

        for ast, hit_bullets in hits.items():
            if any(b.owner_id == UFO_BULLET_OWNER for b in hit_bullets):
                ast.kill()
                result.events.append("asteroid_explosion")
                continue

            player_bullets = [b for b in hit_bullets if b.owner_id > 0]
            scorer = player_bullets[0].owner_id if player_bullets else None
            self._split_asteroid(ast, scorer_id=scorer, result=result)

    def _ufo_vs_player_bullets(
        self,
        ufos: pg.sprite.Group,
        bullets: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        for ufo in list(ufos):
            for bullet in list(bullets):
                if bullet.owner_id <= 0:
                    continue
                if (ufo.pos - bullet.pos).length() < (ufo.r + bullet.r):
                    score = C.UFO_SMALL["score"] if ufo.small else C.UFO_BIG["score"]
                    result.score_deltas[bullet.owner_id] = (
                        result.score_deltas.get(bullet.owner_id, 0) + score
                    )
                    ufo.kill()
                    bullet.kill()
                    result.events.append("ship_explosion")

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

    def _ship_vs_ufo_bullets(
        self,
        ships: dict[C.PlayerId, Ship],
        bullets: pg.sprite.Group,
        result: CollisionResult,
    ) -> None:
        for ship in ships.values():
            if ship.invuln > 0.0 or not ship.alive():
                continue
            for bullet in list(bullets):
                if bullet.owner_id == UFO_BULLET_OWNER:
                    if (bullet.pos - ship.pos).length() < (bullet.r + ship.r):
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

        split = C.AST_SIZES[ast.size]["split"]
        pos = Vec(ast.pos)
        ast.kill()

        result.events.append("asteroid_explosion")

        for new_size in split:
            dirv = rand_unit_vec()
            speed = uniform(C.AST_VEL_MIN, C.AST_VEL_MAX) * C.AST_SPLIT_SPEED_MULT
            result.asteroids_to_spawn.append((pos, dirv * speed, new_size))

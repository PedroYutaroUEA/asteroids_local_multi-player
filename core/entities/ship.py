"""Ship entity."""

from random import uniform

import pygame as pg

from core import config as C
from core.commands import PlayerCommand
from core.utils import Vec, angle_to_vec, wrap_pos
from .base import Entity
from .bullet import Bullet


class Ship(Entity):
    """Player ship – driven by :class:`~core.commands.PlayerCommand`.
    The ship intentionally does **not** read the keyboard directly so that
    the same class can be used for local and networked players.
    """

    def __init__(self, player_id: C.PlayerId, pos: Vec) -> None:
        self.r = int(C.SHIP_RADIUS)
        super().__init__()

        self.player_id = player_id
        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.angle = -90.0
        self.cool = 0.0
        self.invuln = 0.0

    def apply_command(
        self,
        cmd: PlayerCommand,
        dt: float,
        bullets: pg.sprite.Group,
    ) -> "Bullet | None":
        """Apply a player command for this frame, returning a new bullet if fired."""
        if cmd.rotate_left and not cmd.rotate_right:
            self.angle -= C.SHIP_TURN_SPEED * dt
        elif cmd.rotate_right and not cmd.rotate_left:
            self.angle += C.SHIP_TURN_SPEED * dt

        if cmd.thrust:
            self.vel += angle_to_vec(self.angle) * C.SHIP_THRUST * dt

        self.vel *= C.SHIP_FRICTION

        if cmd.shoot:
            return self._try_fire(bullets)

        return None

    def hyperspace(self) -> None:
        """Teleport the ship to a random position and grant brief invulnerability."""
        self.pos = Vec(uniform(0, C.WIDTH), uniform(0, C.HEIGHT))
        self.vel.xy = (0, 0)
        self.invuln = float(C.SAFE_SPAWN_TIME)

    def ship_points(self) -> tuple[Vec, Vec, Vec]:
        """Return the three triangle vertices used for rendering."""
        dirv = angle_to_vec(self.angle)
        left = angle_to_vec(self.angle + C.SHIP_NOSE_ANGLE)
        right = angle_to_vec(self.angle - C.SHIP_NOSE_ANGLE)

        p1 = self.pos + dirv * self.r
        p2 = self.pos + left * self.r * C.SHIP_NOSE_SCALE
        p3 = self.pos + right * self.r * C.SHIP_NOSE_SCALE
        return p1, p2, p3

    def update(self, dt: float) -> None:
        if self.cool > 0.0:
            self.cool = max(0.0, self.cool - dt)

        if self.invuln > 0.0:
            self.invuln = max(0.0, self.invuln - dt)

        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self._sync_rect()

    def _try_fire(self, bullets: pg.sprite.Group) -> "Bullet | None":
        if self.cool > 0.0:
            return None

        owned = sum(
            1 for b in bullets if getattr(b, "owner_id", None) == self.player_id
        )
        if owned >= C.MAX_BULLETS_PER_PLAYER:
            return None

        dirv = angle_to_vec(self.angle)
        pos = self.pos + dirv * (self.r + C.BULLET_SPAWN_OFFSET)
        vel = self.vel + dirv * C.SHIP_BULLET_SPEED

        self.cool = float(C.SHIP_FIRE_RATE)
        return Bullet(self.player_id, pos, vel, ttl=C.BULLET_TTL)

"""Bullet entity."""

from core import config as C
from core.utils import Vec, wrap_pos
from .base import Entity


class Bullet(Entity):
    """Generic projectile fired by ships or UFOs."""

    def __init__(
        self,
        owner_id: C.PlayerId,
        pos: Vec,
        vel: Vec,
        r=int(C.BULLET_RADIUS),
        ttl: float = C.BULLET_TTL,
        can_ricochet=False,
    ) -> None:
        self.r = r
        super().__init__()
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = float(ttl)
        self.owner_id = owner_id

        self.can_ricochet = can_ricochet
        self.bounces = 0
        self.max_bounces = getattr(C, "RICOCHET_MAX_BOUNCES", 5)

    def update(self, dt: float) -> None:
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()

        self.pos += self.vel * dt
        self.react_to_boundary(C.WIDTH, C.HEIGHT)
        self._sync_rect()

    def react_to_boundary(self, width, height):
        if self.can_ricochet and self.bounces < self.max_bounces:
            if self.pos.x <= 0 or self.pos.x >= width:
                self.vel.x *= -1
                self.bounces += 1
            if self.pos.y <= 0 or self.pos.y >= height:
                self.vel.y *= -1
                self.bounces += 1
        else:
            # Comportamento padrão: Wrap-around se não puder mais ricochetear
            self.pos = wrap_pos(self.pos)

"""Bullet entity."""

from core import config as C
from core.utils import Vec, wrap_pos
from .base import Entity

PlayerId = int


class Bullet(Entity):
    """Generic projectile fired by ships or UFOs."""

    def __init__(
        self,
        owner_id: PlayerId,
        pos: Vec,
        vel: Vec,
        ttl: float = C.BULLET_TTL,
    ) -> None:
        self.r = int(C.BULLET_RADIUS)
        super().__init__()

        self.owner_id = owner_id
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = float(ttl)

    def update(self, dt: float) -> None:
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)

        self.ttl -= dt
        if self.ttl <= 0.0:
            self.kill()
            return

        self._sync_rect()

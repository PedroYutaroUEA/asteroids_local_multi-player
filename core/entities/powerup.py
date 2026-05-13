from core.entities.base import Entity
from core.utils import Vec
from core import config as C


class PowerUp(Entity):
    """Collectable power-up on the map."""

    def __init__(self, pos: Vec, kind: str = "RICOCHET"):
        self.r = int(C.POWERUP_RADIUS)
        self.pos = Vec(pos)
        super().__init__()
        self.vel = Vec(0, 0)
        self.kind = kind
        self.ttl = C.POWERUP_LIFETIME

    def update(self, dt: float):
        self.ttl -= dt
        if self.ttl <= 0:
            self.kill()
        self._sync_rect()

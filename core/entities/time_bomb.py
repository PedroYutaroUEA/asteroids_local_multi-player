"""TimeBomb entity."""

from core import config as C
from core.utils import Vec, wrap_pos
from .base import Entity


class TimeBomb(Entity):
    """Time-based explosive entity."""

    def __init__(
        self,
        owner_id: C.PlayerId,
        pos: Vec,
        vel: Vec,
        ttl: float = C.TIME_BOMB_TTL,
    ) -> None:
        self.r = int(C.TIME_BOMB_RADIUS)
        super().__init__()

        self.owner_id = owner_id
        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.ttl = float(ttl)
        self.time_to_explode = C.TIME_BOMB_TIME_TO_EXPLODE
        self.explosion_radius = C.TIME_BOMB_RADIUS * 8
        self.early_explosion = False
        self.exploded = False

    def update(self, dt: float) -> None:
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)

        self.ttl -= dt
        if self.ttl <= 0.0:
            self.kill()
            return

        self._sync_rect()
    
    def check_explode(self, dt: float) -> None:
        """Trigger the explosion effect, affecting nearby entities."""
        if self.time_to_explode > 0.0:
            if self.early_explosion:
                self.exploded = True
                self.time_to_explode = min(self.time_to_explode, 0.0)  # Detona mais rápido se já tiver sido atingida
                self.r = self.explosion_radius
                self.vel = Vec(0, 0)
            self.time_to_explode -= dt
        else:
            self.exploded = True
            self.r = self.explosion_radius
            self.vel = Vec(0, 0)

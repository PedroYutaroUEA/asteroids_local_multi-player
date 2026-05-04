"""Asteroid entity."""

import math
from random import uniform

from core import config as C
from core.utils import Vec, wrap_pos
from .base import Entity


class Asteroid(Entity):
    """Asteroid with an irregular polygon shape."""

    def __init__(self, pos: Vec, vel: Vec, size: str) -> None:
        self.size = size
        self.r = int(C.AST_SIZES[size]["r"])
        super().__init__()

        self.pos = Vec(pos)
        self.vel = Vec(vel)
        self.poly = self._make_poly()

    def _make_poly(self) -> list[Vec]:
        steps = C.AST_POLY_STEPS[self.size]
        pts: list[Vec] = []
        for i in range(steps):
            ang = i * (360 / steps)
            jitter = uniform(C.AST_POLY_JITTER_MIN, C.AST_POLY_JITTER_MAX)
            rr = self.r * jitter
            v = Vec(
                math.cos(math.radians(ang)),
                math.sin(math.radians(ang)),
            )
            pts.append(v * rr)
        return pts

    def update(self, dt: float) -> None:
        self.pos += self.vel * dt
        self.pos = wrap_pos(self.pos)
        self._sync_rect()

"""UFO entity."""

import math
from random import choice, random, uniform

from core import config as C
from core.utils import Vec
from .base import Entity
from .bullet import Bullet

UFO_BULLET_OWNER = -10


def _rotate_vec(v: Vec, deg: float) -> Vec:
    rad = math.radians(deg)
    c, s = math.cos(rad), math.sin(rad)
    return Vec(v.x * c - v.y * s, v.x * s + v.y * c)


class UFO(Entity):
    """Enemy UFO with two movement modes (crossing and pursuing) and aiming logic.

    * **Big UFO** – crosses the screen in a straight line, shoots randomly.
    * **Small UFO** – pursues the player, shoots with slight aim jitter.
    """

    def __init__(
        self,
        pos: Vec,
        small: bool,
        target_pos: Vec | None = None,
    ) -> None:
        self.small = small
        cfg = C.UFO_SMALL if small else C.UFO_BIG
        self.r = int(cfg["r"])
        super().__init__()

        self.pos = Vec(pos)
        self.vel = Vec(0, 0)
        self.speed = float(C.UFO_SPEED_SMALL if small else C.UFO_SPEED_BIG)
        self.cool = 0.0
        self.move_dir: Vec | None = None
        self.target_pos: Vec | None = None

        if self.small:
            self._lock_small_move_dir(target_pos)

        self._setup_crossing_if_needed()

    def update(self, dt: float) -> None:
        if self.cool > 0.0:
            self.cool = max(0.0, self.cool - dt)

        if self.small:
            self._update_pursue(dt)
        else:
            self._update_cross(dt)

        self._sync_rect()

    def try_fire(self) -> "Bullet | None":
        """Attempt to fire a bullet; returns ``None`` if on cooldown or no target."""
        if self.cool > 0.0 or self.target_pos is None:
            return None

        dirv = self._aim_direction()
        if dirv is None:
            return None

        jitter = C.UFO_AIM_JITTER_DEG_SMALL if self.small else C.UFO_AIM_JITTER_DEG_BIG
        dirv = _rotate_vec(dirv, uniform(-jitter, jitter))

        rate = C.UFO_FIRE_RATE_SMALL if self.small else C.UFO_FIRE_RATE_BIG
        self.cool = float(rate)

        return Bullet(
            UFO_BULLET_OWNER,
            self.pos,
            dirv * C.UFO_BULLET_SPEED,
            float(C.UFO_BULLET_TTL),
        )

    def _aim_direction(self) -> Vec | None:
        """Return the normalised direction vector toward the target (with optional random miss)."""
        if not self.small and random() < C.UFO_BIG_MISS_CHANCE:
            ang = uniform(0.0, 360.0)
            return Vec(math.cos(math.radians(ang)), math.sin(math.radians(ang)))

        to_target = self.target_pos - self.pos  # type: ignore[operator]
        if to_target.length_squared() < 1e-6:
            return None
        return to_target.normalize()

    def _lock_small_move_dir(self, target_pos: Vec | None) -> None:
        if target_pos is None:
            ang = uniform(0.0, 360.0)
            self.move_dir = Vec(
                math.cos(math.radians(ang)), math.sin(math.radians(ang))
            )
            return

        to_target = Vec(target_pos) - self.pos
        if to_target.length_squared() < 1e-6:
            ang = uniform(0.0, 360.0)
            self.move_dir = Vec(
                math.cos(math.radians(ang)), math.sin(math.radians(ang))
            )
            return

        self.move_dir = to_target.normalize()

    def _setup_crossing_if_needed(self) -> None:
        if self.small:
            return

        mode = choice(["h", "v", "d"])

        if mode == "h":
            y = uniform(0, C.HEIGHT)
            left_to_right = uniform(0, 1) < 0.5
            self.pos = Vec(0 if left_to_right else C.WIDTH, y)
            self.vel = Vec(1 if left_to_right else -1, 0) * self.speed
            return

        if mode == "v":
            x = uniform(0, C.WIDTH)
            top_to_bottom = uniform(0, 1) < 0.5
            self.pos = Vec(x, 0 if top_to_bottom else C.HEIGHT)
            self.vel = Vec(0, 1 if top_to_bottom else -1) * self.speed
            return

        # diagonal
        corners = [Vec(0, 0), Vec(C.WIDTH, 0), Vec(0, C.HEIGHT), Vec(C.WIDTH, C.HEIGHT)]
        start = choice(corners)
        target = Vec(C.WIDTH - start.x, C.HEIGHT - start.y)
        self.pos = Vec(start)
        dirv = target - start
        if dirv.length_squared() > 0:
            dirv = dirv.normalize()
        self.vel = dirv * self.speed

    def _update_pursue(self, dt: float) -> None:
        if self.move_dir is not None:
            self.vel = self.move_dir * self.speed
        self.pos += self.vel * dt
        self._kill_if_outside_screen()

    def _update_cross(self, dt: float) -> None:
        self.pos += self.vel * dt
        self._kill_if_outside_screen()

    def _kill_if_outside_screen(self) -> None:
        margin = self.r
        out_x = self.pos.x < -margin or self.pos.x > C.WIDTH + margin
        out_y = self.pos.y < -margin or self.pos.y > C.HEIGHT + margin
        if out_x or out_y:
            self.kill()

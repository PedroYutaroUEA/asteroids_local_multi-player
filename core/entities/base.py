"""Abstract base class for all game entities."""

import abc

import pygame as pg

from core.utils import Vec


class Entity(pg.sprite.Sprite, abc.ABC):
    """Base class for every game entity.

    Subclasses must define:
      - ``r``  (int)  – collision radius, set before calling super().__init__()
      - ``pos`` (Vec) – world position
      - ``update(dt)`` – advance simulation by *dt* seconds
    """

    r: int
    pos: Vec

    def __init__(self) -> None:
        super().__init__()
        self.rect = pg.Rect(0, 0, self.r * 2, self.r * 2)

    @abc.abstractmethod
    def update(self, dt: float) -> None:
        """Advance the entity by *dt* seconds."""

    def _sync_rect(self) -> None:
        """Centre ``self.rect`` on the current world position."""
        self.rect.center = (int(self.pos.x), int(self.pos.y))

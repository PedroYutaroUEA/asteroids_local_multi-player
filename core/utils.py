"""Common game utilities."""

import math
from random import random, uniform
from typing import Iterable

import pygame as pg

from core import config as C

Vec = pg.math.Vector2


# --- Matemática e Lógica ---


def wrap_pos(pos: Vec) -> Vec:
    return Vec(pos.x % C.WIDTH, pos.y % C.HEIGHT)


def angle_to_vec(deg: float) -> Vec:
    rad = math.radians(deg)
    return Vec(math.cos(rad), math.sin(rad))


def circles_collide(p1: Vec, r1: float, p2: Vec, r2: float) -> bool:
    """Verifica colisão entre dois círculos."""
    return (p1 - p2).length_squared() < (r1 + r2) ** 2


def reflect_vector(velocity: Vec, pos: Vec, target_pos: Vec) -> Vec:
    """Calcula o vetor de reflexão contra um alvo circular."""
    normal = (pos - target_pos).normalize()
    return velocity - (normal * (2 * velocity.dot(normal)))


def rand_unit_vec() -> Vec:
    ang = uniform(0, math.tau)
    return Vec(math.cos(ang), math.sin(ang))


def rand_edge_pos() -> Vec:
    if random() < 0.5:
        x = uniform(0, C.WIDTH)
        y = 0 if random() < 0.5 else C.HEIGHT
    else:
        x = 0 if random() < 0.5 else C.WIDTH
        y = uniform(0, C.HEIGHT)
    return Vec(x, y)


# --- Desenho Otimizado ---


def draw_circle(
    surface: pg.Surface, pos: Vec, r: int, color: tuple = C.WHITE, width: int = 1
) -> None:
    """Desenha um circulo genérico"""
    pg.draw.circle(surface, color, (int(pos.x), int(pos.y)), int(r), width)


def draw_poly(
    surface: pg.Surface,
    center: Vec,
    points: Iterable[Vec],
    color: tuple = C.WHITE,
    width: int = 1,
) -> None:
    """Desenha um polígono rotacionado ou deslocado baseado em um centro."""
    abs_points = [(int(center.x + p.x), int(center.y + p.y)) for p in points]
    pg.draw.polygon(surface, color, abs_points, width)

"""Client-side rendering (pygame)."""

import pygame as pg

from core import config as C
from core.entities import Asteroid, Bullet, Ship, UFO
from core.scene import SceneState


class Renderer:
    """Draws scenes and entities without coupling game rules to Game."""

    def __init__(
        self,
        screen: pg.Surface,
        config: object = C,
        fonts: dict[str, pg.font.Font] | None = None,
    ) -> None:
        self.screen = screen
        self.config = config
        safe_fonts = fonts or {}
        self.font = safe_fonts["font"]
        self.big = safe_fonts["big"]

        self._draw_dispatch: dict[type, callable] = {
            Bullet: self._draw_bullet,
            Asteroid: self._draw_asteroid,
            Ship: self._draw_ship,
            UFO: self._draw_ufo,
        }

    def clear(self) -> None:
        self.screen.fill(self.config.BLACK)

    def draw_world(self, world: object) -> None:
        sprites = getattr(world, "all_sprites", [])
        for sprite in sprites:
            drawer = self._draw_dispatch.get(type(sprite))
            if drawer is not None:
                drawer(sprite)

    def draw_hud(self, scores: dict, lives: dict, wave: int, state: SceneState) -> None:
        if state != SceneState.PLAY:
            return

        self._draw_wave_indicator(wave)
        self._draw_player_panels(scores, lives)

    def _draw_wave_indicator(self, wave: int) -> None:
        """Renderiza o indicador de wave centralizado com fundo semi-transparente."""
        wave_text = f"WAVE  {wave}"
        label = self.font.render(wave_text, True, self.config.WHITE)
        lw, lh = label.get_size()
        pad_x, pad_y = 18, 6
        cx = C.WIDTH // 2 - (lw + pad_x * 2) // 2
        cy = 8

        bg = pg.Surface((lw + pad_x * 2, lh + pad_y * 2), pg.SRCALPHA)
        bg.fill((255, 255, 255, 25))
        self.screen.blit(bg, (cx, cy))
        pg.draw.rect(
            self.screen,
            (180, 180, 180, 120),
            (cx, cy, lw + pad_x * 2, lh + pad_y * 2),
            1,
        )
        self.screen.blit(label, (cx + pad_x, cy + pad_y))

    def _draw_player_panels(self, scores: dict, lives: dict) -> None:
        """Renderiza um painel HUD para cada jogador, posicionado dinamicamente."""
        pids = sorted(scores.keys())
        n = len(pids)
        if n == 0:
            return

        # Dimensões do painel — fixas mas proporcionais à tela
        pw = max(160, C.WIDTH // 6)   # largura do painel
        ph = 72                        # altura do painel
        margin = 10                    # afastamento das bordas

        # Quadrantes: sempre usa os 4 cantos, independente de quantos jogadores
        quadrant_positions = [
            (margin, margin),                          # top-left
            (C.WIDTH - pw - margin, margin),           # top-right
            (margin, C.HEIGHT - ph - margin),          # bottom-left
            (C.WIDTH - pw - margin, C.HEIGHT - ph - margin),  # bottom-right
        ]

        for idx, pid in enumerate(pids):
            qpos = quadrant_positions[idx % 4]
            self._draw_single_player_panel(
                pid,
                qpos,
                pw,
                ph,
                scores[pid],
                lives[pid],
            )

    def _draw_single_player_panel(
        self,
        pid: int,
        pos: tuple,
        pw: int,
        ph: int,
        score: int,
        life_count: int,
    ) -> None:
        """Desenha o painel completo de um jogador (barra de título + score + vidas)."""
        x, y = pos
        color = C.PLAYER_COLORS.get(pid, self.config.WHITE)
        eliminated = life_count <= 0

        # --- Fundo do painel ---
        bg = pg.Surface((pw, ph), pg.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        self.screen.blit(bg, (x, y))

        # --- Borda ---
        border_color = (80, 80, 80) if eliminated else color
        pg.draw.rect(self.screen, border_color, (x, y, pw, ph), 1)

        # --- Barra de título colorida ---
        bar_h = 20
        bar_surf = pg.Surface((pw, bar_h), pg.SRCALPHA)
        r, g, b = color
        bar_surf.fill((r, g, b, 60 if eliminated else 110))
        self.screen.blit(bar_surf, (x, y))
        name_label = self.font.render(f"PLAYER {pid}", True, color)
        self.screen.blit(name_label, (x + 8, y + 1))

        if eliminated:
            # --- Status ELIMINATED ---
            elim_label = self.font.render("ELIMINATED", True, (200, 60, 60))
            ex = x + pw // 2 - elim_label.get_width() // 2
            ey = y + bar_h + 6
            self.screen.blit(elim_label, (ex, ey))
        else:
            # --- Score ---
            score_label = self.font.render(f"{score:07d}", True, self.config.WHITE)
            self.screen.blit(score_label, (x + 8, y + bar_h + 4))

            # --- Ícones de vida (triângulos mini) ---
            self._draw_life_icons(x + 8, y + bar_h + 28, life_count, color)

    def _draw_life_icons(
        self, x: int, y: int, count: int, color: tuple
    ) -> None:
        """Desenha 'count' mini-naves (triângulos) como ícones de vida."""
        icon_w, icon_h, gap = 12, 14, 5
        for i in range(count):
            ix = x + i * (icon_w + gap)
            # Triângulo apontando para cima, como uma nave vista de frente
            tip = (ix + icon_w // 2, y)
            left = (ix, y + icon_h)
            right = (ix + icon_w, y + icon_h)
            pg.draw.polygon(self.screen, color, [tip, left, right], 1)

    def draw_menu(self) -> None:
        self._draw_text(
            self.big,
            "ASTEROIDS",
            self.config.WIDTH // 2 - 170,
            200,
        )
        self._draw_text(
            self.font,
            "Press any key to start.",
            self.config.WIDTH // 2 - 170,
            350,
        )
        self._draw_text(
            self.font,
            "(or press 'ESC' to exit)",
            self.config.WIDTH // 2 - 175,
            375,
        )

    def draw_game_over(self) -> None:
        self._draw_text(
            self.big,
            "FIM DE JOGO!",
            self.config.WIDTH // 2 - 170,
            260,
        )
        self._draw_text(
            self.font,
            "Press any key to start.",
            self.config.WIDTH // 2 - 170,
            340,
        )

    def _draw_text(
        self,
        font: pg.font.Font,
        text: str,
        x: int,
        y: int,
    ) -> None:
        label = font.render(text, True, self.config.WHITE)
        self.screen.blit(label, (x, y))

    def _draw_bullet(self, bullet: Bullet) -> None:
        center = (int(bullet.pos.x), int(bullet.pos.y))
        color = (
            C.PLAYER_COLORS.get(bullet.owner_id, self.config.WHITE)
            if bullet.owner_id > 0
            else self.config.WHITE
        )

        pg.draw.circle(
            self.screen,
            color,
            center,
            bullet.r,
            width=1,
        )

    def _draw_asteroid(self, asteroid: Asteroid) -> None:
        points = []
        for point in asteroid.poly:
            px = int(asteroid.pos.x + point.x)
            py = int(asteroid.pos.y + point.y)
            points.append((px, py))
        pg.draw.polygon(self.screen, self.config.WHITE, points, width=1)

    def _draw_ship(self, ship: Ship) -> None:
        p1, p2, p3 = ship.ship_points()
        points = [
            (int(p1.x), int(p1.y)),
            (int(p2.x), int(p2.y)),
            (int(p3.x), int(p3.y)),
        ]
        color = C.PLAYER_COLORS.get(ship.player_id, self.config.WHITE)
        pg.draw.polygon(self.screen, color, points, width=1)

        if ship.invuln > 0.0 and int(ship.invuln * 10) % 2 == 0:
            center = (int(ship.pos.x), int(ship.pos.y))
            pg.draw.circle(
                self.screen,
                color,
                center,
                ship.r + 6,
                width=1,
            )

    def _draw_ufo(self, ufo: UFO) -> None:
        width = ufo.r * 2
        height = ufo.r

        body = pg.Rect(0, 0, width, height)
        body.center = (int(ufo.pos.x), int(ufo.pos.y))
        pg.draw.ellipse(self.screen, self.config.WHITE, body, width=1)

        cup = pg.Rect(0, 0, int(width * 0.5), int(height * 0.7))
        cup.center = (int(ufo.pos.x), int(ufo.pos.y - height * 0.3))
        pg.draw.ellipse(self.screen, self.config.WHITE, cup, width=1)

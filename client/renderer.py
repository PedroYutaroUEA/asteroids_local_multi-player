"""Client-side rendering (pygame)."""

import math
import random
import pygame as pg

from core import config as C
from core.entities import Asteroid, Bullet, Ship, UFO, TimeBomb
from core.entities.powerup import PowerUp
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
            TimeBomb: self._draw_time_bomb,
            PowerUp: self._draw_powerup,
        }

    def clear(self) -> None:
        self.screen.fill(self.config.BLACK)

    def draw_world(self, world: object) -> None:
        if hasattr(world, "tethers") and hasattr(world, "ships"):

            for p1, p2 in world.tethers:
                s1 = world.ships.get(p1)
                s2 = world.ships.get(p2)
                if s1 and s2:
                    color = (random.randint(100, 255), random.randint(100, 255), 255)
                    pg.draw.line(
                        self.screen,
                        color,
                        (int(s1.pos.x), int(s1.pos.y)),
                        (int(s2.pos.x), int(s2.pos.y)),
                        3,
                    )

        sprites = getattr(world, "all_sprites", [])
        for sprite in sprites:
            drawer = self._draw_dispatch.get(type(sprite))
            if drawer is not None:
                drawer(sprite)

    def draw_hud(
        self,
        scores: dict,
        lives: dict,
        wave: int,
        state: SceneState,
        ships: dict[int, Ship],
    ) -> None:
        if state != SceneState.PLAY:
            return

        self._draw_wave_indicator(wave)
        self._draw_player_panels(scores, lives, ships)

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

    def _draw_player_panels(
        self, scores: dict, lives: dict, ships: dict[int, Ship]
    ) -> None:
        """Renderiza um painel HUD para cada jogador, posicionado dinamicamente."""
        pids = sorted(scores.keys())
        n = len(pids)
        if n == 0:
            return

        # Dimensões do painel — fixas mas proporcionais à tela
        pw = max(160, C.WIDTH // 6)  # largura do painel
        ph = 72  # altura do painel
        margin = 10  # afastamento das bordas

        # Quadrantes: sempre usa os 4 cantos, independente de quantos jogadores
        quadrant_positions = [
            (margin, margin),  # top-left
            (C.WIDTH - pw - margin, margin),  # top-right
            (margin, C.HEIGHT - ph - margin),  # bottom-left
            (C.WIDTH - pw - margin, C.HEIGHT - ph - margin),  # bottom-right
        ]

        for idx, pid in enumerate(pids):
            ship = ships.get(pid)
            qpos = quadrant_positions[idx % 4]
            self._draw_single_player_panel(
                pid, qpos, pw, ph, scores[pid], lives[pid], ship
            )

    def _draw_single_player_panel(
        self,
        pid: int,
        pos: tuple,
        pw: int,
        ph: int,
        score: int,
        life_count: int,
        ship: Ship | None,
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

        # --- Time Bomb Cooldown ---
        if ship:
            self._draw_cooldown_bar(
                x + 8,
                y + ph - 12,
                pw - 16,
                6,
                ship.time_bomb_cooldown,
                C.TIME_BOMB_COOLDOWN,
            )

    def _draw_cooldown_bar(self, x, y, w, h, current, max_val):
        """Barra de progresso genérica para cooldowns no painel."""
        ratio = 1.0 - (current / max_val)
        pg.draw.rect(self.screen, (40, 40, 40), (x, y, w, h))
        fill_w = int(w * ratio)
        fill_color = (0, 220, 120) if current <= 0 else (255, 180, 0)
        pg.draw.rect(self.screen, fill_color, (x, y, fill_w, h))

    def _draw_life_icons(self, x: int, y: int, count: int, color: tuple) -> None:
        """Desenha 'count' mini-naves (triângulos) como ícones de vida."""
        icon_w, icon_h, gap = 12, 14, 5
        for i in range(count):
            ix = x + i * (icon_w + gap)
            # Triângulo apontando para cima, como uma nave vista de frente
            tip = (ix + icon_w // 2, y)
            left = (ix, y + icon_h)
            right = (ix + icon_w, y + icon_h)
            pg.draw.polygon(self.screen, color, [tip, left, right], 1)

    def _draw_powerup(self, powerup: PowerUp) -> None:
        """Renderiza o powerup coletável no mapa."""
        pos = (int(powerup.pos.x), int(powerup.pos.y))

        # Cor neon para o ricochete (baseado em C.RICOCHET_COLOR se existir, ou verde)
        color = (57, 255, 20)

        # Desenha um losango pulsante
        pulse = 1.0 + 0.15 * math.sin(pg.time.get_ticks() * 0.005)
        r = int(powerup.r * pulse)

        points = [
            (pos[0], pos[1] - r),
            (pos[0] + r, pos[1]),
            (pos[0], pos[1] + r),
            (pos[0] - r, pos[1]),
        ]

        # Brilho externo
        pg.draw.polygon(self.screen, (color[0], color[1], color[2], 100), points, 2)
        # Ícone/Texto interno
        label = self.font.render("R", True, color)
        self.screen.blit(
            label, (pos[0] - label.get_width() // 2, pos[1] - label.get_height() // 2)
        )

    def draw_menu(
        self,
        stars: list[tuple[int, int, int]],
        menu_time: float = 0.0,
    ) -> None:
        """Tela de início polida: starfield, título pulsante, guia de controles."""

        cx = C.WIDTH // 2
        cy = C.HEIGHT // 2

        # ── Fundo de estrelas ──────────────────────────────────────────────────
        for sx, sy, sr in stars:
            brightness = 120 + int(40 * math.sin(menu_time * 0.7 + sx * 0.05))
            pg.draw.circle(
                self.screen, (brightness, brightness, brightness), (sx, sy), sr
            )

        # ── Título "ASTEROIDS" com efeito de brilho pulsante ──────────────────
        # Pulsa suavemente entre 80 % e 100 % de intensidade
        pulse = 0.85 + 0.15 * math.sin(menu_time * 2.2)
        title_color = (
            int(240 * pulse),
            int(240 * pulse),
            int(240 * pulse),
        )
        # Camadas de brilho (glow): renderizar o texto maior e mais transparente
        for glow_scale, alpha in ((1.18, 18), (1.10, 35), (1.04, 60)):
            glow_size = int(C.FONT_SIZE_LARGE * glow_scale)
            glow_font = pg.font.SysFont(C.FONT_NAME, glow_size)
            glow_surf = glow_font.render("ASTEROIDS", True, (255, 255, 255))
            glow_surf.set_alpha(alpha)
            gx = cx - glow_surf.get_width() // 2
            gy = C.HEIGHT // 4 - glow_surf.get_height() // 2
            self.screen.blit(glow_surf, (gx, gy))

        title_surf = self.big.render("ASTEROIDS", True, title_color)
        tx = cx - title_surf.get_width() // 2
        ty = C.HEIGHT // 4 - title_surf.get_height() // 2
        self.screen.blit(title_surf, (tx, ty))

        # ── Subtítulo ─────────────────────────────────────────────────────────
        sub_font = pg.font.SysFont(C.FONT_NAME, 20)
        sub_surf = sub_font.render("LOCAL  MULTIPLAYER", True, (160, 200, 255))
        self.screen.blit(
            sub_surf, (cx - sub_surf.get_width() // 2, ty + title_surf.get_height() + 6)
        )

        # ── Divisor ───────────────────────────────────────────────────────────
        div_y = ty + title_surf.get_height() + 38
        pg.draw.line(self.screen, (60, 60, 80), (cx - 220, div_y), (cx + 220, div_y), 1)

        # ── Guia de controles ─────────────────────────────────────────────────
        guide_y = div_y + 16
        label_font = pg.font.SysFont(C.FONT_NAME, 17)

        sections = [
            (
                "TECLADO  P1",
                (255, 255, 255),
                [
                    ("Mover", "← / ↑ / →"),
                    ("Atirar", "Espaco"),
                    ("Hiperespaco", "L Shift"),
                    ("Entrar", 'Pressione  "1"'),
                ],
            ),
            (
                "TECLADO  P2",
                (0, 255, 100),
                [
                    ("Mover", "W / A / D"),
                    ("Atirar", "Q"),
                    ("Hiperespaco", "E"),
                    ("Entrar", 'Pressione  "2"'),
                ],
            ),
            (
                "CONTROLE",
                (100, 200, 255),
                [
                    ("Mover", "Analogico esq."),
                    ("Atirar", "Botao A / X"),
                    ("Hiperespaco", "Botao B / O"),
                    ("Entrar", "Qualquer botao"),
                ],
            ),
        ]

        col_w = C.WIDTH // 3
        for col_idx, (header, hcolor, rows) in enumerate(sections):
            col_x = col_idx * col_w + col_w // 2
            # Cabeçalho da coluna
            h_surf = label_font.render(header, True, hcolor)
            self.screen.blit(h_surf, (col_x - h_surf.get_width() // 2, guide_y))
            # Linha abaixo do cabeçalho
            pg.draw.line(
                self.screen,
                hcolor,
                (col_x - 90, guide_y + h_surf.get_height() + 3),
                (col_x + 90, guide_y + h_surf.get_height() + 3),
                1,
            )
            row_y = guide_y + h_surf.get_height() + 10
            for action, key in rows:
                act_surf = label_font.render(action + ":", True, (140, 140, 140))
                key_surf = label_font.render(key, True, (210, 210, 210))
                self.screen.blit(act_surf, (col_x - 88, row_y))
                self.screen.blit(
                    key_surf, (col_x - 88 + act_surf.get_width() + 4, row_y)
                )
                row_y += act_surf.get_height() + 4

        # ── Rodapé ────────────────────────────────────────────────────────────
        footer_y = C.HEIGHT - 54
        pg.draw.line(
            self.screen,
            (60, 60, 80),
            (cx - 220, footer_y - 8),
            (cx + 220, footer_y - 8),
            1,
        )

        # Pisca o "pressione para começar" em sincronia com o pulso
        if int(menu_time * 2) % 2 == 0:
            start_surf = self.font.render(
                "Pressione uma tecla ou botao para comecar", True, (200, 200, 200)
            )
            self.screen.blit(start_surf, (cx - start_surf.get_width() // 2, footer_y))

        esc_surf = label_font.render("ESC  para sair", True, (90, 90, 90))
        self.screen.blit(esc_surf, (cx - esc_surf.get_width() // 2, footer_y + 26))

    def draw_game_over(
        self,
        scores: dict | None = None,
        lives: dict | None = None,
        wave: int = 0,
        shots_fired: int = 0,
        power_use_count: int = 0,
        elapsed: float = 0.0,
    ) -> None:
        """Tela de fim de jogo com ranking, estatísticas e fade-in."""

        scores = scores or {}
        lives = lives or {}
        cx = C.WIDTH // 2

        # ── Fade-in de fundo ──────────────────────────────────────────────────
        fade_alpha = min(200, int(elapsed * 340))  # 0→200 em ~0.6 s
        fade = pg.Surface((C.WIDTH, C.HEIGHT), pg.SRCALPHA)
        fade.fill((0, 0, 0, fade_alpha))
        self.screen.blit(fade, (0, 0))

        # Só renderiza o conteúdo após o fundo estar suficientemente opaco
        content_alpha = max(0, min(255, int((elapsed - 0.35) * 510)))
        if content_alpha == 0:
            return

        label_font = pg.font.SysFont(C.FONT_NAME, 17)
        medium_font = pg.font.SysFont(C.FONT_NAME, 22)

        # ── Título "GAME OVER" com pulso ──────────────────────────────────────
        pulse = 0.85 + 0.15 * math.sin(elapsed * 2.5)
        title_color = (int(255 * pulse), int(80 * pulse), int(80 * pulse))
        title_surf = self.big.render("GAME  OVER", True, title_color)
        title_surf.set_alpha(content_alpha)
        self.screen.blit(title_surf, (cx - title_surf.get_width() // 2, 28))

        sub = label_font.render(f"WAVE  {wave}  ENCERRADA", True, (140, 140, 160))
        sub.set_alpha(content_alpha)
        self.screen.blit(
            sub, (cx - sub.get_width() // 2, 28 + title_surf.get_height() + 6)
        )

        # ── Divisor ───────────────────────────────────────────────────────────
        div_y = 28 + title_surf.get_height() + 34
        pg.draw.line(self.screen, (60, 60, 80), (cx - 300, div_y), (cx + 300, div_y), 1)

        # ── Ranking ───────────────────────────────────────────────────────────
        rank_y = div_y + 14
        rank_header = medium_font.render("RANKING FINAL", True, (180, 180, 200))
        rank_header.set_alpha(content_alpha)
        self.screen.blit(rank_header, (cx - rank_header.get_width() // 2, rank_y))
        rank_y += rank_header.get_height() + 10

        # Ordena jogadores do maior para o menor score
        medal_labels = {1: "[1]", 2: "[2]", 3: "[3]", 4: "[4]"}
        medal_colors = {
            1: (255, 215, 60),  # ouro
            2: (200, 200, 210),  # prata
            3: (200, 130, 80),  # bronze
            4: (140, 140, 150),  # 4º
        }

        sorted_pids = sorted(scores.keys(), key=lambda p: scores[p], reverse=True)

        row_h = 38
        row_w = 560
        row_x = cx - row_w // 2

        for rank, pid in enumerate(sorted_pids, start=1):
            ry = rank_y + (rank - 1) * (row_h + 6)
            player_color = C.PLAYER_COLORS.get(pid, self.config.WHITE)
            is_eliminated = lives.get(pid, 0) <= 0
            m_color = medal_colors[rank]

            # Fundo da linha
            row_bg = pg.Surface((row_w, row_h), pg.SRCALPHA)
            row_bg.fill((255, 255, 255, 8) if rank == 1 else (0, 0, 0, 60))
            row_bg.set_alpha(content_alpha)
            self.screen.blit(row_bg, (row_x, ry))
            pg.draw.rect(self.screen, m_color, (row_x, ry, row_w, row_h), 1)

            # Medalha
            medal_surf = medium_font.render(medal_labels[rank], True, m_color)
            medal_surf.set_alpha(content_alpha)
            self.screen.blit(
                medal_surf, (row_x + 10, ry + row_h // 2 - medal_surf.get_height() // 2)
            )

            # Nome do jogador
            name_surf = medium_font.render(f"PLAYER {pid}", True, player_color)
            name_surf.set_alpha(content_alpha)
            self.screen.blit(
                name_surf, (row_x + 60, ry + row_h // 2 - name_surf.get_height() // 2)
            )

            # Score
            score_surf = medium_font.render(
                f"{scores[pid]:07d}", True, self.config.WHITE
            )
            score_surf.set_alpha(content_alpha)
            self.screen.blit(
                score_surf,
                (row_x + 260, ry + row_h // 2 - score_surf.get_height() // 2),
            )

            # Status
            if is_eliminated:
                status_text = "ELIMINADO"
                status_color = (200, 60, 60)
            else:
                status_text = "SOBREVIVEU"
                status_color = (80, 200, 100)
            status_surf = label_font.render(status_text, True, status_color)
            status_surf.set_alpha(content_alpha)
            self.screen.blit(
                status_surf,
                (row_x + 420, ry + row_h // 2 - status_surf.get_height() // 2),
            )

        # ── Estatísticas da Partida ───────────────────────────────────────────
        stats_y = rank_y + len(sorted_pids) * (row_h + 6) + 20
        pg.draw.line(
            self.screen, (60, 60, 80), (cx - 300, stats_y), (cx + 300, stats_y), 1
        )
        stats_y += 12

        stats_header = medium_font.render(
            "ESTATISTICAS DA PARTIDA", True, (160, 160, 180)
        )
        stats_header.set_alpha(content_alpha)
        self.screen.blit(stats_header, (cx - stats_header.get_width() // 2, stats_y))
        stats_y += stats_header.get_height() + 10

        stats = [
            ("Wave alcancada", str(wave)),
            ("Tiros disparados", str(shots_fired)),
            ("Hiperespacos usados", str(power_use_count)),
        ]

        stat_col_w = 300
        stat_x = cx - stat_col_w // 2
        for label_text, value_text in stats:
            lbl = label_font.render(label_text + ":", True, (130, 130, 150))
            val = label_font.render(value_text, True, (220, 220, 220))
            lbl.set_alpha(content_alpha)
            val.set_alpha(content_alpha)
            self.screen.blit(lbl, (stat_x, stats_y))
            self.screen.blit(val, (stat_x + stat_col_w - val.get_width(), stats_y))
            stats_y += lbl.get_height() + 5

        # ── Instrução de reinício ─────────────────────────────────────────────
        footer_y = C.HEIGHT - 50
        pg.draw.line(
            self.screen,
            (60, 60, 80),
            (cx - 260, footer_y - 10),
            (cx + 260, footer_y - 10),
            1,
        )

        if elapsed > 1.2 and int(elapsed * 2) % 2 == 0:
            restart_surf = self.font.render(
                "Pressione  ENTER  para jogar novamente", True, (200, 200, 200)
            )
            restart_surf.set_alpha(content_alpha)
            self.screen.blit(
                restart_surf, (cx - restart_surf.get_width() // 2, footer_y)
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

    def _draw_time_bomb(self, bomb: TimeBomb) -> None:
        center = (int(bomb.pos.x), int(bomb.pos.y))
        color = (
            C.PLAYER_COLORS.get(bomb.owner_id, self.config.WHITE)
            if bomb.owner_id > 0
            else self.config.WHITE
        )

        pg.draw.circle(
            self.screen,
            color,
            center,
            bomb.r,
            width=1,
        )

        if bomb.time_to_explode <= 0:
            pg.draw.circle(
                self.screen,
                color,
                center,
                bomb.explosion_radius,
                width=1,
            )

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
        points = [
            (int(asteroid.pos.x + p.x), int(asteroid.pos.y + p.y))
            for p in asteroid.poly
        ]
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

        # --- Arco de Invulnerabilidade ---
        if ship.invuln > 0.0 and int(ship.invuln * 10) % 2 == 0:
            center = (int(ship.pos.x), int(ship.pos.y))
            pg.draw.circle(
                self.screen,
                color,
                center,
                ship.r + 6,
                width=1,
            )
        # --- Arco de Duração do Ricochete ---
        if hasattr(ship, "ricochet_timer") and ship.ricochet_timer > 0:
            self._draw_power_duration_arc(ship, (57, 255, 20))

    def _draw_power_duration_arc(self, ship: Ship, color: tuple) -> None:
        """Desenha um arco decrescente centralizado na nave com 50% de opacidade."""
        # Configurações do arco
        radius = ship.r + 12
        rect = pg.Rect(
            int(ship.pos.x - radius), int(ship.pos.y - radius), radius * 2, radius * 2
        )

        # Cálculo do ângulo baseado no tempo restante (0 a 2*PI)
        # Assume-se C.RICOCHET_DURATION como base
        ratio = ship.ricochet_timer / getattr(C, "RICOCHET_DURATION", 15.0)
        end_angle = (2 * math.pi) * ratio

        # Superfície temporária para opacidade
        arc_surf = pg.Surface((radius * 2 + 4, radius * 2 + 4), pg.SRCALPHA)
        arc_rect = pg.Rect(2, 2, radius * 2, radius * 2)

        # Desenha o arco na superfície transparente (cor com alpha 128 = 50%)
        pg.draw.arc(arc_surf, (*color, 128), arc_rect, 0, end_angle, 3)

        # Blit na tela principal
        self.screen.blit(
            arc_surf, (int(ship.pos.x - radius - 2), int(ship.pos.y - radius - 2))
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

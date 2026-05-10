"""Lobby de pré-jogo: seleção e entrada de jogadores.

Funcionalidades:
- Slots com borda animada pulsante para jogadores ativos
- Badge de dispositivo [KB] ou [JS] por slot
- Dica de teclas/botão por perfil
- Contagem regressiva de 3 s após ENTER antes de iniciar
"""

import math

import pygame as pg

from core import config as C
from client.input.manager import InputManager


# Mapeamento: nome do perfil -> teclas exibidas no slot
_KB_HINT: dict[int, tuple[str, str]] = {
    1: ("Setas + Espaco", "LShift=hiper"),
    2: ("WASD + Q", "E=hiper"),
}

# Duração (segundos) da contagem regressiva antes de iniciar
_COUNTDOWN_DURATION = 3.0


class Lobby:
    """Gerencia o estado de entrada de jogadores e a interface de pré-jogo."""

    def __init__(self, input_manager: InputManager):
        self.input_mgr = input_manager
        self.p_colors = getattr(
            C,
            "PLAYER_COLORS",
            {1: (255, 255, 255), 2: (0, 255, 100), 3: (100, 200, 255), 4: (255, 200, 0)},
        )
        self.lobby_time: float = 0.0       # acumulador geral para animações
        self._countdown: float = 0.0       # > 0 quando contagem regressiva ativa
        self._starting: bool = False       # flag: ENTER pressionado

    # ──────────────────────────────────────────────────────────────────────────
    # Lógica
    # ──────────────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reseta o estado do lobby para uma nova partida."""
        self.lobby_time = 0.0
        self._countdown = 0.0
        self._starting = False

    def update(self, events: list[pg.event.Event], dt: float = 0.0) -> bool:
        """
        Processa entradas e animações do lobby.
        Retorna True quando o jogo deve começar (após countdown).
        """
        self.lobby_time += dt
        self.input_mgr.handle_lobby_events(events)

        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_RETURN and self.input_mgr.get_player_ids():
                    if not self._starting:
                        self._starting = True
                        self._countdown = _COUNTDOWN_DURATION

        # Countdown regressivo
        if self._starting:
            self._countdown -= dt
            if self._countdown <= 0.0:
                return True

        return False

    # ──────────────────────────────────────────────────────────────────────────
    # Renderização
    # ──────────────────────────────────────────────────────────────────────────

    def draw(self, screen: pg.Surface, font: pg.font.Font, big_font: pg.font.Font):
        """Renderiza a interface do Lobby."""
        screen.fill((0, 0, 0))

        label_font = pg.font.SysFont(C.FONT_NAME, 17)
        small_font = pg.font.SysFont(C.FONT_NAME, 15)
        cx = C.WIDTH // 2
        active_ids = self.input_mgr.get_player_ids()

        # ── Título ────────────────────────────────────────────────────────────
        title = big_font.render("LOBBY", True, (255, 255, 255))
        screen.blit(title, (cx - title.get_width() // 2, 30))

        sub = label_font.render("LOCAL  MULTIPLAYER", True, (160, 200, 255))
        screen.blit(sub, (cx - sub.get_width() // 2, 30 + title.get_height() + 4))

        # ── Slots ─────────────────────────────────────────────────────────────
        slot_w, slot_h = 178, 148
        total_w = C.MAX_PLAYERS * slot_w + (C.MAX_PLAYERS - 1) * 18
        start_x = cx - total_w // 2
        slot_y = 148

        for i in range(1, C.MAX_PLAYERS + 1):
            sx = start_x + (i - 1) * (slot_w + 18)
            self._draw_slot(screen, font, label_font, small_font, i, sx, slot_y, slot_w, slot_h, active_ids)

        # ── Rodapé ────────────────────────────────────────────────────────────
        self._draw_footer(screen, font, label_font, active_ids)

        # ── Countdown ─────────────────────────────────────────────────────────
        if self._starting:
            self._draw_countdown(screen, big_font)

    def _draw_slot(
        self,
        screen: pg.Surface,
        font: pg.font.Font,
        label_font: pg.font.Font,
        small_font: pg.font.Font,
        pid: int,
        sx: int,
        sy: int,
        sw: int,
        sh: int,
        active_ids: list[int],
    ) -> None:
        is_active = pid in active_ids
        color = self.p_colors[pid] if is_active else (55, 55, 65)
        r, g, b = color

        # ── Fundo do slot ─────────────────────────────────────────────────────
        bg = pg.Surface((sw, sh), pg.SRCALPHA)
        bg.fill((r, g, b, 18) if is_active else (20, 20, 28, 200))
        screen.blit(bg, (sx, sy))

        # ── Borda animada (pulsante quando ativo, estática quando vazio) ───────
        if is_active:
            pulse = 0.5 + 0.5 * math.sin(self.lobby_time * 4.0 + pid)
            border_w = 1 + int(pulse * 2)        # oscila entre 1 e 3 px
            border_alpha = 160 + int(pulse * 95)  # oscila entre 160 e 255
            border_color = (
                min(255, int(r * 0.7 + 255 * 0.3 * pulse)),
                min(255, int(g * 0.7 + 255 * 0.3 * pulse)),
                min(255, int(b * 0.7 + 255 * 0.3 * pulse)),
            )
        else:
            border_w = 1
            border_color = (55, 55, 65)

        pg.draw.rect(screen, border_color, (sx, sy, sw, sh), border_w)

        # ── Barra de título do slot ───────────────────────────────────────────
        bar_h = 26
        bar_surf = pg.Surface((sw, bar_h), pg.SRCALPHA)
        bar_surf.fill((r, g, b, 80) if is_active else (40, 40, 50, 200))
        screen.blit(bar_surf, (sx, sy))

        p_label = font.render(f"PLAYER  {pid}", True, color)
        screen.blit(p_label, (sx + sw // 2 - p_label.get_width() // 2, sy + 3))

        if is_active:
            self._draw_active_slot(screen, label_font, small_font, pid, sx, sy, sw, bar_h, color)
        else:
            self._draw_empty_slot(screen, label_font, small_font, pid, sx, sy, sw, sh, bar_h)

    def _draw_active_slot(
        self,
        screen: pg.Surface,
        label_font: pg.font.Font,
        small_font: pg.font.Font,
        pid: int,
        sx: int,
        sy: int,
        sw: int,
        bar_h: int,
        color: tuple,
    ) -> None:
        """Conteúdo do slot quando um jogador está conectado."""
        device_type = self.input_mgr.get_device_type(pid)
        badge_text = "TECLADO" if device_type == "keyboard" else "CONTROLE"
        badge_color = (220, 220, 100) if device_type == "keyboard" else (100, 220, 220)

        # Badge de dispositivo
        badge = label_font.render(badge_text, True, badge_color)
        screen.blit(badge, (sx + sw // 2 - badge.get_width() // 2, sy + bar_h + 8))

        # Teclas de controle
        if device_type == "keyboard" and pid in _KB_HINT:
            line1, line2 = _KB_HINT[pid]
            l1 = small_font.render(line1, True, (180, 180, 180))
            l2 = small_font.render(line2, True, (140, 140, 140))
            screen.blit(l1, (sx + sw // 2 - l1.get_width() // 2, sy + bar_h + 32))
            screen.blit(l2, (sx + sw // 2 - l2.get_width() // 2, sy + bar_h + 50))
        elif device_type == "joystick":
            hint = small_font.render("Analogico + Botoes", True, (180, 180, 180))
            screen.blit(hint, (sx + sw // 2 - hint.get_width() // 2, sy + bar_h + 32))

        # Status PRONTO
        ready_pulse = 0.7 + 0.3 * math.sin(self.lobby_time * 3.0)
        rc = tuple(min(255, int(c * ready_pulse)) for c in color)
        ready = label_font.render("PRONTO!", True, rc)
        screen.blit(ready, (sx + sw // 2 - ready.get_width() // 2, sy + bar_h + 100))

    def _draw_empty_slot(
        self,
        screen: pg.Surface,
        label_font: pg.font.Font,
        small_font: pg.font.Font,
        pid: int,
        sx: int,
        sy: int,
        sw: int,
        sh: int,
        bar_h: int,
    ) -> None:
        """Conteúdo do slot quando nenhum jogador está conectado."""
        # Clip para garantir que nenhum texto vaze além do slot
        screen.set_clip(pg.Rect(sx + 2, sy, sw - 4, sh))

        empty = label_font.render("SLOT  VAZIO", True, (70, 70, 80))
        screen.blit(empty, (sx + sw // 2 - empty.get_width() // 2, sy + bar_h + 14))

        # Dicas específicas por slot
        if pid == 1:
            hints = ['Pressione  "1"', "para entrar"]
        elif pid == 2:
            hints = ['Pressione  "2"', "para entrar"]
        else:
            hints = ["Conecte um controle", "e aperte um botao"]

        hy = sy + bar_h + 42
        for hint_line in hints:
            hs = small_font.render(hint_line, True, (90, 90, 100))
            screen.blit(hs, (sx + sw // 2 - hs.get_width() // 2, hy))
            hy += hs.get_height() + 3

        screen.set_clip(None)  # Remove o clip após o slot


    def _draw_footer(
        self,
        screen: pg.Surface,
        font: pg.font.Font,
        label_font: pg.font.Font,
        active_ids: list[int],
    ) -> None:
        cx = C.WIDTH // 2
        footer_y = C.HEIGHT - 72

        pg.draw.line(screen, (50, 50, 60), (cx - 280, footer_y - 10), (cx + 280, footer_y - 10), 1)

        if not active_ids:
            msg = 'Pressione  "1" (P1)  ou  "2" (P2)  ou botao do controle para entrar'
            s = label_font.render(msg, True, (150, 150, 160))
            screen.blit(s, (cx - s.get_width() // 2, footer_y))
        elif not self._starting:
            enter_msg = "ENTER  para iniciar  |  outros jogadores ainda podem entrar"
            s = font.render(enter_msg, True, (200, 220, 200))
            screen.blit(s, (cx - s.get_width() // 2, footer_y))

        esc_s = label_font.render("ESC para sair", True, (70, 70, 80))
        screen.blit(esc_s, (cx - esc_s.get_width() // 2, footer_y + 30))

    def _draw_countdown(self, screen: pg.Surface, big_font: pg.font.Font) -> None:
        """Sobreposição de contagem regressiva antes de iniciar."""
        cx, cy = C.WIDTH // 2, C.HEIGHT // 2
        secs_left = max(0, math.ceil(self._countdown))

        # Fundo escurecido
        overlay = pg.Surface((C.WIDTH, C.HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        # Número pulsante
        pulse = 0.7 + 0.3 * math.sin(self.lobby_time * 6.0)
        num_color = (
            int(255 * pulse),
            int(220 * pulse),
            int(60 * pulse),
        )
        num_surf = big_font.render(str(secs_left), True, num_color)
        screen.blit(num_surf, (cx - num_surf.get_width() // 2, cy - num_surf.get_height() // 2 - 20))

        start_font = pg.font.SysFont(C.FONT_NAME, 22)
        msg = start_font.render("INICIANDO...", True, (200, 200, 200))
        screen.blit(msg, (cx - msg.get_width() // 2, cy + num_surf.get_height() // 2))

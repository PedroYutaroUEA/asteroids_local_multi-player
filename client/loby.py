import pygame as pg
from core import config as C
from client.input.manager import InputManager


class Lobby:
    """Gerencia o estado de entrada de jogadores e a interface de pré-jogo."""

    def __init__(self, input_manager: InputManager):
        self.input_mgr = input_manager
        # Cores para o feedback visual no lobby
        self.p_colors = getattr(
            C,
            "PLAYER_COLORS",
            {1: (255, 255, 255), 2: (0, 255, 0), 3: (0, 255, 255), 4: (255, 255, 0)},
        )

    def update(self, events: list[pg.event.Event]) -> bool:
        """
        Processa entradas do lobby.
        Retorna True quando o jogo deve começar.
        """
        self.input_mgr.handle_lobby_events(events)

        for event in events:
            if event.type == pg.KEYDOWN:
                # Se houver jogadores e alguém apertar ENTER, inicia
                if event.key == pg.K_RETURN and self.input_mgr.get_player_ids():
                    return True
        return False

    def draw(self, screen: pg.Surface, font: pg.font.Font, big_font: pg.font.Font):
        """Renderiza a interface do Lobby."""
        screen.fill((0, 0, 0))

        # Título
        title = big_font.render("LOBBY MULTIPLAYER", True, (255, 255, 255))
        screen.blit(title, (C.WIDTH // 2 - title.get_width() // 2, 50))

        active_ids = self.input_mgr.get_player_ids()
        # Status dos 4 Slots
        for i in range(1, C.MAX_PLAYERS + 1):
            spacing = 200
            x = (C.WIDTH // 2 - 400) + (i - 1) * spacing
            y = 250

            is_active = i in active_ids
            color = self.p_colors[i] if is_active else (60, 60, 60)

            # Moldura do Slot
            pg.draw.rect(screen, color, (x, y, 160, 120), 2 if is_active else 1)

            # Texto do Jogador
            p_txt = font.render(f"PLAYER {i}", True, color)
            screen.blit(p_txt, (x + 80 - p_txt.get_width() // 2, y + 20))

            status = "PRONTO!" if is_active else "AGUARDANDO..."
            s_txt = font.render(status, True, color)
            screen.blit(s_txt, (x + 80 - s_txt.get_width() // 2, y + 70))

        # Rodapé de instruções
        instruction = (
            "PRESSIONE ENTER PARA INICIAR"
            if active_ids
            else "PRESSIONE '1', '2' OU BOTÃO DO CONTROLE"
        )
        hint = font.render(instruction, True, (200, 200, 200))
        screen.blit(hint, (C.WIDTH // 2 - hint.get_width() // 2, 450))

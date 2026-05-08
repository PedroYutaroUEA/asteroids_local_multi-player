import pygame as pg
from client.input.device import InputDevice
from core.commands import PlayerCommand


class KeyboardDevice(InputDevice):
    """Mapeia teclas físicas para nomes de atributos do PlayerCommand."""

    def __init__(self, key_map: dict[int, str]):
        super().__init__()
        # key_map ex: {pg.K_w: "thrust", pg.K_SPACE: "shoot"}
        self.key_map = key_map

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type == pg.KEYDOWN:
            action = self.key_map.get(event.key)
            if action in self.trigger_states:
                self.trigger_states[action] = True

    def build_command(self) -> PlayerCommand:
        pressed = pg.key.get_pressed()
        cmd_data = {}

        # 1. Processa inputs contínuos (Polling)
        for key_code, action in self.key_map.items():
            if not isinstance(key_code, int):
                continue
            if action not in self.trigger_states:
                cmd_data[action] = bool(pressed[key_code])

        # 2. Processa inputs discretos (Eventos salvos)
        for action, was_pressed in self.trigger_states.items():
            cmd_data[action] = was_pressed
            self.trigger_states[action] = False  # Consome o evento

        # Retorna a instância da Dataclass do Core preenchida
        return PlayerCommand(**cmd_data)

from client.input.device import InputDevice
from client.input.profiles import JOYSTICK_XBOX_STYLE, JOYSTICK_GENERIC
from client.input.joystick import JoystickDevice
from core.commands import PlayerCommand
import pygame as pg


class InputManager:
    """Gerencia múltiplos dispositivos e mapeia para IDs de jogadores."""

    def __init__(self):
        self.devices: dict[int, InputDevice] = {}

    def add_player(self, player_id: int, device: InputDevice):
        self.devices[player_id] = device

    def handle_events(self, events: list[pg.event.Event]):
        for event in events:
            for device in self.devices.values():
                device.handle_event(event)

    def get_all_commands(self) -> dict[int, PlayerCommand]:
        """Retorna o dicionário que o World.update espera."""
        return {pid: dev.build_command() for pid, dev in self.devices.items()}

    def auto_assign_joystick(self, player_id: int, joystick: pg.joystick.Joystick):
        name = joystick.get_name().lower()

        # Lógica de seleção automática de perfil
        if "xbox" in name or "x-input" in name:
            profile = JOYSTICK_XBOX_STYLE
        else:
            profile = JOYSTICK_GENERIC

        print(f"Assigning {name} to Player {player_id} using generic profile.")
        self.devices[player_id] = JoystickDevice(joystick, profile)

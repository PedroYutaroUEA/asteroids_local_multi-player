from client.input.device import InputDevice
from client.input.joystick import JoystickDevice
from client.input.keyboard import KeyboardDevice

from client.input.profiles import (
    JOYSTICK_XBOX,
    KEYBOARD_PROFILES,
    JOYSTICK_GENERIC,
)
from core.commands import PlayerCommand
from core import config as C
import pygame as pg


class InputManager:
    """Gerencia múltiplos dispositivos e mapeia para IDs de jogadores."""

    def __init__(self):
        self.devices: dict[C.PlayerId, InputDevice] = {}
        self.active_joystick_ids = set()

    def _get_next_available_id(self) -> int:
        """Encontra o menor ID de 1 a 4 que não está em uso."""
        for i in range(1, C.MAX_PLAYERS + 1):
            if i not in self.devices:
                return i
        return None

    def handle_lobby_events(self, events: list[pg.event.Event]):
        """Detecta novos jogadores pressionando teclas de entrada."""
        for event in events:
            # Entrada por Teclado
            if event.type == pg.KEYDOWN:
                for profile_name, mapping in KEYBOARD_PROFILES.items():
                    if event.key == mapping["join_key"]:
                        pid = int(profile_name[-1])  # P1 -> 1, P2 -> 2
                        if pid not in self.devices:
                            self.devices[pid] = KeyboardDevice(mapping)

            # Entrada por Joystick
            if event.type == pg.JOYBUTTONDOWN:
                if event.joy not in self.active_joystick_ids:
                    pid = self._get_next_available_id()
                    if pid:
                        joy = pg.joystick.Joystick(event.joy)
                        self.assign_joystick_profile(pid, joy)
                        self.active_joystick_ids.add(event.joy)

    def assign_joystick_profile(self, player_id: int, joystick: pg.joystick.Joystick):
        """Identifica o modelo do controle e atribui o mapeamento correto."""
        name = joystick.get_name().lower()
        if "xbox" in name or "x-input" in name:
            profile = JOYSTICK_XBOX
        else:
            profile = JOYSTICK_GENERIC

        print(f"Assigning {name} to Player {player_id} using generic profile.")
        self.devices[player_id] = JoystickDevice(joystick, profile)

    def handle_gameplay_events(self, events: list[pg.event.Event]):
        """Roteia eventos discretos para cada dispositivo ativo."""
        for event in events:
            for device in self.devices.values():
                device.handle_event(event)

    def get_player_ids(self) -> list[C.PlayerId]:
        """Retorna os IDs de todos os jogadores pelos seus devices"""
        return list(self.devices.keys())

    def get_all_commands(self) -> dict[C.PlayerId, PlayerCommand]:
        """Gera o dicionário de comandos para o World.update."""
        return {pid: dev.build_command() for pid, dev in self.devices.items()}

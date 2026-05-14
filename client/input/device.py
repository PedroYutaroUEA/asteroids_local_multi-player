import pygame as pg
from abc import ABC, abstractmethod
from core.commands import PlayerCommand


class InputDevice(ABC):
    """Interface abstrata para qualquer dispositivo de entrada."""

    def __init__(self):
        self.trigger_states = {"shoot": False, "hyperspace": False, "time_bomb": False}

    @abstractmethod
    def handle_event(self, event: pg.event.Event) -> None:
        """Processa eventos discretos (cliques únicos)."""

    @abstractmethod
    def build_command(self) -> PlayerCommand:
        """Lê estados contínuos e retorna o comando final."""

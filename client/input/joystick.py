import pygame as pg
from client.input.device import InputDevice
from core.commands import PlayerCommand


class JoystickDevice(InputDevice):
    def __init__(self, joystick: pg.joystick.Joystick, profile: dict):
        super().__init__()
        self.joy = joystick
        self.profile = profile
        self.deadzone = 0.2
        self.held_states = {"special": False}

    def handle_event(self, event: pg.event.Event) -> None:
        if event.type == pg.JOYBUTTONDOWN and event.joy == self.joy.get_id():
            action = self.profile["buttons"].get(event.button)
            if action in self.trigger_states:
                self.trigger_states[action] = True
            elif action in self.held_states:
                self.held_states[action] = True

        elif event.type == pg.JOYBUTTONUP and event.joy == self.joy.get_id():
            action = self.profile["buttons"].get(event.button)
            if action in self.held_states:
                self.held_states[action] = False

    def build_command(self) -> PlayerCommand:
        cmd_dict = {
            "rotate_left": False,
            "rotate_right": False,
            "thrust": False,
            "shoot": self.trigger_states["shoot"],
            "time_bomb": self.trigger_states["time_bomb"],
            "hyperspace": self.trigger_states["hyperspace"],
            "special": self.held_states["special"],
        }
        self.trigger_states["shoot"] = False
        self.trigger_states["time_bomb"] = False
        self.trigger_states["hyperspace"] = False

        # Processa Eixos
        for axis_id, mapping in self.profile["axes"].items():
            val = self.joy.get_axis(axis_id)
            if val < -self.deadzone and "neg" in mapping:
                cmd_dict[mapping["neg"]] = True
            if val > self.deadzone and "pos" in mapping:
                cmd_dict[mapping["pos"]] = True

        # Processa botões que podem ser segurados (ex: thrust no botão)
        for btn_id, action in self.profile["buttons"].items():
            if action == "thrust" and self.joy.get_button(btn_id):
                cmd_dict["thrust"] = True

        return PlayerCommand(**cmd_dict)

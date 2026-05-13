"""Game loop and scenes (menu, play, game over).

- World updates the simulation and generates events (strings) for Game.
- Game handles audio and screen transitions (low coupling).
"""

import sys
import random

import pygame as pg

from client.input.manager import InputManager
from client.loby import Lobby
from core import config as C
from core.scene import SceneState
from client.audio.pack import load_sounds
from client.audio.manager import AudioManager
from client.renderer import Renderer
from core.world import World


class Game:
    """Orchestrates input -> update -> draw."""

    def __init__(self) -> None:
        pg.mixer.pre_init(
            C.AUDIO_FREQUENCY, C.AUDIO_SIZE, C.AUDIO_CHANNELS, C.AUDIO_BUFFER
        )
        pg.init()
        pg.joystick.init()
        pg.mixer.init()

        self.screen = pg.display.set_mode((C.WIDTH, C.HEIGHT))
        pg.display.set_caption("Asteroids Multiplayer Local")

        self.clock = pg.time.Clock()
        self.running = True
        self.menu_time: float = 0.0  # acumulador para animações do menu
        self.gameover_time: float = 0.0  # acumulador para fade-in do game over

        self.font = pg.font.SysFont(C.FONT_NAME, C.FONT_SIZE_SMALL)
        self.big = pg.font.SysFont(C.FONT_NAME, C.FONT_SIZE_LARGE)
        self.renderer = Renderer(
            self.screen,
            config=C,
            fonts={"font": self.font, "big": self.big},
        )

        self.input_manager = InputManager()
        self.lobby = Lobby(self.input_manager)
        self.world = None
        self.scene = SceneState.MENU
        self._pending_events: list = []

        # Starfield estático — seed fixa garante sempre as mesmas estrelas
        rng = random.Random(42)
        self.stars: list[tuple[int, int, int]] = [
            (rng.randint(0, C.WIDTH), rng.randint(0, C.HEIGHT), rng.randint(1, 3))
            for _ in range(120)
        ]

        self.sounds = load_sounds(C.SOUND_PATH)
        self.audio = AudioManager(self.sounds)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(C.FPS) / 1000.0
            if self.scene == SceneState.MENU:
                self.menu_time += dt
            elif self.scene == SceneState.GAME_OVER:
                self.gameover_time += dt
            self._handle_events()
            self._update(dt)
            self._draw()

        pg.quit()

    def _handle_events(self) -> None:
        self._pending_events = pg.event.get()
        for event in self._pending_events:
            if event.type == pg.QUIT or (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ):
                self._quit()

            if self.scene == SceneState.MENU:
                if event.type == pg.KEYDOWN:
                    self.lobby.reset()
                    self.scene = SceneState.LOBBY
                    self._pending_events = (
                        []
                    )  # evita que a tecla vaze para lobby.update()

            elif self.scene == SceneState.GAME_OVER:
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    self.world.reset()
                    self.lobby.reset()
                    self.scene = SceneState.LOBBY
                    self._pending_events = (
                        []
                    )  # evita que o ENTER vaze para lobby.update()

            elif self.scene == SceneState.PLAY:
                self.input_manager.handle_gameplay_events([event])

    def _update(self, dt: float) -> None:
        # Lobby: processado uma vez por frame com dt para o countdown
        if self.scene == SceneState.LOBBY:
            if self.lobby.update(self._pending_events, dt):
                self.world = World(self.input_manager.get_player_ids())
                self.scene = SceneState.PLAY
            return

        if self.scene != SceneState.PLAY:
            return

        commands = self.input_manager.get_all_commands()
        self.world.update(dt, commands)

        if self.world.game_over:
            self.audio.stop_all()
            self.gameover_time = 0.0
            self.scene = SceneState.GAME_OVER
            return

        any_thrust = any(
            cmd.thrust
            and self.world.ships.get(pid, None)
            and self.world.ships[pid].alive()
            for pid, cmd in commands.items()
        )
        self.audio.update_thrust(any_thrust)
        self.audio.update_ufo_siren(list(self.world.ufos))
        self.audio.play_events(self.world.events)

    def _draw(self) -> None:
        self.renderer.clear()
        if self.scene == SceneState.MENU:
            self.renderer.draw_menu(self.stars, self.menu_time)
        elif self.scene == SceneState.LOBBY:
            self.lobby.draw(self.screen, self.font, self.big)
        elif self.scene == SceneState.GAME_OVER:
            self.renderer.draw_game_over(
                scores=self.world.scores,
                lives=self.world.lives,
                wave=self.world.wave,
                shots_fired=self.world.shots_fired,
                power_use_count=self.world.power_use_count,
                elapsed=self.gameover_time,
            )
        elif self.scene == SceneState.PLAY:
            self.renderer.draw_world(self.world)
            self.renderer.draw_hud(
                self.world.scores,
                self.lives_copy(),
                self.world.wave,
                self.scene,
                self.world.ships,
            )
        pg.display.flip()

    def lives_copy(self):
        return self.world.lives if self.world else {}

    def _quit(self) -> None:
        self.running = False
        pg.quit()
        sys.exit(0)

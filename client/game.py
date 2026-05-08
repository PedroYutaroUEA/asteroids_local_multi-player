"""Game loop and scenes (menu, play, game over).

- InputMapper converts keyboard input into PlayerCommand.
- World updates the simulation and generates events (strings) for Game.
- Game handles audio and screen transitions (low coupling).
"""

import sys

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
        pg.mixer.init()

        self.screen = pg.display.set_mode((C.WIDTH, C.HEIGHT))
        pg.display.set_caption("Asteroids Multiplayer Local")

        self.clock = pg.time.Clock()
        self.running = True

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

        self.sounds = load_sounds(C.SOUND_PATH)
        self.audio = AudioManager(self.sounds)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(C.FPS) / 1000.0
            self._handle_events()
            self._update(dt)
            self._draw()

        pg.quit()

    def _handle_events(self) -> None:
        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT or (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ):
                self._quit()

            if self.scene == SceneState.MENU:
                if event.type == pg.KEYDOWN:
                    self.scene = SceneState.LOBBY

            elif self.scene == SceneState.LOBBY:
                # O Lobby decide quando o jogo começa
                if self.lobby.update([event]):
                    # INJEÇÃO DE DEPENDÊNCIA: Criamos o mundo com os IDs reais
                    self.world = World(self.input_manager.get_player_ids())
                    self.scene = SceneState.PLAY

            elif self.scene == SceneState.GAME_OVER:
                if event.type == pg.KEYDOWN:
                    self.world.reset()
                    self.scene = SceneState.LOBBY

            elif self.scene == SceneState.PLAY:
                self.input_manager.handle_gameplay_events([event])

    def _update(self, dt: float) -> None:
        if self.scene != SceneState.PLAY:
            return

        commands = self.input_manager.get_all_commands()
        self.world.update(dt, commands)

        if self.world.game_over:
            self.audio.stop_all()
            self.scene = SceneState.GAME_OVER
            return

        any_thrust = any(c.thrust for c in commands.values())
        self.audio.update_thrust(any_thrust)
        self.audio.update_ufo_siren(list(self.world.ufos))
        self.audio.play_events(self.world.events)

    def _draw(self) -> None:
        self.renderer.clear()
        if self.scene == SceneState.MENU:
            self.renderer.draw_menu()
        elif self.scene == SceneState.LOBBY:
            self.lobby.draw(self.screen, self.font, self.big)
        elif self.scene == SceneState.GAME_OVER:
            self.renderer.draw_game_over()
        elif self.scene == SceneState.PLAY:
            self.renderer.draw_world(self.world)
            self.renderer.draw_hud(
                self.world.scores, self.lives_copy(), self.world.wave, self.scene
            )
        pg.display.flip()

    def lives_copy(self):
        return self.world.lives if self.world else {}

    def _quit(self) -> None:
        self.running = False
        pg.quit()
        sys.exit(0)

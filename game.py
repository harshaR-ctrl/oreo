"""
game.py — Central Game Manager.

Owns the main loop, manages state transitions, and coordinates
the renderer, input handler, and all game systems.
"""

from __future__ import annotations
import pygame
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, GAME_TITLE,
    SOUND_ENABLED, SAMPLE_RATE,
)
from input_handler import InputHandler
from renderer import Renderer
from physics import PhysicsEngine
from camera import Camera
from particles import ParticleSystem
from sounds import SoundManager
from states import MenuState, PlayingState, GameOverState


class Game:
    """Central game manager — runs the main loop and state machine."""

    def __init__(self) -> None:
        pygame.init()
        if SOUND_ENABLED:
            try:
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
            except Exception:
                pass

        self.screen: pygame.Surface = pygame.display.set_mode(
            (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        pygame.display.set_caption(GAME_TITLE)
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.running: bool = True
        self.time: float = 0.0

        # ── Core systems ─────────────────────────────────────────
        self.input: InputHandler = InputHandler()
        self.renderer: Renderer = Renderer(self.screen)
        self.physics: PhysicsEngine = PhysicsEngine()
        self.camera: Camera = Camera()
        self.particles: ParticleSystem = ParticleSystem()
        self.sound: SoundManager = SoundManager()

        # ── States ───────────────────────────────────────────────
        self.menu_state: MenuState = MenuState(self.particles)
        self.playing_state: PlayingState = PlayingState(
            self.physics, self.camera, self.particles, self.sound,
        )
        self.gameover_state: GameOverState = GameOverState(
            self.particles, self.sound,
        )

        self.current_state_name: str = "menu"
        self.current_state = self.menu_state
        self.current_state.enter()

    def _transition(self, new_state_name: str) -> None:
        """Switch to a new game state."""
        self.current_state.exit()

        if new_state_name == "menu":
            self.current_state = self.menu_state
        elif new_state_name == "playing":
            self.current_state = self.playing_state
        elif new_state_name == "gameover":
            # Pass results to game over screen
            self.gameover_state.set_results(
                self.playing_state.score,
                self.playing_state.level_number,
            )
            self.current_state = self.gameover_state

        self.current_state_name = new_state_name
        self.current_state.enter()

    def run(self) -> None:
        """Main game loop."""
        while self.running:
            # ── Timing ───────────────────────────────────────────
            dt: float = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Cap dt to prevent spiral of death
            self.time += dt

            # ── Input ────────────────────────────────────────────
            self.input.process_events()
            if self.input.quit_requested:
                self.running = False
                break

            # ── Update ───────────────────────────────────────────
            next_state = self.current_state.update(self.input, dt)
            if next_state is not None:
                self._transition(next_state)

            # ── Render ───────────────────────────────────────────
            cam_y = self.camera.y if self.current_state_name == "playing" else 0
            surface = self.renderer.begin_frame(cam_y, self.time)
            self.current_state.render(surface, self.time)
            self.renderer.end_frame()

        pygame.quit()

"""
game.py — Central Game Manager.

Owns the main loop, manages state transitions, and coordinates
the renderer, input handler, and all game systems. Supports
menu, difficulty, high scores, controls, playing, pause, and game over states.
"""

from __future__ import annotations
import pygame
from settings import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, GAME_TITLE,
    SOUND_ENABLED, SAMPLE_RATE, DEFAULT_DIFFICULTY,
)
from input_handler import InputHandler
from renderer import Renderer
from physics import PhysicsEngine
from camera import Camera
from particles import ParticleSystem
from sounds import SoundManager
from states import (
    MenuState, PlayingState, GameOverState,
    PauseState, DifficultySelectState, HighScoreState, ControlsState,
)


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

        # Set window icon (small Oreo-like circle)
        try:
            icon = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(icon, (35, 25, 20), (16, 16), 14)
            pygame.draw.circle(icon, (240, 230, 210), (16, 16), 10)
            pygame.draw.circle(icon, (35, 25, 20), (16, 16), 7)
            pygame.draw.circle(icon, (240, 230, 210), (16, 16), 2)
            pygame.display.set_icon(icon)
        except Exception:
            pass

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

        # ── Current difficulty ───────────────────────────────────
        self.difficulty: str = DEFAULT_DIFFICULTY

        # ── States ───────────────────────────────────────────────
        self.menu_state: MenuState = MenuState(self.particles, self.sound)
        self.difficulty_state: DifficultySelectState = DifficultySelectState(
            self.particles, self.sound,
        )
        self.highscore_state: HighScoreState = HighScoreState(
            self.particles, self.sound,
        )
        self.controls_state: ControlsState = ControlsState(
            self.particles, self.sound,
        )
        self.playing_state: PlayingState = PlayingState(
            self.physics, self.camera, self.particles, self.sound,
        )
        self.pause_state: PauseState = PauseState(
            self.particles, self.sound,
        )
        self.gameover_state: GameOverState = GameOverState(
            self.particles, self.sound,
        )

        self.current_state_name: str = "menu"
        self.current_state = self.menu_state
        self.current_state.enter()

    def _transition(self, new_state_name: str) -> None:
        """Switch to a new game state."""
        # For resume/pause, don't exit the playing state
        if new_state_name not in ("resume", "pause"):
            self.current_state.exit()

        if new_state_name == "menu":
            # Sync difficulty between states
            self.menu_state.difficulty_name = self.difficulty
            self.current_state = self.menu_state
        elif new_state_name == "difficulty":
            self.difficulty_state.chosen_difficulty = self.difficulty
            self.current_state = self.difficulty_state
        elif new_state_name == "highscores":
            self.current_state = self.highscore_state
        elif new_state_name == "controls":
            self.current_state = self.controls_state
        elif new_state_name == "playing":
            self.playing_state.difficulty_name = self.difficulty
            self.current_state = self.playing_state
        elif new_state_name == "pause":
            # Overlay pause on top of playing
            self.current_state = self.pause_state
        elif new_state_name == "resume":
            # Go back to playing without resetting — no enter() call
            self.current_state = self.playing_state
            self.current_state_name = "playing"
            self.sound.start_music()
            return
        elif new_state_name == "restart":
            # Restart the game
            self.playing_state.difficulty_name = self.difficulty
            self.current_state = self.playing_state
            new_state_name = "playing"
        elif new_state_name == "gameover":
            # Pass results to game over screen
            self.gameover_state.set_results(
                self.playing_state.score,
                int(self.playing_state.max_distance / 10),
                enemies=self.playing_state.enemies_killed,
                coins=self.playing_state.coins_collected,
                time_survived=self.playing_state.time_survived,
                best_combo=self.playing_state.best_combo,
                difficulty=self.difficulty,
            )
            self.current_state = self.gameover_state
        elif new_state_name == "quit":
            self.running = False
            return

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

            # Handle difficulty state returning — update our stored difficulty
            if self.current_state_name == "difficulty" and next_state == "menu":
                self.difficulty = self.difficulty_state.chosen_difficulty

            if next_state is not None:
                self._transition(next_state)

            # ── Render ───────────────────────────────────────────
            is_playing = self.current_state_name in ("playing", "pause")
            cam_x = self.camera.x if is_playing else 0
            cam_y = self.camera.y if is_playing else 0
            surface = self.renderer.begin_frame(cam_x, cam_y, self.time)

            # For pause, render the playing state underneath
            if self.current_state_name == "pause":
                self.playing_state.render(surface, self.time)

            self.current_state.render(surface, self.time)
            self.renderer.end_frame()

        pygame.quit()

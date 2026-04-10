"""
input_handler.py — Decoupled input abstraction.

Separates raw Pygame key events from game logic. Provides semantic
methods like move_direction(), jump_pressed(), dash_pressed() instead
of exposing raw key codes to the game systems.
"""

from __future__ import annotations
import pygame


class InputHandler:
    """Processes raw Pygame events into semantic game actions."""

    def __init__(self) -> None:
        self._keys_held: set[int] = set()
        self._keys_just_pressed: set[int] = set()
        self._keys_just_released: set[int] = set()
        self.quit_requested: bool = False

    # ── Per-frame update ─────────────────────────────────────────────

    def process_events(self) -> None:
        """Call once per frame BEFORE game logic. Processes all pending events."""
        self._keys_just_pressed.clear()
        self._keys_just_released.clear()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True
            elif event.type == pygame.KEYDOWN:
                self._keys_held.add(event.key)
                self._keys_just_pressed.add(event.key)
            elif event.type == pygame.KEYUP:
                self._keys_held.discard(event.key)
                self._keys_just_released.add(event.key)

    # ── Semantic queries ─────────────────────────────────────────────

    def move_direction(self) -> float:
        """Returns -1.0 (left), 0.0 (neutral), or 1.0 (right)."""
        left = self._is_held(pygame.K_LEFT) or self._is_held(pygame.K_a)
        right = self._is_held(pygame.K_RIGHT) or self._is_held(pygame.K_d)
        if left and right:
            return 0.0
        if left:
            return -1.0
        if right:
            return 1.0
        return 0.0

    def jump_pressed(self) -> bool:
        """True on the frame spacebar or W or Up is first pressed."""
        return (
            self._just_pressed(pygame.K_SPACE)
            or self._just_pressed(pygame.K_w)
            or self._just_pressed(pygame.K_UP)
        )

    def jump_held(self) -> bool:
        """True while spacebar or W or Up is held down."""
        return (
            self._is_held(pygame.K_SPACE)
            or self._is_held(pygame.K_w)
            or self._is_held(pygame.K_UP)
        )

    def jump_released(self) -> bool:
        """True on the frame spacebar or W or Up is released."""
        return (
            self._just_released(pygame.K_SPACE)
            or self._just_released(pygame.K_w)
            or self._just_released(pygame.K_UP)
        )

    def dash_pressed(self) -> bool:
        """True on the frame Shift or X is first pressed."""
        return (
            self._just_pressed(pygame.K_LSHIFT)
            or self._just_pressed(pygame.K_RSHIFT)
            or self._just_pressed(pygame.K_x)
        )

    def restart_pressed(self) -> bool:
        """True when R is pressed (for restarting)."""
        return self._just_pressed(pygame.K_r)

    def confirm_pressed(self) -> bool:
        """True when Space or Enter is pressed (for menus)."""
        return (
            self._just_pressed(pygame.K_SPACE)
            or self._just_pressed(pygame.K_RETURN)
        )

    def up_direction(self) -> float:
        """Returns -1.0 (up) or 1.0 (down) or 0.0 for vertical aim during dash."""
        up = self._is_held(pygame.K_UP) or self._is_held(pygame.K_w)
        down = self._is_held(pygame.K_DOWN) or self._is_held(pygame.K_s)
        if up and down:
            return 0.0
        if up:
            return -1.0
        if down:
            return 1.0
        return 0.0

    def shoot_pressed(self) -> bool:
        """True on the frame F or Z is first pressed (for shooting)."""
        return (
            self._just_pressed(pygame.K_f)
            or self._just_pressed(pygame.K_z)
        )

    def shoot_held(self) -> bool:
        """True while F or Z is held down (for continuous laser)."""
        return self._is_held(pygame.K_f) or self._is_held(pygame.K_z)

    def weapon_switch_pressed(self) -> bool:
        """True on the frame Q is first pressed (cycle weapons)."""
        return self._just_pressed(pygame.K_q)

    # ── Raw key helpers ──────────────────────────────────────────────

    def _is_held(self, key: int) -> bool:
        return key in self._keys_held

    def _just_pressed(self, key: int) -> bool:
        return key in self._keys_just_pressed

    def _just_released(self, key: int) -> bool:
        return key in self._keys_just_released

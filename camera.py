"""
camera.py — Camera system with smooth follow and screen shake.

Uses lerp-based tracking for buttery smooth camera movement.
Screen shake uses a "trauma" model: trauma decays over time,
and the actual shake intensity = trauma² * max_offset.
"""

from __future__ import annotations
import random
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    CAMERA_LERP_SPEED, SCREEN_SHAKE_DECAY, SCREEN_SHAKE_MAX_OFFSET,
)


class Camera:
    """Smooth-following camera with screen shake support."""

    def __init__(self) -> None:
        self.offset: pygame.Vector2 = pygame.Vector2(0, 0)
        self.target: pygame.Vector2 = pygame.Vector2(0, 0)
        self.trauma: float = 0.0  # 0.0 to 1.0
        self.shake_offset: pygame.Vector2 = pygame.Vector2(0, 0)

    def set_target(self, target_x: float, target_y: float) -> None:
        """Set the point the camera should follow (usually player center)."""
        self.target.x = target_x - INTERNAL_WIDTH / 2
        self.target.y = target_y - INTERNAL_HEIGHT / 2

    def update(self, dt: float) -> None:
        """Smoothly interpolate toward target and apply shake."""
        # Lerp toward target
        lerp = 1.0 - (1.0 - CAMERA_LERP_SPEED) ** (dt * 60)
        self.offset.x += (self.target.x - self.offset.x) * lerp
        self.offset.y += (self.target.y - self.offset.y) * lerp

        # Decay trauma
        if self.trauma > 0:
            self.trauma *= SCREEN_SHAKE_DECAY
            if self.trauma < 0.01:
                self.trauma = 0.0

            # Shake = trauma² * max_offset * random direction
            intensity = self.trauma * self.trauma * SCREEN_SHAKE_MAX_OFFSET
            self.shake_offset.x = random.uniform(-intensity, intensity)
            self.shake_offset.y = random.uniform(-intensity, intensity)
        else:
            self.shake_offset.x = 0.0
            self.shake_offset.y = 0.0

    def add_trauma(self, amount: float) -> None:
        """Add screen shake trauma (clamped to 1.0)."""
        self.trauma = min(1.0, self.trauma + amount)

    @property
    def x(self) -> float:
        """Final camera X offset including shake."""
        return self.offset.x + self.shake_offset.x

    @property
    def y(self) -> float:
        """Final camera Y offset including shake."""
        return self.offset.y + self.shake_offset.y

    def reset(self, x: float = 0.0, y: float = 0.0) -> None:
        """Snap camera to a position without interpolation."""
        self.offset.x = x - INTERNAL_WIDTH / 2
        self.offset.y = y - INTERNAL_HEIGHT / 2
        self.target.x = self.offset.x
        self.target.y = self.offset.y
        self.trauma = 0.0
        self.shake_offset.x = 0.0
        self.shake_offset.y = 0.0

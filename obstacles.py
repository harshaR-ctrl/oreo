"""
obstacles.py — Static obstacle blocks.

Simple impassable blocks placed on platforms. Block movement
for the player, enemies, and projectiles using rect.colliderect.
"""

from __future__ import annotations
import pygame
from settings import (
    OBSTACLE_WIDTH, OBSTACLE_HEIGHT,
    COL_OBSTACLE, COL_OBSTACLE_EDGE,
)


class Obstacle(pygame.sprite.Sprite):
    """A static rectangular obstacle that blocks movement."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (OBSTACLE_WIDTH, OBSTACLE_HEIGHT), pygame.SRCALPHA,
        )
        self.rect: pygame.Rect = pygame.Rect(x, y, OBSTACLE_WIDTH, OBSTACLE_HEIGHT)
        self.active: bool = True

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw a metallic-looking obstacle block."""
        sx = int(self.rect.x - cam_x)
        sy = int(self.rect.y - cam_y)

        # Main body
        pygame.draw.rect(
            surface, COL_OBSTACLE,
            (sx, sy, OBSTACLE_WIDTH, OBSTACLE_HEIGHT),
        )
        # Top edge highlight
        pygame.draw.rect(
            surface, COL_OBSTACLE_EDGE,
            (sx, sy, OBSTACLE_WIDTH, 1),
        )
        # Left edge highlight
        pygame.draw.rect(
            surface, COL_OBSTACLE_EDGE,
            (sx, sy, 1, OBSTACLE_HEIGHT),
        )
        # Bottom-right shadow
        pygame.draw.rect(
            surface, (40, 42, 55),
            (sx, sy + OBSTACLE_HEIGHT - 1, OBSTACLE_WIDTH, 1),
        )
        pygame.draw.rect(
            surface, (40, 42, 55),
            (sx + OBSTACLE_WIDTH - 1, sy, 1, OBSTACLE_HEIGHT),
        )

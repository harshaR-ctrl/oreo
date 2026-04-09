"""
renderer.py — Resolution-independent rendering pipeline.

Draws everything to a small internal surface (400×300), then scales
up to the window size (800×600) for a clean pixel aesthetic.
Handles background gradients, parallax stars, and the HUD overlay.
"""

from __future__ import annotations
import random
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT,
    COL_BG, COL_BG_GRADIENT_TOP, COL_BG_GRADIENT_BOT,
)


class StarField:
    """Simple parallax starfield for the background."""

    def __init__(self, count: int = 60) -> None:
        self.stars: list[tuple[float, float, float, int]] = []
        for _ in range(count):
            x = random.uniform(0, INTERNAL_WIDTH)
            y = random.uniform(0, INTERNAL_HEIGHT * 3)
            depth = random.uniform(0.1, 0.5)
            brightness = random.randint(30, 90)
            self.stars.append((x, y, depth, brightness))

    def draw(
        self, surface: pygame.Surface, cam_y: float, time: float
    ) -> None:
        """Draw parallax stars that twinkle subtly."""
        for sx, sy, depth, brightness in self.stars:
            px = int(sx)
            py = int(sy - cam_y * depth) % (INTERNAL_HEIGHT + 100) - 50
            # Slight twinkle
            twinkle = int(brightness + 20 * ((hash((sx, sy)) + time * 2) % 1))
            twinkle = max(20, min(100, twinkle))
            color = (twinkle, twinkle, twinkle + 15)
            surface.set_at((px % INTERNAL_WIDTH, py % INTERNAL_HEIGHT), color)


class Renderer:
    """Manages the rendering pipeline with resolution independence."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self.internal_surface: pygame.Surface = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT)
        )
        self.starfield: StarField = StarField(80)
        self._bg_surface: pygame.Surface = self._create_gradient()

    def _create_gradient(self) -> pygame.Surface:
        """Create a cached vertical gradient background."""
        surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        for y in range(INTERNAL_HEIGHT):
            t = y / INTERNAL_HEIGHT
            r = int(COL_BG_GRADIENT_TOP[0] + (COL_BG_GRADIENT_BOT[0] - COL_BG_GRADIENT_TOP[0]) * t)
            g = int(COL_BG_GRADIENT_TOP[1] + (COL_BG_GRADIENT_BOT[1] - COL_BG_GRADIENT_TOP[1]) * t)
            b = int(COL_BG_GRADIENT_TOP[2] + (COL_BG_GRADIENT_BOT[2] - COL_BG_GRADIENT_TOP[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (INTERNAL_WIDTH, y))
        return surf

    def begin_frame(self, cam_y: float, time: float) -> pygame.Surface:
        """Clear the internal surface with background. Returns it for drawing."""
        self.internal_surface.blit(self._bg_surface, (0, 0))
        self.starfield.draw(self.internal_surface, cam_y, time)
        return self.internal_surface

    def end_frame(self) -> None:
        """Scale internal surface to window and flip."""
        scaled = pygame.transform.scale(
            self.internal_surface, (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def get_surface(self) -> pygame.Surface:
        """Get the internal drawing surface."""
        return self.internal_surface

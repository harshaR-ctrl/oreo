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
    COL_TREE_L1, COL_TREE_L2, COL_TREE_L3
)


class ForestBackground:
    """Parallax forest background for the scene."""

    def __init__(self, count: int = 40) -> None:
        self.trees: list[tuple[float, float, float, tuple[int, int, int], float, float]] = []
        for _ in range(count):
            x = random.uniform(0, INTERNAL_WIDTH)
            # Trees are anchored lower on the screen
            speed_layer = random.choice([1, 2, 3])
            if speed_layer == 1:
                depth = 0.2
                color = COL_TREE_L1
                width = random.uniform(20, 30)
                height = random.uniform(100, 160)
            elif speed_layer == 2:
                depth = 0.4
                color = COL_TREE_L2
                width = random.uniform(25, 35)
                height = random.uniform(120, 180)
            else:
                depth = 0.6
                color = COL_TREE_L3
                width = random.uniform(30, 45)
                height = random.uniform(140, 200)
            
            # y offset anchor
            y = INTERNAL_HEIGHT

            self.trees.append((x, y, depth, color, width, height))

        # Sort by depth so back trees draw first
        self.trees.sort(key=lambda t: t[2])

    def draw(
        self, surface: pygame.Surface, cam_x: float, cam_y: float, time: float
    ) -> None:
        """Draw parallax trees that scroll with the camera."""
        for sx, sy, depth, color, width, height in self.trees:
            px = int(sx - cam_x * depth * 0.3) % (INTERNAL_WIDTH + 100) - 50
            # Camera mostly pans horizontally, slight vertical parallax
            py = int(sy - cam_y * depth * 0.2 + 20)
            
            # Draw tree trunk as an abstract rectangle
            rect = pygame.Rect(px - width//2, py - height, width, height)
            pygame.draw.rect(surface, color, rect)
            
            # Draw a simple triangle canopy on top
            points = [
                (px - width, py - height + 20),
                (px, py - height - width * 1.5),
                (px + width, py - height + 20)
            ]
            pygame.draw.polygon(surface, color, points)


class Renderer:
    """Manages the rendering pipeline with resolution independence."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self.internal_surface: pygame.Surface = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT)
        )
        self.forest: ForestBackground = ForestBackground(40)
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

    def begin_frame(self, cam_x: float, cam_y: float, time: float) -> pygame.Surface:
        """Clear the internal surface with background. Returns it for drawing."""
        self.internal_surface.blit(self._bg_surface, (0, 0))
        self.forest.draw(self.internal_surface, cam_x, cam_y, time)
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

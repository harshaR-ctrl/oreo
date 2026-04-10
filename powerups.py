"""
powerups.py — Collectible power-ups.

The Gun/Milk power-up enables the player's shooting ability.
Inherits from pygame.sprite.Sprite for group-based collision.
"""

from __future__ import annotations
import math
import random
import pygame
from settings import (
    COL_POWERUP_GUN, COL_POWERUP_GLOW,
)


class GunPowerUp(pygame.sprite.Sprite):
    """Collectible that enables player.can_shoot.

    Has a bobbing animation and glowing visual.
    """

    SIZE: int = 7

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (self.SIZE, self.SIZE), pygame.SRCALPHA,
        )
        self.x: float = float(x)
        self.y: float = float(y)
        self.rect: pygame.Rect = pygame.Rect(
            x - self.SIZE // 2, y - self.SIZE // 2,
            self.SIZE, self.SIZE,
        )
        self.collected: bool = False
        self.bob_timer: float = random.uniform(0, math.pi * 2)

    def update(self, dt: float) -> None:
        """Animate the bobbing motion."""
        if self.collected:
            return
        self.bob_timer += dt * 2.5
        bob_y = int(math.sin(self.bob_timer) * 3)
        self.rect.x = int(self.x) - self.SIZE // 2
        self.rect.y = int(self.y) - self.SIZE // 2 + bob_y

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw a glowing milk-bottle / gun icon."""
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)

        # Outer glow (pulsing)
        glow_alpha = int(3 + 2 * math.sin(self.bob_timer * 1.5))
        pygame.draw.circle(surface, COL_POWERUP_GLOW, (sx, sy), self.SIZE // 2 + glow_alpha)
        # Body (bottle shape using rect + top)
        bottle_w = self.SIZE - 2
        bottle_h = self.SIZE
        bx = sx - bottle_w // 2
        by = sy - bottle_h // 2
        pygame.draw.rect(surface, COL_POWERUP_GUN, (bx, by + 2, bottle_w, bottle_h - 2))
        # Neck
        neck_w = bottle_w // 2
        pygame.draw.rect(surface, COL_POWERUP_GUN, (sx - neck_w // 2, by, neck_w, 3))
        # Shine
        pygame.draw.rect(surface, (255, 255, 255), (bx + 1, by + 3, 1, 2))

"""
projectiles.py — Projectile and PlayerBullet sprites.

Enemy projectiles and player bullets, all using pygame.sprite.Sprite
for efficient group-based collision detection.
"""

from __future__ import annotations
import pygame
from settings import (
    PROJECTILE_SPEED, PLAYER_BULLET_SPEED,
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_ENEMY_PROJECTILE, COL_PLAYER_BULLET,
)


class Projectile(pygame.sprite.Sprite):
    """Enemy-fired projectile that travels in a fixed direction.

    Destroyed on collision with platforms, obstacles, or leaving the screen.
    """

    SIZE: int = 3

    def __init__(
        self, x: float, y: float, dx: float, dy: float, speed: float = 0,
    ) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (self.SIZE * 2, self.SIZE * 2), pygame.SRCALPHA,
        )
        self.position: pygame.Vector2 = pygame.Vector2(x, y)
        direction = pygame.Vector2(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()
        self.velocity: pygame.Vector2 = direction * (speed if speed > 0 else PROJECTILE_SPEED)
        self.rect: pygame.Rect = pygame.Rect(
            int(x) - self.SIZE, int(y) - self.SIZE,
            self.SIZE * 2, self.SIZE * 2,
        )
        self.alive: bool = True

    def update(self, platforms: list, obstacles, dt: float) -> None:
        """Move the projectile and check collisions."""
        if not self.alive:
            return

        self.position += self.velocity * dt
        self.rect.x = int(self.position.x) - self.SIZE
        self.rect.y = int(self.position.y) - self.SIZE

        # Off-screen check (generous margin)
        if (
            self.position.x < -100 or self.position.x > INTERNAL_WIDTH + 500
            or self.position.y < -500 or self.position.y > INTERNAL_HEIGHT + 500
        ):
            self.alive = False
            self.kill()
            return

        # Platform collision
        for plat in platforms:
            if not plat.active:
                continue
            if self.rect.colliderect(plat.rect):
                self.alive = False
                self.kill()
                return

        # Obstacle collision
        if obstacles:
            for obs in obstacles:
                if self.rect.colliderect(obs.rect):
                    self.alive = False
                    self.kill()
                    return

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw a small glowing projectile circle."""
        if not self.alive:
            return
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)
        # Outer glow
        pygame.draw.circle(surface, (180, 60, 60), (sx, sy), self.SIZE + 1)
        # Core
        pygame.draw.circle(surface, COL_ENEMY_PROJECTILE, (sx, sy), self.SIZE)


class PlayerBullet(pygame.sprite.Sprite):
    """Player-fired bullet that travels horizontally in the facing direction.

    Destroyed on hitting an enemy, platform, obstacle, or leaving screen.
    """

    SIZE: int = 2

    def __init__(self, x: float, y: float, facing: float) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (self.SIZE * 2 + 2, self.SIZE * 2), pygame.SRCALPHA,
        )
        self.position: pygame.Vector2 = pygame.Vector2(x, y)
        self.velocity: pygame.Vector2 = pygame.Vector2(
            facing * PLAYER_BULLET_SPEED, 0,
        )
        self.rect: pygame.Rect = pygame.Rect(
            int(x) - self.SIZE, int(y) - self.SIZE,
            self.SIZE * 2 + 2, self.SIZE * 2,
        )
        self.alive: bool = True

    def update(self, platforms: list, obstacles, dt: float) -> None:
        """Move and check collisions (platforms & obstacles only; enemy hit done externally)."""
        if not self.alive:
            return

        self.position += self.velocity * dt
        self.rect.x = int(self.position.x) - self.SIZE
        self.rect.y = int(self.position.y) - self.SIZE

        # Off-screen
        if (
            self.position.x < -100 or self.position.x > INTERNAL_WIDTH + 500
            or self.position.y < -500 or self.position.y > INTERNAL_HEIGHT + 500
        ):
            self.alive = False
            self.kill()
            return

        # Platform collision
        for plat in platforms:
            if not plat.active:
                continue
            if self.rect.colliderect(plat.rect):
                self.alive = False
                self.kill()
                return

        # Obstacle collision
        if obstacles:
            for obs in obstacles:
                if self.rect.colliderect(obs.rect):
                    self.alive = False
                    self.kill()
                    return

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw a cyan horizontal bullet streak."""
        if not self.alive:
            return
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)
        # Trail
        trail_len = 4 if self.velocity.x > 0 else -4
        pygame.draw.line(
            surface, (60, 180, 160),
            (sx - trail_len, sy), (sx, sy), 1,
        )
        # Core
        pygame.draw.circle(surface, COL_PLAYER_BULLET, (sx, sy), self.SIZE)

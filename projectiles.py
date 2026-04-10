"""
projectiles.py — Projectile and PlayerBullet sprites.

Enemy projectiles, player bullets (with angle spread for shotgun),
FriendlyBullet (reflected Void bullets), and LaserBeam (continuous).
All use pygame.sprite.Sprite for group-based collision.
"""

from __future__ import annotations
import math
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
    """Player-fired bullet with optional angle offset for weapon spread.

    Destroyed on hitting an enemy, platform, obstacle, or leaving screen.
    """

    SIZE: int = 2

    def __init__(
        self, x: float, y: float, facing: float, angle_offset: float = 0.0,
    ) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (self.SIZE * 2 + 2, self.SIZE * 2), pygame.SRCALPHA,
        )
        self.position: pygame.Vector2 = pygame.Vector2(x, y)

        # Calculate velocity with angle offset (degrees → radians)
        base_angle = 0.0 if facing > 0 else math.pi
        rad_offset = math.radians(angle_offset)
        final_angle = base_angle + rad_offset
        self.velocity: pygame.Vector2 = pygame.Vector2(
            math.cos(final_angle) * PLAYER_BULLET_SPEED,
            math.sin(final_angle) * PLAYER_BULLET_SPEED,
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
        trail_dx = -int(self.velocity.x * 0.015)
        trail_dy = -int(self.velocity.y * 0.015)
        pygame.draw.line(
            surface, (60, 180, 160),
            (sx + trail_dx, sy + trail_dy), (sx, sy), 1,
        )
        # Core
        pygame.draw.circle(surface, COL_PLAYER_BULLET, (sx, sy), self.SIZE)


class FriendlyBullet(pygame.sprite.Sprite):
    """A reflected enemy bullet (from Void powerup).

    Inherits position from the original bullet, reverses velocity,
    and damages enemies instead of the player.
    """

    SIZE: int = 3

    def __init__(
        self, position: pygame.Vector2, velocity: pygame.Vector2,
    ) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (self.SIZE * 2, self.SIZE * 2), pygame.SRCALPHA,
        )
        self.position: pygame.Vector2 = pygame.Vector2(position.x, position.y)
        self.velocity: pygame.Vector2 = pygame.Vector2(-velocity.x, -velocity.y)
        self.rect: pygame.Rect = pygame.Rect(
            int(position.x) - self.SIZE, int(position.y) - self.SIZE,
            self.SIZE * 2, self.SIZE * 2,
        )
        self.alive: bool = True

    def update(self, platforms: list, obstacles, dt: float) -> None:
        """Move the reflected bullet."""
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
        """Draw a purple reflected bullet."""
        if not self.alive:
            return
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)
        # Outer glow
        pygame.draw.circle(surface, (160, 40, 200), (sx, sy), self.SIZE + 1)
        # Core
        pygame.draw.circle(surface, (220, 120, 255), (sx, sy), self.SIZE)


class LaserBeam:
    """Continuous hitscan laser beam — not a moving projectile.

    Exists for a single frame, drawn as a line from the player to
    the first collision point. Damage is checked along the line.
    """

    def __init__(
        self, start: pygame.Vector2, facing: float, max_range: float = 500.0,
    ) -> None:
        self.start: pygame.Vector2 = pygame.Vector2(start.x, start.y)
        self.facing: float = facing
        self.max_range: float = max_range
        self.end: pygame.Vector2 = pygame.Vector2(
            start.x + facing * max_range, start.y,
        )
        self.alive: bool = True
        # Build collision rect along the beam
        min_x = min(self.start.x, self.end.x)
        max_x = max(self.start.x, self.end.x)
        self.rect: pygame.Rect = pygame.Rect(
            int(min_x), int(start.y) - 1,
            int(max_x - min_x), 3,
        )

    def clip_to_platforms(self, platforms: list, obstacles: list) -> None:
        """Shorten the beam to the first solid collision."""
        best_dist = self.max_range
        all_solids = [p for p in platforms if p.active]
        if obstacles:
            all_solids.extend(obstacles)

        for solid in all_solids:
            if self.rect.colliderect(solid.rect):
                # Find the closest edge in the beam direction
                if self.facing > 0:
                    dist = solid.rect.left - self.start.x
                else:
                    dist = self.start.x - solid.rect.right
                if 0 < dist < best_dist:
                    best_dist = dist

        self.end.x = self.start.x + self.facing * best_dist
        # Rebuild rect
        min_x = min(self.start.x, self.end.x)
        max_x = max(self.start.x, self.end.x)
        self.rect = pygame.Rect(
            int(min_x), int(self.start.y) - 1,
            max(1, int(max_x - min_x)), 3,
        )

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw a bright laser line with glow."""
        if not self.alive:
            return
        sx1 = int(self.start.x - cam_x)
        sy1 = int(self.start.y - cam_y)
        sx2 = int(self.end.x - cam_x)
        sy2 = int(self.end.y - cam_y)
        # Outer glow
        pygame.draw.line(surface, (60, 180, 160), (sx1, sy1), (sx2, sy2), 3)
        # Core
        pygame.draw.line(surface, (100, 255, 220), (sx1, sy1), (sx2, sy2), 1)

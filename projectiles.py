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
        self, x: float, y: float, dx: float, dy: float, speed: float = 0, ptype: str = "ground_flame"
    ) -> None:
        super().__init__()
        self.ptype = ptype
        self.visual_size = self.SIZE if self.ptype == "ground_flame" else self.SIZE * 2

        self.image: pygame.Surface = pygame.Surface(
            (self.visual_size * 2, self.visual_size * 2), pygame.SRCALPHA,
        )
        self.position: pygame.Vector2 = pygame.Vector2(x, y)
        direction = pygame.Vector2(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()
        self.velocity: pygame.Vector2 = direction * (speed if speed > 0 else PROJECTILE_SPEED)
        self.rect: pygame.Rect = pygame.Rect(
            int(x) - self.visual_size, int(y) - self.visual_size,
            self.visual_size * 2, self.visual_size * 2,
        )
        self.alive: bool = True
        self.distance_traveled: float = 0.0

    def update(self, platforms: list, obstacles, dt: float) -> None:
        """Move the projectile depending on its type."""
        if not self.alive:
            return

        if self.ptype == "big_flame":
            # Linear aerial fireball: completely ignores gravity
            self.position += self.velocity * dt
            self.rect.x = int(self.position.x) - self.visual_size
            self.rect.y = int(self.position.y) - self.visual_size

            self.distance_traveled += (self.velocity.length() * dt)
            if self.distance_traveled > 1500 or self.position.y > INTERNAL_HEIGHT * 3:
                self.alive = False
                self.kill()
                return

            # Linear aerial flames die on walls & platforms
            if obstacles:
                for obs in obstacles:
                    if self.rect.colliderect(obs.rect):
                        self.alive = False
                        self.kill()
                        return
            for plat in platforms:
                if not plat.active: continue
                if self.rect.colliderect(plat.rect):
                    self.alive = False
                    self.kill()
                    return
            return

        # Ground flame logic (creeping)
        if abs(self.velocity.x) < 50:
            self.velocity.x = PROJECTILE_SPEED if self.velocity.x >= 0 else -PROJECTILE_SPEED
        else:
            self.velocity.x = (PROJECTILE_SPEED if self.velocity.x > 0 else -PROJECTILE_SPEED)

        self.velocity.y += 980.0 * dt
        self.velocity.y = min(self.velocity.y, 600.0)

        self.position.x += self.velocity.x * dt
        self.rect.x = int(self.position.x) - self.visual_size
        
        if obstacles:
            for obs in obstacles:
                if self.rect.colliderect(obs.rect):
                    self.alive = False
                    self.kill()
                    return

        self.distance_traveled += (abs(self.velocity.x) * dt)
        if self.distance_traveled > 1500 or self.position.y > INTERNAL_HEIGHT * 3:
            self.alive = False
            self.kill()
            return

        self.position.y += self.velocity.y * dt
        self.rect.y = int(self.position.y) - self.visual_size

        for plat in platforms:
            if not plat.active:
                continue
            if self.rect.colliderect(plat.rect) and self.velocity.y > 0:
                self.position.y = plat.rect.top - self.visual_size
                self.velocity.y = 0
                self.rect.y = int(self.position.y) - self.visual_size
                break

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw either a creeping ground flame or a big aerial straightforward fireball."""
        if not self.alive:
            return
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)

        import random, math
        flicker_y = int(math.sin(pygame.time.get_ticks() * 0.02) * (2 if self.ptype == "ground_flame" else 4))
        flicker_w = random.randint(0, 2 if self.ptype == "ground_flame" else 4)

        if self.ptype == "big_flame":
            # Drawing a larger, horizontal flying fireball
            dx = 1 if self.velocity.x > 0 else -1
            
            # Fireball trails
            core_points = [
                (sx + dx * self.visual_size, sy),
                (sx - dx * self.visual_size, sy - self.visual_size + flicker_w),
                (sx - dx * self.visual_size - flicker_y, sy),
                (sx - dx * self.visual_size, sy + self.visual_size - flicker_w),
            ]
            
            pygame.draw.circle(surface, (255, 40, 20, 100), (sx, sy), self.visual_size + 4) # Aura
            pygame.draw.polygon(surface, (255, 60, 20), core_points) 
            
            inner_points = [
                (sx + dx * (self.visual_size - 2), sy),
                (sx - dx * (self.visual_size - 2), sy - self.visual_size // 2 + flicker_w),
                (sx - dx * (self.visual_size - 2) - flicker_y, sy),
                (sx - dx * (self.visual_size - 2), sy + self.visual_size // 2 - flicker_w),
            ]
            pygame.draw.polygon(surface, (255, 200, 100), inner_points)

        else:
            # Ground flame
            flame_points = [
                (sx, sy - self.visual_size - flicker_y),
                (sx - self.visual_size + flicker_w, sy + self.visual_size),
                (sx + self.visual_size - flicker_w, sy + self.visual_size)
            ]
            pygame.draw.circle(surface, (255, 60, 20, 100), (sx, sy + self.visual_size//2), self.visual_size + 2)
            pygame.draw.polygon(surface, (255, 100, 20), flame_points)
            
            core_points = [
                (sx, sy - self.visual_size//2 - flicker_y),
                (sx - self.visual_size//2 + flicker_w, sy + self.visual_size),
                (sx + self.visual_size//2 - flicker_w, sy + self.visual_size)
            ]
            pygame.draw.polygon(surface, (255, 220, 100), core_points)


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
        self.distance_traveled: float = 0.0

    def update(self, platforms: list, obstacles, dt: float) -> None:
        """Move and check collisions (platforms & obstacles only; enemy hit done externally)."""
        if not self.alive:
            return

        self.position += self.velocity * dt
        self.rect.x = int(self.position.x) - self.SIZE
        self.rect.y = int(self.position.y) - self.SIZE

        # Range check: kill bullet if it traveled too far
        self.distance_traveled += (self.velocity.length() * dt)
        if self.distance_traveled > 1200 or self.position.y > INTERNAL_HEIGHT * 3:
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

"""
enemies.py — Enemy types: Dasher, Marksman, Hybrid.

All enemies inherit from pygame.sprite.Sprite for group-based
collision detection. The Marksman uses a state machine with
precise tick-based flash telegraphing.
"""

from __future__ import annotations
import math
import pygame
from settings import (
    DASHER_SPEED, ENEMY_WIDTH, ENEMY_HEIGHT,
    MARKSMAN_COOLDOWN, MARKSMAN_FLASH_DURATION, MARKSMAN_LEAD_FACTOR,
    HYBRID_FIRE_COOLDOWN, PROJECTILE_SPEED,
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_DASHER, COL_DASHER_EYE,
    COL_MARKSMAN, COL_MARKSMAN_FLASH, COL_MARKSMAN_EYE,
    COL_HYBRID, COL_HYBRID_EYE,
)


# ─── Dasher ───────────────────────────────────────────────────────────


class Dasher(pygame.sprite.Sprite):
    """Chases the player at 70% of player speed.

    Simple AI: moves toward the player on the X-axis,
    respects platform edges and obstacles.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (ENEMY_WIDTH, ENEMY_HEIGHT), pygame.SRCALPHA,
        )
        self.rect: pygame.Rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.position: pygame.Vector2 = pygame.Vector2(float(x), float(y))
        self.velocity: pygame.Vector2 = pygame.Vector2(0, 0)
        self.facing: float = -1.0
        self.speed: float = DASHER_SPEED
        self.alive: bool = True

    def update(
        self,
        player_pos: pygame.Vector2,
        player_vel: pygame.Vector2,
        platforms: list,
        obstacles,
        dt: float,
    ) -> None:
        """Move toward the player on the X-axis."""
        if not self.alive:
            return

        # Direction to player
        dx = player_pos.x - self.position.x
        if abs(dx) > 2:
            self.facing = 1.0 if dx > 0 else -1.0
            self.position.x += self.facing * self.speed * dt
        else:
            self.facing = 1.0 if dx >= 0 else -1.0

        # Simple gravity & platform snapping
        self.velocity.y += 980.0 * dt
        self.velocity.y = min(self.velocity.y, 600.0)
        self.position.y += self.velocity.y * dt

        # Collision with platforms (vertical only — land on top)
        test_rect = pygame.Rect(
            int(self.position.x), int(self.position.y),
            ENEMY_WIDTH, ENEMY_HEIGHT,
        )
        for plat in platforms:
            if not plat.active:
                continue
            if test_rect.colliderect(plat.rect) and self.velocity.y > 0:
                self.position.y = plat.rect.top - ENEMY_HEIGHT
                self.velocity.y = 0

        # Collision with obstacles (stop horizontal movement)
        if obstacles:
            test_rect.x = int(self.position.x)
            test_rect.y = int(self.position.y)
            for obs in obstacles:
                if test_rect.colliderect(obs.rect):
                    if self.facing > 0:
                        self.position.x = obs.rect.left - ENEMY_WIDTH
                    else:
                        self.position.x = obs.rect.right

        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw the Dasher with angry eyes."""
        if not self.alive:
            return
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)

        # Body
        body_rect = pygame.Rect(sx, sy, ENEMY_WIDTH, ENEMY_HEIGHT)
        pygame.draw.rect(surface, COL_DASHER, body_rect)
        # Dark outline
        pygame.draw.rect(surface, (140, 30, 30), body_rect, 1)

        # Eyes — angry slant
        eye_y = sy + ENEMY_HEIGHT // 3
        eye_x = sx + ENEMY_WIDTH // 2 + int(self.facing * 1)
        eye_size = max(1, ENEMY_WIDTH // 5)
        pygame.draw.rect(
            surface, COL_DASHER_EYE,
            (eye_x - 2, eye_y, eye_size, eye_size),
        )
        pygame.draw.rect(
            surface, COL_DASHER_EYE,
            (eye_x + 2, eye_y, eye_size, eye_size),
        )

    def get_fire_request(self) -> dict | None:
        """Dashers don't shoot."""
        return None


# ─── Marksman ─────────────────────────────────────────────────────────


class MarksmanState:
    """Enum for the Marksman's state machine."""
    IDLE = "idle"
    FLASHING = "flashing"
    FIRING = "firing"


class Marksman(pygame.sprite.Sprite):
    """Stationary sniper with predictive aim and telegraph flash.

    State machine:
        IDLE → (cooldown expired) → FLASHING → (0.2s) → FIRING → IDLE

    During FLASHING, the Marksman locks onto the predicted future
    position of the player and changes color as a visual warning.
    Uses pygame.time.get_ticks() for precise 200ms flash timing.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (ENEMY_WIDTH, ENEMY_HEIGHT), pygame.SRCALPHA,
        )
        self.rect: pygame.Rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.position: pygame.Vector2 = pygame.Vector2(float(x), float(y))
        self.velocity: pygame.Vector2 = pygame.Vector2(0, 0)
        self.facing: float = -1.0
        self.alive: bool = True

        # State machine
        self.state: str = MarksmanState.IDLE
        self.cooldown_timer: float = MARKSMAN_COOLDOWN
        self.flash_start_tick: int = 0  # pygame.time.get_ticks() snapshot
        self.locked_target: pygame.Vector2 = pygame.Vector2(0, 0)

        # Pending fire request (yielded to the state manager)
        self._pending_fire: dict | None = None

    def update(
        self,
        player_pos: pygame.Vector2,
        player_vel: pygame.Vector2,
        platforms: list,
        obstacles,
        dt: float,
    ) -> None:
        """Marksman state machine update."""
        if not self.alive:
            return

        self._pending_fire = None

        # Face the player
        dx = player_pos.x - self.position.x
        self.facing = 1.0 if dx >= 0 else -1.0

        # Simple gravity
        self.velocity.y += 980.0 * dt
        self.velocity.y = min(self.velocity.y, 600.0)
        self.position.y += self.velocity.y * dt

        # Land on platforms
        test_rect = pygame.Rect(
            int(self.position.x), int(self.position.y),
            ENEMY_WIDTH, ENEMY_HEIGHT,
        )
        for plat in platforms:
            if not plat.active:
                continue
            if test_rect.colliderect(plat.rect) and self.velocity.y > 0:
                self.position.y = plat.rect.top - ENEMY_HEIGHT
                self.velocity.y = 0

        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

        # ── State machine ────────────────────────────────────────
        now = pygame.time.get_ticks()

        if self.state == MarksmanState.IDLE:
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0:
                # Transition → FLASHING
                self.state = MarksmanState.FLASHING
                self.flash_start_tick = now

                # Lock onto predicted target position
                self.locked_target = pygame.Vector2(
                    player_pos.x + player_vel.x * MARKSMAN_LEAD_FACTOR,
                    player_pos.y + player_vel.y * MARKSMAN_LEAD_FACTOR,
                )

        elif self.state == MarksmanState.FLASHING:
            elapsed_ms = now - self.flash_start_tick
            if elapsed_ms >= int(MARKSMAN_FLASH_DURATION * 1000):
                # Transition → FIRING
                self.state = MarksmanState.FIRING

        elif self.state == MarksmanState.FIRING:
            # Calculate direction to the locked target
            origin = pygame.Vector2(
                self.position.x + ENEMY_WIDTH / 2,
                self.position.y + ENEMY_HEIGHT / 2,
            )
            direction = self.locked_target - origin
            if direction.length() > 0:
                direction = direction.normalize()
            else:
                direction = pygame.Vector2(self.facing, 0)

            self._pending_fire = {
                "x": origin.x,
                "y": origin.y,
                "dx": direction.x,
                "dy": direction.y,
                "speed": PROJECTILE_SPEED,
            }

            # Transition → IDLE
            self.state = MarksmanState.IDLE
            self.cooldown_timer = MARKSMAN_COOLDOWN

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw with flash state color change."""
        if not self.alive:
            return
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)

        # Color based on state
        if self.state == MarksmanState.FLASHING:
            body_color = COL_MARKSMAN_FLASH
            outline_color = (200, 200, 200)
        else:
            body_color = COL_MARKSMAN
            outline_color = (100, 40, 140)

        body_rect = pygame.Rect(sx, sy, ENEMY_WIDTH, ENEMY_HEIGHT)
        pygame.draw.rect(surface, outline_color, body_rect.inflate(2, 2))
        pygame.draw.rect(surface, body_color, body_rect)

        # Scope eye (single centered dot)
        eye_y = sy + ENEMY_HEIGHT // 3
        eye_x = sx + ENEMY_WIDTH // 2 + int(self.facing * 2)
        pygame.draw.circle(surface, COL_MARKSMAN_EYE, (eye_x, eye_y), 2)

        # Draw aim line when flashing (warning telegraph)
        if self.state == MarksmanState.FLASHING:
            origin_x = sx + ENEMY_WIDTH // 2
            origin_y = sy + ENEMY_HEIGHT // 2
            target_x = int(self.locked_target.x - cam_x)
            target_y = int(self.locked_target.y - cam_y)
            pygame.draw.line(
                surface, (255, 60, 60),
                (origin_x, origin_y), (target_x, target_y), 1,
            )

    def get_fire_request(self) -> dict | None:
        """Returns fire data if the Marksman just fired, else None."""
        return self._pending_fire


# ─── Hybrid ───────────────────────────────────────────────────────────


class Hybrid(pygame.sprite.Sprite):
    """Moves like a Dasher, fires straight-ahead every 2 seconds.

    Combines chasing AI with periodic projectile attacks.
    No predictive aim — just fires in the facing direction.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (ENEMY_WIDTH, ENEMY_HEIGHT), pygame.SRCALPHA,
        )
        self.rect: pygame.Rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.position: pygame.Vector2 = pygame.Vector2(float(x), float(y))
        self.velocity: pygame.Vector2 = pygame.Vector2(0, 0)
        self.facing: float = -1.0
        self.speed: float = DASHER_SPEED
        self.alive: bool = True

        # Fire timer
        self.fire_timer: float = HYBRID_FIRE_COOLDOWN
        self._pending_fire: dict | None = None

    def update(
        self,
        player_pos: pygame.Vector2,
        player_vel: pygame.Vector2,
        platforms: list,
        obstacles,
        dt: float,
    ) -> None:
        """Chase + periodic fire update."""
        if not self.alive:
            return

        self._pending_fire = None

        # Chase (same as Dasher)
        dx = player_pos.x - self.position.x
        if abs(dx) > 2:
            self.facing = 1.0 if dx > 0 else -1.0
            self.position.x += self.facing * self.speed * dt

        # Gravity
        self.velocity.y += 980.0 * dt
        self.velocity.y = min(self.velocity.y, 600.0)
        self.position.y += self.velocity.y * dt

        # Platform collision
        test_rect = pygame.Rect(
            int(self.position.x), int(self.position.y),
            ENEMY_WIDTH, ENEMY_HEIGHT,
        )
        for plat in platforms:
            if not plat.active:
                continue
            if test_rect.colliderect(plat.rect) and self.velocity.y > 0:
                self.position.y = plat.rect.top - ENEMY_HEIGHT
                self.velocity.y = 0

        # Obstacle collision
        if obstacles:
            test_rect.x = int(self.position.x)
            test_rect.y = int(self.position.y)
            for obs in obstacles:
                if test_rect.colliderect(obs.rect):
                    if self.facing > 0:
                        self.position.x = obs.rect.left - ENEMY_WIDTH
                    else:
                        self.position.x = obs.rect.right

        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

        # Fire timer
        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = HYBRID_FIRE_COOLDOWN
            origin_x = self.position.x + ENEMY_WIDTH / 2
            origin_y = self.position.y + ENEMY_HEIGHT / 2
            self._pending_fire = {
                "x": origin_x,
                "y": origin_y,
                "dx": self.facing,
                "dy": 0.0,
                "speed": PROJECTILE_SPEED,
            }

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw the Hybrid enemy."""
        if not self.alive:
            return
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)

        body_rect = pygame.Rect(sx, sy, ENEMY_WIDTH, ENEMY_HEIGHT)
        pygame.draw.rect(surface, (160, 90, 20), body_rect.inflate(2, 2))
        pygame.draw.rect(surface, COL_HYBRID, body_rect)

        # Eyes
        eye_y = sy + ENEMY_HEIGHT // 3
        eye_x = sx + ENEMY_WIDTH // 2 + int(self.facing * 1)
        eye_size = max(1, ENEMY_WIDTH // 5)
        pygame.draw.rect(
            surface, COL_HYBRID_EYE,
            (eye_x - 2, eye_y, eye_size, eye_size),
        )
        pygame.draw.rect(
            surface, COL_HYBRID_EYE,
            (eye_x + 2, eye_y, eye_size, eye_size),
        )

    def get_fire_request(self) -> dict | None:
        """Returns fire data if the Hybrid just fired, else None."""
        return self._pending_fire

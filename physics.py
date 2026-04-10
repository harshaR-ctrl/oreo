"""
physics.py — Physics engine with ghost-collision prevention.

Implements kinematic equations (v = u + at), gravity, friction, and
2-step X/Y axis collision resolution. High-velocity sweep tests
prevent objects from tunneling through thin platforms.
"""

from __future__ import annotations
import math
import pygame
from settings import (
    GRAVITY, FRICTION, AIR_FRICTION, MAX_FALL_SPEED,
    MAX_RUN_SPEED, GROUND_Y, INTERNAL_HEIGHT,
)


class PhysicsEngine:
    """Handles all physics simulation: gravity, friction, collision."""

    def __init__(self) -> None:
        pass

    def apply_gravity(
        self, velocity: pygame.Vector2, dt: float, on_ground: bool
    ) -> None:
        """Apply gravitational acceleration."""
        if not on_ground:
            velocity.y += GRAVITY * dt
            velocity.y = min(velocity.y, MAX_FALL_SPEED)

    def apply_friction(
        self, velocity: pygame.Vector2, on_ground: bool
    ) -> None:
        """Apply ground or air friction to horizontal velocity."""
        if on_ground:
            velocity.x *= FRICTION
        else:
            velocity.x *= AIR_FRICTION

        # Clamp small values to zero to prevent drift
        if abs(velocity.x) < 0.5:
            velocity.x = 0

    def apply_acceleration(
        self,
        velocity: pygame.Vector2,
        direction: float,
        accel: float,
        dt: float,
    ) -> None:
        """Apply horizontal acceleration in the given direction.
        
        Uses v = u + at, then clamps to max run speed.
        """
        if direction != 0:
            velocity.x += direction * accel * dt
            velocity.x = max(-MAX_RUN_SPEED, min(MAX_RUN_SPEED, velocity.x))

    def move_and_collide(
        self,
        position: pygame.Vector2,
        velocity: pygame.Vector2,
        width: int,
        height: int,
        platforms: list,
        dt: float,
        obstacles: list | None = None,
    ) -> dict:
        """Move entity and resolve collisions using 2-step axis separation.
        
        Returns a dict with collision flags:
          - on_ground: bool
          - hit_ceiling: bool
          - hit_wall_left: bool
          - hit_wall_right: bool
          - wall_speed: float (speed at wall impact for shake)
        """
        result = {
            "on_ground": False,
            "hit_ceiling": False,
            "hit_wall_left": False,
            "hit_wall_right": False,
            "wall_speed": 0.0,
        }

        # Calculate movement this frame
        dx: float = velocity.x * dt
        dy: float = velocity.y * dt

        # Ghost collision prevention: subdivide if moving too fast
        min_dim = min(width, height)
        total_dist = math.sqrt(dx * dx + dy * dy)
        steps = max(1, int(math.ceil(total_dist / (min_dim * 0.8))))
        sub_dx = dx / steps
        sub_dy = dy / steps

        for _ in range(steps):
            # ── Step 1: Move X and resolve ────────────────────────
            position.x += sub_dx
            player_rect = pygame.Rect(
                int(position.x), int(position.y), width, height
            )

            for plat in platforms:
                if not plat.active:
                    continue
                if player_rect.colliderect(plat.rect):
                    if sub_dx > 0:  # Moving right
                        position.x = plat.rect.left - width
                        result["hit_wall_right"] = True
                        result["wall_speed"] = abs(velocity.x)
                        velocity.x = 0
                    elif sub_dx < 0:  # Moving left
                        position.x = plat.rect.right
                        result["hit_wall_left"] = True
                        result["wall_speed"] = abs(velocity.x)
                        velocity.x = 0
                    player_rect.x = int(position.x)

            # Obstacle X collision
            if obstacles:
                for obs in obstacles:
                    if player_rect.colliderect(obs.rect):
                        if sub_dx > 0:
                            position.x = obs.rect.left - width
                            result["hit_wall_right"] = True
                            result["wall_speed"] = abs(velocity.x)
                            velocity.x = 0
                        elif sub_dx < 0:
                            position.x = obs.rect.right
                            result["hit_wall_left"] = True
                            result["wall_speed"] = abs(velocity.x)
                            velocity.x = 0
                        player_rect.x = int(position.x)

            # ── Step 2: Move Y and resolve ────────────────────────
            position.y += sub_dy
            player_rect = pygame.Rect(
                int(position.x), int(position.y), width, height
            )

            for plat in platforms:
                if not plat.active:
                    continue
                if player_rect.colliderect(plat.rect):
                    if sub_dy > 0:  # Falling down
                        position.y = plat.rect.top - height
                        velocity.y = 0
                        result["on_ground"] = True
                        # Trigger crumble
                        if hasattr(plat, "platform_type") and plat.platform_type == "crumble":
                            plat.start_crumble()
                        # Bounce platform
                        if hasattr(plat, "platform_type") and plat.platform_type == "bounce":
                            velocity.y = -350  # strong bounce
                            result["on_ground"] = False
                    elif sub_dy < 0:  # Hitting ceiling
                        position.y = plat.rect.bottom
                        velocity.y = 0
                        result["hit_ceiling"] = True
                    player_rect.y = int(position.y)

            # Obstacle Y collision
            if obstacles:
                for obs in obstacles:
                    if player_rect.colliderect(obs.rect):
                        if sub_dy > 0:
                            position.y = obs.rect.top - height
                            velocity.y = 0
                            result["on_ground"] = True
                        elif sub_dy < 0:
                            position.y = obs.rect.bottom
                            velocity.y = 0
                            result["hit_ceiling"] = True
                        player_rect.y = int(position.y)

        # Check if player fell off the bottom (works for horizontal levels too)
        if position.y > GROUND_Y + INTERNAL_HEIGHT * 0.5:
            result["fell_off"] = True

        return result

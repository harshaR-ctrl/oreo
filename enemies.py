"""
enemies.py — Enemy types: Dasher, Marksman, Hybrid.

All enemies inherit from pygame.sprite.Sprite.
Now includes optimized edge detection and obstacle avoidance so enemies
don't blindly fall off platforms and vanish.
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

def _apply_gravity_and_floor(
    enemy, platforms: list, dt: float
) -> bool:
    """Apply gravity and platform collision uniformly.
    Returns True if the enemy is on the ground.
    """
    enemy.velocity.y += 980.0 * dt
    enemy.velocity.y = min(enemy.velocity.y, 600.0)
    enemy.position.y += enemy.velocity.y * dt

    test_rect = pygame.Rect(
        int(enemy.position.x), int(enemy.position.y),
        ENEMY_WIDTH, ENEMY_HEIGHT,
    )
    on_ground = False
    for plat in platforms:
        if not plat.active:
            continue
        if test_rect.colliderect(plat.rect) and enemy.velocity.y > 0:
            enemy.position.y = plat.rect.top - ENEMY_HEIGHT
            enemy.velocity.y = 0
            on_ground = True
            break
            
    return on_ground

def _can_move_x(
    enemy, move_x: float, platforms: list, obstacles: list, on_ground: bool
) -> bool:
    """Check if the enemy can move horizontally without hitting an obstacle or falling."""
    new_x = enemy.position.x + move_x
    test_rect = pygame.Rect(
        int(new_x), int(enemy.position.y),
        ENEMY_WIDTH, ENEMY_HEIGHT,
    )
    
    # 1. Obstacle collision
    for obs in obstacles:
        if test_rect.colliderect(obs.rect):
            return False

    # 2. Edge detection (only if on ground)
    if on_ground:
        # Check the floor exactly under the leading edge
        probe_x = new_x + ENEMY_WIDTH if move_x > 0 else new_x
        probe_rect = pygame.Rect(int(probe_x) - 1, int(enemy.position.y + ENEMY_HEIGHT), 2, 2)
        has_floor = False
        for plat in platforms:
            if not plat.active:
                continue
            if probe_rect.colliderect(plat.rect):
                has_floor = True
                break
        if not has_floor:
            return False

    return True

# ─── Dasher ───────────────────────────────────────────────────────────

class Dasher(pygame.sprite.Sprite):
    """Chases the player, but respects platform edges and obstacles."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((ENEMY_WIDTH, ENEMY_HEIGHT), pygame.SRCALPHA)
        self.rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.position = pygame.Vector2(float(x), float(y))
        self.velocity = pygame.Vector2(0, 0)
        self.facing = -1.0
        self.speed = DASHER_SPEED
        self.alive = True

    def update(
        self,
        player_pos: pygame.Vector2,
        player_vel: pygame.Vector2,
        platforms: list,
        obstacles,
        dt: float,
    ) -> None:
        if not self.alive:
            return

        # Gravity & Floor
        on_ground = _apply_gravity_and_floor(self, platforms, dt)

        # Smart X Movement
        dx = player_pos.x - self.position.x
        if abs(dx) > 2:
            self.facing = 1.0 if dx > 0 else -1.0
            move_x = self.facing * self.speed * dt
            
            if _can_move_x(self, move_x, platforms, obstacles, on_ground):
                self.position.x += move_x

        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if not self.alive:
            return
        sx, sy = int(self.position.x - cam_x), int(self.position.y - cam_y)
        body_rect = pygame.Rect(sx, sy, ENEMY_WIDTH, ENEMY_HEIGHT)
        pygame.draw.rect(surface, COL_DASHER, body_rect)
        pygame.draw.rect(surface, (140, 30, 30), body_rect, 1)

        eye_y = sy + ENEMY_HEIGHT // 3
        eye_x = sx + ENEMY_WIDTH // 2 + int(self.facing * 1)
        eye_size = max(1, ENEMY_WIDTH // 5)
        pygame.draw.rect(surface, COL_DASHER_EYE, (eye_x - 2, eye_y, eye_size, eye_size))
        pygame.draw.rect(surface, COL_DASHER_EYE, (eye_x + 2, eye_y, eye_size, eye_size))

    def get_fire_request(self) -> dict | None:
        return None

# ─── Marksman ─────────────────────────────────────────────────────────

class MarksmanState:
    IDLE = "idle"
    FLASHING = "flashing"
    FIRING = "firing"

class Marksman(pygame.sprite.Sprite):
    """Stationary sniper with predictive aim and telegraph flash."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((ENEMY_WIDTH, ENEMY_HEIGHT), pygame.SRCALPHA)
        self.rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.position = pygame.Vector2(float(x), float(y))
        self.velocity = pygame.Vector2(0, 0)
        self.facing = -1.0
        self.alive = True

        self.state = MarksmanState.IDLE
        self.cooldown_timer = MARKSMAN_COOLDOWN
        self.flash_start_tick = 0
        self.locked_target = pygame.Vector2(0, 0)
        self._pending_fire = None

    def update(
        self,
        player_pos: pygame.Vector2,
        player_vel: pygame.Vector2,
        platforms: list,
        obstacles,
        dt: float,
    ) -> None:
        if not self.alive:
            return
        self._pending_fire = None

        dx = player_pos.x - self.position.x
        self.facing = 1.0 if dx >= 0 else -1.0

        _apply_gravity_and_floor(self, platforms, dt)
        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

        # Logic
        now = pygame.time.get_ticks()
        if self.state == MarksmanState.IDLE:
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0:
                self.state = MarksmanState.FLASHING
                self.flash_start_tick = now
                self.locked_target = pygame.Vector2(
                    player_pos.x + player_vel.x * MARKSMAN_LEAD_FACTOR,
                    player_pos.y + player_vel.y * MARKSMAN_LEAD_FACTOR,
                )

        elif self.state == MarksmanState.FLASHING:
            elapsed_ms = now - self.flash_start_tick
            if elapsed_ms >= int(MARKSMAN_FLASH_DURATION * 1000):
                self.state = MarksmanState.FIRING

        elif self.state == MarksmanState.FIRING:
            origin = pygame.Vector2(self.position.x + ENEMY_WIDTH / 2, self.position.y + ENEMY_HEIGHT / 2)
            direction = self.locked_target - origin
            if direction.length() > 0:
                direction = direction.normalize()
            else:
                direction = pygame.Vector2(self.facing, 0)

            self._pending_fire = {
                "x": origin.x, "y": origin.y,
                "dx": direction.x, "dy": direction.y,
                "speed": PROJECTILE_SPEED,
                "type": "ground_flame",
            }
            self.state = MarksmanState.IDLE
            self.cooldown_timer = MARKSMAN_COOLDOWN

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if not self.alive:
            return
        sx, sy = int(self.position.x - cam_x), int(self.position.y - cam_y)

        if self.state == MarksmanState.FLASHING:
            body_color, outline_color = COL_MARKSMAN_FLASH, (200, 200, 200)
        else:
            body_color, outline_color = COL_MARKSMAN, (100, 40, 140)

        body_rect = pygame.Rect(sx, sy, ENEMY_WIDTH, ENEMY_HEIGHT)
        pygame.draw.rect(surface, outline_color, body_rect.inflate(2, 2))
        pygame.draw.rect(surface, body_color, body_rect)

        eye_y = sy + ENEMY_HEIGHT // 3
        eye_x = sx + ENEMY_WIDTH // 2 + int(self.facing * 2)
        pygame.draw.circle(surface, COL_MARKSMAN_EYE, (eye_x, eye_y), 2)

        if self.state == MarksmanState.FLASHING:
            ox, oy = sx + ENEMY_WIDTH // 2, sy + ENEMY_HEIGHT // 2
            tx, ty = int(self.locked_target.x - cam_x), int(self.locked_target.y - cam_y)
            pygame.draw.line(surface, (255, 60, 60), (ox, oy), (tx, ty), 1)

    def get_fire_request(self) -> dict | None:
        return self._pending_fire

# ─── Hybrid ───────────────────────────────────────────────────────────

class Hybrid(pygame.sprite.Sprite):
    """Moves like a Dasher but stops at edges, periodically fires straight."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((ENEMY_WIDTH, ENEMY_HEIGHT), pygame.SRCALPHA)
        self.rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
        self.position = pygame.Vector2(float(x), float(y))
        self.velocity = pygame.Vector2(0, 0)
        self.facing = -1.0
        self.speed = DASHER_SPEED
        self.alive = True
        self.fire_timer = HYBRID_FIRE_COOLDOWN
        self._pending_fire = None

    def update(
        self,
        player_pos: pygame.Vector2,
        player_vel: pygame.Vector2,
        platforms: list,
        obstacles,
        dt: float,
    ) -> None:
        if not self.alive:
            return
        self._pending_fire = None

        on_ground = _apply_gravity_and_floor(self, platforms, dt)

        dx = player_pos.x - self.position.x
        if abs(dx) > 2:
            self.facing = 1.0 if dx > 0 else -1.0
            move_x = self.facing * self.speed * dt
            
            if _can_move_x(self, move_x, platforms, obstacles, on_ground):
                self.position.x += move_x

        self.rect.x = int(self.position.x)
        self.rect.y = int(self.position.y)

        self.fire_timer -= dt
        if self.fire_timer <= 0:
            self.fire_timer = HYBRID_FIRE_COOLDOWN
            self._pending_fire = {
                "x": self.position.x + ENEMY_WIDTH / 2,
                "y": self.position.y + ENEMY_HEIGHT / 2,
                "dx": self.facing, "dy": 0.0,
                "speed": PROJECTILE_SPEED * 1.5,
                "type": "big_flame",
            }

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if not self.alive:
            return
        sx, sy = int(self.position.x - cam_x), int(self.position.y - cam_y)

        body_rect = pygame.Rect(sx, sy, ENEMY_WIDTH, ENEMY_HEIGHT)
        pygame.draw.rect(surface, (160, 90, 20), body_rect.inflate(2, 2))
        pygame.draw.rect(surface, COL_HYBRID, body_rect)

        eye_y = sy + ENEMY_HEIGHT // 3
        eye_x = sx + ENEMY_WIDTH // 2 + int(self.facing * 1)
        eye_size = max(1, ENEMY_WIDTH // 5)
        pygame.draw.rect(surface, COL_HYBRID_EYE, (eye_x - 2, eye_y, eye_size, eye_size))
        pygame.draw.rect(surface, COL_HYBRID_EYE, (eye_x + 2, eye_y, eye_size, eye_size))

    def get_fire_request(self) -> dict | None:
        return self._pending_fire

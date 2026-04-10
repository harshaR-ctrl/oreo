"""
player.py — Player controller with kinematic movement.

Implements variable jump height, coyote time, jump buffering,
and momentum-based dash. Uses Vector2 for all movement math.
"""

from __future__ import annotations
import math
import pygame
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    ACCELERATION, JUMP_IMPULSE, JUMP_CUT_MULTIPLIER,
    MAX_JUMP_HOLD_TIME, JUMP_HOLD_FORCE,
    DASH_SPEED, MOMENTUM_FACTOR, DASH_COOLDOWN, DASH_DURATION,
    COYOTE_FRAMES, JUMP_BUFFER_FRAMES,
    COL_PLAYER_BODY, COL_PLAYER_OUTLINE, COL_PLAYER_DASH, COL_PLAYER_EYE,
    FPS, PLAYER_SHOOT_COOLDOWN,
)
from input_handler import InputHandler
from physics import PhysicsEngine
from particles import ParticleSystem


class PlayerState:
    """Enum for player animation/logic states."""
    IDLE = "idle"
    RUNNING = "running"
    JUMPING = "jumping"
    FALLING = "falling"
    DASHING = "dashing"


class Player:
    """The player character with full kinematic movement."""

    def __init__(self, physics: PhysicsEngine, particles: ParticleSystem) -> None:
        self.position: pygame.Vector2 = pygame.Vector2(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.velocity: pygame.Vector2 = pygame.Vector2(0, 0)
        self.width: int = PLAYER_WIDTH
        self.height: int = PLAYER_HEIGHT

        self.physics: PhysicsEngine = physics
        self.particles: ParticleSystem = particles

        # State
        self.state: str = PlayerState.IDLE
        self.on_ground: bool = False
        self.facing: float = 1.0  # 1.0 = right, -1.0 = left
        self.alive: bool = True

        # Jump mechanics
        self.coyote_counter: int = 0
        self.jump_buffer_counter: int = 0
        self.jump_hold_timer: float = 0.0
        self.is_jumping: bool = False

        # Dash mechanics
        self.dash_cooldown_timer: float = 0.0
        self.dash_timer: float = 0.0
        self.is_dashing: bool = False
        self.dash_direction: pygame.Vector2 = pygame.Vector2(0, 0)
        self.can_dash: bool = True  # Reset on landing
        self.dash_ghost_timer: float = 0.0

        # Shooting
        self.can_shoot: bool = False
        self.shoot_cooldown_timer: float = 0.0

        # Visual
        self.squash_stretch: float = 1.0  # 1.0 = normal, <1 = squash, >1 = stretch
        self.eye_target_x: float = 0.0

    @property
    def rect(self) -> pygame.Rect:
        """Current collision rectangle."""
        return pygame.Rect(
            int(self.position.x), int(self.position.y),
            self.width, self.height,
        )

    @property
    def center_x(self) -> float:
        return self.position.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.position.y + self.height / 2

    def reset(self, x: float = PLAYER_SPAWN_X, y: float = PLAYER_SPAWN_Y) -> None:
        """Reset player to spawn position."""
        self.position.x = x
        self.position.y = y
        self.velocity.x = 0
        self.velocity.y = 0
        self.state = PlayerState.IDLE
        self.on_ground = False
        self.alive = True
        self.coyote_counter = 0
        self.jump_buffer_counter = 0
        self.jump_hold_timer = 0.0
        self.is_jumping = False
        self.dash_cooldown_timer = 0.0
        self.dash_timer = 0.0
        self.is_dashing = False
        self.can_dash = True
        self.can_shoot = False
        self.shoot_cooldown_timer = 0.0
        self.squash_stretch = 1.0

    def update(self, inp: InputHandler, platforms: list, dt: float) -> dict:
        """Full player update: input → physics → collision → state.
        
        Returns event dict with flags for sound/VFX triggers:
          - jumped, landed, dashed, died, wall_hit, wall_speed, shot
        """
        events: dict = {
            "jumped": False,
            "landed": False,
            "dashed": False,
            "died": False,
            "wall_hit": False,
            "wall_speed": 0.0,
            "shot": False,
        }

        if not self.alive:
            return events

        was_on_ground = self.on_ground

        # ── Dashing ──────────────────────────────────────────────
        self.dash_cooldown_timer = max(0, self.dash_cooldown_timer - dt)

        if self.is_dashing:
            self.dash_timer -= dt
            # Emit ghost trail
            self.dash_ghost_timer -= dt
            if self.dash_ghost_timer <= 0:
                self.particles.emit_dash_ghost(self.position.x, self.position.y)
                self.dash_ghost_timer = DASH_DURATION / 6

            if self.dash_timer <= 0:
                self.is_dashing = False
            else:
                # During dash: override velocity with dash direction
                self.velocity.x = self.dash_direction.x
                self.velocity.y = self.dash_direction.y

                # Reduced gravity during dash
                self.physics.apply_gravity(self.velocity, dt * 0.1, self.on_ground)

                collision = self.physics.move_and_collide(
                    self.position, self.velocity,
                    self.width, self.height, platforms, dt,
                )
                self._handle_collision(collision, events)
                self._update_visual_state(inp, dt)
                return events

        # ── Horizontal movement ──────────────────────────────────
        direction = inp.move_direction()
        if direction != 0:
            self.facing = direction
        self.eye_target_x = direction

        self.physics.apply_acceleration(self.velocity, direction, ACCELERATION, dt)
        self.physics.apply_friction(self.velocity, self.on_ground)
        self.physics.apply_gravity(self.velocity, dt, self.on_ground)

        # ── Coyote time ──────────────────────────────────────────
        if self.on_ground:
            self.coyote_counter = COYOTE_FRAMES
        else:
            self.coyote_counter = max(0, self.coyote_counter - 1)

        # ── Jump buffering ───────────────────────────────────────
        if inp.jump_pressed():
            self.jump_buffer_counter = JUMP_BUFFER_FRAMES

        if self.jump_buffer_counter > 0:
            self.jump_buffer_counter -= 1

        # ── Jump logic ───────────────────────────────────────────
        can_jump = self.coyote_counter > 0 and not self.is_jumping

        if self.jump_buffer_counter > 0 and can_jump:
            self.velocity.y = JUMP_IMPULSE
            self.is_jumping = True
            self.jump_hold_timer = 0.0
            self.coyote_counter = 0
            self.jump_buffer_counter = 0
            self.on_ground = False
            events["jumped"] = True
            self.squash_stretch = 1.3  # Stretch on jump
            self.particles.emit_jump_dust(self.center_x, self.position.y + self.height)

        # Variable jump height — hold for higher
        if self.is_jumping and inp.jump_held():
            self.jump_hold_timer += dt
            if self.jump_hold_timer < MAX_JUMP_HOLD_TIME:
                self.velocity.y += JUMP_HOLD_FORCE * dt

        # Cut jump short on release
        if inp.jump_released() and self.velocity.y < 0:
            self.velocity.y *= JUMP_CUT_MULTIPLIER
            self.is_jumping = False

        # ── Dash logic ───────────────────────────────────────────
        if inp.dash_pressed() and self.can_dash and self.dash_cooldown_timer <= 0:
            self._start_dash(inp)
            events["dashed"] = True

        # ── Shooting ──────────────────────────────────────────────────
        self.shoot_cooldown_timer = max(0, self.shoot_cooldown_timer - dt)
        if inp.shoot_pressed() and self.can_shoot and self.shoot_cooldown_timer <= 0:
            self.shoot_cooldown_timer = PLAYER_SHOOT_COOLDOWN
            events["shot"] = True

        # ── Move and collide ─────────────────────────────────────
        collision = self.physics.move_and_collide(
            self.position, self.velocity,
            self.width, self.height, platforms, dt,
        )
        self._handle_collision(collision, events)

        # ── Landing detection ────────────────────────────────────
        if not was_on_ground and self.on_ground:
            events["landed"] = True
            self.is_jumping = False
            self.can_dash = True
            self.squash_stretch = 0.6  # Squash on landing
            self.particles.emit_landing_dust(self.center_x, self.position.y + self.height)

        # ── Death check ──────────────────────────────────────────
        if collision.get("fell_off", False):
            self.alive = False
            events["died"] = True
            self.particles.emit_death_burst(self.center_x, self.center_y)

        self._update_visual_state(inp, dt)
        return events

    def _start_dash(self, inp: InputHandler) -> None:
        """Initiate a momentum-based dash."""
        # Determine dash direction from input, default to facing direction
        dx = inp.move_direction()
        dy = inp.up_direction()

        if dx == 0 and dy == 0:
            dx = self.facing

        direction = pygame.Vector2(dx, dy)
        if direction.length() > 0:
            direction = direction.normalize()

        # Momentum-based: dash velocity = direction * dash_speed + velocity * momentum_factor
        dash_vel = direction * DASH_SPEED
        momentum = self.velocity * MOMENTUM_FACTOR
        self.dash_direction = dash_vel + momentum

        self.is_dashing = True
        self.dash_timer = DASH_DURATION
        self.dash_cooldown_timer = DASH_COOLDOWN
        self.can_dash = False
        self.dash_ghost_timer = 0.0
        self.squash_stretch = 1.5  # Extreme stretch

    def _handle_collision(self, collision: dict, events: dict) -> None:
        """Process collision results."""
        self.on_ground = collision["on_ground"]

        if collision["hit_wall_left"] or collision["hit_wall_right"]:
            events["wall_hit"] = True
            events["wall_speed"] = collision["wall_speed"]
            if collision["wall_speed"] > 100:
                wx = self.position.x if collision["hit_wall_left"] else self.position.x + self.width
                self.particles.emit_wall_hit(wx, self.center_y)

    def _update_visual_state(self, inp: InputHandler, dt: float) -> None:
        """Update animation state and squash/stretch."""
        # Recover squash/stretch toward 1.0
        self.squash_stretch += (1.0 - self.squash_stretch) * min(1.0, dt * 12)

        if self.is_dashing:
            self.state = PlayerState.DASHING
        elif not self.on_ground:
            self.state = PlayerState.JUMPING if self.velocity.y < 0 else PlayerState.FALLING
        elif abs(self.velocity.x) > 5:
            self.state = PlayerState.RUNNING
        else:
            self.state = PlayerState.IDLE

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw the player character with squash/stretch and eyes."""
        if not self.alive:
            return

        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)

        # Apply squash/stretch
        draw_w = int(self.width * (2.0 - self.squash_stretch))
        draw_h = int(self.height * self.squash_stretch)
        offset_x = (self.width - draw_w) // 2
        offset_y = self.height - draw_h

        body_rect = pygame.Rect(sx + offset_x, sy + offset_y, draw_w, draw_h)

        # Choose color based on state
        if self.is_dashing:
            body_color = COL_PLAYER_DASH
        else:
            body_color = COL_PLAYER_BODY

        # Outline
        outline_rect = body_rect.inflate(2, 2)
        pygame.draw.rect(surface, COL_PLAYER_OUTLINE, outline_rect)
        # Body
        pygame.draw.rect(surface, body_color, body_rect)

        # Eyes
        eye_y = sy + offset_y + draw_h // 3
        eye_base_x = sx + offset_x + draw_w // 2
        eye_offset = int(self.facing * 2)

        # Two small eye dots
        eye_size = max(1, draw_w // 5)
        pygame.draw.rect(
            surface, COL_PLAYER_EYE,
            (eye_base_x + eye_offset - 2, eye_y, eye_size, eye_size),
        )
        pygame.draw.rect(
            surface, COL_PLAYER_EYE,
            (eye_base_x + eye_offset + 2, eye_y, eye_size, eye_size),
        )

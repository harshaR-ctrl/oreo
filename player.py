"""
player.py — Player controller with kinematic movement.

Implements variable jump height, coyote time, jump buffering,
momentum-based dash, lives system, state-driven powerup manager,
and weapon strategy pattern. Features Oreo-themed character design.
"""

from __future__ import annotations
import math
import random
import pygame
from settings import (
    PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    ACCELERATION, JUMP_IMPULSE, JUMP_CUT_MULTIPLIER,
    MAX_JUMP_HOLD_TIME, JUMP_HOLD_FORCE,
    DASH_SPEED, MOMENTUM_FACTOR, DASH_COOLDOWN, DASH_DURATION,
    COYOTE_FRAMES, JUMP_BUFFER_FRAMES,
    COL_PLAYER_BODY, COL_PLAYER_OUTLINE, COL_PLAYER_DASH, COL_PLAYER_EYE,
    COL_SHIELD_RING, COL_OREO_DARK, COL_OREO_CREAM, COL_OREO_OUTLINE,
    FPS, PLAYER_SHOOT_COOLDOWN,
    MAX_LIVES, DAMAGE_INVINCIBILITY, MAX_RUN_SPEED,
    WEAPON_TYPES, WEAPON_ORDER,
    POWERUP_DASH_DURATION, POWERUP_MAGNET_DURATION,
    POWERUP_SHIELD_DURATION, POWERUP_BLACKHOLE_DURATION,
    POWERUP_VOID_DURATION,
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


# ─── Duration lookup for activate_powerup convenience ─────────────────
_POWERUP_DURATIONS: dict[str, int] = {
    "dash":      POWERUP_DASH_DURATION,
    "magnet":    POWERUP_MAGNET_DURATION,
    "shield":    POWERUP_SHIELD_DURATION,
    "blackhole": POWERUP_BLACKHOLE_DURATION,
    "void":      POWERUP_VOID_DURATION,
}


class Player:
    """The player character with full kinematic movement and Oreo visuals."""

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

        # ── Lives system ─────────────────────────────────────────
        self.lives: int = MAX_LIVES
        self.max_lives: int = MAX_LIVES
        self.invincible: bool = False
        self.invincible_timer: float = 0.0

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

        # ── PowerUp Manager (non-blocking, tick-based) ───────────
        self.active_powerups: dict[str, int] = {}  # type → expiry tick (ms)
        self.speed_multiplier: float = 1.0
        self.shield_active: bool = False

        # ── Weapon Strategy Pattern ──────────────────────────────
        self.can_shoot: bool = True   # Start with pistol available
        self.current_weapon: str = "pistol"
        self.unlocked_weapons: list[str] = ["pistol"]
        self.weapon_cooldown_tick: int = 0  # expiry tick for weapon cooldown

        # Visual
        self.squash_stretch: float = 1.0  # 1.0 = normal, <1 = squash, >1 = stretch
        self.eye_target_x: float = 0.0
        self.run_anim_timer: float = 0.0
        self.invuln_flash_timer: float = 0.0
        self.roll_angle: float = 0.0  # accumulates rotation in degrees

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

    @property
    def shield_rect(self) -> pygame.Rect:
        """Collision rect for the shield bubble (slightly larger than player)."""
        shield_r = 12
        cx, cy = int(self.center_x), int(self.center_y)
        return pygame.Rect(cx - shield_r, cy - shield_r, shield_r * 2, shield_r * 2)

    def reset(self, x: float = PLAYER_SPAWN_X, y: float = PLAYER_SPAWN_Y) -> None:
        """Reset player to spawn position."""
        self.position.x = x
        self.position.y = y
        self.velocity.x = 0
        self.velocity.y = 0
        self.state = PlayerState.IDLE
        self.on_ground = False
        self.alive = True
        self.lives = self.max_lives
        self.invincible = False
        self.invincible_timer = 0.0
        self.coyote_counter = 0
        self.jump_buffer_counter = 0
        self.jump_hold_timer = 0.0
        self.is_jumping = False
        self.dash_cooldown_timer = 0.0
        self.dash_timer = 0.0
        self.is_dashing = False
        self.can_dash = True
        self.can_shoot = True
        self.current_weapon = "pistol"
        self.unlocked_weapons = ["pistol"]
        self.weapon_cooldown_tick = 0
        self.active_powerups.clear()
        self.speed_multiplier = 1.0
        self.shield_active = False
        self.squash_stretch = 1.0
        self.run_anim_timer = 0.0
        self.invuln_flash_timer = 0.0
        self.roll_angle = 0.0

    # ── Lives & Damage ───────────────────────────────────────────────

    def take_damage(self) -> bool:
        """Reduce lives by 1, start i-frames. Returns True if player died."""
        if self.invincible:
            return False
        self.lives -= 1
        if self.lives <= 0:
            self.alive = False
            return True
        # Grant invincibility frames
        self.invincible = True
        self.invincible_timer = DAMAGE_INVINCIBILITY
        return False

    # ── PowerUp Manager ──────────────────────────────────────────────

    def activate_powerup(self, ptype: str, duration_ms: int | None = None) -> None:
        """Activate a timed powerup. Uses default duration if none given."""
        if duration_ms is None:
            duration_ms = _POWERUP_DURATIONS.get(ptype, 5000)
        self.active_powerups[ptype] = pygame.time.get_ticks() + duration_ms
        self._apply_powerup_effect(ptype, active=True)

    def _apply_powerup_effect(self, ptype: str, active: bool) -> None:
        """Apply or remove the side-effect of a powerup."""
        if ptype == "dash":
            self.speed_multiplier = 2.0 if active else 1.0
        elif ptype == "shield":
            self.shield_active = active
            self.invincible = active

    def _update_powerups(self) -> None:
        """Expire powerups whose ticks have passed."""
        now = pygame.time.get_ticks()
        expired = [k for k, v in self.active_powerups.items() if now > v]
        for ptype in expired:
            self._apply_powerup_effect(ptype, active=False)
            del self.active_powerups[ptype]

    def has_powerup(self, ptype: str) -> bool:
        """Check if a powerup is currently active."""
        return ptype in self.active_powerups

    # ── Weapon Strategy ──────────────────────────────────────────────

    def cycle_weapon(self) -> None:
        """Advance to the next unlocked weapon."""
        if len(self.unlocked_weapons) <= 1:
            return
        idx = self.unlocked_weapons.index(self.current_weapon)
        self.current_weapon = self.unlocked_weapons[(idx + 1) % len(self.unlocked_weapons)]

    def unlock_next_weapon(self) -> str:
        """Unlock the next weapon in WEAPON_ORDER. Returns the newly unlocked name."""
        for w in WEAPON_ORDER:
            if w not in self.unlocked_weapons:
                self.unlocked_weapons.append(w)
                self.current_weapon = w
                return w
        # All unlocked — just cycle
        self.cycle_weapon()
        return self.current_weapon

    def shoot(self, inp: InputHandler) -> list[dict]:
        """Attempt to fire based on current weapon stats.

        Returns a list of dicts with keys: x, y, facing, angle_offset
        for each bullet to spawn. Empty list if on cooldown.
        """
        now = pygame.time.get_ticks()
        stats = WEAPON_TYPES[self.current_weapon]

        # Continuous weapons fire while held; others fire on press
        if stats["is_continuous"]:
            if not inp.shoot_held():
                return []
        else:
            if not inp.shoot_pressed():
                return []

        # Cooldown check (tick-based)
        if now < self.weapon_cooldown_tick:
            return []

        self.weapon_cooldown_tick = now + stats["cooldown"]

        bullets: list[dict] = []
        num = stats["bullets"]
        spread = stats["spread"]

        bx = self.center_x + self.facing * 6
        by = self.center_y

        if num == 1:
            angle = random.uniform(-spread, spread) if spread > 0 else 0.0
            bullets.append({"x": bx, "y": by, "facing": self.facing, "angle": angle})
        else:
            # Multi-bullet: evenly distribute across spread range
            for i in range(num):
                if num > 1:
                    angle = -spread + (2 * spread * i / (num - 1))
                else:
                    angle = 0.0
                bullets.append({"x": bx, "y": by, "facing": self.facing, "angle": angle})

        return bullets

    # ── Main update ──────────────────────────────────────────────────

    def update(self, inp: InputHandler, platforms: list, dt: float, obstacles: list | None = None) -> dict:
        """Full player update: input → physics → collision → state.

        Returns event dict with flags for sound/VFX triggers:
          - jumped, landed, dashed, died, wall_hit, wall_speed, shot
          - weapon_switched, powerup_expired
        """
        events: dict = {
            "jumped": False,
            "landed": False,
            "dashed": False,
            "died": False,
            "wall_hit": False,
            "wall_speed": 0.0,
            "shot": False,
            "shot_bullets": [],       # list of bullet spawn dicts
            "weapon_switched": False,
            "is_laser": False,
        }

        if not self.alive:
            return events

        was_on_ground = self.on_ground

        # ── Update powerups ──────────────────────────────────────
        self._update_powerups()

        # ── Update invincibility timer ───────────────────────────
        if self.invincible and not self.shield_active:
            self.invincible_timer -= dt
            self.invuln_flash_timer += dt
            if self.invincible_timer <= 0:
                self.invincible = False
                self.invincible_timer = 0.0
                self.invuln_flash_timer = 0.0

        # ── Effective speed ──────────────────────────────────────
        effective_accel = ACCELERATION * self.speed_multiplier
        effective_max_speed = MAX_RUN_SPEED * self.speed_multiplier

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
                    obstacles=obstacles,
                )
                self._handle_collision(collision, events)
                self._update_visual_state(inp, dt)
                return events

        # ── Horizontal movement ──────────────────────────────────
        direction = inp.move_direction()
        if direction != 0:
            self.facing = direction
        self.eye_target_x = direction

        self.physics.apply_acceleration(self.velocity, direction, effective_accel, dt)
        # Clamp to effective max speed
        self.velocity.x = max(-effective_max_speed, min(effective_max_speed, self.velocity.x))
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

        # ── Weapon switch ────────────────────────────────────────
        if inp.weapon_switch_pressed() and self.can_shoot:
            self.cycle_weapon()
            events["weapon_switched"] = True

        # ── Shooting ─────────────────────────────────────────────
        if self.can_shoot:
            bullet_data = self.shoot(inp)
            if bullet_data:
                events["shot"] = True
                events["shot_bullets"] = bullet_data
                stats = WEAPON_TYPES[self.current_weapon]
                events["is_laser"] = stats["is_continuous"]

        # ── Move and collide ─────────────────────────────────────
        collision = self.physics.move_and_collide(
            self.position, self.velocity,
            self.width, self.height, platforms, dt,
            obstacles=obstacles,
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

        # ── Speed lines ──────────────────────────────────────────
        if abs(self.velocity.x) > 100:
            self.particles.emit_speed_lines(self.center_x, self.center_y, self.velocity.x)

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
        """Update animation state, squash/stretch, and roll angle."""
        # Recover squash/stretch toward 1.0
        self.squash_stretch += (1.0 - self.squash_stretch) * min(1.0, dt * 12)

        # Run animation timer
        if abs(self.velocity.x) > 5 and self.on_ground:
            self.run_anim_timer += dt * abs(self.velocity.x) * 0.08
        else:
            self.run_anim_timer = 0.0

        # ── Rolling rotation ─────────────────────────────────────
        # angle = distance / radius  (radians), converted to degrees.
        # The Oreo radius is roughly half of PLAYER_WIDTH (~5px).
        radius = self.width / 2.0
        if self.on_ground or self.is_dashing:
            # Full roll speed on ground / dashing
            distance = self.velocity.x * dt
            angle_delta_deg = math.degrees(distance / radius) if radius > 0 else 0
            self.roll_angle += angle_delta_deg
        else:
            # In air: slow spin for floaty feel (20% of ground speed)
            distance = self.velocity.x * dt * 0.2
            angle_delta_deg = math.degrees(distance / radius) if radius > 0 else 0
            self.roll_angle += angle_delta_deg

        # Keep angle in 0-360 range
        self.roll_angle %= 360.0

        if self.is_dashing:
            self.state = PlayerState.DASHING
        elif not self.on_ground:
            self.state = PlayerState.JUMPING if self.velocity.y < 0 else PlayerState.FALLING
        elif abs(self.velocity.x) > 5:
            self.state = PlayerState.RUNNING
        else:
            self.state = PlayerState.IDLE

    def _build_oreo_surface(
        self, radius: int,
        dark_color: tuple, cream_color: tuple,
    ) -> pygame.Surface:
        """Build the Oreo cookie sprite at given radius (unrotated).

        The cookie is a circle with:
          - Dark biscuit as the main fill
          - A horizontal cream band through the center
          - Texture dots on the biscuit
          - Two eyes on the cream band
        """
        size = radius * 2 + 2  # +2 for anti-alias breathing room
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx, cy = size // 2, size // 2

        # ── Outline shadow ─────────────────────────────────
        pygame.draw.circle(surf, COL_OREO_OUTLINE, (cx, cy), radius + 1)

        # ── Dark biscuit fill ──────────────────────────────
        pygame.draw.circle(surf, dark_color, (cx, cy), radius)

        # ── Cream band (horizontal stripe through center) ─
        band_h = max(3, radius * 2 // 3)  # cream is ~1/3 of diameter
        cream_rect = pygame.Rect(cx - radius, cy - band_h // 2, radius * 2, band_h)
        # Fast circle-clipped cream band using alpha blending
        cream_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(cream_surf, (*cream_color, 255), cream_rect)
        # Create circle mask for clipping
        mask_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255), (cx, cy), radius)
        # Use the mask to clip cream to circle shape
        cream_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(cream_surf, (0, 0))

        # ── Texture dots on biscuit (above and below cream) ─
        dot_color = (
            min(255, dark_color[0] + 20),
            min(255, dark_color[1] + 20),
            min(255, dark_color[2] + 20),
        )
        # Top arc dots
        for angle_deg in range(-60, 61, 30):
            a = math.radians(angle_deg - 90)  # -90 so 0° = top
            dx = int(math.cos(a) * (radius - 2))
            dy = int(math.sin(a) * (radius - 2))
            dot_x, dot_y = cx + dx, cy + dy
            if 0 <= dot_x < size and 0 <= dot_y < size:
                surf.set_at((dot_x, dot_y), dot_color)
        # Bottom arc dots
        for angle_deg in range(-60, 61, 30):
            a = math.radians(angle_deg + 90)  # +90 = bottom
            dx = int(math.cos(a) * (radius - 2))
            dy = int(math.sin(a) * (radius - 2))
            dot_x, dot_y = cx + dx, cy + dy
            if 0 <= dot_x < size and 0 <= dot_y < size:
                surf.set_at((dot_x, dot_y), dot_color)

        # ── Eyes on the cream band ─────────────────────────
        eye_y = cy
        eye_spacing = max(2, radius // 2)
        # Left eye
        pygame.draw.circle(surf, COL_PLAYER_EYE, (cx - eye_spacing + 1, eye_y), 2)
        surf.set_at((cx - eye_spacing + 1, eye_y), (0, 0, 0))  # pupil
        # Right eye
        pygame.draw.circle(surf, COL_PLAYER_EYE, (cx + eye_spacing - 1, eye_y), 2)
        surf.set_at((cx + eye_spacing - 1, eye_y), (0, 0, 0))  # pupil

        return surf

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw the rolling Oreo cookie with rotation, squash/stretch, and effects."""
        if not self.alive:
            return

        # Invincibility flash: color cycling instead of simple blink
        if self.invincible and not self.shield_active:
            flash_phase = int(self.invuln_flash_timer * 12.5) % 3
            if flash_phase == 2:
                return  # Brief invisible frame

        # Screen position
        sx = int(self.position.x - cam_x)
        sy = int(self.position.y - cam_y)

        # ── Choose colors based on state ─────────────────────
        if self.is_dashing:
            dark_color = COL_PLAYER_DASH
            cream_color = (220, 180, 255)
        elif self.has_powerup("dash"):
            dark_color = (180, 140, 40)  # golden oreo
            cream_color = (255, 240, 180)
        elif self.invincible and not self.shield_active:
            flash_phase = int(self.invuln_flash_timer * 12.5) % 3
            if flash_phase == 0:
                dark_color = (255, 100, 100)
                cream_color = (255, 200, 200)
            else:
                dark_color = COL_OREO_DARK
                cream_color = COL_OREO_CREAM
        else:
            dark_color = COL_OREO_DARK
            cream_color = COL_OREO_CREAM

        # ── Build the cookie sprite ──────────────────────────
        # Use the larger dimension to determine radius for a nice round cookie
        base_radius = max(self.width, self.height) // 2 + 1  # ~8px
        oreo_surf = self._build_oreo_surface(base_radius, dark_color, cream_color)

        # ── Apply squash/stretch as scale ─────────────────────
        oreo_w = oreo_surf.get_width()
        oreo_h = oreo_surf.get_height()
        stretch_w = max(4, int(oreo_w * (2.0 - self.squash_stretch)))
        stretch_h = max(4, int(oreo_h * self.squash_stretch))
        stretched = pygame.transform.scale(oreo_surf, (stretch_w, stretch_h))

        # ── Rotate by roll_angle ──────────────────────────────
        # Negative because pygame rotation is counter-clockwise
        rotated = pygame.transform.rotate(stretched, -self.roll_angle)

        # ── Position: center the rotated surface on the player ─
        rot_rect = rotated.get_rect()
        center_x = sx + self.width // 2
        center_y = sy + self.height // 2
        # Run bob
        run_bob = 0
        if self.state == PlayerState.RUNNING:
            run_bob = int(math.sin(self.run_anim_timer) * 1.5)
        center_y += run_bob

        rot_rect.center = (center_x, center_y)
        surface.blit(rotated, rot_rect.topleft)

        # ── Shield visual ────────────────────────────────────────
        if self.shield_active:
            shield_r = 12
            shield_surf = pygame.Surface((shield_r * 2 + 4, shield_r * 2 + 4), pygame.SRCALPHA)
            pulse = 0.7 + 0.3 * math.sin(pygame.time.get_ticks() * 0.008)
            alpha_fill = int(40 * pulse)
            alpha_ring = int(100 * pulse)
            pygame.draw.circle(
                shield_surf, (*COL_SHIELD_RING, alpha_fill),
                (shield_r + 2, shield_r + 2), shield_r,
            )
            pygame.draw.circle(
                shield_surf, (*COL_SHIELD_RING, alpha_ring),
                (shield_r + 2, shield_r + 2), shield_r, 1,
            )
            surface.blit(shield_surf, (center_x - shield_r - 2, center_y - shield_r - 2))

        # ── Speed trail during speed boost ───────────────────────
        if self.has_powerup("dash") and abs(self.velocity.x) > 50:
            trail_color = (255, 200, 60)
            for i in range(3):
                trail_x = center_x - int(self.facing * (6 + i * 3))
                trail_y = center_y + random.randint(-2, 2)
                trail_alpha = 80 - i * 25
                trail_surf = pygame.Surface((2, 2), pygame.SRCALPHA)
                trail_surf.fill((*trail_color, max(0, trail_alpha)))
                surface.blit(trail_surf, (trail_x, trail_y))

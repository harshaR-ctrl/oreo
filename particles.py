"""
particles.py — Particle system for visual juice.

Manages particle pools for dust, sparks, dash trails, death bursts,
and coin collection effects. All particles fade and shrink over time.
"""

from __future__ import annotations
import random
import math
import pygame
from settings import (
    PARTICLE_GRAVITY, PARTICLE_FRICTION,
    COL_DUST, COL_JUMP_DUST, COL_DASH_TRAIL, COL_DEATH,
    COL_COIN_SPARKLE, COL_PLAYER_BODY,
    DASH_TRAIL_LIFETIME, PLAYER_WIDTH, PLAYER_HEIGHT,
)


class Particle:
    """A single particle with position, velocity, lifetime, size, and color."""

    __slots__ = (
        "x", "y", "vx", "vy", "lifetime", "max_lifetime",
        "size", "max_size", "color", "use_gravity",
    )

    def __init__(
        self,
        x: float, y: float,
        vx: float, vy: float,
        lifetime: float,
        size: float,
        color: tuple[int, int, int],
        use_gravity: bool = True,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.vx: float = vx
        self.vy: float = vy
        self.lifetime: float = lifetime
        self.max_lifetime: float = lifetime
        self.size: float = size
        self.max_size: float = size
        self.color: tuple[int, int, int] = color
        self.use_gravity: bool = use_gravity

    def update(self, dt: float) -> bool:
        """Update particle. Returns False when dead."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False

        if self.use_gravity:
            self.vy += PARTICLE_GRAVITY * dt
        self.vx *= PARTICLE_FRICTION
        self.vy *= PARTICLE_FRICTION

        self.x += self.vx * dt
        self.y += self.vy * dt

        # Shrink over time
        t: float = self.lifetime / self.max_lifetime
        self.size = self.max_size * t
        return True

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw the particle as a filled circle with alpha-fade."""
        if self.size < 0.5:
            return
        t: float = self.lifetime / self.max_lifetime
        alpha_factor: float = min(1.0, t * 2.0)  # fade out in the last 50%
        r = int(self.color[0] * alpha_factor)
        g = int(self.color[1] * alpha_factor)
        b = int(self.color[2] * alpha_factor)
        color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        radius = max(1, int(self.size))
        pygame.draw.circle(surface, color, (sx, sy), radius)


class DashGhost:
    """A fading rectangle ghost left behind during a dash."""

    __slots__ = ("x", "y", "width", "height", "lifetime", "max_lifetime", "color")

    def __init__(
        self,
        x: float, y: float,
        width: int, height: int,
        color: tuple[int, int, int],
        lifetime: float = DASH_TRAIL_LIFETIME,
    ) -> None:
        self.x: float = x
        self.y: float = y
        self.width: int = width
        self.height: int = height
        self.lifetime: float = lifetime
        self.max_lifetime: float = lifetime
        self.color: tuple[int, int, int] = color

    def update(self, dt: float) -> bool:
        """Returns False when expired."""
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw fading ghost rectangle."""
        t: float = max(0.0, self.lifetime / self.max_lifetime)
        alpha: int = int(120 * t)
        ghost_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ghost_surf.fill((*self.color, alpha))
        surface.blit(ghost_surf, (int(self.x - cam_x), int(self.y - cam_y)))


class ParticleSystem:
    """Manages all active particles and dash ghosts."""

    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.ghosts: list[DashGhost] = []

    def update(self, dt: float) -> None:
        """Update all particles and ghosts, removing dead ones."""
        self.particles = [p for p in self.particles if p.update(dt)]
        self.ghosts = [g for g in self.ghosts if g.update(dt)]

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Render all particles and ghosts."""
        for ghost in self.ghosts:
            ghost.draw(surface, cam_x, cam_y)
        for particle in self.particles:
            particle.draw(surface, cam_x, cam_y)

    def clear(self) -> None:
        """Remove all particles and ghosts."""
        self.particles.clear()
        self.ghosts.clear()

    # ── Emitter methods ──────────────────────────────────────────────

    def emit_landing_dust(self, x: float, y: float) -> None:
        """Burst of horizontal dust particles when landing."""
        for _ in range(random.randint(8, 12)):
            vx = random.uniform(-80, 80)
            vy = random.uniform(-30, -10)
            size = random.uniform(1.2, 2.5)
            lifetime = random.uniform(0.2, 0.45)
            self.particles.append(
                Particle(x + random.uniform(-4, 4), y,
                         vx, vy, lifetime, size, COL_DUST)
            )

    def emit_jump_dust(self, x: float, y: float) -> None:
        """Small downward burst when jumping."""
        for _ in range(random.randint(4, 6)):
            vx = random.uniform(-30, 30)
            vy = random.uniform(10, 50)
            size = random.uniform(1.0, 2.0)
            lifetime = random.uniform(0.15, 0.3)
            self.particles.append(
                Particle(x + random.uniform(-3, 3), y,
                         vx, vy, lifetime, size, COL_JUMP_DUST)
            )

    def emit_dash_ghost(self, x: float, y: float) -> None:
        """Add a ghost rectangle at the player's position."""
        self.ghosts.append(
            DashGhost(x, y, PLAYER_WIDTH, PLAYER_HEIGHT, COL_DASH_TRAIL)
        )

    def emit_death_burst(self, x: float, y: float) -> None:
        """Dramatic explosion of particles on death."""
        for _ in range(25):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 180)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(1.5, 3.5)
            lifetime = random.uniform(0.4, 0.9)
            color = random.choice([COL_DEATH, COL_PLAYER_BODY, (255, 180, 100)])
            self.particles.append(
                Particle(x, y, vx, vy, lifetime, size, color)
            )

    def emit_coin_sparkle(self, x: float, y: float) -> None:
        """Golden sparkle particles when collecting a coin."""
        for _ in range(10):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 100)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(1.0, 2.5)
            lifetime = random.uniform(0.25, 0.5)
            self.particles.append(
                Particle(x, y, vx, vy, lifetime, size, COL_COIN_SPARKLE, use_gravity=False)
            )

    def emit_wall_hit(self, x: float, y: float) -> None:
        """Small burst when hitting a wall at speed."""
        for _ in range(6):
            vx = random.uniform(-40, 40)
            vy = random.uniform(-60, -10)
            size = random.uniform(1.0, 2.0)
            lifetime = random.uniform(0.15, 0.3)
            self.particles.append(
                Particle(x, y, vx, vy, lifetime, size, COL_DUST)
            )

    def emit_menu_particle(self, width: int, height: int) -> None:
        """Emit a slow floating particle for the menu background."""
        x = random.uniform(0, width)
        y = random.uniform(0, height)
        vx = random.uniform(-8, 8)
        vy = random.uniform(-15, -5)
        size = random.uniform(1.0, 3.0)
        lifetime = random.uniform(2.0, 5.0)
        color = (
            random.randint(40, 80),
            random.randint(50, 90),
            random.randint(80, 140),
        )
        self.particles.append(
            Particle(x, y, vx, vy, lifetime, size, color, use_gravity=False)
        )

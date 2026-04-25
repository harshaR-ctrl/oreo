"""
particles.py — Enhanced particle system for visual juice.

Manages particle pools for dust, sparks, dash trails, death bursts,
coin collection effects, speed lines, screen flashes, ambient leaves,
and combo sparkles. All particles fade and shrink over time.
"""

from __future__ import annotations
import random
import math
import pygame
from settings import (
    PARTICLE_GRAVITY, PARTICLE_FRICTION, INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_DUST, COL_JUMP_DUST, COL_DASH_TRAIL, COL_DEATH,
    COL_COIN_SPARKLE, COL_PLAYER_BODY,
    DASH_TRAIL_LIFETIME, PLAYER_WIDTH, PLAYER_HEIGHT,
    COL_DASHER, COL_MARKSMAN, COL_HYBRID,
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


class SpeedLine:
    """Horizontal speed line that appears when moving fast."""

    __slots__ = ("x", "y", "length", "lifetime", "max_lifetime", "color")

    def __init__(self, x: float, y: float, length: float) -> None:
        self.x: float = x
        self.y: float = y
        self.length: float = length
        self.lifetime: float = 0.15
        self.max_lifetime: float = 0.15
        self.color: tuple = (255, 255, 255)

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        t = max(0.0, self.lifetime / self.max_lifetime)
        alpha = int(80 * t)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y)
        # Draw as thin line
        line_surf = pygame.Surface((int(self.length), 1), pygame.SRCALPHA)
        line_surf.fill((255, 255, 255, alpha))
        surface.blit(line_surf, (sx, sy))


class FloatingText:
    """Floating text that rises and fades (for milestones, combos)."""

    __slots__ = ("x", "y", "text", "color", "lifetime", "max_lifetime", "font")

    def __init__(self, x: float, y: float, text: str, color: tuple, lifetime: float = 1.5) -> None:
        self.x: float = x
        self.y: float = y
        self.text: str = text
        self.color: tuple = color
        self.lifetime: float = lifetime
        self.max_lifetime: float = lifetime
        self.font: pygame.font.Font | None = None

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        self.y -= 30 * dt  # float upward
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.font is None:
            self.font = pygame.font.Font(None, 16)
        t = max(0.0, self.lifetime / self.max_lifetime)
        # Scale color with alpha simulation
        alpha = t
        r = int(self.color[0] * alpha)
        g = int(self.color[1] * alpha)
        b = int(self.color[2] * alpha)
        color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))
        text_surf = self.font.render(self.text, True, color)
        sx = int(self.x - cam_x) - text_surf.get_width() // 2
        sy = int(self.y - cam_y)
        surface.blit(text_surf, (sx, sy))


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


class ScreenFlash:
    """Brief screen-wide flash effect."""

    __slots__ = ("lifetime", "max_lifetime", "color")

    def __init__(self, color: tuple = (255, 255, 255), duration: float = 0.1) -> None:
        self.color: tuple = color
        self.lifetime: float = duration
        self.max_lifetime: float = duration

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        return self.lifetime > 0

    def draw(self, surface: pygame.Surface) -> None:
        t = max(0.0, self.lifetime / self.max_lifetime)
        alpha = int(40 * t)
        flash_surf = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        flash_surf.fill((*self.color[:3], alpha))
        surface.blit(flash_surf, (0, 0))


class ParticleSystem:
    """Manages all active particles, ghosts, speed lines, floating texts, and flashes."""

    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.ghosts: list[DashGhost] = []
        self.speed_lines: list[SpeedLine] = []
        self.floating_texts: list[FloatingText] = []
        self.screen_flashes: list[ScreenFlash] = []

    def update(self, dt: float) -> None:
        """Update all particles and effects, removing dead ones."""
        self.particles = [p for p in self.particles if p.update(dt)]
        self.ghosts = [g for g in self.ghosts if g.update(dt)]
        self.speed_lines = [s for s in self.speed_lines if s.update(dt)]
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]
        self.screen_flashes = [f for f in self.screen_flashes if f.update(dt)]

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Render all particles and effects."""
        for ghost in self.ghosts:
            ghost.draw(surface, cam_x, cam_y)
        for sl in self.speed_lines:
            sl.draw(surface, cam_x, cam_y)
        for particle in self.particles:
            particle.draw(surface, cam_x, cam_y)
        for ft in self.floating_texts:
            ft.draw(surface, cam_x, cam_y)

    def draw_screen_effects(self, surface: pygame.Surface) -> None:
        """Draw screen-wide effects (flashes) — call without camera offset."""
        for flash in self.screen_flashes:
            flash.draw(surface)

    def clear(self) -> None:
        """Remove all particles and effects."""
        self.particles.clear()
        self.ghosts.clear()
        self.speed_lines.clear()
        self.floating_texts.clear()
        self.screen_flashes.clear()

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
        for _ in range(30):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(40, 200)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(1.5, 4.0)
            lifetime = random.uniform(0.4, 1.0)
            color = random.choice([COL_DEATH, COL_PLAYER_BODY, (255, 180, 100), (255, 255, 200)])
            self.particles.append(
                Particle(x, y, vx, vy, lifetime, size, color)
            )

    def emit_enemy_death(self, x: float, y: float, enemy_type: str = "dasher") -> None:
        """Colored burst based on enemy type."""
        color_map = {
            "dasher": [COL_DASHER, (255, 100, 100), (180, 40, 40)],
            "marksman": [COL_MARKSMAN, (200, 120, 255), (120, 60, 180)],
            "hybrid": [COL_HYBRID, (255, 180, 80), (200, 100, 20)],
        }
        colors = color_map.get(enemy_type, [COL_DEATH, (255, 180, 100)])
        for _ in range(20):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(30, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(1.0, 3.0)
            lifetime = random.uniform(0.3, 0.7)
            color = random.choice(colors)
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

    def emit_speed_lines(self, x: float, y: float, speed: float) -> None:
        """Emit horizontal speed lines when player is moving fast."""
        if abs(speed) < 100:
            return
        for _ in range(random.randint(1, 3)):
            sx = x + random.uniform(-20, -8) * (1 if speed > 0 else -1)
            sy = y + random.uniform(-8, 8)
            length = random.uniform(5, 15) * (abs(speed) / 200)
            self.speed_lines.append(SpeedLine(sx, sy, length))

    def emit_combo_sparkle(self, x: float, y: float, combo: int) -> None:
        """Sparkle effect for combo kills."""
        for _ in range(8 + combo * 3):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            size = random.uniform(1.5, 3.5)
            lifetime = random.uniform(0.3, 0.6)
            # Rainbow-ish colors for combos
            color = random.choice([
                (255, 200, 60), (60, 255, 200), (200, 60, 255),
                (255, 100, 100), (100, 255, 100), (255, 255, 100),
            ])
            self.particles.append(
                Particle(x, y, vx, vy, lifetime, size, color, use_gravity=False)
            )

    def emit_screen_flash(self, color: tuple = (255, 255, 255), duration: float = 0.1) -> None:
        """Add a screen-wide flash effect."""
        self.screen_flashes.append(ScreenFlash(color, duration))

    def add_floating_text(self, x: float, y: float, text: str,
                          color: tuple = (255, 255, 255), lifetime: float = 1.5) -> None:
        """Add floating text that rises and fades."""
        self.floating_texts.append(FloatingText(x, y, text, color, lifetime))

    def emit_ambient_leaf(self, cam_x: float, cam_y: float) -> None:
        """Emit a floating leaf particle in the visible area."""
        x = cam_x + random.uniform(-20, INTERNAL_WIDTH + 20)
        y = cam_y + random.uniform(-10, 0)
        vx = random.uniform(-15, 15)
        vy = random.uniform(10, 30)
        size = random.uniform(1.0, 2.0)
        lifetime = random.uniform(3.0, 6.0)
        # Green-brown leaf colors
        color = random.choice([
            (60, 100, 40), (80, 120, 50), (100, 80, 30),
            (70, 90, 35), (50, 80, 45),
        ])
        self.particles.append(
            Particle(x, y, vx, vy, lifetime, size, color, use_gravity=False)
        )

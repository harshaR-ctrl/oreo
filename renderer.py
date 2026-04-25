"""
renderer.py — Enhanced resolution-independent rendering pipeline.

Draws everything to a small internal surface (400×300), then scales
up to the window size (800×600) for a clean pixel aesthetic.
Features: gradient background, multi-layer parallax forest, atmospheric
fog, vignette overlay, and floating firefly lights.
"""

from __future__ import annotations
import random
import math
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT,
    COL_BG, COL_BG_GRADIENT_TOP, COL_BG_GRADIENT_BOT,
    COL_TREE_L1, COL_TREE_L2, COL_TREE_L3,
)


class Firefly:
    """A floating light that drifts and pulses."""

    __slots__ = ("x", "y", "vx", "vy", "phase", "brightness", "size")

    def __init__(self) -> None:
        self.x: float = random.uniform(0, INTERNAL_WIDTH)
        self.y: float = random.uniform(INTERNAL_HEIGHT * 0.3, INTERNAL_HEIGHT * 0.9)
        self.vx: float = random.uniform(-5, 5)
        self.vy: float = random.uniform(-3, 3)
        self.phase: float = random.uniform(0, math.pi * 2)
        self.brightness: float = random.uniform(0.3, 1.0)
        self.size: float = random.uniform(1.0, 2.0)


class ForestBackground:
    """Multi-layer parallax forest background with varied tree silhouettes."""

    def __init__(self, count: int = 50) -> None:
        self.trees: list[tuple[float, float, float, tuple[int, int, int], float, float, int]] = []
        for _ in range(count):
            x = random.uniform(0, INTERNAL_WIDTH)
            speed_layer = random.choice([1, 2, 3])
            if speed_layer == 1:
                depth = 0.15
                color = COL_TREE_L1
                width = random.uniform(15, 25)
                height = random.uniform(90, 150)
            elif speed_layer == 2:
                depth = 0.35
                color = COL_TREE_L2
                width = random.uniform(20, 32)
                height = random.uniform(110, 170)
            else:
                depth = 0.55
                color = COL_TREE_L3
                width = random.uniform(25, 40)
                height = random.uniform(130, 190)

            y = INTERNAL_HEIGHT
            tree_style = random.randint(0, 2)  # 0=pointed, 1=round, 2=bushy
            self.trees.append((x, y, depth, color, width, height, tree_style))

        self.trees.sort(key=lambda t: t[2])

        # Fireflies
        self.fireflies: list[Firefly] = [Firefly() for _ in range(12)]

        # Mountain silhouettes (far background)
        self.mountains: list[tuple[float, float, float]] = []
        mx = 0
        while mx < INTERNAL_WIDTH + 100:
            mh = random.uniform(40, 90)
            mw = random.uniform(60, 120)
            self.mountains.append((mx, mh, mw))
            mx += mw * 0.6

    def draw(
        self, surface: pygame.Surface, cam_x: float, cam_y: float, time: float
    ) -> None:
        """Draw parallax forest with mountains, trees, and fireflies."""
        # ── Distant mountains ─────────────────────────────────────
        mountain_color = (12, 18, 28)
        for mx, mh, mw in self.mountains:
            px = int(mx - cam_x * 0.05) % (INTERNAL_WIDTH + 200) - 100
            py = INTERNAL_HEIGHT
            points = [
                (px, py),
                (px + int(mw * 0.3), py - int(mh)),
                (px + int(mw * 0.5), py - int(mh * 0.9)),
                (px + int(mw * 0.7), py - int(mh * 0.7)),
                (px + int(mw), py),
            ]
            pygame.draw.polygon(surface, mountain_color, points)

        # ── Trees ─────────────────────────────────────────────────
        for sx, sy, depth, color, width, height, style in self.trees:
            px = int(sx - cam_x * depth * 0.3) % (INTERNAL_WIDTH + 100) - 50
            py = int(sy - cam_y * depth * 0.15 + 20)

            # Trunk
            trunk_w = max(3, int(width * 0.2))
            trunk_h = int(height * 0.4)
            trunk_color = (
                max(0, color[0] - 5),
                max(0, color[1] - 5),
                max(0, color[2] - 5),
            )
            pygame.draw.rect(
                surface, trunk_color,
                (px - trunk_w // 2, py - trunk_h, trunk_w, trunk_h),
            )

            # Canopy based on style
            canopy_y = py - trunk_h
            hw = int(width)

            if style == 0:  # Pointed (pine)
                for i in range(3):
                    tier_w = hw - i * int(hw * 0.2)
                    tier_h = int(height * 0.2)
                    tier_y = canopy_y - i * int(tier_h * 0.7)
                    tier_color = (
                        min(255, color[0] + i * 3),
                        min(255, color[1] + i * 4),
                        min(255, color[2] + i * 2),
                    )
                    points = [
                        (px - tier_w, tier_y),
                        (px, tier_y - tier_h),
                        (px + tier_w, tier_y),
                    ]
                    pygame.draw.polygon(surface, tier_color, points)
            elif style == 1:  # Round
                r = int(hw * 0.8)
                pygame.draw.circle(surface, color, (px, canopy_y - r // 2), r)
                lighter = (
                    min(255, color[0] + 8),
                    min(255, color[1] + 10),
                    min(255, color[2] + 5),
                )
                pygame.draw.circle(surface, lighter, (px - 2, canopy_y - r // 2 - 3), max(1, r - 4))
            else:  # Bushy (multiple circles)
                for ox, oy, r in [(-5, 0, hw // 2), (4, -3, hw // 2 - 2), (-1, -6, hw // 2 - 1)]:
                    pygame.draw.circle(surface, color, (px + ox, canopy_y + oy - hw // 3), max(2, r))

        # ── Fireflies ─────────────────────────────────────────────
        for ff in self.fireflies:
            ff.phase += 0.02
            ff.x += ff.vx * 0.01
            ff.y += ff.vy * 0.01

            # Wrap around                           
            if ff.x < -10: ff.x = INTERNAL_WIDTH + 10
            if ff.x > INTERNAL_WIDTH + 10: ff.x = -10
            if ff.y < INTERNAL_HEIGHT * 0.2: ff.vy = abs(ff.vy)
            if ff.y > INTERNAL_HEIGHT * 0.95: ff.vy = -abs(ff.vy)

            px = int(ff.x - cam_x * 0.1) % INTERNAL_WIDTH
            py = int(ff.y)
            pulse = 0.5 + 0.5 * math.sin(time * 2.0 + ff.phase)
            alpha = int(pulse * ff.brightness * 200)
            r = max(1, int(ff.size * pulse))

            glow_surf = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (200, 255, 120, alpha // 3), (r * 2, r * 2), r * 2)
            pygame.draw.circle(glow_surf, (220, 255, 150, alpha), (r * 2, r * 2), r)
            surface.blit(glow_surf, (px - r * 2, py - r * 2))


class Renderer:
    """Manages the rendering pipeline with resolution independence."""

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen: pygame.Surface = screen
        self.internal_surface: pygame.Surface = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT)
        )
        self.forest: ForestBackground = ForestBackground(50)
        self._bg_surface: pygame.Surface = self._create_gradient()
        self._vignette: pygame.Surface = self._create_vignette()
        self._fog_offset: float = 0.0

    def _create_gradient(self) -> pygame.Surface:
        """Create a cached vertical gradient background."""
        surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
        for y in range(INTERNAL_HEIGHT):
            t = y / INTERNAL_HEIGHT
            r = int(COL_BG_GRADIENT_TOP[0] + (COL_BG_GRADIENT_BOT[0] - COL_BG_GRADIENT_TOP[0]) * t)
            g = int(COL_BG_GRADIENT_TOP[1] + (COL_BG_GRADIENT_BOT[1] - COL_BG_GRADIENT_TOP[1]) * t)
            b = int(COL_BG_GRADIENT_TOP[2] + (COL_BG_GRADIENT_BOT[2] - COL_BG_GRADIENT_TOP[2]) * t)
            pygame.draw.line(surf, (r, g, b), (0, y), (INTERNAL_WIDTH, y))
        return surf

    def _create_vignette(self) -> pygame.Surface:
        """Create a vignette overlay for cinematic darkened edges."""
        surf = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
        max_r = math.sqrt(cx * cx + cy * cy)
        for radius in range(int(max_r), 0, -3):
            t = radius / max_r
            if t > 0.6:  # Only darken the edges
                alpha = int((t - 0.6) / 0.4 * 60)
                pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), radius)
        return surf

    def _draw_fog(self, surface: pygame.Surface, time: float) -> None:
        """Draw semi-transparent drifting fog layer."""
        fog_surf = pygame.Surface((INTERNAL_WIDTH, 40), pygame.SRCALPHA)
        self._fog_offset = (time * 8) % INTERNAL_WIDTH

        for i in range(0, INTERNAL_WIDTH + 40, 40):
            x = int(i - self._fog_offset) % (INTERNAL_WIDTH + 40) - 20
            wave = math.sin(time * 0.3 + i * 0.05) * 5
            alpha = int(12 + 8 * math.sin(time * 0.5 + i * 0.1))
            fog_rect = pygame.Rect(x, int(wave), 50, 30)
            pygame.draw.ellipse(fog_surf, (180, 200, 180, alpha), fog_rect)

        surface.blit(fog_surf, (0, INTERNAL_HEIGHT - 80))

    def begin_frame(self, cam_x: float, cam_y: float, time: float) -> pygame.Surface:
        """Clear the internal surface with background. Returns it for drawing."""
        self.internal_surface.blit(self._bg_surface, (0, 0))
        self.forest.draw(self.internal_surface, cam_x, cam_y, time)
        self._draw_fog(self.internal_surface, time)
        return self.internal_surface

    def end_frame(self) -> None:
        """Apply vignette, scale internal surface to window, and flip."""
        # Apply vignette
        self.internal_surface.blit(self._vignette, (0, 0))

        scaled = pygame.transform.scale(
            self.internal_surface, (WINDOW_WIDTH, WINDOW_HEIGHT)
        )
        self.screen.blit(scaled, (0, 0))
        pygame.display.flip()

    def get_surface(self) -> pygame.Surface:
        """Get the internal drawing surface."""
        return self.internal_surface

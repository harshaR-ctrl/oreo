"""
powerups.py — Collectible power-up system.

BasePowerUp provides common bob animation and glow. Subclasses define
unique visuals and a `type` string consumed by PlayingState.
spawn_random_loot() creates a weighted-random pickup.
"""

from __future__ import annotations
import math
import random
import pygame
from settings import (
    COL_POWERUP_GUN, COL_POWERUP_GLOW,
    COL_HEART_FULL, COL_DASH_POWERUP, COL_MAGNET,
    COL_WORMHOLE, COL_BLACKHOLE, COL_VOID, COL_SHIELD_RING,
    COL_WEAPON_PICKUP,
    LOOT_WEIGHTS,
)


# ─── Base class ───────────────────────────────────────────────────────

class BasePowerUp(pygame.sprite.Sprite):
    """Base collectible with bobbing animation and glow.

    Subclasses must set:
        self.powerup_type: str
        self.color: tuple
    and override draw() for unique visuals.
    """

    SIZE: int = 7

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image: pygame.Surface = pygame.Surface(
            (self.SIZE, self.SIZE), pygame.SRCALPHA,
        )
        self.x: float = float(x)
        self.y: float = float(y)
        self.rect: pygame.Rect = pygame.Rect(
            x - self.SIZE // 2, y - self.SIZE // 2,
            self.SIZE, self.SIZE,
        )
        self.collected: bool = False
        self.bob_timer: float = random.uniform(0, math.pi * 2)
        self.powerup_type: str = "generic"
        self.color: tuple = COL_POWERUP_GUN

    def update(self, dt: float) -> None:
        """Animate the bobbing motion."""
        if self.collected:
            return
        self.bob_timer += dt * 2.5
        bob_y = int(math.sin(self.bob_timer) * 3)
        self.rect.x = int(self.x) - self.SIZE // 2
        self.rect.y = int(self.y) - self.SIZE // 2 + bob_y

    def _draw_glow(
        self, surface: pygame.Surface, sx: int, sy: int,
        glow_color: tuple | None = None,
    ) -> None:
        """Draw pulsing outer glow common to all pickups."""
        glow_alpha = int(3 + 2 * math.sin(self.bob_timer * 1.5))
        gc = glow_color or COL_POWERUP_GLOW
        pygame.draw.circle(surface, gc, (sx, sy), self.SIZE // 2 + glow_alpha)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Default draw — subclasses override for unique shapes."""
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy)
        pygame.draw.circle(surface, self.color, (sx, sy), self.SIZE // 2)


# ─── Heart pickup ─────────────────────────────────────────────────────

class HeartPickup(BasePowerUp):
    """Restores 1 life if below max."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "heart"
        self.color = COL_HEART_FULL

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (180, 40, 60))
        # Heart shape: two small circles + triangle
        r = self.SIZE // 3 + 1
        pygame.draw.circle(surface, self.color, (sx - r // 2, sy - 1), r)
        pygame.draw.circle(surface, self.color, (sx + r // 2, sy - 1), r)
        pygame.draw.polygon(surface, self.color, [
            (sx - r - 1, sy), (sx + r + 1, sy), (sx, sy + r + 2),
        ])
        # Shine
        pygame.draw.circle(surface, (255, 200, 200), (sx - 1, sy - 2), 1)


# ─── Dash pickup ──────────────────────────────────────────────────────

class DashPickup(BasePowerUp):
    """Grants 2x speed multiplier for a duration."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "dash"
        self.color = COL_DASH_POWERUP

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (200, 160, 40))
        # Lightning bolt shape
        points = [
            (sx - 1, sy - 4), (sx + 2, sy - 1),
            (sx, sy - 1), (sx + 1, sy + 4),
            (sx - 2, sy + 1), (sx, sy + 1),
        ]
        pygame.draw.polygon(surface, self.color, points)


# ─── Magnet pickup ────────────────────────────────────────────────────

class MagnetPickup(BasePowerUp):
    """Attracts nearby coins and powerups toward the player."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "magnet"
        self.color = COL_MAGNET

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (200, 80, 200))
        # U-magnet shape
        pygame.draw.arc(
            surface, self.color,
            (sx - 3, sy - 1, 7, 8), math.pi, 2 * math.pi, 2,
        )
        pygame.draw.line(surface, (255, 60, 60), (sx - 3, sy - 1), (sx - 3, sy + 2), 2)
        pygame.draw.line(surface, (60, 60, 255), (sx + 3, sy - 1), (sx + 3, sy + 2), 2)


# ─── Wormhole pickup ─────────────────────────────────────────────────

class WormholePickup(BasePowerUp):
    """Instant teleport 5 tiles forward with safety check."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "wormhole"
        self.color = COL_WORMHOLE

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (60, 200, 140))
        # Swirl / portal ring
        r = self.SIZE // 2
        pygame.draw.circle(surface, self.color, (sx, sy), r, 2)
        inner_r = max(1, r - 2)
        pygame.draw.circle(surface, (180, 255, 220), (sx, sy), inner_r)
        # Dot center
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 1)


# ─── Blackhole pickup ────────────────────────────────────────────────

class BlackholePickup(BasePowerUp):
    """Absorbs enemy bullets — they are destroyed on contact."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "blackhole"
        self.color = COL_BLACKHOLE

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (60, 0, 100))
        # Dark sphere with purple ring
        r = self.SIZE // 2
        pygame.draw.circle(surface, (20, 0, 40), (sx, sy), r)
        pygame.draw.circle(surface, (120, 40, 200), (sx, sy), r, 1)
        # Event horizon shimmer
        pygame.draw.circle(surface, (80, 20, 140), (sx - 1, sy - 1), 1)


# ─── Void pickup ──────────────────────────────────────────────────────

class VoidPickup(BasePowerUp):
    """Reflects enemy bullets back as friendly bullets."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "void"
        self.color = COL_VOID

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (160, 40, 200))
        # Inverted diamond with arrows
        r = self.SIZE // 2
        points = [(sx, sy - r), (sx + r, sy), (sx, sy + r), (sx - r, sy)]
        pygame.draw.polygon(surface, self.color, points)
        pygame.draw.polygon(surface, (255, 180, 255), points, 1)
        # Center dot
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy), 1)


# ─── Shield pickup ───────────────────────────────────────────────────

class ShieldPickup(BasePowerUp):
    """Grants invincibility with a visible shield ring."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "shield"
        self.color = COL_SHIELD_RING

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (60, 160, 220))
        # Shield icon: circle with cross
        r = self.SIZE // 2
        pygame.draw.circle(surface, self.color, (sx, sy), r, 2)
        pygame.draw.circle(surface, (180, 240, 255), (sx, sy), r - 1)
        pygame.draw.line(surface, self.color, (sx - 2, sy), (sx + 2, sy), 1)
        pygame.draw.line(surface, self.color, (sx, sy - 2), (sx, sy + 2), 1)


# ─── Weapon pickup ───────────────────────────────────────────────────

class WeaponPickup(BasePowerUp):
    """Unlocks the next weapon in the player's arsenal."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__(x, y)
        self.powerup_type = "weapon"
        self.color = COL_WEAPON_PICKUP

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 3)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        self._draw_glow(surface, sx, sy, (80, 200, 160))
        # Gun icon: barrel + grip
        bw, bh = self.SIZE - 2, 3
        bx = sx - bw // 2
        by = sy - bh // 2
        pygame.draw.rect(surface, self.color, (bx, by, bw, bh))
        # Grip
        gw, gh = 2, 3
        pygame.draw.rect(surface, self.color, (sx - gw // 2, by + bh, gw, gh))
        # Muzzle flash dot
        pygame.draw.circle(surface, (255, 255, 255), (bx + bw, sy), 1)


# ─── Loot spawner ────────────────────────────────────────────────────

_LOOT_CLASSES: dict[str, type] = {
    "heart":     HeartPickup,
    "dash":      DashPickup,
    "magnet":    MagnetPickup,
    "wormhole":  WormholePickup,
    "blackhole": BlackholePickup,
    "void":      VoidPickup,
    "shield":    ShieldPickup,
    "weapon":    WeaponPickup,
}


def spawn_random_loot(x: int, y: int) -> BasePowerUp:
    """Create a weighted-random powerup pickup at (x, y).

    Uses random.choices() with LOOT_WEIGHTS for rarity control.
    Hearts are rare (weight 5) while Dash is common (weight 20).
    """
    types = list(LOOT_WEIGHTS.keys())
    weights = [LOOT_WEIGHTS[t] for t in types]
    chosen = random.choices(types, weights=weights, k=1)[0]
    cls = _LOOT_CLASSES[chosen]
    return cls(x, y)

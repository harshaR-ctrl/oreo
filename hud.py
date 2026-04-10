"""
hud.py — Heads-up display overlay.

Renders score, level info, hearts, active powerup indicators,
dash cooldown, and current weapon. Uses minimal text to avoid
cluttering the small internal resolution.
"""

from __future__ import annotations
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TEXT, COL_TEXT_DIM, COL_TEXT_ACCENT, COL_PLAYER_DASH,
    DASH_COOLDOWN,
    COL_HEART_FULL, COL_HEART_EMPTY,
    COL_DASH_POWERUP, COL_MAGNET, COL_SHIELD_RING,
    COL_BLACKHOLE, COL_VOID,
    MAX_LIVES,
)


# ─── Powerup display colors ──────────────────────────────────────────
_POWERUP_COLORS: dict[str, tuple] = {
    "dash":      COL_DASH_POWERUP,
    "magnet":    COL_MAGNET,
    "shield":    COL_SHIELD_RING,
    "blackhole": (120, 40, 200),
    "void":      COL_VOID,
}

_WEAPON_LABELS: dict[str, str] = {
    "pistol":  "PISTOL",
    "shotgun": "SHOTGUN",
    "rapid":   "RAPID",
    "laser":   "LASER",
}


class HUD:
    """Full HUD: score, hearts, powerup icons, weapon, dash indicator."""

    def __init__(self) -> None:
        self._font: pygame.font.Font | None = None
        self._font_small: pygame.font.Font | None = None

    def _ensure_fonts(self) -> None:
        """Lazy-init fonts (must be called after pygame.init)."""
        if self._font is None:
            self._font = pygame.font.Font(None, 14)
            self._font_small = pygame.font.Font(None, 11)

    def draw(
        self,
        surface: pygame.Surface,
        score: int,
        distance: int,
        dash_cooldown: float,
        coins_collected: int,
        player=None,
    ) -> None:
        """Draw the HUD overlay."""
        self._ensure_fonts()

        # Score — top left
        score_text = self._font.render(f"SCORE {score}", True, COL_TEXT)
        surface.blit(score_text, (4, 4))

        # Distance — top right
        dist_text = self._font_small.render(f"{distance}m", True, COL_TEXT_DIM)
        surface.blit(dist_text, (INTERNAL_WIDTH - dist_text.get_width() - 4, 5))

        # ── Hearts — below score ─────────────────────────────────
        if player is not None:
            self._draw_hearts(surface, player.lives, player.max_lives)
            self._draw_active_powerups(surface, player)
            self._draw_weapon_indicator(surface, player)

        # Dash cooldown indicator — bottom left
        if dash_cooldown > 0:
            bar_width = 20
            bar_height = 3
            fill = int(bar_width * (1.0 - dash_cooldown / DASH_COOLDOWN))
            bx, by = 4, INTERNAL_HEIGHT - 10
            pygame.draw.rect(surface, (40, 40, 50), (bx, by, bar_width, bar_height))
            pygame.draw.rect(surface, COL_PLAYER_DASH, (bx, by, fill, bar_height))
            dash_label = self._font_small.render("DASH", True, COL_TEXT_DIM)
            surface.blit(dash_label, (bx, by - 9))
        else:
            dash_label = self._font_small.render("DASH ●", True, COL_TEXT_ACCENT)
            surface.blit(dash_label, (4, INTERNAL_HEIGHT - 17))

    def _draw_hearts(
        self, surface: pygame.Surface, lives: int, max_lives: int,
    ) -> None:
        """Draw a row of heart icons. Full if i < lives, empty otherwise."""
        start_x = 4
        start_y = 16
        spacing = 10

        for i in range(max_lives):
            hx = start_x + i * spacing
            hy = start_y
            color = COL_HEART_FULL if i < lives else COL_HEART_EMPTY

            # Heart shape: two small circles + triangle
            r = 2
            pygame.draw.circle(surface, color, (hx + r, hy), r)
            pygame.draw.circle(surface, color, (hx + r + 3, hy), r)
            pygame.draw.polygon(surface, color, [
                (hx, hy + 1),
                (hx + r + 3 + r, hy + 1),
                (hx + r + 1, hy + 5),
            ])

    def _draw_active_powerups(self, surface: pygame.Surface, player) -> None:
        """Draw small colored dots for each active powerup with time bars."""
        if not player.active_powerups:
            return

        now = pygame.time.get_ticks()
        x_start = INTERNAL_WIDTH - 8
        y_pos = 18

        for ptype, expiry in player.active_powerups.items():
            color = _POWERUP_COLORS.get(ptype, COL_TEXT_DIM)
            # Dot
            pygame.draw.circle(surface, color, (x_start, y_pos), 3)
            # Time remaining bar
            remaining = max(0, expiry - now)
            # Normalize to 0-1 (assume max ~10s = 10000ms)
            frac = min(1.0, remaining / 10000.0)
            bar_w = int(12 * frac)
            pygame.draw.rect(surface, color, (x_start - 16, y_pos - 1, bar_w, 2))

            y_pos += 8

    def _draw_weapon_indicator(self, surface: pygame.Surface, player) -> None:
        """Draw the current weapon name in the bottom-right corner."""
        if not player.can_shoot:
            return
        label = _WEAPON_LABELS.get(player.current_weapon, "???")
        text = self._font_small.render(label, True, COL_TEXT_ACCENT)
        surface.blit(text, (INTERNAL_WIDTH - text.get_width() - 4, INTERNAL_HEIGHT - 12))

    def draw_controls_hint(self, surface: pygame.Surface) -> None:
        """Draw control hints at the bottom of the screen."""
        self._ensure_fonts()
        hint = self._font_small.render(
            "←→ MOVE  SPACE JUMP  SHIFT DASH  F SHOOT  Q WEAPON", True, COL_TEXT_DIM
        )
        surface.blit(
            hint,
            ((INTERNAL_WIDTH - hint.get_width()) // 2, INTERNAL_HEIGHT - 10),
        )

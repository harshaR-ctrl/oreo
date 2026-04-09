"""
hud.py — Heads-up display overlay.

Renders score, level info, dash cooldown indicator, and control hints.
Uses minimal text to avoid cluttering the small internal resolution.
"""

from __future__ import annotations
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TEXT, COL_TEXT_DIM, COL_TEXT_ACCENT, COL_PLAYER_DASH,
    DASH_COOLDOWN,
)


class HUD:
    """Minimal HUD for the game."""

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
        level: int,
        dash_cooldown: float,
        coins_collected: int,
    ) -> None:
        """Draw the HUD overlay."""
        self._ensure_fonts()

        # Score — top left
        score_text = self._font.render(f"SCORE {score}", True, COL_TEXT)
        surface.blit(score_text, (4, 4))

        # Level — top right
        level_text = self._font_small.render(f"LV {level}", True, COL_TEXT_DIM)
        surface.blit(level_text, (INTERNAL_WIDTH - level_text.get_width() - 4, 5))

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

    def draw_controls_hint(self, surface: pygame.Surface) -> None:
        """Draw control hints at the bottom of the screen."""
        self._ensure_fonts()
        hint = self._font_small.render(
            "←→ MOVE  SPACE JUMP  SHIFT DASH", True, COL_TEXT_DIM
        )
        surface.blit(
            hint,
            ((INTERNAL_WIDTH - hint.get_width()) // 2, INTERNAL_HEIGHT - 10),
        )

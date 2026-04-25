"""
hud.py — Enhanced heads-up display overlay.

Renders score with rolling animation, hearts, active powerup indicators,
dash cooldown, current weapon, combo counter, kill counter, difficulty
indicator, and distance milestones. Uses semi-transparent panel backgrounds.
"""

from __future__ import annotations
import math
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TEXT, COL_TEXT_DIM, COL_TEXT_ACCENT, COL_PLAYER_DASH,
    DASH_COOLDOWN,
    COL_HEART_FULL, COL_HEART_EMPTY,
    COL_DASH_POWERUP, COL_MAGNET, COL_SHIELD_RING,
    COL_BLACKHOLE, COL_VOID,
    MAX_LIVES, DIFFICULTY_PRESETS,
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
    """Full HUD: score, hearts, powerup icons, weapon, dash, combo, difficulty."""

    def __init__(self) -> None:
        self._font: pygame.font.Font | None = None
        self._font_small: pygame.font.Font | None = None
        self._font_combo: pygame.font.Font | None = None

        # Score animation
        self._display_score: float = 0.0
        self._target_score: int = 0

    def _ensure_fonts(self) -> None:
        """Lazy-init fonts (must be called after pygame.init)."""
        if self._font is None:
            self._font = pygame.font.Font(None, 14)
            self._font_small = pygame.font.Font(None, 11)
            self._font_combo = pygame.font.Font(None, 18)

    def draw(
        self,
        surface: pygame.Surface,
        score: int,
        distance: int,
        dash_cooldown: float,
        coins_collected: int,
        player=None,
        combo: int = 0,
        enemies_killed: int = 0,
        difficulty_name: str = "normal",
        time_survived: float = 0.0,
    ) -> None:
        """Draw the HUD overlay with all info panels."""
        self._ensure_fonts()

        # ── Score rolling animation ──────────────────────────────
        self._target_score = score
        score_diff = self._target_score - self._display_score
        self._display_score += score_diff * 0.15  # smooth roll
        if abs(score_diff) < 1:
            self._display_score = float(self._target_score)

        display_score = int(self._display_score)

        # ── Top-left panel background ────────────────────────────
        panel_surf = pygame.Surface((90, 28), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 80))
        surface.blit(panel_surf, (2, 2))

        # Score
        score_text = self._font.render(f"SCORE {display_score}", True, COL_TEXT)
        surface.blit(score_text, (5, 4))

        # Distance
        dist_text = self._font_small.render(f"{distance}m", True, COL_TEXT_DIM)
        surface.blit(dist_text, (5, 16))

        # Time survived
        minutes = int(time_survived) // 60
        seconds = int(time_survived) % 60
        time_text = self._font_small.render(f"{minutes}:{seconds:02d}", True, COL_TEXT_DIM)
        surface.blit(time_text, (40, 16))

        # ── Top-right panel: difficulty + kill count ─────────────
        diff_config = DIFFICULTY_PRESETS.get(difficulty_name, DIFFICULTY_PRESETS["normal"])
        diff_color = diff_config.get("color", COL_TEXT_DIM)
        diff_label = diff_config.get("label", "NORMAL")

        # Panel background
        panel_r = pygame.Surface((55, 28), pygame.SRCALPHA)
        panel_r.fill((0, 0, 0, 80))
        surface.blit(panel_r, (INTERNAL_WIDTH - 57, 2))

        diff_text = self._font_small.render(diff_label, True, diff_color)
        surface.blit(diff_text, (INTERNAL_WIDTH - diff_text.get_width() - 5, 4))

        # Kill count
        kill_text = self._font_small.render(f"K:{enemies_killed}", True, COL_TEXT_DIM)
        surface.blit(kill_text, (INTERNAL_WIDTH - kill_text.get_width() - 5, 16))

        # ── Hearts — below top-left panel ────────────────────────
        if player is not None:
            self._draw_hearts(surface, player.lives, player.max_lives)
            self._draw_active_powerups(surface, player)
            self._draw_weapon_indicator(surface, player)

        # ── Combo counter ────────────────────────────────────────
        if combo > 1:
            self._draw_combo(surface, combo)

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
        """Draw a row of heart icons with glow for full hearts."""
        start_x = 4
        start_y = 34
        spacing = 10

        for i in range(max_lives):
            hx = start_x + i * spacing
            hy = start_y
            is_full = i < lives
            color = COL_HEART_FULL if is_full else COL_HEART_EMPTY

            # Heart shape: two small circles + triangle
            r = 2
            pygame.draw.circle(surface, color, (hx + r, hy), r)
            pygame.draw.circle(surface, color, (hx + r + 3, hy), r)
            pygame.draw.polygon(surface, color, [
                (hx, hy + 1),
                (hx + r + 3 + r, hy + 1),
                (hx + r + 1, hy + 5),
            ])

            # Subtle glow for full hearts
            if is_full:
                glow_surf = pygame.Surface((12, 10), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 60, 80, 30), (6, 4), 5)
                surface.blit(glow_surf, (hx - 1, hy - 3))

    def _draw_active_powerups(self, surface: pygame.Surface, player) -> None:
        """Draw small colored dots for each active powerup with time bars."""
        if not player.active_powerups:
            return

        now = pygame.time.get_ticks()
        x_start = INTERNAL_WIDTH - 8
        y_pos = 34

        for ptype, expiry in player.active_powerups.items():
            color = _POWERUP_COLORS.get(ptype, COL_TEXT_DIM)
            # Dot with glow
            glow_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, 40), (5, 5), 5)
            surface.blit(glow_surf, (x_start - 5, y_pos - 5))
            pygame.draw.circle(surface, color, (x_start, y_pos), 3)

            # Time remaining bar
            remaining = max(0, expiry - now)
            frac = min(1.0, remaining / 10000.0)
            bar_w = int(12 * frac)
            pygame.draw.rect(surface, (*color[:3],), (x_start - 16, y_pos - 1, bar_w, 2))

            # Label
            label = self._font_small.render(ptype[:3].upper(), True, color)
            surface.blit(label, (x_start - 16 - label.get_width() - 2, y_pos - 4))

            y_pos += 10

    def _draw_weapon_indicator(self, surface: pygame.Surface, player) -> None:
        """Draw the current weapon name in the bottom-right corner with panel."""
        if not player.can_shoot:
            return
        label = _WEAPON_LABELS.get(player.current_weapon, "???")

        # Panel background
        text = self._font_small.render(label, True, COL_TEXT_ACCENT)
        panel_w = text.get_width() + 6
        panel_surf = pygame.Surface((panel_w, 12), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 80))
        px = INTERNAL_WIDTH - panel_w - 3
        py = INTERNAL_HEIGHT - 14
        surface.blit(panel_surf, (px, py))
        surface.blit(text, (px + 3, py + 1))

    def _draw_combo(self, surface: pygame.Surface, combo: int) -> None:
        """Draw combo counter in the center-top."""
        # Combo colors escalate
        if combo >= 5:
            combo_color = (255, 60, 60)
        elif combo >= 3:
            combo_color = (255, 200, 60)
        else:
            combo_color = (100, 255, 200)

        text = f"x{combo}!"
        combo_surf = self._font_combo.render(text, True, combo_color)

        # Pulsing scale effect (simulated with glow)
        cx = INTERNAL_WIDTH // 2 - combo_surf.get_width() // 2
        cy = 45

        # Glow behind
        glow_surf = pygame.Surface((combo_surf.get_width() + 8, combo_surf.get_height() + 4), pygame.SRCALPHA)
        glow_color = (*combo_color, 40)
        pygame.draw.rect(glow_surf, glow_color, (0, 0, glow_surf.get_width(), glow_surf.get_height()))
        surface.blit(glow_surf, (cx - 4, cy - 2))

        surface.blit(combo_surf, (cx, cy))

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

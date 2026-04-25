"""
states.py — Complete game state machine with full menu system.

States: Menu, DifficultySelect, HighScores, Controls, Playing, Pause, GameOver.
Each state implements enter(), exit(), update(dt), and render(surface).
The PlayingState orchestrates all game systems including the powerup
manager, weapon strategy, lives/damage, shield, combos, and milestones.
"""

from __future__ import annotations
import math
import random
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TEXT, COL_TEXT_DIM, COL_TEXT_ACCENT, COL_PLAYER_BODY,
    COL_BG, COIN_SCORE, COL_MENU_SELECTED, COL_MENU_UNSELECTED,
    COL_OREO_DARK, COL_OREO_CREAM,
    PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
    MAGNET_RANGE, MAGNET_FORCE,
    WORMHOLE_TILES, TILE_SIZE,
    POWERUP_DASH_DURATION, POWERUP_MAGNET_DURATION,
    POWERUP_SHIELD_DURATION, POWERUP_BLACKHOLE_DURATION,
    POWERUP_VOID_DURATION,
    COMBO_WINDOW, COMBO_BONUS_PER_LEVEL,
    MILESTONE_DISTANCES, MILESTONE_BONUS,
    DIFFICULTY_PRESETS, DIFFICULTY_ORDER, DEFAULT_DIFFICULTY,
    GAME_VERSION,
)
from input_handler import InputHandler
from physics import PhysicsEngine
from camera import Camera
from particles import ParticleSystem
from player import Player
from level import LevelGenerator
from hud import HUD
from sounds import SoundManager
from projectiles import Projectile, PlayerBullet, FriendlyBullet, LaserBeam
from enemies import Dasher, Marksman, Hybrid
from highscores import load_scores, add_score, get_high_score


class GameState:
    """Base class for game states."""

    def enter(self) -> None:
        """Called when transitioning into this state."""
        pass

    def exit(self) -> None:
        """Called when transitioning out of this state."""
        pass

    def update(self, inp: InputHandler, dt: float) -> str | None:
        """Update logic. Returns new state name or None to stay."""
        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        """Draw this state to the internal surface."""
        pass


# ─── Helper: draw animated background used by all menu screens ───────

def _draw_menu_bg(surface: pygame.Surface, particles: ParticleSystem,
                   time: float, cam_x: float = 0, cam_y: float = 0) -> None:
    """Draw particles and subtle animated elements common to menu screens."""
    particles.draw(surface, cam_x, cam_y)


def _draw_oreo_logo(surface: pygame.Surface, cx: int, cy: int, time: float) -> None:
    """Draw a rotating Oreo cookie logo at the given center."""
    # Outer dark biscuit (circle)
    r = 18
    pygame.draw.circle(surface, COL_OREO_DARK, (cx, cy), r)
    pygame.draw.circle(surface, (50, 35, 30), (cx, cy), r, 1)

    # Cream ring
    cream_r = r - 4
    pygame.draw.circle(surface, COL_OREO_CREAM, (cx, cy), cream_r)

    # Inner dark biscuit
    inner_r = cream_r - 3
    pygame.draw.circle(surface, COL_OREO_DARK, (cx, cy), inner_r)

    # Decorative dots on inner biscuit (rotate with time)
    for i in range(6):
        angle = time * 0.5 + i * math.pi / 3
        dx = int(math.cos(angle) * (inner_r - 3))
        dy = int(math.sin(angle) * (inner_r - 3))
        pygame.draw.circle(surface, (55, 40, 35), (cx + dx, cy + dy), 1)

    # Center dot
    pygame.draw.circle(surface, COL_OREO_CREAM, (cx, cy), 2)

    # Glow
    pulse = 0.5 + 0.5 * math.sin(time * 2.0)
    glow_surf = pygame.Surface((r * 3, r * 3), pygame.SRCALPHA)
    glow_alpha = int(20 * pulse)
    pygame.draw.circle(glow_surf, (255, 220, 180, glow_alpha),
                       (r * 3 // 2, r * 3 // 2), r + 5)
    surface.blit(glow_surf, (cx - r * 3 // 2, cy - r * 3 // 2))


# ═══════════════════════════════════════════════════════════════════════
# MENU STATE
# ═══════════════════════════════════════════════════════════════════════

class MenuState(GameState):
    """Title screen with Oreo logo, menu options, and floating particles."""

    MENU_ITEMS = ["PLAY", "DIFFICULTY", "HIGH SCORES", "CONTROLS", "QUIT"]

    def __init__(self, particles: ParticleSystem, sound: SoundManager) -> None:
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.title_font: pygame.font.Font | None = None
        self.menu_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.timer: float = 0.0
        self.selected: int = 0
        self.difficulty_name: str = DEFAULT_DIFFICULTY

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 28)
            self.menu_font = pygame.font.Font(None, 16)
            self.hint_font = pygame.font.Font(None, 11)

    def enter(self) -> None:
        self.particles.clear()
        self.timer = 0.0
        self.selected = 0

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        # Spawn ambient particles
        if random.random() < 0.15:
            self.particles.emit_menu_particle(INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.particles.update(dt)

        if self.timer < 0.3:
            return None

        # Menu navigation
        if inp.menu_down():
            self.selected = (self.selected + 1) % len(self.MENU_ITEMS)
            self.sound.play("menu_nav")
        if inp.menu_up():
            self.selected = (self.selected - 1) % len(self.MENU_ITEMS)
            self.sound.play("menu_nav")

        if inp.confirm_pressed():
            self.sound.play("menu_select")
            item = self.MENU_ITEMS[self.selected]
            if item == "PLAY":
                return "playing"
            elif item == "DIFFICULTY":
                return "difficulty"
            elif item == "HIGH SCORES":
                return "highscores"
            elif item == "CONTROLS":
                return "controls"
            elif item == "QUIT":
                return "quit"

        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()

        # Draw particles behind everything
        _draw_menu_bg(surface, self.particles, time)

        # Oreo logo
        logo_y = INTERNAL_HEIGHT // 5
        _draw_oreo_logo(surface, INTERNAL_WIDTH // 2, logo_y, time)

        # Title
        title_y = logo_y + 28
        title_text = "OREO"
        title_surf = self.title_font.render(title_text, True, COL_OREO_CREAM)
        tx = (INTERNAL_WIDTH - title_surf.get_width()) // 2
        # Glow
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            glow = self.title_font.render(title_text, True, (80, 60, 40))
            surface.blit(glow, (tx + ox, title_y + oy))
        surface.blit(title_surf, (tx, title_y))

        # Subtitle
        sub = self.menu_font.render("RUNNER", True, COL_TEXT)
        surface.blit(sub, ((INTERNAL_WIDTH - sub.get_width()) // 2, title_y + 22))

        # Menu items
        menu_start_y = title_y + 50
        for i, item in enumerate(self.MENU_ITEMS):
            is_selected = (i == self.selected)
            if is_selected:
                # Selection indicator
                pulse = 0.8 + 0.2 * math.sin(time * 5.0)
                color = (
                    int(COL_MENU_SELECTED[0] * pulse),
                    int(COL_MENU_SELECTED[1] * pulse),
                    int(COL_MENU_SELECTED[2] * pulse),
                )
                prefix = "► "
            else:
                color = COL_MENU_UNSELECTED
                prefix = "  "

            text = self.menu_font.render(f"{prefix}{item}", True, color)
            iy = menu_start_y + i * 18
            surface.blit(text, ((INTERNAL_WIDTH - text.get_width()) // 2, iy))

            # Selection highlight bar
            if is_selected:
                bar_surf = pygame.Surface((text.get_width() + 10, 14), pygame.SRCALPHA)
                bar_surf.fill((255, 200, 60, 20))
                surface.blit(bar_surf, ((INTERNAL_WIDTH - text.get_width()) // 2 - 5, iy - 1))

        # Difficulty preview
        diff_cfg = DIFFICULTY_PRESETS.get(self.difficulty_name, DIFFICULTY_PRESETS[DEFAULT_DIFFICULTY])
        diff_label = f"Difficulty: {diff_cfg['label']}"
        diff_text = self.hint_font.render(diff_label, True, diff_cfg["color"])
        surface.blit(diff_text, ((INTERNAL_WIDTH - diff_text.get_width()) // 2, INTERNAL_HEIGHT - 28))

        # Version
        ver = self.hint_font.render(f"v{GAME_VERSION}", True, (60, 60, 80))
        surface.blit(ver, (INTERNAL_WIDTH - ver.get_width() - 4, INTERNAL_HEIGHT - 10))

        # High score
        hs = get_high_score()
        if hs > 0:
            hs_text = self.hint_font.render(f"HIGH SCORE: {hs}", True, COL_TEXT_DIM)
            surface.blit(hs_text, ((INTERNAL_WIDTH - hs_text.get_width()) // 2, INTERNAL_HEIGHT - 16))


# ═══════════════════════════════════════════════════════════════════════
# DIFFICULTY SELECT STATE
# ═══════════════════════════════════════════════════════════════════════

class DifficultySelectState(GameState):
    """Select difficulty level with visual descriptions."""

    def __init__(self, particles: ParticleSystem, sound: SoundManager) -> None:
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.title_font: pygame.font.Font | None = None
        self.menu_font: pygame.font.Font | None = None
        self.desc_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.selected: int = 1  # Default to Normal
        self.timer: float = 0.0
        self.chosen_difficulty: str = DEFAULT_DIFFICULTY

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 22)
            self.menu_font = pygame.font.Font(None, 16)
            self.desc_font = pygame.font.Font(None, 12)
            self.hint_font = pygame.font.Font(None, 11)

    def enter(self) -> None:
        self.timer = 0.0
        # Set selection to current difficulty
        try:
            self.selected = DIFFICULTY_ORDER.index(self.chosen_difficulty)
        except ValueError:
            self.selected = 1

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        if random.random() < 0.1:
            self.particles.emit_menu_particle(INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.particles.update(dt)

        if self.timer < 0.2:
            return None

        if inp.menu_down() or inp.menu_right():
            self.selected = (self.selected + 1) % len(DIFFICULTY_ORDER)
            self.sound.play("menu_nav")
        if inp.menu_up() or inp.menu_left():
            self.selected = (self.selected - 1) % len(DIFFICULTY_ORDER)
            self.sound.play("menu_nav")

        if inp.confirm_pressed():
            self.chosen_difficulty = DIFFICULTY_ORDER[self.selected]
            self.sound.play("menu_select")
            return "menu"

        if inp.back_pressed():
            return "menu"

        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()
        _draw_menu_bg(surface, self.particles, time)

        # Title
        title = self.title_font.render("DIFFICULTY", True, COL_TEXT)
        surface.blit(title, ((INTERNAL_WIDTH - title.get_width()) // 2, 30))

        # Difficulty options
        start_y = 65
        for i, diff_key in enumerate(DIFFICULTY_ORDER):
            cfg = DIFFICULTY_PRESETS[diff_key]
            is_selected = (i == self.selected)

            if is_selected:
                pulse = 0.8 + 0.2 * math.sin(time * 5.0)
                color = (
                    int(cfg["color"][0] * pulse),
                    int(cfg["color"][1] * pulse),
                    int(cfg["color"][2] * pulse),
                )
                prefix = "► "
            else:
                color = COL_MENU_UNSELECTED
                prefix = "  "

            label = self.menu_font.render(f"{prefix}{cfg['label']}", True, color)
            iy = start_y + i * 40

            # Selection highlight
            if is_selected:
                bar_surf = pygame.Surface((INTERNAL_WIDTH - 40, 34), pygame.SRCALPHA)
                bar_surf.fill((*cfg["color"], 15))
                surface.blit(bar_surf, (20, iy - 3))

            surface.blit(label, ((INTERNAL_WIDTH - label.get_width()) // 2, iy))

            # Description under each option
            desc = self.desc_font.render(cfg["description"], True, COL_TEXT_DIM if not is_selected else color)
            surface.blit(desc, ((INTERNAL_WIDTH - desc.get_width()) // 2, iy + 14))

            # Stats line
            lives_text = f"Lives: {cfg['lives']}  Score: x{cfg['score_mult']}"
            stats = self.desc_font.render(lives_text, True, COL_TEXT_DIM)
            surface.blit(stats, ((INTERNAL_WIDTH - stats.get_width()) // 2, iy + 24))

        # Hint
        hint = self.hint_font.render("ENTER to select  ESC to go back", True, COL_TEXT_DIM)
        surface.blit(hint, ((INTERNAL_WIDTH - hint.get_width()) // 2, INTERNAL_HEIGHT - 15))


# ═══════════════════════════════════════════════════════════════════════
# HIGH SCORES STATE
# ═══════════════════════════════════════════════════════════════════════

class HighScoreState(GameState):
    """Display top 10 high scores."""

    def __init__(self, particles: ParticleSystem, sound: SoundManager) -> None:
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.title_font: pygame.font.Font | None = None
        self.score_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.scores: list[dict] = []
        self.timer: float = 0.0

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 22)
            self.score_font = pygame.font.Font(None, 12)
            self.hint_font = pygame.font.Font(None, 11)

    def enter(self) -> None:
        self.scores = load_scores()
        self.timer = 0.0

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        if random.random() < 0.1:
            self.particles.emit_menu_particle(INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.particles.update(dt)

        if self.timer > 0.3 and (inp.back_pressed() or inp.confirm_pressed()):
            return "menu"

        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()
        _draw_menu_bg(surface, self.particles, time)

        # Title with trophy icon
        title = self.title_font.render("HIGH SCORES", True, (255, 220, 60))
        surface.blit(title, ((INTERNAL_WIDTH - title.get_width()) // 2, 20))

        if not self.scores:
            empty_text = self.score_font.render("No scores yet! Go play!", True, COL_TEXT_DIM)
            surface.blit(empty_text, ((INTERNAL_WIDTH - empty_text.get_width()) // 2, INTERNAL_HEIGHT // 2))
        else:
            # Header
            header = self.score_font.render(
                f"{'#':>2}  {'SCORE':>7}  {'DIST':>5}  {'DIFF':>6}  {'KILLS':>5}  {'DATE':>10}",
                True, COL_TEXT_ACCENT,
            )
            surface.blit(header, (20, 42))

            # Horizontal line
            pygame.draw.line(surface, COL_TEXT_DIM, (20, 54), (INTERNAL_WIDTH - 20, 54), 1)

            # Score entries
            for i, entry in enumerate(self.scores[:10]):
                y = 58 + i * 18

                # Highlight top 3
                if i == 0:
                    rank_color = (255, 215, 0)  # Gold
                elif i == 1:
                    rank_color = (192, 192, 192)  # Silver
                elif i == 2:
                    rank_color = (205, 127, 50)  # Bronze
                else:
                    rank_color = COL_TEXT_DIM

                # Alternating row background
                if i % 2 == 0:
                    row_bg = pygame.Surface((INTERNAL_WIDTH - 40, 16), pygame.SRCALPHA)
                    row_bg.fill((255, 255, 255, 8))
                    surface.blit(row_bg, (20, y - 1))

                diff_name = entry.get("difficulty", "?")[:4].upper()
                date_str = entry.get("date", "???")
                kills = entry.get("enemies_killed", 0)

                line = f"{i+1:>2}  {entry.get('score', 0):>7}  {entry.get('distance', 0):>4}m  {diff_name:>6}  {kills:>5}  {date_str:>10}"
                text = self.score_font.render(line, True, rank_color if i < 3 else COL_TEXT)
                surface.blit(text, (20, y))

        # Hint
        hint = self.hint_font.render("Press ESC or ENTER to go back", True, COL_TEXT_DIM)
        surface.blit(hint, ((INTERNAL_WIDTH - hint.get_width()) // 2, INTERNAL_HEIGHT - 15))


# ═══════════════════════════════════════════════════════════════════════
# CONTROLS STATE
# ═══════════════════════════════════════════════════════════════════════

class ControlsState(GameState):
    """Display controls overlay."""

    def __init__(self, particles: ParticleSystem, sound: SoundManager) -> None:
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.title_font: pygame.font.Font | None = None
        self.control_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.timer: float = 0.0

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 22)
            self.control_font = pygame.font.Font(None, 13)
            self.hint_font = pygame.font.Font(None, 11)

    def enter(self) -> None:
        self.timer = 0.0

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        if random.random() < 0.1:
            self.particles.emit_menu_particle(INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.particles.update(dt)

        if self.timer > 0.3 and (inp.back_pressed() or inp.confirm_pressed()):
            return "menu"

        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()
        _draw_menu_bg(surface, self.particles, time)

        # Title
        title = self.title_font.render("CONTROLS", True, COL_TEXT)
        surface.blit(title, ((INTERNAL_WIDTH - title.get_width()) // 2, 20))

        # Controls list
        controls = [
            ("MOVEMENT", "←→ / A D", COL_TEXT_ACCENT),
            ("JUMP", "SPACE / W / ↑ (hold for higher)", COL_TEXT_ACCENT),
            ("DASH", "SHIFT / X (preserves momentum!)", COL_TEXT_ACCENT),
            ("SHOOT", "F / Z", COL_TEXT_ACCENT),
            ("SWITCH WEAPON", "Q", COL_TEXT_ACCENT),
            ("PAUSE", "ESC / P", COL_TEXT_ACCENT),
            ("", "", COL_TEXT_DIM),
            ("TIPS", "", (255, 200, 60)),
            ("", "• Dash mid-air for maximum distance", COL_TEXT_DIM),
            ("", "• Hold jump to go higher", COL_TEXT_DIM),
            ("", "• Chain kills for combo bonuses", COL_TEXT_DIM),
            ("", "• Shield kills enemies on contact", COL_TEXT_DIM),
            ("", "• Void reflects enemy bullets!", COL_TEXT_DIM),
        ]

        y = 48
        for label, value, color in controls:
            if label:
                label_surf = self.control_font.render(label, True, color)
                surface.blit(label_surf, (40, y))
            if value:
                val_surf = self.control_font.render(value, True, COL_TEXT if label else COL_TEXT_DIM)
                surface.blit(val_surf, (160 if label else 50, y))
            y += 16

        # Hint
        hint = self.hint_font.render("Press ESC or ENTER to go back", True, COL_TEXT_DIM)
        surface.blit(hint, ((INTERNAL_WIDTH - hint.get_width()) // 2, INTERNAL_HEIGHT - 15))


# ═══════════════════════════════════════════════════════════════════════
# PLAYING STATE
# ═══════════════════════════════════════════════════════════════════════

class PlayingState(GameState):
    """Main gameplay state — orchestrates all systems."""

    def __init__(
        self,
        physics: PhysicsEngine,
        camera: Camera,
        particles: ParticleSystem,
        sound: SoundManager,
    ) -> None:
        self.physics: PhysicsEngine = physics
        self.camera: Camera = camera
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.player: Player = Player(physics, particles)
        self.level: LevelGenerator = LevelGenerator()
        self.hud: HUD = HUD()

        self.score: int = 0
        self.coins_collected: int = 0
        self.death_timer: float = 0.0
        self.max_distance: float = 0.0     # tracks furthest X for distance score
        self.enemies_killed: int = 0
        self.time_survived: float = 0.0
        self.difficulty_name: str = DEFAULT_DIFFICULTY

        # Combo system
        self.combo: int = 0
        self.combo_timer: float = 0.0
        self.best_combo: int = 0

        # Milestone tracking
        self.milestones_hit: set[int] = set()

        # Ambient particles
        self._ambient_timer: float = 0.0

        # Projectile groups
        self.enemy_projectiles: list[Projectile] = []
        self.player_bullets: list[PlayerBullet | FriendlyBullet] = []
        self.laser_beam: LaserBeam | None = None

    def enter(self) -> None:
        self.score = 0
        self.coins_collected = 0
        self.max_distance = 0.0
        self.enemies_killed = 0
        self.time_survived = 0.0
        self.combo = 0
        self.combo_timer = 0.0
        self.best_combo = 0
        self.milestones_hit.clear()
        self._ambient_timer = 0.0
        self._load_level()
        self.sound.start_music()

    def exit(self) -> None:
        self.sound.stop_music()

    def _load_level(self) -> None:
        """Generate and start a new level."""
        # Apply difficulty
        self.level.set_difficulty(self.difficulty_name)
        diff_cfg = DIFFICULTY_PRESETS.get(self.difficulty_name, DIFFICULTY_PRESETS[DEFAULT_DIFFICULTY])
        self.player.max_lives = diff_cfg["lives"]

        self.level.generate(1)
        self.player.reset(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.particles.clear()
        self.camera.reset(self.player.center_x, self.player.center_y)
        self.death_timer = 0.0
        self.enemy_projectiles.clear()
        self.player_bullets.clear()
        self.laser_beam = None

    def _register_kill(self, x: float, y: float, enemy_type: str = "dasher") -> None:
        """Track a kill, update combo, emit effects."""
        self.enemies_killed += 1
        base_score = 200

        # Combo logic
        self.combo += 1
        self.combo_timer = COMBO_WINDOW
        if self.combo > self.best_combo:
            self.best_combo = self.combo

        # Bonus for combo
        combo_bonus = max(0, (self.combo - 1)) * COMBO_BONUS_PER_LEVEL
        diff_cfg = DIFFICULTY_PRESETS.get(self.difficulty_name, DIFFICULTY_PRESETS[DEFAULT_DIFFICULTY])
        total = int((base_score + combo_bonus) * diff_cfg.get("score_mult", 1.0))
        self.score += total

        # Effects
        self.particles.emit_enemy_death(x, y, enemy_type)
        if self.combo >= 2:
            self.particles.emit_combo_sparkle(x, y, self.combo)
            self.particles.add_floating_text(x, y - 10, f"x{self.combo}!", (255, 200, 60))
            self.sound.play("combo")

    def update(self, inp: InputHandler, dt: float) -> str | None:
        # ── Pause ────────────────────────────────────────────────
        if inp.pause_pressed() and self.player.alive:
            self.sound.play("pause")
            return "pause"

        # ── Death state ──────────────────────────────────────────
        if not self.player.alive:
            self.death_timer += dt
            self.particles.update(dt)
            self.camera.update(dt)
            if self.death_timer > 1.5:
                return "gameover"
            return None

        self.time_survived += dt

        # ── Update combo timer ───────────────────────────────────
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0
                self.combo_timer = 0.0

        # ── Update level (crumbling platforms) ───────────────────
        self.level.update(dt)

        # ── Update player ────────────────────────────────────
        active_platforms = self.level.get_active_platforms()
        events = self.player.update(inp, active_platforms, dt, obstacles=self.level.obstacles)

        # ── Handle player events ────────────────────────────
        if events["jumped"]:
            self.sound.play("jump")
        if events["landed"]:
            self.sound.play("land")
        if events["dashed"]:
            self.sound.play("dash")
        if events["died"]:
            self.sound.play("death")
            self.camera.add_trauma(0.8)
        if events["wall_hit"] and events["wall_speed"] > 120:
            self.camera.add_trauma(events["wall_speed"] / 500.0)
        if events["weapon_switched"]:
            self.sound.play("weapon_switch")

        # ── Player shooting → spawn bullets ─────────────────────
        self.laser_beam = None  # clear previous frame's laser
        if events["shot"]:
            if events["is_laser"]:
                start = pygame.Vector2(
                    self.player.center_x + self.player.facing * 6,
                    self.player.center_y,
                )
                beam = LaserBeam(start, self.player.facing)
                beam.clip_to_platforms(active_platforms, self.level.obstacles)
                self.laser_beam = beam

                # Check laser ↔ enemies
                for enemy in self.level.enemies:
                    if not enemy.alive:
                        continue
                    if beam.rect.colliderect(enemy.rect):
                        enemy.alive = False
                        etype = getattr(enemy, "ENEMY_TYPE", "dasher")
                        self._register_kill(
                            enemy.position.x + enemy.rect.width / 2,
                            enemy.position.y + enemy.rect.height / 2,
                            etype,
                        )
            else:
                for b_data in events["shot_bullets"]:
                    bullet = PlayerBullet(
                        b_data["x"], b_data["y"],
                        b_data["facing"], b_data["angle"],
                    )
                    self.player_bullets.append(bullet)

        # ── Update enemies ───────────────────────────────────
        player_pos = pygame.Vector2(self.player.center_x, self.player.center_y)
        player_vel = pygame.Vector2(self.player.velocity.x, self.player.velocity.y)
        for enemy in self.level.enemies:
            if not enemy.alive:
                continue
            enemy.update(
                player_pos, player_vel,
                active_platforms, self.level.obstacles, dt,
            )
            # Check if enemy wants to fire a projectile
            fire = enemy.get_fire_request()
            if fire is not None:
                proj = Projectile(
                    fire["x"], fire["y"],
                    fire["dx"], fire["dy"],
                    fire["speed"],
                    ptype=fire.get("type", "ground_flame")
                )
                self.enemy_projectiles.append(proj)

        # ── Update projectiles ───────────────────────────────
        for proj in self.enemy_projectiles:
            proj.update(active_platforms, self.level.obstacles, dt)
        self.enemy_projectiles = [p for p in self.enemy_projectiles if p.alive]

        for bullet in self.player_bullets:
            bullet.update(active_platforms, self.level.obstacles, dt)
        self.player_bullets = [b for b in self.player_bullets if b.alive]

        # ── Collision: player bullets ↔ enemies ───────────────
        for bullet in self.player_bullets[:]:
            if not bullet.alive:
                continue
            for enemy in self.level.enemies:
                if not enemy.alive:
                    continue
                if bullet.rect.colliderect(enemy.rect):
                    bullet.alive = False
                    enemy.alive = False
                    etype = getattr(enemy, "ENEMY_TYPE", "dasher")
                    self._register_kill(
                        enemy.position.x + enemy.rect.width / 2,
                        enemy.position.y + enemy.rect.height / 2,
                        etype,
                    )
                    break

        # ── Collision: enemy projectiles ↔ player ─────────────
        if self.player.alive:
            player_rect = self.player.rect
            shield_rect = self.player.shield_rect
            has_blackhole = self.player.has_powerup("blackhole")
            has_void = self.player.has_powerup("void")
            has_shield = self.player.shield_active

            for proj in self.enemy_projectiles[:]:
                if not proj.alive:
                    continue

                # ── Shield / Blackhole / Void interception ────
                if (has_shield or has_blackhole or has_void) and shield_rect.colliderect(proj.rect):
                    if has_void:
                        reflected = FriendlyBullet(proj.position, proj.velocity)
                        self.player_bullets.append(reflected)
                        proj.alive = False
                        self.sound.play("shield_hit")
                    elif has_blackhole:
                        proj.alive = False
                        self.sound.play("shield_hit")
                    elif has_shield:
                        proj.alive = False
                        self.sound.play("shield_hit")
                    continue

                # Normal hit check
                if player_rect.colliderect(proj.rect):
                    died = self.player.take_damage()
                    if died:
                        events["died"] = True
                        self.sound.play("death")
                        self.camera.add_trauma(0.8)
                        self.particles.emit_death_burst(
                            self.player.center_x, self.player.center_y,
                        )
                    else:
                        self.sound.play("damage")
                        self.camera.add_trauma(0.4)
                        self.particles.emit_screen_flash((255, 60, 60), 0.08)
                        # Reset combo on damage
                        self.combo = 0
                        self.combo_timer = 0.0
                    proj.alive = False
                    break

        # ── Collision: player body ↔ enemies ─────────────────
        if self.player.alive:
            player_rect = self.player.rect
            for enemy in self.level.enemies:
                if not enemy.alive:
                    continue
                if player_rect.colliderect(enemy.rect):
                    if self.player.shield_active:
                        enemy.alive = False
                        etype = getattr(enemy, "ENEMY_TYPE", "dasher")
                        self._register_kill(
                            enemy.position.x + enemy.rect.width / 2,
                            enemy.position.y + enemy.rect.height / 2,
                            etype,
                        )
                        self.sound.play("shield_hit")
                    else:
                        died = self.player.take_damage()
                        if died:
                            events["died"] = True
                            self.sound.play("death")
                            self.camera.add_trauma(0.8)
                            self.particles.emit_death_burst(
                                self.player.center_x, self.player.center_y,
                            )
                        else:
                            self.sound.play("damage")
                            self.camera.add_trauma(0.4)
                            self.particles.emit_screen_flash((255, 60, 60), 0.08)
                            self.combo = 0
                            self.combo_timer = 0.0
                    break

        # ── Magnet powerup — attract coins & uncollected pickups ─
        if self.player.alive and self.player.has_powerup("magnet"):
            magnet_pos = pygame.Vector2(self.player.center_x, self.player.center_y)

            for coin in self.level.coins:
                if coin.collected:
                    continue
                coin_pos = pygame.Vector2(coin.x, coin.y)
                dist = magnet_pos.distance_to(coin_pos)
                if dist < MAGNET_RANGE and dist > 1:
                    direction = (magnet_pos - coin_pos).normalize() * MAGNET_FORCE
                    coin.x += direction.x
                    coin.y += direction.y

            for pu in self.level.powerups:
                if pu.collected:
                    continue
                pu_pos = pygame.Vector2(pu.x, pu.y)
                dist = magnet_pos.distance_to(pu_pos)
                if dist < MAGNET_RANGE and dist > 1:
                    direction = (magnet_pos - pu_pos).normalize() * MAGNET_FORCE
                    pu.x += direction.x
                    pu.y += direction.y

        # ── Power-up collection ───────────────────────────────
        if self.player.alive:
            player_rect = self.player.rect
            for pu in self.level.powerups:
                if pu.collected:
                    continue
                if not player_rect.colliderect(pu.rect):
                    continue

                pu.collected = True
                ptype = pu.powerup_type

                if ptype == "heart":
                    if self.player.lives < self.player.max_lives:
                        self.player.lives += 1
                    self.sound.play("powerup")

                elif ptype == "wormhole":
                    new_x = self.player.position.x + (self.player.facing * WORMHOLE_TILES * TILE_SIZE)
                    test_rect = pygame.Rect(
                        int(new_x), int(self.player.position.y),
                        self.player.width, self.player.height,
                    )
                    step = -1 if self.player.facing > 0 else 1
                    for _ in range(WORMHOLE_TILES * TILE_SIZE):
                        collides = False
                        for plat in active_platforms:
                            if test_rect.colliderect(plat.rect):
                                collides = True
                                break
                        if not collides:
                            for obs in self.level.obstacles:
                                if test_rect.colliderect(obs.rect):
                                    collides = True
                                    break
                        if not collides:
                            break
                        new_x += step
                        test_rect.x = int(new_x)
                    self.player.position.x = new_x
                    self.sound.play("wormhole")
                    self.particles.emit_coin_sparkle(
                        int(self.player.center_x), int(self.player.center_y),
                    )

                elif ptype == "weapon":
                    weapon_name = self.player.unlock_next_weapon()
                    self.sound.play("powerup")

                elif ptype in ("dash", "magnet", "shield", "blackhole", "void"):
                    self.player.activate_powerup(ptype)
                    self.sound.play("powerup")

                self.particles.emit_coin_sparkle(int(pu.x), int(pu.y))
                self.particles.emit_screen_flash((255, 255, 200), 0.06)

        # ── Coin collection ──────────────────────────────────
        if self.player.alive:
            player_rect = self.player.rect
            for coin in self.level.coins:
                if not coin.collected and player_rect.colliderect(coin.rect):
                    coin.collected = True
                    diff_cfg = DIFFICULTY_PRESETS.get(self.difficulty_name, DIFFICULTY_PRESETS[DEFAULT_DIFFICULTY])
                    self.score += int(COIN_SCORE * diff_cfg.get("score_mult", 1.0))
                    self.coins_collected += 1
                    self.particles.emit_coin_sparkle(int(coin.x), int(coin.y))
                    self.sound.play("coin")

        # ── Endless streaming — generate ahead, cleanup behind ──
        self.level.stream_update(self.player.position.x)

        # ── Distance score & milestones ───────────────────────
        current_dist = max(0, self.player.position.x - PLAYER_SPAWN_X)
        if current_dist > self.max_distance:
            dist_delta = current_dist - self.max_distance
            self.score += int(dist_delta * 0.5)
            self.max_distance = current_dist

        # Check milestones
        current_dist_m = int(self.max_distance / 10)
        for milestone in MILESTONE_DISTANCES:
            if milestone not in self.milestones_hit and current_dist_m >= milestone:
                self.milestones_hit.add(milestone)
                self.score += MILESTONE_BONUS
                self.sound.play("milestone")
                self.particles.add_floating_text(
                    self.player.center_x, self.player.center_y - 20,
                    f"{milestone}m!", (255, 200, 60), 2.0,
                )
                self.particles.emit_screen_flash((255, 255, 200), 0.12)

        # ── Ambient particles ────────────────────────────────
        self._ambient_timer += dt
        if self._ambient_timer > 0.5:
            self._ambient_timer = 0.0
            if random.random() < 0.6:
                self.particles.emit_ambient_leaf(self.camera.x, self.camera.y)

        # ── Update systems ───────────────────────────────────
        self.particles.update(dt)
        self.camera.set_target(self.player.center_x, self.player.center_y)
        self.camera.update(dt)

        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        cam_x = self.camera.x
        cam_y = self.camera.y

        # Draw level (platforms, coins, obstacles, powerups)
        self.level.draw(surface, cam_x, cam_y)

        # Draw enemies
        for enemy in self.level.enemies:
            enemy.draw(surface, cam_x, cam_y)

        # Draw projectiles
        for proj in self.enemy_projectiles:
            proj.draw(surface, cam_x, cam_y)
        for bullet in self.player_bullets:
            bullet.draw(surface, cam_x, cam_y)

        # Draw laser beam (single frame)
        if self.laser_beam is not None:
            self.laser_beam.draw(surface, cam_x, cam_y)

        # Draw particles (behind and in front of player)
        self.particles.draw(surface, cam_x, cam_y)

        # Draw player
        self.player.draw(surface, cam_x, cam_y)

        # Draw screen effects (flashes)
        self.particles.draw_screen_effects(surface)

        # Draw HUD
        distance_m = int(self.max_distance / 10)
        self.hud.draw(
            surface, self.score, distance_m,
            self.player.dash_cooldown_timer, self.coins_collected,
            player=self.player,
            combo=self.combo,
            enemies_killed=self.enemies_killed,
            difficulty_name=self.difficulty_name,
            time_survived=self.time_survived,
        )


# ═══════════════════════════════════════════════════════════════════════
# PAUSE STATE
# ═══════════════════════════════════════════════════════════════════════

class PauseState(GameState):
    """In-game pause menu."""

    MENU_ITEMS = ["RESUME", "RESTART", "QUIT TO MENU"]

    def __init__(self, particles: ParticleSystem, sound: SoundManager) -> None:
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.title_font: pygame.font.Font | None = None
        self.menu_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.selected: int = 0
        self.timer: float = 0.0

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 22)
            self.menu_font = pygame.font.Font(None, 16)
            self.hint_font = pygame.font.Font(None, 11)

    def enter(self) -> None:
        self.selected = 0
        self.timer = 0.0

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        if self.timer < 0.2:
            return None

        if inp.menu_down():
            self.selected = (self.selected + 1) % len(self.MENU_ITEMS)
            self.sound.play("menu_nav")
        if inp.menu_up():
            self.selected = (self.selected - 1) % len(self.MENU_ITEMS)
            self.sound.play("menu_nav")

        if inp.pause_pressed():
            self.sound.play("pause")
            return "resume"

        if inp.confirm_pressed():
            self.sound.play("menu_select")
            item = self.MENU_ITEMS[self.selected]
            if item == "RESUME":
                return "resume"
            elif item == "RESTART":
                return "restart"
            elif item == "QUIT TO MENU":
                return "menu"

        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()

        # Dim overlay
        dim = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 140))
        surface.blit(dim, (0, 0))

        # Title
        title = self.title_font.render("PAUSED", True, COL_TEXT)
        surface.blit(title, ((INTERNAL_WIDTH - title.get_width()) // 2, INTERNAL_HEIGHT // 3 - 15))

        # Menu items
        start_y = INTERNAL_HEIGHT // 3 + 15
        for i, item in enumerate(self.MENU_ITEMS):
            is_selected = (i == self.selected)
            if is_selected:
                pulse = 0.8 + 0.2 * math.sin(time * 5.0)
                color = (
                    int(COL_MENU_SELECTED[0] * pulse),
                    int(COL_MENU_SELECTED[1] * pulse),
                    int(COL_MENU_SELECTED[2] * pulse),
                )
                prefix = "► "
            else:
                color = COL_MENU_UNSELECTED
                prefix = "  "

            text = self.menu_font.render(f"{prefix}{item}", True, color)
            iy = start_y + i * 22
            surface.blit(text, ((INTERNAL_WIDTH - text.get_width()) // 2, iy))

        # Hint
        hint = self.hint_font.render("ESC to resume", True, COL_TEXT_DIM)
        surface.blit(hint, ((INTERNAL_WIDTH - hint.get_width()) // 2, INTERNAL_HEIGHT * 3 // 4))


# ═══════════════════════════════════════════════════════════════════════
# GAME OVER STATE
# ═══════════════════════════════════════════════════════════════════════

class GameOverState(GameState):
    """Game over screen with stats breakdown and high score check."""

    def __init__(self, particles: ParticleSystem, sound: SoundManager) -> None:
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.title_font: pygame.font.Font | None = None
        self.score_font: pygame.font.Font | None = None
        self.stat_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.menu_font: pygame.font.Font | None = None
        self.timer: float = 0.0
        self.final_score: int = 0
        self.final_distance: int = 0
        self.final_enemies: int = 0
        self.final_coins: int = 0
        self.final_time: float = 0.0
        self.final_combo: int = 0
        self.difficulty_name: str = DEFAULT_DIFFICULTY
        self.is_new_high: bool = False
        self.rank: int = 0
        self.selected: int = 0
        self._highscore_saved: bool = False

    MENU_ITEMS = ["PLAY AGAIN", "MENU"]

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 24)
            self.score_font = pygame.font.Font(None, 20)
            self.stat_font = pygame.font.Font(None, 12)
            self.hint_font = pygame.font.Font(None, 11)
            self.menu_font = pygame.font.Font(None, 14)

    def enter(self) -> None:
        self.timer = 0.0
        self.selected = 0
        self._highscore_saved = False

    def set_results(
        self, score: int, distance: int,
        enemies: int = 0, coins: int = 0,
        time_survived: float = 0.0,
        best_combo: int = 0,
        difficulty: str = "normal",
    ) -> None:
        """Set the results to display."""
        self.final_score = score
        self.final_distance = distance
        self.final_enemies = enemies
        self.final_coins = coins
        self.final_time = time_survived
        self.final_combo = best_combo
        self.difficulty_name = difficulty

        # Save high score
        if not self._highscore_saved:
            self.rank, self.is_new_high = add_score(
                score, distance, difficulty,
                enemies_killed=enemies,
                coins=coins,
                time_survived=time_survived,
            )
            self._highscore_saved = True
            if self.is_new_high:
                self.sound.play("highscore")

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        if random.random() < 0.1:
            self.particles.emit_menu_particle(INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.particles.update(dt)

        if self.timer < 0.5:
            return None

        if inp.menu_down():
            self.selected = (self.selected + 1) % len(self.MENU_ITEMS)
            self.sound.play("menu_nav")
        if inp.menu_up():
            self.selected = (self.selected - 1) % len(self.MENU_ITEMS)
            self.sound.play("menu_nav")

        if inp.confirm_pressed() or inp.restart_pressed():
            self.sound.play("menu_select")
            if inp.restart_pressed() or self.selected == 0:
                return "playing"
            elif self.selected == 1:
                return "menu"

        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()

        self.particles.draw(surface, 0, 0)

        # "GAME OVER" title
        if self.is_new_high:
            # Rainbow pulsing for new high score
            hue = (time * 100) % 360
            r = int(128 + 127 * math.sin(math.radians(hue)))
            g = int(128 + 127 * math.sin(math.radians(hue + 120)))
            b = int(128 + 127 * math.sin(math.radians(hue + 240)))
            title_color = (r, g, b)
            title = self.title_font.render("NEW HIGH SCORE!", True, title_color)
        else:
            title = self.title_font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(title, ((INTERNAL_WIDTH - title.get_width()) // 2, 20))

        # Score
        score_text = self.score_font.render(
            f"SCORE: {self.final_score}", True, COL_TEXT,
        )
        surface.blit(
            score_text,
            ((INTERNAL_WIDTH - score_text.get_width()) // 2, 46),
        )

        # Rank
        if self.rank > 0:
            rank_text = self.stat_font.render(
                f"Rank #{self.rank} on leaderboard", True, (255, 200, 60),
            )
            surface.blit(rank_text, ((INTERNAL_WIDTH - rank_text.get_width()) // 2, 64))

        # Stats breakdown
        stats = [
            ("Distance", f"{self.final_distance}m"),
            ("Enemies", f"{self.final_enemies}"),
            ("Coins", f"{self.final_coins}"),
            ("Best Combo", f"x{self.final_combo}"),
            ("Time", f"{int(self.final_time) // 60}:{int(self.final_time) % 60:02d}"),
            ("Difficulty", DIFFICULTY_PRESETS.get(self.difficulty_name, {}).get("label", "?")),
        ]

        stat_y = 80
        # Panel background
        panel_h = len(stats) * 14 + 6
        panel_surf = pygame.Surface((160, panel_h), pygame.SRCALPHA)
        panel_surf.fill((0, 0, 0, 60))
        panel_x = (INTERNAL_WIDTH - 160) // 2
        surface.blit(panel_surf, (panel_x, stat_y - 3))

        for label, value in stats:
            label_surf = self.stat_font.render(f"{label}:", True, COL_TEXT_DIM)
            value_surf = self.stat_font.render(value, True, COL_TEXT)
            surface.blit(label_surf, (panel_x + 8, stat_y))
            surface.blit(value_surf, (panel_x + 152 - value_surf.get_width(), stat_y))
            stat_y += 14

        # Menu options
        menu_y = stat_y + 15
        for i, item in enumerate(self.MENU_ITEMS):
            is_selected = (i == self.selected)
            if is_selected:
                pulse = 0.8 + 0.2 * math.sin(time * 5.0)
                color = (
                    int(COL_MENU_SELECTED[0] * pulse),
                    int(COL_MENU_SELECTED[1] * pulse),
                    int(COL_MENU_SELECTED[2] * pulse),
                )
                prefix = "► "
            else:
                color = COL_MENU_UNSELECTED
                prefix = "  "

            text = self.menu_font.render(f"{prefix}{item}", True, color)
            surface.blit(text, ((INTERNAL_WIDTH - text.get_width()) // 2, menu_y + i * 18))

        # Hint
        hint = self.hint_font.render("R to retry  ↑↓ to select", True, COL_TEXT_DIM)
        surface.blit(hint, ((INTERNAL_WIDTH - hint.get_width()) // 2, INTERNAL_HEIGHT - 12))

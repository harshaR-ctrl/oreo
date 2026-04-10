"""
states.py — Game state machine: Menu, Playing, GameOver.

Each state implements enter(), exit(), update(dt), and render(surface).
The PlayingState orchestrates all game systems.
"""

from __future__ import annotations
import math
import random
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TEXT, COL_TEXT_DIM, COL_TEXT_ACCENT, COL_PLAYER_BODY,
    COL_BG, COIN_SCORE, LEVEL_COMPLETE_BONUS,
    PLAYER_SPAWN_X, PLAYER_SPAWN_Y,
)
from input_handler import InputHandler
from physics import PhysicsEngine
from camera import Camera
from particles import ParticleSystem
from player import Player
from level import LevelGenerator
from hud import HUD
from sounds import SoundManager
from projectiles import Projectile, PlayerBullet
from enemies import Dasher, Marksman, Hybrid


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


class MenuState(GameState):
    """Title screen with floating particles and pulsing text."""

    def __init__(self, particles: ParticleSystem) -> None:
        self.particles: ParticleSystem = particles
        self.title_font: pygame.font.Font | None = None
        self.sub_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.timer: float = 0.0

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 28)
            self.sub_font = pygame.font.Font(None, 14)
            self.hint_font = pygame.font.Font(None, 11)

    def enter(self) -> None:
        self.particles.clear()
        self.timer = 0.0

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        # Spawn ambient particles
        if random.random() < 0.15:
            self.particles.emit_menu_particle(INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.particles.update(dt)

        if inp.confirm_pressed() and self.timer > 0.3:
            return "playing"
        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()

        # Draw particles behind text
        self.particles.draw(surface, 0, 0)

        # Title with glow effect
        title_text = "MICRO"
        title_surf = self.title_font.render(title_text, True, COL_PLAYER_BODY)
        tx = (INTERNAL_WIDTH - title_surf.get_width()) // 2
        ty = INTERNAL_HEIGHT // 3 - 10

        # Glow (draw offset copies)
        glow_color = (40, 100, 140)
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            glow = self.title_font.render(title_text, True, glow_color)
            surface.blit(glow, (tx + ox, ty + oy))
        surface.blit(title_surf, (tx, ty))

        # Subtitle
        sub = self.title_font.render("PLATFORMER", True, COL_TEXT)
        surface.blit(sub, ((INTERNAL_WIDTH - sub.get_width()) // 2, ty + 22))

        # Pulsing "Press SPACE" text
        alpha = int(128 + 127 * math.sin(time * 3.0))
        prompt_color = (alpha, alpha, min(255, alpha + 20))
        prompt = self.sub_font.render("PRESS  SPACE  TO  START", True, prompt_color)
        surface.blit(
            prompt,
            ((INTERNAL_WIDTH - prompt.get_width()) // 2, INTERNAL_HEIGHT * 2 // 3),
        )

        # Controls hint
        controls = self.hint_font.render(
            "←→ / AD Move  SPACE Jump  SHIFT Dash  F Shoot", True, COL_TEXT_DIM
        )
        surface.blit(
            controls,
            ((INTERNAL_WIDTH - controls.get_width()) // 2, INTERNAL_HEIGHT - 20),
        )

        # Dash hint
        dash_hint = self.hint_font.render(
            "Dash preserves momentum — slingshot around!", True, COL_TEXT_DIM
        )
        surface.blit(
            dash_hint,
            ((INTERNAL_WIDTH - dash_hint.get_width()) // 2, INTERNAL_HEIGHT - 10),
        )


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
        self.level_number: int = 1
        self.coins_collected: int = 0
        self.death_timer: float = 0.0

        # Projectile groups
        self.enemy_projectiles: list[Projectile] = []
        self.player_bullets: list[PlayerBullet] = []

    def enter(self) -> None:
        self.score = 0
        self.level_number = 1
        self.coins_collected = 0
        self._load_level()

    def _load_level(self) -> None:
        """Generate and start a new level."""
        self.level.generate(self.level_number)
        self.player.reset(PLAYER_SPAWN_X, PLAYER_SPAWN_Y)
        self.particles.clear()
        self.camera.reset(self.player.center_x, self.player.center_y)
        self.death_timer = 0.0
        self.enemy_projectiles.clear()
        self.player_bullets.clear()

    def update(self, inp: InputHandler, dt: float) -> str | None:
        # ── Death state ──────────────────────────────────────────
        if not self.player.alive:
            self.death_timer += dt
            self.particles.update(dt)
            self.camera.update(dt)
            if self.death_timer > 1.5:
                return "gameover"
            return None

        # ── Update level (crumbling platforms) ───────────────────
        self.level.update(dt)

        # ── Update player ────────────────────────────────────
        active_platforms = self.level.get_active_platforms()
        events = self.player.update(inp, active_platforms, dt)

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

        # ── Player shooting → spawn bullet ─────────────────────
        if events["shot"]:
            bullet = PlayerBullet(
                self.player.center_x + self.player.facing * 6,
                self.player.center_y,
                self.player.facing,
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
                    self.particles.emit_death_burst(
                        enemy.position.x + enemy.rect.width / 2,
                        enemy.position.y + enemy.rect.height / 2,
                    )
                    self.score += 200
                    break

        # ── Collision: enemy projectiles ↔ player ─────────────
        if self.player.alive:
            player_rect = self.player.rect
            for proj in self.enemy_projectiles:
                if not proj.alive:
                    continue
                if player_rect.colliderect(proj.rect):
                    self.player.alive = False
                    events["died"] = True
                    self.sound.play("death")
                    self.camera.add_trauma(0.8)
                    self.particles.emit_death_burst(
                        self.player.center_x, self.player.center_y,
                    )
                    break

        # ── Collision: player body ↔ enemies ─────────────────
        if self.player.alive:
            player_rect = self.player.rect
            for enemy in self.level.enemies:
                if not enemy.alive:
                    continue
                if player_rect.colliderect(enemy.rect):
                    self.player.alive = False
                    events["died"] = True
                    self.sound.play("death")
                    self.camera.add_trauma(0.8)
                    self.particles.emit_death_burst(
                        self.player.center_x, self.player.center_y,
                    )
                    break

        # ── Power-up collection ───────────────────────────────
        if self.player.alive:
            player_rect = self.player.rect
            for pu in self.level.powerups:
                if not pu.collected and player_rect.colliderect(pu.rect):
                    pu.collected = True
                    self.player.can_shoot = True
                    self.particles.emit_coin_sparkle(int(pu.x), int(pu.y))
                    self.sound.play("coin")  # reuse coin sound

        # ── Coin collection ──────────────────────────────────
        if self.player.alive:
            player_rect = self.player.rect
            for coin in self.level.coins:
                if not coin.collected and player_rect.colliderect(coin.rect):
                    coin.collected = True
                    self.score += COIN_SCORE
                    self.coins_collected += 1
                    self.particles.emit_coin_sparkle(coin.x, coin.y)
                    self.sound.play("coin")

        # ── Level completion ─────────────────────────────────
        if self.level.goal_platform and self.player.on_ground:
            if self.player.rect.colliderect(self.level.goal_platform.rect):
                self.score += LEVEL_COMPLETE_BONUS
                self.level_number += 1
                self.sound.play("level_complete")
                self._load_level()

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

        # Draw particles (behind and in front of player)
        self.particles.draw(surface, cam_x, cam_y)

        # Draw player
        self.player.draw(surface, cam_x, cam_y)

        # Draw HUD
        self.hud.draw(
            surface, self.score, self.level_number,
            self.player.dash_cooldown_timer, self.coins_collected,
        )


class GameOverState(GameState):
    """Game over screen showing final score."""

    def __init__(self, particles: ParticleSystem, sound: SoundManager) -> None:
        self.particles: ParticleSystem = particles
        self.sound: SoundManager = sound
        self.title_font: pygame.font.Font | None = None
        self.score_font: pygame.font.Font | None = None
        self.hint_font: pygame.font.Font | None = None
        self.timer: float = 0.0
        self.final_score: int = 0
        self.final_level: int = 1

    def _ensure_fonts(self) -> None:
        if self.title_font is None:
            self.title_font = pygame.font.Font(None, 22)
            self.score_font = pygame.font.Font(None, 18)
            self.hint_font = pygame.font.Font(None, 12)

    def enter(self) -> None:
        self.timer = 0.0

    def set_results(self, score: int, level: int) -> None:
        """Set the score and level to display."""
        self.final_score = score
        self.final_level = level

    def update(self, inp: InputHandler, dt: float) -> str | None:
        self.timer += dt

        if random.random() < 0.1:
            self.particles.emit_menu_particle(INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self.particles.update(dt)

        if (inp.restart_pressed() or inp.confirm_pressed()) and self.timer > 0.5:
            return "playing"
        return None

    def render(self, surface: pygame.Surface, time: float) -> None:
        self._ensure_fonts()

        self.particles.draw(surface, 0, 0)

        # "GAME OVER" title
        title = self.title_font.render("GAME OVER", True, (255, 80, 80))
        surface.blit(title, ((INTERNAL_WIDTH - title.get_width()) // 2, INTERNAL_HEIGHT // 3 - 5))

        # Score
        score_text = self.score_font.render(
            f"SCORE: {self.final_score}", True, COL_TEXT,
        )
        surface.blit(
            score_text,
            ((INTERNAL_WIDTH - score_text.get_width()) // 2, INTERNAL_HEIGHT // 2 - 5),
        )

        # Level
        level_text = self.hint_font.render(
            f"Reached Level {self.final_level}", True, COL_TEXT_DIM,
        )
        surface.blit(
            level_text,
            ((INTERNAL_WIDTH - level_text.get_width()) // 2, INTERNAL_HEIGHT // 2 + 15),
        )

        # Retry prompt
        alpha = int(128 + 127 * math.sin(time * 3.0))
        prompt = self.hint_font.render(
            "PRESS  R  OR  SPACE  TO  RETRY", True, (alpha, alpha, min(255, alpha + 20)),
        )
        surface.blit(
            prompt,
            ((INTERNAL_WIDTH - prompt.get_width()) // 2, INTERNAL_HEIGHT * 3 // 4),
        )

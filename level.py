"""
level.py — Endless procedural level generator (horizontal side-scroller).

Generates platform chunks as the player progresses rightward. Old chunks
behind the player are cleaned up to save memory. Difficulty gradually
increases with distance traveled. There is no end — the game runs until
the player dies.
"""

from __future__ import annotations
import random
import math
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, GROUND_Y,
    PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH, PLATFORM_HEIGHT,
    MIN_GAP_X, MAX_GAP_X, MIN_GAP_Y, MAX_GAP_Y,
    PLATFORMS_PER_LEVEL, COIN_SIZE,
    JUMP_IMPULSE, GRAVITY, MAX_RUN_SPEED,
    COL_PLATFORM, COL_PLATFORM_TOP, COL_PLATFORM_BOUNCE,
    COL_PLATFORM_CRUMBLE, COL_GOAL_PLATFORM, COL_COIN,
    ENEMY_WIDTH, ENEMY_HEIGHT, OBSTACLE_WIDTH, OBSTACLE_HEIGHT,
)
from enemies import Dasher, Marksman, Hybrid
from obstacles import Obstacle
from powerups import BasePowerUp, spawn_random_loot


# ── How far ahead / behind to generate / cull ─────────────────────────
CHUNK_WIDTH: int = INTERNAL_WIDTH       # generate one screen-width at a time
GENERATE_AHEAD: float = INTERNAL_WIDTH * 2.0   # pre-generate 2 screens ahead
CLEANUP_BEHIND: float = INTERNAL_WIDTH * 1.5   # remove stuff >1.5 screens behind


class Platform:
    """A single platform in the level."""

    def __init__(
        self,
        x: int, y: int, w: int, h: int,
        platform_type: str = "normal",
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, w, h)
        self.platform_type: str = platform_type
        self.active: bool = True

        # Crumble state
        self.crumble_timer: float = 0.0
        self.crumble_delay: float = 0.35
        self.crumbling: bool = False
        self.shake_offset: float = 0.0

    def start_crumble(self) -> None:
        if not self.crumbling:
            self.crumbling = True
            self.crumble_timer = self.crumble_delay

    def update(self, dt: float) -> None:
        if self.crumbling and self.active:
            self.crumble_timer -= dt
            self.shake_offset = random.uniform(-1.5, 1.5)
            if self.crumble_timer <= 0:
                self.active = False
                self.shake_offset = 0

    def get_color(self) -> tuple[int, int, int]:
        if self.platform_type == "bounce":
            return COL_PLATFORM_BOUNCE
        elif self.platform_type == "crumble":
            return COL_PLATFORM_CRUMBLE
        return COL_PLATFORM

    def get_top_color(self) -> tuple[int, int, int]:
        if self.platform_type == "bounce":
            return (120, 255, 210)
        elif self.platform_type == "crumble":
            return (180, 100, 80)
        return COL_PLATFORM_TOP

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if not self.active:
            return
        sx = int(self.rect.x - cam_x + self.shake_offset)
        sy = int(self.rect.y - cam_y)
        # Cull off-screen
        if sx > INTERNAL_WIDTH + 20 or sx + self.rect.width < -20:
            return
        pygame.draw.rect(surface, self.get_color(),
                         (sx, sy, self.rect.width, self.rect.height))
        pygame.draw.rect(surface, self.get_top_color(),
                         (sx, sy, self.rect.width, 1))


class Coin:
    """A collectible coin on a platform."""

    def __init__(self, x: int, y: int) -> None:
        self.x: float = float(x)
        self.y: float = float(y)
        self.size: int = COIN_SIZE
        self.collected: bool = False
        self.bob_timer: float = random.uniform(0, math.pi * 2)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x) - self.size // 2,
            int(self.y) - self.size // 2 + int(math.sin(self.bob_timer) * 2),
            self.size, self.size,
        )

    def update(self, dt: float) -> None:
        self.bob_timer += dt * 3.0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 2)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)
        if sx > INTERNAL_WIDTH + 20 or sx < -20:
            return
        pygame.draw.circle(surface, (255, 200, 40), (sx, sy), self.size // 2 + 1)
        pygame.draw.circle(surface, COL_COIN, (sx, sy), self.size // 2)
        pygame.draw.circle(surface, (255, 255, 200),
                           (sx - 1, sy - 1), max(1, self.size // 4))


class LevelGenerator:
    """Endless side-scrolling level: generates chunks as the player moves."""

    def __init__(self) -> None:
        self.platforms: list[Platform] = []
        self.coins: list[Coin] = []
        self.enemies: list = []
        self.obstacles: list[Obstacle] = []
        self.powerups: list[BasePowerUp] = []
        self.goal_platform = None           # Not used in endless mode

        self.level_number: int = 0
        self.seed: int = 0

        # Endless generation state
        self._frontier_x: float = 0.0      # rightmost edge of generated content
        self._frontier_y: float = GROUND_Y  # last platform Y for continuity
        self._distance: float = 0.0        # total distance generated (for difficulty)
        self._platforms_generated: int = 0  # counter for spawn spacing

    @property
    def difficulty(self) -> float:
        """0.0 → 1.0 ramp based on distance traveled."""
        return min(self._distance / 5000.0, 1.0)

    def generate(self, level_number: int, seed: int | None = None) -> None:
        """Reset and generate the starting area."""
        self.level_number = level_number
        self.seed = seed if seed is not None else random.randint(0, 999999)
        random.seed(self.seed)

        self.platforms.clear()
        self.coins.clear()
        self.enemies.clear()
        self.obstacles.clear()
        self.powerups.clear()
        self._platforms_generated = 0
        self._distance = 0.0

        # Wide starting ground
        ground = Platform(0, GROUND_Y, INTERNAL_WIDTH, PLATFORM_HEIGHT, "normal")
        self.platforms.append(ground)

        self._frontier_x = float(INTERNAL_WIDTH)
        self._frontier_y = float(GROUND_Y)

        # Pre-generate the first 2 screens
        self._generate_ahead(INTERNAL_WIDTH * 2.0)

    def _generate_ahead(self, up_to_x: float) -> None:
        """Generate platforms until _frontier_x >= up_to_x."""
        difficulty = self.difficulty
        bounce_chance = 0.1 + difficulty * 0.1
        crumble_chance = 0.03 + difficulty * 0.1
        enemy_classes = [Dasher, Marksman, Hybrid]

        y_min = GROUND_Y - 100
        y_max = GROUND_Y

        while self._frontier_x < up_to_x:
            # Horizontal gap — always progresses right
            gap_x = random.randint(
                int(MIN_GAP_X + difficulty * 3),
                int(MAX_GAP_X + difficulty * 5),
            )

            # Vertical variation
            y_shift = random.randint(-MAX_GAP_Y, MIN_GAP_Y)
            new_y = self._frontier_y + y_shift
            new_y = max(y_min, min(y_max, new_y))

            new_x = self._frontier_x + gap_x

            # Platform type
            roll = random.random()
            if roll < crumble_chance and self._platforms_generated > 5:
                ptype = "crumble"
            elif roll < crumble_chance + bounce_chance:
                ptype = "bounce"
            else:
                ptype = "normal"

            # Platform width
            if ptype == "crumble":
                width = random.randint(35, 80) # Short, snappy width for brown platforms
            else:
                width = random.randint(
                    max(35, int(PLATFORM_MIN_WIDTH - difficulty * 4)),
                    max(50, int(PLATFORM_MAX_WIDTH - difficulty * 6)),
                )

            plat = Platform(int(new_x), int(new_y), width, PLATFORM_HEIGHT, ptype)
            self.platforms.append(plat)
            self._platforms_generated += 1

            # Coin on ~40% of non-crumble platforms
            if random.random() < 0.4 and ptype != "crumble":
                self.coins.append(Coin(int(new_x + width // 2), int(new_y - 10)))

            # Enemy spawn logic (scales with difficulty)
            enemy_chance = 0.35 + difficulty * 0.30  # 35% to 65% chance
            if (ptype == "normal"
                    and self._platforms_generated > 3
                    and random.random() < enemy_chance):
                ex = int(new_x) + width // 2 - ENEMY_WIDTH // 2
                ey = int(new_y) - ENEMY_HEIGHT
                ecls = random.choice(enemy_classes)
                self.enemies.append(ecls(ex, ey))

            # Obstacle logic
            if ptype == "normal" and width > 120 and self._platforms_generated > 2:
                # Up to 2 obstacles on wide platforms
                if random.random() < 0.4 + difficulty * 0.2:
                    ox = int(new_x) + random.randint(15, 30)
                    oy = int(new_y) - OBSTACLE_HEIGHT
                    self.obstacles.append(Obstacle(ox, oy))
                
                if width > 200 and random.random() < 0.4 + difficulty * 0.2:
                    ox = int(new_x) + width - random.randint(15 + OBSTACLE_WIDTH, 30 + OBSTACLE_WIDTH)
                    oy = int(new_y) - OBSTACLE_HEIGHT
                    self.obstacles.append(Obstacle(ox, oy))

            # Loot every ~5th platform
            if self._platforms_generated % 5 == 0:
                px = int(new_x + width // 2)
                py = int(new_y - 12)
                self.powerups.append(spawn_random_loot(px, py))

            self._frontier_x = new_x + width
            self._frontier_y = new_y
            self._distance = self._frontier_x

    def _cleanup_behind(self, player_x: float) -> None:
        """Remove entities that are far behind the player."""
        cutoff = player_x - CLEANUP_BEHIND

        self.platforms = [p for p in self.platforms if p.rect.right > cutoff]
        self.coins = [c for c in self.coins if c.x > cutoff or c.collected]
        self.enemies = [e for e in self.enemies if e.position.x > cutoff - 50]
        self.obstacles = [o for o in self.obstacles if o.rect.right > cutoff]
        self.powerups = [p for p in self.powerups if p.x > cutoff or p.collected]

    def stream_update(self, player_x: float) -> None:
        """Called every frame: generate ahead and cleanup behind."""
        target_x = player_x + GENERATE_AHEAD
        if target_x > self._frontier_x:
            self._generate_ahead(target_x)
        self._cleanup_behind(player_x)

    def update(self, dt: float) -> None:
        """Update all platforms, coins, and powerups."""
        for plat in self.platforms:
            plat.update(dt)
        for coin in self.coins:
            coin.update(dt)
        for pu in self.powerups:
            pu.update(dt)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw all visible entities."""
        for plat in self.platforms:
            plat.draw(surface, cam_x, cam_y)
        for coin in self.coins:
            coin.draw(surface, cam_x, cam_y)
        for obs in self.obstacles:
            obs.draw(surface, cam_x, cam_y)
        for pu in self.powerups:
            pu.draw(surface, cam_x, cam_y)

    def get_active_platforms(self) -> list[Platform]:
        return [p for p in self.platforms if p.active]

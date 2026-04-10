"""
level.py — Procedural level generator (horizontal side-scroller).

Creates platforms progressing rightward. Each new platform is placed
within jump range to the right of the previous one. Difficulty scales
with level number. Includes coins, enemies, obstacles, loot, and a
goal platform at the far right.
"""

from __future__ import annotations
import random
import math
import pygame
from settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, GROUND_Y,
    PLATFORM_MIN_WIDTH, PLATFORM_MAX_WIDTH, PLATFORM_HEIGHT,
    MIN_GAP_X, MAX_GAP_X, MIN_GAP_Y, MAX_GAP_Y,
    PLATFORMS_PER_LEVEL, COIN_SIZE, COIN_SCORE, LEVEL_COMPLETE_BONUS,
    JUMP_IMPULSE, GRAVITY, MAX_RUN_SPEED,
    COL_PLATFORM, COL_PLATFORM_TOP, COL_PLATFORM_BOUNCE,
    COL_PLATFORM_CRUMBLE, COL_GOAL_PLATFORM, COL_COIN,
    ENEMY_WIDTH, ENEMY_HEIGHT, OBSTACLE_WIDTH, OBSTACLE_HEIGHT,
)
from enemies import Dasher, Marksman, Hybrid
from obstacles import Obstacle
from powerups import BasePowerUp, spawn_random_loot


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
        """Begin the crumble countdown."""
        if not self.crumbling:
            self.crumbling = True
            self.crumble_timer = self.crumble_delay

    def update(self, dt: float) -> None:
        """Update platform state (crumbling timer)."""
        if self.crumbling and self.active:
            self.crumble_timer -= dt
            self.shake_offset = random.uniform(-1.5, 1.5)
            if self.crumble_timer <= 0:
                self.active = False
                self.shake_offset = 0

    def get_color(self) -> tuple[int, int, int]:
        """Return the platform's color based on its type."""
        if self.platform_type == "bounce":
            return COL_PLATFORM_BOUNCE
        elif self.platform_type == "crumble":
            return COL_PLATFORM_CRUMBLE
        elif self.platform_type == "goal":
            return COL_GOAL_PLATFORM
        return COL_PLATFORM

    def get_top_color(self) -> tuple[int, int, int]:
        """Return highlight color for the top edge."""
        if self.platform_type == "bounce":
            return (120, 255, 210)
        elif self.platform_type == "crumble":
            return (180, 100, 80)
        elif self.platform_type == "goal":
            return (255, 240, 120)
        return COL_PLATFORM_TOP

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw the platform with a highlight strip on top."""
        if not self.active:
            return
        sx = int(self.rect.x - cam_x + self.shake_offset)
        sy = int(self.rect.y - cam_y)

        # Main body
        pygame.draw.rect(surface, self.get_color(),
                         (sx, sy, self.rect.width, self.rect.height))
        # Top highlight (1px)
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
        """Collision rect for the coin."""
        return pygame.Rect(
            int(self.x) - self.size // 2,
            int(self.y) - self.size // 2 + int(math.sin(self.bob_timer) * 2),
            self.size, self.size,
        )

    def update(self, dt: float) -> None:
        """Animate the bobbing motion."""
        self.bob_timer += dt * 3.0

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw a shiny coin."""
        if self.collected:
            return
        bob_y = int(math.sin(self.bob_timer) * 2)
        sx = int(self.x - cam_x)
        sy = int(self.y - cam_y + bob_y)

        # Outer glow
        pygame.draw.circle(surface, (255, 200, 40), (sx, sy), self.size // 2 + 1)
        # Inner
        pygame.draw.circle(surface, COL_COIN, (sx, sy), self.size // 2)
        # Shine highlight
        pygame.draw.circle(surface, (255, 255, 200),
                           (sx - 1, sy - 1), max(1, self.size // 4))


class LevelGenerator:
    """Procedural side-scrolling level: platforms progress rightward."""

    def __init__(self) -> None:
        self.platforms: list[Platform] = []
        self.coins: list[Coin] = []
        self.enemies: list = []          # Dasher, Marksman, Hybrid
        self.obstacles: list[Obstacle] = []
        self.powerups: list[BasePowerUp] = []
        self.goal_platform: Platform | None = None
        self.level_number: int = 0
        self.seed: int = 0

        # Pre-calculate max jump metrics from physics constants
        self.max_jump_height: float = (JUMP_IMPULSE ** 2) / (2 * GRAVITY)
        time_up = abs(JUMP_IMPULSE) / GRAVITY
        self.max_jump_distance: float = MAX_RUN_SPEED * time_up * 2

    def generate(self, level_number: int, seed: int | None = None) -> None:
        """Generate a new horizontal level layout.

        Args:
            level_number: Current level (affects difficulty).
            seed: Random seed for reproducibility.
        """
        self.level_number = level_number
        self.seed = seed if seed is not None else random.randint(0, 999999)
        random.seed(self.seed)

        self.platforms.clear()
        self.coins.clear()
        self.enemies.clear()
        self.obstacles.clear()
        self.powerups.clear()

        # Difficulty scaling
        difficulty = min(level_number / 10.0, 1.0)

        # ── Ground / starting platform (wide, at the left) ────────
        ground = Platform(0, GROUND_Y, INTERNAL_WIDTH // 2, PLATFORM_HEIGHT, "normal")
        self.platforms.append(ground)

        # Generate platforms progressing rightward
        num_platforms = PLATFORMS_PER_LEVEL + int(difficulty * 4)
        last_x = ground.rect.right  # start from end of ground
        last_y = GROUND_Y

        # Y-range for platform placement (stay within screen vertically)
        y_min = GROUND_Y - 100
        y_max = GROUND_Y

        bounce_chance = 0.1 + difficulty * 0.1
        crumble_chance = 0.03 + difficulty * 0.1

        for i in range(num_platforms):
            # Horizontal gap — always move RIGHT
            gap_x = random.randint(
                int(MIN_GAP_X + difficulty * 3),
                int(MAX_GAP_X + difficulty * 5),
            )

            # Vertical variation — platforms go up AND down
            y_shift = random.randint(-MAX_GAP_Y, MIN_GAP_Y)
            new_y = last_y + y_shift

            # Clamp Y so platforms stay within playable vertical band
            new_y = max(y_min, min(y_max, new_y))

            new_x = last_x + gap_x

            # Platform width
            width = random.randint(
                max(35, int(PLATFORM_MIN_WIDTH - difficulty * 4)),
                max(50, int(PLATFORM_MAX_WIDTH - difficulty * 6)),
            )

            # Determine platform type
            roll = random.random()
            if roll < crumble_chance and i > 2:
                ptype = "crumble"
            elif roll < crumble_chance + bounce_chance:
                ptype = "bounce"
            else:
                ptype = "normal"

            plat = Platform(int(new_x), int(new_y), width, PLATFORM_HEIGHT, ptype)
            self.platforms.append(plat)

            # Place a coin on some platforms
            if random.random() < 0.4 and ptype != "crumble":
                coin_x = int(new_x + width // 2)
                coin_y = int(new_y - 10)
                self.coins.append(Coin(coin_x, coin_y))

            last_x = int(new_x + width)  # next platform starts after this one ends
            last_y = int(new_y)

        # ── Goal platform at the far right ────────────────────────
        goal_x = last_x + MAX_GAP_X
        goal_y = last_y
        self.goal_platform = Platform(
            int(goal_x), int(goal_y), 60, PLATFORM_HEIGHT, "goal"
        )
        self.platforms.append(self.goal_platform)

        # Coin on goal
        self.coins.append(Coin(int(goal_x) + 30, int(goal_y) - 10))

        # ── Spawn enemies on random platforms ─────────────────────
        eligible_plats = [
            p for p in self.platforms
            if p.platform_type == "normal" and p != ground and p != self.goal_platform
        ]
        random.shuffle(eligible_plats)

        # No enemies on level 1
        if level_number <= 1:
            num_enemies = 0
        else:
            num_enemies = min(len(eligible_plats), int(difficulty * 2))
        enemy_classes = [Dasher, Marksman, Hybrid]

        for i in range(num_enemies):
            plat = eligible_plats[i]
            ex = plat.rect.x + plat.rect.width // 2 - ENEMY_WIDTH // 2
            ey = plat.rect.y - ENEMY_HEIGHT
            enemy_cls = enemy_classes[i % len(enemy_classes)]
            self.enemies.append(enemy_cls(ex, ey))

        # ── Spawn obstacles ──────────────────────────────────────
        remaining_plats = eligible_plats[num_enemies:]
        random.shuffle(remaining_plats)
        num_obstacles = min(len(remaining_plats), max(0, int(difficulty * 1.5)))
        for i in range(num_obstacles):
            plat = remaining_plats[i]
            ox = plat.rect.x + random.randint(2, max(3, plat.rect.width - OBSTACLE_WIDTH - 2))
            oy = plat.rect.y - OBSTACLE_HEIGHT
            self.obstacles.append(Obstacle(ox, oy))

        # ── Spawn weighted-random loot pickups ────────────────────
        loot_plats = remaining_plats[num_obstacles:]
        random.shuffle(loot_plats)
        num_loot = min(len(loot_plats), 3 + int(difficulty * 2))
        for i in range(num_loot):
            plat = loot_plats[i]
            px = plat.rect.x + plat.rect.width // 2
            py = plat.rect.y - 12
            self.powerups.append(spawn_random_loot(px, py))

    def update(self, dt: float) -> None:
        """Update all platforms, coins, and powerups."""
        for plat in self.platforms:
            plat.update(dt)
        for coin in self.coins:
            coin.update(dt)
        for pu in self.powerups:
            pu.update(dt)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw all platforms, coins, obstacles, and powerups."""
        for plat in self.platforms:
            plat.draw(surface, cam_x, cam_y)
        for coin in self.coins:
            coin.draw(surface, cam_x, cam_y)
        for obs in self.obstacles:
            obs.draw(surface, cam_x, cam_y)
        for pu in self.powerups:
            pu.draw(surface, cam_x, cam_y)

    def get_active_platforms(self) -> list[Platform]:
        """Return only active (non-crumbled) platforms."""
        return [p for p in self.platforms if p.active]

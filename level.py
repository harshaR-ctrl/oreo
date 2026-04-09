"""
level.py — Procedural level generator.

Creates platforms using a reachability-based algorithm: each new platform
is placed within jump range of the previous one. Difficulty scales with
level number. Includes coins and a goal platform at the top.
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
)


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
        self.x: int = x
        self.y: int = y
        self.size: int = COIN_SIZE
        self.collected: bool = False
        self.bob_timer: float = random.uniform(0, math.pi * 2)

    @property
    def rect(self) -> pygame.Rect:
        """Collision rect for the coin."""
        return pygame.Rect(
            self.x - self.size // 2,
            self.y - self.size // 2 + int(math.sin(self.bob_timer) * 2),
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
    """Procedural level generation with reachability constraints."""

    def __init__(self) -> None:
        self.platforms: list[Platform] = []
        self.coins: list[Coin] = []
        self.goal_platform: Platform | None = None
        self.level_number: int = 0
        self.seed: int = 0

        # Pre-calculate max jump metrics from physics constants
        # Max jump height: v²/(2g) where v = JUMP_IMPULSE
        self.max_jump_height: float = (JUMP_IMPULSE ** 2) / (2 * GRAVITY)
        # Max jump distance: horizontal speed * time_in_air
        time_up = abs(JUMP_IMPULSE) / GRAVITY
        self.max_jump_distance: float = MAX_RUN_SPEED * time_up * 2

    def generate(self, level_number: int, seed: int | None = None) -> None:
        """Generate a new level layout.
        
        Args:
            level_number: Current level (affects difficulty).
            seed: Random seed for reproducibility.
        """
        self.level_number = level_number
        self.seed = seed if seed is not None else random.randint(0, 999999)
        random.seed(self.seed)

        self.platforms.clear()
        self.coins.clear()

        # Difficulty scaling
        difficulty = min(level_number / 10.0, 1.0)  # 0.0 to 1.0 over 10 levels

        # Ground platform
        ground = Platform(0, GROUND_Y, INTERNAL_WIDTH, PLATFORM_HEIGHT, "normal")
        self.platforms.append(ground)

        # Generate platforms going upward
        num_platforms = PLATFORMS_PER_LEVEL + int(difficulty * 4)
        last_x = INTERNAL_WIDTH // 4
        last_y = GROUND_Y

        # Platform type weights change with difficulty
        bounce_chance = 0.1 + difficulty * 0.1
        crumble_chance = 0.05 + difficulty * 0.2

        for i in range(num_platforms):
            # Calculate reachable area from last platform
            gap_y = random.randint(
                MIN_GAP_Y,
                int(MAX_GAP_Y + difficulty * 10),
            )
            gap_x = random.randint(
                int(MIN_GAP_X + difficulty * 8),
                int(MAX_GAP_X + difficulty * 15),
            )

            new_y = last_y - gap_y
            direction = random.choice([-1, 1])
            new_x = last_x + direction * gap_x

            # Width gets narrower with difficulty
            width = random.randint(
                max(20, int(PLATFORM_MIN_WIDTH - difficulty * 10)),
                max(30, int(PLATFORM_MAX_WIDTH - difficulty * 15)),
            )

            # Keep within bounds with wrapping
            new_x = new_x % (INTERNAL_WIDTH - width)
            if new_x < 0:
                new_x += INTERNAL_WIDTH - width

            # Determine platform type
            roll = random.random()
            if roll < crumble_chance and i > 2:  # no crumbles near start
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

            last_x = int(new_x + width // 2)
            last_y = int(new_y)

        # Goal platform at the top
        goal_y = last_y - MAX_GAP_Y
        goal_x = random.randint(20, INTERNAL_WIDTH - 60)
        self.goal_platform = Platform(
            goal_x, int(goal_y), 50, PLATFORM_HEIGHT, "goal"
        )
        self.platforms.append(self.goal_platform)

        # Coin on goal
        self.coins.append(Coin(goal_x + 25, int(goal_y) - 10))

    def update(self, dt: float) -> None:
        """Update all platforms and coins."""
        for plat in self.platforms:
            plat.update(dt)
        for coin in self.coins:
            coin.update(dt)

    def draw(self, surface: pygame.Surface, cam_x: float, cam_y: float) -> None:
        """Draw all platforms and coins."""
        for plat in self.platforms:
            plat.draw(surface, cam_x, cam_y)
        for coin in self.coins:
            coin.draw(surface, cam_x, cam_y)

    def get_active_platforms(self) -> list[Platform]:
        """Return only active (non-crumbled) platforms."""
        return [p for p in self.platforms if p.active]

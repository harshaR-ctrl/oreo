"""
settings.py — Central configuration for Micro-Platformer.

All physics constants, display settings, colors, and game-feel tuning
parameters live here. Changing these values affects the entire game.
Includes difficulty presets and combo/milestone thresholds.
"""

import pygame

# ─── Game Info ─────────────────────────────────────────────────────────
GAME_VERSION: str = "2.0.0"

# ─── Display ──────────────────────────────────────────────────────────
INTERNAL_WIDTH: int = 400
INTERNAL_HEIGHT: int = 300
WINDOW_WIDTH: int = 800
WINDOW_HEIGHT: int = 600
FPS: int = 60
GAME_TITLE: str = "OREO RUNNER"

# ─── Physics ──────────────────────────────────────────────────────────
GRAVITY: float = 980.0               # px/s²
FRICTION: float = 0.82               # velocity multiplier per frame
AIR_FRICTION: float = 0.94           # less friction in the air
MAX_FALL_SPEED: float = 600.0        # terminal velocity
MAX_RUN_SPEED: float = 130.0         # max horizontal speed
ACCELERATION: float = 650.0          # horizontal acceleration px/s²

# ─── Jump ─────────────────────────────────────────────────────────────
JUMP_IMPULSE: float = -290.0         # initial jump velocity (upward)
JUMP_CUT_MULTIPLIER: float = 0.38   # velocity multiplied when releasing early
MAX_JUMP_HOLD_TIME: float = 0.18    # seconds spacebar adds upward force
JUMP_HOLD_FORCE: float = -400.0     # additional upward force while holding

# ─── Dash (Momentum-Based) ───────────────────────────────────────────
DASH_SPEED: float = 320.0            # base dash speed
MOMENTUM_FACTOR: float = 0.6         # how much current velocity is preserved
DASH_COOLDOWN: float = 0.5           # seconds between dashes
DASH_DURATION: float = 0.12          # how long the dash lasts
DASH_TRAIL_COUNT: int = 6            # number of ghost images in trail
DASH_TRAIL_LIFETIME: float = 0.25    # how long each ghost lasts

# ─── Game Feel ────────────────────────────────────────────────────────
COYOTE_FRAMES: int = 7               # frames of grace after leaving ledge
JUMP_BUFFER_FRAMES: int = 8          # frames of pre-land jump buffering
SCREEN_SHAKE_DECAY: float = 0.85     # how quickly shake dies down
SCREEN_SHAKE_MAX_OFFSET: float = 6.0 # max pixel displacement
CAMERA_LERP_SPEED: float = 0.08      # lower = smoother camera follow

# ─── Player ───────────────────────────────────────────────────────────
PLAYER_WIDTH: int = 10
PLAYER_HEIGHT: int = 14
PLAYER_SPAWN_X: int = 40
PLAYER_SPAWN_Y: int = 260

# ─── Level Generation ────────────────────────────────────────────────
PLATFORM_MIN_WIDTH: int = 200
PLATFORM_MAX_WIDTH: int = 400
PLATFORM_HEIGHT: int = 16
MIN_GAP_X: int = 10
MAX_GAP_X: int = 35
MIN_GAP_Y: int = 14
MAX_GAP_Y: int = 30
GROUND_Y: int = 290
PLATFORMS_PER_LEVEL: int = 12
COIN_SIZE: int = 6
COIN_SCORE: int = 100
LEVEL_COMPLETE_BONUS: int = 500

# ─── Particles ────────────────────────────────────────────────────────
PARTICLE_GRAVITY: float = 300.0
PARTICLE_FRICTION: float = 0.96

# ─── Colors (Curated palette — dark mode with neon accents) ──────────
# Background & environment
COL_BG: tuple = (10, 25, 15)
COL_BG_GRADIENT_TOP: tuple = (18, 10, 35)
COL_BG_GRADIENT_BOT: tuple = (5, 15, 8)

# Forest Tree Layers
COL_TREE_L1: tuple = (15, 30, 20)
COL_TREE_L2: tuple = (20, 40, 25)
COL_TREE_L3: tuple = (25, 50, 30)

# Platforms
COL_PLATFORM: tuple = (45, 50, 70)
COL_PLATFORM_TOP: tuple = (75, 85, 120)
COL_PLATFORM_BOUNCE: tuple = (80, 200, 170)
COL_PLATFORM_CRUMBLE: tuple = (120, 70, 60)
COL_GOAL_PLATFORM: tuple = (220, 180, 60)

# Player
COL_PLAYER_BODY: tuple = (100, 220, 255)
COL_PLAYER_OUTLINE: tuple = (40, 100, 160)
COL_PLAYER_DASH: tuple = (180, 120, 255)
COL_PLAYER_EYE: tuple = (255, 255, 255)

# Oreo themed colors
COL_OREO_DARK: tuple = (35, 25, 20)
COL_OREO_CREAM: tuple = (240, 230, 210)
COL_OREO_OUTLINE: tuple = (20, 15, 10)

# Particles
COL_DUST: tuple = (160, 160, 180)
COL_JUMP_DUST: tuple = (100, 180, 255)
COL_DASH_TRAIL: tuple = (140, 90, 220)
COL_DEATH: tuple = (255, 80, 80)
COL_COIN: tuple = (255, 220, 60)
COL_COIN_SPARKLE: tuple = (255, 240, 150)

# UI
COL_TEXT: tuple = (230, 230, 240)
COL_TEXT_DIM: tuple = (120, 120, 140)
COL_TEXT_ACCENT: tuple = (100, 220, 255)
COL_HUD_BG: tuple = (12, 12, 20, 180)
COL_MENU_PARTICLE: tuple = (60, 70, 100)
COL_MENU_SELECTED: tuple = (255, 200, 60)
COL_MENU_UNSELECTED: tuple = (140, 140, 160)

# ─── Enemies ──────────────────────────────────────────────────────────
DASHER_SPEED: float = MAX_RUN_SPEED * 0.5  # slower chase (was 0.7)
MARKSMAN_COOLDOWN: float = 3.5            # seconds between shots (was 2.5)
MARKSMAN_FLASH_DURATION: float = 0.4      # longer telegraph (was 0.2)
MARKSMAN_LEAD_FACTOR: float = 0.2         # less prediction (was 0.35)
HYBRID_FIRE_COOLDOWN: float = 3.0         # seconds between hybrid shots (was 2.0)
PROJECTILE_SPEED: float = 120.0           # enemy projectile px/s (was 200)
PLAYER_BULLET_SPEED: float = 300.0        # player bullet px/s
PLAYER_SHOOT_COOLDOWN: float = 0.3        # seconds between player shots
ENEMY_WIDTH: int = 10
ENEMY_HEIGHT: int = 12

# ─── Obstacles ────────────────────────────────────────────────────────
OBSTACLE_WIDTH: int = 24
OBSTACLE_HEIGHT: int = 24

# ─── Enemy & Entity Colors ───────────────────────────────────────────
COL_DASHER: tuple = (220, 60, 60)
COL_DASHER_EYE: tuple = (255, 200, 200)
COL_MARKSMAN: tuple = (160, 80, 220)
COL_MARKSMAN_FLASH: tuple = (255, 255, 255)
COL_MARKSMAN_EYE: tuple = (255, 180, 255)
COL_HYBRID: tuple = (240, 140, 40)
COL_HYBRID_EYE: tuple = (255, 220, 160)
COL_ENEMY_PROJECTILE: tuple = (255, 100, 100)
COL_PLAYER_BULLET: tuple = (100, 255, 220)
COL_OBSTACLE: tuple = (70, 75, 90)
COL_OBSTACLE_EDGE: tuple = (100, 110, 130)
COL_POWERUP_GUN: tuple = (255, 255, 200)
COL_POWERUP_GLOW: tuple = (255, 240, 150)

# ─── Lives ────────────────────────────────────────────────────────────
MAX_LIVES: int = 5
DAMAGE_INVINCIBILITY: float = 2.0     # seconds of i-frames after taking damage

# ─── PowerUp Durations (ms, for pygame.time.get_ticks()) ─────────────
POWERUP_DASH_DURATION: int = 8000     # 8 seconds of 2x speed
POWERUP_MAGNET_DURATION: int = 10000  # 10 seconds
POWERUP_SHIELD_DURATION: int = 6000   # 6 seconds
POWERUP_BLACKHOLE_DURATION: int = 6000
POWERUP_VOID_DURATION: int = 6000
MAGNET_RANGE: float = 200.0           # px radius for coin/powerup attraction
MAGNET_FORCE: float = 5.0             # attraction vector magnitude
WORMHOLE_TILES: int = 5               # teleport distance in tiles
TILE_SIZE: int = 12                   # reference tile unit for wormhole

# ─── Weapons (Strategy Pattern) ──────────────────────────────────────
WEAPON_TYPES: dict = {
    'pistol':  {'cooldown': 500,  'bullets': 1, 'spread': 0,  'is_continuous': False},
    'shotgun': {'cooldown': 800,  'bullets': 3, 'spread': 15, 'is_continuous': False},
    'rapid':   {'cooldown': 150,  'bullets': 1, 'spread': 5,  'is_continuous': False},
    'laser':   {'cooldown': 0,    'bullets': 1, 'spread': 0,  'is_continuous': True},
}
WEAPON_ORDER: list = ['pistol', 'shotgun', 'rapid', 'laser']

# ─── Loot Weights (for random.choices) ───────────────────────────────
LOOT_WEIGHTS: dict = {
    'heart':     5,
    'dash':      20,
    'magnet':    15,
    'wormhole':  10,
    'blackhole': 8,
    'void':      7,
    'shield':    12,
    'weapon':    15,
}

# ─── New Colors ───────────────────────────────────────────────────────
COL_HEART_FULL: tuple = (255, 60, 80)
COL_HEART_EMPTY: tuple = (60, 60, 80)
COL_SHIELD_RING: tuple = (80, 200, 255)
COL_MAGNET: tuple = (255, 100, 255)
COL_WORMHOLE: tuple = (100, 255, 180)
COL_BLACKHOLE: tuple = (40, 0, 80)
COL_VOID: tuple = (200, 60, 255)
COL_DASH_POWERUP: tuple = (255, 200, 60)
COL_WEAPON_PICKUP: tuple = (100, 255, 200)

# ─── Sound ────────────────────────────────────────────────────────────
SOUND_ENABLED: bool = True
SAMPLE_RATE: int = 22050
SOUND_VOLUME: float = 0.3
MUSIC_VOLUME: float = 0.15

# ─── Combo & Milestone System ────────────────────────────────────────
COMBO_WINDOW: float = 3.0            # seconds to chain kills
COMBO_BONUS_PER_LEVEL: int = 50      # extra points per combo level
MILESTONE_DISTANCES: list = [100, 250, 500, 1000, 2000, 5000]
MILESTONE_BONUS: int = 250           # points per milestone

# ─── Difficulty Presets ───────────────────────────────────────────────
# Each preset is a dict of multipliers applied to base values.
# Keys: lives, enemy_speed, enemy_fire_rate, obstacle_density,
#        powerup_frequency, platform_width, gap_size, score_mult
DIFFICULTY_PRESETS: dict = {
    "easy": {
        "label": "EASY",
        "description": "Relaxed pace, forgiving jumps",
        "lives": 7,
        "enemy_speed_mult": 0.6,
        "enemy_fire_rate_mult": 0.6,
        "obstacle_density_mult": 0.5,
        "powerup_frequency_mult": 1.5,
        "platform_width_mult": 1.3,
        "gap_size_mult": 0.7,
        "enemy_spawn_mult": 0.5,
        "score_mult": 0.8,
        "color": (80, 200, 120),
    },
    "normal": {
        "label": "NORMAL",
        "description": "Balanced challenge for all",
        "lives": 5,
        "enemy_speed_mult": 1.0,
        "enemy_fire_rate_mult": 1.0,
        "obstacle_density_mult": 1.0,
        "powerup_frequency_mult": 1.0,
        "platform_width_mult": 1.0,
        "gap_size_mult": 1.0,
        "enemy_spawn_mult": 1.0,
        "score_mult": 1.0,
        "color": (100, 180, 255),
    },
    "hard": {
        "label": "HARD",
        "description": "Tight platforms, aggressive foes",
        "lives": 3,
        "enemy_speed_mult": 1.4,
        "enemy_fire_rate_mult": 1.4,
        "obstacle_density_mult": 1.5,
        "powerup_frequency_mult": 0.6,
        "platform_width_mult": 0.75,
        "gap_size_mult": 1.3,
        "enemy_spawn_mult": 1.5,
        "score_mult": 1.5,
        "color": (255, 140, 60),
    },
    "insane": {
        "label": "INSANE",
        "description": "One life. No mercy.",
        "lives": 1,
        "enemy_speed_mult": 1.8,
        "enemy_fire_rate_mult": 1.8,
        "obstacle_density_mult": 2.0,
        "powerup_frequency_mult": 0.3,
        "platform_width_mult": 0.6,
        "gap_size_mult": 1.5,
        "enemy_spawn_mult": 2.0,
        "score_mult": 3.0,
        "color": (255, 40, 60),
    },
}
DIFFICULTY_ORDER: list = ["easy", "normal", "hard", "insane"]
DEFAULT_DIFFICULTY: str = "normal"

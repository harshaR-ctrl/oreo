"""
settings.py — Central configuration for Micro-Platformer.

All physics constants, display settings, colors, and game-feel tuning
parameters live here. Changing these values affects the entire game.
"""

import pygame

# ─── Display ──────────────────────────────────────────────────────────
INTERNAL_WIDTH: int = 400
INTERNAL_HEIGHT: int = 300
WINDOW_WIDTH: int = 800
WINDOW_HEIGHT: int = 600
FPS: int = 60
GAME_TITLE: str = "MICRO-PLATFORMER"

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
PLATFORM_MIN_WIDTH: int = 30
PLATFORM_MAX_WIDTH: int = 70
PLATFORM_HEIGHT: int = 6
MIN_GAP_X: int = 20
MAX_GAP_X: int = 65
MIN_GAP_Y: int = 18
MAX_GAP_Y: int = 45
GROUND_Y: int = 290
PLATFORMS_PER_LEVEL: int = 14
COIN_SIZE: int = 6
COIN_SCORE: int = 100
LEVEL_COMPLETE_BONUS: int = 500

# ─── Particles ────────────────────────────────────────────────────────
PARTICLE_GRAVITY: float = 300.0
PARTICLE_FRICTION: float = 0.96

# ─── Colors (Curated palette — dark mode with neon accents) ──────────
# Background & environment
COL_BG: tuple = (12, 12, 20)
COL_BG_GRADIENT_TOP: tuple = (8, 8, 18)
COL_BG_GRADIENT_BOT: tuple = (18, 14, 28)

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

# ─── Enemies ──────────────────────────────────────────────────────────
DASHER_SPEED: float = MAX_RUN_SPEED * 0.7
MARKSMAN_COOLDOWN: float = 2.5            # seconds between shots
MARKSMAN_FLASH_DURATION: float = 0.2      # seconds of telegraph flash
MARKSMAN_LEAD_FACTOR: float = 0.35        # prediction lookahead multiplier
HYBRID_FIRE_COOLDOWN: float = 2.0         # seconds between hybrid shots
PROJECTILE_SPEED: float = 200.0           # enemy projectile px/s
PLAYER_BULLET_SPEED: float = 300.0        # player bullet px/s
PLAYER_SHOOT_COOLDOWN: float = 0.3        # seconds between player shots
ENEMY_WIDTH: int = 10
ENEMY_HEIGHT: int = 12

# ─── Obstacles ────────────────────────────────────────────────────────
OBSTACLE_WIDTH: int = 12
OBSTACLE_HEIGHT: int = 12

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

# ─── Sound ────────────────────────────────────────────────────────────
SOUND_ENABLED: bool = True
SAMPLE_RATE: int = 22050
SOUND_VOLUME: float = 0.3

# 🍪 OREO RUNNER

An endless side-scrolling platformer with Oreo-themed visuals, procedural level generation, and synthesized audio — all built with pure Python and Pygame.

## Features

- **Endless Procedural Levels** — Platforms, enemies, and obstacles generate infinitely as you run
- **Oreo-Themed Character** — Play as a cute Oreo cookie with squash/stretch animations
- **4 Difficulty Levels** — Easy, Normal, Hard, and Insane modes with distinct balancing
- **3 Enemy Types** — Dasher (chaser), Marksman (sniper), Hybrid (chaser + shooter)
- **4 Weapon Types** — Pistol, Shotgun, Rapid-fire, and Laser
- **8 Power-ups** — Heart, Speed Boost, Magnet, Wormhole, Shield, Blackhole, Void, Weapon Upgrade
- **Combo System** — Chain kills for bonus points with visual feedback
- **Distance Milestones** — Earn bonuses at 100m, 250m, 500m, 1000m, 2000m, 5000m
- **Persistent High Scores** — Top 10 leaderboard saved locally
- **Procedural Sound Effects** — All audio synthesized at runtime, no external files needed
- **Ambient Music** — Procedural background music with chord progressions
- **Enhanced Visuals** — Parallax forest, fireflies, fog, vignette, particle effects

## Controls

| Action | Keys |
|--------|------|
| Move | ← → / A D |
| Jump | Space / W / ↑ (hold for higher) |
| Dash | Shift / X |
| Shoot | F / Z |
| Switch Weapon | Q |
| Pause | ESC / P |
| Retry (Game Over) | R |

## Installation

```bash
pip install pygame
```

## Running

```bash
python main.py
```

## Requirements

- Python 3.10+
- Pygame 2.0+

## Architecture

| File | Description |
|------|-------------|
| `main.py` | Entry point with error handling |
| `game.py` | Main loop and state machine manager |
| `states.py` | All game states (Menu, Playing, Pause, Game Over, etc.) |
| `settings.py` | Central configuration and difficulty presets |
| `player.py` | Player controller with kinematic movement |
| `level.py` | Endless procedural level generator |
| `enemies.py` | Three enemy types with AI behaviors |
| `projectiles.py` | Bullet, laser, and flame projectile systems |
| `powerups.py` | Eight collectible power-up types |
| `physics.py` | Physics engine with collision resolution |
| `camera.py` | Smooth camera follow with screen shake |
| `renderer.py` | Resolution-independent rendering pipeline |
| `particles.py` | Particle system for visual effects |
| `hud.py` | Heads-up display with score, hearts, combos |
| `sounds.py` | Procedural sound synthesis and music |
| `input_handler.py` | Decoupled input abstraction |
| `obstacles.py` | Static obstacle blocks |
| `highscores.py` | Persistent high score storage |

## Tips

- **Dash preserves momentum** — dash while running fast for a sling-shot effect
- **Hold jump** for maximum height
- **Chain kills** within 3 seconds for combo bonuses
- **Shield** makes you invincible AND kills enemies on contact
- **Void power-up** reflects enemy bullets back at them!
- Higher difficulties give higher score multipliers

## License

MIT
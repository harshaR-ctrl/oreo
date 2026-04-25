"""
main.py — Entry point for Oreo Runner.

Initializes and runs the game with proper error handling
and deprecation warning suppression.

Controls:
    ←→ / A/D    Move
    Space / W   Jump (hold for higher)
    Shift / X   Dash (preserves momentum!)
    F / Z       Shoot
    Q           Switch weapon
    ESC / P     Pause
    R           Restart (on game over)
"""

import warnings
import os

# Suppress the pkg_resources deprecation warning from pygame internals
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from game import Game


def main() -> None:
    """Create and run the game."""
    try:
        game = Game()
        game.run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"\n[Oreo Runner] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()

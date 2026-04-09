"""
main.py — Entry point for Micro-Platformer.

Initializes and runs the game. That's it — all logic lives in game.py.

Controls:
    ←→ / A/D    Move
    Space / W   Jump (hold for higher)
    Shift / X   Dash (preserves momentum!)
    R           Restart (on game over)
    ESC / X     Quit
"""

from game import Game


def main() -> None:
    """Create and run the game."""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

"""
highscores.py — Persistent high score storage.

JSON-based top-10 leaderboard stored in the user's home directory.
Each entry stores initials, score, distance, difficulty, enemies killed, and date.
"""

from __future__ import annotations
import json
import os
from datetime import datetime

SCORE_FILE: str = os.path.join(os.path.expanduser("~"), ".oreo_scores.json")
MAX_SCORES: int = 10


def _default_scores() -> list[dict]:
    """Create default empty score list."""
    return []


def load_scores() -> list[dict]:
    """Load scores from disk. Returns sorted list (highest first)."""
    try:
        if os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return sorted(data, key=lambda s: s.get("score", 0), reverse=True)[:MAX_SCORES]
    except (json.JSONDecodeError, IOError, KeyError):
        pass
    return _default_scores()


def save_scores(scores: list[dict]) -> None:
    """Save scores to disk."""
    try:
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(scores[:MAX_SCORES], f, indent=2)
    except IOError:
        pass


def add_score(
    score: int,
    distance: int,
    difficulty: str,
    enemies_killed: int = 0,
    coins: int = 0,
    time_survived: float = 0.0,
) -> tuple[int, bool]:
    """Add a score to the leaderboard.

    Returns (rank, is_new_high_score) where rank is 1-indexed position.
    rank == 0 means it didn't make the leaderboard.
    """
    scores = load_scores()

    entry = {
        "score": score,
        "distance": distance,
        "difficulty": difficulty,
        "enemies_killed": enemies_killed,
        "coins": coins,
        "time_survived": round(time_survived, 1),
        "date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Check if it's a new high score (beats #1)
    is_new_high = len(scores) == 0 or score > scores[0].get("score", 0)

    # Insert in sorted position
    scores.append(entry)
    scores.sort(key=lambda s: s.get("score", 0), reverse=True)
    scores = scores[:MAX_SCORES]

    # Find rank
    rank = 0
    for i, s in enumerate(scores):
        if s is entry:
            rank = i + 1
            break

    save_scores(scores)
    return rank, is_new_high


def get_high_score() -> int:
    """Get the current #1 high score, or 0 if none."""
    scores = load_scores()
    if scores:
        return scores[0].get("score", 0)
    return 0

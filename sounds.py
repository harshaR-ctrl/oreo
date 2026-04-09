"""
sounds.py — Procedural sound effect generator.

Creates all game sounds from synthesized waveforms at runtime —
no external audio files required. Uses numpy-less pure-Python
waveform generation for maximum portability.
"""

from __future__ import annotations
import array
import math
import random
import pygame
from settings import SAMPLE_RATE, SOUND_VOLUME, SOUND_ENABLED


def _make_sound(samples: list[int], freq: int = SAMPLE_RATE) -> pygame.mixer.Sound:
    """Convert a list of 16-bit signed samples into a Pygame Sound."""
    buf = array.array("h", samples)
    sound = pygame.mixer.Sound(buffer=buf)
    sound.set_volume(SOUND_VOLUME)
    return sound


def _sine(t: float, freq: float) -> float:
    return math.sin(2 * math.pi * freq * t)


def _square(t: float, freq: float) -> float:
    return 1.0 if _sine(t, freq) > 0 else -1.0


def _noise() -> float:
    return random.uniform(-1, 1)


def generate_jump_sound() -> pygame.mixer.Sound:
    """Short rising chirp."""
    duration = 0.1
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 300 + 800 * (t / duration)  # rising pitch
        env = 1.0 - (t / duration)  # fade out
        val = _square(t, freq) * env * 0.3
        samples.append(int(val * 32767))
    return _make_sound(samples)


def generate_land_sound() -> pygame.mixer.Sound:
    """Soft thud with noise."""
    duration = 0.06
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0 - (t / duration)
        val = (_sine(t, 80) * 0.5 + _noise() * 0.2) * env * 0.25
        samples.append(int(val * 32767))
    return _make_sound(samples)


def generate_dash_sound() -> pygame.mixer.Sound:
    """Whooshing sweep."""
    duration = 0.12
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 400 - 300 * (t / duration)  # falling pitch
        env = 1.0 - (t / duration) ** 0.5
        val = (_noise() * 0.4 + _sine(t, freq) * 0.3) * env * 0.3
        samples.append(int(val * 32767))
    return _make_sound(samples)


def generate_coin_sound() -> pygame.mixer.Sound:
    """Bright ding."""
    duration = 0.15
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0 - (t / duration)
        val = (_sine(t, 880) * 0.3 + _sine(t, 1320) * 0.2) * env * 0.3
        samples.append(int(val * 32767))
    return _make_sound(samples)


def generate_death_sound() -> pygame.mixer.Sound:
    """Descending buzz."""
    duration = 0.35
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 300 - 200 * (t / duration)
        env = 1.0 - (t / duration) ** 0.7
        val = (_square(t, freq) * 0.3 + _noise() * 0.15) * env * 0.25
        samples.append(int(val * 32767))
    return _make_sound(samples)


def generate_level_complete_sound() -> pygame.mixer.Sound:
    """Ascending arpeggio."""
    duration = 0.4
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    notes = [440, 554, 659, 880]
    note_dur = duration / len(notes)
    for i in range(n):
        t = i / SAMPLE_RATE
        note_idx = min(int(t / note_dur), len(notes) - 1)
        freq = notes[note_idx]
        local_t = (t - note_idx * note_dur) / note_dur
        env = 1.0 - local_t * 0.5
        val = _sine(t, freq) * env * 0.3
        samples.append(int(val * 32767))
    return _make_sound(samples)


class SoundManager:
    """Manages all game sounds."""

    def __init__(self) -> None:
        self.enabled: bool = SOUND_ENABLED
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        if self.enabled:
            try:
                self.sounds["jump"] = generate_jump_sound()
                self.sounds["land"] = generate_land_sound()
                self.sounds["dash"] = generate_dash_sound()
                self.sounds["coin"] = generate_coin_sound()
                self.sounds["death"] = generate_death_sound()
                self.sounds["level_complete"] = generate_level_complete_sound()
            except Exception:
                self.enabled = False

    def play(self, name: str) -> None:
        """Play a sound by name."""
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

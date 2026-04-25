"""
sounds.py — Procedural sound effect generator with background music.

Creates all game sounds from synthesized waveforms at runtime —
no external audio files required. Uses pure-Python waveform generation.
Includes a simple procedural ambient music loop.
"""

from __future__ import annotations
import array
import math
import random
import pygame
from settings import SAMPLE_RATE, SOUND_VOLUME, SOUND_ENABLED, MUSIC_VOLUME


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


def _triangle(t: float, freq: float) -> float:
    phase = (t * freq) % 1.0
    return 4.0 * abs(phase - 0.5) - 1.0


def _noise() -> float:
    return random.uniform(-1, 1)


def _adsr(t: float, duration: float, attack: float = 0.02, decay: float = 0.1,
           sustain: float = 0.6, release_start: float = 0.8) -> float:
    """ADSR envelope for richer sounds."""
    frac = t / duration
    if frac < attack:
        return frac / attack
    elif frac < attack + decay:
        return 1.0 - (1.0 - sustain) * ((frac - attack) / decay)
    elif frac < release_start:
        return sustain
    else:
        return sustain * (1.0 - (frac - release_start) / (1.0 - release_start))


# ─── Sound Generators ────────────────────────────────────────────────


def generate_jump_sound() -> pygame.mixer.Sound:
    """Short rising chirp with harmonics."""
    duration = 0.1
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 300 + 900 * (t / duration)
        env = _adsr(t, duration, 0.01, 0.02, 0.7, 0.7)
        val = (_square(t, freq) * 0.2 + _sine(t, freq * 2) * 0.1) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
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
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_dash_sound() -> pygame.mixer.Sound:
    """Whooshing sweep with harmonics."""
    duration = 0.12
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 400 - 300 * (t / duration)
        env = 1.0 - (t / duration) ** 0.5
        val = (_noise() * 0.35 + _sine(t, freq) * 0.25 + _sine(t, freq * 0.5) * 0.1) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_coin_sound() -> pygame.mixer.Sound:
    """Bright ding with shimmer."""
    duration = 0.18
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = _adsr(t, duration, 0.005, 0.03, 0.5, 0.6)
        val = (_sine(t, 880) * 0.25 + _sine(t, 1320) * 0.15 + _sine(t, 1760) * 0.08) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_death_sound() -> pygame.mixer.Sound:
    """Descending buzz with crunch."""
    duration = 0.4
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 300 - 200 * (t / duration)
        env = _adsr(t, duration, 0.01, 0.05, 0.6, 0.6)
        val = (_square(t, freq) * 0.25 + _noise() * 0.15 + _sine(t, freq * 0.5) * 0.1) * env * 0.25
        samples.append(int(max(-1, min(1, val)) * 32767))
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
        val = (_sine(t, freq) * 0.25 + _sine(t, freq * 2) * 0.08) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_powerup_sound() -> pygame.mixer.Sound:
    """Bright ascending chime for powerup pickup."""
    duration = 0.25
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 600 + 1200 * (t / duration)
        env = _adsr(t, duration, 0.01, 0.05, 0.7, 0.7)
        val = (_sine(t, freq) * 0.3 + _sine(t, freq * 1.5) * 0.12 + _triangle(t, freq * 0.5) * 0.05) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_damage_sound() -> pygame.mixer.Sound:
    """Crunchy impact hit."""
    duration = 0.15
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 200 - 100 * (t / duration)
        env = 1.0 - (t / duration)
        val = (_square(t, freq) * 0.3 + _noise() * 0.25) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_shield_hit_sound() -> pygame.mixer.Sound:
    """Metallic ping when shield absorbs a hit."""
    duration = 0.15
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = _adsr(t, duration, 0.005, 0.02, 0.5, 0.6)
        val = (_sine(t, 1200) * 0.25 + _sine(t, 2400) * 0.12 + _sine(t, 3600) * 0.06) * env * 0.25
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_weapon_switch_sound() -> pygame.mixer.Sound:
    """Short click/snap for weapon cycling."""
    duration = 0.05
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0 - (t / duration) ** 2
        val = _noise() * 0.2 * env
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_wormhole_sound() -> pygame.mixer.Sound:
    """Whoosh with reverb tail for teleportation."""
    duration = 0.25
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 500 - 400 * (t / duration)
        env = (1.0 - (t / duration)) ** 0.4
        val = (_sine(t, freq) * 0.2 + _noise() * 0.15) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_menu_select_sound() -> pygame.mixer.Sound:
    """Crisp blip for menu selection."""
    duration = 0.08
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = _adsr(t, duration, 0.005, 0.01, 0.8, 0.5)
        val = (_sine(t, 660) * 0.3 + _sine(t, 990) * 0.1) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_menu_navigate_sound() -> pygame.mixer.Sound:
    """Subtle tick for menu navigation."""
    duration = 0.04
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0 - (t / duration)
        val = _sine(t, 440) * 0.15 * env
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_pause_sound() -> pygame.mixer.Sound:
    """Low tone for pause."""
    duration = 0.12
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        env = 1.0 - (t / duration) ** 0.5
        val = (_sine(t, 220) * 0.25 + _sine(t, 330) * 0.1) * env * 0.25
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_combo_sound() -> pygame.mixer.Sound:
    """Quick ascending combo ding."""
    duration = 0.15
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    for i in range(n):
        t = i / SAMPLE_RATE
        freq = 800 + 600 * (t / duration)
        env = _adsr(t, duration, 0.005, 0.02, 0.6, 0.6)
        val = (_sine(t, freq) * 0.3 + _sine(t, freq * 1.5) * 0.1) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_milestone_sound() -> pygame.mixer.Sound:
    """Triumphant fanfare for distance milestones."""
    duration = 0.35
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    notes = [523, 659, 784]  # C5, E5, G5
    note_dur = duration / len(notes)
    for i in range(n):
        t = i / SAMPLE_RATE
        note_idx = min(int(t / note_dur), len(notes) - 1)
        freq = notes[note_idx]
        env = _adsr(t, duration, 0.01, 0.05, 0.7, 0.75)
        val = (_sine(t, freq) * 0.25 + _sine(t, freq * 2) * 0.08 + _triangle(t, freq) * 0.05) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_highscore_sound() -> pygame.mixer.Sound:
    """Celebratory chime for new high score."""
    duration = 0.6
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)
    notes = [523, 659, 784, 1047, 784, 1047]  # C5 E5 G5 C6 G5 C6
    note_dur = duration / len(notes)
    for i in range(n):
        t = i / SAMPLE_RATE
        note_idx = min(int(t / note_dur), len(notes) - 1)
        freq = notes[note_idx]
        env = _adsr(t, duration, 0.01, 0.05, 0.7, 0.8)
        val = (_sine(t, freq) * 0.2 + _sine(t, freq * 2) * 0.08 + _sine(t, freq * 3) * 0.03) * env * 0.3
        samples.append(int(max(-1, min(1, val)) * 32767))
    return _make_sound(samples)


def generate_ambient_music() -> pygame.mixer.Sound:
    """Generate a procedural ambient music loop (~8 seconds).

    Uses layered sine waves with a gentle chord progression
    for a dreamy forest atmosphere.
    """
    duration = 8.0
    samples: list[int] = []
    n = int(SAMPLE_RATE * duration)

    # Chord progression: Am → F → C → G (two bars each)
    chords = [
        (220, 261.6, 329.6),   # Am
        (174.6, 220, 261.6),   # F
        (261.6, 329.6, 392),   # C
        (196, 246.9, 293.7),   # G
    ]
    chord_dur = duration / len(chords)

    for i in range(n):
        t = i / SAMPLE_RATE
        chord_idx = min(int(t / chord_dur), len(chords) - 1)
        root, third, fifth = chords[chord_idx]

        # Smooth crossfade between chords
        chord_t = (t % chord_dur) / chord_dur
        fade = 1.0
        if chord_t < 0.05:
            fade = chord_t / 0.05
        elif chord_t > 0.95:
            fade = (1.0 - chord_t) / 0.05

        # Pad: soft sine layers
        pad = (
            _sine(t, root) * 0.15
            + _sine(t, third) * 0.10
            + _sine(t, fifth) * 0.08
            + _sine(t, root * 0.5) * 0.12  # sub bass
        )

        # Shimmer: high harmonics with tremolo
        shimmer = _sine(t, root * 4) * 0.02 * (0.5 + 0.5 * _sine(t, 0.8))

        # Overall envelope — gentle
        global_env = 0.5 + 0.5 * _sine(t, 0.25)  # slow breathing

        val = (pad + shimmer) * fade * global_env * MUSIC_VOLUME
        val = max(-1.0, min(1.0, val))
        samples.append(int(val * 32767))

    return _make_sound(samples)


class SoundManager:
    """Manages all game sounds and background music."""

    def __init__(self) -> None:
        self.enabled: bool = SOUND_ENABLED
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music: pygame.mixer.Sound | None = None
        self.music_channel: pygame.mixer.Channel | None = None

        if self.enabled:
            try:
                self.sounds["jump"] = generate_jump_sound()
                self.sounds["land"] = generate_land_sound()
                self.sounds["dash"] = generate_dash_sound()
                self.sounds["coin"] = generate_coin_sound()
                self.sounds["death"] = generate_death_sound()
                self.sounds["level_complete"] = generate_level_complete_sound()
                self.sounds["powerup"] = generate_powerup_sound()
                self.sounds["damage"] = generate_damage_sound()
                self.sounds["shield_hit"] = generate_shield_hit_sound()
                self.sounds["weapon_switch"] = generate_weapon_switch_sound()
                self.sounds["wormhole"] = generate_wormhole_sound()
                self.sounds["menu_select"] = generate_menu_select_sound()
                self.sounds["menu_nav"] = generate_menu_navigate_sound()
                self.sounds["pause"] = generate_pause_sound()
                self.sounds["combo"] = generate_combo_sound()
                self.sounds["milestone"] = generate_milestone_sound()
                self.sounds["highscore"] = generate_highscore_sound()
                # Generate music loop
                try:
                    self.music = generate_ambient_music()
                except Exception:
                    self.music = None
            except Exception:
                self.enabled = False

    def play(self, name: str) -> None:
        """Play a sound by name."""
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def start_music(self) -> None:
        """Start playing background music on loop."""
        if self.enabled and self.music is not None:
            try:
                self.music_channel = self.music.play(loops=-1)
                if self.music_channel:
                    self.music_channel.set_volume(MUSIC_VOLUME)
            except Exception:
                pass

    def stop_music(self) -> None:
        """Stop background music."""
        if self.music_channel is not None:
            try:
                self.music_channel.stop()
            except Exception:
                pass
            self.music_channel = None

    def set_music_volume(self, volume: float) -> None:
        """Set music volume (0.0 to 1.0)."""
        if self.music_channel is not None:
            try:
                self.music_channel.set_volume(volume)
            except Exception:
                pass

"""Original synthesized music and effects; no official game recordings."""
from array import array
import math
from pathlib import Path
import sys
import wave
import pygame

RATE = 22050
ASSETS = Path(__file__).resolve().parent / 'assets' / 'audio'


def write_wav(path, samples):
    values = array('h', (int(max(-.95, min(.95, s)) * 32767) for s in samples))
    if sys.byteorder != 'little':
        values.byteswap()
    with wave.open(str(path), 'wb') as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(RATE)
        out.writeframes(values.tobytes())


def add_note(buffer, start, duration, freq, volume=.18, soft=False):
    begin, count = int(start * RATE), int(duration * RATE)
    for i in range(count):
        if begin+i >= len(buffer):
            break
        t = i / RATE
        envelope = min(1, t / .018) * max(0, 1-i/count) ** (1.4 if soft else 2.5)
        tone = math.sin(math.tau * freq * t) + .2 * math.sin(math.tau * freq * 2 * t)
        buffer[begin+i] += tone * envelope * volume


def build_assets():
    ASSETS.mkdir(parents=True, exist_ok=True)
    patterns = {
        'dew': ([880, 1174], .055), 'seed': ([523, 659, 784, 1047], .11),
        'berry': ([440, 660, 880], .10), 'escape': ([330, 494, 740, 1110], .08),
        'hit': ([220, 165, 110], .13), 'cleared': ([523, 659, 784, 1047, 1318], .16),
        'caught': ([392, 330, 262, 196], .19), 'click': ([660], .05),
    }
    for name, (notes, step) in patterns.items():
        data = [0.0] * int((len(notes)*step+.2)*RATE)
        for i, frequency in enumerate(notes):
            add_note(data, i*step, step+.13, frequency, .24)
        write_wav(ASSETS / f'{name}.wav', data)
    # A newly composed 16-second, pentatonic garden loop.
    data = [0.0] * (RATE * 16)
    melody = [64, 67, 69, 67, 64, 62, 60, 62, 64, 67, 72, 69, 67, 64, 62, 60,
              57, 60, 64, 67, 64, 60, 62, 64, 67, 69, 72, 67, 64, 62, 60, 67]
    hz = lambda midi: 440 * 2 ** ((midi-69)/12)
    for i, note in enumerate(melody):
        add_note(data, i*.5, .45, hz(note), .105, True)
        if i % 2 == 0:
            add_note(data, i*.5, .9, hz([48, 45, 53, 55][i//8]), .075, True)
    write_wav(ASSETS / 'orchard_loop.wav', data)


class Audio:
    def __init__(self, music=True, effects=True):
        self.available = False
        self.music, self.effects = music, effects
        self.sounds = {}
        self.current_biome = None
        self.danger = False
        self.danger_channel = None
        self.danger_layers = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            for path in ASSETS.glob('*.wav'):
                if path.stem.startswith('pursuit_'):
                    self.danger_layers[int(path.stem.split('_')[1])-1] = pygame.mixer.Sound(str(path))
                elif path.stem != 'orchard_loop' and not path.stem.startswith('biome_'):
                    self.sounds[path.stem] = pygame.mixer.Sound(str(path))
            pygame.mixer.music.load(str(ASSETS / 'orchard_loop.wav'))
            pygame.mixer.music.set_volume(.4)
            pygame.mixer.music.play(-1)
            pygame.mixer.set_reserved(1)
            self.danger_channel = pygame.mixer.Channel(0)
            self.available = True
            self.apply()
        except (pygame.error, FileNotFoundError):
            pass

    def set_biome(self, tier):
        if not self.available or tier == self.current_biome:
            return
        self.set_danger(False)
        filename = 'orchard_loop.wav' if tier is None else f'biome_{tier+1}.wav'
        try:
            pygame.mixer.music.load(str(ASSETS / filename))
            pygame.mixer.music.play(-1, fade_ms=500)
            self.current_biome = tier
            self.apply()
        except (pygame.error, FileNotFoundError):
            self.available = False

    def apply(self):
        if self.available:
            pygame.mixer.music.set_volume(.4 if self.music else 0)
            if self.danger_channel: self.danger_channel.set_volume(.28 if self.music and self.danger else 0)

    def set_danger(self, active):
        active = bool(active and self.current_biome is not None)
        if not self.available or active == self.danger: return
        self.danger = active
        if active and self.current_biome in self.danger_layers:
            self.danger_channel.play(self.danger_layers[self.current_biome], loops=-1, fade_ms=600)
        elif self.danger_channel:
            self.danger_channel.fadeout(600)
        self.apply()

    def play(self, event):
        if self.available and self.effects and event in self.sounds:
            channel = self.sounds[event].play()
            if channel: channel.set_volume(.55 if event == 'warning' else .8)


if __name__ == '__main__':
    build_assets()

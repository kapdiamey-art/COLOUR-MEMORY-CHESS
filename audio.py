import pygame
import math
import array
import random

class SoundManager:
    def __init__(self):
        pygame.mixer.init(frequency=44100, size=-16, channels=2)
        self.enabled = True
        self.sounds = {
            "click": self._gen_tone(440, 0.05),
            "match": self._gen_tone(880, 0.15),
            "fail": self._gen_tone(220, 0.2),
            "move": self._gen_tone(660, 0.08),
            "win": self._gen_tone(1100, 0.5),
        }
        self.bg_music = self._gen_music()
        self.bg_music.play(-1) # Loop forever

    def _gen_tone(self, freq, duration, vol=0.3):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            t = i / sample_rate
            val = math.sin(2.0 * math.pi * freq * t) * (1 - i / n_samples)
            buf[i] = int(val * 32767 * vol)
        return pygame.mixer.Sound(buf)

    def _gen_music(self):
        # Generate a meditative, airy soundscape (Zen-like)
        sample_rate = 44100
        duration = 10.0 # Long loop
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        # Airy frequencies (F major 7th feel)
        frequencies = [174.61, 220.00, 261.63, 329.63] # F, A, C, E
        
        for i in range(n_samples):
            t = i / sample_rate
            
            # Very slow, multi-layered modulation for an "organic" feel
            mod1 = math.sin(2.0 * math.pi * 0.1 * t) * 0.5 + 0.5
            mod2 = math.sin(2.0 * math.pi * 0.05 * t) * 0.5 + 0.5
            
            val = 0
            for idx, freq in enumerate(frequencies):
                # Each frequency has its own slow-moving envelope
                env = math.sin(math.pi * (t + idx * 2.5) / 10.0) ** 2
                val += math.sin(2.0 * math.pi * freq * t) * env * 0.25
            
            # Add a tiny bit of "air" (soft noise-like component)
            air = (random.random() * 2 - 1) * 0.02
            
            final_val = (val + air) * (0.05 + 0.05 * mod1)
            buf[i] = int(final_val * 32767)
            
        return pygame.mixer.Sound(buf)

    def play(self, key):
        if self.enabled and key in self.sounds:
            self.sounds[key].play()

    def set_volume(self, vol):
        for s in self.sounds.values():
            s.set_volume(vol)
        self.bg_music.set_volume(vol * 0.5)

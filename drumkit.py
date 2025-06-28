import sounddevice as sd
import numpy as np

class DrumKit:
    def __init__(self):
        # Load your drum samples here as dict: instrument -> list of (audio_array, sample_rate)
        self.samples = {
            "kick": [], "snare": [], "hat": [], "perc": []
        }
        self.variations = 5  # number of variations per instrument

    def play_track_step(self, track_idx, step):
        inst_map = {0: "kick", 1: "snare", 2: "hat", 3: "perc"}
        inst = inst_map.get(track_idx)
        if not inst:
            return
        variation = step.get("variation", 0)
        velocity = step.get("velocity", 1.0)
        self.play(inst, variation, velocity)

    def play(self, inst, variation=0, velocity=1.0):
        if inst not in self.samples or not self.samples[inst]:
            print(f"No samples for {inst}")
            return
        variation = max(0, min(self.variations - 1, variation))
        if variation >= len(self.samples[inst]):
            print(f"Variation {variation} not loaded for {inst}")
            return
        sample, sr = self.samples[inst][variation]
        scaled = (sample * velocity).astype(np.int16)
        sd.play(scaled, samplerate=sr, blocking=False)

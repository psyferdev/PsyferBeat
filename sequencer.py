import time
import json
from drumkit import DrumKit
from synth import Synth, generate_synth_sample, play_sample

class StepSequencer:
    def __init__(self, steps=16, tempo=120, resolution="1/16"):
        self.steps = steps
        self.tempo = tempo
        self.resolution = resolution
        self.pattern = [[{"on": 0, "note": 60, "velocity": 1.0, "variation": 0} for _ in range(steps)] for _ in range(8)]
        self.track_names = ["Kick", "Snare", "Hat", "Perc", "Synth 1", "Synth 2", "Synth 3", "Synth 4"]
        self.drumkit = DrumKit()
        self.synth_patch = {
            "name": "Reasonified Lead",
            "osc1_type": "sawtooth",
            "osc1_level": 0.6,
            "osc2_type": "square",
            "osc2_level": 0.4,
            "filter_type": "lowpass",
            "filter_cutoff": 1200,
            "filter_resonance": 0.7,
            "adsr": {"attack": 0.01, "decay": 0.2, "sustain": 0.8, "release": 0.3},
            "lfo_rate": 5.0,
            "lfo_depth": 0.2,
            "volume": 0.9,
        }
        self.synth = Synth(self.synth_patch)

    def toggle_step(self, track_index, step_index):
        self.pattern[track_index][step_index]["on"] ^= 1

    def set_note(self, track_index, step_index, note):
        self.pattern[track_index][step_index]["note"] = note

    def get_step_duration(self):
        beat_duration = 60.0 / self.tempo
        subdivision = int(self.resolution.split("/")[1])
        return beat_duration * (4 / subdivision)

    def play_step_callback(self, track_idx, step):
        if track_idx < 4:
            self.drumkit.play_track_step(track_idx, step)
        else:
            note = step.get("note", 60)
            velocity = step.get("velocity", 1.0)
            duration = self.get_step_duration()
            sample = generate_synth_sample(self.synth.patch, freq=note, duration=duration, velocity=velocity)
            play_sample(sample)

    def save_to_file(self, filename):
        with open(filename, "w") as f:
            json.dump({
                "steps": self.steps,
                "tempo": self.tempo,
                "resolution": self.resolution,
                "pattern": self.pattern,
                "track_names": self.track_names
            }, f, indent=2)

    @staticmethod
    def load_from_file(filename):
        with open(filename, "r") as f:
            data = json.load(f)
        seq = StepSequencer(steps=data["steps"], tempo=data["tempo"], resolution=data["resolution"])
        seq.pattern = data["pattern"]
        seq.track_names = data["track_names"]
        return seq

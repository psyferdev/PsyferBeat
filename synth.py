import numpy as np
import sounddevice as sd

def sine_wave(freq, length, sr):
    t = np.linspace(0, length, int(sr * length), False)
    return np.sin(2 * np.pi * freq * t)

def saw_wave(freq, length, sr):
    t = np.linspace(0, length, int(sr * length), False)
    return 2 * (t * freq - np.floor(0.5 + t * freq))

def apply_adsr(signal, sr, attack, decay, sustain, release):
    length = len(signal)
    attack_len = int(sr * attack)
    decay_len = int(sr * decay)
    release_len = int(sr * release)
    sustain_len = length - attack_len - decay_len - release_len
    sustain_len = max(0, sustain_len)
    envelope = np.concatenate([
        np.linspace(0, 1, attack_len),
        np.linspace(1, sustain, decay_len),
        np.full(sustain_len, sustain),
        np.linspace(sustain, 0, release_len)
    ])
    return signal[:len(envelope)] * envelope

def lowpass_filter(signal, cutoff, sr):
    rc = 1.0 / (2 * np.pi * cutoff)
    dt = 1.0 / sr
    alpha = dt / (rc + dt)
    filtered = np.zeros_like(signal)
    for i in range(1, len(signal)):
        filtered[i] = filtered[i-1] + alpha * (signal[i] - filtered[i-1])
    return filtered

def generate_synth_sample(patch, freq, duration, velocity=1.0, sr=44100):
    osc1 = patch.get('osc1_type', 'sine')
    osc2 = patch.get('osc2_type', 'sine')
    osc1_level = patch.get('osc1_level', 0.7)
    osc2_level = patch.get('osc2_level', 0.3)

    wave_map = {
        'sine': sine_wave,
        'sawtooth': saw_wave,
    }
    sig1 = wave_map[osc1](freq, duration, sr) * osc1_level
    sig2 = wave_map[osc2](freq, duration, sr) * osc2_level

    signal = sig1 + sig2
    signal = signal / np.max(np.abs(signal))

    adsr = patch.get('adsr', {'attack':0.01, 'decay':0.2, 'sustain':0.8, 'release':0.3})
    signal = apply_adsr(signal, sr,
                       adsr.get('attack',0.01),
                       adsr.get('decay',0.2),
                       adsr.get('sustain',0.8),
                       adsr.get('release',0.3))

    cutoff = patch.get('filter_cutoff', 1000)
    filtered = lowpass_filter(signal, cutoff, sr)

    volume = patch.get('volume', 0.8) * velocity
    output = filtered * volume

    output = np.int16(output / np.max(np.abs(output)) * 32767)
    return output

def play_sample(sample, samplerate=44100):
    sd.play(sample, samplerate=samplerate, blocking=False)

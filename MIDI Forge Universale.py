import streamlit as st
import streamlit.components.v1 as components
import mido
import random
import math
import io
import base64
from datetime import datetime
from collections import Counter

# ================= CONFIGURAZIONE PAGINA =================
st.set_page_config(page_title="MIDI Forge Universale", page_icon="🎛️", layout="wide")

# ================= DATABASE DEI GENERI =================
GENRES = {
    'acid': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'ambient': {'bpm_default': 80, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.15, 'swing': 0.0},
    'armonico': {'bpm_default': 100, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.70, 'swing': 0.10},
    'breakcore': {'bpm_default': 200, 'bars_default': 48, 'kick': [1,0,0,1, 0,1,0,0, 1,0,1,0, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,1,0,0, 1,0,0,1], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,0, 0,1,0,1], 'arp_density': 0.80, 'swing': 0.05},
    'commerciale_90s': {'bpm_default': 128, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'arp_density': 0.60, 'swing': 0.0},
    'deep': {'bpm_default': 122, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.50, 'swing': 0.15},
    'disco': {'bpm_default': 120, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.05},
    'drone': {'bpm_default': 70, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.05, 'swing': 0.0},
    'drum_n_bass': {'bpm_default': 174, 'bars_default': 48, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,1, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.70, 'swing': 0.0},
    'dub_techno': {'bpm_default': 125, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'arp_density': 0.40, 'swing': 0.0},
    'edm_2000s': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'elettronico': {'bpm_default': 128, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'funk': {'bpm_default': 110, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,1,0,0], 'arp_density': 0.60, 'swing': 0.15},
    'glitch': {'bpm_default': 120, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,1, 0,0,0,0, 1,0,0,0], 'arp_density': 0.95, 'swing': 0.0},
    'harsh_noise': {'bpm_default': 100, 'bars_default': 64, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 1.0, 'swing': 0.0},
    'hip_hop': {'bpm_default': 90, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.30, 'swing': 0.35},
    'idm': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'snare': [0,0,1,0, 1,0,0,1, 0,0,1,0, 1,0,1,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.85, 'swing': 0.10},
    'industrial': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.70, 'swing': 0.0},
    'lowercase': {'bpm_default': 60, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.05, 'swing': 0.0},
    'microsound': {'bpm_default': 80, 'bars_default': 96, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.10, 'swing': 0.0},
    'minimal': {'bpm_default': 124, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.30, 'swing': 0.0},
    'minimal_techno': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.50, 'swing': 0.0},
    'minimalismo_ritmico': {'bpm_default': 110, 'bars_default': 64, 'kick': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.60, 'swing': 0.05},
    'noise': {'bpm_default': 120, 'bars_default': 64, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 0.90, 'swing': 0.0},
    'onkyo': {'bpm_default': 50, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.02, 'swing': 0.0},
    'r&b': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.55, 'swing': 0.25},
    'reggaeton': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.50, 'swing': 0.0},
    'sperimentale': {'bpm_default': 100, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,1,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,1,0,0, 1,0,0,1, 0,0,1,0, 1,0,0,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,1], 'arp_density': 0.70, 'swing': 0.10},
    'soul': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.60, 'swing': 0.30},
    'synthpop': {'bpm_default': 118, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.75, 'swing': 0.0},
    'techno': {'bpm_default': 128, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'trap': {'bpm_default': 140, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.40, 'swing': 0.0},
    'trance': {'bpm_default': 138, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1]*16, 'arp_density': 0.90, 'swing': 0.0},
    'underground': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.65, 'swing': 0.0}
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
TICKS_BEAT = 480
DRUM_CH = 9

# ================= FUNZIONI CORE =================
def extract_notes(mid_file):
    notes = []
    mid = mido.MidiFile(file=mid_file)
    for track in mid.tracks:
        current_tick = 0
        for msg in track:
            current_tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append({'pitch': msg.note, 'tick': current_tick, 'vel': msg.velocity})
    return notes

def extract_dna(notes):
    all_pc, low_pc = Counter(), Counter()
    for n in notes:
        pc = n['pitch'] % 12
        all_pc[pc] += 1
        if n['pitch'] < 60: low_pc[pc] += 1
    root = (low_pc or all_pc).most_common(1)[0][0]
    intervals = sorted({(pc - root) % 12 for pc in all_pc})
    if len(intervals) < 4:
        for i in (3, 5, 7, 10):
            if i not in intervals: intervals.append(i)
        intervals = sorted(set(intervals))
    if 0 not in intervals: intervals.insert(0, 0)
    return root, intervals

def snap_to_scale(pitch, root, scale):
    octave = (pitch - root) // 12
    note_in_octave = (pitch - root) % 12
    closest = min(scale, key=lambda x: abs(x - note_in_octave))
    return root + (octave * 12) + closest

def generate_minimal(notes_data, g, submode, bars, seed):
    random.seed(seed)
    root, scale = extract_dna(notes_data)
    events = []
    
    if submode == 'extract':
        max_tick = max(n['tick'] for n in notes_data)
        notes_by_step = {}
        for n in notes_data:
            step = round(n['tick'] / (TICKS_BEAT // 4))
            if step not in notes_by_step: notes_by_step[step] = []
            notes_by_step[step].append(n['pitch'])
    
    m = [random.randrange(len(scale)) if random.random() < g['arp_density'] else None for _ in range(8)]
    
    for bar in range(bars):
        base_tick = bar * 4 * TICKS_BEAT
        if bar % 4 == 0 and bar > 0:
            op = random.choice(['transpose', 'invert', 'drop'])
            if op == 'transpose': m = [(x + 1) % len(scale) if x is not None else None for x in m]
            elif op == 'invert': m = list(reversed(m))
            else: m = [None if random.random() < 0.3 else x for x in m]

        for s in range(16):
            tick = base_tick + s * (TICKS_BEAT // 4)
            p_step = s % 16
            swing_offset = int(g['swing'] * (TICKS_BEAT // 4)) if (p_step % 2 == 1) else 0
            
            if g['kick'][p_step]:
                events.extend([{'tick': tick, 'type': 'on', 'pitch': 36, 'vel': 110, 'channel': DRUM_CH},
                               {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': 36, 'vel': 0, 'channel': DRUM_CH}])
            if g.get('snare', [0]*16)[p_step]:
                events.extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': 38, 'vel': 100, 'channel': DRUM_CH},
                               {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': 38, 'vel': 0, 'channel': DRUM_CH}])
            if g.get('clap', [0]*16)[p_step]:
                events.extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': 39, 'vel': 90, 'channel': DRUM_CH},
                               {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': 39, 'vel': 0, 'channel': DRUM_CH}])
            if g['hat'][p_step]:
                events.extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': 42, 'vel': 70 + random.randint(0, 20), 'channel': DRUM_CH},
                               {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': 42, 'vel': 0, 'channel': DRUM_CH}])
            
            if submode == 'extract' and s in notes_by_step:
                low_p, high_p = min(notes_by_step[s]), max(notes_by_step[s])
                if g['bass'][p_step]:
                    pitch = max(28, min(snap_to_scale(low_p, root, scale) - 24, 45))
                    events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 95, 'channel': 0},
                                   {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 0}])
                if random.random() < g['arp_density']:
                    pitch = max(60, snap_to_scale(high_p, root, scale))
                    events.extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': pitch, 'vel': 70, 'channel': 1},
                                   {'tick': tick + (TICKS_BEAT//4) - 10, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 1}])
            else:
                if g['bass'][p_step]:
                    idx = 0 if random.random() < 0.8 else random.choice([1, len(scale)-1])
                    pitch = max(28, min(root - 24 + scale[idx % len(scale)], 45))
                    events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 95, 'channel': 0},
                                   {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 0}])
                if m[s % 8] is not None:
                    pitch = root + 12 + scale[m[s % 8] % len(scale)]
                    events.extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': pitch, 'vel': 70, 'channel': 1},
                                   {'tick': tick + (TICKS_BEAT//4) - 20, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 1}])
    return events, root, scale

def generate_multitrack(mid_file_bytes, g, submode, bars, seed):
    random.seed(seed)
    mid = mido.MidiFile(file=mid_file_bytes)
    
    all_notes_flat = []
    for track in mid.tracks:
        current_tick = 0
        for msg in track:
            current_tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                all_notes_flat.append({'pitch': msg.note, 'tick': current_tick})
    
    root, scale = extract_dna(all_notes_flat)
    events = []
    
    if submode == 'faithful':
        track_channel = 0
        for original_track in mid.tracks:
            if any(msg.channel == DRUM_CH for msg in original_track if hasattr(msg, 'channel')):
                continue
            current_tick = 0
            for msg in original_track:
                current_tick += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    step = round(current_tick / (TICKS_BEAT // 4))
                    tick = step * (TICKS_BEAT // 4)
                    pitch = snap_to_scale(msg.note, root, scale)
                    events.extend([
                        {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': msg.velocity, 'channel': track_channel},
                        {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': track_channel}
                    ])
            track_channel += 1
    else:
        roles = [
            ('sub_bass', 0, (24, 36)),
            ('bassline', 1, (36, 48)),
            ('pad', 2, (48, 60)),
            ('chords', 3, (55, 67)),
            ('arp', 4, (60, 72)),
            ('lead', 5, (67, 79)),
            ('fx_perc', 6, (72, 84))
        ]
        
        for role_name, channel, (low_pitch, high_pitch) in roles:
            for bar in range(bars):
                base_tick = bar * 4 * TICKS_BEAT
                
                if role_name == 'sub_bass':
                    if bar % 4 == 0:
                        pitch = root - 24 + scale[0]
                        events.extend([{'tick': base_tick, 'type': 'on', 'pitch': max(24, pitch), 'vel': 100, 'channel': channel},
                                       {'tick': base_tick + 4 * TICKS_BEAT, 'type': 'off', 'pitch': max(24, pitch), 'vel': 0, 'channel': channel}])
                elif role_name == 'bassline':
                    for s in range(16):
                        if g['bass'][s]:
                            tick = base_tick + s * (TICKS_BEAT // 4)
                            idx = 0 if random.random() < 0.8 else random.choice([1, len(scale)-1])
                            pitch = root - 12 + scale[idx % len(scale)]
                            events.extend([{'tick': tick, 'type': 'on', 'pitch': max(30, min(pitch, 48)), 'vel': 95, 'channel': channel},
                                           {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': max(30, min(pitch, 48)), 'vel': 0, 'channel': channel}])
                elif role_name in ['pad', 'chords']:
                    if random.random() < 0.5:
                        tick = base_tick
                        for i in range(3):
                            idx = random.randrange(len(scale))
                            pitch = random.randint(low_pitch, high_pitch)
                            pitch = snap_to_scale(pitch, root, scale)
                            dur = 4 * TICKS_BEAT if role_name == 'pad' else (TICKS_BEAT // 2)
                            events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 70, 'channel': channel},
                                           {'tick': tick + dur, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}])
                elif role_name == 'arp':
                    for s in range(16):
                        if random.random() < g['arp_density']:
                            tick = base_tick + s * (TICKS_BEAT // 4)
                            idx = random.randrange(len(scale))
                            pitch = random.randint(low_pitch, high_pitch)
                            pitch = snap_to_scale(pitch, root, scale)
                            events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 75, 'channel': channel},
                                           {'tick': tick + (TICKS_BEAT//4) - 10, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}])
                elif role_name == 'lead':
                    if random.random() < 0.3:
                        tick = base_tick + random.choice([0, TICKS_BEAT, 2*TICKS_BEAT, 3*TICKS_BEAT])
                        pitch = random.randint(low_pitch, high_pitch)
                        pitch = snap_to_scale(pitch, root, scale)
                        events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 85, 'channel': channel},
                                       {'tick': tick + TICKS_BEAT, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}])
                elif role_name == 'fx_perc':
                    for s in range(16):
                        if random.random() < 0.1:
                            tick = base_tick + s * (TICKS_BEAT // 4)
                            pitch = random.randint(80, 95)
                            events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 50, 'channel': channel},
                                           {'tick': tick + 20, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}])

    for bar in range(bars):
        base_tick = bar * 4 * TICKS_BEAT
        for s in range(16):
            tick = base_tick + s * (TICKS_BEAT // 4)
            p_step = s % 16
            swing_offset = int(g['swing'] * (TICKS_BEAT // 4)) if (p_step % 2 == 1) else 0
            
            if g['kick'][p_step]:
                events.extend([{'tick': tick, 'type': 'on', 'pitch': 36, 'vel': 110, 'channel': DRUM_CH},
                               {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': 36, 'vel': 0, 'channel': DRUM_CH}])
            if g.get('snare', [0]*16)[p_step]:
                events.extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': 38, 'vel': 100, 'channel': DRUM_CH},
                               {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': 38, 'vel': 0, 'channel': DRUM_CH}])
            if g['hat'][p_step]:
                events.extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': 42, 'vel': 75, 'channel': DRUM_CH},
                               {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': 42, 'vel': 0, 'channel': DRUM_CH}])

    return events, root, scale

def build_midi_file(events, bpm, mode, submode):
    mid = mido.MidiFile(ticks_per_beat=TICKS_BEAT)
    t_tempo = mido.MidiTrack()
    t_tempo.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    mid.tracks.append(t_tempo)
    
    events.sort(key=lambda e: (e['tick'], 0 if e['type'] == 'off' else 1))
    
    channels = {}
    for e in events:
        ch = e.get('channel', 0)
        if ch not in channels: channels[ch] = []
        channels[ch].append(e)
    
    track_names = {
        'minimal': {0: 'Bass', 1: 'Arp/Synth', 9: 'Drums'},
        'multitrack': {0: 'Sub Bass', 1: 'Bassline', 2: 'Pad', 3: 'Chords/Stabs', 
                       4: 'Arpeggio', 5: 'Lead/Melody', 6: 'FX/Percs', 9: 'Drums'}
    }
    
    if mode == 'multitrack' and submode == 'faithful':
        track_names['multitrack'] = {i: f'Track {i+1}' for i in range(20)}
        track_names['multitrack'][9] = 'Drums'
    
    for ch, ch_events in channels.items():
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track_name = track_names.get(mode, {}).get(ch, f'Channel {ch+1}')
        track.append(mido.MetaMessage('track_name', name=track_name, time=0))
        
        prev_tick = 0
        for e in ch_events:
            delta = e['tick'] - prev_tick
            msg_type = 'note_on' if e['type'] == 'on' else 'note_off'
            vel = e['vel'] if e['type'] == 'on' else 0
            track.append(mido.Message(msg_type, note=e['pitch'], velocity=vel, time=delta, channel=ch))
            prev_tick = e['tick']
            
    buf = io.BytesIO()
    mid.save(file=buf)
    buf.seek(0)
    return buf

def generate_report(midi_buffer, genre, mode, submode, bpm, bars, seed, root, scale, duration_mode, duration_seconds, original_filename):
    report = []
    report.append("=" * 60)
    report.append("🎛️ MIDI FORGE UNIVERSALE - REPORT DI GENERAZIONE")
    report.append("=" * 60)
    report.append("")
    
    report.append("📅 DATA E ORA")
    report.append(f"   Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    report.append("⚙️ PARAMETRI GENERAZIONE")
    report.append(f"   File originale: {original_filename}")
    report.append(f"   Modalità: {mode.upper()}")
    report.append(f"   Sotto-modalità: {submode.upper()}")
    report.append(f"   Genere: {genre.upper()}")
    report.append(f"   Seed: {seed}")
    report.append(f"   BPM: {bpm}")
    report.append(f"   Battute: {bars}")
    if duration_mode == "Minuti:Secondi" and duration_seconds:
        mins = duration_seconds // 60
        secs = duration_seconds % 60
        report.append(f"   Durata target: {mins}:{secs:02d}")
    duration_actual = (bars * 4 * 60) / bpm
    mins = int(duration_actual)
    secs = int((duration_actual - mins) * 60)
    report.append(f"   Durata effettiva: {mins}:{secs:02d}")
    report.append("")
    
    report.append("🎵 ANALISI TONALE")
    report.append(f"   Tonica rilevata: {NOTE_NAMES[root]}")
    scale_notes = [NOTE_NAMES[(root + i) % 12] for i in scale]
    report.append(f"   Scala: {' - '.join(scale_notes)}")
    report.append(f"   Intervalli: {scale}")
    report.append("")
    
    g = GENRES[genre]
    report.append("🥁 PATTERN RITMICI (1 sedicesimi)")
    report.append(f"   Kick:  {''.join(['█' if x else '·' for x in g['kick']])}")
    report.append(f"   Snare: {''.join(['█' if x else '·' for x in g.get('snare', [0]*16)])}")
    if 'clap' in g:
        report.append(f"   Clap:  {''.join(['█' if x else '·' for x in g['clap']])}")
    report.append(f"   Hat:   {''.join(['█' if x else '·' for x in g['hat']])}")
    report.append(f"   Bass:  {''.join(['█' if x else '·' for x in g['bass']])}")
    report.append(f"   Swing: {g['swing'] * 100:.0f}%")
    report.append(f"   Densità Arp: {g['arp_density'] * 100:.0f}%")
    report.append("")
    
    report.append("🎼 TRACCE OUTPUT")
    if mode == 'minimal':
        report.append("   1. Bass (Canale 1)")
        report.append("   2. Arp/Synth (Canale 2)")
        report.append("   3. Drums (Canale 10)")
    elif mode == 'multitrack' and submode == 'faithful':
        report.append("   Tracce originali preservate + Drums (Canale 10)")
    else:
        report.append("   1. Sub Bass (Canale 1)")
        report.append("   2. Bassline (Canale 2)")
        report.append("   3. Pad (Canale 3)")
        report.append("   4. Chords/Stabs (Canale 4)")
        report.append("   5. Arpeggio (Canale 5)")
        report.append("   6. Lead/Melody (Canale 6)")
        report.append("   7. FX/Percs (Canale 7)")
        report.append("   8. Drums (Canale 10)")
    report.append("")
    
    midi_buffer.seek(0)
    mid_out = mido.MidiFile(file=midi_buffer)
    total_notes = 0
    channels_used = set()
    for track in mid_out.tracks:
        for msg in track:
            if msg.type == 'note_on' and msg.velocity > 0:
                total_notes += 1
                channels_used.add(msg.channel)
    
    report.append("📊 STATISTICHE MIDI")
    report.append(f"   Note totali generate: {total_notes}")
    report.append(f"   Canali MIDI utilizzati: {len(channels_used)}")
    report.append(f"   Tracce MIDI: {len(mid_out.tracks)}")
    report.append(f"   Dimensione file: {midi_buffer.getbuffer().nbytes / 1024:.1f} KB")
    report.append("")
    
    report.append("💡 NOTE PER LOGIC PRO")
    report.append("   - Importa il MIDI trascinandolo nell'Arrange window")
    report.append("   - I nomi delle tracce sono già impostati")
    report.append("   - Assegna i tuoi VST preferiti a ogni traccia")
    report.append("   - Per la batteria: usa Drum Machine Designer (canale 10)")
    report.append("")
    
    report.append("=" * 60)
    report.append("Generato con MIDI Forge Universale | 100% Free & Open Source")
    report.append("=" * 60)
    
    return "\n".join(report)

def render_midi_player(midi_buffer, bpm):
    midi_buffer.seek(0)
    midi_bytes = midi_buffer.read()
    midi_b64 = base64.b64encode(midi_bytes).decode('ascii')
    
    html_player = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 15px; background: #0e1117; color: #fafafa; }}
            .player {{ background: #1a1d23; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
            .title {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; color: #fafafa; }}
            .controls {{ display: flex; gap: 10px; align-items: center; margin-bottom: 15px; }}
            button {{ background: #ff4b4b; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 14px; transition: all 0.2s; }}
            button:hover {{ background: #ff6b6b; transform: translateY(-1px); }}
            button:disabled {{ background: #555; cursor: not-allowed; transform: none; }}
            .status {{ font-size: 13px; color: #aaa; }}
            .info {{ font-size: 12px; color: #888; margin-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="player">
            <div class="title">🎧 Anteprima MIDI (suona nel browser)</div>
            <div class="controls">
                <button id="playBtn" onclick="togglePlay()">▶ Play</button>
                <button onclick="stop()">⏹ Stop</button>
                <span class="status" id="status">Pronto - {bpm} BPM</span>
            </div>
            <div class="info">💡 Usa synth Web Audio API nativi del browser</div>
        </div>
        
        <script>
            const midiBase64 = "{midi_b64}";
            let isPlaying = false;
            let synths = {{}};
            let scheduledEvents = [];
            
            function base64ToArrayBuffer(base64) {{
                const binaryString = window.atob(base64);
                const len = binaryString.length;
                const bytes = new Uint8Array(len);
                for (let i = 0; i < len; i++) {{
                    bytes[i] = binaryString.charCodeAt(i);
                }}
                return bytes.buffer;
            }}
            
            function parseMidi(arrayBuffer) {{
                const data = new DataView(arrayBuffer);
                let offset = 0;
                
                function readUint32() {{
                    const val = data.getUint32(offset, false);
                    offset += 4;
                    return val;
                }}
                
                function readUint16() {{
                    const val = data.getUint16(offset, false);
                    offset += 2;
                    return val;
                }}
                
                function readUint8() {{
                    return data.getUint8(offset++);
                }}
                
                function readString(len) {{
                    let str = '';
                    for (let i = 0; i < len; i++) {{
                        str += String.fromCharCode(readUint8());
                    }}
                    return str;
                }}
                
                const header = readString(4);
                if (header !== 'MThd') throw new Error('Not a MIDI file');
                
                const headerLength = readUint32();
                const format = readUint16();
                const numTracks = readUint16();
                const ticksPerBeat = readUint16();
                
                const tracks = [];
                for (let t = 0; t < numTracks; t++) {{
                    const trackHeader = readString(4);
                    if (trackHeader !== 'MTrk') throw new Error('Invalid track header');
                    
                    const trackLength = readUint32();
                    const trackEnd = offset + trackLength;
                    const events = [];
                    let currentTime = 0;
                    let lastStatus = 0;
                    
                    while (offset < trackEnd) {{
                        let deltaTime = 0;
                        let byte = readUint8();
                        while (byte & 0x80) {{
                            deltaTime = (deltaTime << 7) | (byte & 0x7F);
                            byte = readUint8();
                        }}
                        deltaTime = (deltaTime << 7) | (byte & 0x7F);
                        currentTime += deltaTime;
                        
                        let status = readUint8();
                        if (status < 0x80) {{
                            status = lastStatus;
                            offset--;
                        }}
                        lastStatus = status;
                        
                        const type = status & 0xF0;
                        const channel = status & 0x0F;
                        
                        if (type === 0x90 || type === 0x80) {{
                            const note = readUint8();
                            const velocity = readUint8();
                            events.push({{
                                time: currentTime,
                                type: type === 0x90 && velocity > 0 ? 'noteOn' : 'noteOff',
                                note: note,
                                velocity: velocity,
                                channel: channel
                            }});
                        }} else if (type === 0xC0 || type === 0xD0) {{
                            readUint8();
                        }} else if (type === 0xA0 || type === 0xE0) {{
                            readUint8();
                            readUint8();
                        }} else if (status === 0xFF) {{
                            const metaType = readUint8();
                            let length = 0;
                            byte = readUint8();
                            while (byte & 0x80) {{
                                length = (length << 7) | (byte & 0x7F);
                                byte = readUint8();
                            }}
                            length = (length << 7) | (byte & 0x7F);
                            offset += length;
                        }}
                    }}
                    
                    tracks.push(events);
                }}
                
                return {{ format, numTracks, ticksPerBeat, tracks }};
            }}
            
            async function togglePlay() {{
                if (isPlaying) {{
                    stop();
                    return;
                }}
                
                await Tone.start();
                document.getElementById('status').textContent = 'Caricamento...';
                
                try {{
                    const arrayBuffer = base64ToArrayBuffer(midiBase64);
                    const midi = parseMidi(arrayBuffer);
                    
                    const ticksPerSecond = (midi.ticksPerBeat * {bpm}) / 60;
                    
                    for (let ch = 0; ch < 16; ch++) {{
                        if (ch === 9) {{
                            synths[ch] = new Tone.MembraneSynth().toDestination();
                        }} else {{
                            synths[ch] = new Tone.PolySynth(Tone.Synth).toDestination();
                            synths[ch].set({{
                                oscillator: {{ type: 'triangle' }},
                                envelope: {{ attack: 0.02, decay: 0.3, sustain: 0.2, release: 0.5 }}
                            }});
                        }}
                    }}
                    
                    midi.tracks.forEach(track => {{
                        track.forEach(event => {{
                            const timeInSeconds = event.time / ticksPerSecond;
                            const noteName = Tone.Frequency(event.note, 'midi').toNote();
                            
                            if (event.type === 'noteOn') {{
                                if (event.channel === 9) {{
                                    scheduledEvents.push(
                                        Tone.getTransport().schedule(time => {{
                                            synths[9].triggerAttackRelease('C1', '8n', time, event.velocity / 127);
                                        }}, timeInSeconds)
                                    );
                                }} else {{
                                    scheduledEvents.push(
                                        Tone.getTransport().schedule(time => {{
                                            synths[event.channel].triggerAttackRelease(noteName, '8n', time, event.velocity / 127);
                                        }}, timeInSeconds)
                                    );
                                }}
                            }}
                        }});
                    }});
                    
                    Tone.getTransport().start();
                    isPlaying = true;
                    document.getElementById('playBtn').textContent = '⏸ Pause';
                    document.getElementById('status').textContent = 'In riproduzione...';
                    
                }} catch (e) {{
                    document.getElementById('status').textContent = 'Errore: ' + e.message;
                    console.error(e);
                }}
            }}
            
            function stop() {{
                Tone.getTransport().stop();
                scheduledEvents.forEach(id => Tone.getTransport().clear(id));
                scheduledEvents = [];
                Object.values(synths).forEach(synth => synth.releaseAll());
                isPlaying = false;
                document.getElementById('playBtn').textContent = '▶ Play';
                document.getElementById('status').textContent = 'Pronto - {bpm} BPM';
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_player, height=180)

# ================= INTERFACCIA STREAMLIT =================
st.title("🎛️ MIDI Forge Universale")
st.markdown("Trasforma qualsiasi file MIDI in 30+ generi musicali. Carica, ascolta in anteprima e scarica.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Carica il tuo file MIDI (.mid o .midi)", type=["mid", "midi"])
    
    mode = st.selectbox("Modalità Principale", ["minimal", "multitrack"], 
                        help="Minimal: 3 tracce compatte. Multitrack: Preserva la struttura a più tracce.")
    
    if mode == "minimal":
        submode = st.selectbox("Sotto-modalità", ["extract", "generate"], 
                               help="extract: Usa le note originali. generate: Crea melodie nuove da zero.")
    else:
        submode = st.selectbox("Sotto-modalità", ["faithful", "generative"], 
                               help="faithful: Cambio genere riconoscibile. generative: Arrangiamento nuovo ma strutturato.")

with col2:
    genre_list = sorted(GENRES.keys())
    genre = st.selectbox("Genere Musicale", genre_list, index=genre_list.index("techno"))
    
    g_defaults = GENRES[genre]
    
    col_bpm1, col_bpm2 = st.columns(2)
    with col_bpm1:
        use_default_bpm = st.checkbox("BPM Automatico", value=True)
        bpm = st.number_input("BPM", min_value=40, max_value=300, value=g_defaults['bpm_default'], disabled=use_default_bpm)
    
    with col_bpm2:
        duration_mode = st.radio("Durata traccia", ["Battute", "Minuti:Secondi"], horizontal=True)
        
        if duration_mode == "Battute":
            use_default_bars = st.checkbox("Battute Automatiche", value=True)
            bars = st.number_input("Battute", min_value=8, max_value=512, value=g_defaults['bars_default'], disabled=use_default_bars)
            duration_seconds = None
        else:
            col_min, col_sec = st.columns(2)
            with col_min:
                minutes = st.number_input("Minuti", min_value=0, max_value=30, value=1)
            with col_sec:
                seconds = st.number_input("Secondi", min_value=0, max_value=59, value=0)
            duration_seconds = minutes * 60 + seconds
            bars = None
        
    seed = st.number_input("Seed (per variazioni infinite)", min_value=1, max_value=99999, value=42)

st.markdown("---")

if st.button("🚀 Genera MIDI", type="primary", use_container_width=True):
    if not uploaded_file:
        st.error("⚠️ Per favore, carica prima un file MIDI!")
    else:
        with st.spinner("🎼 Analisi del DNA armonico e generazione in corso..."):
            try:
                file_bytes = io.BytesIO(uploaded_file.getvalue())
                notes_data = extract_notes(file_bytes)
                
                if not notes_data:
                    st.error("Il file MIDI caricato non contiene note valide.")
                else:
                    final_bpm = g_defaults['bpm_default'] if use_default_bpm else bpm
                    
                    if duration_mode == "Minuti:Secondi" and duration_seconds:
                        final_bars = int((duration_seconds * final_bpm) / 240)
                        final_bars = max(8, final_bars)
                        st.info(f"📏 Durata calcolata: {final_bars} battute ({duration_seconds} secondi a {final_bpm} BPM)")
                    else:
                        final_bars = g_defaults['bars_default'] if use_default_bars else bars
                    
                    if mode == "minimal":
                        events, root, scale = generate_minimal(notes_data, g_defaults, submode, final_bars, seed)
                    else:
                        file_bytes.seek(0)
                        events, root, scale = generate_multitrack(file_bytes, g_defaults, submode, final_bars, seed)
                    
                    midi_buffer = build_midi_file(events, final_bpm, mode, submode)
                    
                    st.success(f"✅ Generazione completata! (Tonica: {NOTE_NAMES[root]})")
                    
                    st.markdown("### 🎧 Anteprima")
                    render_midi_player(midi_buffer, final_bpm)
                    
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            label="📥 Scarica MIDI",
                            data=midi_buffer,
                            file_name=f"midi_forge_{genre}_{mode}_{submode}.mid",
                            mime="audio/midi",
                            use_container_width=True
                        )
                    with col_dl2:
                        report_text = generate_report(
                            midi_buffer, genre, mode, submode, final_bpm, final_bars, 
                            seed, root, scale, duration_mode, duration_seconds, uploaded_file.name
                        )
                        st.download_button(
                            label="📄 Scarica Report TXT",
                            data=report_text.encode('utf-8'),
                            file_name=f"report_{genre}_{mode}_{submode}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    with st.expander("📋 Visualizza Report Completo"):
                        st.code(report_text, language=None)
                        
            except Exception as e:
                st.error(f"Si è verificato un errore: {str(e)}")

st.markdown("---")
st.caption("MIDI Forge Universale | Librerie: Streamlit, Mido, Tone.js | 100% Open Source & Free")

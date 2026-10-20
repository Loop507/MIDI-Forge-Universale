import streamlit as st
import streamlit.components.v1 as components
import mido
import random
import math
import io
import json
from datetime import datetime
from collections import Counter

# ================= CONFIGURAZIONE PAGINA =================
st.set_page_config(page_title="MIDI Forge Universale", page_icon="🎛️", layout="wide")

# ================= DATABASE DEI GENERI =================
GENRES = {
    'acid': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'ambient': {'bpm_default': 80, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.15, 'swing': 0.0},
    'armonico': {'bpm_default': 100, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.70, 'swing': 0.10},
    'breakcore': {'bpm_default': 200, 'bars_default': 48, 'kick': [1,0,0,1, 0,1,0,0, 1,0,1,0, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,1,0,0, 1,0,0,1], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,0, 0,1,0,1], 'arp_density': 0.80, 'swing': 0.05},
    'commerciale_90s': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'arp_density': 0.60, 'swing': 0.0},
    'deep': {'bpm_default': 124, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.50, 'swing': 0.15},
    'disco': {'bpm_default': 122, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.05},
    'drone': {'bpm_default': 70, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.05, 'swing': 0.0},
    'drum_n_bass': {'bpm_default': 174, 'bars_default': 48, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,1, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.70, 'swing': 0.0},
    'dub_techno': {'bpm_default': 128, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'arp_density': 0.40, 'swing': 0.0},
    'edm_2000s': {'bpm_default': 132, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'elettronico': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'funk': {'bpm_default': 112, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,1,0,0], 'arp_density': 0.60, 'swing': 0.15},
    'glitch': {'bpm_default': 125, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,1, 0,0,0,0, 1,0,0,0], 'arp_density': 0.95, 'swing': 0.0},
    'harsh_noise': {'bpm_default': 100, 'bars_default': 64, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 1.0, 'swing': 0.0},
    'hip_hop': {'bpm_default': 92, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.30, 'swing': 0.35},
    'idm': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'snare': [0,0,1,0, 1,0,0,1, 0,0,1,0, 1,0,1,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.85, 'swing': 0.10},
    'industrial': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.70, 'swing': 0.0},
    'lowercase': {'bpm_default': 60, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.05, 'swing': 0.0},
    'microsound': {'bpm_default': 80, 'bars_default': 96, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.10, 'swing': 0.0},
    'minimal': {'bpm_default': 126, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.30, 'swing': 0.0},
    'minimal_techno': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.50, 'swing': 0.0},
    'minimalismo_ritmico': {'bpm_default': 115, 'bars_default': 64, 'kick': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.60, 'swing': 0.05},
    'noise': {'bpm_default': 120, 'bars_default': 64, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 0.90, 'swing': 0.0},
    'onkyo': {'bpm_default': 50, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.02, 'swing': 0.0},
    'r&b': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.55, 'swing': 0.25},
    'reggaeton': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.50, 'swing': 0.0},
    'sperimentale': {'bpm_default': 100, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,1,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,1,0,0, 1,0,0,1, 0,0,1,0, 1,0,0,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,1], 'arp_density': 0.70, 'swing': 0.10},
    'soul': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.60, 'swing': 0.30},
    'synthpop': {'bpm_default': 120, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.75, 'swing': 0.0},
    'techno': {'bpm_default': 138, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'trap': {'bpm_default': 140, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.40, 'swing': 0.0},
    'trance': {'bpm_default': 140, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1]*16, 'arp_density': 0.90, 'swing': 0.0},
    'underground': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.65, 'swing': 0.0}
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
TICKS_BEAT = 480

# ================= STANDARD GENERAL MIDI =================
DRUM_CH = 9  # Canale 10 (0-indexed = 9)

# Pitch GM standard per percussioni
GM_KICK = 36
GM_SNARE = 38
GM_CLAP = 39
GM_HAT_CLOSED = 42
GM_HAT_OPEN = 46

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
    
    tracks = {
        'bass': [],
        'arp': [],
        'drums': []
    }
    
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
            
            # BATTERIA - CANALE 9 (GM 10), PITCH GM
            if g['kick'][p_step]:
                tracks['drums'].extend([
                    {'tick': tick, 'type': 'on', 'pitch': GM_KICK, 'vel': 110, 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_KICK, 'vel': 0, 'channel': DRUM_CH}
                ])
            if g.get('snare', [0]*16)[p_step]:
                tracks['drums'].extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_SNARE, 'vel': 100, 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_SNARE, 'vel': 0, 'channel': DRUM_CH}
                ])
            if g.get('clap', [0]*16)[p_step]:
                tracks['drums'].extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_CLAP, 'vel': 90, 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_CLAP, 'vel': 0, 'channel': DRUM_CH}
                ])
            if g['hat'][p_step]:
                tracks['drums'].extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_HAT_CLOSED, 'vel': 70 + random.randint(0, 20), 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_HAT_CLOSED, 'vel': 0, 'channel': DRUM_CH}
                ])
            
            # BASSO & ARP
            if submode == 'extract' and s in notes_by_step:
                low_p, high_p = min(notes_by_step[s]), max(notes_by_step[s])
                if g['bass'][p_step]:
                    pitch = max(28, min(snap_to_scale(low_p, root, scale) - 24, 45))
                    tracks['bass'].extend([
                        {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 95, 'channel': 0},
                        {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 0}
                    ])
                if random.random() < g['arp_density']:
                    pitch = max(60, snap_to_scale(high_p, root, scale))
                    tracks['arp'].extend([
                        {'tick': tick + swing_offset, 'type': 'on', 'pitch': pitch, 'vel': 70, 'channel': 1},
                        {'tick': tick + (TICKS_BEAT//4) - 10, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 1}
                    ])
            else:
                if g['bass'][p_step]:
                    idx = 0 if random.random() < 0.8 else random.choice([1, len(scale)-1])
                    pitch = max(28, min(root - 24 + scale[idx % len(scale)], 45))
                    tracks['bass'].extend([
                        {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 95, 'channel': 0},
                        {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 0}
                    ])
                if m[s % 8] is not None:
                    pitch = root + 12 + scale[m[s % 8] % len(scale)]
                    tracks['arp'].extend([
                        {'tick': tick + swing_offset, 'type': 'on', 'pitch': pitch, 'vel': 70, 'channel': 1},
                        {'tick': tick + (TICKS_BEAT//4) - 20, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': 1}
                    ])
    return tracks, root, scale

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
    
    tracks = {}
    
    if submode == 'faithful':
        track_idx = 0
        for original_track in mid.tracks:
            if any(msg.channel == DRUM_CH for msg in original_track if hasattr(msg, 'channel')):
                continue
            
            original_name = None
            for msg in original_track:
                if msg.type == 'track_name':
                    original_name = msg.name
                    break
            
            track_events = []
            current_tick = 0
            for msg in original_track:
                current_tick += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    step = round(current_tick / (TICKS_BEAT // 4))
                    tick = step * (TICKS_BEAT // 4)
                    pitch = snap_to_scale(msg.note, root, scale)
                    track_events.extend([
                        {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': msg.velocity, 'channel': track_idx % 16},
                        {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': track_idx % 16}
                    ])
            
            if track_events:
                track_key = original_name if original_name else f'instrument_{track_idx}'
                tracks[track_key] = track_events
                track_idx += 1
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
            track_events = []
            for bar in range(bars):
                base_tick = bar * 4 * TICKS_BEAT
                
                if role_name == 'sub_bass':
                    if bar % 4 == 0:
                        pitch = root - 24 + scale[0]
                        track_events.extend([
                            {'tick': base_tick, 'type': 'on', 'pitch': max(24, pitch), 'vel': 100, 'channel': channel},
                            {'tick': base_tick + 4 * TICKS_BEAT, 'type': 'off', 'pitch': max(24, pitch), 'vel': 0, 'channel': channel}
                        ])
                elif role_name == 'bassline':
                    for s in range(16):
                        if g['bass'][s]:
                            tick = base_tick + s * (TICKS_BEAT // 4)
                            idx = 0 if random.random() < 0.8 else random.choice([1, len(scale)-1])
                            pitch = root - 12 + scale[idx % len(scale)]
                            track_events.extend([
                                {'tick': tick, 'type': 'on', 'pitch': max(30, min(pitch, 48)), 'vel': 95, 'channel': channel},
                                {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': max(30, min(pitch, 48)), 'vel': 0, 'channel': channel}
                            ])
                elif role_name in ['pad', 'chords']:
                    if random.random() < 0.5:
                        tick = base_tick
                        for i in range(3):
                            idx = random.randrange(len(scale))
                            pitch = random.randint(low_pitch, high_pitch)
                            pitch = snap_to_scale(pitch, root, scale)
                            dur = 4 * TICKS_BEAT if role_name == 'pad' else (TICKS_BEAT // 2)
                            track_events.extend([
                                {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 70, 'channel': channel},
                                {'tick': tick + dur, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}
                            ])
                elif role_name == 'arp':
                    for s in range(16):
                        if random.random() < g['arp_density']:
                            tick = base_tick + s * (TICKS_BEAT // 4)
                            idx = random.randrange(len(scale))
                            pitch = random.randint(low_pitch, high_pitch)
                            pitch = snap_to_scale(pitch, root, scale)
                            track_events.extend([
                                {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 75, 'channel': channel},
                                {'tick': tick + (TICKS_BEAT//4) - 10, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}
                            ])
                elif role_name == 'lead':
                    if random.random() < 0.3:
                        tick = base_tick + random.choice([0, TICKS_BEAT, 2*TICKS_BEAT, 3*TICKS_BEAT])
                        pitch = random.randint(low_pitch, high_pitch)
                        pitch = snap_to_scale(pitch, root, scale)
                        track_events.extend([
                            {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 85, 'channel': channel},
                            {'tick': tick + TICKS_BEAT, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}
                        ])
                elif role_name == 'fx_perc':
                    for s in range(16):
                        if random.random() < 0.1:
                            tick = base_tick + s * (TICKS_BEAT // 4)
                            pitch = random.randint(80, 95)
                            track_events.extend([
                                {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 50, 'channel': channel},
                                {'tick': tick + 20, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}
                            ])
            
            if track_events:
                tracks[role_name] = track_events
    
    # BATTERIA
    drum_events = []
    for bar in range(bars):
        base_tick = bar * 4 * TICKS_BEAT
        for s in range(16):
            tick = base_tick + s * (TICKS_BEAT // 4)
            p_step = s % 16
            swing_offset = int(g['swing'] * (TICKS_BEAT // 4)) if (p_step % 2 == 1) else 0
            
            if g['kick'][p_step]:
                drum_events.extend([
                    {'tick': tick, 'type': 'on', 'pitch': GM_KICK, 'vel': 110, 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_KICK, 'vel': 0, 'channel': DRUM_CH}
                ])
            if g.get('snare', [0]*16)[p_step]:
                drum_events.extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_SNARE, 'vel': 100, 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_SNARE, 'vel': 0, 'channel': DRUM_CH}
                ])
            if g.get('clap', [0]*16)[p_step]:
                drum_events.extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_CLAP, 'vel': 90, 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_CLAP, 'vel': 0, 'channel': DRUM_CH}
                ])
            if g['hat'][p_step]:
                drum_events.extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_HAT_CLOSED, 'vel': 75, 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_HAT_CLOSED, 'vel': 0, 'channel': DRUM_CH}
                ])
    
    if drum_events:
        tracks['drums'] = drum_events
    
    return tracks, root, scale

def build_midi_file(tracks, bpm, mode, submode):
    """Costruisce un file MIDI con Program Change GM per Logic Pro."""
    mid = mido.MidiFile(ticks_per_beat=TICKS_BEAT)
    
    t_tempo = mido.MidiTrack()
    t_tempo.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    mid.tracks.append(t_tempo)
    
    # Program Change GM per Logic Pro
    gm_programs = {
        'bass': 38, 'arp': 80, 'sub_bass': 39, 'bassline': 38,
        'pad': 89, 'chords': 0, 'lead': 81, 'fx_perc': 117, 'drums': 0
    }
    
    # Nomi tracce per Logic Pro
    logic_names = {
        'bass': 'Bass', 'arp': 'Synth', 'sub_bass': 'Sub Bass',
        'bassline': 'Bass', 'pad': 'Pad', 'chords': 'Piano',
        'lead': 'Lead', 'fx_perc': 'Percussion', 'drums': 'Drum Kit'
    }
    
    track_idx = 0
    for track_key, events in tracks.items():
        if not events:
            continue
        
        events_sorted = sorted(events, key=lambda e: (e['tick'], 0 if e['type'] == 'off' else 1))
        
        midi_track = mido.MidiTrack()
        mid.tracks.append(midi_track)
        
        if track_key.startswith('instrument_'):
            track_name = f'Instrument {track_idx + 1}'
        else:
            track_name = logic_names.get(track_key, f'Track {track_idx + 1}')
        
        midi_track.append(mido.MetaMessage('track_name', name=track_name, time=0))
        
        ch = events_sorted[0].get('channel', 0)
        
        if track_key != 'drums':
            pc = gm_programs.get(track_key, 0)
            midi_track.append(mido.Message('program_change', program=pc, channel=ch, time=0))
        
        prev_tick = 0
        for e in events_sorted:
            delta = e['tick'] - prev_tick
            msg_type = 'note_on' if e['type'] == 'on' else 'note_off'
            vel = e['vel'] if e['type'] == 'on' else 0
            midi_track.append(mido.Message(
                msg_type, note=e['pitch'], velocity=vel, time=delta, channel=ch
            ))
            prev_tick = e['tick']
        
        track_idx += 1
    
    buf = io.BytesIO()
    mid.save(file=buf)
    buf.seek(0)
    return buf

def generate_report(tracks, genre, mode, submode, bpm, bars, seed, root, scale, duration_mode, duration_seconds, original_filename):
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
    report.append(f"   Kick (GM 36):  {''.join(['█' if x else '·' for x in g['kick']])}")
    report.append(f"   Snare (GM 38): {''.join(['█' if x else '·' for x in g.get('snare', [0]*16)])}")
    if 'clap' in g:
        report.append(f"   Clap (GM 39):  {''.join(['█' if x else '·' for x in g['clap']])}")
    report.append(f"   Hat (GM 42):   {''.join(['█' if x else '·' for x in g['hat']])}")
    report.append(f"   Bass:          {''.join(['█' if x else '·' for x in g['bass']])}")
    report.append(f"   Swing: {g['swing'] * 100:.0f}%")
    report.append(f"   Densità Arp: {g['arp_density'] * 100:.0f}%")
    report.append("")
    
    report.append("🎼 TRACCE OUTPUT")
    track_idx = 1
    for track_key in tracks.keys():
        if track_key == 'drums':
            report.append(f"   {track_idx}. Drums (Canale 10 - GM Drum Map)")
        elif track_key.startswith('instrument_'):
            report.append(f"   {track_idx}. {track_key} (Canale melodico)")
        else:
            report.append(f"   {track_idx}. {track_key.replace('_', ' ').title()} (Canale melodico)")
        track_idx += 1
    report.append("")
    
    total_notes = sum(1 for events in tracks.values() for e in events if e['type'] == 'on')
    
    report.append("📊 STATISTICHE MIDI")
    report.append(f"   Note totali generate: {total_notes}")
    report.append(f"   Tracce MIDI: {len(tracks) + 1}")
    report.append("")
    
    report.append("💡 NOTE PER LOGIC PRO")
    report.append("   - Importa il MIDI trascinandolo nell'Arrange window")
    report.append("   - Logic caricherà automaticamente gli strumenti")
    report.append("   - La traccia Drums usa Drum Machine Designer")
    report.append("")
    
    report.append("=" * 60)
    report.append("Generato con MIDI Forge Universale | 100% Free & Open Source")
    report.append("=" * 60)
    
    return "\n".join(report)

def render_midi_player(tracks, bpm):
    all_events = []
    for events in tracks.values():
        all_events.extend(events)
    
    events_json = json.dumps([{
        'tick': e['tick'], 'type': e['type'], 'pitch': e['pitch'],
        'vel': e['vel'], 'channel': e.get('channel', 0)
    } for e in all_events])
    
    html_player = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 15px; background: #0e1117; color: #fafafa; }}
            .player {{ background: #1a1d23; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }}
            .title {{ font-size: 14px; font-weight: 600; margin-bottom: 12px; }}
            .controls {{ display: flex; gap: 10px; align-items: center; margin-bottom: 15px; }}
            button {{ background: #ff4b4b; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600; }}
            button:hover {{ background: #ff6b6b; }}
            .status {{ font-size: 13px; color: #aaa; }}
        </style>
    </head>
    <body>
        <div class="player">
            <div class="title">🎧 Anteprima MIDI</div>
            <div class="controls">
                <button id="playBtn" onclick="togglePlay()">▶ Play</button>
                <button onclick="stop()">⏹ Stop</button>
                <span class="status" id="status">Pronto - {bpm} BPM</span>
            </div>
        </div>
        
        <script>
            const events = {events_json};
            let isPlaying = false;
            let synths = {{}};
            let scheduledEvents = [];
            
            async function togglePlay() {{
                if (isPlaying) {{ stop(); return; }}
                
                await Tone.start();
                
                try {{
                    const ticksPerSecond = ({TICKS_BEAT} * {bpm}) / 60;
                    
                    for (let ch = 0; ch < 16; ch++) {{
                        if (ch === {DRUM_CH}) {{
                            synths[ch] = {{
                                kick: new Tone.MembraneSynth().toDestination(),
                                snare: new Tone.NoiseSynth({{ noise: {{ type: 'white' }}, envelope: {{ attack: 0.001, decay: 0.2, sustain: 0 }} }}).toDestination(),
                                hat: new Tone.MetalSynth({{ envelope: {{ attack: 0.001, decay: 0.05, release: 0.01 }}, harmonicity: 5.1, modulationIndex: 32, resonance: 4000, octaves: 1.5 }}).toDestination(),
                                clap: new Tone.NoiseSynth({{ noise: {{ type: 'pink' }}, envelope: {{ attack: 0.001, decay: 0.15, sustain: 0 }} }}).toDestination()
                            }};
                        }} else {{
                            synths[ch] = new Tone.PolySynth(Tone.Synth).toDestination();
                            synths[ch].set({{ oscillator: {{ type: 'triangle' }}, envelope: {{ attack: 0.02, decay: 0.3, sustain: 0.2, release: 0.5 }} }});
                        }}
                    }}
                    
                    events.forEach(event => {{
                        const timeInSeconds = event.tick / ticksPerSecond;
                        
                        if (event.type === 'on') {{
                            if (event.channel === {DRUM_CH}) {{
                                scheduledEvents.push(
                                    Tone.getTransport().schedule(time => {{
                                        if (event.pitch === {GM_KICK}) synths[{DRUM_CH}].kick.triggerAttackRelease('C1', '8n', time, event.vel / 127);
                                        else if (event.pitch === {GM_SNARE}) synths[{DRUM_CH}].snare.triggerAttackRelease('16n', time, event.vel / 127);
                                        else if (event.pitch === {GM_CLAP}) synths[{DRUM_CH}].clap.triggerAttackRelease('16n', time, event.vel / 127);
                                        else if (event.pitch === {GM_HAT_CLOSED} || event.pitch === {GM_HAT_OPEN}) synths[{DRUM_CH}].hat.triggerAttackRelease('C3', '32n', time, event.vel / 127);
                                    }}, timeInSeconds)
                                );
                            }} else {{
                                const noteName = Tone.Frequency(event.pitch, 'midi').toNote();
                                scheduledEvents.push(
                                    Tone.getTransport().schedule(time => {{
                                        synths[event.channel].triggerAttackRelease(noteName, '8n', time, event.vel / 127);
                                    }}, timeInSeconds)
                                );
                            }}
                        }}
                    }});
                    
                    Tone.getTransport().start();
                    isPlaying = true;
                    document.getElementById('playBtn').textContent = '⏸ Pause';
                    document.getElementById('status').textContent = 'In riproduzione...';
                    
                }} catch (e) {{
                    document.getElementById('status').textContent = 'Errore: ' + e.message;
                }}
            }}
            
            function stop() {{
                Tone.getTransport().stop();
                scheduledEvents.forEach(id => Tone.getTransport().clear(id));
                scheduledEvents = [];
                isPlaying = false;
                document.getElementById('playBtn').textContent = '▶ Play';
                document.getElementById('status').textContent = 'Pronto - {bpm} BPM';
            }}
        </script>
    </body>
    </html>
    """
    components.html(html_player, height=150)

# ================= INTERFACCIA STREAMLIT =================
st.title("🎛️ MIDI Forge Universale")
st.markdown("Trasforma qualsiasi file MIDI in 30+ generi musicali. Standard General MIDI / DAW-compliant.")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Carica il tuo file MIDI (.mid o .midi)", type=["mid", "midi"])
    
    mode = st.selectbox("Modalità Principale", ["minimal", "multitrack"])
    
    if mode == "minimal":
        submode = st.selectbox("Sotto-modalità", ["extract", "generate"])
    else:
        submode = st.selectbox("Sotto-modalità", ["faithful", "generative"])

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
        
    seed = st.number_input("Seed", min_value=1, max_value=99999, value=42)

st.markdown("---")

if st.button("🚀 Genera MIDI", type="primary", use_container_width=True):
    if not uploaded_file:
        st.error("⚠️ Carica prima un file MIDI!")
    else:
        with st.spinner("🎼 Generazione in corso..."):
            try:
                file_bytes = io.BytesIO(uploaded_file.getvalue())
                notes_data = extract_notes(file_bytes)
                
                if not notes_data:
                    st.error("Il file MIDI non contiene note valide.")
                else:
                    final_bpm = g_defaults['bpm_default'] if use_default_bpm else bpm
                    
                    if duration_mode == "Minuti:Secondi" and duration_seconds:
                        final_bars = int((duration_seconds * final_bpm) / 240)
                        final_bars = max(8, final_bars)
                        st.info(f"📏 Durata calcolata: {final_bars} battute")
                    else:
                        final_bars = g_defaults['bars_default'] if use_default_bars else bars
                    
                    if mode == "minimal":
                        tracks, root, scale = generate_minimal(notes_data, g_defaults, submode, final_bars, seed)
                    else:
                        file_bytes.seek(0)
                        tracks, root, scale = generate_multitrack(file_bytes, g_defaults, submode, final_bars, seed)
                    
                    midi_buffer = build_midi_file(tracks, final_bpm, mode, submode)
                    
                    st.success(f"✅ Completato! (Tonica: {NOTE_NAMES[root]}, BPM: {final_bpm})")
                    
                    st.markdown("### 🎧 Anteprima")
                    render_midi_player(tracks, final_bpm)
                    
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
                            tracks, genre, mode, submode, final_bpm, final_bars, 
                            seed, root, scale, duration_mode, duration_seconds, uploaded_file.name
                        )
                        st.download_button(
                            label="📄 Scarica Report TXT",
                            data=report_text.encode('utf-8'),
                            file_name=f"report_{genre}_{mode}_{submode}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    
                    with st.expander("📋 Visualizza Report"):
                        st.code(report_text, language=None)
                        
            except Exception as e:
                st.error(f"Errore: {str(e)}")

st.markdown("---")
st.caption("MIDI Forge Universale | Standard General MIDI | 100% Open Source & Free")

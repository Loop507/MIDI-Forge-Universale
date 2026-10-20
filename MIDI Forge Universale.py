import streamlit as st
import streamlit.components.v1 as components
import mido
import random
import io
import json
from datetime import datetime
from collections import Counter

# ================= CONFIGURAZIONE PAGINA =================
st.set_page_config(page_title="MIDI Forge Universale", page_icon="🎛️", layout="wide")

# ================= DATABASE DEI GENERI =================
GENRES = {
    'acid': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'ambient': {'bpm_default': 80, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.15, 'swing': 0.0},
    'armonico': {'bpm_default': 100, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.70, 'swing': 0.10},
    'breakcore': {'bpm_default': 200, 'bars_default': 48, 'kick': [1,0,0,1, 0,1,0,0, 1,0,1,0, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,1,0,0, 1,0,0,1], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,0, 0,1,0,1], 'arp_density': 0.80, 'swing': 0.05},
    'commerciale_90s': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'arp_density': 0.60, 'swing': 0.0},
    'deep': {'bpm_default': 124, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.50, 'swing': 0.15},
    'disco': {'bpm_default': 122, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.05},
    'drone': {'bpm_default': 70, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.05, 'swing': 0.0},
    'drum_n_bass': {'bpm_default': 174, 'bars_default': 48, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,1, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.70, 'swing': 0.0},
    'dub_techno': {'bpm_default': 128, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'arp_density': 0.40, 'swing': 0.0},
    'edm_2000s': {'bpm_default': 132, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'elettronico': {'bpm_default': 130, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'funk': {'bpm_default': 112, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,1,0,0], 'arp_density': 0.60, 'swing': 0.15},
    'glitch': {'bpm_default': 125, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,1, 0,0,0,0, 1,0,0,0], 'arp_density': 0.95, 'swing': 0.0},
    'harsh_noise': {'bpm_default': 100, 'bars_default': 64, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 1.0, 'swing': 0.0},
    'hip_hop': {'bpm_default': 92, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.30, 'swing': 0.35},
    'idm': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'snare': [0,0,1,0, 1,0,0,1, 0,0,1,0, 1,0,1,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.85, 'swing': 0.10},
    'industrial': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.70, 'swing': 0.0},
    'lowercase': {'bpm_default': 60, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.05, 'swing': 0.0},
    'microsound': {'bpm_default': 80, 'bars_default': 96, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.10, 'swing': 0.0},
    'minimal': {'bpm_default': 126, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.30, 'swing': 0.0},
    'minimal_techno': {'bpm_default': 135, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.50, 'swing': 0.0},
    'minimalismo_ritmico': {'bpm_default': 115, 'bars_default': 64, 'kick': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.60, 'swing': 0.05},
    'noise': {'bpm_default': 120, 'bars_default': 64, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 0.90, 'swing': 0.0},
    'onkyo': {'bpm_default': 50, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.02, 'swing': 0.0},
    'r&b': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.55, 'swing': 0.25},
    'reggaeton': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,1,0,1, 0,1,0,1, 0,1,0,1, 0,1,0,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.50, 'swing': 0.0},
    'sperimentale': {'bpm_default': 100, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,1,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,1,0,0, 1,0,0,1, 0,0,1,0, 1,0,0,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,1], 'arp_density': 0.70, 'swing': 0.10},
    'soul': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,1,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'arp_density': 0.60, 'swing': 0.30},
    'synthpop': {'bpm_default': 120, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.75, 'swing': 0.0},
    'techno': {'bpm_default': 138, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,1], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
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
    scale_t = TICKS_BEAT / mid.ticks_per_beat  # normalizza il PPQ (Logic esporta a 960)
    for track in mid.tracks:
        current_tick = 0
        for msg in track:
            current_tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                notes.append({'pitch': msg.note, 'tick': int(round(current_tick * scale_t)), 'vel': msg.velocity})
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

def generate_multitrack(mid_file_bytes, g, submode, bars, seed, split_drums=True):
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
    
    headers = {}
    scale_t = TICKS_BEAT / mid.ticks_per_beat  # normalizza il PPQ della sorgente
    free_channels = [c for c in range(16) if c != DRUM_CH]  # il canale 10 resta riservato alla batteria

    if submode == 'faithful':
        track_idx = 0
        for original_track in mid.tracks:
            if any(msg.channel == DRUM_CH for msg in original_track if hasattr(msg, 'channel')):
                continue

            original_name = next((m.name for m in original_track if m.type == 'track_name'), None)
            header = _extract_instrument_header(original_track)

            ch = free_channels[track_idx % len(free_channels)]
            track_events = []
            current_tick = 0
            for msg in original_track:
                current_tick += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    step = round(current_tick * scale_t / (TICKS_BEAT // 4))
                    tick = step * (TICKS_BEAT // 4)
                    pitch = snap_to_scale(msg.note, root, scale)
                    track_events.extend([
                        {'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': msg.velocity, 'channel': ch},
                        {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': ch}
                    ])

            if track_events:
                track_key = (original_name or '').strip() or f'instrument_{track_idx}'
                base_key, n = track_key, 2
                while track_key in tracks or track_key in DRUM_TRACK_NAMES:
                    track_key = f'{base_key} {n}'
                    n += 1
                tracks[track_key] = track_events
                if header:
                    headers[track_key] = header
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
    
    # In faithful le tracce melodiche seguono il brano sorgente (non vengono mai tagliate): la batteria
    # deve coprire le stesse battute, altrimenti finisce prima del resto.
    if tracks:
        last_tick = max(e['tick'] for ev in tracks.values() for e in ev)
        bars = max(bars, -(-last_tick // (4 * TICKS_BEAT)))

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
        if split_drums:
            tracks = split_drum_track(tracks)
    
    return tracks, root, scale, headers, bars


GM_PROGRAM_NAMES = [
    'Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano', 'Honky-tonk Piano',
    'Electric Piano 1', 'Electric Piano 2', 'Harpsichord', 'Clavinet',
    'Celesta', 'Glockenspiel', 'Music Box', 'Vibraphone',
    'Marimba', 'Xylophone', 'Tubular Bells', 'Dulcimer',
    'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ',
    'Reed Organ', 'Accordion', 'Harmonica', 'Tango Accordion',
    'Acoustic Guitar (nylon)', 'Acoustic Guitar (steel)', 'Electric Guitar (jazz)', 'Electric Guitar (clean)',
    'Electric Guitar (muted)', 'Overdriven Guitar', 'Distortion Guitar', 'Guitar Harmonics',
    'Acoustic Bass', 'Electric Bass (finger)', 'Electric Bass (pick)', 'Fretless Bass',
    'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1', 'Synth Bass 2',
    'Violin', 'Viola', 'Cello', 'Contrabass',
    'Tremolo Strings', 'Pizzicato Strings', 'Orchestral Harp', 'Timpani',
    'String Ensemble 1', 'String Ensemble 2', 'Synth Strings 1', 'Synth Strings 2',
    'Choir Aahs', 'Voice Oohs', 'Synth Voice', 'Orchestra Hit',
    'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet',
    'French Horn', 'Brass Section', 'Synth Brass 1', 'Synth Brass 2',
    'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax',
    'Oboe', 'English Horn', 'Bassoon', 'Clarinet',
    'Piccolo', 'Flute', 'Recorder', 'Pan Flute',
    'Blown Bottle', 'Shakuhachi', 'Whistle', 'Ocarina',
    'Lead 1 (square)', 'Lead 2 (sawtooth)', 'Lead 3 (calliope)', 'Lead 4 (chiff)',
    'Lead 5 (charang)', 'Lead 6 (voice)', 'Lead 7 (fifths)', 'Lead 8 (bass + lead)',
    'Pad 1 (new age)', 'Pad 2 (warm)', 'Pad 3 (polysynth)', 'Pad 4 (choir)',
    'Pad 5 (bowed)', 'Pad 6 (metallic)', 'Pad 7 (halo)', 'Pad 8 (sweep)',
    'FX 1 (rain)', 'FX 2 (soundtrack)', 'FX 3 (crystal)', 'FX 4 (atmosphere)',
    'FX 5 (brightness)', 'FX 6 (goblins)', 'FX 7 (echoes)', 'FX 8 (sci-fi)',
    'Sitar', 'Banjo', 'Shamisen', 'Koto',
    'Kalimba', 'Bag pipe', 'Fiddle', 'Shanai',
    'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock',
    'Taiko Drum', 'Melodic Tom', 'Synth Drum', 'Reverse Cymbal',
    'Guitar Fret Noise', 'Breath Noise', 'Seashore', 'Bird Tweet',
    'Telephone Ring', 'Helicopter', 'Applause', 'Gunshot',
]

# Nomi-chiave -> programma GM, per dare uno strumento alle tracce senza program change
_GM_NAME_HINTS = [
    (("bass", "basso", "contrabb"), 33), (("chitarr", "guitar"), 25), (("piano", "pianof"), 0), (("organ", "organo"), 19),
    (("string", "archi", "violin", "cello"), 48), (("pad",), 89), (("lead",), 80), (("vox", "voce", "vocal", "choir", "coro"), 52),
    (("flaut", "flute"), 73), (("sax",), 65), (("trump", "tromba"), 56), (("tromb",), 57), (("synth",), 81),
]

# CC che definiscono strumento e mix: bank select (0/32), volume, pan, expression, riverbero, chorus
_MIX_CCS = (7, 10, 11, 91, 93)


def _guess_program(name):
    low = (name or "").lower()
    for keys, prog in _GM_NAME_HINTS:
        if any(k in low for k in keys):
            return prog
    return 0


def _extract_instrument_header(track):
    """Messaggi di strumento e mix letti prima della prima nota (program change, bank select,
    volume/pan/expression/riverbero/chorus). Senza di essi Logic assegna lo strumento di default."""
    header = []
    for msg in track:
        if msg.type in ('note_on', 'note_off'):
            break
        if msg.type == 'program_change':
            header.append({'type': 'program_change', 'program': msg.program})
        elif msg.type == 'control_change' and (msg.control in (0, 32) or msg.control in _MIX_CCS):
            header.append({'type': 'control_change', 'control': msg.control, 'value': msg.value})
    return header


# Pezzi del kit -> traccia dedicata (tutte sul canale 10, come le tracce "Ritmica" di MidiDecomposer)
DRUM_PIECES = [(GM_KICK, 'drum_kick'), (GM_SNARE, 'drum_snare'), (GM_HAT_CLOSED, 'drum_hat'), (GM_CLAP, 'drum_clap')]
DRUM_TRACK_NAMES = {'drums': 'Drums', 'drum_kick': 'Kick', 'drum_snare': 'Snare', 'drum_hat': 'Hat', 'drum_clap': 'Clap'}


def split_drum_track(tracks):
    """tracks['drums'] -> una traccia per pezzo del kit (Kick/Snare/Hat/Clap). Nessuna nota va persa:
    eventuali altezze fuori dalla mappa restano in 'drums'."""
    events = tracks.get('drums')
    if not events:
        return tracks
    out = {k: v for k, v in tracks.items() if k != 'drums'}
    known = {p for p, _k in DRUM_PIECES}
    for pitch, key in DRUM_PIECES:
        ev = [e for e in events if e['pitch'] == pitch]
        if ev:
            out[key] = ev
    rest = [e for e in events if e['pitch'] not in known]
    if rest:
        out['drums'] = rest
    return out


GM_ROLE_PROGRAMS = {
    'bass': 38, 'arp': 80, 'sub_bass': 39, 'bassline': 38,
    'pad': 89, 'chords': 0, 'lead': 81, 'fx_perc': 117
}

LOGIC_ROLE_NAMES = {
    'bass': 'Bass', 'arp': 'Synth', 'sub_bass': 'Sub Bass',
    'bassline': 'Bass', 'pad': 'Pad', 'chords': 'Piano',
    'lead': 'Lead', 'fx_perc': 'Percussion', 'drums': 'Drums'
}


def _events_to_notes(events):
    """Coppie on/off -> note (start, end, pitch, vel) pulite per Logic.
    - pitch/velocity forzati nel range MIDI valido
    - note identiche sulla stessa posizione fuse, sovrapposte sullo stesso pitch troncate
      (altrimenti il primo note_off taglia la seconda nota o la lascia appesa)"""
    notes = []
    i, n = 0, len(events)
    while i < n:
        e = events[i]
        if e['type'] == 'on' and i + 1 < n and events[i + 1]['type'] == 'off' and events[i + 1]['pitch'] == e['pitch']:
            start = int(e['tick'])
            end = max(int(events[i + 1]['tick']), start + 1)
            pitch = max(0, min(127, int(e['pitch'])))
            vel = max(1, min(127, int(e['vel'])))
            notes.append([start, end, pitch, vel])
            i += 2
        else:
            i += 1

    by_pitch = {}
    for nt in notes:
        by_pitch.setdefault(nt[2], []).append(nt)

    cleaned_all = []
    for lst in by_pitch.values():
        lst.sort(key=lambda x: (x[0], -x[3]))
        cleaned = []
        for nt in lst:
            if cleaned and nt[0] == cleaned[-1][0]:
                cleaned[-1][1] = max(cleaned[-1][1], nt[1])
                continue
            if cleaned and cleaned[-1][1] > nt[0]:
                cleaned[-1][1] = nt[0]
            cleaned.append(nt)
        cleaned_all.extend(cleaned)

    cleaned_all.sort(key=lambda x: (x[0], x[2]))
    return cleaned_all


def build_midi_file(tracks, bpm, mode, submode, headers=None, label=None):
    """MIDI Format 1 per Logic Pro (File > Apri), con le stesse convenzioni di MidiDecomposer (daw_optimize):
      - prima traccia con SOLO tempo e metrica espliciti al tick 0 + marker 'Loop507 - ...'
      - una traccia = un canale, con nome e (bank select, program change, mix) al tick 0
      - batteria sul canale 10 (Kick/Snare/Hat/Clap su tracce separate, oppure 'Drums') con program change 0
      - tutte le tracce chiudono con end_of_track sull'ultima nota del brano: le regioni finiscono insieme."""
    headers = headers or {}
    faithful = (mode == 'multitrack' and submode == 'faithful')

    notes_by_track = {}
    for key, events in tracks.items():
        notes = _events_to_notes(events)
        if notes:
            notes_by_track[key] = (events[0].get('channel', 0), notes)

    mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_BEAT)
    total_end = max((nt[1] for _, notes in notes_by_track.values() for nt in notes), default=0)

    t_tempo = mido.MidiTrack()
    t_tempo.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    t_tempo.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    if label:
        text = ("Loop507 - " + label).encode('ascii', 'ignore').decode('ascii')[:120]
        t_tempo.append(mido.MetaMessage('marker', text=text, time=0))
    t_tempo.append(mido.MetaMessage('end_of_track', time=total_end))
    mid.tracks.append(t_tempo)

    used_names = Counter()
    for key, (ch, notes) in notes_by_track.items():
        is_drums = (ch == DRUM_CH)

        header = list(headers.get(key, []))
        if not any(h['type'] == 'program_change' for h in header):
            if is_drums:
                pc = 0  # Standard Kit GM, come _rb_render_track di MidiDecomposer
            else:
                pc = None if faithful else GM_ROLE_PROGRAMS.get(key)
                if pc is None:
                    pc = _guess_program(key)
            header.append({'type': 'program_change', 'program': pc})
        bank = [h for h in header if h['type'] == 'control_change' and h['control'] in (0, 32)]
        pcs = [h for h in header if h['type'] == 'program_change'][:1]
        mix = {}
        for h in header:
            if h['type'] == 'control_change' and h['control'] not in (0, 32):
                mix[h['control']] = h
        program = pcs[0]['program'] & 0x7F if pcs else None

        if is_drums:
            name = DRUM_TRACK_NAMES.get(key, 'Drums')
        elif key.startswith('instrument_'):
            name = GM_PROGRAM_NAMES[program] if program is not None else key
        elif faithful:
            name = key
        else:
            name = LOGIC_ROLE_NAMES.get(key, key.replace('_', ' ').title())
        used_names[name] += 1
        if used_names[name] > 1:
            name = f'{name} {used_names[name]}'

        midi_track = mido.MidiTrack()
        midi_track.append(mido.MetaMessage('track_name', name=name, time=0))
        for h in bank:
            midi_track.append(mido.Message('control_change', control=h['control'], value=h['value'], channel=ch, time=0))
        if program is not None:
            midi_track.append(mido.Message('program_change', program=program, channel=ch, time=0))
        for h in mix.values():
            midi_track.append(mido.Message('control_change', control=h['control'], value=h['value'], channel=ch, time=0))

        ev = []
        for start, end, pitch, vel in notes:
            ev.append((end, 0, pitch, 0))
            ev.append((start, 1, pitch, vel))
        ev.sort(key=lambda x: (x[0], x[1]))  # a pari tick: prima i note_off

        prev = 0
        for tick, is_on, pitch, vel in ev:
            midi_track.append(mido.Message('note_on' if is_on else 'note_off',
                                           note=pitch, velocity=vel, time=tick - prev, channel=ch))
            prev = tick
        midi_track.append(mido.MetaMessage('end_of_track', time=max(0, total_end - prev)))
        mid.tracks.append(midi_track)

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
        if track_key in DRUM_TRACK_NAMES:
            report.append(f"   {track_idx}. {DRUM_TRACK_NAMES[track_key]} (Canale 10 - GM Drum Map)")
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
    
    report.append("💡 NOTE PER LOGIC PRO :: LOGIC PRO NOTES")
    report.append("   - Apri con File > Apri (non Importa) :: Use File > Open (not Import)")
    report.append("   - Importa ignora tempo, metrica, nomi traccia e marker; Apri li legge :: Import ignores tempo, time signature, track names and markers; Open reads them")
    report.append("   - Ogni traccia ha nome e program change al tick 0: lo strumento giusto sulla traccia giusta :: Every track has a name and a tick-0 program change: right instrument on the right track")
    report.append("   - Batteria su canale 10 (Kick/Snare/Hat/Clap o 'Drums'): se non carica un kit, assegna Drum Kit Designer :: Drums on ch.10 (Kick/Snare/Hat/Clap or 'Drums'): if no kit loads, assign Drum Kit Designer")
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
        split_drums = st.checkbox("🥁 Batteria su tracce separate (Kick / Snare / Hat / Clap)", value=True)

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
                        headers = {}
                    else:
                        file_bytes.seek(0)
                        requested_bars = final_bars
                        tracks, root, scale, headers, final_bars = generate_multitrack(file_bytes, g_defaults, submode, final_bars, seed, split_drums)
                        if final_bars != requested_bars:
                            st.info(f"📏 Durata allineata al brano sorgente: {final_bars} battute (richieste: {requested_bars})")
                    
                    midi_buffer = build_midi_file(tracks, final_bpm, mode, submode, headers, label=f"MIDI Forge - {genre} - {mode}/{submode}")
                    
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

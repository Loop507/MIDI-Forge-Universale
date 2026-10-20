import streamlit as st
import mido
import random
import math
import io
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
        total_steps = math.ceil(max_tick / (TICKS_BEAT // 4))
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
            
            # Drums
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
            
            # Bass & Arp
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

def generate_multitrack(notes_data, g, submode, bars, seed):
    random.seed(seed)
    root, scale = extract_dna(notes_data)
    events = []
    
    low_notes = [n for n in notes_data if n['pitch'] < 50]
    mid_notes = [n for n in notes_data if 50 <= n['pitch'] < 75]
    high_notes = [n for n in notes_data if n['pitch'] >= 75]
    
    def create_track(notes_list, channel, is_bass=False):
        if submode == 'faithful':
            for n in notes_list:
                step = round(n['tick'] / (TICKS_BEAT // 4))
                tick = step * (TICKS_BEAT // 4)
                pitch = snap_to_scale(n['pitch'], root, scale)
                if is_bass: pitch = max(28, min(pitch - 12, 45))
                elif pitch < 60: pitch += 24
                events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': n['vel'], 'channel': channel},
                               {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}])
        else:
            for bar in range(bars):
                base_tick = bar * 4 * TICKS_BEAT
                for s in range(16):
                    if random.random() < 0.3:
                        tick = base_tick + s * (TICKS_BEAT // 4)
                        idx = random.randrange(len(scale))
                        pitch = (root - 24 + scale[idx % len(scale)]) if is_bass else (root + 12 + scale[idx % len(scale)])
                        pitch = max(28, min(pitch, 45)) if is_bass else pitch
                        events.extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 75, 'channel': channel},
                                       {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}])

    create_track(low_notes, 0, is_bass=True)
    create_track(mid_notes, 1, is_bass=False)
    create_track(high_notes, 2, is_bass=False)
    
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

def build_midi_file(events, bpm):
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
        
    for ch, ch_events in channels.items():
        track = mido.MidiTrack()
        mid.tracks.append(track)
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

# ================= INTERFACCIA STREAMLIT =================
st.title("🎛️ MIDI Forge Universale")
st.markdown("Trasforma qualsiasi file MIDI in 25+ generi musicali. Carica il tuo file, scegli le impostazioni e scarica il risultato.")

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
        use_default_bars = st.checkbox("Battute Automatiche", value=True)
        bars = st.number_input("Battute", min_value=8, max_value=256, value=g_defaults['bars_default'], disabled=use_default_bars)
        
    seed = st.number_input("Seed (per variazioni infinite)", min_value=1, max_value=99999, value=42)

st.markdown("---")

if st.button("🚀 Genera MIDI", type="primary", use_container_width=True):
    if not uploaded_file:
        st.error("⚠️ Per favore, carica prima un file MIDI!")
    else:
        with st.spinner("🎼 Analisi del DNA armonico e generazione in corso..."):
            try:
                # Leggi il file caricato
                file_bytes = io.BytesIO(uploaded_file.getvalue())
                notes_data = extract_notes(file_bytes)
                
                if not notes_data:
                    st.error("Il file MIDI caricato non contiene note valide.")
                else:
                    final_bpm = g_defaults['bpm_default'] if use_default_bpm else bpm
                    final_bars = g_defaults['bars_default'] if use_default_bars else bars
                    
                    if mode == "minimal":
                        events, root, scale = generate_minimal(notes_data, g_defaults, submode, final_bars, seed)
                    else:
                        events, root, scale = generate_multitrack(notes_data, g_defaults, submode, final_bars, seed)
                    
                    # Costruisci il file MIDI in memoria
                    midi_buffer = build_midi_file(events, final_bpm)
                    
                    st.success(f"✅ Generazione completata! (Tonica rilevata: {['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][root]})")
                    
                    st.download_button(
                        label="📥 Scarica il tuo MIDI Generato",
                        data=midi_buffer,
                        file_name=f"midi_forge_{genre}_{mode}_{submode}.mid",
                        mime="audio/midi",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Si è verificato un errore: {str(e)}")

st.markdown("---")
st.caption("MIDI Forge Universale | Librerie: Streamlit, Mido | 100% Open Source & Free")

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
DRUM_CH = 9
GM_KICK = 36
GM_SNARE = 38
GM_CLAP = 39
GM_HAT_CLOSED = 42
GM_HAT_OPEN = 46
GM_TOM_HIGH = 50
GM_RIMSHOT = 37

# ================= FUNZIONI AUXILIARIE =================

def _root_to_key_name(root, is_minor):
    return NOTE_NAMES[root] + ('m' if is_minor else '')

def _is_minor_scale(scale):
    return 3 in scale

def _compute_key_signature(root, scale):
    return _root_to_key_name(root, _is_minor_scale(scale))

def _compute_note_durations(events):
    pending = {}
    notes = []
    for e in sorted(events, key=lambda x: x['tick']):
        key = (e['pitch'], e.get('channel', 0))
        if e['type'] == 'on':
            pending[key] = e
        elif e['type'] == 'off' and key in pending:
            start = pending[key]['tick']
            dur = e['tick'] - start
            vel = pending[key]['vel']
            notes.append({'tick': start, 'dur': max(1, dur), 'pitch': e['pitch'], 'vel': vel, 'channel': e.get('channel', 0)})
            del pending[key]
    return notes

def extract_notes(mid_file):
    notes = []
    mid = mido.MidiFile(file=mid_file)
    scale_t = TICKS_BEAT / mid.ticks_per_beat
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

# ================= GENERAZIONE MINIMAL (TECHNO PRO) =================

def generate_minimal(notes_data, g, submode, bars, seed):
    """Modalità Minimal: 3 tracce (Bass, Arp, Drums) con variazioni Techno reali."""
    random.seed(seed)
    root, scale = extract_dna(notes_data)
    tracks = {'bass': [], 'arp': [], 'drums': []}
    
    if submode == 'extract':
        notes_by_step = {}
        for n in notes_data:
            step = round(n['tick'] / (TICKS_BEAT // 4))
            if step not in notes_by_step: notes_by_step[step] = []
            notes_by_step[step].append(n['pitch'])
    
    m = [random.randrange(len(scale)) if random.random() < g['arp_density'] else None for _ in range(8)]
    
    intro_bars = min(4, max(4, bars // 8))
    outro_bars = min(4, max(4, bars // 8))

    for bar in range(bars):
        base_tick = bar * 4 * TICKS_BEAT
        
        if bar % 4 == 0 and bar > 0:
            op = random.choice(['transpose', 'invert', 'drop'])
            if op == 'transpose': m = [(x + 1) % len(scale) if x is not None else None for x in m]
            elif op == 'invert': m = list(reversed(m))
            else: m = [None if random.random() < 0.3 else x for x in m]

        is_intro_outro = (bar < intro_bars or bar >= (bars - outro_bars))
        is_fill_bar = (bar % 8 == 7)
        is_open_hat_bar = (bar % 4 == 2)

        # Simuliamo le velocity in base alla sezione
        drum_mode = 'kick_hat' if is_intro_outro else 'full'
        kicks, snares, hats, claps = [], [], [], []
        for s in range(16):
            is_accent = (s % 4 == 0)
            if drum_mode == 'kick_hat':
                kicks.append(110 + random.randint(0, 5) if is_accent else 95 + random.randint(0, 10))
                hats.append(65 + random.randint(0, 15))
                snares.append(0); claps.append(0)
            else:
                kicks.append(120 + random.randint(0, 5) if is_accent else 100 + random.randint(0, 10))
                hats.append(75 + random.randint(0, 20))
                snares.append(105 + random.randint(0, 10))
                claps.append(90 + random.randint(0, 10))
        drum_vel = {'kick': kicks, 'snare': snares, 'hat': hats, 'clap': claps}

        for s in range(16):
            tick = base_tick + s * (TICKS_BEAT // 4)
            p_step = s % 16
            swing_offset = int(g['swing'] * (TICKS_BEAT // 4)) if (p_step % 2 == 1) else 0

            # 1. KICK (Accento più forte sul battere 1 e 3 per dare "punch")
            if drum_vel['kick'][p_step] > 0:
                vel = drum_vel['kick'][p_step] + 10 if p_step in [0, 8] else drum_vel['kick'][p_step]
                tracks['drums'].extend([
                    {'tick': tick, 'type': 'on', 'pitch': GM_KICK, 'vel': min(127, vel), 'channel': DRUM_CH},
                    {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_KICK, 'vel': 0, 'channel': DRUM_CH}
                ])
            
            # 2. SNARE / CLAP (Solo nel corpo del brano)
            if not is_intro_outro:
                if drum_vel['snare'][p_step] > 0 and g.get('snare', [0]*16)[p_step]:
                    tracks['drums'].extend([
                        {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_SNARE, 'vel': drum_vel['snare'][p_step], 'channel': DRUM_CH},
                        {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_SNARE, 'vel': 0, 'channel': DRUM_CH}
                    ])
                if drum_vel['clap'][p_step] > 0 and g.get('clap', [0]*16)[p_step]:
                    tracks['drums'].extend([
                        {'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_CLAP, 'vel': drum_vel['clap'][p_step], 'channel': DRUM_CH},
                        {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_CLAP, 'vel': 0, 'channel': DRUM_CH}
                    ])
                
                # Fill di snare/tom alla fine delle frasi (es. rullata di 4 sedicesimi)
                if is_fill_bar and p_step >= 12:
                    fill_vel = 70 + (p_step - 12) * 15
                    perc = GM_SNARE if p_step % 2 == 0 else GM_TOM_HIGH
                    tracks['drums'].extend([
                        {'tick': tick, 'type': 'on', 'pitch': perc, 'vel': min(127, fill_vel), 'channel': DRUM_CH},
                        {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': perc, 'vel': 0, 'channel': DRUM_CH}
                    ])

            # 3. HI-HAT (con variazione Open/Closed per dare respiro e groove)
            if drum_vel['hat'][p_step] > 0 and g['hat'][p_step]:
                hat_pitch = GM_HAT_OPEN if (is_open_hat_bar and p_step in [6, 14]) else GM_HAT_CLOSED
                hat_vel = drum_vel['hat'][p_step] + 15 if hat_pitch == GM_HAT_OPEN else drum_vel['hat'][p_step]
                hat_dur = (TICKS_BEAT//2) if hat_pitch == GM_HAT_OPEN else (TICKS_BEAT//4)//2
                
                tracks['drums'].extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': hat_pitch, 'vel': min(127, hat_vel), 'channel': DRUM_CH},
                    {'tick': tick + swing_offset + hat_dur, 'type': 'off', 'pitch': hat_pitch, 'vel': 0, 'channel': DRUM_CH}
                ])
                
            # 4. PERCUSSIONI AGGIUNTIVE (Groove Techno)
            if not is_intro_outro and p_step % 2 == 1 and random.random() < 0.15:
                perc_pitch = GM_RIMSHOT if random.random() < 0.5 else GM_TOM_HIGH
                tracks['drums'].extend([
                    {'tick': tick + swing_offset, 'type': 'on', 'pitch': perc_pitch, 'vel': 50 + random.randint(0, 40), 'channel': DRUM_CH},
                    {'tick': tick + swing_offset + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': perc_pitch, 'vel': 0, 'channel': DRUM_CH}
                ])

            # 5. BASSO & ARP (presenti nel corpo del brano)
            if not is_intro_outro:
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

# ================= GENERAZIONE MULTITRACK =================

def _extract_instrument_header(track):
    header = []
    for msg in track:
        if msg.type in ('note_on', 'note_off'): break
        if msg.type == 'program_change':
            header.append({'type': 'program_change', 'program': msg.program})
        elif msg.type == 'control_change' and msg.control in (0, 32, 7, 10, 11, 91, 93):
            header.append({'type': 'control_change', 'control': msg.control, 'value': msg.value})
    return header

GM_PROGRAM_NAMES = ['Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano', 'Honky-tonk Piano', 'Electric Piano 1', 'Electric Piano 2', 'Harpsichord', 'Clavinet', 'Celesta', 'Glockenspiel', 'Music Box', 'Vibraphone', 'Marimba', 'Xylophone', 'Tubular Bells', 'Dulcimer', 'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ', 'Reed Organ', 'Accordion', 'Harmonica', 'Tango Accordion', 'Acoustic Guitar (nylon)', 'Acoustic Guitar (steel)', 'Electric Guitar (jazz)', 'Electric Guitar (clean)', 'Electric Guitar (muted)', 'Overdriven Guitar', 'Distortion Guitar', 'Guitar Harmonics', 'Acoustic Bass', 'Electric Bass (finger)', 'Electric Bass (pick)', 'Fretless Bass', 'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1', 'Synth Bass 2', 'Violin', 'Viola', 'Cello', 'Contrabass', 'Tremolo Strings', 'Pizzicato Strings', 'Orchestral Harp', 'Timpani', 'String Ensemble 1', 'String Ensemble 2', 'Synth Strings 1', 'Synth Strings 2', 'Choir Aahs', 'Voice Oohs', 'Synth Voice', 'Orchestra Hit', 'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet', 'French Horn', 'Brass Section', 'Synth Brass 1', 'Synth Brass 2', 'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax', 'Oboe', 'English Horn', 'Bassoon', 'Clarinet', 'Piccolo', 'Flute', 'Recorder', 'Pan Flute', 'Blown Bottle', 'Shakuhachi', 'Whistle', 'Ocarina', 'Lead 1 (square)', 'Lead 2 (sawtooth)', 'Lead 3 (calliope)', 'Lead 4 (chiff)', 'Lead 5 (charang)', 'Lead 6 (voice)', 'Lead 7 (fifths)', 'Lead 8 (bass + lead)', 'Pad 1 (new age)', 'Pad 2 (warm)', 'Pad 3 (polysynth)', 'Pad 4 (choir)', 'Pad 5 (bowed)', 'Pad 6 (metallic)', 'Pad 7 (halo)', 'Pad 8 (sweep)', 'FX 1 (rain)', 'FX 2 (soundtrack)', 'FX 3 (crystal)', 'FX 4 (atmosphere)', 'FX 5 (brightness)', 'FX 6 (goblins)', 'FX 7 (echoes)', 'FX 8 (sci-fi)', 'Sitar', 'Banjo', 'Shamisen', 'Koto', 'Kalimba', 'Bag pipe', 'Fiddle', 'Shanai', 'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock', 'Taiko Drum', 'Melodic Tom', 'Synth Drum', 'Reverse Cymbal', 'Guitar Fret Noise', 'Breath Noise', 'Seashore', 'Bird Tweet', 'Telephone Ring', 'Helicopter', 'Applause', 'Gunshot']

_GM_NAME_HINTS = [(("bass ", "basso ", "contrabb "), 33), (("chitarr ", "guitar "), 25), (("piano ", "pianof "), 0), (("organ ", "organo "), 19), (("string ", "archi ", "violin ", "cello "), 48), (("pad ",), 89), (("lead ",), 80), (("vox ", "voce ", "vocal ", "choir ", "coro "), 52), (("flaut ", "flute "), 73), (("sax ",), 65), (("trump ", "tromba "), 56), (("tromb ",), 57), (("synth ",), 81)]

def _guess_program(name):
    low = (name or "").lower()
    for keys, prog in _GM_NAME_HINTS:
        if any(k in low for k in keys): return prog
    return 0

DRUM_PIECES = [(GM_KICK, 'drum_kick'), (GM_SNARE, 'drum_snare'), (GM_HAT_CLOSED, 'drum_hat'), (GM_CLAP, 'drum_clap')]
DRUM_TRACK_NAMES = {'drums': 'Drums', 'drum_kick': 'Kick', 'drum_snare': 'Snare', 'drum_hat': 'Hat', 'drum_clap': 'Clap'}

def split_drum_track(tracks):
    events = tracks.get('drums')
    if not events: return tracks
    out = {k: v for k, v in tracks.items() if k != 'drums'}
    known = {p for p, _k in DRUM_PIECES}
    for pitch, key in DRUM_PIECES:
        ev = [e for e in events if e['pitch'] == pitch]
        if ev: out[key] = ev
    rest = [e for e in events if e['pitch'] not in known]
    if rest: out['drums'] = rest
    return out

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
    scale_t = TICKS_BEAT / mid.ticks_per_beat
    free_channels = [c for c in range(16) if c != DRUM_CH]

    if submode == 'faithful':
        track_idx = 0
        for original_track in mid.tracks:
            if any(msg.channel == DRUM_CH for msg in original_track if hasattr(msg, 'channel')): continue
            original_name = next((m.name for m in original_track if m.type == 'track_name'), None)
            header = _extract_instrument_header(original_track)
            ch = free_channels[track_idx % len(free_channels)]
            pending, pairs, current_tick_raw = {}, [], 0
            for msg in original_track:
                current_tick_raw += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    pending[msg.note] = (current_tick_raw, msg.velocity)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in pending:
                        on_raw, vel = pending.pop(msg.note)
                        on_quantized = round(on_raw * scale_t / (TICKS_BEAT // 16)) * (TICKS_BEAT // 16)
                        dur_raw = current_tick_raw - on_raw
                        dur_quantized = max(TICKS_BEAT // 16, round(dur_raw * scale_t / (TICKS_BEAT // 16)) * (TICKS_BEAT // 16))
                        pitch = snap_to_scale(msg.note, root, scale)
                        pairs.append({'tick': on_quantized, 'dur': dur_quantized, 'pitch': pitch, 'vel': vel})
            for note, (on_raw, vel) in pending.items():
                on_quantized = round(on_raw * scale_t / (TICKS_BEAT // 16)) * (TICKS_BEAT // 16)
                dur_quantized = (TICKS_BEAT // 16) * 4
                pitch = snap_to_scale(note, root, scale)
                pairs.append({'tick': on_quantized, 'dur': dur_quantized, 'pitch': pitch, 'vel': vel})
            
            track_events = []
            for p in pairs:
                track_events.extend([{'tick': p['tick'], 'type': 'on', 'pitch': p['pitch'], 'vel': p['vel'], 'channel': ch}, {'tick': p['tick'] + p['dur'], 'type': 'off', 'pitch': p['pitch'], 'vel': 0, 'channel': ch}])
            if track_events:
                track_key = (original_name or '').strip() or f'instrument_{track_idx}'
                base_key, n = track_key, 2
                while track_key in tracks or track_key in DRUM_TRACK_NAMES:
                    track_key = f'{base_key} {n}'; n += 1
                tracks[track_key] = track_events
                if header: headers[track_key] = header
                track_idx += 1
    else:
        roles = [('sub_bass', 0, (24, 36)), ('bassline', 1, (36, 48)), ('pad', 2, (48, 60)), ('chords', 3, (55, 67)), ('arp', 4, (60, 72)), ('lead', 5, (67, 79)), ('fx_perc', 6, (72, 84))]
        for role_name, channel, _ in roles: tracks[role_name] = []
        
        # Semplificazione per multitrack generative: usa la stessa logica base
        for bar in range(bars):
            base_tick = bar * 4 * TICKS_BEAT
            for s in range(16):
                tick = base_tick + s * (TICKS_BEAT // 4)
                p_step = s % 16
                swing_offset = int(g['swing'] * (TICKS_BEAT // 4)) if (p_step % 2 == 1) else 0
                
                if g['kick'][p_step]:
                    if 'drums' not in tracks: tracks['drums'] = []
                    tracks['drums'].extend([{'tick': tick, 'type': 'on', 'pitch': GM_KICK, 'vel': 110, 'channel': DRUM_CH}, {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_KICK, 'vel': 0, 'channel': DRUM_CH}])
                if g.get('snare', [0]*16)[p_step]:
                    tracks['drums'].extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_SNARE, 'vel': 100, 'channel': DRUM_CH}, {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_SNARE, 'vel': 0, 'channel': DRUM_CH}])
                if g.get('clap', [0]*16)[p_step]:
                    tracks['drums'].extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_CLAP, 'vel': 90, 'channel': DRUM_CH}, {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_CLAP, 'vel': 0, 'channel': DRUM_CH}])
                if g['hat'][p_step]:
                    tracks['drums'].extend([{'tick': tick + swing_offset, 'type': 'on', 'pitch': GM_HAT_CLOSED, 'vel': 75, 'channel': DRUM_CH}, {'tick': tick + (TICKS_BEAT//4)//2, 'type': 'off', 'pitch': GM_HAT_CLOSED, 'vel': 0, 'channel': DRUM_CH}])
                
                for role_name, channel, (low_pitch, high_pitch) in roles:
                    if role_name == 'bassline' and g['bass'][p_step]:
                        idx = 0 if random.random() < 0.8 else random.choice([1, len(scale)-1])
                        pitch = root - 12 + scale[idx % len(scale)]
                        tracks['bassline'].extend([{'tick': tick, 'type': 'on', 'pitch': max(30, min(pitch, 48)), 'vel': 95, 'channel': channel}, {'tick': tick + (TICKS_BEAT//4), 'type': 'off', 'pitch': max(30, min(pitch, 48)), 'vel': 0, 'channel': channel}])
                    elif role_name == 'arp' and random.random() < g['arp_density']:
                        pitch = random.randint(low_pitch, high_pitch)
                        pitch = snap_to_scale(pitch, root, scale)
                        tracks['arp'].extend([{'tick': tick, 'type': 'on', 'pitch': pitch, 'vel': 75, 'channel': channel}, {'tick': tick + (TICKS_BEAT//4) - 10, 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': channel}])

    if split_drums and 'drums' in tracks:
        tracks = split_drum_track(tracks)
    return tracks, root, scale, headers, bars

def _events_to_notes(events):
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
    for nt in notes: by_pitch.setdefault(nt[2], []).append(nt)
    cleaned_all = []
    for lst in by_pitch.values():
        lst.sort(key=lambda x: (x[0], -x[3]))
        cleaned = []
        for nt in lst:
            if cleaned and nt[0] == cleaned[-1][0]: cleaned[-1][1] = max(cleaned[-1][1], nt[1]); continue
            if cleaned and cleaned[-1][1] > nt[0]: cleaned[-1][1] = nt[0]
            cleaned.append(nt)
        cleaned_all.extend(cleaned)
    cleaned_all.sort(key=lambda x: (x[0], x[2]))
    return cleaned_all

def build_midi_file(tracks, bpm, mode, submode, headers=None, label=None):
    headers = headers or {}
    faithful = (mode == 'multitrack' and submode == 'faithful')
    notes_by_track = {}
    for key, events in tracks.items():
        notes = _events_to_notes(events)
        if notes: notes_by_track[key] = (events[0].get('channel', 0), notes)

    mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_BEAT)
    total_end = max((nt[1] for _, notes in notes_by_track.values() for nt in notes), default=0)
    t_tempo = mido.MidiTrack()
    t_tempo.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    t_tempo.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))
    if label:
        text = ("MIDI Forge - " + label).encode('ascii', 'ignore').decode('ascii')[:120]
        t_tempo.append(mido.MetaMessage('marker', text=text, time=0))
    t_tempo.append(mido.MetaMessage('end_of_track', time=total_end))
    mid.tracks.append(t_tempo)

    used_names = Counter()
    for key, (ch, notes) in notes_by_track.items():
        is_drums = (ch == DRUM_CH)
        header = list(headers.get(key, []))
        if not any(h['type'] == 'program_change' for h in header):
            if is_drums: pc = 0
            else:
                pc = None if faithful else {'bass': 38, 'arp': 80, 'sub_bass': 39, 'bassline': 38, 'pad': 89, 'chords': 0, 'lead': 81, 'fx_perc': 117}.get(key)
                if pc is None: pc = _guess_program(key)
            header.append({'type': 'program_change', 'program': pc})
        bank = [h for h in header if h['type'] == 'control_change' and h['control'] in (0, 32)]
        pcs = [h for h in header if h['type'] == 'program_change'][:1]
        mix = {h['control']: h for h in header if h['type'] == 'control_change' and h['control'] not in (0, 32)}
        program = pcs[0]['program'] & 0x7F if pcs else None
        
        if is_drums: name = DRUM_TRACK_NAMES.get(key, 'Drums')
        elif key.startswith('instrument_'): name = GM_PROGRAM_NAMES[program] if program is not None else key
        elif faithful: name = key
        else: name = {'bass': 'Bass', 'arp': 'Synth', 'sub_bass': 'Sub Bass', 'bassline': 'Bass', 'pad': 'Pad', 'chords': 'Piano', 'lead': 'Lead', 'fx_perc': 'Percussion', 'drums': 'Drums'}.get(key, key.replace('_', ' ').title())
        
        used_names[name] += 1
        if used_names[name] > 1: name = f'{name} {used_names[name]}'
        
        midi_track = mido.MidiTrack()
        midi_track.append(mido.MetaMessage('track_name', name=name, time=0))
        for h in bank: midi_track.append(mido.Message('control_change', control=h['control'], value=h['value'], channel=ch, time=0))
        if program is not None: midi_track.append(mido.Message('program_change', program=program, channel=ch, time=0))
        for h in mix.values(): midi_track.append(mido.Message('control_change', control=h['control'], value=h['value'], channel=ch, time=0))
        
        ev = []
        for start, end, pitch, vel in notes:
            ev.append((end, 0, pitch, 0))
            ev.append((start, 1, pitch, vel))
        ev.sort(key=lambda x: (x[0], x[1]))
        prev = 0
        for tick, is_on, pitch, vel in ev:
            midi_track.append(mido.Message('note_on' if is_on else 'note_off', note=pitch, velocity=vel, time=tick - prev, channel=ch))
            prev = tick
        midi_track.append(mido.MetaMessage('end_of_track', time=max(0, total_end - prev)))
        mid.tracks.append(midi_track)

    buf = io.BytesIO()
    mid.save(file=buf)
    buf.seek(0)
    return buf

def generate_report(tracks, genre, mode, submode, bpm, bars, seed, root, scale, duration_mode, duration_seconds, original_filename):
    report = ["=" * 60, "MIDI FORGE UNIVERSALE - REPORT DI GENERAZIONE", "=" * 60, "", "DATA E ORA", f"   Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "", "PARAMETRI GENERAZIONE", f"   File originale: {original_filename}", f"   Modalità: {mode.upper()}", f"   Sotto-modalità: {submode.upper()}", f"   Genere: {genre.upper()}", f"   Seed: {seed}", f"   BPM: {bpm}", f"   Battute: {bars}"]
    if duration_mode == "Minuti:Secondi" and duration_seconds:
        report.append(f"   Durata target: {duration_seconds // 60}:{duration_seconds % 60:02d}")
    duration_actual = (bars * 4 * 60) / bpm
    report.extend([f"   Durata effettiva: {int(duration_actual)}:{int((duration_actual - int(duration_actual)) * 60):02d}", "", "ANALISI TONALE", f"   Tonica rilevata: {NOTE_NAMES[root]}", f"   Scala: {' - '.join([NOTE_NAMES[(root + i) % 12] for i in scale])}", f"   Intervalli: {scale}", ""])
    g = GENRES[genre]
    report.extend(["PATTERN RITMICI (1 sedicesimi)", f"   Kick (GM 36):  {''.join(['#' if x else '.' for x in g['kick']])}", f"   Snare (GM 38): {''.join(['#' if x else '.' for x in g.get('snare', [0]*16)])}"])
    if 'clap' in g: report.append(f"   Clap (GM 39):  {''.join(['#' if x else '.' for x in g['clap']])}")
    report.extend([f"   Hat (GM 42):   {''.join(['#' if x else '.' for x in g['hat']])}", f"   Bass:          {''.join(['#' if x else '.' for x in g['bass']])}", f"   Swing: {g['swing'] * 100:.0f}%", f"   Densità Arp: {g['arp_density'] * 100:.0f}%", "", "STRUTTURA BRANO (DJ-Friendly)", "   [ INTRO drum-only ] -> [ BREAK 1 ] -> [ BUILD-UP ] -> [ DROP ] -> [ BREAK 2 ] -> [ OUTRO drum-only ]", "", "TRACCE OUTPUT"])
    track_idx = 1
    for track_key in tracks.keys():
        if track_key in DRUM_TRACK_NAMES: report.append(f"   {track_idx}. {DRUM_TRACK_NAMES[track_key]} (Canale 10 - GM Drum Map)")
        elif track_key.startswith('instrument_'): report.append(f"   {track_idx}. {track_key} (Canale melodico)")
        else: report.append(f"   {track_idx}. {track_key.replace('_', ' ').title()} (Canale melodico)")
        track_idx += 1
    report.extend(["", "STATISTICHE MIDI", f"   Note totali generate: {sum(1 for events in tracks.values() for e in events if e['type'] == 'on')}", f"   Tracce MIDI: {len(tracks) + 1}", "", "NOTE PER LOGIC PRO", "   - Apri con File > Apri (non Importa)", "   - INTRO e OUTRO sono drum-only per beatmatching", "   - Ogni traccia ha nome e program change al tick 0", "   - Batteria su canale 10: assegna Drum Kit Designer se necessario", "", "=" * 60, "Generato con MIDI Forge Universale | 100% Free & Open Source", "=" * 60])
    return "\n".join(report)

def render_midi_player(tracks, bpm):
    all_notes_with_dur = []
    for events in tracks.values(): all_notes_with_dur.extend(_compute_note_durations(events))
    notes_json = json.dumps([{'tick': n['tick'], 'dur': n['dur'], 'pitch': n['pitch'], 'vel': n['vel'], 'channel': n['channel']} for n in all_notes_with_dur])
    html_player = f"""<!DOCTYPE html><html><head><script src="https://cdnjs.cloudflare.com/ajax/libs/tone/14.8.49/Tone.js"></script><style>body{{font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:0;padding:15px;background:#0e1117;color:#fafafa}}.player{{background:#1a1d23;border-radius:12px;padding:20px;box-shadow:0 4px 12px rgba(0,0,0,0.3)}}.title{{font-size:14px;font-weight:600;margin-bottom:12px}}.controls{{display:flex;gap:10px;align-items:center;margin-bottom:15px}}button{{background:#ff4b4b;color:white;border:none;padding:10px 20px;border-radius:8px;cursor:pointer;font-weight:600}}button:hover{{background:#ff6b6b}}.status{{font-size:13px;color:#aaa}}</style></head><body><div class="player"><div class="title">Anteprima MIDI (con durate reali)</div><div class="controls"><button id="playBtn" onclick="togglePlay()">Play</button><button onclick="stop()">Stop</button><span class="status" id="status">Pronto - {bpm} BPM</span></div></div><script>const notes={notes_json};let isPlaying=false,synths={{}},scheduledEvents=[];async function togglePlay(){{if(isPlaying){{stop();return}}await Tone.start();try{{const ticksPerSecond=({TICKS_BEAT}*{bpm})/60;for(let ch=0;ch<16;ch++){{if(ch==={DRUM_CH}){{synths[ch]={{kick:new Tone.MembraneSynth().toDestination(),snare:new Tone.NoiseSynth({{noise:{{type:'white'}},envelope:{{attack:0.001,decay:0.2,sustain:0}}}}).toDestination(),hat:new Tone.MetalSynth({{envelope:{{attack:0.001,decay:0.05,release:0.01}},harmonicity:5.1,modulationIndex:32,resonance:4000,octaves:1.5}}).toDestination(),clap:new Tone.NoiseSynth({{noise:{{type:'pink'}},envelope:{{attack:0.001,decay:0.15,sustain:0}}}}).toDestination()}}}}else{{synths[ch]=new Tone.PolySynth(Tone.Synth).toDestination();synths[ch].set({{oscillator:{{type:'triangle'}},envelope:{{attack:0.02,decay:0.3,sustain:0.2,release:0.5}}}})}}}}notes.forEach(note=>{{const timeInSeconds=note.tick/ticksPerSecond,durInSeconds=note.dur/ticksPerSecond;if(note.channel==={DRUM_CH}){{scheduledEvents.push(Tone.getTransport().schedule(time=>{{if(note.pitch==={GM_KICK})synths[{DRUM_CH}].kick.triggerAttackRelease('C1',durInSeconds,time,note.vel/127);else if(note.pitch==={GM_SNARE})synths[{DRUM_CH}].snare.triggerAttackRelease(durInSeconds,time,note.vel/127);else if(note.pitch==={GM_CLAP})synths[{DRUM_CH}].clap.triggerAttackRelease(durInSeconds,time,note.vel/127);else if(note.pitch==={GM_HAT_CLOSED}||note.pitch==={GM_HAT_OPEN})synths[{DRUM_CH}].hat.triggerAttackRelease('C3',durInSeconds,time,note.vel/127)}}},timeInSeconds)))}}else{{const noteName=Tone.Frequency(note.pitch,'midi').toNote();scheduledEvents.push(Tone.getTransport().schedule(time=>{{synths[note.channel].triggerAttackRelease(noteName,durInSeconds,time,note.vel/127)}}},timeInSeconds)))}}}});Tone.getTransport().start();isPlaying=true;document.getElementById('playBtn').textContent='Pause';document.getElementById('status').textContent='In riproduzione...'}}catch(e){{document.getElementById('status').textContent='Errore: '+e.message}}}}function stop(){{Tone.getTransport().stop();scheduledEvents.forEach(id=>Tone.getTransport().clear(id));scheduledEvents=[];isPlaying=false;document.getElementById('playBtn').textContent='Play';document.getElementById('status').textContent='Pronto - {bpm} BPM'}}</script></body></html>"""
    components.html(html_player, height=150)

# ================= INTERFACCIA STREAMLIT =================

if 'generated' not in st.session_state:
    st.session_state.generated = {'tracks': None, 'root': None, 'scale': None, 'headers': None, 'bars': None, 'bpm': None, 'midi_bytes': None, 'report_text': '', 'label': None, 'mode': None, 'submode': None, 'genre': None, 'duration_mode': None, 'duration_seconds': None, 'original_filename': None}

st.title("MIDI Forge Universale")
st.markdown("Trasforma qualsiasi file MIDI in 30+ generi musicali. Struttura DJ-Friendly: INTRO -> BREAK -> BUILD -> DROP -> BREAK -> OUTRO")

col1, col2 = st.columns([1, 1])

with col1:
    uploaded_file = st.file_uploader("Carica il tuo file MIDI (.mid o .midi)", type=["mid", "midi"])
    mode = st.selectbox("Modalità Principale", ["minimal", "multitrack"])
    if mode == "minimal":
        submode = st.selectbox("Sotto-modalità", ["extract", "generate"])
    else:
        submode = st.selectbox("Sotto-modalità", ["faithful", "generative"])
        split_drums = st.checkbox("Batteria su tracce separate (Kick / Snare / Hat / Clap)", value=True)

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
            bars = st.number_input("Battute", min_value=16, max_value=512, step=4, value=g_defaults['bars_default'], disabled=use_default_bars)
            duration_seconds = None
        else:
            col_min, col_sec = st.columns(2)
            with col_min:
                minutes = st.number_input("Minuti", min_value=0, max_value=30, value=3)
            with col_sec:
                seconds = st.number_input("Secondi", min_value=0, max_value=59, value=0) # Step rimosso come richiesto
            duration_seconds = (minutes * 60) + seconds
            bars = None
    seed = st.number_input("Seed", min_value=1, max_value=99999, value=42)

st.markdown("---")

if st.button("Genera MIDI", type="primary", use_container_width=True):
    if not uploaded_file:
        st.error("Carica prima un file MIDI!")
    else:
        with st.spinner("Generazione in corso..."):
            try:
                file_bytes = io.BytesIO(uploaded_file.getvalue())
                notes_data = extract_notes(file_bytes)
                if not notes_data:
                    st.error("Il file MIDI non contiene note valide.")
                else:
                    final_bpm = g_defaults['bpm_default'] if use_default_bpm else bpm
                    if duration_mode == "Minuti:Secondi" and duration_seconds:
                        raw_bars = (duration_seconds * final_bpm) / 240
                        final_bars = int(round(raw_bars / 4) * 4) # Arrotonda al multiplo di 4
                        final_bars = max(16, final_bars)
                        st.info(f"Durata calcolata: {final_bars} battute (per coprire ~{duration_seconds} secondi a {final_bpm} BPM)")
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
                            st.info(f"Durata allineata: {final_bars} battute (richieste: {requested_bars})")

                    label = f"{genre} - {mode}/{submode}"
                    midi_buffer = build_midi_file(tracks, final_bpm, mode, submode, headers, label=label)
                    report_text = generate_report(tracks, genre, mode, submode, final_bpm, final_bars, seed, root, scale, duration_mode, duration_seconds, uploaded_file.name)

                    st.session_state.generated = {
                        'tracks': tracks, 'root': root, 'scale': scale, 'headers': headers,
                        'bars': final_bars, 'bpm': final_bpm, 'midi_bytes': midi_buffer.getvalue(),
                        'report_text': report_text, 'label': label, 'mode': mode,
                        'submode': submode, 'genre': genre, 'duration_mode': duration_mode,
                        'duration_seconds': duration_seconds, 'original_filename': uploaded_file.name
                    }
                    st.success(f"Completato! (Tonica: {NOTE_NAMES[root]}, BPM: {final_bpm})")
            except Exception as e:
                st.error(f"Errore: {str(e)}")

g = st.session_state.generated
if g and g.get('midi_bytes') is not None and g.get('report_text'):
    st.markdown("### Anteprima")
    render_midi_player(g['tracks'], g['bpm'])
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(label="Scarica MIDI", data=g['midi_bytes'], file_name=f"midi_forge_{g['genre']}_{g['mode']}_{g['submode']}.mid", mime="audio/midi", use_container_width=True)
    with col_dl2:
        st.download_button(label="Scarica Report TXT", data=g['report_text'].encode('utf-8'), file_name=f"report_{g['genre']}_{g['mode']}_{g['submode']}.txt", mime="text/plain", use_container_width=True)
    with st.expander("Visualizza Report"):
        st.code(g['report_text'], language=None)
else:
    st.info("Carica un MIDI e clicca 'Genera' per iniziare.")

st.markdown("---")
st.caption("MIDI Forge Universale | Standard General MIDI | Struttura DJ-Friendly | 100% Open Source & Free")

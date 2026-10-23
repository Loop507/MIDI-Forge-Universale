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
    'acid': {'bpm_default': 135, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,1, 0,1,0,1, 1,0,1,0, 1,1,0,1], 'arp_density': 0.85, 'swing': 0.0},
    'ambient': {'bpm_default': 80, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.15, 'swing': 0.0},
    'armonico': {'bpm_default': 100, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.7, 'swing': 0.1},
    'breakcore': {'bpm_default': 200, 'bars_default': 52, 'kick': [1,0,0,1, 0,1,0,0, 1,0,1,0, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,1,0,0, 1,0,0,1], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,0, 0,1,0,1], 'arp_density': 0.8, 'swing': 0.05, 'meter': ['7/8', '7/8', '4/4', '13/8']},
    'commerciale_90s': {'bpm_default': 120, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'arp_density': 0.6, 'swing': 0.08},
    'deep': {'bpm_default': 124, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.15},
    'disco': {'bpm_default': 122, 'bars_default': 76, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.2},
    'drone': {'bpm_default': 70, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.05, 'swing': 0.0},
    'drum_n_bass': {'bpm_default': 174, 'bars_default': 116, 'kick': [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,1, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.7, 'swing': 0.0},
    'dub_techno': {'bpm_default': 128, 'bars_default': 156, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0},
    'edm_2000s': {'bpm_default': 128, 'bars_default': 100, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'elettronico': {'bpm_default': 130, 'bars_default': 84, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'funk': {'bpm_default': 112, 'bars_default': 56, 'kick': [1,0,0,1, 0,0,0,0, 1,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [2,1,1,1, 2,1,1,1, 2,1,1,1, 2,1,1,1], 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,1,0,0], 'ghost': [0,0,0,1, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.05},
    'glitch': {'bpm_default': 128, 'bars_default': 60, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,1, 0,0,0,0, 1,0,0,0], 'arp_density': 0.95, 'swing': 0.1},
    'harsh_noise': {'bpm_default': 100, 'bars_default': 68, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 1.0, 'swing': 0.0, 'meter': ['7/8', '9/8', '4/4']},
    'hip_hop': {'bpm_default': 92, 'bars_default': 76, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.3, 'swing': 0.2, 'lazy': 0.12},
    'idm': {'bpm_default': 135, 'bars_default': 72, 'kick': [1,0,0,1, 0,1,0,1, 0,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,0,1,0, 1,0,1,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.85, 'swing': 0.1},
    'industrial': {'bpm_default': 135, 'bars_default': 76, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.7, 'swing': 0.0},
    'lowercase': {'bpm_default': 104, 'bars_default': 116, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.05, 'swing': 0.0, 'meter': ['17/8']},
    'microsound': {'bpm_default': 90, 'bars_default': 92, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.1, 'swing': 0.0},
    'minimal': {'bpm_default': 126, 'bars_default': 68, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.3, 'swing': 0.0},
    'minimal_techno': {'bpm_default': 130, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.5, 'swing': 0.0},
    'minimalismo_ritmico': {'bpm_default': 115, 'bars_default': 92, 'kick': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.05, 'meter': ['11/8', '11/8', '15/8', '15/8']},
    'noise': {'bpm_default': 120, 'bars_default': 76, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 0.9, 'swing': 0.0, 'meter': ['29/16', '4/4']},
    'onkyo': {'bpm_default': 50, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.02, 'swing': 0.0},
    'r&b': {'bpm_default': 95, 'bars_default': 76, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,1], 'arp_density': 0.55, 'swing': 0.2, 'lazy': 0.12},
    'reggaeton': {'bpm_default': 95, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,1,0, 0,1,0,0, 0,0,1,0, 0,1,0,0], 'clap': [0]*16, 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.0},
    'sperimentale': {'bpm_default': 100, 'bars_default': 72, 'kick': [1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,1,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,1,0,0, 1,0,0,1, 0,0,1,0, 1,0,0,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,1], 'arp_density': 0.7, 'swing': 0.1, 'meter': ['5/16', '7/16', '4/4']},
    'soul': {'bpm_default': 95, 'bars_default': 60, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,1, 0,0,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.25, 'lazy': 0.08},
    'synthpop': {'bpm_default': 120, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.75, 'swing': 0.0},
    'techno': {'bpm_default': 132, 'bars_default': 148, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [0,1,1,1, 0,1,1,1, 0,1,1,1, 0,1,1,1], 'arp_density': 0.75, 'swing': 0.0},
    'trap': {'bpm_default': 140, 'bars_default': 68, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0},
    'trance': {'bpm_default': 140, 'bars_default': 148, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0]*16, 'arp_density': 0.9, 'swing': 0.0},
    'underground': {'bpm_default': 135, 'bars_default': 84, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0]*16, 'hat': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.1, 'snare_shift': True},
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
SCALES = {'Minore naturale': [0,2,3,5,7,8,10], 'Maggiore': [0,2,4,5,7,9,11], 'Dorico': [0,2,3,5,7,9,10], 'Frigio': [0,1,3,5,7,8,10],
          'Misolidio': [0,2,4,5,7,9,10], 'Minore armonica': [0,2,3,5,7,8,11], 'Pentatonica minore': [0,3,5,7,10]}
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

_KEY_MAJOR = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
_KEY_MINOR = ['Cm', 'C#m', 'Dm', 'Ebm', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'Bbm', 'Bm']

def _compute_key_signature(root, scale):
    # nomi validi per il meta-evento key_signature di mido
    return (_KEY_MINOR if _is_minor_scale(scale) else _KEY_MAJOR)[root % 12]

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

def notes_from_midi(mid):
    """Note melodiche (canale batteria escluso) con durata; tick scalati a TICKS_BEAT."""
    scale_t = TICKS_BEAT / mid.ticks_per_beat
    out = []
    for ti, track in enumerate(mid.tracks):
        t, pending = 0, {}

        def close(key, end):
            st, vel = pending.pop(key)
            out.append({'pitch': key[1], 'tick': int(round(st * scale_t)),
                        'dur': max(1, int(round((end - st) * scale_t))), 'vel': vel, 'track': ti})

        for msg in track:
            t += msg.time
            if msg.type not in ('note_on', 'note_off') or msg.channel == DRUM_CH:
                continue
            key = (msg.channel, msg.note)
            if msg.type == 'note_on' and msg.velocity > 0:
                if key in pending: close(key, t)
                pending[key] = (t, msg.velocity)
            elif key in pending:
                close(key, t)
        for key in list(pending):
            close(key, pending[key][0] + mid.ticks_per_beat // 4)
    return out

def extract_notes(mid_file):
    return notes_from_midi(mido.MidiFile(file=mid_file))

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

# ================= STRUTTURA PER GENERE: TIMELINE A STRATI =================
# Ogni genere ha la sua timeline: sezioni con nome, battute e STRATI attivi. Gli strati entrano ed escono come nelle guide
# di arrangiamento (es. Deep House: intro kick+hat+pad -> groove: +basso +clap +open hat -> armonia: +accordi +perc -> hook ...).
#   batteria : kick hat clap(snare+clap sul backbeat) open(open hat sui levare) perc fill(fill ogni 8 battute)
#              roll(rullata di snare nelle ultime 4 battute) rolls(rullata corta e piano, ultime 2)
#   melodici : bass bassl(basso sui battiti, piano) pad chords(stab) chordsl(accordi lunghi) arp arpl(arp rado) lead leadl(lead rado)
# Gli strati melodici che entrano di nuovo salgono di volume in 4 battute (ingresso morbido, niente tagli netti).
LAYER_TOKENS = frozenset('kick hat clap open perc bass bassl pad chords chordsl arp arpl lead leadl roll rolls fill event'.split())
EVENT = frozenset({'event'})   # un suono isolato e piano per battuta (Lowercase, Onkyo)
MELODIC = frozenset('bass bassl pad chords chordsl arp arpl lead leadl'.split())
DRUM_LAYERS = frozenset('kick hat clap open perc roll rolls fill'.split())
FAMILY = {'bass': 'bass', 'bassl': 'bass', 'pad': 'pad', 'chords': 'chords', 'chordsl': 'chords',
          'arp': 'arp', 'arpl': 'arp', 'lead': 'lead', 'leadl': 'lead'}
SYN_FACTOR = {'arp': 1.0, 'lead': 1.0, 'chords': 0.85, 'arpl': 0.5, 'leadl': 0.5, 'chordsl': 0.5, 'pad': 0.5}

TIMELINES = {
 # Famiglia 1: generi ritmici e da club
 'acid': [('Intro DJ', 32, 'kick hat pad bassl'), ('Groove building', 32, 'kick hat perc pad bass'), ('Main 1', 32, 'kick hat clap perc pad bass fill'),
          ('Breakdown', 16, 'pad bass'), ('Build-up', 16, 'hat pad bassl roll'), ('Drop / Main 2', 32, 'kick hat clap open perc pad bass fill'),
          ('Outro', 32, 'kick hat')],
 'drum_n_bass': [('Intro', 32, 'hat pad leadl'), ('Tension / Build', 16, 'kick hat pad roll'), ('Drop 1', 32, 'kick hat clap bass fill'),
                 ('Breakdown', 16, 'pad lead'), ('Build 2', 16, 'kick hat pad roll'), ('Drop 2', 32, 'kick hat clap perc bass arp lead fill'),
                 ('Outro', 16, 'pad')],
 'dub_techno': [('Intro sommersa', 32, 'kick pad'), ('Groove dub', 32, 'kick hat open pad bass chords'), ('Evoluzione', 32, 'kick hat open pad bass chords perc'),
                ('Breakdown dub', 16, 'pad chords'), ('Ritorno', 32, 'kick hat open pad bass chords perc'), ('Outro', 16, 'kick pad')],
 'edm_2000s': [('Intro', 16, 'kick hat arpl'), ('Build 1', 16, 'kick hat pad arpl roll'), ('Drop 1', 32, 'kick hat clap open perc bass chords lead fill'),
               ('Breakdown', 16, 'pad lead'), ('Build 2', 16, 'kick hat pad chords roll'),
               ('Drop 2', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'kick hat bass')],
 'hip_hop': [('Intro', 4, 'hat chordsl'), ('Beat completo', 4, 'kick hat clap bass'), ('Strofa 1', 16, 'kick hat clap bass chordsl leadl'),
             ('Hook', 8, 'kick hat clap bass pad chords lead'), ('Strofa 2', 16, 'kick hat clap perc bass chordsl leadl'),
             ('Hook 2', 8, 'kick hat clap bass pad chords lead fill'), ('Bridge', 8, 'pad chordsl'),
             ('Strofa 3 / Hook', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'pad chordsl')],
 'minimal_techno': [('Intro loop', 32, 'kick hat'), ('Evoluzione 1', 32, 'kick hat perc bass'), ('Evoluzione 2', 32, 'kick hat perc bass arpl'),
                    ('Evoluzione 3', 32, 'kick hat clap perc bass arp'), ('Outro loop', 32, 'kick hat')],
 'reggaeton': [('Intro', 8, 'kick clap hat'), ('Beat completo', 8, 'kick clap hat perc bass'), ('Strofa 1', 8, 'kick clap hat bass chordsl leadl'),
               ('Hook', 8, 'kick clap hat perc bass pad chords lead'), ('Strofa 2', 8, 'kick clap hat perc bass chordsl leadl'),
               ('Hook 2', 8, 'kick clap hat perc bass pad chords lead fill'), ('Bridge', 8, 'clap hat pad bassl'),
               ('Hook finale', 16, 'kick clap hat open perc bass pad chords arp lead fill'), ('Outro', 24, 'kick clap hat')],
 'techno': [('Intro DJ', 32, 'kick hat'), ('Build', 32, 'kick hat clap open bass'), ('Main 1', 32, 'kick hat clap open perc bass chords arp'),
            ('Breakdown', 16, 'pad'), ('Build-up', 16, 'hat pad roll'), ('Drop / Main 2', 32, 'kick hat clap open perc bass pad chords arp lead fill'),
            ('Outro', 32, 'kick hat')],
 'trance': [('Intro lunga', 64, 'kick hat pad arpl'), ('Main 1', 32, 'kick hat clap open bass pad arpl lead'), ('Breakdown', 32, 'pad chordsl lead'),
            ('Build', 16, 'hat pad chords arp roll'), ('Drop', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'pad')],
 'trap': [('Intro', 8, 'pad leadl bassl'), ('Hook', 8, 'kick hat clap perc bass pad lead'), ('Strofa 1', 16, 'kick hat clap bass pad leadl'),
          ('Hook 2', 16, 'kick hat clap perc bass pad lead arp fill'), ('Strofa 2', 16, 'kick hat clap bass pad leadl'), ('Bridge', 8, 'pad leadl'),
          ('Hook finale', 16, 'kick hat clap perc bass pad lead arp fill'), ('Outro', 8, 'pad leadl bassl')],
 # Famiglia 2: generi armonici e da canzone
 'commerciale_90s': [('Intro', 8, 'kick hat arpl'), ('Strofa 1', 16, 'kick hat clap bass chordsl leadl'), ('Pre-chorus', 8, 'kick hat clap bass pad roll'),
                     ('Ritornello', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Strofa 2', 16, 'kick hat clap open bass chordsl leadl arpl'),
                     ('Pre-chorus 2', 8, 'kick hat clap bass pad roll'), ('Ritornello 2', 16, 'kick hat clap open perc bass pad chords arp lead fill'),
                     ('Bridge', 8, 'pad chordsl bassl'), ('Ritornello finale', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'kick hat bass')],
 'deep': [('Intro DJ', 16, 'kick hat pad'), ('Groove base', 16, 'kick hat clap open bass pad'), ('Armonia', 16, 'kick hat clap open perc bass pad chords'),
          ('Hook / Main 1', 16, 'kick hat clap open perc bass pad chords arpl lead'), ('Breakdown breve', 8, 'kick hat perc pad chordsl'),
          ('Build-up soft', 8, 'kick hat open bass pad chordsl rolls'), ('Main 2', 32, 'kick hat clap open perc bass pad chords arp lead fill'),
          ('Outro DJ', 16, 'kick hat bass')],
 'disco': [('Intro vamp', 32, 'kick hat open bass chords'), ('Strofa 1', 16, 'kick hat open clap bass chords leadl arpl'),
           ('Ritornello', 16, 'kick hat open clap perc bass chords arp lead fill'), ('Strofa 2', 16, 'kick hat open clap bass chords leadl arpl'),
           ('Ritornello 2', 16, 'kick hat open clap perc bass chords arp lead fill'), ('Breakdown strumentale', 16, 'kick hat open bass chords arp'),
           ('Ritornello finale', 16, 'kick hat open clap perc bass chords arp lead fill'), ('Outro vamp', 16, 'kick hat open bass chords')],
 'funk': [('Intro', 8, 'kick hat clap chords'), ('Riff principale', 8, 'kick hat clap bass chords lead'), ('Strofa', 16, 'kick hat clap bass chords leadl'),
          ('Ritornello / Vamp', 16, 'kick hat clap perc bass chords lead arp fill'), ('Strofa 2', 16, 'kick hat clap perc bass chords leadl'),
          ('Bridge', 8, 'bass chords'), ('Assolo', 8, 'kick hat clap bass chords lead'), ('Finale', 16, 'kick hat clap open perc bass chords arp lead fill')],
 'r&b': [('Intro', 8, 'pad chordsl'), ('Strofa 1', 16, 'kick hat clap bass chords leadl'), ('Pre-chorus', 8, 'kick hat clap bass pad rolls'),
         ('Ritornello', 12, 'kick hat clap open perc bass pad chords arp lead'), ('Strofa 2', 16, 'kick hat clap perc bass chords leadl arpl'),
         ('Ritornello 2', 12, 'kick hat clap open perc bass pad chords arp lead'), ('Bridge', 8, 'pad chordsl bassl'),
         ('Ritornello finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
 'soul': [('Intro', 4, 'kick hat clap bass chords'), ('Strofa 1', 16, 'kick hat clap bass chords leadl arpl'), ('Pre-chorus', 8, 'kick hat clap bass chords arp rolls'),
          ('Ritornello', 12, 'kick hat clap perc bass pad chords arp lead'), ('Strofa 2', 16, 'kick hat clap perc bass chords leadl arpl'),
          ('Ritornello 2', 12, 'kick hat clap perc bass pad chords arp lead'), ('Bridge / Vamp', 12, 'kick hat clap bass pad chords arp'),
          ('Finale', 16, 'kick hat clap perc bass pad chords arp lead fill')],
 'synthpop': [('Intro', 8, 'kick hat leadl arpl'), ('Verse 1', 8, 'kick hat clap bass arp leadl'), ('Chorus', 16, 'kick hat clap open perc bass chords arp lead fill'),
              ('Verse 2', 16, 'kick hat clap bass arp leadl chordsl'), ('Chorus 2', 8, 'kick hat clap open perc bass chords arp lead fill'),
              ('Bridge', 8, 'pad chordsl bassl'), ('Chorus finale', 8, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 8, 'kick hat bass')],
 # Famiglia 3: generi sperimentali e d'avanguardia
 'ambient': [('Fade in', 32, 'pad'), ('Evoluzione 1', 32, 'pad chordsl'), ('Trasformazione', 32, 'chordsl leadl'), ('Sovrapposizione', 32, 'pad chordsl arp leadl'),
             ('Fade out', 32, 'pad')],
 'breakcore': [('Intro', 8, 'hat perc arpl leadl'), ('Sezione A', 16, 'kick hat clap perc bass fill'), ('Sezione B', 8, 'kick hat clap perc bass arpl fill'),
               ('Transizione', 8, 'hat clap perc bass rolls'), ('Sezione C', 16, 'kick hat clap perc bass arp lead fill'),
               ('Finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
 'drone': [('Tono fondamentale', 32, 'pad'), ('Armoniche', 32, 'pad chordsl'), ('Morphing', 32, 'pad bass chordsl'), ('Dissolvenza', 32, 'pad')],
 'glitch': [('Intro', 8, 'hat arpl'), ('Beat', 8, 'kick hat clap perc fill'), ('Evoluzione', 16, 'kick hat clap perc bass arp'), ('Breakdown', 8, 'pad arpl'),
            ('Ritorno', 16, 'kick hat clap perc bass arp lead fill')],
 'idm': [('Intro', 8, 'pad arpl'), ('Sezione 1', 8, 'kick hat clap perc'), ('Sezione 2', 16, 'kick hat clap perc bass arp lead'), ('Breakdown', 8, 'pad arpl'),
         ('Sezione 3', 16, 'kick hat clap perc bass arp lead fill')],
 'lowercase': [('Silenzio', 8, ''), ('Evento 1', 1, 'event'), ('Silenzio 2', 15, ''), ('Eventi ravvicinati', 2, 'event'), ('Silenzio 3', 22, ''), ('Evento 2', 2, 'event')],
 'microsound': [('Nube 1', 16, 'arpl'), ('Aumento densita', 16, 'arp'), ('Nube 2', 16, 'arp lead'), ('Dissolvenza', 16, 'arpl')],
 'minimal': [('Cellula 1', 16, 'kick hat bass'), ('Cellula 2', 16, 'kick hat bass arpl'), ('Addizione', 16, 'kick hat clap bass arp'),
             ('Sottrazione', 16, 'kick hat bass arpl'), ('Ritorno', 16, 'kick hat clap bass arp')],
 'minimalismo_ritmico': [('Pattern 1', 15, 'kick hat'), ('Pattern 2', 15, 'kick hat perc bass'), ('Pattern 3', 15, 'kick hat clap perc bass arpl'),
                         ('Trasformazione', 15, 'kick hat clap perc bass arp lead'), ('Dissoluzione', 15, 'kick hat bass arpl')],
 'noise': [('Texture 1', 16, 'pad'), ('Texture 2', 16, 'pad bass arpl'), ('Muro di rumore', 16, 'pad bass arp lead'), ('Silenzio', 8, ''), ('Texture 3', 16, 'pad arpl')],
 'onkyo': [('Silenzio', 8, ''), ('Gesto 1', 1, 'event'), ('Silenzio 2', 11, ''), ('Gesto 2 + risposta', 2, 'event'), ('Silenzio 3', 18, ''), ('Dialogo', 4, 'event arpl')],
 'sperimentale': [('Processo 1', 8, 'hat arpl'), ('Processo 2', 8, 'kick clap bass arpl'), ('Processo 3', 8, 'hat perc bass arp lead'), ('Dissoluzione', 8, 'arpl')],
 'underground': [('Intro', 8, 'pad leadl bassl'), ('Beat drill', 8, 'kick hat clap bass'), ('Strofa 1', 16, 'kick hat clap bass pad leadl'),
                 ('Hook', 8, 'kick hat clap perc bass pad chords lead arp'), ('Strofa 2', 16, 'kick hat clap perc bass pad leadl'),
                 ('Hook 2', 8, 'kick hat clap perc bass pad chords lead arp fill'), ('Bridge', 8, 'pad chordsl bassl'),
                 ('Hook finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
 # Famiglia 4: noise e glitch (approfondimento)
 'harsh_noise': [('Wall 1', 16, 'pad arp'), ('Wall 2', 16, 'pad bass arp lead'), ('Blocco dinamico', 16, 'bass lead'), ('Wall finale', 16, 'pad bass arp lead chords')],
 'industrial': [('Intro', 16, 'kick hat arpl'), ('Verse', 16, 'kick hat clap bass'), ('Chorus', 16, 'kick hat clap open perc bass chords lead arp'),
                ('Bridge', 16, 'pad bassl'), ('Finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
 'armonico': [('Intro armonica', 8, 'pad chordsl'), ('Sezione A', 16, 'kick hat clap bass chords leadl'), ("Sezione A'", 8, 'kick hat clap bass pad chords lead arpl'),
              ('Sezione B', 16, 'kick hat clap bass chords lead arp'), ('Bridge / modulazione', 8, 'pad chordsl leadl'),
              ('Ritorno tema', 16, 'kick hat clap bass pad chords lead arp'), ('Outro', 24, 'pad chordsl')],
 'elettronico': [('Intro', 16, 'kick hat'), ('Build', 16, 'kick hat clap open bass'), ('Main / Drop', 32, 'kick hat clap open perc bass pad chords lead'),
                 ('Breakdown', 16, 'pad chordsl'), ('Build 2', 16, 'hat pad chords arp roll'),
                 ('Drop 2', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'kick hat bass')],
}

def _parse_timeline(rows):
    out = []
    for name, bars, layers in rows:
        ls = frozenset(layers.split())
        assert ls <= LAYER_TOKENS, (name, ls - LAYER_TOKENS)
        assert bars > 0, (name, bars)
        out.append((name, bars, ls))
    return out

assert set(TIMELINES) == set(GENRES), set(TIMELINES) ^ set(GENRES)
for _k, _v in GENRES.items():
    _tl = _parse_timeline(TIMELINES[_k])
    _v['timeline'] = _tl
    _v['bars_default'] = sum(b for _n, b, _l in _tl)

# Stile armonico e di basso per genere: probabilita' di accordi di settima / nona (per brano) e carattere del basso.
#   acid: accenti, slide (note legate) e salti d'ottava | octave: ottave alternate (disco) | long: sub 808 lungo (trap)
#   reese: note sostenute + seconda traccia leggermente scordata (pitch bend) con filtro che si muove (DnB)
#   rolling: basso fisso sulla tonica tra i kick (techno) | offbeat: basso sui levare (trance) | sync: sincopato (deep)
GENRE_STYLE = {
    'deep': dict(seventh=1.0, ninth=0.6, bass_style='sync'), 'dub_techno': dict(seventh=0.9, ninth=0.2), 'r&b': dict(seventh=0.95, ninth=0.5),
    'soul': dict(seventh=0.95, ninth=0.5), 'funk': dict(seventh=0.9, ninth=0.3), 'disco': dict(seventh=0.8, ninth=0.2, bass_style='octave'),
    'armonico': dict(seventh=0.8, ninth=0.4), 'hip_hop': dict(seventh=0.6, ninth=0.2), 'synthpop': dict(seventh=0.15), 'trance': dict(seventh=0.0, bass_style='offbeat'),
    'techno': dict(seventh=0.1, bass_style='rolling'), 'edm_2000s': dict(seventh=0.0), 'minimal_techno': dict(seventh=0.2), 'acid': dict(seventh=0.5, bass_style='acid'),
    'trap': dict(seventh=0.3, bass_style='long'), 'drum_n_bass': dict(seventh=0.4, bass_style='reese'), 'reggaeton': dict(seventh=0.3), 'elettronico': dict(seventh=0.35), 'commerciale_90s': dict(seventh=0.3),
}
for _k, _s in GENRE_STYLE.items(): GENRES[_k].update(_s)
#   funk: slap/pop (ottave staccate e ghost) | walk: giro sulle note dell'accordo | arp: arpeggio | dubsub: sub sostenuto solo sulla tonica
STYLE_EXTRA = {'funk': dict(bass_style='funk'), 'soul': dict(bass_style='walk'), 'armonico': dict(bass_style='walk'), 'synthpop': dict(bass_style='arp'),
               'r&b': dict(bass_style='long'), 'hip_hop': dict(bass_style='long'), 'reggaeton': dict(bass_style='long'), 'dub_techno': dict(bass_style='dubsub'),
               'industrial': dict(seventh=0.1, bass_style='rolling'), 'edm_2000s': dict(bass_style='offbeat')}
for _k, _s in STYLE_EXTRA.items(): GENRES[_k].update(_s)
BASS_ROOT_P = {'rolling': 0.97, 'offbeat': 0.92, 'acid': 0.7, 'octave': 0.9, 'long': 0.85, 'reese': 0.9, 'dubsub': 0.98, 'funk': 0.8}

def _bass_pc(style, hit, cpcs, rpc, root_p):
    """Nota (classe di altezza) del basso: arp = arpeggio sull'accordo (synthpop), walk = giro sulle note dell'accordo (soul, armonico)."""
    if style == 'arp': return cpcs[(0, 2, 0, 1)[hit % 4] % len(cpcs)]
    if style == 'walk': return cpcs[(0, 1, 2, 1)[hit % 4] % len(cpcs)]
    return rpc if random.random() < root_p else random.choice(cpcs[1:])

def _bass_shape(style, hit, gap, room):
    """(ottava extra, durata in step, velocity extra) per una nota di basso secondo lo stile del genere."""
    if style == 'acid':
        return (12 if random.random() < 0.2 else 0), (gap + 1 if random.random() < 0.35 else gap), (22 if random.random() < 0.3 else 0)
    if style == 'octave': return (12 if hit % 2 else 0), gap, 0
    if style == 'long': return (12 if random.random() < 0.12 else 0), min(gap * 2, room), 0
    if style in ('reese', 'dubsub'): return 0, min(gap * 2, room), 0          # note lunghe e sostenute
    if style == 'funk':                                             # slap/pop: ottave staccate e note fantasma
        r = random.random()
        if r < 0.25: return 12, 1, 12
        if r < 0.45: return 0, 1, -38
        return 0, gap, 0
    return 0, gap, 0


DEFAULT_TIMELINE = _parse_timeline([
    ('Intro', 8, 'kick hat'), ('Break', 8, 'kick hat pad chordsl arpl bassl'), ('Build-up', 8, 'kick hat clap bass pad chords arp roll'),
    ('Drop', 24, 'kick hat clap open perc bass pad chords arp lead fill'), ('Break 2', 8, 'kick hat pad chordsl leadl bassl'), ('Outro', 8, 'kick hat')])

def timeline_unit(tl):
    """Le sezioni si allocano a blocchi di 4 battute; se la timeline ha sezioni non multiple di 4 (silenzi, eventi singoli) a battuta singola."""
    return 4 if all(b % 4 == 0 for _n, b, _l in (tl or DEFAULT_TIMELINE)) else 1

LAYER_ORDER = ['kick', 'hat', 'clap', 'open', 'perc', 'bass', 'bassl', 'pad', 'chords', 'chordsl', 'arp', 'arpl', 'lead', 'leadl', 'roll', 'rolls', 'fill', 'event']

def timeline_table(timeline):
    """Righe: sezioni; colonne: battute e strati attivi (per l'anteprima nell'app)."""
    cols = [t for t in LAYER_ORDER if any(t in ls for _n, _b, ls in timeline)]
    rows, pos = [], 0
    for n, b, ls in timeline:
        rows.append({'Sezione': n, 'Battute': f"{pos + 1}-{pos + b}", **{t: ('●' if t in ls else '') for t in cols}})
        pos += b
    return rows

def timelines_to_json():
    """Le timeline attuali di tutti i generi in JSON modificabile: {genere: [[nome, battute, "strati"], ...]}."""
    data = {k: [[n, b, ' '.join(t for t in LAYER_ORDER if t in ls)] for n, b, ls in v['timeline']] for k, v in sorted(GENRES.items())}
    return json.dumps(data, ensure_ascii=False, indent=1)

def apply_timelines(data):
    """Applica timeline personalizzate (anche solo di alcuni generi). Solleva ValueError con un messaggio chiaro se qualcosa non va."""
    if not isinstance(data, dict): raise ValueError("il JSON deve essere un oggetto {genere: [[nome, battute, strati], ...]}")
    parsed = {}
    for k, rows in data.items():
        if k not in GENRES: raise ValueError(f"genere sconosciuto: {k}")
        if not isinstance(rows, list) or not rows: raise ValueError(f"{k}: serve una lista di sezioni")
        try: parsed[k] = _parse_timeline([(str(r[0]), int(r[1]), str(r[2])) for r in rows])
        except (AssertionError, IndexError, TypeError, ValueError) as e: raise ValueError(f"{k}: sezione non valida ({e})")
    for k, tl in parsed.items():
        GENRES[k]['timeline'] = tl
        GENRES[k]['bars_default'] = sum(b for _n, b, _l in tl)
    return len(parsed)

TIMELINE_FILE_MSG = ''
try:
    from pathlib import Path
    _tlp = Path(__file__).with_name('midi_forge_timelines.json')
    if _tlp.exists():
        TIMELINE_FILE_MSG = f"Timeline personalizzate caricate da {_tlp.name} ({apply_timelines(json.loads(_tlp.read_text(encoding='utf-8')))} generi)"
except NameError: pass
except Exception as _e: TIMELINE_FILE_MSG = f"midi_forge_timelines.json ignorato: {_e}"

def min_bars(g):
    tl = g.get('timeline') or DEFAULT_TIMELINE
    return timeline_unit(tl) * len(tl)

def compute_structure(bars, timeline=None, seed=None):
    """Distribuisce le battute sulle sezioni della timeline del genere (multipli di 4, o di 1 se la timeline ha eventi singoli). A durata di default si ottengono
    esattamente le lunghezze della timeline; con altre durate le sezioni scalano in proporzione. Con un seed le sezioni
    centrali variano (+-20% circa). Ritorna (battute, [(nome, inizio, lunghezza, strati)])."""
    tl = timeline or DEFAULT_TIMELINE
    n = len(tl)
    unit = timeline_unit(tl)
    bars = max(unit * n, (int(bars) // unit) * unit)
    units = bars // unit
    w = [float(b) for _n, b, _l in tl]
    if seed is not None:
        rs = random.Random(int(seed) * 31 + 7)
        for i in range(1, n - 1): w[i] *= rs.uniform(0.8, 1.25)
    tot, alloc = sum(w), [1] * n
    for _ in range(units - n):
        k = max(range(n), key=lambda i: w[i] / tot * units - alloc[i])
        alloc[k] += 1
    sections, pos = [], 0
    for (name, _b, layers), a in zip(tl, alloc):
        sections.append((name, pos, a * unit, layers)); pos += a * unit
    return bars, sections

# ================= METRI (battuta = N sedicesimi raggruppati) =================
# chiave -> ((numeratore, denominatore) MIDI, raggruppamento in sedicesimi). Il pattern a 16 step del genere viene
# "piegato" sul raggruppamento: ogni gruppo prende i 4 step di un battito del 4/4 (+ i primi step del battito dopo).
METERS = {
    '4/4':   ((4, 4),   [4, 4, 4, 4]),
    '5/16':  ((5, 16),  [3, 2]),
    '7/16':  ((7, 16),  [4, 3]),
    '7/8':   ((7, 8),   [4, 4, 6]),
    '9/8':   ((9, 8),   [4, 4, 4, 6]),
    '11/8':  ((11, 8),  [6, 6, 6, 4]),
    '13/8':  ((13, 8),  [6, 6, 6, 4, 4]),
    '15/8':  ((15, 8),  [6, 6, 6, 6, 6]),
    '17/8':  ((17, 8),  [6, 6, 6, 6, 10]),     # 3+3+3+3+5 (ottavi)
    '29/16': ((29, 16), [5, 6, 6, 6, 6]),
}

def plan_meter(g, bars, odd=True):
    """Una voce per battuta: start (tick), L (sedicesimi), idx (step -> indice nel pattern a 16), gstarts, ends, sig, key.
    odd=False forza il 4/4 (usato quando si riarrangia un MIDI esistente, che e' in 4/4)."""
    keys = g.get('meter', ['4/4']) if odd else ['4/4']
    q, plan, pos = TICKS_BEAT // 4, [], 0
    for b in range(bars):
        key = keys[b % len(keys)]
        sig, groups = METERS[key]
        idx, gstarts, ends, c = [], [], [], 0
        for gi, gs in enumerate(groups):
            gstarts.append(c)
            idx += [(gi * 4 + j) % 16 for j in range(gs)]
            c += gs; ends.append(c)
        plan.append({'start': pos, 'L': c, 'idx': idx, 'gstarts': gstarts, 'ends': ends, 'sig': sig, 'key': key})
        pos += c * q
    return plan

def uses_odd_meter(mode, submode, has_notes):
    """Metri dispari solo dove la musica e' generata: non nel Remix (extract) ne' in Faithful, che seguono le battute del MIDI originale (4/4)."""
    if mode == 'minimal': return not (submode == 'extract' and has_notes)
    return submode == 'generative'

def avg_bar_sixteenths(g, odd=True):
    keys = g.get('meter', ['4/4']) if odd else ['4/4']
    return sum(sum(METERS[k][1]) for k in keys) / len(keys)

for _k, _v in GENRES.items(): _v['_name'] = _k

def legacy_name(layers, seen_drop):
    """Nome 'storico' della sezione (usato da Faithful): intro/outro = senza strati melodici."""
    if not (layers & MELODIC): return 'outro' if seen_drop else 'intro'
    if layers & {'roll', 'rolls'}: return 'build'
    if 'clap' in layers and 'kick' in layers: return 'drop'
    return 'break2' if seen_drop else 'break1'

def section_map(sections, bars):
    """Per ogni battuta: dict con sec (nome storico), idx (indice nella sezione), length, layers, prev (strati della sezione prima), label."""
    out, prev, seen = [], frozenset(), False
    for label, _s, length, layers in sections:
        sec = legacy_name(layers, seen)
        if sec == 'drop': seen = True
        for i in range(length):
            out.append({'sec': sec, 'idx': i, 'length': length, 'layers': layers, 'prev': prev, 'label': label})
        prev = layers
    return out[:bars]

def _fade(B, fam):
    """Ingresso morbido: uno strato che entra sale di volume in 4 battute."""
    if fam in {FAMILY[t] for t in B['prev'] if t in FAMILY}: return 1.0
    return min(1.0, 0.5 + 0.5 * (B['idx'] + 1) / min(4, B['length']))

def _structure_line(bars, timeline=None, seed=None):
    _, sections = compute_structure(bars, timeline, seed)
    return "   " + " -> ".join(f"[ {n} {l} ]" for n, _s, l, _ls in sections)

def _structure_report(bars, timeline=None, seed=None):
    _, sections = compute_structure(bars, timeline, seed)
    lines, prev = [], frozenset()
    for n, s, l, ls in sections:
        ins, outs = sorted(ls - prev), sorted(prev - ls)
        lines.append(f"   {s + 1:>3}-{s + l:<3} {n:<18} " + (f"entrano: {' '.join(ins)}" if ins else "entrano: -") + (f" | escono: {' '.join(outs)}" if outs else ""))
        prev = ls
    return lines

def is_drumless(g):
    return not (any(g['kick']) or any(g['hat']) or any(g.get('snare', [0] * 16)))

def eff_section(name, drumless):
    # generi senza batteria (ambient, drone...): intro/outro suonano pad/arp invece del solo drum
    return 'break1' if drumless and name in ('intro', 'outro') else name

def _note(ev, tick, dur, pitch, vel, ch):
    pitch = max(0, min(127, int(pitch)))
    ev.append({'tick': int(tick), 'type': 'on', 'pitch': pitch, 'vel': max(1, min(127, int(vel))), 'channel': ch})
    ev.append({'tick': int(tick + max(1, int(dur))), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': ch})

def _question(motif, n):
    """Frase 'domanda': l'ultima nota resta lontana dalla tonica."""
    q = list(motif); idx = [i for i, v in enumerate(q) if v is not None]
    if idx and q[idx[-1]] == 0: q[idx[-1]] = random.choice([2, 4]) % n
    return q

def _answer(motif):
    """Frase 'risposta': contorno discendente nella seconda meta' e chiusura sulla tonica."""
    a = list(motif); idx = [i for i, v in enumerate(a) if v is not None]
    if idx:
        for i in idx[len(idx) // 2:]: a[i] = max(0, a[i] - random.choice([1, 2]))
        a[idx[-1]] = 0
    return a

def _thin(motif, p=0.25):
    return [None if (v is not None and random.random() < p) else v for v in motif]

def _gaps(steps, size=16, cap=4):
    steps = sorted(steps)
    out = {}
    for i, s in enumerate(steps):
        gap = (steps[(i + 1) % len(steps)] - s) % size or size
        out[s] = min(gap, cap)
    return out

def _pc_pitch(pc, lo):
    return lo + ((pc - lo) % 12)

def _bass_pitch(pc, lo=28, hi=45):
    p = _pc_pitch(pc, lo)
    return p if p <= hi else p - 12

def _fold(p, lo=60, hi=83):
    while p < lo: p += 12
    while p > hi: p -= 12
    return p

# ================= BATTERIA (condivisa) =================

# ================= VARIAZIONE COL SEED =================
# Ogni genere ha un'identita' (ancore: kick sul battere, backbeat, dembow...) e il seed sposta/aggiunge/toglie il resto,
# cosi' due brani dello stesso genere hanno batteria, basso e armonia diversi.
BPM_RANGES = {
    'acid': [(135, 150)], 'ambient': [(60, 90)], 'armonico': [(60, 120)], 'breakcore': [(170, 230)],
    'commerciale_90s': [(105, 128)], 'deep': [(118, 126)], 'disco': [(110, 130)], 'drone': [(60, 100)],
    'drum_n_bass': [(160, 180)], 'dub_techno': [(112, 130)], 'edm_2000s': [(126, 130)], 'elettronico': [(95, 140)],
    'funk': [(95, 120)], 'glitch': [(80, 115), (128, 148)], 'harsh_noise': [(60, 120)], 'hip_hop': [(85, 95)],
    'idm': [(100, 140)], 'industrial': [(110, 140)], 'lowercase': [(104, 162)], 'microsound': [(80, 100)],
    'minimal': [(110, 130)], 'minimal_techno': [(125, 132)], 'minimalismo_ritmico': [(100, 130)], 'noise': [(60, 154)],
    'onkyo': [(50, 90)], 'r&b': [(60, 110)], 'reggaeton': [(90, 100)], 'sperimentale': [(88, 132)], 'soul': [(60, 110)],
    'synthpop': [(111, 127)], 'techno': [(125, 135)], 'trap': [(130, 150)], 'trance': [(120, 150)], 'underground': [(72, 150)],
}
LOOSE_SNARE = {'breakcore', 'idm', 'sperimentale', 'glitch', 'minimalismo_ritmico'}   # snare non vincolato al backbeat
FIXED_KICK = {'reggaeton'}                                                           # il kick e' identita' del genere

def seeded_bpm(name, g, seed):
    rs = random.Random(int(seed) * 17 + 3)
    lo, hi = rs.choice(BPM_RANGES.get(name, [(g['bpm_default'], g['bpm_default'])]))
    return rs.randint(lo, hi)

def _mutate(pat, rs, anchors, cand, p_move, p_del, p_add, max_add):
    out = list(pat)
    for s in range(16):
        if out[s] and s not in anchors:
            r = rs.random()
            if r < p_del: out[s] = 0
            elif r < p_del + p_move:
                t = (s + rs.choice([-2, -1, 1, 2])) % 16
                if not out[t]: out[s], out[t] = 0, out[s]
    adds = 0
    for s in rs.sample(cand, len(cand)):
        if adds >= max_add: break
        if not out[s] and s not in anchors and rs.random() < p_add: out[s] = 1; adds += 1
    return out

def _vary_hat(hat, rs, groove, amount):
    out = list(hat)
    for s in range(16):
        if out[s]:
            r = rs.random()
            if s % 4 and r < amount * 0.6: out[s] = 0
            elif r < amount: out[s] = rs.choice([1, 2, 3])
        elif groove and rs.random() < amount * 0.35: out[s] = 3
    return out

# ================= LIBRERIA DI PATTERN PER GENERE =================
# Pattern reali a 16 step (x = colpo, X = accento, g = ghost, - = vuoto). Il seed sceglie una variante per kick / hat / basso
# (poi le mutazioni di vary_genre la rifiniscono). Dove il kick e' l'identita' del genere (four-on-the-floor, reggaeton) non c'e' la variante.
def _pat(s, binary=False):
    m = {'x': 1, 'X': 2, 'g': 3, '-': 0, '.': 0}
    out = [m[c] for c in s if c in m]
    assert len(out) == 16, s
    return [1 if v else 0 for v in out] if binary else out

PATTERN_LIB = {
 'acid': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxXx xxXx xxXx xxXx', '-x-X -x-X -x-X -x-X', 'x-X- x-X- x-X- x-X-', 'xgXg xgXg xgXg xgXg'],
          'bass': ['x-xx -x-x x-x- xx-x', 'x-x- xx-x x-xx -x-x', 'xx-x -xx- x-x- xx-x', 'x--x -x-x x-xx -x--']},
 'breakcore': {'kick': ['x--- --x- -x-- x-x-', 'x-x- --x- ---x x--x', 'x--x --x- x--- -x-x', 'x-x- x--- -x-x --x-'],
               'hat': ['xxxx xxxx xxxx xxxx', 'xgxx xgxx xgxx xgxx', 'x-xx -xx- xx-x x-xx'], 'bass': ['x--- x--- -x-- x-x-', 'x-x- --x- x--x -x--']},
 'commerciale_90s': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-'],
                     'bass': ['x-x- x-x- x-x- x-x-', 'x--x --x- x--x --x-', 'x-xx -x-x x-xx -x-x']},
 'deep': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--x ---- x---'], 'hat': ['x-X- x-X- x-X- x-X-', 'xgXg xgXg xgXg xgXg', 'x-Xg x-Xg x-Xg x-Xg'],
          'bass': ['x--- --x- ---- --x-', 'x--x --x- --x- -x--', 'x-x- ---x --x- x---', 'x--- -x-- --x- x--x']},
 'disco': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--- ---x x---'], 'hat': ['xxXx xxXx xxXx xxXx', 'x-X- x-X- x-X- x-X-', 'xgXg xgXg xgXg xgXg'],
           'bass': ['x-xx -xx- x-xx -xx-', 'x--x x-x- x--x x-x-', 'xx-x xx-x xx-x xx-x', 'x-x- xx-x x-x- xx-x']},
 'drum_n_bass': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--x ---- x---'], 'kick': ['x--- ---- --x- ----', 'x--- --x- --x- ----', 'x--- ---- --x- --x-', 'x--x ---- --x- ----'],
                 'hat': ['xxxx xxxx xxxx xxxx', 'xgxg xgxg xgxg xgxg', 'x-xx x-xx x-xx x-xx'],
                 'bass': ['x--- ---x --x- ----', 'x--x ---- x--- --x-', 'x--- --x- ---x ----', 'x-x- ---- --x- x---']},
 'dub_techno': {'clap': ['---- x--- ---- x---', '---- ---- ---- x---', '---- x--- ---- ----'], 'hat': ['--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-', '--X- ---- --X- ----'],
                'bass': ['x--- ---- x--- ----', 'x--- ---x ---- x---', 'x--- ---- x--x ----', 'x--- --x- ---- ----']},
 'edm_2000s': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-'],
               'bass': ['--x- --x- --x- --x-', 'x-x- x-x- x-x- x-x-', '-xx- -xx- -xx- -xx-', 'xxxx xxxx xxxx xxxx']},
 'elettronico': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-'],
                 'bass': ['x--x --x- x--x --x-', 'x-x- x-x- x-x- x-x-', 'x--- x--- x--x -x--']},
 'funk': {'snare': ['---- x--- ---- x---', '---- x--x ---- x---', '---- x--- ---x x---', '---- x--- ---- x-x-'], 'kick': ['x--x ---- x-x- ----', 'x--- --x- x--x ----', 'x-x- --x- x--- -x--', 'x--x -x-- x-x- ----'],
          'hat': ['Xxxx Xxxx Xxxx Xxxx', 'xgxg xgxg xgxg xgxg', 'Xxgx Xxgx Xxgx Xxgx'],
          'bass': ['x--x -x-x x--- x-x-', 'x-x- -x-x x--x --x-', 'x--x x--- x-x- -x--', 'x-xx --x- x--x -x--']},
 'glitch': {'snare': ['---- ---- x--- ----', 'x--- ---- x--- ----', '---- ---- x--- --x-'], 'kick': ['x--- ---- x--- ----', 'x--- ---x x--- ----', 'x--- ---- x-x- ----'],
            'hat': ['xxxx xxxx xxxx xxxx', 'x-xx -xx- x-xx -xxx', 'xgxx xgxg xxgx xgxx'], 'bass': ['x--- x--- x-x- ----', 'x-x- ---- x--x ----']},
 'hip_hop': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--- --x- x---', '---- x--x ---- x---'], 'kick': ['x--- --x- x--- ----', 'x--- --x- x-x- ----', 'x-x- ---- x--- --x-', 'x--- ---x x--- -x--'],
             'hat': ['xgxg xgxg xgxg xgxg', 'x-x- x-x- x-x- x-x-', 'xgx- xgxg xgx- xgxx'],
             'bass': ['x--- --x- x--- --x-', 'x--- ---x x--x ----', 'x-x- --x- x--- -x--']},
 'idm': {'kick': ['x--x -x-x ---x --x-', 'x-x- -x-- x--x -x--', 'x--x --x- -x-x x---', 'x-x- --x- x--x --x-'],
         'hat': ['x-xg xgx- gxxg x-xg', 'xxgx -xgx xgxx gx-x', 'x-x- xxg- x-xg -xxx'], 'bass': ['x--x -x-- x-x- -x--', 'x-x- --x- x--x x---']},
 'industrial': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxxx xxxx xxxx xxxx', 'x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx'],
                'bass': ['xxxx xxxx xxxx xxxx', 'x-x- x-x- x-x- x-x-', 'x--x x--x x-x- x-x-']},
 'minimal': {'hat': ['xxxx xxxx xxxx xxxx', 'x-x- x-x- x-x- x-x-', 'x-xg x-xg x-xg x-xg'],
             'bass': ['x--- ---- x--- ----', 'x--x ---- x--- -x--', 'x-x- ---- x--- ----']},
 'minimal_techno': {'hat': ['xxxx xxxx xxxx xxxx', 'x-xx x-xx x-xx x-xx', 'xgxx xgxx xgxx xgxx', 'x-X- x-X- x-X- x-X-'],
                    'bass': ['x--x --x- --x- x---', 'x--- x--- --x- ----', 'x-x- ---x --x- ----', 'x--- --x- x--- ---x']},
 'minimalismo_ritmico': {'kick': ['x--x --x- --x- x---', 'x--- x--x --x- --x-', 'x-x- --x- x--- x-x-'],
                         'hat': ['xxxx xxxx xxxx xxxx', 'x-x- xx-x x-x- xx-x'], 'bass': ['x--x --x- --x- x---', 'x-x- x--x --x- ----']},
 'r&b': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--- --x- x---'], 'kick': ['x--- --x- x--- ----', 'x--- --x- x--- -x--', 'x--- ---x x--- --x-', 'x-x- ---- x--- --x-'],
         'hat': ['xgxg xgxg xgxg xgxg', 'xgXg xgxg xgXg xgxg', 'x-xg x-xg x-xg x-xx'],
         'bass': ['x--- --x- x--- --x-', 'x--- ---x --x- x---', 'x-x- --x- x--- ----']},
 'reggaeton': {'hat': ['x-x- x-x- x-x- x-x-', '--x- --x- --x- --x-', 'x-xx x-xx x-xx x-xx', 'x-x- x-xx x-x- x-xx'],
               'bass': ['x--x --x- x--- ----', 'x--x --x- x--x --x-', 'x--- --x- x--x ----']},
 'sperimentale': {'kick': ['x--- ---x --x- ----', 'x-x- --x- ---- x---', 'x--x ---- -x-- x---'],
                  'hat': ['x-x- -xx- x--x -x--', 'xxxx ---- xxxx ----', 'x-xx -x-x x-x- xx--'], 'bass': ['x--- x--x ---x ----', 'x-x- ---- x--x -x--']},
 'soul': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'kick': ['x--- ---- x--- ----', 'x--- --x- x--- ----', 'x--- ---- x--- -x--'],
          'hat': ['xgxg xgxg xgxg xgxg', 'x-x- x-x- x-x- x-x-', 'xgx- xgx- xgx- xgxg'],
          'bass': ['x--- ---- x--- --x-', 'x--- --x- x--- ----', 'x-x- ---- x--- --x-']},
 'synthpop': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx', 'x-x- x-x- x-x- x-x-'],
              'bass': ['x-x- x-x- x-x- x-x-', 'xxxx xxxx xxxx xxxx', 'x--x x--x x--x x--x']},
 'techno': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- ---- ---- x---'], 'hat': ['xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-', '-xXx -xXx -xXx -xXx'],
            'bass': ['-xxx -xxx -xxx -xxx', '-x-x -x-x -x-x -x-x', '-xx- -xx- -xx- -xx-', '-xxx -x-x -xxx -x-x']},
 'trance': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-'],
            'bass': ['--x- --x- --x- --x-', '-xx- -xx- -xx- -xx-', '--x- --xx --x- --xx', '-x-x -x-x -x-x -x-x']},
 'trap': {'kick': ['x--- --x- ---- ----', 'x--- --x- --x- ----', 'x--x ---- --x- ----', 'x--- ---- -x-- x---'],
          'hat': ['xxxx xxxx xxxx xxxx', 'x-xx x-xx xxxx x-xx', 'xxgx xxgx xxxg xxgx'],
          'bass': ['x--- ---- ---- ----', 'x--- --x- ---- ----', 'x--- ---- --x- ----', 'x--x ---- --x- ----']},
 'underground': {'kick': ['x--- ---- x--- ----', 'x--- ---x x--- ----', 'x--- --x- x--- ----'],
                 'hat': ['x--x --x- x--x --x-', 'x--x --x- x--x --xx', 'x--x -xx- x--x -xx-'],
                 'bass': ['x--x --x- x--x --x-', 'x--x --x- x--x -x--', 'x--x -xx- x--x -xx-']},
 'armonico': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx'], 'bass': ['x--- ---- x--- ----', 'x--- --x- x--- --x-', 'x-x- x-x- x-x- x-x-']},
}
for _g, _d in PATTERN_LIB.items():            # controllo all'avvio: ogni pattern deve avere 16 step
    assert _g in GENRES, _g
    for _k, _vs in _d.items():
        for _s in _vs: _pat(_s)

def vary_genre(g, seed, name=None):
    """Copia del genere con pattern variati in modo deterministico dal seed (+ 'alt': variante B per le frasi pari)."""
    g2 = dict(g)
    rs = random.Random(int(seed) * 7919 + 11)
    kick, bass = list(g['kick']), list(g['bass'])
    lib = PATTERN_LIB.get(name or g.get('_name'), {})
    if lib.get('kick'): kick = _pat(rs.choice(lib['kick']), True)
    if lib.get('bass'): bass = _pat(rs.choice(lib['bass']), True)
    hat_src = _pat(rs.choice(lib['hat'])) if lib.get('hat') else list(g['hat'])
    four = all(kick[i] for i in (0, 4, 8, 12))
    groove = not four
    if any(kick):
        if not four and name not in FIXED_KICK:
            kick = _mutate(kick, rs, {0}, [3, 6, 7, 10, 11, 14, 15], 0.35, 0.12, 0.4, 2)
    snare, clap = list(g.get('snare', [0] * 16)), list(g.get('clap', [0] * 16))
    if lib.get('snare'): snare = _pat(rs.choice(lib['snare']), True)
    if lib.get('clap'): clap = _pat(rs.choice(lib['clap']), True)
    if any(snare) and name in LOOSE_SNARE:
        snare = _mutate(snare, rs, {s for s in range(0, 16, 4) if snare[s]}, [2, 3, 6, 7, 10, 11, 14, 15], 0.3, 0.1, 0.3, 2)
    ghost = list(g.get('ghost', [0] * 16))
    if any(ghost):
        cand = [s for s in range(16) if s % 4 and not snare[s]]
        ghost = [0] * 16
        for s in rs.sample(cand, rs.randint(2, min(5, len(cand)))): ghost[s] = 1
    if any(bass):
        bass = _mutate(bass, rs, {0}, [2, 3, 6, 7, 10, 11, 14, 15], 0.15 if four else 0.3, 0.1 if four else 0.15, 0.2 if four else 0.35, 1 if four else 2)
    hat = _vary_hat(hat_src, rs, groove, 0.10 if four else 0.2) if any(g['hat']) else list(g['hat'])
    g2.update(kick=kick, snare=snare, clap=clap, ghost=ghost, bass=bass, hat=hat)
    # linea di percussioni del seed (rimshot / claves / shaker / tamburello / cowbell) sui levare, solo nel drop
    taken = {s for s in range(16) if kick[s] or snare[s]}
    cand = [s for s in (2, 3, 6, 7, 10, 11, 14, 15) if s not in taken]
    def _perc():
        out = [0] * 16
        for s in rs.sample(cand, min(len(cand), rs.randint(2, 4))): out[s] = 1
        return out
    perc = _perc() if any(kick) or any(g['hat']) else [0] * 16
    g2['perc'], g2['perc_note'] = perc, rs.choice([GM_RIMSHOT, 75, 70, 54, 56])
    if g.get('swing'): g2['swing'] = round(g['swing'] * rs.uniform(0.7, 1.3), 3)
    g2['arp_density'] = min(0.95, g['arp_density'] * rs.uniform(0.8, 1.25))
    # variante B (usata nella seconda meta' di ogni frase di 8 battute del drop)
    alt = {'kick': kick, 'snare': snare, 'clap': clap, 'ghost': ghost, 'hat': hat, 'perc': _perc() if any(perc) else perc}
    if any(kick) and not four and name not in FIXED_KICK:
        alt['kick'] = _mutate(kick, rs, {0}, [3, 6, 7, 10, 11, 14, 15], 0.2, 0.08, 0.35, 1)
    if any(hat): alt['hat'] = _vary_hat(hat, rs, groove, 0.14)
    g2['alt'] = alt
    return g2

# ================= TRANSIZIONI (crash, reverse, pausa prima del drop, fill di fine sezione) =================
GM_CRASH, GM_REVERSE = 49, 119
TOMS = (50, 48, 47, 45)
# Generi con transizioni "forti" (pausa di un beat + reverse prima del drop); gli altri hanno transizioni morbide (crash leggero, fill piccoli)
BIG_TRANSITIONS = frozenset({'techno', 'trance', 'edm_2000s', 'drum_n_bass', 'acid', 'elettronico', 'commerciale_90s', 'trap', 'breakcore', 'industrial', 'synthpop'})

def _entry_strong(layers, prev):
    """Una sezione 'forte': entra il backbeat (clap) o rientra il kick."""
    return ('clap' in layers and 'clap' not in prev) or ('kick' in layers and 'kick' not in prev and bool(prev))

def _pause_before(nxt_layers, cur):
    """Prima del drop: pausa se la sezione corrente ha la rullata o non ha il kick."""
    return _entry_strong(nxt_layers, cur) and bool((cur & {'roll', 'rolls'}) or 'kick' not in cur)

def _transition_fill(L, big):
    """Fill di fine sezione: [(step, nota, velocity)], scelto a caso (cambia a ogni transizione)."""
    S = GM_SNARE
    t = random.choice(['snare16', 'tom', 'snare8', 'open', 'kicksn'] if big else ['open', 'tom'])
    if t == 'snare16': f = [(L - 4, S, 70), (L - 3, GM_TOM_HIGH, 85), (L - 2, S, 100), (L - 1, GM_TOM_HIGH, 115)]
    elif t == 'tom': f = [(L - 4, TOMS[0], 80), (L - 3, TOMS[1], 88), (L - 2, TOMS[2], 96), (L - 1, TOMS[3], 108)]
    elif t == 'snare8': f = [(L - 8, S, 60), (L - 6, S, 72), (L - 4, S, 84), (L - 2, S, 100), (L - 1, S, 112)]
    elif t == 'open': f = [(L - 2, GM_CLAP, 95), (L - 1, GM_HAT_OPEN, 100)]
    else: f = [(L - 4, GM_KICK, 110), (L - 3, S, 90), (L - 2, GM_KICK, 110), (L - 1, S, 115)]
    return [x for x in f if x[0] >= 0]

def build_drum_events(g, secmap, bm=None):
    """Batteria a strati secondo la timeline del genere: kick, hat, clap (snare+clap sul backbeat), open hat, perc entrano ed escono
    per sezione; fill ogni 8 battute con 'fill'; rullata di snare con 'roll' (ultime 4 battute) o 'rolls' (ultime 2, piano).
    Transizioni (g['transitions'], default attive): crash sui cambi forti, fill diverso a ogni fine sezione e, nei generi 'big',
    reverse cymbal + un beat di pausa prima del drop."""
    if is_drumless(g): return []
    ev, q, R = [], TICKS_BEAT // 4, random.randint
    bm = bm or plan_meter(g, len(secmap), False)
    use_tr = g.get('transitions', True)
    big = g.get('_name') in BIG_TRANSITIONS
    pat_a = {'kick': g['kick'], 'snare': g.get('snare', [0] * 16), 'clap': g.get('clap', [0] * 16), 'ghost': g.get('ghost', [0] * 16), 'hat': g['hat'], 'perc': g.get('perc', [0] * 16)}
    pat_b = g.get('alt') or pat_a
    lazy = int(g.get('lazy', 0) * (TICKS_BEAT // 4))   # snare dietro la griglia (hip hop, R&B, soul)
    for bar, B in enumerate(secmap):
        layers, idx, length, prev = B['layers'], B['idx'], B['length'], B['prev']
        m = bm[bar]; base, L, pi, gst = m['start'], m['L'], m['idx'], set(m['gstarts'])
        nxt = secmap[bar + 1] if bar + 1 < len(secmap) else None
        new_sec = bool(nxt and nxt['idx'] == 0)
        # crash all'inizio di una sezione forte (o quando il kick esce / entrano molti strati insieme)
        if use_tr and idx == 0 and bar > 0:
            strong_in = _entry_strong(layers, prev)
            kick_out = 'kick' in prev and 'kick' not in layers
            if strong_in or (big and (kick_out or len(layers - prev) >= 3)):
                _note(ev, base, TICKS_BEAT * 2, GM_CRASH, (105 if big else 72) - (15 if (kick_out and not strong_in) else 0) + R(0, 8), DRUM_CH)
        # reverse cymbal + pausa di un beat prima del drop
        pause_from = None
        if use_tr and big and new_sec and _pause_before(nxt['layers'], layers) and L >= 8:
            pause_from = L - 4
            sb = bar - 1 if idx >= 1 else bar
            _note(ev, bm[sb]['start'], base + L * q - bm[sb]['start'], GM_REVERSE, 85, DRUM_CH)
        if not (layers & DRUM_LAYERS): continue
        strong = {0, 8} if L == 16 else {0}
        open_steps = {e - 2 for e in m['ends']}
        P = pat_b if ('clap' in layers and idx % 8 >= 4) else pat_a
        roll_any = bool(layers & {'roll', 'rolls'})
        energy = 'clap' in layers or roll_any
        N = min(4 if 'roll' in layers else (2 if 'rolls' in layers else 0), length)
        in_roll = bool(N) and idx >= length - N
        rr = idx - (length - N) if in_roll else 0
        roll_skip = ([4, 2, 2, 1] if N == 4 else [2, 1])[-N:][rr] if in_roll else 0
        roll_amp = 70 if 'roll' in layers else 40
        sn_shift = 4 if g.get('snare_shift') and (idx // 2) % 2 == 1 else 0   # drill: snare dal beat 3 al beat 4 ogni 2 battute
        # fill di fine sezione (diverso a ogni transizione)
        tfill = []
        if use_tr and new_sec and idx == length - 1 and pause_from is None and not in_roll and L >= 8 and (layers & {'kick', 'clap'}) and nxt['layers'] != layers:
            tfill = _transition_fill(L, big)
        fill_set = {x[0] for x in tfill}
        fill_bar = 'fill' in layers and idx % 8 == 7 and not tfill
        for s in range(L):
            if pause_from is not None and s >= pause_from: continue
            p = pi[s]
            tick = base + s * q
            sw = int(g['swing'] * q) if s % 2 == 1 else 0
            # KICK
            if 'kick' in layers and P['kick'][p] and s not in fill_set:
                if not energy: vel = (110 + R(0, 5)) if s in gst else (95 + R(0, 10))
                else:          vel = (120 + R(0, 5)) if s in gst else (100 + R(0, 10))
                if s in strong: vel += 10
                _note(ev, tick, q // 2, GM_KICK, vel, DRUM_CH)
            # HI-HAT (con 'open': open hat sui levare al posto del chiuso)
            hat_on = 'hat' in layers and P['hat'][p]
            op = 'open' in layers and s in open_steps
            if hat_on or op:
                hv = (75 + R(0, 20)) if energy else (62 + R(0, 14))
                if hat_on: hv += {2: 18, 3: -28}.get(P['hat'][p], 0)    # 2 = accento, 3 = ghost
                if hv:
                    _note(ev, tick + sw, (TICKS_BEAT // 2) if op else q // 2, GM_HAT_OPEN if op else GM_HAT_CLOSED, hv + (15 if op else 0), DRUM_CH)
            # SNARE / CLAP / ROLL / FILL
            if in_roll:
                if s % roll_skip == 0:
                    _note(ev, tick, q // 2, GM_SNARE, 55 + int(roll_amp * (rr * L + s) / (N * L)), DRUM_CH)
            elif fill_bar and s >= L - 4:
                _note(ev, tick, q // 2, GM_SNARE if s % 2 == 0 else GM_TOM_HIGH, 70 + (s - (L - 4)) * 15, DRUM_CH)
            elif 'clap' in layers and s not in fill_set:
                if P['snare'][(p - sn_shift) % 16]: _note(ev, tick + sw + lazy, q // 2, GM_SNARE, (90 if roll_any else 105) + R(0, 10), DRUM_CH)
                elif P['ghost'][p] and random.random() < 0.65: _note(ev, tick + sw, q // 2, GM_SNARE, 28 + R(0, 16), DRUM_CH)
                if P['clap'][p]: _note(ev, tick + sw + lazy, q // 2, GM_CLAP, 90 + R(0, 10), DRUM_CH)
            # PERCUSSIONI
            if 'perc' in layers and not in_roll and not (fill_bar and s >= L - 4) and s not in fill_set:
                if P['perc'][p]: _note(ev, tick + sw, q // 2, g.get('perc_note', GM_RIMSHOT), 55 + R(0, 30), DRUM_CH)
                if s % 2 == 1 and random.random() < 0.15:
                    _note(ev, tick + sw, q // 2, GM_RIMSHOT if random.random() < 0.5 else GM_TOM_HIGH, 50 + R(0, 40), DRUM_CH)
        for s_, pch, v in tfill:
            _note(ev, base + s_ * q, q // 2, pch, min(127, int(v * (1.0 if big else 0.8)) + R(0, 6)), DRUM_CH)
    return ev

# ================= GENERAZIONE MINIMAL (3 TRACCE: Bass / Synth / Drums) =================

def _bar_pools(notes):
    """Note del MIDI originale raggruppate per battuta (incluse quelle che ci passano sopra)."""
    q, bt = TICKS_BEAT // 4, 4 * TICKS_BEAT
    pools = {}
    for n in notes:
        st = int(round(n['tick'] / q)) * q
        en = st + max(q, int(round(n['dur'] / q)) * q)
        b0 = st // bt
        for b in range(b0, min((en - 1) // bt, b0 + 7) + 1):
            pools.setdefault(b, []).append((st, en, n['pitch']))
    return pools, min(pools), max(pools)

def _pool_at(pools, first, last, ob):
    b = ob
    for _ in range(last - first + 1):
        if pools.get(b): return b, pools[b]
        b = b - 1 if b > first else last
    return ob, []

def generate_minimal(notes_data, g, submode, bars, seed, dna=None):
    """extract  = REMIX: riarrangia il MIDI originale (stesse armonie/melodia) sul groove del genere.
       generate = NUOVO TEMA: compone basso e motivo nuovi usando le note (pesate) del MIDI originale.
       Sempre 3 tracce: bass, arp (Synth), drums."""
    random.seed(seed)
    g = vary_genre(g, seed, g.get('_name'))
    bars, sections = compute_structure(bars, g.get('timeline'), seed)
    secmap = section_map(sections, bars)
    q, bt = TICKS_BEAT // 4, 4 * TICKS_BEAT
    root, scale = dna or extract_dna(notes_data)
    n = len(scale)
    remix = (submode == 'extract') and bool(notes_data)
    bm = plan_meter(g, bars, not remix)
    tracks = {'bass': [], 'arp': [], 'drums': build_drum_events(g, secmap, bm)}
    bass_gap = _gaps([s for s in range(16) if g['bass'][s]]) if any(g['bass']) else {}

    if remix:
        pools, first_b, last_b = _bar_pools(notes_data)
        loop_bars = last_b - first_b + 1
    else:
        counts = Counter(p['pitch'] % 12 for p in notes_data)
        w = [counts.get((root + i) % 12, 0) + 0.5 for i in scale]
        if not notes_data: w[0] += 2      # da zero: la tonica pesa di più
        pick = lambda: random.choices(range(n), weights=w)[0]
        motif = [pick() if random.random() < g['arp_density'] else None for _ in range(16)]
        while sum(x is not None for x in motif) < 3:      # generi quasi senza densità: il tema deve avere note
            motif[random.randrange(16)] = pick()
        m_cur = motif
        bass_prog = [0, random.choice([0, pick()]), pick(), pick()]
    arp_counter = 0
    arp_base = random.choice([60, 67, 72])

    for bar, B in enumerate(secmap):
        layers, idx, length = B['layers'], B['idx'], B['length']
        bass_full, bass_soft = 'bass' in layers, 'bassl' in layers
        factor = max([SYN_FACTOR[t] for t in layers if t in SYN_FACTOR] or [0])
        if not (bass_full or bass_soft or factor or 'event' in layers): continue
        m = bm[bar]; base, L, pi, gst = m['start'], m['L'], m['idx'], set(m['gstarts'])
        ramp = idx / max(1, length - 1)
        if 'event' in layers:       # un suono isolato e piano in un punto a caso della battuta
            _note(tracks['arp'], base + random.randrange(L) * q, 2 * q, _pc_pitch((root + scale[random.randrange(n)]) % 12, arp_base), 32 + random.randint(0, 18), 1)
        roll_any, energy = bool(layers & {'roll', 'rolls'}), 'clap' in layers
        arp_vel = (62 + int(18 * ramp)) if roll_any else (72 if energy else 55)
        fb = _fade(B, 'bass')
        fs = max([_fade(B, FAMILY[t]) for t in layers if t in SYN_FACTOR] or [1.0])
        hit = 0
        if remix:
            ob, pool = _pool_at(pools, first_b, last_b, first_b + idx % loop_bars)
            bar_tones = sorted({_pc_pitch(p % 12, 60) for _s, _e, p in pool})
            tones = bar_tones + [t + 12 for t in bar_tones]
        elif bar % 4 == 0 and bar > 0:
            op = random.choice(['transpose', 'invert', 'drop'])
            if op == 'transpose': motif = [(x + 1) % n if x is not None else None for x in motif]; m_cur = motif
            elif op == 'invert': motif = list(reversed(motif)); m_cur = motif
            else: m_cur = [None if random.random() < 0.3 else x for x in motif]

        for s in range(L):
            p = pi[s]
            tick = base + s * q
            sw = int(g['swing'] * q) if s % 2 == 1 else 0
            t_abs = (ob * bt + s * q) if remix else 0

            # BASSO (build-up: solo sui battiti; drop: pattern completo del genere)
            if g['bass'][p] and (bass_full or (bass_soft and s in gst)):
                if remix:
                    snd = [p for st, en, p in pool if st <= t_abs < en] or [p for _s, _e, p in pool]
                    pc = min(snd) % 12
                else:
                    pc = (root + scale[(bass_prog[bar % 4] if random.random() < 0.8 else pick()) % n]) % 12
                gap = bass_gap[p] if L == 16 else min(bass_gap[p], L - s)
                oc, dur, vx = _bass_shape(g.get('bass_style'), hit, gap, L - s); hit += 1
                _note(tracks['bass'], tick, dur * q - 15, _bass_pitch(pc) + oc, min(127, max(1, int(((95 if bass_full else 82) + (5 if s in gst else 0) + vx) * fb))), 0)

            # SYNTH / ARP
            av = int((arp_vel + random.randint(0, 8)) * fs)
            if not factor: continue
            if remix:
                onsets = [p for st, en, p in pool if st == t_abs]
                if onsets and random.random() < (1.0 if (roll_any or energy) else 0.6):
                    _note(tracks['arp'], tick + sw, q - 15, _fold(max(onsets)), av, 1)
                elif tones and random.random() < g['arp_density'] * 0.5 * factor:
                    _note(tracks['arp'], tick + sw, q - 15, tones[arp_counter % len(tones)], av, 1)
                    arp_counter += 1
            elif m_cur[p] is not None and random.random() < factor:
                _note(tracks['arp'], tick + sw, q - 20, _pc_pitch((root + scale[m_cur[p] % n]) % 12, arp_base), av, 1)

    return {k: v for k, v in tracks.items() if v}, root, scale

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

DRUM_GROUPS = [('drum_kick', {GM_KICK}), ('drum_snare', {GM_SNARE}), ('drum_hat', {GM_HAT_CLOSED, GM_HAT_OPEN}),
               ('drum_clap', {GM_CLAP}), ('drum_perc', {GM_RIMSHOT, GM_TOM_HIGH, 54, 56, 70, 75, 43, 45, 47, 48}), ('drum_fx', {49, 119})]
DRUM_TRACK_NAMES = {'drums': 'Drums', 'drum_kick': 'Kick', 'drum_snare': 'Snare', 'drum_hat': 'Hat', 'drum_clap': 'Clap', 'drum_perc': 'Perc', 'drum_fx': 'Crash / FX'}

def split_drum_track(tracks):
    events = tracks.get('drums')
    if not events: return tracks
    out = {k: v for k, v in tracks.items() if k != 'drums'}
    known = set()
    for key, pitches in DRUM_GROUPS:
        known |= pitches
        ev = [e for e in events if e['pitch'] in pitches]
        if ev: out[key] = ev
    rest = [e for e in events if e['pitch'] not in known]
    if rest: out['drums'] = rest
    return out

def _arrange_faithful(mid, all_notes, g, secmap, tracks, headers, root, scale):
    """FAITHFUL: le tracce melodiche originali vengono ri-arrangiate nella struttura DJ
    (niente note in intro/outro, solo batteria) con swing del genere; la batteria è del nuovo genere."""
    q, bt, grid = TICKS_BEAT // 4, 4 * TICKS_BEAT, TICKS_BEAT // 16
    free_channels = [c for c in range(16) if c != DRUM_CH]
    by_track = {}
    for nt in all_notes: by_track.setdefault(nt['track'], []).append(nt)
    prepared = {}
    for ti, lst in by_track.items():
        prepared[ti] = [(int(round(nt['tick'] / grid)) * grid, max(grid, int(round(nt['dur'] / grid)) * grid),
                         snap_to_scale(nt['pitch'], root, scale), nt['vel']) for nt in lst]
    first_bar = min(st for arr in prepared.values() for st, _d, _p, _v in arr) // bt
    end = max(st + du for arr in prepared.values() for st, du, _p, _v in arr)
    loop_bars = max(1, -(-(end - first_bar * bt) // bt))
    buckets = {ti: {} for ti in prepared}
    for ti, arr in prepared.items():
        for st, du, p, v in arr:
            buckets[ti].setdefault(st // bt - first_bar, []).append((st % bt, du, p, v))

    avg = {ti: sum(p for _s, _d, p, _v in arr) / len(arr) for ti, arr in prepared.items()}
    bass_t = {ti for ti, a in avg.items() if a < 52}
    lead_t = ({max(avg, key=avg.get)} - bass_t) if len(avg) >= 3 else set()
    all_t = set(prepared)

    def active(mel, idx, length):
        non_bass = all_t - bass_t
        if mel == 'drop': res = all_t
        elif mel == 'build': res = non_bass | (bass_t if idx >= length // 2 else set())
        elif mel == 'break2': res = non_bass
        else: res = (non_bass - lead_t) or non_bass
        return res or all_t

    keys = {}
    for track_idx, ti in enumerate(sorted(prepared)):
        mt = mid.tracks[ti]
        name = next((m.name for m in mt if m.type == 'track_name'), None)
        track_key = (name or '').strip() or f'instrument_{track_idx}'
        base_key, k = track_key, 2
        while track_key in tracks or track_key in DRUM_TRACK_NAMES:
            track_key = f'{base_key} {k}'; k += 1
        tracks[track_key] = []
        hd = _extract_instrument_header(mt)
        if hd: headers[track_key] = hd
        keys[ti] = (track_key, free_channels[track_idx % len(free_channels)])

    swing = g['swing']
    for bar, B in enumerate(secmap):
        idx, length = B['idx'], B['length']
        if not (B['layers'] & (MELODIC | EVENT)): continue
        mel = B['sec'] if B['sec'] in ('break1', 'break2', 'build', 'drop') else 'break1'   # eventi: suonano le battute originali
        base = bar * bt
        sec_end = base + (length - idx) * bt
        ob = idx % loop_bars
        vf = {'break1': 0.8, 'break2': 0.8, 'build': 0.75 + 0.25 * idx / max(1, length - 1), 'drop': 1.0}[mel]
        for ti in active(mel, idx, length):
            key, ch = keys[ti]
            for rel, du, pitch, vel in buckets[ti].get(ob, ()):
                st = base + rel
                if swing and abs(rel % (2 * q) - q) <= grid // 2: st += int(swing * q)
                du = min(du, sec_end - st)
                if du > 0: _note(tracks[key], st, du, pitch, vel * vf, ch)

def _tame_scale(scale):
    """Se il DNA ha troppe note (MIDI cromatico) usa una scala a 7 note vicina a quella rilevata."""
    if len(scale) <= 8: return scale
    ideal = [0, 2, 3, 5, 7, 8, 10] if _is_minor_scale(scale) else [0, 2, 4, 5, 7, 9, 11]
    sel = [i for i in ideal if i in scale]
    return sel if len(sel) >= 5 else ideal

def _add_reese(g, tracks):
    """Reese bass: la linea di basso raddoppiata su un altro canale; build_automation la scorda con il pitch bend."""
    if g.get('bass_style') == 'reese' and tracks.get('bassline'):
        tracks['reese'] = [dict(e, channel=7) for e in tracks['bassline']]

def _arrange_generative(g, root, scale, secmap, tracks, bm=None):
    """GENERATIVE: ignora le note originali, usa solo tonalità/scala (DNA). 7 ruoli + batteria,
    ognuno attivo solo nelle sezioni dove ha senso."""
    q = TICKS_BEAT // 4
    bm = bm or plan_meter(g, len(secmap), False)
    scale = _tame_scale(scale)
    n = len(scale)
    pc_of = lambda d: (root + scale[d % n]) % 12
    for role in ('sub_bass', 'bassline', 'pad', 'chords', 'arp', 'lead', 'fx_perc'): tracks[role] = []
    def _rand_prog():
        head = 0 if random.random() < 0.85 else random.choice([3, 4])
        return [head] + random.choices([2, 3, 4, 5, 1, 6], weights=[2, 3, 4, 3, 1, 1], k=3)
    prog_a, prog_b = _rand_prog(), _rand_prog()
    use7 = random.random() < g.get('seventh', 0.35)       # accordi di settima (Deep, Soul, R&B... quasi sempre)
    use9 = random.random() < g.get('ninth', 0.0)          # con la nona
    bass_style = g.get('bass_style')
    chord_off = random.choice([0, 1, 2, 2, 3])           # dove cadono gli stab degli accordi nel gruppo
    arp_base, lead_oct = random.choice([60, 67, 72]), random.choice([67, 72])
    bass_root_p, lead_p = BASS_ROOT_P.get(bass_style, random.uniform(0.6, 0.9)), random.uniform(0.3, 0.6)
    bass_steps = [s for s in range(16) if g['bass'][s]]
    bass_gap = _gaps(bass_steps) if bass_steps else {}
    lead_base = [random.randrange(n) if random.random() < lead_p else None for _ in range(16)]
    lead = lead_base
    lead_q, lead_a = _question(lead_base, n), _answer(lead_base)
    arp_mode, R = 'up', random.randint

    for bar, B in enumerate(secmap):
        layers, idx, length, prev = B['layers'], B['idx'], B['length'], B['prev']
        if not (layers & (MELODIC | EVENT)): continue
        m = bm[bar]; base, L, pi, gstarts = m['start'], m['L'], m['idx'], m['gstarts']
        gst, bt = set(gstarts), L * q
        if bar % 4 == 0:
            arp_mode = random.choice(['up', 'updown', 'rand'])
            blk = lead_base
            if bar > 0:
                op = random.choice(['transpose', 'invert', 'drop'])
                if op == 'transpose': lead_base = [(x + 1) % n if x is not None else None for x in lead_base]; blk = lead_base
                elif op == 'invert': lead_base = list(reversed(lead_base)); blk = lead_base
                else: blk = _thin(lead_base, 0.3)
            lead_q, lead_a = _question(blk, n), _answer(blk)      # frase di 4 battute: domanda, domanda, domanda variata, risposta
        lead = lead_a if bar % 4 == 3 else (_thin(lead_q) if bar % 4 == 2 else lead_q)
        d = (prog_a if (bar // 4) % 2 == 0 else prog_b)[bar % 4]
        cpcs = [pc_of(d), pc_of(d + 2), pc_of(d + 4)] + ([pc_of(d + 6)] if use7 else []) + ([pc_of(d + 8)] if use9 else [])
        rpc = cpcs[0]
        ramp = idx / max(1, length - 1)
        roll_any, energy = bool(layers & {'roll', 'rolls'}), 'clap' in layers
        if 'event' in layers:       # un suono isolato e piano in un punto a caso della battuta
            _note(tracks['lead'], base + random.randrange(L) * q, 2 * q, _pc_pitch(pc_of(random.randrange(n)), lead_oct), 32 + R(0, 18), 5)

        # SUB BASS + BASSLINE: il basso e' portante (bass = pattern del genere, bassl = solo sui battiti e piu' piano)
        if 'bass' in layers or 'bassl' in layers:
            soft, fb = 'bass' not in layers, _fade(B, 'bass')
            _note(tracks['sub_bass'], base, bt - 20, _pc_pitch(rpc, 24), int((84 if soft else 100) * fb), 0)
            hit = 0
            for s in range(L):
                if not g['bass'][pi[s]]: continue
                if soft and s not in gst: continue
                pc = _bass_pc(bass_style, hit, cpcs, rpc, bass_root_p)
                gap = bass_gap[pi[s]] if L == 16 else min(bass_gap[pi[s]], L - s)
                oc, dur, vx = _bass_shape(bass_style, hit, gap, L - s); hit += 1
                _note(tracks['bassline'], base + s * q, dur * q - 15, _pc_pitch(pc, 36) + oc, min(127, max(1, int(((82 if soft else 95) + (5 if s in gst else 0) + vx) * fb))), 1)

        # PAD: accordo lungo
        if 'pad' in layers:
            pad_vel = int(((62 if energy else 52) + (int(15 * ramp) if roll_any else 0)) * _fade(B, 'pad'))
            for pc in cpcs: _note(tracks['pad'], base, bt - 10, _pc_pitch(pc, 48), pad_vel, 2)

        # CHORDS: stab (chords) o accordi lunghi (chordsl)
        c_steps, c_dur, c_vel = [], 0, 0
        if 'chords' in layers: c_steps, c_dur, c_vel = [x + chord_off for x in gstarts if x + chord_off < L], q + q // 2, (65 + int(25 * ramp)) if roll_any else 80
        elif 'chordsl' in layers: c_steps, c_dur, c_vel = [gstarts[0], gstarts[len(gstarts) // 2]], 2 * TICKS_BEAT - 20, 58
        cf = _fade(B, 'chords')
        for s in c_steps:
            if 'chords' in layers and not roll_any and random.random() > 0.85: continue
            for pc in cpcs: _note(tracks['chords'], base + s * q, c_dur, _pc_pitch(pc, 55), int((c_vel + R(0, 8)) * cf), 3)

        # ARP sulle note dell'accordo (arp = densita' del genere, arpl = meta')
        if 'arp' in layers or 'arpl' in layers:
            tones = sorted(_pc_pitch(pc, arp_base) + 12 * k for pc in cpcs for k in (0, 1))
            factor = (1.0 if 'arp' in layers else 0.5) * ((0.85 + 0.15 * ramp) if roll_any else 1.0)
            a_vel = 72 if energy else ((58 + int(20 * ramp)) if roll_any else 52)
            af, NT = _fade(B, 'arp'), len(tones)
            for s in range(L):
                if random.random() < min(1.0, g['arp_density'] * factor):
                    if arp_mode == 'up': i = s % NT
                    elif arp_mode == 'updown':
                        k = s % (2 * (NT - 1)); i = k if k < NT else 2 * (NT - 1) - k
                    else: i = random.randrange(NT)
                    sw = int(g['swing'] * q) if s % 2 == 1 else 0
                    _note(tracks['arp'], base + s * q + sw, q - 10, tones[i], int((a_vel + R(0, 8)) * af), 4)

        # LEAD: motivo pieno (lead) o versione rada sui battiti (leadl)
        l_steps = [s for s, v in enumerate(lead) if v is not None]
        if ('lead' in layers or 'leadl' in layers) and l_steps:
            full, lf, gaps = 'lead' in layers, _fade(B, 'lead'), _gaps(l_steps)
            for s in range(L):
                lp = pi[s]
                if lead[lp] is None: continue
                if not full and s not in gst: continue
                gp = gaps[lp] if L == 16 else min(gaps[lp], L - s)
                du = gp * q - 10 if full else 2 * TICKS_BEAT - 10
                _note(tracks['lead'], base + s * q, du, _pc_pitch(pc_of(lead[lp]), lead_oct), int((88 if full else 70) * lf), 5)

        # FX: impatto quando entra qualcosa di nuovo + riser nelle ultime 2 battute di una sezione con rullata
        if idx == 0 and (layers - prev):
            _note(tracks['fx_perc'], base, bt - 10, _pc_pitch(rpc, 72), 110 if ('clap' in layers and 'clap' not in prev) else 75, 6)
        riser = min(2, length)
        if roll_any and idx >= length - riser:
            k0 = (idx - (length - riser)) * 8
            for k, s in enumerate([int(x * L / 8) for x in range(8)]):
                j = k0 + k
                _note(tracks['fx_perc'], base + s * q, q * 2 - 10,
                      _pc_pitch(root, 60) + scale[j % n] + 12 * (j // n), 60 + int(50 * (j + 1) / (riser * 8)), 6)

def generate_multitrack(mid_file_bytes, g, submode, bars, seed, split_drums=True):
    random.seed(seed)
    g = vary_genre(g, seed, g.get('_name'))
    bars, sections = compute_structure(bars, g.get('timeline'), seed)
    secmap = section_map(sections, bars)
    bm = plan_meter(g, bars, submode != 'faithful')
    mid = mido.MidiFile(file=mid_file_bytes)
    all_notes = notes_from_midi(mid)
    if not all_notes:
        raise ValueError("Il file MIDI non contiene note melodiche (i canali batteria vengono ignorati).")
    root, scale = extract_dna(all_notes)
    tracks, headers = {}, {}
    if submode == 'faithful':
        _arrange_faithful(mid, all_notes, g, secmap, tracks, headers, root, scale)
    else:
        _arrange_generative(g, root, scale, secmap, tracks, bm)
        _add_reese(g, tracks)
    drums = build_drum_events(g, secmap, bm)
    if drums: tracks['drums'] = drums
    tracks = {k: v for k, v in tracks.items() if v}
    if split_drums and 'drums' in tracks:
        tracks = split_drum_track(tracks)
    return tracks, root, scale, headers, bars

def generate_from_scratch(g, dna, bars, seed, split_drums=True):
    """Multitraccia generativa senza MIDI originale: tonalità e scala scelte (o random)."""
    random.seed(seed)
    root, scale = dna
    g = vary_genre(g, seed, g.get('_name'))
    bars, sections = compute_structure(bars, g.get('timeline'), seed)
    secmap = section_map(sections, bars)
    tracks, headers = {}, {}
    bm = plan_meter(g, bars, True)
    _arrange_generative(g, root, scale, secmap, tracks, bm)
    _add_reese(g, tracks)
    drums = build_drum_events(g, secmap, bm)
    if drums: tracks['drums'] = drums
    tracks = {k: v for k, v in tracks.items() if v}
    if split_drums and 'drums' in tracks: tracks = split_drum_track(tracks)
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

# ================= MARKER DI SEZIONE + AUTOMAZIONI FILTRO (CC74) =================
import unicodedata

def _ascii(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

def section_markers(sections, bm):
    """[(tick, testo)] un marker per sezione: nome, battuta di inizio e strati che entrano (compaiono nella Marker List di Logic)."""
    out, prev = [], frozenset()
    for name, start, _length, layers in sections:
        ins = sorted(layers - prev)
        txt = f"{name} - bar {start + 1}" + (" | +" + " +".join(ins) if ins else "")
        out.append((bm[start]['start'], _ascii(txt)[:110]))
        prev = layers
    return out

_SYNTH_MIN = frozenset({'arp', 'arpl', 'lead', 'leadl', 'chords', 'chordsl', 'pad'})

def build_automation(sections, bm, tracks, style=None):
    """CC74 (cutoff/brightness) per le tracce melodiche: uno strato che entra apre il filtro in 4 battute (25 -> livello della sezione),
    i break lo chiudono un po', le sezioni con rullata (build) aprono il filtro fino a 127 nelle ultime 8 battute.
    Ritorna {chiave_traccia: [(tick, cc, valore)]}."""
    q = TICKS_BEAT // 4
    if 'bassline' in tracks:
        maps = {'sub_bass': ({'bass', 'bassl'}, {'bassl'}), 'bassline': ({'bass', 'bassl'}, {'bassl'}), 'pad': ({'pad'}, set()),
                'chords': ({'chords', 'chordsl'}, {'chordsl'}), 'arp': ({'arp', 'arpl'}, {'arpl'}), 'lead': ({'lead', 'leadl'}, {'leadl'})}
    else:
        maps = {'bass': ({'bass', 'bassl'}, {'bassl'}), 'arp': (set(_SYNTH_MIN), {'arpl', 'leadl', 'chordsl', 'pad'})}
    maps = {k: v for k, v in maps.items() if k in tracks}
    pts = {k: {} for k in maps}          # tick -> valore (l'ultimo scritto vince)
    last = {k: None for k in maps}
    def ramp(k, t0, t1, v0, v1, nsteps):
        for i in range(nsteps):
            pts[k][int(t0 + (t1 - t0) * i / nsteps)] = int(round(v0 + (v1 - v0) * i / nsteps))
        pts[k][max(int(t0), int(t1) - 1)] = int(v1)
    prev = frozenset()
    for name, start, length, layers in sections:
        t0 = bm[start]['start']
        tend = bm[start + length - 1]['start'] + bm[start + length - 1]['L'] * q
        avg = (tend - t0) / length
        roll_any = bool(layers & {'roll', 'rolls'})
        base = 110 if 'clap' in layers else 92
        W = min(8, length)
        ts = tend - W * avg
        for k, (tok, light) in maps.items():
            active = layers & tok
            if not active:
                last[k] = None; continue
            target = base if (active - light) else base - 28
            fresh = last[k] is None or not (prev & tok)
            R = min(4, length)
            if fresh:
                if roll_any and t0 + R * avg > ts: pass            # lo sweep del build copre gia' l'ingresso
                else: ramp(k, t0, t0 + R * avg, 25, target, R * 4)
            elif last[k] == 127: pts[k][t0] = target                  # dopo il build il filtro torna subito al livello normale
            elif abs(target - last[k]) > 4: ramp(k, t0, t0 + min(2, length) * avg, last[k], target, min(2, length) * 4)
            last[k] = target
            if roll_any:
                ramp(k, ts, tend, 25 if fresh else max(60, target - 40), 127, W * 4)
                last[k] = 127
        prev = layers
    out = {k: [(t, 74, v) for t, v in sorted(p.items())] for k, p in pts.items() if p}
    # glide (pitch bend) tra note vicine del basso: 808 lungo (trap) e slide dell'acid. Range del bend = 12 semitoni (RPN 0).
    if style in ('long', 'acid'):
        max_gap, max_glen = (3840, 360) if style == 'long' else (240, 100)
        for k in ('sub_bass', 'bassline', 'bass'):
            if k not in tracks: continue
            ons = sorted([e for e in tracks[k] if e['type'] == 'on'], key=lambda e: e['tick'])
            glide = []
            for a_, b_ in zip(ons, ons[1:]):
                d = a_['pitch'] - b_['pitch']
                if d == 0 or abs(d) > 12 or b_['tick'] - a_['tick'] > max_gap or (b_['tick'] // 120 + b_['pitch']) % 5 >= 3: continue
                glen = min(b_['tick'] - a_['tick'], max_glen); n_ = max(2, glen // 60)
                for i in range(n_): glide.append((b_['tick'] + i * glen // n_, 'pb', int(max(-8192, min(8191, round(d / 12 * 8191 * (1 - i / n_)))))))
                glide.append((b_['tick'] + glen, 'pb', 0))
            if glide:
                rpn = [(0, 101, 0), (0, 100, 0), (0, 6, 12), (0, 38, 0), (0, 101, 127), (0, 100, 127)]
                out[k] = rpn + sorted(out.get(k, []) + glide, key=lambda x: x[0])
    # Reese: seconda traccia scordata (+0.17 semitoni) e cutoff che si muove lentamente (periodo 8 battute)
    if 'reese' in tracks:
        import math
        end = bm[-1]['start'] + bm[-1]['L'] * q
        out['reese'] = [(0, 'pb', 700)] + [(t, 74, int(75 + 35 * math.sin(2 * math.pi * t / (8 * 1920)))) for t in range(0, end, 960)]
    return out

def _show_html(html, height):
    """Mostra un blocco HTML: st.iframe se disponibile (components.html e' deprecato), altrimenti components.html."""
    if hasattr(st, 'iframe'): st.iframe(html, height=height)
    else: components.html(html, height=height)

def build_midi_file(tracks, bpm, mode, submode, headers=None, label=None, key_name=None, meter_plan=None, automation=None, markers=None):
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
    ts_changes, prev_sig = [], None
    for m in (meter_plan or []):
        if m['sig'] != prev_sig: ts_changes.append((m['start'], m['sig'])); prev_sig = m['sig']
    if not ts_changes: ts_changes = [(0, (4, 4))]
    t_tempo.append(mido.MetaMessage('time_signature', numerator=ts_changes[0][1][0], denominator=ts_changes[0][1][1], time=0))
    if key_name:
        try: t_tempo.append(mido.MetaMessage('key_signature', key=key_name, time=0))
        except ValueError: pass
    if label:
        text = ("MIDI Forge - " + label).encode('ascii', 'ignore').decode('ascii')[:120]
        t_tempo.append(mido.MetaMessage('marker', text=text, time=0))
    timed = [(tk, 0, 'ts', sig) for tk, sig in ts_changes[1:]] + [(tk, 1, 'mk', txt) for tk, txt in (markers or [])]
    timed.sort(key=lambda x: (x[0], x[1]))
    last = 0
    for tk, _o, kind, val in timed:
        if kind == 'ts': t_tempo.append(mido.MetaMessage('time_signature', numerator=val[0], denominator=val[1], time=tk - last))
        else: t_tempo.append(mido.MetaMessage('marker', text=val, time=tk - last))
        last = tk
    t_tempo.append(mido.MetaMessage('end_of_track', time=max(0, total_end - last)))
    mid.tracks.append(t_tempo)

    used_names = Counter()
    for key, (ch, notes) in notes_by_track.items():
        is_drums = (ch == DRUM_CH)
        header = list(headers.get(key, []))
        if not any(h['type'] == 'program_change' for h in header):
            if is_drums: pc = 0
            else:
                pc = None if faithful else {'bass': 38, 'arp': 80, 'sub_bass': 39, 'bassline': 38, 'pad': 89, 'chords': 0, 'lead': 81, 'fx_perc': 117, 'reese': 39}.get(key)
                if pc is None: pc = _guess_program(key)
            header.append({'type': 'program_change', 'program': pc})
        bank = [h for h in header if h['type'] == 'control_change' and h['control'] in (0, 32)]
        pcs = [h for h in header if h['type'] == 'program_change'][:1]
        mix = {h['control']: h for h in header if h['type'] == 'control_change' and h['control'] not in (0, 32)}
        program = pcs[0]['program'] & 0x7F if pcs else None
        
        if is_drums: name = DRUM_TRACK_NAMES.get(key, 'Drums')
        elif key.startswith('instrument_'): name = GM_PROGRAM_NAMES[program] if program is not None else key
        elif faithful: name = key
        else: name = {'bass': 'Bass', 'arp': 'Synth', 'sub_bass': 'Sub Bass', 'bassline': 'Bass', 'pad': 'Pad', 'chords': 'Piano', 'lead': 'Lead', 'fx_perc': 'Percussion', 'drums': 'Drums', 'reese': 'Reese Bass'}.get(key, key.replace('_', ' ').title())
        
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
        for tk, cc, val in (automation or {}).get(key, []):
            if cc == 'pb': ev.append((tk, -2, max(-8192, min(8191, int(val))), 0))   # pitch bend
            else: ev.append((tk, -1, cc, val))                 # CC prima delle note allo stesso tick
        ev.sort(key=lambda x: (x[0], x[1]))
        prev = 0
        for tick, kind, a_, b_ in ev:
            if kind == -2: midi_track.append(mido.Message('pitchwheel', pitch=a_, time=tick - prev, channel=ch))
            elif kind == -1: midi_track.append(mido.Message('control_change', control=a_, value=b_, time=tick - prev, channel=ch))
            else: midi_track.append(mido.Message('note_on' if kind else 'note_off', note=a_, velocity=b_, time=tick - prev, channel=ch))
            prev = tick
        midi_track.append(mido.MetaMessage('end_of_track', time=max(0, total_end - prev)))
        mid.tracks.append(midi_track)

    buf = io.BytesIO()
    mid.save(file=buf)
    buf.seek(0)
    return buf

def _style_line(g):
    return f"   Basso: {g.get('bass_style') or 'standard'} | accordi: settima {g.get('seventh', 0.35):.0%}, nona {g.get('ninth', 0.0):.0%} dei brani"

def _meter_line(meter_plan):
    if not meter_plan: return "   4/4 (tutto il brano)"
    c = Counter(m['key'] for m in meter_plan)
    if len(c) == 1: return f"   {next(iter(c))} (tutto il brano)"
    return "   Ciclo: " + " | ".join(f"{k} x{n}" for k, n in c.items()) + "  (cambi di time signature scritti nel MIDI)"

def generate_report(tracks, genre, mode, submode, bpm, bars, seed, root, scale, duration_mode, duration_seconds, original_filename, meter_plan=None, g_used=None, cc_markers=(False, False)):
    report = ["=" * 60, "MIDI FORGE UNIVERSALE - REPORT DI GENERAZIONE", "=" * 60, "", "DATA E ORA", f"   Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "", "PARAMETRI GENERAZIONE", f"   File originale: {original_filename}", f"   Modalità: {mode.upper()}", f"   Sotto-modalità: {submode.upper()}", f"   Genere: {genre.upper()}", f"   Seed: {seed}", f"   BPM: {bpm}", f"   Battute: {bars}"]
    if duration_mode == "Minuti:Secondi" and duration_seconds:
        report.append(f"   Durata target: {duration_seconds // 60}:{duration_seconds % 60:02d}")
    total_q = sum(m['L'] for m in meter_plan) if meter_plan else bars * 16
    duration_actual = (total_q / 4 * 60) / bpm
    report.extend([f"   Durata effettiva: {int(duration_actual)}:{int((duration_actual - int(duration_actual)) * 60):02d}", "", "METRO", _meter_line(meter_plan), "", "STILE BASSO / ARMONIA", _style_line(g_used or GENRES[genre]), "", "ANALISI TONALE", f"   Tonica rilevata: {NOTE_NAMES[root]}", f"   Scala: {' - '.join([NOTE_NAMES[(root + i) % 12] for i in scale])}", f"   Intervalli: {scale}", ""])
    g = g_used or GENRES[genre]
    report.extend(["PATTERN RITMICI (16 step, adattati ai gruppi del metro)", f"   Kick (GM 36):  {''.join(['#' if x else '.' for x in g['kick']])}", f"   Snare (GM 38): {''.join(['#' if x else '.' for x in g.get('snare', [0]*16)])}"])
    if 'clap' in g: report.append(f"   Clap (GM 39):  {''.join(['#' if x else '.' for x in g['clap']])}")
    report.extend([f"   Hat (GM 42):   {''.join('.' if not x else ('+' if x == 3 else '#') for x in g['hat'])}  (+ = ghost)", f"   Bass:          {''.join(['#' if x else '.' for x in g['bass']])}", f"   Ghost snare: {''.join(['#' if x else '.' for x in g.get('ghost', [0]*16)])}", f"   Swing: {g['swing'] * 100:.0f}%", f"   Densità Arp: {g['arp_density'] * 100:.0f}%", "", "STRUTTURA STRUTTURA DEL GENERE (ingressi/uscite per strati)", *_structure_report(bars, g.get('timeline'), seed), "", "TRACCE OUTPUT"])
    track_idx = 1
    for track_key in tracks.keys():
        if track_key in DRUM_TRACK_NAMES: report.append(f"   {track_idx}. {DRUM_TRACK_NAMES[track_key]} (Canale 10 - GM Drum Map)")
        elif track_key.startswith('instrument_'): report.append(f"   {track_idx}. {track_key} (Canale melodico)")
        else: report.append(f"   {track_idx}. {track_key.replace('_', ' ').title()} (Canale melodico)")
        track_idx += 1
    report.extend(["", "STATISTICHE MIDI", f"   Note totali generate: {sum(1 for events in tracks.values() for e in events if e['type'] == 'on')}", f"   Tracce MIDI: {len(tracks) + 1}", "", "NOTE PER LOGIC PRO", "   - Apri con File > Apri (non Importa)", "   - Intro e outro seguono la timeline del genere (di solito pochi strati, per il mix DJ)", "   - Ogni traccia ha nome e program change al tick 0", *(["   - Automazioni CC74 (filtro): mappa CC74 sul cutoff del synth di ogni traccia; gli strati che entrano aprono il filtro in 4 battute, il build lo apre fino in fondo"] if cc_markers[0] else []), *(["   - Marker di sezione nel file: in Logic li trovi nella Marker List (Navigate > Open Marker List) e sulla timeline, con gli strati che entrano"] if cc_markers[1] else []), *(["   - Transizioni: crash (nota 49) e reverse cymbal (nota 119) sono nella traccia Crash / FX; se il tuo drum kit non mappa la 119 sostituiscila con un riser. Prima del drop, nei generi forti, c'e' un beat di pausa"] if any(e.get('pitch') in (49, 119) for k_ in ('drum_fx', 'drums') for e in tracks.get(k_, [])) else []), "   - Batteria su canale 10: assegna Drum Kit Designer se necessario", "", "=" * 60, "Generato con MIDI Forge Universale | 100% Free & Open Source", "=" * 60])
    return "\n".join(report)

def render_midi_player(tracks, bpm):
    all_notes_with_dur = []
    for events in tracks.values(): 
        all_notes_with_dur.extend(_compute_note_durations(events))
    
    notes_json = json.dumps([{'tick': n['tick'], 'dur': n['dur'], 'pitch': n['pitch'], 'vel': n['vel'], 'channel': n['channel']} for n in all_notes_with_dur])
    
    # F-string con parentesi graffe correttamente raddoppiate per JS/CSS
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
            <div class="title">Anteprima MIDI (con durate reali)</div>
            <div class="controls">
                <button id="playBtn" onclick="togglePlay()">Play</button>
                <button onclick="stop()">Stop</button>
                <span class="status" id="status">Pronto - {bpm} BPM</span>
            </div>
        </div>
        <script>
            const notes = {notes_json};
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
                    notes.forEach(note => {{
                        const timeInSeconds = note.tick / ticksPerSecond;
                        const durInSeconds = note.dur / ticksPerSecond;
                        if (note.channel === {DRUM_CH}) {{
                            scheduledEvents.push(
                                Tone.getTransport().schedule(time => {{
                                    if (note.pitch === {GM_KICK}) synths[{DRUM_CH}].kick.triggerAttackRelease('C1', durInSeconds, time, note.vel / 127);
                                    else if (note.pitch === {GM_SNARE}) synths[{DRUM_CH}].snare.triggerAttackRelease(durInSeconds, time, note.vel / 127);
                                    else if (note.pitch === {GM_CLAP}) synths[{DRUM_CH}].clap.triggerAttackRelease(durInSeconds, time, note.vel / 127);
                                    else if (note.pitch === {GM_HAT_CLOSED} || note.pitch === {GM_HAT_OPEN}) synths[{DRUM_CH}].hat.triggerAttackRelease('C3', durInSeconds, time, note.vel / 127);
                                }}, timeInSeconds)
                            );
                        }} else {{
                            const noteName = Tone.Frequency(note.pitch, 'midi').toNote();
                            scheduledEvents.push(
                                Tone.getTransport().schedule(time => {{
                                    synths[note.channel].triggerAttackRelease(noteName, durInSeconds, time, note.vel / 127);
                                }}, timeInSeconds)
                            );
                        }}
                    }});
                    Tone.getTransport().start();
                    isPlaying = true;
                    document.getElementById('playBtn').textContent = 'Pause';
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
                document.getElementById('playBtn').textContent = 'Play';
                document.getElementById('status').textContent = 'Pronto - {bpm} BPM';
            }}
        </script>
    </body>
    </html>
    """
    _show_html(html_player, 150)

# ================= INTERFACCIA STREAMLIT =================

if 'generated' not in st.session_state:
    st.session_state.generated = {'tracks': None, 'root': None, 'scale': None, 'headers': None, 'bars': None, 'bpm': None, 'midi_bytes': None, 'report_text': '', 'label': None, 'mode': None, 'submode': None, 'genre': None, 'duration_mode': None, 'duration_seconds': None, 'original_filename': None}

st.title("MIDI Forge Universale")
st.markdown("Trasforma qualsiasi file MIDI in 30+ generi musicali. Ogni genere ha la sua struttura a strati, con ingressi e uscite graduali (intro DJ, groove, main, breakdown, outro)")

col1, col2 = st.columns([1, 1])

with col1:
    source = st.radio("Sorgente", ["Da un MIDI caricato", "Da zero (senza MIDI)"], horizontal=True)
    scratch = source.startswith("Da zero")
    if scratch:
        uploaded_file = None
        key_choice = st.selectbox("Tonalità", ["Random"] + NOTE_NAMES)
        scale_choice = st.selectbox("Scala", ["Random"] + list(SCALES.keys()))
        mode = st.selectbox("Modalità Principale", ["minimal", "multitrack"], format_func=lambda x: {"minimal": "Minimal (3 tracce)", "multitrack": "Multitraccia (7+ tracce)"}[x])
        submode = "generate" if mode == "minimal" else "generative"
    else:
        uploaded_file = st.file_uploader("Carica il tuo file MIDI (.mid o .midi)", type=["mid", "midi"])
        mode = st.selectbox("Modalità Principale", ["minimal", "multitrack"])
        if mode == "minimal":
            submode = st.selectbox("Sotto-modalità", ["extract", "generate"], format_func=lambda x: {"extract": "Remix (riarrangia le note originali)", "generate": "Nuovo tema (dalle note originali)"}[x])
        else:
            submode = st.selectbox("Sotto-modalità", ["faithful", "generative"], format_func=lambda x: {"faithful": "Faithful (fedele all'originale)", "generative": "Generative (solo tonalità, da zero)"}[x])
    split_drums = st.checkbox("Batteria su tracce separate (Kick / Snare / Hat / Clap)", value=True) if mode == "multitrack" else False
    auto_cc = st.checkbox("Automazioni filtro (CC74), glide e movimento del basso", value=True)
    add_markers = st.checkbox("Marker di sezione nel MIDI", value=True)
    use_trans = st.checkbox("Transizioni (crash, reverse, pausa prima del drop, fill)", value=True)

with col2:
    with st.expander("Timeline personalizzate (JSON)"):
        _up = st.file_uploader("Carica timeline modificate (.json)", type=["json"], key="tl_json")
        if _up is not None:
            try: st.success(f"Timeline applicate a {apply_timelines(json.loads(_up.getvalue().decode('utf-8')))} generi")
            except Exception as _e: st.error(f"JSON non valido: {_e}")
        st.download_button("Scarica le timeline attuali (JSON)", data=timelines_to_json(), file_name="midi_forge_timelines.json", mime="application/json")
        if TIMELINE_FILE_MSG: st.caption(TIMELINE_FILE_MSG)
        st.caption("Formato: {\"deep\": [[\"Intro DJ\", 16, \"kick hat pad\"], ...]}. Strati: " + " ".join(LAYER_ORDER) + ". Un file midi_forge_timelines.json accanto allo script viene caricato in automatico.")
    genre_list = sorted(GENRES.keys())
    genre = st.selectbox("Genere Musicale", genre_list, index=genre_list.index("techno"))
    g_defaults = GENRES[genre]
    st.caption('Struttura tipica (' + str(g_defaults['bars_default']) + ' battute):' + _structure_line(g_defaults['bars_default'], g_defaults.get('timeline')))
    with st.expander("Anteprima struttura e strati"):
        _off = st.multiselect("Spegni questi strati in tutto il brano", [t for t in LAYER_ORDER if t != 'event'], key=f"off_{genre}")
        st.table(timeline_table([(n, b, ls - set(_off)) for n, b, ls in g_defaults['timeline']]))
        st.caption("Le lunghezze valgono per la durata di default: con un altro numero di battute, o col seed, le sezioni scalano in proporzione.")
    g_run = dict(g_defaults, timeline=[(n, b, frozenset(ls - set(_off))) for n, b, ls in g_defaults['timeline']])
    if g_defaults.get('meter'):
        st.caption('Metro: ' + ' | '.join(g_defaults['meter']) + ' (ciclo per battuta). Con Remix/Faithful resta 4/4, come il MIDI originale.')
    col_bpm1, col_bpm2 = st.columns(2)
    with col_bpm1:
        use_default_bpm = st.checkbox("BPM Automatico (varia col seed, nel range del genere)", value=True)
        bpm = st.number_input("BPM", min_value=40, max_value=300, value=g_defaults['bpm_default'], disabled=use_default_bpm)
    with col_bpm2:
        duration_mode = st.radio("Durata traccia", ["Battute", "Minuti:Secondi"], horizontal=True)
        if duration_mode == "Battute":
            use_default_bars = st.checkbox("Battute Automatiche", value=True)
            bars = st.number_input("Battute", min_value=min(16, min_bars(g_defaults)), max_value=512, step=timeline_unit(g_defaults['timeline']), value=g_defaults['bars_default'], disabled=use_default_bars)
            duration_seconds = None
        else:
            col_min, col_sec = st.columns(2)
            with col_min:
                minutes = st.number_input("Minuti", min_value=0, max_value=30, value=3)
            with col_sec:
                seconds = st.number_input("Secondi", min_value=0, max_value=59, value=0)
            duration_seconds = (minutes * 60) + seconds
            bars = None
    seed = st.number_input("Seed", min_value=1, max_value=99999, value=42)

st.markdown("---")

if st.button("Genera MIDI", type="primary", use_container_width=True):
    if not scratch and not uploaded_file:
        st.error("Carica prima un file MIDI!")
    else:
        with st.spinner("Generazione in corso..."):
            try:
                if scratch:
                    rng = random.Random(seed)
                    s_root = rng.randrange(12) if key_choice == "Random" else NOTE_NAMES.index(key_choice)
                    s_name = rng.choice(list(SCALES)) if scale_choice == "Random" else scale_choice
                    dna, file_bytes, notes_data = (s_root, SCALES[s_name]), None, []
                    src_name = f"da zero ({NOTE_NAMES[s_root]} {s_name})"
                else:
                    dna = None
                    file_bytes = io.BytesIO(uploaded_file.getvalue())
                    notes_data = extract_notes(file_bytes)
                    src_name = uploaded_file.name
                if not scratch and not notes_data:
                    st.error("Il file MIDI non contiene note melodiche (i canali batteria vengono ignorati).")
                else:
                    final_bpm = seeded_bpm(genre, g_defaults, seed) if use_default_bpm else bpm
                    if duration_mode == "Minuti:Secondi" and duration_seconds:
                        odd_ok = uses_odd_meter(mode, submode, bool(notes_data))
                        raw_bars = (duration_seconds * final_bpm) / 60 * 4 / avg_bar_sixteenths(g_defaults, odd_ok)
                        _u = timeline_unit(g_defaults['timeline'])
                        final_bars = int(round(raw_bars / _u) * _u)  # arrotonda all'unita' della struttura
                        final_bars = max(min_bars(g_defaults), final_bars)
                        st.info(f"Durata calcolata: {final_bars} battute (per coprire ~{duration_seconds} secondi a {final_bpm} BPM)")
                    else:
                        final_bars = g_defaults['bars_default'] if use_default_bars else bars

                    _u = timeline_unit(g_defaults['timeline'])
                    norm_bars = max(min_bars(g_defaults), (int(final_bars) // _u) * _u)
                    if norm_bars != final_bars:
                        st.info(f"Battute allineate alla struttura del genere: {norm_bars}")
                        final_bars = norm_bars

                    if mode == "minimal":
                        tracks, root, scale = generate_minimal(notes_data, dict(g_run, transitions=use_trans), submode, final_bars, seed, dna=dna)
                        headers = {}
                    else:
                        requested_bars = final_bars
                        if scratch:
                            tracks, root, scale, headers, final_bars = generate_from_scratch(dict(g_run, transitions=use_trans), dna, final_bars, seed, split_drums)
                        else:
                            file_bytes.seek(0)
                            tracks, root, scale, headers, final_bars = generate_multitrack(file_bytes, dict(g_run, transitions=use_trans), submode, final_bars, seed, split_drums)
                        if final_bars != requested_bars:
                            st.info(f"Durata allineata: {final_bars} battute (richieste: {requested_bars})")

                    label = f"{genre} - {mode}/{submode}"
                    meter_plan = plan_meter(g_defaults, final_bars, uses_odd_meter(mode, submode, bool(notes_data)))
                    _, sections_now = compute_structure(final_bars, g_run.get('timeline'), seed)
                    use_cc = auto_cc and not (mode == 'multitrack' and submode == 'faithful')   # in Faithful le tracce sono quelle originali
                    automation = build_automation(sections_now, meter_plan, tracks, g_defaults.get('bass_style')) if use_cc else None
                    markers = section_markers(sections_now, meter_plan) if add_markers else None
                    midi_buffer = build_midi_file(tracks, final_bpm, mode, submode, headers, label=label, key_name=_compute_key_signature(root, scale), meter_plan=meter_plan, automation=automation, markers=markers)
                    report_text = generate_report(tracks, genre, mode, submode, final_bpm, final_bars, seed, root, scale, duration_mode, duration_seconds, src_name, meter_plan, vary_genre(g_run, seed, genre), (bool(use_cc), bool(add_markers)))

                    st.session_state.generated = {
                        'tracks': tracks, 'root': root, 'scale': scale, 'headers': headers,
                        'bars': final_bars, 'bpm': final_bpm, 'midi_bytes': midi_buffer.getvalue(),
                        'report_text': report_text, 'label': label, 'mode': mode,
                        'submode': submode, 'genre': genre, 'duration_mode': duration_mode,
                        'duration_seconds': duration_seconds, 'original_filename': src_name
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
st.caption("MIDI Forge Universale | Standard General MIDI | Struttura per genere a strati | 100% Open Source & Free")

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
    'acid': {'bpm_default': 135, 'bars_default': 96, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0, 'struct': (16, 8, 8, 32, 16)},
    'ambient': {'bpm_default': 80, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.15, 'swing': 0.0, 'struct': (16, 16, 16, 48, 16)},
    'armonico': {'bpm_default': 100, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.7, 'swing': 0.1, 'struct': (8, 8, 8, 24, 8)},
    'breakcore': {'bpm_default': 200, 'bars_default': 56, 'kick': [1,0,0,1, 0,1,0,0, 1,0,1,0, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,1,0,0, 1,0,0,1], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,0, 0,1,0,1], 'arp_density': 0.8, 'swing': 0.05, 'struct': (8, 8, 8, 16, 8)},
    'commerciale_90s': {'bpm_default': 120, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'arp_density': 0.6, 'swing': 0.08, 'struct': (8, 16, 8, 16, 8)},
    'deep': {'bpm_default': 124, 'bars_default': 96, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.15, 'struct': (16, 8, 8, 32, 16)},
    'disco': {'bpm_default': 122, 'bars_default': 80, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.2, 'struct': (16, 16, 8, 16, 8)},
    'drone': {'bpm_default': 70, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.05, 'swing': 0.0, 'struct': (16, 16, 16, 48, 16)},
    'drum_n_bass': {'bpm_default': 174, 'bars_default': 120, 'kick': [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,1, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.7, 'swing': 0.0, 'struct': (16, 16, 8, 48, 16)},
    'dub_techno': {'bpm_default': 128, 'bars_default': 160, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0, 'struct': (32, 16, 16, 48, 16)},
    'edm_2000s': {'bpm_default': 128, 'bars_default': 104, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0, 'struct': (16, 8, 16, 32, 16)},
    'elettronico': {'bpm_default': 130, 'bars_default': 88, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0, 'struct': (16, 8, 8, 32, 8)},
    'funk': {'bpm_default': 112, 'bars_default': 60, 'kick': [1,0,0,1, 0,0,0,0, 1,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [2,1,1,1, 2,1,1,1, 2,1,1,1, 2,1,1,1], 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,1,0,0], 'ghost': [0,0,0,1, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.05, 'struct': (8, 16, 4, 16, 8)},
    'glitch': {'bpm_default': 128, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,1, 0,0,0,0, 1,0,0,0], 'arp_density': 0.95, 'swing': 0.1, 'struct': (8, 8, 8, 24, 8)},
    'harsh_noise': {'bpm_default': 100, 'bars_default': 72, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 1.0, 'swing': 0.0, 'struct': (8, 8, 8, 32, 8)},
    'hip_hop': {'bpm_default': 92, 'bars_default': 80, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.3, 'swing': 0.2, 'lazy': 0.12, 'struct': (8, 16, 8, 32, 8)},
    'idm': {'bpm_default': 135, 'bars_default': 76, 'kick': [1,0,0,1, 0,1,0,1, 0,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,0,1,0, 1,0,1,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.85, 'swing': 0.1, 'struct': (8, 12, 8, 28, 12)},
    'industrial': {'bpm_default': 135, 'bars_default': 80, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.7, 'swing': 0.0, 'struct': (8, 16, 8, 32, 8)},
    'lowercase': {'bpm_default': 104, 'bars_default': 120, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.05, 'swing': 0.0, 'struct': (16, 24, 8, 40, 16)},
    'microsound': {'bpm_default': 90, 'bars_default': 96, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.1, 'swing': 0.0, 'struct': (8, 16, 8, 40, 16)},
    'minimal': {'bpm_default': 126, 'bars_default': 72, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.3, 'swing': 0.0, 'struct': (8, 8, 8, 32, 8)},
    'minimal_techno': {'bpm_default': 130, 'bars_default': 96, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.5, 'swing': 0.0, 'struct': (16, 8, 8, 32, 16)},
    'minimalismo_ritmico': {'bpm_default': 115, 'bars_default': 96, 'kick': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.05, 'struct': (16, 12, 8, 32, 12)},
    'noise': {'bpm_default': 120, 'bars_default': 80, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 0.9, 'swing': 0.0, 'struct': (8, 8, 8, 40, 8)},
    'onkyo': {'bpm_default': 50, 'bars_default': 128, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.02, 'swing': 0.0, 'struct': (16, 24, 8, 40, 24)},
    'r&b': {'bpm_default': 95, 'bars_default': 80, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,1], 'arp_density': 0.55, 'swing': 0.2, 'lazy': 0.12, 'struct': (12, 16, 8, 24, 8)},
    'reggaeton': {'bpm_default': 95, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,1,0, 0,1,0,0, 0,0,1,0, 0,1,0,0], 'clap': [0]*16, 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.0, 'struct': (8, 8, 8, 24, 8)},
    'sperimentale': {'bpm_default': 100, 'bars_default': 76, 'kick': [1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,1,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,1,0,0, 1,0,0,1, 0,0,1,0, 1,0,0,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,1], 'arp_density': 0.7, 'swing': 0.1, 'struct': (8, 16, 8, 24, 12)},
    'soul': {'bpm_default': 95, 'bars_default': 60, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,1, 0,0,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.25, 'lazy': 0.08, 'struct': (4, 16, 8, 16, 12)},
    'synthpop': {'bpm_default': 120, 'bars_default': 64, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.75, 'swing': 0.0, 'struct': (8, 16, 8, 16, 8)},
    'techno': {'bpm_default': 132, 'bars_default': 152, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0, 'struct': (32, 16, 8, 48, 16)},
    'trap': {'bpm_default': 140, 'bars_default': 72, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0, 'struct': (8, 16, 8, 24, 8)},
    'trance': {'bpm_default': 140, 'bars_default': 152, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1]*16, 'arp_density': 0.9, 'swing': 0.0, 'struct': (32, 24, 16, 32, 16)},
    'underground': {'bpm_default': 135, 'bars_default': 88, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.1, 'struct': (8, 16, 8, 32, 16)},
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

# ================= STRUTTURA DJ-FRIENDLY (condivisa da tutte le modalità) =================

SECTION_LABELS = {'intro': 'INTRO', 'break1': 'BREAK 1', 'build': 'BUILD-UP', 'drop': 'DROP', 'break2': 'BREAK 2', 'outro': 'OUTRO'}

DEFAULT_STRUCT = (8, 8, 8, 24, 8)   # (intro/outro, break1, build, drop, break2) in battute

def compute_structure(bars, struct=None):
    """Divide il brano in INTRO / BREAK 1 / BUILD-UP / DROP / BREAK 2 / OUTRO (sempre multipli di 4 battute).
    INTRO e OUTRO sono solo batteria. Le proporzioni vengono dal profilo del genere (g['struct'] =
    intro/outro, break1, build, drop, break2 in battute): a durata di default si ottengono esattamente quelle lunghezze,
    con altre durate le sezioni scalano in proporzione."""
    edge, *w = struct or DEFAULT_STRUCT
    bars = max(16, (int(bars) // 4) * 4)
    while edge > 4 and bars - 2 * edge < bars * 0.5:   # il centro del brano resta almeno metà
        edge -= 4
    edge = max(4, edge)
    units = (bars - 2 * edge) // 4
    order = ['break1', 'build', 'drop', 'break2']
    tot = float(sum(w))
    weights = {k: w[i] / tot for i, k in enumerate(order)}
    alloc = {k: 0 for k in order}
    for k in ['drop', 'build', 'break1', 'break2'][:units]:
        alloc[k] = 1
    for _ in range(units - sum(alloc.values())):
        k = max(order, key=lambda x: weights[x] * units - alloc[x])
        alloc[k] += 1
    sections, pos = [('intro', 0, edge)], edge
    for k in order:
        if alloc[k]:
            sections.append((k, pos, alloc[k] * 4)); pos += alloc[k] * 4
    sections.append(('outro', pos, bars - pos))
    return bars, sections

def section_map(sections, bars):
    """Per ogni battuta: (sezione, indice nella sezione, lunghezza sezione)."""
    return [(name, i, length) for name, _s, length in sections for i in range(length)][:bars]

def _structure_line(bars, struct=None):
    _, sections = compute_structure(bars, struct)
    return "   " + " -> ".join(f"[ {SECTION_LABELS[n]} {l} batt. ]" for n, _s, l in sections)

def is_drumless(g):
    return not (any(g['kick']) or any(g['hat']) or any(g.get('snare', [0] * 16)))

def eff_section(name, drumless):
    # generi senza batteria (ambient, drone...): intro/outro suonano pad/arp invece del solo drum
    return 'break1' if drumless and name in ('intro', 'outro') else name

def _note(ev, tick, dur, pitch, vel, ch):
    pitch = max(0, min(127, int(pitch)))
    ev.append({'tick': int(tick), 'type': 'on', 'pitch': pitch, 'vel': max(1, min(127, int(vel))), 'channel': ch})
    ev.append({'tick': int(tick + max(1, int(dur))), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': ch})

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

def build_drum_events(g, secmap):
    """Il ritmo non si ferma mai. INTRO/OUTRO/BREAK: kick + hat (nei break la melodia entra sopra il groove, senza snare/clap).
    BUILD-UP: kick + rullata di snare crescente. DROP: kit completo, open-hat, fill ogni 8 battute, percussioni."""
    if is_drumless(g): return []
    ev, q, R = [], TICKS_BEAT // 4, random.randint
    snare_p, clap_p = g.get('snare', [0] * 16), g.get('clap', [0] * 16)
    ghost_p, lazy = g.get('ghost', [0] * 16), int(g.get('lazy', 0) * (TICKS_BEAT // 4))   # snare dietro la griglia (hip hop, R&B, soul)
    for bar, (sec, idx, length) in enumerate(secmap):
        base = bar * 4 * TICKS_BEAT
        edge = sec in ('intro', 'outro')
        drop = sec == 'drop'
        fill_bar = drop and idx % 8 == 7
        open_bar = drop and idx % 4 == 2
        roll_bars = min(4, length)
        in_roll = sec == 'build' and idx >= length - roll_bars
        rr = idx - (length - roll_bars)
        roll_skip = [4, 2, 2, 1][-roll_bars:][rr] if in_roll else 0
        for s in range(16):
            tick = base + s * q
            sw = int(g['swing'] * q) if s % 2 == 1 else 0
            # KICK (solo dove il pattern del genere lo prevede)
            if g['kick'][s]:
                if sec not in ('build', 'drop'): vel = (110 + R(0, 5)) if s % 4 == 0 else (95 + R(0, 10))
                else:    vel = (120 + R(0, 5)) if s % 4 == 0 else (100 + R(0, 10))
                if s in (0, 8): vel += 10
                _note(ev, tick, q // 2, GM_KICK, vel, DRUM_CH)
            # HI-HAT (open-hat sui levare nel drop per dare respiro)
            if g['hat'][s]:
                if edge: hv = 65 + R(0, 15)
                elif sec in ('build', 'drop'): hv = 75 + R(0, 20)
                else: hv = 58 + R(0, 14)
                hv += {2: 18, 3: -28}.get(g['hat'][s], 0)    # 2 = accento, 3 = ghost
                if hv:
                    op = open_bar and s in (6, 14)
                    _note(ev, tick + sw, (TICKS_BEAT // 2) if op else q // 2,
                          GM_HAT_OPEN if op else GM_HAT_CLOSED, hv + (15 if op else 0), DRUM_CH)
            # SNARE / CLAP / FILL / PERCUSSIONI
            if drop:
                if fill_bar and s >= 12:
                    _note(ev, tick, q // 2, GM_SNARE if s % 2 == 0 else GM_TOM_HIGH, 70 + (s - 12) * 15, DRUM_CH)
                else:
                    if snare_p[s]: _note(ev, tick + sw + lazy, q // 2, GM_SNARE, 105 + R(0, 10), DRUM_CH)
                    elif ghost_p[s] and random.random() < 0.65: _note(ev, tick + sw, q // 2, GM_SNARE, 28 + R(0, 16), DRUM_CH)
                    if clap_p[s]:  _note(ev, tick + sw + lazy, q // 2, GM_CLAP, 90 + R(0, 10), DRUM_CH)
                    if s % 2 == 1 and random.random() < 0.15:
                        _note(ev, tick + sw, q // 2, GM_RIMSHOT if random.random() < 0.5 else GM_TOM_HIGH, 50 + R(0, 40), DRUM_CH)
            elif sec == 'build':
                if in_roll:
                    if s % roll_skip == 0:
                        _note(ev, tick, q // 2, GM_SNARE, 55 + int(70 * (rr * 16 + s) / (roll_bars * 16)), DRUM_CH)
                elif snare_p[s]:
                    _note(ev, tick + sw, q // 2, GM_SNARE, 80 + R(0, 10), DRUM_CH)
            elif not edge and idx >= length // 2 and s % 2 == 1 and random.random() < 0.10:
                _note(ev, tick + sw, q // 2, GM_RIMSHOT, 45 + R(0, 20), DRUM_CH)
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
    bars, sections = compute_structure(bars, g.get('struct'))
    secmap = section_map(sections, bars)
    drumless = is_drumless(g)
    q, bt = TICKS_BEAT // 4, 4 * TICKS_BEAT
    root, scale = dna or extract_dna(notes_data)
    n = len(scale)
    tracks = {'bass': [], 'arp': [], 'drums': build_drum_events(g, secmap)}
    bass_gap = _gaps([s for s in range(16) if g['bass'][s]]) if any(g['bass']) else {}
    remix = (submode == 'extract') and bool(notes_data)

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
        bass_prog = [0, 0, pick(), pick()]
    arp_counter = 0

    for bar, (sec, idx, length) in enumerate(secmap):
        mel = eff_section(sec, drumless)
        if mel in ('intro', 'outro'): continue
        base = bar * bt
        ramp = idx / max(1, length - 1)
        factor = {'break1': 0.5, 'break2': 0.5, 'build': 0.85, 'drop': 1.0}[mel]
        arp_vel = {'break1': 55, 'break2': 55, 'build': 62 + int(18 * ramp), 'drop': 72}[mel]
        if remix:
            ob, pool = _pool_at(pools, first_b, last_b, first_b + idx % loop_bars)
            bar_tones = sorted({_pc_pitch(p % 12, 60) for _s, _e, p in pool})
            tones = bar_tones + [t + 12 for t in bar_tones]
        elif bar % 4 == 0 and bar > 0:
            op = random.choice(['transpose', 'invert', 'drop'])
            if op == 'transpose': motif = [(x + 1) % n if x is not None else None for x in motif]; m_cur = motif
            elif op == 'invert': motif = list(reversed(motif)); m_cur = motif
            else: m_cur = [None if random.random() < 0.3 else x for x in motif]

        for s in range(16):
            tick = base + s * q
            sw = int(g['swing'] * q) if s % 2 == 1 else 0
            t_abs = (ob * bt + s * q) if remix else 0

            # BASSO (build-up: solo sui battiti; drop: pattern completo del genere)
            if mel in ('build', 'drop') and g['bass'][s] and (mel == 'drop' or s % 4 == 0):
                if remix:
                    snd = [p for st, en, p in pool if st <= t_abs < en] or [p for _s, _e, p in pool]
                    pc = min(snd) % 12
                else:
                    pc = (root + scale[(bass_prog[bar % 4] if random.random() < 0.8 else pick()) % n]) % 12
                _note(tracks['bass'], tick, bass_gap[s] * q - 15, _bass_pitch(pc), 95 + (5 if s % 4 == 0 else 0), 0)

            # SYNTH / ARP
            av = arp_vel + random.randint(0, 8)
            if remix:
                onsets = [p for st, en, p in pool if st == t_abs]
                if onsets and random.random() < (1.0 if mel in ('build', 'drop') else 0.6):
                    _note(tracks['arp'], tick + sw, q - 15, _fold(max(onsets)), av, 1)
                elif tones and random.random() < g['arp_density'] * 0.5 * factor:
                    _note(tracks['arp'], tick + sw, q - 15, tones[arp_counter % len(tones)], av, 1)
                    arp_counter += 1
            elif m_cur[s] is not None and random.random() < factor:
                _note(tracks['arp'], tick + sw, q - 20, _pc_pitch((root + scale[m_cur[s] % n]) % 12, 60), av, 1)

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
               ('drum_clap', {GM_CLAP}), ('drum_perc', {GM_RIMSHOT, GM_TOM_HIGH})]
DRUM_TRACK_NAMES = {'drums': 'Drums', 'drum_kick': 'Kick', 'drum_snare': 'Snare', 'drum_hat': 'Hat', 'drum_clap': 'Clap', 'drum_perc': 'Perc'}

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
    drumless = is_drumless(g)
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
    for bar, (sec, idx, length) in enumerate(secmap):
        mel = eff_section(sec, drumless)
        if mel in ('intro', 'outro'): continue
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

def _arrange_generative(g, root, scale, secmap, tracks):
    """GENERATIVE: ignora le note originali, usa solo tonalità/scala (DNA). 7 ruoli + batteria,
    ognuno attivo solo nelle sezioni dove ha senso."""
    q, bt = TICKS_BEAT // 4, 4 * TICKS_BEAT
    drumless = is_drumless(g)
    scale = _tame_scale(scale)
    n = len(scale)
    pc_of = lambda d: (root + scale[d % n]) % 12
    for role in ('sub_bass', 'bassline', 'pad', 'chords', 'arp', 'lead', 'fx_perc'): tracks[role] = []
    progs = [[0, 0, 3, 4], [0, 5, 3, 4], [0, 3, 5, 4], [0, 2, 3, 4], [0, 4, 5, 3]]
    prog_a, prog_b = random.sample(progs, 2)
    bass_steps = [s for s in range(16) if g['bass'][s]]
    bass_gap = _gaps(bass_steps) if bass_steps else {}
    lead_base = [random.randrange(n) if random.random() < 0.45 else None for _ in range(16)]
    lead = lead_base
    arp_mode, R = 'up', random.randint

    for bar, (sec, idx, length) in enumerate(secmap):
        mel = eff_section(sec, drumless)
        if mel in ('intro', 'outro'): continue
        base = bar * bt
        if bar % 4 == 0:
            arp_mode = random.choice(['up', 'updown', 'rand'])
            if bar > 0:
                op = random.choice(['transpose', 'invert', 'drop'])
                if op == 'transpose': lead_base = [(x + 1) % n if x is not None else None for x in lead_base]; lead = lead_base
                elif op == 'invert': lead_base = list(reversed(lead_base)); lead = lead_base
                else: lead = [None if random.random() < 0.3 else x for x in lead_base]
        d = (prog_a if (bar // 4) % 2 == 0 else prog_b)[bar % 4]
        cpcs = [pc_of(d), pc_of(d + 2), pc_of(d + 4)]
        rpc = cpcs[0]
        ramp = idx / max(1, length - 1)
        half = idx >= length // 2

        # SUB BASS: una nota lunga per battuta (build 2a metà, drop)
        if mel == 'drop' or (mel == 'build' and half):
            _note(tracks['sub_bass'], base, bt - 20, _pc_pitch(rpc, 24), 100, 0)
            # BASSLINE: pattern del genere (build: solo sui battiti)
            for s in bass_steps:
                if mel == 'build' and s % 4: continue
                pc = rpc if random.random() < 0.8 else random.choice(cpcs[1:])
                _note(tracks['bassline'], base + s * q, bass_gap[s] * q - 15, _pc_pitch(pc, 36), 95 + (5 if s % 4 == 0 else 0), 1)

        # PAD: accordo lungo in tutte le sezioni melodiche
        pad_vel = {'break1': 50, 'break2': 55, 'build': 55 + int(15 * ramp), 'drop': 62}[mel]
        for pc in cpcs: _note(tracks['pad'], base, bt - 10, _pc_pitch(pc, 48), pad_vel, 2)

        # CHORDS: stab sui levare (drop), sui battiti (build), accordi lunghi (break 2)
        if mel == 'drop': c_steps, c_dur, c_vel = [2, 6, 10, 14], q + q // 2, 80
        elif mel == 'build': c_steps, c_dur, c_vel = [0, 4, 8, 12], q * 2, 65 + int(25 * ramp)
        elif mel == 'break2': c_steps, c_dur, c_vel = [0, 8], 2 * TICKS_BEAT - 20, 58
        else: c_steps, c_dur, c_vel = [], 0, 0
        for s in c_steps:
            if mel == 'drop' and random.random() > 0.85: continue
            for pc in cpcs: _note(tracks['chords'], base + s * q, c_dur, _pc_pitch(pc, 55), c_vel + R(0, 8), 3)

        # ARP sulle note dell'accordo (densità del genere, ridotta nei break)
        tones = sorted(_pc_pitch(pc, 60) + 12 * k for pc in cpcs for k in (0, 1))
        factor = {'break1': 0.5, 'break2': 0.5, 'build': 0.85 + 0.15 * ramp, 'drop': 1.0}[mel]
        a_vel = {'break1': 52, 'break2': 52, 'build': 58 + int(20 * ramp), 'drop': 72}[mel]
        L = len(tones)
        for s in range(16):
            if random.random() < min(1.0, g['arp_density'] * factor):
                if arp_mode == 'up': i = s % L
                elif arp_mode == 'updown':
                    k = s % (2 * (L - 1)); i = k if k < L else 2 * (L - 1) - k
                else: i = random.randrange(L)
                sw = int(g['swing'] * q) if s % 2 == 1 else 0
                _note(tracks['arp'], base + s * q + sw, q - 10, tones[i], a_vel + R(0, 8), 4)

        # LEAD: motivo nel drop, versione rada nel break 2
        l_steps = [s for s, v in enumerate(lead) if v is not None]
        if mel in ('drop', 'break2') and l_steps:
            gaps = _gaps(l_steps)
            for s in l_steps:
                if mel == 'break2' and s % 4: continue
                du = gaps[s] * q - 10 if mel == 'drop' else 2 * TICKS_BEAT - 10
                _note(tracks['lead'], base + s * q, du, _pc_pitch(pc_of(lead[s]), 67), 88 if mel == 'drop' else 70, 5)

        # FX: impatto a inizio sezione + riser nelle ultime 2 battute del build-up
        if idx == 0:
            _note(tracks['fx_perc'], base, bt - 10, _pc_pitch(rpc, 72), 110 if mel == 'drop' else 80, 6)
        riser = min(2, length)
        if mel == 'build' and idx >= length - riser:
            k0 = (idx - (length - riser)) * 8
            for k, s in enumerate(range(0, 16, 2)):
                j = k0 + k
                _note(tracks['fx_perc'], base + s * q, q * 2 - 10,
                      _pc_pitch(root, 60) + scale[j % n] + 12 * (j // n), 60 + int(50 * (j + 1) / (riser * 8)), 6)

def generate_multitrack(mid_file_bytes, g, submode, bars, seed, split_drums=True):
    random.seed(seed)
    bars, sections = compute_structure(bars, g.get('struct'))
    secmap = section_map(sections, bars)
    mid = mido.MidiFile(file=mid_file_bytes)
    all_notes = notes_from_midi(mid)
    if not all_notes:
        raise ValueError("Il file MIDI non contiene note melodiche (i canali batteria vengono ignorati).")
    root, scale = extract_dna(all_notes)
    tracks, headers = {}, {}
    if submode == 'faithful':
        _arrange_faithful(mid, all_notes, g, secmap, tracks, headers, root, scale)
    else:
        _arrange_generative(g, root, scale, secmap, tracks)
    drums = build_drum_events(g, secmap)
    if drums: tracks['drums'] = drums
    tracks = {k: v for k, v in tracks.items() if v}
    if split_drums and 'drums' in tracks:
        tracks = split_drum_track(tracks)
    return tracks, root, scale, headers, bars

def generate_from_scratch(g, dna, bars, seed, split_drums=True):
    """Multitraccia generativa senza MIDI originale: tonalità e scala scelte (o random)."""
    random.seed(seed)
    root, scale = dna
    bars, sections = compute_structure(bars, g.get('struct'))
    secmap = section_map(sections, bars)
    tracks, headers = {}, {}
    _arrange_generative(g, root, scale, secmap, tracks)
    drums = build_drum_events(g, secmap)
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

def build_midi_file(tracks, bpm, mode, submode, headers=None, label=None, key_name=None):
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
    if key_name:
        try: t_tempo.append(mido.MetaMessage('key_signature', key=key_name, time=0))
        except ValueError: pass
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
    report.extend([f"   Hat (GM 42):   {''.join('.' if not x else ('+' if x == 3 else '#') for x in g['hat'])}  (+ = ghost)", f"   Bass:          {''.join(['#' if x else '.' for x in g['bass']])}", f"   Ghost snare: {''.join(['#' if x else '.' for x in g.get('ghost', [0]*16)])}", f"   Swing: {g['swing'] * 100:.0f}%", f"   Densità Arp: {g['arp_density'] * 100:.0f}%", "", "STRUTTURA BRANO (DJ-Friendly)", _structure_line(bars, g.get('struct')), "", "TRACCE OUTPUT"])
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
    components.html(html_player, height=150)

# ================= INTERFACCIA STREAMLIT =================

if 'generated' not in st.session_state:
    st.session_state.generated = {'tracks': None, 'root': None, 'scale': None, 'headers': None, 'bars': None, 'bpm': None, 'midi_bytes': None, 'report_text': '', 'label': None, 'mode': None, 'submode': None, 'genre': None, 'duration_mode': None, 'duration_seconds': None, 'original_filename': None}

st.title("MIDI Forge Universale")
st.markdown("Trasforma qualsiasi file MIDI in 30+ generi musicali. Struttura DJ-Friendly adattata allo stile del genere: INTRO -> BREAK -> BUILD -> DROP -> BREAK -> OUTRO")

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
    if mode == "multitrack":
        split_drums = st.checkbox("Batteria su tracce separate (Kick / Snare / Hat / Clap)", value=True)

with col2:
    genre_list = sorted(GENRES.keys())
    genre = st.selectbox("Genere Musicale", genre_list, index=genre_list.index("techno"))
    g_defaults = GENRES[genre]
    st.caption('Struttura tipica:' + _structure_line(g_defaults['bars_default'], g_defaults.get('struct')))
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
                    final_bpm = g_defaults['bpm_default'] if use_default_bpm else bpm
                    if duration_mode == "Minuti:Secondi" and duration_seconds:
                        raw_bars = (duration_seconds * final_bpm) / 240
                        final_bars = int(round(raw_bars / 4) * 4)  # Arrotonda al multiplo di 4
                        final_bars = max(16, final_bars)
                        st.info(f"Durata calcolata: {final_bars} battute (per coprire ~{duration_seconds} secondi a {final_bpm} BPM)")
                    else:
                        final_bars = g_defaults['bars_default'] if use_default_bars else bars

                    norm_bars = max(16, (int(final_bars) // 4) * 4)
                    if norm_bars != final_bars:
                        st.info(f"Battute allineate al multiplo di 4: {norm_bars}")
                        final_bars = norm_bars

                    if mode == "minimal":
                        tracks, root, scale = generate_minimal(notes_data, g_defaults, submode, final_bars, seed, dna=dna)
                        headers = {}
                    else:
                        requested_bars = final_bars
                        if scratch:
                            tracks, root, scale, headers, final_bars = generate_from_scratch(g_defaults, dna, final_bars, seed, split_drums)
                        else:
                            file_bytes.seek(0)
                            tracks, root, scale, headers, final_bars = generate_multitrack(file_bytes, g_defaults, submode, final_bars, seed, split_drums)
                        if final_bars != requested_bars:
                            st.info(f"Durata allineata: {final_bars} battute (richieste: {requested_bars})")

                    label = f"{genre} - {mode}/{submode}"
                    midi_buffer = build_midi_file(tracks, final_bpm, mode, submode, headers, label=label, key_name=_compute_key_signature(root, scale))
                    report_text = generate_report(tracks, genre, mode, submode, final_bpm, final_bars, seed, root, scale, duration_mode, duration_seconds, src_name)

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
st.caption("MIDI Forge Universale | Standard General MIDI | Struttura DJ-Friendly | 100% Open Source & Free")

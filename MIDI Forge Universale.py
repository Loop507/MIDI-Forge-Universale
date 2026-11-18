import streamlit as st
import streamlit.components.v1 as components
import mido
import bisect
import itertools
import math
import random as _stdlib_random
import threading
import zlib
import io
import json
import re
import os
import tempfile
from pathlib import Path
from datetime import datetime
from collections import Counter

# ================= AUDIO TO MIDI (Basic Pitch - Opzionale) =================
try:
    from basic_pitch.inference import predict, Model
    from basic_pitch import ICASSP_2022_MODEL_PATH
    BASIC_PITCH_AVAILABLE = True
except ImportError:
    BASIC_PITCH_AVAILABLE = False

def audio_to_midi_notes(audio_bytes: bytes, bpm: int = 120) -> list[dict]:
    """
    Trascrive un file audio (WAV/MP3) in note MIDI usando Basic Pitch (Spotify).
    Ritorna una lista di note nel formato interno dell'app: {'tick': int, 'dur': int, 'pitch': int, 'vel': int, 'track': int}
    """
    if not BASIC_PITCH_AVAILABLE:
        raise ImportError("La libreria 'basic-pitch' non è installata. Esegui: pip install basic-pitch onnxruntime")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        tmp_audio.write(audio_bytes)
        tmp_audio_path = tmp_audio.name

    try:
        model = Model(ICASSP_2022_MODEL_PATH)
        model_output, note_events, sonif = predict(tmp_audio_path, model)
        
        seconds_per_beat = 60.0 / bpm
        ticks_per_second = TICKS_BEAT / seconds_per_beat
        
        notes_data = []
        for note in note_events:
            start_tick = int(note['start_time_s'] * ticks_per_second)
            dur_tick = max(120, int(note['duration_s'] * ticks_per_second)) # Minimo 1/4 di battuta
            pitch = int(note['pitch_midi'])
            velocity = int(note['amplitude'] * 127)
            
            if 24 <= pitch <= 108 and velocity > 20:
                notes_data.append({
                    'tick': start_tick,
                    'dur': dur_tick,
                    'pitch': pitch,
                    'vel': velocity,
                    'track': 0
                })
        
        return sorted(notes_data, key=lambda x: x['tick'])
    finally:
        if os.path.exists(tmp_audio_path):
            os.remove(tmp_audio_path)

# ================= THREAD-SAFE RANDOM =================
class _ThreadRandom:
    """Generatore casuale per thread: ogni sessione ha il suo flusso."""
    Random = _stdlib_random.Random
    SystemRandom = _stdlib_random.SystemRandom
    def __init__(self):
        self._loc = threading.local()
    def _rng(self):
        r = getattr(self._loc, 'r', None)
        if r is None:
            r = self._loc.r = _stdlib_random.Random()
        return r
    def __getattr__(self, name):
        return getattr(self._rng(), name)

class _ThreadOpts:
    """Opzioni modificate dall'interfaccia: una copia per thread."""
    def __init__(self, defaults):
        self._defaults, self._loc = dict(defaults), threading.local()
    def _opts(self):
        m = getattr(self._loc, 'm', None)
        if m is None:
            m = self._loc.m = dict(self._defaults)
        return m
    def get(self, key, default=None):
        return self._opts().get(key, default)
    def __getitem__(self, key):
        return self._opts()[key]
    def __setitem__(self, key, value):
        self._opts()[key] = value

random = _ThreadRandom()

# ================= CONFIGURAZIONE PAGINA =================
st.set_page_config(page_title="MIDI Forge Universale", page_icon="🎛️", layout="wide")

# ================= DATABASE DEI GENERI =================
GENRES = {
    'acid': {'bpm_default': 126, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0,  0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,1, 0,1,0,1, 1,0,1,0, 1,1,0,1], 'arp_density': 0.85, 'swing': 0.0},
    'afro_house': {'bpm_default': 122,  'bars_default': 192, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.08},
    'amapiano': {'bpm_default': 112, 'bars_default': 192, 'kick': [1,0,0,0, 1,0,0,0, 1,0, 0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [0,0,1,0, 0,1,1,0, 0,0,1,0, 0,1,0,0], 'ghost': [0 ]*16, 'arp_density': 0.25, 'swing': 0.16},
    'ambient': {'bpm_default': 80, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.15,  'swing': 0.0},
    'armonico': {'bpm_default': 100, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0, 0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.7, 'swing': 0.1},
    'breakcore': {'bpm_default': 200, 'bars_default': 52, 'kick': [1,0,0,1, 0 ,1,0,0, 1,0,1,0, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,1,0,0, 1,0,0,1], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,0, 0,1,0,1], 'arp_density': 0.8, 'swing': 0.05, 'meter': [ '7/8', '7/8', '4/4', '13/8']},
    'chiptune': {'bpm_default': 120, 'bars_default': 48, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.8, 'swing': 0.0, 'arp_sub': 2},
    'commerciale_90s': {'bpm_default': 120, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1 ,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'arp_density': 0.6, 'swing': 0.08},
    'deep': {'bpm_default': 124, 'bars_default':  92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0 ,0,1,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.15, 'open_pad': True},
    'disco': {'bpm_default': 122, 'bars_default': 76, 'kick': [1,0,0,0, 1,0 ,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,1,  0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.2},
    'drone': {'bpm_default': 70, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1,0,0,0,  0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.05, 'swing': 0.0},
    'drum_n_bass': {'bpm_default': 174, 'bars_default': 116, 'kick': [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,0,0,0], 'snare': [0, 0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,1, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.7, 'swing': 0.0},
    'dub_techno': {'bpm_default': 128, 'bars_default': 156, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0, 0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0},
    'dubstep': {'bpm_default': 140, 'bars_def ault': 144, 'kick': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3 ,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.25, 'swing': 0.0, 'roll32': True},
    'edm_2000s': {'bpm_default': 128, 'bars_default':  100, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1,  1,1,2,1], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'elettronico': {'bpm_default': 130, 'bars_default': 84, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0 ,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0 ,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'funk': {'bpm_default': 112, 'bars_default': 56, 'kick': [1,0,0,1, 0,0,0,0, 1,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0 ,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [2,1,1,1, 2,1,1,1, 2,1,1,1, 2,1,1,1], 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,1,0,0], 'ghost': [0,1,1,0, 0,1,0,1, 0,1,0,1, 0,1,1,1], 'arp_density': 0.6, 'swing': 0.05},
    'future_bass': {'bpm_default': 150, 'bars_default': 80, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3 ], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.5, 'swing': 0.0, 'chord_off': 2, 'hat_triplet': True, 'roll32': True},
    'glitch': {'bpm_default':  128, 'bars_default': 60, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,1, 0,0,0,0, 1,0,0,0], 'arp_density': 0.95, 'swing': 0.1},
    'hardstyle': {'bpm_default': 150, 'bars_default': 112, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0,  0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.5, 'swing': 0.0, 'lead_triplet': True},
    'harsh_noise': {'bpm_default': 100, 'bars_default': 68, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 1.0, 'swing': 0.0, 'meter': ['7/8', '9/8' , '4/4']},
    'hip_hop': {'bpm_default': 92, 'bars_default': 76, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3,  1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.2, 'lazy': 0.12},
    'house_90s': {'bpm_default': 122, 'bars_default' : 112, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,2,0, 0,0,2,0, 0,0,2,0, 0,0,2,0], 'bass': [0,0,1,0, 0 ,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.05},
    'hyperpop': {'bpm_default': 140, 'bars_default': 56, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,1,1,1, 1,0,1,1, 1,1,1,0, 1,1,1,1], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0,0,0,0, 0,0,0,1,  0,0,0,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.0, 'meter_sections': ['4/4', '4/4', '7/8', '3/4', '4/4', '4/4'], 'tempo_plan': [70, 140, 94, 120, 170, 70], 'hat_sub': True},
    'idm': {'bpm_default': 135, 'bars_default': 72, 'kick': [1,0,0,1, 0,1,0,1, 0,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,0,1,0, 1,0,1,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,1,0,0,  1,0,0,1, 0,0,1,0], 'arp_density': 0.85, 'swing': 0.1},
    'industrial': {'bpm_default': 135, 'bars_default': 76, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0 ,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.7, 'swing': 0.0},
    'jungle': {'bpm_default': 165,  'bars_default': 144, 'kick': [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass ': [0,1,1,1, 0,1,1,1, 0,1,1,1, 0,1,1,1], 'ghost': [0,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.2, 'swing': 0.15, 'chord_off': 2},
    'lowercase': {'bpm_default': 104, 'bars_ default': 116, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.05, 'swing': 0.0, 'meter': ['17/8']},
    'microsound': {'bpm_default': 90, 'bars_defaul t': 92, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.1, 'swing': 0.0},
    'minimal': {'bpm_default': 126, 'bars_default': 68, 'kick': [1,0,0,0, 1,0 ,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0. 3, 'swing': 0.0},
    'minimal_techno': {'bpm_default': 130, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1] *16, 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.5, 'swing': 0.0},
    'minimalismo_ritmico': {'bpm_default': 115, 'bars_default': 92, 'kick': [1,0,0,1, 0,1,0,0, 1,0 ,0,1, 0,0,1,0], 'snare': [0,0,1,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.6, 'swing ': 0.05, 'meter': ['11/8', '11/8', '15/8', '15/8']},
    'musique_concrete': {'bpm_default': 90, 'bars_default': 80, 'kick': [0]*16, 'snare': [0]*16, 'clap': [0]*16, 'hat': [0]*16, 'ba ss': [0]*16, 'ghost': [0]*16, 'arp_density': 0.2, 'swing': 0.0, 'meter': ['5/4', '7/8', '11/8', '3/4'], 'tempo_plan': [60, 72, 58, 90, 60], 'free_time': 240},
    'noise': {'bpm_defaul t': 120, 'bars_default': 76, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 0.9, 'swing': 0.0, 'meter': ['29/16', '4/4']},
    'onkyo': {'bpm_default':  50, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.02, 'swing': 0.0},
    'psytrance': {'bpm_default': 145, 'bars_default': 224,  'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [0,1,1,1, 0,1,1,1, 0,1,1,1, 0,1,1,1], 'ghost': [ 0]*16, 'arp_density': 0.8, 'swing': 0.0},
    'r&b': {'bpm_default': 95, 'bars_default': 76, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3 ], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,0], 'arp_density': 0.55, 'swing': 0.2, 'lazy': 0.12},
    'reggae': {'bpm_default': 76, 'bar s_default': 68, 'kick': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0]*16, 'hat': [3,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1 ,0,0,1, 1,0,0,0, 1,0,0,1, 1,0,0,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.03, 'lazy': 0.1, 'chord_off': 2, 'snare_note': 37},
    'reggaeton': {'bpm_default': 95, 'bars_defau lt': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,1, 0,0,1,0, 0,0,0,1, 0,0,1,0], 'clap': [0]*16, 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0,  0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.0},
    'jazz': {'bpm_default': 140, 'bars_default': 80, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'cla p': [0]*16, 'hat': [1,0,0,0, 1,0,2,0, 1,0,0,0, 1,0,2,0], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'ghost': [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.3, 'swing': 0 .0, 'lazy': 0.05, 'chord_off': 0, 'hat_note': 51, 'kick_scale': 0.45, 'pedal_hat': True},
    'soul': {'bpm_default': 95, 'bars_default': 60, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0, 0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,0, 0,0,1,0, 0 ,0,0,0], 'arp_density': 0.6, 'swing': 0.25, 'lazy': 0.08, 'chord_off': 0},
    'soulful_house': {'bpm_default': 123, 'bars_default': 128, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],  'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,2,3, 1,3,2,3, 1,3,2,3, 1,3,2,3], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_dens ity': 0.3, 'swing': 0.15},
    'space_disco': {'bpm_default': 120, 'bars_default': 128, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'cl ap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'ghost': [0]*16, 'arp_density': 0.6, 'swing':  0.02},
    'sperimentale': {'bpm_default': 100, 'bars_default': 72, 'kick': [1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,1,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,1,0,0, 1,0,0, 1, 0,0,1,0, 1,0,0,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,1], 'arp_density': 0.7, 'swing': 0.1, 'meter': ['5/16', '7/16', '4/4']},
    'synthpop': {'bpm_default': 120, 'bars_defa ult': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1 ,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.75, 'swing': 0.0},
    'synthwave': {'bpm_default': 90, 'bars_default': 80, 'kick': [1,0,0,0, 1,0,0,0, 1,0, 0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1]*16, 'ghost': [0]*16, 'arp_density': 0.5, 'swi ng': 0.02},
    'techno': {'bpm_default': 132, 'bars_default': 148, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0 ,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [0,1,1,1, 0,1,1,1, 0,1,1,1, 0,1,1,1], 'arp_density': 0.75, 'swing': 0.0},
    'trance': {'bpm_default': 140,  'bars_default': 148, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [0, 0, 1, 0,  0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0,  0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0,  0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0,  0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0,  0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0], 'arp_density': 0.9, 'swing': 0.0},
    'trap': {'bpm_default': 140, 'bars_default': 68, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0, 0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0},
    'trip_hop': {'bpm_default': 80, 'bars_default': 88, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,0,3,0, 1,0,3 ,0, 1,0,3,0, 1,0,3,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0,0,1,0, 0,0,0,0, 0,0,1,0, 0,0,1,0], 'arp_density': 0.3, 'swing': 0.2, 'lazy': 0.12},
    'uk_garage': {' bpm_default': 132, 'bars_default': 88, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,3,1,3, 1,3,1,3, 1,3,1, 3, 1,3,1,3], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.4, 'swing': 0.15},
    'underground': {'bpm_default': 135, 'bars_default': 84, 'kick': [1,0 ,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0]*16, 'hat': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0, 0,1,0], 'arp_density': 0.65, 'swing': 0.1, 'snare_shift': True},
    'vaporwave': {'bpm_default': 70, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0, 0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [3,0,3,0, 3,0,3,0, 3,0,3,0, 3,0,3,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swin g': 0.2, 'lazy': 0.1},
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
SCALES = {'Minore naturale': [0,2,3,5,7,8,10], 'Maggiore': [0,2,4,5,7,9,11], 'Dorico': [0,2,3,5,7,9,10], 'Frigio': [0,1,3,5,7,8,10],
'Misolidio': [0,2,4,5,7,9,10], 'Minore armonica': [0,2,3,5,7,8,11], 'Pentatonica minore': [0,3,5,7,10]}
TICKS_BEAT = 480

# ================= STRUTTURE DI FRASE (PHRASE LENGTHS) =================
PHRASE_STRUCTURES = {
    'techno': {'drop': 16, 'break': 16, 'build': 8, 'default': 16},
    'minimal': {'default': 16}, 'minimal_techno': {'default': 16}, 'acid': {'default': 8}, 'dub_techno': {'default': 16},
    'house_90s': {'default': 8}, 'deep': {'default': 8}, 'disco': {'default': 8}, 'funk': {'default': 8}, 'synthpop': {'default': 8}, 'commerciale_90s': {'default': 8},
    'trance': {'drop': 16, 'break': 32, 'build': 16, 'default': 16}, 'psytrance': {'default': 16}, 'ambient': {'default': 32}, 'drone': {'default': 32},
    'breakcore': {'default': 4}, 'idm': {'default': 8}, 'glitch': {'default': 8},
    'default': {'default': 8}
}

def get_phrase_config(genre: str, section_name: str, section_length: int) -> tuple[int, int]:
    genre_cfg = PHRASE_STRUCTURES.get(genre, PHRASE_STRUCTURES['default'])
    if section_name in ('break1', 'break2', 'intro', 'outro'): sec_type = 'break'
    elif section_name == 'build': sec_type = 'build'
    elif section_name == 'drop': sec_type = 'drop'
    else: sec_type = 'default'
    
    phrase_len = genre_cfg.get(sec_type, genre_cfg.get('default', 8))
    phrase_len = min(phrase_len, section_length)
    if phrase_len == 0: phrase_len = 1
    subphrase_len = max(1, phrase_len // 2)
    return phrase_len, subphrase_len

def generate_macro_motif(phrase_len: int, scale_len: int, rng: _stdlib_random.Random) -> list[int | None]:
    contour = []
    current_interval = 0
    for bar in range(phrase_len):
        bar_motif = []
        for step in range(4):
            if rng.random() < 0.30:
                bar_motif.append(None)
            else:
                move = rng.choices([-2, -1, 0, 1, 2, 3, 4, -3, -4], weights=[10, 30, 15, 30, 10, 5, 2, 5, 2], k=1)[0]
                current_interval += move
                current_interval = max(-7, min(7, current_interval))
                bar_motif.append(current_interval)
        contour.extend(bar_motif)
    return contour

def generate_coherent_melody_bar(bar_idx: int, chord_degrees: set[int], scale: list[int], root: int, 
                                 rhythmic_motif: list[bool], prev_motif: list[int | None] | None, is_answer: bool, n: int) -> list[tuple[int, int, int]]:
    chord_tones = {d % n for d in chord_degrees}
    out = []
    active_steps = [i for i, active in enumerate(rhythmic_motif) if active]
    if not active_steps: return out
    
    current_pitch = prev_motif[-1] if prev_motif and prev_motif[-1] is not None else 0
    
    for i, step in enumerate(active_steps):
        is_strong_beat = (step % 4 == 0)
        if is_strong_beat:
            valid_targets = [d for d in range(n + 2) if d % n in chord_tones]
        else:
            valid_targets = list(range(n + 2))
            
        if current_pitch is not None:
            valid_targets.sort(key=lambda x: (abs(x - current_pitch), x))
            chosen = valid_targets[_stdlib_random.randint(0, min(1, len(valid_targets) - 1))] if _stdlib_random.random() < 0.7 else _stdlib_random.choice(valid_targets)
        else:
            chosen = _stdlib_random.choice(valid_targets)
            
        if is_answer and step == active_steps[-1]:
            chosen = 0 
            
        current_pitch = chosen
        next_step = active_steps[i + 1] if i + 1 < len(active_steps) else 16
        duration = next_step - step
        out.append((step, chosen, duration))
    return out

# ================= STANDARD GENERAL MIDI =================
DRUM_CH = 9
GM_KICK = 36
GM_SNARE = 38
GM_CLAP = 39
GM_HAT_CLOSED = 42
GM_HAT_OPEN = 46
GM_RIDE = 51
GM_TOM_HIGH = 50
GM_RIMSHOT = 37

# ================= FUNZIONI AUSILIARIE =================
def _root_to_key_name(root, is_minor):
    return NOTE_NAMES[root] + ('m' if is_minor else '')

def _is_minor_scale(scale):
    return 3 in scale

_KEY_MAJOR = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
_KEY_MINOR = ['Cm', 'C#m', 'Dm', 'Ebm', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'Bbm', 'Bm']

def _compute_key_signature(root, scale):
    return (_KEY_MINOR if _is_minor_scale(scale) else _KEY_MAJOR)[root % 12]

def _pair_events(events):
    pending, out = {}, []
    for e in sorted(events, key=lambda x: (x['tick'], x['type'] != 'off')):
        key = (e.get('channel', 0), e['pitch'])
        if e['type'] == 'on':
            pending.setdefault(key, []).append(e)
        else:
            q = pending.get(key)
            if q:
                on = q.pop(0)
                s = int(on['tick'])
                out.append((s, max(int(e['tick']), s + 1), key[1], on['vel'], key[0]))
    return out

def _compute_note_durations(events):
    return [{'tick': s, 'dur': en - s, 'pitch': p, 'vel': v, 'channel': ch} for s, en, p, v, ch in _pair_events(events)]

def notes_from_midi(mid):
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
LAYER_TOKENS = frozenset('kick hat clap open perc bass bassl pad chords chordsl arp arpl lead leadl roll rolls fill event'.split())
EVENT = frozenset({'event'})
MELODIC = frozenset('bass bassl pad chords chordsl arp arpl lead leadl'.split())
DRUM_LAYERS = frozenset('kick hat clap open perc roll rolls fill'.split())
FAMILY = {'bass': 'bass', 'bassl': 'bass', 'pad': 'pad', 'chords': 'chords', 'chordsl': 'chords',
          'arp': 'arp', 'arpl': 'arp', 'lead': 'lead', 'leadl': 'lead'}
SYN_FACTOR = {'arp': 1.0, 'lead': 1.0, 'chords': 0.85, 'arpl': 0.5, 'leadl': 0.5, 'chordsl': 0.5, 'pad': 0.5}

TIMELINES = {
    'acid': [('Intro DJ 1', 8, 'kick'), ('Intro DJ 2', 8, 'kick hat'), ('Intro DJ 3', 16, 'kick hat bassl'), ('Groove building', 32, 'kick hat perc bass'), ('Main 1', 32, 'kick hat clap perc bass fill'), ('Breakdown', 16, 'bass pad'), ('Build-up', 8, 'hat bass pad roll'), ('Drop / Main 2', 48, 'kick hat clap open perc bass chordsl fill'), ('Outro 1', 8, 'kick hat clap perc bass'), ('Outro 2', 8, 'kick hat bass'), ('Outro 3', 8, 'kick')],
    'afro_house': [('Intro progressiva', 32, 'hat perc pad chordsl'), ('Build-up', 32, 'kick hat perc bass pad chordsl'), ('Peak / Main 1', 32, 'kick hat clap open perc bass pad chords lead'), ('Breakdown', 16, 'perc pad chords lead'), ('Main 2 / Secondo drop', 48, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 32, 'kick hat perc pad')],
    'amapiano': [('Intro atmosferica', 32, 'hat perc pad chordsl bassl'), ('Build', 32, 'kick hat perc bassl pad chords'), ('Groove principale', 48, 'kick hat clap perc bass pad chords lead'), ('Bridge', 32, 'hat perc pad chords leadl'), ('Secondo picco', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'hat perc bassl pad')],
    'ambient': [('Fade in', 32, 'pad'), ('Evoluzione 1', 32, 'pad chordsl'), ('Trasformazione', 32, 'chordsl leadl'), ('Sovrapposizione', 32, 'pad chordsl arp leadl'), ('Fade out', 32, 'pad')],
    'armonico': [('Intro armonica', 8, 'pad chordsl'), ('Sezione A', 16, 'kick hat clap bass chords leadl'), ("Sezione A' ", 8, 'kick hat clap bass pad chords lead arpl'), ('Sezione B', 16, 'kick hat clap bass chords lead arp'), ('Bridge / modulazione', 8, 'pad chordsl leadl'), ('Ritorno tema', 16, 'kick hat clap bass pad chords lead arp'), ('Outro', 24, 'pad chordsl')],
    'breakcore': [('Intro', 8, 'hat perc arpl leadl'), ('Sezione A', 16, 'kick hat clap perc bass fill'), ('Sezione B', 8, 'kick hat clap perc bass arpl fill'), ('Transizione', 8, 'hat clap perc bass rolls'), ('Sezione C', 16, 'kick hat clap perc bass arp lead fill'), ('Finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'chiptune': [('Intro', 8, 'hat arp'), ('Verse', 8, 'kick hat clap bass lead'), ('Chorus', 16, 'kick hat clap perc bass chords arp lead fill'), ('Bridge', 8, 'arp'), ('Chorus finale', 8, 'kick hat clap perc bass chords arp lead fill')],
    'commerciale_90s': [('Intro', 8, 'kick hat arpl'), ('Strofa 1', 16, 'kick hat clap bass chordsl leadl'), ('Pre-chorus', 8, 'kick hat clap bass pad roll'), ('Ritornello', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Strofa 2', 16, 'kick hat clap open bass chordsl leadl arpl'), ('Pre-chorus 2', 8, 'kick hat clap bass pad roll'), ('Ritornello 2', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Bridge', 8, 'pad chordsl bassl'), ('Ritornello finale', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'kick hat bass')],
    'deep': [('Intro DJ', 16, 'kick hat pad'), ('Groove base', 16, 'kick hat clap open bass pad'), ('Armonia', 16, 'kick hat clap open perc bass pad chords'), ('Hook / Main 1', 16, 'kick hat clap open perc bass pad chords arpl lead'), ('Breakdown breve', 8, 'kick hat perc pad chordsl'), ('Build-up soft', 8, 'kick hat open bass pad chordsl rolls'), ('Main 2', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro DJ', 16, 'kick hat bass')],
    'disco': [('Intro vamp', 32, 'kick hat open bass chords'), ('Strofa 1', 16, 'kick hat open clap bass chords leadl arpl'), ('Ritornello', 16, 'kick hat open clap perc bass chords arp lead fill'), ('Strofa 2', 16, 'kick hat open clap bass chords leadl arpl'), ('Ritornello 2', 16, 'kick hat open clap perc bass chords arp lead fill'), ('Breakdown strumentale', 16, 'kick hat open bass chords arp'), ('Ritornello finale', 16, 'kick hat open clap perc bass chords arp lead fill'), ('Outro vamp', 16, 'kick hat open bass chords')],
    'drone': [('Tono fondamentale', 32, 'pad'), ('Armoniche', 32, 'pad chordsl'), ('Morphing', 32, 'pad bass chordsl'), ('Dissolvenza', 32, 'pad')],
    'drum_n_bass': [('Intro', 32, 'hat pad leadl'), ('Tension / Build', 16, 'kick hat pad roll'), ('Drop 1', 32, 'kick hat clap bass fill'), ('Breakdown', 16, 'pad lead'), ('Build 2', 16, 'kick hat pad roll'), ('Drop 2', 32, 'kick hat clap perc bass arp lead fill'), ('Outro', 16, 'pad')],
    'dub_techno': [('Intro sommersa', 32, 'kick pad'), ('Groove dub', 32, 'kick hat open pad bass chords'), ('Evoluzione', 32, 'kick hat open pad bass chords perc'), ('Breakdown dub', 16, 'pad chords'), ('Ritorno', 32, 'kick hat open pad bass chords perc'), ('Outro', 16, 'kick pad')],
    'dubstep': [('Intro', 16, 'hat pad leadl'), ('Build-up', 16, 'hat pad roll'), ('Drop 1', 16, 'kick hat clap bass fill'), ('Mid-section', 16, 'kick hat clap perc bass arpl'), ('Breakdown', 16, 'pad lead'), ('Build 2', 16, 'kick hat pad roll'), ('Drop 2', 32, 'kick hat clap perc bass pad lead arp fill'), ('Outro', 16, 'pad')],
    'edm_2000s': [('Intro', 16, 'kick hat arpl'), ('Build 1', 16, 'kick hat pad arpl roll'), ('Drop 1', 32, 'kick hat clap open perc bass chords lead fill'), ('Breakdown', 16, 'pad lead'), ('Build 2', 16, 'kick hat pad chords roll'), ('Drop 2', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'kick hat bass')],
    'elettronico': [('Intro', 16, 'kick hat'), ('Build', 16, 'kick hat clap open bass'), ('Main / Drop', 32, 'kick hat clap open perc bass pad chords lead'), ('Breakdown', 16, 'pad chordsl'), ('Build 2', 16, 'hat pad chords arp roll'), ('Drop 2', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'kick hat bass')],
    'funk': [('Intro', 8, 'kick hat clap chords'), ('Riff principale', 8, 'kick hat clap bass chords lead'), ('Strofa', 16, 'kick hat clap bass chords leadl'), ('Ritornello / Vamp', 16, 'kick hat clap perc bass chords lead arp fill'), ('Strofa 2', 16, 'kick hat clap perc bass chords leadl'), ('Bridge', 8, 'bass chords'), ('Assolo', 8, 'kick hat clap bass chords lead'), ('Finale', 16, 'kick hat clap open perc bass chords arp lead fill')],
    'future_bass': [('Intro', 8, 'pad bassl leadl'), ('Build-up', 8, 'hat pad chordsl roll'), ('Drop 1', 8, 'kick hat clap bass pad chords lead arp fill'), ('Breakdown / Verse', 16, 'pad lead'), ('Build 2', 8, 'hat pad chords roll'), ('Drop 2', 24, 'kick hat clap perc bass pad chords arp lead fill'), ('Outro', 8, 'pad')],
    'glitch': [('Intro', 8, 'hat arpl'), ('Beat', 8, 'kick hat clap perc fill'), ('Evoluzione', 16, 'kick hat clap perc bass arp'), ('Breakdown', 8, 'pad arpl'), ('Ritorno', 16, 'kick hat clap perc bass arp lead fill')],
    'hardstyle': [('Intro noise', 16, 'kick hat pad'), ('Melodic section', 32, 'kick hat clap bass pad arp lead'), ('Build-up', 16, 'hat pad arp lead roll'), ('Pausa', 8, ''), ('Climax / Drop', 24, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro noise', 16, 'kick pad')],
    'harsh_noise': [('Wall 1', 16, 'pad arp'), ('Wall 2', 16, 'pad bass arp lead'), ('Blocco dinamico', 16, 'bass lead'), ('Wall finale', 16, 'pad bass arp lead chords')],
    'hip_hop': [('Intro', 4, 'hat chordsl'), ('Beat completo', 4, 'kick hat clap bass'), ('Strofa 1', 16, 'kick hat clap bass chordsl leadl'), ('Hook', 8, 'kick hat clap bass pad chords lead'), ('Strofa 2', 16, 'kick hat clap perc bass chordsl leadl'), ('Hook 2', 8, 'kick hat clap bass pad chords lead fill'), ('Bridge', 8, 'pad chordsl'), ('Strofa 3 / Hook', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'pad chordsl')],
    'house_90s': [('Intro DJ', 16, 'kick hat perc'), ('Groove base', 16, 'kick hat clap open bass'), ('Strofe', 16, 'kick hat clap open bass pad chords lead'), ('Ritornello', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Midsection', 16, 'kick hat clap open bass pad'), ('Ritornello 2', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro DJ', 16, 'kick hat')],
    'hyperpop': [('Intro', 8, 'pad leadl hat'), ('Blocco 1', 8, 'kick hat clap perc bass fill'), ('Blocco 2', 8, 'hat clap perc arpl lead'), ('Momento pop', 8, 'kick hat clap bass pad chords lead'), ('Climax', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Dissoluzione', 8, 'arpl hat')],
    'idm': [('Intro', 8, 'pad arpl'), ('Sezione 1', 8, 'kick hat clap perc'), ('Sezione 2', 16, 'kick hat clap perc bass arp lead'), ('Breakdown', 8, 'pad arpl'), ('Sezione 3', 16, 'kick hat clap perc bass arp lead fill')],
    'industrial': [('Intro', 16, 'kick hat arpl'), ('Verse', 16, 'kick hat clap bass'), ('Chorus', 16, 'kick hat clap open perc bass chords lead arp'), ('Bridge', 16, 'pad bassl'), ('Finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'jungle': [('Intro', 16, 'pad chordsl leadl'), ('Build', 16, 'hat perc roll'), ('Drop 1', 32, 'kick hat clap perc bass fill'), ('Sezione dub', 16, 'pad chords perc'), ('Build 2', 16, 'hat perc roll'), ('Drop 2', 32, 'kick hat clap perc bass arp lead fill'), ('Outro', 16, 'pad')],
    'lowercase': [('Silenzio', 8, ''), ('Evento 1', 1, 'event'), ('Silenzio 2', 15, ''), ('Eventi ravvicinati', 2, 'event'), ('Silenzio 3', 22, ''), ('Evento 2', 2, 'event')],
    'microsound': [('Nube 1', 16, 'arpl'), ('Aumento densita', 16, 'arp'), ('Nube 2', 16, 'arp lead'), ('Dissolvenza', 16, 'arpl')],
    'minimal': [('Cellula 1', 16, 'kick hat bass'), ('Cellula 2', 16, 'kick hat bass arpl'), ('Addizione', 16, 'kick hat clap bass arp'), ('Sottrazione', 16, 'kick hat bass arpl'), ('Ritorno', 16, 'kick hat clap bass arp')],
    'minimal_techno': [('Intro loop', 32, 'kick hat'), ('Evoluzione 1', 32, 'kick hat perc bass'), ('Evoluzione 2', 32, 'kick hat perc bass arpl'), ('Evoluzione 3', 32, 'kick hat clap perc bass arp'), ('Outro loop', 32, 'kick hat')],
    'minimalismo_ritmico': [('Pattern 1', 15, 'kick hat'), ('Pattern 2', 15, 'kick hat perc bass'), ('Pattern 3', 15, 'kick hat clap perc bass arpl'), ('Trasformazione', 15, 'kick hat clap perc bass arp lead'), ('Dissoluzione', 15, 'kick hat bass arpl')],
    'musique_concrete': [('Materiale A', 16, 'arpl event'), ('Trasformazione', 16, 'arp leadl'), ('Sovrapposizione', 16, 'arp lead pad'), ('Montaggio', 16, 'leadl event'), ('Dissoluzione', 16, 'arpl event')],
    'noise': [('Texture 1', 16, 'pad'), ('Texture 2', 16, 'pad bass arpl'), ('Muro di rumore', 16, 'pad bass arp lead'), ('Silenzio', 8, ''), ('Texture 3', 16, 'pad arpl')],
    'onkyo': [('Silenzio', 8, ''), ('Gesto 1', 1, 'event'), ('Silenzio 2', 11, ''), ('Gesto 2 + risposta', 2, 'event'), ('Silenzio 3', 18, ''), ('Dialogo', 4, 'event arpl')],
    'psytrance': [('Intro ipnotica', 32, 'kick hat bass pad arpl'), ('Build 1', 32, 'kick hat open bass pad arp roll'), ('First Break', 32, 'pad arpl lead'), ('Drop 1 (Groove)', 32, 'kick hat open perc bass pad arp lead fill'), ('Second Break', 32, 'pad arpl lead'), ('Peak', 32, 'kick hat open perc bass pad chords arp lead fill'), ('Outro', 32, 'kick hat bass')],
    'r&b': [('Intro', 8, 'pad chordsl'), ('Strofa 1', 16, 'kick hat clap bass chords leadl'), ('Pre-chorus', 8, 'kick hat clap bass pad rolls'), ('Ritornello', 12, 'kick hat clap open perc bass pad chords arp lead'), ('Strofa 2', 16, 'kick hat clap perc bass chords leadl arpl'), ('Ritornello 2', 12, 'kick hat clap open perc bass pad chords arp lead'), ('Bridge', 8, 'pad chordsl bassl'), ('Ritornello finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'reggae': [('Intro', 4, 'kick hat bass chords'), ('Verse 1', 16, 'kick clap hat bass chords pad leadl'), ('Chorus', 8, 'kick clap hat perc bass chords pad arp lead'), ('Verse 2', 16, 'kick clap hat bass chords pad leadl'), ('Chorus 2', 8, 'kick clap hat perc bass chords pad arp lead'), ('Bridge / Dub', 8, 'kick clap hat bass'), ('Chorus finale', 8, 'kick clap hat perc bass chords pad arp lead fill')],
    'reggaeton': [('Intro', 8, 'kick clap hat'), ('Beat completo', 8, 'kick clap hat perc bass'), ('Strofa 1', 8, 'kick clap hat bass chordsl leadl'), ('Hook', 8, 'kick clap hat perc bass pad chords lead'), ('Strofa 2', 8, 'kick clap hat perc bass chordsl leadl'), ('Hook 2', 8, 'kick clap hat perc bass pad chords lead fill'), ('Bridge', 8, 'clap hat pad bassl'), ('Hook finale', 16, 'kick clap hat open perc bass pad chords arp lead fill'), ('Outro', 24, 'kick clap hat')],
    'jazz': [('Intro', 4, 'hat bass chords'), ('Tema A', 8, 'kick hat clap bass chords lead'), ('Tema A2', 8, 'kick hat clap bass chords lead'), ('Ponte', 8, 'kick hat clap bass chords leadl'), ('Tema A3', 8, 'kick hat clap bass chords lead'), ('Assolo 1', 16, 'kick hat clap bass chords leadl'), ('Assolo 2', 16, 'kick hat clap bass chords leadl'), ('Tema finale', 8, 'kick hat clap bass chords lead'), ('Outro', 4, 'hat bass chords fill')],
    'soul': [('Intro', 4, 'kick hat clap bass chords'), ('Strofa 1', 16, 'kick hat clap bass chords leadl arpl'), ('Pre-chorus', 8, 'kick hat clap bass chords arp rolls'), ('Ritornello', 12, 'kick hat clap perc bass pad chords arp lead'), ('Strofa 2', 16, 'kick hat clap perc bass chords leadl arpl'), ('Ritornello 2', 12, 'kick hat clap perc bass pad chords arp lead'), ('Bridge / Vamp', 12, 'kick hat clap bass pad chords arp'), ('Finale', 16, 'kick hat clap perc bass pad chords arp lead fill')],
    'soulful_house': [('Intro DJ', 32, 'kick pad chordsl leadl'), ('Verse 1', 16, 'kick hat clap open bass pad chords leadl'), ('Pre-chorus', 8, 'kick hat clap bass pad chordsl arpl rolls'), ('Chorus', 16, 'kick hat clap open perc bass pad chords arp lead'), ('Verse 2', 16, 'kick hat clap open bass pad chords leadl arpl'), ('Breakdown', 8, 'pad chordsl lead'), ('Rebuild / Drop', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Chorus finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'space_disco': [('Intro vamp', 32, 'kick hat open bass arpl'), ('Verse', 16, 'kick hat open clap bass chords arp leadl'), ('Chorus', 16, 'kick hat open clap perc bass pad chords arp lead fill'), ('Verse 2', 16, 'kick hat open clap bass chords arp leadl'), ('Breakdown strumentale', 16, 'kick hat open bass pad chords arp'), ('Chorus finale', 16, 'kick hat open clap perc bass pad chords arp lead fill'), ('Outro vamp', 16, 'kick hat open bass')],
    'sperimentale': [('Processo 1', 8, 'hat arpl'), ('Processo 2', 8, 'kick clap bass arpl'), ('Processo 3', 8, 'hat perc bass arp lead'), ('Dissoluzione', 8, 'arpl')],
    'synthpop': [('Intro', 8, 'kick hat leadl arpl'), ('Verse 1', 8, 'kick hat clap bass arp leadl'), ('Chorus', 16, 'kick hat clap open perc bass chords arp lead fill'), ('Verse 2', 16, 'kick hat clap bass arp leadl chordsl'), ('Chorus 2', 8, 'kick hat clap open perc bass chords arp lead fill'), ('Bridge', 8, 'pad chordsl bassl'), ('Chorus finale', 8, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 8, 'kick hat bass')],
    'synthwave': [('Intro', 8, 'kick hat arpl pad'), ('Verse', 16, 'kick hat clap bass arp lead'), ('Chorus', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Verse 2', 16, 'kick hat clap bass pad arp leadl'), ('Bridge', 8, 'pad arp'), ('Chorus finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'techno': [('Intro 1', 2, 'kick'), ('Intro 2', 2, 'kick hat'), ('Intro 3', 2, 'kick hat perc'), ('Intro 4', 2, 'kick hat perc clap open'), ('Intro 5', 2, 'kick hat perc clap open bass'), ('Intro 6', 2, 'kick hat perc clap open bass chords'), ('Intro 7', 2, 'kick hat perc clap open bass chords pad'), ('Intro 8', 2, 'kick hat perc clap open bass chords pad arp'), ('Main 1 / First Drop', 64, 'kick hat perc clap open bass chords pad arp fill'), ('Breakdown', 16, 'perc pad leadl'), ('Build-up', 16, 'hat pad roll'), ('Second Drop / Variation', 64, 'kick hat perc clap open bass chords pad arp lead fill'), ('Outro 1', 2, 'kick hat perc clap open bass chords pad arp'), ('Outro 2', 2, 'kick hat perc clap open bass chords pad'), ('Outro 3', 2, 'kick hat perc clap open bass chords'), ('Outro 4', 2, 'kick hat perc clap open bass'), ('Outro 5', 2, 'kick hat perc clap open'), ('Outro 6', 2, 'kick hat perc'), ('Outro 7', 2, 'kick hat'), ('Outro 8', 2, 'kick')],
    'trance': [('Intro lunga', 64, 'kick hat pad arpl'), ('Main 1', 32, 'kick hat clap open bass pad arpl lead'), ('Breakdown', 32, 'pad chordsl lead'), ('Build', 16, 'hat pad chords arp roll'), ('Drop', 32, 'kick hat clap open perc bass pad chords arp lead fill'), ('Outro', 16, 'pad')],
    'trap': [('Intro', 8, 'pad leadl bassl'), ('Hook', 8, 'kick hat clap perc bass pad lead'), ('Strofa 1', 16, 'kick hat clap bass pad leadl'), ('Hook 2', 16, 'kick hat clap perc bass pad lead arp fill'), ('Strofa 2', 16, 'kick hat clap bass pad leadl'), ('Bridge', 8, 'pad leadl'), ('Hook finale', 16, 'kick hat clap perc bass pad lead arp fill'), ('Outro', 8, 'pad leadl bassl')],
    'trip_hop': [('Intro', 8, 'kick hat pad chordsl'), ('Verse 1', 16, 'kick hat clap bass chords leadl'), ('Pre-chorus', 8, 'kick hat clap bass pad chordsl arpl rolls'), ('Chorus', 16, 'kick hat clap perc bass pad chords arp lead'), ('Verse 2', 16, 'kick hat clap perc bass chords leadl'), ('Bridge', 8, 'pad lead'), ('Chorus finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'uk_garage': [('Intro', 8, 'hat pad leadl'), ('Verse 1', 16, 'kick hat clap bass leadl'), ('Pre-chorus', 8, 'kick hat clap bass pad arp rolls'), ('Chorus', 16, 'kick hat clap open perc bass pad chords arp lead fill'), ('Verse 2', 16, 'kick hat clap perc bass leadl arpl'), ('Bridge', 8, 'pad arp'), ('Chorus finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'underground': [('Intro', 8, 'pad leadl bassl'), ('Beat drill', 8, 'kick hat clap bass'), ('Strofa 1', 16, 'kick hat clap bass pad leadl'), ('Hook', 8, 'kick hat clap perc bass pad chords lead arp'), ('Strofa 2', 16, 'kick hat clap perc bass pad leadl'), ('Hook 2', 8, 'kick hat clap perc bass pad chords lead arp fill'), ('Bridge', 8, 'pad chordsl bassl'), ('Hook finale', 16, 'kick hat clap open perc bass pad chords arp lead fill')],
    'vaporwave': [('Intro', 16, 'pad leadl'), ('Sezione A', 16, 'kick hat clap bass pad chords lead'), ('Sezione B', 16, 'kick hat clap bass pad chords arp lead'), ('Ritorno A', 16, 'kick hat clap bass pad chords arp lead')],
}

def _parse_timeline(rows):
    out = []
    for name, bars, layers in rows:
        ls = frozenset(layers.split())
        assert ls <= LAYER_TOKENS, (name, ls - LAYER_TOKENS)
        assert bars > 0, (name, bars)
        out.append((name, bars, ls))
    return out

if set(TIMELINES) != set(GENRES):
    raise ValueError(f"TIMELINES e GENRES non coincidono: {sorted(set(TIMELINES) ^ set(GENRES))}")

for _k, _v in GENRES.items():
    _tl = _parse_timeline(TIMELINES[_k])
    _v['timeline'] = _tl
    _v['bars_default'] = sum(b for _n, b, _l in _tl)

# ================= STILE ARMONICO E DI BASSO =================
GENRE_STYLE = {
    'acid': dict(seventh=0.5, bass_style='acid', pad_lo=62, chords_lo=64),
    'afro_house': dict(seventh=0.5, perc_layers=[('shaker', [70]*4 + [69]*4 + [82], [.67,.67,1,.67, .67,.67,1,.67, .67,.67,1,.67, .67,.67,1,.67], (57, 90), (8, 10)), ('conga', [64]*4 + [63]*3 + [62]*3, [1,.17,0,1, .67,.33,1,.33, .33,0,.67,.67, 0,.33,1,0], (70, 112), (8, 10)), ('bongo', [60, 60, 61], [0,.17,.33,0, 0,.5,0,.33, 0,.67,0,.33, 0,.04,.04,.04], (66, 96), (17, 9)), ('tom', [45, 47], [0,0,.17,0, 0,0,0,.17, 0,0,0,0, 0,.21,.08,.08], (86, 108), (13, 10)), ('bell', [68, 68, 56, 56, 67], [0,.33,.67,0, 0,.33,.67,0, 0,.33,.67,0, 0,0,.67,0], (73, 78), (7, 10))], lead_thin=0.7, lead_merge=0.6, lead_rest=4, lead_repeat=True),
    'amapiano': dict(seventh=0.6, ninth=0.2, bass_style='logdrum'),
    'armonico': dict(seventh=0.8, ninth=0.4, bass_style='walk'),
    'chiptune': dict(seventh=0.0, bass_style='rolling'),
    'commerciale_90s': dict(seventh=0.3),
    'deep': dict(seventh=1.0, ninth=0.6, bass_style='sync'),
    'disco': dict(seventh=0.8, ninth=0.2, bass_style='disco'),
    'drum_n_bass': dict(seventh=0.4, bass_style='reese'),
    'dub_techno': dict(seventh=0.9, ninth=0.2, bass_style='dubsub'),
    'dubstep': dict(seventh=0.2, bass_style='wobble'),
    'edm_2000s': dict(seventh=0.0, bass_style='offbeat', lead_thin=0.6, lead_merge=0.6, lead_rest=4, lead_repeat=True),
    'elettronico': dict(seventh=0.35),
    'funk': dict(seventh=0.9, ninth=0.3, bass_style='funk', ghost_p=0.4, ghost_vel=(18, 32)),
    'future_bass': dict(seventh=0.7, ninth=0.3, bass_style='long'),
    'hardstyle': dict(seventh=0.0, bass_style='offbeat'),
    'hip_hop': dict(seventh=0.6, ninth=0.2, bass_style='long'),
    'house_90s': dict(seventh=0.5, ninth=0.1),
    'hyperpop': dict(seventh=0.3),
    'industrial': dict(seventh=0.1, bass_style='rolling'),
    'jungle': dict(seventh=0.3, bass_style='rollacc'),
    'minimal_techno': dict(seventh=0.2, lead_keep=8, lead_rest=4, lead_repeat=True),
    'musique_concrete': dict(seventh=0.3),
    'psytrance': dict(seventh=0.0, bass_style='rollacc'),
    'r&b': dict(seventh=0.95, ninth=0.5, bass_style='long'),
    'reggae': dict(seventh=0.3, bass_style='walk'),
    'reggaeton': dict(seventh=0.3, bass_style='long'),
    'jazz': dict(seventh=0.6, ninth=0.2, bass_style='walk'),
    'soul': dict(seventh=0.95, ninth=0.5, bass_style='walk'),
    'soulful_house': dict(seventh=1.0, ninth=0.7, bass_style='sync'),
    'space_disco': dict(seventh=0.9, ninth=0.3, bass_style='fretless'),
    'synthpop': dict(seventh=0.15, bass_style='arp'),
    'synthwave': dict(seventh=0.4, bass_style='octave'),
    'techno': dict(seventh=0.1, bass_style='rolling', lead_keep=8, lead_rest=4, lead_repeat=True, filter_slow=True, pan={'lead': 40, 'pad': 88, 'arp': 84, 'chords': 78}, melodic_loops=0.7, bass_pedal=0.7, bass_approach=0.3, lead_sync=True),
    'trance': dict(seventh=0.0, bass_style='offbeat', lead_thin=0.7, lead_merge=0.6, lead_rest=4, lead_repeat=True),
    'trap': dict(seventh=0.3, bass_style='long', hat_roll=0.7),
    'trip_hop': dict(seventh=0.8, ninth=0.3, bass_style='dubsub'),
    'uk_garage': dict(seventh=0.5, bass_style='long'),
    'vaporwave': dict(seventh=0.9, ninth=0.5, bass_style='long'),
}

for _k, _s in GENRE_STYLE.items(): GENRES[_k].update(_s)

BASS_ROOT_P = {'rollacc': 0.97, 'fretless': 0.85, 'rolling': 0.97, 'offbeat': 0.92, 'acid': 0.7, 'octave': 0.9, 'disco': 0.9, 'long': 0.85, 'reese': 0.9, 'dubsub': 0.98, 'funk': 0.8, 'wobble': 0.95, 'logdrum': 0.75}

def _bass_pc(style, hit, cpcs, rpc, root_p):
    if style == 'arp': return cpcs[(0, 2, 0, 1)[hit % 4] % len(cpcs)]
    if style == 'walk': return cpcs[(0, 1, 2, 1)[hit % 4] % len(cpcs)]
    return rpc if random.random() < root_p else random.choice(cpcs[1:])

def _bass_shape(style, hit, gap, room, step=0):
    if style == 'acid': return (12 if random.random() < 0.2 else 0), (gap + 1 if random.random() < 0.35 else gap), (22 if random.random() < 0.3 else 0)
    if style == 'octave': return (12 if hit % 2 else 0), gap, 0
    if style == 'disco': return (12 if (hit % 2 and random.random() < 0.18) else 0), gap, 0
    if style == 'rollacc': return 0, gap, (14 if step % 4 == 2 else -16)
    if style == 'long': return (12 if random.random() < 0.12 else 0), min(gap * 2, room), 0
    if style in ('reese', 'dubsub', 'wobble'): return 0, min(gap * 2, room), 0
    if style == 'logdrum': return (12 if random.random() < 0.15 else 0), (1 if random.random() < 0.7 else 2), (10 if random.random() < 0.3 else 0)
    if style == 'funk':
        r = random.random()
        if r < 0.25: return 12, 1, 12
        if r < 0.45: return 0, 1, -38
        return 0, gap, 0
    return 0, gap, 0

DEFAULT_TIMELINE = _parse_timeline([('Intro', 8, 'kick hat'), ('Break', 8, 'kick hat pad chordsl arpl bassl'), ('Build-up', 8, 'kick hat clap bass pad chords arp roll'), ('Drop', 24, 'kick hat clap open perc bass pad chords arp lead fill'), ('Break 2', 8, 'kick hat pad chordsl leadl bassl'), ('Outro', 8, 'kick hat')])

BLOCK8_GENRES = ('techno', 'acid')
_BLOCK8_SIGS = set()

def timeline_unit(tl):
    tl = tl or DEFAULT_TIMELINE
    if tuple(n for n, _b, _l in tl) in _BLOCK8_SIGS and all(b % 8 == 0 for _n, b, _l in tl if b >= 8) and all(b % 2 == 0 for _n, b, _l in tl): return 8
    return 4 if all(b % 4 == 0 for _n, b, _l in tl) else 1

LAYER_ORDER = ['kick', 'hat', 'clap', 'open', 'perc', 'bass', 'bassl', 'pad', 'chords', 'chordsl', 'arp', 'arpl', 'lead', 'leadl', 'roll', 'rolls', 'fill', 'event']

def timeline_table(timeline):
    cols = [t for t in LAYER_ORDER if any(t in ls for _n, _b, ls in timeline)]
    rows, pos = [], 0
    for n, b, ls in timeline:
        rows.append({'Sezione': n, 'Battute': f"{pos + 1}-{pos + b}", **{t: ('●' if t in ls else '') for t in cols}})
        pos += b
    return rows

def timelines_to_json():
    data = {k: [[n, b, ' '.join(t for t in LAYER_ORDER if t in ls)] for n, b, ls in v['timeline']] for k, v in sorted(GENRES.items())}
    return json.dumps(data, ensure_ascii=False, indent=1)

def apply_timelines(data):
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

_BLOCK8_SIGS.update(tuple(n for n, _b, _l in GENRES[k]['timeline']) for k in BLOCK8_GENRES if GENRES.get(k, {}).get('timeline'))

TIMELINE_FILE_MSG = ''
try:
    _tlp = Path(__file__).with_name('midi_forge_timelines.json')
    if _tlp.exists():
        TIMELINE_FILE_MSG = f"Timeline personalizzate caricate da {_tlp.name} ({apply_timelines(json.loads(_tlp.read_text(encoding='utf-8')))} generi)"
except NameError: pass
except Exception as _e: TIMELINE_FILE_MSG = f"midi_forge_timelines.json ignorato: {_e}"

def _ladder_split(tl, unit):
    tl = list(tl); h = t = 0
    if unit > 1:
        while h < len(tl) - 1 and tl[h][1] < unit: h += 1
        while t < len(tl) - 1 - h and tl[len(tl) - 1 - t][1] < unit: t += 1
    return tl[:h], tl[h:len(tl) - t], tl[len(tl) - t:]

_LADDER_TEMPLATES = [('perc', 'clap', 'bass', 'chords', 'pad', 'arp'), ('perc', 'bass', 'clap', 'pad', 'chords', 'arp'), ('clap', 'perc', 'bass', 'arp', 'pad', 'chords'), ('perc', 'bass', 'pad', 'clap', 'arp', 'chords'), ('clap', 'bass', 'perc', 'chords', 'arp', 'pad')]

def vary_ladder(head, tail, bars, seed):
    if seed is None or len(head) != 8 or len(tail) != 8: return head, tail
    cum = [l for _n, _b, l in head]
    groups = [cum[0]] + [cum[i] - cum[i - 1] for i in range(1, 8)]
    key = {'perc': groups[2], 'clap': groups[3], 'bass': groups[4], 'chords': groups[5], 'pad': groups[6], 'arp': groups[7]}
    if not (cum[0] == frozenset({'kick'}) or 'kick' in groups[0]) or not all(any(t.startswith(k) for t in key[k]) for k in key if key[k]): return head, tail
    rs = random.Random(int(seed) * 17 + 3)
    order = rs.choice(LADDER_TEMPLATES)
    step = 4 if (bars >= 160 and rs.random() < 0.3) else head[0][1]
    new_groups = [groups[0], groups[1]] + [key[k] for k in order]
    states, cur = [], frozenset()
    for g in new_groups:
        cur = cur | g; states.append(cur)
    return [(head[i][0], step, states[i]) for i in range(8)], [(tail[i][0], step, states[7 - i]) for i in range(8)]

def min_bars(g):
    tl = g.get('timeline') or DEFAULT_TIMELINE
    u = timeline_unit(tl)
    head, mid, tail = _ladder_split(tl, u)
    return sum(b for _n, b, _l in head + tail) + u * len(mid)

def compute_structure(bars, timeline=None, seed=None):
    tl = timeline or DEFAULT_TIMELINE
    unit = timeline_unit(tl)
    head, mid, tail = _ladder_split(tl, unit)
    head, tail = vary_ladder(head, tail, bars, seed)
    fixed = sum(b for _n, b, _l in head + tail)
    n = len(mid)
    bars = max(fixed + unit * n, fixed + ((int(bars) - fixed) // unit) * unit)
    units = (bars - fixed) // unit
    w = [float(b) for _n, b, _l in mid]
    if seed is not None:
        rs = random.Random(int(seed) * 31 + 7)
        lo, hi = (0, n) if (head or tail) else (1, n - 1)
        for i in range(lo, hi): w[i] *= rs.uniform(0.8, 1.25)
    tot, alloc = sum(w), [1] * n
    for _ in range(units - n):
        k = max(range(n), key=lambda i: w[i] / tot * units - alloc[i])
        alloc[k] += 1
    sections, pos = [], 0
    for name, b, layers in head:
        sections.append((name, pos, b, layers)); pos += b
    for (name, _b, layers), a in zip(mid, alloc):
        sections.append((name, pos, a * unit, layers)); pos += a * unit
    for name, b, layers in tail:
        sections.append((name, pos, b, layers)); pos += b
    return bars, sections

# ================= METRI =================
METERS = {
    '4/4':   ((4, 4),   [4, 4, 4, 4]),
    '3/4':   ((3, 4),   [4, 4, 4]),
    '5/4':   ((5, 4),   [4, 4, 4, 4, 4]),
    '5/16':  ((5, 16),  [3, 2]),
    '7/16':  ((7, 16),  [4, 3]),
    '7/8':   ((7, 8),   [4, 4, 6]),
    '9/8':   ((9, 8),   [4, 4, 4, 6]),
    '11/8':  ((11, 8),  [6, 6, 6, 4]),
    '13/8':  ((13, 8),  [6, 6, 6, 4, 4]),
    '15/8':  ((15, 8),  [6, 6, 6, 6, 6]),
    '17/8':  ((17, 8),  [6, 6, 6, 6, 10]),
    '29/16': ((29, 16), [5, 6, 6, 6, 6]),
}

def plan_meter(g, bars, odd=True, seed=None):
    keys = g.get('meter', ['4/4']) if odd else ['4/4']
    ms, sec_keys = (g.get('meter_sections') if odd else None), None
    if ms and g.get('timeline') and len(ms) == len(g['timeline']):
        secs = compute_structure(bars, g['timeline'], seed)
        sec_keys = [ms[i] for i, (n, s, l, ls) in enumerate(secs) for _ in range(l)]
    q, plan, pos = TICKS_BEAT // 4, [], 0
    for b in range(bars):
        key = sec_keys[b] if sec_keys and b < len(sec_keys) else keys[b % len(keys)]
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
    if mode == 'minimal': return not (submode == 'extract' and has_notes)
    return submode == 'generative'

def avg_bar_sixteenths(g, odd=True):
    ms, tl = (g.get('meter_sections') if odd else None), g.get('timeline')
    if ms and tl and len(ms) == len(tl):
        return sum(sum(METERS[k][1]) * b for k, (_n, b, _l) in zip(ms, tl)) / sum(b for _n, b, _l in tl)
    keys = g.get('meter', ['4/4']) if odd else ['4/4']
    return sum(sum(METERS[k][1]) for k in keys) / len(keys)

for _k, _v in GENRES.items(): _v['_name'] = _k

def legacy_name(layers, seen_drop):
    if not (layers & MELODIC): return 'outro' if seen_drop else 'intro'
    if layers & {'roll', 'rolls'}: return 'build'
    if 'clap' in layers and 'kick' in layers: return 'drop'
    return 'break2' if seen_drop else 'break1'

def section_map(sections, bars):
    out, prev, seen = [], frozenset(), False
    block8 = tuple(n for n, _s, _l, _ls in sections) in _BLOCK8_SIGS
    for label, _s, length, layers in sections:
        sec = legacy_name(layers, seen)
        if sec == 'drop': seen = True
        ladder = block8 and length < 8
        for i in range(length):
            out.append({'sec': sec, 'idx': i, 'length': length, 'layers': layers, 'prev': prev, 'label': label, 'ladder': ladder})
        prev = layers
    return out[:bars]

def _fade(B, fam):
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
    return 'break1' if drumless and name in ('intro', 'outro') else name

def _note(ev, tick, dur, pitch, vel, ch):
    pitch = max(0, min(127, int(pitch)))
    ev.append({'tick': int(tick), 'type': 'on', 'pitch': pitch, 'vel': max(1, min(127, int(vel))), 'channel': ch})
    ev.append({'tick': int(tick + max(1, int(dur))), 'type': 'off', 'pitch': pitch, 'vel': 0, 'channel': ch})

def _question(motif, n):
    q = list(motif); idx = [i for i, v in enumerate(q) if v is not None]
    if idx and q[idx[-1]] == 0: q[idx[-1]] = random.choice([2, 4]) % n
    return q

def _answer(motif):
    a = list(motif); idx = [i for i, v in enumerate(a) if v is not None]
    if idx:
        for i in idx[len(idx) // 2:]: a[i] = max(0, a[i] - random.choice([1, 2]))
        a[idx[-1]] = 0
    return a

# ================= CORPUS DI MOTIVI =================
CORPUS_TEXT = """
genre,id,bpm,meter,key,mode,pattern
Techno,T01,132,4/4,Am,minor,1.3:2 1.3:2 1.3:2 1.3:2 5.3:2 5.3:2 1.3:2 1.3:2 1.3:2 1.3:2 3.3:2 3.3:2 5.3:2 5.3:2 1.3:2 1.3:2
House,H01,124,4/4,Cmaj,major,1.4:2 3.4:2 5.4:2 3.4:2 1.4:2 3.4:2 5.4:2 6.4:2 5.4:2 3.4:2 2.4:2 3.4:2 1.4:2 3.4:2 5.4:2 1.4:2
Trance,TR01,138,4/4,Em,minor,1.4:2 5.4:2 6.4:2 5.4:2 1.4:2 5.4:2 6.4:2 5.4:2 3.4:2 5.4:2 6.4:2 5.4:2 1.4:2 5.4:2 6.4:2 1.5:2
"""
def parse_corpus(text):
    out = {}
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.startswith('#') or ln.startswith('genre,'): continue
        p = ln.split(',', 6)
        if len(p) < 7 or p[3].strip() != '4/4': continue
        notes, pos = [], 0
        try:
            for t in p[6].split():
                a, d = t.rsplit(':', 1); d = int(d)
                if a != 'r':
                    g, o_ = a.split('.'); notes.append((pos, int(g), int(o_), d))
                pos += d
        except Exception: continue
        if pos != 32 or not notes: continue
        base_oct = Counter(o for _, _, o, _ in notes).most_common(1)[0][0]
        out.setdefault(p[0].strip(), []).append([(s_, g_ - 1, o_ - base_oct, d) for s_, g_, o_, d in notes])
    return out

CORPUS = parse_corpus(CORPUS_TEXT)
_CORPUS_FAMILY = {'techno': 'Techno', 'minimal_techno': 'Techno', 'industrial': 'Techno', 'underground': 'Tech House', 'minimal': 'Tech House', 'house_90s': 'House', 'commerciale_90s': 'House', 'afro_house': 'House', 'deep': 'Deep House', 'dub_techno': 'Deep House', 'soulful_house': 'Deep House', 'uk_garage': 'Deep House', 'trance': 'Trance', 'psytrance': 'Trance', 'edm_2000s': 'Trance', 'elettronico': 'Electro', 'acid': 'Electro', 'synthwave': 'Electro', 'space_disco': 'Electro'}
LEAD_THIN_MIN_JUMP = 3

def corpus_bar(g, bar, n, ct, st):
    pats = CORPUS.get(_CORPUS_FAMILY.get(g.get('_name')))
    if not pats: return None
    if bar % 4 == 0 or 'p1' not in st:
        if g.get('lead_repeat') and (bar // 4) % 2 == 1 and 'p1' in st: pass
        else: st['p1'] = random.choice(pats); st['p2'] = st['p1'] if random.random() < 0.4 else random.choice(pats)
    pat, off = (st['p1'] if bar % 4 < 2 else st['p2']), 16 * (bar % 2)
    cts = [k for k in range(-n, 2 * n + 1) if k % n in ct]
    out = []
    for s, deg, octv, du in pat:
        if not off <= s < off + 16: continue
        dg = deg + n * octv
        if (s - off) % 4 == 0 and dg % n not in ct: dg = min(cts, key=lambda c: (abs(c - dg), c))
        out.append((s - off, dg, du))
    thin, pm, pr = g.get('lead_thin', 0), g.get('lead_merge', 0), g.get('lead_rest', 0)
    if (thin or pm) and out:
        rz = random.Random(zlib.crc32(repr((pat, off)).encode()))
        mg = [list(out[0])]
        for s_, dg, du in out[1:]:
            l = mg[-1]
            absorb = thin and s_ % 2 == 1 and l[0] + l[2] == s_ and l[2] + du <= 8 and rz.random() < thin and abs(dg - l[1]) >= LEAD_THIN_MIN_JUMP
            same = pm and l[1] == dg and l[0] + l[2] == s_ and l[2] + du <= 8 and rz.random() < pm
            if absorb or same: l[2] += du
            else: mg.append([s_, dg, du])
        out = [tuple(x) for x in mg]
    return out

def _mel_template(k=16):
    out, sign = [], random.choice([-1, 1])
    for _ in range(k):
        if random.random() > 0.65: sign = -sign
        out.append(sign * random.choices([0, 1, 2], weights=[1, 7, 2])[0])
    return out

MOTIF_REPLAY = {0}
MOTIF_PHRASE_REUSE = True
_ACTIVE_RES = {6: 1, 5: -1, 3: -1, 1: -1}

def melody_bar(positions, strong, ct, root_deg, n, st, variant):
    lo, hi = 0, n + 1
    cts = [k for k in range(lo, hi + 1) if k % n in ct] or [0]
    tonic = [k for k in cts if k % n in (0, 2, 4)] or cts
    near = lambda x, pool=cts: min(pool, key=lambda c: (abs(c - x), c))
    first_of_phrase = st.get('phrase_start', False)
    tpl = st.get('tpl') or _mel_template()
    if st.get('real') and not first_of_phrase and variant in MOTIF_REPLAY: tpl = st['real']
    if variant == 1: tpl = [-t if random.random() < 0.3 else t for t in tpl]
    elif variant == 2: tpl = list(reversed(tpl))
    prev_end = st.get('cur')
    cur = near(prev_end if prev_end is not None else n // 2)
    mv = st.get('mv', 0)
    out = {}
    for i, s in enumerate(positions):
        step = tpl[i % len(tpl)]
        if i > 0 and abs(mv) > 2: step = -1 if mv > 0 else 1
        elif i > 0 and n >= 7 and (cur % n) in _ACTIVE_RES and random.random() < 0.75: step = _ACTIVE_RES[cur % n]
        x = max(lo, min(hi, cur + step))
        if s in strong or i == 0: x = near(x)
        if i == 0 and first_of_phrase: x = near(x, tonic)
        mv, cur = x - (prev_end if (i == 0 and prev_end is not None) else cur), x
        out[s] = cur
    pl = list(positions)
    for i in range(1, len(pl) - 1):
        x, a, b = out[pl[i]], out[pl[i - 1]], out[pl[i + 1]]
        if x % n not in ct and not (abs(x - a) <= 1 and abs(b - x) <= 1): out[pl[i]] = near(x)
    st['phrase_start'] = False
    if variant == 2 and positions:
        fin = near(cur, tonic)
        out[positions[-1]] = cur = fin
        if len(positions) > 1:
            cand = [fin - 1, fin + 1]
            dom = [c for c in cand if lo <= c <= hi and c % n in (4, 6, 1)]
            if positions[-2] not in strong: out[positions[-2]] = (dom or [c for c in cand if lo <= c <= hi] or [fin])[0]
    if first_of_phrase and len(positions) > 1:
        seq = [out[s] for s in positions]; st['real'] = [0] + [seq[i] - seq[i - 1] for i in range(1, len(seq))]
    st['cur'], st['mv'] = cur, mv
    return out

HUMAN_TICKS = {'hip_hop': 10, 'r&b': 10, 'soul': 10, 'jazz': 12, 'funk': 8, 'reggae': 12, 'trip_hop': 12, 'vaporwave': 12, 'jungle': 6, 'disco': 6, 'afro_house': 6, 'amapiano': 6, 'soulful_house': 6, 'space_disco': 5, 'uk_garage': 6, 'deep': 5, 'house_90s': 5, 'armonico': 6, 'synthwave': 3, 'dub_techno': 4}
for _k, _v in HUMAN_TICKS.items(): GENRES[_k]['human'] = _v

def humanize(tracks, amount, seed):
    rs = random.Random(int(seed) * 29 + 3)
    for k, evs in tracks.items():
        if k == 'drum_kick' or k == 'drum_fx' or k.startswith('instrument'): continue
        evs.sort(key=lambda e: (e['tick'], e['type'] != 'off'))
        open_ = {}
        for e in evs:
            fixed = e['pitch'] in (36, 49, 57, 119) and (k.startswith('drum'))
            amt = amount // 3 if (k.startswith('drum') and e['pitch'] in (37, 38, 39)) else amount
            if e['type'] == 'on':
                d = 0 if fixed else max(rs.randint(-amt, amt), -e['tick'])
                open_.setdefault(e['pitch'], []).append(d); e['tick'] += d
                e['vel'] = max(1, min(127, e['vel'] + (0 if fixed else rs.randint(-5, 5))))
            else:
                st_ = open_.get(e['pitch']); e['tick'] = max(0, e['tick'] + (st_.pop(0) if st_ else 0))
        evs.sort(key=lambda e: (e['tick'], e['type'] != 'off'))

def free_time(tracks, amount):
    rs = random.Random(12345 + len(tracks))
    for k, evs in tracks.items():
        if k.startswith('drum'): continue
        evs.sort(key=lambda e: (e['tick'], e['type'] != 'off'))
        open_ = {}
        for e in evs:
            if e['type'] == 'on':
                d = max(rs.randint(-amount, amount), -e['tick']); open_.setdefault(e['pitch'], []).append(d); e['tick'] += d
            else:
                st_ = open_.get(e['pitch']); e['tick'] = max(0, e['tick'] + (st_.pop(0) if st_ else 0))
        evs.sort(key=lambda e: (e['tick'], e['type'] != 'off'))

def _gaps(steps, size=16, cap=4):
    steps = sorted(steps)
    out = {}
    for i, s in enumerate(steps):
        gap = (steps[(i + 1) % len(steps)] - s) % size or size
        out[s] = min(gap, cap)
    return out

def _pc_pitch(pc, lo):
    return lo + ((pc - lo) % 12)

def _deg_pitch(root, scale, dg, lo):
    n = len(scale)
    return lo + ((root - lo + 6) % 12) - 6 + 12 * (dg // n) + scale[dg % n]

def _bass_pitch(pc, lo=28, hi=45):
    p = _pc_pitch(pc, lo)
    return p if p <= hi else p - 12

def _fold(p, lo=60, hi=83):
    while p < lo: p += 12
    while p > hi: p -= 12
    return p

# ================= BATTERIA E VARIAZIONE COL SEED =================
BPM_RANGES = {
    'acid': [(120, 130)], 'afro_house': [(120, 125)], 'amapiano': [(110, 115)], 'ambient': [(60, 90)], 'armonico': [(60, 120)], 'breakcore': [(170, 230)], 'chiptune': [(112, 128)], 'commerciale_90s': [(105, 128), (125, 138), (130, 142)], 'deep': [(118, 126)], 'disco': [(108, 132)], 'drone': [(60, 100)], 'drum_n_bass': [(160, 180)], 'dub_techno': [(112, 130)], 'dubstep': [(138, 142)], 'edm_2000s': [(126, 130), (128, 134)], 'elettronico': [(95, 140)], 'funk': [(95, 120)], 'future_bass': [(140, 160)], 'glitch': [(80, 115), (128, 148)], 'hardstyle': [(145, 155)], 'harsh_noise': [(60, 120)], 'hip_hop': [(85, 100), (85, 100), (96, 114)], 'house_90s': [(118, 125), (122, 128), (126, 132), (128, 134)], 'hyperpop': [(120, 170)], 'idm': [(100, 140)], 'industrial': [(110, 140)], 'jungle': [(160, 170)], 'lowercase': [(104, 162)], 'microsound': [(80, 100)], 'minimal': [(110, 130)], 'minimal_techno': [(125, 132)], 'minimalismo_ritmico': [(100, 130)], 'musique_concrete': [(60, 90)], 'noise': [(60, 154)], 'onkyo': [(50, 90)], 'psytrance': [(140, 150)], 'r&b': [(60, 110)], 'reggae': [(66, 90), (66, 90), (88, 100)], 'reggaeton': [(90, 100)], 'jazz': [(100, 140), (100, 140), (140, 190), (70, 100)], 'soul': [(60, 110), (95, 125)], 'soulful_house': [(120, 125)], 'space_disco': [(110, 130)], 'sperimentale': [(88, 132)], 'synthpop': [(111, 127), (122, 135)], 'synthwave': [(80, 110)], 'techno': [(123, 135), (130, 140), (136, 146)], 'trance': [(120, 150)], 'trap': [(130, 150)], 'trip_hop': [(70, 90)], 'uk_garage': [(128, 135)], 'underground': [(72, 150)], 'vaporwave': [(60, 80)],
}

LOOSE_SNARE = {'breakcore', 'glitch', 'hyperpop', 'idm', 'minimalismo_ritmico', 'sperimentale'}
JAZZ_SWING_P = 0.4
JAZZ_FUSION = {'kick': ['x--- ---- --x- ----', 'x--- --x- x--- --x-', 'x--- --x- x--- ----', 'x--x ---x --x- ----', 'x--- x--- x--- x---'], 'hat': ['x-x- x-x- x-x- x-x-'] * 4 + ['x-X- x-X- x-X- x-X-'], 'bass': ['x-x- x-x- x-x- x-x-', 'x--x --xx --x- --x-', 'x--- -xx- x--- ----', 'x--- ---- x--- x---', 'x-x- x-x- x--x --xx', 'x--- ---x x--- x-x-']}
HIPHOP_HALFTIME = 0.15
REGGAE_BACKBEAT = 0.20
REGGAE_ROCKERS = 0.15
REGGAE_STEPPERS = 0.15
REGGAE_SKANK24 = 0.25
FIXED_KICK = {'commerciale_90s', 'synthpop', 'jazz', 'hip_hop', 'soul', 'disco', 'dubstep', 'future_bass', 'jungle', 'reggae', 'reggaeton', 'uk_garage'}
BASS_FIXED = {'jazz', 'hip_hop', 'amapiano', 'hardstyle', 'jungle', 'psytrance', 'uk_garage'}
GHOST_FIXED = {'jungle', 'trip_hop', 'soul', 'hip_hop', 'funk', 'r&b'}

def _default_bpm(name, g, seed):
    plan = g.get('tempo_plan')
    return sorted(plan)[len(plan) // 2] if plan else seeded_bpm(name, g, seed)

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

def _pat(s, binary=False):
    m = {'x': 1, 'X': 2, 'g': 3, '-': 0, '.': 0}
    out = [m[c] for c in s if c in m]
    assert len(out) == 16, s
    return [1 if v else 0 for v in out] if binary else out

PATTERN_LIB = {
    'acid': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxXx xxXx xxXx xxXx', '-x-X -x-X -x-X -x-X', 'x-X- x-X- x-X- x-X-', 'xgXg xgXg xgXg xgXg'], 'bass': ['x-xx -x-x x-x- xx-x', 'x-x- xx-x x-xx -x-x', 'xx-x -xx- x-x- xx-x', 'x--x -x-x x-xx -x--']},
    'afro_house': {'hat': ['xgxg xgxg xgxg xgxg', 'xgxx xgxg xgxx xgxg', '-gxg -gxg -gxg -gxg'], 'bass': ['--x- --x- --x- --x-', '--x- --x- --x- -xx-', 'x-x- --x- x-x- --x-', '-xx- -xx- -xx- -xx-'], 'clap': ['---- x--- ---- x---', '---- x--- ---- x--x']},
    'amapiano': {'kick': ['x--- x--- x--- x---', 'x--- x--- x--- x---', 'x--- x--- x--- x---', 'x--- ---- x--- ----'], 'hat': ['xgxg xgxg xgxg xgxg', 'x-xg x-xg x-xg x-xg', 'xgx- xgxg xgx- xgxg'], 'bass': ['--x- -xx- --x- -x--', '--x- -x-- --x- x-x-', '--x- -xx- --x- -x-x', '--x- -xx- ---x -x--'], 'clap': ['---- x--- ---- x---', '---- x--- ---- x--x']},
    'armonico': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx'], 'bass': ['x--- ---- x--- ----', 'x--- --x- x--- --x-', 'x-x- x-x- x-x- x-x-']},
    'breakcore': {'kick': ['x--- --x- -x-- x-x-', 'x-x- --x- ---x x--x', 'x--x --x- x--- -x-x', 'x-x- x--- -x-x --x-'], 'hat': ['xxxx xxxx xxxx xxxx', 'xgxx xgxx xgxx xgxx', 'x-xx -xx- xx-x x-xx'], 'bass': ['x--- x--- -x-- x-x-', 'x-x- --x- x--x -x--']},
    'chiptune': {'hat': ['--x- --x- --x- --x-', 'x-x- x-x- x-x- x-x-'], 'bass': ['x--- ---- x--- ----', 'x-x- x-x- x-x- x-x-', 'x--- x--- x--- x---']},
    'commerciale_90s': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'kick': ['x--- x--- x--- x---'] * 7 + ['x--- ---- x--- ----'], 'hat': ['x-x- x-x- x-x- x-x-'] * 2 + ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx', 'xxx- xxx- xxx- xxx-', '--X- --X- --X- --X-'], 'bass': ['x-x- x-x- x-x- x-x-', 'x--x --x- x--x --x-', 'x-xx -x-x x-xx -x-x', 'x-xx x-xx x-xx x-xx', '--x- --x- --x- --x-', 'x--- --x- x--- --x-']},
    'deep': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--x ---- x---'], 'hat': ['x-X- x-X- x-X- x-X-', 'xgXg xgXg xgXg xgXg', 'x-Xg x-Xg x-Xg x-Xg'], 'bass': ['x--- --x- ---- --x-', 'x--x --x- --x- -x--', 'x-x- ---x --x- x---', 'x--- -x-- --x- x--x']},
    'disco': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--- ---x x---'], 'kick': ['x--- x--- x--- x---'] * 16 + ['x--- ---- x--- ----'] * 2 + ['x--- ---x x--- ----', 'x--- ---- x--- x---'], 'hat': ['x-x- x-x- x-x- x-x-'] * 3 + ['x-X- x-X- x-X- x-X-'] * 2 + ['xgXg xgXg xgXg xgXg'], 'bass': ['x-x- x-x- x-x- x-x-'] * 2 + ['x-x- x-x- ---- x---', 'x-x- ---- x-x- --x-', 'x--- --x- x--- --x-', 'x--- --x- ---- --x-', 'x--- x--- x--- x---']},
    'drum_n_bass': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--x ---- x---'], 'kick': ['x--- ---- --x- ----', 'x--- --x- --x- ----', 'x--- ---- --x- --x-', 'x--x ---- --x- ----'], 'hat': ['xxxx xxxx xxxx xxxx', 'xgxg xgxg xgxg xgxg', 'x-xx x-xx x-xx x-xx'], 'bass': ['x--- ---x --x- ----', 'x--x ---- x--- --x-', 'x--- --x- ---x ----', 'x-x- ---- --x- x---']},
    'dub_techno': {'clap': ['---- x--- ---- x---', '---- ---- ---- x---', '---- x--- ---- ----'], 'hat': ['--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-', '--X- ---- --X- ----'], 'bass': ['x--- ---- x--- ----', 'x--- ---x ---- x---', 'x--- ---- x--x ----', 'x--- --x- ---- ----']},
    'dubstep': {'kick': ['x--- ---- ---- ----', 'x--- --x- --x- ----', 'x--- ---- --x- ----', 'x--- --x- ---- ----', 'x--- ---- x--- ----'], 'hat': ['xgxg xgxg xgxg xgxg', 'x-x- x-x- x-x- x-x-', 'x-xg x-xg x-xg x-xg'], 'bass': ['x--- ---- x--- ----', 'x--- --x- x--- ----', 'x--- ---- x--x ----', 'x--x ---- x--- ----']},
    'edm_2000s': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-'], 'bass': ['--x- --x- --x- --x-', 'x-x- x-x- x-x- x-x-', '-xx- -xx- -xx- -xx-', 'xxxx xxxx xxxx xxxx', 'x--x --x- x--x --x-', 'x-x- x--x --x- x-x-', 'x--- x-x- x-x- ----', 'x-x- x-xx x-x- x-x-']},
    'elettronico': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-'], 'bass': ['x--x --x- x--x --x-', 'x-x- x-x- x-x- x-x-', 'x--- x--- x--x -x--']},
    'funk': {'snare': ['---- x--- ---- x---', '---- x--x ---- x---', '---- x--- ---x x---', '---- x--- ---- x-x-'], 'kick': ['x--x ---- x-x- ----', 'x--- --x- x--x ----', 'x-x- --x- x--- -x--', 'x--x -x-- x-x- ----', 'xx-- ---x --x- -x--', 'x-x- -x-- x--- ----', 'x--x ---- x-xx ----'], 'hat': ['Xxxx Xxxx Xxxx Xxxx', 'xgxg xgxg xgxg xgxg', 'Xxgx Xxgx Xxgx Xxgx', 'x-x- x-x- x-x- x-x-', 'x-x- x-x- x-x- x-x-', 'xxxx -xxx xxxx -xxx'], 'bass': ['x--x -x-x x--- x-x-', 'x-x- -x-x x--x --x-', 'x--x x--- x-x- -x--', 'x-xx --x- x--x -x--']},
    'future_bass': {'kick': ['x--- ---- x--- ----', 'x--- x--- x--- x---', 'x--- ---- x--- --x-', 'x--x ---- x--- ----'], 'hat': ['xgxg xgxg xgxg xgxg', 'xxxx xxxx xxxx xxxx', 'x-xx x-xx x-xx x-xx'], 'bass': ['x--- ---- x--- ----', 'x--- ---- x--x ----', 'x--- --x- x--- ----']},
    'glitch': {'snare': ['---- ---- x--- ----', 'x--- ---- x--- ----', '---- ---- x--- --x-'], 'kick': ['x--- ---- x--- ----', 'x--- ---x x--- ----', 'x--- ---- x-x- ----'], 'hat': ['xxxx xxxx xxxx xxxx', 'x-xx -xx- x-xx -xxx', 'xgxx xgxg xxgx xgxx'], 'bass': ['x--- x--- x-x- ----', 'x-x- ---- x--x ----']},
    'hardstyle': {'hat': ['--x- --x- --x- --x-', '--X- --X- --X- --X-'], 'bass': ['--x- --x- --x- --x-'], 'clap': ['---- x--- ---- x---', '---- x--- ---- x--x']},
    'hip_hop': {'snare': ['---- x--- ---- x---'] * 5 + ['---- x--- ---- x--x'], 'kick': ['x--- --x- x--- ----', 'x--- --x- x-x- ----', 'x-x- ---- x--- --x-', 'x--- ---x x--- -x--', 'x--x ---- --x- ----', 'x--x ---- x--x ----', 'x-x- --x- x-x- --x-', 'x-x- ---x x-x- ----', 'x-x- -x-- x-x- ----'], 'hat': ['x-x- x-x- x-x- x-x-'] * 4 + ['x-x- xgxg x-x- xgxg', 'xgxg xgxg xgxg xgxg'], 'bass': ['x--- ---- ---- ----'] * 2 + ['x--- ---- ---- x---', 'x--- ---- x--- ----', 'x--- ---- x--- --x-', 'x-x- x-x- x-x- x-x-']},
    'house_90s': {'hat': ['--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-'], 'bass': ['--x- --x- --x- --x-', '--x- --x- --xx --x-', 'x-x- --x- --x- x---', 'x--x --x- x--x --x-', 'x-x- x-x- x-x- x-x-', 'x--- x--- x--- x---', 'x-x- x--x --x- x-x-', 'x--- x-x- x-x- ----'], 'clap': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--x ---- x---']},
    'hyperpop': {'kick': ['x--- ---- x--- ----', 'x-x- --x- x--x ----', 'x--x --x- --x- x-x-', 'x-x- x--- --x- -x-x', 'x--- -x-x x--x ----'], 'hat': ['xxxx x-xx xxx- xxxx', 'x-xx -xxx x-x- xxxx', 'xgxx xgxg xxxg xxgx'], 'bass': ['x--- ---- x--- ----', 'x--x -x-- x-x- --x-', 'x--- ---x x--- -x--']},
    'idm': {'kick': ['x--x -x-x ---x --x-', 'x-x- -x-- x--x -x--', 'x--x --x- -x-x x---', 'x-x- --x- x--x --x-'], 'hat': ['x-xg xgx- gxxg x-xg', 'xxgx -xgx xgxx gx-x', 'x-x- xxg- x-xg -xxx'], 'bass': ['x--x -x-- x-x- -x--', 'x-x- --x- x--x x---']},
    'industrial': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxxx xxxx xxxx xxxx', 'x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx'], 'bass': ['xxxx xxxx xxxx xxxx', 'x-x- x-x- x-x- x-x-', 'x--x x--x x-x- x-x-']},
    'jungle': {'kick': ['x--- --x- --x- ----', 'x--x --x- --x- ----', 'x--- --x- --x- --x-'], 'hat': ['xgxg xgxg xgxg xgxg', 'x-xg x-xg x-xg x-xg', 'xxxx xxxx xxxx xxxx'], 'bass': ['-xxx -xxx -xxx -xxx', '-xxx -xxx -xxx -xx-', '-xxx -xxx -xx- -xxx']},
    'minimal': {'hat': ['xxxx xxxx xxxx xxxx', 'x-x- x-x- x-x- x-x-', 'x-xg x-xg x-xg x-xg'], 'bass': ['x--- ---- x--- ----', 'x--x ---- x--- -x--', 'x-x- ---- x--- ----']},
    'minimal_techno': {'hat': ['xxxx xxxx xxxx xxxx', 'x-xx x-xx x-xx x-xx', 'xgxx xgxx xgxx xgxx', 'x-X- x-X- x-X- x-X-'], 'bass': ['x--x --x- --x- x---', 'x--- x--- --x- ----', 'x-x- ---x --x- ----', 'x--- --x- x--- ---x']},
    'minimalismo_ritmico': {'kick': ['x--x --x- --x- x---', 'x--- x--x --x- --x-', 'x-x- --x- x--- x-x-'], 'hat': ['xxxx xxxx xxxx xxxx', 'x-x- xx-x x-x- xx-x'], 'bass': ['x--x --x- --x- x---', 'x-x- x--x --x- ----']},
    'psytrance': {'hat': ['--x- --x- --x- --x-', '--X- --X- --X- --X-', 'x-x- x-x- x-x- x-x-'], 'bass': ['-xxx -xxx -xxx -xxx', '-xxx -xxx -xxx -xx-', '-xxx -xxx -xxx -x-x']},
    'r&b': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--- --x- x---'], 'kick': ['x--- --x- x--- ----', 'x--- --x- x--- -x--', 'x--- ---x x--- --x-', 'x-x- ---- x--- --x-', 'x-x- --x- --x- ----', 'x--x ---x -x-x -x--', 'x-xx ---- x--x ----'], 'hat': ['x-x- x-x- x-x- x-x-'] * 4 + ['xgxg xgxg xgxg xgxg', '--x- --x- --x- --x-'], 'bass': ['x--- --x- x--- --x-', 'x--- ---x --x- x---', 'x-x- --x- x--- ----']},
    'reggae': {'hat': ['g-X- g-X- g-X- g-X-'] * 2 + ['x-X- x-X- x-X- x-X-'] * 2 + ['g-x- x-x- x-x- x-x-', 'g-X- x-X- g-X- x-Xg'], 'bass': ['x--- ---- x--- ----', 'x--x ---- x--x ----', '---- --x- x--x --x-', 'x--- --x- x--- -x--', 'x-x- x--- ---- xxx-', 'x-x- x--- --x- x---', 'x--x -xx- --x- xx--', 'x--x ---x x--x x--x']},
    'reggaeton': {'hat': ['x-x- x-x- x-x- x-x-', '--x- --x- --x- --x-', 'x-xx x-xx x-xx x-xx', 'x-x- x-xx x-x- x-xx', 'x--x x-x- x--x x-x-'], 'bass': ['x--x --x- x--- ----', 'x--x --x- x--x --x-', 'x--- --x- x--x ----']},
    'jazz': {'kick': ['x--- x--- x--- x---'] * 3 + ['x--- ---- ---- ----', 'x--- ---- --x- ----'], 'hat': ['x--- x-X- x--- x-X-'] * 3 + ['x--- x-X- x-x- x-X-'], 'bass': ['x--- x--- x--- x---'] * 5 + ['x--- x--- x--- x-x-']},
    'soul': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'kick': ['x--- ---- x--- ----', 'x--- ---x x--- ----', 'x--- --x- x--- --x-', 'x--- ---x x--- ---x', 'x--- ---- x-x- --x-', 'x--- ---x x-x- ----'], 'hat': ['x-x- x-x- x-x- x-x-'] * 3 + ['x-xg x-xg x-xg x-xg', 'x-x- x-xg x-x- x-xg'], 'bass': ['x--- ---- x--- --x-', 'x--- --x- ---- x-x-', 'x--- ---x x--- -x-x', 'x--- ---x x--x x--x', 'x--- x-x- x-x- x-x-', 'x-xx -xx- x-x- x-x-']},
    'soulful_house': {'hat': ['xgXg xgXg xgXg xgXg', 'x-Xg x-Xg x-Xg x-Xg'], 'bass': ['--x- --x- --x- --x-', '--x- --x- -xx- --x-', 'x-x- --x- --x- x---'], 'clap': ['---- x--- ---- x---', '---- x--- ---- x--x']},
    'space_disco': {'hat': ['xxXx xxXx xxXx xxXx', 'x-X- x-X- x-X- x-X-'], 'bass': ['x-x- x-x- x-x- x-x-', 'x-x- x-x- x-xx x-x-', 'x-xx x-x- x-xx x-x-'], 'snare': ['---- x--- ---- x---', '---- x--- ---- x--x']},
    'sperimentale': {'kick': ['x--- ---x --x- ----', 'x-x- --x- ---- x---', 'x--x ---- -x-- x---'], 'hat': ['x-x- -xx- x--x -x--', 'xxxx ---- xxxx ----', 'x-xx -x-x x-x- xx--'], 'bass': ['x--- x--x ---x ----', 'x-x- ---- x--x -x--']},
    'synthpop': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'kick': ['x--- x--- x--- x---'] * 7 + ['x--- ---- x--- ----'] * 4, 'hat': ['x-X- x-X- x-X- x-X-', 'xxXx xxXx xxXx xxXx', 'x-x- x-x- x-x- x-x-'], 'bass': ['x-x- x-x- x-x- x-x-', 'xxxx xxxx xxxx xxxx', 'x--x x--x x--x x--x']},
    'synthwave': {'hat': ['x-x- x-x- x-x- x-x-', 'xxxx xxxx xxxx xxxx', 'x-X- x-X- x-X- x-X-'], 'bass': ['xxxx xxxx xxxx xxxx', 'x-x- x-x- x-x- x-x-', 'x-xx x-xx x-xx x-xx'], 'snare': ['---- x--- ---- x---', '---- x--- ---- x--x']},
    'techno': {'clap': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- ---- ---- ----', '---- ---- ---- ----', '---- ---- ---- ----'], 'hat': ['x-x- x-x- x-x- x-x-'] * 2 + ['x-X- x-X- x-X- x-X-'] * 2 + ['--X- --X- --X- --X-'] * 2 + ['xxXx xxXx xxXx xxXx', 'xxx- xxx- xxx- xxx-'], 'bass': ['-xxx -xxx -xxx -xxx', '-x-x -x-x -x-x -x-x', '--x- --x- --x- --x-', 'x-x- x-x- xxx- x-x-', 'xxx- xxxx xxx- x-x-', 'x-xx xxxx x-xx x-xx', 'x-xx -x-x x-xx -x-x', 'x--x x-x- xx-x x---', 'x-x- x-x- x-x- x-x-', 'x--- x--- x--- x---', 'x--- ---- ---- ----']},
    'trance': {'snare': ['---- x--- ---- x---', '---- x--- ---- x--x'], 'hat': ['xxXx xxXx xxXx xxXx', '--X- --X- --X- --X-', 'x-X- x-X- x-X- x-X-'], 'bass': ['--x- --x- --x- --x-', '-xx- -xx- -xx- -xx-', '--x- --xx --x- --xx', '-x-x -x-x -x-x -x-x']},
    'trap': {'kick': ['x--- --x- ---- ----', 'x--- --x- --x- ----', 'x--x ---- --x- ----', 'x--- ---- -x-- x---'], 'hat': ['xxxx xxxx xxxx xxxx', 'x-xx x-xx xxxx x-xx', 'xxgx xxgx xxxg xxgx'], 'bass': ['x--- ---- ---- ----', 'x--- --x- ---- ----', 'x--- ---- --x- ----', 'x--x ---- --x- ----']},
    'trip_hop': {'kick': ['x--- --x- ---- ----', 'x--- ---- x--- ----', 'x--- --x- x--- ----', 'x--- --x- ---- x---'], 'hat': ['x-g- x-g- x-g- x-g-', 'xgxg xgxg xgxg xgxg', 'x--g x--g x--g x-xg'], 'bass': ['x--- ---- x--- ----', 'x--- --x- x--- ----', 'x--- ---- x--- --x-'], 'snare': ['---- x--- ---- x---', '---- x--- ---- x--x']},
    'uk_garage': {'kick': ['x--- ---- x--- ----', 'x--- --x- x--- ----', 'x--- ---- x--- --x-', 'x--- --x- x--- --x-'], 'hat': ['xgxg xgxg xgxg xgxg', 'x-xg x-xg x-xg x-xg', 'xgxx xgxg xgxx xgxg'], 'bass': ['--x- --x- --x- --x-', '--x- --x- ---x --x-', '--x- x-x- --x- ----', 'x-x- --x- --x- x---'], 'snare': ['---- x--- ---- x---', '---- x--- ---- x--x', '---- x--- --x- x---']},
    'underground': {'kick': ['x--- ---- x--- ----', 'x--- ---x x--- ----', 'x--- --x- x--- ----'], 'hat': ['x--x --x- x--x --x-', 'x--x --x- x--x --xx', 'x--x -xx- x--x -xx-'], 'bass': ['x--x --x- x--x --x-', 'x--x --x- x--x -x--', 'x--x -xx- x--x -xx-']},
    'vaporwave': {'kick': ['x--- ---- x--- ----', 'x--- ---- x--- -x--'], 'hat': ['g-g- g-g- g-g- g-g-', 'x-g- x-g- x-g- x-g-'], 'bass': ['x--- ---- x--- ----', 'x--- ---- x--x ----']},
}

for _g, _d in PATTERN_LIB.items():
    assert _g in GENRES, _g
    for _k, _vs in _d.items():
        for _s in _vs: _pat(_s)

def vary_genre(g, seed, name=None):
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
    if (name or g.get('_name')) == 'hip_hop' and rs.random() < HIPHOP_HALFTIME: snare = _pat('---- ---- x--- ----', True)
    _jfusion = False
    if (name or g.get('_name')) == 'jazz' and rs.random() >= JAZZ_SWING_P:
        _jfusion = True
        kick = _pat(rs.choice(JAZZ_FUSION['kick']), True); snare = _pat('---- x--- ---- x---', True)
        hat = _pat(rs.choice(JAZZ_FUSION['hat'])); bass = _pat(rs.choice(JAZZ_FUSION['bass']), True)
    if (name or g.get('_name')) == 'reggae':
        _r = rs.random()
        if _r < REGGAE_BACKBEAT: kick = _pat('---- x--- ---- x---', True); snare = list(kick)
        elif _r < REGGAE_BACKBEAT + REGGAE_ROCKERS: kick = _pat('x--- ---- x--- ----', True)
        elif _r < REGGAE_BACKBEAT + REGGAE_ROCKERS + REGGAE_STEPPERS: kick = _pat('x--- x--- x--- x---', True)
    if any(snare) and name in LOOSE_SNARE:
        snare = _mutate(snare, rs, {s for s in range(0, 16, 4) if snare[s]}, [2, 3, 6, 7, 10, 11, 14, 15], 0.3, 0.1, 0.3, 2)
    ghost = list(g.get('ghost', [0] * 16))
    if any(ghost) and name not in GHOST_FIXED:
        cand = [s for s in range(16) if s % 4 and not snare[s]]
        ghost = [0] * 16
        for s in rs.sample(cand, rs.randint(2, min(5, len(cand)))): ghost[s] = 1
    if any(bass) and name not in BASS_FIXED:
        bass = _mutate(bass, rs, {0}, [2, 3, 6, 7, 10, 11, 14, 15], 0.15 if four else 0.3, 0.1 if four else 0.15, 0.2 if four else 0.35, 1 if four else 2)
    hat = _vary_hat(hat_src, rs, groove, 0.10 if four else 0.2) if any(g['hat']) else list(g['hat'])
    g2.update(kick=kick, snare=snare, clap=clap, ghost=ghost, bass=bass, hat=hat)
    if (name or g.get('_name')) == 'techno': g2['open_voicing'] = rs.random() < 0.5
    if (name or g.get('_name')) == 'jazz':
        g2['swing8'] = 0 if _jfusion else rs.choice([0.16, 0.16, 0.16, 0.16, 0.11])
        if _jfusion: g2.update(hat_note=GM_HAT_CLOSED, kick_scale=1.0, pedal_hat=False, ghost=[0] * 16, clap=[0] * 16)
    if (name or g.get('_name')) == 'hip_hop': g2['chord_off'] = rs.choice([0, 0, 0, 0, 2])
    if (name or g.get('_name')) == 'soul': g2.update(swing8=rs.choice([0, 0, 0, 0, 0, 0.16, 0.16]), chord_off=rs.choice([0, 0, 0, 0, 0, 2]))
    if (name or g.get('_name')) == 'reggae':
        if rs.random() < REGGAE_SKANK24: g2.update(chord_off=0, skank24=True)
        g2['swing8'] = rs.choice([0, 0, 0, 0.08, 0.125, 0.16, 0.16])
        g2['skank_double'] = rs.random() < 0.4
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
    alt = {'kick': kick, 'snare': snare, 'clap': clap, 'ghost': ghost, 'hat': hat, 'perc': _perc() if any(perc) else perc}
    if any(kick) and not four and name not in FIXED_KICK:
        alt['kick'] = _mutate(kick, rs, {0}, [3, 6, 7, 10, 11, 14, 15], 0.2, 0.08, 0.35, 1)
    if any(hat): alt['hat'] = _vary_hat(hat, rs, groove, 0.14)
    g2['alt'] = alt
    return g2

# ================= TRANSIZIONI =================
GM_CRASH, GM_REVERSE = 49, 119
TOMS = (50, 48, 47, 45)
BIG_TRANSITIONS = frozenset({'acid', 'breakcore', 'commerciale_90s', 'drum_n_bass', 'dubstep', 'edm_2000s', 'elettronico', 'future_bass', 'hardstyle', 'hyperpop', 'industrial', 'jungle', 'psytrance', 'synthpop', 'techno', 'trance', 'trap'})

def _entry_strong(layers, prev):
    return ('clap' in layers and 'clap' not in prev) or ('kick' in layers and 'kick' not in prev and bool(prev))

def _pause_before(nxt_layers, cur):
    return _entry_strong(nxt_layers, cur) and bool((cur & {'roll', 'rolls'}) or 'kick' not in cur)

def _transition_fill(L, big):
    S = GM_SNARE
    t = random.choice(['snare16', 'tom', 'snare8', 'open', 'kicksn'] if big else ['open', 'tom'])
    if t == 'snare16': f = [(L - 4, S, 70), (L - 3, GM_TOM_HIGH, 85), (L - 2, S, 100), (L - 1, GM_TOM_HIGH, 115)]
    elif t == 'tom': f = [(L - 4, TOMS[0], 80), (L - 3, TOMS[1], 88), (L - 2, TOMS[2], 96), (L - 1, TOMS[3], 108)]
    elif t == 'snare8': f = [(L - 8, S, 60), (L - 6, S, 72), (L - 4, S, 84), (L - 2, S, 100), (L - 1, S, 112)]
    elif t == 'open': f = [(L - 2, GM_CLAP, 95), (L - 1, GM_HAT_OPEN, 100)]
    else: f = [(L - 4, GM_KICK, 110), (L - 3, S, 90), (L - 2, GM_KICK, 110), (L - 1, S, 115)]
    return [x for x in f if x[0] >= 0]

def build_drum_events(g, secmap, bm=None):
    if is_drumless(g): return []
    ev, q, R = [], TICKS_BEAT // 4, random.randint
    bm = bm or plan_meter(g, len(secmap), False)
    use_tr = g.get('transitions', True)
    big = g.get('_name') in BIG_TRANSITIONS
    pat_a = {'kick': g['kick'], 'snare': g.get('snare', [0] * 16), 'clap': g.get('clap', [0] * 16), 'ghost': g.get('ghost', [0] * 16), 'hat': g['hat'], 'perc': g.get('perc', [0] * 16)}
    pat_b = g.get('alt') or pat_a
    lazy = int(g.get('lazy', 0) * (TICKS_BEAT // 4))
    for bar, B in enumerate(secmap):
        layers, idx, length, prev = B['layers'], B['idx'], B['length'], B['prev']
        m = bm[bar]; base, L, pi, gst = m['start'], m['L'], m['idx'], set(m['gstarts'])
        nxt = secmap[bar + 1] if bar + 1 < len(secmap) else None
        new_sec = bool(nxt and nxt['idx'] == 0)
        crash_now = False
        if use_tr and idx == 0 and bar > 0 and not B.get('ladder'):
            strong_in = _entry_strong(layers, prev)
            kick_out = 'kick' in prev and 'kick' not in layers
            if strong_in or (big and (kick_out or len(layers - prev) >= 3)):
                crash_now = True
                _note(ev, base, TICKS_BEAT * 2, GM_CRASH, (105 if big else 72) - (15 if (kick_out and not strong_in) else 0) + R(0, 8), DRUM_CH)
        pause_from = None
        if use_tr and big and new_sec and _pause_before(nxt['layers'], layers) and L >= 8 and not B.get('ladder'):
            pause_from = L - 4
            sb = bar - 1 if idx >= 1 else bar
            rn = g.get('reverse_note', GM_REVERSE)
            if rn is not None: _note(ev, bm[sb]['start'], base + L * q - bm[sb]['start'], rn, 85, DRUM_CH)
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
        sn_shift = 4 if g.get('snare_shift') and (idx // 2) % 2 == 1 else 0
        tfill = []
        if use_tr and new_sec and idx == length - 1 and pause_from is None and not in_roll and L >= 8 and not B.get('ladder') and (layers & {'kick', 'clap'}) and nxt['layers'] != layers:
            tfill = _transition_fill(L, big)
        fill_set = {x[0] for x in tfill}
        fill_bar = 'fill' in layers and idx % 8 == 7 and not tfill
        trip_bar = bool(g.get('hat_triplet')) and 'clap' in layers and idx % 4 == 3 and L >= 8
        roll_plan, roll_cover = {}, set()
        if g.get('hat_roll') and 'clap' in layers and 'hat' in layers and L == 16 and not in_roll and not fill_bar and not tfill and not trip_bar and pause_from is None:
            def free(st): return not (P['kick'][pi[st]] or P['snare'][(pi[st] - sn_shift) % 16] or P['ghost'][pi[st]])
            cands = []
            if idx % 2 == 1: cands += [(14, 2, 'cresc'), (15, 1, 'cresc')]
            if idx % 4 == 2: cands += [(s - 1, 1, 'decay') for s in range(1, L) if P['snare'][(pi[s] - sn_shift) % 16]]
            cands = [c for c in cands if all(free(c[0] + k) for k in range(c[1]))]
            if cands and random.random() < g['hat_roll']:
                st_, span_, d_ = random.choice(cands)
                roll_plan[st_] = (random.choice((2, 2, 3, 3, 4)), span_, d_); roll_cover = set(range(st_, st_ + span_))
        for s in range(L):
            if pause_from is not None and s >= pause_from: continue
            p = pi[s]
            tick = base + s * q
            sw = int(g['swing'] * q) if s % 2 == 1 else (int(g.get('swing8', 0) * 4 * q) if s % 4 == 2 else 0)
            if 'kick' in layers and P['kick'][p] and s not in fill_set:
                if not energy: vel = (110 + R(0, 5)) if s in gst else (95 + R(0, 10))
                else: vel = (120 + R(0, 5)) if s in gst else (100 + R(0, 10))
                if s in strong: vel += 10
                vel = int(vel * g.get('kick_scale', 1.0))
                _note(ev, tick, q // 2, GM_KICK, vel, DRUM_CH)
            hat_on = 'hat' in layers and P['hat'][p]
            op = 'open' in layers and s in open_steps
            if s in roll_cover: hat_on = op = False
            if s in roll_plan:
                n_, span_, d_ = roll_plan[s]; tot = n_ * span_
                for i_ in range(tot):
                    f_ = i_ / max(1, tot - 1)
                    v_ = (55 + int(45 * f_)) if d_ == 'cresc' else (100 - int(45 * f_))
                    _note(ev, tick + i_ * q // n_, max(1, q // n_ - 6), g.get('hat_note', GM_HAT_CLOSED), v_ + R(-4, 4), DRUM_CH)
            if trip_bar and s >= L - 4:
                if s == L - 4:
                    for i_ in range(3): _note(ev, tick + i_ * (4 * q // 3), 4 * q // 3 - 10, GM_HAT_CLOSED, 68 + i_ * 14 + R(0, 8), DRUM_CH)
                hat_on = op = False
            if (hat_on or op) and not (crash_now and s == 0):
                hv = (75 + R(0, 20)) if energy else (62 + R(0, 14))
                if hat_on: hv += {2: 18, 3: -28}.get(P['hat'][p], 0)
                hv += 6 if s == 0 else (3 if s % 8 == 0 else 0)
                hv = min(hv, 105)
                if hv: _note(ev, tick + sw, (TICKS_BEAT // 2) if op else q // 2, GM_HAT_OPEN if op else g.get('hat_note', GM_HAT_CLOSED), min(110, hv + (15 if op else 0)), DRUM_CH)
            if g.get('pedal_hat') and s % 8 == 4 and not op: _note(ev, tick, q // 2, 44, 52 + R(0, 14), DRUM_CH)
            if g.get('hat_sub') and not op and random.random() < 0.35: _note(ev, tick + sw + q // 2, q // 4, GM_HAT_CLOSED, max(20, hv - 18), DRUM_CH)
            if in_roll:
                if s % roll_skip == 0: _note(ev, tick, q // 2, GM_SNARE, 55 + int(roll_amp * (rr * L + s) / (N * L)), DRUM_CH)
                if g.get('roll32') and rr == N - 1 and s >= (pause_from - 4 if pause_from is not None else L - 4) and (pause_from is None or s < pause_from): _note(ev, tick + q // 2, q // 4, GM_SNARE, 70 + R(0, 30), DRUM_CH)
            elif fill_bar and s >= L - 4:
                _note(ev, tick, q // 2, GM_SNARE if s % 2 == 0 else GM_TOM_HIGH, 70 + (s - (L - 4)) * 15, DRUM_CH)
            elif 'clap' in layers and s not in fill_set:
                if P['snare'][(p - sn_shift) % 16]: _note(ev, tick + sw + lazy, q // 2, g.get('snare_note', GM_SNARE), (90 if roll_any else 105) + R(0, 10), DRUM_CH)
                elif P['ghost'][p] and random.random() < g.get('ghost_p', 0.65): _note(ev, tick + sw, q // 2, GM_SNARE, R(g.get('ghost_vel', (36, 50))), DRUM_CH)
                if P['clap'][p]: _note(ev, tick + sw + lazy, q // 2, GM_CLAP, 90 + R(0, 10), DRUM_CH)
            if 'perc' in layers and not in_roll and not (fill_bar and s >= L - 4) and s not in fill_set:
                if P['perc'][p]: _note(ev, tick + sw, q // 2, g.get('perc_note', GM_RIMSHOT), 55 + R(0, 30), DRUM_CH)
                if s % 2 == 1 and random.random() < 0.15 and not g.get('perc_layers'): _note(ev, tick + sw, q // 2, GM_RIMSHOT if random.random() < 0.5 else GM_TOM_HIGH, 50 + R(0, 40), DRUM_CH)
            for _nm, _pits, _pr, _vl, _of in g.get('perc_layers', ()):
                if random.random() < _pr[p]: _note(ev, max(0, tick + sw + max(-10, min(30, int(random.gauss(_of[0], _of[1]))))), q // 2, random.choice(_pits), R(_vl), DRUM_CH)
            for s_, pch, v in tfill: _note(ev, base + s_ * q, q // 2, pch, min(127, int(v * (1.0 if big else 0.8)) + R(0, 6)), DRUM_CH)
    return ev

# ================= GENERAZIONE MINIMAL =================
def _bar_pools(notes):
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

BK_FREE_STYLES = {'long', 'reese', 'dubsub', 'wobble', 'logdrum', 'walk'}
BK_GAP = 10
BK_MIN_BODY = 30

def _bass_kick_composite(g, tracks, key):
    if g.get('bass_style') in BK_FREE_STYLES or not tracks.get(key) or not tracks.get('drums'): return 0
    kicks = sorted(e['tick'] for e in tracks['drums'] if e['type'] == 'on' and e['pitch'] == GM_KICK)
    if not kicks: return 0
    open_on, cut = {}, 0
    for e in sorted(tracks[key], key=lambda x: (x['tick'], x['type'] != 'off')):
        k = (e.get('channel', 0), e['pitch'])
        if e['type'] == 'on': open_on.setdefault(k, []).append(e['tick']); continue
        lst = open_on.get(k)
        if not lst: continue
        start = lst.pop(0)
        i = bisect.bisect_right(kicks, start + BK_MIN_BODY)
        if i < len(kicks) and kicks[i] < e['tick']:
            e['tick'] = max(start + 1, kicks[i] - BK_GAP); cut += 1
    return cut

def _finalize_tracks(tracks, g, seed, split_drums=False):
    if g.get('free_time'): free_time(tracks, g['free_time'])
    if g.get('human') and g.get('humanize', True): humanize(tracks, g['human'], seed)
    if split_drums and 'drums' in tracks: tracks = split_drum_track(tracks)
    return tracks

def generate_minimal(notes_data, g, submode, bars, seed, dna=None):
    random.seed(seed)
    g = vary_genre(g, seed, g.get('_name'))
    bars, sections = compute_structure(bars, g.get('timeline'), seed)
    secmap = section_map(sections, bars)
    q, bt = TICKS_BEAT // 4, 4 * TICKS_BEAT
    root, scale = dna or extract_dna(notes_data)
    n = len(scale)
    remix = (submode == 'extract') and bool(notes_data)
    bm = plan_meter(g, bars, not remix, seed)
    tracks = {'bass': [], 'arp': [], 'drums': build_drum_events(g, secmap, bm)}
    bass_gap = _gaps([s for s in range(16) if g['bass'][s]]) if any(g['bass']) else {}
    if remix:
        pools, first_b, last_b = _bar_pools(notes_data)
        loop_bars = last_b - first_b + 1
    else:
        counts = Counter(p['pitch'] % 12 for p in notes_data)
        w = [counts.get((root + i) % 12, 0) + 0.5 for i in scale]
        if not notes_data: w[0] += 2
        pick = lambda: random.choices(range(n), weights=w)[0]
        motif = [pick() if random.random() < g['arp_density'] else None for _ in range(16)]
        while sum(x is not None for x in motif) < 3: motif[random.randrange(16)] = pick()
        m_cur = motif
        bass_prog = [0, random.choice([0, pick()]), pick(), pick()]
        loops_ = None if random.random() < 0.15 else (_L_MAJOR if 4 in scale[:3] else _L_MINOR.get(g.get('_name')))
        if loops_: bass_prog = list(random.choices(loops_, weights=[sum(w[d % n] for d in lp) + 0.1 for lp in loops_])[0])
        mel_st = {'cur': None, 'tpl': _mel_template()}
    arp_counter = 0
    arp_base = random.choice([60, 67, 72])
    
    # Coherent state
    coherent_state = {'macro_motif': None, 'rhythm_motif': None, 'last_pitch_deg': 0}
    
    for bar, B in enumerate(secmap):
        layers, idx, length = B['layers'], B['idx'], B['length']
        bass_full, bass_soft = 'bass' in layers, 'bassl' in layers
        factor = max([SYN_FACTOR[t] for t in layers if t in SYN_FACTOR] or [0])
        if not (bass_full or bass_soft or factor or 'event' in layers): continue
        m = bm[bar]; base, L, pi, gst = m['start'], m['L'], m['idx'], set(m['gstarts'])
        ramp = idx / max(1, length - 1)
        if 'event' in layers:
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
            
        # COHERENT MELODY ENGINE
        if g.get('coherent') and not remix:
            phrase_len, subphrase_len = get_phrase_config(g.get('_name', 'default'), B.get('sec', 'drop'), length)
            bar_in_phrase = idx % phrase_len
            is_phrase_start = (bar_in_phrase == 0)
            is_subphrase_start = (bar_in_phrase % subphrase_len == 0)
            is_phrase_end = (bar_in_phrase == phrase_len - 1)
            is_answer_subphrase = (bar_in_phrase >= subphrase_len)
            
            if is_phrase_start or coherent_state['macro_motif'] is None:
                coherent_state['macro_motif'] = generate_macro_motif(phrase_len, n, random)
                density = int(g.get('arp_density', 0.5) * 16)
                rhythm_motif = [False] * 16
                rhythm_motif[0] = True
                active_pos = random.sample(range(1, 16), max(1, min(density - 1, 10)))
                for pos in active_pos: rhythm_motif[pos] = True
                coherent_state['rhythm_motif'] = rhythm_motif
                
            motif_offset = bar_in_phrase * 4
            current_bar_intervals = coherent_state['macro_motif'][motif_offset : motif_offset + 4]
            current_rhythm = coherent_state['rhythm_motif']
            chord_tones = {d % n, (d + 2) % n, (d + 4) % n}
            coherent_notes = []
            base_deg = coherent_state['last_pitch_deg']
            active_steps = [i for i, active in enumerate(current_rhythm) if active]
            
            for i, step in enumerate(active_steps):
                is_strong_beat = (step % 4 == 0)
                if i < len(current_bar_intervals) and current_bar_intervals[i] is not None:
                    target_deg = base_deg + current_bar_intervals[i]
                else:
                    target_deg = base_deg
                    
                if is_strong_beat:
                    valid_targets = [t for t in range(-n, 2*n) if t % n in chord_tones]
                    target_deg = min(valid_targets, key=lambda x: abs(x - target_deg))
                else:
                    target_deg = target_deg % n 
                    
                if is_answer_subphrase and step == active_steps[-1] and is_phrase_end:
                    target_deg = 0 
                    
                next_step = active_steps[i + 1] if i + 1 < len(active_steps) else 16
                duration = next_step - step
                coherent_notes.append((step, target_deg, duration))
                base_deg = target_deg
                
            coherent_state['last_pitch_deg'] = base_deg
            
            for step, deg, dur in coherent_notes:
                track_key = 'arp'
                pitch = _deg_pitch(root, scale, deg, arp_base)
                vel = 85 if step % 4 == 0 else 65
                tick_offset = base + step * q
                if g.get('humanize', True): tick_offset += random.randint(-5, 5)
                _note(tracks[track_key], tick_offset, dur * q - 10, pitch, vel, 1)
                
        elif not remix:
            if bar % 4 == 0: mel_st['tpl'] = list(mel_st['real']) if (MOTIF_PHRASE_REUSE and (bar // 4) % 2 == 1 and mel_st.get('real')) else _mel_template(); mel_st['phrase_start'] = True
            bd = bass_prog[bar % 4] % n
            mel = melody_bar([s for s in range(L) if m_cur[pi[s]] is not None], gst | set(range(0, L, 4)), {bd, (bd + 2) % n, (bd + 4) % n}, bd, n, mel_st, 0 if bar % 4 < 2 else (1 if bar % 4 == 2 else 2))
            cbm = corpus_bar(g, bar, n, {bd, (bd + 2) % n, (bd + 4) % n}, mel_st) if L == 16 else None
            mel_dur = {}
            if cbm is not None: mel, mel_dur = {s: dg for s, dg, _d in cbm}, {s: d for s, _dg, d in cbm}
            for s in range(L):
                if s in mel and random.random() < factor:
                    dg = mel[s]
                    _note(tracks['arp'], base + s * q + (int(g.get('swing8', 0) * 4 * q) if s % 4 == 2 else 0), mel_dur.get(s, 1) * q - 20, _deg_pitch(root, scale, dg, arp_base), int((arp_vel + random.randint(0, 8)) * fs), 1)

        for s in range(L):
            p = pi[s]
            tick = base + s * q
            sw = int(g['swing'] * q) if s % 2 == 1 else 0
            t_abs = (ob * bt + s * q) if remix else 0
            if g['bass'][p] and (bass_full or (bass_soft and s in gst)):
                if remix:
                    snd = [p for st, en, p in pool if st <= t_abs < en] or [p for _s, _e, p in pool]
                    pc = min(snd) % 12
                else:
                    pc = (root + scale[(bass_prog[bar % 4] if random.random() < 0.8 else pick()) % n]) % 12
                gap = bass_gap[p] if L == 16 else min(bass_gap[p], L - s)
                oc, dur, vx = _bass_shape(g.get('bass_style'), hit, gap, L - s, s); hit += 1
                _note(tracks['bass'], tick, dur * q - 15, _bass_pitch(pc) + oc, min(127, max(1, int(((95 if bass_full else 82) + (5 if s in gst else 0) + vx) * fb))), 0)

    tr_ = {k: v for k, v in tracks.items() if v}
    _bass_kick_composite(g, tr_, 'bass')
    tr_ = _finalize_tracks(tr_, g, seed)
    return tr_, root, scale

# ================= GENERAZIONE MULTITRACK =================
def _extract_instrument_header(track):
    header = []
    for msg in track:
        if msg.type in ('note_on', 'note_off'): break
        if msg.type == 'program_change': header.append({'type': 'program_change', 'program': msg.program})
        elif msg.type == 'control_change' and msg.control in (0, 32, 7, 10, 11, 91, 93):
            header.append({'type': 'control_change', 'control': msg.control, 'value': msg.value})
    return header

GM_PROGRAM_NAMES = ['Acoustic Grand Piano', 'Bright Acoustic Piano', 'Electric Grand Piano', 'Honky-tonk Piano', 'Electric Piano 1', 'Electric Piano 2', 'Harpsichord', 'Clavinet', 'Celesta', 'Glockenspiel', 'Music Box', 'Vibraphone', 'Marimba', 'Xylophone', 'Tubular Bells', 'Dulcimer', 'Drawbar Organ', 'Percussive Organ', 'Rock Organ', 'Church Organ', 'Reed Organ', 'Accordion', 'Harmonica', 'Tango Accordion', 'Acoustic Guitar (nylon)', 'Acoustic Guitar (steel)', 'Electric Guitar (jazz)', 'Electric Guitar (clean)', 'Electric Guitar (muted)', 'Overdriven Guitar', 'Distortion Guitar', 'Guitar Harmonics', 'Acoustic Bass', 'Electric Bass (finger)', 'Electric Bass (pick)', 'Fretless Bass', 'Slap Bass 1', 'Slap Bass 2', 'Synth Bass 1', 'Synth Bass 2', 'Violin', 'Viola', 'Cello', 'Contrabass', 'Tremolo Strings', 'Pizzicato Strings', 'Orchestral Harp', 'Timpani', 'String Ensemble 1', 'String Ensemble 2', 'Synth Strings 1', 'Synth Strings 2', 'Choir Aahs', 'Voice Oohs', 'Synth Voice', 'Orchestra Hit', 'Trumpet', 'Trombone', 'Tuba', 'Muted Trumpet', 'French Horn', 'Brass Section', 'Synth Brass 1', 'Synth Brass 2', 'Soprano Sax', 'Alto Sax', 'Tenor Sax', 'Baritone Sax', 'Oboe', 'English Horn', 'Bassoon', 'Clarinet', 'Piccolo', 'Flute', 'Recorder', 'Pan Flute', 'Blown Bottle', 'Shakuhachi', 'Whistle', 'Ocarina', 'Lead 1 (square)', 'Lead 2 (sawtooth)', 'Lead 3 (calliope)', 'Lead 4 (chiff)', 'Lead 5 (charang)', 'Lead 6 (voice)', 'Lead 7 (fifths)', 'Lead 8 (bass + lead)', 'Pad 1 (new age)', 'Pad 2 (warm)', 'Pad 3 (polysynth)', 'Pad 4 (choir)', 'Pad 5 (bowed)', 'Pad 6 (metallic)', 'Pad 7 (halo)', 'Pad 8 (sweep)', 'FX 1 (rain)', 'FX 2 (soundtrack)', 'FX 3 (crystal)', 'FX 4 (atmosphere)', 'FX 5 (brightness)', 'FX 6 (goblins)', 'FX 7 (echoes)', 'FX 8 (sci-fi)', 'Sitar', 'Banjo', 'Shamisen', 'Koto', 'Kalimba', 'Bag pipe', 'Fiddle', 'Shanai', 'Tinkle Bell', 'Agogo', 'Steel Drums', 'Woodblock', 'Taiko Drum', 'Melodic Tom', 'Synth Drum', 'Reverse Cymbal', 'Guitar Fret Noise', 'Breath Noise', 'Seashore', 'Bird Tweet', 'Telephone Ring', 'Helicopter', 'Applause', 'Gunshot']
_GM_NAME_HINTS = [(("bass", "basso", "contrabb"), 33), (("chitarr", "guitar"), 25), (("piano", "pianof"), 0), (("organ", "organo"), 19), (("string", "archi", "violin", "cello"), 48), (("pad",), 89), (("lead",), 80), (("vox", "voce", "vocal", "choir", "coro"), 52), (("flaut", "flute"), 73), (("sax",), 65), (("trump", "tromba"), 56), (("tromb",), 57), (("synth",), 81)]

def _guess_program(name):
    low = (name or "").lower()
    for keys, prog in _GM_NAME_HINTS:
        if any(k in low for k in keys): return prog
    return 0

DRUM_GROUPS = [('drum_kick', {GM_KICK}), ('drum_snare', {GM_SNARE}), ('drum_hat', {GM_HAT_CLOSED, GM_HAT_OPEN, GM_RIDE, 44}), ('drum_clap', {GM_CLAP}), ('drum_perc', {GM_RIMSHOT, GM_TOM_HIGH, 54, 56, 70, 75, 43, 45, 47, 48}), ('drum_fx', {49, 57, 119})]
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
    q, bt, grid = TICKS_BEAT // 4, 4 * TICKS_BEAT, TICKS_BEAT // 16
    free_channels = [c for c in range(16) if c != DRUM_CH]
    by_track = {}
    for nt in all_notes: by_track.setdefault(nt['track'], []).append(nt)
    prepared = {}
    for ti, lst in by_track.items():
        prepared[ti] = [(int(round(nt['tick'] / grid)) * grid, max(grid, int(round(nt['dur'] / grid)) * grid), snap_to_scale(nt['pitch'], root, scale), nt['vel']) for nt in lst]
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
        mel = B['sec'] if B['sec'] in ('break1', 'break2', 'build', 'drop') else 'break1'
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
    if len(scale) <= 8: return scale
    ideal = [0, 2, 3, 5, 7, 8, 10] if _is_minor_scale(scale) else [0, 2, 4, 5, 7, 9, 11]
    sel = [i for i in ideal if i in scale]
    return sel if len(sel) >= 5 else ideal

def _add_reese(g, tracks):
    if g.get('bass_style') == 'reese' and tracks.get('bassline'):
        tracks['reese'] = [dict(e, channel=7) for e in tracks['bassline']]

_P_MINOR = {'techno': .70, 'minimal_techno': .82, 'underground': .82, 'industrial': .85, 'acid': .8, 'hip_hop': .70, 'trap': .85, 'trance': .68, 'psytrance': .85, 'edm_2000s': .58, 'elettronico': .58, 'synthpop': .53, 'reggae': .50, 'disco': .46, 'space_disco': .5, 'funk': .40, 'r&b': .34, 'soul': .15, 'jazz': .45, 'house_90s': .54, 'commerciale_90s': .5, 'ambient': .5, 'drone': .6}
_MINOR_SCALES = (('Minore naturale', 60), ('Dorico', 20), ('Pentatonica minore', 10), ('Minore armonica', 5), ('Frigio', 5))
_MAJOR_SCALES = (('Maggiore', 75), ('Misolidio', 25))

def random_scale_for_genre(genre, rng):
    pool = _MINOR_SCALES if rng.random() < _P_MINOR.get(genre, 0.65) else _MAJOR_SCALES
    return rng.choices([n for n, _ in pool], weights=[w for _, w in pool])[0]

_L_STATIC = [[0, 0, 0, 0], [0, 0, 0, 6], [0, 0, 3, 0], [0, 0, 5, 6]]
_L_MINOR = {'techno': _L_STATIC, 'minimal_techno': _L_STATIC, 'minimal': _L_STATIC, 'underground': _L_STATIC, 'industrial': _L_STATIC, 'acid': [[0, 0, 0, 0], [0, 0, 6, 0], [0, 0, 3, 6]], 'dub_techno': [[0, 3, 0, 3], [0, 0, 0, 0], [0, 6, 0, 6]], 'house_90s': [[0, 6, 5, 6], [0, 5, 2, 6], [0, 3, 6, 2]], 'deep': [[0, 6, 0, 2], [1, 0, 2, 3], [3, 5, 0, 0], [0, 2, 0, 2], [6, 5, 4, 0], [0, 1, 0, 3], [0, 3, 5, 4], [2, 0, 6, 0]], 'soulful_house': [[0, 3, 6, 2], [3, 6, 2, 5], [0, 5, 3, 6]], 'afro_house': [[0, 6, 5, 6], [0, 3, 0, 6], [0, 5, 6, 0]], 'amapiano': [[0, 3, 5, 6], [0, 5, 3, 6], [0, 6, 5, 3]], 'uk_garage': [[0, 5, 3, 6], [5, 3, 0, 6], [0, 3, 6, 5]], 'trance': [[0, 5, 2, 6], [0, 6, 5, 4], [5, 2, 6, 0]], 'psytrance': [[0, 0, 5, 6], [0, 0, 0, 6], [0, 6, 0, 5]], 'edm_2000s': [[0, 5, 2, 6], [0, 6, 5, 4], [5, 2, 6, 0]], 'elettronico': [[0, 5, 2, 6], [0, 6, 5, 6], [0, 3, 5, 6]], 'hardstyle': [[0, 5, 2, 6], [0, 6, 5, 6], [0, 0, 5, 6]], 'commerciale_90s': [[0, 5, 2, 6], [0, 3, 5, 6], [0, 6, 5, 4]], 'synthpop': [[0, 5, 2, 6], [0, 3, 5, 6], [0, 6, 5, 4]], 'synthwave': [[0, 5, 2, 6], [0, 6, 5, 4], [0, 3, 6, 5]], 'chiptune': [[0, 5, 2, 6], [0, 6, 5, 6], [0, 3, 6, 0]], 'vaporwave': [[3, 6, 2, 5], [0, 5, 3, 6], [5, 3, 6, 0]], 'hyperpop': [[0, 5, 2, 6], [0, 6, 5, 4], [5, 6, 0, 0]], 'future_bass': [[5, 3, 0, 6], [0, 5, 3, 6], [3, 5, 0, 6]], 'trap': [[0, 5, 6, 4], [0, 5, 3, 6], [0, 6, 5, 4], [0, 0, 5, 6]], 'hip_hop': [[0, 5, 3, 6], [0, 3, 5, 6], [5, 3, 0, 6], [0, 6, 5, 6]], 'reggaeton': [[0, 6, 5, 6], [0, 5, 6, 0], [0, 3, 6, 5]], 'trip_hop': [[0, 5, 3, 6], [0, 3, 0, 6], [5, 3, 0, 0]], 'r&b': [[3, 6, 2, 5], [0, 5, 3, 6], [5, 3, 0, 6]], 'soul': [[3, 6, 2, 5], [0, 5, 3, 6], [0, 3, 6, 2]], 'jazz': [[1, 4, 0, 0], [0, 3, 6, 2], [5, 1, 4, 0], [3, 6, 2, 5]], 'funk': [[0, 0, 3, 3], [0, 3, 0, 6], [0, 0, 3, 6]], 'disco': [[3, 6, 2, 5], [0, 3, 6, 2], [5, 3, 0, 6], [0, 0, 0, 0], [0, 4, 0, 4], [6, 0, 0, 0], [6, 0, 4, 0], [0, 3, 0, 3], [5, 4, 5, 4], [3, 0, 0, 4]], 'space_disco': [[0, 3, 6, 5], [3, 6, 2, 5], [0, 5, 3, 6]], 'reggae': [[0, 3, 0, 3], [0, 6, 0, 6], [0, 3, 0, 6], [0, 2, 0, 6], [0, 3, 5, 4], [0, 6, 5, 4], [0, 3, 0, 4]], 'drum_n_bass': [[0, 5, 2, 6], [0, 6, 5, 6], [0, 3, 5, 6]], 'jungle': [[0, 0, 3, 0], [0, 0, 5, 6], [0, 0, 0, 0]], 'dubstep': [[0, 0, 0, 5], [0, 0, 6, 5], [0, 0, 5, 6]], 'breakcore': [[0, 0, 0, 0], [0, 0, 6, 0], [0, 0, 5, 6]], 'glitch': [[0, 3, 2, 6], [0, 5, 3, 6], [0, 0, 5, 6]], 'idm': [[0, 3, 2, 6], [0, 2, 5, 6], [0, 5, 3, 0]], 'ambient': [[0, 5, 3, 6], [0, 2, 5, 6], [0, 0, 5, 5]], 'drone': [[0, 0, 0, 0], [0, 0, 0, 5], [0, 0, 3, 3]], 'lowercase': [[0, 0, 0, 0], [0, 0, 3, 0]], 'microsound': [[0, 0, 0, 0], [0, 0, 5, 0]], 'onkyo': [[0, 0, 0, 0], [0, 0, 0, 3]], 'noise': [[0, 0, 0, 0], [0, 0, 6, 0]], 'harsh_noise': [[0, 0, 0, 0]], 'musique_concrete': [[0, 0, 0, 0], [0, 0, 5, 0], [0, 3, 0, 6]], 'sperimentale': [[0, 3, 2, 6], [0, 0, 5, 0], [0, 5, 3, 0]], 'minimalismo_ritmico': [[0, 0, 2, 0], [0, 0, 3, 0], [0, 0, 0, 5]], 'armonico': [[3, 6, 2, 5], [0, 5, 3, 6], [0, 3, 6, 2]]}
_L_MAJOR = [[0, 4, 5, 3], [0, 5, 3, 4], [0, 3, 4, 3], [0, 5, 1, 4], [0, 3, 0, 4], [0, 3, 1, 4], [3, 4, 0, 5]]
_L_MAJOR_GENRE = {'jazz': [[1, 4, 0, 5], [0, 5, 1, 4], [2, 5, 1, 4], [1, 4, 0, 3]], 'soul': [[0, 3, 0, 3], [0, 4, 0, 4], [3, 4, 0, 0], [0, 0, 5, 5], [4, 3, 4, 3], [5, 1, 0, 1], [0, 2, 3, 0], [0, 0, 0, 0]], 'disco': [[5, 0, 5, 0], [5, 4, 3, 4], [2, 1, 2, 4], [0, 0, 0, 0], [4, 0, 4, 0], [5, 6, 0, 0], [5, 4, 3, 3]], 'reggae': [[0, 3, 0, 3], [0, 4, 3, 4], [0, 1, 4, 0], [0, 1, 3, 0], [3, 3, 4, 5], [0, 3, 4, 3], [0, 5, 3, 4], [0, 4, 5, 3]]}
_L_MAJOR_CLOSE = [[0, 3, 4, 0], [0, 1, 4, 0], [3, 1, 4, 0]]
VL_DRIFT = 1.5
VL_SPAN_MAX = 14
VL_WIN = (-4, 17)

def _vl_voice(prev, pcs, lo):
    base = [_pc_pitch(pc, lo) for pc in pcs]
    if not prev or len(prev) != len(pcs): return base
    opts = [[p for p in range(lo + VL_WIN[0], lo + VL_WIN[1]) if p % 12 == pc % 12] for pc in pcs]
    best = None
    for combo in itertools.product(*opts):
        srt = sorted(combo)
        if len(set(srt)) < len(srt) or srt[-1] - srt[0] > VL_SPAN_MAX: continue
        key = (sum(abs(a - b) for a, b in zip(srt, prev)) + VL_DRIFT * abs(sum(srt) / len(srt) - (lo + 6)), srt[-1] - srt[0])
        if best is None or key < best[0]: best = (key, list(combo))
    return best[1] if best else base

_TECHNO_PAIRS = [([0, 0, 5, 5], [0, 0, 5, 5]), ([0, 0, 6, 6], [5, 5, 6, 6]), ([0, 0, 3, 3], [6, 6, 0, 0]), ([0, 0, 5, 5], [2, 2, 6, 6])]

def _pick_loops(g, scale):
    major = 4 in scale[:3]
    if g.get('_name') == 'techno' and not major and random.random() < g.get('melodic_loops', 0):
        a, b = random.choice(_TECHNO_PAIRS); return list(a), list(b)
    pool = _L_MAJOR_GENRE.get(g.get('_name'), _L_MAJOR) if major else _L_MINOR.get(g.get('_name'))
    if not pool or random.random() < 0.15: return None
    if major and g.get('_name') not in _L_MAJOR_GENRE:
        a = list(random.choice([x for x in pool if x[-1] == 4]))
        b = list(random.choice(_L_MAJOR_CLOSE if random.random() < 0.65 else [x for x in pool if x != a]))
        return a, b
    a = list(random.choice(pool)); b = list(random.choice([x for x in pool if x != a] or pool))
    return a, b

def _arrange_generative(g, root, scale, secmap, tracks, bm=None):
    q = TICKS_BEAT // 4
    bm = bm or plan_meter(g, len(secmap), False)
    scale = _tame_scale(scale)
    n = len(scale)
    pc_of = lambda d: (root + scale[d % n]) % 12
    for role in ('sub_bass', 'bassline', 'pad', 'chords', 'arp', 'lead', 'fx_perc'): tracks[role] = []
    def _rand_prog():
        head = 0 if random.random() < 0.85 else random.choice([3, 4])
        return [head] + random.choices([2, 3, 4, 5, 1, 6], weights=[2, 3, 4, 3, 1, 1], k=3)
    prog_a, prog_b = _pick_loops(g, scale) or (_rand_prog(), _rand_prog())
    use7 = random.random() < g.get('seventh', 0.35)
    use9 = random.random() < g.get('ninth', 0.0)
    ped = bool(g.get('bass_pedal')) and random.random() < g['bass_pedal']
    bass_style = g.get('bass_style')
    chord_off = g['chord_off'] if 'chord_off' in g else random.choice([0, 1, 2, 2, 3])
    arp_base, lead_oct = random.choice([60, 67, 72]), random.choice([67, 72])
    bass_root_p, lead_p = BASS_ROOT_P.get(bass_style, random.uniform(0.6, 0.9)), random.uniform(0.3, 0.6)
    if ped: bass_root_p = min(bass_root_p, 0.85)
    bass_steps = [s for s in range(16) if g['bass'][s]]
    bass_gap = _gaps(bass_steps) if bass_steps else {}
    lead_base = [random.randrange(n) if random.random() < lead_p else None for _ in range(16)]
    lead = lead_base
    lead_q, lead_a = _question(lead_base, n), _answer(lead_base)
    arp_mode, R = 'up', random.randint
    mel_st = {'cur': None, 'tpl': _mel_template()}
    vl_prev = {}
    
    coherent_state = {'macro_motif': None, 'rhythm_motif': None, 'last_pitch_deg': 0}

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
                else: blk = [None if random.random() < 0.3 else x for x in lead_base]
            lead_q, lead_a = _question(blk, n), _answer(blk)
            mel_st['tpl'] = list(mel_st['real']) if (MOTIF_PHRASE_REUSE and (bar // 4) % 2 == 1 and mel_st.get('real')) else _mel_template()
            mel_st['phrase_start'] = True
        lead = lead_a if bar % 4 == 3 else ([None if random.random() < 0.3 else x for x in lead_q] if bar % 4 == 2 else lead_q)
        d = (prog_a if (bar // 4) % 2 == 0 else prog_b)[bar % 4]
        d_next = (prog_a if ((bar + 1) // 4) % 2 == 0 else prog_b)[(bar + 1) % 4]
        d_prev = (prog_a if ((bar - 1) // 4) % 2 == 0 else prog_b)[(bar - 1) % 4] if bar > 0 else d
        cpcs = [pc_of(d), pc_of(d + 2), pc_of(d + 4)] + ([pc_of(d + 6)] if use7 else []) + ([pc_of(d + 8)] if use9 else [])
        rpc = cpcs[0]
        ramp = idx / max(1, length - 1)
        roll_any, energy = bool(layers & {'roll', 'rolls'}), 'clap' in layers
        if 'event' in layers:
            _note(tracks['lead'], base + random.randrange(L) * q, 2 * q, _pc_pitch(pc_of(random.randrange(n)), lead_oct), 32 + R(0, 18), 5)
        if 'bass' in layers or 'bassl' in layers:
            soft, fb = 'bass' not in layers, _fade(B, 'bass')
            bcp = [pc_of(0), pc_of(4), pc_of(4), pc_of(2), pc_of(6)] if ped else cpcs
            brp = bcp[0]
            _note(tracks['sub_bass'], base, bt - 20, _pc_pitch(brp, 24), int((84 if soft else 100) * fb), 0)
            hit = 0
            last_hit = max([s for s in range(L) if g['bass'][pi[s]] and not (soft and s not in gst)] or [-1])
            for s in range(L):
                if not g['bass'][pi[s]]: continue
                if soft and s not in gst: continue
                pc = _bass_pc(bass_style, hit, bcp, brp, bass_root_p)
                if s == last_hit and not ped and d_next != d and g.get('bass_approach') and random.random() < g['bass_approach']:
                    pc = pc_of(d + 4) if random.random() < 0.5 else (pc_of(d_next) - 1) % 12
                gap = bass_gap[pi[s]] if L == 16 else min(bass_gap[pi[s]], L - s)
                oc, dur, vx = _bass_shape(bass_style, hit, gap, L - s, s); hit += 1
                _note(tracks['bassline'], base + s * q, dur * q - 15, _pc_pitch(pc, 36) + oc, min(127, max(1, int(((82 if soft else 95) + (5 if s in gst else 0) + vx) * fb))), 1)
        if 'pad' in layers:
            pad_vel = int(((62 if energy else 52) + (int(15 * ramp) if roll_any else 0)) * _fade(B, 'pad'))
            if g.get('open_pad') or g.get('open_voicing'):
                _pps = [_pc_pitch(cpcs[0], 48), _pc_pitch(cpcs[2], 48)] + [_pc_pitch(pc, 60) for pc in [cpcs[1]] + cpcs[3:]]
            else:
                _pps = _vl_voice(vl_prev.get('pad'), cpcs, g.get('pad_lo', 48)); vl_prev['pad'] = sorted(_pps)
            for _pp in _pps: _note(tracks['pad'], base, bt - 10, _pp, pad_vel, 2)
        c_steps, c_dur, c_vel = [], 0, 0
        if 'chords' in layers: c_steps, c_dur, c_vel = [x + chord_off for x in gstarts if x + chord_off < L and (not g.get('skank24') or x in (4, 12))], q + q // 2, (65 + int(25 * ramp)) if roll_any else 80
        elif 'chordsl' in layers: c_steps, c_dur, c_vel = [gstarts[0], gstarts[len(gstarts) // 2]], 2 * TICKS_BEAT - 20, 58
        cf = _fade(B, 'chords')
        _cv_vl = None
        if c_steps and not g.get('open_voicing'): _cv_vl = _vl_voice(vl_prev.get('chords'), cpcs, g.get('chords_lo', 55)); vl_prev['chords'] = sorted(_cv_vl)
        if g.get('skank_double') and 'chords' in layers: c_steps = sorted(set(c_steps + [x + 1 for x in c_steps if x + 1 < L]))
        for s in c_steps:
            if 'chords' in layers and not roll_any and random.random() > 0.85: continue
            _dbl = bool(g.get('skank_double')) and s % 4 == 3
            _sw8 = int(g.get('swing8', 0) * 4 * q) if s % 4 in (2, 3) else 0
            _cvs = ([_pc_pitch(cpcs[0], 43), _pc_pitch(cpcs[2], 55)] + [_pc_pitch(pc, 60) for pc in [cpcs[1]] + cpcs[3:]]) if g.get('open_voicing') else (_cv_vl or [_pc_pitch(pc, g.get('chords_lo', 55)) for pc in cpcs])
            for _pv in _cvs: _note(tracks['chords'], base + s * q + _sw8, c_dur // 2 if _dbl else c_dur, _pv, int((c_vel + R(0, 8)) * cf * (0.75 if _dbl else 1.0)), 3)
        if 'arp' in layers or 'arpl' in layers:
            tones = sorted(_pc_pitch(pc, arp_base) + 12 * k for pc in cpcs for k in (0, 1))
            factor = (1.0 if 'arp' in layers else 0.5) * ((0.85 + 0.15 * ramp) if roll_any else 1.0)
            a_vel = 72 if energy else ((58 + int(20 * ramp)) if roll_any else 52)
            af = _fade(B, 'arp')
            NT = len(tones)
            for s in range(L):
                if random.random() < min(1.0, g['arp_density'] * factor):
                    if arp_mode == 'up': i = s % NT
                    elif arp_mode == 'updown':
                        k = s % (2 * (NT - 1)); i = k if k < NT else 2 * (NT - 1) - k
                    else: i = random.randrange(NT)
                    sw = int(g['swing'] * q) if s % 2 == 1 else 0
                    sub_ = bool(g.get('arp_sub'))
                    _note(tracks['arp'], base + s * q + sw, (q // 2 - 5) if sub_ else (q - 10), tones[i], int((a_vel + R(0, 8)) * af), 4)
                    if sub_: _note(tracks['arp'], base + s * q + sw + q // 2, q // 2 - 5, tones[(i + 1) % NT], int((a_vel - 8 + R(0, 8)) * af), 4)
                    
        # COHERENT MELODY ENGINE FOR MULTITRACK
        if g.get('coherent') and ('lead' in layers or 'leadl' in layers):
            phrase_len, subphrase_len = get_phrase_config(g.get('_name', 'default'), B.get('sec', 'drop'), length)
            bar_in_phrase = idx % phrase_len
            is_phrase_start = (bar_in_phrase == 0)
            is_subphrase_start = (bar_in_phrase % subphrase_len == 0)
            is_phrase_end = (bar_in_phrase == phrase_len - 1)
            is_answer_subphrase = (bar_in_phrase >= subphrase_len)
            
            if is_phrase_start or coherent_state['macro_motif'] is None:
                coherent_state['macro_motif'] = generate_macro_motif(phrase_len, n, random)
                density = int(g.get('arp_density', 0.5) * 16)
                rhythm_motif = [False] * 16
                rhythm_motif[0] = True
                active_pos = random.sample(range(1, 16), max(1, min(density - 1, 10)))
                for pos in active_pos: rhythm_motif[pos] = True
                coherent_state['rhythm_motif'] = rhythm_motif
                
            motif_offset = bar_in_phrase * 4
            current_bar_intervals = coherent_state['macro_motif'][motif_offset : motif_offset + 4]
            current_rhythm = coherent_state['rhythm_motif']
            chord_tones = {d % n, (d + 2) % n, (d + 4) % n}
            coherent_notes = []
            base_deg = coherent_state['last_pitch_deg']
            active_steps = [i for i, active in enumerate(current_rhythm) if active]
            
            for i, step in enumerate(active_steps):
                is_strong_beat = (step % 4 == 0)
                if i < len(current_bar_intervals) and current_bar_intervals[i] is not None:
                    target_deg = base_deg + current_bar_intervals[i]
                else:
                    target_deg = base_deg
                    
                if is_strong_beat:
                    valid_targets = [t for t in range(-n, 2*n) if t % n in chord_tones]
                    target_deg = min(valid_targets, key=lambda x: abs(x - target_deg))
                else:
                    target_deg = target_deg % n 
                    
                if is_answer_subphrase and step == active_steps[-1] and is_phrase_end:
                    target_deg = 0 
                    
                next_step = active_steps[i + 1] if i + 1 < len(active_steps) else 16
                duration = next_step - step
                coherent_notes.append((step, target_deg, duration))
                base_deg = target_deg
                
            coherent_state['last_pitch_deg'] = base_deg
            
            for step, deg, dur in coherent_notes:
                full = 'lead' in layers
                if not full and step not in gst: continue
                pitch = _deg_pitch(root, scale, deg, lead_oct)
                vel = 88 if full else 70
                tick_offset = base + step * q + (int(g.get('swing8', 0) * 4 * q) if step % 4 == 2 else 0)
                if g.get('humanize', True): tick_offset += random.randint(-5, 5)
                _note(tracks['lead'], tick_offset, (dur if full else 8) * q - 10, pitch, int(vel * _fade(B, 'lead')), 5)
                
        elif ('lead' in layers or 'leadl' in layers) and not g.get('coherent'):
            l_steps = [s for s, v in enumerate(lead) if v is not None]
            if l_steps:
                full, lf, gaps = 'lead' in layers, _fade(B, 'lead'), _gaps(l_steps)
                ct_deg = {d % n, (d + 2) % n, (d + 4) % n} | ({(d + 6) % n} if use7 else set())
                mel = melody_bar([s for s in range(L) if lead[pi[s]] is not None and (full or s in gst)], gst | {x for x in range(0, L, 4)}, ct_deg, d, n, mel_st, 0 if bar % 4 < 2 else (1 if bar % 4 == 2 else 2))
                mel_st['chg_in'], mel_st['chg_next'] = d != d_prev, d_next != d
                cb = corpus_bar(g, bar, n, ct_deg, mel_st) if L == 16 else None
                for s, dg, du_ in (cb or ()):
                    if not full and s not in gst: continue
                    _note(tracks['lead'], base + s * q + (int(g.get('swing8', 0) * 4 * q) if s % 4 == 2 else 0), (du_ if full else 8) * q - 10, _deg_pitch(root, scale, dg, lead_oct), int((88 if full else 70) * lf), 5)
                for s in (range(L) if cb is None else ()):
                    lp = pi[s]
                    if lead[lp] is None: continue
                    if not full and s not in gst: continue
                    gp = gaps[lp] if L == 16 else min(gaps[lp], L - s)
                    du = gp * q - 10 if full else 2 * TICKS_BEAT - 10
                    dg = mel.get(s)
                    if dg is None: continue
                    _note(tracks['lead'], base + s * q + (int(g.get('swing8', 0) * 4 * q) if s % 4 == 2 else 0), du, _deg_pitch(root, scale, dg, lead_oct), int((88 if full else 70) * lf), 5)
                    
        if idx == 0 and (layers - prev):
            _note(tracks['fx_perc'], base, bt - 10, _pc_pitch(rpc, 72), 110 if ('clap' in layers and 'clap' not in prev) else 75, 6)
        riser = min(2, length)
        if roll_any and idx >= length - riser:
            k0 = (idx - (length - riser)) * 8
            for k, s in enumerate([int(x * L / 8) for x in range(8)]):
                j = k0 + k
                _note(tracks['fx_perc'], base + s * q, q * 2 - 10, _pc_pitch(root, 60) + scale[j % n] + 12 * (j // n), 60 + int(50 * (j + 1) / (riser * 8)), 6)

def generate_multitrack(mid_file_bytes, g, submode, bars, seed, split_drums=True):
    random.seed(seed)
    g = vary_genre(g, seed, g.get('_name'))
    bars, sections = compute_structure(bars, g.get('timeline'), seed)
    secmap = section_map(sections, bars)
    bm = plan_meter(g, bars, submode != 'faithful', seed)
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
    if submode != 'faithful': _bass_kick_composite(g, tracks, 'bassline')
    tracks = {k: v for k, v in tracks.items() if v}
    tracks = _finalize_tracks(tracks, g, seed, split_drums)
    return tracks, root, scale, headers, bars

def generate_from_scratch(g, dna, bars, seed, split_drums=True):
    random.seed(seed)
    root, scale = dna
    g = vary_genre(g, seed, g.get('_name'))
    bars, sections = compute_structure(bars, g.get('timeline'), seed)
    secmap = section_map(sections, bars)
    tracks, headers = {}, {}
    bm = plan_meter(g, bars, True, seed)
    _arrange_generative(g, root, scale, secmap, tracks, bm)
    _add_reese(g, tracks)
    drums = build_drum_events(g, secmap, bm)
    if drums: tracks['drums'] = drums
    _bass_kick_composite(g, tracks, 'bassline')
    tracks = {k: v for k, v in tracks.items() if v}
    tracks = _finalize_tracks(tracks, g, seed, split_drums)
    for _k, _v in (g.get('pan') or {}).items():
        if _k in tracks: headers[_k] = [{'type': 'control_change', 'control': 10, 'value': _v}]
    return tracks, root, scale, headers, bars

def _events_to_notes(events):
    notes = [[s, en, max(0, min(127, int(p))), max(1, min(127, int(v)))] for s, en, p, v, _ch in _pair_events(events)]
    by_pitch = {}
    for nt in notes: by_pitch.setdefault(nt[2], []).append(nt)
    cleaned_all = []
    for lst in by_pitch.values():
        lst.sort(key=lambda x: (x[0], -x[3]))
        cleaned = []
        for nt in lst:
            if cleaned and nt[0] - cleaned[-1][0] < 24: cleaned[-1][1] = max(cleaned[-1][1], nt[1]); continue
            if cleaned and cleaned[-1][1] > nt[0]: cleaned[-1][1] = nt[0]
            cleaned.append(nt)
        cleaned_all.extend(cleaned)
    cleaned_all.sort(key=lambda x: (x[0], x[2]))
    return cleaned_all

# ================= GUIDA LOGIC PRO X =================
GUIDE_TEXT = """
ACID
Sub Bass: ES2 (Sine Sub) -> Channel EQ (HPF 30Hz) -> Compressor (Sidechain)
Bassline: Retro Synth (Tube Acid Bass) -> Channel EQ -> Compressor -> Overdrive -> AutoFilter (Resonance alta)
Chords: Alchemy (Dub Chords) -> Channel EQ -> Step FX (Gating)
Pad: Alchemy (Dark Pad) -> Channel EQ -> Chorus -> Send: ChromaVerb
Arp: Retro Synth (Sync Arp) -> Channel EQ -> Stereo Delay (Ping-Pong)
Lead: Retro Synth (Saw Lead) -> Channel EQ -> Phat FX (Presence) -> Stereo Delay -> Send: ChromaVerb
FX Perc: Alchemy (White Noise Riser) -> Channel EQ -> AutoFilter
Drums: Drum Machine Designer (TR-909) -> Channel EQ -> Compressor -> Phat FX (sul Kick)
TECHNO
Sub Bass: ES2 (Sine Sub) -> Channel EQ -> Compressor
Bassline: Retro Synth (Synced Metal Bass) -> Channel EQ -> Compressor -> Phat FX (Distortion)
Chords: Alchemy (Dub Chords) -> Channel EQ -> Step FX (Gating ritmico)
Pad: Alchemy (Dark Pad) -> Channel EQ -> Send: Space Designer
Arp: Retro Synth (Sync Arp) -> Channel EQ -> Stereo Delay
Lead: Retro Synth (Saw Lead) -> Channel EQ -> Phat FX (Drive) -> Stereo Delay
FX Perc: Alchemy (Impact) -> Channel EQ
Drums: Drum Machine Designer (TR-909) -> Channel EQ -> Enveloper -> Compressor
"""
def _parse_guide(text):
    out, cur = {}, None
    for ln in text.splitlines():
        s = ln.strip()
        if not s: continue
        m = re.match(r'^\d+. ([^:]+): (.+)$', s)
        if m and cur: out[cur].append((m.group(1).strip(), m.group(2).strip()))
        elif re.match(r'^[A-Za-z0-9_&]+$', s): cur = s.lower(); out[cur] = []
    return out

GUIDE = _parse_guide(GUIDE_TEXT)
GUIDE_ROLE = {'sub_bass': 'Sub Bass', 'bassline': 'Bassline', 'bass': 'Bassline', 'reese': 'Bassline', 'chords': 'Chords', 'pad': 'Pad', 'arp': 'Arp', 'lead': 'Lead', 'fx_perc': 'FX Perc'}

def guide_entry(genre, track_key):
    role = 'Drums' if track_key in DRUM_TRACK_NAMES else GUIDE_ROLE.get(track_key)
    for r, chain in GUIDE.get(genre, []):
        if r == role: return r, chain
    return None

def guide_preset_names(genre, tracks):
    out = {}
    for k in tracks:
        e = guide_entry(genre, k)
        if e: out[k] = e[1].split(' -> ')[0]
    return out

def guide_report_block(genre, tracks):
    rows = GUIDE.get(genre)
    if not rows: return []
    lines = ["CATENA DI SEGNALE E PRESET (LOGIC PRO X) - " + GENRE_LABELS.get(genre, genre), " "]
    lines += [f"   {i}. {r}: {c}" for i, (r, c) in enumerate(rows, 1)]
    mapped = [(k, guide_entry(genre, k)) for k in tracks]
    mapped = [(k, e) for k, e in mapped if e]
    if mapped:
        lines += [" ", "   Tracce di questo MIDI -> riga della guida: "]
        lines += [f"   - {DRUM_TRACK_NAMES.get(k, k.replace(' ', ' ').title())} -> {e[0]}: {e[1].split(' -> ')[0]}" for k, e in mapped]
    return lines + [" "]

DRUM_KITS = {0: 'SoCal', 8: 'Retro Rock', 16: 'Epic Electro', 25: 'Boutique 808', 32: 'Roots'}
DRUM_KIT_INFO = {0: 'SoCal - Drum Kit Designer', 8: 'Retro Rock - Drum Kit Designer', 16: 'Epic Electro - Ultrabeat', 24: 'Boutique 808 - Drum Machine Designer', 25: 'Boutique 808 - Drum Machine Designer', 32: 'Roots - Drum Kit Designer'}
_KIT_BY_GENRE = {'disco': 0, 'funk': 0, 'armonico': 0, 'soul': 8, 'jazz': 32, 'jungle': 8, 'reggae': 32, 'trip_hop': 32, 'minimalismo_ritmico': 32, 'industrial': 16, 'hardstyle': 16, 'breakcore': 16, 'hyperpop': 16, 'dubstep': 16, 'harsh_noise': 16, 'sperimentale': 16, 'glitch': 16, 'idm': 16, 'chiptune': 16, 'drum_n_bass': 16, 'trap': 25, 'hip_hop': 25, 'future_bass': 25, 'synthpop': 25, 'vaporwave': 25, 'r&b': 25, 'reggaeton': 25, 'underground': 25}

def auto_drum_program(genre): return _KIT_BY_GENRE.get(genre, 24)

LOGIC_PATCH = {0: 'Steinway Grand Piano', 1: 'Afro-Cuban Piano', 2: 'Yamaha Grand Piano', 3: 'Before Talkies', 4: 'Classic Electric Piano', 5: '80s FM Piano', 6: 'Harpsichord', 7: 'Classic D6', 8: 'Celesta', 9: 'Glockenspiel', 10: 'Mystic Vibes', 11: 'Vibraphone', 12: 'Marimba', 13: 'Xylophone', 14: 'Tubular Bells', 15: 'Celtic Hammered Dulcimer', 17: 'Bebop Organ', 18: 'Classic Rock Organ', 19: 'Wedding Organ', 20: 'Noble Organ', 21: 'Tango Accordion', 22: 'Tango Accordion', 23: 'Tango Accordion', 24: 'Classical Acoustic Guitar', 25: 'Steel String Acoustic', 26: 'Roots Rock', 27: 'Classic Clean', 28: 'Tweed Picked Synth', 29: 'British Stack Synth Lead', 30: 'Hard Rock', 31: 'Acoustic Guitar Harmonics', 16: 'Tonewheel Organ', 32: 'Upright Studio Bass', 33: 'Fingerstyle Bass', 34: 'Picked Bass', 35: 'Fretless Bass', 36: 'Picked Bass', 37: 'Picked Bass', 38: 'Pulse Bass', 39: 'Taureg Moon Bass', 40: 'Violins 1', 41: 'Violas', 42: 'Cellos', 43: 'Basses', 44: 'Romance Strings', 45: 'Session Strings', 46: 'Harp', 47: 'Timpani', 48: 'String Ensemble', 49: 'Romance Strings', 50: 'Vintage Synth Strings', 51: 'Synth Pop Strings', 52: 'Classical Ensemble', 53: 'Church Choir', 54: 'Dream Voice', 55: 'Full Brass', 56: 'Trumpets', 57: 'Trombones', 58: 'Tuba', 59: 'Full Brass', 60: 'French Horns', 61: 'Full Brass', 62: 'Bright Synth Brass', 63: 'Classic Synth Brass', 64: 'Saxophone', 65: 'Saxophone', 66: 'Saxophone', 67: 'Saxophone', 68: 'Oboe', 69: 'English Horn', 70: 'Bassoon Solo', 71: 'Clarinet Solo', 72: 'Piccolo', 73: 'Flute Solo', 74: 'Medieval Recorder', 75: 'Peruvian Panpipes', 76: 'Mountain Flute', 77: 'Japanese Shakuhachi Flute', 78: 'Celtic Tin Whistle', 79: 'Mountain Flute', 80: 'Reverse Engineering', 81: 'The Final Lead', 82: 'Deep Organ', 83: 'Pop Brass', 84: '80s Starlight', 85: 'Dream Voice', 86: 'Power Fifths', 87: 'Soft Square Lead', 88: 'Glistening Pad', 89: 'Classic Pad', 90: 'Epic Cloud Formation', 91: 'Synthetic Choir', 92: 'Pulse Strings', 93: 'Ghost Voices', 94: 'Tidal Space', 95: 'Slow Drift', 96: 'Crystal Rain', 97: 'Distant Air', 98: 'Glass Sky', 99: 'Pipe Ambience', 100: 'Cosmonaut Space Capsule', 101: 'Fog Machine', 102: 'Backwards Metal', 103: 'Spiraling Down', 104: 'Indian Sitar', 117: 'Orchestral Kit'}

GENRE_PROGRAMS = {'techno': (39, 38, 94, 86, 80, 81, 102), 'minimal_techno': (39, 38, 94, 86, 80, 87, 101), 'minimal': (39, 38, 95, 0, 80, 87, 99), 'underground': (39, 38, 93, 86, 80, 81, 102), 'acid': (39, 38, 94, 86, 87, 81, 102), 'industrial': (39, 38, 93, 86, 86, 86, 102), 'hardstyle': (39, 38, 89, 86, 84, 81, 102), 'dub_techno': (39, 33, 95, 16, 96, 87, 99), 'deep': (39, 35, 95, 0, 96, 87, 99), 'house_90s': (39, 38, 88, 16, 80, 83, 102), 'soulful_house': (39, 33, 91, 0, 96, 87, 99), 'afro_house': (39, 36, 89, 0, 96, 87, 101), 'amapiano': (39, 39, 91, 0, 96, 87, 99), 'uk_garage': (39, 38, 91, 0, 96, 87, 102), 'trance': (39, 38, 88, 92, 84, 81, 102), 'psytrance': (39, 38, 94, 86, 80, 81, 102), 'edm_2000s': (39, 38, 89, 92, 84, 81, 102), 'elettronico': (39, 38, 89, 92, 80, 81, 102), 'synthpop': (39, 38, 89, 84, 80, 87, 96), 'synthwave': (39, 38, 88, 92, 80, 84, 96), 'commerciale_90s': (39, 38, 89, 83, 80, 87, 102), 'future_bass': (39, 38, 91, 92, 87, 81, 102), 'hyperpop': (39, 38, 91, 84, 96, 81, 102), 'vaporwave': (39, 35, 88, 0, 84, 87, 96), 'chiptune': (39, 38, 89, 87, 80, 87, 96), 'hip_hop': (39, 38, 95, 0, 96, 87, 101), 'trap': (39, 38, 93, 0, 96, 87, 102), 'r&b': (39, 35, 91, 0, 96, 87, 99), 'soul': (39, 33, 91, 0, 96, 83, 99), 'jazz': (32, 32, 48, 0, 0, 4, 99), 'funk': (39, 36, 92, 16, 80, 83, 102), 'disco': (39, 33, 92, 0, 44, 83, 96), 'space_disco': (39, 38, 92, 44, 84, 81, 96), 'reggae': (39, 33, 99, 16, 87, 83, 99), 'reggaeton': (39, 38, 93, 0, 96, 87, 102), 'trip_hop': (39, 32, 95, 0, 96, 87, 101), 'drum_n_bass': (39, 38, 94, 86, 80, 81, 102), 'jungle': (39, 38, 93, 16, 80, 87, 101), 'dubstep': (39, 38, 93, 86, 80, 86, 102), 'breakcore': (39, 38, 93, 86, 80, 86, 102), 'glitch': (39, 38, 94, 84, 96, 87, 102), 'idm': (39, 38, 94, 84, 96, 87, 96), 'ambient': (39, 35, 90, 44, 96, 85, 99), 'drone': (39, 39, 93, 90, 94, 85, 101), 'lowercase': (39, 35, 97, 97, 96, 98, 99), 'microsound': (39, 35, 97, 97, 96, 98, 99), 'onkyo': (39, 35, 97, 97, 96, 98, 101), 'noise': (39, 38, 93, 86, 102, 86, 102), 'harsh_noise': (39, 38, 93, 86, 102, 86, 102), 'musique_concrete': (39, 35, 97, 97, 96, 98, 101), 'sperimentale': (39, 35, 94, 90, 96, 98, 101), 'minimalismo_ritmico': (39, 35, 95, 0, 96, 87, 99), 'armonico': (39, 33, 91, 0, 96, 85, 99)}
_PROG_ROLES = ('sub_bass', 'bassline', 'pad', 'chords', 'arp', 'lead', 'fx_perc')
_PROG_OLD = {'bass': 38, 'arp': 80, 'sub_bass': 39, 'bassline': 38, 'pad': 89, 'chords': 0, 'lead': 81, 'fx_perc': 117, 'reese': 39}
PROG_OPTS = _ThreadOpts({'genre': True, 'match': True})
PATCH_PLUGIN = {**{n: 'Sampler' for n in (0, 1, 2, 3, 6, 8, 9, 11, 12, 13, 14, 15, 21, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 36, 37, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 52, 53, 55, 56, 57, 58, 59, 60, 61, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74)}, 4: 'Vintage Electric Piano', 5: 'ES2', 50: 'ES2', 51: 'Retro Synth', 54: 'Alchemy', 62: 'ES2', 63: 'Retro Synth', 7: 'Vintage Clav', 10: 'Sculpture', 16: 'Vintage B3 Organ', 17: 'Vintage B3 Organ', 18: 'Vintage B3 Organ', 28: 'Sculpture', 29: 'Sculpture', 38: 'ES2', 39: 'Alchemy', 75: 'Sampler', 76: 'Sculpture', 77: 'Sampler', 78: 'Sampler', 79: 'Sculpture', 80: 'Retro Synth', 81: 'ES2', 83: 'Sampler', 84: 'Retro Synth', 85: 'Alchemy', 86: 'ES2', 87: 'ES2', 88: 'ES2', 89: 'ES2', 90: 'Alchemy', 91: 'Retro Synth', 92: 'ES2', 93: 'Alchemy', 94: 'Alchemy', 95: 'ES2', 96: 'ES2', 97: 'Sculpture', 98: 'Sculpture', 99: 'Sculpture', 100: 'Sculpture', 101: 'Retro Synth', 102: 'Alchemy', 103: 'ES2', 104: 'Sampler'}
_PLUGIN_POOLS = {'sub_bass': {'Alchemy': [39], 'ES2': [38]}, 'bassline': {'Alchemy': [39], 'ES2': [38], 'Studio Bass': [33, 35, 36, 32, 34]}, 'pad': {'Alchemy': [90, 94, 93, 85], 'ES2': [88, 89, 95, 92, 50], 'Sculpture': [97, 98, 99, 100], 'Retro Synth': [91, 51], 'Vintage B3 Organ': [17], 'Studio Strings': [44, 48, 45, 52]}, 'chords': {'Alchemy': [94, 90, 93, 85], 'ES2': [92, 88, 89, 50], 'Sculpture': [97, 98, 99], 'Retro Synth': [91, 51], 'Vintage Electric Piano': [4], 'Vintage Clav': [7], 'Vintage B3 Organ': [16, 17, 18], 'Studio Strings': [44, 48, 45, 52]}, 'arp': {'Alchemy': [93, 94, 102, 85], 'Retro Synth': [80, 84], 'ES2': [96, 87, 81], 'Sculpture': [99, 98, 97, 28], 'Vintage Electric Piano': [4]}, 'lead': {'Alchemy': [85, 102, 93], 'Retro Synth': [80, 84, 63], 'ES2': [81, 87, 86, 62], 'Sculpture': [98, 97, 76, 29], 'Vintage Electric Piano': [4], 'Studio Strings': [44, 48], 'Studio Horns': [83, 55, 61, 60]}, 'fx_perc': {'Alchemy': [102, 94, 93], 'ES2': [96, 103], 'Retro Synth': [101], 'Sculpture': [99, 98, 97]}}
_ROLE_GUIDE = {'sub_bass': 'Sub Bass', 'bassline': 'Bassline', 'pad': 'Pad', 'chords': 'Chords', 'arp': 'Arp', 'lead': 'Lead', 'fx_perc': 'FX Perc'}

def _guide_plugin(genre, role):
    for r, chain in GUIDE.get(genre, []):
        if r == _ROLE_GUIDE.get(role):
            n = chain.split(' -> ')[0].split('(')[0].strip().lower()
            return {'es2': 'ES2', 'alchemy': 'Alchemy', 'retro synth': 'Retro Synth', 'sculpture': 'Sculpture', 'vintage electric piano': 'Vintage Electric Piano', 'vintage clav': 'Vintage Clav', 'vintage b3 organ': 'Vintage B3 Organ', 'studio strings': 'Studio Strings', 'studio horns': 'Studio Horns', 'studio bass': 'Studio Bass'}.get(n)
    return None

def role_program(genre, key):
    row = GENRE_PROGRAMS.get(genre) if PROG_OPTS.get('genre') else None
    if row:
        role = {'bass': 'bassline', 'reese': 'sub_bass'}.get(key, key)
        if role in _PROG_ROLES:
            prog = row[_PROG_ROLES.index(role)]
            if PROG_OPTS.get('match'):
                want = _guide_plugin(genre, role)
                pool = _PLUGIN_POOLS.get(role, {}).get(want)
                if want and pool and prog not in pool and PATCH_PLUGIN.get(prog) != want:
                    prog = pool[sum(map(ord, genre)) % len(pool)]
            return prog
    return _PROG_OLD.get(key)

# ================= MARKER DI SEZIONE + AUTOMAZIONI FILTRO (CC74) =================
import unicodedata
GENRE_LABELS = {'acid': 'Acid', 'afro_house': 'Afro House', 'amapiano': 'Amapiano', 'ambient': 'Ambient', 'armonico': 'Armonico', 'breakcore': 'Breakcore', 'chiptune': 'Chiptune', 'commerciale_90s': "Commerciale anni '90", 'deep': 'Deep House', 'disco': 'Disco', 'drone': 'Drone', 'drum_n_bass': "Drum 'n' Bass", 'dub_techno': 'Dub Techno', 'dubstep': 'Dubstep', 'edm_2000s': 'EDM anni 2000', 'elettronico': 'Elettronico', 'funk': 'Funk', 'future_bass': 'Future Bass', 'glitch': 'Glitch', 'hardstyle': 'Hardstyle / Hardcore', 'harsh_noise': 'Harsh Noise', 'hip_hop': 'Hip Hop', 'house_90s': "House anni '90", 'hyperpop': 'Hyperpop / Deconstructed Club', 'idm': 'IDM', 'industrial': 'Industrial', 'jungle': 'Jungle', 'lowercase': 'Lowercase', 'microsound': 'Microsound', 'minimal': 'Minimal', 'minimal_techno': 'Minimal Techno', 'minimalismo_ritmico': 'Minimalismo Ritmico', 'musique_concrete': 'Musique Concrète', 'noise': 'Noise', 'onkyo': 'Onkyo', 'psytrance': 'Psytrance / Goa Trance', 'r&b': 'R&B', 'reggae': 'Reggae', 'reggaeton': 'Reggaeton', 'jazz': 'Jazz', 'soul': 'Soul', 'soulful_house': 'Soulful House', 'space_disco': 'Space Disco', 'sperimentale': 'Sperimentale', 'synthpop': 'Synthpop', 'synthwave': 'Synthwave', 'techno': 'Techno', 'trance': 'Trance', 'trap': 'Trap', 'trip_hop': 'Trip Hop / Downtempo', 'uk_garage': 'UK Garage / 2-Step', 'underground': 'Underground', 'vaporwave': 'Vaporwave'}

def _ascii(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

def section_markers(sections, bm):
    out, prev = [], frozenset()
    for name, start, _length, layers in sections:
        ins, outs = sorted(layers - prev), sorted(prev - layers)
        txt = f"{name} - bar {start + 1} " + (" | + " + " + ".join(ins) if ins else " ") + (" | -" + " -".join(outs) if outs else "")
        out.append((bm[start]['start'], _ascii(txt)[:110]))
        prev = layers
    return out

_SYNTH_MIN = frozenset({'arp', 'arpl', 'lead', 'leadl', 'chords', 'chordsl', 'pad'})

def tempo_events(g, sections, bm):
    plan = g.get('tempo_plan')
    if not plan or len(plan) != len(sections): return None
    return [(bm[start]['start'], plan[i]) for i, (_n, start, _l, _ls) in enumerate(sections)]

def _tempo_line(tempo_ev):
    return "   Tempo variabile: " + " -> ".join(str(b) for _t, b in tempo_ev) + " BPM (un cambio di tempo per sezione, scritto nel MIDI)"

def build_automation(sections, bm, tracks, style=None, slow=False):
    q = TICKS_BEAT // 4
    if 'bassline' in tracks:
        maps = {'sub_bass': ({'bass', 'bassl'}, {'bassl'}), 'bassline': ({'bass', 'bassl'}, {'bassl'}), 'pad': ({'pad'}, set()), 'chords': ({'chords', 'chordsl'}, {'chordsl'}), 'arp': ({'arp', 'arpl'}, {'arpl'}), 'lead': ({'lead', 'leadl'}, {'leadl'})}
    else:
        maps = {'bass': ({'bass', 'bassl'}, {'bassl'}), 'arp': (set(_SYNTH_MIN), {'arpl', 'leadl', 'chordsl', 'pad'})}
    maps = {k: v for k, v in maps.items() if k in tracks}
    pts = {k: {} for k in maps}
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
                if roll_any and t0 + R * avg > ts: pass
                else: ramp(k, t0, t0 + R * avg, 25, target, R * 4)
            elif last[k] == 127: pts[k][t0] = target
            elif abs(target - last[k]) > 4: ramp(k, t0, t0 + min(2, length) * avg, last[k], target, min(2, length) * 4)
            last[k] = target
            if slow and 'clap' in layers and (layers & {'arp', 'lead'}) and not roll_any and length >= 16 and (active - light):
                v1 = min(127, target + 12)
                ramp(k, t0 + (R * avg if fresh else 0), tend - avg, target if fresh else max(40, target - 40), v1, max(4, length * 2)); last[k] = v1
            if roll_any:
                ramp(k, ts, tend, 25 if fresh else max(60, target - 40), 127, W * 4)
                last[k] = 127
        prev = layers
    out = {k: [(t, 74, v) for t, v in sorted(p.items())] for k, p in pts.items() if p}
    if style in ('long', 'acid', 'logdrum', 'fretless'):
        max_gap, max_glen = {'long': (3840, 360), 'acid': (240, 100), 'logdrum': (480, 180), 'fretless': (480, 120)}[style]
        for k in ('sub_bass', 'bassline', 'bass'):
            if k not in tracks: continue
            ons = sorted([e for e in tracks[k] if e['type'] == 'on'], key=lambda e: e['tick'])
            glide = []
            for a, b_ in zip(ons, ons[1:]):
                d = a['pitch'] - b_['pitch']
                if d == 0 or abs(d) > 12 or b_['tick'] - a['tick'] > max_gap or (b_['tick'] // 120 + b_['pitch']) % 5 >= 3: continue
                glen = min(b_['tick'] - a['tick'], max_glen); n_ = max(2, glen // 60)
                for i in range(n_): glide.append((b_['tick'] + i * glen // n_, 'pb', int(max(-8192, min(8191, round(d / 12 * 8191 * (1 - i / n_)))))))
                glide.append((b_['tick'] + glen, 'pb', 0))
            if glide:
                rpn = [(0, 101, 0), (0, 100, 0), (0, 6, 12), (0, 38, 0), (0, 101, 127), (0, 100, 127)]
                out[k] = rpn + sorted(out.get(k, []) + glide, key=lambda x: x[0])
    if style == 'acid' and 'bassline' in tracks:
        pk, seen_break, seen_second, outro_i = list(out.get('bassline', [])), False, False, 0
        PH = {'intro': (20, 55, 55, 65), 'groove': (55, 85, 65, 80), 'main': (85, 105, 80, 92), 'break': (95, 70, 92, 98), 'build': (None, None, 98, 118), 'second': (100, 127, 105, 122), 'outro': (110, 25, 100, 55)}
        for name_, start_, length_, layers_ in sections:
            if not (layers_ & {'bass', 'bassl'}): continue
            t0_ = bm[start_]['start']; te_ = bm[start_ + length_ - 1]['start'] + bm[start_ + length_ - 1]['L'] * q
            if layers_ & {'roll', 'rolls'}: ph = 'build'
            elif 'kick' not in layers_: ph = 'break'; seen_break = True
            elif seen_second: ph = 'outro'
            elif seen_break and 'clap' in layers_: ph = 'second'; seen_second = True
            elif 'clap' in layers_: ph = 'main'
            elif layers_ & {'bass'}: ph = 'groove'
            else: ph = 'intro'
            c0, c1, r0, r1 = PH[ph]
            if ph == 'outro':
                c0, c1, r0, r1 = ((110, 70, 100, 78), (70, 25, 78, 55), (25, 25, 55, 55))[min(outro_i, 2)]; outro_i += 1
            n_ = max(4, length_ * 2)
            if c0 is not None:
                pk = [x for x in pk if not (x[1] == 74 and t0_ <= x[0] < te_)]
                pk += [(int(t0_ + (te_ - t0_) * i / n_), 74, int(round(c0 + (c1 - c0) * i / n_))) for i in range(n_)] + [(te_ - 1, 74, c1)]
                pk += [(int(t0_ + (te_ - t0_) * i / n_), 71, int(round(r0 + (r1 - r0) * i / n_))) for i in range(n_)] + [(te_ - 1, 71, r1)]
        out['bassline'] = sorted(pk, key=lambda x: x[0])
    if style == 'wobble':
        rates = (480, 240, 120, 160)
        for k in ('bassline', 'bass'):
            if k not in tracks: continue
            pk, drop_i = list(out.get(k, [])), 0
            ons_ = [e for e in tracks[k] if e['type'] == 'on']
            for name_, start_, length_, layers_ in sections:
                if 'bass' not in layers_ or 'clap' not in layers_: continue
                t0_ = bm[start_]['start']; te_ = bm[start_ + length_ - 1]['start'] + bm[start_ + length_ - 1]['L'] * q
                per = rates[drop_i % 4]; drop_i += 1
                pk = [x for x in pk if not (x[1] == 74 and t0_ <= x[0] < te_)]
                for t_ in range(t0_, te_, 30): pk.append((t_, 74, int(70 + 50 * math.sin(2 * math.pi * (t_ - t0_) / per))))
                for e in ons_:
                    if t0_ <= e['tick'] < te_:
                        for i_ in range(6): pk.append((e['tick'] + i_ * 40, 'pb', int(4096 * (1 - i_ / 6))))
                        pk.append((e['tick'] + 240, 'pb', 0))
                out[k] = [(0, 101, 0), (0, 100, 0), (0, 6, 12), (0, 38, 0), (0, 101, 127), (0, 100, 127)] + sorted(pk, key=lambda x: x[0])
    if 'reese' in tracks:
        end = bm[-1]['start'] + bm[-1]['L'] * q
        out['reese'] = [(0, 'pb', 700)] + [(t, 74, int(75 + 35 * math.sin(2 * math.pi * t / (8 * 1920)))) for t in range(0, end, 960)]
    return out

def _show_html(html, height):
    if hasattr(st, 'iframe'): st.iframe(html, height=height)
    else: components.html(html, height=height)

def build_midi_file(tracks, bpm, mode, submode, headers=None, label=None, key_name=None, meter_plan=None, automation=None, markers=None, tempo_events=None, preset_names=None, drum_program=0, genre=None):
    headers = headers or {}
    faithful = (mode == 'multitrack' and submode == 'faithful')
    notes_by_track = {}
    for key, events in tracks.items():
        notes = _events_to_notes(events)
        if notes: notes_by_track[key] = (events[0].get('channel', 0), notes)
    mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_BEAT)
    total_end = max((nt[1] for _, notes in notes_by_track.values() for nt in notes), default=0)
    t_tempo = mido.MidiTrack()
    t_tempo.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo_events[0][1] if tempo_events else bpm), time=0))
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
    timed = [(tk, 0, 'ts', sig) for tk, sig in ts_changes[1:]] + [(tk, 1, 'mk', txt) for tk, txt in (markers or [])] + [(tk, -1, 'tp', b_) for tk, b_ in (tempo_events or [])[1:]]
    timed.sort(key=lambda x: (x[0], x[1]))
    last = 0
    for tk, _o, kind, val in timed:
        if kind == 'ts': t_tempo.append(mido.MetaMessage('time_signature', numerator=val[0], denominator=val[1], time=tk - last))
        elif kind == 'tp': t_tempo.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(val), time=tk - last))
        else: t_tempo.append(mido.MetaMessage('marker', text=val, time=tk - last))
        last = tk
    t_tempo.append(mido.MetaMessage('end_of_track', time=max(0, total_end - last)))
    mid.tracks.append(t_tempo)
    used_names = Counter()
    for key, (ch, notes) in notes_by_track.items():
        is_drums = (ch == DRUM_CH)
        header = list(headers.get(key, []))
        if not any(h['type'] == 'program_change' for h in header):
            if is_drums: pc = drum_program
            else:
                pc = None if faithful else role_program(genre, key)
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
        if preset_names and key in preset_names: name = _ascii(f"{name} - {preset_names[key]}")[:60]
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
            if cc == 'pb': ev.append((tk, -2, max(-8192, min(8191, int(val))), 0))
            else: ev.append((tk, -1, cc, val))
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
    return f"   Basso: {g.get('bass_style') or 'standard'} ({'libero sul kick' if g.get('bass_style') in BK_FREE_STYLES else 'tagliato prima di ogni kick'}) | accordi: settima {g.get('seventh', 0.35):.0%}, nona {g.get('ninth', 0.0):.0%} dei brani"

def _meter_line(meter_plan):
    if not meter_plan: return "   4/4 (tutto il brano)"
    c = Counter(m['key'] for m in meter_plan)
    if len(c) == 1: return f"   {next(iter(c))} (tutto il brano)"
    return "   Ciclo: " + " | ".join(f"{k} x{n}" for k, n in c.items()) + "  (cambi di time signature scritti nel MIDI)"

def generate_report(tracks, genre, mode, submode, bpm, bars, seed, root, scale, duration_mode, duration_seconds, original_filename, meter_plan=None, g_used=None, cc_markers=(False, False), tempo_ev=None):
    report = ["=" * 60, "MIDI FORGE UNIVERSALE - REPORT DI GENERAZIONE", "=" * 60, " ", "DATA E ORA", f"   Generato il: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", " ", "PARAMETRI GENERAZIONE", f"   File originale: {original_filename}", f"   Modalità: {mode.upper()}", f"   Sotto-modalità: {submode.upper()}", f"   Genere: {genre.upper()}", f"   Seed: {seed}", f"   BPM: {bpm}", f"   Battute: {bars}"]
    if duration_mode == "Minuti:Secondi" and duration_seconds:
        report.append(f"   Durata target: {duration_seconds // 60}:{duration_seconds % 60:02d}")
    total_q = sum(m['L'] for m in meter_plan) if meter_plan else bars * 16
    if tempo_ev:
        end_t = total_q * (TICKS_BEAT // 4)
        duration_actual = sum(((tempo_ev[i + 1][0] if i + 1 < len(tempo_ev) else end_t) - tk) / TICKS_BEAT * 60 / b_ for i, (tk, b_) in enumerate(tempo_ev))
    else:
        duration_actual = (total_q / 4 * 60) / bpm
    report.extend([f"   Durata effettiva: {int(duration_actual // 60)}:{int(duration_actual % 60):02d}", " ", "METRO", _meter_line(meter_plan), *([_tempo_line(tempo_ev)] if tempo_ev else []), " ", "STILE BASSO / ARMONIA", _style_line(g_used or GENRES[genre]), " ", "ANALISI TONALE", f"   Tonica rilevata: {NOTE_NAMES[root]}", f"   Scala: {' - '.join([NOTE_NAMES[(root + i) % 12] for i in scale])}", f"   Intervalli: {scale}", " "])
    g = g_used or GENRES[genre]
    report.extend(["PATTERN RITMICI (16 step, adattati ai gruppi del metro)", f"   Kick (GM 36):  {''.join(['#' if x else '.' for x in g['kick']])}", f"   Snare (GM 38): {''.join(['#' if x else '.' for x in g.get('snare', [0]*16)])}"])
    if 'clap' in g: report.append(f"   Clap (GM 39):  {''.join(['#' if x else '.' for x in g['clap']])}")
    report.extend([f"   Hat (GM 42):   {''.join('.' if not x else ('+' if x == 3 else '#') for x in g['hat'])}  (+ = ghost)", f"   Bass:          {''.join(['#' if x else '.' for x in g['bass']])}", f"   Ghost snare: {''.join(['#' if x else '.' for x in g.get('ghost', [0]*16)])}", f"   Swing: {g['swing'] * 100:.0f}%", f"   Densità Arp: {g['arp_density'] * 100:.0f}%", " ", "STRUTTURA DEL GENERE (ingressi/uscite per strati)", *_structure_report(bars, g.get('timeline'), seed), " ", "TRACCE OUTPUT"])
    track_idx = 1
    for track_key in tracks.keys():
        if track_key in DRUM_TRACK_NAMES: report.append(f"   {track_idx}. {DRUM_TRACK_NAMES[track_key]} (Canale 10 - GM Drum Map)")
        elif track_key.startswith('instrument'): report.append(f"   {track_idx}. {track_key} (Canale melodico)")
        else: report.append(f"   {track_idx}. {track_key.replace('_', ' ').title()} (Canale melodico)")
        track_idx += 1
    report.extend([" ", "STATISTICHE MIDI", f"   Note totali generate: {sum(1 for events in tracks.values() for e in events if e['type'] == 'on')}", f"   Tracce MIDI: {len(tracks) + 1}", " ", *guide_report_block(genre, tracks), "NOTE PER LOGIC PRO", "   - Apri con File > Apri (non Importa): solo cosi' Logic carica anche marker, cambi di tempo e di metro; se importi in un progetto esistente rispondi Si' a 'importa informazioni di tempo', altrimenti le battute non coincidono", "   - Intro e outro seguono la timeline del genere (di solito pochi strati, per il mix DJ)", "   - Ogni traccia ha nome e program change al tick 0", *(["   - Automazioni CC74 (filtro): mappa CC74 sul cutoff del synth di ogni traccia; gli strati che entrano aprono il filtro in 4 battute, il build lo apre fino in fondo"] if cc_markers[0] else []), *(["   - Marker di sezione nel file: in Logic li trovi nella Marker List (Navigate > Open Marker List) e sulla timeline, con gli strati che entrano"] if cc_markers[1] else []), *(["   - Transizioni: crash (nota 49) e reverse cymbal (nota 119) sono nella traccia Crash / FX; se il tuo drum kit non mappa la 119 sostituiscila con un riser. Prima del drop, nei generi forti, c'e' un beat di pausa"] if any(e.get('pitch') in (49, 119) for k in ('drum_fx', 'drums') for e in tracks.get(k, [])) else []), "   - Batteria su canale 10: assegna Drum Kit Designer se necessario", " ", "=" * 60, "Generato con MIDI Forge Universale | 100% Free & Open Source", "=" * 60])
    return "\n".join(report)

def render_midi_player(tracks, bpm):
    all_notes_with_dur = []
    for events in tracks.values():
        all_notes_with_dur.extend(_compute_note_durations(events))
    notes_json = json.dumps([{'tick': n['tick'], 'dur': n['dur'], 'pitch': n['pitch'], 'vel': n['vel'], 'channel': n['channel']} for n in all_notes_with_dur])
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
                                    else if (note.pitch === {GM_HAT_CLOSED} || note.pitch === {GM_HAT_OPEN} || note.pitch === {GM_RIDE} || note.pitch === 44) synths[{DRUM_CH}].hat.triggerAttackRelease('C3', durInSeconds, time, note.vel / 127);
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
st.markdown("Trasforma qualsiasi file MIDI o Audio in 50+ generi musicali. Ogni genere ha la sua struttura a strati, con ingressi e uscite graduali (intro DJ, groove, main, breakdown, outro)")

col1, col2 = st.columns([1, 1])
with col1:
    source = st.radio("Sorgente", ["Da un MIDI caricato", "Da un file Audio (WAV/MP3) 🎵", "Da zero (senza MIDI)"], horizontal=True, key='source')
    scratch = source.startswith("Da zero")
    audio_mode = source.startswith("Da un file Audio")
    
    key_choice = "Random"
    scale_choice = "Random"
    uploaded_file = None
    audio_file = None

    if scratch:
        key_choice = st.selectbox("Tonalità", ["Random"] + NOTE_NAMES, key='key_choice')
        scale_choice = st.selectbox("Scala", ["Random"] + list(SCALES.keys()), key='scale_choice', help="Random: maggiore o minore in base al genere (dati Lakh dove disponibili)")
    elif audio_mode:
        if not BASIC_PITCH_AVAILABLE:
            st.warning("⚠️ **Modulo Audio-to-MIDI non disponibile.** Installa le dipendenze: `pip install basic-pitch onnxruntime`")
        else:
            audio_file = st.file_uploader("Carica il tuo file Audio (.wav, .mp3, .flac)", type=["wav", "mp3", "flac"])
    else:
        uploaded_file = st.file_uploader("Carica il tuo file MIDI (.mid o .midi)", type=["mid", "midi"])

    mode = st.selectbox("Modalità Principale", ["minimal", "multitrack"], format_func=lambda x: {"minimal": "Minimal (3 tracce)", "multitrack": "Multitraccia (7+ tracce)"}[x], key='mode')
    if mode == "minimal":
        submode = st.selectbox("Sotto-modalità", ["extract", "generate"], format_func=lambda x: {"extract": "Remix (riarrangia le note originali)", "generate": "Nuovo tema (dalle note originali)"}[x], key='submode_minimal')
    else:
        submode = st.selectbox("Sotto-modalità", ["faithful", "generative"], format_func=lambda x: {"faithful": "Faithful (fedele all'originale)", "generative": "Generative (solo tonalità, da zero)"}[x], key='submode_multitrack')
    
    split_drums = st.checkbox("Batteria su tracce separate (Kick / Snare / Hat / Clap)", value=True) if mode == "multitrack" else False
    auto_cc = st.checkbox("Automazioni filtro (CC74), glide e movimento del basso", value=True)
    add_markers = st.checkbox("Marker di sezione nel MIDI", value=True)
    use_trans = st.checkbox("Transizioni (crash, reverse, pausa prima del drop, fill)", value=True)
    rev_note = st.selectbox("Nota del reverse cymbal", [119, 57, None], format_func=lambda n: {119: "119 - Reverse Cymbal (Roland GS)", 57: "57 - Crash 2 (GM)", None: "Nessuno"}[n]) if use_trans else GM_REVERSE
    use_human = st.checkbox("Humanize (micro-timing e velocity nei generi organici)", value=True)
    coherent_mode = st.checkbox("🎵 Modalità Melodia Coerente (Stile Notebin: motivi ritmici persistenti e risoluzione armonica rigorosa)", value=True, help="Forza i tempi forti sulle note dell'accordo e ripete pattern ritmici per creare frasi musicali riconoscibili.")
    
    drum_kit_choice = st.selectbox("Kit batteria (program change)", ["Auto per genere"] + [f"{k} - {v}" for k, v in DRUM_KITS.items()], help="Logic carica il kit corrispondente al program GM della traccia drum")
    PROG_OPTS['drum_override'] = None if drum_kit_choice == 'Auto per genere' else int(drum_kit_choice.split(' - ')[0])
    use_genre_programs = st.checkbox("Strumenti Logic diversi per genere (program GM scelti tra le patch verificate)", value=True)
    PROG_OPTS['genre'] = use_genre_programs
    PROG_OPTS['match'] = st.checkbox("Abbina il plug-in della guida (ES2, Alchemy, Retro Synth, Sculpture) quando esiste una patch adatta", value=True)
    use_preset_names = st.checkbox("Nome traccia con il preset della guida Logic (es. 'Bass - Retro Synth (Deep Bass)')", value=False)

with col2:
    with st.expander("Timeline personalizzate (JSON)"):
        _up = st.file_uploader("Carica timeline modificate (.json)", type=["json"], key="tl_json")
        if _up is not None:
            try: st.success(f"Timeline applicate a {apply_timelines(json.loads(_up.getvalue().decode('utf-8')))} generi")
            except Exception as _e: st.error(f"JSON non valido: {_e}")
        st.download_button("Scarica le timeline attuali (JSON)", data=timelines_to_json(), file_name="midi_forge_timelines.json", mime="application/json")
        if TIMELINE_FILE_MSG: st.caption(TIMELINE_FILE_MSG)
        st.caption("Formato: { 'deep': [['Intro DJ', 16, 'kick hat pad'], ...]}. Strati: " + " ".join(LAYER_ORDER) + ". Un file midi_forge_timelines.json accanto allo script viene caricato in automatico.")

    genre_list = sorted(GENRES.keys(), key=lambda k: _ascii(GENRE_LABELS.get(k, k)).lower())
    st.session_state.setdefault('genre', 'techno')
    genre = st.selectbox("Genere Musicale", genre_list, format_func=lambda k: GENRE_LABELS.get(k, k), key='genre')
    g_defaults = GENRES[genre]
    st.caption('Struttura tipica (' + str(g_defaults['bars_default']) + ' battute): ' + _structure_line(g_defaults['bars_default'], g_defaults.get('timeline')))
    
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
            with col_min: minutes = st.number_input("Minuti", min_value=0, max_value=30, value=3)
            with col_sec: seconds = st.number_input("Secondi", min_value=0, max_value=59, value=0)
            duration_seconds = (minutes * 60) + seconds
            bars = None

    st.session_state.setdefault('seed', 42)
    seed = st.number_input("Seed", min_value=1, max_value=99999, key='seed', help="Stesso seed = stesso brano (utile per ritrovarne uno). Per averne uno diverso usa il pulsante Rigenera.")

st.markdown("---")

def _regen():
    st.session_state['seed'] = random.SystemRandom().randint(1, 99999)
    st.session_state['_regen_run'] = True

def _fav_id(e):
    return (e.get('genre'), e.get('mode'), e.get('submode'), e.get('seed'), e.get('key_choice'), e.get('scale_choice'), e.get('source'))

def _fav_path():
    try: return Path(__file__).with_name('midi_forge_favorites.json')
    except NameError: return None

def _fav_load():
    p = _fav_path()
    try:
        if p and p.exists(): return [x for x in json.loads(p.read_text(encoding='utf-8')) if isinstance(x, dict) and 'seed' in x and 'genre' in x]
    except Exception: pass
    return []

def _fav_save(favs):
    p = _fav_path()
    try:
        if p and p.exists(): p.write_text(json.dumps(favs, ensure_ascii=False, indent=1), encoding='utf-8')
    except Exception: pass

def _fav_add(e):
    if not e: return
    favs = [x for x in st.session_state.get('favorites', []) if _fav_id(x) != _fav_id(e)]
    favs.insert(0, dict(e)); st.session_state['favorites'] = favs[:100]; _fav_save(st.session_state['favorites'])

def _fav_del(i):
    favs = list(st.session_state.get('favorites', []))
    if 0 <= i < len(favs): favs.pop(i)
    st.session_state['favorites'] = favs; _fav_save(favs)

def _fav_restore(e):
    for k_ui in ('source', 'mode', 'genre', 'seed', 'key_choice', 'scale_choice'):
        if e.get(k_ui) is not None: st.session_state[k_ui] = e[k_ui]
    if e.get('submode'): st.session_state['submode_minimal' if e.get('mode') == 'minimal' else 'submode_multitrack'] = e['submode']
    st.session_state['_regen_run'] = True

def _preset_label(e):
    extra = f" - {e['key_choice']} {e['scale_choice']}" if e.get('key_choice') not in (None, 'Random') else ''
    return f"{GENRE_LABELS.get(e['genre'], e['genre'])} - seed {e['seed']} - {e.get('mode')}/{e.get('submode')}{extra}"

_bc1, _bc2 = st.columns([3, 1])
_gen_clicked = _bc1.button("Genera MIDI", type="primary", use_container_width=True)
_bc2.button("Rigenera 🎲", use_container_width=True, on_click=_regen, help="Brano diverso: sceglie un nuovo seed e rigenera subito con le stesse impostazioni")
_regen_flag = st.session_state.pop('_regen_run', False)

if _gen_clicked or _regen_flag:
    if not scratch and not audio_mode and not uploaded_file:
        st.error("Carica prima un file MIDI o Audio!")
    elif audio_mode and not audio_file:
        st.error("Carica prima un file Audio!")
    else:
        with st.spinner("Generazione in corso..."):
            try:
                if scratch:
                    rng = random.Random(seed)
                    s_root = rng.randrange(12) if key_choice == "Random" else NOTE_NAMES.index(key_choice)
                    s_name = random_scale_for_genre(genre, rng) if scale_choice == "Random" else scale_choice
                    dna, file_bytes, notes_data = (s_root, SCALES[s_name]), None, []
                    src_name = f"da zero ({NOTE_NAMES[s_root]} {s_name})"
                elif audio_mode:
                    with st.spinner("🤖 Trascrizione Audio-to-MIDI in corso (può richiedere alcuni secondi)..."):
                        try:
                            estimated_bpm = _default_bpm(genre, g_defaults, seed) if use_default_bpm else bpm
                            notes_data = audio_to_midi_notes(audio_file.getvalue(), bpm=estimated_bpm)
                            src_name = audio_file.name
                            dna = None
                            if not notes_data:
                                st.error("Nessuna nota melodica rilevata nell'audio. Prova con un file più nitido o con strumenti monofonici.")
                                st.stop()
                            st.success(f"Trascrizione completata! Rilevate {len(notes_data)} note.")
                        except Exception as e:
                            st.error(f"Errore nella trascrizione audio: {e}")
                            st.stop()
                else:
                    dna = None
                    file_bytes = io.BytesIO(uploaded_file.getvalue())
                    notes_data = extract_notes(file_bytes)
                    src_name = uploaded_file.name

                if not scratch and not audio_mode and not notes_data:
                    st.error("Il file MIDI non contiene note melodiche (i canali batteria vengono ignorati).")
                else:
                    final_bpm = _default_bpm(genre, g_defaults, seed) if use_default_bpm else bpm
                    if duration_mode == "Minuti:Secondi" and duration_seconds:
                        odd_ok = uses_odd_meter(mode, submode, bool(notes_data))
                        _plan = g_defaults.get('tempo_plan') if use_default_bpm else None
                        if _plan and len(_plan) == len(g_defaults['timeline']):
                            raw_bars = g_defaults['bars_default'] * duration_seconds / sum(b * 240 / bp for (n, b, l), bp in zip(g_defaults['timeline'], _plan))
                        else:
                            raw_bars = (duration_seconds * final_bpm) / 60 * 4 / avg_bar_sixteenths(g_defaults, odd_ok)
                        _u = timeline_unit(g_defaults['timeline'])
                        final_bars = int(round(raw_bars / _u) * _u)
                        final_bars = max(min_bars(g_defaults), final_bars)
                        st.info(f"Durata calcolata: {final_bars} battute (per coprire ~{duration_seconds} secondi a {final_bpm} BPM)")
                    else:
                        final_bars = g_defaults['bars_default'] if use_default_bars else bars
                        _u = timeline_unit(g_defaults['timeline'])
                        norm_bars = max(min_bars(g_defaults), (int(final_bars) // _u) * _u)
                        if norm_bars != final_bars:
                            st.info(f"Battute allineate alla struttura del genere: {norm_bars}")
                            final_bars = norm_bars

                    g_run['coherent'] = coherent_mode
                    
                    if mode == "minimal":
                        tracks, root, scale = generate_minimal(notes_data, dict(g_run, transitions=use_trans, humanize=use_human, reverse_note=rev_note), submode, final_bars, seed, dna=dna)
                        headers = {}
                    else:
                        requested_bars = final_bars
                        if scratch or audio_mode:
                            tracks, root, scale, headers, final_bars = generate_from_scratch(dict(g_run, transitions=use_trans, humanize=use_human, reverse_note=rev_note), dna or extract_dna(notes_data), final_bars, seed, split_drums)
                        else:
                            file_bytes.seek(0)
                            tracks, root, scale, headers, final_bars = generate_multitrack(file_bytes, dict(g_run, transitions=use_trans, humanize=use_human, reverse_note=rev_note), submode, final_bars, seed, split_drums)
                        if final_bars != requested_bars:
                            st.info(f"Durata allineata: {final_bars} battute (richieste: {requested_bars})")
                    
                    label = f"{genre} - {mode}/{submode}"
                    meter_plan = plan_meter(g_run, final_bars, uses_odd_meter(mode, submode, bool(notes_data)), seed)
                    _, sections_now = compute_structure(final_bars, g_run.get('timeline'), seed)
                    use_cc = auto_cc and not (mode == 'multitrack' and submode == 'faithful')
                    automation = build_automation(sections_now, meter_plan, tracks, g_defaults.get('bass_style'), slow=bool(g_defaults.get('filter_slow'))) if use_cc else None
                    markers = section_markers(sections_now, meter_plan) if add_markers else None
                    tempo_ev = tempo_events(g_run, sections_now, meter_plan) if use_default_bpm else None
                    midi_buffer = build_midi_file(tracks, final_bpm, mode, submode, headers, label=label, key_name=_compute_key_signature(root, scale), meter_plan=meter_plan, automation=automation, markers=markers, tempo_events=tempo_ev, preset_names=guide_preset_names(genre, tracks) if use_preset_names else None, drum_program=auto_drum_program(genre) if drum_kit_choice == 'Auto per genere' else int(drum_kit_choice.split(' - ')[0]), genre=genre)
                    report_text = generate_report(tracks, genre, mode, submode, final_bpm, final_bars, seed, root, scale, duration_mode, duration_seconds, src_name, meter_plan, vary_genre(g_run, seed, genre), (bool(use_cc), bool(add_markers)), tempo_ev)
                    _preset = {'genre': genre, 'mode': mode, 'submode': submode, 'seed': int(seed), 'source': source, 'key_choice': key_choice, 'scale_choice': scale_choice, 'bpm': final_bpm}
                    st.session_state.generated = {
                        'tracks': tracks, 'root': root, 'scale': scale, 'headers': headers,
                        'bars': final_bars, 'bpm': final_bpm, 'midi_bytes': midi_buffer.getvalue(),
                        'report_text': report_text, 'label': label, 'mode': mode,
                        'submode': submode, 'genre': genre, 'duration_mode': duration_mode,
                        'duration_seconds': duration_seconds, 'original_filename': src_name, 'seed': seed, 'preset': _preset
                    }
                    st.session_state['seed_history'] = ([_preset] + [x for x in st.session_state.get('seed_history', []) if _fav_id(x) != _fav_id(_preset)])[:10]
                    if tempo_ev or any(m_['key'] != '4/4' for m_ in meter_plan):
                        st.info("Questo brano ha cambi di metro o di tempo: in Logic aprilo con File > Apri (Cmd+O). Se lo importi in un progetto esistente, rispondi Si' a 'importa informazioni di tempo', altrimenti le battute non coincidono.")
                    st.success(f"Completato! (Tonica: {NOTE_NAMES[root]}, BPM: " + (f"variabile {min(b_ for _t, b_ in tempo_ev)}-{max(b_ for _t, b_ in tempo_ev)}" if tempo_ev else str(final_bpm)) + f", Seed: {seed})")
            except Exception as e:
                st.error(f"Errore: {e}")
                with st.expander("Dettagli tecnici"):
                    st.exception(e)

g = st.session_state.generated
if g and g.get('midi_bytes') is not None and g.get('report_text'):
    st.markdown("### Anteprima")
    render_midi_player(g['tracks'], g['bpm'])
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(label="Scarica MIDI", data=g['midi_bytes'], file_name=f"midi_forge_{g['genre']}_{g['mode']}_{g['submode']}_seed{g.get('seed', '')}.mid", mime="audio/midi", use_container_width=True)
    with col_dl2:
        st.download_button(label="Scarica Report TXT", data=g['report_text'].encode('utf-8'), file_name=f"report_{g['genre']}_{g['mode']}_{g['submode']}_seed{g.get('seed', '')}.txt", mime="text/plain", use_container_width=True)
    if g.get('preset'):
        st.button("⭐ Mi piace (salva nei preferiti)", key="fav_add", on_click=_fav_add, args=(g['preset'],), use_container_width=True)
    with st.expander("Visualizza Report"):
        st.code(g['report_text'], language=None)
else:
    st.info("Carica un MIDI/Audio e clicca 'Genera' per iniziare.")

if 'favorites' not in st.session_state: st.session_state['favorites'] = _fav_load()
with st.expander(f"Preferiti ⭐ ({len(st.session_state['favorites'])})"):
    st.caption("Ogni preferito ricorda genere, modalità, tonalità, scala e seed: un clic e ritrovi lo stesso brano. Restano finché l'app è aperta: per conservarli scarica il JSON e ricaricalo la volta dopo. In locale, se accanto allo script crei un file midi_forge_favorites.json con dentro [], si salvano da soli.")
    fv = st.session_state['favorites']
    for i, e in enumerate(fv):
        c1, c2 = st.columns([8, 1])
        c1.button("⭐ " + _preset_label(e), key=f"fav_{i}", on_click=_fav_restore, args=(e,), use_container_width=True)
        c2.button("🗑", key=f"favdel_{i}", on_click=_fav_del, args=(i,))
    if fv: st.download_button("Scarica i preferiti (JSON)", data=json.dumps(fv, ensure_ascii=False, indent=1), file_name="midi_forge_favorites.json", mime="application/json")
    _fu = st.file_uploader("Carica preferiti (.json)", type=["json"], key="fav_json")
    if _fu is not None and st.session_state.get('_fav_imported') != (_fu.name, _fu.size):
        try:
            for x in reversed([x for x in json.loads(_fu.getvalue().decode('utf-8')) if isinstance(x, dict) and 'seed' in x and 'genre' in x]): _fav_add(x)
            st.session_state['_fav_imported'] = (_fu.name, _fu.size); st.rerun()
        except Exception as e:
            st.error(f"JSON dei preferiti non valido: {e}")

if st.session_state.get('seed_history'):
    with st.expander("Cronologia (ultimi brani generati)"):
        for i, h in enumerate(st.session_state['seed_history']):
            st.button(_preset_label(h), key=f"hist_{i}", on_click=_fav_restore, args=(h,), use_container_width=True)

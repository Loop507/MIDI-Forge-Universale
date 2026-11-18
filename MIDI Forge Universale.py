import streamlit as st
import streamlit.components.v1 as components
import mido
import bisect
import itertools
import math
import random as _stdlib_random
import threading
import zlib


class _ThreadRandom:
    """Generatore casuale per thread: ogni sessione (thread) ha il suo flusso, quindi due utenti che generano nello stesso momento non si disturbano.
    Stessa sequenza di random.seed(seed) seguito da random.*: i brani per un seed non cambiano."""
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
    """Opzioni modificate dall'interfaccia (kit di batteria, programmi): una copia per thread, partendo dai valori predefiniti."""

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
import io
import json
import re
from pathlib import Path
from datetime import datetime
from collections import Counter

# Tentativo di importazione librosa per l'analisi audio facoltativa
try:
    import librosa
    import numpy as np
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

# ================= CONFIGURAZIONE PAGINA =================
st.set_page_config(page_title="MIDI Forge Universale", page_icon="🎛️", layout="wide")

# ================= DATABASE DEI GENERI =================
GENRES = {
    'acid': {'bpm_default': 126, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,1, 0,1,0,1, 1,0,1,0, 1,1,0,1], 'arp_density': 0.85, 'swing': 0.0},
    'afro_house': {'bpm_default': 122, 'bars_default': 192, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.08},
    'amapiano': {'bpm_default': 112, 'bars_default': 192, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [0,0,1,0, 0,1,1,0, 0,0,1,0, 0,1,0,0], 'ghost': [0]*16, 'arp_density': 0.25, 'swing': 0.16},
    'ambient': {'bpm_default': 80, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.15, 'swing': 0.0},
    'armonico': {'bpm_default': 100, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.7, 'swing': 0.1},
    'breakcore': {'bpm_default': 200, 'bars_default': 52, 'kick': [1,0,0,1, 0,1,0,0, 1,0,1,0, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,1,0,0, 1,0,0,1], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,0, 0,1,0,1], 'arp_density': 0.8, 'swing': 0.05, 'meter': ['7/8', '7/8', '4/4', '13/8']},
    'chiptune': {'bpm_default': 120, 'bars_default': 48, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.8, 'swing': 0.0, 'arp_sub': 2},
    'commerciale_90s': {'bpm_default': 120, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'arp_density': 0.6, 'swing': 0.08},
    'deep': {'bpm_default': 124, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,1], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.15, 'open_pad': True},
    'disco': {'bpm_default': 122, 'bars_default': 76, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.2},
    'drone': {'bpm_default': 70, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.05, 'swing': 0.0},
    'drum_n_bass': {'bpm_default': 174, 'bars_default': 116, 'kick': [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,1, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.7, 'swing': 0.0},
    'dub_techno': {'bpm_default': 128, 'bars_default': 156, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0},
    'dubstep': {'bpm_default': 140, 'bars_default': 144, 'kick': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.25, 'swing': 0.0, 'roll32': True},
    'edm_2000s': {'bpm_default': 128, 'bars_default': 100, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.85, 'swing': 0.0},
    'elettronico': {'bpm_default': 130, 'bars_default': 84, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.75, 'swing': 0.0},
    'funk': {'bpm_default': 112, 'bars_default': 56, 'kick': [1,0,0,1, 0,0,0,0, 1,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [2,1,1,1, 2,1,1,1, 2,1,1,1, 2,1,1,1], 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,1,0,0], 'ghost': [0,1,1,0, 0,1,0,1, 0,1,0,1, 0,1,1,1], 'arp_density': 0.6, 'swing': 0.05},
    'future_bass': {'bpm_default': 150, 'bars_default': 80, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.5, 'swing': 0.0, 'chord_off': 2, 'hat_triplet': True, 'roll32': True},
    'glitch': {'bpm_default': 128, 'bars_default': 60, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,1, 0,0,0,0, 1,0,0,0], 'arp_density': 0.95, 'swing': 0.1},
    'hardstyle': {'bpm_default': 150, 'bars_default': 112, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.5, 'swing': 0.0, 'lead_triplet': True},
    'harsh_noise': {'bpm_default': 100, 'bars_default': 68, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 1.0, 'swing': 0.0, 'meter': ['7/8', '9/8', '4/4']},
    'hip_hop': {'bpm_default': 92, 'bars_default': 76, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.2, 'lazy': 0.12},
    'house_90s': {'bpm_default': 122, 'bars_default': 112, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,2,0, 0,0,2,0, 0,0,2,0, 0,0,2,0], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.05},
    'hyperpop': {'bpm_default': 140, 'bars_default': 56, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,1,1,1, 1,0,1,1, 1,1,1,0, 1,1,1,1], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.0, 'meter_sections': ['4/4', '4/4', '7/8', '3/4', '4/4', '4/4'], 'tempo_plan': [70, 140, 94, 120, 170, 70], 'hat_sub': True},
    'idm': {'bpm_default': 135, 'bars_default': 72, 'kick': [1,0,0,1, 0,1,0,1, 0,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 1,0,0,1, 0,0,1,0, 1,0,1,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.85, 'swing': 0.1},
    'industrial': {'bpm_default': 135, 'bars_default': 76, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.7, 'swing': 0.0},
    'jungle': {'bpm_default': 165, 'bars_default': 144, 'kick': [1,0,0,0, 0,0,1,0, 0,0,1,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [0,1,1,1, 0,1,1,1, 0,1,1,1, 0,1,1,1], 'ghost': [0,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'arp_density': 0.2, 'swing': 0.15, 'chord_off': 2},
    'lowercase': {'bpm_default': 104, 'bars_default': 116, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.05, 'swing': 0.0, 'meter': ['17/8']},
    'microsound': {'bpm_default': 90, 'bars_default': 92, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.1, 'swing': 0.0},
    'minimal': {'bpm_default': 126, 'bars_default': 68, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.3, 'swing': 0.0},
    'minimal_techno': {'bpm_default': 130, 'bars_default': 92, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,1], 'arp_density': 0.5, 'swing': 0.0},
    'minimalismo_ritmico': {'bpm_default': 115, 'bars_default': 92, 'kick': [1,0,0,1, 0,1,0,0, 1,0,0,1, 0,0,1,0], 'snare': [0,0,1,0, 0,0,0,1, 0,1,0,0, 0,0,0,1], 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], 'arp_density': 0.6, 'swing': 0.05, 'meter': ['11/8', '11/8', '15/8', '15/8']},
    'musique_concrete': {'bpm_default': 90, 'bars_default': 80, 'kick': [0]*16, 'snare': [0]*16, 'clap': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'ghost': [0]*16, 'arp_density': 0.2, 'swing': 0.0, 'meter': ['5/4', '7/8', '11/8', '3/4'], 'tempo_plan': [60, 72, 58, 90, 60], 'free_time': 240},
    'noise': {'bpm_default': 120, 'bars_default': 76, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [1]*16, 'arp_density': 0.9, 'swing': 0.0, 'meter': ['29/16', '4/4']},
    'onkyo': {'bpm_default': 50, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.

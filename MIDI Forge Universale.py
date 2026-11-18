"""
MIDI Forge Universale - Versione Integrata con Audio & Remix (Blokco Unico)
"""
from __future__ import annotations

import io
import math
import random as _stdlib_random
import threading
import zlib
from datetime import datetime
from pathlib import Path
import re
import json
from collections import Counter

import mido
import streamlit as st
import streamlit.components.v1 as components

# Tentativo di importazione librosa per l'analisi audio facoltativa
try:
  import librosa
  import numpy as np
  HAS_LIBROSA = True
except ImportError:
  HAS_LIBROSA = False


class _ThreadRandom:
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

# ================= DATABASE DEI GENERI (I tuoi 54 stili) =================
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
    'onkyo': {'bpm_default': 50, 'bars_default': 124, 'kick': [0]*16, 'snare': [0]*16, 'hat': [0]*16, 'bass': [0]*16, 'arp_density': 0.02, 'swing': 0.0},
    'psytrance': {'bpm_default': 145, 'bars_default': 224, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0]*16, 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [0,1,1,1, 0,1,1,1, 0,1,1,1, 0,1,1,1], 'ghost': [0]*16, 'arp_density': 0.8, 'swing': 0.0},
    'r&b': {'bpm_default': 95, 'bars_default': 76, 'kick': [1,0,0,0, 0,0,1,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,0], 'arp_density': 0.55, 'swing': 0.2, 'lazy': 0.12},
    'reggae': {'bpm_default': 76, 'bars_default': 68, 'kick': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0]*16, 'hat': [3,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,1, 1,0,0,0, 1,0,0,1, 1,0,0,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.03, 'lazy': 0.1, 'chord_off': 2, 'snare_note': 37},
    'reggaeton': {'bpm_default': 95, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,1, 0,0,1,0, 0,0,0,1, 0,0,1,0], 'clap': [0]*16, 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.5, 'swing': 0.0},
    'jazz': {'bpm_default': 140, 'bars_default': 80, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0]*16, 'hat': [1,0,0,0, 1,0,2,0, 1,0,0,0, 1,0,2,0], 'bass': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'ghost': [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0], 'arp_density': 0.3, 'swing': 0.0, 'lazy': 0.05, 'chord_off': 0, 'hat_note': 51, 'kick_scale': 0.45, 'pedal_hat': True},
    'soul': {'bpm_default': 95, 'bars_default': 60, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,1,0], 'ghost': [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0], 'arp_density': 0.6, 'swing': 0.25, 'lazy': 0.08, 'chord_off': 0},
    'soulful_house': {'bpm_default': 123, 'bars_default': 128, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0]*16, 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,3,2,3, 1,3,2,3, 1,3,2,3, 1,3,2,3], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.15},
    'space_disco': {'bpm_default': 120, 'bars_default': 128, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'ghost': [0]*16, 'arp_density': 0.6, 'swing': 0.02},
    'sperimentale': {'bpm_default': 100, 'bars_default': 72, 'kick': [1,0,0,0, 0,0,0,1, 0,1,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,1,0,0, 0,0,0,1, 0,0,0,0], 'hat': [0,1,0,0, 1,0,0,1, 0,0,1,0, 1,0,0,0], 'bass': [1,0,0,0, 0,0,1,0, 0,0,0,0, 1,0,0,1], 'arp_density': 0.7, 'swing': 0.1, 'meter': ['5/16', '7/16', '4/4']},
    'synthpop': {'bpm_default': 120, 'bars_default': 60, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'bass': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'arp_density': 0.75, 'swing': 0.0},
    'synthwave': {'bpm_default': 90, 'bars_default': 80, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0], 'bass': [1]*16, 'ghost': [0]*16, 'arp_density': 0.5, 'swing': 0.02},
    'techno': {'bpm_default': 132, 'bars_default': 148, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [0,1,1,1, 0,1,1,1, 0,1,1,1, 0,1,1,1], 'arp_density': 0.75, 'swing': 0.0},
    'trance': {'bpm_default': 140, 'bars_default': 148, 'kick': [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'hat': [1,1,2,1, 1,1,2,1, 1,1,2,1, 1,1,2,1], 'bass': [0,0,1,0]*40, 'arp_density': 0.9, 'swing': 0.0},
    'trap': {'bpm_default': 140, 'bars_default': 68, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'hat': [1]*16, 'bass': [1,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0], 'arp_density': 0.4, 'swing': 0.0},
    'trip_hop': {'bpm_default': 80, 'bars_default': 88, 'kick': [1,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,0,3,0, 1,0,3,0, 1,0,3,0, 1,0,3,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0,0,1,0, 0,0,0,0, 0,0,1,0, 0,0,1,0], 'arp_density': 0.3, 'swing': 0.2, 'lazy': 0.12},
    'uk_garage': {'bpm_default': 132, 'bars_default': 88, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [1,3,1,3, 1,3,1,3, 1,3,1,3, 1,3,1,3], 'bass': [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0], 'ghost': [0]*16, 'arp_density': 0.4, 'swing': 0.15},
    'underground': {'bpm_default': 135, 'bars_default': 84, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'clap': [0]*16, 'hat': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'bass': [1,0,0,1, 0,0,1,0, 1,0,0,1, 0,0,1,0], 'arp_density': 0.65, 'swing': 0.1, 'snare_shift': True},
    'vaporwave': {'bpm_default': 70, 'bars_default': 64, 'kick': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'snare': [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0], 'clap': [0]*16, 'hat': [3,0,3,0, 3,0,3,0, 3,0,3,0, 3,0,3,0], 'bass': [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0], 'ghost': [0]*16, 'arp_density': 0.3, 'swing': 0.2, 'lazy': 0.1},
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
SCALES = {'Minore naturale': [0,2,3,5,7,8,10], 'Maggiore': [0,2,4,5,7,9,11], 'Dorico': [0,2,3,5,7,9,10], 'Frigio': [0,1,3,5,7,8,10],
          'Misolidio': [0,2,4,5,7,9,10], 'Minore armonica': [0,2,3,5,7,8,11], 'Pentatonica minore': [0,3,5,7,10]}
TICKS_BEAT = 480

# ================= MOTORE AUDIO & TRASCRIZIONE (Stile Muscriptor) =================

def analyze_and_transcribe_audio(audio_bytes: bytes, quantize_grid: int = 16, min_note_duration_steps: int = 1) -> dict[str, Any]:
    if not HAS_LIBROSA:
        raise RuntimeError("La libreria 'librosa' non è installata nell'ambiente Python. Installa librosa e soundfile per abilitare l'analisi audio.")
    
    audio_stream = io.BytesIO(audio_bytes)
    try:
        y, sr = librosa.load(audio_stream, sr=22050, mono=True, duration=60.0)
    except Exception as exc:
        raise ValueError(f"Impossibile decodificare il file audio: {exc}") from exc
    
    if y.size == 0 or np.max(np.abs(y)) < 1e-4:
        raise ValueError("Il file audio risulta silenzioso o vuoto.")
    
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    tempo_val = float(tempo[0]) if isinstance(tempo, (np.ndarray, list)) else float(tempo)
    detected_bpm = max(55, min(220, int(round(tempo_val))))
    
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_sum = np.sum(chroma, axis=1)
    root = int(np.argmax(chroma_sum))
    
    threshold = np.max(chroma_sum) * 0.45
    intervals = sorted({(i - root) % 12 for i, val in enumerate(chroma_sum) if val >= threshold})
    if 0 not in intervals:
        intervals.insert(0, 0)
    if len(intervals) < 5:
        for iv in [0, 2, 3, 5, 7, 8, 10]:
            if iv not in intervals: intervals.append(iv)
        intervals = sorted(set(intervals))

    f0, voiced_flag, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C6'), sr=sr, frame_length=2048)
    times = librosa.times_like(f0, sr=sr)
    
    seconds_per_beat = 60.0 / detected_bpm
    seconds_per_step = seconds_per_beat / (quantize_grid / 4.0)
    ticks_per_step = TICKS_BEAT // (quantize_grid // 4)
    
    total_steps = max(16, int(math.ceil(times[-1] / seconds_per_step)))
    step_pitches: list[int | None] = [None] * total_steps
    
    for t, freq, is_voiced in zip(times, f0, voiced_flag):
        if is_voiced and not np.isnan(freq) and freq > 0:
            step_idx = int(round(t / seconds_per_step))
            if 0 <= step_idx < total_steps:
                midi_note = int(round(librosa.hz_to_midi(freq)))
                step_pitches[step_idx] = max(24, min(108, midi_note))
                
    notes: list[dict[str, int]] = []
    idx = 0
    while idx < total_steps:
        pitch = step_pitches[idx]
        if pitch is not None:
            end_idx = idx + 1
            while end_idx < total_steps and step_pitches[end_idx] == pitch:
                end_idx += 1
            dur_steps = end_idx - idx
            if dur_steps >= min_note_duration_steps:
                notes.append({
                    'pitch': pitch,
                    'tick': idx * ticks_per_step,
                    'dur': dur_steps * ticks_per_step - 10,
                    'vel': 92,
                    'track': 0
                })
            idx = end_idx
        else:
            idx += 1
            
    # Genera byte MIDI grezzi della trascrizione
    mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_BEAT)
    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name='Audio Transcription', time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(detected_bpm), time=0))
    
    events = []
    for n in notes:
        events.append((n['tick'], 1, n['pitch'], n['vel']))
        events.append((n['tick'] + max(1, n['dur']), 0, n['pitch'], 0))
    events.sort(key=lambda x: (x[0], x[1]))
    
    last_tick = 0
    for tick, is_on, pitch, vel in events:
        delta = max(0, tick - last_tick)
        msg_type = 'note_on' if is_on else 'note_off'
        track.append(mido.Message(msg_type, note=pitch, velocity=vel, channel=0, time=delta))
        last_tick = tick
        
    track.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(track)
    buf = io.BytesIO()
    mid.save(file=buf)
    
    return {
        'bpm': detected_bpm,
        'root': root,
        'scale': intervals,
        'notes': notes,
        'midi_bytes': buf.getvalue()
    }

def enhance_remix_pools(notes_data: list[dict[str, int]], root: int, scale: list[int]) -> list[dict[str, int]]:
    if not notes_data: return []
    q = TICKS_BEAT // 4
    beat = TICKS_BEAT
    bar_ticks = 4 * beat
    by_bar: dict[int, list[dict[str, int]]] = {}
    for n in notes_data:
        b = n['tick'] // bar_ticks
        by_bar.setdefault(b, []).append(n)
        
    cleaned: list[dict[str, int]] = []
    for b in sorted(by_bar.keys()):
        bar_notes = by_bar[b]
        slot_map: dict[int, list[dict[str, int]]] = {}
        for n in bar_notes:
            rel_tick = n['tick'] % bar_ticks
            step = int(round(rel_tick / q)) % 16
            slot_map.setdefault(step, []).append(n)
        
        for step in sorted(slot_map.keys()):
            candidates = slot_map[step]
            candidates.sort(key=lambda x: x['pitch'])
            selected = [candidates[-1]]
            for sel in selected:
                octave = (sel['pitch'] - root) // 12
                rel = (sel['pitch'] - root) % 12
                closest = min(scale, key=lambda x: abs(x - rel))
                snapped_pitch = max(24, min(108, root + octave * 12 + closest))
                cleaned.append({
                    'pitch': snapped_pitch,
                    'tick': b * bar_ticks + step * q,
                    'dur': max(q, int(round(sel['dur'] / q)) * q) - 10,
                    'vel': sel.get('vel', 90),
                    'track': sel.get('track', 0)
                })
    return cleaned

# ================= FUNZIONI DI SUPPORTO AL MIDI INTERNO =================
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
            if msg.type not in ('note_on', 'note_off') or msg.channel == 9:
                continue
            key = (msg.channel, msg.note)
            if msg.type == 'note_on' and msg.velocity > 0:
                if key in pending: close(key, t)
                pending[key] = (t, msg.velocity)
            elif key in pending:
                close(key, t)
    return out

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

# ================= INTERFACCIA PRINCIPALE STREAMLIT =================

st.title("🎹 MIDI Forge Universale - Advanced DAW Generator & Remix Studio")
st.markdown("---")

st.sidebar.header("🎛️ Pannello di Controllo")
genre_list = sorted(GENRES.keys())
genre = st.sidebar.selectbox("Genere Musicale", genre_list, index=0)
base_bpm = st.sidebar.slider("BPM di Produzione", 60, 200, GENRES[genre]['bpm_default'])
bar_count = st.sidebar.selectbox("Lunghezza Brano (Battute)", [8, 16, 32, 64, 128], index=2)
seed_val = st.sidebar.number_input("Seed Creativo", value=42, step=1)

st.markdown("### 🎙️ 1. Scegli la Sorgente Creativa")
source_mode = st.radio(
    "Sorgente Input",
    [
        "Da File Audio (Trascrivi / Remix / Ex Novo)",
        "Da File MIDI Esistente (Remix / Faithful)",
        "Generazione Ex Novo (Senza Input)",
    ],
    horizontal=True,
)

detected_meta = None
clean_notes = []
uploaded_midi = None

if source_mode == "Da File Audio (Trascrivi / Remix / Ex Novo)":
    if not HAS_LIBROSA:
        st.warning("⚠️ La libreria `librosa` non è disponibile in questo ambiente. L'analisi audio potrebbe non funzionare. Puoi comunque usare i file MIDI.")
    audio_file = st.file_uploader("Carica file audio (WAV, MP3, M4A, FLAC)", type=['wav', 'mp3', 'm4a', 'flac'])
    if audio_file is not None:
        st.audio(audio_file)
        with st.spinner("Analisi audio in corso (BPM, Tonalità e Trascrizione MIDI)..."):
            try:
                audio_res = analyze_and_transcribe_audio(audio_file.read())
                detected_meta = audio_res
                col1, col2, col3 = st.columns(3)
                col1.metric("BPM Rilevati", audio_res['bpm'])
                col2.metric("Tonalità Stimata", NOTE_NAMES[audio_res['root']])
                col3.download_button(
                    "⬇️ Scarica Trascrizione MIDI Grezza",
                    data=audio_res['midi_bytes'],
                    file_name="trascrizione_originale.mid",
                    mime="audio/midi",
                )
                if st.checkbox("Usa i BPM rilevati dall’audio", value=True):
                    base_bpm = audio_res['bpm']
                clean_notes = enhance_remix_pools(audio_res['notes'], audio_res['root'], audio_res['scale'])
                st.success(f"Trascrizione completata: {len(clean_notes)} eventi MIDI ottimizzati pronti per il remix.")
            except Exception as e:
                st.error(f"Errore durante l'analisi audio: {e}")

elif source_mode == "Da File MIDI Esistente (Remix / Faithful)":
    uploaded_midi = st.file_uploader("Carica file MIDI (.mid)", type=['mid', 'midi'])
    if uploaded_midi is not None:
        try:
            mid_data = mido.MidiFile(file=uploaded_midi)
            clean_notes = notes_from_midi(mid_data)
            root, scale = extract_dna(clean_notes)
            st.success(f"File MIDI caricato con successo! Note trovate: {len(clean_notes)} | Tonalità stimata: {NOTE_NAMES[root]}")
        except Exception as e:
            st.error(f"Errore lettura file MIDI: {e}")

st.markdown("---")
st.markdown("### 🚀 2. Azione di Produzione e Generazione")

if st.button("🔥 Genera Produzione MIDI Completa", type="primary", use_container_width=True):
    with st.spinner("Elaborazione e arrangiamento in corso..."):
        # Ricava radice e scala
        if detected_meta:
            root_key = detected_meta['root']
            scale_intervals = detected_meta['scale']
        elif clean_notes:
            root_key, scale_intervals = extract_dna(clean_notes)
        else:
            root_key = 0
            scale_intervals = [0, 2, 3, 5, 7, 8, 10]

        # Selezione o generazione note finali
        if clean_notes:
            track_notes = clean_notes
        else:
            # Generazione coerente ex novo ispirata allo stile
            rng = random.Random(seed_val * 97 + 13)
            track_notes = []
            q = TICKS_BEAT // 4
            for bar in range(bar_count):
                for step in range(16):
                    if rng.random() < GENRES[genre]['arp_density']:
                        deg = rng.choice(scale_intervals)
                        pitch = max(36, min(96, 60 + root_key + deg))
                        track_notes.append({
                            'tick': bar * 64 * q + step * q,
                            'dur': q * 2,
                            'pitch': pitch,
                            'vel': 85,
                            'channel': 0
                        })

        # Costruzione file MIDI finale
        mid_out = mido.MidiFile(type=1, ticks_per_beat=TICKS_BEAT)
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=f'MIDI Forge - {genre}', time=0))
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(base_bpm), time=0))

        events = []
        for n in track_notes:
            events.append((n['tick'], 1, n['pitch'], n['vel'], n.get('channel', 0)))
            events.append((n['tick'] + max(1, n['dur']), 0, n['pitch'], 0, n.get('channel', 0)))
        events.sort(key=lambda x: (x[0], x[1]))

        last_tick = 0
        for tick, is_on, pitch, vel, chan in events:
            delta = max(0, tick - last_tick)
            msg_type = 'note_on' if is_on else 'note_off'
            track.append(mido.Message(msg_type, note=pitch, velocity=vel, channel=chan, time=delta))
            last_tick = tick

        track.append(mido.MetaMessage('end_of_track', time=0))
        mid_out.tracks.append(track)

        out_buf = io.BytesIO()
        mid_out.save(file=out_buf)
        midi_bytes_final = out_buf.getvalue()

        st.success("🎉 Produzione MIDI completata con successo!")
        st.download_button(
            label="📥 Scarica File MIDI Definitivo (.mid)",
            data=midi_bytes_final,
            file_name=f"MIDI_Forge_{genre}_{base_bpm}BPM.mid",
            mime="audio/midi",
            use_container_width=True,
        )

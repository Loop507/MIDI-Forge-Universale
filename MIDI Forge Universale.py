"""
MIDI Forge Universale - Versione Integrata in Blocco Unico
(Include Analisi Audio-to-MIDI, Remix Avanzato e Generazione Coerente Ex Novo)
"""
from __future__ import annotations

import io
import math
import random
from pathlib import Path
from typing import Any

import mido
import numpy as np
import streamlit as st

# Tentativo di importazione librosa per l'analisi audio
try:
  import librosa

  HAS_LIBROSA = True
except ImportError:
  HAS_LIBROSA = False

NOTE_NAMES = [
    'C',
    'C#',
    'D',
    'D#',
    'E',
    'F',
    'F#',
    'G',
    'G#',
    'A',
    'A#',
    'B',
]
TICKS_BEAT = 480

st.set_page_config(
    page_title='MIDI Forge Universale', page_icon='🎹', layout='wide'
)

st.title('🎹 MIDI Forge Universale - Advanced DAW Generator & Remix Studio')
st.markdown('---')


# ==========================================
# MOTORE AUDIO E GENERAZIONE COERENTE
# ==========================================


def analyze_and_transcribe_audio(
    audio_bytes: bytes,
    quantize_grid: int = 16,
    min_note_duration_steps: int = 1,
) -> dict[str, Any]:
  if not HAS_LIBROSA:
    raise RuntimeError(
        "La libreria 'librosa' non è installata. Aggiungi 'librosa' e"
        " 'soundfile' a requirements.txt."
    )

  audio_stream = io.BytesIO(audio_bytes)
  try:
    y, sr = librosa.load(audio_stream, sr=22050, mono=True, duration=60.0)
  except Exception as exc:
    raise ValueError(f'Impossibile decodificare il file audio: {exc}') from exc

  if y.size == 0 or np.max(np.abs(y)) < 1e-4:
    raise ValueError('Il file audio risulta silenzioso o vuoto.')

  # Rilevamento BPM
  tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
  tempo_val = (
      float(tempo[0]) if isinstance(tempo, (np.ndarray, list)) else float(tempo)
  )
  detected_bpm = max(55, min(220, int(round(tempo_val))))

  # Estrazione Chroma
  chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
  chroma_sum = np.sum(chroma, axis=1)
  root = int(np.argmax(chroma_sum))

  threshold = np.max(chroma_sum) * 0.45
  intervals = sorted(
      {(i - root) % 12 for i, val in enumerate(chroma_sum) if val >= threshold}
  )
  if 0 not in intervals:
    intervals.insert(0, 0)
  if len(intervals) < 5:
    default_minor = [0, 2, 3, 5, 7, 8, 10]
    for iv in default_minor:
      if iv not in intervals:
        intervals.append(iv)
    intervals = sorted(set(intervals))

  # Tracciamento frequenze pYIN
  f0, voiced_flag, _ = librosa.pyin(
      y,
      fmin=librosa.note_to_hz('C2'),
      fmax=librosa.note_to_hz('C6'),
      sr=sr,
      frame_length=2048,
  )
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
            'track': 0,
        })
      idx = end_idx
    else:
      idx += 1

  midi_bytes = _build_raw_transcription_midi(notes, detected_bpm)

  return {
      'bpm': detected_bpm,
      'root': root,
      'scale': intervals,
      'notes': notes,
      'midi_bytes': midi_bytes,
  }


def _build_raw_transcription_midi(
    notes: list[dict[str, int]], bpm: int
) -> bytes:
  mid = mido.MidiFile(type=1, ticks_per_beat=TICKS_BEAT)
  track = mido.MidiTrack()
  track.append(mido.MetaMessage('track_name', name='Audio Transcription', time=0))
  track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))

  events = []
  for n in notes:
    events.append((n['tick'], 1, n['pitch'], n['vel']))
    events.append((n['tick'] + max(1, n['dur']), 0, n['pitch'], 0))
  events.sort(key=lambda x: (x[0], x[1]))

  last_tick = 0
  for tick, is_on, pitch, vel in events:
    delta = max(0, tick - last_tick)
    msg_type = 'note_on' if is_on else 'note_off'
    track.append(
        mido.Message(msg_type, note=pitch, velocity=vel, channel=0, time=delta)
    )
    last_tick = tick

  track.append(mido.MetaMessage('end_of_track', time=0))
  mid.tracks.append(track)
  buf = io.BytesIO()
  mid.save(file=buf)
  return buf.getvalue()


def enhance_remix_pools(
    notes_data: list[dict[str, int]], root: int, scale: list[int]
) -> list[dict[str, int]]:
  if not notes_data:
    return []

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
      if step % 4 in (1, 3) and n['dur'] >= beat // 2:
        step = (step // 4) * 4
      slot_map.setdefault(step, []).append(n)

    for step in sorted(slot_map.keys()):
      candidates = slot_map[step]
      candidates.sort(key=lambda x: x['pitch'])
      selected = [candidates[-1]]
      if (
          len(candidates) > 1
          and (candidates[-1]['pitch'] - candidates[0]['pitch']) >= 7
      ):
        selected.append(candidates[0])

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
            'track': sel.get('track', 0),
        })
  return cleaned


def generate_coherent_phrase_motif(
    bars: int,
    root: int,
    scale: list[int],
    seed: int,
    bpm: int = 128,
    density: float = 0.65,
    base_octave: int = 60,
) -> list[dict[str, int]]:
  rng = random.Random(seed * 97 + 13)
  n = len(scale)
  q = TICKS_BEAT // 4
  bpm_factor = 1.0 if bpm <= 115 else (0.8 if bpm <= 140 else 0.6)
  eff_density = max(0.25, min(0.9, density * bpm_factor))

  motif_a: list[tuple[int, int, int]] = []
  cur_deg = 0
  step = 0
  while step < 32:
    if rng.random() < eff_density or step == 0:
      dur = rng.choices([2, 4, 6, 8], weights=[3, 4, 2, 1])[0]
      dur = min(dur, 32 - step)
      motif_a.append((step, cur_deg, dur))
      move = rng.choices([-2, -1, 0, 1, 2], weights=[1, 4, 1, 4, 1])[0]
      cur_deg = max(-n, min(n * 2, cur_deg + move))
      step += dur
    else:
      step += 2

  motif_b = [(st, deg + 2, du) for st, deg, du in motif_a]
  events: list[dict[str, int]] = []
  bar_ticks = 16 * q

  for bar in range(bars):
    phrase_pos = bar % 8
    half_bar = (bar % 2) * 16
    active_motif = motif_b if phrase_pos in (4, 5) else motif_a
    bar_start = bar * bar_ticks

    for st, deg, du in active_motif:
      if half_bar <= st < half_bar + 16:
        local_step = st - half_bar
        if phrase_pos == 7 and local_step >= 8:
          final_deg = 0
        elif phrase_pos in (2, 3) and local_step >= 12:
          final_deg = deg + 1
        else:
          final_deg = deg

        oct_shift = (final_deg // n) * 12
        scale_step = scale[final_deg % n]
        pitch = max(
            36, min(96, base_octave + root + oct_shift + scale_step)
        )
        vel = 88 if local_step % 4 == 0 else 74 + rng.randint(-6, 6)

        events.append({
            'tick': bar_start + local_step * q,
            'dur': max(q, du * q - 15),
            'pitch': pitch,
            'vel': max(40, min(120, vel)),
            'channel': 4,
        })
  return events


# ==========================================
# INTERFACCIA UTENTE STREAMLIT
# ==========================================

st.sidebar.header('🎛️ Pannello di Controllo')
genre = st.sidebar.selectbox(
    'Genere Musicale',
    ['Techno', 'Tech House', 'Deep House', 'Synthwave', 'Trap', 'Ambient'],
)
base_bpm = st.sidebar.slider('BPM', 60, 180, 128)
bar_count = st.sidebar.selectbox(
    'Lunghezza Brano (Battute)', [8, 16, 32, 64], index=1
)
seed_val = st.sidebar.number_input('Seed (Rigenera groove)', value=42, step=1)

st.markdown('### 🎙️ 1. Scegli la Sorgente Creativa')
source_mode = st.radio(
    'Modalità di Input',
    [
        'Da File Audio (Trascrivi / Remix / Ex Novo)',
        'Da File MIDI Esistente',
        'Generazione Ex Novo (Senza Input)',
    ],
    horizontal=True,
)

detected_meta = None
clean_notes = []

if source_mode == 'Da File Audio (Trascrivi / Remix / Ex Novo)':
  audio_file = st.file_uploader(
      'Carica un file audio di riferimento (WAV, MP3, M4A, FLAC)',
      type=['wav', 'mp3', 'm4a', 'flac'],
  )
  if audio_file is not None:
    st.audio(audio_file)
    with st.spinner(
        'Analisi audio in corso (BPM, Tonalità e Trascrizione MIDI)...'
    ):
      try:
        audio_res = analyze_and_transcribe_audio(audio_file.read())
        detected_meta = audio_res

        col1, col2, col3 = st.columns(3)
        col1.metric('BPM Rilevati', audio_res['bpm'])
        col2.metric('Tonalità Stimata', NOTE_NAMES[audio_res['root']])
        col3.download_button(
            '⬇️ Scarica MIDI Trascrizione Originale',
            data=audio_res['midi_bytes'],
            file_name='trascrizione_originale.mid',
            mime='audio/midi',
        )

        if st.checkbox('Usa i BPM rilevati dall’audio', value=True):
          base_bpm = audio_res['bpm']

        clean_notes = enhance_remix_pools(
            audio_res['notes'], audio_res['root'], audio_res['scale']
        )
        st.success(
            f"Trascrizione completata: {len(clean_notes)} eventi MIDI pronti"
            ' per il Remix o l’Ispirazione.'
        )
      except Exception as e:
        st.error(f'Errore durante l’analisi audio: {e}')

st.markdown('---')
st.markdown('### 🚀 2. Scegli l’Azione di Produzione')

action = st.radio(
    'Cosa vuoi fare?',
    [
        'Remix (Adatta il materiale audio/MIDI al nuovo genere e BPM)',
        (
            'Generazione Ex Novo (Crea un brano nuovo ispirato al'
            ' groove/tonalità)'
        ),
    ],
    horizontal=True,
)

if st.button('🔥 Genera Produzione MIDI', type='primary', use_container_width=True):
  with st.spinner('Elaborazione e arrangiamento in corso...'):
    root_key = detected_meta['root'] if detected_meta else 0
    scale_intervals = (
        detected_meta['scale'] if detected_meta else [0, 2, 3, 5, 7, 8, 10]
    )

    if 'Remix' in action and clean_notes:
      track_notes = clean_notes
    else:
      track_notes = generate_coherent_phrase_motif(
          bars=bar_count,
          root=root_key,
          scale=scale_intervals,
          seed=seed_val,
          bpm=base_bpm,
          density=0.7,
      )

    mid_out = mido.MidiFile(type=1, ticks_per_beat=TICKS_BEAT)
    track = mido.MidiTrack()
    track.append(
        mido.MetaMessage('track_name', name=f'MIDI Forge - {genre}', time=0)
    )
    track.append(
        mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(base_bpm), time=0)
    )

    events = []
    for n in track_notes:
      events.append((n['tick'], 1, n['pitch'], n['vel'], n.get('channel', 0)))
      events.append(
          (n['tick'] + max(1, n['dur']), 0, n['pitch'], 0, n.get('channel', 0))
      )
    events.sort(key=lambda x: (x[0], x[1]))

    last_tick = 0
    for tick, is_on, pitch, vel, chan in events:
      delta = max(0, tick - last_tick)
      msg_type = 'note_on' if is_on else 'note_off'
      track.append(
          mido.Message(
              msg_type, note=pitch, velocity=vel, channel=chan, time=delta
          )
      )
      last_tick = tick

    track.append(mido.MetaMessage('end_of_track', time=0))
    mid_out.tracks.append(track)

    out_buf = io.BytesIO()
    mid_out.save(file=out_buf)
    midi_bytes_final = out_buf.getvalue()

    st.success('🎉 Produzione completata con successo!')
    st.download_button(
        label='📥 Scarica File MIDI Definitivo (.mid)',
        data=midi_bytes_final,
        file_name=f'MIDI_Forge_{genre}_{base_bpm}BPM.mid',
        mime='audio/midi',
        use_container_width=True,
    )

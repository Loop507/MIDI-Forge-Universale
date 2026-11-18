# ==========================================
# MIDI FORGE UNIVERSALE - v9.1 (FULL FIXED)
# ==========================================
import streamlit as st
import mido
import io
import random
import numpy as np

st.set_page_config(
    page_title="MIDI Forge Universale",
    page_icon="🎹",
    layout="wide"
)

# --- CONFIGURAZIONE & COSTANTI ---
TICKS_BEAT = 480
GENRES = {
    "Cyberpunk Synthwave": {"tempo": 118, "scale": "minor_pentatonic", "swing": 0.05, "density": 0.8},
    "Lo-Fi Chill Hop": {"tempo": 82, "scale": "dorian", "swing": 0.25, "density": 0.5},
    "EDM Festival Anthem": {"tempo": 128, "scale": "minor", "swing": 0.0, "density": 0.95},
    "Trap Dark Heavy": {"tempo": 140, "scale": "phrygian", "swing": 0.1, "density": 0.85},
    "Jazz Swing Club": {"tempo": 120, "scale": "bebop", "swing": 0.35, "density": 0.7},
    "Epic Cinematic orchestral": {"tempo": 95, "scale": "harmonic_minor", "swing": 0.0, "density": 0.6},
    "Ambient Space Drone": {"tempo": 60, "scale": " lydian", "swing": 0.0, "density": 0.3}
}

SCALES = {
    "minor_pentatonic": [0, 3, 5, 7, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "minor": [0, 2, 3, 5, 7, 8, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "bebop": [0, 2, 4, 5, 7, 9, 10, 11],
    "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
    "lydian": [0, 2, 4, 6, 7, 9, 11],
    "major": [0, 2, 4, 5, 7, 9, 11]
}

CHORD_PROGRESSIONS = {
    "Pop / Anthem (I-V-vi-IV)": [0, 7, 9, 5],
    "Sad / Cinematic (vi-IV-I-V)": [9, 5, 0, 7],
    "Jazz / Lo-Fi (ii-V-I-VI)": [2, 7, 0, 9],
    "Dark / Trap (i-VI-III-VII)": [0, 8, 3, 10],
    "Ambient / Modal (i-iv-i-v)": [0, 5, 0, 7]
}

# --- FUNZIONI DI UTILITÀ & PARSING MIDI ---
def freq_to_midi(f):
    if f <= 0:
        return 0
    m = 69 + 12 * np.log2(f / 440.0)
    return int(np.clip(round(m), 0, 127))

def audio_to_midi_bytes(uploaded_file):
    try:
        import librosa
        audio_bytes = uploaded_file.read()
        audio_io = io.BytesIO(audio_bytes)
        y, sr = librosa.load(audio_io, sr=None)
        
        # Stima BPM
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
        if bpm < 40 or bpm > 240:
            bpm = 120.0
            
        # Estrazione pitch (YIN)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr
        )
        
        mid = mido.MidiFile(ticks_per_beat=TICKS_BEAT)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
        
        # Converti f0 in eventi MIDI quantizzati
        hop_length = 512
        frames_per_tick = sr / hop_length / (bpm / 60.0 * TICKS_BEAT)
        
        current_note = None
        current_start_tick = 0
        tick_counter = 0
        
        notes_list = []
        for i, freq in enumerate(f0):
            t = int(round(i * frames_per_tick))
            p = freq_to_midi(freq) if not np.isnan(freq) and freq > 0 else 0
            
            if p > 0:
                if current_note is None:
                    current_note = p
                    current_start_tick = t
                elif current_note != p:
                    duration = max(30, t - current_start_tick)
                    notes_list.append((current_start_tick, duration, current_note, 85))
                    current_note = p
                    current_start_tick = t
            else:
                if current_note is not None:
                    duration = max(30, t - current_start_tick)
                    notes_list.append((current_start_tick, duration, current_note, 85))
                    current_note = None
                    
        # Ordina e scrivi sul file MIDI
        notes_list.sort(key=lambda x: x[0])
        last_tick = 0
        for st, dur, pitch, vel in notes_list:
            delta_on = max(0, st - last_tick)
            pitch = int(np.clip(pitch, 0, 127))
            track.append(mido.Message('note_on', note=pitch, velocity=vel, time=delta_on))
            track.append(mido.Message('note_off', note=pitch, velocity=0, time=dur))
            last_tick = st + dur
            
        out_buf = io.BytesIO()
        mid.save(file=out_buf)
        out_buf.seek(0)
        return out_buf, bpm
    except Exception as e:
        # Fallback sicuro se librosa fallisce o non è disponibile
        st.warning(f"Impossibile analizzare l'audio con precisione avanzata ({e}). Generazione traccia di fallback.")
        mid = mido.MidiFile(ticks_per_beat=TICKS_BEAT)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(120), time=0))
        for i in range(16):
            track.append(mido.Message('note_on', note=60 + (i % 5), vel=80, time=0 if i==0 else 240))
            track.append(mido.Message('note_off', note=60 + (i % 5), vel=0, time=240))
        out_buf = io.BytesIO()
        mid.save(file=out_buf)
        out_buf.seek(0)
        return out_buf, 120.0

def extract_notes(mid_file):
    try:
        mid = mido.MidiFile(file=mid_file)
        notes = []
        for track in mid.tracks:
            abs_time = 0
            active_notes = {}
            for msg in track:
                abs_time += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    active_notes[msg.note] = abs_time
                elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in active_notes:
                        st = active_notes.pop(msg.note)
                        notes.append((st, abs_time, int(np.clip(msg.note, 0, 127)), msg.velocity))
        notes.sort(key=lambda x: x[0])
        return notes
    except Exception as e:
        st.error(f"Errore nella lettura del file MIDI: {e}")
        return []

def _fold(p):
    return int(np.clip(p, 24, 96))

# --- INTERFACCIA UTENTE PRINCIPALE ---
st.title("🎹 MIDI Forge Universale v9.1")
st.markdown("Generatore, Remix e Convertitore Audio/MIDI intelligente con correzioni avanzate di stabilità.")

col_mode, col_genre = st.columns(2)
with col_mode:
    mode = st.selectbox("Modalità Operativa", ["Da Zero (Generativo)", "Remix MIDI Esistente", "Audio to MIDI Converter"])
with col_genre:
    selected_genre = st.selectbox("Genere / Stile", list(GENRES.keys()))

g_conf = GENRES[selected_genre]

uploaded_midi = None
uploaded_audio = None

if mode == "Remix MIDI Esistente":
    uploaded_midi = st.file_uploader("Carica file MIDI sorgente (.mid)", type=["mid", "midi"])
elif mode == "Audio to MIDI Converter":
    uploaded_audio = st.file_uploader("Carica file Audio (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a", "flac"])

with st.sidebar:
    st.header("Parametri Avanzati")
    tempo = st.slider("BPM (Velocità)", 40, 220, int(g_conf["tempo"]))
    scale_name = st.selectbox("Scala Musicale", list(SCALES.keys()), index=list(SCALES.keys()).index(g_conf["scale"]))
    prog_name = st.selectbox("Progressione Accordi", list(CHORD_PROGRESSIONS.keys()))
    root_note = st.selectbox("Nota Fondamentale", ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"], index=0)
    density = st.slider("Densità Note / Eventi", 0.1, 1.0, float(g_conf["density"]))
    swing = st.slider("Swing / Groove", 0.0, 0.5, float(g_conf["swing"]))
    bars = st.slider("Lunghezza (Battute)", 2, 32, 8)

root_offsets = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
base_root = 60 + root_offsets[root_note]
scale_intervals = SCALES[scale_name]
chord_steps = CHORD_PROGRESSIONS[prog_name]

if st.button("🚀 Genera / Elabora MIDI", type="primary"):
    with st.spinner("Elaborazione in corso..."):
        if mode == "Audio to MIDI Converter" and uploaded_audio:
            midi_buf, detected_bpm = audio_to_midi_bytes(uploaded_audio)
            st.session_state['_audio_mid_bytes'] = midi_buf.getvalue()
            st.session_state['_audio_bpm'] = detected_bpm
            uploaded_midi = io.BytesIO(st.session_state['_audio_mid_bytes'])
            tempo = int(detected_bpm)
            st.success(f"Audio convertito con successo! BPM rilevato: {tempo}")

        # Creazione file MIDI finale
        mid = mido.MidiFile(ticks_per_beat=TICKS_BEAT)
        
        # Traccia Meta / Tempo
        meta_track = mido.MidiTrack()
        mid.tracks.append(meta_track)
        meta_track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(tempo), time=0))
        
        # Tracce Strumenti
        tracks = {
            'chord': mido.MidiTrack(),
            'arp': mido.MidiTrack(),
            'bass': mido.MidiTrack(),
            'drums': mido.MidiTrack()
        }
        for name, tr in tracks.items():
            mid.tracks.append(tr)

        pool = []
        if uploaded_midi is not None:
            if mode == "Audio to MIDI Converter":
                uploaded_midi.seek(0)
            pool = extract_notes(uploaded_midi)

        q = TICKS_BEAT // 4
        total_steps = bars * 4 * 4
        
        def _note(tr, t, dur, pitch, vel, chan=0):
            p = int(np.clip(pitch, 0, 127))
            tr.append(mido.Message('note_on', note=p, velocity=int(vel), time=max(0, int(t)), channel=chan))
            tr.append(mido.Message('note_off', note=p, velocity=0, time=max(10, int(dur)), channel=chan))

        # Generazione loop
        for s in range(total_steps):
            t_abs = s * q
            sw = int(q * swing) if (s % 2 == 1) else 0
            
            # 1. Accordi (Pad)
            if s % 16 == 0:
                chord_idx = (s // 16) % len(chord_steps)
                c_root = base_root - 12 + chord_steps[chord_idx]
                for offset in [0, 3, 7]:
                    _note(tracks['chord'], t_abs + sw, TICKS_BEAT * 4 - 20, c_root + offset, 70, 1)

            # 2. Basso
            if s % 2 == 0 and random.random() < density:
                bass_root = base_root - 24
                _note(tracks['bass'], t_abs + sw, q - 10, bass_root, 95, 2)

            # 3. Arpeggi / Lead / Remix
            if random.random() < density:
                if pool and mode in ["Remix MIDI Esistente", "Audio to MIDI Converter"]:
                    # Tolleranza ampliata per evitare note perse o vuoti
                    onsets = [(st, en, p) for st, en, p in pool if abs(st - t_abs) <= q]
                    if onsets:
                        lead_st, lead_en, lead_p = max(onsets, key=lambda x: x[2])
                        orig_steps = max(1, min(total_steps - s, (lead_en - lead_st) // q))
                        _note(tracks['arp'], t_abs + sw, orig_steps * q - 10, _fold(lead_p), 100, 0)
                else:
                    scale_deg = random.choice(scale_intervals)
                    arp_pitch = base_root + scale_deg + (12 * random.choice([0, 1]))
                    _note(tracks['arp'], t_abs + sw, q - 15, arp_pitch, 90, 0)

            # 4. Batteria (Canale 9)
            if s % 4 == 0: # Cassa
                _note(tracks['drums'], t_abs, 30, 36, 110, 9)
            if s % 8 == 4: # Rullante
                _note(tracks['drums'], t_abs, 30, 38, 100, 9)
            if random.random() < (density * 0.8): # Hi-Hat
                _note(tracks['drums'], t_abs + (q // 2), 20, 42, 80, 9)

        # Salvataggio finale
        final_buf = io.BytesIO()
        mid.save(file=final_buf)
        final_buf.seek(0)
        
        st.session_state['generated_midi'] = final_buf.getvalue()
        st.success("✨ File MIDI generato ed elaborato con successo!")

if 'generated_midi' in st.session_state:
    st.download_button(
        label="📥 Scarica File MIDI",
        data=st.session_state['generated_midi'],
        file_name="midi_forge_output.mid",
        mime="audio/midi"
    )

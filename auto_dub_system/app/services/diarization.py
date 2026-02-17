import os
import torch
import librosa
import numpy as np
import warnings
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning)

# =========================
# SPEAKER ANALYZER
# =========================
class SpeakerAnalyzer:

    def __init__(self, hf_token=None, enable_gender=True):

        self.token = hf_token or os.getenv("HF_TOKEN")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.pipeline = None
        self.enable_gender = enable_gender

        self._load_diarizer()

    # -------------------------
    # LOAD DIARIZATION MODEL
    # -------------------------
    def _load_diarizer(self):
        try:
            from pyannote.audio import Pipeline

            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=self.token
            )

            self.pipeline.to(torch.device(self.device))
            print("✅ Diarization model loaded")

        except Exception as e:
            print("❌ Failed loading diarization model:", e)
            self.pipeline = None


    # -------------------------
    # MAIN ANALYSIS FUNCTION
    # -------------------------
    def analyze(self, audio):

        if not self.pipeline:
            return [], {}

        diarization = self._run_diarization(audio)
        turns = self._extract_turns(diarization)

        if not self.enable_gender:
            return turns, {}

        genders = self._detect_genders(audio, turns)

        return turns, genders


    # -------------------------
    # RUN MODEL
    # -------------------------
    def _run_diarization(self, audio):

        if isinstance(audio, np.ndarray):
            waveform = torch.from_numpy(audio).float()

            if waveform.ndim == 1:
                waveform = waveform.unsqueeze(0)

            return self.pipeline({
                "waveform": waveform,
                "sample_rate": 16000
            })

        return self.pipeline(audio)


    # -------------------------
    # EXTRACT SPEAKER SEGMENTS
    # -------------------------
    def _extract_turns(self, diarization):

        turns = []

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append({
                "start": turn.start,
                "end": turn.end,
                "speaker": speaker
            })

        return turns


    # -------------------------
    # GENDER DETECTION
    # -------------------------
    def _detect_genders(self, audio, turns):

        sr = 16000

        if isinstance(audio, str):
            y, _ = librosa.load(audio, sr=sr)
        else:
            y = audio

        samples = {}

        # collect samples per speaker
        for t in turns:
            spk = t["speaker"]

            if spk not in samples:
                samples[spk] = []

            dur = min(t["end"] - t["start"], 3)
            if dur < 0.4:
                continue

            s = int(t["start"] * sr)
            e = int((t["start"] + dur) * sr)

            samples[spk].append(y[s:e])

            # limit total length
            if sum(len(x) for x in samples[spk]) > sr * 10:
                continue

        genders = {}

        for spk, segs in samples.items():

            if not segs:
                genders[spk] = "Unknown"
                continue

            data = np.concatenate(segs)

            f0, voiced, _ = librosa.pyin(
                data,
                fmin=librosa.note_to_hz("C2"),
                fmax=librosa.note_to_hz("C7"),
                sr=sr
            )

            voiced_f0 = f0[voiced]

            if len(voiced_f0) == 0:
                genders[spk] = "Unknown"
            else:
                genders[spk] = "Female" if np.nanmean(voiced_f0) > 165 else "Male"

        return genders


# =========================
# WORD → SPEAKER MAPPING
# =========================
def get_speaker(start, end, turns):

    best = None
    best_overlap = 0

    for t in turns:
        overlap = max(0, min(end, t["end"]) - max(start, t["start"]))
        if overlap > best_overlap:
            best_overlap = overlap
            best = t["speaker"]

    return best if best else turns[0]["speaker"]


def assign_word_speakers(words, turns):
    for w in words:
        w["speaker"] = get_speaker(w["start"], w["end"], turns)
    return words

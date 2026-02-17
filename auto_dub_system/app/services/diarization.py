import os
import torch
import librosa
import numpy as np
import warnings

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Suppress noisy library warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*torchcodec.*")

# from transformers import pipeline (Moved inside class for robustness)
from src.core.config import settings
import json
import src.config_constants as config

class SpeakerAnalyzer:
    def __init__(self, hf_token=None):
        # Priority: 1) Passed token, 2) Environment variable from .env
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.diarization_pipeline = None
        self.gender_pipeline = None
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Check global flag first
        if settings.ENABLE_GENDER_DETECTION:
             self.load_models()
        else:
             print("⚠️ Gender Detection DISABLED in config. Skipping model load.")

    def load_models(self):
        if not config.ENABLE_TORCHCODEC:
             print("INFO: TorchCodec disabled via config. Skipping Pyannote full pipeline if it depends on it.")
             # We still try to load Pyannote unless we know for sure it crashes
             pass

        # Lazy Import to prevent libtorchcodec crash on module load
        try:
             from pyannote.audio import Pipeline
        except ImportError as e:
             if not config.ENABLE_TORCHCODEC:
                 print(f"⚠️ Pyannote Import Failed (likely torchcodec), but ENABLE_TORCHCODEC=False. Continuing.")
             else:
                 print(f"❌ Pyannote Import Failed (libtorchcodec issue?): {e}")
             return
        except Exception as e:
             print(f"❌ Pyannote Import Error: {e}")
             return
        # Diagnostic logging (Safe)
        if self.hf_token:
            token_display = f"{self.hf_token[:4]}...{self.hf_token[-4:]}"
            print(f"DEBUG: HF_TOKEN found: {token_display}")
        else:
            print("DEBUG: HF_TOKEN NOT FOUND in environment or init.")

        if self.hf_token:
            # List of model IDs to try (standard IDs)
            model_ids = [
                "pyannote/speaker-diarization-3.1",
                "pyannote/speaker-diarization@2.1",
                "pyannote/speaker-diarization"
            ]
            
            error_details = []
            for model_id in model_ids:
                try:
                    print(f"Attempting to load diarization model: {model_id}")
                    # Try with 'token' argument first
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        model_id,
                        token=self.hf_token
                    )
                    if self.diarization_pipeline:
                        break
                except Exception as e1:
                    try:
                        # Try with legacy 'use_auth_token' argument
                        self.diarization_pipeline = Pipeline.from_pretrained(
                            model_id,
                            use_auth_token=self.hf_token
                        )
                        if self.diarization_pipeline:
                            break
                    except Exception as e2:
                        error_details.append(f"{model_id}: {str(e2)}")
                        continue
            
            if self.diarization_pipeline:
                if self.device == 0:
                    try:
                        self.diarization_pipeline.to(torch.device("cuda"))
                    except:
                        pass
                print(f"✅ Pyannote speaker diarization loaded successfully: {model_id}")
            else:
                print("❌ Speaker diarization failed to load after trying all models.")
                for detail in error_details:
                    print(f"   - {detail}")
                self.diarization_pipeline = None
        else:
            print("No HF token provided, diarization will be restricted or skipped.")

        try:
            # Using a highly standard public model
            from transformers import pipeline
            self.gender_pipeline = pipeline(
                "audio-classification",
                model="superb/wav2vec2-base-superb-sid",
                device=self.device
            )
            print("✅ Pitch-based gender detection ready")
        except Exception as e:
            print(f"⚠️  Gender model unavailable (transformers import failed): {e}")
            # Final fallback
            self.gender_pipeline = None

    def analyze_audio(self, audio_path_or_data):
        """
        Returns speaker turns and their identified genders.
        Accepts either a file path or a NumPy array of audio data.
        """
        if not self.diarization_pipeline:
            print("Diarization pipeline not available.")
            return [], {}

        print(f"Diarizing audio...")
        try:
            import numpy as np
            if isinstance(audio_path_or_data, np.ndarray):
                # Pyannote pipeline expects a dict for in-memory audio
                # Waveform MUST be (channel, time)
                waveform = torch.from_numpy(audio_path_or_data).float()
                if len(waveform.shape) == 1:
                    waveform = waveform.unsqueeze(0) # (1, time)
                
                audio_input = {
                    "waveform": waveform,
                    "sample_rate": 16000
                }
                diarization = self.diarization_pipeline(audio_input)
            else:
                diarization = self.diarization_pipeline(audio_path_or_data)
            
            # Robust check for different return types
            speaker_turns = []
            iterator = None
            
            # Case 1: Standard Pyannote Annotation object
            if hasattr(diarization, "itertracks"):
                iterator = diarization.itertracks(yield_label=True)
            if iterator is None:
                # Fallback: check all attributes for anything that looks like an annotation or list
                for attr_name in dir(diarization):
                    if not attr_name.startswith("_"):
                        attr_val = getattr(diarization, attr_name)
                        if hasattr(attr_val, "itertracks"):
                            print(f"Found tracks in attribute: {attr_name}")
                            iterator = attr_val.itertracks(yield_label=True)
                            break
                        elif isinstance(attr_val, (list, tuple)) and len(attr_val) > 0:
                            print(f"Found tracks in list attribute: {attr_name}")
                            iterator = attr_val
                            break
            
            if iterator is None:
                print(f"Warning: Unexpected diarization output type: {type(diarization)}. Attributes: {dir(diarization)}")
                # One last attempt: if it's subscriptsable but not a dict
                try:
                    target = diarization["annotation"] if "annotation" in dir(diarization) or hasattr(diarization, "__getitem__") else diarization
                    if hasattr(target, "itertracks"):
                        iterator = target.itertracks(yield_label=True)
                    else:
                        iterator = iter(target)
                except:
                    iterator = []

            for turn_info in iterator:
                # Handle different iteration formats
                if len(turn_info) == 3: # (segment, track, label)
                    turn, _, speaker = turn_info
                    speaker_turns.append({
                        "start": turn.start,
                        "end": turn.end,
                        "speaker": speaker
                    })
                elif hasattr(turn_info, "start"): # direct segment objects
                    speaker_turns.append({
                        "start": turn_info.start,
                        "end": turn_info.end,
                        "speaker": getattr(turn_info, "speaker", "SPEAKER_00")
                    })
                
            print(f"Found {len(set(s['speaker'] for s in speaker_turns))} speakers.")
            
            speaker_genders = self._identify_speaker_genders(audio_path_or_data, speaker_turns)
            
            return speaker_turns, speaker_genders
        except Exception as e:
            print(f"Diarization failed: {e}")
            import traceback
            traceback.print_exc()
            return [], {}

    def identify_gender_for_segment(self, audio_path, start, end):
        """
        Identifies gender for a specific time range in the audio using pitch detection.
        Higher pitch (F0 > 165Hz) is usually Female, lower is Male.
        """
        try:
            # Lazy import pydub to handle FFmpeg checks
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_path)
            # Optimize: Limit analysis to max 2 seconds to speed up pyin
            duration_ms = int((end - start) * 1000)
            analysis_duration = min(duration_ms, 2000) 
            
            # Take the middle part if longer than 2s, or just the beginning
            start_ms = int(start * 1000)
            if duration_ms > 2000:
                 offset = (duration_ms - 2000) // 2
                 start_ms += offset
            
            segment = audio[start_ms : start_ms + analysis_duration]
            
            # Convert to numpy
            samples = np.array(segment.get_array_of_samples()).astype(np.float32)
            if segment.sample_width == 2:
                samples = samples / 32768.0
            if segment.channels > 1:
                samples = samples.reshape((-1, segment.channels)).mean(axis=1)
            
            sr = segment.frame_rate
            
            # Extract pitch (Fundamental Frequency F0) using YIN algorithm
            # We filter out silent parts or very low/high outliers
            f0, voiced_flag, voiced_probs = librosa.pyin(
                samples, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr
            )
            
            # Get mean F0 of voiced parts
            voiced_f0 = f0[voiced_flag]
            if len(voiced_f0) > 0:
                mean_f0 = np.nanmean(voiced_f0)
                # Typical Male: 85-180Hz, Typical Female: 165-255Hz
                # Threshold ~165Hz is a good balance
                print(f"Detected Segment Frequency: {mean_f0:.2f}Hz")
                return "Female" if mean_f0 > 165 else "Male"
            
            # Use pipeline if pitch detection is inconclusive
            if self.gender_pipeline:
                results = self.gender_pipeline(samples)
                best_match = max(results, key=lambda x: x["score"])
                label = best_match["label"].lower()
                return "Female" if ("female" in label or "woman" in label) else "Male"
                
            return "Male" # Final default
        except Exception as e:
            err_str = str(e)
            if "torchcodec" in err_str or not config.ENABLE_TORCHCODEC:
                # Suppress noisy torchcodec error as requested
                pass 
            else:
                print(f"Segment gender detection failed: {e}")
            return "Unknown"


    def _identify_speaker_genders(self, audio_path_or_data, turns):
        if not self.gender_pipeline:
            return {}

        print("Identifying speaker genders...")
        try:
            import numpy as np
            sr = 16000
            if isinstance(audio_path_or_data, np.ndarray):
                y = audio_path_or_data
            else:
                # Load audio for gender analysis
                y, _ = librosa.load(audio_path_or_data, sr=sr)
            
            speaker_samples = {}
            
            # Collect representative samples for each speaker
            for turn in turns:
                speaker = turn["speaker"]
                if speaker not in speaker_samples:
                    speaker_samples[speaker] = []
                
                # Take up to 3 seconds from each turn, total up to 10 seconds per speaker
                start_s = turn["start"]
                duration = min(turn["end"] - turn["start"], 3.0)
                
                if duration < 0.5: continue # Skip too short segments
                
                start_idx = int(start_s * sr)
                end_idx = int((start_s + duration) * sr)
                
                if end_idx > len(y):
                    end_idx = len(y)
                
                if start_idx < end_idx:
                    speaker_samples[speaker].append(y[start_idx:end_idx])
                
                # Don't collect too much to save time
                if sum(len(s) for s in speaker_samples[speaker]) > 10 * sr:
                    continue

            speaker_genders = {}
            for speaker, samples in speaker_samples.items():
                if not samples:
                    speaker_genders[speaker] = "Male" # Default
                    continue
                
                # Concatenate samples
                audio_data = np.concatenate(samples)
                if len(audio_data) < 0.1 * sr:
                    speaker_genders[speaker] = "Male"
                    continue
                    
                # Get mean F0 of voiced parts
                f0, voiced_flag, voiced_probs = librosa.pyin(
                    audio_data, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr
                )
                
                voiced_f0 = f0[voiced_flag]
                if len(voiced_f0) > 0:
                    mean_f0 = np.nanmean(voiced_f0)
                    speaker_genders[speaker] = "Female" if mean_f0 > 165 else "Male"
                    print(f"Speaker {speaker} pitch: {mean_f0:.2f}Hz -> {speaker_genders[speaker]}")
                else:
                    speaker_genders[speaker] = "Male"
                
            return speaker_genders
        except Exception as e:
            print(f"Gender identification failed: {e}")
            return {}

def get_speaker_for_segment(start, end, speaker_turns):
    """
    Finds the speaker with the most overlap for a given segment.
    Uses time-weighted overlap for high precision.
    """
    if not speaker_turns:
        return "SPEAKER_00"
        
    overlap_map = {}
    
    for turn in speaker_turns:
        overlap_start = max(start, turn["start"])
        overlap_end = min(end, turn["end"])
        overlap = max(0, overlap_end - overlap_start)
        
        if overlap > 0:
            speaker = turn["speaker"]
            overlap_map[speaker] = overlap_map.get(speaker, 0) + overlap
            
    if not overlap_map:
        # Fallback: find nearest speaker if no direct overlap
        nearest_speaker = speaker_turns[0]["speaker"]
        min_dist = float('inf')
        for turn in speaker_turns:
            dist = min(abs(start - turn["end"]), abs(end - turn["start"]))
            if dist < min_dist:
                min_dist = dist
                nearest_speaker = turn["speaker"]
        return nearest_speaker
        
    return max(overlap_map.items(), key=lambda x: x[1])[0]

def assign_word_speakers(words, speaker_turns):
    """
    Assigns a speaker to each individual word based on diarization timing.
    Essential for perfect word-level subtitles and gender matching.
    """
    for word in words:
        word['speaker'] = get_speaker_for_segment(word['start'], word['end'], speaker_turns)
    return words
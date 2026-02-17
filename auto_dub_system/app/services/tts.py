import os
import re
import uuid
import subprocess
import asyncio
import edge_tts
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment

# --- 1. CORE UTILITIES (from media_engine.py) ---
class MediaUtils:
    FFMPEG_PATH = "ffmpeg"

    @classmethod
    def change_speed(cls, input_path, output_path, factor):
        """High-quality time stretching without pitch shift using FFmpeg."""
        # FFmpeg atempo filter is limited to 0.5x to 2.0x, we cap it safely
        factor = max(0.5, min(2.0, factor))
        cmd = [
            cls.FFMPEG_PATH, "-y", "-i", input_path,
            "-filter:a", f"atempo={factor}",
            "-ar", "44100", "-loglevel", "error",
            output_path
        ]
        subprocess.run(cmd, check=True)
        return output_path

    @classmethod
    def concat_audios(cls, audio_paths, output_path):
        """Joins multiple audio files into one."""
        combined = AudioSegment.empty()
        for path in audio_paths:
            combined += AudioSegment.from_file(path)
        combined.export(output_path, format="wav")
        return output_path

# --- 2. THE SYNTHESIS SERVICES (Kokoro & Microsoft) ---
class TTSServices:
    @staticmethod
    def generate_kokoro(text, voice="af_heart", speed=1.0):
        """Simulated Kokoro call (requires 'kokoro' library installed locally)."""
        try:
            from kokoro import KPipeline
            pipeline = KPipeline(lang_code='a')
            # Actual implementation would save to a temp file
            temp_file = f"temp_{uuid.uuid4().hex}.wav"
            # ... synthesis logic ...
            return temp_file
        except ImportError:
            return None # Fallback trigger

    @staticmethod
    async def generate_microsoft(text, voice="en-US-AvaMultilingualNeural", save_path="temp.mp3"):
        """Cloud-based Edge TTS synthesis."""
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(save_path)
        return save_path

# --- 3. THE SYNC & DUBBING ENGINE (from dubbing_engine.py) ---
class TTSOrchestrator:
    def __init__(self, target_lang="English"):
        self.target_lang = target_lang

    def synthesize_segment(self, text, gender, target_path, expected_duration):
        """
        Main Engine Logic:
        1. Pick Engine (Kokoro or Microsoft)
        2. Generate Raw Audio
        3. Compare length to expected video duration
        4. Speed up/slow down to fit (Elastic Sync)
        """
        # A. Pick Voice
        voice = "am_adam" if gender == "Male" else "af_heart"
        
        # B. Synthesize Raw (Microsoft fallback example)
        raw_path = f"raw_{uuid.uuid4().hex}.mp3"
        asyncio.run(TTSServices.generate_microsoft(text, save_path=raw_path))
        
        # C. Elastic Speed Engine (Synchronizing to video timing)
        raw_audio = AudioSegment.from_file(raw_path)
        actual_dur = len(raw_audio) / 1000.0  # seconds
        
        if expected_duration > 0:
            stretch_factor = actual_dur / expected_duration
            
            # If the audio is too long (> 50ms difference), we stretch it
            if abs(actual_dur - expected_duration) > 0.05:
                print(f"⏳ Syncing: {actual_dur:.2f}s -> {expected_duration:.2f}s ({stretch_factor:.2f}x)")
                MediaUtils.change_speed(raw_path, target_path, stretch_factor)
            else:
                raw_audio.export(target_path, format="wav")
        
        return target_path

# --- 4. SRT PROCESSOR (Final Workflow) ---
class SRTDubbing:
    @staticmethod
    def parse_srt(srt_content):
        """Extracts text, speaker, and timestamps from SRT."""
        entries = []
        # Basic parsing logic for entries...
        # Each entry: {'text': '...', 'start': 0.0, 'end': 2.5, 'gender': 'Male'}
        return entries

    def process_full_video(self, srt_path, output_dub_path):
        orchestrator = TTSOrchestrator()
        result = self.parse_srt(open(srt_path).read())
        
        final_pieces = []
        last_end_time = 0
        
        for i, entry in enumerate(result):
            # 1. Handle Silence/Pause between segments
            pause_dur = (entry['start'] - last_end_time) * 1000
            if pause_dur > 0:
                silence = AudioSegment.silent(duration=int(pause_dur))
                silence_path = f"pause_{i}.wav"
                silence.export(silence_path, format="wav")
                final_pieces.append(silence_path)

            # 2. Synthesize & Sync Speech
            speech_path = f"speech_{i}.wav"
            expected_dur = entry['end'] - entry['start']
            orchestrator.synthesize_segment(entry['text'], entry['gender'], speech_path, expected_dur)
            final_pieces.append(speech_path)
            
            last_end_time = entry['end']

        # 3. Final Concatenation
        MediaUtils.concat_audios(final_pieces, output_dub_path)
        return output_dub_path

# --- HOW TO RUN ---
# dub_engine = SRTDubbing()
# dub_engine.process_full_video("subtitles.srt", "final_dubbed_audio.wav")



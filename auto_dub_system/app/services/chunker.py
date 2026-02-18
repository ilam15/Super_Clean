import os
import subprocess
import shutil
import numpy as np
import torch
import librosa
import soundfile as sf

from pydub import AudioSegment
from pydub.silence import split_on_silence
from collections import Counter, defaultdict
from types import SimpleNamespace


# =========================================================
# CORE ENGINE
# =========================================================

class ChunkingManager:

    FFMPEG = "ffmpeg"

    # -----------------------------------------------------
    # INIT
    # -----------------------------------------------------
    @classmethod
    def initialize(cls):
        if not shutil.which("ffmpeg"):
            try:
                import static_ffmpeg
                static_ffmpeg.add_paths()
            except:
                pass
        cls.FFMPEG = shutil.which("ffmpeg") or "ffmpeg"


    # =====================================================
    # UNIVERSAL AUDIO GENERATOR (STREAM + SEGMENT + ASR)
    # =====================================================
    @classmethod
    def audio_chunks(cls, source, sr=16000, chunk_sec=5, start=None, duration=None):

        if not os.path.exists(source):
            raise FileNotFoundError(source)

        cmd = [cls.FFMPEG, "-loglevel", "error"]

        if start:
            cmd += ["-ss", str(start)]

        cmd += ["-i", source]

        if duration:
            cmd += ["-t", str(duration)]

        cmd += ["-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "pipe:1"]

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        size = sr * chunk_sec * 2

        while True:
            raw = p.stdout.read(size)
            if not raw:
                break
            yield np.frombuffer(raw, np.int16).astype(np.float32) / 32768


    # =====================================================
    # SEGMENT NUMPY (PRECISE CLIP EXTRACTION)
    # =====================================================
    @classmethod
    def segment_numpy(cls, source, start, duration=None, sr=16000):
        chunks = list(
            cls.audio_chunks(
                source,
                sr,
                chunk_sec=duration or 600,
                start=start,
                duration=duration
            )
        )
        return np.concatenate(chunks) if chunks else np.array([], np.float32)


    # =====================================================
    # ASR CHUNKING
    # =====================================================
    @staticmethod
    def asr(audio, model, src_lang="auto", device="cpu"):

        sr = 16000
        dur = len(audio) / sr
        win = 20 if dur > 60 else 10
        step = win * sr

        segs = []
        infos = []

        for i in range(0, len(audio), step):

            chunk = audio[i:i + step]
            if len(chunk) < 8000:
                continue

            offset = i / sr

            out, info = model.transcribe(
                chunk,
                vad_filter=True,
                language=None if src_lang == "auto" else src_lang,
                beam_size=5 if device == "cuda" else 2,
                word_timestamps=True
            )

            infos.append(info)

            for s in out:
                segs.append(SimpleNamespace(
                    start=s.start + offset,
                    end=s.end + offset,
                    text=s.text,
                    words=s.words,
                    segment_language=info.language,
                    segment_language_prob=info.language_probability
                ))

        return segs


    # =====================================================
    # SPEAKER GROUPING
    # =====================================================
    @staticmethod
    def speakers(audio, diarizer, gender_model, min_sec=2.5):

        wav = torch.from_numpy(audio).float().unsqueeze(0)
        diar = diarizer({"waveform": wav, "sample_rate": 16000})

        sr = 16000
        turns = []
        bank = {}

        for t, _, spk in diar.itertracks(yield_label=True):
            turns.append({"start": t.start, "end": t.end, "speaker": spk})
            seg = audio[int(t.start * sr):int(t.end * sr)]
            if len(seg) > 0:
                bank.setdefault(spk, []).append(seg)

        genders = {}

        for spk, chunks in bank.items():
            merged = np.concatenate(chunks)
            if len(merged) < sr * min_sec:
                genders[spk] = "Unknown"
                continue
            r = gender_model.predict(merged)
            genders[spk] = r.get("gender", "Unknown").capitalize()

        return turns, genders


    # =====================================================
    # SILENCE REMOVAL
    # =====================================================
    @staticmethod
    def remove_silence(in_path, out_path, min_len=100, thresh=-45, keep=50):

        snd = AudioSegment.from_file(in_path)
        parts = split_on_silence(snd, min_len, thresh, keep)
        out = sum(parts, AudioSegment.empty())
        out.set_frame_rate(24000).set_channels(1).export(out_path, format="wav")
        return out_path


    @staticmethod
    def trim_edges(path):
        y, sr = librosa.load(path)
        y, _ = librosa.effects.trim(y, top_db=60)
        new = path.replace(".wav", "_trim.wav")
        sf.write(new, y, sr)
        return new


    # =====================================================
    # LAYER 3: CHUNK → SEGMENTS
    # =====================================================
    @classmethod
    def chunk_to_segments(cls, chunks_data, output_folder="segments"):
        """
        Groups chunk-level outputs by speaker
        and merges them into segment files.
        """

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Group by segment to preserve timeline
        segment_groups = defaultdict(list)
        for chunk in chunks_data:
            # Fallback to speaker_no if segment_id is missing
            sid = chunk.get("segment_id", f"s_{chunk['speaker_no']}")
            segment_groups[sid].append(chunk)

        segment_outputs = []

        # Merge per segment
        for sid, chunks in segment_groups.items():

            chunks = sorted(
                chunks,
                key=lambda x: x["start_time"]
            )

            speaker_no = chunks[0]["speaker_no"]

            segment_path = os.path.join(
                output_folder,
                f"segment_{sid}.wav"
            )

            temp_file = os.path.join(output_folder, f"chunk_list_{sid}.txt")

            with open(temp_file, "w") as f:
                for chunk in chunks:
                    path = chunk.get('audio_path')
                    if not path or not os.path.exists(path):
                        # Create a silence file if TTS failed
                        silence_dur = max(chunk["end_time"] - chunk["start_time"], 0.1)
                        silence_path = os.path.abspath(os.path.join(output_folder, f"silence_{sid}_{chunks.index(chunk)}.wav"))
                        
                        # Generate silence using FFmpeg
                        command_silence = [
                            cls.FFMPEG,
                            "-f", "lavfi",
                            "-i", f"anullsrc=r=22050:cl=mono",
                            "-t", str(silence_dur),
                            "-y",
                            silence_path
                        ]
                        subprocess.run(command_silence, check=True, capture_output=True)
                        path = silence_path
                    
                    f.write(f"file '{os.path.abspath(path)}'\n")

            command = [
                cls.FFMPEG,
                "-f", "concat",
                "-safe", "0",
                "-i", temp_file,
                "-acodec", "pcm_s16le",
                "-ar", "22050",
                "-ac", "1",
                "-y",
                segment_path
            ]

            subprocess.run(command, check=True)
            
            # Clean up silence files created for this segment
            # (In a production system you might want to cache these, but for now we clean up)
            with open(temp_file, "r") as f:
                for line in f:
                    if "silence_" in line:
                        sil_path = line.strip().split("'")[1]
                        if os.path.exists(sil_path):
                            try: os.remove(sil_path)
                            except: pass

            os.remove(temp_file)

            segment_outputs.append({
                "segment_path": segment_path,
                "start_time": chunks[0]["start_time"],
                "end_time": chunks[-1]["end_time"],
                "speaker_no": speaker_no,
                "overlap": chunks[0].get("overlap", False),
                "segment_id": sid
            })

        return segment_outputs

    # =====================================================
    # LAYER 3: FINAL AUDIO CONNECT
    # =====================================================
    @classmethod
    def final_audio_connect(cls, segments_data, output_path="final_audio.wav"):
        """
        Merges all segment files into one final audio file
        in timeline order.
        """

        if not segments_data:
            raise ValueError("No segment data provided")

        # 1️⃣ Sort segments by start time
        segments_data = sorted(
            segments_data,
            key=lambda x: x["start_time"]
        )

        temp_file = "segment_list.txt"

        # 2️⃣ Create FFmpeg concat list
        with open(temp_file, "w") as f:
            for segment in segments_data:
                f.write(
                    f"file '{os.path.abspath(segment['segment_path'])}'\n"
                )

        # 3️⃣ Run FFmpeg merge
        command = [
            cls.FFMPEG,
            "-f", "concat",
            "-safe", "0",
            "-i", temp_file,
            "-acodec", "pcm_s16le",
            "-ar", "22050",
            "-ac", "1",
            "-y",
            output_path
        ]

        subprocess.run(command, check=True)

        # 4️⃣ Remove temp file
        os.remove(temp_file)

        return output_path

    # =====================================================
    # LAYER 3: FINAL VIDEO CONNECT
    # =====================================================
    @classmethod
    def final_connect_with_video(
        cls,
        final_audio_path,
        video_path,
        output_path="final_video.mp4"
    ):
        """
        Replaces original audio with dubbed audio.
        """

        command = [
            cls.FFMPEG,
            "-y",  # auto overwrite
            "-i", video_path,
            "-i", final_audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            output_path
        ]

        subprocess.run(command, check=True)

        return output_path


    # =====================================================
    # LAYER 1: CHUNK SEPARATION
    # =====================================================
    @classmethod
    def chunk_separation(cls, segment_path, start, end, speaker_no, overlap, segment_id=None, chunk_sec=5):
        """
        Splits a segment into smaller fixed-size chunks (e.g., 5s)
        Returns list of chunk metadata.
        """
        import soundfile as sf
        
        if not os.path.exists(segment_path):
            raise FileNotFoundError(segment_path)
            
        chunks_metadata = []
        
        # Load audio (using librosa or soundfile)
        # Using librosa for consistency or static ffmpeg
        # Let's use ffmpeg based generator for efficiency or just pydub/librosa for simplicity
        # implementation using existing audio_chunks generator
        
        # audio_chunks yields numpy arrays
        sr = 16000
        gen = cls.audio_chunks(segment_path, sr=sr, chunk_sec=chunk_sec)
        
        base_name = os.path.splitext(os.path.basename(segment_path))[0]
        output_dir = os.path.dirname(segment_path)
        
        current_time = start
        
        for i, audio_data in enumerate(gen):
            chunk_dur = len(audio_data) / sr
            chunk_filename = f"{base_name}_chunk_{i:04d}.wav"
            chunk_path = os.path.join(output_dir, chunk_filename)
            
            # Save chunk
            sf.write(chunk_path, audio_data, sr)
            
            chunks_metadata.append({
                "chunk_path": chunk_path,
                "start_time": round(current_time, 3),
                "end_time": round(current_time + chunk_dur, 3),
                "speaker_no": speaker_no,
                "overlap": overlap,
                "segment_id": segment_id
            })
            
            current_time += chunk_dur
            
        return chunks_metadata


# Standalone wrapper to match import in stage1_tasks
def chunk_separation(segment_path, start, end, speaker_no, overlap, segment_id=None):
    return ChunkingManager.chunk_separation(segment_path, start, end, speaker_no, overlap, segment_id)

# auto init
ChunkingManager.initialize()

"""
PRODUCTION AUDIO EXTRACTOR
Unified FFmpeg audio decoding engine
Supports file | numpy | stream | raw | segments | cache
"""

import subprocess
import numpy as np
import os
import shutil


class AudioExtractor:
    FFMPEG = "ffmpeg"

    # ---------------------------------------------------------
    # INITIALIZER (detect ffmpeg or static-ffmpeg)
    # ---------------------------------------------------------
    @classmethod
    def initialize(cls):
        if not shutil.which("ffmpeg"):
            try:
                import static_ffmpeg
                static_ffmpeg.add_paths()
            except ImportError:
                raise RuntimeError("FFmpeg not found. Install ffmpeg or static-ffmpeg.")

        cls.FFMPEG = shutil.which("ffmpeg") or "ffmpeg"
        print(f"✓ Using FFmpeg: {cls.FFMPEG}")

    # ---------------------------------------------------------
    # INTERNAL COMMAND BUILDER
    # ---------------------------------------------------------
    @staticmethod
    def _cmd(video, sr, start=None, dur=None, pipe=True):

        cmd = [AudioExtractor.FFMPEG, "-hide_banner", "-loglevel", "quiet"]

        if start is not None:
            cmd += ["-ss", str(start)]

        cmd += ["-i", video]

        if dur is not None:
            cmd += ["-t", str(dur)]

        cmd += [
            "-vn",
            "-ac", "1",
            "-ar", str(sr),
            "-f", "s16le",
            "-threads", "1"
        ]

        if pipe:
            cmd += ["pipe:1"]

        return cmd

    # ---------------------------------------------------------
    # MASTER EXTRACTION FUNCTION
    # ---------------------------------------------------------
    @classmethod
    def extract(
        cls,
        video_path,
        mode="numpy",            # numpy | file | stream | raw
        sample_rate=16000,
        start=None,
        duration=None,
        outfile=None,
        chunk_size=65536
    ):

        if not os.path.exists(video_path):
            raise FileNotFoundError(video_path)

        # ---------------- FILE OUTPUT MODE ----------------
        if mode == "file":
            if not outfile:
                raise ValueError("outfile required for file mode")

            cmd = cls._cmd(video_path, sample_rate, start, duration, pipe=False)
            cmd.append(outfile)

            subprocess.run(cmd, check=True)
            return outfile

        # ---------------- PIPE MODES ----------------
        cmd = cls._cmd(video_path, sample_rate, start, duration, pipe=True)
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

        # STREAM MODE
        if mode == "stream":
            def generator():
                while True:
                    chunk = process.stdout.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
                process.wait()
            return generator()

        # RAW MODE
        if mode == "raw":
            data = process.stdout.read()
            process.wait()
            return data

        # NUMPY MODE (default)
        raw = process.stdout.read()
        process.wait()

        audio = np.frombuffer(raw, np.int16).astype(np.float32)
        audio *= (1.0 / 32768.0)
        return audio

    # ---------------------------------------------------------
    # FAST FULL DECODE (BEST FOR MULTI SEGMENT WORK)
    # ---------------------------------------------------------
    @classmethod
    def decode_full(cls, video_path, sr=16000):
        return cls.extract(video_path, mode="numpy", sample_rate=sr)

    # ---------------------------------------------------------
    # SEGMENT FROM BUFFER (INSTANT)
    # ---------------------------------------------------------
    @staticmethod
    def segment_from_buffer(audio, sr, start, dur):
        s = int(start * sr)
        e = s + int(dur * sr)
        return audio[s:e]


# =============================================================
# EXAMPLE USAGE
# =============================================================
if __name__ == "__main__":

    AudioExtractor.initialize()

    video = "video.mp4"

    # -------- FULL AUDIO NUMPY ----------
    audio = AudioExtractor.extract(video)
    print("Audio samples:", len(audio))

    # -------- SEGMENT EXTRACTION ----------
    segment = AudioExtractor.extract(video, start=5, duration=2)
    print("Segment samples:", len(segment))

    # -------- SAVE FILE ----------
    AudioExtractor.extract(video, mode="file", outfile="audio.raw")

    # -------- STREAM ----------
    print("Streaming first chunks...")
    for i, chunk in enumerate(AudioExtractor.extract(video, mode="stream")):
        print("chunk", i, len(chunk))
        if i == 3:
            break

    # -------- FAST MULTI SEGMENT WORKFLOW ----------
    print("\nFast segment pipeline")
    full_audio = AudioExtractor.decode_full(video)

    seg1 = AudioExtractor.segment_from_buffer(full_audio, 16000, 3, 2)
    seg2 = AudioExtractor.segment_from_buffer(full_audio, 16000, 7, 1)

    print("Seg1:", len(seg1))
    print("Seg2:", len(seg2))

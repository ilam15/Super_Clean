"""
SEGMENT SEPARATION ENGINE — OPTIMIZED VERSION
Time-based FFmpeg slicing using diarization timestamps
"""

import os
import subprocess
import shutil
from typing import List, Dict, Tuple, Optional


class SegmentSeparator:
    FFMPEG = "ffmpeg"

    # ---------------------------------------------------------
    # INITIALIZE FFMPEG
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

    # ---------------------------------------------------------
    # VALIDATE TIMESTAMPS
    # ---------------------------------------------------------
    @staticmethod
    def _valid_timestamp(start: float, end: float) -> bool:
        if start < 0:
            return False
        if end <= start:
            return False
        return True

    # ---------------------------------------------------------
    # BUILD FFMPEG COMMAND
    # ---------------------------------------------------------
    @classmethod
    def _cmd(
        cls,
        input_audio: str,
        start: float,
        duration: float,
        out_path: str,
        sample_rate: int,
        channels: int
    ):
        return [
            cls.FFMPEG,
            "-hide_banner",
            "-loglevel", "error",
            "-ss", str(start),
            "-i", input_audio,
            "-t", str(duration),
            "-ac", str(channels),
            "-ar", str(sample_rate),
            "-vn",
            "-y",
            out_path
        ]

    # ---------------------------------------------------------
    # SAFE FFMPEG EXECUTION
    # ---------------------------------------------------------
    @staticmethod
    def _run_ffmpeg(cmd: List[str], retries: int = 2) -> bool:
        for _ in range(retries + 1):
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                return True
            except subprocess.CalledProcessError:
                continue
        return False

    # ---------------------------------------------------------
    # MAIN FUNCTION
    # ---------------------------------------------------------
    @classmethod
    def segment_separation(
        cls,
        audio_path: str,
        timestamps: List[Tuple[float, float]],
        speaker_labels: List[str],
        overlap_flags: List[bool],
        output_dir: str = "segments",
        padding: float = 0.10,
        sample_rate: int = 16000,
        channels: int = 1,
        skip_overlaps: bool = False,
        min_duration: float = 0.15
    ) -> List[Dict]:
        """
        Returns list of segment metadata dictionaries.
        """

        cls.initialize()

        if not os.path.exists(audio_path):
            raise FileNotFoundError(audio_path)

        if not (len(timestamps) == len(speaker_labels) == len(overlap_flags)):
            raise ValueError("timestamps, speakers, overlap lists must be same length")

        os.makedirs(output_dir, exist_ok=True)
        results = []

        for idx, ((start, end), speaker, overlap) in enumerate(
            zip(timestamps, speaker_labels, overlap_flags)
        ):

            # Skip overlaps if requested
            if overlap and skip_overlaps:
                continue

            # Validate timestamps
            if not cls._valid_timestamp(start, end):
                continue

            # Padding
            start = max(0, start - padding)
            end += padding

            duration = end - start

            # Skip too small segments
            if duration < min_duration:
                continue

            outfile = os.path.join(
                output_dir,
                f"seg_{idx:04d}_{speaker}.wav"
            )

            cmd = cls._cmd(
                input_audio=audio_path,
                start=start,
                duration=duration,
                out_path=outfile,
                sample_rate=sample_rate,
                channels=channels
            )

            success = cls._run_ffmpeg(cmd)

            # Skip failed segments
            if not success:
                continue

            # Validate output file
            if not os.path.exists(outfile) or os.path.getsize(outfile) == 0:
                continue

            results.append({
                "segment_path": outfile,
                "start_time": round(start, 3),
                "end_time": round(end, 3),
                "speaker_no": speaker,
                "overlap": overlap,
                "duration": round(duration, 3)
            })

        return results

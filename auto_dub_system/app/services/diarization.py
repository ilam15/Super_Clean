"""
Speaker Diarization Module
Input: full_audio_path
Output: timestamps + speaker_labels + speaker_count + overlap
"""

import logging
import warnings
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json

# Suppress noisy warnings
warnings.filterwarnings("ignore", category=UserWarning)

logger = logging.getLogger(__name__)

# Singleton instance (per worker process)
_diarizer_instance = None


# ============================================================================
# Factory (Singleton)
# ============================================================================

def get_diarizer(
    model: str = "pyannote/speaker-diarization-3.1",
    token: Optional[str] = None,
    device: str = "cpu",
):
    global _diarizer_instance
    if _diarizer_instance is None:
        _diarizer_instance = SpeakerDiarizer(model, token, device)
    return _diarizer_instance


# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class SpeakerSegment:
    start_time: float
    end_time: float
    speaker_label: str
    overlap: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class DiarizationResult:
    timestamps: List[Tuple[float, float]]
    speaker_labels: List[str]
    speaker_count: int
    overlap: bool
    segments: List[SpeakerSegment]

    def to_dict(self) -> dict:
        return {
            "timestamps": self.timestamps,
            "speaker_labels": self.speaker_labels,
            "speaker_count": self.speaker_count,
            "overlap": self.overlap,
            "segments": [s.to_dict() for s in self.segments],
        }

    def save_json(self, path: str):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))


class SpeakerDiarizationError(Exception):
    pass


# ============================================================================
# Core Diarizer
# ============================================================================

class SpeakerDiarizer:
    def __init__(
        self,
        model: str = "pyannote/speaker-diarization-3.1",
        token: Optional[str] = None,
        device: str = "cpu",
    ):
        try:
            from pyannote.audio import Pipeline
            import torch
            import inspect

            # Handle token argument compatibility
            sig = inspect.signature(Pipeline.from_pretrained)
            if "token" in sig.parameters:
                self.pipeline = Pipeline.from_pretrained(model, token=token)
            else:
                self.pipeline = Pipeline.from_pretrained(
                    model, use_auth_token=token
                )

            dev = torch.device(
                "cuda" if device == "cuda" and torch.cuda.is_available() else "cpu"
            )

            self.pipeline = self.pipeline.to(dev)

            logger.info(f"Pyannote pipeline loaded on {dev}")
            print(f"INFO: Pyannote Diarization Model ({model}) ACTIVE on {dev}")

        except ImportError:
            raise SpeakerDiarizationError(
                "Missing dependency. Install: pip install pyannote.audio torch"
            )
        except Exception as e:
            raise SpeakerDiarizationError(f"Initialization failed: {e}")

    # ---------------------------------------------------------------------

    def _find_overlaps(self, diarization) -> List[Tuple[float, float]]:
        overlaps = set()
        tracks = list(diarization.itertracks(yield_label=True))

        for i, (seg1, _, _) in enumerate(tracks):
            for seg2, _, _ in tracks[i + 1 :]:
                start = max(seg1.start, seg2.start)
                end = min(seg1.end, seg2.end)
                if end > start:
                    overlaps.add((start, end))

        return sorted(overlaps)

    # ---------------------------------------------------------------------

    def _build_segments(self, diarization, overlaps) -> List[SpeakerSegment]:
        segments = []

        for seg, _, label in diarization.itertracks(yield_label=True):
            has_overlap = False
            for os, oe in overlaps:
                if max(seg.start, os) < min(seg.end, oe):
                    has_overlap = True
                    break

            segments.append(
                SpeakerSegment(
                    start_time=seg.start,
                    end_time=seg.end,
                    speaker_label=label,
                    overlap=has_overlap,
                )
            )

        return segments

    # ---------------------------------------------------------------------

    def process(self, audio_path: str) -> DiarizationResult:
        """
        Run diarization directly on file path.
        No torchaudio. No torchcodec.
        """
        path = Path(audio_path)

        if not path.is_file():
            raise SpeakerDiarizationError(f"File not found: {audio_path}")

        logger.info(f"Processing: {path.name}")

        try:
            logger.info("Running diarization pipeline...")
            diarization = self.pipeline(str(path))
            logger.info("Pipeline finished.")

            # pyannote >=3 sometimes wraps result
            if not hasattr(diarization, "itertracks") and hasattr(
                diarization, "speaker_diarization"
            ):
                diarization = diarization.speaker_diarization

            overlaps = self._find_overlaps(diarization)
            segments = self._build_segments(diarization, overlaps)

            timestamps = [(s.start_time, s.end_time) for s in segments]
            labels = [s.speaker_label for s in segments]

            result = DiarizationResult(
                timestamps=timestamps,
                speaker_labels=labels,
                speaker_count=len(set(labels)),
                overlap=len(overlaps) > 0,
                segments=segments,
            )

            logger.info(
                f"✓ {result.speaker_count} speakers | "
                f"{len(segments)} segments | overlap: {result.overlap}"
            )

            return result

        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            raise SpeakerDiarizationError(f"Process failed: {e}")


# ============================================================================
# Public API
# ============================================================================

def speaker_diarization(
    full_audio_path: str,
    model_name: str = "pyannote/speaker-diarization-3.1",
    use_auth_token: Optional[str] = None,
    device: str = "cpu",
    save_json: bool = False,
    output_json_path: Optional[str] = None,
) -> Dict:
    diarizer = get_diarizer(model_name, use_auth_token, device)
    result = diarizer.process(full_audio_path)

    if save_json:
        json_path = output_json_path or f"{Path(full_audio_path).stem}_diarization.json"
        result.save_json(json_path)

    return result.to_dict()


# ============================================================================
# CLI (Optional Testing)
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python diarization.py <audio_file> [hf_token]")
        sys.exit(0)

    try:
        result = speaker_diarization(
            full_audio_path=sys.argv[1],
            use_auth_token=sys.argv[2] if len(sys.argv) > 2 else None,
            save_json=True,
        )

        print(
            f"\n✓ Speakers: {result['speaker_count']}, "
            f"Segments: {len(result['segments'])}, "
            f"Overlap: {result['overlap']}"
        )

    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)

"""
Speaker Diarization Module
Input: full_audio_path
Output: timestamps + speaker_labels + speaker_count + overlap
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

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
            "segments": [s.to_dict() for s in self.segments]
        }
    
    def save_json(self, path: str):
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))


class SpeakerDiarizationError(Exception):
    pass


# ============================================================================
# Core Logic
# ============================================================================

class SpeakerDiarizer:
    def __init__(self, model: str = "pyannote/speaker-diarization-3.1", 
                 token: Optional[str] = None, device: str = "cpu"):
        try:
            import torchaudio
            import numpy as np

            # Patch for torchaudio >= 2.1 (set_audio_backend was removed)
            if not hasattr(torchaudio, "set_audio_backend"):
                torchaudio.set_audio_backend = lambda x: None

            # Patch for numpy 2.0 (np.NaN was removed)
            if not hasattr(np, "NaN"):
                np.NaN = np.nan

            # Patch huggingface_hub: pyannote internals may still pass use_auth_token
            import huggingface_hub
            if not getattr(huggingface_hub, "_patched_for_pyannote", False):
                def _make_patched(original_fn):
                    def patched(*args, **kwargs):
                        if "use_auth_token" in kwargs:
                            kwargs["token"] = kwargs.pop("use_auth_token")
                        return original_fn(*args, **kwargs)
                    return patched

                huggingface_hub.hf_hub_download = _make_patched(huggingface_hub.hf_hub_download)
                if hasattr(huggingface_hub, "snapshot_download"):
                    huggingface_hub.snapshot_download = _make_patched(huggingface_hub.snapshot_download)
                huggingface_hub._patched_for_pyannote = True

            from pyannote.audio import Pipeline
            import torch
            import inspect

            # pyannote >= 3.x renamed use_auth_token → token in Pipeline.from_pretrained
            pretrained_sig = inspect.signature(Pipeline.from_pretrained)
            if "token" in pretrained_sig.parameters:
                self.pipeline = Pipeline.from_pretrained(model, token=token)
            else:
                # Older pyannote still uses use_auth_token
                self.pipeline = Pipeline.from_pretrained(model, use_auth_token=token)

            dev = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
            self.pipeline = self.pipeline.to(dev)
            logger.info(f"Pipeline ready on {dev}")
        except ImportError:
            raise SpeakerDiarizationError("Install: pip install pyannote.audio torch torchaudio")
        except Exception as e:
            raise SpeakerDiarizationError(f"Init failed: {e}")
    
    def _find_overlaps(self, diarization) -> List[Tuple[float, float]]:
        overlaps = set()
        tracks = list(diarization.itertracks(yield_label=True))
        for i, (s1, _, _) in enumerate(tracks):
            for s2, _, _ in tracks[i+1:]:
                if s1.overlaps(s2):
                    start, end = max(s1.start, s2.start), min(s1.end, s2.end)
                    if end > start:
                        overlaps.add((start, end))
        return sorted(overlaps)
    
    def _build_segments(self, diarization, overlaps) -> List[SpeakerSegment]:
        segments = []
        for seg, _, label in diarization.itertracks(yield_label=True):
            has_overlap = any(not (seg.end <= os or seg.start >= oe) for os, oe in overlaps)
            segments.append(SpeakerSegment(seg.start, seg.end, label, has_overlap))
        return segments
    
    def process(self, audio_path: str) -> DiarizationResult:
        path = Path(audio_path)
        if not path.is_file():
            raise SpeakerDiarizationError(f"File not found: {audio_path}")
        
        logger.info(f"Processing: {path.name}")
        diarization = self.pipeline(str(path))
        overlaps = self._find_overlaps(diarization)
        segments = self._build_segments(diarization, overlaps)
        
        timestamps = [(s.start_time, s.end_time) for s in segments]
        labels = [s.speaker_label for s in segments]
        
        result = DiarizationResult(
            timestamps=timestamps,
            speaker_labels=labels,
            speaker_count=len(set(labels)),
            overlap=len(overlaps) > 0,
            segments=segments
        )
        
        logger.info(f"✓ {result.speaker_count} speakers, {len(segments)} segments, overlap: {result.overlap}")
        return result


# ============================================================================
# Main Interface
# ============================================================================

def speaker_diarization(full_audio_path: str,
                       model_name: str = "pyannote/speaker-diarization-3.1",
                       use_auth_token: Optional[str] = None,
                       device: str = "cpu",
                       save_json: bool = False,
                       output_json_path: Optional[str] = None) -> Dict:
    """
    Perform speaker diarization with overlap detection.
    
    Returns: {timestamps, speaker_labels, speaker_count, overlap, segments}
    """
    diarizer = SpeakerDiarizer(model_name, use_auth_token, device)
    result = diarizer.process(full_audio_path)
    
    if save_json:
        json_path = output_json_path or f"{Path(full_audio_path).stem}_diarization.json"
        result.save_json(json_path)
    
    return result.to_dict()


def check_dependencies() -> Dict[str, bool]:
    deps = {}
    for pkg in ['pyannote.audio', 'torch', 'torchaudio']:
        try:
            __import__(pkg.replace('.', '_') if '.' in pkg else pkg)
            deps[pkg] = True
        except ImportError:
            deps[pkg] = False
    return deps


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    deps = check_dependencies()
    if not all(deps.values()):
        print("❌ Install: pip install pyannote.audio torch torchaudio")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("Usage: python speaker_diarization.py <audio_file> [hf_token]")
        sys.exit(0)
    
    try:
        result = speaker_diarization(
            full_audio_path=sys.argv[1],
            use_auth_token=sys.argv[2] if len(sys.argv) > 2 else None,
            save_json=True
        )
        print(f"\n✓ Speakers: {result['speaker_count']}, Segments: {len(result['segments'])}, Overlap: {result['overlap']}")
        for seg in result['segments'][:5]:
            print(f"  [{seg['start_time']:.2f}s-{seg['end_time']:.2f}s] {seg['speaker_label']}" + 
                  (" ⚠️" if seg['overlap'] else ""))
    except Exception as e:
        print(f"❌ {e}")
        sys.exit(1)

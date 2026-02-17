"""
Overlapping Audio Split Module (Conditional)
Input: timestamps + speaker_count + audio_path + overlap
Output: separated_audio_paths
Condition: Only runs if overlap == True
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class AudioSplitError(Exception):
    pass


# ============================================================================
# Main Function
# ============================================================================

def overlapping_audio_split(timestamps: List[Tuple[float, float]],
                           speaker_count: int,
                           audio_path: str,
                           overlap: bool,
                           output_dir: Optional[str] = None,
                           method: str = "demucs") -> List[str]:
    """
    Conditionally split overlapping audio. Only runs if overlap == True.
    Returns: separated_audio_paths or [] if no overlap
    """
    if not overlap:
        logger.info("⏭️  No overlap - skipping")
        return []
    
    logger.info(f"⚠️  Separating {speaker_count} speakers")
    
    path = Path(audio_path)
    if not path.is_file():
        raise AudioSplitError(f"Audio not found: {audio_path}")
    
    out_dir = Path(output_dir) if output_dir else path.parent / "separated"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if method == "demucs":
        return _demucs(path, out_dir)
    elif method == "spleeter":
        return _spleeter(path, out_dir, speaker_count)
    else:
        raise AudioSplitError(f"Unknown method: {method}")


# ============================================================================
# Separation Methods
# ============================================================================

def _demucs(audio: Path, out_dir: Path) -> List[str]:
    """Demucs separation"""
    try:
        cmd = ["demucs", "-n", "htdemucs", "--two-stems", "vocals",
               "-o", str(out_dir), str(audio)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        vocals = out_dir / "htdemucs" / audio.stem / "vocals.wav"
        if not vocals.exists():
            raise AudioSplitError("No output created")
        
        result = [str(vocals)]
        logger.info(f"✓ Demucs: {len(result)} files")
        return result
        
    except FileNotFoundError:
        raise FileNotFoundError("Install: pip install demucs")
    except subprocess.CalledProcessError as e:
        raise AudioSplitError(f"Demucs failed: {e.stderr}")


def _spleeter(audio: Path, out_dir: Path, speakers: int) -> List[str]:
    """Spleeter separation"""
    try:
        stems = min(max(speakers, 2), 5)
        cmd = ["spleeter", "separate", "-p", f"spleeter:{stems}stems",
               "-o", str(out_dir), str(audio)]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        result = sorted([str(f) for f in (out_dir / audio.stem).glob("*.wav")])
        if not result:
            raise AudioSplitError("No output created")
        
        logger.info(f"✓ Spleeter: {len(result)} files")
        return result
        
    except FileNotFoundError:
        raise FileNotFoundError("Install: pip install spleeter")
    except subprocess.CalledProcessError as e:
        raise AudioSplitError(f"Spleeter failed: {e.stderr}")


def check_separation_tools() -> dict:
    """Check available tools"""
    tools = {}
    for tool in ['demucs', 'spleeter']:
        try:
            subprocess.run([tool, "--help"], capture_output=True, check=True)
            tools[tool] = True
        except:
            tools[tool] = False
    return tools


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    tools = check_separation_tools()
    if not any(tools.values()):
        print("❌ Install: pip install demucs  OR  pip install spleeter")
        sys.exit(1)
    
    if len(sys.argv) < 3:
        print("Usage: python overlapping_audio_split.py <audio_file> <overlap_bool>")
        print("Example: python overlapping_audio_split.py audio.wav true")
        sys.exit(0)
    
    try:
        separated_audio_paths = overlapping_audio_split(
            timestamps=[(0.0, 2.5), (2.5, 5.0)],
            speaker_count=2,
            audio_path=sys.argv[1],
            overlap=sys.argv[2].lower() == "true",
            method="demucs" if tools['demucs'] else "spleeter"
        )
        
        if separated_audio_paths:
            print(f"\n✓ Separated: {len(separated_audio_paths)} files")
            for p in separated_audio_paths:
                print(f"  - {p}")
        else:
            print("\n✓ No separation needed")
        
    except Exception as e:
        print(f"\n❌ {e}")
        sys.exit(1)

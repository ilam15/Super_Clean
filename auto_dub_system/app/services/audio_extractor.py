"""
Audio Separator Module
Input: video_path
Output: audio_path
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ============================================================================
# Exception
# ============================================================================

class AudioSeparatorError(Exception):
    pass


# ============================================================================
# Core Logic
# ============================================================================

def audio_separator(video_path: str,
                   output_dir: Optional[str] = None,
                   output_format: str = "wav",
                   audio_codec: str = "pcm_s16le",
                   sample_rate: int = 16000,
                   channels: int = 1,
                   overwrite: bool = False) -> str:
    """
    Extract audio from video using FFmpeg.
    
    Returns: Path to extracted audio file
    """
    # Validate input
    video_path = Path(video_path)
    if not video_path.is_file():
        raise AudioSeparatorError(f"Video file not found: {video_path}")
    
    # Determine output path
    output_dir = Path(output_dir) if output_dir else video_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_path = output_dir / f"{video_path.stem}_audio.{output_format}"
    
    # Check if already exists
    if audio_path.exists() and not overwrite:
        logger.warning(f"Audio exists: {audio_path} (set overwrite=True to regenerate)")
        return str(audio_path)
    
    # Build FFmpeg command
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", audio_codec,
        "-ar", str(sample_rate),
        "-ac", str(channels),
        "-y" if overwrite else "-n",
        str(audio_path)
    ]
    
    try:
        logger.info(f"Extracting audio: {video_path.name} → {audio_path.name}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        if not audio_path.exists():
            raise AudioSeparatorError("FFmpeg completed but output file not created")
        
        logger.info(f"✓ Audio extracted: {audio_path}")
        return str(audio_path)
        
    except FileNotFoundError:
        raise FileNotFoundError("FFmpeg not installed. Install: winget install ffmpeg")
    except subprocess.CalledProcessError as e:
        raise AudioSeparatorError(f"FFmpeg error: {e.stderr}")
    except Exception as e:
        raise AudioSeparatorError(f"Extraction failed: {e}")


def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is available"""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_audio_info(video_path: str) -> dict:
    """Get audio metadata from video file"""
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels,duration",
            "-of", "default=noprint_wrappers=1",
            str(video_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        info = dict(line.split('=', 1) for line in result.stdout.strip().split('\n') if '=' in line)
        return {
            "codec": info.get("codec_name", "unknown"),
            "sample_rate": int(info.get("sample_rate", 0)),
            "channels": int(info.get("channels", 0)),
            "duration": float(info.get("duration", 0.0))
        }
    except Exception as e:
        raise AudioSeparatorError(f"Failed to get audio info: {e}")


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if not check_ffmpeg_installed():
        print("❌ FFmpeg not installed. Install: winget install ffmpeg")
        sys.exit(1)
    
    print("✓ FFmpeg ready\n")
    
    if len(sys.argv) < 2:
        print("Usage: python audio_separator.py <video_file>")
        print("\nExample:")
        print("  python audio_separator.py video.mp4")
        sys.exit(0)
    
    try:
        video_file = sys.argv[1]
        
        # Show audio info
        print("📊 Audio info:")
        info = get_audio_info(video_file)
        print(f"  Codec: {info['codec']}")
        print(f"  Sample Rate: {info['sample_rate']} Hz")
        print(f"  Channels: {info['channels']}")
        print(f"  Duration: {info['duration']:.2f}s\n")
        
        # Extract audio
        print("🎵 Extracting audio...")
        audio_path = audio_separator(video_file, overwrite=True)
        print(f"\n✓ Success: {audio_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

"""
Audio Separator Module

Function: audio_separator
Input: video_path
Process: FFmpeg
Output: audio_path

This module extracts audio from video files using FFmpeg.
"""

import os
import subprocess
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AudioSeparatorError(Exception):
    """Custom exception for audio separator errors"""
    pass


def audio_separator(
    video_path: str,
    output_dir: Optional[str] = None,
    output_format: str = "wav",
    audio_codec: str = "pcm_s16le",
    sample_rate: int = 16000,
    channels: int = 1,
    overwrite: bool = False
) -> str:
    """
    Extracts audio from a video file using FFmpeg.
    
    Args:
        video_path (str): Path to the input video file
        output_dir (str, optional): Directory to save the extracted audio. 
                                   If None, saves in the same directory as the video.
        output_format (str): Output audio format (default: "wav")
        audio_codec (str): Audio codec to use (default: "pcm_s16le" for WAV)
        sample_rate (int): Audio sample rate in Hz (default: 16000)
        channels (int): Number of audio channels (default: 1 for mono)
        overwrite (bool): Whether to overwrite existing output file (default: False)
    
    Returns:
        str: Path to the extracted audio file
    
    Raises:
        AudioSeparatorError: If video file doesn't exist or FFmpeg fails
        FileNotFoundError: If FFmpeg is not installed/accessible
    
    Example:
        >>> audio_path = audio_separator("input_video.mp4")
        >>> print(f"Audio extracted to: {audio_path}")
    """
    
    # Validate input video path
    video_path = Path(video_path)
    if not video_path.exists():
        raise AudioSeparatorError(f"Video file not found: {video_path}")
    
    if not video_path.is_file():
        raise AudioSeparatorError(f"Path is not a file: {video_path}")
    
    # Determine output directory
    if output_dir is None:
        output_dir = video_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate output audio path
    audio_filename = f"{video_path.stem}_audio.{output_format}"
    audio_path = output_dir / audio_filename
    
    # Check if output file already exists
    if audio_path.exists() and not overwrite:
        logger.warning(f"Audio file already exists: {audio_path}")
        logger.info("Returning existing file path. Set overwrite=True to regenerate.")
        return str(audio_path)
    
    # Build FFmpeg command
    ffmpeg_command = [
        "ffmpeg",
        "-i", str(video_path),           # Input video file
        "-vn",                            # Disable video
        "-acodec", audio_codec,           # Audio codec
        "-ar", str(sample_rate),          # Sample rate
        "-ac", str(channels),             # Number of channels
    ]
    
    if overwrite:
        ffmpeg_command.append("-y")       # Overwrite output file
    else:
        ffmpeg_command.append("-n")       # Do not overwrite
    
    ffmpeg_command.append(str(audio_path))  # Output file
    
    try:
        logger.info(f"Extracting audio from: {video_path}")
        logger.info(f"Output path: {audio_path}")
        logger.info(f"Settings: {output_format}, {sample_rate}Hz, {channels} channel(s)")
        
        # Execute FFmpeg command
        result = subprocess.run(
            ffmpeg_command,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Verify output file was created
        if not audio_path.exists():
            raise AudioSeparatorError("FFmpeg completed but output file was not created")
        
        logger.info(f"✓ Audio extraction successful: {audio_path}")
        return str(audio_path)
    
    except FileNotFoundError:
        raise FileNotFoundError(
            "FFmpeg not found. Please install FFmpeg:\n"
            "  - Windows: Download from https://ffmpeg.org/download.html or use 'winget install ffmpeg'\n"
            "  - Linux: sudo apt-get install ffmpeg\n"
            "  - macOS: brew install ffmpeg"
        )
    
    except subprocess.CalledProcessError as e:
        error_msg = f"FFmpeg error: {e.stderr}"
        logger.error(error_msg)
        raise AudioSeparatorError(error_msg)
    
    except Exception as e:
        logger.error(f"Unexpected error during audio extraction: {str(e)}")
        raise AudioSeparatorError(f"Audio extraction failed: {str(e)}")


def check_ffmpeg_installed() -> bool:
    """
    Check if FFmpeg is installed and accessible.
    
    Returns:
        bool: True if FFmpeg is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def get_audio_info(video_path: str) -> dict:
    """
    Get audio information from a video file using FFprobe.
    
    Args:
        video_path (str): Path to the video file
    
    Returns:
        dict: Audio information including codec, sample_rate, channels, duration
    
    Raises:
        AudioSeparatorError: If FFprobe fails or no audio stream found
    """
    try:
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "a:0",
            "-show_entries", "stream=codec_name,sample_rate,channels,duration",
            "-of", "default=noprint_wrappers=1",
            str(video_path)
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output
        info = {}
        for line in result.stdout.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                info[key] = value
        
        return {
            "codec": info.get("codec_name", "unknown"),
            "sample_rate": int(info.get("sample_rate", 0)),
            "channels": int(info.get("channels", 0)),
            "duration": float(info.get("duration", 0.0))
        }
    
    except subprocess.CalledProcessError:
        raise AudioSeparatorError("No audio stream found in video file")
    except Exception as e:
        raise AudioSeparatorError(f"Failed to get audio info: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Check if FFmpeg is installed
    if not check_ffmpeg_installed():
        print("❌ FFmpeg is not installed. Please install FFmpeg to use this module.")
        sys.exit(1)
    
    print("✓ FFmpeg is installed and accessible\n")
    
    # Example usage
    if len(sys.argv) > 1:
        # Use command line argument as video path
        video_file = sys.argv[1]
        
        try:
            # Get audio info first
            print("📊 Getting audio information...")
            audio_info = get_audio_info(video_file)
            print(f"  Codec: {audio_info['codec']}")
            print(f"  Sample Rate: {audio_info['sample_rate']} Hz")
            print(f"  Channels: {audio_info['channels']}")
            print(f"  Duration: {audio_info['duration']:.2f} seconds\n")
            
            # Extract audio
            print("🎵 Extracting audio...")
            audio_path = audio_separator(
                video_path=video_file,
                output_format="wav",
                sample_rate=16000,
                channels=1,
                overwrite=True
            )
            
            print(f"\n✓ Success! Audio saved to: {audio_path}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    
    else:
        print("Usage: python audio_separator.py <video_file_path>")
        print("\nExample:")
        print("  python audio_separator.py input_video.mp4")
        print("\nThis will extract audio and save it as 'input_video_audio.wav'")

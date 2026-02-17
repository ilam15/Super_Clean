"""
Standalone Audio Extractor
Combines all audio extraction methods from the AutoDub project
"""

import subprocess
import os
import numpy as np
import shutil
from typing import Generator, Optional

class AudioExtractor:
    """
    Standalone audio extraction utility using FFmpeg.
    No dependencies on project-specific modules.
    """
    FFMPEG_PATH = "ffmpeg"
    FFPROBE_PATH = "ffprobe"
    
    @classmethod
    def initialize(cls):
        """Initialize FFmpeg paths (checks system or static-ffmpeg)."""
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            try:
                import static_ffmpeg
                print("System ffmpeg not found, using static-ffmpeg...")
                static_ffmpeg.add_paths()
            except ImportError:
                print("WARNING: static-ffmpeg not installed and system ffmpeg missing.")
        
        cls.FFMPEG_PATH = shutil.which("ffmpeg") or "ffmpeg"
        cls.FFPROBE_PATH = shutil.which("ffprobe") or "ffprobe"
        
        if shutil.which(cls.FFMPEG_PATH):
            print(f"✓ FFmpeg found: {cls.FFMPEG_PATH}")
        else:
            raise RuntimeError("FFmpeg not found! Please install FFmpeg.")
    
    @classmethod
    def extract_audio_to_file(cls, video_path: str, output_path: str, sample_rate: int = 16000) -> str:
        """
        Extract audio from video and save to WAV file.
        
        Args:
            video_path: Path to input video file
            output_path: Path to save output WAV file
            sample_rate: Sample rate in Hz (default: 16000)
        
        Returns:
            Path to extracted audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cmd = [
            cls.FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error",
            "-i", video_path,
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # WAV format
            "-ar", str(sample_rate),  # Sample rate
            "-ac", "1",  # Mono
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {result.stderr}")
        
        print(f"✓ Audio extracted to: {output_path}")
        return output_path
    
    @classmethod
    def extract_audio_to_numpy(cls, video_path: str, sample_rate: int = 16000) -> np.ndarray:
        """
        Extract audio from video directly to NumPy array (in-memory).
        
        Args:
            video_path: Path to input video file
            sample_rate: Sample rate in Hz (default: 16000)
        
        Returns:
            NumPy array of audio samples (float32, normalized to [-1, 1])
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cmd = [
            cls.FFMPEG_PATH,
            "-y", "-hide_banner", "-loglevel", "error",
            "-i", video_path,
            "-vn",  # No video
            "-sn",  # No subtitles (pure audio)
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",  # Mono
            "-f", "s16le",  # Raw PCM
            "pipe:1"  # Output to stdout
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        if process.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {error.decode()}")
        
        # Convert raw PCM to float32 normalized array
        audio = np.frombuffer(output, dtype=np.int16).astype(np.float32) / 32768.0
        print(f"✓ Audio extracted to NumPy: {len(audio)} samples @ {sample_rate}Hz")
        return audio
    
    @classmethod
    def extract_audio_segment(cls, video_path: str, start_sec: float, 
                            duration_sec: float, sample_rate: int = 16000) -> np.ndarray:
        """
        Extract a specific time segment from audio as NumPy array.
        
        Args:
            video_path: Path to input video file
            start_sec: Start time in seconds
            duration_sec: Duration in seconds
            sample_rate: Sample rate in Hz (default: 16000)
        
        Returns:
            NumPy array of audio segment
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cmd = [cls.FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error"]
        
        # Seek to start time (input-level seeking is faster)
        if start_sec > 0:
            cmd.extend(["-ss", str(start_sec)])
        
        cmd.extend(["-i", video_path])
        
        # Set duration
        if duration_sec:
            cmd.extend(["-t", str(duration_sec)])
        
        cmd.extend([
            "-vn",  # No video
            "-sn",  # No subtitles
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            "-f", "s16le",
            "pipe:1"
        ])
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output, error = process.communicate()
        
        if process.returncode != 0:
            print(f"Warning: Extraction failed for segment {start_sec}s-{start_sec+duration_sec}s")
            return np.array([], dtype=np.float32)
        
        audio = np.frombuffer(output, dtype=np.int16).astype(np.float32) / 32768.0
        print(f"✓ Segment extracted: {start_sec}s-{start_sec+duration_sec}s ({len(audio)} samples)")
        return audio
    
    @classmethod
    def stream_audio(cls, video_path: str, chunk_size: int = 4096, 
                    sample_rate: int = 16000) -> Generator[bytes, None, None]:
        """
        Stream audio from video in chunks (generator).
        
        Args:
            video_path: Path to input video file
            chunk_size: Size of each chunk in bytes
            sample_rate: Sample rate in Hz (default: 16000)
        
        Yields:
            Audio chunks as bytes
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cmd = [
            cls.FFMPEG_PATH,
            "-y", "-hide_banner", "-loglevel", "error",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", "1",
            "-f", "wav",
            "pipe:1"
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        try:
            while True:
                chunk = process.stdout.read(chunk_size)
                if not chunk:
                    break
                yield chunk
        finally:
            process.stdout.close()
            process.wait()
            if process.returncode != 0:
                error = process.stderr.read().decode()
                print(f"Warning: Streaming error: {error}")


# =============================================================================
# USAGE EXAMPLES
# =============================================================================

if __name__ == "__main__":
    # Initialize FFmpeg
    AudioExtractor.initialize()
    
    # Example video path
    video_file = "path/to/your/video.mp4"
    
    # -------------------------------------------------------------------------
    # Method 1: Extract to WAV file
    # -------------------------------------------------------------------------
    output_wav = "extracted_audio.wav"
    AudioExtractor.extract_audio_to_file(video_file, output_wav, sample_rate=16000)
    
    # -------------------------------------------------------------------------
    # Method 2: Extract to NumPy array (full audio)
    # -------------------------------------------------------------------------
    audio_array = AudioExtractor.extract_audio_to_numpy(video_file, sample_rate=16000)
    print(f"Audio shape: {audio_array.shape}, dtype: {audio_array.dtype}")
    print(f"Duration: {len(audio_array) / 16000:.2f} seconds")
    
    # -------------------------------------------------------------------------
    # Method 3: Extract specific segment (5s to 10s)
    # -------------------------------------------------------------------------
    segment = AudioExtractor.extract_audio_segment(
        video_file, 
        start_sec=5.0, 
        duration_sec=5.0,
        sample_rate=16000
    )
    print(f"Segment shape: {segment.shape}")
    
    # -------------------------------------------------------------------------
    # Method 4: Stream audio in chunks
    # -------------------------------------------------------------------------
    print("\nStreaming audio chunks...")
    chunk_count = 0
    for chunk in AudioExtractor.stream_audio(video_file, chunk_size=8192):
        chunk_count += 1
        if chunk_count <= 3:  # Show first 3 chunks
            print(f"  Chunk {chunk_count}: {len(chunk)} bytes")
        if chunk_count >= 10:  # Stop after 10 chunks for demo
            break
    
    print(f"\n✓ All methods demonstrated successfully!")
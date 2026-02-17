"""
FFmpeg merge layers.
"""
import subprocess

def merge_audio_video(video_path, audio_path, output_path):
    # subprocess.run(["ffmpeg", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", output_path])
    pass

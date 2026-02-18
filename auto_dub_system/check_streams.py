import subprocess
import json
import shutil

def get_streams(file_path):
    ffprobe = shutil.which("ffprobe") or "ffprobe"
    cmd = [
        ffprobe, "-v", "quiet",
        "-show_streams",
        "-of", "csv=p=0",
        "-select_streams", "a", # Select only audio
        file_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.stdout
    except Exception as e:
        return str(e)

info = get_streams(r'c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system\data\outputs\final_video.mp4')
if info.strip():
    print(f"AUDIO STREAMS FOUND: {info}")
else:
    print("NO AUDIO STREAMS FOUND")

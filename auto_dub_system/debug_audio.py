import soundfile as sf
import numpy as np
import sys
import glob

try:
    for fpath in glob.glob(r'c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system\tts_chunks\*.wav')[:5]:
        try:
            data, sr = sf.read(fpath)
            if data.ndim > 1:
                data = data.mean(axis=1)
            max_vol = np.max(np.abs(data))
            print(f"File: {fpath}")
            print(f"  Rate: {sr}, Duration: {len(data)/sr:.2f}s, Max Vol: {max_vol}")
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
except Exception as e:
    print(f"Global Error: {e}")

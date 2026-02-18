import os
import sys

# Add project root to path
sys.path.append(r'c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system')

from app.services.gender_detection import get_gender_detector
import glob

detector = get_gender_detector()
if detector.model is None:
    print("FATAL: Gender model NOT loaded!")
    sys.exit(1)

print(f"Model loaded from: {detector.model_path}")
print(f"Encoder loaded from: {detector.encoder_path}")

segments = glob.glob(r'c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system\data\outputs\segments\*.wav')
print(f"Found {len(segments)} segments.")

for seg in segments[:10]:
    res = detector.predict(seg)
    print(f"File: {os.path.basename(seg)}")
    print(f"  Predicted Gender: {res.get('gender')}")
    print(f"  Confidence: {res.get('confidence'):.2f}")
    print(f"  Pitch Mean: {res.get('pitch', 0):.1f}Hz")

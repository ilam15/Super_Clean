import pickle
import sys

encoder_path = r'c:\Users\sweth\OneDrive\Desktop\autodub1\Super_Clean\auto_dub_system\app\models\gender\label_encoder.pkl'

with open(encoder_path, 'rb') as f:
    encoder = pickle.load(f)

print(f"Classes: {encoder.classes_}")

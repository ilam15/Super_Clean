import numpy as np
import librosa
import logging
from typing import Union

logger = logging.getLogger(__name__)

class FeatureExtractor:
    """
    Enhanced Feature Extractor for Gender Recognition.
    Matches the 'Correct Architecture' requested by the user.
    Uses MFCCs, Pitch (YIN), Spectral Centroid, ZCR, and RMS.
    """

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

    def preprocess_audio(self, audio: Union[str, np.ndarray]) -> np.ndarray:
        """
        Loads and normalizes audio.
        Normalization is CRITICAL for stable feature extraction.
        """
        try:
            if isinstance(audio, str):
                y, sr = librosa.load(audio, sr=self.sample_rate, mono=True)
            elif isinstance(audio, np.ndarray):
                if audio.ndim > 1:
                    audio = librosa.to_mono(audio)
                y = audio
            else:
                raise ValueError("Unsupported audio input type.")
            
            # --- NORMALIZATION (Requested Fix #6) ---
            if len(y) > 0:
                max_val = np.max(np.abs(y))
                if max_val > 0:
                    y = y / max_val
            
            return y
        except Exception as e:
            logger.error(f"Error preprocessing audio: {e}")
            raise

    def extract_features(self, y: np.ndarray) -> np.ndarray:
        """
        Extracts acoustic features requested by the user:
        Pitch (F0), Formants (LPC), MFCCs, Spectral Centroid, ZCR.
        """
        try:
            # Min length 0.25s
            if len(y) < 4000:
                return np.zeros(60) # Increased dimension to 60 for new features

            # 1. MFCCs (20 coefficients)
            mfcc = librosa.feature.mfcc(y=y, sr=self.sample_rate, n_mfcc=20)
            
            # 2. Pitch (YIN) - Strongest gender indicator
            try:
                # User's recommended range: fmin=50, fmax=300
                f0 = librosa.yin(y, fmin=50, fmax=300)
                f0 = f0[~np.isnan(f0)]
                if len(f0) == 0: f0 = np.zeros(1)
            except:
                f0 = np.zeros(1)

            # 3. Formants (via Linear Predictive Coding)
            # Use order 12-16 for 16kHz audio
            try:
                lpc = librosa.lpc(y, order=12)
                # LPC coefficients are a good proxy for formants
            except:
                lpc = np.zeros(13)

            # 4. Spectral Centroid
            spec = librosa.feature.spectral_centroid(y=y, sr=self.sample_rate)

            # 5. Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(y)

            # 6. RMS (Energy)
            rms = librosa.feature.rms(y=y)

            # --- Aggregation (Mean and Std) ---
            # Dimensionality check:
            # mfcc (20 mean, 20 std) = 40
            # f0 (1 mean, 1 std) = 2
            # lpc (13) = 13
            # spec (1 mean, 1 std) = 2
            # zcr (1 mean, 1 std) = 2
            # rms (1 mean) = 1
            # Total = 60
            
            features = np.hstack([
                mfcc.mean(axis=1), mfcc.std(axis=1),
                f0.mean(), f0.std() if len(f0) > 1 else 0.0,
                lpc, # LPC constants are already stable
                spec.mean(), spec.std(),
                zcr.mean(), zcr.std(),
                rms.mean()
            ])
            
            # Ensure fixed length by padding/clipping if necessary (defensive)
            if len(features) < 60:
                features = np.pad(features, (0, 60 - len(features)))
            elif len(features) > 60:
                features = features[:60]
                
            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.zeros(60)

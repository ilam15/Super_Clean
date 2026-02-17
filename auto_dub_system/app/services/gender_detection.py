"""
Consolidated Gender Detection Module for AutoDub
Combines feature extraction and gender prediction into a single production-ready module.
Uses LightGBM model with 60-dimensional acoustic features.
"""

import os
import pickle
import logging
import numpy as np
import librosa
import lightgbm as lgb
from typing import Dict, List, Any, Optional, Union

logger = logging.getLogger(__name__)


class GenderDetector:
    """
    Production-ready gender detection using LightGBM and acoustic features.
    Combines feature extraction and prediction in a single class.
    """

    def __init__(self, model_path: Optional[str] = None, encoder_path: Optional[str] = None, sample_rate: int = 16000):
        """
        Initialize gender detector with optional custom model paths.
        
        Args:
            model_path: Path to LightGBM model file (.pkl)
            encoder_path: Path to label encoder file (.pkl)
            sample_rate: Audio sample rate (default: 16000 Hz)
        """
        self.model = None
        self.label_encoder = None
        self.sample_rate = sample_rate
        
        # Default model paths
        default_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "gender"))
        self.model_path = model_path or os.path.join(default_dir, "gender_lgbm.pkl")
        self.encoder_path = encoder_path or os.path.join(default_dir, "label_encoder.pkl")
        
        # Load models if available
        if os.path.exists(self.model_path) and os.path.exists(self.encoder_path):
            self.load_model()
        else:
            logger.warning(f"Model files not found at {default_dir}")

    def load_model(self):
        """Load the pre-trained LightGBM model and label encoder."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(self.encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
            logger.info("✅ Gender detection model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    def preprocess_audio(self, audio: Union[str, np.ndarray]) -> np.ndarray:
        """
        Load and normalize audio data.
        
        Args:
            audio: Audio file path or numpy array
            
        Returns:
            Normalized audio array
        """
        try:
            # Load audio
            if isinstance(audio, str):
                y, sr = librosa.load(audio, sr=self.sample_rate, mono=True)
            elif isinstance(audio, np.ndarray):
                if audio.ndim > 1:
                    audio = librosa.to_mono(audio)
                y = audio
            else:
                raise ValueError("Unsupported audio input type")
            
            # Normalize audio
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
        Extract 60-dimensional acoustic features from audio.
        
        Features include:
        - MFCCs (20 mean + 20 std = 40 features)
        - Pitch/F0 (mean + std = 2 features)
        - LPC coefficients (13 features)
        - Spectral Centroid (mean + std = 2 features)
        - Zero Crossing Rate (mean + std = 2 features)
        - RMS Energy (1 feature)
        
        Args:
            y: Audio signal array
            
        Returns:
            60-dimensional feature vector
        """
        try:
            # Minimum length check (0.25s)
            if len(y) < 4000:
                return np.zeros(60)

            # 1. MFCCs (20 coefficients)
            mfcc = librosa.feature.mfcc(y=y, sr=self.sample_rate, n_mfcc=20)
            
            # 2. Pitch (F0) using YIN algorithm
            try:
                f0 = librosa.yin(y, fmin=50, fmax=300)
                f0 = f0[~np.isnan(f0)]
                if len(f0) == 0:
                    f0 = np.zeros(1)
            except:
                f0 = np.zeros(1)

            # 3. Formants via Linear Predictive Coding
            try:
                lpc = librosa.lpc(y, order=12)
            except:
                lpc = np.zeros(13)

            # 4. Spectral Centroid
            spec = librosa.feature.spectral_centroid(y=y, sr=self.sample_rate)

            # 5. Zero Crossing Rate
            zcr = librosa.feature.zero_crossing_rate(y)

            # 6. RMS Energy
            rms = librosa.feature.rms(y=y)

            # Combine all features
            features = np.hstack([
                mfcc.mean(axis=1), mfcc.std(axis=1),  # 40 features
                f0.mean(), f0.std() if len(f0) > 1 else 0.0,  # 2 features
                lpc,  # 13 features
                spec.mean(), spec.std(),  # 2 features
                zcr.mean(), zcr.std(),  # 2 features
                rms.mean()  # 1 feature
            ])
            
            # Ensure fixed length (60 dimensions)
            if len(features) < 60:
                features = np.pad(features, (0, 60 - len(features)))
            elif len(features) > 60:
                features = features[:60]
                
            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return np.zeros(60)

    def predict(self, audio: Union[str, np.ndarray], prob_threshold: float = 0.55) -> Dict[str, Any]:
        """
        Predict gender from audio with confidence score.
        
        Uses hybrid approach:
        1. ML-based prediction using LightGBM
        2. Pitch-based sanity checks
        3. Confidence gating
        
        Args:
            audio: Audio file path or numpy array
            prob_threshold: Minimum confidence threshold (default: 0.55)
            
        Returns:
            Dictionary with 'gender', 'confidence', and 'pitch' keys
        """
        if self.model is None or self.label_encoder is None:
            return {"gender": "unknown", "confidence": 0.0}

        try:
            # 1. Feature Extraction
            y = self.preprocess_audio(audio)
            features = self.extract_features(y)
            
            if np.all(features == 0):
                return {"gender": "unknown", "confidence": 0.0}

            # 2. ML Prediction
            features_reshaped = features.reshape(1, -1)
            prob_dist = self.model.predict_proba(features_reshaped)[0]
            class_idx = np.argmax(prob_dist)
            model_confidence = float(prob_dist[class_idx])
            model_gender = self.label_encoder.inverse_transform([class_idx])[0]

            # 3. Pitch-based Sanity Check
            # Pitch mean is at index 40 in the 60-dim vector
            pitch_mean = features[40]
            final_gender = model_gender
            
            # Biological pitch ranges: Female >165Hz, Male <155Hz
            if pitch_mean > 190 and model_gender != 'female':
                final_gender = 'female'
                model_confidence = max(model_confidence, 0.85)
            elif 50 < pitch_mean < 100 and model_gender != 'male':
                final_gender = 'male'
                model_confidence = max(model_confidence, 0.85)

            # 4. Confidence Gating
            if model_confidence < prob_threshold:
                # Use pitch as fallback for very clear cases
                if pitch_mean > 200:
                    return {"gender": "female", "confidence": 0.60, "pitch": float(pitch_mean)}
                elif 50 < pitch_mean < 95:
                    return {"gender": "male", "confidence": 0.60, "pitch": float(pitch_mean)}
                
                logger.debug(f"Confidence too low ({model_confidence:.2f} < {prob_threshold})")
                return {"gender": "unknown", "confidence": model_confidence}

            return {
                "gender": final_gender,
                "confidence": model_confidence,
                "pitch": float(pitch_mean)
            }
            
        except Exception as e:
            logger.error(f"Gender prediction error: {e}")
            return {"gender": "unknown", "confidence": 0.0}

    def batch_predict(self, audio_list: List[Union[str, np.ndarray]]) -> List[Dict[str, Any]]:
        """
        Predict gender for multiple audio samples.
        
        Args:
            audio_list: List of audio file paths or numpy arrays
            
        Returns:
            List of prediction dictionaries
        """
        return [self.predict(audio) for audio in audio_list]


def detect_gender_for_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect gender for a list of audio segments.
    
    Args:
        segments: List of segment dictionaries with 'audio_path' or 'audio_data' keys
        
    Returns:
        Updated segments with 'gender' and 'gender_confidence' fields
    """
    detector = GenderDetector()
    
    for seg in segments:
        audio = seg.get('audio_path') or seg.get('audio_data')
        if audio is not None:
            result = detector.predict(audio)
            seg['gender'] = result['gender']
            seg['gender_confidence'] = result['confidence']
    
    return segments

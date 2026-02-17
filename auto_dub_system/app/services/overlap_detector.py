"""
Overlap true/false logic.
"""
import os
import torch
import warnings
from dotenv import load_dotenv
from src.core.config import settings

# Load environment variables
load_dotenv()

class OverlapDetector:
    def __init__(self, hf_token=None):
        """
        Initialize the Overlap Detector using Pyannote's pre-trained model.
        """
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.pipeline = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self._load_pipeline()

    def _load_pipeline(self):
        try:
            # Lazy import to avoid startup crashes if dependencies are missing
            from pyannote.audio import Pipeline
            
            model_id = "pyannote/overlapped-speech-detection"
            
            print(f"Loading Overlap Detection Pipeline: {model_id}")
            
            try:
                # Try loading with token
                self.pipeline = Pipeline.from_pretrained(
                    model_id, 
                    use_auth_token=self.hf_token
                )
            except Exception as e:
                print(f"Failed to load with use_auth_token, trying 'token' arg... ({e})")
                self.pipeline = Pipeline.from_pretrained(
                    model_id, 
                    token=self.hf_token
                )

            if self.pipeline:
                self.pipeline.to(self.device)
                print("✅ Overlap Detection Pipeline Loaded Successfully")
            else:
                print("❌ Failed to load Overlap Detection Pipeline")

        except Exception as e:
            print(f"❌ Error initializing OverlapDetector: {e}")
            import traceback
            traceback.print_exc()

    def detect_overlaps(self, audio_path):
        """
        Detects overlapping speech segments in the given audio file.
        
        :param audio_path: Path to the audio file.
        :return: List of tuples [(start, end), ...] indicating overlap regions.
        """
        if not self.pipeline:
            print("Pipeline not loaded. Returning empty overlaps.")
            return []

        if not os.path.exists(audio_path):
            print(f"Audio file not found: {audio_path}")
            return []

        try:
            print(f"Processing overlap detection for: {audio_path}")
            
            # Run inference
            # The pipeline usually returns an explicit Annotation of "OV" (Overlap) segments
            output = self.pipeline(audio_path)

            overlaps = []
            
            # Iterate through the timeline of detected overlaps
            for segment in output.get_timeline().support():
                overlaps.append((segment.start, segment.end))
                
            print(f"Found {len(overlaps)} overlapping segments.")
            return overlaps

        except Exception as e:
            print(f"Overlap detection failed: {e}")
            return []

if __name__ == "__main__":
    # Test execution
    import sys
    if len(sys.argv) > 1:
        detector = OverlapDetector()
        results = detector.detect_overlaps(sys.argv[1])
        for start, end in results:
            print(f"Overlap: {start:.2f}s - {end:.2f}s (Duration: {end-start:.2f}s)")
    else:
        print("Usage: python overlap_detector.py <audio_file_path>")
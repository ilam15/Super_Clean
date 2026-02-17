import os
import torch


class OverlapDetector:
    """
    Overlap true/false detection using pyannote overlapped speech model.
    """

    def __init__(self, hf_token=None):
        self.hf_token = hf_token or os.getenv("HF_TOKEN")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = self._load_pipeline()

    def _load_pipeline(self):
        try:
            from pyannote.audio import Pipeline

            model_id = "pyannote/overlapped-speech-detection"

            # try both token formats for compatibility
            try:
                pipe = Pipeline.from_pretrained(model_id, use_auth_token=self.hf_token)
            except Exception:
                pipe = Pipeline.from_pretrained(model_id, token=self.hf_token)

            return pipe.to(self.device)

        except Exception as e:
            print(f"Overlap model load failed: {e}")
            return None

    def detect_overlaps(self, audio_path):
        """
        Returns list of (start, end) overlap timestamps
        """
        if not self.pipeline or not os.path.exists(audio_path):
            return []

        try:
            output = self.pipeline(audio_path)
            return [(s.start, s.end) for s in output.get_timeline().support()]
        except Exception as e:
            print(f"Overlap detection error: {e}")
            return []


# Optional CLI usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        detector = OverlapDetector()
        for s, e in detector.detect_overlaps(sys.argv[1]):
            print(f"{s:.2f}s → {e:.2f}s | {e-s:.2f}s")
    else:
        print("Usage: python overlap_detector.py <audio_file>")

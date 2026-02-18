import os
import re
import logging
import urllib.request
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    fasttext = None
    FASTTEXT_AVAILABLE = False


class LanguageIdentifier:
    _model = None
    _model_path = None

    @classmethod
    def _load_model(cls):
        if cls._model:
            return cls._model

        if not FASTTEXT_AVAILABLE:
            logger.warning("fasttext not installed. Language detection will use fallback only.")
            return None

        # Use a local directory relative to this file
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        model_dir = os.path.join(base_dir, "data", "lid")
        os.makedirs(model_dir, exist_ok=True)
        cls._model_path = os.path.join(model_dir, "lid.176.bin")

        if not os.path.exists(cls._model_path):
            logger.info("Downloading fastText LID model...")
            try:
                urllib.request.urlretrieve(
                    "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin",
                    cls._model_path
                )
                logger.info("fastText model downloaded successfully")
            except Exception as e:
                logger.warning(f"Failed to download fastText model: {e}")
                return None

        try:
            fasttext.FastText.eprint = lambda x: None
            cls._model = fasttext.load_model(cls._model_path)
            logger.info("✅ fastText LID model ready")
        except Exception as e:
            logger.warning(f"Failed to load fastText model: {e}")
            cls._model = None

        return cls._model

    @staticmethod
    def identify(text: str, whisper_hint: str = None, whisper_prob: float = 0.0) -> Tuple[str, float, str]:
        text = text.strip()
        if not text:
            return "unknown", 0.0, "empty"

        model = LanguageIdentifier._load_model()

        text_lang = None
        text_conf = 0.0

        # ---------- SHORT TEXT ----------
        if len(text) < 3:
            if whisper_hint:
                return whisper_hint, whisper_prob or 0.7, "audio_probe_short"
            return "unknown", 0.0, "short_text"

        # ---------- FASTTEXT DETECTION ----------
        if model:
            try:
                predictions = model.predict(text.replace('\n', ' '), k=1)
                t_lang = predictions[0][0].replace('__label__', '')
                t_conf = float(predictions[1][0])

                lang_map = {
                    'eng': 'en', 'hin': 'hi', 'tel': 'te', 'tam': 'ta', 'kan': 'kn',
                    'mal': 'ml', 'mar': 'mr', 'guj': 'gu', 'ben': 'bn', 'pan': 'pa',
                    'deu': 'de', 'fra': 'fr', 'spa': 'es', 'por': 'pt', 'ita': 'it',
                    'rus': 'ru', 'jpn': 'ja', 'kor': 'ko', 'zho': 'zh', 'ara': 'ar'
                }

                text_lang = lang_map.get(t_lang, t_lang[:2])
                text_conf = t_conf

            except Exception as e:
                logger.warning(f"FastText failed: {e}")

        # ---------- NO TEXT RESULT ----------
        if not text_lang:
            return whisper_hint or "unknown", whisper_prob or 0.0, "whisper_fallback_no_text"

        # ---------- NO WHISPER ----------
        if not whisper_hint:
            return text_lang, text_conf, "text_only"

        hint = whisper_hint.lower()

        # ---------- AGREEMENT ----------
        if text_lang == hint:
            confidence = max(text_conf, whisper_prob or 0.8)
            return text_lang, confidence, "confirmed"

        # ---------- AUDIO PRIORITY ----------
        if hint != 'en' and (text_lang == 'en' or text_conf < 0.7):
            return hint, whisper_prob or 0.8, "audio_probe_priority"

        # ---------- TEXT OVERRIDE ----------
        if text_conf > 0.85:
            return text_lang, text_conf, "text_override"

        # ---------- DEFAULT ----------
        return hint, whisper_prob or 0.5, "whisper_audio_fallback"


def is_devanagari(text):
    return any('\u0900' <= c <= '\u097F' for c in text)


def contains_english_script(text):
    return bool(re.search(r'[a-zA-Z]{3,}', text))

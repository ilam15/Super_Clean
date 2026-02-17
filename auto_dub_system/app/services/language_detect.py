import os
import re
import urllib.request
import logging
from typing import Tuple, Optional
from src.core.config import settings
from src.core.logger import logger

# Try optional fasttext import
try:
    import fasttext
    FASTTEXT_AVAILABLE = True
except ImportError:
    fasttext = None
    FASTTEXT_AVAILABLE = False

import langid

class LanguageIdentifier:
    _model = None
    _model_path = None

    @classmethod
    def _load_model(cls):
        if cls._model:
            return cls._model

        if not FASTTEXT_AVAILABLE:
            return None

        # Standard location for the model
        model_dir = os.path.join(settings.BASE_DIR, "engine", "lid")
        os.makedirs(model_dir, exist_ok=True)
        cls._model_path = os.path.join(model_dir, "lid.176.bin")

        if not os.path.exists(cls._model_path):
            logger.info("Initializing fastText download at shared location...")
            try:
                urllib.request.urlretrieve(
                    "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin",
                    cls._model_path
                )
                logger.info("Shared fastText model downloaded successfully")
            except Exception as e:
                logger.warning(f"Failed to download fastText model: {e}. Falling back to langid.")
                return None

        try:
            # Suppress fastText warnings
            fasttext.FastText.eprint = lambda x: None
            cls._model = fasttext.load_model(cls._model_path)
            logger.info("✅ fastText LID model ready")
        except Exception as e:
            logger.warning(f"Failed to load fastText model: {e}")
            cls._model = None
            
        return cls._model

    @staticmethod
    def identify(text: str, whisper_hint: str = None, whisper_prob: float = 0.0) -> Tuple[str, float, str]:
        """
        Hybrid language identification using FastText, LangID, and Whisper hints.
        Returns: (language_code, confidence, method)
        """
        text = text.strip()
        if not text:
            return "unknown", 0.0, "empty"

        model = LanguageIdentifier._load_model()
        
        # 1. Text-based Detection
        text_lang = None
        text_conf = 0.0
        
        if len(text) < 3:
            # Too short for reliable text-based
            if whisper_hint:
                return whisper_hint, whisper_prob or 0.7, "audio_probe_short"
            return "unknown", 0.0, "short_text"

        if model:
            try:
                predictions = model.predict(text.replace('\n', ' '), k=1)
                t_lang = predictions[0][0].replace('__label__', '')
                t_conf = float(predictions[1][0])
                
                # Normalize fastText 3-letter codes to 2-letter
                lang_map = {'eng': 'en', 'hin': 'hi', 'tel': 'te', 'tam': 'ta', 'kan': 'kn', 
                           'mal': 'ml', 'mar': 'mr', 'guj': 'gu', 'ben': 'bn', 'pan': 'pa',
                           'deu': 'de', 'fra': 'fr', 'spa': 'es', 'por': 'pt', 'ita': 'it',
                           'rus': 'ru', 'jpn': 'ja', 'kor': 'ko', 'zho': 'zh', 'ara': 'ar'}
                text_lang = lang_map.get(t_lang, t_lang[:2])
                text_conf = t_conf
            except Exception as e:
                logger.warning(f"FastText failed: {e}")

        if not text_lang:
            # Fallback to langid
            try:
                res_lang, res_prob = langid.classify(text)
                text_lang = res_lang
                text_conf = float(res_prob) # langid returns high probability usually
            except:
                pass

        if not text_lang:
             return whisper_hint or "unknown", whisper_prob or 0.0, "whisper_fallback_no_text"

        # 2. Hybrid Decision Logic (The "Anti-Bias" Logic)
        
        # If no hint, trust text
        if not whisper_hint:
            return text_lang, text_conf, "text_only"

        # Compare Text vs Audio
        hint = whisper_hint.lower()
        
        if text_lang == hint:
            # Agreement
            confidence = max(text_conf, whisper_prob or 0.8)
            return text_lang, confidence, "confirmed"

        # Disagreement Handling
        
        # CRITICAL: Trust Whisper if it hears a non-English language but text thinks it's English (Caption Bias)
        if hint != 'en' and (text_lang == 'en' or text_conf < 0.7):
            return hint, whisper_prob or 0.8, "audio_probe_priority"

        # Check for High Confidence Text Override
        if text_conf > 0.85:
             return text_lang, text_conf, "text_override"

        # Check for common script mismatches (e.g. Hindi text but detected as English)
        # (Already handled partly by FastText, but let's be safe)
        
        # Default fallback to Whisper if text is weak
        return hint, whisper_prob or 0.5, "whisper_audio_fallback"

def is_devanagari(text):
    return any('\u0900' <= c <= '\u097F' for c in text)

def contains_english_script(text):
    return bool(re.search(r'[a-zA-Z]{3,}', text))
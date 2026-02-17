import re
import time
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from deep_translator import GoogleTranslator

# --- 1. LANGUAGE DECISION LOGIC (from decision.py) ---
class TranslationDecision:
    @staticmethod
    def identify_language(text, whisper_lang):
        """Simple identification fallback if fasttext is unavailable."""
        # In the real system, this uses fastText/langid
        return whisper_lang or "en"

    @staticmethod
    def get_decision(segments, target_lang):
        """Decides which segments to send to the translator."""
        processed = []
        target_code = target_lang[:2].lower() # e.g., 'Hindi' -> 'hi'

        for s in segments:
            text = s['text']
            detected_lang = TranslationDecision.identify_language(text, s.get('lang'))
            
            # Logic: If it's noise or already the target language, keep it original
            is_noise = not bool(re.search(r'[a-zA-Z\u0900-\u0D7F]', text)) or len(text.strip()) < 2
            
            if is_noise or detected_lang == target_code:
                action = "KEEP"
            else:
                action = "TRANSLATE"
                
            s.update({"lang": detected_lang, "action": action})
            processed.append(s)
        return processed

# --- 2. THE TRANSLATOR ENGINE (Combined translator.py & google_translate.py) ---
class CombinedTranslator:
    def __init__(self, model_manager=None):
        self.model_manager = model_manager # Reference to local NLLB model

    def translate_batch(self, subtitles, src_lang, dst_lang):
        """The core engine: Tries Local NLLB first, then falls back to Google."""
        
        # Shielding tags like <S:01|G:Male>
        tags, texts_to_translate = [], []
        for sub in subtitles:
            match = re.search(r'(<S:.*?\|G:.*?>)?(.*)', sub.text, re.DOTALL)
            tag = match.group(1) or ""
            text = match.group(2).strip()
            tags.append(tag); texts_to_translate.append(text)

        # STEP A: Try Local NLLB (if model is loaded)
        try:
            if self.model_manager and self.model_manager.get_translator():
                local_model = self.model_manager.get_translator()
                # Assuming NLLB codes like 'hin_Deva' are provided
                results = local_model(texts_to_translate, src_lang=src_lang, tgt_lang=dst_lang)
                
                final_subs = []
                for i, res in enumerate(results):
                    translated = res['translation_text']
                    final_subs.append(f"{tags[i]} {translated}".strip())
                return final_subs
        except Exception as e:
            print(f"Local NLLB failed, falling back to Google: {e}")

        # STEP B: Fallback to Google Translate
        return self.google_fallback(texts_to_translate, tags, src_lang, dst_lang)

    def google_fallback(self, texts, tags, src, dst):
        """Robust Google Translate fallback with thread-safe batching."""
        def call_google(text_chunk):
            try:
                # Normalizing codes (e.g., 'hin_Deva' -> 'hi')
                src_code = src[:2] if len(src) > 3 else src
                dst_code = dst[:2] if len(dst) > 3 else dst
                return GoogleTranslator(source=src_code, target=dst_code).translate(text_chunk)
            except:
                return text_chunk

        with ThreadPoolExecutor(max_workers=5) as exe:
            results = list(exe.map(call_google, texts))
        
        return [f"{tags[i]} {results[i]}".strip() for i in range(len(results))]

# --- 3. THE COMPLETE WORKFLOW ---
def run_translation_process(raw_segments, target_lang):
    """
    Simulates the full working process:
    1. Identify vs Decision engine
    2. Filter segments needing translation
    3. Run the hybrid translator
    """
    # Phase 1: Decision
    decision_engine = TranslationDecision()
    evaluated_segments = decision_engine.get_decision(raw_segments, target_lang)
    
    # Phase 2: Separate segments that need translation
    to_translate = [s for s in evaluated_segments if s['action'] == "TRANSLATE"]
    
    if not to_translate:
        return evaluated_segments

    # Phase 3: Execute Translation
    translator = CombinedTranslator()
    # we convert to objects for the batch processor
    sub_objects = [SimpleNamespace(text=s['text']) for s in to_translate]
    
    # Run the translator
    translated_texts = translator.translate_batch(sub_objects, "auto", target_lang)

    # Phase 4: Map back to segments
    for i, s in enumerate(to_translate):
        s['text'] = translated_texts[i]
        s['translated'] = True

    return evaluated_segments

# Example Usage:
# raw_data = [{'text': '<S:01|G:Male> Hello how are you?', 'lang': 'en'}]
# result = run_translation_process(raw_data, 'Hindi')


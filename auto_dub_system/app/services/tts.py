import re
import time
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
from deep_translator import GoogleTranslator


# =========================================================
# CONFIG
# =========================================================
MAX_WORKERS = 5
RETRY_LIMIT = 3
RETRY_DELAY = 1.2
CACHE = {}
CACHE_LOCK = threading.Lock()


# =========================================================
# UTILS
# =========================================================
def cache_key(text, src, tgt):
    return hashlib.md5(f"{src}:{tgt}:{text}".encode()).hexdigest()


def detect_language(text, whisper_lang):
    return whisper_lang or "en"


def is_noise(text):
    return not re.search(r"[a-zA-Z\u0900-\u0D7F]", text) or len(text.strip()) < 2


def split_tag(text):
    m = re.match(r'(<S:.*?\|G:.*?>)?(.*)', text, re.S)
    return (m.group(1) or "", m.group(2).strip())


def short(code):
    return code[:2]


# =========================================================
# RATE LIMITED GOOGLE TRANSLATOR
# =========================================================
def google_translate_safe(text, src, tgt):
    key = cache_key(text, src, tgt)

    with CACHE_LOCK:
        if key in CACHE:
            return CACHE[key]

    for _ in range(RETRY_LIMIT):
        try:
            out = GoogleTranslator(source=src, target=tgt).translate(text)
            with CACHE_LOCK:
                CACHE[key] = out
            return out
        except:
            time.sleep(RETRY_DELAY)

    return text  # final fallback


# =========================================================
# BATCH TRANSLATION ENGINE
# =========================================================
def batch_translate(texts, src, tgt):
    with ThreadPoolExecutor(MAX_WORKERS) as ex:
        return list(ex.map(lambda t: google_translate_safe(t, src, tgt), texts))


# =========================================================
# MAIN ENTERPRISE PIPELINE
# =========================================================
def enterprise_translate(segments, target_lang, model_manager=None):

    to_translate = []
    indexes = []

    tgt = short(target_lang)

    # ---------- DECISION ENGINE ----------
    for i, seg in enumerate(segments):

        text = seg["text"]
        lang = short(detect_language(text, seg.get("lang")))

        seg["lang"] = lang

        if is_noise(text) or lang == tgt:
            seg["action"] = "KEEP"
            continue

        tag, clean = split_tag(text)

        to_translate.append((tag, clean))
        indexes.append(i)
        seg["action"] = "TRANSLATE"

    if not to_translate:
        return segments

    tags, texts = zip(*to_translate)

    # ---------- LOCAL MODEL FIRST ----------
    translated = None

    if model_manager:
        try:
            model = model_manager.get_translator()
            if model:
                out = model(list(texts), src_lang="auto", tgt_lang=target_lang)
                translated = [o["translation_text"] for o in out]
        except:
            translated = None

    # ---------- FALLBACK ----------
    if translated is None:
        translated = batch_translate(texts, "auto", tgt)

    # ---------- MERGE BACK ----------
    for idx, tr, tg in zip(indexes, translated, tags):
        segments[idx]["text"] = f"{tg} {tr}".strip()
        segments[idx]["translated"] = True

    return segments

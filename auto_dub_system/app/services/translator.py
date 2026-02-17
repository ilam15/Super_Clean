import re
from concurrent.futures import ThreadPoolExecutor
from deep_translator import GoogleTranslator


# ---------- LANGUAGE DECISION ----------
def identify_language(text, whisper_lang):
    return whisper_lang or "en"


def needs_translation(text, detected, target):
    if not re.search(r"[a-zA-Z\u0900-\u0D7F]", text):
        return False
    if len(text.strip()) < 2:
        return False
    return detected != target[:2]


# ---------- TAG SAFE SPLIT ----------
def split_tag(text):
    m = re.match(r'(<S:.*?\|G:.*?>)?(.*)', text, re.S)
    return (m.group(1) or "", m.group(2).strip())


# ---------- GOOGLE FALLBACK ----------
def google_batch(texts, src, dst):
    src_code = src[:2] if len(src) > 3 else src
    dst_code = dst[:2] if len(dst) > 3 else dst

    def translate(t):
        try:
            return GoogleTranslator(source=src_code, target=dst_code).translate(t)
        except:
            return t

    with ThreadPoolExecutor(max_workers=5) as exe:
        return list(exe.map(translate, texts))


# ---------- MAIN PIPELINE ----------
def run_translation_process(raw_segments, target_lang, model_manager=None):
    
    processed = []
    to_translate = []
    indexes = []

    # ---- Decision Phase ----
    for i, s in enumerate(raw_segments):
        text = s["text"]
        detected = identify_language(text, s.get("lang"))

        if needs_translation(text, detected, target_lang):
            tag, clean = split_tag(text)
            to_translate.append((tag, clean))
            indexes.append(i)
            s["action"] = "TRANSLATE"
        else:
            s["action"] = "KEEP"

        s["lang"] = detected
        processed.append(s)

    if not to_translate:
        return processed

    tags, texts = zip(*to_translate)

    # ---- Translation Phase ----
    try:
        if model_manager and model_manager.get_translator():
            model = model_manager.get_translator()
            results = model(list(texts), src_lang="auto", tgt_lang=target_lang)
            translated = [r["translation_text"] for r in results]
        else:
            raise RuntimeError
    except:
        translated = google_batch(texts, "auto", target_lang)

    # ---- Merge Back ----
    for idx, out, tag in zip(indexes, translated, tags):
        processed[idx]["text"] = f"{tag} {out}".strip()
        processed[idx]["translated"] = True

    return processed

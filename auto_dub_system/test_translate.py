from app.services.stt import sarvam_translate
import logging

logging.basicConfig(level=logging.INFO)

def test_translator():
    # Test case 1: English to Hindi
    text = "Hello, how are you today?"
    translated = sarvam_translate(text, "en", "hi")
    print(f"EN -> HI: {translated}")

    # Test case 2: Hindi to English
    text = "नमस्ते, आप कैसे हैं?"
    translated = sarvam_translate(text, "hi", "en")
    print(f"HI -> EN: {translated}")

    # Test case 3: Tamil to English
    text = "வணக்கம், எப்படி இருக்கிறீர்கள்?"
    translated = sarvam_translate(text, "ta", "en")
    print(f"TA -> EN: {translated}")

if __name__ == "__main__":
    test_translator()

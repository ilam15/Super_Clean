import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from app.services.language_detect import LanguageIdentifier

def test_detection():
    test_cases = [
        ("Hello, how are you today?", "en"),
        ("नमस्ते, आप कैसे हैं?", "hi"),
        ("ഹലോ, സുഖമാണോ?", "ml"),
        ("வணக்கம், எப்படி இருக்கிறீர்கள்?", "ta"),
        ("Bonjour, comment ça va?", "fr"),
        ("Hola, ¿cómo estás?", "es"),
        ("Guten Tag, wie geht es Ihnen?", "de"),
        ("హలో, మీరు ఎలా ఉన్నారు?", "te")
    ]

    with open("test_results.txt", "w", encoding="utf-8") as f:
        f.write(f"{'Text':<40} | {'Expected':<10} | {'Detected':<10} | {'Conf':<6} | {'Reason'}\n")
        f.write("-" * 85 + "\n")
        
        for text, expected in test_cases:
            try:
                lang, conf, reason = LanguageIdentifier.identify(text)
                f.write(f"{text[:38]:<40} | {expected:<10} | {lang:<10} | {conf:.2f} | {reason}\n")
            except Exception as e:
                f.write(f"Error for '{text}': {e}\n")

if __name__ == "__main__":
    test_detection()

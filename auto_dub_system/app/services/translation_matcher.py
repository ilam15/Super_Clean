def translation_matcher(
    text: str,
    start_time: float,
    end_time: float,
    speaker_no: str,
    overlap: bool,
    gender: str
):
    """
    INPUT:
        text, start_time, end_time, speaker_no, overlap, gender

    PROCESS:
        - word count check
        - timestamp alignment
        - overflow correction

    OUTPUT:
        {
            aligned_text,
            start_time,
            end_time,
            speaker_no,
            overlap,
            gender
        }
    """

    try:
        # -------------------------
        # BASIC CLEAN
        # -------------------------
        text = text.strip()
        
        # -------------------------
        # EMPTY TEXT HANDLING
        # -------------------------
        # If the translation is empty or just whitespace, pass it through as empty
        # instead of generating "...". The TTS engine will see empty text and generate silence.
        if not text:
            aligned_text = ""
        else:
            # We no longer aggressively truncate words here based on a flawed heuristic.
            # If the text is too long for the duration, the TTS engine (or a later processing step)
            # should handle dynamic speedup (e.g., using pyrubberband or ffmpeg atempo)
            # rather than deleting the translated content and destroying the sentence meaning.
            aligned_text = text

        # -------------------------
        # FINAL STRUCTURE
        # -------------------------
        # Preserve precision! Rounding to 3 decimal places (milliseconds) instead of 2.
        # This prevents tiny gaps/overlaps from accumulating and drifting over a long video.
        return {
            "aligned_text": aligned_text,
            "start_time": round(start_time, 3),
            "end_time": round(end_time, 3),
            "speaker_no": speaker_no,
            "overlap": overlap,
            "gender": gender
        }

    except Exception as e:
        print(f"Alignment Error: {e}")
        return {
            "aligned_text": text,
            "start_time": start_time,
            "end_time": end_time,
            "speaker_no": speaker_no,
            "overlap": overlap,
            "gender": gender
        }

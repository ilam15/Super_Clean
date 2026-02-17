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
        words = text.split()

        # -------------------------
        # DURATION CALC
        # -------------------------
        duration = max(end_time - start_time, 0.1)

        # average speaking speed ≈ 2.5 words/sec
        max_words = int(duration * 3)

        # -------------------------
        # OVERFLOW CORRECTION
        # -------------------------
        if len(words) > max_words:
            words = words[:max_words]

        aligned_text = " ".join(words)

        # -------------------------
        # UNDERFLOW CORRECTION
        # -------------------------
        if len(words) < 1:
            aligned_text = "..."

        # -------------------------
        # FINAL STRUCTURE
        # -------------------------
        return {
            "aligned_text": aligned_text,
            "start_time": round(start_time, 2),
            "end_time": round(end_time, 2),
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

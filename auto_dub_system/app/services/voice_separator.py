import os
import logging

logger = logging.getLogger(__name__)

# Lazy-load the model only when needed (prevents crash on import if speechbrain not installed)
_model = None


def _get_model():
    global _model
    if _model is not None:
        return _model

    try:
        import torch
        from speechbrain.inference.separation import SepformerSeparation

        _model = SepformerSeparation.from_hparams(
            source="speechbrain/sepformer-wsj0-2mix",
            savedir="pretrained_sepformer",
            run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"}
        )
        logger.info("✅ SepformerSeparation model loaded")
    except ImportError:
        logger.warning("speechbrain not installed. Voice separation unavailable.")
        _model = None
    except Exception as e:
        logger.error(f"Failed to load SepformerSeparation model: {e}")
        _model = None

    return _model


def separate_voice(audio_path, output_dir=None):
    if not os.path.exists(audio_path):
        return []

    model = _get_model()
    if model is None:
        logger.warning("Voice separation model not available. Returning empty list.")
        return []

    try:
        import torchaudio

        output_dir = output_dir or os.path.dirname(audio_path)
        os.makedirs(output_dir, exist_ok=True)

        sources = model.separate_file(path=audio_path)
        sr = 8000
        base = os.path.splitext(os.path.basename(audio_path))[0]
        paths = []

        for i in range(sources.shape[2]):
            out = os.path.join(output_dir, f"{base}_speaker_{i+1}.wav")
            audio = sources[:, :, i].cpu()

            if audio.abs().max() > 0:   # prevent clipping
                audio = audio / audio.abs().max()

            torchaudio.save(out, audio, sr)
            paths.append(out)

        return paths

    except Exception as e:
        logger.error(f"Voice separation failed: {e}")
        return []

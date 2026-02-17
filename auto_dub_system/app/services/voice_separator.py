import os
import torch
import torchaudio
from speechbrain.inference.separation import SepformerSeparation


# Load model once (major speed improvement)
_model = SepformerSeparation.from_hparams(
    source="speechbrain/sepformer-wsj0-2mix",
    savedir="pretrained_sepformer",
    run_opts={"device": "cuda" if torch.cuda.is_available() else "cpu"}
)


def separate_voice(audio_path, output_dir=None):
    if not os.path.exists(audio_path):
        return []

    output_dir = output_dir or os.path.dirname(audio_path)
    os.makedirs(output_dir, exist_ok=True)

    sources = _model.separate_file(path=audio_path)
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

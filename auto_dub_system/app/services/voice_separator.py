import os
import torch
import torchaudio

def separate_voice(audio_path, output_dir=None):
    """
    Separates overlapping speech in an audio file using SpeechBrain SepFormer.
    
    Args:
        audio_path (str): Path to the input audio file.
        output_dir (str, optional): Directory to save output files. Defaults to 'separated_results'.
        
    Returns:
        list: Paths to the separated audio files.
    """
    try:
        from speechbrain.inference.separation import SepformerSeparation
    except ImportError:
        try:
            from speechbrain.pretrained import SepformerSeparation
        except ImportError:
            raise ImportError("SpeechBrain is not installed. Run: pip install speechbrain")

    if not os.path.exists(audio_path):
        print(f"Error: File not found {audio_path}")
        return []

    if output_dir is None:
        output_dir = os.path.dirname(audio_path)
    
    os.makedirs(output_dir, exist_ok=True)
    
    print("Loading SpeechBrain SepFormer model...")
    
    # Correct source is 'speechbrain/sepformer-wsj0-2mix' (note the dash)
    # Using CUDA if available
    run_opts = {"device": "cuda" if torch.cuda.is_available() else "cpu"}
    
    model = SepformerSeparation.from_hparams(
        source="speechbrain/sepformer-wsj0-2mix", 
        savedir="pretrained_models/sepformer-wsj0-2mix",
        run_opts=run_opts
    )

    print(f"Separating overlapping voices in: {audio_path}")
    
    # Perform separation
    # est_sources shape: [batch, time, channels]
    est_sources = model.separate_file(path=audio_path)

    output_paths = []
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    
    # The models typically operate at 8000Hz for WSJ0-2mix
    sample_rate = 8000
    
    # Iterate over separated sources (usually 2 for this model)
    num_sources = est_sources.shape[2]
    
    for i in range(num_sources):
        save_path = os.path.join(output_dir, f"{base_name}_speaker_{i+1}.wav")
        
        # Get source tensor: [1, time] -> [1, time]
        source = est_sources[:, :, i].detach().cpu()
        
        # Normalize to prevent clipping (optional)
        if source.abs().max() > 0:
            source = source / source.abs().max()

        torchaudio.save(save_path, source, sample_rate)
        output_paths.append(save_path)
        print(f"Saved source {i+1} to: {save_path}")

    return output_paths

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        separate_voice(sys.argv[1])
    else:
        print("Usage: python separate_voice.py <input_audio_path>")
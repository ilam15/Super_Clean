import subprocess

class FastAudioMixer:

    @staticmethod
    def mix(layers, output_path):

        if not layers:
            raise ValueError("No audio layers")

        inputs = []
        filters = []

        for i, layer in enumerate(layers):
            inputs += ["-i", layer["path"]]

            volume = layer.get("volume", 0)
            filters.append(f"[{i}:a]volume={1 + volume/10}[a{i}]")

        mix_inputs = "".join(f"[a{i}]" for i in range(len(layers)))

        filter_complex = (
            ";".join(filters) +
            f";{mix_inputs}amix=inputs={len(layers)}:duration=longest"
        )

        cmd = [
            "ffmpeg","-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-c:a","pcm_s16le",
            output_path
        ]

        subprocess.run(cmd, check=True)
        return output_path

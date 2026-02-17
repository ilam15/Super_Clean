import tempfile
import os
from mixer import FastAudioMixer
from merger import VideoAudioMerger


class RenderPipeline:

    @staticmethod
    def render(video_path, layers, output_path):

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_audio = tmp.name

        try:
            FastAudioMixer.mix(layers, temp_audio)
            VideoAudioMerger.merge(video_path, temp_audio, output_path)
            return output_path

        finally:
            if os.path.exists(temp_audio):
                os.remove(temp_audio)

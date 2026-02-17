import subprocess

class VideoAudioMerger:

    @staticmethod
    def merge(video, audio, output):

        cmd = [
            "ffmpeg","-y",
            "-i", video,
            "-i", audio,
            "-map","0:v:0",
            "-map","1:a:0",
            "-c:v","copy",
            "-c:a","aac",
            "-shortest",
            output
        ]

        subprocess.run(cmd, check=True)
        return output

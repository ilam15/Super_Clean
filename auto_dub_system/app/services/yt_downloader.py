"""
Optimized YouTube Video Downloader
Efficient format parsing + resilient download handling
"""

import yt_dlp
import os
import logging
import time
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("YouTubeDownloader")


class YouTubeDownloader:
    def __init__(self, download_dir: str = "temp_downloads"):
        self.download_dir = download_dir
        os.makedirs(download_dir, exist_ok=True)

        self.base_ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                }
            },
            "retries": 5,
            "fragment_retries": 5,
            "socket_timeout": 30,
        }

    # ------------------------------------------------------------------ #
    # VIDEO INFO
    # ------------------------------------------------------------------ #

    def get_video_info(self, url: str) -> Dict:
        try:
            with yt_dlp.YoutubeDL(self.base_ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            video_data = {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
                "description": (info.get("description") or "")[:200],
                "formats": [],
            }

            # Efficient format parsing
            format_map = {}

            for fmt in info.get("formats", []):
                height = fmt.get("height")
                if not height:
                    continue

                # Prefer progressive (video+audio)
                has_audio = fmt.get("acodec") != "none"
                has_video = fmt.get("vcodec") != "none"

                if has_video:
                    if height not in format_map or has_audio:
                        format_map[height] = {
                            "quality": f"{height}p",
                            "height": height,
                            "format_id": fmt.get("format_id"),
                            "ext": fmt.get("ext"),
                            "filesize": fmt.get("filesize"),
                            "has_audio": has_audio,
                        }

            video_data["formats"] = sorted(
                format_map.values(),
                key=lambda x: x["height"],
                reverse=True,
            )

            logger.info(f"Fetched info: {video_data['title']}")
            return video_data

        except Exception as e:
            raise Exception(f"Failed to fetch video info: {e}")

    # ------------------------------------------------------------------ #
    # DOWNLOAD
    # ------------------------------------------------------------------ #

    def download_video(
        self,
        url: str,
        quality: str = "720p",
        filename: Optional[str] = None,
    ) -> str:

        height = int(quality.replace("p", ""))
        format_selector = f"bv*[height<={height}]+ba/b[height<={height}]"

        ydl_opts = {
            **self.base_ydl_opts,
            "format": format_selector,
            "outtmpl": os.path.join(
                self.download_dir,
                filename if filename else "%(title)s.%(ext)s",
            ),
            "merge_output_format": "mp4",
            "quiet": False,
        }

        max_retries = 3

        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading {quality} (Attempt {attempt+1})")

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info)

                if not os.path.exists(file_path):
                    raise FileNotFoundError("Download failed")

                logger.info("Download successful")
                return file_path

            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Download failed: {e}")

                wait_time = 2 ** attempt
                logger.warning(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

    # ------------------------------------------------------------------ #
    # BEST QUALITY
    # ------------------------------------------------------------------ #

    def get_best_quality_available(self, url: str) -> str:
        info = self.get_video_info(url)
        if not info["formats"]:
            return "720p"

        return info["formats"][0]["quality"]


# ---------------------------------------------------------------------- #
# Example Usage
# ---------------------------------------------------------------------- #

if __name__ == "__main__":
    downloader = YouTubeDownloader()
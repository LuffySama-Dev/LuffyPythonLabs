#!/usr/bin/env python3
"""
universal_video_downloader.py
Download any public-facing YouTube or Instagram URL as
 • full-quality video   or
 • audio-only track (MP3)

Dependencies
    pip install yt-dlp instaloader  # ffmpeg must also be on PATH for audio ↔ video conversion

Usage
    python universal_video_downloader.py URL
    python universal_video_downloader.py URL --audio-only
    python universal_video_downloader.py URL --quality 720p
    python universal_video_downloader.py URL -o my_downloads -n custom_name
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yt_dlp                   # one tool covers YT + Instagram[2][49]
except ImportError:
    sys.exit("❌  yt-dlp is required:  pip install yt-dlp")

# ──────────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────────
def detect_platform(url: str) -> str:
    """Return 'youtube', 'instagram' or 'other' based on netloc."""
    netloc = urlparse(url).netloc.lower()
    if any(p in netloc for p in ("youtube.com", "youtu.be", "youtube-nocookie.com")):
        return "youtube"
    if any(p in netloc for p in ("instagram.com", "instagr.am")):
        return "instagram"
    return "other"                                   # yt-dlp still supports thousands of sites[2]

def safe_title(title: str) -> str:
    """Remove illegal filesystem characters."""
    return re.sub(r'[<>:"/\\|?*]', "_", title).strip()

# ──────────────────────────────────────────────────────────────────────────────
# core download routine (yt-dlp does the heavy lifting)
# ──────────────────────────────────────────────────────────────────────────────
def download(url: str, *, audio_only=False, quality="best", out_dir="downloads",
             custom_name: str | None = None) -> None:
    out_path = Path(out_dir).expanduser()
    out_path.mkdir(parents=True, exist_ok=True)

    # build output template
    template = (custom_name or "%(title)s").strip()
    template = safe_title(template)
    template = str(out_path / f"{template}.%(ext)s")

    # yt-dlp option block
    ydl_opts = {
        "outtmpl": template,
        "ignoreerrors": False,
        "quiet": False,
        "no_warnings": True,
    }

    # format selection
    if audio_only:
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        if quality == "best":
            ydl_opts["format"] = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        elif quality == "worst":
            ydl_opts["format"] = "worst"
        else:                                            # e.g. "720p"
            height = quality.rstrip("p")
            ydl_opts["format"] = (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
                f"/best[height<={height}]/best"
            )

    print(f"→ platform: {detect_platform(url)}")
    print(f"→ saving to: {out_path}\n")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    print("✅ finished\n")

# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    p = argparse.ArgumentParser(
        description="Download YouTube / Instagram video or audio via yt-dlp",
    )
    p.add_argument("url", help="video / reel / short / post URL")
    p.add_argument("-a", "--audio-only", action="store_true",
                   help="grab audio track and convert to MP3")
    p.add_argument("-q", "--quality", default="best",
                   choices=["best", "worst", "720p", "480p", "360p"],
                   help="target resolution when downloading video (default: best)")
    p.add_argument("-o", "--output-dir", default="downloads",
                   help="directory to store the media files")
    p.add_argument("-n", "--name", help="manual filename (no extension)")
    args = p.parse_args()

    try:
        download(
            args.url,
            audio_only=args.audio_only,
            quality=args.quality,
            out_dir=args.output_dir,
            custom_name=args.name,
        )
    except KeyboardInterrupt:
        sys.exit("\n⏹️  aborted by user")

if __name__ == "__main__":
    main()

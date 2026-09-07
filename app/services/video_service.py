"""
Video processing service.

Wraps optional FFmpeg-based HLS transcoding. If FFmpeg is not installed
on the host, the application gracefully falls back to serving the
original MP4 file directly -- HLS is a nice-to-have, never a hard
requirement for local development.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)


def ffmpeg_available() -> bool:
    """Return True if the `ffmpeg` binary is on PATH."""
    return shutil.which("ffmpeg") is not None


def convert_to_hls(input_path: str, output_dir: str, segment_seconds: int = 6) -> str | None:
    """Convert a source video file into an HLS playlist + segments.

    Args:
        input_path: Path to the source video file (e.g. an uploaded .mp4).
        output_dir: Directory where `master.m3u8` and `.ts` segments are written.
        segment_seconds: Target duration of each HLS segment.

    Returns:
        The path to `master.m3u8` on success, or None if FFmpeg is
        unavailable or the conversion failed (callers should fall back
        to serving the original MP4 in that case).
    """
    if not ffmpeg_available():
        logger.warning("FFmpeg not found on PATH; skipping HLS conversion, using MP4 fallback.")
        return None

    os.makedirs(output_dir, exist_ok=True)
    playlist_path = os.path.join(output_dir, "master.m3u8")
    segment_pattern = os.path.join(output_dir, "segment_%03d.ts")

    command = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-codec:", "copy",
        "-start_number", "0",
        "-hls_time", str(segment_seconds),
        "-hls_list_size", "0",
        "-f", "hls",
        "-hls_segment_filename", segment_pattern,
        playlist_path,
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, timeout=1800)
        return playlist_path
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        logger.error("HLS conversion failed for %s: %s", input_path, exc)
        return None


def resolve_stream_url(movie) -> tuple[str, str]:
    """Decide which URL/type to hand to the front-end video player.

    Returns a `(url, media_type)` tuple where `media_type` is either
    `"application/x-mpegURL"` for HLS or `"video/mp4"` for a direct
    file, letting the player (hls.js or native `<video>`) pick the
    right playback strategy.
    """
    if movie.video_url and movie.video_url.endswith(".m3u8"):
        return movie.video_url, "application/x-mpegURL"
    return movie.video_url, "video/mp4"

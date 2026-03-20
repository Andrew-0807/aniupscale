"""yt-dlp stream resolution + mpv launch logic.

Resolution order:
  1. Direct stream URLs (.m3u8, .mp4, etc.) → pass straight to mpv
  2. Plugin extractors (AnimeKai, HiAnime, AniWatch) → resolve via scraper/plugin
  3. yt-dlp binary (YouTube, Crunchyroll, etc.) → fallback
"""

from __future__ import annotations
import os
import re
import subprocess
import sys
from typing import Callable, Optional

import plugins  # plugin registry
import plugins.animekai  # noqa: registers AnimeKai extractor
import plugins.hianime  # noqa: registers HiAnime + AniWatch extractors


class PipelineError(Exception):
    """Raised for any recoverable pipeline failure."""


# ── Direct stream detection ────────────────────────────────────────────────

_STREAM_EXTS = re.compile(r"\.(m3u8?|mpd|mp4|webm|mkv|ts)(\?|$)", re.IGNORECASE)


def _is_direct_stream(url: str) -> bool:
    return bool(_STREAM_EXTS.search(url))


# ── Plugin resolver ────────────────────────────────────────────────────────


def _try_plugins(
    url: str,
    status_cb: Optional[Callable[[str], None]],
    episode: Optional[str] = None,
    lang: str = "sub",
) -> Optional[str]:
    """Try registered plugin extractors. Returns stream URL or None."""
    try:
        return plugins.resolve(
            url, status_cb or (lambda _: None), episode=episode, lang=lang
        )
    except Exception:
        return None


# ── yt-dlp ─────────────────────────────────────────────────────────────────


def resolve_stream_url(
    ytdlp_path: str,
    url: str,
    timeout: int = 30,
) -> str:
    """Run yt-dlp --get-url and return the first direct stream URL."""
    if not url.strip():
        raise PipelineError("URL is empty.")

    cmd = [
        ytdlp_path,
        "--get-url",
        "-f",
        "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "--no-playlist",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        raise PipelineError(
            f"yt-dlp not found at '{ytdlp_path}'. "
            "Install yt-dlp or set the correct path in Settings."
        )
    except subprocess.TimeoutExpired:
        raise PipelineError(f"yt-dlp timed out after {timeout} s.")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # Extract the most useful line from yt-dlp's verbose stderr
        detail = next(
            (ln for ln in reversed(stderr.splitlines()) if ln.strip()),
            "Unknown error",
        )
        raise PipelineError(f"yt-dlp error: {detail}")

    # yt-dlp may emit two lines for DASH (video URL + audio URL).
    # mpv handles the audio track itself; pass only the first URL.
    first_url = result.stdout.strip().splitlines()[0] if result.stdout.strip() else ""
    if not first_url:
        raise PipelineError(
            "yt-dlp returned no URL. "
            "The URL may be unsupported, geo-blocked, or require login."
        )
    return first_url


# ── mpv ────────────────────────────────────────────────────────────────────


def launch_mpv(
    mpv_path: str,
    stream_url: str,
    shader_arg: Optional[str],
    config_dir: Optional[str] = None,
) -> None:
    """Spawn mpv as a fully detached process (non-blocking).

    config_dir: path to folder containing mpv.conf and input.conf.
                Falls back to built-in defaults if not provided.
    """
    cmd = [mpv_path]

    if config_dir:
        cmd.append(f"--config-dir={config_dir}")
    else:
        # Inline defaults when no config dir is available
        cmd += [
            "--profile=gpu-hq",
            "--vo=gpu",
            "--hwdec=auto",
            "--keep-open=yes",
        ]

    if shader_arg:
        cmd.append(f"--glsl-shaders={shader_arg}")

    # URL must come after all options
    cmd.append(stream_url)

    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROC_GROUP = 0x00000200
            subprocess.Popen(
                cmd,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROC_GROUP,
                close_fds=True,
            )
        else:
            subprocess.Popen(cmd, start_new_session=True, close_fds=True)
    except FileNotFoundError:
        raise PipelineError(
            f"mpv not found at '{mpv_path}'. "
            "Install mpv or set the correct path in Settings."
        )
    except OSError as exc:
        raise PipelineError(f"Failed to launch mpv: {exc}")


# ── Orchestrator ───────────────────────────────────────────────────────────


def run_pipeline(
    url: str,
    mpv_path: str,
    ytdlp_path: str,
    shader_arg: Optional[str],
    status_cb: Optional[Callable[[str], None]] = None,
    episode: Optional[str] = None,
    lang: str = "sub",
) -> None:
    """Resolve URL then launch mpv.  Raises PipelineError on any failure."""
    _cb = status_cb or (lambda _: None)

    # 1. Direct stream URL — pass straight to mpv
    if _is_direct_stream(url):
        _cb("Direct stream detected")
        stream_url = url

    else:
        # 2. Try plugin extractors (AnimeKai, HiAnime, AniWatch)
        _cb("Trying plugin extractors...")
        stream_url = _try_plugins(url, _cb, episode=episode, lang=lang)

        # 3. Fall back to yt-dlp binary
        if not stream_url:
            _cb("Resolving with yt-dlp...")
            stream_url = resolve_stream_url(ytdlp_path, url)

    _cb("Launching mpv...")
    _config_dir = os.path.join(os.path.dirname(__file__), "mpv")
    if not os.path.isdir(_config_dir):
        _config_dir = None
    launch_mpv(mpv_path, stream_url, shader_arg, config_dir=_config_dir)

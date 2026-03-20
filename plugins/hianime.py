"""HiAnime and AniWatch stream resolver — uses yt-dlp Python API with plugin.

HiAnime: resolved via yt-dlp-hianime plugin (Megacloud decryption).
AniWatch: uses yt-dlp generic extractor (may not always work).
"""

from __future__ import annotations
from typing import Callable, Optional

from plugins import register


def _ytdlp_extract(
    url: str,
    status_cb: Callable[[str], None] = lambda _: None,
    episode: Optional[str] = None,
    lang: str = "sub",
) -> str:
    """Use yt-dlp Python API to extract stream URL."""
    import yt_dlp

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "format": "best",
        "forceurl": True,
        "simulate": True,
        "skip_download": True,
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if info:
            if "entries" in info:
                # If episode specified, try to find matching entry
                entries = list(info["entries"])
                if episode:
                    match = next(
                        (
                            e
                            for e in entries
                            if str(e.get("episode", "")) == episode
                            or str(e.get("episode_number", "")) == episode
                        ),
                        entries[0],
                    )
                    info = match
                else:
                    info = entries[0]
            stream = info.get("url")
            if stream:
                status_cb("Stream resolved via yt-dlp")
                return stream

    raise RuntimeError("yt-dlp could not extract stream URL")


@register(["hianime.to", "hianimez.to", "hianime.bz", "hianime.cx"])
def _hianime_handler(
    url: str,
    status_cb: Callable[[str], None] = lambda _: None,
    episode: Optional[str] = None,
    lang: str = "sub",
) -> str:
    return _ytdlp_extract(url, status_cb, episode=episode, lang=lang)


@register(["aniwatchtv.to", "aniwatch.to"])
def _aniwatch_handler(
    url: str,
    status_cb: Callable[[str], None] = lambda _: None,
    episode: Optional[str] = None,
    lang: str = "sub",
) -> str:
    return _ytdlp_extract(url, status_cb, episode=episode, lang=lang)

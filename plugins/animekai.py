"""AnimeKai stream resolver — direct scraping without yt-dlp.

Flow: page URL → scrape ani_id → fetch episodes → fetch servers → resolve m3u8.
Uses enc-dec.app for rolling token encryption/decryption.
"""

from __future__ import annotations
import json
import re
from typing import Callable, Optional

import requests
from bs4 import BeautifulSoup

from plugins import register

BASE = "https://anikai.to/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": BASE,
}
AJAX = {**HEADERS, "X-Requested-With": "XMLHttpRequest"}

ENC_URL = "https://enc-dec.app/api/enc-kai"
DEC_KAI_URL = "https://enc-dec.app/api/dec-kai"
DEC_MEGA_URL = "https://enc-dec.app/api/dec-mega"


def _ajax_get(url: str, params: dict = None) -> dict:
    r = requests.get(url, params=params, headers=AJAX, timeout=20)
    r.raise_for_status()
    return r.json()


def _encode_token(text: str) -> Optional[str]:
    r = requests.get(ENC_URL, params={"text": text}, timeout=15)
    r.raise_for_status()
    d = r.json()
    return d.get("result") if d.get("status") == 200 else None


def _decode_kai(text: str) -> Optional[dict]:
    r = requests.post(DEC_KAI_URL, json={"text": text}, timeout=15)
    r.raise_for_status()
    d = r.json()
    return d.get("result") if d.get("status") == 200 else None


def _decode_mega(text: str) -> Optional[dict]:
    r = requests.post(
        DEC_MEGA_URL,
        json={"text": text, "agent": HEADERS["User-Agent"]},
        timeout=15,
    )
    r.raise_for_status()
    d = r.json()
    return d.get("result") if d.get("status") == 200 else None


def _extract_slug(url: str) -> str:
    m = re.search(r"animekai\.\w+/watch/([^/?#]+)", url)
    if m:
        return m.group(1)
    m = re.search(r"animekai\.\w+/anime/([^/?#]+)", url)
    if m:
        return m.group(1)
    return url.rstrip("/").split("/")[-1]


def _scrape_ani_id(slug: str) -> str:
    page = requests.get(f"{BASE}watch/{slug}", headers=HEADERS, timeout=15)
    page.raise_for_status()
    soup = BeautifulSoup(page.text, "html.parser")
    sync = soup.select_one("script#syncData")
    if sync and sync.string:
        return json.loads(sync.string).get("anime_id", "")
    return ""


def _fetch_episodes(ani_id: str) -> list[dict]:
    token = _encode_token(ani_id)
    if not token:
        return []
    d = _ajax_get(f"{BASE}ajax/episodes/list", {"ani_id": ani_id, "_": token})
    html = d.get("result", "")
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    eps = []
    for a in soup.select(".eplist a"):
        langs = a.get("langs", "0")
        lang_bits = int(langs) if langs.isdigit() else 0
        eps.append(
            {
                "number": a.get("num", ""),
                "token": a.get("token", ""),
                "has_sub": bool(lang_bits & 1),
                "has_dub": bool(lang_bits & 2),
            }
        )
    return eps


def _fetch_servers(ep_token: str, lang: str = "sub") -> list[dict]:
    """Fetch servers for an episode, filtered by language.

    lang: "sub" or "dub"
    AnimeKai groups servers in .server-items[data-id="sub"] / [data-id="dub"]
    """
    enc = _encode_token(ep_token)
    if not enc:
        return []
    d = _ajax_get(f"{BASE}ajax/links/list", {"token": ep_token, "_": enc})
    html = d.get("result", "")
    soup = BeautifulSoup(html, "html.parser")

    # Find the matching language group
    target_group = None
    for group in soup.select(".server-items"):
        if group.get("data-id", "").lower() == lang:
            target_group = group
            break

    # Fallback: if no matching group, use the first available
    if target_group is None:
        target_group = soup.select_one(".server-items")
    if target_group is None:
        return []

    servers = []
    for s in target_group.select(".server"):
        servers.append(
            {
                "name": s.get_text(strip=True),
                "link_id": s.get("data-lid", ""),
            }
        )
    return servers


def _resolve_source(link_id: str) -> Optional[str]:
    enc = _encode_token(link_id)
    if not enc:
        return None
    resp = _ajax_get(f"{BASE}ajax/links/view", {"id": link_id, "_": enc})
    encrypted = resp.get("result", "")
    embed_data = _decode_kai(encrypted)
    if not embed_data:
        return None
    embed_url = embed_data.get("url", "")
    if not embed_url:
        return None

    vid_id = embed_url.rstrip("/").split("/")[-1]
    embed_base = (
        embed_url.rsplit("/e/", 1)[0]
        if "/e/" in embed_url
        else embed_url.rsplit("/", 1)[0]
    )
    media_r = requests.get(f"{embed_base}/media/{vid_id}", headers=HEADERS, timeout=15)
    media_r.raise_for_status()
    encrypted_media = media_r.json().get("result", "")

    final = _decode_mega(encrypted_media)
    if not final:
        return None
    sources = final.get("sources", [])
    if sources:
        return sources[0].get("url") or sources[0].get("file", "")
    return None


def resolve_animekai(
    url: str,
    status_cb: Callable[[str], None] = lambda _: None,
    episode: Optional[str] = None,
    lang: str = "sub",
) -> str:
    """Resolve an AnimeKai page URL to a direct m3u8 stream URL.

    episode: episode number string (e.g. "5"), or None for first episode.
    lang: "sub" or "dub"
    """
    status_cb("Extracting AnimeKai slug...")
    slug = _extract_slug(url)

    status_cb("Fetching anime metadata...")
    ani_id = _scrape_ani_id(slug)
    if not ani_id:
        raise RuntimeError(f"Could not find anime ID for slug: {slug}")

    status_cb("Fetching episode list...")
    episodes = _fetch_episodes(ani_id)
    if not episodes:
        raise RuntimeError("No episodes found")

    # Determine which episode to play
    # Priority: explicit episode param > URL hash #ep=N > first episode
    if episode:
        ep = next((e for e in episodes if e["number"] == episode), None)
        if ep is None:
            raise RuntimeError(
                f"Episode {episode} not found. Available: 1-{episodes[-1]['number']}"
            )
    else:
        ep_match = re.search(r"#ep=(\d+)", url)
        if ep_match:
            ep = ep_match.group(1)
            ep = next((e for e in episodes if e["number"] == ep), episodes[0])
        else:
            ep = episodes[0]

    # Check language availability
    if lang == "dub" and not ep.get("has_dub"):
        status_cb(f"Episode {ep['number']} has no dub, falling back to sub")
        lang = "sub"
    elif lang == "sub" and not ep.get("has_sub"):
        status_cb(f"Episode {ep['number']} has no sub, falling back to dub")
        lang = "dub"

    status_cb(f"Fetching {lang} servers for episode {ep['number']}...")
    servers = _fetch_servers(ep["token"], lang=lang)
    if not servers:
        raise RuntimeError(f"No {lang} servers found for episode {ep['number']}")

    for srv in servers:
        status_cb(f"Trying server: {srv['name']}...")
        try:
            stream = _resolve_source(srv["link_id"])
            if stream:
                status_cb(f"Resolved via {srv['name']} ({lang})")
                return stream
        except Exception:
            continue

    raise RuntimeError("All servers failed to resolve stream")


@register(["animekai.to", "animekai.cyou", "animekai.asia", "anikai.to"])
def _animekai_handler(
    url: str,
    status_cb: Callable[[str], None] = lambda _: None,
    episode: Optional[str] = None,
    lang: str = "sub",
) -> str:
    return resolve_animekai(url, status_cb, episode=episode, lang=lang)

"""AniUpscale stream resolver plugins for anime sites."""

from __future__ import annotations
from typing import Callable, Dict, List, Optional, Tuple

# Type: resolver(url, status_cb, episode, lang) -> stream_url
Resolver = Callable[..., str]

_REGISTRY: List[Tuple[List[str], Resolver]] = []


def register(domain_patterns: List[str]):
    """Decorator to register a resolver for given domain patterns."""

    def _wrap(fn: Resolver):
        _REGISTRY.append((domain_patterns, fn))
        return fn

    return _wrap


def resolve(
    url: str,
    status_cb: Callable[[str], None] = lambda _: None,
    episode: Optional[str] = None,
    lang: str = "sub",
) -> Optional[str]:
    """Try each registered resolver. Returns stream URL or None."""
    url_lower = url.lower()
    for patterns, resolver in _REGISTRY:
        for pat in patterns:
            if pat in url_lower:
                try:
                    return resolver(url, status_cb, episode=episode, lang=lang)
                except Exception:
                    return None
    return None


def supported_sites() -> List[str]:
    """Return list of supported domain patterns."""
    sites = []
    for patterns, _ in _REGISTRY:
        sites.extend(patterns)
    return sites

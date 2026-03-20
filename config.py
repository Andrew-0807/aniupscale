"""Load and persist app configuration to/from config.json."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

CONFIG_FILE = Path(__file__).parent / "config.json"

DEFAULT_CONFIG: Dict[str, Any] = {
    "mpv_path":    "mpv",
    "ytdlp_path":  "yt-dlp",
    "shaders_dir": "",
    "mode":        "A",
    "quality":     "Quality",
    "last_url":    "",
}


def load_config() -> Dict[str, Any]:
    """Return config merged over defaults (tolerates missing keys)."""
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as fh:
                cfg.update(json.load(fh))
        except (json.JSONDecodeError, OSError):
            pass  # Corrupt file — fall back to defaults
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist cfg to config.json; raises RuntimeError on I/O failure."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2, ensure_ascii=False)
    except OSError as exc:
        raise RuntimeError(f"Cannot save config: {exc}") from exc

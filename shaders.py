"""Anime4K shader preset mappings and shader-argument builder."""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# (mode, quality) -> ordered list of .glsl filenames
SHADER_PRESETS: Dict[Tuple[str, str], List[str]] = {
    ("A", "Fast"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_S.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
    ("A", "Balanced"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_M.glsl",
        "Anime4K_Upscale_CNN_x2_M.glsl",
    ],
    ("A", "Quality"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_L.glsl",
        "Anime4K_Upscale_CNN_x2_L.glsl",
    ],
    ("B", "Fast"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_Soft_S.glsl",
        "Anime4K_Upscale_CNN_x2_S.glsl",
    ],
    ("B", "Balanced"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_Soft_M.glsl",
        "Anime4K_Upscale_CNN_x2_M.glsl",
    ],
    ("B", "Quality"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_Soft_L.glsl",
        "Anime4K_Upscale_CNN_x2_L.glsl",
    ],
    ("C", "Fast"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_CNN_x2_L.glsl",
    ],
    ("C", "Balanced"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_CNN_x2_L.glsl",
    ],
    ("C", "Quality"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_CNN_x2_L.glsl",
    ],
    # ── Extended tiers ────────────────────────────────────────────────────
    ("A", "Ultra"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_VL.glsl",
        "Anime4K_Upscale_CNN_x2_VL.glsl",
    ],
    ("A", "Extreme"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_UL.glsl",
        "Anime4K_Upscale_CNN_x2_UL.glsl",
    ],
    ("B", "Ultra"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_Soft_VL.glsl",
        "Anime4K_Upscale_CNN_x2_VL.glsl",
    ],
    ("B", "Extreme"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Restore_CNN_Soft_UL.glsl",
        "Anime4K_Upscale_CNN_x2_UL.glsl",
    ],
    ("C", "Ultra"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_CNN_x2_VL.glsl",
    ],
    ("C", "Extreme"): [
        "Anime4K_Clamp_Highlights.glsl",
        "Anime4K_Upscale_CNN_x2_UL.glsl",
    ],
}

MODE_LABELS: Dict[str, str] = {
    "A": "Mode A  —  Restore + Upscale (best for most anime)",
    "B": "Mode B  —  Soft Restore + Upscale (blurry / watercolour art)",
    "C": "Mode C  —  Upscale Only, no restore (clean source)",
}

QUALITY_LABELS: Dict[str, str] = {
    "Fast": "Fast     — S-size, real-time on most GPUs",
    "Balanced": "Balanced — M-size, good quality/performance",
    "Quality": "Quality  — L-size, needs decent GPU",
    "Ultra": "Ultra    — VL-size, best quality, needs strong GPU",
    "Extreme": "Extreme  — UL-size, maximum quality, very demanding",
}


def build_shader_arg(shaders_dir: str, mode: str, quality: str) -> str:
    """Return the value for mpv's --glsl-shaders=... flag."""
    key = (mode, quality)
    filenames = SHADER_PRESETS.get(key, SHADER_PRESETS[("A", "Quality")])
    base = Path(shaders_dir)
    paths = [str(base / fn) for fn in filenames]
    # mpv uses ";" as list separator on Windows (drive letters contain ":"),
    # and ":" on POSIX.
    sep = ";" if sys.platform == "win32" else ":"
    return sep.join(paths)


def shader_filenames(mode: str, quality: str) -> List[str]:
    """Return just the filenames for a given preset (used for validation)."""
    return SHADER_PRESETS.get((mode, quality), [])

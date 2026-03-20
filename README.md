# AniUpscale

Real-time anime upscaling in a clean desktop GUI — powered by
**Anime4K shaders**, **mpv**, and **yt-dlp**, wrapped in a dark-themed
Python + CustomTkinter interface.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **Real-time 2x upscaling** via GPU-accelerated Anime4K GLSL shaders
- **Stream anything** — paste a URL and AniUpscale resolves it through plugins or yt-dlp
- **3 upscaling modes**: Restore + Upscale, Soft Restore + Upscale, Upscale Only
- **3 quality tiers**: Fast (S), Balanced (M), Quality (L) shader sizes
- **Built-in plugins** for AnimeKai, HiAnime, and AniWatch (scrapes stream URLs directly)
- **Portable mpv config** — ships its own `mpv.conf`, `input.conf`, and OSC skin
- **Dark glassmorphic UI** with emerald accent palette

---

## Prerequisites

You need **three external tools** installed. None are bundled.

### 1 · Python 3.10+

Download from <https://www.python.org/downloads/> and ensure `python` is on your PATH.

### 2 · mpv

**Windows (recommended — portable)**

1. Download the latest portable zip from <https://mpv.io/installation/>
   (direct mirror: <https://sourceforge.net/projects/mpv-player-windows/files/>).
2. Extract to a permanent folder, e.g. `C:\tools\mpv\`.
3. Add that folder to your system PATH
   *or* set the path in Settings → Path Overrides inside AniUpscale.

**Package managers:**

```
winget install mpv
# or
scoop install mpv
# or
choco install mpv
```

Verify: `mpv --version`.

### 3 · yt-dlp

```
pip install yt-dlp
# or
winget install yt-dlp
# or
scoop install yt-dlp
```

Verify: `yt-dlp --version`.

### 4 · Anime4K shaders

1. Download from <https://github.com/bloc97/Anime4K/releases> — grab `Anime4K_v4.x.zip`.
2. Extract all `.glsl` files into a single flat folder.
3. In AniUpscale → Settings → **Shaders dir**, point to that folder.

> The `shaders/` directory in this repo already contains the required shader files.

---

## Installation

```bash
git clone https://github.com/user/aniupscale.git
cd aniupscale

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

python main.py
```

---

## Usage

1. Paste any **yt-dlp-supported URL** into the *Stream URL* field
   (YouTube, Crunchyroll, Twitch, direct `.m3u8` / `.mp4` links, etc.).
2. Open **Settings** and configure your preferred mode and quality.
3. Press **Watch** (or hit Enter).

AniUpscale resolves the stream via plugins or yt-dlp, then launches mpv with the selected Anime4K shaders.

### Supported sites (built-in plugins)

| Site | Resolver |
|------|----------|
| AnimeKai (`animekai.to`, `.cyou`, `.asia`) | Direct scraping (no yt-dlp needed) |
| HiAnime (`hianime.to`, `.bz`, `.cx`) | yt-dlp Python API |
| AniWatch (`aniwatchtv.to`, `.to`) | yt-dlp Python API |
| Everything else | Falls back to yt-dlp binary |

### Shader presets

| Mode + Quality | Shaders loaded |
|----------------|----------------|
| A · Fast | Clamp_Highlights + Restore_CNN_S + Upscale_CNN_x2_S |
| A · Balanced | Clamp_Highlights + Restore_CNN_M + Upscale_CNN_x2_M |
| A · Quality | Clamp_Highlights + Restore_CNN_L + Upscale_CNN_x2_L |
| B · Fast | Clamp_Highlights + Restore_CNN_Soft_S + Upscale_CNN_x2_S |
| B · Balanced | Clamp_Highlights + Restore_CNN_Soft_M + Upscale_CNN_x2_M |
| B · Quality | Clamp_Highlights + Restore_CNN_Soft_L + Upscale_CNN_x2_L |
| C · Fast | Clamp_Highlights + Upscale_CNN_x2_S |
| C · Balanced | Clamp_Highlights + Upscale_CNN_x2_M |
| C · Quality | Clamp_Highlights + Upscale_CNN_x2_L |

---

## Project structure

```
aniupscale/
├── main.py              # Entry point
├── app.py               # CustomTkinter UI (AniUpscaleApp)
├── pipeline.py          # yt-dlp resolve + mpv launch logic
├── config.py            # Load / save config.json
├── shaders.py           # Shader preset mappings + CLI arg builder
├── requirements.txt
├── LICENSE
├── .gitignore
│
├── plugins/             # Stream resolver plugins
│   ├── __init__.py      # Plugin registry
│   ├── animekai.py      # AnimeKai scraper
│   └── hianime.py       # HiAnime / AniWatch via yt-dlp
│
├── shaders/             # Anime4K GLSL shader files
│   └── *.glsl
│
├── mpv/                 # Portable mpv configuration
│   ├── mpv.conf         # Video output, subtitles, window settings
│   ├── input.conf       # Keybindings
│   └── scripts/
│       └── nova-osc.lua # Custom glassmorphic OSC skin
│
└── Theme/
    └── nova-osc.lua     # OSC skin (copy for manual mpv installs)
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `yt-dlp not found` | Install yt-dlp or set path in Settings |
| `mpv not found` | Install mpv or set path in Settings |
| `yt-dlp error: Unsupported URL` | URL not supported — check yt-dlp compatibility |
| mpv opens but no upscaling visible | Verify the shaders folder path; check filenames match |
| Shaders slow / stuttering | Switch to **Fast** quality or a lighter mode |
| Black screen in mpv | Try removing `--hwdec=auto` by launching mpv manually first |

---

## Third-party credits

| Component | License | Source |
|-----------|---------|--------|
| [Anime4K shaders](https://github.com/bloc97/Anime4K) | MIT | bloc97 et al. — included in `shaders/` |
| [mpv](https://mpv.io) | GPL-2.0+ / LGPL-2.1+ | External binary — not bundled |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The Unlicense | External binary — not bundled |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | MIT | Installed via pip |

The Anime4K `.glsl` shader files in `shaders/` are redistributed under the [MIT license](https://github.com/bloc97/Anime4K/blob/master/LICENSE). All other code in this repository is original work.

---

## License

MIT — see [LICENSE](LICENSE).

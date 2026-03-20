<div align="center">

# AniUpscale

**Real-time anime upscaling for your desktop.**

Powered by Anime4K shaders, mpv, and yt-dlp — wrapped in a dark-themed Python + CustomTkinter interface.

![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge&logo=open-source-initiative&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey?style=for-the-badge&logo=windows&logoColor=white)

---

</div>

## Preview

<table>
  <tr>
    <td align="center"><b>Compact View</b></td>
    <td align="center"><b>Settings Expanded</b></td>
  </tr>
  <tr>
    <td><img src="images/Small UI.png" alt="AniUpscale compact view" width="100%"></td>
    <td><img src="images/Expanded UI.png" alt="AniUpscale with settings panel expanded" width="100%"></td>
  </tr>
</table>

---

## Features

| Feature | Description |
|---------|-------------|
| **Real-time 2x upscaling** | GPU-accelerated Anime4K GLSL shaders applied in real time |
| **Universal streaming** | Paste any URL — resolved via built-in plugins or yt-dlp |
| **3 upscaling modes** | Restore + Upscale, Soft Restore + Upscale, Upscale Only |
| **3 quality tiers** | Fast (S), Balanced (M), Quality (L) shader sizes |
| **Built-in plugins** | Direct scraping for AnimeKai, HiAnime, AniWatch — no yt-dlp needed |
| **Portable mpv config** | Ships its own `mpv.conf`, `input.conf`, and custom OSC skin |
| **Dark glassmorphic UI** | Emerald accent palette, tactile button feedback, staggered reveals |

---

## Prerequisites

AniUpscale requires three external tools. None are bundled with this repository.

<details>
<summary><b>1 &middot; Python 3.10+</b></summary>

Download from [python.org](https://www.python.org/downloads/) and ensure `python` is on your PATH.

</details>

<details>
<summary><b>2 &middot; mpv</b></summary>

**Option A — Portable (recommended):**

1. Download the latest portable zip from [mpv.io](https://mpv.io/installation/) or [Sourceforge mirror](https://sourceforge.net/projects/mpv-player-windows/files/).
2. Extract to a permanent folder, e.g. `C:\tools\mpv\`.
3. Add that folder to your system PATH, or set the path in **Settings → Path Overrides** inside AniUpscale.

**Option B — Package manager:**

```bash
winget install mpv
# or
scoop install mpv
# or
choco install mpv
```

Verify: `mpv --version`

</details>

<details>
<summary><b>3 &middot; yt-dlp</b></summary>

```bash
pip install yt-dlp
# or
winget install yt-dlp
# or
scoop install yt-dlp
```

Verify: `yt-dlp --version`

</details>

<details>
<summary><b>4 &middot; Anime4K shaders</b></summary>

1. Download from [Anime4K releases](https://github.com/bloc97/Anime4K/releases) — grab `Anime4K_v4.x.zip`.
2. Extract all `.glsl` files into a single flat folder.
3. In AniUpscale → Settings → **Shaders dir**, point to that folder.

> **Note:** The `shaders/` directory in this repository already contains all required shader files pre-bundled.

</details>

---

## Installation

```bash
# Clone the repository
git clone https://github.com/Andrew-0807/aniupscale.git
cd aniupscale

# Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

---

## Usage

1. Paste any **yt-dlp-supported URL** into the Stream URL field — YouTube, Crunchyroll, Twitch, direct `.m3u8` / `.mp4` links, etc.
2. Open **Settings** and configure your preferred mode and quality tier.
3. Press **Watch** (or hit Enter).

AniUpscale resolves the stream via built-in plugins or yt-dlp, then launches mpv with the selected Anime4K shaders.

### Supported Sites

| Site | Resolver | Method |
|------|----------|--------|
| AnimeKai (`animekai.to`, `.cyou`, `.asia`, `anikai.to`) | Built-in plugin | Direct scraping |
| HiAnime (`hianime.to`, `.bz`, `.cx`) | Built-in plugin | yt-dlp Python API |
| AniWatch (`aniwatchtv.to`, `.to`) | Built-in plugin | yt-dlp Python API |
| Everything else | yt-dlp binary | Generic extractor |

### Shader Presets

| Preset | Fast (S) | Balanced (M) | Quality (L) |
|--------|----------|--------------|-------------|
| **Mode A** — Restore + Upscale | Clamp + Restore\_S + Upscale\_S | Clamp + Restore\_M + Upscale\_M | Clamp + Restore\_L + Upscale\_L |
| **Mode B** — Soft Restore + Upscale | Clamp + SoftRestore\_S + Upscale\_S | Clamp + SoftRestore\_M + Upscale\_M | Clamp + SoftRestore\_L + Upscale\_L |
| **Mode C** — Upscale Only | Clamp + Upscale\_S | Clamp + Upscale\_M | Clamp + Upscale\_L |

---

## Project Structure

```
aniupscale/
├── main.py                    Entry point
├── app.py                     CustomTkinter UI (AniUpscaleApp)
├── pipeline.py                yt-dlp resolve + mpv launch logic
├── config.py                  Load / save config.json
├── shaders.py                 Shader preset mappings + CLI arg builder
├── requirements.txt
├── LICENSE
├── .gitignore
│
├── plugins/
│   ├── __init__.py            Plugin registry
│   ├── animekai.py            AnimeKai stream resolver
│   └── hianime.py             HiAnime / AniWatch stream resolver
│
├── shaders/                   Anime4K GLSL shader files (bundled)
│   └── *.glsl
│
├── mpv/                       Portable mpv configuration
│   ├── mpv.conf               Video output, subtitles, window
│   ├── input.conf             Custom keybindings
│   └── scripts/
│       └── nova-osc.lua       Glassmorphic OSC skin
│
├── Theme/
│   └── nova-osc.lua           OSC skin for manual mpv installs
│
└── images/
    ├── Small UI.png           Compact view screenshot
    └── Expanded UI.png        Settings expanded screenshot
```

---

## Troubleshooting

| Symptom | Resolution |
|---------|------------|
| `yt-dlp not found` | Install yt-dlp or set the correct path in Settings → Path Overrides |
| `mpv not found` | Install mpv or set the correct path in Settings → Path Overrides |
| `yt-dlp error: Unsupported URL` | The URL is not supported by yt-dlp — check [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md) |
| mpv opens but no upscaling visible | Verify the shaders folder path and ensure filenames match exactly |
| Shaders slow or stuttering | Switch to **Fast** quality tier or use **Mode C** (upscale only) |
| Black screen in mpv | Remove `--hwdec=auto` — test by launching mpv manually first |

---

## Third-Party Credits

| Component | License | Notes |
|-----------|---------|-------|
| [Anime4K](https://github.com/bloc97/Anime4K) | MIT | GLSL shaders — redistributed in `shaders/` under [MIT license](https://github.com/bloc97/Anime4K/blob/master/LICENSE) |
| [mpv](https://mpv.io) | GPL-2.0+ / LGPL-2.1+ | Media player — external binary, not bundled |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | The Unlicense | Video extractor — external binary, not bundled |
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | MIT | Python UI framework — installed via pip |

All application code in this repository is original work. Only the `.glsl` shader files in `shaders/` originate from the Anime4K project (MIT licensed, redistributed with permission).

---

## License

[MIT](LICENSE) — do whatever you want, no warranty implied.

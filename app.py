"""AniUpscale — CustomTkinter UI.

Design follows taste-skill principles:
- No pure black (#000000) — warm off-black base
- No AI Purple — desaturated emerald accent
- Inner borders for depth (liquid glass refraction)
- Tactile button feedback (scale on press)
- Off-black, zinc-950, charcoal palette
"""

from __future__ import annotations
import os
import threading
from pathlib import Path
from tkinter import filedialog
from typing import Optional

import customtkinter as ctk

from config import load_config, save_config
from pipeline import PipelineError, run_pipeline
from shaders import MODE_LABELS, QUALITY_LABELS, build_shader_arg

# ── Palette (taste-skill compliant) ─────────────────────────────────────────
# Off-black warm base — never pure #000000
# Emerald desaturated accent — Lila Ban compliant (no AI purple)
# Zinc/slate neutrals for surfaces and borders
C = {
    "bg": "#0c0c0e",  # warm off-black base (Zinc-950)
    "surface": "#161618",  # elevated card surface
    "surface2": "#1c1c1f",  # inset surface (entry bg)
    "border": "#27272a",  # subtle border (Zinc-800)
    "border_hi": "#3f3f46",  # highlight border (Zinc-700)
    "accent": "#10b981",  # emerald primary (desaturated)
    "accent_h": "#059669",  # emerald hover (deeper)
    "accent_mute": "#064e3b",  # emerald muted bg
    "accent_sub": "#022c22",  # emerald subtle (deepest)
    "txt": "#e4e4e7",  # primary text (Zinc-200)
    "txt2": "#71717a",  # secondary text (Zinc-500)
    "txt3": "#52525b",  # tertiary text (Zinc-600)
    "ok": "#34d399",  # success (emerald-400)
    "warn": "#fbbf24",  # working amber
    "err": "#f87171",  # error red
    "inner_glow": "#ffffff08",  # inner border highlight (subtle)
}

_ST_IDLE = "idle"
_ST_WORK = "working"
_ST_OK = "ok"
_ST_ERR = "err"

_ST_COLOR = {
    _ST_IDLE: C["txt2"],
    _ST_WORK: C["warn"],
    _ST_OK: C["ok"],
    _ST_ERR: C["err"],
}


# ── Typography ──────────────────────────────────────────────────────────────


def _font(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    return ctk.CTkFont(family="Segoe UI", size=size, weight=weight)


# ── Reusable components ─────────────────────────────────────────────────────


class _SectionLabel(ctk.CTkLabel):
    """Eyebrow label for section headers."""

    def __init__(self, parent, text: str, **kw):
        super().__init__(
            parent,
            text=text,
            font=_font(9, "bold"),
            text_color=C["txt3"],
            anchor="w",
            **kw,
        )


class _Card(ctk.CTkFrame):
    """Surface card with inner border for depth (liquid glass refraction)."""

    def __init__(self, parent, **kw):
        super().__init__(
            parent,
            fg_color=C["surface"],
            corner_radius=12,
            border_color=C["border"],
            border_width=1,
            **kw,
        )


class _InnerCard(ctk.CTkFrame):
    """Nested inner card — creates depth illusion via lighter border."""

    def __init__(self, parent, **kw):
        super().__init__(
            parent,
            fg_color=C["surface2"],
            corner_radius=8,
            border_color=C["border_hi"],
            border_width=1,
            **kw,
        )


def _entry(
    parent, placeholder: str = "", initial: str = "", height: int = 34
) -> ctk.CTkEntry:
    e = ctk.CTkEntry(
        parent,
        placeholder_text=placeholder,
        font=_font(12),
        fg_color=C["surface2"],
        border_color=C["border"],
        border_width=1,
        text_color=C["txt"],
        placeholder_text_color=C["txt3"],
        height=height,
        corner_radius=8,
    )
    if initial:
        e.insert(0, initial)
    return e


def _browse_btn(parent, command) -> ctk.CTkButton:
    return ctk.CTkButton(
        parent,
        text="...",
        width=32,
        height=30,
        corner_radius=6,
        fg_color=C["accent_mute"],
        hover_color=C["accent"],
        text_color=C["txt"],
        font=_font(12),
        command=command,
    )


# ── Tactile button (taste-skill: scale on press) ────────────────────────────


class _TactileButton(ctk.CTkButton):
    """Button with physical press feedback — visual scale on active."""

    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self._press_active = False
        self.bind("<ButtonPress-1>", self._on_press, add="+")
        self.bind("<ButtonRelease-1>", self._on_release, add="+")
        self.bind("<Leave>", self._on_leave, add="+")

    def _on_press(self, _event=None):
        self._press_active = True
        # Tactile feedback: slightly darken on press
        current = self.cget("fg_color")
        if current and current != "transparent":
            self._pre_press_color = current
            self.configure(fg_color=self.cget("hover_color"))

    def _on_release(self, _event=None):
        if self._press_active:
            self._press_active = False
            if hasattr(self, "_pre_press_color"):
                self.configure(fg_color=self._pre_press_color)

    def _on_leave(self, _event=None):
        if self._press_active:
            self._press_active = False
            if hasattr(self, "_pre_press_color"):
                self.configure(fg_color=self._pre_press_color)


# ── Main window ─────────────────────────────────────────────────────────────


class AniUpscaleApp(ctk.CTk):
    _WIN_COMPACT = "620x460"
    _WIN_EXPANDED = "620x790"

    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        super().__init__()

        # Window icon
        _ico = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.isfile(_ico):
            self.iconbitmap(_ico)

        self.title("AniUpscale")
        self.geometry(self._WIN_COMPACT)
        self.minsize(560, 420)
        self.configure(fg_color=C["bg"])
        self.resizable(True, True)

        self._cfg = load_config()
        self._settings_open = False

        self._build_header()
        self._build_body()
        self._build_settings_panel()

        # Restore last URL
        last = self._cfg.get("last_url", "")
        if last:
            self.url_entry.insert(0, last)

    # ── Header ─────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = ctk.CTkFrame(self, fg_color=C["surface"], corner_radius=0)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            hdr,
            text="AniUpscale",
            font=_font(24, "bold"),
            text_color=C["txt"],
        ).grid(row=0, column=0, padx=24, pady=(18, 0), sticky="w")

        # Subtitle
        ctk.CTkLabel(
            hdr,
            text="Real-time upscaling  \u00b7  Anime4K + mpv + yt-dlp",
            font=_font(11),
            text_color=C["txt2"],
        ).grid(row=1, column=0, padx=24, pady=(2, 16), sticky="w")

        # Accent rule (subtle, not neon)
        ctk.CTkFrame(
            hdr,
            height=1,
            fg_color=C["accent_mute"],
            corner_radius=0,
        ).grid(row=2, column=0, sticky="ew")

    # ── Body ───────────────────────────────────────────────────────────────

    def _build_body(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=20, pady=18)
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        # ── URL card ───────────────────────────────────────────────────────
        url_card = _Card(body)
        url_card.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        url_card.grid_columnconfigure(0, weight=1)

        _SectionLabel(url_card, "STREAM URL").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(12, 2)
        )

        input_row = ctk.CTkFrame(url_card, fg_color="transparent")
        input_row.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14)
        )
        input_row.grid_columnconfigure(0, weight=1)

        self.url_entry = _entry(
            input_row,
            placeholder="Paste a YouTube, Crunchyroll, or other yt-dlp URL",
            height=42,
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.url_entry.bind("<Return>", lambda _e: self._on_watch())

        self.watch_btn = _TactileButton(
            input_row,
            text="Watch",
            font=_font(13, "bold"),
            fg_color=C["accent"],
            hover_color=C["accent_h"],
            text_color="#ffffff",
            width=110,
            height=42,
            corner_radius=8,
            command=self._on_watch,
        )
        self.watch_btn.grid(row=0, column=1)

        # ── Playback options card (sub/dub + episode) ───────────────────────
        opts_card = _Card(body)
        opts_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        opts_card.grid_columnconfigure(1, weight=1)

        # Sub / Dub toggle
        _SectionLabel(opts_card, "AUDIO").grid(
            row=0, column=0, sticky="w", padx=14, pady=(10, 2)
        )
        self._lang_var = ctk.StringVar(value=self._cfg.get("lang", "sub"))
        lang_row = ctk.CTkFrame(opts_card, fg_color="transparent")
        lang_row.grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))
        for i, (val, label) in enumerate([("sub", "Sub"), ("dub", "Dub")]):
            ctk.CTkRadioButton(
                lang_row,
                text=label,
                variable=self._lang_var,
                value=val,
                font=_font(12),
                text_color=C["txt"],
                fg_color=C["accent"],
                hover_color=C["accent_h"],
                border_color=C["border_hi"],
                radiobutton_width=16,
                radiobutton_height=16,
                command=self._on_lang_change,
            ).grid(row=0, column=i, padx=(0 if i == 0 else 16, 0))

        # Episode number
        _SectionLabel(opts_card, "EPISODE").grid(
            row=0, column=1, sticky="w", padx=14, pady=(10, 2)
        )
        ep_row = ctk.CTkFrame(opts_card, fg_color="transparent")
        ep_row.grid(row=1, column=1, sticky="w", padx=14, pady=(0, 6))

        self._ep_entry = _entry(
            ep_row,
            placeholder="auto",
            initial=self._cfg.get("episode", ""),
            height=34,
        )
        self._ep_entry.configure(width=100)
        self._ep_entry.grid(row=0, column=0)
        self._ep_entry.bind(
            "<FocusOut>",
            lambda _e: self._on_ep_change(),
        )

        ctk.CTkLabel(
            ep_row,
            text="(blank = first)",
            font=_font(10),
            text_color=C["txt3"],
        ).grid(row=0, column=1, padx=(8, 0))

        # ── Status bar ─────────────────────────────────────────────────────
        st_card = _Card(body)
        st_card.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        st_card.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(
            st_card,
            text="\u25cf",
            font=_font(9),
            text_color=C["txt3"],
            width=20,
        )
        self._dot.grid(row=0, column=0, padx=(14, 4), pady=10)

        self._status_lbl = ctk.CTkLabel(
            st_card,
            text="Ready \u2014 paste a URL and press Watch",
            font=_font(12),
            text_color=C["txt2"],
            anchor="w",
        )
        self._status_lbl.grid(row=0, column=1, sticky="ew", padx=(0, 14), pady=10)

        # ── Settings toggle row ────────────────────────────────────────────
        tog_row = ctk.CTkFrame(body, fg_color="transparent")
        tog_row.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        tog_row.grid_columnconfigure(1, weight=1)

        self._tog_btn = ctk.CTkButton(
            tog_row,
            text="Settings",
            font=_font(11),
            fg_color="transparent",
            hover_color=C["surface2"],
            text_color=C["txt2"],
            border_color=C["border"],
            border_width=1,
            width=110,
            height=30,
            corner_radius=6,
            command=self._toggle_settings,
        )
        self._tog_btn.grid(row=0, column=0, sticky="w")

        self._preset_lbl = ctk.CTkLabel(
            tog_row,
            text=self._preset_summary(),
            font=_font(11),
            text_color=C["accent"],
            anchor="e",
        )
        self._preset_lbl.grid(row=0, column=1, sticky="e")

    # ── Settings panel (collapsible) ───────────────────────────────────────

    def _build_settings_panel(self):
        panel = _Card(self._body)
        panel.grid_columnconfigure((0, 1), weight=1)
        self._settings_panel = panel

        row = 0

        # ── Mode ───────────────────────────────────────────────────────────
        _SectionLabel(panel, "ANIME4K MODE").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=14, pady=(14, 2)
        )
        row += 1

        # Inner card for mode selection
        mode_inner = _InnerCard(panel)
        mode_inner.grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 6)
        )
        self._mode_var = ctk.StringVar(value=self._cfg.get("mode", "A"))
        for i, (m, lbl) in enumerate(MODE_LABELS.items()):
            ctk.CTkRadioButton(
                mode_inner,
                text=lbl,
                variable=self._mode_var,
                value=m,
                font=_font(12),
                text_color=C["txt"],
                fg_color=C["accent"],
                hover_color=C["accent_h"],
                border_color=C["border_hi"],
                radiobutton_width=16,
                radiobutton_height=16,
                command=self._on_preset_change,
            ).grid(
                row=i,
                column=0,
                sticky="w",
                padx=12,
                pady=(8 if i == 0 else 2, 8 if i == 2 else 2),
            )
        row += 1

        # ── Quality ────────────────────────────────────────────────────────
        _SectionLabel(panel, "QUALITY PRESET").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 2)
        )
        row += 1

        qual_inner = _InnerCard(panel)
        qual_inner.grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 6)
        )
        self._qual_var = ctk.StringVar(value=self._cfg.get("quality", "Quality"))
        _qual_items = list(QUALITY_LABELS.items())
        for i, (q, lbl) in enumerate(_qual_items):
            ctk.CTkRadioButton(
                qual_inner,
                text=lbl,
                variable=self._qual_var,
                value=q,
                font=_font(12),
                text_color=C["txt"],
                fg_color=C["accent"],
                hover_color=C["accent_h"],
                border_color=C["border_hi"],
                radiobutton_width=16,
                radiobutton_height=16,
                command=self._on_preset_change,
            ).grid(
                row=i,
                column=0,
                sticky="w",
                padx=12,
                pady=(8 if i == 0 else 2, 8 if i == len(_qual_items) - 1 else 2),
            )
        row += 1

        # ── Path overrides ─────────────────────────────────────────────────
        _SectionLabel(panel, "PATH OVERRIDES").grid(
            row=row, column=0, columnspan=2, sticky="w", padx=14, pady=(10, 2)
        )
        row += 1

        paths_inner = _InnerCard(panel)
        paths_inner.grid(
            row=row, column=0, columnspan=2, sticky="ew", padx=14, pady=(0, 14)
        )
        paths_inner.grid_columnconfigure(1, weight=1)

        self.mpv_entry = self._path_row(paths_inner, "mpv", "mpv_path", 0, False)
        self.ytdlp_entry = self._path_row(paths_inner, "yt-dlp", "ytdlp_path", 1, False)
        self.shaders_entry = self._path_row(
            paths_inner, "Shaders dir", "shaders_dir", 2, True
        )

        # Placeholders when value equals default sentinel
        if self._cfg.get("mpv_path", "mpv") in ("mpv", ""):
            self.mpv_entry.configure(placeholder_text="mpv  (must be on PATH)")
        if self._cfg.get("ytdlp_path", "yt-dlp") in ("yt-dlp", ""):
            self.ytdlp_entry.configure(placeholder_text="yt-dlp  (must be on PATH)")
        if not self._cfg.get("shaders_dir"):
            self.shaders_entry.configure(
                placeholder_text="Folder with Anime4K .glsl files"
            )

        # Edit mpv config button
        row += 1
        mpv_cfg_btn = ctk.CTkButton(
            panel,
            text="Edit mpv config",
            font=_font(11),
            fg_color=C["surface2"],
            hover_color=C["border_hi"],
            text_color=C["txt2"],
            border_color=C["border"],
            border_width=1,
            height=30,
            corner_radius=6,
            command=self._open_mpv_config,
        )
        mpv_cfg_btn.grid(
            row=row, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 14)
        )

        # Don't show the panel yet
        panel.grid_forget()

    def _path_row(
        self,
        parent: ctk.CTkFrame,
        label: str,
        cfg_key: str,
        row: int,
        is_dir: bool,
    ) -> ctk.CTkEntry:
        ctk.CTkLabel(
            parent,
            text=label,
            font=_font(11),
            text_color=C["txt2"],
            anchor="w",
            width=82,
        ).grid(row=row, column=0, padx=(12, 6), pady=7, sticky="w")

        e = _entry(parent, height=30, initial=self._cfg.get(cfg_key, ""))
        e.grid(row=row, column=1, sticky="ew", padx=(0, 6), pady=7)
        e.bind(
            "<FocusOut>", lambda _ev, k=cfg_key, ent=e: self._save_path(k, ent.get())
        )

        def _browse(ent=e, d=is_dir, k=cfg_key):
            p = filedialog.askdirectory() if d else filedialog.askopenfilename()
            if p:
                ent.delete(0, "end")
                ent.insert(0, p)
                self._save_path(k, p)

        _browse_btn(parent, _browse).grid(row=row, column=2, padx=(0, 10), pady=7)
        return e

    # ── Toggle (taste-skill compliant: spring-like snap, staggered reveal) ──

    def _stagger_reveal(self, parent, delay_ms: int = 18):
        """Cascade-fade children in with staggered delays (taste-skill §4)."""
        children = parent.winfo_children()
        for i, child in enumerate(children):
            # Hide then schedule show — creates waterfall reveal
            child.grid_remove()
            child.after(delay_ms * i, child.grid)

    def _toggle_settings(self):
        self._settings_open = not self._settings_open
        if self._settings_open:
            self._settings_panel.grid(row=4, column=0, sticky="ew", pady=(4, 0))
            self._settings_panel.update_idletasks()
            self._tog_btn.configure(text="Close Settings")
            # Snap expand, then stagger content in
            self.geometry(f"620x{self._settings_panel.winfo_height() + 480}")
            self.after(30, lambda: self._stagger_reveal(self._settings_panel))
        else:
            self._tog_btn.configure(text="Settings")
            self.geometry("620x460")
            self.after(80, self._settings_panel.grid_forget)

    # ── Preset helpers ─────────────────────────────────────────────────────

    def _preset_summary(self) -> str:
        m = self._cfg.get("mode", "A")
        q = self._cfg.get("quality", "Quality")
        return f"Mode {m}  \u00b7  {q}"

    def _on_preset_change(self):
        self._cfg["mode"] = self._mode_var.get()
        self._cfg["quality"] = self._qual_var.get()
        self._preset_lbl.configure(text=self._preset_summary())
        self._flush_cfg()

    # ── Status ─────────────────────────────────────────────────────────────

    def _set_status(self, text: str, state: str = _ST_IDLE):
        col = _ST_COLOR.get(state, C["txt2"])
        self._status_lbl.configure(text=text, text_color=col)
        self._dot.configure(text_color=col)

    # ── Config I/O ─────────────────────────────────────────────────────────

    def _save_path(self, key: str, value: str):
        self._cfg[key] = value
        self._flush_cfg()

    def _flush_cfg(self):
        try:
            save_config(self._cfg)
        except RuntimeError:
            pass

    def _open_mpv_config(self):
        """Open the mpv/ config folder in Explorer for editing."""
        mpv_dir = os.path.join(os.path.dirname(__file__), "mpv")
        os.makedirs(mpv_dir, exist_ok=True)
        os.startfile(mpv_dir)

    def _collect_paths(self):
        """Read live values from path entries (handles settings-not-open case)."""
        mpv = getattr(self, "mpv_entry", None)
        ytdlp = getattr(self, "ytdlp_entry", None)
        shd = getattr(self, "shaders_entry", None)
        return (
            (mpv.get().strip() or "mpv") if mpv else self._cfg.get("mpv_path", "mpv"),
            (ytdlp.get().strip() or "yt-dlp")
            if ytdlp
            else self._cfg.get("ytdlp_path", "yt-dlp"),
            (shd.get().strip()) if shd else self._cfg.get("shaders_dir", ""),
        )

    # ── Watch ──────────────────────────────────────────────────────────────

    def _on_lang_change(self):
        self._cfg["lang"] = self._lang_var.get()
        self._flush_cfg()

    def _on_ep_change(self):
        ep = self._ep_entry.get().strip()
        self._cfg["episode"] = ep
        self._flush_cfg()

    def _on_watch(self):
        url = self.url_entry.get().strip()
        if not url:
            self._set_status("Error: URL field is empty.", _ST_ERR)
            return

        mpv_path, ytdlp_path, shaders_dir = self._collect_paths()

        self._cfg["last_url"] = url
        self._flush_cfg()

        shader_arg: Optional[str] = None
        if shaders_dir:
            shader_arg = build_shader_arg(
                shaders_dir,
                self._cfg.get("mode", "A"),
                self._cfg.get("quality", "Quality"),
            )

        self.watch_btn.configure(state="disabled", text="Working...")
        self._set_status("Resolving stream\u2026", _ST_WORK)

        def _worker():
            try:
                run_pipeline(
                    url=url,
                    mpv_path=mpv_path,
                    ytdlp_path=ytdlp_path,
                    shader_arg=shader_arg,
                    status_cb=lambda m: self.after(
                        0, lambda msg=m: self._set_status(msg, _ST_WORK)
                    ),
                    episode=self._cfg.get("episode") or None,
                    lang=self._cfg.get("lang", "sub"),
                )
                self.after(0, lambda: self._set_status("mpv launched", _ST_OK))
            except PipelineError as exc:
                msg = str(exc)
                self.after(0, lambda m=msg: self._set_status(f"Error: {m}", _ST_ERR))
            finally:
                self.after(
                    0, lambda: self.watch_btn.configure(state="normal", text="Watch")
                )

        threading.Thread(target=_worker, daemon=True).start()

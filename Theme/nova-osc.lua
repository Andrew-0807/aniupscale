-- ╭──────────────────────────────────────────────────────────────╮
-- │  nova-osc.lua  ·  A modern glassmorphic OSC skin for mpv     │
-- │                                                              │
-- │  INSTALL:                                                    │
-- │    1. Copy to ~/.config/mpv/scripts/nova-osc.lua             │
-- │    2. Add  osc=no  to ~/.config/mpv/mpv.conf                 │
-- ╰──────────────────────────────────────────────────────────────╯
local assdraw = require "mp.assdraw"

-- ── Palette & config ─────────────────────────────────────────────────────────
local CFG = {
    -- Panel
    panel_color  = "111318",   -- deep slate background (RGB)
    panel_alpha  = 0xA8,       -- panel transparency (0=opaque, 255=invisible)
    panel_radius = 12,         -- top-corner roundness

    -- Accent (seekbar fill & knob)
    accent       = "A855F7",   -- electric violet  (#A855F7 RGB)

    -- Text
    title_color  = "E2E8F0",   -- slate-200
    time_color   = "94A3B8",   -- slate-400
    btn_color    = "CBD5E1",   -- slate-300

    -- Seekbar track (empty part)
    track_color  = "2D3748",
    bar_thick    = 3,          -- track height in virtual px
    knob_r       = 7,          -- handle radius

    -- Layout  (virtual 720-line canvas)
    res_y        = 720,
    bar_h        = 84,         -- total bar height
    pad_x        = 26,         -- horizontal padding
    title_y      = 14,         -- title text Y offset from bar top
    seek_y       = 36,         -- seekbar Y offset from bar top
    btn_y_off    = 19,         -- button center Y from bar bottom
    btn_fs       = 20,         -- button icon font size
    btn_gap      = 42,         -- spacing between center buttons

    -- Fade / hide
    hide_ms      = 2800,
    fade_ms      = 220,
}

-- ── Runtime state ─────────────────────────────────────────────────────────────
local ST = {
    osd     = nil,
    alpha   = 255,      -- 0=fully visible, 255=fully hidden
    fade_t  = nil,
    hide_t  = nil,
    pause   = false,
    pos     = 0,
    dur     = 0,
    mute    = false,
    vol     = 100,
    fs      = false,
    title   = "",
    scr_w   = 1920,
    scr_h   = 1080,
    lmx     = nil,
    lmy     = nil,
}

-- ── Pure helpers ─────────────────────────────────────────────────────────────
local function to_bgr(rgb)
    return rgb:sub(5,6)..rgb:sub(3,4)..rgb:sub(1,2)
end

local function clamp(v,lo,hi) return math.max(lo,math.min(hi,v)) end

local function fmt_time(t)
    t = math.max(0, math.floor(t or 0))
    local h = math.floor(t/3600)
    local m = math.floor(t%3600/60)
    local s = t%60
    if h > 0 then return string.format("%d:%02d:%02d",h,m,s) end
    return string.format("%d:%02d",m,s)
end

local function virt_w()
    return math.floor(CFG.res_y * ST.scr_w / math.max(ST.scr_h,1))
end

-- ── Render ───────────────────────────────────────────────────────────────────
local function render()
    if not ST.osd then return end
    local a = ST.alpha
    if a >= 255 then
        ST.osd.hidden = true; ST.osd:update(); return
    end

    local vw  = virt_w()
    local vh  = CFG.res_y
    local bh  = CFG.bar_h
    local by  = vh - bh
    local px  = CFG.pad_x
    local ass = assdraw.ass_new()

    -- 1 ── Panel background (rounded top corners) ─────────────────────────
    ass:new_event(); ass:pos(0,0); ass:an(7)
    ass:append(string.format(
        "{\\bord0\\blur0\\1c&H%s&\\1a&H%02X&\\p1}",
        to_bgr(CFG.panel_color), clamp(CFG.panel_alpha+a,0,255)
    ))
    ass:draw_start()
    ass:round_rect_cw(0, by, vw, vh, CFG.panel_radius, 0)
    ass:draw_stop()

    -- 2 ── Thin separator line at bar top ─────────────────────────────────
    ass:new_event(); ass:pos(0,0); ass:an(7)
    ass:append(string.format(
        "{\\bord0\\blur0\\1c&H%s&\\1a&H%02X&\\p1}",
        to_bgr(CFG.accent), clamp(a+170,0,255)
    ))
    ass:draw_start()
    ass:rect_cw(0, by, vw, by+1)
    ass:draw_stop()

    -- 3 ── Title (left) ────────────────────────────────────────────────────
    local title = ST.title ~= "" and ST.title or "mpv"
    local max_c = math.floor((vw - 200) / 9)
    if #title > max_c then title = title:sub(1, max_c-1).."…" end

    ass:new_event(); ass:pos(px, by+CFG.title_y); ass:an(7)
    ass:append(string.format(
        "{\\bord0\\blur0\\shad0\\1c&H%s&\\1a&H%02X&\\fs13\\fnSans Serif\\q2}",
        to_bgr(CFG.title_color), a
    ))
    ass:append(title)

    -- 4 ── Time (right) ────────────────────────────────────────────────────
    if ST.dur > 0 then
        local tstr = fmt_time(ST.pos).."  /  "..fmt_time(ST.dur)
        ass:new_event(); ass:pos(vw-px, by+CFG.title_y); ass:an(9)
        ass:append(string.format(
            "{\\bord0\\blur0\\shad0\\1c&H%s&\\1a&H%02X&\\fs13\\fnSans Serif}",
            to_bgr(CFG.time_color), a
        ))
        ass:append(tstr)
    end

    -- 5 ── Seekbar ─────────────────────────────────────────────────────────
    local sx0 = px
    local sx1 = vw - px
    local sy  = by + CFG.seek_y
    local sh  = CFG.bar_thick
    local r   = sh / 2

    -- Track
    ass:new_event(); ass:pos(0,0); ass:an(7)
    ass:append(string.format(
        "{\\bord0\\blur0\\1c&H%s&\\1a&H%02X&\\p1}",
        to_bgr(CFG.track_color), a
    ))
    ass:draw_start()
    ass:round_rect_cw(sx0, sy-r, sx1, sy+r, r)
    ass:draw_stop()

    -- Filled progress
    local pct  = ST.dur > 0 and clamp(ST.pos/ST.dur, 0, 1) or 0
    local sxp  = sx0 + (sx1-sx0) * pct

    if sxp > sx0 + r then
        ass:new_event(); ass:pos(0,0); ass:an(7)
        ass:append(string.format(
            "{\\bord0\\blur0\\1c&H%s&\\1a&H%02X&\\p1}",
            to_bgr(CFG.accent), a
        ))
        ass:draw_start()
        ass:round_rect_cw(sx0, sy-r, sxp, sy+r, r)
        ass:draw_stop()
    end

    -- Knob: soft glow + solid dot
    if ST.dur > 0 then
        local kr = CFG.knob_r
        -- glow layer
        ass:new_event(); ass:pos(0,0); ass:an(7)
        ass:append(string.format(
            "{\\bord0\\blur5\\1c&H%s&\\1a&H%02X&\\p1}",
            to_bgr(CFG.accent), clamp(a+100,0,255)
        ))
        ass:draw_start()
        ass:round_rect_cw(sxp-kr, sy-kr, sxp+kr, sy+kr, kr)
        ass:draw_stop()
        -- solid dot
        ass:new_event(); ass:pos(0,0); ass:an(7)
        ass:append(string.format(
            "{\\bord0\\blur0\\1c&HFFFFFF&\\1a&H%02X&\\p1}", a
        ))
        ass:draw_start()
        ass:round_rect_cw(sxp-kr+1, sy-kr+1, sxp+kr-1, sy+kr-1, kr-1)
        ass:draw_stop()
    end

    -- 6 ── Buttons ─────────────────────────────────────────────────────────
    local font = "mpv-osd-symbols"
    local bty  = by + bh - CFG.btn_y_off
    local bfs  = CFG.btn_fs
    local gap  = CFG.btn_gap
    local cx   = vw / 2

    -- mpv-osd-symbols glyphs (UTF-8 byte sequences for PUA codepoints)
    -- E002 = pause bars | E101 = play triangle | E110 = prev (play-backward)
    -- E004 = skip-back  | E005 = skip-forward
    -- E108 = fullscreen | E109 = exit-fullscreen
    -- E10A = mute       | E10D = volume-high
    local ICO = {
        prev   = "\238\132\144",   -- E110
        rew    = "\238\128\132",   -- E004
        pause  = "\238\128\130",   -- E002
        play   = "\238\132\129",   -- E101  (same glyph as "next" in older fonts)
        ffw    = "\238\128\133",   -- E005
        next   = "\238\132\129",   -- E101
        mute   = "\238\132\138",   -- E10A
        vol    = "\238\132\141",   -- E10D
        vol_lo = "\238\132\139",   -- E10B
        fse    = "\238\132\136",   -- E108  enter fullscreen
        fsx    = "\238\132\137",   -- E109  exit fullscreen
    }

    local function ico(bx, glyph)
        ass:new_event(); ass:pos(bx, bty); ass:an(8)
        ass:append(string.format(
            "{\\bord0\\blur0\\shad0\\1c&H%s&\\1a&H%02X&\\fs%d\\fn%s}",
            to_bgr(CFG.btn_color), a, bfs, font
        ))
        ass:append(glyph)
    end

    -- Center cluster
    ico(cx - gap*2, ICO.prev)
    ico(cx - gap,   ICO.rew)
    ico(cx,         ST.pause and ICO.play or ICO.pause)
    ico(cx + gap,   ICO.ffw)
    ico(cx + gap*2, ICO.next)

    -- Volume (left edge)
    local vol_ico = ST.mute and ICO.mute
                    or (ST.vol > 55 and ICO.vol or ICO.vol_lo)
    ico(px + 14, vol_ico)

    -- Fullscreen (right edge)
    ico(vw - px - 14, ST.fs and ICO.fsx or ICO.fse)

    -- ── Push to screen ────────────────────────────────────────────────────
    ST.osd.data   = ass.text
    ST.osd.hidden = false
    ST.osd:update()
end

-- ── Fade engine ───────────────────────────────────────────────────────────────
local function stop_fade()
    if ST.fade_t then ST.fade_t:kill(); ST.fade_t = nil end
end

local function fade_to(target)
    stop_fade()
    local tick = 1/60
    ST.fade_t = mp.add_periodic_timer(tick, function()
        local step = math.max(1, math.ceil(255 * tick * 1000 / CFG.fade_ms))
        if target == 0 then
            ST.alpha = math.max(0, ST.alpha - step)
        else
            ST.alpha = math.min(255, ST.alpha + step)
        end
        render()
        if ST.alpha == target then stop_fade() end
    end)
end

local function schedule_hide()
    if ST.hide_t then ST.hide_t:kill() end
    ST.hide_t = mp.add_timeout(CFG.hide_ms / 1000, function()
        fade_to(255)
    end)
end

local function show_osc()
    fade_to(0)
    schedule_hide()
end

-- ── Click / scroll handler ────────────────────────────────────────────────────
local function on_click()
    show_osc()
    local rx, ry = mp.get_mouse_pos()
    local vw = virt_w()
    local vh = CFG.res_y
    local mx = rx * vw / ST.scr_w
    local my = ry * vh / ST.scr_h

    local by  = vh - CFG.bar_h
    local px  = CFG.pad_x
    local cx  = vw / 2
    local gap = CFG.btn_gap

    -- Click outside bar → toggle pause (standard behaviour)
    if my < by then
        mp.commandv("cycle","pause")
        return
    end

    -- Seekbar click (±14 px tolerance)
    local sy = by + CFG.seek_y
    if my >= sy-14 and my <= sy+14 and mx >= px and mx <= vw-px then
        local pct = clamp((mx-px)/((vw-px)-px), 0, 1)
        mp.commandv("seek", pct*100, "absolute-percent", "exact")
        return
    end

    -- Button clicks
    local bty = by + CFG.bar_h - CFG.btn_y_off
    local function near(bx)
        return mx >= bx-20 and mx <= bx+20 and my >= bty-20 and my <= bty+12
    end

    if     near(cx - gap*2)   then mp.commandv("playlist-prev")
    elseif near(cx - gap)     then mp.commandv("seek",-5)
    elseif near(cx)           then mp.commandv("cycle","pause")
    elseif near(cx + gap)     then mp.commandv("seek", 5)
    elseif near(cx + gap*2)   then mp.commandv("playlist-next")
    elseif near(px + 14)      then mp.commandv("cycle","mute")
    elseif near(vw - px - 14) then mp.commandv("cycle","fullscreen")
    end
end

-- ── Key / mouse bindings ──────────────────────────────────────────────────────
mp.add_key_binding("mbtn_left",     "nova-click",  on_click)
mp.add_key_binding("mbtn_left_dbl", "nova-dbl",    function() mp.commandv("cycle","fullscreen") end)
mp.add_key_binding("wheel_up",      "nova-wup",    function() mp.commandv("add","volume", 5); show_osc() end)
mp.add_key_binding("wheel_down",    "nova-wdn",    function() mp.commandv("add","volume",-5); show_osc() end)

mp.observe_property("mouse-pos","native", function(_,p)
    if not p then return end
    if p.x ~= ST.lmx or p.y ~= ST.lmy then
        ST.lmx, ST.lmy = p.x, p.y
        show_osc()
    end
end)

-- ── Property watchers ─────────────────────────────────────────────────────────
mp.observe_property("pause",          "bool",   function(_,v) ST.pause = v or false;  render() end)
mp.observe_property("time-pos",       "number", function(_,v) ST.pos   = v or 0;      render() end)
mp.observe_property("duration",       "number", function(_,v) ST.dur   = v or 0;      render() end)
mp.observe_property("mute",           "bool",   function(_,v) ST.mute  = v or false;  render() end)
mp.observe_property("volume",         "number", function(_,v) ST.vol   = v or 100;    render() end)
mp.observe_property("fullscreen",     "bool",   function(_,v) ST.fs    = v or false;  render() end)
mp.observe_property("media-title",    "string", function(_,v) ST.title = v or "";     render() end)
mp.observe_property("osd-dimensions", "native", function(_,v)
    if v then ST.scr_w, ST.scr_h = v.w, v.h end
    render()
end)

-- ── Bootstrap ─────────────────────────────────────────────────────────────────
ST.osd       = mp.create_osd_overlay("ass-events")
ST.osd.z     = 1000
ST.osd.res_y = CFG.res_y
ST.osd.res_x = 0   -- 0 = mpv auto-derives width from display aspect ratio

show_osc()

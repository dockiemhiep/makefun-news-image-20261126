#!/usr/bin/env python3
"""Generate the 1024x1024 front-page news image entry.png using Pillow."""

from __future__ import annotations

import math
import os
from typing import Callable, List, Tuple

from PIL import Image, ImageDraw, ImageFont

# Exact canvas and style constants
WIDTH = 1024
HEIGHT = 1024
MAX_BYTES = 1_048_576

BG_COLOR = (247, 243, 232)       # #F7F3E8 off-white archival newsprint
INK_COLOR = (17, 17, 17)         # #111111 crisp black
ACCENT_COLOR = (163, 22, 33)     # #A31621 deep red
MUTED_INK = (55, 55, 55)         # subtle secondary tone for flat motif depth
LIGHT_RULE = (214, 206, 190)     # subtle warm paper tint for motif details

FONT_BOLD_PATH = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REG_PATH = "/System/Library/Fonts/Supplemental/Arial.ttf"

# Exact verified copy (do not alter wording)
MASTHEAD_TITLE = "THE WORLD IN ONE PICTURE"
MASTHEAD_DATE = "THURSDAY · 26 NOVEMBER 2026"
FOOTER_TEXT = (
    "ALSO TODAY — KIM JONG UN CALLS FOR MORE TACTICAL NUKES · "
    "31 KILLED IN CAIRO FUEL-TANKER FIRE · "
    "BIRTHRIGHT ORDER BLOCKED BY SECOND JUDGE"
)

PANELS = [
    {
        "tag": "TRADE",
        "headline": "US PROPOSES NEW TARIFFS ON 14 PARTNERS",
        "subline": "China hit hardest; Taiwan faces up to 15%; markets slide",
        "motif": "trade",
    },
    {
        "tag": "OIL",
        "headline": "HOUTHIS CLAIM HIT ON SAUDI REFINERY; BRENT TOPS $94",
        "subline": "Riyadh says four drones shot down; oil jumps 3.5%",
        "motif": "oil",
    },
    {
        "tag": "WAR",
        "headline": "UKRAINE SAYS IT HIT RUSSIAN AIR BASE",
        "subline": "Five planes damaged at Savasleyka; Kyiv hit by missiles",
        "motif": "war",
    },
    {
        "tag": "MARKETS",
        "headline": "NASDAQ SINKS NEARLY 4% AS AI FEARS SPREAD",
        "subline": "Stocks slide after tariff plan; Nvidia faces antitrust questions",
        "motif": "markets",
    },
]


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def text_size(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> Tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> List[str]:
    """Word-wrap text using draw.textbbox so every line fits inside max_width."""
    words = text.split()
    if not words:
        return []

    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        w, _ = text_size(draw, candidate, font)
        if w <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)

    # Verify every line fits within max_width
    for line in lines:
        w, _ = text_size(draw, line, font)
        if w > max_width:
            raise ValueError(
                f"Wrapped line {line!r} width {w} exceeds max_width {max_width}"
            )
    return lines


def draw_wrapped_block(
    draw: ImageDraw.ImageDraw,
    lines: List[str],
    font: ImageFont.FreeTypeFont,
    x: int,
    y: int,
    line_spacing: int,
    fill: Tuple[int, int, int],
    max_width: int,
    align: str = "left",
) -> int:
    """Draw wrapped lines with exact top alignment and return bottom y."""
    ascent, descent = font.getmetrics()
    line_step = ascent + descent + line_spacing
    cursor_y = y
    bottom_y = y

    for idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        if line_w > max_width:
            raise ValueError(f"Line {line!r} overflows max_width ({line_w} > {max_width})")

        if align == "center":
            draw_x = x + (max_width - line_w) // 2 - bbox[0]
        else:
            draw_x = x - bbox[0]

        draw_y = cursor_y - bbox[1] if idx == 0 else cursor_y
        if idx == 0:
            # Anchor subsequent baselines consistently from first line's drawn y
            base_y = draw_y
        else:
            draw_y = base_y + idx * line_step

        draw.text((draw_x, draw_y), line, font=font, fill=fill)
        placed = draw.textbbox((draw_x, draw_y), line, font=font)
        bottom_y = max(bottom_y, placed[3])

    return bottom_y


def render_supersampled_motif(
    w: int,
    h: int,
    painter: Callable[[ImageDraw.ImageDraw, int, int], None],
    scale: int = 2,
) -> Image.Image:
    """Render a flat geometric motif at 2x scale and downsample cleanly."""
    canvas = Image.new("RGB", (w * scale, h * scale), BG_COLOR)
    d = ImageDraw.Draw(canvas)
    painter(d, w * scale, h * scale)
    return canvas.resize((w, h), Image.Resampling.LANCZOS)


def draw_motif_trade(d: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """Three stacked shipping containers with corrugation lines + big bold '%'."""
    pad_y = int(h * 0.08)
    ground_y = h - pad_y
    usable_h = ground_y - pad_y

    # Ground baseline under the container stack
    d.line([(int(w * 0.06), ground_y), (int(w * 0.61), ground_y)], fill=INK_COLOR, width=5)

    # Three stacked shipping containers on the left ~56%
    stack_w = int(w * 0.48)
    box_h = int(usable_h * 0.30)
    gap = max(4, int(usable_h * 0.03))
    base_x = int(w * 0.09)

    containers = [
        (0, INK_COLOR, BG_COLOR),        # bottom: black container, cream corrugation
        (14, ACCENT_COLOR, BG_COLOR),    # middle: deep-red container, cream corrugation
        (-8, MUTED_INK, BG_COLOR),       # top: dark slate container, cream corrugation
    ]

    stack_top = ground_y
    for idx, (x_off, fill_col, rib_col) in enumerate(containers):
        y1 = ground_y - 4 - idx * (box_h + gap)
        y0 = y1 - box_h
        stack_top = min(stack_top, y0)
        x0 = base_x + x_off
        x1 = x0 + stack_w
        d.rectangle([x0, y0, x1, y1], fill=fill_col, outline=INK_COLOR, width=4)

        # Vertical corrugation lines inside container
        inset_x = 18
        inset_y = max(8, int(box_h * 0.16))
        num_ribs = 9
        rib_span = (x1 - x0) - 2 * inset_x
        for r in range(num_ribs):
            rx = x0 + inset_x + int(r * rib_span / (num_ribs - 1))
            d.line([(rx, y0 + inset_y), (rx, y1 - inset_y)], fill=rib_col, width=4)

        # Crisp corner-casting accents and outer frame
        cast = 8
        for cx0, cy0 in ((x0, y0), (x1 - cast, y0), (x0, y1 - cast), (x1 - cast, y1 - cast)):
            d.rectangle([cx0, cy0, cx0 + cast, cy0 + cast], fill=INK_COLOR)
        d.rectangle([x0, y0, x1, y1], outline=INK_COLOR, width=4)

    # Big bold "%" sign vertically aligned to the exact height of the container stack
    stack_h = ground_y - stack_top
    pct_size = int(stack_h * 1.02)
    pct_font = load_font(FONT_BOLD_PATH, pct_size)
    bbox = d.textbbox((0, 0), "%", font=pct_font)
    pw = bbox[2] - bbox[0]
    ph = bbox[3] - bbox[1]

    right_zone_x0 = int(w * 0.63)
    right_zone_x1 = int(w * 0.94)
    px = right_zone_x0 + (right_zone_x1 - right_zone_x0 - pw) // 2 - bbox[0]
    py = stack_top + (stack_h - ph) // 2 - bbox[1]
    d.text((px, py), "%", font=pct_font, fill=ACCENT_COLOR)


def draw_motif_oil(d: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """Oil refinery (two tall towers + chimney with small flame) + small drone above."""
    pad_y = int(h * 0.05)
    ground_y = h - pad_y
    usable_h = ground_y - pad_y

    # Balanced ground baseline
    d.line([(int(w * 0.08), ground_y), (int(w * 0.92), ground_y)], fill=INK_COLOR, width=4)

    # Horizontally centered refinery complex (x: 17% .. 84%) with extra sky headroom
    # Tower 1 (tallest distillation tower)
    t1_x0 = int(w * 0.17)
    t1_w = int(w * 0.088)
    t1_h = int(usable_h * 0.65)
    t1_y0 = ground_y - t1_h

    # Tower 2 (second tall tower)
    t2_x0 = int(w * 0.32)
    t2_w = int(w * 0.082)
    t2_h = int(usable_h * 0.53)
    t2_y0 = ground_y - t2_h

    # Connecting overhead pipes between towers
    for frac in (0.30, 0.62):
        py = ground_y - int(t2_h * frac)
        d.line([(t1_x0 + t1_w, py), (t2_x0, py)], fill=INK_COLOR, width=5)

    # Draw Tower 1 with domed cap and structural rings
    d.rectangle([t1_x0, t1_y0, t1_x0 + t1_w, ground_y], fill=INK_COLOR)
    d.pieslice([t1_x0, t1_y0 - t1_w // 2, t1_x0 + t1_w, t1_y0 + t1_w // 2], 180, 360, fill=INK_COLOR)
    for frac in (0.24, 0.48, 0.72):
        by = t1_y0 + int(t1_h * frac)
        d.line([(t1_x0 + 4, by), (t1_x0 + t1_w - 4, by)], fill=BG_COLOR, width=4)
        d.line([(t1_x0 - 8, by + 5), (t1_x0 + t1_w + 8, by + 5)], fill=INK_COLOR, width=3)

    # Draw Tower 2
    d.rectangle([t2_x0, t2_y0, t2_x0 + t2_w, ground_y], fill=MUTED_INK, outline=INK_COLOR, width=4)
    d.pieslice([t2_x0, t2_y0 - t2_w // 2, t2_x0 + t2_w, t2_y0 + t2_w // 2], 180, 360, fill=MUTED_INK, outline=INK_COLOR, width=4)
    for frac in (0.28, 0.56, 0.80):
        by = t2_y0 + int(t2_h * frac)
        d.line([(t2_x0 + 4, by), (t2_x0 + t2_w - 4, by)], fill=BG_COLOR, width=4)

    # Low refinery storage unit connecting Tower 2 to Chimney
    tank_x0 = int(w * 0.46)
    tank_x1 = int(w * 0.65)
    tank_y0 = ground_y - int(usable_h * 0.24)
    d.rectangle([tank_x0, tank_y0, tank_x1, ground_y], fill=LIGHT_RULE, outline=INK_COLOR, width=4)
    pipe_low = ground_y - int(usable_h * 0.12)
    d.line([(t2_x0 + t2_w, pipe_low), (tank_x0, pipe_low)], fill=INK_COLOR, width=5)

    # Tall tapered chimney stack on right
    ch_cx = int(w * 0.78)
    ch_bot_w = int(w * 0.056)
    ch_top_w = int(w * 0.030)
    ch_h = int(usable_h * 0.59)
    ch_y0 = ground_y - ch_h
    d.polygon(
        [
            (ch_cx - ch_bot_w // 2, ground_y),
            (ch_cx - ch_top_w // 2, ch_y0),
            (ch_cx + ch_top_w // 2, ch_y0),
            (ch_cx + ch_bot_w // 2, ground_y),
        ],
        fill=INK_COLOR,
    )
    d.line([(tank_x1, pipe_low), (ch_cx - ch_bot_w // 2, pipe_low)], fill=INK_COLOR, width=5)

    # Crisp flickering organic flame above chimney
    fl_base = ch_y0 - 2
    fl_h = int(usable_h * 0.30)
    fl_w = int(w * 0.028)
    d.polygon(
        [
            (ch_cx - int(fl_w * 0.48), fl_base),
            (ch_cx - int(fl_w * 0.95), fl_base - int(fl_h * 0.24)),
            (ch_cx - int(fl_w * 0.75), fl_base - int(fl_h * 0.56)),
            (ch_cx - int(fl_w * 0.20), fl_base - int(fl_h * 0.46)),
            (ch_cx + int(fl_w * 0.08), fl_base - fl_h),
            (ch_cx + int(fl_w * 0.70), fl_base - int(fl_h * 0.55)),
            (ch_cx + int(fl_w * 0.95), fl_base - int(fl_h * 0.25)),
            (ch_cx + int(fl_w * 0.48), fl_base),
        ],
        fill=ACCENT_COLOR,
    )
    # Small inner cream flame tongue
    d.polygon(
        [
            (ch_cx - int(fl_w * 0.22), fl_base - 2),
            (ch_cx - int(fl_w * 0.36), fl_base - int(fl_h * 0.28)),
            (ch_cx + int(fl_w * 0.04), fl_base - int(fl_h * 0.56)),
            (ch_cx + int(fl_w * 0.34), fl_base - int(fl_h * 0.28)),
            (ch_cx + int(fl_w * 0.20), fl_base - 2),
        ],
        fill=BG_COLOR,
    )

    # Small drone cleanly positioned in open sky with generous margin below sub-line
    dr_cx = int(w * 0.55)
    dr_cy = pad_y + int(usable_h * 0.23)
    body_w = int(w * 0.072)
    body_h = int(usable_h * 0.105)
    d.rectangle(
        [dr_cx - body_w // 2, dr_cy - body_h // 2, dr_cx + body_w // 2, dr_cy + body_h // 2],
        fill=ACCENT_COLOR,
        outline=INK_COLOR,
        width=3,
    )
    arm_span = int(w * 0.068)
    stem_h = max(8, int(usable_h * 0.08))
    rotor_half = int(w * 0.042)
    for side in (-1, 1):
        arm_x = dr_cx + side * arm_span
        d.line([(dr_cx + side * (body_w // 2), dr_cy), (arm_x, dr_cy)], fill=INK_COLOR, width=4)
        d.line([(arm_x, dr_cy), (arm_x, dr_cy - stem_h)], fill=INK_COLOR, width=4)
        d.line(
            [(arm_x - rotor_half, dr_cy - stem_h), (arm_x + rotor_half, dr_cy - stem_h)],
            fill=INK_COLOR,
            width=4,
        )


def draw_motif_war(d: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """Fighter jet silhouette above a runway strip, with a small starburst explosion beside it."""
    pad_y = int(h * 0.07)
    runway_h = max(24, int(h * 0.19))
    runway_y1 = h - pad_y
    runway_y0 = runway_y1 - runway_h

    # Runway strip at bottom
    rw_x0 = int(w * 0.06)
    rw_x1 = int(w * 0.94)
    d.rectangle([rw_x0, runway_y0, rw_x1, runway_y1], fill=INK_COLOR)
    mid_ry = (runway_y0 + runway_y1) // 2
    dash_w = 34
    gap_w = 24
    cx = rw_x0 + 22
    while cx + dash_w < rw_x1 - 16:
        d.rectangle([cx, mid_ry - 3, cx + dash_w, mid_ry + 3], fill=BG_COLOR)
        cx += dash_w + gap_w

    # Fighter jet silhouette above the runway (solid, clean single-piece silhouette)
    sky_h = runway_y0 - pad_y
    jet_cy = pad_y + int(sky_h * 0.50)
    nose_x = int(w * 0.59)
    tail_x = int(w * 0.11)
    fuselage_half = max(13, int(sky_h * 0.12))

    # Swept main wings
    wing_lead_x = int(w * 0.43)
    wing_tip_x = int(w * 0.24)
    wing_trail_x = int(w * 0.28)
    wing_span = int(sky_h * 0.43)
    d.polygon(
        [
            (wing_lead_x, jet_cy - fuselage_half + 4),
            (wing_tip_x, jet_cy - wing_span),
            (wing_tip_x - 16, jet_cy - wing_span),
            (wing_trail_x, jet_cy - fuselage_half + 4),
        ],
        fill=INK_COLOR,
    )
    d.polygon(
        [
            (wing_lead_x, jet_cy + fuselage_half - 4),
            (wing_tip_x, jet_cy + wing_span),
            (wing_tip_x - 16, jet_cy + wing_span),
            (wing_trail_x, jet_cy + fuselage_half - 4),
        ],
        fill=INK_COLOR,
    )

    # Tail stabilizers
    stab_span = int(sky_h * 0.25)
    d.polygon(
        [
            (tail_x + 52, jet_cy - fuselage_half + 4),
            (tail_x + 8, jet_cy - stab_span),
            (tail_x - 4, jet_cy - stab_span),
            (tail_x + 14, jet_cy - fuselage_half + 4),
        ],
        fill=INK_COLOR,
    )
    d.polygon(
        [
            (tail_x + 52, jet_cy + fuselage_half - 4),
            (tail_x + 8, jet_cy + stab_span),
            (tail_x - 4, jet_cy + stab_span),
            (tail_x + 14, jet_cy + fuselage_half - 4),
        ],
        fill=INK_COLOR,
    )

    # Clean, solid fuselage triangle with sturdy tapered nose (no detached pixels)
    d.polygon(
        [
            (nose_x, jet_cy),
            (int(w * 0.44), jet_cy - fuselage_half),
            (tail_x, jet_cy - int(fuselage_half * 0.72)),
            (tail_x + 10, jet_cy),
            (tail_x, jet_cy + int(fuselage_half * 0.72)),
            (int(w * 0.44), jet_cy + fuselage_half),
        ],
        fill=INK_COLOR,
    )
    # Subtle cockpit canopy well inside the thicker mid-fuselage
    d.polygon(
        [
            (int(w * 0.47), jet_cy),
            (int(w * 0.42), jet_cy - 5),
            (int(w * 0.37), jet_cy),
            (int(w * 0.42), jet_cy + 5),
        ],
        fill=BG_COLOR,
    )

    # Small deep-red starburst explosion beside the jet (right side)
    bx = int(w * 0.79)
    by = pad_y + int(sky_h * 0.50)
    outer_r = int(min(w * 0.115, sky_h * 0.43))
    inner_r = int(outer_r * 0.44)
    points = []
    num_spikes = 10
    for i in range(num_spikes * 2):
        angle = -math.pi / 2 + i * math.pi / num_spikes
        r = outer_r if i % 2 == 0 else inner_r
        points.append((bx + r * math.cos(angle), by + r * math.sin(angle)))
    d.polygon(points, fill=ACCENT_COLOR, outline=INK_COLOR, width=3)

    core_points = []
    for i in range(num_spikes * 2):
        angle = -math.pi / 2 + i * math.pi / num_spikes
        r = int(outer_r * 0.42) if i % 2 == 0 else int(inner_r * 0.42)
        core_points.append((bx + r * math.cos(angle), by + r * math.sin(angle)))
    d.polygon(core_points, fill=BG_COLOR)


def draw_motif_markets(d: ImageDraw.ImageDraw, w: int, h: int) -> None:
    """Falling zigzag line chart with downward arrow above a small computer chip."""
    pad_y = int(h * 0.04)
    chart_top = pad_y
    chart_bot = int(h * 0.50)
    chart_x0 = int(w * 0.08)
    chart_x1 = int(w * 0.92)

    # Crisp L-axis + subtle horizontal grid lines for chart
    for frac in (0.14, 0.54, 0.94):
        gy = chart_top + int((chart_bot - chart_top) * frac)
        d.line([(chart_x0, gy), (chart_x1, gy)], fill=LIGHT_RULE, width=3)
    d.line([(chart_x0, chart_top + 6), (chart_x0, chart_bot - 4)], fill=MUTED_INK, width=4)
    d.line([(chart_x0, chart_bot - 4), (chart_x1, chart_bot - 4)], fill=MUTED_INK, width=4)

    # Bold zigzag falling line descending sharply left to right
    pts = [
        (int(w * 0.11), chart_top + int((chart_bot - chart_top) * 0.10)),
        (int(w * 0.28), chart_top + int((chart_bot - chart_top) * 0.42)),
        (int(w * 0.42), chart_top + int((chart_bot - chart_top) * 0.22)),
        (int(w * 0.61), chart_top + int((chart_bot - chart_top) * 0.64)),
        (int(w * 0.72), chart_top + int((chart_bot - chart_top) * 0.44)),
        (int(w * 0.87), chart_top + int((chart_bot - chart_top) * 0.80)),
    ]
    d.line(pts, fill=ACCENT_COLOR, width=11)
    for px, py in pts[:-1]:
        d.ellipse([px - 5, py - 5, px + 5, py + 5], fill=ACCENT_COLOR)

    # Crisp downward arrowhead at the end of the falling line
    ex, ey = pts[-1]
    prev_x, prev_y = pts[-2]
    angle = math.atan2(ey - prev_y, ex - prev_x)
    head_len = 36
    spread = 0.52
    tip = (ex + 12 * math.cos(angle), ey + 12 * math.sin(angle))
    left_pt = (
        tip[0] - head_len * math.cos(angle - spread),
        tip[1] - head_len * math.sin(angle - spread),
    )
    right_pt = (
        tip[0] - head_len * math.cos(angle + spread),
        tip[1] - head_len * math.sin(angle + spread),
    )
    d.polygon([tip, left_pt, right_pt], fill=ACCENT_COLOR)

    # Crisp computer chip centered below the falling line (filled square with pin lines)
    chip_zone_top = int(h * 0.54)
    chip_zone_bot = h - pad_y
    chip_zone_h = chip_zone_bot - chip_zone_top
    pin_len = max(16, int(chip_zone_h * 0.19))
    chip_side = max(64, chip_zone_h - 2 * pin_len)
    cx = w // 2
    cy = chip_zone_top + chip_zone_h // 2

    x0 = cx - chip_side // 2
    y0 = cy - chip_side // 2
    x1 = cx + chip_side // 2
    y1 = cy + chip_side // 2

    num_pins = 4
    pin_margin = int(chip_side * 0.18)
    pin_span = chip_side - 2 * pin_margin
    for i in range(num_pins):
        offset = pin_margin + int(i * pin_span / (num_pins - 1))
        d.line([(x0 + offset, y0 - pin_len), (x0 + offset, y0)], fill=INK_COLOR, width=5)
        d.line([(x0 + offset, y1), (x0 + offset, y1 + pin_len)], fill=INK_COLOR, width=5)
        d.line([(x0 - pin_len, y0 + offset), (x0, y0 + offset)], fill=INK_COLOR, width=5)
        d.line([(x1, y0 + offset), (x1 + pin_len, y0 + offset)], fill=INK_COLOR, width=5)

    d.rectangle([x0, y0, x1, y1], fill=INK_COLOR)
    inset = max(14, int(chip_side * 0.22))
    d.rectangle([x0 + inset, y0 + inset, x1 - inset, y1 - inset], outline=BG_COLOR, width=4)
    core = max(8, int(chip_side * 0.12))
    d.rectangle([cx - core, cy - core, cx + core, cy + core], fill=ACCENT_COLOR)


MOTIF_DRAWERS = {
    "trade": draw_motif_trade,
    "oil": draw_motif_oil,
    "war": draw_motif_war,
    "markets": draw_motif_markets,
}


def build_image(output_path: str) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    outer_x = 22
    usable_w = WIDTH - 2 * outer_x

    # 1. Masthead
    # Choose largest size up to 64px that fits comfortably inside usable_w
    masthead_size = 64
    while masthead_size > 48:
        mf = load_font(FONT_BOLD_PATH, masthead_size)
        mw, _ = text_size(draw, MASTHEAD_TITLE, mf)
        if mw <= usable_w - 8:
            break
        masthead_size -= 1
    masthead_font = load_font(FONT_BOLD_PATH, masthead_size)
    mbbox = draw.textbbox((0, 0), MASTHEAD_TITLE, font=masthead_font)
    mw = mbbox[2] - mbbox[0]
    mh = mbbox[3] - mbbox[1]
    title_x = (WIDTH - mw) // 2 - mbbox[0]
    title_y = 18 - mbbox[1]
    draw.text((title_x, title_y), MASTHEAD_TITLE, font=masthead_font, fill=INK_COLOR)
    title_bottom = 18 + mh

    # Deep-red rule line below masthead title
    rule_y = title_bottom + 10
    draw.rectangle([outer_x, rule_y, WIDTH - outer_x, rule_y + 4], fill=ACCENT_COLOR)

    # Date line centered below rule (30px)
    date_font = load_font(FONT_BOLD_PATH, 30)
    dbbox = draw.textbbox((0, 0), MASTHEAD_DATE, font=date_font)
    dw = dbbox[2] - dbbox[0]
    dh = dbbox[3] - dbbox[1]
    date_y = rule_y + 11 - dbbox[1]
    draw.text(((WIDTH - dw) // 2 - dbbox[0], date_y), MASTHEAD_DATE, font=date_font, fill=INK_COLOR)
    date_bottom = rule_y + 11 + dh

    # 2. Measure footer first so we know exact vertical budget for the 2x2 grid
    footer_font = load_font(FONT_REG_PATH, 22)
    footer_lines = wrap_text(draw, FOOTER_TEXT, footer_font, usable_w)
    f_ascent, f_descent = footer_font.getmetrics()
    footer_line_spacing = 4
    footer_block_h = (f_ascent + f_descent) * len(footer_lines) + footer_line_spacing * (len(footer_lines) - 1)
    footer_bottom_margin = 14
    footer_text_top = HEIGHT - footer_bottom_margin - footer_block_h
    footer_rule_y = footer_text_top - 11

    # Draw footer black rule + wrapped text
    draw.rectangle([outer_x, footer_rule_y, WIDTH - outer_x, footer_rule_y + 3], fill=INK_COLOR)
    footer_actual_bottom = draw_wrapped_block(
        draw=draw,
        lines=footer_lines,
        font=footer_font,
        x=outer_x,
        y=footer_text_top,
        line_spacing=footer_line_spacing,
        fill=INK_COLOR,
        max_width=usable_w,
        align="center",
    )
    assert footer_actual_bottom <= HEIGHT - 8, f"Footer overflowed canvas: {footer_actual_bottom}"

    # 3. 2x2 Panel Grid between masthead and footer
    grid_top = date_bottom + 12
    grid_bottom = footer_rule_y - 12
    col_gap = 14
    row_gap = 14
    panel_w = (usable_w - col_gap) // 2
    panel_h = (grid_bottom - grid_top - row_gap) // 2

    tag_font = load_font(FONT_BOLD_PATH, 19)
    headline_font = load_font(FONT_BOLD_PATH, 44)
    sub_font = load_font(FONT_REG_PATH, 24)

    for idx, spec in enumerate(PANELS):
        row = idx // 2
        col = idx % 2
        px0 = outer_x + col * (panel_w + col_gap)
        py0 = grid_top + row * (panel_h + row_gap)
        px1 = px0 + panel_w
        py1 = py0 + panel_h

        # Thin black panel border
        draw.rectangle([px0, py0, px1, py1], fill=BG_COLOR, outline=INK_COLOR, width=2)

        pad_x = 16
        pad_top = 11
        pad_bot = 10
        inner_x = px0 + pad_x
        inner_w = panel_w - 2 * pad_x

        # Deep-red category tag at top-left
        tag_text = spec["tag"]
        tbbox = draw.textbbox((0, 0), tag_text, font=tag_font)
        tw = tbbox[2] - tbbox[0]
        th = tbbox[3] - tbbox[1]
        tag_pad_x = 8
        tag_pad_y = 4
        tag_box = [inner_x, py0 + pad_top, inner_x + tw + 2 * tag_pad_x, py0 + pad_top + th + 2 * tag_pad_y]
        draw.rectangle(tag_box, fill=ACCENT_COLOR)
        draw.text(
            (inner_x + tag_pad_x - tbbox[0], py0 + pad_top + tag_pad_y - tbbox[1]),
            tag_text,
            font=tag_font,
            fill=BG_COLOR,
        )
        cursor_y = tag_box[3] + 8

        # Big bold headline (>= 44px), wrapped to fit inner_w
        hl_lines = wrap_text(draw, spec["headline"], headline_font, inner_w)
        hl_line_spacing = -5 if len(hl_lines) >= 4 else -4
        hl_bottom = draw_wrapped_block(
            draw=draw,
            lines=hl_lines,
            font=headline_font,
            x=inner_x,
            y=cursor_y,
            line_spacing=hl_line_spacing,
            fill=INK_COLOR,
            max_width=inner_w,
            align="left",
        )
        assert hl_bottom < py1 - pad_bot, f"Headline overflowed panel {spec['tag']}"

        # Smaller sub-line (24px), wrapped to fit inner_w in crisp black (#111111)
        sub_y = hl_bottom + 8
        sub_lines = wrap_text(draw, spec["subline"], sub_font, inner_w)
        sub_bottom = draw_wrapped_block(
            draw=draw,
            lines=sub_lines,
            font=sub_font,
            x=inner_x,
            y=sub_y,
            line_spacing=2,
            fill=INK_COLOR,
            max_width=inner_w,
            align="left",
        )
        assert sub_bottom < py1 - pad_bot, f"Sub-line overflowed panel {spec['tag']}"

        # Remaining space for flat motif
        motif_top = sub_bottom + 7
        motif_bot = py1 - pad_bot
        motif_h = motif_bot - motif_top
        assert motif_h >= 60, (
            f"Not enough remaining height ({motif_h}px) for motif in panel {spec['tag']}"
        )

        motif_img = render_supersampled_motif(inner_w, motif_h, MOTIF_DRAWERS[spec["motif"]])
        img.paste(motif_img, (inner_x, motif_top))

    # Re-verify final dimensions before saving
    assert img.size == (WIDTH, HEIGHT), f"Expected {(WIDTH, HEIGHT)}, got {img.size}"
    img.save(output_path, format="PNG", optimize=True)

    # Post-save verification
    with Image.open(output_path) as check:
        assert check.size == (WIDTH, HEIGHT), f"Saved image size mismatch: {check.size}"
    byte_size = os.path.getsize(output_path)
    assert byte_size <= MAX_BYTES, f"File size {byte_size} exceeds limit {MAX_BYTES}"


def main() -> None:
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(repo_dir, "entry.png")
    build_image(out_path)


if __name__ == "__main__":
    main()

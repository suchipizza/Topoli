"""Property card — ``card.png`` (1200×630) and ``card-square.png`` (1080×1080), pure Python.

Renderer decision (docs/decisions/010): Pillow + the bundled Inter font (SIL OFL 1.1, see
``ui/local-report/card/fonts/OFL.txt``); no browser, no extra install step. Emoji are not drawn
(no colour-emoji rasteriser without a browser); each finding gets a class badge and a severity
colour instead. Text auto-shrinks to fit; the longest German strings are the test case.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from topoli.core.domain import Lang
from topoli.core.i18n import t
from topoli.core.reporting.layer0 import Layer0
from topoli.core.reporting.share import TOPOLI_SITE_URL, run_link
from topoli.paths import asset_dir

ACCENT = (15, 107, 92)
INK = (27, 31, 30)
MUTED = (93, 102, 99)
BG = (251, 250, 247)
CARD = (255, 255, 255)
CLASS_COLOURS = {"A": (15, 107, 92), "B": (43, 108, 176), "C": (183, 121, 31), "D": (128, 90, 213)}
SEVERITY_COLOURS = {
    "info": (107, 114, 128),
    "low": (47, 133, 90),
    "medium": (192, 86, 33),
    "high": (184, 50, 50),
}


@dataclass(frozen=True)
class CardSize:
    width: int
    height: int
    name: str


LANDSCAPE = CardSize(1200, 630, "card.png")
SQUARE = CardSize(1080, 1080, "card-square.png")


def _font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    fonts = asset_dir("ui") / "local-report" / "card" / "fonts"
    path = fonts / ("Inter-Bold.ttf" if bold else "Inter-Regular.ttf")
    return ImageFont.truetype(str(path), size=size)


def _fit(  # noqa: PLR0917
    text: str, font_bold: bool, max_width: int, max_lines: int, start: int, minimum: int
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """Largest font size ≤ ``start`` at which ``text`` wraps into ≤ ``max_lines`` lines."""
    size = start
    while True:
        font = _font(font_bold, size)
        avg = max(1.0, font.getlength("n"))
        lines = textwrap.wrap(text, width=max(8, int(max_width / avg)))
        # verify with real measurements, re-wrapping tighter if needed
        while any(font.getlength(ln) > max_width for ln in lines) and len(lines) < 40:
            lines = textwrap.wrap(text, width=max(8, max(len(ln) for ln in lines) - 2))
        if len(lines) <= max_lines or size <= minimum:
            if size <= minimum and len(lines) > max_lines:
                last = lines[max_lines - 1][: max(0, int(max_width / avg) - 1)] + "…"
                lines = [*lines[: max_lines - 1], last]
            return font, lines
        size -= 2


def render_card(
    layer0: Layer0,
    out_dir: Path,
    *,
    map_image: Path | None = None,
    size: CardSize = LANDSCAPE,
) -> Path:
    lang: Lang = layer0.lang
    img = Image.new("RGB", (size.width, size.height), BG)
    draw = ImageDraw.Draw(img)
    pad = 40
    square = size.name == SQUARE.name
    text_w = size.width - 2 * pad - (0 if square else 300)

    # header
    draw.rounded_rectangle((pad, pad, pad + 118, pad + 40), radius=10, fill=ACCENT)
    draw.text((pad + 14, pad + 8), "Topoli", font=_font(True, 22), fill=(255, 255, 255))
    draw.text((pad + 132, pad + 12), t("report.tagline", lang), font=_font(False, 18), fill=MUTED)
    title_font, title_lines = _fit(layer0.header, True, text_w, 2, 34, 22)
    y = pad + 62
    for ln in title_lines:
        draw.text((pad, y), ln, font=title_font, fill=INK)
        y += int(title_font.size * 1.25)
    y += 10

    # findings — one uniform font size for all rows, up to two lines each
    n = len(layer0.lines)
    avail = (size.height - y - 150) if not square else (size.height - y - 380)
    per = max(56, avail // max(1, n))
    line_h = 1.22
    max_lines = 2 if per >= 16 + 2 * 14 * line_h else 1
    titles = [title for _icon, title, _consequence in layer0.lines]
    fits = [_fit(tt, False, text_w - 70, max_lines, 22, 14) for tt in titles]
    uniform = int(min((f.size for f, _ in fits), default=22))
    uniform = min(uniform, int((per - 16) / (max_lines * line_h)))
    fits = [_fit(tt, False, text_w - 70, max_lines, uniform, 14) for tt in titles]
    for f, (font, lines) in zip(layer0.findings, fits, strict=True):
        colour = SEVERITY_COLOURS.get(f.severity, MUTED)
        draw.rounded_rectangle(
            (pad, y, pad + text_w, y + per - 8), radius=10, fill=CARD, outline=(226, 229, 227)
        )
        draw.rectangle((pad, y + 6, pad + 6, y + per - 14), fill=colour)
        badge = CLASS_COLOURS.get(f.cls, MUTED)
        draw.ellipse((pad + 18, y + 12, pad + 44, y + 38), fill=badge)
        draw.text((pad + 24, y + 14), f.cls, font=_font(True, 17), fill=(255, 255, 255))
        ty = y + 10
        for ln in lines:
            draw.text((pad + 56, ty), ln, font=font, fill=INK)
            ty += int(font.size * line_h)
        y += per

    # map thumbnail
    if square:
        map_box = (pad, y + 4, size.width - pad, size.height - 150)
    else:
        map_box = (size.width - pad - 280, pad + 62, size.width - pad, size.height - 150)
    _paste_map(img, map_image, map_box)

    # footer: confidence, run link, star
    fy = size.height - 130
    conf_font, conf_lines = _fit(layer0.confidence, True, size.width - 2 * pad, 2, 20, 14)
    for ln in conf_lines:
        draw.text((pad, fy), ln, font=conf_font, fill=INK)
        fy += int(conf_font.size * 1.3)
    draw.text(
        (pad, size.height - 62),
        t("layer0.run_yourself", lang, url=run_link("card", lang).replace("https://", "")),
        font=_font(False, 18),
        fill=ACCENT,
    )
    star = (
        "★ "
        + t("report.star", lang).replace("⭐", "").strip()
        + " · "
        + TOPOLI_SITE_URL.replace("https://", "")
    )
    draw.text((pad, size.height - 36), star, font=_font(False, 16), fill=MUTED)

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / size.name
    # 256-colour palette keeps text crisp and the map thumbnail small (~150 KB instead of ~450 KB)
    img.quantize(
        colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FLOYDSTEINBERG
    ).save(path, format="PNG", optimize=True)
    return path


def _paste_map(img: Image.Image, map_image: Path | None, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if w <= 20 or h <= 20:
        return
    draw = ImageDraw.Draw(img)
    if map_image and map_image.is_file():
        thumb = Image.open(map_image).convert("RGB")
        scale = max(w / thumb.width, h / thumb.height)
        thumb = thumb.resize((max(1, int(thumb.width * scale)), max(1, int(thumb.height * scale))))
        left = (thumb.width - w) // 2
        top = (thumb.height - h) // 2
        thumb = thumb.crop((left, top, left + w, top + h))
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=14, fill=255)
        img.paste(thumb, (x0, y0), mask)
    else:
        draw.rounded_rectangle(box, radius=14, fill=(232, 236, 234), outline=(226, 229, 227))
    draw.rounded_rectangle(box, radius=14, outline=(200, 205, 203), width=2)


def render_cards(layer0: Layer0, out_dir: Path, *, map_image: Path | None = None) -> list[Path]:
    return [render_card(layer0, out_dir, map_image=map_image, size=s) for s in (LANDSCAPE, SQUARE)]

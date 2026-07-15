#!/usr/bin/env python3
"""Local font preflight for multilingual diagram previews.

The skill never bundles or redistributes fonts. It verifies that the host has a
font capable of rendering the non-ASCII text in a preview before rasterizing it,
so a successful PNG cannot silently contain tofu boxes.
"""
from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
import unicodedata
from pathlib import Path
from typing import Iterable

SVG_FONT_STACK = (
    "'Noto Sans CJK KR', 'NanumGothic', 'NanumBarunGothic', "
    "'Apple SD Gothic Neo', 'Malgun Gothic', 'Arial Unicode MS', "
    "'DejaVu Sans', sans-serif"
)

# Family order is also the order used in SVG_FONT_STACK. Known paths cover the
# common Linux, macOS, and Windows installations used by coding agents.
FONT_CANDIDATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Noto Sans CJK KR",
        (
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/Library/Fonts/NotoSansCJKkr-Regular.otf",
            "/System/Library/Fonts/NotoSansCJKkr-Regular.otf",
        ),
    ),
    (
        "NanumGothic",
        (
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/Library/Fonts/NanumGothic.ttf",
            str(Path.home() / "Library/Fonts/NanumGothic.ttf"),
        ),
    ),
    (
        "NanumBarunGothic",
        (
            "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf",
            "/Library/Fonts/NanumBarunGothic.ttf",
            str(Path.home() / "Library/Fonts/NanumBarunGothic.ttf"),
        ),
    ),
    (
        "Apple SD Gothic Neo",
        (
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/AppleSDGothicNeo-Regular.otf",
        ),
    ),
    (
        "Malgun Gothic",
        (
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/malgunbd.ttf",
        ),
    ),
    (
        "Arial Unicode MS",
        (
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "C:/Windows/Fonts/ARIALUNI.TTF",
        ),
    ),
)


@dataclass(frozen=True)
class FontResolution:
    family: str
    path: Path | None
    required_codepoints: frozenset[int]

    def public_report(self) -> dict[str, object]:
        return {
            "fontStack": SVG_FONT_STACK,
            "selectedFamily": self.family,
            "coverageVerified": True,
            "requiredCodepoints": len(self.required_codepoints),
        }


def required_non_ascii_codepoints(text: str) -> frozenset[int]:
    """Return visible non-ASCII codepoints that must be present in the font."""
    points: set[int] = set()
    for char in text:
        cp = ord(char)
        if cp < 128:
            continue
        category = unicodedata.category(char)
        if category.startswith("Z") or category in {"Cc", "Cf"}:
            continue
        points.add(cp)
    return frozenset(points)


def _font_codepoints(path: Path) -> set[int]:
    try:
        from fontTools.ttLib import TTCollection, TTFont
    except ImportError as exc:
        raise RuntimeError(
            "fontTools is required to verify multilingual preview glyph coverage; "
            "install it with `python -m pip install fonttools`"
        ) from exc

    codepoints: set[int] = set()
    suffix = path.suffix.lower()
    if suffix in {".ttc", ".otc"}:
        collection = TTCollection(str(path), lazy=True)
        try:
            fonts = collection.fonts
            for font in fonts:
                if "cmap" not in font:
                    continue
                for table in font["cmap"].tables:
                    codepoints.update(table.cmap.keys())
        finally:
            for font in collection.fonts:
                try:
                    font.close()
                except Exception:
                    pass
        return codepoints

    font = TTFont(str(path), lazy=True)
    try:
        if "cmap" in font:
            for table in font["cmap"].tables:
                codepoints.update(table.cmap.keys())
    finally:
        font.close()
    return codepoints


def _fc_match_path(family: str) -> Path | None:
    if not shutil.which("fc-match"):
        return None
    try:
        result = subprocess.run(
            ["fc-match", "-f", "%{file}\n", family],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None
    for line in result.stdout.splitlines():
        candidate = Path(line.strip())
        if candidate.is_file():
            return candidate
    return None


def _candidate_paths(family: str, known_paths: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    matched = _fc_match_path(family)
    if matched:
        paths.append(matched)
    for raw in known_paths:
        path = Path(raw)
        if path.is_file() and path not in paths:
            paths.append(path)
    return paths


def resolve_text_font(text: str) -> FontResolution:
    """Resolve a local font that covers all visible non-ASCII text.

    Latin-only previews do not require a special local font. Multilingual
    previews fail closed when no compatible font exists instead of emitting a
    syntactically valid but unreadable PNG.
    """
    required = required_non_ascii_codepoints(text)
    if not required:
        return FontResolution("DejaVu Sans", None, required)

    inspected: list[str] = []
    for family, known_paths in FONT_CANDIDATES:
        for path in _candidate_paths(family, known_paths):
            try:
                coverage = _font_codepoints(path)
            except Exception as exc:
                inspected.append(f"{family} ({path}): unreadable ({exc})")
                continue
            missing = required - coverage
            if not missing:
                return FontResolution(family, path, required)
            inspected.append(f"{family} ({path}): missing {len(missing)} codepoints")

    sample = "".join(chr(cp) for cp in sorted(required)[:20])
    detail = "; ".join(inspected[:8]) or "no candidate font files found"
    raise RuntimeError(
        "Multilingual text was detected but no installed font covers it. "
        "Install 'Noto Sans CJK KR' or 'NanumGothic' and rerun the preview. "
        f"Required sample: {sample!r}. Checked: {detail}"
    )

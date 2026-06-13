#!/usr/bin/env python3
"""Generate WebP variants and image metadata for portfolio pages."""
from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [
    "index.html",
    "illustration.html",
    "game-design.html",
    "graphic-design.html",
    "uxui-design.html",
    "use-cases.html",
]
WIDTHS = (640, 960, 1280, 1920)
WEBP_QUALITY = 82


def collect_image_srcs() -> list[str]:
    srcs: set[str] = set()
    pattern = re.compile(r'src="([^"]+\.(?:png|jpg|jpeg))"', re.I)
    for name in HTML_FILES:
        text = (ROOT / name).read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            srcs.add(match.group(1).replace("&amp;", "&"))
    return sorted(srcs)


def resize_width(img: Image.Image, target_w: int) -> Image.Image:
    if img.width <= target_w:
        return img.copy()
    target_h = round(img.height * (target_w / img.width))
    return img.resize((target_w, target_h), Image.Resampling.LANCZOS)


def optimize_image(rel_src: str) -> dict:
    src_path = ROOT / rel_src.replace("/", "\\")
    if not src_path.exists():
        return {"src": rel_src, "missing": True}

    original_kb = src_path.stat().st_size / 1024
    with Image.open(src_path) as img:
        img = img.convert("RGBA") if img.mode in ("RGBA", "P") else img.convert("RGB")
        width, height = img.size
        stem = src_path.with_suffix("")
        variants: list[dict] = []

        # Full-size WebP
        full_webp = stem.with_suffix(".webp")
        if not full_webp.exists() or full_webp.stat().st_mtime < src_path.stat().st_mtime:
            img.save(full_webp, "WEBP", quality=WEBP_QUALITY, method=6)
        variants.append(
            {
                "url": str(full_webp.relative_to(ROOT)).replace("\\", "/"),
                "w": width,
                "kb": round(full_webp.stat().st_size / 1024, 1),
            }
        )

        # Responsive widths
        srcset: list[dict] = []
        for target_w in WIDTHS:
            if target_w >= width:
                continue
            out = Path(f"{stem}-{target_w}w.webp")
            if not out.exists() or out.stat().st_mtime < src_path.stat().st_mtime:
                resized = resize_width(img, target_w)
                resized.save(out, "WEBP", quality=WEBP_QUALITY, method=6)
            srcset.append(
                {
                    "url": str(out.relative_to(ROOT)).replace("\\", "/"),
                    "w": target_w,
                    "kb": round(out.stat().st_size / 1024, 1),
                }
            )

        srcset.append(variants[0])
        srcset.sort(key=lambda item: item["w"])
        webp_kb = sum(item["kb"] for item in srcset)

        return {
            "src": rel_src,
            "width": width,
            "height": height,
            "original_kb": round(original_kb, 1),
            "webp_full_kb": variants[0]["kb"],
            "srcset": srcset,
            "savings_pct": round((1 - variants[0]["kb"] / original_kb) * 100, 1) if original_kb else 0,
        }


def main() -> None:
    srcs = collect_image_srcs()
    report = [optimize_image(src) for src in srcs]
    out = ROOT / "scripts" / "image-manifest.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    total_orig = sum(r.get("original_kb", 0) for r in report if not r.get("missing"))
    total_webp = sum(r.get("webp_full_kb", 0) for r in report if not r.get("missing"))
    print(f"Processed {len(report)} images")
    print(f"Original total: {total_orig:.0f} KB")
    print(f"WebP full total: {total_webp:.0f} KB")
    print(f"Savings (full WebP): {total_orig - total_webp:.0f} KB ({(1-total_webp/total_orig)*100:.1f}%)")


if __name__ == "__main__":
    main()

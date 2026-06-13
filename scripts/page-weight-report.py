#!/usr/bin/env python3
"""Estimate per-page image payload before/after optimization."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = {item["src"]: item for item in json.loads((ROOT / "scripts/image-manifest.json").read_text())}
PAGES = ["index.html", "illustration.html", "game-design.html", "graphic-design.html", "uxui-design.html", "use-cases.html"]


def pick_variant(meta: dict, viewport_w: int) -> float:
    for item in meta["srcset"]:
        if item["w"] >= viewport_w:
            return item["kb"]
    return meta["srcset"][-1]["kb"]


def page_images(name: str) -> list[str]:
    text = (ROOT / name).read_text(encoding="utf-8")
    srcs = re.findall(r'<img src="([^"]+\.(?:png|jpg|jpeg))"', text, re.I)
    return [s.replace("&amp;", "&") for s in srcs if "project-modal" not in text[text.find(s)-80:text.find(s)]]


def main() -> None:
    for vp_name, vp in [("mobile", 640), ("desktop", 1280)]:
        print(f"\n=== {vp_name} ({vp}px) ===")
        for page in PAGES:
            orig = webp = 0.0
            for src in page_images(page):
                meta = MANIFEST.get(src)
                if not meta:
                    continue
                orig += meta["original_kb"]
                webp += pick_variant(meta, vp)
            if orig:
                print(f"{page:22} {orig:8.0f} KB PNG/JPG -> {webp:8.0f} KB WebP  (-{orig-webp:.0f} KB, {(1-webp/orig)*100:.0f}%)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Apply picture/srcset/lazy attributes to portfolio HTML files."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "scripts" / "image-manifest.json"
HTML_FILES = [
    "index.html",
    "illustration.html",
    "game-design.html",
    "graphic-design.html",
    "uxui-design.html",
    "use-cases.html",
]

SIZES_GALLERY_2COL = "(max-width: 900px) 100vw, 50vw"
SIZES_GALLERY_FULL = "100vw"
SIZES_CASE_STUDY = "(max-width: 900px) 100vw, min(720px, 100vw)"
SIZES_ABOUT = "(max-width: 900px) 100vw, 40vw"


def build_picture(meta: dict, *, sizes: str, loading: str, fetchpriority: str | None = None) -> str:
    src = meta["src"].replace("&", "&amp;")
    srcset_items = [f'{item["url"]} {item["w"]}w' for item in meta["srcset"]]
    srcset = ", ".join(srcset_items)
    attrs = [
        f'width="{meta["width"]}"',
        f'height="{meta["height"]}"',
        f'loading="{loading}"',
        'decoding="async"',
    ]
    if fetchpriority:
        attrs.append(f'fetchpriority="{fetchpriority}"')
    img_attrs = " ".join(attrs)
    return (
        f'<picture>\n'
        f'      <source type="image/webp" srcset="{srcset}" sizes="{sizes}">\n'
        f'      <img src="{src}" alt="ALT_PLACEHOLDER" {img_attrs}>\n'
        f'    </picture>'
    )


def replace_img_tag(html: str, old_src: str, picture_html: str) -> str:
    escaped = re.escape(old_src.replace("&", "&amp;"))
    pattern = re.compile(
        rf'<img\s+src="{escaped}"\s+alt="([^"]*)"(?:\s[^>]*)?>',
        re.I,
    )
    return pattern.sub(lambda m: picture_html.replace("ALT_PLACEHOLDER", m.group(1)), html, count=1)


def main() -> None:
    manifest = {item["src"]: item for item in json.loads(MANIFEST.read_text(encoding="utf-8"))}

    for name in HTML_FILES:
        path = ROOT / name
        html = path.read_text(encoding="utf-8")
        original = html

        for src, meta in manifest.items():
            if meta.get("missing"):
                continue
            html_src = src.replace("&", "&amp;")
            if f'src="{html_src}"' not in html:
                continue

            if name == "index.html" and src == "Vector-profile.png":
                sizes, loading = SIZES_ABOUT, "lazy"
                fetchpriority = None
            elif name == "use-cases.html":
                sizes, loading = SIZES_CASE_STUDY, "lazy"
                fetchpriority = None
            elif name == "game-design.html" and "Steam Capsule Concepts" in src:
                sizes, loading = SIZES_GALLERY_FULL, "lazy"
                fetchpriority = None
            else:
                sizes, loading = SIZES_GALLERY_2COL, "lazy"
                fetchpriority = None

            picture = build_picture(meta, sizes=sizes, loading=loading, fetchpriority=fetchpriority)
            html = replace_img_tag(html, src, picture)

        # First two visible gallery images on portfolio subpages
        if name not in ("index.html", "use-cases.html"):
            html = html.replace('loading="lazy" decoding="async">', 'loading="eager" decoding="async">', 2)

        # Modal image should stay plain img without lazy on empty src
        html = re.sub(
            r'(<img class="project-modal-image"[^>]*)( loading="[^"]*")?( decoding="[^"]*")?',
            r'\1',
            html,
        )

        if html != original:
            path.write_text(html, encoding="utf-8")
            print(f"Updated {name}")


if __name__ == "__main__":
    main()

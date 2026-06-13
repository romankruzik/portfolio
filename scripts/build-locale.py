#!/usr/bin/env python3
"""Build Czech HTML pages and inject language switcher into English pages."""
from __future__ import annotations

import re
from pathlib import Path

from locale_data import PAGE_META_CS, PAGE_META_EN, PAGES, TRANSLATIONS

ROOT = Path(__file__).resolve().parents[1]

LANG_SWITCHER_CSS = """
  .lang-switch {
    display: flex;
    align-items: center;
    gap: 6px;
    font-family: 'DM Mono', monospace;
    font-size: 12px;
    letter-spacing: 0.14em;
    text-transform: uppercase;
  }
  .lang-switch__link {
    color: var(--muted);
    text-decoration: none;
    transition: color 0.2s;
  }
  .lang-switch__link:hover { color: var(--electric); }
  .lang-switch__link.is-active {
    color: var(--electric);
  }
  .lang-switch__sep {
    color: var(--tag);
    opacity: 0.6;
  }
  .nav-actions {
    display: flex;
    align-items: center;
    gap: 28px;
  }
  .mobile-menu-lang {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
  }
"""

INTERNAL_HTML = [p for p in PAGES]


def page_pair(name: str) -> tuple[str, str]:
    if name.endswith("-cz.html"):
        en = name.replace("-cz.html", ".html")
        return en, name
    return name, name.replace(".html", "-cz.html")


def lang_switcher_html(en_name: str, active: str) -> str:
    _, cz_name = page_pair(en_name)
    if active == "cs":
        cz_class = ' class="lang-switch__link is-active" hreflang="cs" lang="cs" aria-current="page"'
        en_class = ' class="lang-switch__link" hreflang="en" lang="en"'
    else:
        cz_class = ' class="lang-switch__link" hreflang="cs" lang="cs"'
        en_class = ' class="lang-switch__link is-active" hreflang="en" lang="en" aria-current="page"'
    label = "Jazyk" if active == "cs" else "Language"
    return (
        f'<div class="lang-switch" aria-label="{label}">\n'
        f'    <a href="{cz_name}"{cz_class}>CZ</a>\n'
        f'    <span class="lang-switch__sep" aria-hidden="true">/</span>\n'
        f'    <a href="{en_name}"{en_class}>EN</a>\n'
        f'  </div>'
    )


def fix_href_for_locale(href: str, to_cz: bool) -> str:
    if re.match(r"^(https?:|mailto:|tel:|#)", href):
        return href
    if not to_cz:
        return re.sub(r"([\w-]+)-cz\.html", r"\1.html", href)
    def repl(match: re.Match[str]) -> str:
        base = match.group(1)
        if base.endswith("-cz"):
            return match.group(0)
        return f"{base}-cz.html"
    return re.sub(r"([\w-]+)\.html", repl, href)


def rewrite_internal_links(html: str, to_cz: bool) -> str:
    def repl(match: re.Match[str]) -> str:
        href = match.group(1)
        return f'href="{fix_href_for_locale(href, to_cz)}"'

    return re.sub(r'href="([^"]+\.html[^"]*)"', repl, html)


LOCALE_STATE_SCRIPT = '<script src="locale-state.js"></script>\n'


def inject_locale_state_script(html: str) -> str:
    if "locale-state.js" in html:
        return html
    return html.replace("</body>", LOCALE_STATE_SCRIPT + "</body>", 1)


def protect_asset_paths(text: str) -> tuple[str, dict[str, str]]:
    """Keep file paths in src/srcset/href out of translation replacements."""
    store: dict[str, str] = {}
    idx = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal idx
        key = f"\x00ASSETPATH{idx}\x00"
        store[key] = match.group(0)
        idx += 1
        return key

    protected = re.sub(
        r'(?:src|srcset|href)="[^"]*(?:Case Studies/|Work/|Logos/)[^"]*"',
        repl,
        text,
    )
    return protected, store


def restore_asset_paths(text: str, store: dict[str, str]) -> str:
    for key, value in store.items():
        text = text.replace(key, value)
    return text


def apply_translations(html: str) -> str:
  parts = re.split(r"(<style[\s\S]*?</style>|<script[\s\S]*?</script>)", html)
  for i, part in enumerate(parts):
    if part.startswith("<style") or part.startswith("<script"):
      continue
    protected, store = protect_asset_paths(part)
    for en, cs in TRANSLATIONS:
      protected = protected.replace(en, cs)
    parts[i] = restore_asset_paths(protected, store)
  return "".join(parts)


def inject_meta(html: str, name: str, lang: str) -> str:
    if lang == "cs":
        meta = PAGE_META_CS.get(name, {})
        title = meta.get("title", "")
        desc = meta.get("description", "")
        html = re.sub(r"<html lang=\"en\">", '<html lang="cs">', html, count=1)
        if title:
            html = re.sub(r"<title>[^<]+</title>", f"<title>{title}</title>", html, count=1)
    else:
        meta = PAGE_META_EN.get(name, {})
        desc = meta.get("description", "")
    if desc and 'name="description"' not in html:
        html = html.replace(
            "<meta name=\"viewport\"",
            f'<meta name="description" content="{desc}">\n<meta name="viewport"',
            1,
        )
    if lang == "cs" and desc and 'name="description"' in html:
        html = re.sub(
            r'<meta name="description" content="[^"]*">',
            f'<meta name="description" content="{desc}">',
            html,
            count=1,
        )
    return html


def inject_lang_css(html: str) -> str:
    if ".lang-switch" in html:
        return html
    return html.replace("</style>", LANG_SWITCHER_CSS + "</style>", 1)


def inject_lang_switcher_index(html: str, en_name: str, active: str) -> str:
    switcher = lang_switcher_html(en_name, active)
    html = html.replace(
        '  <a href="#contact" class="nav-cta">',
        f"  {switcher}\n  <a href=\"#contact\" class=\"nav-cta\">",
        1,
    )
    html = html.replace(
        '    <li><a href="#contact" class="mobile-menu-link">Contact</a></li>\n  </ul>',
        f'    <li><a href="#contact" class="mobile-menu-link">{"Kontakt" if active == "cs" else "Contact"}</a></li>\n'
        f'    <li class="mobile-menu-lang">{switcher}</li>\n  </ul>',
        1,
    )
    html = html.replace(
        '    <li><a href="#contact" class="mobile-menu-link">Kontakt</a></li>\n  </ul>',
        f'    <li><a href="#contact" class="mobile-menu-link">Kontakt</a></li>\n'
        f'    <li class="mobile-menu-lang">{switcher}</li>\n  </ul>',
        1,
    )
    return html


def inject_lang_switcher_subpage(html: str, en_name: str, active: str) -> str:
    switcher = lang_switcher_html(en_name, active)
    back_anchor = "#why-roman" if en_name == "use-cases.html" else "#services"
    back_text = "← Zpět" if active == "cs" else "← Back"
    index_href = "index-cz.html" if active == "cs" else "index.html"
    block = (
        f'  <div class="nav-actions">\n'
        f"    {switcher}\n"
        f'    <a href="{index_href}{back_anchor}" class="back-link">{back_text}</a>\n'
        f"  </div>\n"
    )
    html = re.sub(
        r'(<nav id="nav">\s*<a href=")[^"]*(" class="nav-logo">)',
        rf"\1{index_href}\2",
        html,
        count=1,
    )
    return html.replace("</nav>", block + "</nav>", 1)


def strip_lang_switcher(html: str) -> str:
    html = re.sub(r'<div class="lang-switch"[\s\S]*?</div>\s*', "", html)
    html = re.sub(r'<div class="nav-actions"[\s\S]*?</div>\s*', "", html)
    html = re.sub(r'<li class="mobile-menu-lang">[\s\S]*?</li>\s*', "", html)
    return html


def build_czech_page(en_name: str) -> str:
    html = (ROOT / en_name).read_text(encoding="utf-8")
    html = strip_lang_switcher(html)
    html = inject_lang_css(html)
    html = apply_translations(html)
    html = rewrite_internal_links(html, to_cz=True)
    html = inject_meta(html, en_name, "cs")
    if en_name == "index.html":
        html = inject_lang_switcher_index(html, en_name, "cs")
        html = html.replace('href="#" class="nav-logo"', 'href="index-cz.html" class="nav-logo"', 1)
    else:
        html = inject_lang_switcher_subpage(html, en_name, "cs")
    html = inject_locale_state_script(html)
    return html


def patch_english_page(en_name: str) -> str:
    html = (ROOT / en_name).read_text(encoding="utf-8")
    html = strip_lang_switcher(html)
    html = inject_lang_css(html)
    html = inject_meta(html, en_name, "en")
    if en_name == "index.html":
        html = inject_lang_switcher_index(html, en_name, "en")
    else:
        html = inject_lang_switcher_subpage(html, en_name, "en")
    html = inject_locale_state_script(html)
    return html


def main() -> None:
    created: list[str] = []
    modified: list[str] = []

    for en_name in PAGES:
        cz_name = en_name.replace(".html", "-cz.html")
        cz_html = build_czech_page(en_name)
        (ROOT / cz_name).write_text(cz_html, encoding="utf-8")
        created.append(cz_name)

        en_html = patch_english_page(en_name)
        (ROOT / en_name).write_text(en_html, encoding="utf-8")
        modified.append(en_name)

    print("Created:", ", ".join(created))
    print("Modified:", ", ".join(modified))


if __name__ == "__main__":
    main()

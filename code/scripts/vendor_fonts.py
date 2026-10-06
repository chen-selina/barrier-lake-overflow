#!/usr/bin/env python3
"""
把儀表板用的 Google Fonts 下載到 dashboard/vendor/fonts/，離線也能正常顯示。

    python scripts/vendor_fonts.py      # 在 code/ 底下執行，需要網路

Archivo、IBM Plex Mono 下載 latin 與 latin-ext 全部切片。Noto Sans TC 的
Google 切片有上百個，只下載「儀表板文字與資料檔用得到的字」所在的切片；
資料更新、出現新字時重跑一次。用不到的字（例如人工查證備註）會退回系統字型
（Microsoft JhengHei／PingFang TC，見 styles.css 的 --sans）。

字型授權：三者皆為 SIL Open Font License 1.1。
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

DASH = Path(__file__).resolve().parents[1] / "dashboard"
OUT = DASH / "vendor" / "fonts"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")   # 沒有瀏覽器 UA 會拿到 ttf 而不是 woff2

LATIN_CSS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@75..125,400..800"
             "&family=IBM+Plex+Mono:wght@400;500&display=swap")
TC_CSS = "https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700&display=swap"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def used_chars() -> set:
    chars = set()
    for p in [DASH / "index.html", *DASH.glob("*.js"), *(DASH / "data").glob("*.js")]:
        chars |= set(p.read_text(encoding="utf-8"))
    return {ord(c) for c in chars if ord(c) > 0x7F}


def parse_range(s: str) -> list:
    out = []
    for part in s.split(","):
        part = part.strip().upper().removeprefix("U+")
        if "-" in part:
            a, b = part.split("-")
            out.append((int(a, 16), int(b, 16)))
        elif "?" in part:
            out.append((int(part.replace("?", "0"), 16), int(part.replace("?", "F"), 16)))
        else:
            out.append((int(part, 16), int(part, 16)))
    return out


def blocks(css: str) -> list:
    return re.findall(r"(/\*[^*]*\*/\s*)?(@font-face\s*\{[^}]*\})", css)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.woff2"):
        old.unlink()
    need = used_chars()
    kept, total_bytes = [], 0

    for css_url, subset_all in ((LATIN_CSS, True), (TC_CSS, False)):
        css = fetch(css_url).decode("utf-8")
        for comment, face in blocks(css):
            label = (comment or "").strip()
            if subset_all:
                if label not in ("/* latin */", "/* latin-ext */"):
                    continue
            else:
                m = re.search(r"unicode-range:\s*([^;]+);", face)
                ranges = parse_range(m.group(1)) if m else []
                if not any(a <= c <= b for c in need for a, b in ranges):
                    continue
            url = re.search(r"url\((https://[^)]+\.woff2)\)", face).group(1)
            family = re.search(r"font-family:\s*'([^']+)'", face).group(1)
            name = family.replace(" ", "") + "-" + url.rsplit("/", 1)[1]
            data = fetch(url)
            (OUT / name).write_bytes(data)
            total_bytes += len(data)
            kept.append(face.replace(url, name))

    (OUT / "fonts.css").write_text(
        "/* 由 scripts/vendor_fonts.py 產生，請勿手動編輯。字型授權：SIL Open Font License 1.1 */\n"
        + "\n".join(kept) + "\n", encoding="utf-8")
    print(f"{len(kept)} 個字型切片，共 {total_bytes / 1e6:.1f} MB → {OUT}")


if __name__ == "__main__":
    main()

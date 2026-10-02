#!/usr/bin/env python3
"""
SAR 判定結果 → 影像證據圖（PNG），給 GitHub、簡報、儀表板直接看。

每張圖三格：事件前中位數｜事件後｜複核期（沒有複核期就兩格），
疊上候選多邊形（A 級綠、B 級橘、C 級灰；複核未持續者虛線）與壩址紅點。
影像以 σ⁰ VV dB 顯示（-25～0 dB，水體為暗色）。

    cd code
    python scripts/make_sar_evidence.py              # 跑下面 RUNS 裡檔案齊全的組合
    python scripts/make_sar_evidence.py --out-dir ../docs/evidence

需要 matplotlib（pip install matplotlib）。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from analyze_ndwi_change import crop_window  # noqa: E402
from pipeline.preprocess.sar import load_s1_geotiff  # noqa: E402

S1 = "../data/raw/sentinel1"
DERIVED = "../data/derived"
DAM = (121.29752, 23.70061)
HALF_KM = 2.0

# (結果 JSON, 事件後影像, 複核影像或 None, 輸出檔名, 標題)
RUNS = [
    ("final_0722.json", "S1_VV_post_matai_an.tif", "S1_VV_post2_matai_an.tif",
     "bl071_sar_0722.png", "2025-07-22（形成後約 36 小時）＋ 7/28 複核"),
    ("final_0728.json", "S1_VV_post0728_matai_an.tif", "S1_VV_post0803_matai_an.tif",
     "bl071_sar_0728.png", "2025-07-28（形成後約 7 天）＋ 8/3 複核"),
    ("final_0821.json", "S1_VV_post0821_matai_an.tif", "S1_VV_post0827_matai_an.tif",
     "bl071_sar_0821.png", "2025-08-21 ＋ 8/27 複核"),
    ("final_0827.json", "S1_VV_post0827_matai_an.tif", None,
     "bl071_sar_0827.png", "2025-08-27（單期）"),
]

GRADE_COLOR = {"A": "#2ecc71", "B": "#f39c12", "C": "#bdc3c7"}


def _crop(path: str):
    sc = load_s1_geotiff(path)
    win, row0, col0 = crop_window(sc, DAM[0], DAM[1], HALF_KM, key="db")
    a, _, c, _, e, f = sc["transform"]
    west = c + col0 * a
    north = f + row0 * e
    east = west + win.shape[1] * a
    south = north + win.shape[0] * e
    return win, (west, east, south, north)


def render(result_json: str, pre_tif: str, post_tif: str, later_tif, out_png: str, title: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import patheffects
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    cjk = [n for n in ("Microsoft JhengHei", "Noto Sans CJK TC", "PingFang TC", "Heiti TC",
                                "Noto Sans CJK JP", "Noto Sans CJK SC") if n in have]
    matplotlib.rcParams["font.family"] = cjk[:1] + ["sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    with open(result_json, encoding="utf-8") as fh:
        res = json.load(fh)
    panels = [("事件前（中位數）", pre_tif, False), ("事件後", post_tif, True)]
    if later_tif:
        panels.append(("複核期", later_tif, True))

    fig, axes = plt.subplots(1, len(panels), figsize=(5.2 * len(panels), 5.6), squeeze=False)
    for ax, (label, path, overlay) in zip(axes[0], panels):
        img, extent = _crop(path)
        ax.imshow(img, cmap="gray", vmin=-25, vmax=0, extent=extent, interpolation="nearest")
        ax.plot(*DAM, "o", color="red", ms=7, mec="white", mew=1.2, zorder=5)
        if overlay:
            for cand in res.get("candidates", []):
                poly = cand.get("polygonLonLat") or []
                if len(poly) < 3:
                    continue
                xs, ys = zip(*(poly + [poly[0]]))
                persistent = cand.get("persistent")
                checked = cand.get("laterScenesChecked", 0) > 0
                style = "--" if (checked and not persistent) else "-"
                ax.plot(xs, ys, style, color=GRADE_COLOR.get(cand["grade"], "white"), lw=2, zorder=4)
                cx, cy = cand["centroidLonLat"]
                ax.annotate(f"{cand['grade']} {cand['areaHectare']:.1f} ha", (cx, cy),
                            xytext=(6, 6), textcoords="offset points", fontsize=9,
                            color=GRADE_COLOR.get(cand["grade"], "white"), weight="bold",
                            path_effects=[patheffects.withStroke(linewidth=3, foreground="black")])
        ax.set_title(label, fontsize=11)
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_aspect(1 / np.cos(np.radians(DAM[1])))

    n = len(res.get("candidates", []))
    grades = "、".join(f"{c['grade']} 級 {c['areaHectare']:.1f} 公頃" for c in res.get("candidates", []))
    fig.suptitle(f"馬太鞍溪 Sentinel-1 SAR｜{title}", fontsize=13, weight="bold")
    fig.text(0.5, 0.02,
             (f"候選 {n} 個：{grades}" if n else "無候選")
             + "｜紅點：壩址｜實線：持續或未複核，虛線：複核未持續｜σ⁰ VV −25～0 dB，水體為暗色",
             ha="center", fontsize=9, color="#444")
    fig.tight_layout(rect=(0, 0.05, 1, 0.94))
    fig.savefig(out_png, dpi=130)
    plt.close(fig)
    print(f"寫入 {out_png}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--s1-dir", default=S1)
    ap.add_argument("--derived-dir", default=DERIVED)
    ap.add_argument("--out-dir", default="../docs/evidence")
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    pre = os.path.join(args.s1_dir, "S1_VV_pre_matai_an.tif")
    for res, post, later, out, title in RUNS:
        paths = [os.path.join(args.derived_dir, res), pre, os.path.join(args.s1_dir, post)]
        later_path = os.path.join(args.s1_dir, later) if later else None
        missing = [p for p in paths + ([later_path] if later_path else []) if not os.path.exists(p)]
        if missing:
            print(f"略過 {out}：缺少 {', '.join(missing)}")
            continue
        render(paths[0], pre, paths[2], later_path, os.path.join(args.out_dir, out), title)


if __name__ == "__main__":
    main()

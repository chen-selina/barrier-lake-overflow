#!/usr/bin/env python3
"""
負案例 E1 查證：把 2026 各期 SAR 候選範圍疊到 Sentinel-2 光學影像上，逐期看那裡是不是水。

    cd code
    python scripts/check_neg_e1.py

需要：
    data/raw/sentinel2/S2_E1_check_2026.tif   （scripts/gee_check_s2_e1.js 匯出，12 期 × B2 B3 B4 B8 B11 SCL）
    data/derived/final_neg2026_matai_an_*.json （run_sar_series.py 的結果）
    data/raw/sentinel1/*.tif                   （畫 SAR 對照圖用；缺的話只略過那張圖）

輸出：
    終端機印出逐期統計表（E1 範圍內的 SCL 分類、MNDWI、近紅外線，並和外圍一圈比較）
    docs/evidence/neg2026_e1_optical.png      晴天三期真色＋MNDWI，疊 E1 範圍
    docs/evidence/neg2026_e1_sar.png          2025／2026 SAR 與地形，疊 E1 範圍

判讀：水的近紅外線（B8）通常 < 500、MNDWI 明顯 > 0、SCL 會判為 6（水）。
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
from collections import Counter

import numpy as np

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DAM = (121.29752, 23.70061)
SCL_TEXT = {0: "無資料", 1: "飽和", 2: "暗色地表", 3: "雲影", 4: "植生", 5: "裸露地表", 6: "水",
            7: "未分類", 8: "雲（中）", 9: "雲（高）", 10: "卷雲", 11: "雪"}
CLOUDY = {3, 8, 9, 10}


def _font():
    import matplotlib
    from matplotlib import font_manager
    have = {f.name for f in font_manager.fontManager.ttflist}
    cjk = [n for n in ("Microsoft JhengHei", "Noto Sans CJK TC", "PingFang TC", "Heiti TC",
                       "Noto Sans CJK JP", "Noto Sans CJK SC") if n in have]
    matplotlib.rcParams["font.family"] = cjk[:1] + ["sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False


def e1_polygons(derived: str, name: str) -> list:
    out = []
    for f in sorted(glob.glob(os.path.join(derived, f"final_{name}_*.json"))):
        with open(f, encoding="utf-8") as fh:
            for c in json.load(fh)["candidates"]:
                if len(c.get("polygonLonLat") or []) >= 3:
                    out.append(c["polygonLonLat"])
    return out


def optical(s2_path: str, polys: list, out_png: str) -> None:
    import rasterio
    from rasterio.features import rasterize
    from scipy import ndimage

    src = rasterio.open(s2_path)
    desc = src.descriptions
    dates = sorted({d.split("_")[-1] for d in desc})

    def band(b, d):
        name = next(x for x in desc if x.endswith(f"_{b}_{d}"))
        return src.read(desc.index(name) + 1).astype(float)

    mask = rasterize([({"type": "Polygon", "coordinates": [p]}, 1) for p in polys],
                     out_shape=(src.height, src.width), transform=src.transform).astype(bool)
    ring = ndimage.binary_dilation(mask, iterations=6) & ~mask
    print(f"E1 範圍（2026 各期 SAR 候選聯集）：{mask.sum()} 像元，約 {mask.sum() * 0.0091:.1f} 公頃\n")
    print("日期        E1 範圍內 SCL 分類（前兩名）         MNDWI E1／外圍   B8 E1／外圍   晴天")
    clear = []
    for d in dates:
        scl = band("SCL", d)
        b3, b8, b11 = band("B3", d), band("B8", d), band("B11", d)
        m = (b3 - b11) / (b3 + b11 + 1e-9)
        cnt = Counter(scl[mask].astype(int))
        tot = sum(cnt.values())
        cls = "、".join(f"{SCL_TEXT.get(k, k)} {100 * v / tot:.0f}%" for k, v in cnt.most_common(2))
        is_clear = sum(v for k, v in cnt.items() if k in CLOUDY) / tot < 0.5
        if is_clear:
            clear.append(d)
        print(f"{d[:4]}-{d[4:6]}-{d[6:]}  {cls:30s}  {m[mask].mean():6.2f}／{m[ring].mean():5.2f}"
              f"   {b8[mask].mean():5.0f}／{b8[ring].mean():5.0f}   {'是' if is_clear else '否（雲）'}")
    water_px = sum(int((band("SCL", d)[mask] == 6).sum()) for d in clear)
    print(f"\n晴天 {len(clear)} 期，E1 範圍內被判為水的像元合計：{water_px}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _font()
    t = src.transform
    ext = (t.c, t.c + src.width * t.a, t.f + src.height * t.e, t.f)
    show = clear[:1] + clear[len(clear) // 2:len(clear) // 2 + 1] + clear[-1:]
    fig, axs = plt.subplots(2, len(show), figsize=(5.7 * len(show), 11.5), squeeze=False)
    for j, d in enumerate(show):
        label = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        rgb = np.clip(np.dstack([band(b, d) for b in ("B4", "B3", "B2")]) / 2500, 0, 1) ** 0.8
        b3, b11, scl = band("B3", d), band("B11", d), band("SCL", d)
        axs[0, j].imshow(rgb, extent=ext)
        axs[0, j].set_title(f"{label} 真色")
        axs[1, j].imshow((b3 - b11) / (b3 + b11 + 1e-9), cmap="BrBG", vmin=-0.5, vmax=0.5, extent=ext)
        axs[1, j].imshow(np.ma.masked_where(scl != 6, scl), cmap="winter", extent=ext)
        axs[1, j].set_title(f"{label} MNDWI（綠＝偏水）＋S2 判為水（藍）")
        for ax in axs[:, j]:
            for p in polys:
                xs, ys = zip(*(p + [p[0]]))
                ax.plot(xs, ys, "-", color="magenta", lw=1.2)
            ax.plot(*DAM, "o", color="red", ms=7, mec="white")
            ax.set_xticks([]), ax.set_yticks([])
            ax.set_aspect(1 / math.cos(math.radians(DAM[1])))
    fig.suptitle("負案例 E1 光學查證：洋紅框＝2026 各期 SAR 候選範圍、紅點＝清冊壩址", fontsize=14)
    fig.tight_layout()
    fig.savefig(out_png, dpi=90)
    print(f"寫入 {out_png}")


def sar(s1_dir: str, derived: str, name: str, out_png: str) -> None:
    import rasterio
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _font()
    half = 1.2
    panels = [
        ("2025 事件前中位數", "S1_VV_pre_matai_an.tif", None),
        ("2025-08-27（湖）", "S1_VV_post0827_matai_an.tif", "final_0827.json"),
        ("2026 事件前中位數（3–5 月）", f"S1_VV_{name}_pre.tif", None),
        ("2026-06-05", f"S1_VV_{name}_20260605.tif", f"final_{name}_20260605.json"),
        ("2026-07-06", f"S1_VV_{name}_20260706.tif", f"final_{name}_20260706.json"),
        ("2026-09-16", f"S1_VV_{name}_20260916.tif", f"final_{name}_20260916.json"),
    ]
    missing = [p for _, p, _ in panels if not os.path.exists(os.path.join(s1_dir, p))]
    if missing:
        print(f"略過 SAR 對照圖：缺少 {', '.join(missing)}")
        return

    def crop(path):
        with rasterio.open(path) as s:
            a, t = s.read(1), s.transform
            dlat = half / 111.32
            dlon = half / (111.32 * math.cos(math.radians(DAM[1])))
            r0, c0 = s.index(DAM[0] - dlon, DAM[1] + dlat)
            r1, c1 = s.index(DAM[0] + dlon, DAM[1] - dlat)
            return a[r0:r1, c0:c1], (t.c + c0 * t.a, t.c + c1 * t.a, t.f + r1 * t.e, t.f + r0 * t.e)

    fig, axs = plt.subplots(2, 4, figsize=(20, 10.5))
    for ax, (label, tif, js) in zip(axs.flat, panels):
        w, ext = crop(os.path.join(s1_dir, tif))
        ax.imshow(w, cmap="gray", vmin=-25, vmax=0, extent=ext)
        if js and os.path.exists(os.path.join(derived, js)):
            with open(os.path.join(derived, js), encoding="utf-8") as fh:
                for c in json.load(fh)["candidates"]:
                    p = c["polygonLonLat"]
                    xs, ys = zip(*(p + [p[0]]))
                    ax.plot(xs, ys, "-", color="#2ecc71" if c["grade"] == "A" else "#f39c12", lw=2)
        ax.set_title(label)
    dem, ext = crop(os.path.join(s1_dir, "NASADEM_matai_an.tif"))
    dem = dem.astype(float)
    gy, gx = np.gradient(dem, 10.0, 9.16)
    xs = np.linspace(ext[0], ext[1], dem.shape[1])
    ys = np.linspace(ext[3], ext[2], dem.shape[0])
    cs = axs.flat[6].contour(xs, ys, dem, levels=range(700, 2000, 50), colors="k", linewidths=.4)
    axs.flat[6].clabel(cs, fmt="%d", fontsize=6)
    axs.flat[6].set_title("NASADEM 等高線（事件前地形）")
    im = axs.flat[7].imshow(np.degrees(np.arctan(np.hypot(gx, gy))), cmap="magma", vmin=0, vmax=60, extent=ext)
    plt.colorbar(im, ax=axs.flat[7], fraction=.046, label="坡度（度）")
    axs.flat[7].set_title("坡度")
    for ax in axs.flat:
        ax.plot(*DAM, "o", color="red", ms=7, mec="white")
        ax.set_xticks([]), ax.set_yticks([])
        ax.set_aspect(1 / math.cos(math.radians(DAM[1])))
    fig.suptitle("負案例 E1 位置（2.4 km 視窗；紅點＝清冊壩址；綠／橘框＝SAR 候選）", fontsize=14)
    fig.tight_layout()
    fig.savefig(out_png, dpi=90)
    print(f"寫入 {out_png}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", default="neg2026_matai_an")
    ap.add_argument("--s2", default=os.path.join(REPO, "data", "raw", "sentinel2", "S2_E1_check_2026.tif"))
    ap.add_argument("--s1-dir", default=os.path.join(REPO, "data", "raw", "sentinel1"))
    ap.add_argument("--derived", default=os.path.join(REPO, "data", "derived"))
    ap.add_argument("--out-dir", default=os.path.join(REPO, "docs", "evidence"))
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    polys = e1_polygons(args.derived, args.name)
    if not polys:
        raise SystemExit(f"找不到 final_{args.name}_*.json 的候選，請先跑 run_sar_series.py")
    if os.path.exists(args.s2):
        optical(args.s2, polys, os.path.join(args.out_dir, "neg2026_e1_optical.png"))
    else:
        print(f"略過光學查證：找不到 {args.s2}（見 scripts/gee_check_s2_e1.js）")
    sar(args.s1_dir, args.derived, args.name, os.path.join(args.out_dir, "neg2026_e1_sar.png"))


if __name__ == "__main__":
    main()

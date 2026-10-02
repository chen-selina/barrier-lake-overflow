#!/usr/bin/env python3
"""
疑似堰塞湖判定

    事件前／後 σ⁰ → Lee 濾波 ┬ 低回波判水（扣陰影／疊置／陡坡）→ 新增水體
                             └ 振幅比值（扣水體、疊置、陰影）→ 崩塌
    每塊新增水體依下列條件評分 → A/B/C

1. 貼河道：外擴 river_buffer_px 後碰到河道（事件前水體 ∪ DEM D8 河網）。
   堰塞湖是河道被堵後往上游回淹，離河道遠的低回波多半是水田或殘餘陰影。
2. 附近有崩塌：search_radius_m 內有崩塌像元。有 DEM 時還要求崩塌最低點
   不高於湖底 + 容許值，代表土石到了河床、在湖的下游端。
3. 持續：後續影像同位置也有新增水體（IoU ≥ persistence_iou）。

A = 1+2+3，B = 1+2，C = 只有 1，不貼河道的不列入。

    python -m pipeline.detect.barrier_lake
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Sequence, Union

import numpy as np
from scipy import ndimage

from pipeline.detect.landslide import LANDSLIDE_THRESHOLD_DB, LandslideResult, detect_landslides
from pipeline.detect.water import WaterExtent, change_detection, extract_water_sar
from pipeline.preprocess.mask import (S1_IW_MID_INCIDENCE_DEG, S1_LOOK_AZIMUTH_DEG,
                                      sar_invalid_masks)
from pipeline.preprocess.sar import lee_filter

EIGHT = np.ones((3, 3), dtype=bool)


def _area_cell(cell_size_m: Union[float, tuple]) -> float:
    """等效邊長（面積用）：(dx, dy) → sqrt(dx·dy)。"""
    if isinstance(cell_size_m, (tuple, list)):
        return math.sqrt(float(cell_size_m[0]) * float(cell_size_m[1]))
    return float(cell_size_m)


def _sampling(cell_size_m: Union[float, tuple]) -> tuple:
    """distance_transform_edt 的 (row, col) 取樣間距：(dy, dx)。"""
    if isinstance(cell_size_m, (tuple, list)):
        return float(cell_size_m[1]), float(cell_size_m[0])
    return float(cell_size_m), float(cell_size_m)


# 河道：事件前水體 ∪ DEM D8 流量累積河網

_D8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def flow_accumulation_d8(dem: np.ndarray) -> np.ndarray:
    """
    簡易 D8 流量累積（像元數，含自身）。每個像元流向 8 鄰域中坡降最大
    （高差/距離）的較低像元，由高到低依序往下游累加。沒有先做填窪，
    窪地會截斷累積——窄谷河網用 10m DEM 影響不大，要精確集水區時再換
    正式水文前處理。nan 視為無資料、不收不送。

    >>> dem = np.array([[3.0, 2.0, 1.0]])
    >>> flow_accumulation_d8(dem).tolist()
    [[1.0, 2.0, 3.0]]
    """
    z = np.asarray(dem, dtype="float64")
    rows, cols = z.shape
    padded = np.pad(z, 1, constant_values=np.nan)
    best_drop = np.zeros_like(z)
    receiver = np.full(z.shape, -1, dtype=np.int64)
    rr, cc = np.mgrid[0:rows, 0:cols]
    for dr, dc in _D8:
        neigh = padded[1 + dr:1 + dr + rows, 1 + dc:1 + dc + cols]
        with np.errstate(invalid="ignore"):
            drop = (z - neigh) / math.hypot(dr, dc)
        drop = np.nan_to_num(drop, nan=0.0)
        better = drop > best_drop
        best_drop = np.where(better, drop, best_drop)
        target = (rr + dr) * cols + (cc + dc)
        receiver = np.where(better, target, receiver)

    flat_z = z.ravel()
    valid_idx = np.flatnonzero(~np.isnan(flat_z))
    order = valid_idx[np.argsort(flat_z[valid_idx])[::-1]]
    acc = np.where(np.isnan(flat_z), 0.0, 1.0)
    recv = receiver.ravel()
    for i in order:
        r = recv[i]
        if r >= 0:
            acc[r] += acc[i]
    return acc.reshape(z.shape)


def fill_depressions(dem: np.ndarray, eps: float = 1e-3) -> np.ndarray:
    """
    Priority-flood 填窪（Barnes et al. 2014）：從影像邊界與 nan 旁的像元
    往內淹，窪地填到出口高程再加 eps，保證每個像元都有往邊界流的路徑。
    30 m DEM 重採樣到 10 m 後窄谷底常有小窪地，不填的話 D8 累積會一路被
    截斷，河網斷成碎段。

    >>> z = np.array([[5., 5., 5.], [5., 1., 3.], [5., 5., 5.]])
    >>> f = fill_depressions(z)
    >>> bool(f[1, 1] > 3.0), float(f[1, 2])
    (True, 3.0)
    """
    import heapq
    z = np.asarray(dem, dtype="float64")
    rows, cols = z.shape
    filled = z.copy()
    nan = np.isnan(z)
    closed = nan.copy()
    seeds = np.zeros_like(nan)
    seeds[0, :] = seeds[-1, :] = True
    seeds[:, 0] = seeds[:, -1] = True
    if nan.any():
        seeds |= ndimage.binary_dilation(nan, EIGHT) & ~nan
    seeds &= ~nan
    heap = [(filled[r, c], r, c) for r, c in zip(*np.nonzero(seeds))]
    heapq.heapify(heap)
    closed |= seeds
    while heap:
        h, r, c = heapq.heappop(heap)
        for dr, dc in _D8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and not closed[nr, nc]:
                closed[nr, nc] = True
                if filled[nr, nc] <= h:
                    filled[nr, nc] = h + eps
                heapq.heappush(heap, (filled[nr, nc], nr, nc))
    return filled


def river_mask(pre_water: np.ndarray, dem: Optional[np.ndarray] = None,
               cell_size_m: Union[float, tuple] = 10.0,
               min_catchment_km2: float = 1.0,
               fill: bool = True) -> np.ndarray:
    """
    河道遮罩 = 事件前水體 ∪（有 DEM 時）集水面積 ≥ min_catchment_km2 的
    D8 河網。事件前影像上河道可能太窄、被陰影遮住而抓不到，DEM 河網補
    這個洞。

    >>> pre = np.zeros((1, 3), dtype=bool)
    >>> dem = np.array([[3.0, 2.0, 1.0]])
    >>> river_mask(pre, dem, cell_size_m=1000.0, min_catchment_km2=2.0).tolist()
    [[False, True, True]]
    """
    river = np.asarray(pre_water, dtype=bool).copy()
    if dem is not None:
        cell_km2 = _area_cell(cell_size_m) ** 2 / 1e6
        acc = flow_accumulation_d8(fill_depressions(dem) if fill else dem)
        river |= acc * cell_km2 >= min_catchment_km2
    return river


# 候選判定

@dataclass
class Candidate:
    """一塊疑似堰塞湖（新增水體連通塊）的判定結果。"""
    id: str
    grade: str                          # "A" / "B" / "C"
    area_m2: float
    centroid_row: float
    centroid_col: float
    on_river: bool
    landslide_nearby: bool
    dam_downstream: Optional[bool]      # 沒有 DEM 時為 None（無法判斷）
    persistent: bool
    n_later_scenes: int
    landslide_area_m2: float
    lake_floor_m: Optional[float] = None
    water_level_m: Optional[float] = None  # 事件前 DEM 上湖緣最高點，粗估水位
    centroid_xy: Optional[tuple] = None    # 有 transform 時：地圖座標 (x, y)
    reasons: list = field(default_factory=list)
    mask: Optional[np.ndarray] = field(default=None, repr=False)

    @property
    def area_hectare(self) -> float:
        return self.area_m2 / 1e4

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "grade": self.grade,
            "areaHectare": round(self.area_hectare, 3),
            "centroidRowCol": [round(self.centroid_row, 1), round(self.centroid_col, 1)],
            "centroidXY": list(self.centroid_xy) if self.centroid_xy else None,
            "onRiver": self.on_river,
            "landslideNearby": self.landslide_nearby,
            "damDownstream": self.dam_downstream,
            "persistent": self.persistent,
            "laterScenesChecked": self.n_later_scenes,
            "landslideAreaHectare": round(self.landslide_area_m2 / 1e4, 3),
            "lakeFloorM": None if self.lake_floor_m is None else round(self.lake_floor_m, 1),
            "waterLevelM": None if self.water_level_m is None else round(self.water_level_m, 1),
            "reasons": self.reasons,
        }


def _grade(on_river: bool, landslide_ok: bool, persistent: bool) -> Optional[str]:
    """
    >>> _grade(True, True, True), _grade(True, True, False), _grade(True, False, True), _grade(False, True, True)
    ('A', 'B', 'C', None)
    """
    if not on_river:
        return None
    if landslide_ok and persistent:
        return "A"
    if landslide_ok:
        return "B"
    return "C"


def _iou_with(comp: np.ndarray, other: np.ndarray) -> float:
    """comp 與 other 中「跟 comp 有重疊的連通塊」的 IoU。"""
    other = np.asarray(other, dtype=bool)
    if not (comp & other).any():
        return 0.0
    labeled, _ = ndimage.label(other, structure=EIGHT)
    hit = np.unique(labeled[comp & other])
    hit = hit[hit > 0]
    touched = np.isin(labeled, hit)
    inter = (comp & touched).sum()
    union = (comp | touched).sum()
    return float(inter) / float(union) if union else 0.0


def classify(new_water: np.ndarray, landslide: np.ndarray, river: np.ndarray,
             cell_size_m: Union[float, tuple],
             dem: Optional[np.ndarray] = None,
             later_new_water: Sequence[np.ndarray] = (),
             transform: Optional[tuple] = None,
             min_area_m2: float = 5000.0,
             merge_gap_px: int = 3,
             river_buffer_px: int = 2,
             search_radius_m: float = 500.0,
             dam_elev_tolerance_m: float = 5.0,
             persistence_iou: float = 0.3) -> list:
    """
    逐塊評分新增水體，回傳 Candidate 清單（依 A→B→C、面積大→小排序），
    不貼河道的塊不列入。

    分塊：原河道是事件前水體，change_detection 會把它扣掉，於是一座
    湖常被原河道切成左右兩半。這裡先把新增水體外擴 merge_gap_px 像元
    再做連通分析，相隔 ≤ 2×merge_gap_px 的碎塊視為同一座湖（面積仍只
    算新增水體像元，不含原河道）。

    >>> nw = np.zeros((20, 20), dtype=bool); nw[5:10, 8:12] = True    # 新增水體
    >>> river = np.zeros_like(nw); river[:, 10] = True; river[5:10, 10] = False
    >>> ls = np.zeros_like(nw); ls[11:13, 7:13] = True                 # 下游崩塌
    >>> [c.grade for c in classify(nw, ls, river, 10.0, min_area_m2=100)]
    ['B']
    >>> [c.grade for c in classify(nw, ls, river, 10.0, later_new_water=[nw], min_area_m2=100)]
    ['A']
    """
    new_water = np.asarray(new_water, dtype=bool)
    landslide = np.asarray(landslide, dtype=bool)
    river = np.asarray(river, dtype=bool)
    for name, arr in (("landslide", landslide), ("river", river)):
        if arr.shape != new_water.shape:
            raise ValueError(f"{name} 網格尺寸 {arr.shape} 與新增水體 {new_water.shape} 不一致")

    cell = _area_cell(cell_size_m)
    sampling = _sampling(cell_size_m)
    min_px = max(1, int(math.ceil(min_area_m2 / cell ** 2)))

    grouping = ndimage.binary_dilation(new_water, EIGHT, iterations=merge_gap_px)         if merge_gap_px > 0 else new_water
    groups, n = ndimage.label(grouping, structure=EIGHT)
    labeled = np.where(new_water, groups, 0)
    ls_labeled, _ = ndimage.label(landslide, structure=EIGHT)
    river_zone = ndimage.binary_dilation(river, structure=EIGHT, iterations=river_buffer_px) \
        if river_buffer_px > 0 else river

    candidates = []
    for lab in range(1, n + 1):
        comp = labeled == lab
        n_px = int(comp.sum())
        if n_px < min_px:
            continue

        on_river = bool((comp & river_zone).any() or (ndimage.binary_dilation(comp, EIGHT) & river).any())
        if not on_river:
            continue

        dist = ndimage.distance_transform_edt(~comp, sampling=sampling)
        near = landslide & (dist <= search_radius_m)
        landslide_nearby = bool(near.any())
        ls_ids = np.unique(ls_labeled[near])
        ls_ids = ls_ids[ls_ids > 0]
        ls_full = np.isin(ls_labeled, ls_ids)
        landslide_area = float(ls_full.sum()) * cell ** 2

        lake_floor = water_level = None
        dam_downstream: Optional[bool] = None
        if dem is not None:
            dem_arr = np.asarray(dem, dtype="float64")
            lake_vals = dem_arr[comp]
            if np.isfinite(lake_vals).any():
                lake_floor = float(np.nanmin(lake_vals))
                water_level = float(np.nanmax(lake_vals))
            if landslide_nearby and lake_floor is not None:
                ls_vals = dem_arr[ls_full]
                ls_low = float(np.nanmin(ls_vals)) if np.isfinite(ls_vals).any() else math.inf
                dam_downstream = ls_low <= lake_floor + dam_elev_tolerance_m
            elif lake_floor is not None:
                dam_downstream = False
        landslide_ok = landslide_nearby and dam_downstream is not False

        ious = [_iou_with(comp, m) for m in later_new_water]
        persistent = any(v >= persistence_iou for v in ious)

        grade = _grade(on_river, landslide_ok, persistent)
        if grade is None:
            continue

        ys, xs = np.nonzero(comp)
        cr, cc = float(ys.mean()), float(xs.mean())
        xy = None
        if transform is not None:
            a, b, c0, d, e, f0 = transform
            xy = (a * (cc + 0.5) + b * (cr + 0.5) + c0, d * (cc + 0.5) + e * (cr + 0.5) + f0)

        reasons = [f"新增水體 {n_px * cell ** 2 / 1e4:.2f} 公頃，緊貼事件前河道"]
        if landslide_nearby:
            reasons.append(f"{search_radius_m:.0f} m 內偵測到崩塌 {landslide_area / 1e4:.2f} 公頃（SAR 回波變化 ≥ 門檻）")
            if dam_downstream is True:
                reasons.append(f"崩塌延伸至湖底高程（{lake_floor:.0f} m）附近或以下，研判土石堵塞下游河道")
            elif dam_downstream is False:
                reasons.append("但鄰近崩塌全在湖面以上坡面，未到達河床，不視為壩體")
            else:
                reasons.append("未提供 DEM，無法確認崩塌是否位於湖的下游端")
        else:
            reasons.append(f"{search_radius_m:.0f} m 內未偵測到崩塌（可能位於雷達陰影／疊置區，建議光學或現地複核）")
        if later_new_water:
            best = max(ious) if ious else 0.0
            reasons.append(f"後續 {len(later_new_water)} 期影像同位置水體 IoU 最高 {best:.2f}"
                           + ("，持續蓄水" if persistent else "，未確認持續"))
        else:
            reasons.append("僅單期影像，尚未確認多時相持續性")

        candidates.append(Candidate(
            id="", grade=grade, area_m2=n_px * cell ** 2,
            centroid_row=cr, centroid_col=cc,
            on_river=on_river, landslide_nearby=landslide_nearby,
            dam_downstream=dam_downstream, persistent=persistent,
            n_later_scenes=len(later_new_water), landslide_area_m2=landslide_area,
            lake_floor_m=lake_floor, water_level_m=water_level,
            centroid_xy=xy, reasons=reasons, mask=comp,
        ))

    candidates.sort(key=lambda c: (c.grade, -c.area_m2))
    for i, c in enumerate(candidates, start=1):
        c.id = f"cand{i}"
    return candidates


# 一站式：事件前後 SAR →（新增水體、崩塌）→ 候選

def run_sar_chain(pre_db: np.ndarray, post_db: np.ndarray,
                  cell_size_m: Union[float, tuple],
                  dem: Optional[np.ndarray] = None,
                  later_post_dbs: Sequence[np.ndarray] = (),
                  transform: Optional[tuple] = None,
                  incidence_deg: float = S1_IW_MID_INCIDENCE_DEG,
                  look_azimuth_deg: float = S1_LOOK_AZIMUTH_DEG["ASCENDING"],
                  water_threshold_db: Optional[float] = None,
                  landslide_threshold_db: float = LANDSLIDE_THRESHOLD_DB,
                  landslide_min_pixels: int = 10,
                  water_filter_size: int = 3,
                  landslide_filter_size: int = 5,
                  water_edge_buffer_px: int = 2,
                  min_catchment_km2: float = 1.0,
                  dates: Sequence[Optional[str]] = (),
                  max_water_slope_deg: float = 20.0,
                  **classify_kwargs) -> dict:
    """
    pre_db / post_db / later_post_dbs：同軌道、同網格的 σ⁰（dB），未濾波。
    dem：事件前 DEM，同網格；沒有就跳過幾何遮罩、DEM 河網與壩體位置檢核。
    max_water_slope_deg：坡度超過此值的像元不判水（預設 20°）。陡峭窄谷配
    30 m DEM 時，谷底坡度會被山壁拉高，湖面可能整片被遮掉，可視情況放寬。

    回傳 dict：pre_water / post_water（WaterExtent）、new_water、
    landslides（LandslideResult）、river、invalid（遮罩 dict 或 None）、
    candidates（Candidate 清單）。
    """
    cell = _area_cell(cell_size_m)
    dates = list(dates) + [None] * (2 + len(later_post_dbs) - len(dates))

    invalid = None
    water_invalid = ls_invalid = None
    if dem is not None:
        invalid = sar_invalid_masks(dem, cell_size_m, incidence_deg, look_azimuth_deg,
                                    max_water_slope_deg=max_water_slope_deg)
        water_invalid, ls_invalid = invalid["water"], invalid["landslide"]

    # 水體與崩塌用不同濾波視窗：山區河道常只有 2–3 像元寬，5×5 Lee 會把
    # 河道邊緣像元拉高到門檻以上，事件前河道變細、事件後湖內原河道被
    # 當成新增水體；崩塌 3 dB 門檻則需要較強的 speckle 抑制。
    pre_w = lee_filter(pre_db, size=water_filter_size)
    post_w = lee_filter(post_db, size=water_filter_size)
    pre_f = lee_filter(pre_db, size=landslide_filter_size)
    post_f = lee_filter(post_db, size=landslide_filter_size)

    pre_water = extract_water_sar(pre_w, cell, threshold=water_threshold_db,
                                  invalid_mask=water_invalid, date=dates[0])
    post_water = extract_water_sar(post_w, cell, threshold=water_threshold_db,
                                   invalid_mask=water_invalid, date=dates[1])
    new_water = change_detection(pre_water, post_water)

    # 水體（含事件前河道）外擴幾像元一併排除：濾波後水陸交界像元的 σ⁰
    # 介於兩者之間，沒被判成水但回波掉了好幾 dB，不排除會沿湖岸冒出
    # 一圈假崩塌，進而誤判成「崩塌延伸到湖底」。
    water_any = pre_water.mask | post_water.mask
    if water_edge_buffer_px > 0:
        water_any = ndimage.binary_dilation(water_any, EIGHT, iterations=water_edge_buffer_px)
    landslides = detect_landslides(pre_f, post_f, cell, threshold_db=landslide_threshold_db,
                                   min_pixels=landslide_min_pixels, invalid_mask=ls_invalid,
                                   exclude_mask=water_any, date=dates[1])

    later_new = []
    for db, dt in zip(later_post_dbs, dates[2:]):
        ext = extract_water_sar(lee_filter(db, size=water_filter_size), cell,
                                threshold=water_threshold_db, invalid_mask=water_invalid, date=dt)
        later_new.append(change_detection(pre_water, ext))

    river = river_mask(pre_water.mask, dem, cell_size_m, min_catchment_km2)
    candidates = classify(new_water, landslides.mask, river, cell_size_m, dem=dem,
                          later_new_water=later_new, transform=transform, **classify_kwargs)
    return {
        "pre_water": pre_water,
        "post_water": post_water,
        "new_water": new_water,
        "later_new_water": later_new,
        "landslides": landslides,
        "river": river,
        "invalid": invalid,
        "candidates": candidates,
    }


# 合成場景（示範與測試共用）

LAND_DB, WATER_DB, SCAR_DB = -8.0, -22.0, -3.0


def synthetic_scene(with_landslide: bool = True, landslide_upslope_only: bool = False,
                    with_puddle: bool = True, n_later: int = 1,
                    speckle: bool = True, seed: int = 0) -> dict:
    """
    南北向山谷（列號往下＝往下游、河床每格降 1 m），寬 13 像元的谷底、
    兩側 ~39° 山壁，谷底中央 3 像元寬河道。另外：
    - 西北角一塊 60° 背向衛星陡坡（升軌 → 雷達陰影，σ⁰ 低得像水）
    - 西南角一塊平台（跟河道不相連），事件後出現積水（with_puddle）
    - 事件後：列 50–54 谷底崩塌堆積 + 東側山壁崩崖（with_landslide），
      上游列 25–49 谷底回淹成湖；landslide_upslope_only=True 則改成只在
      湖邊高處山坡有崩塌、沒堵到河床。
    cell 10 m。回傳 dict：dem、pre_db、post_db、later_dbs、truth（真值遮罩）。
    """
    rng = np.random.default_rng(seed)
    rows, cols, c = 80, 60, 30
    rr, cc = np.mgrid[0:rows, 0:cols]
    dc = np.abs(cc - c)
    dem = 600.0 - rr * 1.0 + np.where(dc <= 6, 0.3 * dc, 1.8 + 8.0 * (dc - 6))
    shadow_zone = (rr >= 3) & (rr < 15) & (cc >= 2) & (cc < 12)
    dem = np.where(shadow_zone, dem + (12 - cc) * 17.0, dem)       # 往東下降 ~60°
    terrace = (rr >= 60) & (rr < 76) & (cc < 9)
    dem = np.where(terrace, 700.0, dem)

    river = (dc <= 1)
    lake = (rr >= 25) & (rr < 50) & (dc <= 6)
    dam = (rr >= 50) & (rr < 55) & (dc <= 6)
    scar = (rr >= 44) & (rr < 58) & (cc >= c + 7) & (cc < c + 20)
    upslope_scar = (rr >= 30) & (rr < 40) & (cc >= c + 10) & (cc < c + 22)
    puddle = (rr >= 64) & (rr < 71) & (cc >= 1) & (cc < 7)

    pre = np.full((rows, cols), LAND_DB)
    pre[river] = WATER_DB
    pre[shadow_zone] = WATER_DB + 1.0       # 陰影：事件前後都很暗

    def post_scene():
        post = pre.copy()
        if with_landslide and not landslide_upslope_only:
            post[lake] = WATER_DB
            post[dam | scar] = SCAR_DB
        elif with_landslide and landslide_upslope_only:
            post[lake] = WATER_DB
            post[upslope_scar] = SCAR_DB
        else:
            post[lake] = WATER_DB
        if with_puddle:
            post[puddle] = WATER_DB
        return post

    def noisy(db):
        if not speckle:
            return db
        lin = 10 ** (db / 10)
        return 10 * np.log10(rng.gamma(4.4, lin / 4.4))

    post_clean = post_scene()
    truth_ls = np.zeros_like(river)
    if with_landslide:
        truth_ls = upslope_scar if landslide_upslope_only else (dam | scar)
    return {
        "dem": dem,
        "cell_size_m": 10.0,
        "pre_db": noisy(pre),
        "post_db": noisy(post_clean),
        "later_dbs": [noisy(post_clean) for _ in range(n_later)],
        "truth": {"river": river, "lake": lake, "landslide": truth_ls,
                  "puddle": puddle, "shadow_zone": shadow_zone},
    }


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"barrier_lake: {total - fails}/{total} 通過")

    scenarios = [
        ("完整：崩塌堵河 + 回淹 + 兩期持續", dict()),
        ("只有單期影像", dict(n_later=0)),
        ("有回淹、沒偵測到崩塌", dict(with_landslide=False)),
        ("崩塌只在湖面以上山坡", dict(landslide_upslope_only=True)),
    ]
    for title, kw in scenarios:
        s = synthetic_scene(**kw)
        out = run_sar_chain(s["pre_db"], s["post_db"], s["cell_size_m"], dem=s["dem"],
                            later_post_dbs=s["later_dbs"], min_catchment_km2=0.05)
        print(f"\n【{title}】 新增水體 {out['new_water'].sum()} 像元、"
              f"崩塌 {out['landslides'].mask.sum()} 像元")
        if not out["candidates"]:
            print("  （無候選）")
        for cand in out["candidates"]:
            print(f"  {cand.id} 等級 {cand.grade}｜{cand.area_hectare:.2f} 公頃｜"
                  + "；".join(cand.reasons))
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Сбалансированный отбор и нарезка негативов для wake-word датасета.

НОВОЕ В ЭТОЙ ВЕРСИИ:
- После расчёта плана (ШАГ 2/3) строится график "План негативов":
  1) Вклад категорий в часах (по плану)
  2) Сравнение: ЦЕЛЬ vs ПЛАН (в часах)
- График показывается ДО подтверждения нарезки, чтобы можно было сразу оценить перекос.
"""

import os
import csv
import json
import math
import random
import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import soundfile as sf
import librosa
from tqdm import tqdm

# --- график плана (matplotlib) ---
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


# =========================
# 0) ОСНОВНЫЕ НАСТРОЙКИ
# =========================

OUTPUT_SR = 16000          # приводим всё к 16k
SEGMENT_SEC = 2.0          # конечная нарезка в сегменты
SEGMENT_SAMPLES = int(round(OUTPUT_SR * SEGMENT_SEC))

# Сколько часов негативов нужно на выходе (после нарезки на 2 сек)
TARGET_NEG_HOURS = 17.0    # <-- поменяй под себя

# Общие (дефолтные) настройки "окон"
DEFAULT_WINDOWS_PER_FILE = 3
DEFAULT_MIN_WINDOW_SEC = 10.0

# Как сильно можно "шатать" позицию окна вокруг якоря
WINDOW_JITTER_FRACTION = 0.15   # 15% от длины окна
WINDOW_JITTER_MAX_SEC = 3.0     # но не больше 3 секунд

# Сколько файлов минимум оставить в каждой категории (чтобы категория не исчезла целиком)
MIN_KEEP_FILES_PER_CATEGORY = 1

# Куда писать нарезанные негативы
OUTPUT_ROOT = r"E:\LABS_VOLGU\WakeWord_Neiro\data\NEGATIVES_BALANCED"

# Какие форматы собирать как негативы
NEG_EXTS = (".wav", ".flac", ".ogg")   # (mp3 лучше заранее конвертировать)
RECURSIVE = True

# Мягкий шум для паддинга (если tail_policy="pad_noise")
LOW_NOISE_DIRS = [r"data\low_noise"]
LOW_NOISE_EXTS = (".wav", ".flac", ".ogg")
LOW_NOISE_RECURSIVE = True

# Сид для воспроизводимости (None => полностью случайно)
RANDOM_SEED = 1234

# Спрашивать подтверждение перед реальной нарезкой после расчёта плана
ASK_CONFIRMATION = True

# --- ГРАФИК ПЛАНА ---
SHOW_PLAN_PLOT = True      # показать окно matplotlib с планом перед нарезкой
SAVE_PLAN_PLOT = False     # сохранить png рядом (в OUTPUT_ROOT/_plan_plots)
PLAN_PLOT_DPI = 170
PLAN_PLOT_AXIS_LABEL_FONTSIZE = 16
PLAN_PLOT_VALUE_LABEL_FONTSIZE = 13
PLAN_PLOT_YTICK_FONTSIZE = 13

# ПРЕДУПРЕЖДЕНИЕ:
# Скрипт НЕ чистит OUTPUT_ROOT автоматически. Если ты запускаешь его повторно,
# в папках категорий могут накопиться старые .wav.
# Если хочешь чистить вручную — удали OUTPUT_ROOT/имя_категории перед запуском.


# =========================
# 1) ОПИСАНИЕ КАТЕГОРИЙ
# =========================

CATEGORIES = [
    {
        "name": "Бытовые",
        "dirs": [
            r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\BbItovie",
        ],
        "priority": True,
        "mode": "full",
        "sacrifice": False,
        "tail_policy": "pad_noise",
    },
    {
        "name": "Разное",
        "dirs": [
            r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\random",
        ],
        "priority": True,
        "mode": "full",
        "sacrifice": False,
        "tail_policy": "pad_noise",
    },
    {
        "name": "Музыка",
        "dirs": [
            r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\miusic_classical",
        ],
        "priority": False,
        "mode": "windowed",
        "sacrifice": True,
        "windows_per_file": 3,
        "min_window_sec": 14.0,
        "tail_policy": "drop",
    },
    {
        "name": "pdsounds\nнабор",
        "dirs": [
            r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\pdsounds_march2009",
        ],
        "priority": False,
        "mode": "windowed",
        "sacrifice": False,
        "windows_per_file": 3,
        "min_window_sec": 20.0,
        "tail_policy": "drop",
    },
    {
        "name": "youtube\nподкасты",
        "dirs": [
            r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\Random_YT_muz",
        ],
        "priority": True,
        "mode": "full",
        "sacrifice": False,
        "tail_policy": "pad_noise",
    },
]


# =========================
# 2) META / I/O ВСПОМОГАТЕЛЬНОЕ
# =========================

@dataclass(frozen=True)
class AudioMeta:
    path: str
    sr: int
    frames: int
    channels: int
    duration_sec: float
    mtime: float
    size: int


def _stat_stamp(path: str) -> Tuple[float, int]:
    st = os.stat(path)
    return float(st.st_mtime), int(st.st_size)


def _safe_name(s: str, max_len: int = 80) -> str:
    out = []
    for ch in str(s):
        if ch.isalnum() or ch in ("_", "-", "."):
            out.append(ch)
        else:
            out.append("_")
    res = "".join(out).strip("_")
    return (res or "item")[:max_len]


def collect_files(dirs: List[str], exts: Tuple[str, ...], recursive: bool = True) -> List[str]:
    exts_l = tuple(e.lower() for e in exts)
    out: List[str] = []
    for root in dirs:
        if not root:
            continue
        if not os.path.isdir(root):
            print(f"[ПРЕДУПРЕЖДЕНИЕ] Папка не найдена: {root}")
            continue
        if recursive:
            for dp, _, fns in os.walk(root):
                for fn in fns:
                    if os.path.splitext(fn)[1].lower() in exts_l:
                        out.append(os.path.join(dp, fn))
        else:
            for fn in os.listdir(root):
                p = os.path.join(root, fn)
                if os.path.isfile(p) and os.path.splitext(fn)[1].lower() in exts_l:
                    out.append(p)
    return sorted(set(out))


def load_or_build_meta(files: List[str], cache_path: str) -> List[AudioMeta]:
    cached: Dict[str, Dict] = {}
    if os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
        except Exception:
            cached = {}

    metas: List[AudioMeta] = []
    updated: Dict[str, Dict] = {}

    for path in tqdm(files, desc="META", leave=False):
        try:
            mtime, size = _stat_stamp(path)
            key = path.replace("\\", "/")
            rec = cached.get(key)

            if rec and rec.get("mtime") == mtime and rec.get("size") == size:
                sr = int(rec["sr"])
                frames = int(rec["frames"])
                ch = int(rec.get("channels", 1))
            else:
                info = sf.info(path)
                sr = int(info.samplerate)
                frames = int(info.frames)
                ch = int(info.channels)

            dur = float(frames) / float(sr) if sr > 0 else 0.0
            meta = AudioMeta(path=path, sr=sr, frames=frames, channels=ch, duration_sec=dur, mtime=mtime, size=size)
            metas.append(meta)

            updated[key] = {"sr": sr, "frames": frames, "channels": ch, "mtime": mtime, "size": size}

        except Exception:
            continue

    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(updated, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    metas = [m for m in metas if m.sr > 0 and m.frames > 0 and m.duration_sec > 0.0]
    return metas


def _ceil_to_segments(sec: float) -> float:
    n = int(math.ceil(sec / SEGMENT_SEC))
    return float(n) * SEGMENT_SEC


def _floor_to_segments(sec: float) -> float:
    n = int(math.floor(sec / SEGMENT_SEC))
    return float(n) * SEGMENT_SEC


# =========================
# 3) LOW-NOISE (паддинг хвостов)
# =========================

class LowNoisePool:
    def __init__(self, metas: List[AudioMeta]):
        self.metas = metas
        if not metas:
            raise RuntimeError("LowNoisePool: пустой список")

        weights = [max(1, int(m.frames)) for m in metas]
        self._cum = np.cumsum(weights).astype(np.int64)
        self._total = int(self._cum[-1])

    def pick(self) -> AudioMeta:
        r = random.randint(1, self._total)
        idx = int(np.searchsorted(self._cum, r, side="left"))
        return self.metas[idx]


def read_segment(meta: AudioMeta, start_sec: float, dur_sec: float, target_sr: int = OUTPUT_SR) -> np.ndarray:
    start_sec = max(0.0, float(start_sec))
    dur_sec = max(0.0, float(dur_sec))
    if dur_sec <= 0:
        return np.zeros(0, dtype=np.float32)

    file_sr = int(meta.sr)
    start_frame = int(round(start_sec * file_sr))
    frames_to_read = int(round(dur_sec * file_sr))
    frames_to_read = max(1, frames_to_read)

    try:
        with sf.SoundFile(meta.path) as f:
            start_frame = max(0, min(start_frame, meta.frames))
            f.seek(start_frame)
            audio = f.read(frames_to_read, dtype="float32", always_2d=True)
    except Exception:
        y, sr = librosa.load(meta.path, sr=None, mono=True)
        if sr is None or sr <= 0:
            return np.zeros(0, dtype=np.float32)
        s = int(round(start_sec * sr))
        e = int(round((start_sec + dur_sec) * sr))
        y = y[max(0, s):max(0, e)].astype(np.float32)
        if sr != target_sr and len(y) > 0:
            y = librosa.resample(y, orig_sr=sr, target_sr=target_sr).astype(np.float32)
        return np.nan_to_num(y)

    if audio.size == 0:
        return np.zeros(0, dtype=np.float32)

    audio = np.mean(audio, axis=1).astype(np.float32)

    if file_sr != target_sr and len(audio) > 0:
        audio = librosa.resample(audio, orig_sr=file_sr, target_sr=target_sr).astype(np.float32)

    return np.nan_to_num(audio)


def make_low_noise(pool: LowNoisePool, length_samples: int) -> np.ndarray:
    meta = pool.pick()
    dur_sec = float(length_samples) / float(OUTPUT_SR)
    max_start = max(0.0, meta.duration_sec - dur_sec)
    start = random.uniform(0.0, max_start) if max_start > 0 else 0.0
    y = read_segment(meta, start, dur_sec, target_sr=OUTPUT_SR)

    if len(y) < length_samples:
        if len(y) == 0:
            return np.zeros(length_samples, dtype=np.float32)
        reps = int(math.ceil(length_samples / len(y)))
        y = np.tile(y, reps)[:length_samples]
    else:
        y = y[:length_samples]

    mx = float(np.max(np.abs(y)) + 1e-8)
    if mx > 1.0:
        y = y / mx
    return y.astype(np.float32)


# =========================
# 4) ОКНА: где вырезать
# =========================

def pick_window_starts(file_dur: float, window_sec: float, windows_per_file: int) -> List[float]:
    file_dur = float(file_dur)
    window_sec = float(window_sec)
    k = int(windows_per_file)

    if k <= 0 or window_sec <= 0 or file_dur <= 0:
        return []

    if file_dur <= window_sec:
        return [0.0]

    max_start = file_dur - window_sec
    if max_start <= 0:
        return [0.0]

    starts: List[float] = []
    for i in range(k):
        center = ((i + 0.5) / k) * file_dur
        s = center - window_sec / 2.0
        s = max(0.0, min(s, max_start))

        jitter = min(window_sec * WINDOW_JITTER_FRACTION, WINDOW_JITTER_MAX_SEC, max_start)
        if jitter > 0:
            s = s + random.uniform(-jitter, jitter)
            s = max(0.0, min(s, max_start))

        starts.append(float(s))

    return starts


# =========================
# 5) ПЛАНИРОВАНИЕ ОБЪЁМА (под TARGET_NEG_HOURS)
# =========================

def category_min_nseg(cat: Dict) -> int:
    min_sec = float(cat.get("min_window_sec", DEFAULT_MIN_WINDOW_SEC))
    min_sec = max(min_sec, SEGMENT_SEC)
    return int(math.ceil(min_sec / SEGMENT_SEC))


def category_windows_per_file(cat: Dict) -> int:
    return int(cat.get("windows_per_file", DEFAULT_WINDOWS_PER_FILE))


def file_contribution_seconds(meta: AudioMeta, cat: Dict, base_window_nseg: int) -> float:
    mode = cat.get("mode", "windowed")
    tail_policy = cat.get("tail_policy", "drop")

    if tail_policy == "pad_noise":
        full_sec = _ceil_to_segments(meta.duration_sec)
    else:
        full_sec = _floor_to_segments(meta.duration_sec)

    if full_sec < SEGMENT_SEC:
        return 0.0

    if mode == "full":
        return full_sec

    k = max(1, category_windows_per_file(cat))
    min_nseg = category_min_nseg(cat)
    nseg = max(int(base_window_nseg), int(min_nseg))
    win_sec = float(nseg) * SEGMENT_SEC

    if meta.duration_sec <= win_sec * k:
        return full_sec

    return float(k) * win_sec


def total_duration_seconds(all_metas_by_cat: Dict[str, List[AudioMeta]], cats_by_name: Dict[str, Dict], base_window_nseg: int) -> float:
    tot = 0.0
    for cname, metas in all_metas_by_cat.items():
        cat = cats_by_name[cname]
        for m in metas:
            tot += file_contribution_seconds(m, cat, base_window_nseg)
    return tot


def choose_base_window_nseg(all_metas_by_cat: Dict[str, List[AudioMeta]], cats_by_name: Dict[str, Dict], target_sec: float) -> int:
    base_min = int(math.ceil(max(DEFAULT_MIN_WINDOW_SEC, SEGMENT_SEC) / SEGMENT_SEC))
    base_max = int(math.ceil(600.0 / SEGMENT_SEC))

    tot_min = total_duration_seconds(all_metas_by_cat, cats_by_name, base_min)
    if target_sec >= tot_min:
        lo, hi = base_min, base_min
        tot_hi = tot_min
        while hi < base_max and tot_hi < target_sec:
            hi = min(base_max, hi * 2)
            tot_hi = total_duration_seconds(all_metas_by_cat, cats_by_name, hi)
            if tot_hi == total_duration_seconds(all_metas_by_cat, cats_by_name, hi + 1):
                break

        if tot_hi <= target_sec:
            return hi

        lo, hi = base_min, hi
        best = base_min
        while lo <= hi:
            mid = (lo + hi) // 2
            t = total_duration_seconds(all_metas_by_cat, cats_by_name, mid)
            if t <= target_sec:
                best = mid
                lo = mid + 1
            else:
                hi = mid - 1
        return int(best)

    return int(base_min)


# =========================
# 6) ОТБОР ФАЙЛОВ, ЕСЛИ МАЛО TARGET
# =========================

def downsample_files_if_needed(
    all_metas_by_cat: Dict[str, List[AudioMeta]],
    cats_by_name: Dict[str, Dict],
    base_window_nseg: int,
    target_sec: float,
) -> Tuple[Dict[str, List[AudioMeta]], List[str]]:
    warnings: List[str] = []

    contrib: Dict[str, List[Tuple[AudioMeta, float]]] = {}
    for cname, metas in all_metas_by_cat.items():
        cat = cats_by_name[cname]
        rows = []
        for m in metas:
            c = file_contribution_seconds(m, cat, base_window_nseg)
            if c > 0:
                rows.append((m, c))
        contrib[cname] = rows

    def current_total() -> float:
        s = 0.0
        for rows in contrib.values():
            for _, c in rows:
                s += c
        return s

    total = current_total()
    if total <= target_sec:
        new_map = {c: [m for m, _ in rows] for c, rows in contrib.items()}
        return new_map, warnings

    need_remove = total - target_sec

    sacrifice_cats = [c for c in contrib.keys() if cats_by_name[c].get("sacrifice", False)]
    normal_cats = [c for c in contrib.keys() if (c not in sacrifice_cats and not cats_by_name[c].get("priority", False))]
    priority_cats = [c for c in contrib.keys() if cats_by_name[c].get("priority", False)]

    def drop_from_categories(cat_names: List[str], allow_empty_category: bool = False) -> float:
        nonlocal need_remove
        removed = 0.0
        for cname in cat_names:
            rows = contrib.get(cname, [])
            if not rows:
                continue

            keep_min = 0 if allow_empty_category else int(MIN_KEEP_FILES_PER_CATEGORY)
            keep_min = max(0, keep_min)

            random.shuffle(rows)
            rows.sort(key=lambda t: t[1], reverse=True)

            while need_remove > 0 and len(rows) > keep_min:
                _m, c = rows.pop(0)
                removed += c
                need_remove -= c

            contrib[cname] = rows

            if need_remove <= 0:
                break
        return removed

    _ = drop_from_categories(sacrifice_cats, allow_empty_category=False)
    if need_remove > 0:
        _ = drop_from_categories(normal_cats, allow_empty_category=False)

    if need_remove > 0:
        warnings.append(
            "ВНИМАНИЕ: цель слишком маленькая даже после удаления sacrifice+обычных категорий. "
            "Приходится удалять файлы из PRIORITY категорий."
        )
        _ = drop_from_categories(priority_cats, allow_empty_category=True)

    if need_remove > 0:
        warnings.append(f"ВНИМАНИЕ: всё ещё выше цели на {need_remove/3600:.2f} ч (больше нечего удалять).")

    new_map = {c: [m for m, _ in rows] for c, rows in contrib.items()}
    return new_map, warnings


# =========================
# 6.5) ГРАФИК ПЛАНА (как в статистике)
# =========================

def _seconds_to_hours(sec: float) -> float:
    return float(sec) / 3600.0


def _sort_dict_by_value_desc(d: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(d.items(), key=lambda kv: kv[1], reverse=True)


def _annotate_bars(ax, bars, values, fmt: str = "{:.2f}"):
    ylim = ax.get_ylim()
    y_span = max(1e-9, float(ylim[1] - ylim[0]))
    pad = 0.01 * y_span
    for rect, v in zip(bars, values):
        h = float(rect.get_height())
        ax.text(
            rect.get_x() + rect.get_width() / 2.0,
            h + pad,
            fmt.format(v),
            ha="center",
            va="bottom",
            fontsize=PLAN_PLOT_VALUE_LABEL_FONTSIZE,
        )


def _plot_category_bars(ax, hours_by_cat: Dict[str, float], title: str, color: str):
    if not hours_by_cat:
        ax.set_title(title)
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return

    items = _sort_dict_by_value_desc(hours_by_cat)
    labels = [k for k, _ in items]
    values = [v for _, v in items]

    bars = ax.bar(labels, values, color=color)
    ax.set_title(title)
    ax.set_ylabel("Часы", fontsize=PLAN_PLOT_AXIS_LABEL_FONTSIZE)
    ax.tick_params(axis="x", labelrotation=45)
    ax.tick_params(axis="y", labelsize=PLAN_PLOT_YTICK_FONTSIZE)
    for tick in ax.get_xticklabels():
        tick.set_ha("right")

    max_v = max(values) if values else 0.0
    ax.set_ylim(0.0, max_v * 1.12 + 1e-9)
    _annotate_bars(ax, bars, values, fmt="{:.3f} ч")


def plot_negatives_plan(
    hours_by_cat: Dict[str, float],
    target_hours: float,
    planned_hours: float,
    save_png: bool,
    output_root: str,
):
    if plt is None:
        print("[ПРЕДУПРЕЖДЕНИЕ] matplotlib не доступен — график плана построить не удалось.")
        return None

    n_cats = max(1, len(hours_by_cat))
    fig_h = max(8.0, min(16.0, 6.0 + n_cats * 0.18))
    fig_w = max(12.0, min(24.0, 10.0 + n_cats * 0.20))

    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_h))
    ax_cat, ax_tot = axes

    _plot_category_bars(ax_cat, hours_by_cat, "План негативов: вклад категорий (часы)", color="tab:orange")

    bars = ax_tot.bar(
        ["Цель", "План"],
        [target_hours, planned_hours],
        color=["tab:gray", "tab:orange"],
    )
    diff = planned_hours - target_hours
    ax_tot.set_title(f"Цель vs План (Δ={diff:+.3f} ч)")
    ax_tot.set_ylabel("Часы", fontsize=PLAN_PLOT_AXIS_LABEL_FONTSIZE)
    ax_tot.tick_params(axis="y", labelsize=PLAN_PLOT_YTICK_FONTSIZE)
    max_v = max(target_hours, planned_hours, 0.0)
    ax_tot.set_ylim(0.0, max_v * 1.15 + 1e-9)
    _annotate_bars(ax_tot, bars, [target_hours, planned_hours], fmt="{:.3f} ч")

    fig.tight_layout()

    if save_png:
        try:
            out_dir = os.path.join(output_root, "_plan_plots")
            os.makedirs(out_dir, exist_ok=True)
            out_png = os.path.join(out_dir, "negatives_plan.png")
            fig.savefig(out_png, dpi=int(PLAN_PLOT_DPI))
            print(f"[ГРАФИК] PNG сохранён: {out_png}")
        except Exception as e:
            print("[ПРЕДУПРЕЖДЕНИЕ] Не удалось сохранить PNG графика плана:", e)

    return fig


# =========================
# 7) РЕАЛЬНАЯ НАРЕЗКА И СОХРАНЕНИЕ
# =========================

def split_and_write(
    y: np.ndarray,
    out_dir: str,
    base_stem: str,
    tail_policy: str,
    low_noise_pool: Optional[LowNoisePool],
) -> int:
    os.makedirs(out_dir, exist_ok=True)

    if y is None or len(y) < 1:
        return 0

    total = len(y)
    n_full = total // SEGMENT_SAMPLES
    written = 0

    for i in range(n_full):
        seg = y[i * SEGMENT_SAMPLES:(i + 1) * SEGMENT_SAMPLES]
        out_path = os.path.join(out_dir, f"{base_stem}__seg{i:04d}.wav")
        sf.write(out_path, seg.astype(np.float32), OUTPUT_SR)
        written += 1

    rem = total - n_full * SEGMENT_SAMPLES
    if rem > 0 and tail_policy == "pad_noise":
        seg = y[n_full * SEGMENT_SAMPLES:]
        if low_noise_pool is None:
            pad = np.zeros(SEGMENT_SAMPLES - rem, dtype=np.float32)
        else:
            pad = make_low_noise(low_noise_pool, SEGMENT_SAMPLES - rem)
        seg = np.concatenate([seg, pad]).astype(np.float32)
        out_path = os.path.join(out_dir, f"{base_stem}__seg{n_full:04d}.wav")
        sf.write(out_path, seg, OUTPUT_SR)
        written += 1

    return written


def process_file(
    meta: AudioMeta,
    cat: Dict,
    base_window_nseg: int,
    out_cat_dir: str,
    low_noise_pool: Optional[LowNoisePool],
    details_rows: List[Dict],
) -> int:
    mode = cat.get("mode", "windowed")
    tail_policy = cat.get("tail_policy", "drop")

    k = max(1, category_windows_per_file(cat))
    min_nseg = category_min_nseg(cat)
    nseg = max(int(base_window_nseg), int(min_nseg))
    win_sec = float(nseg) * SEGMENT_SEC

    base = os.path.splitext(os.path.basename(meta.path))[0]
    base = _safe_name(base)

    total_written = 0

    def handle_chunk(start_sec: float, dur_sec: float, chunk_tag: str):
        nonlocal total_written
        y = read_segment(meta, start_sec, dur_sec, target_sr=OUTPUT_SR)

        if len(y) > 0:
            y = y - float(np.mean(y))

        stem = f"{base}__{chunk_tag}"
        written = split_and_write(y, out_cat_dir, stem, tail_policy, low_noise_pool)

        details_rows.append({
            "category": cat.get("name", ""),
            "file": meta.path,
            "file_dur_sec": f"{meta.duration_sec:.3f}",
            "chunk_tag": chunk_tag,
            "chunk_start_sec": f"{start_sec:.3f}",
            "chunk_dur_sec": f"{dur_sec:.3f}",
            "segments_written": int(written),
            "tail_policy": tail_policy,
            "mode": mode,
        })
        total_written += written

    if mode == "full":
        handle_chunk(0.0, meta.duration_sec, "FULL")
        return total_written

    if meta.duration_sec <= win_sec * k:
        handle_chunk(0.0, meta.duration_sec, "SHORT_FULL")
        return total_written

    starts = pick_window_starts(meta.duration_sec, win_sec, k)
    for wi, s in enumerate(starts):
        handle_chunk(s, win_sec, f"W{wi:02d}")

    return total_written


# =========================
# 8) MAIN
# =========================

def _fmt_hours(sec: float) -> str:
    return f"{sec/3600.0:.2f} ч"


def _ask_yes_no(prompt: str) -> bool:
    while True:
        ans = input(prompt).strip().lower()
        if ans in ("y", "yes", "д", "да"):
            return True
        if ans in ("n", "no", "н", "нет"):
            return False
        print("Введите 'y' (да) или 'n' (нет).")


def main():
    if RANDOM_SEED is not None:
        random.seed(int(RANDOM_SEED))
        np.random.seed(int(RANDOM_SEED))

    os.makedirs(OUTPUT_ROOT, exist_ok=True)

    print("==============================================")
    print("Скрипт: Сбалансированная нарезка негативов")
    print("==============================================")
    print(f"Папка вывода: {OUTPUT_ROOT}")
    print(f"Цель по негативам: {TARGET_NEG_HOURS:.2f} ч (после нарезки на {SEGMENT_SEC:.1f} сек)")
    print(f"Форматы: {', '.join(NEG_EXTS)} | рекурсивно: {RECURSIVE}")
    print("")

    # --- low-noise pool ---
    low_noise_pool = None
    try:
        low_files = collect_files(LOW_NOISE_DIRS, LOW_NOISE_EXTS, recursive=LOW_NOISE_RECURSIVE)
        if low_files:
            cache_dir = os.path.join(OUTPUT_ROOT, "_cache_meta")
            low_meta = load_or_build_meta(low_files, os.path.join(cache_dir, "low_noise_meta.json"))
            if low_meta:
                low_noise_pool = LowNoisePool(low_meta)
                print(f"[LOW_NOISE] Пул готов: {len(low_meta)} файлов (для pad_noise)")
            else:
                print("[LOW_NOISE] Мета пустая (все файлы битые?) -> pad_noise будет паддить НУЛЯМИ")
        else:
            print("[LOW_NOISE] Файлы low-noise не найдены -> pad_noise будет паддить НУЛЯМИ")
    except Exception as e:
        print("[LOW_NOISE] Ошибка подготовки low-noise:", e)

    # --- меты по категориям ---
    cache_dir = os.path.join(OUTPUT_ROOT, "_cache_meta")
    os.makedirs(cache_dir, exist_ok=True)

    all_metas_by_cat: Dict[str, List[AudioMeta]] = {}
    cats_by_name: Dict[str, Dict] = {}

    active_cats = []
    for cat in CATEGORIES:
        name = cat.get("name") or "category"
        dirs = [d for d in cat.get("dirs", []) if d]
        if not dirs:
            continue
        cat = dict(cat)
        cat["name"] = name
        cat["dirs"] = dirs
        active_cats.append(cat)

    if not active_cats:
        print("Не настроены категории (CATEGORIES). Заполни поле 'dirs' хотя бы у одной категории.")
        return

    print(f"Категорий активных: {len(active_cats)}")
    for cat in active_cats:
        print(
            f" - {cat['name']} | mode={cat.get('mode','windowed')} | "
            f"priority={bool(cat.get('priority',False))} | sacrifice={bool(cat.get('sacrifice',False))} | "
            f"tail={cat.get('tail_policy','drop')}"
        )

    print("\n[ШАГ 1/3] Сканирование файлов и построение метаданных (может занять время)...")
    for cat in active_cats:
        cname = cat["name"]
        cats_by_name[cname] = cat

        files = collect_files(cat["dirs"], NEG_EXTS, recursive=RECURSIVE)
        if not files:
            print(f"[ПРЕДУПРЕЖДЕНИЕ] Категория '{cname}' содержит 0 файлов и будет пропущена.")
            all_metas_by_cat[cname] = []
            continue

        h = hashlib.md5(("|".join(cat["dirs"]) + cname).encode("utf-8")).hexdigest()[:8]
        cache_path = os.path.join(cache_dir, f"meta_{_safe_name(cname)}__{h}.json")

        metas = load_or_build_meta(files, cache_path)
        all_metas_by_cat[cname] = metas
        print(f"[META] {cname}: файлов={len(files)} | meta_ok={len(metas)}")

    all_metas_by_cat = {c: ms for c, ms in all_metas_by_cat.items() if ms}
    if not all_metas_by_cat:
        print("Не найдено ни одного валидного аудиофайла в категориях.")
        return

    target_sec = float(TARGET_NEG_HOURS) * 3600.0

    print("\n[ШАГ 2/3] Расчёт плана (сколько и как резать)...")

    base_window_nseg = choose_base_window_nseg(all_metas_by_cat, cats_by_name, target_sec)
    base_window_sec = float(base_window_nseg) * SEGMENT_SEC

    tot_now = total_duration_seconds(all_metas_by_cat, cats_by_name, base_window_nseg)

    print("\n=== ПЛАН ===")
    print(f"Цель: {TARGET_NEG_HOURS:.2f} ч ({target_sec:.0f} сек)")
    print(f"Базовое окно: {base_window_sec:.1f} сек (nseg={base_window_nseg}, сегмент={SEGMENT_SEC:.1f}с)")
    print(f"Итого по плану ДО урезания файлами: {_fmt_hours(tot_now)}")

    selected_metas_by_cat, warnings = downsample_files_if_needed(
        all_metas_by_cat, cats_by_name, base_window_nseg, target_sec
    )

    tot_sel = total_duration_seconds(selected_metas_by_cat, cats_by_name, base_window_nseg)
    print(f"Итого по плану ПОСЛЕ урезания файлами: {_fmt_hours(tot_sel)}")
    if warnings:
        print("\n" + "\n".join([f"!!! {w}" for w in warnings]) + "\n")

    # --- СВОДКА ПО КАТЕГОРИЯМ (в часах) + ГРАФИК ПЛАНА ---
    planned_hours_by_cat: Dict[str, float] = {}
    print("\nПлан по категориям (после урезания файлами):")
    for cname, metas in selected_metas_by_cat.items():
        cat = cats_by_name[cname]
        sec = sum(file_contribution_seconds(m, cat, base_window_nseg) for m in metas)
        h = _seconds_to_hours(sec)
        planned_hours_by_cat[cname] = h
        print(f" - {cname}: {h:.3f} ч | файлов: {len(metas)} | mode={cat.get('mode','windowed')} | tail={cat.get('tail_policy','drop')}")

    planned_total_h = _seconds_to_hours(tot_sel)

    # --- график ДО подтверждения ---
    fig_plan = None
    if (SHOW_PLAN_PLOT or SAVE_PLAN_PLOT) and (plt is not None):
        fig_plan = plot_negatives_plan(
            hours_by_cat=planned_hours_by_cat,
            target_hours=float(TARGET_NEG_HOURS),
            planned_hours=float(planned_total_h),
            save_png=bool(SAVE_PLAN_PLOT),
            output_root=str(OUTPUT_ROOT),
        )

        if SHOW_PLAN_PLOT:
            print("\n[ГРАФИК] Открылся график плана. Закрой окно графика, чтобы продолжить.")
            plt.show()  # блокирует до закрытия окна

    # --- предупреждение, если output не пустой (игнорируем служебные папки) ---
    IGNORE_IN_OUTPUT = {"_cache_meta", "_plan_plots"}

    try:
        dirty = False
        if os.path.isdir(OUTPUT_ROOT):
            for e in os.scandir(OUTPUT_ROOT):
                if e.name in IGNORE_IN_OUTPUT:
                    continue
                dirty = True
                break

        if dirty:
            print("[ПРЕДУПРЕЖДЕНИЕ] Папка вывода не пустая. Скрипт не удаляет старые файлы автоматически.")
            print(f"Если запускаешь повторно и хочешь чистый результат — удали вручную папки категорий в OUTPUT_ROOT = {OUTPUT_ROOT}")
    except Exception:
        pass

    # --- подтверждение ---
    if ASK_CONFIRMATION:
        ok = _ask_yes_no("\nПродолжить и начать нарезку/запись файлов? (y/n): ")
        if not ok:
            print("Операция отменена пользователем.")
            return

    print("\n[ШАГ 3/3] Нарезка и сохранение...")

    summary = {
        "target_hours": TARGET_NEG_HOURS,
        "segment_sec": SEGMENT_SEC,
        "base_window_sec": base_window_sec,
        "base_window_nseg": base_window_nseg,
        "total_hours_planned": tot_sel / 3600.0,
        "defaults": {
            "windows_per_file": DEFAULT_WINDOWS_PER_FILE,
            "min_window_sec": DEFAULT_MIN_WINDOW_SEC,
        },
        "categories": [],
        "warnings": warnings,
        "planned_hours_by_category": planned_hours_by_cat,
    }

    details_rows: List[Dict] = []

    total_written_segments = 0
    for cname, metas in selected_metas_by_cat.items():
        cat = cats_by_name[cname]
        out_cat_dir = os.path.join(OUTPUT_ROOT, _safe_name(cname))

        cat_tot_sec = sum(file_contribution_seconds(m, cat, base_window_nseg) for m in metas)
        summary["categories"].append({
            "name": cname,
            "files_selected": len(metas),
            "planned_hours": cat_tot_sec / 3600.0,
            "mode": cat.get("mode", "windowed"),
            "priority": bool(cat.get("priority", False)),
            "sacrifice": bool(cat.get("sacrifice", False)),
            "windows_per_file": category_windows_per_file(cat),
            "min_window_sec": float(cat.get("min_window_sec", DEFAULT_MIN_WINDOW_SEC)),
            "tail_policy": cat.get("tail_policy", "drop"),
        })

        print(f"\n--- КАТЕГОРИЯ: {cname} | файлов: {len(metas)} | план: {_fmt_hours(cat_tot_sec)}")
        for m in tqdm(metas, desc=cname, leave=False):
            total_written_segments += process_file(
                m, cat, base_window_nseg, out_cat_dir, low_noise_pool, details_rows
            )

    os.makedirs(OUTPUT_ROOT, exist_ok=True)
    with open(os.path.join(OUTPUT_ROOT, "selection_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    csv_path = os.path.join(OUTPUT_ROOT, "selection_details.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "category", "file", "file_dur_sec",
            "chunk_tag", "chunk_start_sec", "chunk_dur_sec",
            "segments_written", "tail_policy", "mode",
        ]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in details_rows:
            w.writerow(row)

    print("\n=== ГОТОВО ===")
    print(f"Папка вывода: {OUTPUT_ROOT}")
    print(f"Записано сегментов: {total_written_segments}  (~{(total_written_segments*SEGMENT_SEC)/3600.0:.2f} ч)")
    print("Отчёты: selection_summary.json, selection_details.csv")


if __name__ == "__main__":
    main()

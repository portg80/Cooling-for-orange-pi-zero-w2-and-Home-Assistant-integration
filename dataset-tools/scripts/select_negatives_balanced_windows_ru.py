#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Сбалансированный отбор и нарезка негативов для wake-word датасета.

Задача
------
Негативы очень разнородные и сильно неравномерные по длительности.
Если "отбрасывать треки целиком", то некоторые типы звуков могут полностью исчезнуть.
Этот скрипт делает наоборот:

1) Негативы задаются списком КАТЕГОРИЙ (обычно это папки).
2) По умолчанию из каждого файла берётся N "окон" (windows_per_file) длиной W секунд,
   где W подбирается под желаемое общее время и не опускается ниже min_window_sec.
   Окна берутся равномерно по треку + случайный jitter.
3) Каждое окно режется на фиксированные сегменты segment_sec (по умолчанию 2 сек).
   Хвост < segment_sec:
     - обычно отбрасывается (tail_policy="drop"),
     - но для важных категорий можно включить tail_policy="pad_noise" (паддинг мягким шумом, НЕ нулями),
       чтобы не терять последние 0.5–1.9 сек (особенно важно для речи).
4) Важные категории (priority=True) можно брать целиком (mode="full").
5) Если при минимальном окне всё равно получается слишком много часов, скрипт начинает
   "урезать" выборку (выкидывать файлы), начиная с sacrifice=True категорий.
   Если дошло до priority — печатает заметное предупреждение.
6) Пишет подробный отчёт:
   - selection_summary.json
   - selection_details.csv

Зависимости
-----------
pip install numpy soundfile librosa tqdm

Заметки по форматам
------------------
- Для скорости используется sf.info() (читает только заголовок) и sf.SoundFile.seek(),
  поэтому лучше wav/flac/ogg.
- mp3 может обработаться через librosa (fallback), но это часто медленнее и может грузить файл целиком.
- Мягкий шум для паддинга хвостов берётся из LOW_NOISE_DIRS (короткие wav/flac/ogg).
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


# =========================
# 0) ОСНОВНЫЕ НАСТРОЙКИ
# =========================

OUTPUT_SR = 16000          # приводим всё к 16k
SEGMENT_SEC = 2.0          # конечная нарезка в сегменты
SEGMENT_SAMPLES = int(round(OUTPUT_SR * SEGMENT_SEC))

# Сколько часов негативов нужно на выходе (после нарезки на 2 сек)
TARGET_NEG_HOURS = 27.0    # <-- поменяй под себя

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

# ПРЕДУПРЕЖДЕНИЕ:
# Скрипт НЕ чистит OUTPUT_ROOT автоматически. Если ты запускаешь его повторно,
# в папках категорий могут накопиться старые .wav.
# Если хочешь чистить вручную — удали OUTPUT_ROOT/имя_категории перед запуском.


# =========================
# 1) ОПИСАНИЕ КАТЕГОРИЙ
# =========================
# Категория = один "тип" негативов. Обычно это одна или несколько папок.
#
# Параметры:
# - name: как будет называться папка в OUTPUT_ROOT
# - dirs: список путей
# - priority: True => это "важная" категория (речь дикторов и т.п.)
# - mode:
#     "full"     => брать файлы целиком (полезно для речи)
#     "windowed" => брать по N окон из каждого файла
# - sacrifice: True => если нужно уменьшать объём, сначала выкидываем файлы отсюда
# - windows_per_file: (опционально) override вместо DEFAULT_WINDOWS_PER_FILE
# - min_window_sec:   (опционально) override вместо DEFAULT_MIN_WINDOW_SEC
# - tail_policy:
#     "drop"      => хвост < 2сек отбрасываем
#     "pad_noise" => хвост дополняем мягким шумом (НЕ нулями) и сохраняем
#
# ВАЖНО: даже для mode="full" можно поставить tail_policy="pad_noise", чтобы не терять хвост.

CATEGORIES = [
    # Пример: "речь дикторов" — важная, берём целиком
    {
        "name": "BbItovie",
        "dirs": [
            r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\BbItovie",
        ],
        "priority": True,
        "mode": "full",
        "sacrifice": False,
        "tail_policy": "pad_noise",
    },

    # Пример: "речь дикторов" — важная, берём целиком
    {
        "name": "randomSound",
        "dirs": [
            r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\random",
        ],
        "priority": True,
        "mode": "full",
        "sacrifice": False,
        "tail_policy": "pad_noise",
    },

    # Пример: музыка — берём по окнам, можно жертвовать
    {
        "name": "music_mix",
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

    # Пример: город/быт/атмосфера — тоже окна
    {
        "name": "pdsounds_march2009",
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

    # Пример: подкасты/ютуб — длинные, окна
    {
        "name": "podcasts_youtube",
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
            # битый/неподдерживаемый файл — пропускаем
            continue

    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(updated, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # убираем нулевые
    metas = [m for m in metas if m.sr > 0 and m.frames > 0 and m.duration_sec > 0.0]
    return metas


def _ceil_to_segments(sec: float) -> float:
    # округляем вверх до кратности SEGMENT_SEC
    n = int(math.ceil(sec / SEGMENT_SEC))
    return float(n) * SEGMENT_SEC


def _floor_to_segments(sec: float) -> float:
    # округляем вниз до кратности SEGMENT_SEC
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

        # веса по длительности (frames)
        weights = [max(1, int(m.frames)) for m in metas]
        self._cum = np.cumsum(weights).astype(np.int64)
        self._total = int(self._cum[-1])

    def pick(self) -> AudioMeta:
        r = random.randint(1, self._total)
        idx = int(np.searchsorted(self._cum, r, side="left"))
        return self.metas[idx]


def read_segment(meta: AudioMeta, start_sec: float, dur_sec: float, target_sr: int = OUTPUT_SR) -> np.ndarray:
    """
    Читает кусок из файла (seek) и ресемплит до target_sr.
    Возвращает mono float32.
    """
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
        # fallback на librosa (может подхватить некоторые форматы, но чаще грузит целиком)
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

    # mono
    audio = np.mean(audio, axis=1).astype(np.float32)

    if file_sr != target_sr and len(audio) > 0:
        audio = librosa.resample(audio, orig_sr=file_sr, target_sr=target_sr).astype(np.float32)

    audio = np.nan_to_num(audio)
    return audio


def make_low_noise(pool: LowNoisePool, length_samples: int) -> np.ndarray:
    meta = pool.pick()
    # читаем случайный кусок
    dur_sec = float(length_samples) / float(OUTPUT_SR)
    max_start = max(0.0, meta.duration_sec - dur_sec)
    start = random.uniform(0.0, max_start) if max_start > 0 else 0.0
    y = read_segment(meta, start, dur_sec, target_sr=OUTPUT_SR)

    if len(y) < length_samples:
        # тайлим
        if len(y) == 0:
            return np.zeros(length_samples, dtype=np.float32)
        reps = int(math.ceil(length_samples / len(y)))
        y = np.tile(y, reps)[:length_samples]
    else:
        y = y[:length_samples]

    # лёгкая нормализация по пику (чтобы внезапно не был клиппинг)
    mx = float(np.max(np.abs(y)) + 1e-8)
    if mx > 1.0:
        y = y / mx
    return y.astype(np.float32)


# =========================
# 4) ОКНА: где вырезать
# =========================

def pick_window_starts(file_dur: float, window_sec: float, windows_per_file: int) -> List[float]:
    """
    Возвращает список start_sec для окон.
    Якоря равномерно распределены по файлу, затем применяется jitter.
    """
    file_dur = float(file_dur)
    window_sec = float(window_sec)
    k = int(windows_per_file)

    if k <= 0 or window_sec <= 0 or file_dur <= 0:
        return []

    # если файл слишком короткий — возьмём одно окно с 0
    if file_dur <= window_sec:
        return [0.0]

    max_start = file_dur - window_sec
    if max_start <= 0:
        return [0.0]

    starts: List[float] = []
    # центры: (i+0.5)/k
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
    """
    Сколько секунд (кратно SEGMENT_SEC) этот файл даст в датасет при заданном base_window_nseg.
    """
    mode = cat.get("mode", "windowed")
    tail_policy = cat.get("tail_policy", "drop")

    # сколько "полных" секунд можно реально использовать из файла при drop/pad
    if tail_policy == "pad_noise":
        full_sec = _ceil_to_segments(meta.duration_sec)
    else:
        full_sec = _floor_to_segments(meta.duration_sec)

    if full_sec < SEGMENT_SEC:
        return 0.0

    if mode == "full":
        return full_sec

    # windowed
    k = category_windows_per_file(cat)
    k = max(1, k)
    min_nseg = category_min_nseg(cat)
    nseg = max(int(base_window_nseg), int(min_nseg))
    win_sec = float(nseg) * SEGMENT_SEC

    # если файл короткий — берём целиком
    if meta.duration_sec <= win_sec * k:
        return full_sec

    # иначе берём k окон по win_sec (каждое кратно SEGMENT_SEC)
    return float(k) * win_sec


def total_duration_seconds(all_metas_by_cat: Dict[str, List[AudioMeta]], cats_by_name: Dict[str, Dict], base_window_nseg: int) -> float:
    tot = 0.0
    for cname, metas in all_metas_by_cat.items():
        cat = cats_by_name[cname]
        for m in metas:
            tot += file_contribution_seconds(m, cat, base_window_nseg)
    return tot


def choose_base_window_nseg(all_metas_by_cat: Dict[str, List[AudioMeta]], cats_by_name: Dict[str, Dict], target_sec: float) -> int:
    """
    Подбираем base_window_nseg (в сегментах по 2 сек), чтобы суммарная длительность
    была как можно ближе к target_sec, но НЕ меньше минимальных ограничений категорий.
    """
    # минимально возможный base_window_nseg (из глобального min)
    base_min = int(math.ceil(max(DEFAULT_MIN_WINDOW_SEC, SEGMENT_SEC) / SEGMENT_SEC))
    # разумный потолок: 10 минут окна (на всякий)
    base_max = int(math.ceil(600.0 / SEGMENT_SEC))

    tot_min = total_duration_seconds(all_metas_by_cat, cats_by_name, base_min)
    if target_sec >= tot_min:
        # найдём base_nseg, при котором total >= target (или достигнем насыщения)
        lo, hi = base_min, base_min
        tot_hi = tot_min
        while hi < base_max and tot_hi < target_sec:
            hi = min(base_max, hi * 2)
            tot_hi = total_duration_seconds(all_metas_by_cat, cats_by_name, hi)

            # если уже не растёт (все упёрлись в full), смысла дальше нет
            if tot_hi == total_duration_seconds(all_metas_by_cat, cats_by_name, hi + 1):
                break

        if tot_hi <= target_sec:
            return hi  # даже на максимуме меньше/равно цели => берём максимум (почти всё)

        # бинарный поиск: найдём наибольший nseg, чтобы total <= target_sec
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

    # target меньше минимального => потом будем урезать файлами
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
    """
    Если даже при минимальном окне суммарная длительность больше target_sec,
    то выкидываем файлы, начиная с sacrifice категорий.

    Возвращает: (new_metas_by_cat, warnings)
    """
    warnings: List[str] = []

    # посчитаем contributions
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
        # ничего не нужно выкидывать
        new_map = {c: [m for m, _ in rows] for c, rows in contrib.items()}
        return new_map, warnings

    need_remove = total - target_sec

    # категории по группам
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

            # чтобы категория не исчезла совсем
            keep_min = 0 if allow_empty_category else int(MIN_KEEP_FILES_PER_CATEGORY)
            keep_min = max(0, keep_min)

            # сортируем по вкладy (длинные файлы — первыми), но внутри одинаковых — рандом
            random.shuffle(rows)
            rows.sort(key=lambda t: t[1], reverse=True)

            while need_remove > 0 and len(rows) > keep_min:
                _m, c = rows.pop(0)  # выкинули один файл
                removed += c
                need_remove -= c

            contrib[cname] = rows

            if need_remove <= 0:
                break
        return removed

    _removed1 = drop_from_categories(sacrifice_cats, allow_empty_category=False)
    if need_remove > 0:
        _removed2 = drop_from_categories(normal_cats, allow_empty_category=False)
    else:
        _removed2 = 0.0

    if need_remove > 0:
        warnings.append(
            "ВНИМАНИЕ: цель слишком маленькая даже после удаления sacrifice+обычных категорий. "
            "Приходится удалять файлы из PRIORITY категорий."
        )
        _removed3 = drop_from_categories(priority_cats, allow_empty_category=True)
    else:
        _removed3 = 0.0

    if need_remove > 0:
        warnings.append(
            f"ВНИМАНИЕ: всё ещё выше цели на {need_remove/3600:.2f} ч (больше нечего удалять)."
        )

    new_map = {c: [m for m, _ in rows] for c, rows in contrib.items()}
    return new_map, warnings


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
    """
    Режет сигнал (mono, OUTPUT_SR) на SEGMENT_SAMPLES и пишет wav.
    Возвращает сколько сегментов записано.
    """
    os.makedirs(out_dir, exist_ok=True)

    if y is None or len(y) < 1:
        return 0

    total = len(y)
    n_full = total // SEGMENT_SAMPLES
    written = 0

    # полные
    for i in range(n_full):
        seg = y[i * SEGMENT_SAMPLES:(i + 1) * SEGMENT_SAMPLES]
        out_path = os.path.join(out_dir, f"{base_stem}__seg{i:04d}.wav")
        sf.write(out_path, seg.astype(np.float32), OUTPUT_SR)
        written += 1

    # хвост
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
    """
    Делает фактическую нарезку одного файла согласно стратегии категории.
    """
    mode = cat.get("mode", "windowed")
    tail_policy = cat.get("tail_policy", "drop")

    k = max(1, category_windows_per_file(cat))
    min_nseg = category_min_nseg(cat)
    nseg = max(int(base_window_nseg), int(min_nseg))
    win_sec = float(nseg) * SEGMENT_SEC

    base = os.path.splitext(os.path.basename(meta.path))[0]
    base = _safe_name(base)

    total_written = 0

    # helper: читаем и пишем один "кусок"
    def handle_chunk(start_sec: float, dur_sec: float, chunk_tag: str):
        nonlocal total_written
        y = read_segment(meta, start_sec, dur_sec, target_sr=OUTPUT_SR)

        # лёгкий DC removal
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

    # windowed
    if meta.duration_sec <= win_sec * k:
        # короткий файл — берём целиком
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

    # --- загрузим low-noise pool для паддинга хвостов (если нужно) ---
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

    # --- собираем меты по категориям ---
    cache_dir = os.path.join(OUTPUT_ROOT, "_cache_meta")
    os.makedirs(cache_dir, exist_ok=True)

    all_metas_by_cat: Dict[str, List[AudioMeta]] = {}
    cats_by_name: Dict[str, Dict] = {}

    # нормализуем категории: пропускаем пустые dirs
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

        # кэш мета на категорию
        h = hashlib.md5(("|".join(cat["dirs"]) + cname).encode("utf-8")).hexdigest()[:8]
        cache_path = os.path.join(cache_dir, f"meta_{_safe_name(cname)}__{h}.json")

        metas = load_or_build_meta(files, cache_path)
        all_metas_by_cat[cname] = metas
        print(f"[META] {cname}: файлов={len(files)} | meta_ok={len(metas)}")

    # удалить пустые категории
    all_metas_by_cat = {c: ms for c, ms in all_metas_by_cat.items() if ms}
    if not all_metas_by_cat:
        print("Не найдено ни одного валидного аудиофайла в категориях.")
        return

    target_sec = float(TARGET_NEG_HOURS) * 3600.0

    print("\n[ШАГ 2/3] Расчёт плана (сколько и как резать)...")

    # --- подбираем базовую длину окна ---
    base_window_nseg = choose_base_window_nseg(all_metas_by_cat, cats_by_name, target_sec)
    base_window_sec = float(base_window_nseg) * SEGMENT_SEC

    tot_now = total_duration_seconds(all_metas_by_cat, cats_by_name, base_window_nseg)

    print("\n=== ПЛАН ===")
    print(f"Цель: {TARGET_NEG_HOURS:.2f} ч ({target_sec:.0f} сек)")
    print(f"Базовое окно: {base_window_sec:.1f} сек (nseg={base_window_nseg}, сегмент={SEGMENT_SEC:.1f}с)")
    print(f"Итого по плану ДО урезания файлами: {_fmt_hours(tot_now)}")

    # --- если цель меньше минимума — урезаем файлами ---
    selected_metas_by_cat, warnings = downsample_files_if_needed(
        all_metas_by_cat, cats_by_name, base_window_nseg, target_sec
    )

    tot_sel = total_duration_seconds(selected_metas_by_cat, cats_by_name, base_window_nseg)
    print(f"Итого по плану ПОСЛЕ урезания файлами: {_fmt_hours(tot_sel)}")
    if warnings:
        print("\n" + "\n".join([f"!!! {w}" for w in warnings]) + "\n")

    # --- предупреждение, если output не пустой (игнорируем служебные папки) ---
    IGNORE_IN_OUTPUT = {"_cache_meta"}

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

    # --- отчёты ---
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
    }

    details_rows: List[Dict] = []

    # --- режем ---
    total_written_segments = 0
    for cname, metas in selected_metas_by_cat.items():
        cat = cats_by_name[cname]
        out_cat_dir = os.path.join(OUTPUT_ROOT, _safe_name(cname))

        # статистика по категории
        cat_tot = sum(file_contribution_seconds(m, cat, base_window_nseg) for m in metas)
        summary["categories"].append({
            "name": cname,
            "files_selected": len(metas),
            "planned_hours": cat_tot / 3600.0,
            "mode": cat.get("mode", "windowed"),
            "priority": bool(cat.get("priority", False)),
            "sacrifice": bool(cat.get("sacrifice", False)),
            "windows_per_file": category_windows_per_file(cat),
            "min_window_sec": float(cat.get("min_window_sec", DEFAULT_MIN_WINDOW_SEC)),
            "tail_policy": cat.get("tail_policy", "drop"),
        })

        print(f"\n--- КАТЕГОРИЯ: {cname} | файлов: {len(metas)} | план: {_fmt_hours(cat_tot)}")
        for m in tqdm(metas, desc=cname, leave=False):
            total_written_segments += process_file(
                m, cat, base_window_nseg, out_cat_dir, low_noise_pool, details_rows
            )

    # финальная запись summary + csv
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

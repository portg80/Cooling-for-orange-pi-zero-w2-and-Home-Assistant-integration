"""
Audio augmentation script (wake-word / keyword spotting dataset)

Что делает этот скрипт:
1) Берёт "позитивные" исходники (голос / wake-word) из INPUT_DIR
2) Для каждого файла создаёт несколько версий (аугментаций):
   - оригинал (2 секунды, с низким фоновым шумом для паддинга)
   - pitch shift (изменение высоты тона)
   - reverb (реверберация через convolution с impulse response)
   - aggressive noise (агрессивный шум поверх всей дорожки)
   - pitch + reverb
   - pitch + aggressive noise
3) Сохраняет:
   - позитивные аугментации в OUTPUT_DIR
   - отдельно сохраняет "чистый шум", который использовался при наложении,
     в AGGRESSIVE_NOISE_USED_FOR_NEGATIVE_DIR (это удобно как негативные примеры)

Зачем здесь два типа шума:
- low_noise: мягкий шум используется как "фон" для паддинга до 2 секунд,
  чтобы вместо тишины (нулей) не появлялась "чёрная полоса" на спектрограмме.
- aggressive_noise: сильный шум накладывается на всю дорожку, имитирует реальный фон
  (улица, техника, помещение и т.п.). Параллельно сохраняется сам шум как NEG samples.

Требования к структуре папок:
INPUT_DIR/
  *.wav или *.mp3

data/low_noise/*.wav
data/aggressive_noise/*.wav
data/ir/*.wav  (impulse response файлы для реверба)

Результат будет рядом с исходниками:
INPUT_DIR/AUGMENTS/positive_augments/
INPUT_DIR/AUGMENTS/aggressive_noise_used_for_negative/
"""

import os
import glob
import random

import numpy as np
import librosa
import soundfile as sf
from tqdm import tqdm
from scipy.signal import fftconvolve

import torch
from silero_vad import load_silero_vad, get_speech_timestamps
from typing import List, Tuple

import json
import bisect
from dataclasses import dataclass
from typing import List, Tuple, Optional
import hashlib


# =============================
# 1) БАЗОВЫЕ ПАРАМЕТРЫ АУДИО
# =============================

SR = 16000           # sample rate: приводим всё к 16 kHz (часто стандарт для wakeword/KWS)
DURATION = 2         # каждая итоговая дорожка будет ровно 2 секунды

# INPUT_DIR = "data/positive_raw"
# =============================
# ПАПКИ С ПОЗИТИВАМИ/негативами (СПИСОК)
# =============================
# INPUT_DIRS = [
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_PREOBRABOTKA\v2_positive\PAPA_NoiseRedux_volume_minus20db",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_PREOBRABOTKA\v2_positive\MAXIM_volume_minus20db",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_PREOBRABOTKA\v2_positive\MAMA_NoiseRedux_volume_minus20db",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_PREOBRABOTKA\v2_positive\Elizaveta_NoiseRedux_volume_minus20db",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_positive\TTS_VOICE_timeBad",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_PREOBRABOTKA\v2_positive\MY_VOICE_volgu_na_pare",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_PREOBRABOTKA\v2_positive\MY_one_mic",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_PREOBRABOTKA\v2_positive\MY_3_mic",
#     r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_positive\IGOREK_SAVINOV"
# ]

INPUT_DIRS = [
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\Похожие_на_позитив_Афина_слова_НЕГАТИВЫ",
]

# Ищем позитивы рекурсивно? (если у тебя внутри папок есть подпапки)
POSITIVE_RECURSIVE = True  # True если надо обходить подпапки

# =============================
# КУДА СОХРАНЯТЬ РЕЗУЛЬТАТЫ
# =============================

# "near"    -> рядом с исходниками: <input_dir>/AUGMENTS/...
# "central" -> в одну папку: <CENTRAL_OUTPUT_ROOT>/<dataset_name>/...
OUTPUT_MODE = "central"

CENTRAL_OUTPUT_ROOT = r"E:\LABS_VOLGU\WakeWord_Neiro\data\NEGATIVES_SPEAKERS_2s_DONE_AGUMENTATION\new_vtoroy_dop"





# Как именно "вставлять" исходный клип в 2 секунды:
# - start  : прижать к началу
# - end    : прижать к концу
# - center : примерно по центру (и ещё добавляется небольшой random jitter)
crop_mode = 'center'


# =============================
# 2) ПАРАМЕТРЫ АУГМЕНТАЦИЙ
# =============================

# Pitch-shift: в полутонах (например -1 = чуть ниже, +2 = чуть выше)
PITCH_SHIFTS = [-1, 2]

# # Эти параметры не используются в текущей версии (видимо старый вариант reverb),
# # но оставлены, чтобы было понятно, что можно тюнить.
# REVERB_ALPHAS = [0.35, 0.22, 0.15]
# REVERB_DELAYS = [int(SR*0.03), int(SR*0.07), int(SR*0.12)]

# Допустимые расширения входных файлов
ALLOWED_EXTENSIONS = ['.wav', '.mp3']


# =============================
# 3) ПАПКИ С ШУМАМИ (СПИСКИ ПАПОК)
# =============================

# Можно указать много папок, внутри могут быть подпапки (если recursive=True)
LOW_NOISE_DIRS = [
    r"data\low_noise",
    # r"E:\NOISES\soft\room",
    # r"E:\NOISES\soft\street",
]

AGGRESSIVE_NOISE_DIRS = [
    r"data\aggressive_noise",
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\BbItovie",
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\miusic_classical",
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\pdsounds_march2009",
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\random",
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\Random_YT_muz",
]

# Какие форматы искать в шумовых папках
NOISE_EXTENSIONS = (".wav", ".flac", ".ogg")  # soundfile читает это нормально
NOISE_RECURSIVE = False  # True = искать во всех подпапках

# ВАЖНО: mp3 лучше не использовать для шумов в таком пайплайне —
# random seek по mp3 часто медленный/неточный. Лучше заранее конвертировать в wav.


# =============================
# 4) ГРОМКОСТЬ ШУМОВ (RMS)
# =============================
# Идея: мы смотрим RMS исходника и делаем шум "тише" относительно него.
# Чем больше число — тем ТИШЕ шум (потому что target_rms = clip_rms / factor)

LOW_NOISE_MULTIPLE_VOLUME_DOWN = 2.0

AGGRESSIVE_NOISE_MULTIPLE_VOLUME_DOWNS = [3.0, 4.0, 5.5, 8.5]

# Сколько раз повторять генерацию для каждого уровня агрессивного шума.
# Если 2 — датасет увеличится, потому что каждый раз будет новый случайный шум.
AGGRESSIVE_NOISE_PASSES = 2  # 1 = текущий размер, 2 = в 2 раза больше шумовых вариантов


# =============================
# 5) СЛУЧАЙНАЯ ГРОМКОСТЬ ИТОГА
# =============================

# Рандомная громкость итоговой дорожки (как data augmentation)
# 0.5–1.5: может стать тише/громче по амплитуде.
VOLUME_JITTER_MIN = 0.5
VOLUME_JITTER_MAX = 1.5


# =============================
# 6) REVERB: IMPULSE RESPONSES
# =============================

IR_DIR = "data/ir"  # impulse responses (.wav)

# Загружаем IR заранее (один раз), чтобы не делать это на каждый файл
ir_list = []
for ir_path in glob.glob(os.path.join(IR_DIR, "*.wav")):
    ir, _ = librosa.load(ir_path, sr=SR, mono=True)
    tag = os.path.splitext(os.path.basename(ir_path))[0]  # имя файла без .wav
    ir_list.append((tag, ir))


# =============================
# 7) TRIM/ПРЕДОБРАБОТКА ДЛЯ TTS
# =============================
# Если исходники TTS — там часто есть "клеёная" тишина.
# Мы её вырезаем точнее, маленькими окнами, и возвращаем немного контекста.

TRIM_TOP_DB = 35
TRIM_FRAME_LEN = 512     # 32 мс при SR=16k
TRIM_HOP_LEN = 128       # 8 мс
TRIM_PAD_MS = 30         # вернуть немного контекста после trim (чтобы не отрезать согласные)


# =============================
# 8) ЗАЩИТА ОТ "СЛИШКОМ НУЛЕВОГО" ПАДДИНГ-ШУМА
# =============================

# Если запись почти тишина — RMS может стать почти 0.
# Тогда паддинг-шум тоже станет почти нулём и не решит проблему "чёрных полос".
PAD_NOISE_RMS_FLOOR_DB = -60
PAD_NOISE_RMS_FLOOR = 10 ** (PAD_NOISE_RMS_FLOOR_DB / 20)

# Эти параметры сейчас не используются напрямую (возможно планы на сглаживание),
# но оставлены.
PAD_CROSSFADE_MS = 20

# Смещение центра вставки, чтобы не всегда идеально в центре (модель будет устойчивее)
CENTER_JITTER_MS = 150

# При вставке речи в шум — шум "заходит" внутрь речи на N мс с плавным fade,
# чтобы не было резкого перехода.
NOISE_EDGE_OVERLAP_MS = 100

# Шум под речью:
# 0 = полностью вырезать шум под речью (как было бы при "нулевом фоне")
# 0.1–0.3 обычно хорошо: сохраняем часть шума под речью => более реалистично.
LOW_NOISE_UNDER_SPEECH_RATIO = 0.15
LOW_NOISE_UNDER_SPEECH_JITTER = 0.05  # чуть рандомим ratio



# =============================
# VAD (Silero) — безопасный сдвиг фразы внутри 2 секунд
# =============================

USE_SILERO_VAD = True

# Порог "это речь". 0.5 обычно норм, но можно тюнить под свой датасет. :contentReference[oaicite:2]{index=2}
VAD_THRESHOLD = 0.5

# Минимальная длительность "куска речи" — для wakeword можно меньше, чем дефолт.
VAD_MIN_SPEECH_MS = 120
VAD_MIN_SILENCE_MS = 80

# Расширяем границы речи на N мс, чтобы не срезать согласные/атаки
VAD_SPEECH_PAD_MS = 80

# Если VAD дал несколько кусков речи, и пауза между ними маленькая — считаем это одной фразой
VAD_MERGE_GAP_MS = 500

# Печатать в консоль, на сколько можно сдвинуть (в мс)
DEBUG_VAD_SHIFT = False

# Silero VAD модель грузим один раз, потом используем на всех файлах
_vad_model = None

def init_vad():
    """
    Загружает Silero VAD модель один раз.
    Модель небольшая и быстрая; на CPU обычно хватает.
    """
    global _vad_model
    if _vad_model is None:
        _vad_model = load_silero_vad()
    return _vad_model


# =============================
# КЭШ МЕТАДАННЫХ ШУМОВ (ускорение на больших наборах)
# =============================

NOISE_META_CACHE_ENABLE = True

# Куда сохранять кэш (логично рядом с AUGMENTS, чтобы относилось к проекту)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
NOISE_META_CACHE_DIR = os.path.join(SCRIPT_DIR, "_cache_noise_meta")
os.makedirs(NOISE_META_CACHE_DIR, exist_ok=True)

LOW_NOISE_META_CACHE_PATH = os.path.join(NOISE_META_CACHE_DIR, "low_noise_meta.json")
AGGR_NOISE_META_CACHE_PATH = os.path.join(NOISE_META_CACHE_DIR, "aggr_noise_meta.json")

# Выбор шума:
# False = равновероятно по файлам (много коротких файлов будут попадаться чаще)
# True  = взвешенно по длительности (более “честное” распределение по времени)
NOISE_WEIGHT_BY_DURATION = True


# =============================
# 9) ЗАГРУЗКА ШУМОВ
# =============================
def collect_audio_files(dirs: List[str], exts: Tuple[str, ...], recursive: bool = True) -> List[str]:
    """
    Собирает список файлов с нужными расширениями из списка папок.
    recursive=True => обходит подпапки.
    """
    exts = tuple(e.lower() for e in exts)
    out = []

    for root in dirs:
        if not root:
            continue
        if not os.path.isdir(root):
            print(f"[WARN] Noise dir not found: {root}")
            continue

        if recursive:
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    if os.path.splitext(fn)[1].lower() in exts:
                        out.append(os.path.join(dirpath, fn))
        else:
            for fn in os.listdir(root):
                path = os.path.join(root, fn)
                if os.path.isfile(path) and os.path.splitext(fn)[1].lower() in exts:
                    out.append(path)

    # убираем дубликаты (на всякий)
    out = sorted(set(out))
    return out


@dataclass(frozen=True)
class NoiseMeta:
    path: str
    sr: int
    frames: int
    channels: int
    mtime: float
    size: int


def _file_stamp(path: str) -> Tuple[float, int]:
    st = os.stat(path)
    return float(st.st_mtime), int(st.st_size)


def load_or_build_noise_meta(
    files: List[str],
    cache_path: str,
    enable_cache: bool = True,
) -> List[NoiseMeta]:
    """
    Делает список метаданных NoiseMeta для файлов.
    Если enable_cache=True и cache_path существует:
      - загружает JSON
      - проверяет mtime/size (если файл поменялся — пересчитывает)
      - дополняет новыми файлами
      - сохраняет обратно
    """
    cached = {}
    if enable_cache and os.path.isfile(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
        except Exception:
            cached = {}

    metas: List[NoiseMeta] = []
    updated_cache = {}

    # Чтобы не печатать тонны, но было понятно что происходит
    print(f"[NOISE_META] Building meta for {len(files)} files (cache={'ON' if enable_cache else 'OFF'})")

    for path in tqdm(files, desc="Noise meta", leave=False):
        try:
            mtime, size = _file_stamp(path)

            key = path.replace("\\", "/")  # нормализуем ключ под Windows/JSON
            rec = cached.get(key)

            if rec and rec.get("mtime") == mtime and rec.get("size") == size:
                sr = int(rec["sr"])
                frames = int(rec["frames"])
                channels = int(rec.get("channels", 1))
            else:
                info = sf.info(path)  # читает только заголовок
                sr = int(info.samplerate)
                frames = int(info.frames)
                channels = int(info.channels)

            meta = NoiseMeta(
                path=path,
                sr=sr,
                frames=frames,
                channels=channels,
                mtime=mtime,
                size=size,
            )
            metas.append(meta)

            updated_cache[key] = {
                "sr": sr,
                "frames": frames,
                "channels": channels,
                "mtime": mtime,
                "size": size,
            }

        except Exception:
            # пропускаем битые/неподдерживаемые файлы
            continue

    if enable_cache:
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(updated_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # Отфильтруем нулевые (на всякий)
    metas = [m for m in metas if m.frames > 0 and m.sr > 0]
    return metas


class NoisePool:
    """
    Пул шумов:
    - хранит NoiseMeta (sr, frames, path)
    - умеет выбирать случайный файл:
        * равновероятно по файлам
        * или взвешенно по длительности (frames)
    """
    def __init__(self, metas: List[NoiseMeta], weight_by_duration: bool = True):
        if not metas:
            raise RuntimeError("NoisePool: empty metas")

        self.metas = metas
        self.weight_by_duration = bool(weight_by_duration)

        if self.weight_by_duration:
            weights = [max(1, int(m.frames)) for m in metas]
            self._cum = np.cumsum(weights).astype(np.int64)
            self._total = int(self._cum[-1])
        else:
            self._cum = None
            self._total = 0

    def pick(self) -> NoiseMeta:
        if not self.weight_by_duration:
            return random.choice(self.metas)

        r = random.randint(1, self._total)
        idx = int(np.searchsorted(self._cum, r, side="left"))
        return self.metas[idx]


def read_random_segment_from_meta(meta: NoiseMeta, target_len_samples: int, target_sr: int = SR) -> np.ndarray:
    """
    Читает случайный сегмент из файла, используя кэшированные sr/frames.
    Файл всё равно открываем (иначе не прочитать), но НЕ вычисляем frames/sr из заголовка каждый раз.
    """
    eps = 1e-8
    file_sr = int(meta.sr)
    frames = int(meta.frames)

    # сколько фреймов нужно прочитать при file_sr
    seg_len_frames = int(round(target_len_samples * (file_sr / target_sr)))
    seg_len_frames = max(1, seg_len_frames)

    with sf.SoundFile(meta.path) as f:
        if frames >= seg_len_frames:
            start = random.randint(0, frames - seg_len_frames)
            f.seek(start)
            audio = f.read(seg_len_frames, dtype="float32", always_2d=True)  # [T, C]
        else:
            f.seek(0)
            audio = f.read(frames, dtype="float32", always_2d=True)
            if audio.shape[0] == 0:
                return np.zeros(target_len_samples, dtype=np.float32)
            reps = int(np.ceil(seg_len_frames / audio.shape[0]))
            audio = np.tile(audio, (reps, 1))[:seg_len_frames]

    # mono
    audio = np.mean(audio, axis=1).astype(np.float32)

    # ресемпл если нужно
    if file_sr != target_sr:
        audio = librosa.resample(audio, orig_sr=file_sr, target_sr=target_sr).astype(np.float32)

    # доводим до нужной длины
    if len(audio) > target_len_samples:
        audio = audio[:target_len_samples]
    elif len(audio) < target_len_samples:
        audio = np.pad(audio, (0, target_len_samples - len(audio)), mode="constant")

    audio = np.nan_to_num(audio)
    max_abs = float(np.max(np.abs(audio)) + eps)
    if max_abs > 10:
        audio = audio / max_abs

    return audio


low_noise_files = collect_audio_files(LOW_NOISE_DIRS, NOISE_EXTENSIONS, recursive=NOISE_RECURSIVE)
aggressive_noise_files = collect_audio_files(AGGRESSIVE_NOISE_DIRS, NOISE_EXTENSIONS, recursive=NOISE_RECURSIVE)

if not low_noise_files:
    raise RuntimeError(f"Не найдено шумов low_noise в папках: {LOW_NOISE_DIRS}")
if not aggressive_noise_files:
    raise RuntimeError(f"Не найдено шумов aggressive_noise в папках: {AGGRESSIVE_NOISE_DIRS}")

print(f"[NOISE] low files: {len(low_noise_files)}")
print(f"[NOISE] aggr files: {len(aggressive_noise_files)}")

# Метаданные с кэшем
low_noise_meta = load_or_build_noise_meta(
    low_noise_files,
    cache_path=LOW_NOISE_META_CACHE_PATH,
    enable_cache=NOISE_META_CACHE_ENABLE,
)
aggr_noise_meta = load_or_build_noise_meta(
    aggressive_noise_files,
    cache_path=AGGR_NOISE_META_CACHE_PATH,
    enable_cache=NOISE_META_CACHE_ENABLE,
)

if not low_noise_meta:
    raise RuntimeError("low_noise_meta пуст — все файлы битые/неподдерживаемые?")
if not aggr_noise_meta:
    raise RuntimeError("aggr_noise_meta пуст — все файлы битые/неподдерживаемые?")

# Пулы шумов (быстрый random pick)
low_noise_pool = NoisePool(low_noise_meta, weight_by_duration=NOISE_WEIGHT_BY_DURATION)
aggressive_noise_pool = NoisePool(aggr_noise_meta, weight_by_duration=NOISE_WEIGHT_BY_DURATION)

print(f"[NOISE_META] low meta ok: {len(low_noise_meta)}")
print(f"[NOISE_META] aggr meta ok: {len(aggr_noise_meta)}")

# =====================================
# 10) ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (UTILS)
# =====================================

def dataset_folder_name(input_dir: str) -> str:
    base = os.path.basename(os.path.normpath(input_dir))
    h = hashlib.md5(input_dir.encode("utf-8")).hexdigest()[:8]
    return f"{base}__{h}"

def collect_positive_files(input_dir: str, exts: list[str], recursive: bool = False) -> list[str]:
    """
    Собирает список позитивных файлов из input_dir.
    recursive=False => только файлы в корне папки
    recursive=True  => обходит подпапки
    """
    out = []
    exts_l = set(e.lower() for e in exts)

    if recursive:
        for dirpath, _, filenames in os.walk(input_dir):
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in exts_l:
                    out.append(os.path.join(dirpath, fn))
    else:
        for ext in exts:
            out.extend(glob.glob(os.path.join(input_dir, f"*{ext}")))

    return sorted(set(out))


def setup_aug_dirs(input_dir: str):
    """
    Создаёт папки для результатов.

    Режимы:
    - OUTPUT_MODE="near":
        <input_dir>/AUGMENTS/positive_augments
        <input_dir>/AUGMENTS/aggressive_noise_used_for_negative

    - OUTPUT_MODE="central":
        <CENTRAL_OUTPUT_ROOT>/<dataset_name>/positive_augments
        <CENTRAL_OUTPUT_ROOT>/<dataset_name>/aggressive_noise_used_for_negative
    """
    if OUTPUT_MODE not in ("near", "central"):
        raise ValueError("OUTPUT_MODE must be 'near' or 'central'")

    if OUTPUT_MODE == "near":
        root = os.path.join(input_dir, "AUGMENTS")
    else:
        dataset_name = dataset_folder_name(input_dir)
        root = os.path.join(CENTRAL_OUTPUT_ROOT, dataset_name)

    output_dir = os.path.join(root, "positive_augments")
    neg_dir = os.path.join(root, "aggressive_noise_used_for_negative")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(neg_dir, exist_ok=True)

    return root, output_dir, neg_dir


def _safe_tag(s: str, max_len: int = 40) -> str:
    """
    Делает строку безопасной для имени файла:
    - оставляет буквы/цифры/ '_' / '-'
    - пробелы/точки/запятые заменяет на '_'
    - остальное удаляет
    - ограничивает длину
    """
    out = []
    for ch in str(s):
        if ch.isalnum() or ch in ("_", "-"):
            out.append(ch)
        elif ch in (" ", ".", ","):
            out.append("_")
    res = "".join(out).strip("_")
    if not res:
        res = "ir"
    return res[:max_len]


def get_random_segment(pool: NoisePool, length: int, target_rms=None):
    """
    Берёт случайный шумовой сегмент длиной length (в сэмплах SR) из NoisePool.
    """
    eps = 1e-8
    meta = pool.pick()
    noise_segment = read_random_segment_from_meta(meta, target_len_samples=length, target_sr=SR)

    if target_rms is not None:
        current_rms = float(np.sqrt(np.mean(noise_segment ** 2) + eps))
        if current_rms > 0:
            noise_segment = noise_segment * (target_rms / current_rms)

    return noise_segment



def get_low_noise_segment(length, target_rms=None):
    return get_random_segment(low_noise_pool, length, target_rms)

def get_aggressive_noise_segment(length, target_rms=None):
    return get_random_segment(aggressive_noise_pool, length, target_rms)




def estimate_background_rms(y, sr=SR, window_ms=100, percentile=20):
    """
    Оценка RMS фонового уровня записи.

    Почему не просто RMS всего сигнала:
    - если в записи есть тишина, общий RMS может сильно "просесть"
    - для TTS это критично: тишина может сделать RMS почти 0
      => паддинг-шум станет почти нулём

    Как считается:
    - делим сигнал на окна window_ms
    - считаем RMS каждого окна
    - берём percentile (например 20-й процентиль) как "фон"
    - применяем нижнюю границу PAD_NOISE_RMS_FLOOR
    """
    eps = 1e-8
    frame_len = int(sr * window_ms / 1000)

    if len(y) < frame_len:
        bg = float(np.sqrt(np.mean(y ** 2) + eps))
        return max(bg, PAD_NOISE_RMS_FLOOR)

    rms_values = []
    for start in range(0, len(y) - frame_len + 1, frame_len):
        frame = y[start:start + frame_len]
        rms = float(np.sqrt(np.mean(frame ** 2) + eps))
        rms_values.append(rms)

    rms_values = np.array(rms_values, dtype=np.float32)

    # выкидываем совсем малые значения, чтобы percentile не "упал" в почти 0
    usable = rms_values[rms_values > PAD_NOISE_RMS_FLOOR]
    if usable.size == 0:
        bg = float(np.sqrt(np.mean(y ** 2) + eps))
    else:
        bg = float(np.percentile(usable, percentile))

    return max(bg, PAD_NOISE_RMS_FLOOR)


def adjust_length_with_noise(y, duration=DURATION, mode='center', base_rms=None):
    """
    Делает из произвольного клипа ровно `duration` секунд (по умолчанию 2 сек).

    ВАЖНО: мы не просто дополняем нулями, а:
    1) создаём low-noise на всю длину 2 сек (одним непрерывным куском)
    2) вставляем оригинальную речь на нужное место (start/end/center)
    3) под речью оставляем часть шума (LOW_NOISE_UNDER_SPEECH_RATIO),
       т.е. фон не исчезает полностью
    4) делаем плавный переход на краях речи (NOISE_EDGE_OVERLAP_MS)

    Это нужно, чтобы спектрограммы были более реалистичными и модель не училась на "тишине".
    """
    target_len = int(SR * duration)
    y = np.asarray(y, dtype=np.float32)

    # Если сигнал длиннее 2 секунд — режем (у center есть небольшой random jitter)
    if len(y) > target_len:
        if mode == 'center':
            base_start = (len(y) - target_len) // 2
            jitter = int(SR * CENTER_JITTER_MS / 1000)
            shift = random.randint(-jitter, jitter) if jitter > 0 else 0
            start = max(0, min(base_start + shift, len(y) - target_len))
        elif mode == 'start':
            start = 0
        elif mode == 'end':
            start = len(y) - target_len
        else:
            raise ValueError("Invalid mode")
        return y[start:start + target_len]

    # Если сигнал короче 2 секунд — будем "вставлять" его внутрь
    pad_total = target_len - len(y)

    # Вычисляем, где начнётся речь в итоговом 2-секундном буфере
    if mode == 'center':
        base_left = pad_total // 2
        jitter = int(SR * CENTER_JITTER_MS / 1000)
        shift = random.randint(-jitter, jitter) if jitter > 0 else 0
        pad_left = base_left + shift
        pad_left = max(0, min(pad_left, pad_total))
    elif mode == 'start':
        pad_left = 0
    elif mode == 'end':
        pad_left = pad_total
    else:
        raise ValueError("Invalid mode")

    y_len = len(y)
    y_start = pad_left
    y_end = pad_left + y_len

    # Оценим "фон" записи, чтобы выставить уровень паддинг-шума
    if base_rms is None:
        base_rms = estimate_background_rms(y, sr=SR)

    # target_rms для low-noise: делаем шум тише относительно base_rms
    if LOW_NOISE_MULTIPLE_VOLUME_DOWN and LOW_NOISE_MULTIPLE_VOLUME_DOWN > 0:
        target_rms = max(base_rms / LOW_NOISE_MULTIPLE_VOLUME_DOWN, PAD_NOISE_RMS_FLOOR)
    else:
        target_rms = max(base_rms, PAD_NOISE_RMS_FLOOR)

    # 1) Создаём буфер длиной 2 сек и вставляем оригинал
    out = np.zeros(target_len, dtype=np.float32)
    out[y_start:y_end] = y

    # 2) Генерируем один непрерывный low-noise на всю длину
    noise_full = get_low_noise_segment(target_len, target_rms=target_rms).astype(np.float32)

    # 3) Делаем "огибающую" (маску) для шума:
    #    - вне речи шум = 1.0
    #    - под речью шум = LOW_NOISE_UNDER_SPEECH_RATIO (с джиттером)
    base_under = float(LOW_NOISE_UNDER_SPEECH_RATIO)
    jitter = float(LOW_NOISE_UNDER_SPEECH_JITTER) if 'LOW_NOISE_UNDER_SPEECH_JITTER' in globals() else 0.0
    if jitter > 0:
        base_under = max(0.0, min(1.0, base_under + random.uniform(-jitter, jitter)))

    env = np.ones(target_len, dtype=np.float32)
    env[y_start:y_end] = base_under

    # 4) Плавные переходы на краях речи
    overlap = int(round(SR * (NOISE_EDGE_OVERLAP_MS / 1000.0)))
    overlap = max(1, overlap)
    overlap = min(overlap, y_len // 2) if y_len >= 2 else 0

    if overlap > 0:
        env[y_start:y_start + overlap] = np.linspace(1.0, base_under, overlap, endpoint=True, dtype=np.float32)
        env[y_end - overlap:y_end] = np.linspace(base_under, 1.0, overlap, endpoint=True, dtype=np.float32)

    # 5) Итог: речь + шум*маска
    out = out + noise_full * env
    return out


def adjust_length(y, duration=DURATION, mode='center'):
    """
    Обёртка над adjust_length_with_noise():
    - если y > 2 сек: режем
    - если y < 2 сек: оцениваем фон (RMS) и делаем паддинг шумом
    """
    target_len = int(SR * duration)

    if len(y) > target_len:
        if mode == 'center':
            base_start = (len(y) - target_len) // 2
            jitter = int(SR * CENTER_JITTER_MS / 1000)
            shift = random.randint(-jitter, jitter) if jitter > 0 else 0
            start = max(0, min(base_start + shift, len(y) - target_len))
        elif mode == 'start':
            start = 0
        elif mode == 'end':
            start = len(y) - target_len
        else:
            raise ValueError("Invalid mode")
        return y[start:start + target_len]

    base_rms = estimate_background_rms(y, sr=SR)
    return adjust_length_with_noise(y, duration=duration, mode=mode, base_rms=base_rms)


def add_aggressive_noise(y, volume_down_factor, return_noise=False):
    """
    Накладываем агрессивный шум на всю дорожку (y).

    volume_down_factor > 1:
      target_rms = rms(y) / volume_down_factor
      т.е. чем больше factor, тем тише шум.

    return_noise=True:
      возвращаем (y+noise, noise_segment), чтобы noise_segment можно было сохранить как NEG.
    """
    eps = 1e-8
    clip_rms = np.sqrt(np.mean(y ** 2) + eps)

    if volume_down_factor is not None and volume_down_factor > 0:
        target_rms = clip_rms / volume_down_factor
    else:
        target_rms = clip_rms

    noise = get_aggressive_noise_segment(len(y), target_rms=target_rms)
    y_with_noise = y + noise

    if return_noise:
        return y_with_noise, noise
    else:
        return y_with_noise


def apply_pitch_shift(y, semitones):
    """Pitch shift через librosa (изменение высоты в полутонах)."""
    return librosa.effects.pitch_shift(y, sr=SR, n_steps=semitones)


def apply_reverb(y, wet_range=(0.08, 0.28), ir_max_sec=0.35, pre_delay_ms=(0, 25)):
    """
    Реалистичный convolution reverb через impulse response (IR).

    y: входной сигнал
    wet_range: диапазон доли "реверба" в миксе (wet/dry)
    ir_max_sec: обрезаем хвост IR (для wakeword обычно не нужен длинный хвост)
    pre_delay_ms: небольшой pre-delay, чтобы имитировать комнату

    Возвращает:
      (out, used_ir_tag)
    """
    if not ir_list:
        return y, "noir"

    eps = 1e-8

    ir_tag, ir = random.choice(ir_list)
    ir = ir.copy()

    # 1) ограничиваем хвост IR
    max_len = int(SR * ir_max_sec)
    if len(ir) > max_len:
        ir = ir[:max_len]

    # 2) нормализуем IR по пику
    ir = ir / (np.max(np.abs(ir)) + eps)

    # 3) pre-delay (добавим нули в начало IR)
    pd_ms = random.uniform(pre_delay_ms[0], pre_delay_ms[1])
    pd = int(SR * pd_ms / 1000)
    if pd > 0:
        ir = np.concatenate([np.zeros(pd, dtype=ir.dtype), ir])

    # 4) свёртка (convolution)
    wet = fftconvolve(y, ir, mode="full")[:len(y)]

    # 5) смешиваем dry/wet
    wet_amount = random.uniform(wet_range[0], wet_range[1])
    out = (1.0 - wet_amount) * y + wet_amount * wet

    return out, _safe_tag(ir_tag)


def normalize_and_trim(y):
    """
    Предобработка исходника:
    1) trim тишины (точнее для TTS)
    2) вернуть небольшой паддинг (чтобы не срезать начало/конец фонем)
    3) убрать DC offset
    4) нормализовать амплитуду (librosa.util.normalize)
    """
    y_trim, _ = librosa.effects.trim(
        y,
        top_db=TRIM_TOP_DB,
        frame_length=TRIM_FRAME_LEN,
        hop_length=TRIM_HOP_LEN
    )

    if y_trim is None or len(y_trim) == 0:
        y_trim = y

    pad = int(SR * TRIM_PAD_MS / 1000)
    if pad > 0:
        y_trim = np.pad(y_trim, (pad, pad), mode="constant")

    # убираем DC offset (иногда у TTS бывает смещение)
    y_trim = y_trim - float(np.mean(y_trim))

    return librosa.util.normalize(y_trim)


def apply_random_volume(y, factor=None):
    """
    Случайная громкость (volume jitter).
    Возвращает (y_scaled, used_factor).

    Важно:
    - Если factor передать явно, будет применён тот же коэффициент.
      Это полезно, когда ты хочешь одинаково масштабировать и (позитив) и (его noise_segment),
      чтобы "негатив" соответствовал уровню шума из "позитива".
    - Есть лёгкий лимитер: если вышли за [-1, 1], нормируем назад.
    """
    eps = 1e-8
    if VOLUME_JITTER_MIN is None or VOLUME_JITTER_MAX is None:
        return y, 1.0

    if factor is None:
        factor = random.uniform(VOLUME_JITTER_MIN, VOLUME_JITTER_MAX)

    y = y * factor

    max_abs = float(np.max(np.abs(y)) + eps)
    if max_abs > 1.0:
        y = y / max_abs

    return y, factor



def vad_get_phrase_bounds(y: np.ndarray, sr: int = SR):
    """
    Возвращает (speech_start, speech_end) в СЭМПЛАХ для основной фразы в сигнале.

    Логика:
    - get_speech_timestamps может вернуть несколько сегментов
    - мы их "склеиваем", если пауза между ними < VAD_MERGE_GAP_MS
    - затем берём общий [min_start, max_end] как границы фразы (wakeword обычно один кластер)
    """
    if not USE_SILERO_VAD:
        return None

    model = init_vad()

    # Silero ожидает torch.Tensor 1D float
    wav = torch.from_numpy(y.astype(np.float32))

    chunks = get_speech_timestamps(
        wav,
        model,
        sampling_rate=sr,
        threshold=VAD_THRESHOLD,
        min_speech_duration_ms=VAD_MIN_SPEECH_MS,
        min_silence_duration_ms=VAD_MIN_SILENCE_MS,
        speech_pad_ms=VAD_SPEECH_PAD_MS,
        return_seconds=False,
    )

    if not chunks:
        return None

    # Сортируем и склеиваем близкие сегменты
    chunks = sorted(chunks, key=lambda d: d["start"])
    merge_gap = int(sr * (VAD_MERGE_GAP_MS / 1000.0))

    merged = []
    cur_s, cur_e = chunks[0]["start"], chunks[0]["end"]
    for seg in chunks[1:]:
        s, e = seg["start"], seg["end"]
        if s <= cur_e + merge_gap:
            cur_e = max(cur_e, e)
        else:
            merged.append((cur_s, cur_e))
            cur_s, cur_e = s, e
    merged.append((cur_s, cur_e))

    # Для wakeword обычно берем самый "главный" кластер:
    # вариант 1: самый длинный
    best = max(merged, key=lambda t: (t[1] - t[0]))
    return int(best[0]), int(best[1])


def _shift_with_zeros(x: np.ndarray, delta: int) -> np.ndarray:
    """
    Сдвиг массива на delta с заполнением освободившегося места нулями.
    delta > 0 => сдвиг вправо
    delta < 0 => сдвиг влево
    """
    out = np.zeros_like(x)
    if delta == 0:
        out[:] = x
        return out

    if delta > 0:
        out[delta:] = x[:-delta]
    else:
        d = -delta
        out[:-d] = x[d:]
    return out


def _noise_envelope_for_speech(target_len: int, speech_start: int, speech_end: int) -> np.ndarray:
    """
    Делает маску для low-noise:
    - вне речи: 1.0 (шум полностью)
    - под речью: LOW_NOISE_UNDER_SPEECH_RATIO (шум приглушён)
    + плавные переходы на краях речи (NOISE_EDGE_OVERLAP_MS)
    """
    # ratio + джиттер
    base_under = float(LOW_NOISE_UNDER_SPEECH_RATIO)
    if LOW_NOISE_UNDER_SPEECH_JITTER > 0:
        base_under = max(0.0, min(1.0, base_under + random.uniform(-LOW_NOISE_UNDER_SPEECH_JITTER, LOW_NOISE_UNDER_SPEECH_JITTER)))

    env = np.ones(target_len, dtype=np.float32)

    s = max(0, min(target_len, int(speech_start)))
    e = max(0, min(target_len, int(speech_end)))
    if e > s:
        env[s:e] = base_under

        overlap = int(round(SR * (NOISE_EDGE_OVERLAP_MS / 1000.0)))
        overlap = max(1, overlap)
        overlap = min(overlap, (e - s) // 2) if (e - s) >= 2 else 0

        if overlap > 0:
            env[s:s + overlap] = np.linspace(1.0, base_under, overlap, endpoint=True, dtype=np.float32)
            env[e - overlap:e] = np.linspace(base_under, 1.0, overlap, endpoint=True, dtype=np.float32)

    return env


def make_2s_vad_shifted(y: np.ndarray, speech_bounds, duration=DURATION) -> np.ndarray:
    """
    Главная функция: делает ровно 2 секунды и безопасно сдвигает фразу внутри окна.

    Важно:
    - если исходник НЕ 2 секунды, сначала приводим его к 2 секундам так,
      чтобы речь точно попала внутрь (crop/pad вокруг речи)
    - затем делаем "внутренний" сдвиг в пределах delta_min..delta_max,
      чтобы речь не обрезалась
    - добавляем low-noise фон по твоей логике (как для TTS)
    """
    target_len = int(SR * duration)
    y = np.asarray(y, dtype=np.float32)

    if speech_bounds is None:
        # fallback на старое поведение
        return adjust_length(y, duration=duration, mode=crop_mode)

    speech_start, speech_end = speech_bounds

    # --- Шаг 1: гарантируем окно ровно 2 сек и переносим границы речи в это окно ---
    if len(y) > target_len:
        # выбираем crop так, чтобы [speech_start..speech_end] гарантированно влезало
        min_ws = max(0, speech_end - target_len)
        max_ws = min(speech_start, len(y) - target_len)

        if min_ws <= max_ws:
            ws = random.randint(int(min_ws), int(max_ws))
        else:
            # если вдруг границы странные — fallback на центр
            ws = max(0, min((len(y) - target_len) // 2, len(y) - target_len))

        y2 = y[ws:ws + target_len]
        ss = speech_start - ws
        se = speech_end - ws

    elif len(y) < target_len:
        pad_total = target_len - len(y)
        # Здесь можно сразу рандомно разместить клип (это уже даёт разнообразие)
        pad_left = random.randint(0, pad_total)
        y2 = np.zeros(target_len, dtype=np.float32)
        y2[pad_left:pad_left + len(y)] = y
        ss = speech_start + pad_left
        se = speech_end + pad_left

    else:
        y2 = y
        ss, se = speech_start, speech_end

    # --- Шаг 2: безопасный внутренний сдвиг ---
    # Хотим: 0 <= ss + delta  и  se + delta <= target_len
    delta_min = -int(ss)
    delta_max = target_len - int(se)

    if delta_min > delta_max:
        # речи "некуда двигаться" (например, она почти на весь клип)
        delta = 0
    else:
        delta = random.randint(delta_min, delta_max)

    if DEBUG_VAD_SHIFT:
        ms_min = int(round(delta_min * 1000 / SR))
        ms_max = int(round(delta_max * 1000 / SR))
        ms_chosen = int(round(delta * 1000 / SR))
        print(f"[VAD] shift range: {ms_min}..{ms_max} ms, chosen: {ms_chosen} ms")

    y_shift = _shift_with_zeros(y2, delta)
    ss2 = int(ss + delta)
    se2 = int(se + delta)

    # --- Шаг 3: добавляем low-noise фон (как в твоём TTS-паддинге) ---
    base_rms = estimate_background_rms(y_shift, sr=SR)
    target_rms = max(base_rms / LOW_NOISE_MULTIPLE_VOLUME_DOWN, PAD_NOISE_RMS_FLOOR)

    noise_full = get_low_noise_segment(target_len, target_rms=target_rms).astype(np.float32)
    env = _noise_envelope_for_speech(target_len, ss2, se2)

    out = y_shift + noise_full * env
    return out


# =============================
# 11) ОСНОВНАЯ АУГМЕНТАЦИЯ
# =============================

def augment_and_save(original_path, file_id, output_dir, negative_dir):
    global crop_mode
    created_count = 0

    y, _ = librosa.load(original_path, sr=SR)
    base_name = os.path.splitext(os.path.basename(original_path))[0]

    # Лёгкая нормализация без trim (важно для VAD-сдвига)
    y = y.astype(np.float32)
    y = y - float(np.mean(y))            # убрать DC
    y = librosa.util.normalize(y)        # норм по пику, тишина останется тишиной

    speech_bounds = vad_get_phrase_bounds(y, sr=SR) if USE_SILERO_VAD else None

    passes = int(AGGRESSIVE_NOISE_PASSES) if 'AGGRESSIVE_NOISE_PASSES' in globals() else 1
    if passes < 1:
        passes = 1

    # ----- Original -----
    y_base = make_2s_vad_shifted(y, speech_bounds, duration=DURATION)
    y_base, _ = apply_random_volume(y_base)
    sf.write(os.path.join(output_dir, f"{base_name}_orig_{file_id}.wav"), y_base, SR)
    created_count += 1

    # ----- Pitch only -----
    for shift in PITCH_SHIFTS:
        y_shift = apply_pitch_shift(y, shift)
        # границы по времени не меняются (pitch не растягивает), поэтому speech_bounds те же
        y_shift = make_2s_vad_shifted(y_shift, speech_bounds, duration=DURATION)
        y_shift, _ = apply_random_volume(y_shift)
        sf.write(os.path.join(output_dir, f"{base_name}_pitch{shift}_{file_id}.wav"), y_shift, SR)
        created_count += 1

    # ----- Reverb only -----
    y_rev = make_2s_vad_shifted(y, speech_bounds, duration=DURATION)
    y_rev, ir_tag = apply_reverb(y_rev)
    y_rev, _ = apply_random_volume(y_rev)
    sf.write(os.path.join(output_dir, f"{base_name}_reverb_{ir_tag}_{file_id}.wav"), y_rev, SR)
    created_count += 1

    # ----- Noise only (агрессивный шум) -----
    for lvl in AGGRESSIVE_NOISE_MULTIPLE_VOLUME_DOWNS:
        lvl_tag = str(lvl).replace('.', 'p')

        for pass_idx in range(1, passes + 1):
            y_base_noise = make_2s_vad_shifted(y, speech_bounds, duration=DURATION)
            y_noise, noise_seg = add_aggressive_noise(y_base_noise, volume_down_factor=lvl, return_noise=True)

            y_noise, factor = apply_random_volume(y_noise)
            noise_seg, _ = apply_random_volume(noise_seg, factor=factor)

            sf.write(
                os.path.join(output_dir, f"{base_name}_noise_lvl{lvl_tag}_p{pass_idx}_{file_id}.wav"),
                y_noise, SR
            )
            sf.write(
                os.path.join(
                    negative_dir,
                    f"{base_name}_NEG_noise_lvl{lvl_tag}_p{pass_idx}_{file_id}.wav"
                ),
                noise_seg, SR
            )
            created_count += 1

    # ----- Pitch + reverb -----
    for shift in PITCH_SHIFTS:
        y_pr = apply_pitch_shift(y, shift)
        y_pr = make_2s_vad_shifted(y_pr, speech_bounds, duration=DURATION)
        y_pr, ir_tag = apply_reverb(y_pr)
        y_pr, _ = apply_random_volume(y_pr)

        sf.write(
            os.path.join(output_dir, f"{base_name}_pitch{shift}_reverb_{ir_tag}_{file_id}.wav"),
            y_pr, SR
        )
        created_count += 1

    # ----- Pitch + aggressive noise -----
    for shift in PITCH_SHIFTS:
        for lvl in AGGRESSIVE_NOISE_MULTIPLE_VOLUME_DOWNS:
            lvl_tag = str(lvl).replace('.', 'p')

            for pass_idx in range(1, passes + 1):
                y_pn_base = apply_pitch_shift(y, shift)
                y_pn_base = make_2s_vad_shifted(y_pn_base, speech_bounds, duration=DURATION)
                y_pn, noise_seg = add_aggressive_noise(y_pn_base, volume_down_factor=lvl, return_noise=True)

                y_pn, factor = apply_random_volume(y_pn)
                noise_seg, _ = apply_random_volume(noise_seg, factor=factor)

                sf.write(
                    os.path.join(
                        output_dir,
                        f"{base_name}_pitch{shift}_noise_lvl{lvl_tag}_p{pass_idx}_{file_id}.wav"
                    ),
                    y_pn, SR
                )

                sf.write(
                    os.path.join(
                        negative_dir,
                        f"{base_name}_NEG_pitch{shift}_noise_lvl{lvl_tag}_p{pass_idx}_{file_id}.wav"
                    ),
                    noise_seg, SR
                )
                created_count += 1

    return created_count



# =====================================
# 12) ОЦЕНКА РАЗМЕРА ДАТАСЕТА ДО ЗАПУСКА
# =====================================

def _format_hh_mm(total_seconds: float) -> str:
    """Красивый вывод длительности: 'X ч Y мин'."""
    total_seconds = int(round(total_seconds))
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours} ч {minutes} мин"


def estimate_dataset_size(num_originals: int, duration_sec: float = DURATION):
    """
    Оценивает:
    - сколько файлов получится (позитив/негатив)
    - суммарную длительность аудио в секундах и в формате 'ч/мин'

    Учитывает:
    - количество pitch вариантов
    - количество уровней агрессивного шума
    - количество прогонов AGGRESSIVE_NOISE_PASSES
    """
    p = len(PITCH_SHIFTS)
    n = len(AGGRESSIVE_NOISE_MULTIPLE_VOLUME_DOWNS)
    k = int(AGGRESSIVE_NOISE_PASSES) if 'AGGRESSIVE_NOISE_PASSES' in globals() else 1
    if k < 1:
        k = 1

    # Позитивы на 1 исходник:
    # orig: 1
    # pitch: p
    # reverb: 1
    # noise-only: n*k
    # pitch+reverb: p
    # pitch+noise: p*n*k
    positives_per_file = 1 + p + 1 + (n * k) + p + (p * n * k)

    # Негативы (чистый шум) на 1 исходник:
    # noise-only: n*k
    # pitch+noise: p*n*k
    negatives_per_file = (n * k) + (p * n * k)

    total_positives = num_originals * positives_per_file
    total_negatives = num_originals * negatives_per_file

    total_pos_seconds = total_positives * duration_sec
    total_neg_seconds = total_negatives * duration_sec

    return {
        "num_originals": num_originals,
        "positives_per_file": positives_per_file,
        "negatives_per_file": negatives_per_file,
        "total_positives": total_positives,
        "total_negatives": total_negatives,
        "total_pos_time_str": _format_hh_mm(total_pos_seconds),
        "total_neg_time_str": _format_hh_mm(total_neg_seconds),
        "total_pos_seconds": total_pos_seconds,
        "total_neg_seconds": total_neg_seconds,
    }


# =============================
# 13) MAIN
# =============================

if __name__ == "__main__":
    # 0) Шумы/NoisePool должны быть загружены выше один раз.

    # 1) Собираем позитивы по всем папкам
    datasets = []
    total_originals = 0

    for input_dir in INPUT_DIRS:
        if not os.path.isdir(input_dir):
            print(f"[WARN] Папка не найдена, пропуск: {input_dir}")
            continue

        files = collect_positive_files(input_dir, ALLOWED_EXTENSIONS, recursive=POSITIVE_RECURSIVE)
        print(f"\n=== DATASET: {input_dir}")
        print(f"Найдено {len(files)} оригинальных файлов.")
        total_originals += len(files)

        stats = estimate_dataset_size(len(files), duration_sec=DURATION)
        print("=== Оценка итогового датасета ===")
        print(f"Позитивов на 1 исходник: {stats['positives_per_file']}")
        print(f"Негативов на 1 исходник: {stats['negatives_per_file']}")
        print(f"Итого позитивов: {stats['total_positives']} файлов")
        print(f"Итого негативов: {stats['total_negatives']} файлов")
        print(f"Суммарная длительность позитивов: {stats['total_pos_time_str']}")
        print(f"Суммарная длительность негативов: {stats['total_neg_time_str']}")
        print("=================================")

        datasets.append((input_dir, files))

    if not datasets:
        print("Нет валидных папок/файлов для обработки.")
        exit(0)

    # 2) Один общий запрос подтверждения
    print(f"\nБудет обработано папок: {len(datasets)} | всего исходников: {total_originals}")
    while True:
        user_input = input("Продолжить генерацию? (y/n): ").strip().lower()
        if user_input in ("y", "yes", "д", "да"):
            print("Запуск аугментации...\n")
            break
        elif user_input in ("n", "no", "н", "нет"):
            print("Операция отменена пользователем.")
            exit(0)
        else:
            print("Введите 'y' (да) или 'n' (нет).")

    # 3) Обрабатываем каждую папку отдельно, создавая AUGMENTS внутри неё
    for input_dir, files in datasets:
        aug_root, output_dir, neg_dir = setup_aug_dirs(input_dir)

        print(f"\n--- PROCESS: {input_dir}")
        print(f"OUTPUT_DIR: {output_dir}")
        print(f"NEG_DIR   : {neg_dir}")

        total_created = 0
        for idx, file_path in enumerate(tqdm(files, desc=os.path.basename(input_dir)), start=1):
            created = augment_and_save(file_path, file_id=idx, output_dir=output_dir, negative_dir=neg_dir)
            total_created += created

        print(f"Готово для: {input_dir}")
        print(f"Создано {total_created} файлов в {output_dir}")
        print(f"NEG-шумы лежат в {neg_dir}")

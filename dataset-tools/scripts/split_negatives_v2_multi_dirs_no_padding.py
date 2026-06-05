
"""
Split negative audio into fixed-length segments WITHOUT zero-padding.

Why:
- Your current splitter pads the last chunk with zeros if the remainder is >50% of a segment.
  That produces unnatural "silence tails" on spectrograms. Better to DROP the tail
  (or optionally pad with noise, but default here is drop).

Features:
- Multiple input directories (INPUT_DIRS)
- Optional recursive scan
- Central vs near output structure (like your augmentation script)
- Drops last incomplete segment by default (DROP_LAST=True)

Output structure:
- OUTPUT_MODE="near":
    <neg_dir>/NEG_SPLIT/<dataset_name>/
- OUTPUT_MODE="central":
    <CENTRAL_OUTPUT_ROOT>/<dataset_name>/

Inside each dataset folder:
    negative_2s/   (2-second clips)

Notes:
- librosa.load is used for broad codec support (mp3/m4a/aac...), but it's slower.
  If most of your negatives are WAV/FLAC/OGG, we can switch to SoundFile streaming.
"""

import os
import glob
import random
import hashlib
from datetime import datetime

import numpy as np
import librosa
import soundfile as sf
from tqdm import tqdm

# =============================
# CONFIG
# =============================

SR = 16000
SEGMENT_SEC = 2.0

# Negatives: multiple source folders
INPUT_DIRS = [
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_negative\bitovie",
    # r"...",
]

INPUT_RECURSIVE = True  # True => walk subfolders
AUDIO_EXTS = (".wav", ".mp3", ".flac", ".aac", ".m4a", ".ogg")

# Save mode
OUTPUT_MODE = "central"  # "near" or "central"
CENTRAL_OUTPUT_ROOT = r"E:\LABS_VOLGU\WakeWord_Neiro\data\NEG_SPLITS"

# Behaviour
DROP_LAST = True         # True => drop last chunk if < full segment
MIN_LAST_RATIO = 1.0     # used only if DROP_LAST=False (e.g. 0.75)
RANDOM_SEED = 42

# Optional: limit segments to keep dataset size under control
# 0 => no limit
MAX_SEGMENTS_PER_FILE = 0

# =============================
# UTILS
# =============================

def dataset_folder_name(input_dir: str) -> str:
    base = os.path.basename(os.path.normpath(input_dir))
    h = hashlib.md5(input_dir.encode("utf-8")).hexdigest()[:8]
    return f"{base}__{h}"

def collect_audio_files(input_dir: str, recursive: bool) -> list[str]:
    files = []
    if recursive:
        for dirpath, _, filenames in os.walk(input_dir):
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in AUDIO_EXTS:
                    files.append(os.path.join(dirpath, fn))
    else:
        for ext in AUDIO_EXTS:
            files.extend(glob.glob(os.path.join(input_dir, f"*{ext}")))
    return sorted(set(files))

def setup_out_dir(input_dir: str) -> str:
    ds = dataset_folder_name(input_dir)
    if OUTPUT_MODE == "near":
        root = os.path.join(input_dir, "NEG_SPLIT", ds)
    elif OUTPUT_MODE == "central":
        root = os.path.join(CENTRAL_OUTPUT_ROOT, ds)
    else:
        raise ValueError("OUTPUT_MODE must be 'near' or 'central'")
    out_dir = os.path.join(root, "negative_2s")
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def split_file_to_segments(path: str, out_dir: str) -> int:
    """Return number of segments written."""
    try:
        y, _ = librosa.load(path, sr=SR, mono=True)
        if y is None or len(y) == 0:
            return 0

        seg_len = int(round(SR * SEGMENT_SEC))
        total = len(y)
        full = total // seg_len
        remainder = total % seg_len

        base = os.path.splitext(os.path.basename(path))[0]
        created = 0

        # Sequential full segments
        for i in range(full):
            if MAX_SEGMENTS_PER_FILE and created >= MAX_SEGMENTS_PER_FILE:
                break
            s = i * seg_len
            seg = y[s:s+seg_len].astype(np.float32)
            ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            out = os.path.join(out_dir, f"{base}_part{i+1}_{ts}.wav")
            sf.write(out, seg, SR, subtype="PCM_16")
            created += 1

        # Tail
        if not DROP_LAST and remainder > 0 and (not MAX_SEGMENTS_PER_FILE or created < MAX_SEGMENTS_PER_FILE):
            if remainder >= int(seg_len * MIN_LAST_RATIO):
                seg = y[full * seg_len:].astype(np.float32)
                # pad (only if user explicitly decided to keep)
                if len(seg) < seg_len:
                    seg = np.pad(seg, (0, seg_len - len(seg)), mode="constant")
                ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                out = os.path.join(out_dir, f"{base}_part{full+1}_{ts}.wav")
                sf.write(out, seg, SR, subtype="PCM_16")
                created += 1

        return created
    except Exception as e:
        print(f"[ERR] {path}: {e}")
        return 0

def main():
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    total_files = 0
    total_segments = 0

    for d in INPUT_DIRS:
        if not os.path.isdir(d):
            print(f"[WARN] dir not found: {d}")
            continue

        files = collect_audio_files(d, recursive=INPUT_RECURSIVE)
        print(f"\n=== NEG DIR: {d}")
        print(f"Found files: {len(files)}")

        out_dir = setup_out_dir(d)
        print(f"Output dir: {out_dir}")

        total_files += len(files)

        for p in tqdm(files, desc=os.path.basename(d)):
            total_segments += split_file_to_segments(p, out_dir)

    print("\nDone.")
    print("Total input files:", total_files)
    print("Total segments written:", total_segments)
    print("DROP_LAST:", DROP_LAST, "| MAX_SEGMENTS_PER_FILE:", MAX_SEGMENTS_PER_FILE)

if __name__ == "__main__":
    main()

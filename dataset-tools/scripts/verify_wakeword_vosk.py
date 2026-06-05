"""
verify_wakeword_vosk_ide.py

Проверяет итоговые аугментированные файлы через Vosk:
- Если распознал слово "Афина" (в тексте или в word-list), печатает PASS + имя файла
- Иначе печатает FAIL + имя файла
- В конце — статистика.

Запуск из IDE:
- Укажите DEFAULT_* переменные ниже.
- Запустите скрипт из IDE.

Зависимости:
pip install vosk librosa soundfile tqdm
"""

import os
import json
from typing import Tuple, List, Optional

import numpy as np
import librosa
from tqdm import tqdm
from vosk import Model, KaldiRecognizer


# =========================================================
# НАСТРОЙКИ ПО УМОЛЧАНИЮ (под запуск из IDE)
# =========================================================

# Укажите тот же INPUT_DIR, что используется в основном скрипте.
DEFAULT_INPUT_DIR = r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_positive\TTS_VOICE_timeBad\TEST"

# Папка с итоговыми позитивными аугментациями.
DEFAULT_AUG_ROOT = os.path.join(DEFAULT_INPUT_DIR, "AUGMENTS")
DEFAULT_VERIFY_DIR = os.path.join(DEFAULT_AUG_ROOT, "positive_augments")

# Путь к распакованной модели Vosk (папка!)
# Пример: r"E:\models\vosk-model-small-ru-0.22"
DEFAULT_VOSK_MODEL_DIR = r"C:\Users\Admin123\Downloads\vosk-model-ru-0.42"

# Что ищем
DEFAULT_KEYWORD = "афина"

# Аудио настройки
DEFAULT_SR = 16000
DEFAULT_EXTS = (".wav", ".mp3")
DEFAULT_RECURSIVE = True

# Параметры проверки
DEFAULT_PRINT_TEXT = True      # печатать распознанный текст
DEFAULT_MIN_CONF = None        # например 0.5 если хочешь отсеивать сомнительные
DEFAULT_USE_GRAMMAR = True     # "узкая грамматика" под keyword spotting (часто помогает)


# =========================================================
# УТИЛИТЫ
# =========================================================

def normalize_text_ru(s: str) -> str:
    """Нормализация: нижний регистр, ё->е, схлопывание пробелов."""
    s = (s or "").lower().replace("ё", "е")
    return " ".join(s.split())


def load_audio_16k_mono(path: str, sr: int = 16000) -> np.ndarray:
    """Загрузка в mono float32 + ресемпл к 16k."""
    y, _ = librosa.load(path, sr=sr, mono=True)
    y = y.astype(np.float32)
    return np.clip(y, -1.0, 1.0)


def float_to_pcm16_bytes(y: np.ndarray) -> bytes:
    """float [-1..1] -> PCM16 bytes (формат, который ждёт Vosk)."""
    pcm16 = (y * 32767.0).astype(np.int16)
    return pcm16.tobytes()


def recognize_with_vosk(
    model: Model,
    y: np.ndarray,
    sr: int = 16000,
    words: bool = True,
    grammar_json: Optional[str] = None
):
    """
    Распознавание одним файлом.
    Возвращает:
      full_text (str), words_list (list), raw_final (dict)
    """
    if grammar_json:
        rec = KaldiRecognizer(model, sr, grammar_json)
    else:
        rec = KaldiRecognizer(model, sr)

    rec.SetWords(words)

    pcm = float_to_pcm16_bytes(y)

    # Кормим кусками: 4000 сэмплов ~= 0.25 сек при 16k
    chunk_samples = 4000
    chunk_bytes = chunk_samples * 2

    for i in range(0, len(pcm), chunk_bytes):
        rec.AcceptWaveform(pcm[i:i + chunk_bytes])

    final = json.loads(rec.FinalResult())
    full_text = normalize_text_ru(final.get("text", ""))

    # Когда words=True — обычно есть final["result"] = [{word, conf, ...}, ...]
    words_list = final.get("result", [])
    if not isinstance(words_list, list):
        words_list = []

    return full_text, words_list, final


def check_keyword_in_result(
    keyword: str,
    full_text: str,
    words_list: List[dict],
    min_conf: Optional[float] = None
) -> bool:
    """
    Проверка наличия keyword:
    - если есть список слов (words_list), ищем точное совпадение word == keyword
      и (опционально) conf >= min_conf
    - иначе ищем keyword как подстроку в full_text
    """
    kw = normalize_text_ru(keyword)

    if words_list:
        for w in words_list:
            word = normalize_text_ru(w.get("word", ""))
            conf = w.get("conf", None)
            if word == kw:
                if min_conf is None:
                    return True
                if isinstance(conf, (int, float)) and conf >= min_conf:
                    return True
        return False

    return kw in full_text


def iter_audio_files(root: str, exts: Tuple[str, ...], recursive: bool = True):
    """Генератор аудио-файлов по расширениям."""
    exts = tuple(e.lower() for e in exts)

    if recursive:
        for dirpath, _, filenames in os.walk(root):
            for fn in filenames:
                if os.path.splitext(fn)[1].lower() in exts:
                    yield os.path.join(dirpath, fn)
    else:
        for fn in os.listdir(root):
            path = os.path.join(root, fn)
            if os.path.isfile(path) and os.path.splitext(fn)[1].lower() in exts:
                yield path


# =========================================================
# MAIN (для IDE)
# =========================================================

def main():
    verify_dir = DEFAULT_VERIFY_DIR
    model_dir = DEFAULT_VOSK_MODEL_DIR
    keyword = DEFAULT_KEYWORD
    sr = DEFAULT_SR
    exts = DEFAULT_EXTS
    recursive = DEFAULT_RECURSIVE
    print_text = DEFAULT_PRINT_TEXT
    min_conf = DEFAULT_MIN_CONF
    use_grammar = DEFAULT_USE_GRAMMAR

    if not os.path.isdir(verify_dir):
        raise RuntimeError(f"Папка с аугментациями не найдена: {verify_dir}")

    if not os.path.isdir(model_dir):
        raise RuntimeError(f"Папка модели Vosk не найдена: {model_dir}")

    print(f"VERIFY_DIR: {verify_dir}")
    print(f"VOSK_MODEL: {model_dir}")
    print(f"KEYWORD   : {keyword}")
    print(f"SR        : {sr}")
    print(f"EXTS      : {exts}")
    print(f"RECURSIVE : {recursive}")
    print(f"GRAMMAR   : {use_grammar}")
    print("")

    print("Loading Vosk model...")
    model = Model(model_dir)

    files = list(iter_audio_files(verify_dir, exts=exts, recursive=recursive))
    if not files:
        raise RuntimeError("Файлы не найдены. Проверь путь и расширения.")

    # Узкая грамматика (keyword spotting). Обычно помогает именно для "проверки слова".
    grammar_json = None
    if use_grammar:
        # Можно расширить список вариантами, если надо:
        # grammar_json = json.dumps(["афина", "афину", "афиной", "[unk]"], ensure_ascii=False)
        grammar_json = json.dumps([normalize_text_ru(keyword), "[unk]"], ensure_ascii=False)

    passed = 0
    failed = 0
    errors = 0

    print(f"Found {len(files)} files. Start...\n")

    for path in tqdm(files, desc="Verifying"):
        rel = os.path.relpath(path, verify_dir)
        try:
            y = load_audio_16k_mono(path, sr=sr)
            full_text, words_list, _raw = recognize_with_vosk(
                model, y, sr=sr, words=True, grammar_json=grammar_json
            )

            ok = check_keyword_in_result(keyword, full_text, words_list, min_conf=min_conf)

            if ok:
                passed += 1
                status = "PASS"
            else:
                failed += 1
                status = "FAIL"

            if print_text:
                print(f"{status}: {rel} | text='{full_text}'")
            else:
                print(f"{status}: {rel}")

        except Exception as e:
            errors += 1
            print(f"ERROR: {rel} | {type(e).__name__}: {e}")

    print("\n========== SUMMARY ==========")
    print(f"Total : {len(files)}")
    print(f"PASS  : {passed}")
    print(f"FAIL  : {failed}")
    print(f"ERROR : {errors}")
    print("=============================\n")


if __name__ == "__main__":
    main()

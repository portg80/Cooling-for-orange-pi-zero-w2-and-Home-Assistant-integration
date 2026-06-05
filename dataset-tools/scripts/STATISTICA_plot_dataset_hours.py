#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
plot_dataset_hours.py

Строит статистику по уже НАРЕЗАННЫМ датасетам (обычно по 2 секунды) и рисует диаграммы
в ОДНОМ окне matplotlib (одна Figure, несколько Subplot):

1) Позитивы (AGUMENTATIONS) — вклад по категориям (в часах)
2) Негативы (NEGATIVES_BALANCED) — вклад по категориям (в часах)
3) Сравнение суммарных часов: базовые позитивы, аугментированные позитивы и негативы

По умолчанию считает, что один файл = один сегмент фиксированной длины SEGMENT_SEC.

Ожидаемая структура:
- BASE_DATA_DIR = E:\LABS_VOLGU\WakeWord_Neiro\data
- NEGATIVES_BALANCED\<Категория>\*.wav (и подпапки)
- AGUMENTATIONS\<Категория или Dataset>\positive_augments\*.wav
  (если папки positive_augments нет — считаем любые аудио внутри папки, кроме служебных/NEG)

Запуск:
    python plot_dataset_hours.py

Опции:
    python plot_dataset_hours.py --segment-sec 2
    python plot_dataset_hours.py --no-save       (не сохранять PNG, только окна matplotlib)
    python plot_dataset_hours.py --no-show       (не показывать окна, только сохранить PNG)

Важно про окна matplotlib:
- Если запускаешь из обычного терминала/PowerShell на Windows — окна откроются.
- В headless окружении (без GUI) окна не появятся (тогда используй --no-show и смотри PNG).
"""

import os
import csv
import argparse
from pathlib import Path
from typing import Dict, Iterable, Tuple, List, Optional

import matplotlib.pyplot as plt


# =============================
# НАСТРОЙКИ ПО УМОЛЧАНИЮ
# =============================

BASE_DATA_DIR_DEFAULT = r"E:\LABS_VOLGU\WakeWord_Neiro\data"

NEG_ROOT_NAME = "NEGATIVES_BALANCED"
POS_ROOT_NAME = "AGUMENTATIONS"

# Длительность одного сегмента (сек)
SEGMENT_SEC_DEFAULT = 2.0
BASE_POSITIVE_HOURS_DEFAULT = 38.0 / 60.0

# Какие расширения считать "аудио"
AUDIO_EXTS = {".wav", ".flac", ".ogg", ".mp3"}

# Что игнорировать в выходных папках (служебное)
IGNORE_DIR_NAMES = {
    "_cache_meta",
    "_cache_noise_meta",
    "_dataset_stats",
    "__pycache__",
}

# В агументациях игнорируем папки с NEG шумами, если случайно попадутся
POS_EXCLUDE_DIR_KEYWORDS = {
    "aggressive_noise_used_for_negative",
    "negative",
    "neg",
}

# Куда сохранять png/csv отчёт (по умолчанию рядом с data)
DEFAULT_OUT_DIR_NAME = "_dataset_stats"

PLOT_AXIS_LABEL_FONTSIZE = 16
PLOT_VALUE_LABEL_FONTSIZE = 13
PLOT_TICK_FONTSIZE = 13

POSITIVE_CATEGORY_LABELS = {
    "MY_3_mic__e8a7f576": "Мои записи\n3 микрофона",
    "Elizaveta_NoiseRedux_volume_minus20db__9b52b398": "Елизавета",
    "MAMA_NoiseRedux_volume_minus20db__2daa986a": "Ольга",
    "MY_one_mic__489b75b7": "Мои записи\nодин микрофон",
    "TTS_VOICE_timeBad__eeac3c12": "TTS генерация",
    "MAXIM_volume_minus20db__e76664d8": "Максим",
    "PAPA_NoiseRedux_volume_minus20db__369b25ab": "Андрей",
    "IGOREK_SAVINOV__9e24f891": "Игорь",
    "MY_VOICE_volgu_na_pare__f61a9a99": "Мои записи\nв шумном месте",
}

NEGATIVE_CATEGORY_LABELS = {
    "podcasts_youtube": "YouTube\nПодкасты",
    "music_mix": "Музыка",
    "NEGATIVE_SPEAKERS_AUGMENTATION": "Негативы\nотрезки\nот позитивов",
    "pdsounds_march2009": "pdsounds\nнабор",
    "BbItovie": "Бытовые",
    "randomSound": "Разные",
}


# =============================
# УТИЛИТЫ
# =============================

def is_audio_file(p: Path) -> bool:
    return p.is_file() and (p.suffix.lower() in AUDIO_EXTS)


def count_audio_files(
    root: Path,
    exclude_dir_names: Iterable[str] = (),
    exclude_dir_keywords: Iterable[str] = (),
) -> int:
    """Считает аудиофайлы рекурсивно."""
    if not root.exists():
        return 0

    exclude_dir_names = set(str(x) for x in exclude_dir_names)
    exclude_dir_keywords = set(str(x).lower() for x in exclude_dir_keywords)

    total = 0
    for dp, dirnames, filenames in os.walk(root):
        # вырезаем исключаемые папки на уровне os.walk (ускорение)
        new_dirnames = []
        for d in dirnames:
            if d in exclude_dir_names:
                continue
            d_low = d.lower()
            if any(k in d_low for k in exclude_dir_keywords):
                continue
            new_dirnames.append(d)
        dirnames[:] = new_dirnames

        # если сам путь содержит keyword — пропускаем
        dp_low = str(dp).lower()
        if any(k in dp_low for k in exclude_dir_keywords):
            continue

        for fn in filenames:
            if Path(fn).suffix.lower() in AUDIO_EXTS:
                total += 1
    return total


def seconds_to_hours(sec: float) -> float:
    return float(sec) / 3600.0


def sort_dict_by_value_desc(d: Dict[str, float]) -> List[Tuple[str, float]]:
    return sorted(d.items(), key=lambda kv: kv[1], reverse=True)


# =============================
# ПЛОТЫ (ОДНО ОКНО)
# =============================

def _annotate_bars(ax, bars, values, fmt: str = "{:.2f}"):
    """Пишет точные значения над столбцами."""
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
            fontsize=PLOT_VALUE_LABEL_FONTSIZE,
        )


def _plot_category_bars(
    ax,
    hours_by_cat: Dict[str, float],
    title: str,
    color: str,
    label_map: Optional[Dict[str, str]] = None,
    x_label_rotation: int = 0,
    x_label_ha: str = "center",
):
    if not hours_by_cat:
        ax.set_title(title)
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return

    items = sort_dict_by_value_desc(hours_by_cat)
    labels = [(label_map or {}).get(k, k) for k, _ in items]
    values = [v for _, v in items]

    bars = ax.bar(labels, values, color=color)
    ax.set_title(title)
    ax.set_ylabel("Часы", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax.tick_params(axis="x", labelrotation=x_label_rotation, labelsize=PLOT_TICK_FONTSIZE)
    ax.tick_params(axis="y", labelsize=PLOT_TICK_FONTSIZE)
    for tick in ax.get_xticklabels():
        tick.set_ha(x_label_ha)

    max_v = max(values) if values else 0.0
    ax.set_ylim(0.0, max_v * 1.12 + 1e-9)
    _annotate_bars(ax, bars, values, fmt="{:.3f} ч")


def save_category_plot(
    hours_by_cat: Dict[str, float],
    title: str,
    color: str,
    out_png: Path,
    label_map: Optional[Dict[str, str]] = None,
    x_label_rotation: int = 0,
    x_label_ha: str = "center",
):
    fig, ax = plt.subplots(figsize=(12, 7))
    _plot_category_bars(
        ax,
        hours_by_cat,
        title,
        color=color,
        label_map=label_map,
        x_label_rotation=x_label_rotation,
        x_label_ha=x_label_ha,
    )
    fig.tight_layout()
    fig.savefig(out_png, dpi=170)
    plt.close(fig)


def save_totals_plot(base_pos_h: float, total_pos_h: float, total_neg_h: float, out_png: Path):
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(
        ["Базовые\nпозитивы", "Аугментированные\nпозитивы", "Негативы"],
        [base_pos_h, total_pos_h, total_neg_h],
        color=["tab:cyan", "tab:blue", "tab:orange"],
    )
    ax.set_title("Сравнение суммарных часов по этапам подготовки датасета")
    ax.set_ylabel("Часы", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax.tick_params(axis="x", labelsize=PLOT_TICK_FONTSIZE)
    ax.tick_params(axis="y", labelsize=PLOT_TICK_FONTSIZE)
    max_v = max(base_pos_h, total_pos_h, total_neg_h, 0.0)
    ax.set_ylim(0.0, max_v * 1.15 + 1e-9)
    _annotate_bars(ax, bars, [base_pos_h, total_pos_h, total_neg_h], fmt="{:.3f} ч")
    fig.tight_layout()
    fig.savefig(out_png, dpi=170)
    plt.close(fig)


def plot_all_in_one(
    pos_hours: Dict[str, float],
    neg_hours: Dict[str, float],
    total_pos_h: float,
    total_neg_h: float,
    out_png: Path,
    save: bool,
):
    # Подгоняем размер фигуры под количество категорий, чтобы подписи читались.
    n_pos = len(pos_hours)
    n_neg = len(neg_hours)
    max_cats = max(n_pos, n_neg, 1)

    fig_h = max(10.0, min(22.0, 8.0 + max_cats * 0.18))
    fig_w = max(12.0, min(24.0, 10.0 + max_cats * 0.20))

    fig, axes = plt.subplots(1, 3, figsize=(fig_w, fig_h))
    ax_pos, ax_neg, ax_tot = axes

    # Разные цвета — по просьбе.
    _plot_category_bars(
        ax_pos,
        pos_hours,
        "Позитивы: вклад категорий (часы)",
        color="tab:blue",
        label_map=POSITIVE_CATEGORY_LABELS,
        x_label_rotation=45,
        x_label_ha="right",
    )
    _plot_category_bars(
        ax_neg,
        neg_hours,
        "Негативы: вклад категорий (часы)",
        color="tab:orange",
        label_map=NEGATIVE_CATEGORY_LABELS,
    )

    bars = ax_tot.bar(
        ["Позитивы", "Негативы"],
        [total_pos_h, total_neg_h],
        color=["tab:blue", "tab:orange"],
    )
    ax_tot.set_title("Сравнение суммарных часов (позитивы vs негативы)")
    ax_tot.set_ylabel("Часы", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax_tot.tick_params(axis="x", labelsize=PLOT_TICK_FONTSIZE)
    ax_tot.tick_params(axis="y", labelsize=PLOT_TICK_FONTSIZE)
    max_v = max(total_pos_h, total_neg_h, 0.0)
    ax_tot.set_ylim(0.0, max_v * 1.15 + 1e-9)
    _annotate_bars(ax_tot, bars, [total_pos_h, total_neg_h], fmt="{:.3f} ч")

    fig.tight_layout()
    if save:
        fig.savefig(out_png, dpi=170)
    return fig


# =============================
# СКАНИРОВАНИЕ СТРУКТУРЫ
# =============================

def scan_negatives(neg_root: Path) -> Dict[str, int]:
    """NEGATIVES_BALANCED: считаем по 1-му уровню подпапок как "категории"."""
    out: Dict[str, int] = {}
    if not neg_root.exists():
        return out

    for entry in neg_root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name in IGNORE_DIR_NAMES:
            continue
        cnt = count_audio_files(entry, exclude_dir_names=IGNORE_DIR_NAMES)
        if cnt > 0:
            out[entry.name] = cnt
    return out


def scan_positives(pos_root: Path) -> Dict[str, int]:
    """AGUMENTATIONS: positive_augments если есть, иначе всё аудио кроме NEG папок."""
    out: Dict[str, int] = {}
    if not pos_root.exists():
        return out

    for entry in pos_root.iterdir():
        if not entry.is_dir():
            continue
        if entry.name in IGNORE_DIR_NAMES:
            continue

        pos_aug_dir = entry / "positive_augments"
        if pos_aug_dir.is_dir():
            cnt = count_audio_files(pos_aug_dir, exclude_dir_names=IGNORE_DIR_NAMES)
        else:
            cnt = count_audio_files(
                entry,
                exclude_dir_names=IGNORE_DIR_NAMES,
                exclude_dir_keywords=POS_EXCLUDE_DIR_KEYWORDS,
            )

        if cnt > 0:
            out[entry.name] = cnt

    return out


# =============================
# MAIN
# =============================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-data-dir", type=str, default=BASE_DATA_DIR_DEFAULT, help="Корневая папка data")
    ap.add_argument("--segment-sec", type=float, default=SEGMENT_SEC_DEFAULT, help="Длительность одного сегмента (сек)")
    ap.add_argument("--base-positive-hours", type=float, default=BASE_POSITIVE_HOURS_DEFAULT, help="Суммарная длительность базовых позитивов до аугментации (часы)")
    ap.add_argument("--out-dir", type=str, default="", help="Куда сохранить графики/отчёт (по умолчанию <base>/_dataset_stats)")
    ap.add_argument("--no-show", action="store_true", help="Не показывать окна matplotlib")
    ap.add_argument("--no-save", action="store_true", help="Не сохранять PNG (только окна matplotlib)")
    args = ap.parse_args()

    base = Path(args.base_data_dir)
    neg_root = base / NEG_ROOT_NAME
    pos_root = base / POS_ROOT_NAME

    segment_sec = float(args.segment_sec)
    if segment_sec <= 0:
        raise ValueError("segment-sec должен быть > 0")
    base_positive_hours = float(args.base_positive_hours)
    if base_positive_hours < 0:
        raise ValueError("base-positive-hours должен быть >= 0")

    out_dir = Path(args.out_dir) if args.out_dir else (base / DEFAULT_OUT_DIR_NAME)
    out_dir.mkdir(parents=True, exist_ok=True)

    show = not bool(args.no_show)
    save = not bool(args.no_save)

    print("==============================================")
    print("Статистика по датасету (по уже нарезанным файлам)")
    print("==============================================")
    print(f"BASE_DATA_DIR: {base}")
    print(f"NEG_ROOT     : {neg_root}")
    print(f"POS_ROOT     : {pos_root}")
    print(f"SEGMENT_SEC  : {segment_sec}")
    print(f"BASE_POS_H   : {base_positive_hours}")
    print(f"OUT_DIR      : {out_dir}")
    print(f"SHOW_WINDOWS : {show}")
    print(f"SAVE_PNG     : {save}")
    print("")

    # --- сбор ---
    neg_counts = scan_negatives(neg_root)
    pos_counts = scan_positives(pos_root)

    if not neg_counts:
        print("[ПРЕДУПРЕЖДЕНИЕ] Негативы не найдены или пустые.")
    if not pos_counts:
        print("[ПРЕДУПРЕЖДЕНИЕ] Позитивы не найдены или пустые.")

    # --- переводим в часы ---
    neg_hours = {k: seconds_to_hours(v * segment_sec) for k, v in neg_counts.items()}
    pos_hours = {k: seconds_to_hours(v * segment_sec) for k, v in pos_counts.items()}

    total_neg_h = sum(neg_hours.values())
    total_pos_h = sum(pos_hours.values())

    # --- печать краткого отчёта ---
    def print_top(name: str, d: Dict[str, float], n: int = 10):
        print(f"\n{name} (топ {n} по часам):")
        items = sort_dict_by_value_desc(d)
        for k, v in items[:n]:
            print(f" - {k}: {v:.2f} ч")
        if len(items) > n:
            print(f" ... ещё категорий: {len(items) - n}")

    print_top("Позитивы", pos_hours, n=10)
    print_top("Негативы", neg_hours, n=10)

    print("\nИТОГО:")
    print(f" - Позитивы: {total_pos_h:.2f} ч")
    print(f" - Негативы: {total_neg_h:.2f} ч")

    # --- CSV ---
    csv_path = out_dir / "dataset_hours_summary.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["type", "category", "files", "segment_sec", "hours"])
        for cat, cnt in sorted(pos_counts.items()):
            w.writerow(["positive", cat, cnt, segment_sec, pos_hours.get(cat, 0.0)])
        for cat, cnt in sorted(neg_counts.items()):
            w.writerow(["negative", cat, cnt, segment_sec, neg_hours.get(cat, 0.0)])
        w.writerow(["TOTAL", "positives", sum(pos_counts.values()), segment_sec, total_pos_h])
        w.writerow(["TOTAL", "negatives", sum(neg_counts.values()), segment_sec, total_neg_h])

    # --- график (одно окно) ---
    out_png = out_dir / "dataset_hours_all_in_one.png"
    fig = plot_all_in_one(
        pos_hours=pos_hours,
        neg_hours=neg_hours,
        total_pos_h=total_pos_h,
        total_neg_h=total_neg_h,
        out_png=out_png,
        save=save,
    )

    if save:
        print("\nPNG график сохранён в:")
        print(f" - {out_png}")
        positives_png = out_dir / "positives_by_category.png"
        negatives_png = out_dir / "negatives_by_category.png"
        totals_png = out_dir / "totals_pos_vs_neg.png"

        save_category_plot(
            pos_hours,
            "Позитивы: вклад категорий (часы)",
            color="tab:blue",
            out_png=positives_png,
            label_map=POSITIVE_CATEGORY_LABELS,
            x_label_rotation=45,
            x_label_ha="right",
        )
        save_category_plot(
            neg_hours,
            "Негативы: вклад категорий (часы)",
            color="tab:orange",
            out_png=negatives_png,
            label_map=NEGATIVE_CATEGORY_LABELS,
        )
        save_totals_plot(base_positive_hours, total_pos_h, total_neg_h, totals_png)

        print(f" - {positives_png}")
        print(f" - {negatives_png}")
        print(f" - {totals_png}")

    print(f"CSV отчёт: {csv_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)

    print("\nГотово.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Построение MFCC-картинки для НИР на основе реального WAV-файла.

Скрипт использует те же базовые параметры, что и пайплайн обучения wake word:
- sample_rate = 8000 Гц
- fft_size = 400
- window_stride = (400, 200)
- num_filt = 40
- num_coeffs = 40

Скрипт можно запускать двумя способами:

1. Просто из IDE кнопкой Run, без аргументов.
   Тогда будут использованы пути из блока IDE_DEFAULTS.

2. Через аргументы командной строки:
    py -3 generate_mfcc_figure.py ^
        --input-wav "E:\\path\\to\\example.wav" ^
        --output-png "E:\\path\\to\\mfcc_positive_example.png"
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torchaudio
from sonopy import mfcc_spec


DEFAULT_SAMPLE_RATE = 8000
DEFAULT_FFT_SIZE = 400
DEFAULT_WINDOW = 400
DEFAULT_STRIDE = 200
DEFAULT_NUM_FILT = 40
DEFAULT_NUM_COEFFS = 40

PLOT_TITLE_FONTSIZE = 17
PLOT_AXIS_LABEL_FONTSIZE = 15
PLOT_TICK_FONTSIZE = 13
PLOT_COLORBAR_LABEL_FONTSIZE = 15


# =============================
# НАСТРОЙКИ ДЛЯ ЗАПУСКА ИЗ IDE
# =============================

IDE_DEFAULT_INPUT_WAV = Path(
    r"E:\LABS_VOLGU\WakeWord_Neiro\data\v2_RAWS\v2_positive\MY_one_mic\MY_positive_PROD_001.wav"
)
IDE_DEFAULT_OUTPUT_PNG = Path(__file__).resolve().parent / "mfcc_positive_example.png"
IDE_DEFAULT_TITLE = "MFCC-представление аудиофрагмента с ключевым словом"


def load_audio(input_wav: Path, target_sr: int) -> np.ndarray:
    waveform, sr = torchaudio.load(str(input_wav))

    # Если каналов несколько, усредняем до моно.
    if waveform.shape[0] > 1:
        waveform = waveform.mean(dim=0, keepdim=True)

    if sr != target_sr:
        waveform = torchaudio.transforms.Resample(sr, target_sr)(waveform)

    return waveform.squeeze(0).numpy().astype(np.float32)


def compute_mfcc(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    mfcc = mfcc_spec(
        samples,
        sample_rate,
        (DEFAULT_WINDOW, DEFAULT_STRIDE),
        DEFAULT_FFT_SIZE,
        DEFAULT_NUM_FILT,
        DEFAULT_NUM_COEFFS,
    )
    return np.asarray(mfcc, dtype=np.float32)


def normalize_for_plot(mfcc: np.ndarray, mode: str) -> np.ndarray:
    if mode == "none":
        return mfcc

    result = mfcc.astype(np.float32).copy()
    eps = 1e-8

    if mode == "row":
        mean = result.mean(axis=1, keepdims=True)
        std = result.std(axis=1, keepdims=True)
        return (result - mean) / (std + eps)

    if mode == "col":
        mean = result.mean(axis=0, keepdims=True)
        std = result.std(axis=0, keepdims=True)
        return (result - mean) / (std + eps)

    if mode == "both":
        mean = result.mean(axis=1, keepdims=True)
        std = result.std(axis=1, keepdims=True)
        result = (result - mean) / (std + eps)
        mean = result.mean(axis=0, keepdims=True)
        std = result.std(axis=0, keepdims=True)
        return (result - mean) / (std + eps)

    raise ValueError(f"Неизвестный режим нормализации: {mode}")


def make_plot(
    samples: np.ndarray,
    mfcc: np.ndarray,
    output_png: Path,
    title: str | None,
    sample_rate: int,
    drop_first_coeff: bool,
    normalize_mode: str,
) -> None:
    output_png.parent.mkdir(parents=True, exist_ok=True)

    plot_mfcc = normalize_for_plot(mfcc, normalize_mode)
    coeff_offset = 0
    if drop_first_coeff and plot_mfcc.shape[1] > 1:
        plot_mfcc = plot_mfcc[:, 1:]
        coeff_offset = 1

    # Робастный диапазон делает структуру речи заметнее.
    vmin = float(np.percentile(plot_mfcc, 5))
    vmax = float(np.percentile(plot_mfcc, 95))
    if np.isclose(vmin, vmax):
        vmin = float(plot_mfcc.min())
        vmax = float(plot_mfcc.max())

    fig = plt.figure(figsize=(11, 6.6), constrained_layout=False)
    gs = fig.add_gridspec(
        2, 2,
        height_ratios=[1, 4],
        width_ratios=[40, 1],
        hspace=0.38,
        wspace=0.015,
    )

    ax_wave = fig.add_subplot(gs[0, 0])
    ax_mfcc = fig.add_subplot(gs[1, 0], sharex=ax_wave)
    cax = fig.add_subplot(gs[1, 1])

    time_axis = np.arange(len(samples), dtype=np.float32) / float(sample_rate)
    ax_wave.plot(time_axis, samples, color="tab:orange", linewidth=1.0)
    ax_wave.set_xlim(0, time_axis[-1] if len(time_axis) else 0)
    ax_wave.set_ylabel("Амплитуда", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax_wave.set_xlabel("Время, с", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax_wave.grid(alpha=0.25)
    ax_wave.set_title("Форма сигнала", fontsize=PLOT_TITLE_FONTSIZE)
    ax_wave.tick_params(axis="both", labelsize=PLOT_TICK_FONTSIZE)

    # sonopy возвращает матрицу [time, coeff], для картинки удобнее развернуть.
    duration_sec = time_axis[-1] if len(time_axis) else 0.0
    image = ax_mfcc.imshow(
        plot_mfcc.T,
        origin="lower",
        aspect="auto",
        cmap="viridis",
        vmin=vmin,
        vmax=vmax,
        extent=[0, duration_sec, coeff_offset, coeff_offset + plot_mfcc.shape[1]],
    )

    ax_mfcc.set_xlabel("Время, с", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    if coeff_offset == 1:
        ax_mfcc.set_ylabel("Номер MFCC-коэффициента (без 0-го)", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    else:
        ax_mfcc.set_ylabel("Номер MFCC-коэффициента", fontsize=PLOT_AXIS_LABEL_FONTSIZE)
    ax_mfcc.tick_params(axis="both", labelsize=PLOT_TICK_FONTSIZE)

    if title:
        ax_mfcc.set_title(title, fontsize=PLOT_TITLE_FONTSIZE)

    cbar = fig.colorbar(image, cax=cax)
    cbar.set_label("Амплитуда признака", fontsize=PLOT_COLORBAR_LABEL_FONTSIZE)
    cbar.ax.tick_params(labelsize=PLOT_TICK_FONTSIZE)

    fig.subplots_adjust(left=0.10, right=0.90, top=0.94, bottom=0.11, hspace=0.18, wspace=0.15)
    fig.savefig(output_png, dpi=180)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Строит MFCC-картинку для реального аудиофайла."
    )
    parser.add_argument(
        "--input-wav",
        default=str(IDE_DEFAULT_INPUT_WAV),
        help="Путь к входному WAV-файлу.",
    )
    parser.add_argument(
        "--output-png",
        default=str(IDE_DEFAULT_OUTPUT_PNG),
        help="Путь для сохранения PNG.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=DEFAULT_SAMPLE_RATE,
        help="Целевая частота дискретизации.",
    )
    parser.add_argument(
        "--title",
        default=IDE_DEFAULT_TITLE,
        help="Заголовок внутри изображения. Можно передать пустую строку.",
    )
    parser.add_argument(
        "--keep-c0",
        action="store_true",
        help="Оставить нулевой MFCC-коэффициент на картинке.",
    )
    parser.add_argument(
        "--normalize",
        choices=["none", "row", "col", "both"],
        default="both",
        help="Нормализация MFCC только для визуализации.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_wav = Path(args.input_wav)
    output_png = Path(args.output_png)

    if not input_wav.exists():
        raise FileNotFoundError(f"Файл не найден: {input_wav}")

    title = args.title.strip()
    if not title:
        title = None

    samples = load_audio(input_wav, args.sample_rate)
    mfcc = compute_mfcc(samples, args.sample_rate)
    make_plot(
        samples=samples,
        mfcc=mfcc,
        output_png=output_png,
        title=title,
        sample_rate=args.sample_rate,
        drop_first_coeff=not args.keep_c0,
        normalize_mode=args.normalize,
    )

    print(f"MFCC-картинка сохранена: {output_png}")


if __name__ == "__main__":
    main()

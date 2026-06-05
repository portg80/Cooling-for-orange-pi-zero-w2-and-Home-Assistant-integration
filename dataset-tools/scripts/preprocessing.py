import os, glob, random, numpy as np, librosa, soundfile as sf
from tqdm import tqdm
import pickle

SR = 16000
DURATION = 2
N_MFCC = 40

def load_wav(path, sr=SR, duration=DURATION, center=False):
    y, _ = librosa.load(path, sr=sr)
    # центрируем/усекаем или дополняем нулями до DURATION
    target_len = int(sr * duration)
    if len(y) > target_len:
        if center:
            start = (len(y) - target_len) // 2
        else:
            start = random.randint(0, len(y)-target_len)
        y = y[start:start+target_len]
    else:
        y = np.pad(y, (0, max(0, target_len-len(y))))
    return y


def mfcc_of(y, fixed_frames=105):
    """
    Извлекает MFCC и гарантирует фиксированное количество кадров
    """
    # Вычисляем MFCC
    mf = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=N_MFCC, n_fft=512, hop_length=256)

    # ОБЯЗАТЕЛЬНО: фиксируем количество временных кадров
    if mf.shape[1] > fixed_frames:
        # Обрезаем до нужной длины (берем центральную часть)
        start = (mf.shape[1] - fixed_frames) // 2
        mf = mf[:, start:start + fixed_frames]
    elif mf.shape[1] < fixed_frames:
        # Дополняем нулями
        pad_width = fixed_frames - mf.shape[1]
        mf = np.pad(mf, ((0, 0), (0, pad_width)), mode='constant')

    # Нормализация (z-score)
    mf = (mf - np.mean(mf)) / (np.std(mf) + 1e-8)
    return mf

def augment_speed(y, rate):
    # для librosa >= 0.10
    return librosa.effects.time_stretch(y=y, rate=rate)

def add_noise(y, snr_db=10):
    rms = np.sqrt(np.mean(y**2))
    snr = 10**(snr_db/20)
    noise = np.random.normal(0, rms/snr, size=y.shape)
    return y + noise


def build_dataset(positive_dir, negative_dir, out_pickle="dataset.pkl"):
    X, y = [], []

    # Для позитивных - минимальная аугментация (т.к. уже сделана)
    for p in tqdm(glob.glob(os.path.join(positive_dir, "*.wav"))):
        y_sig = load_wav(p, center=True)
        X.append(mfcc_of(y_sig))
        y.append(1)
        # Только 1-2 дополнительные аугментации
        if random.random() < 0.3:  # 30% примеров получают аугментацию
            X.append(mfcc_of(add_noise(y_sig, snr_db=2)))
            y.append(1)

    # Для негативных - больше разнообразия
    for n in tqdm(glob.glob(os.path.join(negative_dir, "*.wav"))):
        y_sig = load_wav(n, center=False)
        X.append(mfcc_of(y_sig))
        y.append(0)

        # Больше аугментаций для негативных
        X.append(mfcc_of(add_noise(y_sig, snr_db=6)))
        y.append(0)
        X.append(mfcc_of(augment_speed(y_sig, 0.9)))
        y.append(0)
        X.append(mfcc_of(augment_speed(y_sig, 1.1)))
        y.append(0)

    X = np.stack(X)  # (N, 40, 105)
    y = np.array(y)
    # shuffle
    idx = np.random.permutation(len(X))
    X, y = X[idx], y[idx]

    with open(out_pickle, "wb") as f:
        pickle.dump((X,y), f)
    print("Saved:", out_pickle)

if __name__ == "__main__":
    positive_dir = "data/positive"  # путь к вашим позитивным wav
    negative_dir = "data/negative"  # путь к негативным wav
    out_pickle = "dataset.pkl"

    # проверим, что папки существуют
    import os
    if not os.path.exists(positive_dir):
        print(f"Папка {positive_dir} не найдена!")
    if not os.path.exists(negative_dir):
        print(f"Папка {negative_dir} не найдена!")

    # вызываем функцию для подготовки данных
    build_dataset(positive_dir, negative_dir, out_pickle)

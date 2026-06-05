import os
import warnings

import torch
import pyaudio
import numpy as np
import time
from silero import silero_tts

# Отключаем ненужные предупреждения
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# === Настройки ===
current_directory = os.getcwd()
path = 'model_tts'
os.makedirs(path, exist_ok=True)

local_file_ru = 'model_tts/v4_ru.pt'
sample_rate = 24000  # 8000, 24000, 48000
speaker = 'kseniya'  # aidar, baya, kseniya, xenia, random
put_accent = True
put_yo = False
device = torch.device('cpu')
torch.set_num_threads(16)
#RuntimeError: Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: gpu

# === Загрузка модели ===
if not os.path.isfile(local_file_ru):
    torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v4_ru.pt', local_file_ru)

model = torch.package.PackageImporter(local_file_ru).load_pickle("tts_models", "model")
torch._C._jit_set_profiling_mode(False)
torch.set_grad_enabled(False)
model.to(device)

# === Инициализация PyAudio ===
p = pyaudio.PyAudio()
output_device_index = None  # можно указать индекс устройства вручную

def speak(text: str):
    # Генерация аудио
    audio = model.apply_tts(
        text=text + "..",
        speaker=speaker,
        sample_rate=sample_rate,
        put_accent=put_accent,
        put_yo=put_yo
    )

    # Преобразуем в numpy массив float32
    audio_np = np.array(audio, dtype=np.float32)

    # Создаем поток для вывода
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=sample_rate,
                    output=True,
                    output_device_index=output_device_index)

    # Воспроизводим
    stream.write(audio_np.tobytes())

    # Ждем окончания
    time.sleep(len(audio_np) / sample_rate)

    # Останавливаем и очищаем
    stream.stop_stream()
    stream.close()
    del audio_np
    del audio


if __name__ == "__main__":
    speak("рассчитай пиццу диаметром тридцать сантиметров за пятьсот рублей")

    # Закрываем PyAudio после всех вызовов
    p.terminate()

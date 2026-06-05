import pyaudio
import threading
import time
import argparse
import numpy as np
import torch
from .neuralnet.dataset import get_featurizer
import signal
import sys
import pygame
from core.audio_lock import mic_lock
import traceback
from collections import deque
import time

class Listener:
    def __init__(self, sample_rate=8000, device_index=None):
        self.chunk = 1024
        self.sample_rate = sample_rate
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=self.sample_rate,
                                  input=True,
                                  input_device_index=device_index,
                                  frames_per_buffer=self.chunk)

    def listen(self, queue):
        print("[DEBUG] Listener started...")
        while True:
            try:
                # Берём lock, чтобы не читать микрофон одновременно с Recognizer
                with mic_lock:
                    data = self.stream.read(self.chunk, exception_on_overflow=False)
                queue.append(data)
                #print(f"[DEBUG] Read chunk, queue size: {len(queue)}")  # дебаг
            except Exception as e:
                print(f"[ERROR in listen] {e}")
            time.sleep(0.01)

    def run(self, queue):
        thread = threading.Thread(target=self.listen, args=(queue,), daemon=False)  # non-daemon!
        thread.start()
        print("\nWake Word Engine is now listening... \n")

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()

class WakeWordEngine:
    def __init__(self, model_file, device_index=None, threshold=0.99):
        self.listener = Listener(sample_rate=8000, device_index=device_index)
        self.model = torch.jit.load(model_file)
        self.model.eval().to('cpu')
        self.featurizer = get_featurizer(sample_rate=8000)
        self.audio_q = []
        self.paused = False
        self.running = True
        self.threshold = float(threshold)

    def predict(self, audio):
        with torch.no_grad():
            if len(audio) == 0:
                return 0
            raw = b''.join(audio)
            waveform = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            waveform = torch.from_numpy(waveform).unsqueeze(0)
            mfcc = self.featurizer(waveform).transpose(1, 2).transpose(0, 1)
            out = self.model(mfcc)

            prob = torch.sigmoid(out).item()
            pred = 1.0 if prob >= self.threshold else 0.0
            #####print(f"[DEBUG] prob={prob:.4f} thr={self.threshold:.3f} pred={pred}")
            return pred

    def inference_loop(self, action):
        print("[DEBUG] Inference loop started...")
        while self.running:
            if self.paused:
                time.sleep(0.1)
                continue

            # Проверяем, не на паузе ли движок
            if not self.paused:
                if len(self.audio_q) >= 15:
                    current = self.audio_q[-15:]
                    pred = self.predict(current)
                    action(pred)

                    time.sleep(0.01)

                    # Расчёт RMS для фронтенда.
                    raw = b''.join(current)
                    waveform = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
                    rms = np.sqrt(np.mean(waveform**2)) / 32768.0
                    audio_levels = [rms]*100

                    # Подготовка состояния для передачи во фронтенд.
                    status = "listening" if not self.paused else "muted"
                    last_text = getattr(action.__self__, "last_text", "")
                    #push_state(status, last_text, audio_levels)

            # При паузе во фронтенд может отправляться muted-состояние.
            #push_state("muted", getattr(action.__self__, "last_text", ""), [0] * 100)

            time.sleep(0.03)

    def run(self, action):
        self.listener.run(self.audio_q)
        thread = threading.Thread(target=self.inference_loop, args=(action,), daemon=False)
        thread.start()

    def pause(self):
        """Поставить на паузу обработку wake word"""
        self.paused = True
        print("[WAKE WORD] [MUTE] Обработка wake word приостановлена")

    def resume(self):
        """Возобновить обработку wake word"""
        try:
            with mic_lock:
                # безопасно перезапустить stream если нужно
                self.listener.stream.stop_stream()
                self.listener.stream.start_stream()
        except Exception:
            pass

        self.audio_q.clear()

        self.paused = False
        print("[WAKE WORD] [LISTENING] Обработка wake word возобновлена")

    def toggle_pause(self):
        self.paused = not self.paused
        state = "[MUTE] Обработка wake word приостановлена" if self.paused else "[UNMUTE] Обработка wake word возобновлена"
        print(f"[WAKEWORD] {state}")

    def is_paused(self):
        """Проверить, находится ли обработка wake word на паузе"""
        return self.paused

    def stop(self):
        """Остановить движок прослушивания wake word"""
        self.running = False
        self.listener.stop()

"""the interface to interact with wakeword model"""
import pyaudio
import threading
import time
import argparse
import numpy as np
import torch
from neuralnet.dataset import get_featurizer
import signal
import sys
import pygame  # добавили pygame
class Listener:
    def __init__(self, sample_rate=8000, device_index=None):  # добавили device_index
        self.chunk = 1024
        self.sample_rate = sample_rate
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=self.sample_rate,
                                  input=True,
                                  input_device_index=device_index,  # вот сюда
                                  frames_per_buffer=self.chunk)

    def listen(self, queue):
        print("[DEBUG] Listener started...")
        while True:
            try:
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
    def __init__(self, model_file, device_index=None):
        self.listener = Listener(sample_rate=8000, device_index=device_index)
        self.model = torch.jit.load(model_file)
        self.model.eval().to('cpu')
        self.featurizer = get_featurizer(sample_rate=8000)
        self.audio_q = []

    def predict(self, audio):
        with torch.no_grad():
            if len(audio) == 0:
                return 0
            raw = b''.join(audio)
            waveform = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            waveform = torch.from_numpy(waveform).unsqueeze(0)
            mfcc = self.featurizer(waveform).transpose(1, 2).transpose(0, 1)
            out = self.model(mfcc)
            pred = torch.round(torch.sigmoid(out))
            #print(f"[DEBUG] Prediction: {pred.item()} (prob: {torch.sigmoid(out).item():.4f})")
            return pred.item()

    def inference_loop(self, action):
        print("[DEBUG] Inference loop started...")
        while True:
            if len(self.audio_q) >= 15:
                current = self.audio_q[-15:]
                pred = self.predict(current)
                action(pred)
            time.sleep(0.03)

    def run(self, action):
        self.listener.run(self.audio_q)
        thread = threading.Thread(target=self.inference_loop, args=(action,), daemon=False)
        thread.start()

class DemoAction:
    def __init__(self, sensitivity=10):
        import os, random
        from os.path import join, realpath

        pygame.mixer.init()
        self.detect_in_row = 0
        self.sensitivity = sensitivity
        self.random = random
        folder = realpath(join(realpath(__file__), '..', '..', '..', 'fun', 'arnold_audio'))
        self.arnold_mp3 = [os.path.join(folder, x) for x in os.listdir(folder) if x.endswith(('.wav', '.mp3'))]

    def __call__(self, prediction):
        if prediction == 1:
            self.detect_in_row += 1
            if self.detect_in_row >= self.sensitivity:
                self.play()
                self.detect_in_row = 0
        else:
            self.detect_in_row = 0

    def play(self):
        if not self.arnold_mp3:
            print("NO ARNOLD FILES!")
            return
        filename = self.random.choice(self.arnold_mp3)
        print("PLAYING WAKEWORD RESPONSE:", filename)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

def signal_handler(sig, frame):
    print("\nStopping... Ctrl+C caught!")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)  # фикс Ctrl+C

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_file', type=str, required=True)
    parser.add_argument('--sensitivity', type=int, default=10)
    parser.add_argument('--mic_index', type=int, default=None, help="Индекс микрофона из mics.py")
    args = parser.parse_args()

    engine = WakeWordEngine(args.model_file, device_index=args.mic_index)
    action = DemoAction(sensitivity=args.sensitivity)
    print("*** SOX НЕ НУЖЕН! Используем pygame. Папка arnold_audio должна быть! ***")
    engine.run(action)

    # Бесконечный цикл в main (чтобы Ctrl+C работал)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped by user")

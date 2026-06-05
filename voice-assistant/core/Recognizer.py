# core/Recognizer.py
import json
import pyaudio
import time
from vosk import Model, KaldiRecognizer
import threading
from core.audio_lock import mic_lock  # <- импорт глобальной блокировки


class Recognizer:
    def __init__(self, model_path="model_stt/model-small", mic_index=7):
        self.model_path = model_path
        self.mic_index = mic_index
        self.model = Model(model_path)
        self._create_recognizer()

        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=16000,
                                  input=True,
                                  input_device_index=self.mic_index,
                                  frames_per_buffer=8000)
        self.stream.start_stream()

        self._stop_event = threading.Event()
        self._cancel_event = threading.Event()

    def _create_recognizer(self):
        self.rec = KaldiRecognizer(self.model, 16000)

    def listen(self):
        """
        Генератор распознавания.
        """
        while not self._stop_event.is_set() and not self._cancel_event.is_set():
            # Проверяем флаги ДО блокировки
            if self._stop_event.is_set() or self._cancel_event.is_set():
                break

            with mic_lock:
                # Проверяем флаги после получения блокировки
                if self._stop_event.is_set() or self._cancel_event.is_set():
                    break

                try:
                    data = self.stream.read(4000, exception_on_overflow=False)
                except Exception as e:
                    print(f"[Recognizer] stream.read error: {e}")
                    break

                if len(data) == 0:
                    continue

                try:
                    accepted = self.rec.AcceptWaveform(data)
                except Exception as e:
                    print(f"[Recognizer] AcceptWaveform error: {e}")
                    break

            # Проверяем флаги после обработки аудио
            if self._stop_event.is_set() or self._cancel_event.is_set():
                break

            if accepted:
                try:
                    result = json.loads(self.rec.Result())
                except Exception as e:
                    print(f"[Recognizer] Result parse error: {e}")
                    continue

                text = result.get("text", "")
                if text:
                    if not self._cancel_event.is_set():
                        yield text
                    else:
                        break  # Выходим при cancel

        # Финальный результат только при stop (мягкая остановка)
        if self._stop_event.is_set() and not self._cancel_event.is_set():
            with mic_lock:
                try:
                    final_result = json.loads(self.rec.FinalResult())
                    text = final_result.get("text", "")
                    if text:
                        yield text
                except Exception as e:
                    print(f"[Recognizer] FinalResult error: {e}")

    def cancel(self):
        """Отменяем текущую команду — не отсылать результат, завершаем прослушивание."""
        self._cancel_event.set()
        # Дополнительно останавливаем stream для гарантии
        try:
            self.stream.stop_stream()
        except:
            pass
        try:
            self._create_recognizer()
        except Exception:
            pass

    def stop_listening(self):
        """Мягкая остановка: отдать то, что есть, и выйти."""
        self._stop_event.set()
        # Дополнительно останавливаем stream для гарантии
        try:
            self.stream.stop_stream()
        except:
            pass

    def reset(self):
        """Сброс состояния для нового прослушивания."""
        self._stop_event.clear()
        self._cancel_event.clear()
        # Перезапускаем stream
        try:
            self.stream.start_stream()
        except:
            pass
        try:
            self._create_recognizer()
        except Exception:
            pass

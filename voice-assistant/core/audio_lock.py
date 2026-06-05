# core/audio_lock.py
import threading

# Глобальная блокировка для доступа к микрофону / Vosk
mic_lock = threading.Lock()

from flask import Flask, render_template
from flask_sock import Sock
import pyaudio
import numpy as np
import json
import threading
import time

app = Flask(__name__)
sock = Sock(app)

# Настройки микрофона
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

clients = set()
running = True

def audio_stream():
    """Фоновый поток чтения микрофона"""
    global running
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    input_device_index=8,
                    frames_per_buffer=CHUNK)
    print("[AUDIO] Микрофон запущен")

    while running:
        data = np.frombuffer(stream.read(CHUNK, exception_on_overflow=False), dtype=np.int16)
        norm = data / 32768.0  # нормализация -1..1
        message = json.dumps(norm.tolist())

        # Рассылаем всем подключённым клиентам
        dead = []
        for ws in clients:
            try:
                ws.send(message)
            except Exception:
                dead.append(ws)
        for d in dead:
            clients.remove(d)

        time.sleep(0.03)

    stream.stop_stream()
    stream.close()
    p.terminate()


@app.route('/')
def index():
    return render_template('index.html')


@sock.route('/ws')
def websocket(ws):
    clients.add(ws)
    print("[WS] Новый клиент подключился")
    try:
        while True:
            ws.receive()  # держим соединение открытым
    except:
        pass
    finally:
        clients.remove(ws)
        print("[WS] Клиент отключился")


if __name__ == '__main__':
    # Запускаем поток записи микрофона
    threading.Thread(target=audio_stream, daemon=True).start()
    print("[SERVER] Flask сервер запущен на http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000)

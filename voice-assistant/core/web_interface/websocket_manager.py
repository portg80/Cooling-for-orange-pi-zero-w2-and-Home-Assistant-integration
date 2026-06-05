# core/web_interface/websocket_manager.py
import json
import threading
from flask_sock import Sock


class WebSocketManager:
    """Менеджер WebSocket соединений с приоритетом на производительность"""

    def __init__(self):
        self.audio_clients = set()
        self.text_clients = set()
        self.sock = None
        self._audio_lock = threading.Lock()
        self._text_lock = threading.Lock()

    def init_app(self, app):
        self.sock = Sock(app)
        self._setup_routes()

    def _setup_routes(self):
        @self.sock.route('/ws/audio')
        def audio_websocket(ws):
            with self._audio_lock:
                self.audio_clients.add(ws)
            print("[WS] Новый аудио-клиент подключился")
            try:
                while True:
                    ws.receive()
            except Exception as e:
                print(f"[WS] Аудио-клиент отключился: {e}")
            finally:
                with self._audio_lock:
                    if ws in self.audio_clients:
                        self.audio_clients.remove(ws)

        @self.sock.route('/ws/text')
        def text_websocket(ws):
            with self._text_lock:
                self.text_clients.add(ws)
            print("[WS] Новый текст-клиент подключился")
            try:
                while True:
                    ws.receive()
            except Exception as e:
                print(f"[WS] Текст-клиент отключился: {e}")
            finally:
                with self._text_lock:
                    if ws in self.text_clients:
                        self.text_clients.remove(ws)

    def broadcast_audio(self, audio_data):
        """Быстрая трансляция аудио данных"""
        message = json.dumps(audio_data)
        self._broadcast_to_clients(self.audio_clients, message, self._audio_lock)

    def broadcast_text(self, text_data):
        """Трансляция текстовых данных"""
        message = json.dumps(text_data)
        self._broadcast_to_clients(self.text_clients, message, self._text_lock)

    def _broadcast_to_clients(self, clients, message, lock):
        """Быстрая трансляция с минимальной блокировкой"""
        disconnected_clients = []

        # Быстро копируем список клиентов для минимизации времени блокировки
        with lock:
            clients_copy = list(clients)

        # Рассылаем без блокировки
        for client in clients_copy:
            try:
                client.send(message)
            except Exception:
                disconnected_clients.append(client)

        # Быстро удаляем отключенных клиентов
        if disconnected_clients:
            with lock:
                for client in disconnected_clients:
                    if client in clients:
                        clients.remove(client)

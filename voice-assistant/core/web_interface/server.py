import time

from flask import Flask, render_template
from .api import AssistantAPI
from .websocket_manager import WebSocketManager
from .audio_stream import AudioStreamService
from flask_cors import CORS   # <- вот это



class WebInterface:
    """Основной класс веб-интерфейса"""

    def __init__(self, assistant, host='0.0.0.0', port=6789):
        self.assistant = assistant
        self.host = host
        self.port = port
        self.app = None
        self.websocket_manager = None
        self.audio_stream = None
        self.api = None

    def initialize(self):
        """Инициализация всех компонентов"""
        self.app = Flask(__name__)

        # разрешаем CORS для API
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})

        self.websocket_manager = WebSocketManager()
        self.audio_stream = AudioStreamService()
        self.api = AssistantAPI(self.assistant)

        # Настройка компонентов
        self._setup_app()

    def _setup_app(self):
        """Настройка Flask приложения"""

        # Инициализация WebSocket
        self.websocket_manager.init_app(self.app)

        # Регистрация API маршрутов
        self.api.register_routes(self.app)

        # Основной маршрут
        @self.app.route('/')
        def index():
            return render_template('index.html')

        # Обработчик аудио данных
        def process_audio_data(audio_data):
            self.websocket_manager.broadcast_audio(audio_data)

        # Запуск аудио потока
        self.audio_stream.start_stream(process_audio_data)

    def send_assistant_response(self, text, response_type="response"):
        """Отправка ответа ассистента в веб-интерфейс"""
        payload = {
            'type': response_type,
            'text': text,
            'timestamp': time.time()
        }
        payload.update(self._build_state_payload())
        self.websocket_manager.broadcast_text(payload)

    def send_recognized_speech(self, text):
        """Отправка распознанной речи"""
        payload = {
            'type': 'recognized_speech',
            'text': text,
            'timestamp': time.time()
        }
        payload.update(self._build_state_payload())
        self.websocket_manager.broadcast_text(payload)

    def _build_state_payload(self):
        """Собираем актуальные состояния ассистента и wakeword"""
        state_vosk = getattr(self.assistant, 'state_assistant_vosk', 'UNKNOWN')

        wakeword_paused = False
        wakeword_active = False
        manual_mute = False

        # пауза wakeword (как у тебя в REST)
        if hasattr(self.assistant, 'wakeword_engine'):
            try:
                wakeword_paused = self.assistant.wakeword_engine.is_paused()
            except Exception:
                pass

        # детальный статус wakeword (как в get_wakeword_status)
        if hasattr(self.assistant, 'get_wakeword_status'):
            try:
                ws = self.assistant.get_wakeword_status()
                wakeword_active = bool(ws.get('wakeword_active', False))
                manual_mute = bool(ws.get('manual_mute', False))
            except Exception:
                pass

        return {
            'state_assistant_vosk': state_vosk,
            'wakeword_paused': wakeword_paused,
            'wakeword_active': wakeword_active,
            'manual_mute': manual_mute,
        }

    def run(self):
        """Запуск веб-сервера"""
        if not self.app:
            self.initialize()

        print(f"[🚀] Flask сервер запущен на http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=False)

    def stop(self):
        """Остановка веб-интерфейса"""
        if self.audio_stream:
            self.audio_stream.stop_stream()
        print("[🛑] Веб-интерфейс остановлен")

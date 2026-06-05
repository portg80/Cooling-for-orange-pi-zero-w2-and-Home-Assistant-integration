import threading
import time
import pygame
import os
from core.Recognizer import Recognizer
from core.Command_manager import CommandManager
from core.NLU.Nlu import NLU
from core.audio_lock import mic_lock
from core.wake_word_ai.WakeWordEngine import WakeWordEngine  # твой wake word код
from core.MQTT_SENDLER_CLASS import MQTT_SENDLER_CLASS  # импорт твоего класса MQTT
import keyboard
from backend.webserver import app, run_ws_server
from core.web_interface.server import WebInterface
from core.SoundPlayer import SoundPlayer
import logging
logging.getLogger('werkzeug').disabled = True


global_assistant = None  # сюда WS будет писать команды


# детектится на Арина и мычание слова Афина, добавить систему логирования исполненых команд в интерфейс Home assistant
# В веб интерфейсе сделать вывод последних используемых команд и инвертированных команд (если включили свет - команду на выключение)
# Детектится на мычание песни артура пирожкова хэй хэй не стесняйся людей давай все будет окей
# громкость добавить звуков и настройку ее
# отмена команды не работает верно, она отменяет и отчищает буфер, но если сказать любое слово он распознаст его хотя дожен быть остановлен!
# так же ошибка на фронте - при нажатии на кнопку активации цвет кнопки и иконка микрофона не меняются, но если сказать голосом триггер тогда иконка отображает что микрофон якобы выключен (да выключен именно модуль WW) а должен остатся так же зеленым чтобы не путать пользователя!
# при нажатии на аватар и выполнении команды следующее нажатие не опять включает ассистента а пытается завершить команду, хотя команду мы не останавливаем преждевременно
# вместо ответа "команда выполнена: {текст запроса}" нужно выводить имя реально запущенной автоматизации!
# реализовать меню с доступными командами, категории команд (многоуровневые) и возможно редактор команд из UI
# чтобы можно было редактировать файлы, открывать, с подсветкой пайтон синтаксиса и тд и они потом перезаписывались на отредактированые
# фронт в гитхаб закинуть
# https://swagger.io/ инструмент для проектирования API а так же есть заглушка вместо сервера для ответов. Так же нужно настроить автоматическую генерацию документации к API
# Рассмотреть внедрение GraphQL (API клиент может выбирать какие поля он хочет получить. Сервер определяет схему, клиент запрашивает нужные данные) https://youtu.be/XaTwnKLQi4A?list=PL6DxKON1uLOFP5_VPhy6BCE7DA0jdzWO5&t=2051   и пример: https://youtu.be/XaTwnKLQi4A?list=PL6DxKON1uLOFP5_VPhy6BCE7DA0jdzWO5&t=2190
# Также в GraphQL есть подписки для получения данных в реальном времени (сделаны поверх вебсокетов)

class VoiceAssistant:
    def __init__(self):
        # 🔧 Настройки
        self.project_root = os.path.dirname(os.path.abspath(__file__))

        self.model_file = os.path.join(self.project_root, "core", "wake_word_ai", "TEST", "afina_reworked_1.ptc")
        # self.model_file = os.path.join(self.project_root, "core", "wake_word_ai", "WW_models", "wakeword21.ptc")
        self.media_dir = os.path.join(self.project_root, "media")
        self.beep_file = os.path.join("system_audio", "beep_say_please.wav")
        self.mic_index = 1  # индекс микрофона
        self.sensitivity = 8  # чувствительность срабатываний
        self.detect_in_row = 0

        #self.active = False  # состояние ассистента
        # 🔇 Флаг ручного отключения прослушивания
        self.manual_mute = False

        # Объект класса MQTT который настраивает подключение к нему в отдельном потоке и позволяет отправлять команды
        # в MQTT топики (Класс: MQTT_SENDLER_CLASS)
        self.mqtt_sendler_class = None

        # 🎧 Инициализация компонентов
        print("[INIT] Загрузка wake word модели...")
        self.wakeword_engine = WakeWordEngine(self.model_file, device_index=self.mic_index)

        print("[INIT] Загрузка Vosk модели...")
        self.recognizer = Recognizer(mic_index=self.mic_index)
        self.sound_player = SoundPlayer(base_dir=self.media_dir)
        # Конвертировать все аудиозаписи в wav
        self.sound_player.batch_convert_folder()

        self.command_manager = CommandManager(assistant=self, sound_player=self.sound_player)
        self.nlu = NLU(self.command_manager.commands)

        # 🔹 Веб-интерфейс
        self.web_interface = WebInterface(self)

        # Поток отслеживающий нажатия клавиатуры
        #threading.Thread(target=self.keyboard_listener, daemon=True).start()


        # 🔊 Инициализация pygame для звука
        pygame.mixer.init()

        # LOCK потоков
        self._lock = threading.Lock()   # 🔹 блокировка для безопасного toggle
        # Состояние: "IDLE", "LISTENING", "CANCELLING"
        self.state_assistant_vosk = "IDLE"
        self.last_cancel_time = 0.0
        self.cancel_debounce = 1  # секунды

    def start(self):
        # 🔹 Запускаем MQTT
        ########################### MQTT ОТРУБИЛ ПОКА #################################self.start_mqtt()
        # 🔹 Присваиваем MQTT всем командам которые нуждаются в доступе к MQTT (имеют атрибут(поле) mqtt_sendler_class)
        for cmd in self.command_manager.commands:
            if hasattr(cmd, "mqtt_sendler_class"):
                cmd.mqtt_sendler_class = self.mqtt_sendler_class

        # Запускаем wake word engine в отдельном потоке
        threading.Thread(target=self.wakeword_engine.run, args=(self.on_wake,), daemon=True).start()

        # 🔹 Запуск веб-интерфейса в отдельном потоке
        web_thread = threading.Thread(target=self.web_interface.run, daemon=True)
        web_thread.start()

        print("======================================")
        print("  ГОЛОСОВОЙ АССИСТЕНТ ЗАПУЩЕН")
        print("  Web интерфейс: http://127.0.0.1:6789")
        print("  Скажи wake word, чтобы активировать...")
        print("======================================")

        # Основной цикл просто живет
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[EXIT] Ассистент остановлен пользователем.")
            self.stop()

    def on_wake(self, prediction):
        """Колбэк, вызывается при обнаружении wake word."""
        # Игнорируем, если уже слушаем или в процессе отмены
        if self.state_assistant_vosk != "IDLE":
            return

        if prediction == 1 and not self.wakeword_engine.is_paused():
            self.detect_in_row += 1
            if self.detect_in_row >= self.sensitivity:
                print("\n[WAKE WORD] Триггер сработал!")
                print(f"\n{prediction=}\n{self.wakeword_engine.is_paused()=}\n{self.detect_in_row=}"
                      f"\n{self.state_assistant_vosk=}")
                self.detect_in_row = 0

                # вынесли запуск прослушивания команды в отдельный метод
                self.activate_listening_command()  # новый универсальный метод
        else:
            self.detect_in_row = 0

    # Публичный метод для внешнего вызова прослушивания
    def activate_listening_command(self):
        """
        🔹 Запускает процесс прослушивания голосовой команды.
        Можно вызвать из других частей проекта (например, по API или MQTT).
        """
        with self._lock:
            if self.state_assistant_vosk != "IDLE":
                print("[INFO] Ассистент уже занят, состояние:", self.state_assistant_vosk)
                return
            self.state_assistant_vosk = "LISTENING"
            print("[LISTEN] Инициализация прослушивания команды...")

        # При старте прослушивания приостанавливаем wakeword
        try:
            if not self.wakeword_engine.is_paused():
                self.wakeword_engine.pause()
        except Exception:
            pass

        threading.Thread(target=self.handle_command, daemon=True).start()

    def toggle_listening_command(self):
        """Переключение состояния прослушивания команды (start/stop)"""
        with self._lock:
            if self.state_assistant_vosk != "IDLE":
                print("[LISTEN] 🔹 Прерывание текущего прослушивания команды")
                self.recognizer.stop_listening()
                # self.state_assistant_vosk = "IDLE" # handle_command сам доведёт состояние до IDLE в блоке finally  #ИЗМЕНЕНО (4)
                return
        # Запуск потока вне lock
        print("[LISTEN] 🔹 Запуск прослушивания команды")
        self.activate_listening_command()

    def handle_command(self):
        """Ожидание и обработка одной команды через Vosk."""
        try:
            #self.play_beep()
            self.sound_player.play_sound(self.beep_file)
            # подготовка recognizer-а
            self.recognizer.reset()
            # немного реинициализируем аудио-поток (если нужно)
            try:
                with mic_lock:
                    # безопасно перезапустить stream если нужно
                    self.recognizer.stream.stop_stream()
                    self.recognizer.stream.start_stream()
            except Exception:
                pass

            # 🔹 Короткая пауза (чтобы отрезать хвост wake word)
            time.sleep(0.5)
            print("[LISTEN] Говорите команду...")

            timeout = time.time() + 7  # максимум 7 секунд ожидания

            for text in self.recognizer.listen():
                if text:
                    print("→", text)
                    # 🔹 ОТПРАВКА распознанного текста в веб-интерфейс
                    self.web_interface.send_recognized_speech(text)

                    cmd, converted_text = self.nlu.best_match(text)
                    if cmd:
                        # 🔹 Если команда требует ответа - отправляем в веб-интерфейс
                        if hasattr(cmd, 'get_response'):
                            response = cmd.get_response()
                            self.web_interface.send_assistant_response(response)

                        cmd.execute(text, converted_text)
                    else:
                        self.web_interface.send_assistant_response("Команда не распознана", "error")
                        print("Команда не распознана.")
                    break  # после первой команды выходим

                if time.time() > timeout:
                    print("[LISTEN] Таймаут ожидания команды.")
                    break
            time.sleep(0.5)  # Даём время "договорить"

        except Exception as e:
            self.web_interface.send_assistant_response(f"Ошибка: {e}", "error")
            print(f"[ERROR] handle_command: {e}")

        finally:
            self.state_assistant_vosk = "IDLE"
            # сбросим эвенты recognizer для следующего раза
            try:
                self.recognizer.reset()
            except Exception:
                pass

            # 🔴 ВАЖНОЕ ИЗМЕНЕНИЕ: возобновляем wakeword ТОЛЬКО если не было ручного отключения
            if not self.manual_mute:
                try:
                    if hasattr(self, 'wakeword_engine') and hasattr(self.wakeword_engine, 'resume'):
                        self.wakeword_engine.resume()
                except Exception:
                    pass
            else:
                print("[STATE] Прослушивание остаётся отключенным (ручной режим)")

            # Гарантированно вернуть всё в режим ожидания
            print("\n[STATE] Возврат в режим ожидания wake word...\n")

    def cancel_listening_command(self):
        now = time.time()
        if now - self.last_cancel_time < self.cancel_debounce:
            print("[CANCEL] Игнорируем повторное нажатие (debounce)")
            return
        self.last_cancel_time = now

        with self._lock:
            if self.state_assistant_vosk == "IDLE":
                print("[LISTEN] Нет активной команды для отмены")
                return

            print("[LISTEN] 🔹 Отмена текущей команды (cancel)")
            self.state_assistant_vosk = "CANCELLING"

            # Берём блокировку микрофона, чтобы убедиться, что никакой поток
            # не читает микрофон при пересоздании recognizer'а
            from core.audio_lock import mic_lock
            with mic_lock:
                try:
                    self.recognizer.cancel()
                except Exception as e:
                    print(f"[CANCEL] recognizer.cancel error: {e}")

                # перезапустим stream безопасно
                try:
                    self.recognizer.stream.stop_stream()
                    self.recognizer.stream.start_stream()
                except Exception:
                    pass

                # reset очистит флаги
                try:
                    self.recognizer.reset()
                except Exception:
                    pass

            # После безопасного сброса — возобновляем wakeword (если он был на паузе)
            try:
                if self.wakeword_engine.is_paused():
                    self.wakeword_engine.resume()
            except Exception:
                pass

            self.state_assistant_vosk = "IDLE"
            print("[STATE] Ассистент готов к новой команде")

    def wakeword_mute(self):
        """Выключает прослушивание wake word (ручной режим)"""
        self.manual_mute = True
        if hasattr(self, 'wakeword_engine') and hasattr(self.wakeword_engine, 'pause'):
            self.wakeword_engine.pause()
            print("[ASSISTANT] Прослушивание отключено вручную")

            # Отправляем статус в веб-интерфейс
            if hasattr(self, 'web_interface'):
                self.web_interface.send_assistant_response("🔇 Режим прослушивания: ОТКЛЮЧЕН", "system")

            # Отправляем MQTT статус
            self._send_wakeword_status("muted")

        return True

    def wakeword_unmute(self):
        """Включает прослушивание wake word (снимает ручной режим)"""
        self.manual_mute = False
        if hasattr(self, 'wakeword_engine') and hasattr(self.wakeword_engine, 'resume'):
            self.wakeword_engine.resume()
            print("[ASSISTANT] Прослушивание включено вручную")

            # Отправляем статус в веб-интерфейс
            if hasattr(self, 'web_interface'):
                self.web_interface.send_assistant_response("🎤 Режим прослушивания: ВКЛЮЧЕН", "system")

            # Отправляем MQTT статус
            self._send_wakeword_status("listening")

        return True

    def wakeword_toggle_mute(self):
        """Переключает состояние прослушивания"""
        if self.manual_mute or (hasattr(self, 'wakeword_engine') and self.wakeword_engine.is_paused()):
            return self.wakeword_unmute()
        else:
            return self.wakeword_mute()

    def get_wakeword_status(self):
        """Возвращает текущий статус прослушивания"""
        status = {
            'wakeword_active': False,
            'manual_mute': self.manual_mute,
            'state_assistant_vosk': self.state_assistant_vosk
        }

        if hasattr(self, 'wakeword_engine') and hasattr(self.wakeword_engine, 'is_paused'):
            status['wakeword_active'] = not self.wakeword_engine.is_paused()

        return status

    def _send_wakeword_status(self, status):
        """Отправляет статус прослушивания через MQTT"""
        try:
            if hasattr(self, 'mqtt_sendler_class') and self.mqtt_sendler_class:
                status_data = {
                    "wakeword_listening_mode": status,
                    "manual_override": self.manual_mute,
                    "timestamp": time.time()
                }

                self.mqtt_sendler_class.publish_data(
                    "assistant/wakeword_listening/status",
                    status_data
                )
                print(f"[ASSISTANT] 📡 MQTT статус отправлен: {status}")

        except Exception as e:
            print(f"[ASSISTANT] ❌ MQTT ошибка: {e}")

    def play_beep(self):
        """Воспроизведение короткого звука активации."""
        try:
            pygame.mixer.music.load(self.beep_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
        except Exception as e:
            print(f"[WARN] Не удалось воспроизвести beep: {e}")

    # 🔹 Метод для отправки ответов ассистента
    def say(self, text):
        """Метод для ответов ассистента (аналог TTS)"""
        print(f"[Ассистент] {text}")
        if hasattr(self, 'web_interface'):
            self.web_interface.send_assistant_response(text)

    def start_mqtt(self):
        """Инициализация и запуск MQTT в отдельном потоке"""
        self.mqtt_sendler_class = MQTT_SENDLER_CLASS()
        mqtt_thread = threading.Thread(target=self.mqtt_sendler_class.mqtt_background_thread, daemon=True)
        mqtt_thread.start()
        print("[MQTT] Сервис запущен")

    #def stop(self):
    #    """Остановить все компоненты ассистента"""
    #    print("[STOP] Остановка голосового ассистента...")
    #    self.wakeword_engine.stop()
    #    self.recognizer.stop_listening()
    #    print("[STOP] Все компоненты остановлены.")

    def keyboard_listener(self):
        """Фоновый поток для управления ассистентом с клавиатуры"""
        print("[KEYBOARD] Нажмите 'M' чтобы включить/выключить микрофон Wake Word")
        while True:
            if keyboard.is_pressed('m'):
                self.wakeword_engine.toggle_pause()
                time.sleep(0.5)  # защита от дребезга клавиши
            if keyboard.is_pressed('l'):
                # клавиша для начала и остановки прослушивания команды (переключение тонгл)
                self.toggle_listening_command()  # 🔹 вызов toggle
                time.sleep(0.5)
            if keyboard.is_pressed('c'):  # например, 'C' для отмены текущей команды
                self.cancel_listening_command()
                time.sleep(0.5)
            time.sleep(0.1)


if __name__ == "__main__":
    assistant = VoiceAssistant()
    global_assistant = assistant  # WS будет использовать эту ссылку

    # Старт ассистента
    assistant.start()

#2 ктрл зед нажать майн и импорт с переменной сверху

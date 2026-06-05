# Архитектура

Afina построена как локальный конвейер обработки голоса с отдельными модулями активации, распознавания речи, сопоставления команды, выполнения действия и пользовательского управления.

## Рабочий цикл

1. `VoiceAssistant` инициализирует wake word модель, Vosk-распознаватель, менеджер команд, NLU-слой, звуковой модуль и веб-интерфейс.
2. `WakeWordEngine` постоянно читает аудиофрагменты с микрофона и выполняет TorchScript-инференс по MFCC-признакам.
3. После нескольких последовательных срабатываний ключевого слова ассистент переходит из `IDLE` в `LISTENING`.
4. Wake word движок ставится на паузу, пока Vosk принимает команду.
5. Распознанный текст отправляется в веб-интерфейс и в слой сопоставления команд.
6. Выбранная команда выполняет локальное действие, HTTP-запрос, MQTT-публикацию или другую интеграцию.
7. Ассистент возвращается в `IDLE`, если прослушивание не было отключено вручную.

## Основные модули

- [main.py](../voice-assistant/main.py) — сборка приложения и управление состояниями.
- [WakeWordEngine.py](../voice-assistant/core/wake_word_ai/WakeWordEngine.py) — аудиослушатель и инференс wake word модели.
- [Recognizer.py](../voice-assistant/core/Recognizer.py) — обёртка над Vosk/Kaldi STT.
- [audio_lock.py](../voice-assistant/core/audio_lock.py) — блокировка доступа к микрофону.
- [Command_manager.py](../voice-assistant/core/Command_manager.py) — поиск и создание команд.
- [Nlu.py](../voice-assistant/core/NLU/Nlu.py) — сопоставление текста с командами.
- [Base_command.py](../voice-assistant/commands/Base_command.py) — базовый класс команды.
- [MQTT_SENDLER_CLASS.py](../voice-assistant/core/MQTT_SENDLER_CLASS.py) — отправка MQTT-сообщений.
- [server.py](../voice-assistant/core/web_interface/server.py) — Flask-сервер.
- [api.py](../voice-assistant/core/web_interface/api.py) — REST-маршруты.

## API

Flask API доступен под префиксом `/api`.

| Endpoint | Method | Назначение |
| --- | --- | --- |
| `/api/voicecore/status-voice-engine` | GET | Статус Vosk и wake word |
| `/api/voicecore/assistant/activate-listening-command` | POST | Ручной запуск прослушивания команды |
| `/api/voicecore/assistant/cancel-listening-command` | POST | Отмена текущей команды |
| `/api/voicecore/assistant/send-text-command` | POST | Выполнение текстовой команды через общий слой команд |
| `/api/voicecore/wakeword/status` | GET | Статус wake word |
| `/api/voicecore/wakeword/toggle-mute` | POST | Переключение mute/unmute |
| `/api/voicecore/wakeword/mute` | POST | Отключение wake word |
| `/api/voicecore/wakeword/unmute` | POST | Включение wake word |
| `/api/avatar/apply-skin` | POST | Экспериментальный маршрут интерфейса |

## Слой команд

Команды лежат в [voice-assistant/commands](../voice-assistant/commands). Каждая команда наследуется от `BaseCommand`, задаёт имя, набор фраз, режим сопоставления и метод `execute`.

Поддерживаются точные фразы, ключевые слова, поиск подстроки и нечёткое сопоставление через NLU-слой.

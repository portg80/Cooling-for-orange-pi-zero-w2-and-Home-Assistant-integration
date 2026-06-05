# Голосовой ассистент

В этой папке находится основной Python-проект Afina.

## Точка входа

```sh
python main.py
```

`main.py` инициализирует:

- детекцию ключевого слова через `core/wake_word_ai/WakeWordEngine.py`;
- офлайн-распознавание речи через `core/Recognizer.py`;
- динамическую загрузку команд через `core/Command_manager.py`;
- сопоставление команд через `core/NLU/Nlu.py`;
- Flask-интерфейс через `core/web_interface/server.py`;
- локальное воспроизведение звуков через `core/SoundPlayer.py`.

## Внешние файлы

Vosk-модель не включена в Git. Её нужно положить сюда:

```text
model_stt/model-small
```

Большие TTS-модели также не включены. Если они нужны для экспериментов, их нужно положить сюда:

```text
core/TTS/model_tts
```

Текущая wake word модель уже включена:

```text
core/wake_word_ai/TEST/afina_reworked_1.ptc
```

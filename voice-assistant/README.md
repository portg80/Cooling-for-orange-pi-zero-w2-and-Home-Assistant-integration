# Голосовой ассистент

Основной Python-проект Afina.

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

## Модели

Для распознавания речи используется Vosk-модель:

```text
model_stt/model-small
```

Для локального синтеза речи используются TTS-веса:

```text
core/TTS/model_tts
```

Wake word модель ассистента:

```text
core/wake_word_ai/TEST/afina_reworked_1.ptc
```

# Быстрый запуск

Этот файл описывает текущий режим запуска для разработки и демонстрации.

## Голосовой ассистент

Откройте папку ассистента:

```sh
cd voice-assistant
```

Создайте окружение Python:

```sh
python -m venv .venv
.venv\Scripts\activate
```

Установите зависимости. Точный набор зависит от ОС и аудиоустройства, но проект использует Vosk, PyAudio, PyTorch, pygame, Flask, Flask-CORS, Flask-Sock, requests, paho-mqtt и вспомогательные NLP-библиотеки.

Добавьте Vosk-модель в папку:

```text
voice-assistant/model_stt/model-small
```

Модель не хранится в Git, потому что это внешний крупный артефакт.

Проверьте индекс микрофона в [main.py](../voice-assistant/main.py):

```python
self.mic_index = 1
```

Проверьте путь к wake word модели:

```python
self.model_file = os.path.join(self.project_root, "core", "wake_word_ai", "TEST", "afina_reworked_1.ptc")
```

Запустите ассистента:

```sh
python main.py
```

Откройте веб-интерфейс:

```text
http://127.0.0.1:6789
```

## Vue-интерфейс

Новый интерфейс лежит в [frontend-vue](../frontend-vue). Он ожидает API ассистента по адресу `http://127.0.0.1:6789/api`.

```sh
cd frontend-vue
npm install
npm run dev
```

Полезные команды:

```sh
npm run build
npm run type-check
npm run lint
```

## Обучение wake word модели

После подготовки датасета можно сгенерировать манифесты и запустить обучение:

```sh
cd wakeword-training/VoiceAssistant/wakeword
python scripts/create_wakeword_jsons.py --zero_label_dir PATH_TO_NEGATIVE --one_label_dir PATH_TO_POSITIVE --save_json_path .
cd neuralnet
python train.py --train_data_json ..\train.json --test_data_json ..\test.json --save_checkpoint_path ..
python optimize_graph.py --model_checkpoint ..\wakeword.pt --save_path ..\WW_models\wakeword.ptc
```

Историческая команда обучения использовала абсолютные Windows-пути. В репозитории лучше использовать относительные пути и локально созданные манифесты.

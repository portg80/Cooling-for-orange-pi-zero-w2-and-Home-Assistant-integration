# Обучение Wake Word

Подсистема wake word определяет ключевое слово «Афина» до запуска более тяжёлого распознавания речи. Модель обучалась как бинарный классификатор: позитивные примеры содержат ключевое слово, негативные примеры содержат речь, музыку, бытовые звуки, городские шумы и другой фон.

## Модель

Архитектура реализована в [model.py](../wakeword-training/VoiceAssistant/wakeword/neuralnet/model.py).

Основные параметры:

- `feature_size`: 40 MFCC-коэффициентов;
- `hidden_size`: 128 по умолчанию;
- `num_layers`: 1;
- `dropout`: 0.1;
- `bidirectional`: false;
- `num_classes`: 1.

Модель нормализует признаки, передаёт последовательность в LSTM и классифицирует итоговое скрытое состояние линейным слоем.

## Признаки

Извлечение признаков реализовано в [dataset.py](../wakeword-training/VoiceAssistant/wakeword/neuralnet/dataset.py).

Пайплайн использует MFCC при частоте `8000 Hz`. Во время обучения применяются `SpecAugment` и `RandomCut`: первый маскирует части частотно-временного представления, второй слегка меняет границы последовательности в батче.

## Обучение

Обучение реализовано в [train.py](../wakeword-training/VoiceAssistant/wakeword/neuralnet/train.py).

Ключевые параметры:

- оптимизатор: `AdamW`;
- функция потерь: `BCEWithLogitsLoss`;
- планировщик: `ReduceLROnPlateau`;
- эпох по умолчанию: `100`;
- batch size по умолчанию: `32`;
- лучший checkpoint сохраняется по точности на тестовой выборке.

Базовая команда обучения для структуры этого репозитория:

```sh
python train.py --train_data_json ..\train.json --test_data_json ..\test.json --save_checkpoint_path ..
```

Полные `train.json` и `test.json` формируются для конкретного локального датасета. Для повторного обучения их нужно сгенерировать командой `create_wakeword_jsons.py`, указав директории с позитивными и негативными аудиофрагментами.

## Оптимизация

[optimize_graph.py](../wakeword-training/VoiceAssistant/wakeword/neuralnet/optimize_graph.py) загружает checkpoint, трассирует модель через `torch.jit.trace` и сохраняет `.ptc` файл для инференса.

Текущая модель ассистента: [afina_reworked_1.ptc](../voice-assistant/core/wake_word_ai/TEST/afina_reworked_1.ptc). Старая модель [wakeword21.ptc](../voice-assistant/core/wake_word_ai/WW_models/wakeword21.ptc) оставлена как справочный артефакт.

## Инференс

Инференс реализован в двух местах:

- [wakeword-training/VoiceAssistant/wakeword/engine.py](../wakeword-training/VoiceAssistant/wakeword/engine.py) — отдельный движок в проекте обучения;
- [voice-assistant/core/wake_word_ai/WakeWordEngine.py](../voice-assistant/core/wake_word_ai/WakeWordEngine.py) — встроенный движок ассистента с pause/resume и блокировкой микрофона.

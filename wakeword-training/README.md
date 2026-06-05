# Обучение Wake Word

Пайплайн обучения модели ключевого слова для Afina.

Ключевые файлы:

- `VoiceAssistant/wakeword/scripts/create_wakeword_jsons.py` — создание JSONL-манифестов.
- `VoiceAssistant/wakeword/neuralnet/model.py` — LSTM-модель.
- `VoiceAssistant/wakeword/neuralnet/dataset.py` — MFCC-признаки и аугментации.
- `VoiceAssistant/wakeword/neuralnet/train.py` — обучение.
- `VoiceAssistant/wakeword/neuralnet/optimize_graph.py` — экспорт TorchScript.
- `VoiceAssistant/wakeword/engine.py` — отдельный движок инференса.

Примеры JSONL-манифестов лежат в `VoiceAssistant/wakeword/manifests`. Полные `train.json` и `test.json` создаются для конкретного локального аудиодатасета через `create_wakeword_jsons.py`.

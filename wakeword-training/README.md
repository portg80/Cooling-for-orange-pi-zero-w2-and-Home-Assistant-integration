# Обучение Wake Word

В этой папке находится пайплайн обучения модели ключевого слова для Afina.

Ключевые файлы:

- `VoiceAssistant/wakeword/scripts/create_wakeword_jsons.py` — создание JSONL-манифестов.
- `VoiceAssistant/wakeword/neuralnet/model.py` — LSTM-модель.
- `VoiceAssistant/wakeword/neuralnet/dataset.py` — MFCC-признаки и аугментации.
- `VoiceAssistant/wakeword/neuralnet/train.py` — обучение.
- `VoiceAssistant/wakeword/neuralnet/optimize_graph.py` — экспорт TorchScript.
- `VoiceAssistant/wakeword/engine.py` — отдельный движок инференса.

Полные локальные манифесты не включены, потому что содержали абсолютные пути и имена исходных файлов. Переносимые примеры лежат в `VoiceAssistant/wakeword/manifests`.

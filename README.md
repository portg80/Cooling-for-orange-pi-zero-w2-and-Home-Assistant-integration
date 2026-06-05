# Afina

Afina — автономный голосовой ассистент для локального управления умным домом, компьютером и внешними интеграциями. Проект разработан как практическая часть дипломной работы по теме локальной обработки голосовых команд и объединяет голосовой ассистент, обучение модели ключевого слова, подготовку датасета, веб-интерфейсы, интеграции с Home Assistant, MQTT, Node-RED, Satisfactory и систему охлаждения Orange Pi.

Afina работает как локальная умная колонка: система ожидает ключевое слово «Афина», распознаёт следующую команду, сопоставляет её с зарегистрированным навыком и отправляет действие в локальный сервис, игровой API, Home Assistant, MQTT-топик или другой маршрут автоматизации.

## Демонстрации

| Сценарий | Что показывает |
| --- | --- |
| Активация по ключевому слову | Локальная нейросетевая модель переводит ассистента в режим приёма команды |
| Выполнение голосовой команды | Vosk STT, сопоставление команды, ответ ассистента и возврат в ожидание |
| Satisfactory как цифровой макет умного дома | Управление светом, группами устройств, цистернами, хранилищами и производственными секциями |
| Адаптивный будильник и транспорт | Node-RED, данные о транспорте, Home Assistant, MQTT и Android intent |
| Веб-интерфейс | Ручная активация, текстовые команды, mute/unmute wake word |
| Охлаждение Orange Pi | PWM-вентилятор, MQTT-телеметрия, панель Home Assistant и оповещения |

## Что реализовано

- Детекция ключевого слова «Афина» локальной PyTorch/TorchScript-моделью.
- Офлайн-распознавание речи через Vosk/Kaldi.
- Модульная система команд на Python.
- Сопоставление команд по точному совпадению, ключевым словам, вхождению и нечёткому совпадению.
- Нормализация чисел из русской речи в числовой формат.
- Flask REST API и WebSocket-интерфейс для управления ассистентом.
- Новый прототип интерфейса на Vue 3, TypeScript, Vite, Pinia, Tailwind CSS и Axios.
- Интеграция с MQTT и Home Assistant.
- Сценарии автоматизации через Node-RED.
- Интеграция с Satisfactory как цифровым клоном устройств умного дома.
- Отдельная система активного охлаждения Orange Pi Zero W2 с PWM-управлением и дашбордом Home Assistant.
- Скрипты записи, предобработки, аугментации, нарезки и анализа датасета для обучения wake word модели.

## Структура репозитория

```text
voice-assistant/                 основной Python-проект ассистента
wakeword-training/               пайплайн обучения и оптимизации wake word модели
dataset-tools/                   скрипты записи, нарезки, аугментации и анализа датасета
frontend-vue/                    новый Vue-интерфейс ассистента
integrations/cooling-orange-pi/  PWM-демон охлаждения и Lovelace YAML
integrations/satisfactory/       Lua-мост для демо в Satisfactory
assets/dataset-stats/            графики и CSV-статистика датасета
assets/wakeword/                 визуализации MFCC
docs/                            документация проекта
```

## Основной ассистент

Точка входа находится в [voice-assistant/main.py](voice-assistant/main.py). При запуске инициализируются wake word движок, Vosk-распознаватель, менеджер команд, NLU-слой, звуковой модуль и веб-интерфейс.

Ключевые файлы:

- [WakeWordEngine.py](voice-assistant/core/wake_word_ai/WakeWordEngine.py) — инференс wake word модели по аудиопотоку.
- [Recognizer.py](voice-assistant/core/Recognizer.py) — локальное распознавание речи через Vosk.
- [Command_manager.py](voice-assistant/core/Command_manager.py) — динамическая загрузка команд.
- [Base_command.py](voice-assistant/commands/Base_command.py) — базовый API команд.
- [api.py](voice-assistant/core/web_interface/api.py) — REST API управления ассистентом.
- [server.py](voice-assistant/core/web_interface/server.py) — Flask-сервер на порту `6789`.

Подробнее: [docs/architecture.md](docs/architecture.md).

## Wake Word

Подсистема wake word обучалась как бинарный классификатор 2-секундных аудиофрагментов. Модель использует 40 MFCC-признаков, LSTM-слой и экспортируется в TorchScript `.ptc` для быстрого локального инференса.

Фактическая последовательность:

1. Подготовка позитивных и негативных фрагментов скриптами из [dataset-tools/scripts](dataset-tools/scripts).
2. Создание JSONL-манифестов через [create_wakeword_jsons.py](wakeword-training/VoiceAssistant/wakeword/scripts/create_wakeword_jsons.py).
3. Обучение через [train.py](wakeword-training/VoiceAssistant/wakeword/neuralnet/train.py).
4. Оптимизация модели через [optimize_graph.py](wakeword-training/VoiceAssistant/wakeword/neuralnet/optimize_graph.py).
5. Использование `.ptc` модели через [engine.py](wakeword-training/VoiceAssistant/wakeword/engine.py) или встроенный движок ассистента.

Модель, используемая ассистентом: [afina_reworked_1.ptc](voice-assistant/core/wake_word_ai/TEST/afina_reworked_1.ptc). Модель [wakeword21.ptc](voice-assistant/core/wake_word_ai/WW_models/wakeword21.ptc) оставлена для сравнения с предыдущей версией.

Подробнее: [docs/wakeword-training.md](docs/wakeword-training.md).

## Датасет

Раздел с датасетом содержит скрипты записи, предобработки, аугментации, нарезки и анализа аудио. Полный аудиодатасет хранится отдельно из-за объёма и состава исходных записей.

Использованные манифесты обучения содержали:

- `31 745` двухсекундных записей;
- `6 961` позитивный пример;
- `24 784` негативных примера;
- примерно `17.6` часа аудио в train/test манифестах.

Отчёты:

- [dataset_hours_summary.csv](assets/dataset-stats/dataset_hours_summary.csv)
- [dataset_hours_all_in_one.png](assets/dataset-stats/dataset_hours_all_in_one.png)
- [totals_pos_vs_neg.png](assets/dataset-stats/totals_pos_vs_neg.png)
- [positives_by_category.png](assets/dataset-stats/positives_by_category.png)
- [negatives_by_category.png](assets/dataset-stats/negatives_by_category.png)
- [mfcc_positive_example.png](assets/wakeword/mfcc_positive_example.png)

Подробнее: [docs/dataset-pipeline.md](docs/dataset-pipeline.md).

## Команды и интеграции

В проекте есть базовые команды и демонстрационные навыки:

- приветствие;
- дата и время;
- статус прослушивания;
- mute/unmute wake word;
- установка будильника через MQTT;
- поиск телефона через MQTT;
- переключение аудиомаршрута Voicemeter;
- управление светом Satisfactory по всем лампам, группе, конкретной лампе, яркости и цвету;
- демонстрационная логика Satisfactory для чтения состояния цистерн, хранилищ и производственных секций;
- пример произвольного навыка с расчётом стоимости пиццы.

Демонстрационные сценарии описаны в [docs/demo-scenarios.md](docs/demo-scenarios.md).

## Веб-интерфейсы

В проекте есть два направления интерфейса:

- `voice-assistant/core/web_interface` — Flask-интерфейс, который запускается вместе с ассистентом на `http://127.0.0.1:6789`.
- `frontend-vue` — новый интерфейс на Vue 3 и TypeScript, который обращается к Flask API по адресу `http://127.0.0.1:6789/api`.

## Быстрый запуск

Минимально:

```sh
cd voice-assistant
python main.py
```

Перед запуском нужно установить Python-зависимости, добавить Vosk-модель в `voice-assistant/model_stt/model-small`, проверить индекс микрофона в `main.py` и убедиться, что путь к `.ptc` модели wake word существует.

Подробно: [docs/quick-start.md](docs/quick-start.md).

## Охлаждение Orange Pi

Исходная инструкция по охлаждению вынесена в [docs/cooling-orange-pi.md](docs/cooling-orange-pi.md). Кодовые артефакты лежат в [integrations/cooling-orange-pi](integrations/cooling-orange-pi):

- [pwm_fan_daemon.py](integrations/cooling-orange-pi/pwm_fan_daemon.py)
- [dashboard-UI_Lovelace.yaml](integrations/cooling-orange-pi/dashboard-UI_Lovelace.yaml)

## Локальные зависимости

Для полного запуска используются внешние модели и локальные данные:

- Vosk STT модель в `voice-assistant/model_stt/model-small`;
- TTS-веса в `voice-assistant/core/TTS/model_tts`;
- полный сырой и аугментированный аудиодатасет для повторного обучения;
- Python virtualenv для ассистента;
- `node_modules` для Vue-интерфейса.

Подробнее: [docs/environment.md](docs/environment.md).

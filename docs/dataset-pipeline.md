# Пайплайн датасета

Полный аудиодатасет не добавлен в Git. В репозитории хранятся скрипты, статистика и визуальные отчёты, по которым можно восстановить процесс подготовки.

## Основные скрипты

Скрипты находятся в [dataset-tools/scripts](../dataset-tools/scripts).

| Скрипт | Назначение |
| --- | --- |
| `record_word_multi.py` | Запись фиксированных wake word примеров сразу с нескольких микрофонов. |
| `more_positive_speakers_modulyator_v5.py` | Аугментация позитивных примеров: выравнивание длительности, VAD-обрезка, pitch shift, reverb, шумы. |
| `select_negatives_balanced_windows_ru_with_existing_and_plan_plot_STATISTIC.py` | Сбалансированная нарезка негативов с учётом уже подготовленных сегментов. |
| `split_audio_files.py` | Нарезка аудио на фиксированные окна. |
| `split_negatives_v2_multi_dirs_no_padding.py` | Подготовка 2-секундных негативных сегментов из нескольких папок. |
| `translit_RU_bukvi_to_ENG.py` | Транслитерация кириллических имён файлов. |
| `convert_all_to_WAV.py` | Конвертация аудио в WAV. |
| `count_hours_audio.py` | Подсчёт длительности аудио. |
| `STATISTICA_plot_dataset_hours.py` | Генерация графиков статистики датасета. |
| `verify_wakeword_vosk.py` | Проверка wake word записей через Vosk. |

Исходная заметка [ОПИСАНИЕ СКРИПТОВ КОТОРЫЕ ТУТ](../dataset-tools/scripts/ОПИСАНИЕ%20СКРИПТОВ%20КОТОРЫЕ%20ТУТ) содержит описание наиболее важных файлов из рабочей папки.

## Статистика

Фактические локальные манифесты обучения содержали:

- `31 745` двухсекундных записей;
- `6 961` позитивный пример;
- `24 784` негативных примера;
- около `17.6` часа аудио.

Расширенная статистика подготовленных данных:

- [dataset_hours_summary.csv](../assets/dataset-stats/dataset_hours_summary.csv);
- [dataset_hours_all_in_one.png](../assets/dataset-stats/dataset_hours_all_in_one.png);
- [totals_pos_vs_neg.png](../assets/dataset-stats/totals_pos_vs_neg.png);
- [positives_by_category.png](../assets/dataset-stats/positives_by_category.png);
- [negatives_by_category.png](../assets/dataset-stats/negatives_by_category.png).

## Публичное хранение данных

Сырые и аугментированные аудиофайлы исключены, потому что они занимают много места и могут содержать личные записи, сторонние источники или локальные имена файлов. Для публикации датасета лучше использовать отдельный архив, облачное хранилище, GitHub Releases или Git LFS после отдельной проверки.

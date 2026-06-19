# Spotify NoSQL Analytics Project

## Overview

Проєкт демонструє повний цикл роботи з музичним датасетом у MongoDB Atlas: завантаження CSV-даних, побудову документоорієнтованої схеми, практичні запити, aggregation pipeline та аналіз індексів через `explain()`.

Код розділений на логічні Python-модулі, а запуск зібраний у `main.py`. MongoDB aggregation-запити та індекси залишені в JS-файлах, бо вони виконуються безпосередньо через `mongosh`.

## Project Structure

```text
.
├── app/
│   ├── config.py              # .env, MONGO_URI, MONGO_USER/MONGO_PASSWORD/MONGO_HOST
│   ├── dnl_dataset.py         # завантаження датасету з Kaggle
│   ├── load_data.py           # завантаження CSV у tracks_raw
│   └── mongo_scripts.py       # запуск JS-скриптів через mongosh
├── scripts/
│   ├── 01_load_data.py        # сумісний entrypoint для першого етапу
│   └── 02_transform.js        # трансформація tracks_raw -> tracks
├── queries/
│   ├── part2_queries.js
│   ├── part3_analytics.js
│   └── part4_indexes.js
├── reports/
│   └── part4_index_report.md  # створюється автоматично після запуску --part4
├── main.py
├── setup_project.sh
├── requirements.txt
├── .env.example
└── notebooks/
    └── spotify_mongodb_project.ipynb
```

## Environment Setup

1. Створити MongoDB Atlas cluster на AWS. Якщо M0 недоступний, для цього проєкту можна використати Flex як мінімальний доступний варіант.
2. У `Database Access` створити database user з паролем.
3. У `Network Access` додати поточний IP або тимчасово `0.0.0.0/0` для розробки.
4. Скопіювати connection string у `.env`.
5. Покласти `kaggle.json` у `~/.kaggle/kaggle.json`, якщо планується завантаження датасету через CLI.

Приклад `.env`:

```env
MONGO_URI=mongodb+srv://spotify_user:encoded_password@cluster1.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1
```

Альтернативно можна не збирати URI вручну:

```env
MONGO_USER=spotify_user
MONGO_PASSWORD=my@pass#123
MONGO_HOST=cluster1.xxxxx.mongodb.net
MONGO_DB=spotify
```

У цьому випадку `app/config.py` закодує спецсимволи в паролі автоматично.

## Setup Script

Скрипт створює virtual environment, перевіряє залежності з `requirements.txt` і встановлює їх лише якщо їх немає або версії не збігаються.

```bash
chmod +x setup_project.sh
./setup_project.sh
```

Щоб одразу скачати датасет:

```bash
./setup_project.sh --download-dataset
```

## Dataset

За замовчуванням використовується Kaggle dataset:

```text
maharshipandya/-spotify-tracks-dataset
```

Модуль для завантаження:

```bash
python main.py --download-dataset
```

Після завантаження файл нормалізується до назви:

```text
dataset.csv
```

## Run Order

Повний запуск:

```bash
python main.py --download-dataset
python main.py --all
```

Або поетапно:

```bash
python main.py --load
python main.py --transform
python main.py --part2
python main.py --part3
python main.py --part4
```

Сумісні команди з окремими файлами:

```bash
python scripts/01_load_data.py
mongosh "$MONGO_URI" --file scripts/02_transform.js
mongosh "$MONGO_URI" --file queries/part2_queries.js
mongosh "$MONGO_URI" --file queries/part3_analytics.js
mongosh "$MONGO_URI" --file queries/part4_indexes.js
```

## Final Document Schema

Після трансформації основна колекція `tracks` має компактну структуру, де бізнесові поля залишені на верхньому рівні, а аудіоознаки згруповані у вкладений об’єкт.

```json
{
  "track_id": "string",
  "track_name": "string",
  "album_name": "string",
  "artists": ["artist 1", "artist 2"],
  "explicit": false,
  "popularity": 65,
  "popularity_tier": "medium",
  "duration_ms": 210000,
  "duration_sec": 210.0,
  "track_genre": "pop",
  "audio_features": {
    "danceability": 0.72,
    "energy": 0.81,
    "loudness": -5.4,
    "speechiness": 0.05,
    "acousticness": 0.12,
    "instrumentalness": 0.0,
    "liveness": 0.15,
    "valence": 0.64,
    "tempo": 120.5,
    "key": 4,
    "mode": 1,
    "time_signature": 4
  }
}
```

## Index Analysis Report

Після виконання:

```bash
python main.py --part4
```

програма автоматично створює окремий файл звіту:

```text
reports/part4_index_report.md
```

У звіті зберігається повний вивід `mongosh` для аналізу індексів, зокрема фактичні значення з `explain()`:

```text
executionTimeMillis
totalKeysExamined
totalDocsExamined
nReturned
winningPlan.stage / inputStage.stage
indexName
```

Саме ці значення показують, чи відбувся перехід від повного перегляду колекції (`COLLSCAN`) до використання індексу (`IXSCAN`). README описує запуск і структуру проєкту, а фактичний результат роботи програми зберігається у файлі звіту.

## Important Operational Notes

- `.env` не потрібно додавати в Git або архів для перевірки, якщо там є реальні паролі.
- Для архіву краще залишити `.env.example`.
- `dataset.csv` можна не включати в архів, якщо він великий; достатньо описати команду завантаження.
- Якщо пароль містить спецсимволи, у `MONGO_URI` їх треба URL-encode або використати змінні `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_HOST`.

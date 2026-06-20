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

## Theory Notes for Parts 1-3

### Part 1: Data Model

Аудіо-характеристики винесені в об'єкт `audio_features`, бо це одна логічна група полів, яка описує звучання треку: `danceability`, `energy`, `tempo`, `valence`, `speechiness`, `instrumentalness` та інші. У такому вигляді документ легше читати, а запити одразу показують намір: наприклад, пошук танцювальних треків використовує `"audio_features.danceability"`, а пошук музики для роботи - `"audio_features.instrumentalness"` і `"audio_features.speechiness"`. Вкладення вигідне, коли поля часто використовуються разом і належать до одного підоб'єкта. Мінус такого підходу в тому, що для індексів і проєкцій потрібно завжди писати повний шлях до поля; якщо вкладеність стане надто глибокою або структура почне часто змінюватися, запити й індекси буде складніше підтримувати.

Виконавці зберігаються як масив `artists`, а не як один рядок, бо один трек може мати кількох виконавців. Масив дозволяє природно шукати треки конкретного артиста, рахувати статистику по кожному артисту через `$unwind`, групувати за виконавцем і не парсити рядок під час кожного запиту. Наприклад, у `queries/part2_queries.js` та `queries/part3_analytics.js` масив `artists` розгортається через `$unwind`, після чого MongoDB може порахувати кількість треків, мінімальну та середню популярність для кожного окремого артиста.

`$out` у `scripts/02_transform.js` використовується для створення фінальної колекції `tracks` з результату aggregation pipeline. Він перезаписує цільову колекцію результатом пайплайна, тому добре підходить для повної повторюваної трансформації `tracks_raw -> tracks`. `$merge` працює інакше: він записує результат у наявну колекцію з правилами оновлення або вставки документів. `$merge` краще використовувати для інкрементальних оновлень, коли потрібно не перескладати всю колекцію, а додати або оновити частину документів.

### Part 2: Query Operators

`$unwind` використовується для розгортання масиву в окремі документи. У цьому проєкті це потрібно для поля `artists`: якщо трек має кількох виконавців, після `$unwind` кожен виконавець бере участь у групуванні окремо. Без `$unwind` статистика рахувалася б для всього масиву як одного значення, а не для конкретного артиста. Саме тому запити "виконавці, у яких усі треки популярні" і "топ-10 виконавців за середньою популярністю" починаються з `{ $unwind: "$artists" }`.

`$stdDevPop` і `$stdDevSamp` обидва рахують стандартне відхилення, але відповідають на різні статистичні питання. `$stdDevPop` використовується, коли поточні дані вважаються всією генеральною сукупністю. У завданні з нетипово швидкими треками ми порівнюємо треки всередині наявного датасету Spotify, тому `$stdDevPop` підходить для порогу `avg_tempo + 2 * std_tempo`. `$stdDevSamp` краще використовувати, коли дані є лише вибіркою з більшої сукупності, і треба оцінити відхилення для ширшої популяції.

### Part 3: Analytics Choices

У запиті топ-10 виконавців фільтр `track_count >= 5` прибирає артистів, для яких середня популярність може бути випадковою через один-два треки. Якщо знизити поріг до `1`, у топ можуть потрапити виконавці з одним дуже популярним треком: середня популярність виглядатиме високою, але висновок буде менш надійним. Якщо підняти поріг до більш ніж `50` треків, залишаться тільки дуже представлені в датасеті артисти; результат стане стабільнішим статистично, але менш різноманітним і може відсікти нішевих виконавців з високою середньою популярністю.

У запиті "найбільш танцювальний жанр" фільтр `track_count >= 100` робить порівняння жанрів стійкішим: середні `avg_danceability`, `avg_energy` і `avg_valence` не залежать від кількох випадкових треків. Якщо знизити поріг до `50`, у результат може потрапити більше жанрів, але частина з них матиме менш надійну середню оцінку. Тобто нижчий поріг підвищує охоплення, а вищий - довіру до порівняння.

## Index Analysis Report

Після виконання:

```bash
python main.py --part4
```

програма автоматично створює окремий файл звіту:

```text
reports/part4_index_report.md
```

У звіті зберігається повний вивід `mongosh` з термінала. Нижче наведені ключові поля з `explain("executionStats")` і висновки.

### Task 4.1: Compound Index for Pop Danceable Tracks

Запит:

```javascript
db.tracks.find({
  track_genre: "pop",
  "audio_features.danceability": { $gte: 0.7 }
}).sort({ popularity: -1 })
```

Індекс:

```javascript
db.tracks.createIndex(
  { track_genre: 1, "audio_features.danceability": 1, popularity: -1 },
  { name: "idx_genre_danceability_popularity" }
)
```

До створення індексу:

```text
executionTimeMillis: 101
totalKeysExamined: 0
totalDocsExamined: 113999
nReturned: 354
winningPlan.stage: SORT
winningPlan.inputStage.stage: COLLSCAN
```

Після створення індексу:

```text
executionTimeMillis: 2
totalKeysExamined: 354
totalDocsExamined: 354
nReturned: 354
winningPlan.stage: FETCH
winningPlan.inputStage.stage: SORT
winningPlan.inputStage.inputStage.stage: IXSCAN
indexName: idx_genre_danceability_popularity
```

Головна зміна: MongoDB перестала читати всю колекцію. До індексу було `COLLSCAN` і `totalDocsExamined: 113999`, тобто сервер переглянув усі документи. Після індексу з'явився `IXSCAN`, а кількість переглянутих ключів і документів стала `354`, що дорівнює кількості повернених документів. Час виконання зменшився зі `101 ms` до `2 ms`. Індекс використовується, бо в плані є `IXSCAN` і вказаний `indexName`.

### Task 4.2: Index for Background Work Search

Запит шукає не-explicit треки з високою інструментальністю та низькою мовленнєвістю:

```javascript
{
  explicit: false,
  "audio_features.instrumentalness": { $gt: 0.5 },
  "audio_features.speechiness": { $lt: 0.1 }
}
```

Індекс:

```javascript
db.tracks.createIndex(
  {
    explicit: 1,
    "audio_features.instrumentalness": 1,
    "audio_features.speechiness": 1
  },
  { name: "idx_work_music_search" }
)
```

Результат `explain()`:

```text
executionTimeMillis: 43
totalKeysExamined: 16602
totalDocsExamined: 16141
nReturned: 16141
winningPlan.stage: FETCH
winningPlan.inputStage.stage: IXSCAN
indexName: idx_work_music_search
```

План підтверджує використання індексу через `IXSCAN` і `indexName: idx_work_music_search`. Поле `explicit` стоїть першим, бо це точний фільтр; далі йдуть числові аудіоознаки з діапазонами. Через те, що запит повертає повні документи, після `IXSCAN` все одно є `FETCH`: MongoDB знаходить кандидатів за індексом, а потім читає самі документи.

### Task 4.3: Covered Query

Початковий запит:

```javascript
db.tracks.find({
  track_genre: "pop",
  popularity: { $gte: 70 }
})
```

Цей запит не є covered query, навіть якщо існує індекс `idx_genre_danceability_popularity`. Причина в тому, що без проєкції MongoDB має повернути повні документи, а повний документ містить поля, яких немає в індексі: `track_name`, `album_name`, `artists`, `explicit`, `duration_ms`, `audio_features.energy` та інші. Через це план має читати документи з колекції.

`explain()` для початкового запиту:

```text
executionTimeMillis: 1
totalKeysExamined: 620
totalDocsExamined: 317
nReturned: 317
winningPlan.stage: FETCH
winningPlan.inputStage.stage: IXSCAN
indexName: idx_genre_danceability_popularity
```

Тут індекс використовується, але запит не покривний, бо `totalDocsExamined: 317` і є стадія `FETCH`.

Кандидат на covered query з проєкцією:

```javascript
db.tracks.find(
  {
    track_genre: "pop",
    popularity: { $gte: 70 }
  },
  {
    _id: 0,
    track_genre: 1,
    popularity: 1,
    "audio_features.danceability": 1
  }
)
```

`explain()` для варіанта з проєкцією:

```text
executionTimeMillis: 1
totalKeysExamined: 620
totalDocsExamined: 0
nReturned: 317
winningPlan.stage: PROJECTION_DEFAULT
winningPlan.inputStage.stage: IXSCAN
indexName: idx_genre_danceability_popularity
```

Цей варіант є покривним за змістом: усі поля фільтра й проєкції входять до індексу `{ track_genre, audio_features.danceability, popularity }`, а `_id` явно виключений. Найважливіший доказ - `totalDocsExamined: 0`: MongoDB змогла відповісти з індексу без читання документів колекції.

## Important Operational Notes

- `.env` не потрібно додавати в Git або архів для перевірки, якщо там є реальні паролі.
- Для архіву краще залишити `.env.example`.
- `dataset.csv` можна не включати в архів, якщо він великий; достатньо описати команду завантаження.
- Якщо пароль містить спецсимволи, у `MONGO_URI` їх треба URL-encode або використати змінні `MONGO_USER`, `MONGO_PASSWORD`, `MONGO_HOST`.

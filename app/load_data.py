import pandas as pd
from pymongo import MongoClient
from tqdm import tqdm

from app.config import AppConfig, load_config


INT_COLS = ["popularity", "duration_ms", "key", "mode", "time_signature"]
FLOAT_COLS = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
]
REQUIRED_COLS = [
    "track_id", "artists", "album_name", "track_name", "popularity", "duration_ms",
    "explicit", "danceability", "energy", "key", "loudness", "mode", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
    "time_signature", "track_genre",
]


def validate_columns(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLS if col not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")


def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["explicit"] = df["explicit"].astype(bool)
    for col in INT_COLS:
        df[col] = df[col].astype(int)
    for col in FLOAT_COLS:
        df[col] = df[col].astype(float)
    return df


def load_raw_tracks(config: AppConfig | None = None) -> int:
    config = config or load_config()
    if not config.dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {config.dataset_path}. Run `python main.py --download-dataset` "
            "or put dataset.csv into the project root."
        )

    client = MongoClient(config.mongo_uri)
    db = client[config.db_name]
    db["tracks_raw"].drop()

    df = pd.read_csv(config.dataset_path)
    validate_columns(df)
    df = normalize_types(df)

    missing_required = df["artists"].isna() | df["track_name"].isna()
    records = df[~missing_required].to_dict("records")

    print(f"Loading {len(records)} tracks into {config.db_name}.tracks_raw...")
    for i in tqdm(range(0, len(records), config.batch_size)):
        db["tracks_raw"].insert_many(records[i : i + config.batch_size])

    count = db["tracks_raw"].count_documents({})
    print(f"Loaded documents: {count}")
    print("Sample document:")
    print(db["tracks_raw"].find_one())
    return count


if __name__ == "__main__":
    load_raw_tracks()

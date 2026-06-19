import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


@dataclass(frozen=True)
class AppConfig:
    mongo_uri: str
    db_name: str = "spotify"
    dataset_path: Path = Path("dataset.csv")
    batch_size: int = 1000


def build_mongo_uri_from_parts() -> str | None:
    """Build a MongoDB URI from MONGO_USER, MONGO_PASSWORD and MONGO_HOST if MONGO_URI is absent."""
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASSWORD")
    host = os.getenv("MONGO_HOST")
    options = os.getenv("MONGO_OPTIONS", "retryWrites=true&w=majority")
    if not (user and password and host):
        return None
    return f"mongodb+srv://{quote_plus(user)}:{quote_plus(password)}@{host}/?{options}"


def load_config() -> AppConfig:
    load_dotenv()
    mongo_uri = os.getenv("MONGO_URI") or build_mongo_uri_from_parts()
    if not mongo_uri:
        raise RuntimeError(
            "MongoDB connection is not configured. Add MONGO_URI to .env or provide "
            "MONGO_USER, MONGO_PASSWORD and MONGO_HOST."
        )
    return AppConfig(
        mongo_uri=mongo_uri,
        db_name=os.getenv("MONGO_DB", "spotify"),
        dataset_path=Path(os.getenv("DATASET_PATH", "dataset.csv")),
        batch_size=int(os.getenv("BATCH_SIZE", "1000")),
    )

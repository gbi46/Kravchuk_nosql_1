import subprocess
from pathlib import Path

from app.config import AppConfig, load_config


def run_mongosh_script(script_path: str | Path, config: AppConfig | None = None) -> None:
    config = config or load_config()
    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    command = ["mongosh", config.mongo_uri, "--file", str(script_path)]
    print("$ mongosh <MONGO_URI> --file " + str(script_path))
    subprocess.run(command, check=True)


def transform_schema(config: AppConfig | None = None) -> None:
    run_mongosh_script("scripts/02_transform.js", config)


def run_part2_queries(config: AppConfig | None = None) -> None:
    run_mongosh_script("queries/part2_queries.js", config)


def run_part3_analytics(config: AppConfig | None = None) -> None:
    run_mongosh_script("queries/part3_analytics.js", config)


def run_part4_indexes(config: AppConfig | None = None) -> None:
    run_mongosh_script("queries/part4_indexes.js", config)

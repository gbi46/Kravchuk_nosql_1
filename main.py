import argparse

from app.config import load_config
from app.dnl_dataset import download_dataset
from app.load_data import load_raw_tracks
from app.mongo_scripts import (
    run_part2_queries,
    run_part3_analytics,
    run_part4_indexes,
    transform_schema,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spotify MongoDB NoSQL project runner")
    parser.add_argument("--download-dataset", action="store_true", help="Download dataset.csv from Kaggle if it is absent")
    parser.add_argument("--force-download", action="store_true", help="Re-download dataset.csv even if it exists")
    parser.add_argument("--load", action="store_true", help="Load dataset.csv into spotify.tracks_raw")
    parser.add_argument("--transform", action="store_true", help="Build spotify.tracks with aggregation pipeline")
    parser.add_argument("--part2", action="store_true", help="Run practical query tasks")
    parser.add_argument("--part3", action="store_true", help="Run analytics aggregation tasks")
    parser.add_argument("--part4", action="store_true", help="Run index and explain tasks")
    parser.add_argument("--all", action="store_true", help="Run load, transform, part2, part3 and part4")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    explicit_action_requested = any(
        [
            args.download_dataset,
            args.load,
            args.transform,
            args.part2,
            args.part3,
            args.part4,
            args.all,
        ]
    )

    # Default behavior: running `python main.py` executes the full project flow.
    # The dataset downloader is safe to call here because it skips downloading
    # when dataset.csv already exists, unless --force-download is provided.
    if not explicit_action_requested:
        args.download_dataset = True
        args.all = True

    # If the user passes only --force-download, treat it as a dataset action.
    if args.force_download and not args.download_dataset:
        args.download_dataset = True

    if args.download_dataset:
        download_dataset(force=args.force_download)

    should_run_db = args.all or args.load or args.transform or args.part2 or args.part3 or args.part4
    config = load_config() if should_run_db else None

    if args.all or args.load:
        load_raw_tracks(config)
    if args.all or args.transform:
        transform_schema(config)
    if args.all or args.part2:
        run_part2_queries(config)
    if args.all or args.part3:
        run_part3_analytics(config)
    if args.all or args.part4:
        run_part4_indexes(config)


if __name__ == "__main__":
    main()

from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path


DATASET_SLUG = "maharshipandya/-spotify-tracks-dataset"
DATASET_CSV = Path("dataset.csv")


def _run(command: list[str]) -> None:
    print("$", " ".join(command))
    subprocess.run(command, check=True)


def _find_latest_zip() -> Path:
    zip_files = sorted(
        Path(".").glob("*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not zip_files:
        raise FileNotFoundError("No Kaggle archive was found after download.")
    return zip_files[0]


def _extract_csv_from_zip(zip_path: Path) -> Path:
    extract_dir = Path("_kaggle_extract")
    extract_dir.mkdir(exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.namelist()
        csv_members = [name for name in members if name.lower().endswith(".csv")]

        if not csv_members:
            print("Archive contents:")
            for name in members:
                print(" -", name)
            raise FileNotFoundError("No CSV file found inside the Kaggle archive.")

        csv_member = csv_members[0]
        archive.extract(csv_member, extract_dir)

    extracted_csv = extract_dir / csv_member

    if not extracted_csv.exists():
        # Handles archives with nested folders more defensively.
        csv_candidates = list(extract_dir.rglob("*.csv"))
        if not csv_candidates:
            raise FileNotFoundError("CSV was listed in the archive but was not extracted.")
        extracted_csv = csv_candidates[0]

    return extracted_csv


def download_dataset(force: bool = False) -> Path:
    if DATASET_CSV.exists() and not force:
        print(f"{DATASET_CSV} already exists. Skipping download.")
        return DATASET_CSV

    for old_zip in Path(".").glob("*.zip"):
        old_zip.unlink()

    _run(["kaggle", "datasets", "download", "-d", DATASET_SLUG, "-p", "."])

    zip_path = _find_latest_zip()
    print(f"Using archive: {zip_path}")

    extracted_csv = _extract_csv_from_zip(zip_path)

    if DATASET_CSV.exists():
        DATASET_CSV.unlink()

    extracted_csv.replace(DATASET_CSV)

    # Optional cleanup.
    zip_path.unlink(missing_ok=True)

    extract_dir = Path("_kaggle_extract")
    if extract_dir.exists():
        for item in sorted(extract_dir.rglob("*"), reverse=True):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                item.rmdir()
        extract_dir.rmdir()

    print(f"Dataset is ready: {DATASET_CSV}")
    return DATASET_CSV

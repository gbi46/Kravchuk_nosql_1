import subprocess
import sys
from datetime import datetime
from pathlib import Path

from app.config import AppConfig, load_config


def run_mongosh_script(
    script_path: str | Path,
    config: AppConfig | None = None,
    report_path: str | Path | None = None,
) -> None:
    config = config or load_config()
    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    command = ["mongosh", config.mongo_uri, "--file", str(script_path)]
    print("$ mongosh <MONGO_URI> --file " + str(script_path))
    if report_path is None:
        subprocess.run(command, check=True)
        return

    result = subprocess.run(command, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)

    write_report(report_path, script_path, result)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            command,
            output=result.stdout,
            stderr=result.stderr,
        )


def write_report(
    report_path: str | Path,
    script_path: Path,
    result: subprocess.CompletedProcess[str],
) -> None:
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    run_time = datetime.now().astimezone().isoformat(timespec="seconds")
    output = result.stdout or "(no stdout)"
    stderr = result.stderr or ""

    report = [
        "# Part 4 Index Analysis Report",
        "",
        f"- Generated at: `{run_time}`",
        f"- Script: `{script_path}`",
        "- Command: `mongosh <MONGO_URI> --file " + str(script_path) + "`",
        f"- Exit code: `{result.returncode}`",
        "",
        "## mongosh stdout",
        "",
        "```text",
        output.rstrip(),
        "```",
    ]
    if stderr:
        report.extend(
            [
                "",
                "## mongosh stderr",
                "",
                "```text",
                stderr.rstrip(),
                "```",
            ]
        )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nReport written to {report_path}")


def transform_schema(config: AppConfig | None = None) -> None:
    run_mongosh_script("scripts/02_transform.js", config)


def run_part2_queries(config: AppConfig | None = None) -> None:
    run_mongosh_script("queries/part2_queries.js", config)


def run_part3_analytics(config: AppConfig | None = None) -> None:
    run_mongosh_script("queries/part3_analytics.js", config)


def run_part4_indexes(config: AppConfig | None = None) -> None:
    run_mongosh_script(
        "queries/part4_indexes.js",
        config,
        report_path="reports/part4_index_report.md",
    )

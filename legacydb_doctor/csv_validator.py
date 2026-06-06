from __future__ import annotations

import csv
from pathlib import Path


MANIFEST_NAME = "_export_manifest.csv"


def count_csv_data_rows(csv_path: Path) -> int:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)

        # Skip header row.
        try:
            next(reader)
        except StopIteration:
            return 0

        return sum(1 for _ in reader)


def parse_manifest_row_count(value: str | None) -> int | None:
    if value is None or value == "":
        return None

    try:
        return int(value)
    except ValueError:
        return None


def validate_csv_export(export_dir: str | Path) -> list[dict]:
    output_dir = Path(export_dir)
    manifest_path = output_dir / MANIFEST_NAME

    results: list[dict] = []

    if not manifest_path.exists():
        return [
            {
                "level": "error",
                "table": None,
                "csv_path": None,
                "message": f"Manifest file not found: {manifest_path}",
            }
        ]

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as manifest_file:
        reader = csv.DictReader(manifest_file)

        required_columns = {"table", "csv_path", "row_count", "status", "error", "export_limit"}
        fieldnames = set(reader.fieldnames or [])

        missing_columns = sorted(required_columns - fieldnames)
        if missing_columns:
            results.append(
                {
                    "level": "error",
                    "table": None,
                    "csv_path": str(manifest_path),
                    "message": f"Manifest is missing required column(s): {', '.join(missing_columns)}",
                }
            )
            return results

        for row in reader:
            table_name = row.get("table")
            status = row.get("status")
            csv_path_raw = row.get("csv_path")
            manifest_row_count = parse_manifest_row_count(row.get("row_count"))

            if status == "ok":
                if not csv_path_raw:
                    results.append(
                        {
                            "level": "error",
                            "table": table_name,
                            "csv_path": None,
                            "message": "Status is ok but csv_path is empty.",
                        }
                    )
                    continue

                csv_path = Path(csv_path_raw)

                if not csv_path.exists():
                    results.append(
                        {
                            "level": "error",
                            "table": table_name,
                            "csv_path": str(csv_path),
                            "message": "CSV file listed in manifest does not exist.",
                        }
                    )
                    continue

                actual_row_count = count_csv_data_rows(csv_path)

                if manifest_row_count != actual_row_count:
                    results.append(
                        {
                            "level": "error",
                            "table": table_name,
                            "csv_path": str(csv_path),
                            "message": (
                                f"Row count mismatch: manifest={manifest_row_count}, "
                                f"actual_csv_rows={actual_row_count}."
                            ),
                        }
                    )
                else:
                    results.append(
                        {
                            "level": "ok",
                            "table": table_name,
                            "csv_path": str(csv_path),
                            "message": f"CSV file exists and row count matches ({actual_row_count}).",
                        }
                    )

            elif status in {"planned", "skipped_empty"}:
                if csv_path_raw:
                    results.append(
                        {
                            "level": "warning",
                            "table": table_name,
                            "csv_path": csv_path_raw,
                            "message": f"Status is {status}, but csv_path is not empty.",
                        }
                    )
                else:
                    results.append(
                        {
                            "level": "ok",
                            "table": table_name,
                            "csv_path": None,
                            "message": f"Status {status} is consistent with no CSV file.",
                        }
                    )

            elif status == "error":
                results.append(
                    {
                        "level": "warning",
                        "table": table_name,
                        "csv_path": csv_path_raw,
                        "message": f"Export error recorded in manifest: {row.get('error')}",
                    }
                )

            else:
                results.append(
                    {
                        "level": "warning",
                        "table": table_name,
                        "csv_path": csv_path_raw,
                        "message": f"Unknown manifest status: {status}",
                    }
                )

    return results
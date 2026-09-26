#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GBIF_SEARCH = "https://api.gbif.org/v1/occurrence/search"
PAGE_LIMIT = 300
USER_AGENT = "BIO-MIMIC-X/10 (+https://github.com/Dr-starck66/bio-mimic-x-discovery-factory)"


def month_shift(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1


def complete_month_windows(count: int, today: date | None = None):
    if count < 1:
        raise ValueError("count must be >= 1")
    today = today or datetime.now(timezone.utc).date()
    current_first = date(today.year, today.month, 1)
    windows = []
    for back in range(count, 0, -1):
        year, month = month_shift(current_first.year, current_first.month, -back)
        start = date(year, month, 1)
        next_year, next_month = month_shift(year, month, 1)
        end = date(next_year, next_month, 1) - timedelta(days=1)
        windows.append((start, end))
    return windows


def bbox_wkt(bbox: dict) -> str:
    west = float(bbox["min_lon"])
    east = float(bbox["max_lon"])
    south = float(bbox["min_lat"])
    north = float(bbox["max_lat"])
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("invalid bbox")
    return (
        f"POLYGON(({west} {south},{east} {south},{east} {north},"
        f"{west} {north},{west} {south}))"
    )


def request_json(url: str, timeout: int = 30, attempts: int = 3):
    last = None
    for attempt in range(attempts):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GBIF request failed after {attempts} attempts: {last}")


def search_url(config: dict, start: date, end: date, offset: int = 0, limit: int = PAGE_LIMIT):
    source = config["source"]
    params = [
        ("geometry", bbox_wkt(config["study_area"]["bbox"])),
        ("occurrenceStatus", "PRESENT"),
        ("hasCoordinate", "true"),
        ("hasGeospatialIssue", "false"),
        ("eventDate", f"{start.isoformat()},{end.isoformat()}"),
        ("limit", str(limit)),
        ("offset", str(offset)),
    ]
    for basis in source.get("basis_of_record", ["HUMAN_OBSERVATION"]):
        params.append(("basisOfRecord", str(basis)))
    if source.get("country"):
        params.append(("country", str(source["country"])))
    return GBIF_SEARCH + "?" + urlencode(params)


def accepted_species_name(record: dict):
    species = record.get("species")
    if species:
        return str(species).strip()
    if str(record.get("taxonRank", "")).upper() == "SPECIES" and record.get("scientificName"):
        return str(record["scientificName"]).strip()
    return None


def aggregate_records(records: list[dict]):
    taxa = Counter()
    ids = []
    dataset_keys = set()
    licenses = set()
    skipped = 0
    for record in records:
        name = accepted_species_name(record)
        if not name:
            skipped += 1
            continue
        taxa[name] += 1
        key = record.get("key") or record.get("gbifID")
        if key is not None:
            ids.append(str(key))
        if record.get("datasetKey"):
            dataset_keys.add(str(record["datasetKey"]))
        if record.get("license"):
            licenses.add(str(record["license"]))
    digest = hashlib.sha256("\n".join(sorted(ids)).encode("utf-8")).hexdigest()
    return {
        "taxa": dict(sorted(taxa.items())),
        "records_used": sum(taxa.values()),
        "records_without_species_resolution": skipped,
        "gbif_id_sha256": digest,
        "gbif_id_examples": sorted(ids)[:25],
        "dataset_keys": sorted(dataset_keys),
        "licenses": sorted(licenses),
    }


def fetch_month(config: dict, start: date, end: date, fetcher=request_json):
    source = config["source"]
    max_records = int(source.get("max_records_per_month", 5000))
    timeout = int(source.get("timeout_seconds", 30))
    delay = float(source.get("request_delay_seconds", 0.05))
    first_url = search_url(config, start, end, 0, PAGE_LIMIT)
    first = fetcher(first_url, timeout=timeout)
    total = int(first.get("count", len(first.get("results", []))))
    if total > max_records:
        raise RuntimeError(
            f"{start:%Y-%m}: GBIF count {total} exceeds max_records_per_month={max_records}; "
            "refusing a truncated ecological series"
        )
    records = list(first.get("results", []))
    offset = len(records)
    while offset < total:
        if delay:
            time.sleep(delay)
        page = fetcher(search_url(config, start, end, offset, PAGE_LIMIT), timeout=timeout)
        batch = list(page.get("results", []))
        if not batch:
            raise RuntimeError(f"{start:%Y-%m}: pagination stopped at {offset}/{total}")
        records.extend(batch)
        offset += len(batch)

    agg = aggregate_records(records)
    query_digest = hashlib.sha256(
        json.dumps(
            {
                "provider": "GBIF",
                "geometry": bbox_wkt(config["study_area"]["bbox"]),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "basis_of_record": source.get("basis_of_record", ["HUMAN_OBSERVATION"]),
                "country": source.get("country"),
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()
    return {
        "time": start.isoformat(),
        "taxa": agg["taxa"],
        "measurement_semantics": "GBIF_OCCURRENCE_RECORD_COUNT_NOT_ABUNDANCE",
        "environment": {},
        "perturbation": None,
        "provenance": {
            "provider": "GBIF",
            "api": GBIF_SEARCH,
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "gbif_query_count": total,
            "records_used": agg["records_used"],
            "records_without_species_resolution": agg["records_without_species_resolution"],
            "query_sha256": query_digest,
            "record_id_sha256": agg["gbif_id_sha256"],
            "gbif_id_examples": agg["gbif_id_examples"],
            "dataset_keys": agg["dataset_keys"],
            "licenses": agg["licenses"],
        },
    }


def build_document(config: dict, fetcher=request_json, today: date | None = None):
    windows = complete_month_windows(int(config["source"].get("lookback_complete_months", 18)), today)
    observations = []
    zero_record_months = []
    for start, end in windows:
        observation = fetch_month(config, start, end, fetcher=fetcher)
        if observation["taxa"]:
            observations.append(observation)
        else:
            zero_record_months.append(start.isoformat())

    minimum = int(config["source"].get("minimum_observation_months", 12))
    if len(observations) < minimum:
        raise RuntimeError(
            f"only {len(observations)} months contain species-resolved observations; minimum={minimum}"
        )

    document = {
        "schema": "biomimic-ecosystem-observations-v2",
        "ecosystem_id": config["ecosystem_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "factory/ecosystem_gbif_ingest.py",
        "source": {
            "provider": "GBIF",
            "api": GBIF_SEARCH,
            "authentication_required": False,
            "basis_of_record": config["source"].get("basis_of_record", ["HUMAN_OBSERVATION"]),
        },
        "study_area": config["study_area"],
        "measurement_semantics": "GBIF_OCCURRENCE_RECORD_COUNT_NOT_ABUNDANCE",
        "sampling_bias_note": (
            "Monthly taxon values are counts of GBIF occurrence records inside the configured observation "
            "window. They are not organism abundance, density, occupancy, or standardized sampling effort."
        ),
        "zero_record_months": zero_record_months,
        "observations": observations,
    }
    fingerprintable = dict(document)
    fingerprintable.pop("generated_at", None)
    document["sha256"] = hashlib.sha256(
        json.dumps(fingerprintable, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="data/ecosystem_sources.json")
    parser.add_argument("--out", default="data/ecosystem_mimic_observations.json")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    document = build_document(config)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "provider": "GBIF",
                "ecosystem_id": document["ecosystem_id"],
                "months": len(document["observations"]),
                "latest_month": document["observations"][-1]["time"],
                "sha256": document["sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""QC-aware OOI Axial Escargot temperature screening, no physical-event attribution.

Run locally after obtaining the actual OOI THREDDS NetCDF4 file (or --download).
No sample statistics are made unless input bytes are read and validated.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import math
from pathlib import Path
from statistics import median
from urllib.request import urlopen

OOI_2026_08_04_FILENAME = (
    "deployment0009_RS03INT1-MJ03C-10-TRHPHA301-streamed-trhph_sample_"
    "20260804T115012.192326-20260804T120152.132220.nc"
)
OOI_SOURCE_URL = (
    "https://thredds.dataexplorer.oceanobservatories.org/thredds/fileServer/"
    "ooigoldcopy/public/RS03INT1-MJ03C-10-TRHPHA301-streamed-trhph_sample/"
    + OOI_2026_08_04_FILENAME
)
NTP_EPOCH = datetime(1900, 1, 1, tzinfo=timezone.utc)
MAX_DOWNLOAD_BYTES = 1_000_000


def screen(times, temperatures, flags, *, sensor="TRHPHA301", threshold=6, min_good=12):
    """Screen non-missing QARTOD pass=1 points. No cross-sensor event claims."""
    if sensor != "TRHPHA301":
        raise ValueError("sensor_not_escargot_301")
    if not (len(times) == len(temperatures) == len(flags)):
        raise ValueError("length_mismatch")
    if not times:
        raise ValueError("empty_series")
    if any(not math.isfinite(float(x)) or float(x) <= 0 for x in times):
        raise ValueError("invalid_time")
    if any(float(b) <= float(a) for a, b in zip(times, times[1:])):
        raise ValueError("timestamps_not_strictly_increasing")

    counts = Counter(int(flag) for flag in flags)
    if set(counts) - {1, 2, 3, 4, 9}:
        raise ValueError("unknown_qartod_flag")
    good = [(i, float(t), float(v)) for i, (t, v, flag) in enumerate(zip(times, temperatures, flags))
            if int(flag) == 1 and math.isfinite(float(v)) and float(v) != -9999999.0]
    result = {
        "sensor": sensor,
        "n_total": len(times),
        "n_qartod_pass_valid": len(good),
        "n_excluded": len(times) - len(good),
        "qartod_counts": {str(x): counts.get(x, 0) for x in (1, 2, 3, 4, 9)},
        "candidate_anomalies": [],
        "physical_event_confirmed": False,
        "interpretation": "QARTOD-screened exploratory candidates only; no vent-event attribution",
    }
    if len(good) < min_good:
        result["status"] = "INSUFFICIENT_QC_PASS_DATA"
        return result
    values = [v for _, _, v in good]
    centre = median(values)
    mad = median([abs(x - centre) for x in values])
    result["median_degc"] = centre
    result["mad_degc"] = mad
    result["n_points_analyzed"] = len(good)
    if mad == 0:
        result["status"] = "INDETERMINATE_ZERO_MAD"
        return result
    robust_scale = 1.4826 * mad
    for i, stamp, value in good:
        robust_z = abs(value - centre) / robust_scale
        if robust_z >= threshold:
            result["candidate_anomalies"].append({
                "sample_index": i,
                "utc": (NTP_EPOCH + timedelta(seconds=stamp)).isoformat(),
                "temperature_degc": value,
                "absolute_robust_z": round(robust_z, 4),
                "not_a_confirmed_event": True,
            })
    diffs = [float(b) - float(a) for a, b in zip(times, times[1:])]
    typical_step = median(diffs) if diffs else 0
    result["median_cadence_seconds"] = typical_step
    result["long_gaps_over_3x_median"] = sum(d > 3 * typical_step for d in diffs) if typical_step else 0
    result["status"] = "SCREEN_COMPLETED_NOT_PHYSICALLY_VALIDATED"
    return result


def analyze_file(path: Path):
    import h5py  # NetCDF4 is HDF5. Intentional: no external data needed in tests.
    if OOI_2026_08_04_FILENAME != path.name:
        raise ValueError("unexpected_data_filename_no_provenance_match")
    header = path.read_bytes()[:8]
    if header != b"\x89HDF\r\n\x1a\n":
        raise ValueError("not_netcdf4_hdf5")
    with h5py.File(path, "r") as ds:
        required = ("time", "vent_fluid_temperature", "vent_fluid_temperature_qartod_results")
        if any(v not in ds for v in required):
            raise ValueError("missing_required_ooi_variables")
        times = ds["time"][:].tolist()
        temp = ds["vent_fluid_temperature"][:].tolist()
        flags = ds["vent_fluid_temperature_qartod_results"][:].tolist()
        if len(times) != 36:
            raise ValueError("expected_observation_count_36_mismatch")
    report = screen(times, temp, flags)
    report["source_url"] = OOI_SOURCE_URL
    report["source_filename"] = OOI_2026_08_04_FILENAME
    report["source_sha256"] = sha256(path.read_bytes()).hexdigest()
    report["input_type"] = "REAL_FILE_BYTES_NOT_SYNTHETIC"
    report["analysis_version"] = "astra.ooi.axial.escargot.v1"
    return report


def download_to(path: Path):
    with urlopen(OOI_SOURCE_URL, timeout=20) as response:
        data = response.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise ValueError("download_exceeds_safe_sample_limit")
    if not data.startswith(b"\x89HDF\r\n\x1a\n"):
        raise ValueError("download_is_not_netcdf4_hdf5")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path(OOI_2026_08_04_FILENAME))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--download", action="store_true", help="Fetch pinned 129,840-byte public OOI slice")
    args = parser.parse_args()
    if args.download:
        download_to(args.input)
    if not args.input.exists():
        raise SystemExit("UNVERIFIED: actual OOI NetCDF4 file absent; do not report measurements")
    result = analyze_file(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8")
    print(json.dumps({k: result[k] for k in ("status", "source_sha256", "n_total", "n_qartod_pass_valid")}, ensure_ascii=False))


if __name__ == "__main__":
    main()

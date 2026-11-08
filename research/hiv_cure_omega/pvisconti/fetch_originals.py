#!/usr/bin/env python3
"""Read-only retrieval of original XLSX (local only, no upload or scheduled job).

Fails closed on network errors, 40MB size limit and invalid OOXML ZIP.
Publisher licenses must be respected. No clinical or viral experiment.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "source_files.json"


def retrieve(output_dir: Path, timeout: int = 20) -> dict:
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["sources"]
    output_dir.mkdir(parents=True, exist_ok=True)
    findings = []
    for entry in entries:
        output = output_dir / entry["filename"]
        record = {"id": entry["id"], "original_url": entry["url"], "local_path": str(output)}
        try:
            request = urllib.request.Request(
                entry["url"], headers={"User-Agent": "ASTRA-pVISCONTI-documentary-audit/1.0"}
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read(40_000_001)
            if len(content) > 40_000_000:
                raise ValueError("Source exceeds maximum 40 MB")
            if not content.startswith(b"PK\\x03\\x04"):
                raise ValueError("Not a valid XLSX ZIP magic")
            temporary = output.with_suffix(output.suffix + ".tmp")
            temporary.write_bytes(content)
            try:
                with zipfile.ZipFile(temporary) as archive:
                    if "[Content_Types].xml" not in archive.namelist():
                        raise ValueError("Missing OOXML content types")
                    if archive.testzip() is not None:
                        raise ValueError("Corrupt ZIP entry")
                temporary.replace(output)
            finally:
                temporary.unlink(missing_ok=True)
            record.update(status="DOWNLOADED_ARCHIVE_VALIDATED",
                          bytes=len(content),
                          sha256=hashlib.sha256(content).hexdigest())
        except Exception as exc:
            record.update(status="UNAVAILABLE", error=f"{type(exc).__name__}: {exc}")
        findings.append(record)
    audit = {
        "status": "PASS" if all(x["status"] == "DOWNLOADED_ARCHIVE_VALIDATED" for x in findings) else "PARTIAL_OR_FAIL",
        "files": findings,
        "raw_individual_reanalysis_completed": False,
        "warning": "ZIP validation does NOT establish correct sample IDs or biological results",
    }
    (output_dir / "fetch_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return audit


if __name__ == "__main__":
    result = retrieve(ROOT / "original_xlsx_private")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 2)

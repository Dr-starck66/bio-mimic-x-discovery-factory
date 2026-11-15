"""Download PINNED third-party CMU quarter-resolution mirror, NEVER official ZIP.

Network opt-in required. SHA of mirror cannot establish official-UCI ZIP SHA.
"""
import argparse
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen

MIRROR_URL = (
    "https://raw.githubusercontent.com/efeerenc/face_orientation_585/"
    "25984c63f09db08cac5d8ff113bd0963af728406/"
    "cmu%2Bface%2Bimages/faces_4.tar.gz"
)
MIRROR_SHA256 = "fee2175af429f964d51d4b13cd7c2c23afbbc309edf8d9b84c975d2c1b41e8f4"


def download_mirror(dest: Path):
    with urlopen(Request(MIRROR_URL, headers={"User-Agent":"ASTRA-ARCHER-RESEARCH/0.2"}), timeout=45) as conn:
        content = conn.read(2 * 1024 * 1024)
    actual = hashlib.sha256(content).hexdigest()
    if actual != MIRROR_SHA256:
        raise ValueError("FAIL: mirror TAR SHA-256 mismatch: " + actual)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return {"status":"MIRROR_HASH_PASS_OFFICIAL_ZIP_UNVERIFIED", "bytes":len(content),
            "sha256":actual, "path":str(dest)}


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--allow-network", action="store_true", required=True)
    p.add_argument("--out", type=Path, default=Path("data/CMU_FACES4_GITHUB_MIRROR.tar.gz"))
    args=p.parse_args()
    print(download_mirror(args.out))

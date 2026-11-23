#!/usr/bin/env python3
"""ASTRA Ω: persistent, auditable import of authorized vendor ZIP archives.

This does NOT override Gmail connector MIME capabilities or create a scheduler.
It accepts existing local files and approved public HTTPS URLs only; private
sources need a separately authorized file-access mechanism.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
from urllib.parse import urlparse
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener
import zipfile

MAX_DOWNLOAD = 512 * 1024 * 1024
MAX_UNCOMPRESSED = 4 * 1024 * 1024 * 1024
MAX_MEMBERS = 10000
MAX_RATIO = 500
DEFAULT_APPROVED_HOSTS = frozenset({
    'sec-assets.thermofisher.com', 'www.thermofisher.com',
    'documents.thermofisher.com', 'ftp.ncbi.nlm.nih.gov',
})


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('redirect_blocked: direct source URL required')


def approved_url(value: str, hosts: set[str] | frozenset[str]) -> str:
    u = urlparse(value)
    if (u.scheme != 'https' or not u.hostname or u.username or u.password
            or u.port not in (None, 443) or u.fragment):
        raise ValueError('https_host_only')
    if u.hostname.lower() not in hosts:
        raise ValueError('host_not_approved')
    return value


def download(url: str, to: Path, hosts: set[str] | frozenset[str]) -> None:
    approved_url(url, hosts)
    opener = build_opener(HTTPSHandler(), NoRedirect())
    request = Request(url, headers={'User-Agent': 'ASTRA-Archive-Importer/1.0', 'Accept': 'application/zip,application/octet-stream'})
    count = 0
    with opener.open(request, timeout=45) as source, to.open('wb') as dest:
        length = source.headers.get('Content-Length')
        if length is not None and int(length) > MAX_DOWNLOAD:
            raise ValueError('download_too_large')
        while True:
            chunk = source.read(1024 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > MAX_DOWNLOAD:
                raise ValueError('download_too_large')
            dest.write(chunk)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_zip(path: Path) -> dict:
    if not zipfile.is_zipfile(path):
        raise ValueError('not_a_zip_archive')
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if not 1 <= len(members) <= MAX_MEMBERS:
            raise ValueError('invalid_member_count')
        total = 0
        for info in members:
            name = info.filename.replace('\\', '/')
            parts = name.split('/')
            if (name.startswith('/') or any(p in ('.', '..') for p in parts)
                    or ':' in parts[0] or '\x00' in name):
                raise ValueError('unsafe_member_path')
            mode = info.external_attr >> 16
            if mode and stat.S_ISLNK(mode):
                raise ValueError('symlink_member_forbidden')
            if info.flag_bits & 1:
                raise ValueError('encrypted_zip_member')
            if info.file_size > MAX_UNCOMPRESSED:
                raise ValueError('member_too_large')
            if info.file_size > MAX_RATIO * max(info.compress_size, 1):
                raise ValueError('suspicious_compression_ratio')
            total += info.file_size
            if total > MAX_UNCOMPRESSED:
                raise ValueError('uncompressed_limit_exceeded')
        # Validate CRC and decompression in-memory streaming (no arbitrary extraction).
        damaged = archive.testzip()
        if damaged:
            raise ValueError('archive_crc_error:' + damaged)
    return {'zip_members': len(members), 'uncompressed_bytes': total, 'zip_integrity': 'PASS'}


def ingest(*, path: Path | None, url: str | None, output: Path,
           approved_hosts: set[str] | frozenset[str] = DEFAULT_APPROVED_HOSTS,
           expected_sha256: str | None = None, expected_size: int | None = None,
           convert_probes: bool = False) -> dict:
    if (path is None) == (url is None):
        raise ValueError('exactly_one_source_required')
    output.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.astra-source-', suffix='.zip', dir=output)
    os.close(fd)
    tmp = Path(temporary)
    try:
        if path is not None:
            if not path.is_file() or path.is_symlink():
                raise ValueError('source_must_be_regular_file')
            if path.stat().st_size > MAX_DOWNLOAD:
                raise ValueError('download_too_large')
            shutil.copyfile(path, tmp)
        else:
            download(url or '', tmp, approved_hosts)
        size = tmp.stat().st_size
        digest = sha256(tmp)
        if expected_size is not None and size != expected_size:
            raise ValueError('size_mismatch')
        if expected_sha256 and digest.lower() != expected_sha256.lower():
            raise ValueError('sha256_mismatch')
        metadata = inspect_zip(tmp)
        final = output / 'source.zip'
        # Avoid an accidental overwrite of prior evidence: same checksum is okay.
        if final.exists() and sha256(final) != digest:
            raise FileExistsError('existing_source_has_different_sha256')
        if not final.exists():
            tmp.replace(final)
        report = {'status': 'PASS_ARCHIVE_INGEST', 'source_kind': 'local' if path else 'approved_https',
                  'source_locator': path.name if path else url,
                  'bytes': size, 'sha256': digest, **metadata,
                  'gmail_connector_permission_changed': False,
                  'automatic_future_download_enabled': False,
                  'biological_validation': 'UNVERIFIED'}
        if convert_probes:
            try:
                from .vendor_probe_bridge import convert
            except ImportError:
                from vendor_probe_bridge import convert
            report['probe_conversion'] = convert(final, output / 'probes')
        (output / 'source_manifest.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        return report
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    sources = p.add_mutually_exclusive_group(required=True)
    sources.add_argument('--input', type=Path)
    sources.add_argument('--url')
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--expected-sha256')
    p.add_argument('--expected-size', type=int)
    p.add_argument('--allow-host', action='append', default=[],
                   help='Additional explicitly user-approved hostname')
    p.add_argument('--convert-probes', action='store_true')
    a = p.parse_args()
    hosts = set(DEFAULT_APPROVED_HOSTS)
    for host in a.allow_host:
        if '://' in host or '/' in host or '@' in host or not host:
            p.error('allow-host must be a hostname, not a URL')
        hosts.add(host.lower())
    print(json.dumps(ingest(path=a.input, url=a.url, output=a.out,
                            approved_hosts=hosts, expected_sha256=a.expected_sha256,
                            expected_size=a.expected_size, convert_probes=a.convert_probes), indent=2))


if __name__ == '__main__':
    main()

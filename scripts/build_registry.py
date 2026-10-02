#!/usr/bin/env python3
"""Validate .penpkg files and build deterministic registry indexes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"
PACKAGES = REGISTRY / "packages"
INDEX = REGISTRY / "index.json"
CATALOG = REGISTRY / "catalog.json"
MAX_ARCHIVE = 25 * 1024 * 1024
MAX_EXPANDED = 100 * 1024 * 1024
MAX_FILES = 1_000
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*$")
VERSION_RE = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")
FORBIDDEN = {".exe", ".dll", ".so", ".dylib", ".sh", ".bat", ".cmd", ".ps1", ".js", ".mjs", ".cjs", ".py", ".wasm"}


def sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def safe_entry(info: zipfile.ZipInfo) -> None:
    name = info.filename
    path = PurePosixPath(name)
    if not name or "\\" in name or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"unsafe archive path: {name!r}")
    mode = info.external_attr >> 16
    if stat.S_ISLNK(mode):
        raise ValueError(f"symlink entries are forbidden: {name}")
    if path.suffix.lower() in FORBIDDEN:
        raise ValueError(f"active or executable file is forbidden: {name}")


def validate_package(file: Path) -> tuple[dict, str]:
    if file.stat().st_size > MAX_ARCHIVE:
        raise ValueError(f"archive exceeds {MAX_ARCHIVE // 1024 // 1024} MiB")
    archive_bytes = file.read_bytes()
    with zipfile.ZipFile(file) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_FILES:
            raise ValueError(f"archive has more than {MAX_FILES} entries")
        if sum(entry.file_size for entry in entries) > MAX_EXPANDED:
            raise ValueError(f"expanded archive exceeds {MAX_EXPANDED // 1024 // 1024} MiB")
        names: set[str] = set()
        for entry in entries:
            safe_entry(entry)
            if entry.filename in names:
                raise ValueError(f"duplicate archive entry: {entry.filename}")
            names.add(entry.filename)
        if "pentool.package.json" not in names:
            raise ValueError("pentool.package.json is missing")
        manifest = json.loads(archive.read("pentool.package.json"))
        if manifest.get("schema") != 1:
            raise ValueError("unsupported package manifest schema")
        name = manifest.get("name", "")
        version = manifest.get("version", "")
        if not NAME_RE.fullmatch(name):
            raise ValueError(f"invalid package name: {name!r}")
        if not VERSION_RE.fullmatch(version):
            raise ValueError(f"invalid semantic version: {version!r}")
        expected = PACKAGES / Path(*name.split("/")) / f"{version}.penpkg"
        if file.resolve() != expected.resolve():
            raise ValueError(f"package must be stored at {expected.relative_to(ROOT).as_posix()}")
        for asset_id, asset in manifest.get("assets", {}).items():
            asset_path = asset.get("path", "")
            if asset_path not in names:
                raise ValueError(f"asset {asset_id!r} points to missing {asset_path!r}")
            actual = sha256(archive.read(asset_path))
            if actual != asset.get("hash"):
                raise ValueError(f"asset hash mismatch: {asset_id}")
    return manifest, sha256(archive_bytes)


def build() -> tuple[dict, dict]:
    index: dict = {"schema": 1, "packages": {}}
    catalog_packages: list[dict] = []
    for file in sorted(PACKAGES.rglob("*.penpkg")):
        try:
            manifest, package_hash = validate_package(file)
        except Exception as error:
            raise ValueError(f"{file.relative_to(ROOT).as_posix()}: {error}") from error
        name = manifest["name"]
        version = manifest["version"]
        claim = REGISTRY / "namespaces" / f"{name.split('/')[0]}.json"
        if not claim.exists():
            raise ValueError(f"{name}: namespace claim is missing at {claim.relative_to(ROOT)}")
        release = {"path": file.relative_to(REGISTRY).as_posix(), "hash": package_hash, "yanked": False}
        index["packages"].setdefault(name, {})[version] = release
        catalog_packages.append({
            "name": name,
            "version": version,
            "description": manifest.get("description", ""),
            "license": manifest.get("license"),
            "repository": manifest.get("repository"),
            "authors": manifest.get("authors", []),
            "pentool": manifest.get("pentool"),
            "assets": len(manifest.get("assets", {})),
            "hash": package_hash,
            "path": release["path"],
        })
    catalog = {"schema": 1, "generated": None, "packages": catalog_packages}
    return index, catalog


def encoded(data: dict) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed indexes are stale")
    args = parser.parse_args()
    try:
        index, catalog = build()
    except Exception as error:
        print(f"registry validation failed: {error}", file=sys.stderr)
        return 1
    expected = {INDEX: encoded(index), CATALOG: encoded(catalog)}
    if args.check:
        stale = [str(path.relative_to(ROOT)) for path, content in expected.items() if not path.exists() or path.read_text(encoding="utf-8") != content]
        if stale:
            print("generated registry files are stale: " + ", ".join(stale), file=sys.stderr)
            print("run: python scripts/build_registry.py", file=sys.stderr)
            return 1
    else:
        for path, content in expected.items():
            path.write_text(content, encoding="utf-8", newline="\n")
    print(f"validated {len(catalog['packages'])} package release(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

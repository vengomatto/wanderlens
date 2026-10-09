#!/usr/bin/env python3
"""Download photos from a pCloud public folder link into data/photos.

Walks the shared folder tree, skips files whose name+size already exist under
the destination (so re-running does not duplicate), and organizes subfolders as
directories. Reusable: pass --code for a different public link.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import requests

API = "https://api.pcloud.com"
DEFAULT_CODE = "REDACTED"  # REDACTED: Malta + Trentino
DEFAULT_DEST = "data/photos"


def show(code: str, folderid: int | None = None) -> dict:
    params = {"code": code}
    if folderid is not None:
        params["folderid"] = folderid
    response = requests.get(f"{API}/showpublink", params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    if data.get("result") != 0:
        raise SystemExit(f"showpublink failed: {data}")
    return data["metadata"]


def index_existing(root: Path) -> dict[str, set[int]]:
    index: dict[str, set[int]] = {}
    for path in root.rglob("*"):
        if path.is_file():
            index.setdefault(path.name, set()).add(path.stat().st_size)
    return index


def download(code: str, fileid: int, target: Path, size: int) -> None:
    link = requests.get(
        f"{API}/getpublinkdownload", params={"code": code, "fileid": fileid}, timeout=60
    ).json()
    url = f"https://{link['hosts'][0]}{link['path']}"
    with requests.get(url, stream=True, timeout=180) as response:
        response.raise_for_status()
        tmp = target.with_suffix(target.suffix + ".part")
        with open(tmp, "wb") as fh:
            for chunk in response.iter_content(1 << 16):
                fh.write(chunk)
        os.replace(tmp, target)
    if target.stat().st_size != size:
        raise SystemExit(f"size mismatch for {target}")
    print(f"  got {target}")


def walk(node: dict, rel: str, code: str, dest: Path, existing: dict[str, set[int]]) -> None:
    out_dir = dest / rel if rel else dest
    for child in node.get("contents", []):
        if child.get("isfolder"):
            walk(child, f"{rel}/{child['name']}".strip("/"), code, dest, existing)
            continue
        name, size = child["name"], child["size"]
        if size in existing.get(name, set()):
            print(f"  skip {name} (already present)")
            continue
        target = (out_dir / name) if rel else (dest / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        download(code, child["fileid"], target, size)
        existing.setdefault(name, set()).add(size)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", default=DEFAULT_CODE)
    parser.add_argument("--dest", default=DEFAULT_DEST)
    args = parser.parse_args()

    dest = Path(args.dest)
    dest.mkdir(parents=True, exist_ok=True)
    metadata = show(args.code)
    print(f"link root: {metadata.get('name')}")
    walk(metadata, "", args.code, dest, index_existing(dest))


if __name__ == "__main__":
    main()

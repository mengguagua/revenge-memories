#!/usr/bin/env python3
"""Single-threaded, pixel-exact PNG optimisation with an offline source backup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pixels(path):
    with Image.open(path) as image:
        return image.size, image.convert("RGBA").tobytes()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    args.backup.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    records = []
    started = time.time()
    candidates = sorted(root.joinpath("assets").rglob("*.png"), key=lambda p: -p.stat().st_size)
    for i, path in enumerate(candidates):
        before = path.stat().st_size
        size, original = pixels(path)
        record = {"path": str(path.relative_to(root)), "purpose": path.parts[len(root.parts) + 1],
                  "width": size[0], "height": size[1], "before_bytes": before, "after_bytes": before,
                  "before_sha256": digest(path), "pixel_exact": True, "changed": False}
        # Tiny tiles already cost less than the requested small-icon target.
        if before >= 2048:
            target = args.backup / "candidate.png"
            result = subprocess.run(["/opt/homebrew/bin/oxipng", "-o", "2", "--threads", "1", "--strip", "safe",
                                     "--out", str(target), str(path)], capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(f"oxipng failed for {path}: {result.stderr}")
            after_size, after_pixels = pixels(target)
            if size != after_size or original != after_pixels:
                raise RuntimeError(f"Decoded RGBA changed: {path}")
            # Avoid churn where recompression provides no actual byte saving.
            if target.stat().st_size < before:
                backup = args.backup / path.relative_to(root)
                backup.parent.mkdir(parents=True, exist_ok=True)
                if backup.exists():
                    raise RuntimeError(f"Refusing to replace existing original backup: {backup}")
                shutil.copy2(path, backup)
                shutil.copyfile(target, path)
                record.update(after_bytes=path.stat().st_size, changed=True, after_sha256=digest(path))
            target.unlink(missing_ok=True)
        records.append(record)
        if i % 40 == 0:
            print(f"PNG_CHECK {i + 1}/{len(candidates)} changed={sum(r['changed'] for r in records)} saved={sum(r['before_bytes'] - r['after_bytes'] for r in records)}", flush=True)
    report = {"method": "oxipng -o 2 --threads 1 --strip safe; exact decoded RGBA comparison; no alpha alteration",
              "source_root": str(root / "assets"), "original_backup": str(args.backup),
              "elapsed_seconds": round(time.time() - started, 2),
              "before_bytes": sum(r["before_bytes"] for r in records),
              "after_bytes": sum(r["after_bytes"] for r in records),
              "changed": sum(r["changed"] for r in records), "records": records}
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

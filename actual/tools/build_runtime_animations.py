#!/usr/bin/env python3
"""Build byte-indexed animation programs; verify every decoded value against source."""
import hashlib
import json
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {"reviewed": "data/reviewed_animations.json",
           "legacy": "data/legacy/full_animation_effects.json",
           "party": "data/m11_party_motion.json"}


def build():
    out = ROOT / "data/animation_runtime"
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"schema": 2, "groups": {}}
    counts = {}
    for group, relative in SOURCES.items():
        source_path = ROOT / relative
        source_bytes = source_path.read_bytes()
        source = json.loads(source_bytes)
        metadata = {key: value for key, value in source.items() if key != "variants"}
        table = {}
        data_path = out / f"{group}.bin"
        with data_path.open("wb") as stream:
            for key, value in source["variants"].items():
                payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
                packed = zlib.compress(payload, 9)
                table[key] = [stream.tell(), len(packed), len(payload)]
                stream.write(packed)
        # Compare the entire value, including frame arrays, timings and unknown
        # future metadata. This is not a hand-picked field-level equivalence test.
        with data_path.open("rb") as stream:
            for key, (offset, length, raw_length) in table.items():
                stream.seek(offset)
                decoded = zlib.decompress(stream.read(length))
                if len(decoded) != raw_length or json.loads(decoded) != source["variants"][key]:
                    raise RuntimeError(f"Animation changed: {group}/{key}")
        group_path = out / f"{group}.json"
        group_path.write_text(json.dumps({"metadata": metadata, "variants": table}, ensure_ascii=False, separators=(",", ":")) + "\n")
        manifest["groups"][group] = {"source": "res://" + relative,
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "index": "res://" + group_path.relative_to(ROOT).as_posix(),
            "programs": "res://" + data_path.relative_to(ROOT).as_posix(),
            "program_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
            "variant_count": len(table)}
        counts[group] = {"variants": len(table), "source_bytes": len(source_bytes),
                         "index_bytes": group_path.stat().st_size, "program_bytes": data_path.stat().st_size,
                         "all_values_equal": True}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"animation_runtime": counts, "all_variants_equal": True}, ensure_ascii=False))
    return counts


if __name__ == "__main__":
    build()

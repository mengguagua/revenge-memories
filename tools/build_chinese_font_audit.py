#!/usr/bin/env python3
"""Audit localized text coverage and exact binary-alpha font atlas boundaries."""
import json
from pathlib import Path
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "data/font_zh.json").read_text())
glyphs = manifest["glyphs"]
source_glyphs = json.loads((ROOT / "data/graphics.json").read_text())["font"]["char_codes"]
strings = []


def walk(value, localized=False):
    if isinstance(value, dict):
        for key, entry in value.items():
            walk(entry, localized or key.endswith("_zh") or key == "zh")
    elif isinstance(value, list):
        for entry in value:
            walk(entry, localized)
    elif localized and isinstance(value, str):
        strings.append(value)


for name in ("opening.json", "first_battle.json"):
    walk(json.loads((ROOT / "data" / name).read_text()))
# The root controller also has localized HUD/menu labels outside source data.
main_path = ROOT / "core/main.gd"
for literal in re.findall(r'"((?:[^"\\]|\\.)*)"', main_path.read_text()):
    if any("\u3400" <= c <= "\u9fff" for c in literal):
        strings.append(literal)

required = set("".join(strings))
missing = sorted(c for c in required if ord(c) >= 128 and c not in glyphs and c not in source_glyphs)
atlas = Image.open(ROOT / manifest["path"].removeprefix("res://")).convert("RGBA")
assert {color for _count, color in atlas.getchannel("A").getcolors()} == {0, 255}
assert atlas.size == (manifest["texture"]["width"], manifest["texture"]["height"])
assert (ROOT / manifest["path"].removeprefix("res://")).stat().st_size == manifest["texture"]["bytes"]
for character in required:
    if character not in glyphs:
        continue
    g = glyphs[character]
    x, y, w, h = g["rect"]
    assert 0 <= x and 0 <= y and x + w <= atlas.width and y + h <= atlas.height
    tile = atlas.crop((x, y, x + w, y + h))
    bbox = tile.getchannel("A").getbbox()
    actual = [0, 0, 0, 0] if bbox is None else [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]]
    assert actual == g["ink_bounds"], character

result = {"localized_strings": len(strings), "unique_characters": len(required), "missing": missing, "binary_alpha": True, "atlas_rects_and_ink_bounds": "passed", "native_glyph_height": 12, "line_height": 16, "atlas_bytes": manifest["texture"]["bytes"], "glyph_count": manifest["glyph_count"]}
print(json.dumps(result, ensure_ascii=False))
if missing:
    raise SystemExit(1)

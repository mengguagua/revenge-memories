#!/usr/bin/env python3
"""Recover FE2 UI arrows from CHR 0; retain source pixels and OAM flips."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/original/graphics/cursors"
SOURCE_COMMIT = "956365ef33c63751e7afd03f05e600d7728549da"


def decode_white_tile(raw: bytes, tile_id: int) -> Image.Image:
    tile = raw[tile_id * 16 : (tile_id + 1) * 16]
    assert len(tile) == 16
    result = Image.new("RGBA", (8, 8))
    for y in range(8):
        for x in range(8):
            index = ((tile[y] >> (7 - x)) & 1) | (
                ((tile[y + 8] >> (7 - x)) & 1) << 1
            )
            # Both arrow tiles use color 1 exclusively. This assertion avoids
            # silently discarding palette information if source CHR changes.
            assert index in (0, 1), (tile_id, x, y, index)
            result.putpixel((x, y), (255, 255, 255, 255) if index else (0, 0, 0, 0))
    return result


def extract(source: Path) -> dict:
    raw = source.read_bytes()
    right = decode_white_tile(raw, 0xF4)
    down = decode_white_tile(raw, 0xF3)
    images = {
        "right": right,
        # NES OAM attribute bit 6; L049725 uses F4/$42 vs F4/$02.
        "left": right.transpose(Image.Transpose.FLIP_LEFT_RIGHT),
        "down": down,
        "up": down.transpose(Image.Transpose.FLIP_TOP_BOTTOM),
    }
    records = {
        "right": {"tile": "F4", "source_oam": "bank004:L049720,L04972F", "transform": "none"},
        "left": {"tile": "F4", "source_oam": "bank004:L049725", "transform": "OAM bit 6: horizontal flip"},
        "down": {"tile": "F3", "source_oam": "bank001:L0180DA; bank004:L04A040", "transform": "none"},
        "up": {"tile": "F3", "source_oam": "bank004:L048DC5 includes F3/$82", "transform": "OAM bit 7: vertical flip"},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    for name, image in images.items():
        target = OUT / f"{name}.png"
        image.save(target, optimize=True, compress_level=9)
        records[name].update({
            "path": "res://" + str(target.relative_to(ROOT)),
            "native_size": [8, 8],
            "visible_bbox": list(image.getbbox()),
            "bytes": target.stat().st_size,
            "pixel_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
            "alpha_values": sorted(set(image.getchannel("A").tobytes())),
        })
        assert target.stat().st_size < 20_000
        assert records[name]["alpha_values"] == [0, 255]

    # Enlarged, nearest-neighbor review only; runtime arrows remain 8x8.
    # Display each arrow on both dark and pale surfaces to check alpha edges.
    preview = Image.new("RGBA", (256, 128))
    for row, background in enumerate([(0, 0, 0, 255), (176, 184, 196, 255)]):
        for column, name in enumerate(["left", "right", "up", "down"]):
            x, y = column * 64, row * 64
            preview.paste(background, (x, y, x + 64, y + 64))
            enlarged = images[name].resize((48, 48), Image.Resampling.NEAREST)
            preview.alpha_composite(enlarged, (x + 8, y + 8))
    preview_path = OUT / "preview.png"
    preview.save(preview_path, optimize=True, compress_level=9)
    assert preview_path.stat().st_size < 200_000

    manifest = {
        "schema_version": 1,
        "source_repository": "https://github.com/minirop/fe2",
        "source_revision": SOURCE_COMMIT,
        "source_chr": "bank000.chr:first4KiB",
        "source_chr_sha256": hashlib.sha256(raw).hexdigest(),
        "pixel_policy": "Exact 2bpp source pixels. Transparent index 0, white index 1. Only NES OAM flips; no rotation, antialiasing, crop, or redrawing.",
        "arrows": records,
        "context_policy": {
            "menu_selection": "right, placed left of the selected menu item; keep horizontal space before text.",
            "horizontal_previous_next": "left and right on respective sides only when that direction is available.",
            "dialogue_continue": "down, inside the dialogue content safe area at bottom right.",
            "map_position_or_target": "down, above the selected node or unit, pointing at it.",
        },
        "drawing": {
            "coordinates": "All arrows use an 8x8 canvas and are drawn at native pixel coordinates with nearest texture filtering.",
            "menu_vertical_center": "F4's visible center is y=4.5: draw at text row center minus 4.5, rounded to native pixels.",
            "map_tip": "F3's visible tip is [3,6]; place that tip just above the selected sprite/cell.",
            "safe_inset": "Keep the complete 8x8 canvas inside bitmap panel padding and separate it from adjacent text.",
        },
        "verification": {
            "native_arrow_count": 4,
            "all_alpha_binary": True,
            "left_is_exact_source_horizontal_flip": True,
            "up_is_exact_source_vertical_flip": True,
            "preview": "res://" + str(preview_path.relative_to(ROOT)),
            "preview_size": list(preview.size),
            "preview_bytes": preview_path.stat().st_size,
            "preview_columns": ["left", "right", "up", "down"],
            "preview_rows": ["dark", "light"],
        },
    }
    assert images["left"].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes() == right.tobytes()
    assert images["up"].transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes() == down.tobytes()
    original_down = ROOT / "assets/original/graphics/cursor.png"
    if original_down.exists():
        assert Image.open(original_down).convert("RGBA").tobytes() == down.tobytes()
        manifest["verification"]["down_matches_existing_original_cursor"] = True
    (ROOT / "data/cursors.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chr", type=Path, default=ROOT / "assets/original/graphics/source/bank000.chr")
    args = parser.parse_args()
    result = extract(args.chr)
    print(json.dumps({name: {"size": item["native_size"], "bytes": item["bytes"], "source": item["source_oam"]} for name, item in result["arrows"].items()}, ensure_ascii=False))

#!/usr/bin/env python3
"""Recover individual FE2 HP cells from original CHR 0 without redrawing.

bank001 L01B2BB-L01B395 emits tiles CB..CF, which encode one or two
individual HP cells. The native UI can draw the exact four-pixel cell
separately so every HP remains visible even in narrower Chinese panels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw

from extract_graphics import NES

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/original/graphics/health"
REVISION = "956365ef33c63751e7afd03f05e600d7728549da"
PALETTES = {"ally": [0x0F, 0x30, 0x22, 0x11], "enemy": [0x0F, 0x30, 0x26, 0x16]}


def indices(raw: bytes, tile_id: int) -> list[list[int]]:
    tile = raw[tile_id * 16:tile_id * 16 + 16]
    assert len(tile) == 16
    return [[((tile[y] >> (7 - x)) & 1) | (((tile[y + 8] >> (7 - x)) & 1) << 1)
             for x in range(8)] for y in range(8)]


def half(tile: list[list[int]], side: int) -> list[list[int]]:
    return [row[side * 4:side * 4 + 4] for row in tile]


def rgba(cell: list[list[int]], palette: list[int]) -> Image.Image:
    image = Image.new("RGBA", (4, 8))
    for y, row in enumerate(cell):
        for x, index in enumerate(row):
            # Source color 0 is the surrounding black HUD. Preserve those
            # margins as alpha 0 so panels can use the original cell pixels.
            image.putpixel((x, y), NES[palette[index]] + ((255 if index else 0),))
    return image


def original_tile_ids(hp: int, maximum: int) -> list[int]:
    """Readable transcription of L01B310-L01B363 for all HP 0..52."""
    out = []
    full_pairs, odd_filled = divmod(hp, 2)
    out.extend([0xCE] * full_pairs)
    remaining = maximum - hp
    if odd_filled:
        if remaining:
            out.append(0xCD)
            remaining -= 1
        else:
            out.append(0xCF)
    pairs, odd_empty = divmod(remaining, 2)
    out.extend([0xCB] * pairs)
    if odd_empty:
        out.append(0xCC)
    return out


def extract(source: Path) -> dict:
    raw = source.read_bytes()
    tiles = {tid: indices(raw, tid) for tid in range(0xCB, 0xD0)}
    filled = half(tiles[0xCE], 0)
    empty = half(tiles[0xCB], 0)
    assert filled == half(tiles[0xCE], 1) == half(tiles[0xCD], 0) == half(tiles[0xCF], 0)
    assert empty == half(tiles[0xCB], 1) == half(tiles[0xCD], 1) == half(tiles[0xCC], 0)
    assert sum(v == 1 for row in filled for v in row) == 18
    assert sum(v == 1 for row in empty for v in row) == 0
    # Validate cell extraction against the original tile packing for every
    # supported HP/max pair, including odd final cells and an empty gauge.
    checked_pairs = 0
    for maximum in range(1, 53):
        for hp in range(maximum + 1):
            cells = []
            for tid in original_tile_ids(hp, maximum):
                cells.extend([half(tiles[tid], 0), half(tiles[tid], 1)])
            assert len(cells) >= maximum
            assert cells[:maximum] == [filled] * hp + [empty] * (maximum - hp), (hp, maximum)
            checked_pairs += 1

    OUT.mkdir(parents=True, exist_ok=True)
    assets = {}
    decoded = {}
    for side, palette in PALETTES.items():
        assets[side] = {}
        for state, cell in {"filled": filled, "empty": empty}.items():
            image = rgba(cell, palette)
            decoded[(side, state)] = image
            path = OUT / f"{side}_{state}.png"
            image.save(path, optimize=True, compress_level=9)
            assets[side][state] = {
                "path": "res://" + str(path.relative_to(ROOT)),
                "native_size": [4, 8],
                "visible_body_size": [3, 6],
                "source_tile": "CE" if state == "filled" else "CB",
                "source_crop": [0, 0, 4, 8],
                "palette_indices": palette,
                "bytes": path.stat().st_size,
                "alpha_values": sorted(set(image.getchannel("A").tobytes())),
                "pixel_sha256": hashlib.sha256(image.tobytes()).hexdigest(),
            }
            assert path.stat().st_size < 20_000
            assert set(image.getchannel("A").tobytes()) <= {0, 255}

    preview = Image.new("RGBA", (448, 192))
    draw = ImageDraw.Draw(preview)
    for row, bg in enumerate([(0, 0, 0, 255), (184, 190, 196, 255)]):
        preview.paste(bg, (0, row * 96, 448, (row + 1) * 96))
        for col, side in enumerate(["enemy", "ally"]):
            x, y = col * 224 + 8, row * 96 + 8
            draw.text((x, y), f"{side} 18/28; 1 HP = 1 cell", fill="white" if row == 0 else "black")
            gauge = Image.new("RGBA", (104, 16))
            for point in range(28):
                state = "filled" if point < 18 else "empty"
                gauge.alpha_composite(decoded[(side, state)], ((point % 26) * 4, (point // 26) * 8))
            preview.alpha_composite(gauge.resize((208, 32), Image.Resampling.NEAREST), (x, y + 22))
            # Native-size cell pair on each background checks transparency and
            # spacing independent of the enlarged review strip.
            preview.alpha_composite(decoded[(side, "filled")], (x + 4, y + 65))
            preview.alpha_composite(decoded[(side, "empty")], (x + 8, y + 65))
    preview_path = OUT / "preview.png"
    preview.save(preview_path, optimize=True, compress_level=9)

    result = {
        "schema_version": 1,
        "source_repository": "https://github.com/minirop/fe2",
        "source_revision": REVISION,
        "source_chr": "bank000.chr:first4KiB",
        "source_chr_sha256": hashlib.sha256(raw).hexdigest(),
        "source_routine": "bank001:L01B2BB-L01B395",
        "source_palette": "bank005:L05BCCD; ally background group 2, enemy group 3",
        "source_packing": {
            "CB": "two empty HP cells",
            "CC": "one empty HP cell followed by terminator/background",
            "CD": "one filled HP cell and one empty HP cell",
            "CE": "two filled HP cells",
            "CF": "one filled HP cell followed by terminator/background",
        },
        "pixel_policy": "Original 2bpp pixels split into 4x8 half-tiles. Color 0 becomes transparent; source white and side-specific empty-cell/background colors retained. No antialiasing, redrawing, or raster scaling in runtime assets.",
        "cells": assets,
        "layout": {
            "cell_pitch": [4, 8],
            "cell_size": [4, 8],
            "original_cells_per_row": 26,
            "original_max_hp": 52,
            "original_gauge_width": 104,
            "recommended_cells_per_row_for_100px_safe_area": 25,
            "source_wrap": "L01B363-L01B395: above 13 tiles/26 HP, continue in the preceding PPU row; do not merge points into percentages.",
            "native_layout": "Draw exactly max_hp cells, with hp filled and max_hp-hp empty. Wrap every available_width/4 cells; integer pixel coordinates and nearest filtering. Keep the complete 4x8 canvas inside the existing content safe area.",
        },
        "verification": {
            "original_cell_packing_hp_max_pairs_checked": checked_pairs,
            "all_alpha_binary": True,
            "all_cells_match_original_single_and_dual_tile_halves": True,
            "filled_white_pixel_count": 18,
            "empty_white_pixel_count": 0,
            "preview": "res://" + str(preview_path.relative_to(ROOT)),
            "preview_native_and_2x_nearest": True,
            "preview_backgrounds": ["black", "light gray"],
            "preview_bytes": preview_path.stat().st_size,
        },
    }
    (ROOT / "data/health_ui.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chr", type=Path, default=ROOT / "assets/original/graphics/source/bank000.chr")
    args = parser.parse_args()
    result = extract(args.chr)
    print(json.dumps({"cells": result["cells"], "verification": result["verification"]}, ensure_ascii=False))

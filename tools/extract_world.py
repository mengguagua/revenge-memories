#!/usr/bin/env python3
"""Extract original FE2 world nodes and connections, without running the game."""
import argparse
import base64
import hashlib
import json
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("/private/tmp/fe2-analysis-20261012"))
    ap.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data/world_map.json")
    args = ap.parse_args()
    rom = (args.source / "fe2.nes").read_bytes()
    expected_sha1 = "2153ae9a7b1c63e8d4d83a807f1c8c1f482f7293"
    assert hashlib.sha1(rom).hexdigest() == expected_sha1, "Use the source-matching original ROM"

    def offset(cpu_address):
        return 16 + 15 * 0x4000 + (cpu_address - 0xC000)

    def source(label, topic):
        text = (args.source / "src/bank015.asm").read_text()
        return {"file": "src/bank015.asm", "label": label, "topic": topic,
                "line": text[:text.index(label + ":")].count("\n") + 1}

    map_node = ET.parse(args.source / "maps/worldmap.tmx").getroot()
    width, height = int(map_node.get("width")), int(map_node.get("height"))
    raw = zlib.decompress(base64.b64decode("".join(map_node.find("layer/data").text.split())))
    tiles = [gid - 1 for gid in struct.unpack(f"<{width * height}I", raw)]
    # 80 [x,y] pairs at EEF4, before the 80-entry pointer table at EF94.
    positions = rom[offset(0xEEF4):offset(0xEF94)]
    assert len(positions) == 160
    nodes = {}
    for index in range(80):
        position = [positions[index * 2], positions[index * 2 + 1]]
        address = struct.unpack_from("<H", rom, offset(0xEF94) + index * 2)[0]
        begin = offset(address)
        end = rom.index(255, begin)
        assert end - begin <= 5
        nodes[str(index + 1)] = {"map_id": index + 1, "position": position,
                                 "neighbors": list(rom[begin:end]),
                                 "position_cpu_address": hex(0xEEF4 + index * 2),
                                 "neighbors_cpu_address": hex(address)}
    assert nodes["49"]["position"] == [4, 41]
    assert nodes["1"]["position"] == [6, 41]
    assert nodes["49"]["neighbors"] == [1]
    assert nodes["1"]["neighbors"] == [49, 2]
    nodes["49"].update({"name_ja": "ラムのむら", "name_zh": "拉姆村"})
    nodes["1"].update({"name_ja": "ラムのもり", "name_zh": "拉姆森林"})
    village_source = (args.source / "src/bank013.asm").read_text()
    output = {"width": width, "height": height, "tiles": tiles, "source": "maps/worldmap.tmx",
              "coordinate_order": "x,y; original world-node table already uses this order",
              "ram_village": nodes["49"]["position"], "ram_woods": nodes["1"]["position"],
              "ram_village_map_id": 49, "ram_woods_map_id": 1, "initial_route": [49, 1],
              "nodes": nodes, "source_rom_sha1": expected_sha1,
              "node_positions_note": "Confirmed original EEF4 world coordinates and EF94 adjacency table, not visual placeholders",
              "recommended_viewport_origin": [0, -544],
              "viewport_note": "Suggested native256x240 presentation keeping node49 at64,112 and node1 at96,112 above bottom UI; this is not a verified original camera setting",
              "village_exit": {"inside": [22, 8], "boundary": [23, 8], "direction": "right",
                               "evidence": "Composed Ram village has its only accessible exterior gap on right row8. L0D8D76 checks the boundary before ordinary collision.",
                               "scripted_departure_gate": "An explicit Lukas-joined flag check in the boundary handler was not identified; initial Lukas occupies the narrow approach at21,8, and his join script removes his village actor.",
                               "confidence": "source geometry and boundary handler; scripted actor movement and exact gating still need runtime comparison"},
              "provenance": [source("L0FEEF4", "original node coordinates"), source("L0FEF94", "original node neighbors"),
                             source("L0FF034", "Ram Woods neighbors49 and2"), source("L0FF0D7", "Ram village neighbor1"),
                             {"file": "src/bank013.asm", "label": "L0DB262", "topic": "noncombat map1 to world map49",
                              "line": village_source[:village_source.index("L0DB262:")].count("\n") + 1}]}
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ram_village": output["ram_village"], "ram_woods": output["ram_woods"], "world_nodes": len(nodes)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

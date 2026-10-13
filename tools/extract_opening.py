#!/usr/bin/env python3
"""Extract the opening and first battlefield from minirop/fe2, without a ROM.

Only writes data/opening.json and data/first_battle.json. Source statements and
unverified interpretations are retained separately, rather than inventing data.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import struct
import xml.etree.ElementTree as ET
import zlib
from pathlib import Path


NAMES = {
    "ALM": (1, "アルム", "阿鲁姆"),
    "MYCEN": (3, "マイセン", "麦森"),
    "LUKAS": (5, "ルカ", "卢卡"),
    "KLIFF": (6, "クリフ", "克里夫"),
    "TOBIN": (7, "ロビン", "罗宾"),
    "GRAY": (8, "グレイ", "格雷"),
}


class Source:
    def __init__(self, root: Path):
        self.root = root
        self.files = {
            i: (root / "src" / f"bank{i:03}.asm").read_text()
            for i in [2, 3, 4, 8, 9, 10, 11, 12, 13, 15]
        }
        self.defines: dict[str, int] = {}
        for name, value in re.findall(r"\.DEFINE\s+(\w+)\s+(\S+)", (root / "src/defines.s").read_text()):
            if value.startswith("$"):
                self.defines[name] = int(value[1:], 16)
            elif value in self.defines:
                self.defines[name] = self.defines[value]

    def block(self, bank: int, label: str, stop: bool = False) -> str:
        s = self.files[bank]
        start = s.index(label + ":")
        end_match = re.search(r"\.db STOP", s[start:]) if stop else re.search(r"\n\w+:", s[start + len(label) + 1 :])
        if stop:
            return s[start : start + end_match.end()]
        return s[start : start + len(label) + 1 + end_match.start()] if end_match else s[start:]

    def db(self, bank: int, label: str) -> list[int]:
        result = []
        for line in self.block(bank, label).splitlines():
            code = line.split(";")[0].strip()
            if code.startswith(".db "):
                for value in code[4:].split():
                    if value.startswith("$"):
                        result.append(int(value[1:], 16))
                    elif value in self.defines:
                        result.append(self.defines[value])
                    else:
                        raise ValueError((label, value))
        return result

    def ref(self, bank: int, label: str) -> dict:
        s = self.files[bank]
        return {"file": f"src/bank{bank:03}.asm", "label": label, "line": s[: s.index(label + ":")].count("\n") + 1}

    def strings(self, bank: int, label: str) -> list[str]:
        return [json.loads(line.split(",", 1)[1].strip()) for line in self.block(bank, label).splitlines()
                if line.strip().startswith(".STRINGMAP")]


def tilemap(root: Path, filename: str) -> dict:
    node = ET.parse(root / "maps" / filename).getroot()
    width, height = int(node.get("width")), int(node.get("height"))
    data = node.find("layer/data")
    if data.get("encoding") == "csv":
        gids = [int(value) for value in data.text.strip().split(",")]
    else:
        binary = base64.b64decode("".join(data.text.split()))
        binary = zlib.decompress(binary)
        gids = struct.unpack(f"<{width * height}I", binary)
        assert len(binary) == width * height * 4
    assert len(gids) == width * height
    return {
        "width": width, "height": height, "tile_size": int(node.get("tilewidth")),
        "tileset": node.find("tileset").get("source"),
        "tiles": [gid - 1 for gid in gids], "source": f"maps/{filename}",
        "tile_indexing": "zero_based_atlas_id; TMX firstgid 1 subtracted",
    }


def dialogue(src: Source, label: str, default_speaker: str = "") -> list[dict]:
    speaker = default_speaker
    face = default_speaker
    lines, pages = [], []

    def flush():
        nonlocal lines
        if lines:
            pages.append({"speaker": speaker.lower(), "face": face.lower(), "text_ja": "\n".join(lines), "source_label": label})
            lines = []

    for line in src.block(3, label, stop=True).splitlines()[1:]:
        line = line.strip()
        if line.startswith("FACE "):
            flush()
            face = line.split()[1]
        elif line.startswith("NAME "):
            flush()
            speaker = line.split()[1]
        elif line in ("WAIT_CLICK", "PAGE") or line == ".db STOP":
            flush()
        elif line.startswith(".STRINGMAP"):
            lines.append(json.loads(line.split(",", 1)[1].strip()))
    flush()
    return pages


def coordinates(raw: list[int], count: int | None = None) -> list[list[int]]:
    # Tactical deployment pairs are already x,y. L089E7C puts first byte
    # into unit+17 (x) and second into unit+16 (y); map headers use height,width.
    # Village NPC records have their own y,x layout and do not use this helper.
    pairs = [[raw[i], raw[i + 1]] for i in range(1, len(raw) - 1, 2)]
    return pairs[:count] if count is not None else pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, default=Path("/private/tmp/fe2-analysis-20261012"))
    ap.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = ap.parse_args()
    src = Source(args.source)
    args.output.mkdir(parents=True, exist_ok=True)

    characters = {}
    char_labels = {"ALM": "L0890E2", "MYCEN": "L0890FA", "LUKAS": "L089112", "KLIFF": "L08911E", "TOBIN": "L08912A", "GRAY": "L089136"}
    growth_labels = {"ALM": "L098E2D", "MYCEN": "L098E39", "LUKAS": "L098E45", "KLIFF": "L098E4B", "TOBIN": "L098E51", "GRAY": "L098E57"}
    move_values = src.db(15, "L0FEDD3")
    for name, label in char_labels.items():
        raw = src.db(8, label)
        cid, jp, zh = NAMES[name]
        class_name = {21: "fighter", 6: "soldier", 14: "villager", 7: "gold_knight"}[raw[1]]
        characters[name.lower()] = {
            "id": cid, "name_ja": jp, "name_zh": zh, "class_id": raw[1], "class": class_name,
            "level": raw[2], "hp": raw[3], "max_hp": raw[3], "exp": raw[4],
            "strength": raw[5], "skill": raw[6], "speed": raw[7], "luck": raw[8], "defence": raw[9],
            "magic_flags": raw[10], "item_id": raw[11], "move": move_values[raw[1] - 1],
            "growths": dict(zip(["strength", "skill", "speed", "luck", "defence", "hp"], src.db(9, growth_labels[name]))),
            "raw": raw, "provenance": [src.ref(8, label), src.ref(9, growth_labels[name]), src.ref(15, "L0FEDD3")],
            "confidence": "source_table; movement semantic inferred from class table usage",
        }

    dialogue_names = [
        ("training", "L039770", "MYCEN"),
        ("friends_greeting", "L0397D9", ""),
        ("lukas_report", "L0397FE", "LUKAS"),
        ("kliff_reaction", "L0398F4", "KLIFF"),
        ("tobin_encouragement", "L039918", "TOBIN"),
        ("gray_advice", "L039943", "GRAY"),
        ("mycen_refusal", "L039966", "MYCEN"),
        ("alm_volunteers", "L0399AF", "LUKAS"),
        ("lukas_join_repeat", "L039A69", "LUKAS"),
        ("gray_joins", "L039AA6", "GRAY"),
        ("tobin_joins", "L039AFB", "TOBIN"),
        ("kliff_joins", "L039B3F", "KLIFF"),
    ]
    dialogues = {key: dialogue(src, label, speaker) for key, label, speaker in dialogue_names}
    by_label = {label: dialogues[key] for key, label, speaker in dialogue_names}

    lore_paragraphs, paragraph, breaks = [], [], 0
    for line in src.block(4, "L04A0C2", stop=True).splitlines():
        line = line.strip()
        if line == "NEWLINE":
            breaks += 1
        elif line.startswith(".STRINGMAP"):
            if breaks >= 2 and paragraph:
                lore_paragraphs.append("\n".join(paragraph))
                paragraph = []
            paragraph.append(json.loads(line.split(",", 1)[1].strip()))
            breaks = 0
    if paragraph:
        lore_paragraphs.append("\n".join(paragraph))

    village = tilemap(args.source, "0C8070.tmx")
    objects = [
        {"kind": "house_left", "x": 3, "y": 0, "source_map": "house-left.tmx", "tileset_index": 3},
        {"kind": "house_right", "x": 13, "y": 0, "source_map": "0C8188.tmx", "tileset_index": 2},
        {"kind": "house_shadow_left", "x": 8, "y": 2, "source_map": "house-shadow.tmx", "tileset_index": 4},
        {"kind": "house_shadow_right", "x": 18, "y": 2, "source_map": "house-shadow.tmx", "tileset_index": 4},
        {"kind": "tree", "x": 11, "y": 10, "source_map": "tree.tmx", "tileset_index": 5},
        {"kind": "tree", "x": 12, "y": 10, "source_map": "tree.tmx", "tileset_index": 5},
    ]
    for obj in objects:
        obj["map"] = tilemap(args.source, obj["source_map"])
    npc_raw = src.db(10, "L0A8D33")
    npc_names = ["mycen", "kliff", "tobin", "gray", "lukas"]
    npc_data = []
    for index, name in enumerate(npc_names):
        raw = npc_raw[index * 9 : index * 9 + 9]
        npc_data.append({"id": name, "actor_id": index + 2, "position": [raw[1], raw[0]],
                         "sprite_id": raw[6], "raw_movement_flags": raw[7], "raw_interaction_flags": raw[8],
                         "raw": raw, "provenance": [src.ref(10, "L0A8D33"), src.ref(10, "L0A8B49")],
                         "confidence": "source_NPC_table_and_loader"})
    village.update({"id": "ram_village", "map_id": 1, "name_ja": "ラムのむら", "name_zh": "拉姆村", "objects": objects,
                    "spawn": [5, 10], "npcs": npc_data, "coordinate_order": "x,y; source records store y,x",
                    "layout_provenance": src.ref(12, "L0CA23D"),
                    "spawn_provenance": src.ref(13, "L0D853B"),
                    "confidence": "source_map_and_composition; spawn and initial NPC positions source_verified"})
    trigger_raw = src.db(13, "L0DB55E")
    script_labels = ["L0DB697", "L0DB6AA", "L0DB6B4", "L0DB6BE", "L0DB6C8", "L0DB746"]
    opening = {
        "schema_version": 1, "source_project": "https://github.com/minirop/fe2", "source_commit": "956365ef33c63751e7afd03f05e600d7728549da",
        "title": {"name_ja": "ファイアーエムブレム 外伝", "name_zh": "火焰之纹章 外传", "options_ja": ["さいしょから", "つづきをする"],
                  "options_provenance": [src.ref(11, "L0BA11C"), src.ref(11, "L0BA123")]},
        "attract_intro": {"presentation": "original_scrolling_lore; optional title attract sequence", "paragraphs_ja": lore_paragraphs,
                          "source": src.ref(4, "L04A0C2"), "confidence": "source_text; paragraph boundaries follow repeated NEWLINE controls"},
        "chapter": {"number": 1, "title_ja": "ソフィアへ!", "title_zh": "向索菲亚进军！", "source": src.ref(12, "L0CB13D")},
        "village": village, "characters": characters, "dialogues": dialogues, "dialogues_by_label": by_label,
        "npc_actor_ids": {"alm": 1, "mycen": 2, "kliff": 3, "tobin": 4, "gray": 5, "lukas": 6},
        "initial_party": ["alm"], "default_recruit_order": ["lukas", "gray", "tobin", "kliff"],
        "flow": [
            {"id": "training", "dialogue": "training", "script_label": "L0DB697", "automatic": True},
            {"id": "lukas_report", "dialogue": "lukas_report", "actor": "lukas", "set_flag": "heard_lukas", "required": True},
            {"id": "mycen_refusal", "dialogue": "mycen_refusal", "actor": "mycen", "requires": ["heard_lukas"], "set_flag": "mycen_refused", "required": True},
            {"id": "alm_volunteers", "dialogue": "alm_volunteers", "actor": "lukas", "requires": ["mycen_refused"], "recruit": "lukas", "set_flag": "joined_deliverance", "required": True},
            {"id": "gray_joins", "dialogue": "gray_joins", "actor": "gray", "requires": ["joined_deliverance"], "recruit": "gray", "required": False},
            {"id": "tobin_joins", "dialogue": "tobin_joins", "actor": "tobin", "requires": ["joined_deliverance"], "recruit": "tobin", "required": False},
            {"id": "kliff_joins", "dialogue": "kliff_joins", "actor": "kliff", "requires": ["joined_deliverance"], "recruit": "kliff", "required": False},
            {"id": "depart", "requires": ["joined_deliverance"], "next": "ram_woods"},
        ],
        "original_event_triggers": [{"x_or_npc_sentinel": trigger_raw[i], "y_or_actor": trigger_raw[i + 1], "script_index": trigger_raw[i + 2]} for i in range(0, len(trigger_raw), 3)],
        "original_event_scripts": {label: {"raw": src.db(13, label), "provenance": src.ref(13, label)} for label in script_labels},
        "provenance": [src.ref(12, "L0CA13F"), src.ref(12, "L0CA23D"), src.ref(13, "L0DB55E"), src.ref(13, "L0DB61B")],
        "music_ids": {"title": 113, "opening": 114, "ram_village": 166},
        "unverified": ["Original title menu exact glyphs and save-slot layout", "NPC random walk timing and direction flags", "Named flow flags summarize original bitfield states; exact state transitions require runtime verification", "Recruitment order is player selected, not fixed"],
    }

    first_map = tilemap(args.source, "ram-woods.tmx")
    enemy_template = src.db(8, "L089B50")
    enemy_stats = src.db(15, "L0FED8D")
    enemy_positions = coordinates(src.db(8, "L08ABCE"), 5)
    player_positions = coordinates(src.db(8, "L08ABB9"))
    enemies = []
    for i, pos in enumerate(enemy_positions):
        enemies.append({"id": f"brigand_{i + 1}", "name_ja": "さんぞく", "name_zh": "山贼", "class": "brigand", "class_id": 14,
                        "level": 1, "hp": enemy_stats[5], "max_hp": enemy_stats[5], "strength": enemy_stats[0], "skill": enemy_stats[1],
                        "speed": enemy_stats[2], "luck": enemy_stats[3], "defence": enemy_stats[4], "move": move_values[13],
                        "item_id": 0, "exp_value": enemy_stats[6], "raw_ai_flags": enemy_template[4], "raw_magic_flags": 0, "position": pos,
                        "provenance": [src.ref(8, "L089474"), src.ref(8, "L089B50"), src.ref(15, "L0FED8D"), src.ref(8, "L08ABCE")],
                        "confidence": "source_tables_and_level1_enemy_constructor"})
    terrain_types = src.db(15, "L0FE8DE")
    terrain_avoid = src.db(15, "L0FECEE")
    movement_blob = src.db(15, "L0FEADF")
    # The first 43 bytes are the remainder of the 22-entry pointer table.
    # Movement records start at $EB0A, 43 bytes after label $EADF.
    movement_start = 0xEB0A - 0xEADF
    assert movement_start == 43
    movement_costs = {str(cid): movement_blob[movement_start + (cid - 1) * 22 : movement_start + cid * 22]
                      for cid in [6, 14, 21]}
    assert all(len(costs) == 22 for costs in movement_costs.values())
    first = {
        "schema_version": 1, "id": "ram_woods", "map_id": 1, "chapter": 1, "battle_number": 1,
        "name_ja": "ラムのもり", "name_zh": "拉姆森林", "source_commit": opening["source_commit"],
        "map": first_map, "characters": {k: v for k, v in characters.items() if k != "mycen"},
        "initial_party": ["alm"], "party_order": ["alm", "lukas", "gray", "tobin", "kliff"],
        "party_order_note": "Use actual village recruitment order; this is a suggested all-recruited order, not an original forced roster.",
        "player_positions": player_positions, "enemy_positions": enemy_positions, "enemies": enemies,
        "coordinate_order": "x,y; source deployment records already use x,y (L089E7C)",
        "terrain": {"tile_categories": {str(tile): terrain_types[tile] for tile in sorted(set(first_map["tiles"]))},
                    "avoid_by_category": terrain_avoid, "movement_by_class_and_category": movement_costs,
                    "impassable_movement_value": 255,
                    "provenance": [src.ref(15, "L0FE8DE"), src.ref(15, "L0FECEE"), src.ref(15, "L0FEADF")],
                    "confidence": "source_table_and_movement_consumers; labels for categories and recovery pending"},
        "music_ids": {"player_phase": 161, "enemy_phase": 164, "battle": 134, "unit_death": 144, "level_up": 129},
        "ui_ja": {key: {"text": src.strings(11, label)[0], "provenance": src.ref(11, label)}
                  for key, label in {"attack": "L0B9FD1", "wait": "L0B9FE3", "end_turn": "L0B9F53", "retreat": "L0B9F48",
                                     "auto_assault": "L0B9F2B", "gather": "L0B9F31", "status": "L0B9F39", "suspend": "L0B9F41",
                                     "player_phase": "L0B9FC1", "enemy_phase": "L0B9FE7", "level": "L0B9FB2", "hp": "L0B9FB8",
                                     "strength": "L0B9F63", "skill": "L0B9F6D", "speed": "L0B9F77", "luck": "L0B9F81",
                                     "defence": "L0B9F8A", "move": "L0B9F94", "game_over": "L0BA027", "no_item": "L0BA000"}.items()},
        "rules": {"victory": "all_enemies_defeated", "defeat": "alm_defeated", "turn_order": ["player", "enemy"],
                  "permadeath": True, "recruitable_villagers_optional": True,
                  "weapon_triangle": False, "default_attack_range": [1, 1], "starting_items": [],
                  "confidence": "design_verified_where_supported; individual combat formulas require source tracing and comparison"},
        "provenance": [src.ref(2, "L_TILEMAPS"), src.ref(8, "L0892A1"), src.ref(8, "L0893C2"), src.ref(8, "L08AB11"), src.ref(8, "L089E33"), src.ref(8, "L08A31B")],
        "first_battle_identity": {"confidence": "confirmed_by_source_route_and_independent_original-game-map_catalog", "evidence": ["Alm chapter1 route L0892A1 begins map id1", "L_TILEMAPS[1] is L02860B -> ram-woods.bin", "Position lookup indexes map id minus1 -> L08ABB1", "Enemy group0 and1 both L089474 (5 Lv1 brigands)", "Original-game sprite catalog labels Ram Woods Map01; Southern Zofia1 Map05"], "catalog_url": "https://www.spriters-resource.com/nes/fireemblemgaidenjpn/"},
        "unverified": ["Exact RNG/frame timing", "Full AI bitfield semantics", "Exact original experience arithmetic", "Terrain recovery timing and arithmetic", "Victory transition music and original post-battle UI need comparison", "Original deployment uses recruit order and placement table; slot filtering requires runtime confirmation"],
    }
    first["rules"].update({
        "default_weapons": {"non_archer_index": 0, "archer_sniper_bow_knight_index": 1, "first_battle_index": 0,
                            "first_battle_might": 0, "first_battle_weight": 0, "first_battle_hit": 90, "first_battle_critical": 0},
        "physical_formulae": {"attack_speed": "max(speed - weapon_weight, 0)",
                              "damage": "clamp(strength + weapon_might - defender_defence, 1, 60); minimum1 on successful hit",
                              "hit": "clamp(skill + weapon_hit - defender_attack_speed - defender_terrain_avoid, 0, 100)",
                              "critical": "floor((floor((skill + luck) / 2) + weapon_critical) / 2)",
                              "hit_roll": "0..99 < hit", "critical_roll": "critical > 0 and 0..99 <= critical",
                              "follow_up": "one additional strike for strictly higher attack speed"},
        "experience": {"full": "ceil(class_coefficient[player_class-1] * level_coefficient[player_level-1] * enemy_exp_value / 100), cap100",
                       "kill": "full", "no_damage": "1", "nonkill": "ceil(full * enemy_hp_lost / (2 * enemy_max_hp))",
                       "timing": "once per entire exchange, including enemy-phase player counters",
                       "normal_opening_brigand_exp_value": 30, "level_cap": 20,
                       "easy_mode": "doubles full before final cap100 and damage-fraction scaling"},
        "growth": {"roll_order": ["hp", "defence", "luck", "speed", "skill", "strength"], "roll_range": [1, 99],
                   "success": "roll < growth_rate", "normal_increment": 1, "angel_ring_item": 55, "angel_ring_increment": 2,
                   "stat_cap": 40, "hp_cap": 52,
                   "consolation": "HP increment only when all six rolls fail; a successful capped roll suppresses consolation"},
        "terrain_recovery": {"tile_id": 218, "hp_per_phase": 5, "maximum": "max_hp", "dead_units": "skip",
                             "timing": "once at beginning of each side phase for units on that side",
                             "scope": "first-battle pink recovery tile; not every category15 tile"},
        "confidence": "opening physical combat, growth, experience, and recovery derived from source; full AI pending",
    })
    for bank, label, topic in [(9, "L0981B0", "hit formula"), (9, "L098238", "attack speed"),
                               (9, "L0983D8", "critical formula"), (9, "L0984E2", "hit comparison"),
                               (9, "L098526", "critical comparison"), (9, "L098730", "minimum1 damage"),
                               (9, "L098B74", "experience class/level scaling"), (9, "L0980CC", "nonkill damage scaling and miss1"),
                               (9, "L098898", "growth reverse order and caps"), (15, "L0FF426", "default weapon selection"),
                               (3, "L0390EA", "phase recovery"), (3, "L0390F0", "phase recovery"),
                               (3, "L0390F3", "phase recovery"), (3, "L03910F", "phase recovery"), (3, "L0391A5", "phase recovery")]:
        ref = src.ref(bank, label)
        ref["topic"] = topic
        first["provenance"].append(ref)
    first["unverified"] = [item for item in first["unverified"]
                            if item not in ["Exact original experience arithmetic", "Terrain recovery timing and arithmetic"]]
    for name, obj in [("opening.json", opening), ("first_battle.json", first)]:
        (args.output / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"opening_dialogue_pages": sum(map(len, dialogues.values())), "first_map": [first_map["width"], first_map["height"]], "enemy_count": len(enemies), "player_positions": player_positions[:5], "outputs": [str(args.output / n) for n in ("opening.json", "first_battle.json")]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

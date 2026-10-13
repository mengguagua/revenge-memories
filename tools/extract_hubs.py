#!/usr/bin/env python3
"""Decode original noncombat layouts, actors, event programs and dialogue.

The exported event bytecode is game data; the native Godot event runner owns
all movement, dialogue and state changes. No CPU/ROM is loaded at runtime.
"""
from pathlib import Path
import json
import re
import struct
from extract_opening import Source, tilemap

ROOT = Path(__file__).resolve().parents[1]
SRC = Path('/private/tmp/fe2-analysis-20261012')
s = Source(SRC)
rom = (SRC / 'fe2.nes').read_bytes()

def read(bank, address, count):
    offset = 16 + bank * 16384 + (address & 16383)
    return list(rom[offset:offset + count])

def ptrs(bank, label):
    return re.findall(r'\.dw\s+(\w+)', s.block(bank, label))

def db(bank, label):
    return s.db(bank, label)

def terminated(bank, label, stride):
    raw = db(bank, label)
    result = []
    for i in range(0, len(raw), stride):
        if raw[i] == 239:
            break
        assert i + stride <= len(raw), (label, i, stride)
        result.append(raw[i:i + stride])
    return result

def program(raw):
    instructions = []
    actor = None
    i = 0
    while i < len(raw):
        if actor is None:
            if raw[i] == 239:
                break
            actor = raw[i]
            i += 1
        opcode = raw[i]
        start = i
        i += 1
        group, value = opcode >> 4, opcode & 15
        op = {'actor': actor, 'opcode': opcode, 'offset': start}
        if opcode == 0:
            actor = None
            continue
        if group == 0:
            op.update(kind='wait', ticks=8 * value)
        elif group == 1:
            op.update(kind='face', direction=value)
        elif group in (2, 13):
            op.update(kind='walk', steps=value, ticks_per_tile=8 if group == 2 else 16)
        elif group == 3:
            op.update(kind='dialogue', dialogue_id=raw[i]); i += 1
        elif group == 4:
            op.update(kind='special', effect=value)
        elif group == 5:
            op.update(kind='audio', sound_id=raw[i]); i += 1
        elif group in (6, 11):
            op.update(kind='actor_sprite', sprite_id=raw[i] if value else 0)
            i += bool(value)
        elif group == 7:
            op.update(kind='recruit', character_id=raw[i]); i += 1
        elif group == 8:
            op.update(kind='spawn_actor', template=value)
        elif group == 9:
            op.update(kind='choice', choice_id=value)
        elif group == 10:
            op.update(kind='flag', flag_id=raw[i]); i += 1
        elif group == 12:
            op.update(kind='camera', position=[raw[i + 1], raw[i]]); i += 2
        elif group == 14:
            op.update(kind='chapter_transition', transition=value)
        elif group == 15:
            op.update(kind='item_give')
        else:
            raise ValueError(opcode)
        instructions.append(op)
    return instructions

def dialogue(bank, label):
    # Some labelled short replies intentionally fall through to following text.
    block = s.block(bank, label, stop=True)
    pages, lines = [], []
    speaker = 0
    face = 0
    def flush():
        nonlocal lines
        if lines:
            pages.append({'speaker_id': speaker, 'face_id': face,
                          'text_ja': '\n'.join(lines), 'source_label': label})
            lines = []
    for raw in block.splitlines()[1:]:
        line = raw.split(';')[0].strip()
        if line.startswith('FACE '):
            flush(); face = s.defines[line.split()[1]]
        elif line.startswith('NAME '):
            flush(); speaker = s.defines[line.split()[1]]
        elif line in ('WAIT_CLICK', 'PAGE', '.db STOP'):
            flush()
        elif line.startswith('.STRINGMAP'):
            lines.append(json.loads(line.split(',', 1)[1].strip()))
    flush()
    return pages

def main():
    original_maps = []
    for label in ptrs(12, 'L0C8000'):
        filename = re.search(r'\.INCBIN "([^"]+)"', s.block(12, label))[1].replace('.bin', '.tmx')
        original_maps.append(tilemap(SRC, filename))
    for label in ptrs(2, 'L02B4D8'):
        filename = re.search(r'\.INCBIN "([^"]+)"', s.block(2, label))[1].replace('.bin', '.tmx')
        original_maps.append(tilemap(SRC, filename))
    layouts = {}
    for index, label in enumerate(ptrs(12, 'L0CA13F'), 1):
        raw = db(12, label)
        # Opcode6 calls L0FCD44, replacing the initial dimensions from the
        # composition header with the background's own height/width header.
        width, height = raw[1] + 1, raw[0] + 1
        if raw[2] == 6:
            background = original_maps[raw[3]]
            width, height = background['width'], background['height']
        tiles = [0] * (width * height)
        def set_tile(x, y, tile):
            if 0 <= x < width and 0 <= y < height:
                tiles[y * width + x] = tile
        def stamp(map_index, x, y):
            m = original_maps[map_index]
            for yy in range(m['height']):
                for xx in range(m['width']):
                    set_tile(x + xx, y + yy, m['tiles'][yy * m['width'] + xx])
            return m['width'], m['height']
        i, commands = 2, []
        while raw[i] != 239:
            op = raw[i]; i += 1
            size = {0: 5, 1: 3, 2: 4, 3: 4, 4: 4, 5: 3, 6: 1}[op]
            a = raw[i:i + size]; i += size
            commands.append([op] + a)
            if op == 0:
                for y in range(a[0], a[2] + 1):
                    for x in range(a[1], a[3] + 1): set_tile(x, y, a[4])
            elif op == 1:
                stamp(a[2], a[1], a[0])
            elif op == 2:
                y, x, repeats, part = a
                for repeat in range(repeats & 127):
                    dx, dy = stamp(part, x, y)
                    if repeats & 128: y += dy
                    else: x += dx
            elif op == 3:
                for x in range(a[1], a[2] + 1): set_tile(x, a[0], a[3])
            elif op == 4:
                for y in range(a[0], a[2] + 1): set_tile(a[1], y, a[3])
            elif op == 5:
                set_tile(a[1], a[0], a[2])
            else:
                stamp(a[0], 0, 0)
        layouts[str(index)] = {'id': index, 'width': width, 'height': height, 'tiles': tiles,
                               'source_label': label, 'commands': commands}
    actor_tables = ptrs(10, 'L0A8C6B')
    trigger_tables = ptrs(13, 'L0DB4FA')
    features = ptrs(13, 'L0DBD70')
    portals = ptrs(13, 'L0DBA50')
    for hub_id, room in layouts.items():
        hub = int(hub_id)
        room['portals'] = [{'position': [a[1], a[0]], 'destination': a[2], 'spawn': [a[4], a[3]]}
                           for a in terminated(13, portals[hub - 1], 5)] if hub <= len(portals) else []
        room['features'] = [{'position': [a[1], a[0]], 'kind': a[2], 'value': a[3]}
                           for a in terminated(13, features[hub - 1], 4)] if hub <= len(features) else []
        room['edges'] = read(10, 0xBD8F + (hub - 1) * 4, 4)
        room['world_owner'] = 48 + read(13, 0xB9AC + hub - 1, 1)[0] if hub <= 85 else 0
        room['actors'] = []
        if hub <= 50:
            room['triggers'] = [{'actor_id': a[1] if a[0] == 255 else 0,
                                 'position': [a[1], a[0]], 'script_id': a[2]}
                                for a in [db(13, trigger_tables[hub - 1])[i:i + 3]
                                          for i in range(0, len(db(13, trigger_tables[hub - 1])), 3)] if len(a) == 3]
            for variant in range(2):
                raw = db(10, actor_tables[(hub - 1) * 2 + variant])
                actors = []; i = 0; actor = 2
                while i < len(raw) and raw[i] != 239:
                    if raw[i] == 254:
                        i += 1; actor += 1; continue
                    a = raw[i:i + 9]; i += 9
                    actors.append({'actor_id': actor, 'position': [a[1], a[0]], 'sprite_id': a[6],
                                   'wander_bounds': [a[4], a[2], a[5], a[3]], 'movement_flags': a[7], 'interaction_flags': a[8]})
                    actor += 1
                room['actors'].append(actors)
            room['npc_dialogues'] = [read(12, 0xB2BC + (hub - 1) * 14 + i * 2, 2) for i in range(7)]
    script_data = {str(i): {'source_label': label, 'raw': db(13, label), 'instructions': program(db(13, label))}
                   for i, label in enumerate(ptrs(13, 'L0DB61B'))}
    texts = {}
    for bank, pointer, offset in [(3, 'DIALOGUES_POINTER', 0), (10, 'L0AA707', 76)]:
        for index, label in enumerate(ptrs(bank, pointer), offset):
            texts[str(index)] = {'id': index, 'source': s.ref(bank, label), 'pages': dialogue(bank, label)}
    flags = [db(10, label) for label in ptrs(10, 'L0A8000')]
    flag_seed = db(15, 'L0FFB8F')
    flag_seed = {str(flag_seed[i] + 1): flag_seed[i + 1] for i in range(0, len(flag_seed) - 1, 2)}
    entries = read(12, 0xB578, 64)
    hub_ids = db(13, 'L0DB98C')[:32]
    world_entries = {str(49 + i): {'hub_id': hub, 'spawn': [entries[i * 2 + 1], entries[i * 2] & 63],
                                      'facing': ((entries[i * 2] >> 6) + 1)} for i, hub in enumerate(hub_ids)}
    transition_labels = ptrs(13, 'L0DBEF0')
    transitions = {str(i + 1): {'hub_id': db(13, label)[0], 'spawn': [db(13, label)[2], db(13, label)[1]]}
                   for i, label in enumerate(transition_labels)}
    spawn_templates = {}
    for i, label in enumerate(ptrs(13, 'L0DB96B'), 1):
        a = db(13, label)
        spawn_templates[str(i)] = {'position': [a[1], a[0]], 'sprite_id': a[6], 'movement_flags': a[7], 'interaction_flags': a[8]}
    raw_encounters = read(13, 0xBA01, 0xBA50 - 0xBA01)
    room_encounters = {}
    for i in range(0, len(raw_encounters) - 1, 3):
        a = raw_encounters[i:i+3]
        if a[0] == 239: break
        room_encounters[str(a[0])] = {'encounter': a[1] & 127, 'raw_encounter': a[1], 'visited_bit': a[2]}
    patterns = {}
    for i, label in enumerate(ptrs(13, 'L0D8D2D')):
        a = db(13, label)
        patterns[str(i)] = a[:a.index(239)]
    result = {'source_revision': '956365ef33c63751e7afd03f05e600d7728549da',
              'rooms': layouts, 'world_entries': world_entries, 'scripts': script_data, 'dialogues': texts,
              'flag_updates': flags, 'initial_trigger_masks': flag_seed, 'chapter_transitions': transitions,
              'feature_types': {'0': 'item', '1': 'spring', '2': 'sign_dialogue', '3': 'sluice_state', '4': 'passage_state', '6': 'gate_state'},
              'spring_effects': db(13, 'L0DBED2'), 'spring_initial_uses': [n for byte in db(15, 'L0FFBBA')[:-1] for n in [byte & 15, byte >> 4]],
              'tile_actions': db(13, 'L0D8B11'), 'tile_change_patterns': patterns,
              'spawn_templates': spawn_templates, 'room_encounters': room_encounters,
              'source_rules': {'edges':'north,south,west,east; 0 blocked, 1..49 world node, >=50 next hub = value-50',
                               'choice_opcode':'0x9N shows chapter N title/save menu; it does not select a recruit or branch the event program.',
                               'courier_opcode':'0xFN transfers one carried item to opposite army convoy; cancellation does not consume courier.',
                               'room36_shared_triggers':'Rooms35/36 share room37 trigger table but have no enabled masks; retain original coordinates.'},
              'source_notes': ['L0CA7F9 composes noncombat room from opcode0..6; dimensions inclusive',
                               'L0A8B49 selects NPC variant from hide byte bit7 and removes mask-selected actors',
                               'L0CAC6E chooses NPC dialogue from 14-byte row and talk-state bit',
                               'L0D949E dispatches event high nibble; event programs are native data',
                               'L0FFACC applies original AND/OR masks to actor, conversation and trigger flags']}
    (ROOT / 'data/hubs.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print({'rooms': len(layouts), 'scripts': len(script_data), 'dialogues': len(texts),
           'pages': sum(len(t['pages']) for t in texts.values())})

if __name__ == '__main__':
    main()

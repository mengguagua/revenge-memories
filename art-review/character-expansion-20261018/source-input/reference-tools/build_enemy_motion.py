#!/usr/bin/env python3
"""Decode original enemy reference frames only; never changes game/art outputs.

Enemy background writes use a different ROM pointer table and are cumulative.
This is a source decoder, not a method for generating replacement artwork.
"""
from pathlib import Path
import copy
import hashlib
import json
import math
import sys
from PIL import Image

HERE = Path(__file__).resolve()
PRODUCTION = HERE.parents[2]
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO / 'tools'))
from extract_full_graphics import Source, oam_entries, bg_entries, make_sheet
from extract_full_effects import run_effect, effect_image
from fe2_source_cpu import CPU

OUT = PRODUCTION / 'source-input/enemy-motion'
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = Source(REPO / '.reference/fe2-source-956365ef')
GRAPHICS = json.loads((PRODUCTION / 'source-input/legacy/graphics.json').read_text())
EFFECTS = json.loads((PRODUCTION / 'source-input/legacy/full_animation_effects.json').read_text())
CATALOG = json.loads((PRODUCTION / 'catalog/class-catalog.json').read_text())
ACTIVE_ENEMY_CLASSES = {1, 2, 3, 6, 7, 8, 11, 12, 15, 22}


def native_selection(cid, item, key=''):
    """Run the original enemy weapon/class branch itself, stopping before the next actor."""
    cpu = CPU(SOURCE.rom)
    m = cpu.mem
    cpu.x = 1
    m[0x306], m[0x307], m[0x321] = 21, cid, item
    # Original Duma state keys: the legacy beam/eye aliases had item0 but their
    # intended source states are item39/item19. Keep those contexts explicit.
    duma_state = None
    if cid == 21:
        if item == 39 or '_beam' in key:
            m[0x3a6], m[0x3a8] = 1, 2
            item = 39
        elif item == 19 or '_eye' in key:
            m[0x3a6], m[0x3a8] = 0, 1
            item = 19
        else:
            m[0x3a6], m[0x3a8] = 0, 0
            item = 38
        m[0x321] = item
        duma_state = {'exposed_03a6': m[0x3a6], 'attack_type_03a8': m[0x3a8]}
    refs = {}
    for zero_page, table in [(0, 'L058F1C'), (2, 'L058FDD')]:
        ref = SOURCE.b[5][table]['dw'][cid - 1]
        address = int(ref[3:], 16)
        m[zero_page], m[zero_page+1] = address & 255, address >> 8
        refs[table] = ref
    # The selector reaches this point after writing program/effect/idle. The
    # normal DEX would continue to another actor; the hook returns to the caller.
    cpu.hooks[(5, 0x8c0f)] = lambda runner: None
    instruction_count = cpu.call(5, 0x8a17)
    return {'program': m[0x3ec], 'effect': m[0x3ef], 'idle': m[0x3bf],
            'item': item, 'source_entry': 'bank005:L058A17',
            'stop_before': 'bank005:L058C0F', 'lookup_tables': refs,
            'physical_enemy': {'0302': 0, '0303': 0}, 'duma_state': duma_state,
            'instructions': instruction_count}


def digest(im):
    return hashlib.sha256(im.tobytes()).hexdigest()


class EnemyBody:
    def __init__(self, cid):
        self.cid = cid
        self.entry = GRAPHICS['battle'][f'class_{cid}_enemy']
        idx = cid - 1
        b5 = SOURCE.b[5]
        self.bank = SOURCE.b[15]['L0FE436']['db'][idx]
        typ = SOURCE.b[15]['L0FE44C']['db'][idx]
        bank = SOURCE.b[self.bank]
        chrid = b5['L058EAE']['db'][idx]
        self.tiles = SOURCE.tiles[chrid]
        palid = b5['L058EDA']['db'][idx] & 127
        self.palette = b5[b5['L05BCF1']['dw'][palid]]['db'][:4]
        table = SOURCE.ptr(self.bank, 0xbfd0 + 2 * typ)
        refs = bank.get(table, {}).get('dw', [])
        entries = [oam_entries(bank[ref]['db'], self.tiles, self.palette) for ref in refs]
        self.cutoff = len(entries)
        base = SOURCE.ptr(self.bank, 0xbffa)
        bgmap = SOURCE.ptr(self.bank, 0xbffe)
        bgids = bank[bank[bgmap]['dw'][typ]]['db']
        self.bgrefs = [bank[base]['dw'][pose] for pose in bgids]
        entries += [bg_entries(bank[ref]['db'], self.tiles, self.palette, True) for ref in self.bgrefs]
        sheet, self.size, self.anchor, bounds = make_sheet(entries)
        w, h = self.size
        self.frames = [sheet.crop((i*w, 0, (i+1)*w, h)) for i in range(len(entries))]
        self.native_count = len(self.frames)
        self.seen = {digest(im): i for i, im in enumerate(self.frames) if i >= self.cutoff}
        self.transitions = {}
        # Exact raw-sheet reconstruction check against the frozen current source.
        original = PRODUCTION / 'source-input/legacy-assets' / self.entry['path'].removeprefix('res://')
        expected = Image.open(original).convert('RGBA')
        assert expected.size == sheet.size and expected.tobytes() == sheet.tobytes(), (cid, 'raw reference mismatch')
        self.metadata = {
            'class_id': cid, 'side': 'enemy', 'frame_size': self.size,
            'anchor': self.anchor, 'columns': 16, 'source_oam_frame_count': self.cutoff,
            'background_frame_offset': self.cutoff, 'source_chr': chrid,
            'source_palette': self.palette, 'default_facing': 'left',
            'idle_source_pose': self.entry['idle_source_pose'],
            'sequences': {'idle': self.entry['sequences']['idle']},
            'native_base_frames': self.native_count, 'raw_reconstruction_exact': True,
            'source_note': 'Enemy CHR/palette and enemy BG pointer table; BG normalized left; cumulative opaque tile replacement.'
        }

    def compile(self, rows, idle=None):
        if idle is None:
            idle = self.entry['idle_source_pose']
        initial = self.cutoff + idle
        current = initial
        previous = -1
        background = False
        ax, ay = self.anchor
        for row in rows:
            pose = row['source_pose']
            if not row['background']:
                current = pose
                previous = -1
                background = False
            elif not background or pose != previous:
                base = current if background else initial
                identity = (base, pose)
                if identity not in self.transitions:
                    frame = self.frames[base].copy()
                    tiles = bg_entries(SOURCE.b[self.bank][self.bgrefs[pose]]['db'], self.tiles, self.palette, True)
                    for x, y, tile in tiles:
                        frame.paste(tile, (x+ax, y+ay-32))
                    checksum = digest(frame)
                    if checksum not in self.seen:
                        self.seen[checksum] = len(self.frames)
                        self.frames.append(frame)
                    self.transitions[identity] = self.seen[checksum]
                current = self.transitions[identity]
                background = True
                previous = pose
            row['frame'] = current

    def export(self):
        w, h = self.size
        sheet = Image.new('RGBA', (w*16, h*math.ceil(len(self.frames)/16)))
        for i, frame in enumerate(self.frames):
            sheet.paste(frame, ((i%16)*w, (i//16)*h))
        path = OUT / f'class-{self.cid}-enemy.png'
        sheet.save(path, optimize=True)
        self.metadata.update(path=str(path.relative_to(PRODUCTION)), frames=len(self.frames))
        return self.metadata


def main():
    bodies = {}
    variants = {}
    sprites = copy.deepcopy(EFFECTS['sprites'])
    records = []
    excluded = []
    selector_evidence = []
    for sprite in sprites.values():
        sprite['path'] = 'source-input/legacy-assets/' + sprite['path'].removeprefix('res://')
    selected = [c for c in CATALOG['classes'] if c['class_id'] <= 22]
    for cl in selected:
        cid = cl['class_id']
        profile = cl['battle_profiles']['enemy']
        body = EnemyBody(cid)
        bodies[str(cid)] = body
        # Legacy effect traces were initially recorded using a generic idle0.
        # Re-run each trace from its weapon-specific native start, then compile
        # with the same base; changing only the BG composition is insufficient.
        specifications = [(v['key'], EFFECTS['variants'][v['key']]) for v in profile['compiled_variants']]
        if profile['bound_attack_schedule_kind'] == 'melee':
            key = f'original_class_{cid}_enemy_normal'
            specifications.insert(0, (key, {'source_item_id': 0, 'formation': 'near', 'opponent_class_id': 21}))
        jobs = []
        for key, original_trace in specifications:
            item = int(original_trace.get('source_item_id', 0))
            chosen = native_selection(cid, item, key)
            selector_evidence.append({'key': key, 'class_id': cid, **chosen})
            if cid == 6 and item in [4, 7]:
                excluded.append({'key': key, 'class_id': cid, 'status': 'reference_unreachable',
                  'reason': 'Current ItemRules.can_use forbids class6 items4/7 for either side; native selection is program41/idle12, not the former forced program25.',
                  'native_selection': chosen})
                continue
            formation = original_trace.get('formation', 'near')
            opponent = 4 if key.endswith('_vs_heavy') else None
            trace = run_effect(SOURCE, cid, 'enemy', chosen['program'], chosen['effect'], chosen['item'], chosen['idle'], formation, opponent)
            trace['native_selection'] = chosen
            trace['production_scope'] = 'active_enemy_class' if cid in ACTIVE_ENEMY_CLASSES else 'reference_only_inactive_enemy_class'
            assert trace['contact_count'] == 1, (key, trace['contact_count'])
            for row in trace['frames']:
                for state in row['effects']:
                    im, size, anchor, ref = effect_image(SOURCE, state)
                    identity = 'native-' + hashlib.sha256(im.tobytes()+str(anchor).encode()).hexdigest()[:14]
                    if identity not in sprites:
                        path = OUT / 'effects' / f'{identity}.png'
                        path.parent.mkdir(exist_ok=True)
                        im.save(path, optimize=True)
                        sprites[identity] = {'path':str(path.relative_to(PRODUCTION)), 'frame_size':size, 'frames':1, 'anchor':anchor, 'source_oam':ref, 'default_facing':'left', 'flip_origin_offset':[16,0]}
                    keep = {k:state[k] for k in ['position','flip','priority']}
                    state.clear()
                    state.update(keep, sprite=identity)
            body.compile(trace['frames'], chosen['idle'])
            trace['source_program_address'] = SOURCE.b[5]['L05B025']['dw'][trace['source_program_id']]
            variants[key] = trace
            jobs.append((key, trace))
            records.append({'key':key, 'class_id':cid, 'ticks':len(trace['frames']), 'contact_tick':trace['contact_tick'], 'contact_count':trace['contact_count'], 'selected_idle':chosen['idle'], 'initial_source_pose':trace['frames'][0]['source_pose'], 'native_selection':chosen})
        used = sorted({r['frame'] for _, t in jobs for r in t['frames']} | set(body.entry['sequences']['idle']))
        canonical = {}
        alias = {}
        for frame_id in used:
            key = digest(body.frames[frame_id])
            canonical.setdefault(key, frame_id)
            alias[str(frame_id)] = canonical[key]
        body.metadata.update(required_source_frames=used, exact_pixel_aliases=alias, unique_art_frames=sorted(set(alias.values())),
          production_required=cid in ACTIVE_ENEMY_CLASSES,
          production_scope='active_enemy_class'if cid in ACTIVE_ENEMY_CLASSES else'reference_only_inactive_enemy_class')
        print(f'class {cid}: {len(jobs)} traces, {len(used)} used frames, {len(set(alias.values()))} exact distinct', flush=True)
    used_effects = {effect['sprite'] for trace in variants.values() for row in trace['frames'] for effect in row['effects']}
    sprites = {key:value for key,value in sprites.items() if key in used_effects}
    data = {'native_fps':60.0988, 'source_revision':CATALOG['source_revision'], 'rom_sha256':hashlib.sha256(SOURCE.rom).hexdigest(), 'original_bodies':{cid:body.export() for cid,body in bodies.items()}, 'variants':variants, 'sprites':sprites,
      'active_enemy_class_ids':sorted(ACTIVE_ENEMY_CLASSES), 'excluded_variants':excluded,
      'source_note':'Original references only. Weapon/class selection is executed in native selector; traces and cumulative BG use the same selected idle. Only active_enemy_class_ids are production scope.'}
    (OUT/'full-enemy-motion.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    (OUT/'reference-audit.json').write_text(json.dumps({'records':records, 'bodies':data['original_bodies']},ensure_ascii=False,indent=2)+'\n')
    (OUT/'selector-evidence.json').write_text(json.dumps({'routine':'bank005:L058A17 to before L058C0F','physical_enemy':True,'active_enemy_class_ids':sorted(ACTIVE_ENEMY_CLASSES),'records':selector_evidence,'excluded_variants':excluded,'ally_frozen_source_unchanged':True},ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    main()

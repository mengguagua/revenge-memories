#!/usr/bin/env python3
"""Append only the six missing source Recover40/class11 variants."""
from pathlib import Path
import argparse, hashlib, json
from PIL import Image
from extract_full_effects import run_effect, effect_image
from extract_full_graphics import Source, bg_entries
from extract_graphics import ROOT, OUT, DATA, save


def main(source_root):
    src = Source(source_root)
    meta = json.loads(DATA.read_text())
    path = ROOT / 'data/full_animation_effects.json'
    effects = json.loads(path.read_text())
    base = meta['battle']['class_11_ally']
    records, new_assets, reused_assets = [], [], set()
    canonical = {}
    aliases = {}
    # The full extractor deduplicates palettes whose unused entries differ.
    # Match decoded RGBA pixels, size and anchor exactly before adding a PNG.
    for key, sprite in effects['sprites'].items():
        with Image.open(ROOT / sprite['path'].removeprefix('res://')) as image:
            rgba = image.convert('RGBA')
            identity = (rgba.size, hashlib.sha256(rgba.tobytes()).hexdigest(), tuple(sprite['anchor']))
        canonical.setdefault(identity, key)
    for formation in ['near', 'far_ally', 'far_enemy']:
        for opponent in [None, 4]:
            key = 'class_11_ally_item_40' + ('' if formation == 'near' else '_' + formation) + ('_vs_heavy' if opponent == 4 else '')
            variant = run_effect(src, 11, 'ally', 29, 5, 40, base['idle_source_pose'], formation, opponent)
            assert variant['contact_count'] == 1 and variant['contact_tick'] == 89
            for frame in variant['frames']:
                frame['frame'] = frame['source_pose'] + (base['background_frame_offset'] if frame['background'] else 0)
                assert frame['frame'] < base['frames']
                for state in frame['effects']:
                    identity = json.dumps([state.get('table_type'), state.get('source_pose'), state.get('source_oam'), state['chr_bank'], state['palettes']], separators=(',', ':'))
                    asset_key = hashlib.sha1(identity.encode()).hexdigest()[:14]
                    if asset_key in aliases:
                        asset_key = aliases[asset_key]
                    elif asset_key not in effects['sprites']:
                        image, size, anchor, ref = effect_image(src, state)
                        pixel_key = (image.size, hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest(), tuple(anchor))
                        if pixel_key in canonical:
                            aliases[asset_key] = canonical[pixel_key]
                            asset_key = canonical[pixel_key]
                            reused_assets.add(asset_key)
                        else:
                            asset_path = OUT / 'effects' / (asset_key + '.png')
                            save(image, asset_path, meta, kind='full_effect_oam', source_oam=ref, chr_bank=state['chr_bank'], palette_indices=state['palettes'], frame_size=size, frame_count=1)
                            effects['sprites'][asset_key] = {'path': 'res://' + str(asset_path.relative_to(ROOT)), 'frame_size': size, 'frames': 1, 'anchor': anchor, 'source_oam': ref, 'default_facing': 'left', 'flip_origin_offset': [16, 0]}
                            canonical[pixel_key] = asset_key
                            new_assets.append({'path': str(asset_path.relative_to(ROOT)), 'pixels': size, 'bytes': asset_path.stat().st_size})
                    else:
                        reused_assets.add(asset_key)
                    state['sprite'] = asset_key
                    for field in ['palettes', 'chr_bank', 'table_type', 'source_pose', 'source_oam', 'source_bank']:
                        state.pop(field, None)
            effects['variants'][key] = variant
            records.append({'key': key, 'ticks': len(variant['frames']), 'contact_tick': variant['contact_tick'], 'source_class': 11, 'source_program': 29, 'source_effect': 5, 'source_item': 40})
    # Background poses are relative tile uploads, not complete pictures.
    # Recover29 uses partial uploads50..56; preserve unchanged body tiles and
    # replace explicitly uploaded blank tiles when compiling complete frames.
    idx = 10
    bank = src.b[15]['L0FE436']['db'][idx]
    typ = src.b[15]['L0FE44C']['db'][idx]
    bgbase = src.ptr(bank, 0xbffa)
    bgmaps = src.ptr(bank, 0xbffc)
    pose_ids = src.b[bank][src.b[bank][bgmaps]['dw'][typ]]['db']
    body_source = effects['variants']['class_11_ally_item_40']['frames']
    body_paths, body_map, affected = [], None, []
    for name, entry in list(meta['battle'].items()):
        if (name.startswith('class_11_ally') or name == 'promoted_celica_ally') and not entry.get('recovery_body'):
            palette_id = entry['source_palette_id']
            palette_ref = src.b[5]['L05BCF1']['dw'][palette_id]
            palette = src.b[5][palette_ref]['db'][:4]
            tiles = src.tiles[src.b[5]['L058E98']['db'][idx]]
            width, height = entry['frame_size']
            anchor = entry['anchor']
            canvas = Image.new('RGBA', (width, height))
            unique, seen, mapping = [], {}, []
            for frame in body_source:
                assert frame['background']
                ref = src.b[bank][bgbase]['dw'][pose_ids[frame['source_pose']]]
                for x, y, tile in bg_entries(src.b[bank][ref]['db'], tiles, palette):
                    canvas.paste(tile, (x + anchor[0], y + anchor[1] - 32))
                digest = hashlib.sha256(canvas.tobytes()).hexdigest()
                if digest not in seen:
                    seen[digest] = len(unique)
                    unique.append(canvas.copy())
                mapping.append(seen[digest])
            if body_map is None: body_map = mapping
            else: assert body_map == mapping
            sheet = Image.new('RGBA', (width * len(unique), height))
            for i, frame_image in enumerate(unique): sheet.paste(frame_image, (i * width, 0))
            body_key = name + '_recover40_body'
            body_path = OUT / 'battle' / (body_key + '.png')
            meta['assets'] = [a for a in meta['assets'] if a.get('path') != 'res://' + str(body_path.relative_to(ROOT))]
            save(sheet, body_path, meta, kind='full_class_recovery', class_id=11, side='ally', frame_size=[width,height], frame_count=len(unique), source_palette=palette_ref, source_program=29, source_item=40)
            raw_path = ROOT / '.reference/generated/round7-recovery' / body_path.name
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_bytes(body_path.read_bytes())
            body_entry = dict(entry)
            body_entry.update({'path':'res://' + str(body_path.relative_to(ROOT)), 'frames':len(unique), 'sequences':{'idle':[0]}, 'recovery_body':True, 'background_frame_offset':0, 'source_oam_frame_count':0, 'background_pose_count':len(unique)})
            body_entry.pop('spell_body_variants',None)
            body_entry.pop('palette_variants',None)
            body_entry.setdefault('spell_variants', {})['40'] = 'class_11_ally_item_40'
            meta['battle'][body_key] = body_entry
            entry.setdefault('spell_variants', {})['40'] = 'class_11_ally_item_40'
            entry.setdefault('spell_body_variants', {})['40'] = body_key
            body_paths.append({'path':str(body_path.relative_to(ROOT)), 'pixels':list(sheet.size), 'bytes':body_path.stat().st_size, 'unique_body_frames':len(unique), 'source_palette':palette_ref})
            affected.append(name)
    for record in records:
        variant = effects['variants'][record['key']]
        assert [(f['source_pose'],f['background']) for f in variant['frames']] == [(f['source_pose'],f['background']) for f in body_source]
        for tick, frame in enumerate(variant['frames']): frame['frame'] = body_map[tick]
    path.write_text(json.dumps(effects, ensure_ascii=False, separators=(',', ':')) + '\n')
    DATA.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
    result = {'source': ['bank005 L058AAD -> L058BC3 -> L058B39', 'L058F5C program29', 'L058F93 effect5'], 'variants': records, 'graphics': affected, 'new_assets': new_assets, 'body_assets':body_paths, 'body_uploads':'Cumulative original background tile writes, replacing explicit transparent blank tiles; no invented poses.', 'exactly_reused_sprite_count': len(reused_assets), 'runtime_rom_or_cpu': False}
    (ROOT / 'reports/round7-recovery-source-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'variants': len(records), 'graphics': affected, 'new_assets': new_assets, 'body_assets':body_paths, 'exactly_reused_sprite_count': len(reused_assets)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, default=ROOT / '.reference/fe2-source-956365ef')
    main(parser.parse_args().source)

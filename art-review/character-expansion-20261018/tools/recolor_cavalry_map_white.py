#!/usr/bin/env python3
"""Palette-only cavalry revision; accepted animation pixels never move."""
import json
from PIL import Image
from revise_cavalry_map import ROOT, MAPPING, digest, signature

REVISION = 'cavalry-map-white-v2-20261021'
OUT = ROOT / REVISION
PREVIOUS = ROOT / 'cavalry-map-anchor-palette-v1-20261021'
OLD_PALETTE = json.loads((PREVIOUS/'asset-manifest.json').read_text())['palette']
PALETTE = ['1c2027', '34373d', '59616a', 'bcc8d0', 'e8edeb', 'f1f0e8',
           '293a54', '3e5578', '7589a7', '59483c', '95785e', 'ba9b67',
           'dcc08f', 'b38a6f', 'e3b78e', 'fff9e9']
REMAP = {tuple(bytes.fromhex(a)): tuple(bytes.fromhex(b)) for a,b in zip(OLD_PALETTE,PALETTE)}


def create():
    OUT.mkdir(exist_ok=True)
    baseline = OUT/'baseline.json'
    if not baseline.exists():
        mapping = json.loads(MAPPING.read_text())
        assert mapping['revision'] == PREVIOUS.name
        data = json.loads((ROOT/'demos/gallery-data.json').read_text())
        baseline.write_text(json.dumps({'mapping':mapping,
            'digests':{a['id']:a['contentDigest'] for a in data['actions']},
            'timelines':{a['id']:signature(a) for a in data['actions']}},ensure_ascii=False,indent=2)+'\n')
    mapping = json.loads(baseline.read_text())['mapping']
    assets = []

    def save(image, relative, purpose):
        path = OUT/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        image.save(path,optimize=True)
        assets.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),
            'bytes':path.stat().st_size,'sha256':digest(path),
            'visible_colors':len({p[:3] for p in image.getdata() if p[3]})})
        return '../../../'+path.relative_to(ROOT).as_posix()

    for scenario in mapping['scenarios']:
        key = scenario['id'];w,h = scenario['output_frame_size']
        atlas = Image.new('RGBA',(w*len(scenario['frame_mapping']),h))
        for rec in scenario['frame_mapping']:
            source = (MAPPING.parent/rec['output_path']).resolve()
            image = Image.open(source).convert('RGBA')
            result = Image.new('RGBA',image.size)
            result.putdata([(*REMAP[p[:3]],p[3]) if p[3] else p for p in image.getdata()])
            assert result.getchannel('A').tobytes() == image.getchannel('A').tobytes()
            i = rec['source_index'];path = save(result,f'{key}/frame-{i:03}.png','allied cavalry palette only / more white and slightly stronger color')
            atlas.alpha_composite(result,(i*w,0))
            rec.update(palette_source=source.relative_to(ROOT).as_posix(),palette_source_sha256=digest(source),
                path=path,output_path=path,bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],revision=REVISION,
                kind='exact_palette_replacement_of_accepted_motion')
        scenario.update(output_atlas=save(atlas,key+'-atlas.png','offline review atlas / palette only'),
            output_atlas_bytes=assets[-1]['bytes'],revision=REVISION,
            motion_acceptance='user_confirmed_cavalry-map-anchor-palette-v1-20261021',
            review_note='已确认的固定中心和马腿动作逐像素保留；仅将灰色中间调提亮为柔和白色，蓝色、米金和肤色小幅恢复饱和度。待机与四向共用最多16色，未接入游戏。')
    mapping.update(revision=REVISION,art_mode='exact palette replacement; accepted animation, alpha and registration unchanged')
    MAPPING.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    prior = json.loads((PREVIOUS/'asset-manifest.json').read_text())
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,
        'image_generation_invoked':False,'chat_image_output':False,'palette':PALETTE,
        'previous_palette':OLD_PALETTE,'palette_changes':dict(zip(OLD_PALETTE,PALETTE)),
        'motion_reference':PREVIOUS.name,'geometry_changed':False,
        'idle_fixed_point':prior['idle_fixed_point'],'walk_registration':prior['walk_registration'],
        'assets':assets},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'frames':14,'palette_only':True},ensure_ascii=False))


if __name__=='__main__':
    create()

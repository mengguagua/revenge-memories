#!/usr/bin/env python3
"""Review-only integer translation; preserve every pixel of the side gait."""
import hashlib
import json
from PIL import Image
from revise_gold_knight_idle import ROOT

REVISION='gold-knight-side-anchor-v5-20261020'
OUT=ROOT/REVISION
OFFSETS={2:5,3:-1,6:-5,7:1}
ANCHOR_PATCH=(62,41,66,45)


def create():
    (OUT/'frames').mkdir(exist_ok=True)
    before=json.loads((OUT/'baseline-mapping.json').read_text())
    scenario=next(s for s in before['scenarios'] if s['id']=='tactical-walk')
    mapping_dir=ROOT/'professions/class-7-ally/maps'
    original={r['source_index']:(mapping_dir/r['output_path']).resolve() for r in scenario['frame_mapping']}
    frames={}
    records=[]
    for index,dx in OFFSETS.items():
        source=Image.open(original[index]).convert('RGBA')
        source.save(OUT/f'source/previous-{index:03}.png',optimize=True)
        frame=Image.new('RGBA',(128,96));frame.alpha_composite(source,(dx,0))
        # No clipping or deformation: applying the inverse translation must
        # reproduce every opaque source pixel and its full color values.
        inverse=Image.new('RGBA',(128,96));inverse.alpha_composite(frame,(-dx,0))
        visible_source=Image.new('RGBA',(128,96));visible_source.alpha_composite(source)
        assert inverse.tobytes()==visible_source.tobytes()
        path=OUT/f'frames/frame-{index:03}.png';frame.save(path,optimize=True)
        records.append({'source_index':index,'translation':[dx,0],
                        'path':path.relative_to(ROOT).as_posix(),'source':original[index].relative_to(ROOT).as_posix(),
                        'size':list(frame.size),'bytes':path.stat().st_size,
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        frames[index]=frame
    for a,b in [(2,3),(6,7)]:
        patch=frames[a].crop(ANCHOR_PATCH)
        assert patch.tobytes()==frames[b].crop(ANCHOR_PATCH).tobytes()
        assert len(set(patch.getdata()))>=3 and all(p[3] for p in patch.getdata())
    for right,left in [(2,6),(3,7)]:
        assert frames[right].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()==frames[left].tobytes()
    atlas=Image.new('RGBA',(128*8,96))
    for index in range(8):
        frame=frames.get(index)
        if frame is None:frame=Image.open(original[index]).convert('RGBA')
        atlas.alpha_composite(frame,(128*index,0))
    atlas.save(OUT/'walk-atlas.png',optimize=True)
    (OUT/'asset-manifest.json').write_text(json.dumps({
        'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
        'method':'lossless integer horizontal registration only; no redraw/rescale/vertical translation',
        'fixed_point':[64,43],'fixed_multicolor_patch':list(ANCHOR_PATCH),
        'translations':{str(k):[v,0] for k,v in OFFSETS.items()},
        'timing':'16 ticks per pose; original order retained',
        'preserved':['pose pixels','leg action','vertical positions','palette','shadow','up','down','accepted idle'],
        'frames':records,
    },ensure_ascii=False,indent=2)+'\n')
    return frames


if __name__=='__main__':create()

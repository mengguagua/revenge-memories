#!/usr/bin/env python3
"""Normalize whole generated structures, retaining source aspect and alpha."""
from pathlib import Path
import json, subprocess
from PIL import Image

R = Path(__file__).resolve().parents[1]
SOURCE = R / 'source/battlefield-0.3.0/structures-source.png'
OUT = R / 'assets/battlefield-0.3.0'
SPECS = [
    ('coastal_keep', (4,4), (0,0,435,442)),
    ('ruined_watchtower', (2,3), (440,65,705,442)),
    ('sea_gate', (4,3), (710,130,1152,444)),
    ('sea_cliff', (4,4), (1156,145,1448,444)),
    ('hill_granary', (3,2), (0,445,365,737)),
    ('village_clinic', (3,2), (375,445,715,735)),
    ('command_pavilion', (2,2), (725,445,1100,735)),
    ('mine_adit', (3,2), (1104,445,1448,740)),
    ('quay_warehouse', (3,2), (0,742,392,1045)),
    ('fishing_cottage', (2,2), (398,747,730,1046)),
    ('breached_wall', (5,3), (728,742,1128,1060)),
    ('ancient_arch', (4,4), (1130,747,1448,1060)),
]

def main():
    src = Image.open(SOURCE).convert('RGBA')
    records = []
    (OUT/'modules').mkdir(parents=True, exist_ok=True)
    for name, footprint, box in SPECS:
        im = src.crop(box)
        im.putalpha(im.getchannel('A').point(lambda v: 255 if v >= 96 else 0))
        bbox = im.getbbox()
        assert bbox and bbox[0] > 0 and bbox[1] > 0 and bbox[2] < im.width and bbox[3] < im.height, (name, bbox)
        im = im.crop(bbox)
        width, height = [v*16 for v in footprint]
        scale = min((width-4)/im.width, (height-4)/im.height)
        size = (round(im.width*scale), round(im.height*scale))
        im = im.resize(size, Image.Resampling.NEAREST)
        alpha = im.getchannel('A')
        im = im.convert('RGB').quantize(colors=48, dither=Image.Dither.NONE).convert('RGBA')
        im.putalpha(alpha)
        whole = Image.new('RGBA', (width,height))
        whole.alpha_composite(im, ((width-size[0])//2, height-size[1]-2))
        path = OUT/'modules'/f'{name}.png'
        whole.save(path)
        subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(path)],check=True)
        records.append(dict(name=name, footprint=list(footprint), size=[width,height],
                            source_box=list(box), source_opaque_box=list(bbox),
                            opaque_box=list(whole.getbbox()), bytes=path.stat().st_size,
                            path='res://assets/battlefield-0.3.0/modules/'+path.name))
    for name, source in {
        'tactical_house':'world_tiles/modules/village.png',
        'tactical_snow_house':'world_tiles/modules/snow_village.png',
        'tactical_fort':'world_tiles/modules/fort.png',
        'tactical_tent':'world_tiles/modules/camp.png',
        'tactical_store':'battle_tiles/modules/grain_store.png',
        'tactical_deck_post':'chapter2/modules/captain_cabin.png',
        'visit_door':'battle_tiles/modules/clinic_door.png',
        'visit_lighthouse':'chapter2/modules/lighthouse.png',
        'camp_palisade':'battle_tiles/modules/north_fence.png',
    }.items():
        generated={'tactical_fort':'fort','tactical_tent':'tent','tactical_deck_post':'deck'}.get(name)
        relative='source/tactical-buildings-0.3.4/'+generated+'-source.png' if generated else 'assets/'+source
        raw=Image.open(R/relative).convert('RGBA')
        raw.putalpha(raw.getchannel('A').point(lambda a:255 if a>=96 else 0))
        box=raw.getbbox();im=raw.crop(box)
        footprint=(2,3) if name=='visit_lighthouse' else (3,1) if name=='camp_palisade' else (1,1)
        width,height=footprint[0]*16,footprint[1]*16
        tactical=name.startswith('tactical_')
        limit=width if tactical else width-2 if name=='camp_palisade' else 14 if width==16 else width-4
        scale=min(limit/im.width,(height if tactical else height-2)/im.height)
        if not tactical:scale=min(scale,1)
        im=im.resize((max(1,round(im.width*scale)),max(1,round(im.height*scale))),Image.Resampling.NEAREST)
        if generated:
            alpha=im.getchannel('A');im=im.convert('RGB').quantize(colors=20,dither=Image.Dither.NONE).convert('RGBA');im.putalpha(alpha)
        whole=Image.new('RGBA',(width,height));whole.alpha_composite(im,((width-im.width)//2,height-im.height-(0 if tactical else 1)))
        path=OUT/'modules'/f'{name}.png';whole.save(path)
        subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(path)],check=True)
        records.append(dict(name=name,footprint=list(footprint),size=[width,height],source=relative,
            opaque_box=list(whole.getbbox()),whole_source=True,bytes=path.stat().st_size,path='res://assets/battlefield-0.3.0/modules/'+path.name))
    (OUT/'modules.json').write_text(json.dumps({'source':'source/battlefield-0.3.0/structures-source.png',
        'source_mode':'built-in imagegen','native_tile_size':16,'modules':records},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'modules':len(records),'max_bytes':max(m['bytes'] for m in records)}))

if __name__ == '__main__':
    main()

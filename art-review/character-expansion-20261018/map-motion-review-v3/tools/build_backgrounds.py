"""Copy and assemble actual project ground tiles for isolated sprite comparison."""
from pathlib import Path
from PIL import Image
import json,subprocess,hashlib
V=Path(__file__).resolve().parents[1];ROOT=V.parents[2];A=ROOT/'actual';G='/opt/homebrew/bin/magick'
O=V/'reference/grounds';O.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text())
def run(*args):subprocess.run([G,*map(str,args)],check=True)
def local(p):return A/p.removeprefix('res://')
records=[]
def region(name,atlas,layers,x,y,w=64,h=48):
    im=Image.open(atlas);columns=im.width//16
    tiles={};cmd=['-size',f'{w}x{h}','xc:none'];placements=[]
    for layer in layers:
        for ty in range(y//16,(y+h+15)//16):
            for tx in range(x//16,(x+w+15)//16):
                ident=layer[ty][tx]
                if ident is None or ident<0:continue
                if ident not in tiles:
                    tile=O/f'{name}-tile-{ident}.png';run(atlas,'-crop',f'16x16+{ident%columns*16}+{ident//columns*16}','+repage',tile);tiles[ident]=tile
                px,py=tx*16-x,ty*16-y
                cmd.extend([tiles[ident],'-geometry',f'{px:+d}{py:+d}','-compose','Over','-composite'])
                placements.append({'tile':ident,'xy':[px,py]})
    dst=O/f'{name}.png';run(*cmd,dst)
    assert Image.open(dst).size==(w,h)
    assert Image.open(dst).convert('RGBA').getchannel('A').getextrema()==(255,255)
    records.append({'name':name,'output':str(dst.relative_to(V)), 'source_atlas':str(atlas.relative_to(ROOT)), 'source_sha256':hashlib.sha256(atlas.read_bytes()).hexdigest(),'source_pixel_crop':[x,y,w,h],'native_size':[w,h],'placements':placements,'display':'same native pixel density as character; nearest-neighbour integer display scale, no stretched texture'})

# Starting story hub P00 uses cobble variants (x*3+y)%4 in story_hub.gd.
pack=read(A/'assets/battle_tiles/battle-tiles.json')
floor=[[pack['base']['cobble'][(x*3+y)%4]for x in range(14)]for y in range(9)]
region('story-P00-cobble',A/'assets/battle_tiles/battle-tiles.png',[floor],16,96)
records[-1]['source_layout']='actual/core/story_hub.gd:287-294; P00 cobble floor, exact variant pattern'
# First battle deployment area, using the active stage art_atlas/art_layers.
stage=read(A/'data/stages/M11.json')
region('tactical-M11',local(stage['art_atlas']),stage['art_layers'],72,188)
records[-1]['source_layout']='actual/data/stages/M11.json art_layers; area around first player deployment [6,13]'
# Formal world route near W02. Terrain/road layers copied directly, without a
# landmark under the comparison actor (same occupied-camp rule as main.gd).
world=read(A/'data/formal_world.json')
region('world-W02-route',local(world['atlas']),world['layers'][:-1],200,808)
records[-1]['source_layout']='actual/data/formal_world.json layers excluding landmark overlay; W02 approach'
(V/'background-provenance.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
run('montage','-font','/System/Library/Fonts/STHeiti Medium.ttc',*[V/r['output']for r in records],'-tile','3x1','-geometry','64x48+4+4','-background','#26343b',V/'reviews/project-grounds.png')
run(V/'reviews/project-grounds.png','-filter','point','-resize','400%',V/'reviews/project-grounds-4x.png')
print('Prepared actual project P00 story floor, M11 tactical ground, formal world W02 route')

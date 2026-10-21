#!/usr/bin/env python3
"""Replace only the three flying-unit bitmaps in the Holy Light review."""
import copy, hashlib, json
from PIL import Image, ImageDraw
from build_gallery import ROOT

REVISION = 'holy-light-firefly-v1-20261021'
OUT = ROOT / REVISION
FLYING = ['489a22d743e81f', '5ee993bdd4164d', '15889806b31e64']
COLORS = {
    'outline': '#213338', 'shell': '#3c5551', 'shell_light': '#70886b',
    'wing_edge': '#657e83', 'wing': '#a9bfbb', 'wing_light': '#d7e2d5',
    'abdomen': '#8da35f', 'light': '#cbd786', 'core': '#f2e9ba',
}
WINGS = [
    [[(28,27),(17,9),(17,-10),(23,-9),(29,7),(32,26)],
     [(31,26),(39,2),(47,-7),(52,-4),(49,10),(36,31)]],
    [[(29,28),(13,12),(6,12),(4,20),(12,29),(28,35)],
     [(32,28),(45,10),(55,9),(59,17),(50,28),(35,35)]],
    [[(29,29),(12,27),(5,33),(7,40),(17,42),(31,36)],
     [(34,30),(51,23),(59,27),(60,34),(50,40),(37,38)]],
]


def sprite(phase):
    # One fixed insect body, with only the wings changing phase. The tall
    # first source cell has its anchor eight native pixels lower.
    shift = 32 if phase == 0 else 0
    im = Image.new('RGBA', (64, 96 if phase == 0 else 64))
    draw = ImageDraw.Draw(im)
    def points(poly):return [(x,y+shift) for x,y in poly]
    def polygon(poly, fill, outline=None):
        draw.polygon(points(poly),fill=fill,outline=outline)
    def line(poly, fill, width=1):
        draw.line(points(poly),fill=fill,width=width)
    def ellipse(rect, fill, outline=None, width=1):
        draw.ellipse((rect[0],rect[1]+shift,rect[2],rect[3]+shift),fill=fill,outline=outline,width=width)
    # Pixel-edged, restrained lantern glow, kept inside the original cell.
    ellipse((32,34,52,55),(188,209,126,24))
    ellipse((35,37,49,52),(210,222,143,42))
    # Three paired legs and two antennae distinguish an insect from a fairy.
    for leg in [[(29,29),(21,30),(17,35)],[(33,33),(25,39),(25,44)],
                [(37,38),(34,45),(36,49)],[(30,28),(37,22),(41,22)],
                [(34,32),(43,29),(47,31)],[(38,37),(46,37),(49,41)]]:
        line(leg,COLORS['outline'],2)
    for wing in WINGS[phase]:
        polygon(wing,(*bytes.fromhex(COLORS['wing'][1:]),215),COLORS['wing_edge'])
        root,tip=wing[0],wing[2]
        line([root,tip],(*bytes.fromhex(COLORS['wing_light'][1:]),230),1)
        mid=wing[3]
        line([root,mid],(*bytes.fromhex(COLORS['wing_edge'][1:]),180),1)
    # Diagonal segmented abdomen, with a warm yellow-green light organ.
    polygon([(29,29),(35,28),(41,34),(47,43),(46,49),(40,52),(35,47),(30,39)],COLORS['outline'])
    polygon([(31,31),(35,30),(39,35),(41,40),(36,43),(32,38)],COLORS['abdomen'])
    polygon([(37,39),(42,37),(46,43),(44,49),(40,50),(36,46)],COLORS['light'])
    polygon([(40,42),(43,41),(45,45),(43,48),(40,48),(38,45)],COLORS['core'])
    line([(33,35),(38,32)],COLORS['shell'],2)
    line([(35,40),(41,36)],COLORS['shell'],2)
    line([(38,44),(44,40)],COLORS['abdomen'],1)
    # Thorax, small head, reflective eye and short antennae.
    ellipse((24,22,35,33),COLORS['outline'])
    ellipse((26,24,33,30),COLORS['shell'])
    line([(27,24),(30,24),(32,27)],COLORS['shell_light'],1)
    line([(23,20),(16,15),(14,10)],COLORS['outline'],2)
    line([(26,18),(26,12),(29,8)],COLORS['outline'],2)
    ellipse((19,15,29,24),COLORS['outline'])
    ellipse((21,16,27,22),COLORS['shell'])
    ellipse((20,17,22,19),COLORS['wing_light'])
    line([(24,22),(27,24)],COLORS['shell_light'],1)
    return im


def preview():
    from export_gallery import font
    sheet=Image.new('RGB',(1008,530),(14,21,26));draw=ImageDraw.Draw(sheet)
    draw.text((504,16),'圣光 · 萤火虫飞行单位',font=font(22),anchor='mt',fill='#e9f0f0')
    for row,bg in enumerate([(32,45,53),(220,222,216)]):
        for phase in range(3):
            x=16+332*phase;y=58+230*row
            draw.rounded_rectangle((x,y,x+312,y+214),radius=10,fill=bg)
            title=['振翅 · 上举','振翅 · 展开','振翅 · 下压'][phase]
            ink='#e9f0f0'if row==0 else '#26323b'
            draw.text((x+156,y+12),title,font=font(16),anchor='mt',fill=ink)
            im=Image.open(OUT/f'frames/firefly-{phase:03}.png').convert('RGBA')
            # Register every body at the same point rather than centering
            # each silhouette, which would make the insect jump vertically.
            im=im.resize((128,im.height*2),Image.Resampling.NEAREST)
            anchor_y=128 if phase==0 else 64
            sheet.paste(im,(x+92,y+124-anchor_y),im)
            bounds=draw.textbbox((x+156,y+12),title,font=font(16),anchor='mt')
            assert bounds[0]>x+16 and bounds[2]<x+296
    sheet.save(OUT/'firefly-poses.png',optimize=True)


def create():
    (OUT/'frames').mkdir(parents=True,exist_ok=True)
    data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    mapping_paths={side:ROOT/f'professions/class-15-{side}/battle/frame_mapping.json'for side in ['enemy','ally']}
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'mappings':{side:json.loads(p.read_text())for side,p in mapping_paths.items()}},ensure_ascii=False,indent=2)+'\n')
    inventory=[]
    for phase in range(3):
        path=OUT/f'frames/firefly-{phase:03}.png';im=sprite(phase);im.save(path,optimize=True)
        inventory.append({'phase':phase,'path':path.relative_to(ROOT).as_posix(),'size':list(im.size),
          'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
          'anchor_output':[32,64 if phase==0 else 32],'visible_bounds':list(im.getbbox())})
    contracts=[]
    before=json.loads(baseline.read_text())
    for side,path in mapping_paths.items():
        # Extend the preceding review as a new version; its three previously
        # revised spells remain byte-for-byte identical.
        mapping=before['mappings'][side]
        previous=(path.parent/mapping['review_timeline']).resolve()
        timeline=json.loads(previous.read_text())
        timeline['holy_light_revision']=REVISION
        replacement={}
        for phase,key in enumerate(FLYING):
            old=('native-'if side=='enemy'else'')+key
            new=f'review-holy-firefly-{side}-{phase}'
            meta=copy.deepcopy(data['effects'][old]);meta['path']='../../../'+inventory[phase]['path']
            timeline['effects'][new]=meta;replacement[old]=new
        for a in data['actions']:
            if a['profile']!=f'professions-class-15-{side}-battle' or '_item_26'not in a['key']:continue
            rows=copy.deepcopy(a['frames'])
            for row in rows:
                for effect in row.get('effects',[]):effect['sprite']=replacement.get(effect['sprite'],effect['sprite'])
            timeline['actions'][a['key']]={'source_frames_sha256':hashlib.sha256(json.dumps(a['frames'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),
              'frames':rows,'note':'圣光仅把三相基础飞行单位替换为发光尾部的萤火虫；原五单位数量、轨迹、位置、振翅切换节奏、施法姿势、命中和消散效果全部保持。',
              'events':{'bitmap_only':True,'replacement_effects':replacement,'contact_tick_kept':a['contactTick']}}
            contracts.append({'actor':side,'spell_id':26,'spell':'圣光','action':a['id'],'ticks':len(rows),'contact_tick':a['contactTick'],'additional_hits':0})
        target=OUT/f'{side}-motion.json';target.write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':'))+'\n')
        current=json.loads(path.read_text());current['review_timeline']='../../../'+target.relative_to(ROOT).as_posix();current['holy_light_revision']=REVISION
        path.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
    preview()
    path=OUT/'firefly-poses.png'
    inventory.append({'purpose':'three wing phases on dark and light backgrounds','path':path.relative_to(ROOT).as_posix(),
      'size':list(Image.open(path).size),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,'colors':COLORS,'assets':inventory},ensure_ascii=False,indent=2)+'\n')
    (OUT/'spell-action-contract.json').write_text(json.dumps({'source':'actual/data/legacy/rules_full.json ID26; docs2/完整游戏设定.md','gameplay_modified':False,'contracts':contracts},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'sprites':3,'actions':len(contracts)},ensure_ascii=False))


if __name__=='__main__':create()

#!/usr/bin/env python3
"""Arrow Rain review: coherent medieval arrows and twice the flying units."""
import copy, hashlib, json
from PIL import Image, ImageDraw
from build_gallery import ROOT

REVISION = 'arrow-rain-medieval-v1-20261021'
OUT = ROOT / REVISION
FLYING = ['143c2ff72f4e68','c5de617ed6816b','ced934935c0fcf']
PALETTES = {
    'ally': {'outline':'#315c81','shaft':'#7198b1','metal':'#acc4d2','light':'#edf1ec','feather':'#cbdbe1'},
    'enemy':{'outline':'#202c4a','shaft':'#34476d','metal':'#50688e','light':'#9badc3','feather':'#667e9f'},
}
EXTRA_Y = 6


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def arrow(side, phase, direction):
    # Original 48x16 cell at 4x. The visible envelope remains at x25..47,
    # preserving the native registration and the existing projectile paths.
    im=Image.new('RGBA',(192,64));draw=ImageDraw.Draw(im);c=PALETTES[side]
    # Goose-feather vanes, with veins, binding and a narrow nock.
    draw.polygon([(161,46),(172,39),(183,39),(177,46)],fill=c['feather'],outline=c['outline'])
    draw.polygon([(161,50),(172,57),(183,57),(177,50)],fill=c['metal'],outline=c['outline'])
    draw.line([(169,44),(178,41)],fill=c['light']if phase!=1 else c['metal'],width=1)
    draw.line([(169,52),(178,55)],fill=c['feather'],width=1)
    # Slender shaft, with restrained axial highlight rather than noisy bands.
    draw.line([(116,48),(184,48)],fill=c['outline'],width=4)
    draw.line([(119,47),(181,47)],fill=c['shaft'],width=2)
    draw.line([(129,47),(158,47)],fill=c['metal']if phase!=2 else c['feather'],width=1)
    draw.polygon([(166,47),(177,46),(182,47),(178,49),(166,49)],fill=c['feather'])
    draw.line([(163,45),(163,51)],fill=c['outline'],width=2)
    draw.line([(165,46),(165,50)],fill=c['metal'],width=1)
    draw.line([(183,46),(185,47),(185,49),(183,50)],fill=c['outline'],width=1)
    # Western medieval broadhead and short socket; no modern fins or colors.
    draw.polygon([(100,48),(115,41),(113,46),(121,46),(121,50),(113,50),(115,55)],fill=c['outline'])
    draw.polygon([(103,48),(114,43),(111,47),(119,47),(119,49),(111,49),(114,53)],fill=c['metal'])
    draw.line([(104,48),(114,46)],fill=c['light'],width=1)
    draw.line([(112,48),(120,48)],fill=c['shaft'],width=1)
    if direction>0:
        # Mirror the glyph inside its occupied envelope, not the padded cell.
        # Mirroring the entire cell would shift the arrow off its native lane.
        box=im.getbbox();glyph=im.crop(box).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        im=Image.new('RGBA',im.size);im.alpha_composite(glyph,box[:2])
    return im


def save(path,im,inventory,purpose):
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),
      'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'visible_bounds':list(im.getbbox())if im.getbbox()else None})


def movement_direction(rows):
    previous={}
    for row in rows:
        current={e['position'][1]:e['position'][0]for e in row.get('effects',[])if e['sprite'].removeprefix('native-')in FLYING}
        for lane,x in current.items():
            delta=x-previous.get(lane,x)
            if 0<abs(delta)<=16:return 1 if delta>0 else -1
        previous=current
    raise ValueError('No native arrow flight direction found')


def preview(inventory):
    from export_gallery import font
    sheet=Image.new('RGB',(1248,704),(14,21,26));draw=ImageDraw.Draw(sheet)
    draw.text((624,16),'箭雨 · 中世纪西式箭 · 六支同场',font=font(22),anchor='mt',fill='#e9f0f0')
    for row,bg in enumerate([(32,45,53),(220,222,216)]):
        for column,side in enumerate(['ally','enemy']):
            x=16+616*column;y=58+324*row;draw.rounded_rectangle((x,y,x+600,y+306),radius=10,fill=bg)
            label=('友军 · 蓝白'if side=='ally'else'敌军 · 暗蓝')+(' · 暗底'if row==0 else' · 浅底')
            ink='#e9f0f0'if row==0 else '#26323b';draw.text((x+300,y+12),label,font=font(18),anchor='mt',fill=ink)
            for n,direction in enumerate([-1,1]):
                im=arrow(side,0,direction);im=im.crop(im.getbbox());im=im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)
                sheet.paste(im,(x+300-im.width//2,y+48+n*112),im)
                draw.text((x+300,y+132+n*112),'← 左向'if direction<0 else'右向 →',font=font(14),anchor='mt',fill=ink)
            bounds=draw.textbbox((x+300,y+12),label,font=font(18),anchor='mt');assert bounds[0]>x+16 and bounds[2]<x+584
    save(OUT/'arrow-design.png',sheet,inventory,'both factions and directions on dark and light backgrounds')


def create():
    OUT.mkdir(exist_ok=True);data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    paths={side:ROOT/f'professions/class-15-{side}/battle/frame_mapping.json'for side in ['enemy','ally']};baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'actions':{a['id']:{k:a.get(k)for k in ['frames','revisedFrames','fps','origin','contactTick','viewport','closeCamera']}for a in data['actions']},
          'mappings':{side:json.loads(path.read_text())for side,path in paths.items()}},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());inventory=[];contracts=[]
    for side,path in paths.items():
        previous=before['mappings'][side];timeline=json.loads((path.parent/previous['review_timeline']).resolve().read_text());timeline['arrow_rain_revision']=REVISION
        ids={}
        for phase,key in enumerate(FLYING):
            source_key=('native-'if side=='enemy'else'')+key
            for direction in [-1,1]:
                label='left'if direction<0 else'right';target=OUT/f'{side}/arrow-{phase}-{label}.png';save(target,arrow(side,phase,direction),inventory,'medieval arrow / coherent faction palette')
                eid=f'review-arrow-rain-{side}-{phase}-{label}';meta=copy.deepcopy(data['effects'][source_key]);meta['path']='../../../'+target.relative_to(ROOT).as_posix();meta['default_facing']=label
                timeline['effects'][eid]=meta;ids[phase,direction]=eid
        for a in data['actions']:
            if a['profile']!=f'professions-class-15-{side}-battle' or '_item_28'not in a['key']:continue
            rows=copy.deepcopy(a['frames']);direction=movement_direction(rows);replacements={};extra_count=0
            for row in rows:
                copies=[]
                for effect in row.get('effects',[]):
                    key=effect['sprite'].removeprefix('native-')
                    if key not in FLYING:continue
                    local_direction=-direction if effect.get('flip')else direction
                    new=ids[FLYING.index(key),local_direction];replacements[effect['sprite']]=new;effect['sprite']=new
                    extra=copy.deepcopy(effect);extra['position'][1]+=EXTRA_Y;copies.append(extra);extra_count+=1
                row.setdefault('effects',[]).extend(copies)
            events={'full_arrow_replacements':replacements,'additional_lane_offset':[0,EXTRA_Y],
              'full_arrow_count_multiplier':2,'max_visible_arrows_before':3,'max_visible_arrows_after':6,
              'additional_flying_draws':extra_count,'flight_direction':direction,'original_contact_tick_kept':a['contactTick']}
            timeline['actions'][a['key']]={'source_frames_sha256':sha(a['frames']),'frames':rows,
              'note':'箭雨飞行箭重绘为菱形金属箭头、细箭杆与三片尾羽的中世纪西式箭；同场三支增至六支，新增箭沿原轨迹平移6像素错列。'+('敌方采用暗蓝近色系。'if side=='enemy'else'友军保持蓝白近色系。')+'原人物动作、生成与飞行节奏、原轨迹、命中和消散效果保持，不新增结算次数。',
              'events':events}
            contracts.append({'actor':side,'spell_id':28,'spell':'箭雨','action':a['id'],'ticks':len(rows),'contact_tick':a['contactTick'],'additional_hits':0,'events':events})
        target=OUT/f'{side}-motion.json';target.write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':'))+'\n')
        current=json.loads(path.read_text());current['review_timeline']='../../../'+target.relative_to(ROOT).as_posix();current['arrow_rain_revision']=REVISION;path.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
    preview(inventory)
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,'palettes':PALETTES,'assets':inventory},ensure_ascii=False,indent=2)+'\n')
    (OUT/'spell-action-contract.json').write_text(json.dumps({'source':'actual/data/legacy/rules_full.json ID28; docs2/完整游戏设定.md','gameplay_modified':False,'contracts':contracts},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'assets':len(inventory),'arrow_rain_variants':len(contracts)},ensure_ascii=False))


if __name__=='__main__':create()

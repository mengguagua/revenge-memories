#!/usr/bin/env python3
"""Review-only Halo: overhead charge, 1.5x growth, and a particle ending."""
import copy, hashlib, json, math
from PIL import Image, ImageDraw
from build_gallery import ROOT

REVISION='halo-charge-v1-20261021'
OUT=ROOT/REVISION
FULL='e6b1ec951361a1'
BLUE={(0,79,8):(29,42,72),(69,224,130):(58,80,126),(255,255,255):(147,170,205)}
SCALES=[1+n/14 for n in range(8)]
PARTICLE_PHASES=12
PARTICLE_TICKS=24


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def color(image,side):
    if side=='ally':return image.copy()
    result=image.copy()
    result.putdata([(*BLUE[(r,g,b)],a)if a else(0,0,0,0)for r,g,b,a in image.getdata()])
    return result


def save(path,image,inventory,purpose):
    path.parent.mkdir(parents=True,exist_ok=True);image.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),
      'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'visible_bounds':list(image.getbbox())if image.getbbox()else None})


def centered(image,scale=1):
    """Crop only transparent padding; resize the glyph around a fixed center."""
    plate=Image.new('RGBA',(288,192))
    if image.getbbox():
        part=image.crop(image.getbbox())
        part=part.resize((round(part.width*scale*4),round(part.height*scale*4)),Image.Resampling.NEAREST)
        plate.alpha_composite(part,(144-part.width//2,96-part.height//2))
    return plate


def particles(image,phase):
    """Scatter sampled pixels of the final source ring, not unrelated sparks."""
    t=phase/(PARTICLE_PHASES-1);im=Image.new('RGBA',(512,384));draw=ImageDraw.Draw(im)
    if phase==PARTICLE_PHASES-1:return im
    box=image.getbbox()
    if not box:return im
    cx=(box[0]+box[2])/2;cy=(box[1]+box[3])/2
    for y in range(box[1],box[3]):
        for x in range(box[0],box[2]):
            pixel=image.getpixel((x,y))
            seed=(x*31+y*17)%37
            if not pixel[3]or seed%3:continue
            dx=x-cx;dy=y-cy
            distance=max(1,math.hypot(dx,dy))
            spread=(4+seed%9)*t
            px=256+round((dx+dx/distance*spread+(seed%3-1)*t*2)*4)
            py=192+round((dy+dy/distance*spread-t*(3+seed%5))*4)
            alpha=round(pixel[3]*(1-t)**1.3)
            size=4 if t<.55 else 3
            draw.rectangle((px,py,px+size-1,py+size-1),fill=(*pixel[:3],alpha))
    return im


def visible_center(effect,meta,image):
    box=image.getbbox();center=[(box[0]+box[2])/2,(box[1]+box[3])/2]
    if effect.get('flip'):center[0]=meta['frame_size'][0]-center[0]
    delta=meta.get('flip_origin_offset',[0,0])if effect.get('flip')else[0,0]
    return [effect['position'][i]-meta['anchor'][i]+center[i]+delta[i]for i in range(2)]


def create():
    OUT.mkdir(exist_ok=True);data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    paths={s:ROOT/f'professions/class-15-{s}/battle/frame_mapping.json'for s in ['enemy','ally']}
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'mappings':{s:json.loads(p.read_text())for s,p in paths.items()}},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());inventory=[];contracts=[]
    for side,path in paths.items():
        previous=before['mappings'][side];timeline=json.loads((path.parent/previous['review_timeline']).resolve().read_text())
        timeline['halo_revision']=REVISION
        actions=[a for a in data['actions']if a['profile']==f'professions-class-15-{side}-battle'and '_item_29'in a['key']]
        used=sorted({e['sprite']for a in actions for row in a['frames']for e in row.get('effects',[])})
        images={key:Image.open(ROOT/data['effects'][key]['path']).convert('RGBA')for key in used}
        overhead={};recolored={};growth=[];particle_cache={}
        def add(name,image,size,anchor,purpose,meta=None):
            target=OUT/f'{side}/{name}.png';save(target,image,inventory,purpose)
            eid=f'review-halo-{side}-{name}'
            timeline['effects'][eid]={**(copy.deepcopy(meta)if meta else{}),'path':'../../../'+target.relative_to(ROOT).as_posix(),
              'frame_size':size,'frames':1,'anchor':anchor,'flip_origin_offset':(meta.get('flip_origin_offset',[0,0])if meta else[0,0])}
            return eid
        for key,image in images.items():
            short=key.removeprefix('native-');colored=color(image,side)
            overhead[key]=add('charge-'+short,centered(colored),[72,48],[36,24],side+' / native forming ring centered above hood')
            if side=='enemy':
                meta=data['effects'][key]
                recolored[key]=add('blue-'+short,colored,meta['frame_size'],meta['anchor'],'enemy / original downstream halo silhouette, dark-blue palette',meta)
        full_key=next(k for k in used if k.removeprefix('native-')==FULL)
        for n,scale in enumerate(SCALES):
            growth.append(add(f'grow-{n}',centered(color(images[full_key],side),scale),[72,48],[36,24],f'{side} / overhead ring fixed-center growth {scale:.6f}x'))
        for a in actions:
            rows=copy.deepcopy(a['frames'])
            start=next(i for i,row in enumerate(rows)if row.get('effects'))
            charge_effect=rows[start]['effects'][0]
            release=next(i for i,row in enumerate(rows)if i>start and any(e['position']!=charge_effect['position']for e in row.get('effects',[])))
            full_start=next(i for i,row in enumerate(rows)if any(e['sprite']==full_key for e in row.get('effects',[])))
            fixed=[a['origin'][0],77]
            for tick,row in enumerate(rows):
                for effect in row.get('effects',[]):
                    key=effect['sprite']
                    if start<=tick<release:
                        effect['sprite']=growth[min(7,(tick-full_start)//2)]if tick>=full_start and key==full_key else overhead[key]
                        effect['position']=fixed.copy()
                        # Custom cells are visibly centered; their mirrored padding
                        # cannot change registration as native asymmetric cells did.
                    elif side=='enemy':effect['sprite']=recolored[key]
            last=next(i for i in range(len(a['frames'])-1,-1,-1)if any(images[e['sprite']].getbbox()for e in a['frames'][i].get('effects',[])))
            tail_start=last+1;tail_end=tail_start+PARTICLE_TICKS
            tails=[]
            for tick in range(len(rows),tail_end):
                hold=copy.deepcopy(a['frames'][-1]);hold['effects']=[];tails.append(hold)
            final_effects=[e for e in a['frames'][last]['effects']if images[e['sprite']].getbbox()]
            for n,effect in enumerate(final_effects):
                key=effect['sprite'];mirror=bool(effect.get('flip'));cachekey=(key,mirror)
                if cachekey not in particle_cache:
                    original=color(images[key],side)
                    if mirror:original=original.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    particle_cache[cachekey]=[add(f'particles-{key.removeprefix("native-")}-{int(mirror)}-{phase:02}',particles(original,phase),[128,96],[64,48],side+' / source ring pixels disperse and fade')for phase in range(PARTICLE_PHASES)]
                center=visible_center(effect,data['effects'][key],images[key])
                for tick in range(tail_start,tail_end):
                    row=rows[tick]if tick<len(rows)else tails[tick-len(rows)]
                    row.setdefault('effects',[]).append({'sprite':particle_cache[cachekey][(tick-tail_start)//2],'position':center,'flip':False,'priority':effect.get('priority',0)})
            events={'overhead_start':start,'fixed_head_center':fixed,'full_ring_start':full_start,
              'growth_scales':SCALES,'growth_complete_tick':full_start+14,'release_tick_kept':release,
              'contact_tick_kept':a['contactTick'],'original_frames':len(a['frames']),
              'original_last_visible_effect':last,'scatter_start':tail_start,'scatter_end_exclusive':tail_end,
              'scatter_ticks':PARTICLE_TICKS,'appended_ticks':len(tails),'downstream_enemy_replacements':recolored}
            timeline['actions'][a['key']]={'source_frames_sha256':sha(a['frames']),'frames':rows,'tail_frames':tails,
              'note':'光环起始成环移至头顶固定中心，利用原有蓄力停留逐渐放大至1.5倍，再按原时刻释放。'+('敌方光环全程采用暗蓝三色。'if side=='enemy'else'友军保留原绿白配色。')+'目标处环绕、人物动作与结算保持；原光环消失后追加24帧光点散开并渐隐，原作播完后停帧对照，不增加伤害或结算。',
              'events':events}
            contracts.append({'actor':side,'spell_id':29,'spell':'光环','action':a['id'],'source_ticks':len(a['frames']),
              'review_ticks':len(rows)+len(tails),'contact_tick':a['contactTick'],'additional_hits':0,'events':events})
        target=OUT/f'{side}-motion.json';target.write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':'))+'\n')
        mapping=json.loads(path.read_text());mapping['review_timeline']='../../../'+target.relative_to(ROOT).as_posix();mapping['halo_revision']=REVISION
        path.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'enemy_palette':{','.join(map(str,k)):v for k,v in BLUE.items()},'assets':inventory},ensure_ascii=False,indent=2)+'\n')
    (OUT/'spell-action-contract.json').write_text(json.dumps({'source':'actual/data/legacy/rules_full.json ID29; docs2/完整游戏设定.md','gameplay_modified':False,'contracts':contracts},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'assets':len(inventory),'halo_variants':len(contracts)},ensure_ascii=False))


if __name__=='__main__':create()

#!/usr/bin/env python3
"""Review-only Slime: faction colors and a final grow/envelop/disappear sequence."""
import copy, hashlib, json, math
from PIL import Image, ImageDraw, ImageChops
from build_gallery import ROOT

REVISION='slime-engulf-v1-20261021'
OUT=ROOT/REVISION
PALETTES={
 'enemy':{'outline':(23,31,53),'shadow':(29,42,72),'body':(58,80,126),'edge':(88,111,155),'light':(162,181,209)},
 'ally':{'outline':(38,66,91),'shadow':(49,88,120),'body':(114,173,201),'edge':(176,211,227),'light':(234,245,248)},
}
MOVING={'549afb2634113c','b62bf21876ef4f','e1b2bcefa48e73','17573a3fa8db98'}


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def save(path,image,inventory,purpose):
    path.parent.mkdir(parents=True,exist_ok=True);image.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),
      'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'visible_bounds':list(image.getbbox())if image.getbbox()else None})


def recolor(image,side):
    p=PALETTES[side]
    mapping={(11,72,0):p['shadow'],(12,147,0):p['body'],(207,239,150):p['light'],
             (254,110,204):p['body'],(254,196,234):p['edge'],(255,255,255):p['light']}
    result=image.copy();result.putdata([(*mapping[(r,g,b)],a)if a else(0,0,0,0)for r,g,b,a in image.getdata()])
    return result


def target_reference(data,side):
    """Existing soldier art in neutral gray, confined to the final review segment."""
    other='ally'if side=='enemy'else'enemy'
    p=next(p for p in data['profiles']if p['id']==f'professions-class-6-{other}-battle')
    frame='0'if other=='ally'else'6';source=ROOT/p['newFrames'][frame]
    im=Image.open(source).convert('RGBA');im=im.crop(im.getbbox())
    if other=='enemy':im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    shades=[(57,66,77),(98,108,119),(153,164,171),(213,221,222)]
    im.putdata([(*shades[0 if(l:=.2126*r+.7152*g+.0722*b)<55 else 1 if l<115 else 2 if l<185 else 3],a)
                if a else(0,0,0,0)for r,g,b,a in im.getdata()])
    cell=Image.new('RGBA',(224,144));cell.alpha_composite(im,((224-im.width)//2,144-im.height))
    return cell,source.relative_to(ROOT).as_posix()


def gel(side,width,height,mouth,alpha=1):
    """Pixel-painted liquid volume with a stable ground anchor and layered gloss."""
    im=Image.new('RGBA',(96,80));draw=ImageDraw.Draw(im);p=PALETTES[side];foot=72;cx=48
    if height<1 or alpha<=0:return im.resize((384,320),Image.Resampling.NEAREST)
    top=foot-height
    contour=[(-.48,1),(-.54,.87),(-.50,.60),(-.44,.34),(-.32,.12),(-.14,0),
             (.08,0),(.28,.08),(.43,.26),(.50,.52),(.54,.82),(.48,1)]
    pts=[(round(cx+x*width),min(foot-1,round(top+y*height)))for x,y in contour]
    draw.polygon(pts,fill=p['body'],outline=p['outline'])
    mask=im.getchannel('A');shading=Image.new('RGBA',im.size);s=ImageDraw.Draw(shading)
    # Darker lower and right volume, with irregular liquid lobes along the base.
    s.polygon([(cx+width*.16,top),(cx+width*.5,top+height*.24),(cx+width*.6,foot),
      (cx-width*.5,foot),(cx-width*.46,foot-height*.13),(cx+width*.27,foot-height*.2),
      (cx+width*.35,top+height*.42)],fill=p['shadow'])
    s.polygon([(cx-width*.35,top+height*.26),(cx-width*.2,top+height*.1),
      (cx+width*.02,top+height*.07),(cx+width*.15,top+height*.14),(cx-width*.09,top+height*.21),
      (cx-width*.26,top+height*.44),(cx-width*.4,top+height*.61)],fill=p['edge'])
    s.line([(round(cx-width*.27),round(top+height*.25)),(round(cx-width*.16),round(top+height*.16)),
      (round(cx-width*.04),round(top+height*.14))],fill=p['light'],width=1)
    s.rectangle((round(cx-width*.28),round(top+height*.36),round(cx-width*.24),round(top+height*.41)),fill=p['light'])
    s.arc((round(cx-width*.3),round(top+height*.15),round(cx+width*.3),round(foot-height*.16)),20,67,fill=p['edge'],width=1)
    shading.putalpha(ImageChops.multiply(shading.getchannel('A'),mask));im.alpha_composite(shading)
    draw=ImageDraw.Draw(im)
    if mouth>.015 and height>16:
        # The open center frames the reference target; closing the opening
        # hides that target at the unchanged single contact tick.
        mh=max(2,round(min(38,height*.75)*mouth));mw=round(min(56,width*.87))
        cy=foot-min(21,height*.42)
        bounds=(cx-mw//2,round(cy-mh/2),cx+(mw+1)//2,round(cy+mh/2))
        draw.ellipse(bounds,fill=p['outline'])
        inner=(bounds[0]+2,bounds[1]+2,bounds[2]-2,bounds[3]-2)
        if inner[2]>inner[0]and inner[3]>inner[1]:draw.ellipse(inner,fill=(0,0,0,0))
        draw.arc((bounds[0]-1,bounds[1]-1,bounds[2]+1,bounds[3]+1),190,300,fill=p['edge'],width=1)
    elif height>24:
        cy=foot-height*.36
        draw.line([(round(cx-width*.17),round(cy)),(cx,round(cy+1)),(round(cx+width*.17),round(cy))],fill=p['shadow'],width=1)
    if alpha<1:im.putalpha(im.getchannel('A').point(lambda v:round(v*alpha)))
    return im.resize((384,320),Image.Resampling.NEAREST)


def arrival_tick(rows):
    previous=None;moving=False
    for tick,row in enumerate(rows):
        if any(e['sprite'].removeprefix('native-')in MOVING for e in row.get('effects',[])):
            x=row['effects'][0]['position'][0]
            if previous is not None and x!=previous:moving=True
            previous=x
        if moving and not row.get('effects'):
            return tick+1
    raise ValueError('Slime arrival transition not found')


def create():
    OUT.mkdir(exist_ok=True);data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    paths={s:ROOT/f'professions/class-15-{s}/battle/frame_mapping.json'for s in ['enemy','ally']}
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'actions':{a['id']:{k:a.get(k)for k in ['name','frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport','closeCamera','duration']}for a in data['actions']},
          'mappings':{s:json.loads(p.read_text())for s,p in paths.items()},
          'rules_hash':hashlib.sha256((ROOT.parents[1]/'actual/data/legacy/rules_full.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());inventory=[];contracts=[]
    for side,path in paths.items():
        previous=before['mappings'][side];timeline=json.loads((path.parent/previous['review_timeline']).resolve().read_text());timeline['slime_revision']=REVISION
        actions=[a for a in data['actions']if a['profile']==f'professions-class-15-{side}-battle'and '_item_32'in a['key']]
        used=sorted({e['sprite']for a in actions for row in a['frames']for e in row.get('effects',[])})
        recolored={};growth=[];closing=[];holding=[];vanishing=[]
        def add(name,image,size,anchor,purpose,meta=None):
            target=OUT/f'{side}/{name}.png';save(target,image,inventory,purpose);eid=f'review-slime-{side}-{name}'
            timeline['effects'][eid]={**(copy.deepcopy(meta)if meta else{}),'path':'../../../'+target.relative_to(ROOT).as_posix(),
              'frame_size':size,'frames':1,'anchor':anchor,'flip_origin_offset':(meta.get('flip_origin_offset',[0,0])if meta else[0,0])}
            return eid
        for key in used:
            meta=data['effects'][key];image=Image.open(ROOT/meta['path']).convert('RGBA')
            recolored[key]=add('color-'+key.removeprefix('native-'),recolor(image,side),meta['frame_size'],meta['anchor'],side+' / unchanged initial formation and travel pixels, faction colors',meta)
        reference,reference_path=target_reference(data,side)
        target_id=add('target-reference',reference,[56,36],[28,36],'neutral existing soldier reference; review only, not a battle unit or new hit')
        for n in range(12):
            t=n/11;growth.append(add(f'grow-{n:02}',gel(side,round(30+34*t),round(8+44*t),t),[96,80],[48,72],side+' / grounded Slime grows around target'))
        for n in range(10):
            closing.append(add(f'close-{n:02}',gel(side,64,52,1-n/9),[96,80],[48,72],side+' / opening closes around target at original contact'))
        for n in range(4):
            holding.append(add(f'hold-{n:02}',gel(side,64+(n%2),52,0),[96,80],[48,72],side+' / engulfed target held behind solid liquid volume'))
        for n in range(12):
            t=n/11;vanishing.append(add(f'vanish-{n:02}',gel(side,round(64*(1-t*.55)),round(52*(1-t)),0,(1-t)**.7),[96,80],[48,72],side+' / Slime settles and disappears, target reference remains'))
        for a in actions:
            rows=copy.deepcopy(a['frames']);start=arrival_tick(rows);contact=a['contactTick'];end=len(rows)
            grow_start=start+12;close_start=contact-20;gone=end-4
            fade_start=contact+min(18,max(6,(gone-contact)//2))
            target=[185 if side=='enemy'else 65,128]
            for tick,row in enumerate(rows):
                if tick<start:
                    for e in row.get('effects',[]):e['sprite']=recolored[e['sprite']]
                    continue
                row['effects']=[{'sprite':target_id,'position':target,'flip':False,'priority':0}]
                if tick>=gone:continue
                if tick<grow_start:eid=growth[0]
                elif tick<close_start:
                    n=min(11,round((tick-grow_start)/(close_start-grow_start-1)*11));eid=growth[n]
                elif tick<=contact:eid=closing[min(9,round((tick-close_start)/(contact-close_start)*9))]
                elif tick<fade_start:eid=holding[((tick-contact-1)//3)%4]
                else:eid=vanishing[min(11,round((tick-fade_start)/(gone-fade_start-1)*11))]
                row['effects'].append({'sprite':eid,'position':target,'flip':False,'priority':1})
            events={'spell_id':32,'attack_segment_start':start,'growth_start':grow_start,'closing_start':close_start,
              'contact_tick_kept':contact,'fade_start':fade_start,'fully_gone_tick':gone,'total_frames_kept':end,
              'target_foot_anchor':target,'max_slime_size_native':[64,52],'pre_attack_color_replacements':recolored,
              'review_reference_source':reference_path,'target_reference_only':True,'additional_hits':0}
            timeline['actions'][a['key']]={'source_frames_sha256':sha(a['frames']),'frames':rows,
              'note':('敌方史莱姆改为暗蓝色。'if side=='enemy'else'友军史莱姆改为蓝白色。')+'原生成、跳动和移动段仅换色；抵达后的最后攻击改为脚底固定、膨胀包覆目标，原结算时刻合拢吞噬，随后收缩消失。灰色士兵只作吞噬范围验收参照，消失后恢复可见，不表示额外伤害或即死。原人物动作、总时长与结算保持。',
              'events':events}
            contracts.append({'actor':side,'spell_id':32,'spell':'史莱姆','action':a['id'],'ticks':end,'contact_tick':contact,'additional_hits':0,'events':events})
        target=OUT/f'{side}-motion.json';target.write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':'))+'\n')
        mapping=json.loads(path.read_text());mapping['review_timeline']='../../../'+target.relative_to(ROOT).as_posix();mapping['slime_revision']=REVISION
        path.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_art_integrated':False,'image_generation_invoked':False,'chat_image_output':False,'palettes':PALETTES,'assets':inventory},ensure_ascii=False,indent=2)+'\n')
    (OUT/'spell-action-contract.json').write_text(json.dumps({'source':'actual/data/legacy/rules_full.json ID32; docs2/完整游戏设定.md','gameplay_modified':False,'contracts':contracts},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'assets':len(inventory),'slime_variants':len(contracts)},ensure_ascii=False))


if __name__=='__main__':create()

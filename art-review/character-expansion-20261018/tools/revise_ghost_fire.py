#!/usr/bin/env python3
"""Review-only ID31 Ghost Fire: visible eyes, restrained blast growth, rising wisp."""
import copy, hashlib, json, math
from PIL import Image, ImageDraw
from build_gallery import ROOT

REVISION='ghost-fire-v1-20261021'
OUT=ROOT/REVISION
FLIGHT=['ca271c883ab5b7','3a16e2c933bc40','484a0b9bc15faa','16e4b27c3357ee']
BLAST=['4c6ee9651eccb2','3e6396202ccac1','bcab8c7f7893aa','aab3481f3e0706','79c300aa34e915']
SOURCE_COLORS=[(12,147,0),(69,224,130),(181,235,242)]
PALETTE={
    'enemy':{'shadow':(29,42,72),'flame':(58,80,126),'light':(147,170,205),'eye_ink':(18,27,50),'eye_light':(215,225,237)},
    'ally':{'shadow':(49,88,120),'flame':(114,173,201),'light':(230,241,244),'eye_ink':(40,68,96),'eye_light':(255,255,255)},
}
BLAST_SCALE=1.15
RISE_TICKS=30
RISE_PHASES=15


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def save(path,image,inventory,purpose):
    path.parent.mkdir(parents=True,exist_ok=True);image.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),
      'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'visible_bounds':list(image.getbbox())if image.getbbox()else None})


def color(image,side):
    mapping=dict(zip(SOURCE_COLORS,[PALETTE[side][key]for key in ['shadow','flame','light']]))
    result=image.copy();result.putdata([(*mapping[(r,g,b)],a)if a else(0,0,0,0)for r,g,b,a in image.getdata()])
    return result


def eyes(image,side):
    result=image.resize((image.width*4,image.height*4),Image.Resampling.NEAREST)
    draw=ImageDraw.Draw(result);palette=PALETTE[side]
    # Both eyes remain anchored in the head across all four flame phases.
    # Their 3x3-pixel dark sockets separate the pupils from the pale flame core.
    for x in [22,26]:
        draw.rectangle((x*4,10*4,(x+3)*4-1,13*4-1),fill=(*palette['eye_ink'],255))
        draw.rectangle(((x+1)*4,11*4,(x+2)*4-1,12*4-1),fill=(*palette['eye_light'],255))
    return result


def blast(image):
    plate=Image.new('RGBA',(192,192));part=image.crop(image.getbbox())
    # Even dimensions maintain the exact visible center while preserving shape.
    size=[max(2,round(v*4*BLAST_SCALE/2)*2)for v in part.size]
    part=part.resize(tuple(size),Image.Resampling.NEAREST)
    plate.alpha_composite(part,(96-part.width//2,96-part.height//2))
    return plate


def visible_center(effect,meta,image):
    box=image.getbbox();center=[(box[0]+box[2])/2,(box[1]+box[3])/2]
    if effect.get('flip'):center[0]=meta['frame_size'][0]-center[0]
    delta=meta.get('flip_origin_offset',[0,0])if effect.get('flip')else[0,0]
    return [effect['position'][i]-meta['anchor'][i]+center[i]+delta[i]for i in range(2)]


def rising_wisp(flights,phase):
    t=phase/(RISE_PHASES-1);plate=Image.new('RGBA',(256,256))
    if phase==RISE_PHASES-1:return plate
    source=flights[phase%len(flights)]
    # Reuse the existing flame's head, eyes and tail texture; keep the face
    # upright while the trailing flame tapers down below the ascending head.
    head=source.crop((20*4,8*4,29*4,16*4))
    tail=source.crop((8*4,10*4,20*4,16*4)).rotate(90,expand=True,resample=Image.Resampling.NEAREST)
    glyph=Image.new('RGBA',(52,80));glyph.alpha_composite(tail,(10,28));glyph.alpha_composite(head,(8,0))
    scale=.9-.2*t;glyph=glyph.resize((round(glyph.width*scale),round(glyph.height*scale)),Image.Resampling.NEAREST)
    glyph.putalpha(glyph.getchannel('A').point(lambda value:round(value*(1-t)**.8)))
    x=128-glyph.width//2+round(math.sin(t*math.pi*2)*3)
    y=128-glyph.height//2-round(t*18*4)
    plate.alpha_composite(glyph,(x,y));return plate


def create():
    OUT.mkdir(exist_ok=True);data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    paths={s:ROOT/f'professions/class-15-{s}/battle/frame_mapping.json'for s in ['enemy','ally']}
    rules_path=ROOT.parents[1]/'actual/data/legacy/rules_full.json';docs_path=ROOT.parents[1]/'docs2/完整游戏设定.md'
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        rules=json.loads(rules_path.read_text());rule=next(x for x in rules['items']if x['id']==31)
        baseline.write_text(json.dumps({'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'actions':{a['id']:{k:a.get(k)for k in ['name','frames','revisedFrames','reviewTailFrames','fps','origin','contactTick','viewport','closeCamera','duration']}for a in data['actions']},
          'mappings':{s:json.loads(p.read_text())for s,p in paths.items()},'rule31':rule,'rules_sha256':sha(rules),
          'docs_sha256':hashlib.sha256(docs_path.read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());inventory=[];contracts=[]
    for side,path in paths.items():
        previous=before['mappings'][side];timeline=json.loads((path.parent/previous['review_timeline']).resolve().read_text())
        timeline['ghost_fire_revision']=REVISION
        actions=[a for a in data['actions']if a['profile']==f'professions-class-15-{side}-battle'and '_item_31'in a['key']]
        used=sorted({e['sprite']for a in actions for row in a['frames']for e in row.get('effects',[])})
        images={k:Image.open(ROOT/data['effects'][k]['path']).convert('RGBA')for k in used}
        flight_ids={};blast_ids={};other_ids={};flight_images={}
        def add(name,image,size,anchor,purpose,meta=None):
            target=OUT/f'{side}/{name}.png';save(target,image,inventory,purpose)
            eid=f'review-ghost-fire-{side}-{name}'
            timeline['effects'][eid]={**(copy.deepcopy(meta)if meta else{}),'path':'../../../'+target.relative_to(ROOT).as_posix(),
              'frame_size':size,'frames':1,'anchor':anchor,'flip_origin_offset':(meta.get('flip_origin_offset',[0,0])if meta else[0,0])}
            return eid
        for key,image in images.items():
            short=key.removeprefix('native-');meta=data['effects'][key];colored=color(image,side)
            if short in FLIGHT:
                part=eyes(colored,side);flight_images[short]=part
                flight_ids[key]=add('flight-'+short,part,meta['frame_size'],meta['anchor'],side+' / original flight flame with two stable visible eyes',meta)
            elif short in BLAST:
                blast_ids[key]=add('blast-'+short,blast(colored),[48,48],[24,24],side+' / original burst shape enlarged about fifteen percent')
            else:other_ids[key]=add('color-'+short,colored,meta['frame_size'],meta['anchor'],side+' / unchanged blank transition registration',meta)
        rise_ids=[add(f'rise-{n:02}',rising_wisp([flight_images[k]for k in FLIGHT],n),[64,64],[32,32],side+' / upright flame with eyes rises after the original blast, then fades')for n in range(RISE_PHASES)]
        for a in actions:
            rows=copy.deepcopy(a['frames']);replacements={**flight_ids,**blast_ids,**other_ids}
            for row in rows:
                for effect in row.get('effects',[]):
                    key=effect['sprite']
                    if key in blast_ids:
                        effect['position']=visible_center(effect,data['effects'][key],images[key])
                    effect['sprite']=replacements[key]
            final=next(e for row in reversed(a['frames'])for e in row.get('effects',[])if e['sprite']in blast_ids)
            center=visible_center(final,data['effects'][final['sprite']],images[final['sprite']]);tail=[]
            for tick in range(RISE_TICKS):
                row=copy.deepcopy(a['frames'][-1]);row['effects']=[{'sprite':rise_ids[tick//2],'position':center,'flip':False,'priority':0}];tail.append(row)
            first=next(i for i,row in enumerate(a['frames'])if any(e['sprite']in flight_ids for e in row.get('effects',[])))
            release=next(i for i,row in enumerate(a['frames'])if i>first and any(e['sprite']in flight_ids and e['position']!=a['frames'][first]['effects'][0]['position']for e in row.get('effects',[])))
            events={'source_spell_id':31,'display_name':'鬼火','flight_start':first,'release_tick_kept':release,
              'contact_tick_kept':a['contactTick'],'eyes_native_rectangles':[[22,10,25,13],[26,10,29,13]],
              'blast_scale':BLAST_SCALE,'blast_center_kept':center,'source_frames':len(rows),'rise_start':len(rows),
              'rise_ticks':RISE_TICKS,'rise_distance_native':18,'additional_hits':0,'effect_replacements':replacements}
            timeline['actions'][a['key']]={'source_frames_sha256':sha(a['frames']),'frames':rows,'tail_frames':tail,'tail_label':'鬼火上飘',
              'note':'多拉更名为鬼火（编号31保持）。'+('敌方采用暗蓝色。'if side=='enemy'else'友军采用蓝白色。')+'飞行火焰显示固定双眼，沿用原轨迹与释放时刻；原爆炸等比放大约15%，中心、顺序与结算不动。原动画结束后追加30帧鬼火上飘渐隐，人物动作保持，不新增伤害或结算。','events':events}
            contracts.append({'actor':side,'spell_id':31,'former_name':'多拉','spell':'鬼火','action':a['id'],'source_ticks':len(rows),
              'review_ticks':len(rows)+len(tail),'contact_tick':a['contactTick'],'additional_hits':0,'events':events})
        target=OUT/f'{side}-motion.json';target.write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':'))+'\n')
        mapping=json.loads(path.read_text());mapping['review_timeline']='../../../'+target.relative_to(ROOT).as_posix();mapping['ghost_fire_revision']=REVISION
        path.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,
      'chat_image_output':False,'palettes':PALETTE,'assets':inventory},ensure_ascii=False,indent=2)+'\n')
    (OUT/'spell-action-contract.json').write_text(json.dumps({'source':'actual/data/legacy/rules_full.json ID31; docs2/完整游戏设定.md',
      'gameplay_modified':False,'label_renamed':True,'contracts':contracts},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'assets':len(inventory),'ghost_fire_variants':len(contracts)},ensure_ascii=False))


if __name__=='__main__':create()

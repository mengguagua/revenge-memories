#!/usr/bin/env python3
"""Wind Blade review: fixed-center spin inside the existing enlarged hold."""
import copy, hashlib, json
from PIL import Image, ImageDraw
from build_gallery import ROOT

REVISION = 'wind-blade-spin-v1-20261021'
OUT = ROOT / REVISION
FULL = '44865a24d18d0f'
BLUE = {(192,223,255):(46,64,104), (255,255,255):(127,151,188), (146,144,255):(32,43,77)}
PHASES = 16


def sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def recolor(im):
    result=im.copy()
    result.putdata([(*BLUE.get((r,g,b),(46,64,104)),a)if a else (0,0,0,0)for r,g,b,a in im.getdata()])
    return result


def save(path,im,inventory,purpose):
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),
      'visible_bounds':list(im.getbbox())if im.getbbox()else None,'bytes':path.stat().st_size,
      'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})


def center(effect,meta,box):
    x=(box[0]+box[2])/2;y=(box[1]+box[3])/2
    if effect.get('flip'):x=meta['frame_size'][0]-x
    delta=meta.get('flip_origin_offset',[0,0])if effect.get('flip')else [0,0]
    return [effect['position'][0]-meta['anchor'][0]+x+delta[0],
            effect['position'][1]-meta['anchor'][1]+y+delta[1]]


def preview(inventory):
    from export_gallery import font
    sheet=Image.new('RGB',(1240,1400),(14,21,26));draw=ImageDraw.Draw(sheet)
    draw.text((620,16),'风刃 · 放大后原地旋转，再发射',font=font(22),anchor='mt',fill='#e9f0f0')
    for row,(side,bg)in enumerate([('ally',(32,45,53)),('enemy',(32,45,53)),('ally',(220,222,216)),('enemy',(220,222,216))]):
        for column,phase in enumerate([0,5,10,15]):
            x=16+306*column;y=58+332*row
            draw.rounded_rectangle((x,y,x+290,y+316),radius=10,fill=bg)
            label=('友军 · 原色'if side=='ally'else'敌军 · 暗蓝')+' · '+str(phase*24)+'°'
            ink='#e9f0f0'if row<2 else '#26323b'
            draw.text((x+145,y+12),label,font=font(16),anchor='mt',fill=ink)
            im=Image.open(OUT/f'{side}/spin-{phase:02}.png').convert('RGBA')
            sheet.paste(im,(x+17,y+44),im)
            bounds=draw.textbbox((x+145,y+12),label,font=font(16),anchor='mt')
            assert bounds[0]>x+16 and bounds[2]<x+274
    save(OUT/'spin-poses.png',sheet,inventory,'four spin angles, both factions, dark and light backgrounds')


def create():
    OUT.mkdir(exist_ok=True)
    data=json.loads((ROOT/'demos/gallery-data.json').read_text())
    paths={side:ROOT/f'professions/class-15-{side}/battle/frame_mapping.json'for side in ['enemy','ally']}
    baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'mappings':{side:json.loads(path.read_text())for side,path in paths.items()}},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());inventory=[];contracts=[]
    for side,path in paths.items():
        previous=before['mappings'][side];timeline=json.loads((path.parent/previous['review_timeline']).resolve().read_text())
        timeline['wind_blade_revision']=REVISION
        prefix='native-'if side=='enemy'else''
        full_key=prefix+FULL;meta=data['effects'][full_key];source=Image.open(ROOT/meta['path']).convert('RGBA');box=source.getbbox()
        plate=Image.new('RGBA',(256,256));colored=recolor(source)if side=='enemy'else source
        origin=[round(128-(box[0]+box[2])/2*4),round(128-(box[1]+box[3])/2*4)]
        plate.alpha_composite(colored.resize((source.width*4,source.height*4),Image.Resampling.NEAREST),origin)
        spin_ids=[]
        for phase in range(PHASES):
            angle=phase*360/(PHASES-1)
            im=plate.rotate(-angle,resample=Image.Resampling.NEAREST,center=(128,128))
            target=OUT/f'{side}/spin-{phase:02}.png';save(target,im,inventory,side+' / enlarged Wind Blade fixed-center spin')
            eid=f'review-wind-spin-{side}-{phase}'
            timeline['effects'][eid]={'path':'../../../'+target.relative_to(ROOT).as_posix(),'frame_size':[64,64],
              'frames':1,'anchor':[32,32],'flip_origin_offset':[0,0]}
            spin_ids.append(eid)
        recolored={}
        if side=='enemy':
            used={e['sprite']for a in data['actions']if a['profile']==f'professions-class-15-{side}-battle'and '_item_27'in a['key']for row in a['frames']for e in row.get('effects',[])}
            for key in sorted(used):
                original=data['effects'][key];target=OUT/f'enemy/color-{key.removeprefix("native-")}.png'
                im=recolor(Image.open(ROOT/original['path']).convert('RGBA'));save(target,im,inventory,'enemy / original wind and impact silhouette, dark blue palette')
                eid='review-wind-blue-'+key.removeprefix('native-');timeline['effects'][eid]={**copy.deepcopy(original),'path':'../../../'+target.relative_to(ROOT).as_posix()};recolored[key]=eid
        for a in data['actions']:
            if a['profile']!=f'professions-class-15-{side}-battle' or '_item_27'not in a['key']:continue
            rows=copy.deepcopy(a['frames']);start=next(i for i,row in enumerate(rows)if any(e['sprite']==full_key for e in row.get('effects',[])))
            reference=next(e for e in rows[start]['effects']if e['sprite']==full_key)
            release=next(i for i,row in enumerate(rows)if i>start and any(e['sprite']==full_key and e['position']!=reference['position']for e in row.get('effects',[])))
            fixed=center(reference,meta,box)
            for tick in range(start,release):
                phase=round((tick-start)/(release-start-1)*(PHASES-1))
                for effect in rows[tick].get('effects',[]):
                    if effect['sprite']==full_key:
                        effect['sprite']=spin_ids[phase];effect['position']=fixed
            if side=='enemy':
                for row in rows:
                    for effect in row.get('effects',[]):effect['sprite']=recolored.get(effect['sprite'],effect['sprite'])
            events={'spin_start':start,'spin_end_exclusive':release,'degrees':360,'fixed_center':fixed,
              'rotation_in_existing_hold':True,'release_tick_kept':release,'contact_tick_kept':a['contactTick'],
              'enemy_color_replacements':recolored}
            timeline['actions'][a['key']]={'source_frames_sha256':sha(a['frames']),'frames':rows,
              'note':'风刃放大后利用原有停留段绕固定中心旋转一圈，再按原时刻发射；发射后的轨迹、人物动作、命中、收势与总帧数保持。'+('敌方风刃改为暗蓝色为主。'if side=='enemy'else'友军保持原配色。'),
              'events':events}
            contracts.append({'actor':side,'spell_id':27,'spell':'风刃','action':a['id'],'ticks':len(rows),'contact_tick':a['contactTick'],'additional_hits':0,'events':events})
        target=OUT/f'{side}-motion.json';target.write_text(json.dumps(timeline,ensure_ascii=False,separators=(',',':'))+'\n')
        current=json.loads(path.read_text());current['review_timeline']='../../../'+target.relative_to(ROOT).as_posix();current['wind_blade_revision']=REVISION
        path.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n')
    preview(inventory)
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,
      'chat_image_output':False,'enemy_colors':{','.join(map(str,k)):v for k,v in BLUE.items()},'assets':inventory},ensure_ascii=False,indent=2)+'\n')
    (OUT/'spell-action-contract.json').write_text(json.dumps({'source':'actual/data/legacy/rules_full.json ID27; docs2/完整游戏设定.md',
      'gameplay_modified':False,'contracts':contracts},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'assets':len(inventory),'wind_variants':len(contracts)},ensure_ascii=False))


if __name__=='__main__':create()

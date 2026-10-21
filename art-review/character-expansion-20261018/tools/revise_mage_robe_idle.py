#!/usr/bin/env python3
"""Ally mage map idle: enclosed sleeves, fixed head/torso, muted hem motion."""
import colorsys,copy,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT

REVISION='mage-robe-idle-v1-20261021'
OUT=ROOT/REVISION
MAPPING=ROOT/'professions/class-15-ally/maps/frame_mapping.json'
PALETTE={
 'outline':'292b35','robe_shadow':'494856','robe_mid':'706777','robe_light':'a29aaa',
 'trim':'b7ac8b','skin_shadow':'957b69','skin':'d1b096',
}
ALIASES=[0,1,2,1,0,1]
HEM_START=61


def rgba(key):return (*bytes.fromhex(PALETTE[key]),255)


def save(path,image,inventory,purpose):
    path.parent.mkdir(parents=True,exist_ok=True);image.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),
      'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'visible_bounds':list(image.getbbox())if image.getbbox()else None,
      'visible_rgb_colors':len({px[:3]for px in image.convert('RGBA').getdata()if px[3]})})


def simplify_head(source):
    im=Image.new('RGBA',source.size)
    for y in range(44):
        for x in range(source.width):
            r,g,b,a=source.getpixel((x,y))
            if a<128:continue
            l=.2126*r+.7152*g+.0722*b
            if 35<=y<44 and 36<=x<=57 and r>g*1.1 and g>b*1.1:
                key='skin'if l>140 else'skin_shadow'
            elif l<35:key='outline'
            elif r>g*1.2 and g>b*1.2 and l>95:key='trim'
            elif l<75:key='robe_shadow'
            elif l<145:key='robe_mid'
            else:key='robe_light'
            im.putpixel((x,y),rgba(key))
    return im


def canonical(source):
    im=Image.new('RGBA',(96,96));d=ImageDraw.Draw(im)
    # One closed garment replaces the old hands, detached sleeves, short coat,
    # open inner skirt and exposed boots. The shoulders remain still.
    d.polygon([(39,43),(51,43),(59,47),(63,54),(63,61),(58,65),(38,65),
      (31,61),(31,54),(34,48)],fill=rgba('robe_mid'),outline=rgba('outline'))
    d.polygon([(57,48),(61,54),(61,61),(56,64),(50,62),(51,50)],fill=rgba('robe_shadow'))
    d.line([(36,49),(34,55),(35,60),(41,62)],fill=rgba('robe_light'),width=1)
    d.line([(58,52),(57,58),(53,60)],fill=rgba('outline'),width=1)
    # Elbow folds communicate that both arms are tucked inside the robe.
    d.line([(36,54),(42,57),(48,57),(54,54)],fill=rgba('robe_shadow'),width=1)
    d.line([(37,56),(42,59),(49,59)],fill=rgba('robe_light'),width=1)
    # Long, closed lower robe: center fastening and seam remain fixed.
    d.polygon([(38,59),(57,59),(59,66),(63,74),(66,78),(62,79),(33,79),
      (29,77),(33,70),(36,64)],fill=rgba('robe_mid'),outline=rgba('outline'))
    d.polygon([(51,61),(56,61),(58,69),(62,77),(56,77),(52,70)],fill=rgba('robe_shadow'))
    d.polygon([(38,62),(42,61),(40,70),(36,76),(33,76),(36,69)],fill=rgba('robe_light'))
    d.line([(42,63),(43,70),(41,77)],fill=rgba('robe_shadow'),width=1)
    d.line([(55,65),(57,72),(60,76)],fill=rgba('robe_light'),width=1)
    d.line([(34,77),(42,78),(49,78),(58,78),(62,77)],fill=rgba('trim'),width=1)
    d.line([(48,58),(48,77)],fill=rgba('robe_shadow'),width=1)
    d.line([(47,61),(47,73)],fill=rgba('robe_light'),width=1)
    # A small, muted collar edge replaces the old bright gold trim.
    d.polygon([(38,44),(46,47),(54,44),(57,47),(49,51),(37,47)],fill=rgba('outline'))
    d.line([(39,45),(46,49),(54,45)],fill=rgba('trim'),width=2)
    d.rectangle((46,50,49,52),fill=rgba('robe_shadow'))
    d.rectangle((47,50,48,51),fill=rgba('trim'))
    im.alpha_composite(simplify_head(source))
    return im


def sway(base,phase):
    result=base.copy();amplitude=[-2,0,2][phase]
    # Inverse nearest-neighbor sampling avoids cracks as the cloth bends. The
    # central five-pixel seam and every pixel above the lower robe stay fixed.
    for y in range(HEM_START,80):
        bend=amplitude*((y-HEM_START)/(79-HEM_START))**1.35
        for x in range(96):
            if 46<=x<=50:continue
            weight=min(1,abs(x-48)/13)
            sx=round(x-bend*weight)
            result.putpixel((x,y),base.getpixel((sx,y))if 0<=sx<96 else(0,0,0,0))
    return result


def create():
    OUT.mkdir(exist_ok=True);mapping=json.loads(MAPPING.read_text());data=json.loads((ROOT/'demos/gallery-data.json').read_text());baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'mapping':mapping,'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'rules_hash':hashlib.sha256((ROOT.parents[1]/'actual/data/legacy/rules_full.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());old=next(s for s in before['mapping']['scenarios']if s['id']=='tactical-idle')
    source_path=(MAPPING.parent/old['frame_mapping'][0]['output_path']).resolve();source=Image.open(source_path).convert('RGBA')
    base=canonical(source);frames=[sway(base,p)for p in range(3)];assets=[];records=[];atlas=Image.new('RGBA',(576,96))
    for index,phase in enumerate(ALIASES):
        path=OUT/f'frames/idle-{index:03}.png';im=frames[phase];save(path,im,assets,'ally mage / closed sleeves, stationary upper body, lower robe phase '+str(phase));atlas.alpha_composite(im,(index*96,0))
        record=copy.deepcopy(old['frame_mapping'][index]);record['previous_registration']=record.pop('registration',{})
        record.update(output_path='../../../'+path.relative_to(ROOT).as_posix(),path='../../../'+path.relative_to(ROOT).as_posix(),
          canonical_frame=phase,size=[96,96],bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),alpha_bounds=list(im.getbbox()),
          registration={'basis':'Shared first-frame head and upper body; lower robe only, stationary center seam','fixed_upper_y_exclusive':HEM_START,
            'fixed_seam_x_inclusive':[46,50],'hem_amplitude_pixels':[-2,0,2][phase],'foot_y_exclusive':80})
        records.append(record)
    save(OUT/'idle-atlas.png',atlas,assets,'six source slots retain their explicit aliases')
    scenario=next(s for s in mapping['scenarios']if s['id']=='tactical-idle')
    scenario.update(frame_mapping=records,output_atlas='../../../'+(OUT/'idle-atlas.png').relative_to(ROOT).as_posix(),revision=REVISION,
      status='review_candidate',review_note='双臂藏于闭合袖袍，尖帽、头脸、上身和胸前中轴固定；仅下半袍摆小幅循环，七色低饱和灰紫与米金配色。',
      action_note='本轮仅调整术法师战斗地图待机：双臂隐藏在长袍内，头部和中心点固定，仅袍摆左右摆动；原14／8／14／8帧节奏保持。',
      motion_review='../../../'+(OUT/'README.md').relative_to(ROOT).as_posix())
    MAPPING.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    manifest={'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'palette':PALETTE,'original_visible_colors':[len({p[:3]for p in Image.open((MAPPING.parent/r['output_path']).resolve()).convert('RGBA').getdata()if p[3]})for r in old['frame_mapping'][:3]],
      'fixed_upper_y_exclusive':HEM_START,'fixed_seam_x_inclusive':[46,50],'lower_robe_amplitude_pixels':[-2,0,2],
      'arms_hidden':True,'head_source':source_path.relative_to(ROOT).as_posix(),'canvas':[96,96],'logical_frame_size':[24,24],
      'source_anchor':[12,20],'cycle':[0,1,2,1],'ticks':[14,8,14,8],'aliases':ALIASES,'assets':assets}
    (OUT/'asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'frames':len(records),'colors':7,'old_colors':manifest['original_visible_colors']},ensure_ascii=False))


if __name__=='__main__':create()

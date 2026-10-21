#!/usr/bin/env python3
"""Friendly mage battle-only round hat brim and mild 10% desaturation."""
import colorsys,copy,hashlib,json
from PIL import Image,ImageDraw
from build_gallery import ROOT

REVISION='mage-battle-round-hat-v1-20261021'
OUT=ROOT/REVISION
MAPPING=ROOT/'professions/class-15-ally/battle/frame_mapping.json'
SATURATION_FACTOR=.90
CONFIG={
 0:{'center':[199,139],'radius':26,'face':[180,145,213,158]},
 1:{'center':[194,134],'radius':27,'face':[192,139,217,148]},
 2:{'center':[183,137],'radius':26,'face':[164,142,195,154]},
}
BRIM={'outline':'251e25','shadow':'592b3b','surface':'823a4c','gloss':'ac6070','gold':'c89c52','light':'e0ba78'}


def muted_rgb(rgb):
    if max(rgb)<32:return rgb
    h,s,v=colorsys.rgb_to_hsv(*(x/255 for x in rgb))
    return tuple(round(x*255)for x in colorsys.hsv_to_rgb(h,s*SATURATION_FACTOR,v))


def desaturate(image):
    result=image.copy();result.putdata([(*muted_rgb(px[:3]),px[3])if px[3]else px for px in image.getdata()]);return result


def hat(image,config):
    """Brim sits behind crown and face; only its lower rim crosses the crown."""
    cx,cy=config['center'];radius=config['radius'];p={k:(*muted_rgb(tuple(bytes.fromhex(v))),255)for k,v in BRIM.items()}
    colored=desaturate(image);result=Image.new('RGBA',image.size);d=ImageDraw.Draw(result)
    d.ellipse((cx-radius-1,cy-5,cx+radius+1,cy+5),fill=p['outline'])
    d.ellipse((cx-radius,cy-4,cx+radius,cy+4),fill=p['shadow'])
    d.ellipse((cx-radius+2,cy-4,cx+radius-2,cy+1),fill=p['surface'])
    d.arc((cx-radius+3,cy-4,cx+radius-3,cy+2),195,285,fill=p['gloss'],width=1)
    # The source crown, head and foreground hands/staff retain their pose.
    result.alpha_composite(colored);d=ImageDraw.Draw(result)
    d.arc((cx-radius,cy-4,cx+radius,cy+4),8,172,fill=p['gold'],width=2)
    d.arc((cx-radius+2,cy-3,cx+radius-2,cy+3),25,150,fill=p['light'],width=1)
    d.arc((cx-radius-1,cy-5,cx+radius+1,cy+5),12,168,fill=p['outline'],width=1)
    # Do not paint across the visible eyes or face of any pose.
    box=tuple(config['face']);result.paste(colored.crop(box),box[:2])
    return result


def save(path,image,inventory,purpose):
    path.parent.mkdir(parents=True,exist_ok=True);image.save(path,optimize=True)
    inventory.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),
      'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
      'visible_bounds':list(image.getbbox())if image.getbbox()else None})


def create():
    OUT.mkdir(exist_ok=True);mapping=json.loads(MAPPING.read_text());data=json.loads((ROOT/'demos/gallery-data.json').read_text());baseline=OUT/'baseline.json'
    if not baseline.exists():
        baseline.write_text(json.dumps({'mapping':mapping,'digests':{a['id']:a['contentDigest']for a in data['actions']},
          'rules_hash':hashlib.sha256((ROOT.parents[1]/'actual/data/legacy/rules_full.json').read_bytes()).hexdigest()},ensure_ascii=False,indent=2)+'\n')
    before=json.loads(baseline.read_text());assets=[];records=[];order=[0,1,2,100,101,102];atlas=Image.new('RGBA',(1920,256))
    for slot,frame in enumerate(order):
        source=(MAPPING.parent/before['mapping']['frame_mapping'][str(frame)]).resolve();image=Image.open(source).convert('RGBA')
        config=CONFIG[1 if frame>=100 else frame];revised=hat(image,config);target=OUT/f'body/frame-{frame:03}.png'
        save(target,revised,assets,'friendly mage / rounded wide brim; original warm hue, mild 10% desaturation')
        atlas.alpha_composite(revised,(slot*320,0));mapping['frame_mapping'][str(frame)]='../../../'+target.relative_to(ROOT).as_posix()
        records.append({'frame':frame,'source':source.relative_to(ROOT).as_posix(),'source_frame':1 if frame>=100 else frame,
          'hat':config,'path':mapping['frame_mapping'][str(frame)],'size':[320,256],'bytes':target.stat().st_size,
          'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'visible_bounds':list(revised.getbbox()),'revision':REVISION})
    save(OUT/'body-atlas.png',atlas,assets,'offline six-pose review atlas; individual body sprites remain below 50KB')
    mapping.update(revision=REVISION,output_atlas='../../../'+(OUT/'body-atlas.png').relative_to(ROOT).as_posix(),output_atlas_frame_order=order,
      hat_revision=REVISION,body_review_records=records,review_records=[rec for rec in records if rec['frame']>=100],
      review_note='友方术法师战斗形象补椭圆宽帽檐，保留原尖帽帽锥与面部，六姿势帽型统一；全身饱和度仅轻降10%，原暖色保留。原动作和所有已确认法术特效、结算不变。',
      art_mode='existing body pixels mildly desaturated; separate rounded brim under source crown; face protected')
    MAPPING.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
      'saturation_factor':SATURATION_FACTOR,'hue_and_value_preserved':True,'near_black_threshold':32,'hat_config':CONFIG,'brim_palette':BRIM,
      'review_timeline_unchanged':before['mapping']['review_timeline'],'assets':assets},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'body_frames':len(records),'saturation_factor':SATURATION_FACTOR,'review_effects_unchanged':True},ensure_ascii=False))


if __name__=='__main__':create()

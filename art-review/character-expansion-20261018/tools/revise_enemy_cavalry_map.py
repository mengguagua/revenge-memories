#!/usr/bin/env python3
"""Enemy cavalry: register existing leg phases and limit to a blue-violet palette."""
import colorsys
from functools import lru_cache
import json
from PIL import Image
from revise_cavalry_map import ROOT, digest, signature, translate, polygon

REVISION = 'enemy-cavalry-map-blue-violet-v1-20261021'
OUT = ROOT/REVISION
MAPPING = ROOT/'professions/class-1-enemy/maps/frame_mapping.json'
PALETTE = ['191c2b', '292b45', '30385d', '425b83', '647fa6', '8eabc6',
           '454064', '635586', '8b7da9', '7e90a6', '9eadc2', 'd6dce4',
           '947b78', 'cbb5a5', '4f607a', 'b0a2c6']
COLORS = [tuple(bytes.fromhex(c)) for c in PALETTE]
FRONT = [(30,53),(49,53),(48,70),(48,83),(25,83),(25,60),(29,57)]
HIND = [(53,58),(77,58),(84,64),(84,83),(51,83),(51,64)]
WALK = {
    'up': {'frames':[0,1], 'translations':[[0,0],[0,-4]], 'leg_start':70, 'fixed_point':[64,44]},
    'right': {'frames':[2,3], 'translations':[[5,-1],[1,0]], 'leg_start':73, 'fixed_point':[64,54]},
    'down': {'frames':[4,5], 'translations':[[0,0],[0,-5]], 'leg_start':74, 'fixed_point':[64,48]},
}
FACES = {
    'tactical-idle': {0:(49,26,63,35),1:(48,26,62,35),2:(51,26,65,35),
                      3:(48,26,62,35),4:(49,26,63,35),5:(48,26,62,35)},
    'tactical-walk': {2:(55,38,67,48),3:(59,37,71,47),4:(57,27,73,39),5:(57,32,73,44)},
}


def luma(rgb):
    return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2]


@lru_cache(maxsize=60000)
def recolor(rgb, face):
    h,s,v = colorsys.rgb_to_hsv(*(x/255 for x in rgb))
    if v < .12:
        return COLORS[0]
    if v < .23:
        return COLORS[1]
    if face and h < .18 and s > .18:
        candidates = [12,13]
    elif .50 <= h < .78 and s > .18:
        candidates = [1,2,3,4,5]
    elif (h < .055 or h > .88) and s > .23:
        candidates = [1,6,7,8,15]
    else:
        candidates = [0,1,2,14,9,10,11]
    target = .75*max(rgb)+.25*luma(rgb)
    return COLORS[min(candidates,key=lambda i:abs(luma(COLORS[i])-target))]


def limited(image, kind, index):
    box = FACES[kind].get(index)
    result = Image.new('RGBA',image.size)
    data = []
    for y in range(image.height):
        for x in range(image.width):
            p = image.getpixel((x,y))
            face = bool(box and box[0]<=x<box[2] and box[1]<=y<box[3])
            data.append((*recolor(p[:3],face),255) if p[3]>=128 else (0,0,0,0))
    result.putdata(data)
    return result


def create():
    OUT.mkdir(exist_ok=True)
    baseline = OUT/'baseline.json'
    if not baseline.exists():
        mapping = json.loads(MAPPING.read_text())
        data = json.loads((ROOT/'demos/gallery-data.json').read_text())
        baseline.write_text(json.dumps({'mapping':mapping,
            'sources':{r['output_path']:digest((MAPPING.parent/r['output_path']).resolve()) for s in mapping['scenarios'] for r in s['frame_mapping']},
            'digests':{a['id']:a['contentDigest'] for a in data['actions']},
            'timelines':{a['id']:signature(a) for a in data['actions']},
            'accepted_ally_mapping_sha256':digest(ROOT/'professions/class-1-ally/maps/frame_mapping.json')},ensure_ascii=False,indent=2)+'\n')
    before = json.loads(baseline.read_text())
    mapping = json.loads(json.dumps(before['mapping']))
    sources = {s['id']:{r['source_index']:limited(Image.open((MAPPING.parent/r['output_path']).resolve()).convert('RGBA'),s['id'],r['source_index'])
                        for r in s['frame_mapping']} for s in mapping['scenarios']}
    idle = sources['tactical-idle'];stand = idle[1]
    poses = [stand.copy(),stand.copy(),stand.copy()]
    poses[0].paste(translate(idle[0],[-1,0]),(0,0),polygon(stand.size,FRONT))
    poses[2].paste(translate(idle[2],[-3,0]),(0,0),polygon(stand.size,HIND))
    poses = [translate(im,[-6,0]) for im in poses]
    aliases = [0,1,2,1,0,1]
    output = {'tactical-idle':{i:poses[p] for i,p in enumerate(aliases)},'tactical-walk':{}}
    registrations = []
    for direction,c in WALK.items():
        plates = [translate(sources['tactical-walk'][i],delta) for i,delta in zip(c['frames'],c['translations'])]
        for i,plate,delta in zip(c['frames'],plates,c['translations']):
            fixed = (0,0,128,c['leg_start']);image = plate.copy();image.paste(plates[0].crop(fixed),(0,0))
            output['tactical-walk'][i] = image
            registrations.append({'direction':direction,'frame':i,'translation':delta,'fixed_upper_box':list(fixed),'fixed_point':c['fixed_point']})
    for right,left in [(2,6),(3,7)]:
        output['tactical-walk'][left] = translate(output['tactical-walk'][right].transpose(Image.Transpose.FLIP_LEFT_RIGHT),[1,0])
        registrations.append({'direction':'left','frame':left,'mirror_of':right,'mirror_axis':64,'fixed_upper_box':[0,0,128,73],'fixed_point':[64,54]})
    assets = []
    def save(image, name, purpose):
        p = OUT/name;p.parent.mkdir(parents=True,exist_ok=True);image.save(p,optimize=True)
        assets.append({'path':p.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(image.size),'bytes':p.stat().st_size,
            'sha256':digest(p),'visible_bounds':list(image.getbbox()),'visible_colors':len({p[:3] for p in image.getdata() if p[3]})})
        return '../../../'+p.relative_to(ROOT).as_posix()
    for scenario in mapping['scenarios']:
        kind = scenario['id'];w,h = scenario['output_frame_size'];atlas = Image.new('RGBA',(w*len(output[kind]),h))
        for rec in scenario['frame_mapping']:
            i = rec['source_index'];im = output[kind][i];path = save(im,f'{kind}/frame-{i:03}.png','enemy cavalry / fixed center / dark blue-violet sixteen-color palette')
            atlas.alpha_composite(im,(w*i,0));previous = dict(rec);rec.clear()
            rec.update(source_index=i,source_frame=previous.get('source_frame',i),path=path,output_path=path,
                previous_record=previous,previous_output_path=previous['output_path'],revision=REVISION,
                size=[w,h],bytes=assets[-1]['bytes'],sha256=assets[-1]['sha256'],visible_bounds=list(im.getbbox()),
                kind='registered_enemy_pixel_art_with_blue_violet_palette',art_review_status='pending_user_visual_acceptance')
        scenario.update(output_atlas=save(atlas,kind+'-atlas.png','offline enemy cavalry review atlas'),output_atlas_bytes=assets[-1]['bytes'],
            revision=REVISION,status='review_candidate',art_review_status='pending_user_visual_acceptance',
            registration_note='Fixed upper plate and center; original enemy leg phases registered by integer translation; x=64 mirror axis.',
            review_note='敌方骑兵待机和四向主体、中心点固定，保留原马腿动作与节奏；统一最多16色暗蓝、蓝紫与冷蓝灰，保留可辨的色彩饱和度和少量自然肤色。仅更新对照页。')
    mapping.update(revision=REVISION,runtime_integrated=False,status='review_candidate',art_mode='existing enemy pixel art; registered fixed upper plates; shared blue-violet palette without dithering')
    MAPPING.write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    (OUT/'asset-manifest.json').write_text(json.dumps({'revision':REVISION,'runtime_integrated':False,'image_generation_invoked':False,'chat_image_output':False,
        'palette':PALETTE,'palette_roles':'dark blue armor, blue-violet fabric, cool blue-gray horse; skin only inside rider face masks',
        'idle_fixed_point':[48,48],'idle_translation':[-6,0],'idle_foreleg_mask':FRONT,'idle_hindleg_mask':HIND,
        'idle_phase_registration':{'0':[-1,0],'1':[0,0],'2':[-3,0]},'idle_aliases':aliases,'walk_registration':registrations,'face_masks':FACES,
        'assets':assets},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'revision':REVISION,'frames':14,'palette_colors':len(PALETTE)},ensure_ascii=False))
    return output


if __name__=='__main__':
    create()

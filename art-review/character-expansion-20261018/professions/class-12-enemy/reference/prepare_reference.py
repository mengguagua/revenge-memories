"""Copy/crop/nearest-neighbor magnify source pixels only. No new artwork."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,itertools,shutil
R=Path(__file__).resolve().parent
B=R.parents[2]
D=json.loads((B/'source-input/enemy-motion/full-enemy-motion.json').read_text())
C=next(c for c in json.loads((B/'catalog/class-catalog.json').read_text())['classes'] if c['class_id']==12)
BODY=D['original_bodies']['12']
REGIONS=[('head-and-neck',1,[30,30,43,41]),('torso-belt-and-arms',1,[29,37,43,55]),('bow-string-and-nock',5,[19,24,49,57]),('release-hand-and-string',6,[15,24,51,47]),('feet-and-knees',6,[29,49,43,64])]

def save_source(path,name):
    im=Image.open(path).convert('RGBA')
    shutil.copy2(path,R/f'{name}-source-native.png')
    im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(R/f'{name}-source-4x.png')

def main():
    atlas=Image.open(B/BODY['path']).convert('RGBA')
    for i in [1,5,6]:
        f=atlas.crop((i*80,0,(i+1)*80,64));f.save(R/f'battle-pose-{i:03d}-source-native.png')
        f.resize((320,256),Image.Resampling.NEAREST).save(R/f'battle-pose-{i:03d}-source-4x.png')
        b=f.getbbox();f.crop(b).resize(((b[2]-b[0])*12,(b[3]-b[1])*12),Image.Resampling.NEAREST).save(R/f'battle-pose-{i:03d}-tight-12x.png')
    source_paths={'map-idle':'source-input/legacy-assets/assets/original/graphics/map_units/class_12_enemy.png',
      'map-acted':'source-input/legacy-assets/assets/original/graphics/map_units/class_12_enemy_acted.png',
      'map-walk':'source-input/original-motion/original-walk-12.png'}
    for name,path in source_paths.items():save_source(B/path,name)
    arrow_id=next(f['effects'][0]['sprite'] for f in D['variants']['class_12_enemy_bow']['frames'] if f.get('effects'))
    arrow=D['sprites'][arrow_id]
    old=R/'arrow-source-native.png'
    if old.exists() and old.read_bytes()!=(B/arrow['path']).read_bytes():
        shutil.copy2(old,R/'arrow-previous-legacy-reference.png')
    save_source(B/arrow['path'],'arrow')
    aliases={}
    for name,fw,unique in [('map-idle',24,[0,2]),('map-acted',24,[0,2]),('map-walk',32,[0,1])]:
        im=Image.open(R/f'{name}-source-native.png').convert('RGBA');groups={}
        for i in range(6):
            f=im.crop((i*fw,0,(i+1)*fw,24));groups.setdefault(hashlib.sha256(f.tobytes()).hexdigest(),[]).append(i)
            if i in unique and name!='map-acted':
                b=f.getbbox();f.crop(b).resize(((b[2]-b[0])*16,(b[3]-b[1])*16),Image.Resampling.NEAREST).save(R/f'{name}-{i:02d}-tight-16x.png')
        aliases[name]=list(groups.values())
    crops=[]
    for name,i,box in REGIONS:
        f=Image.open(R/f'battle-pose-{i:03d}-source-native.png').convert('RGBA');im=f.crop(box);out=R/f'detail-{name}-12x.png'
        im.resize((im.width*12,im.height*12),Image.Resampling.NEAREST).save(out)
        crops.append({'name':name,'source_frame':i,'source_rect':box,'path':out.name,'magnification':12,'purpose':'source semantic inspection only'})
    font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',18)
    board=Image.new('RGBA',(1180,830),'#1d2b35');draw=ImageDraw.Draw(board)
    draw.text((24,18),'敌弓兵 class12 / enemy · 原像素语义参考裁图',font=font,fill='#f1efe5')
    positions=[(30,80),(260,80),(500,80),(30,520),(520,520)]
    for (name,i,box),pos in zip(REGIONS,positions):
        im=Image.open(R/f'detail-{name}-12x.png').convert('RGBA');board.alpha_composite(im,pos)
        draw.text((pos[0],pos[1]-24),name,font=font,fill='#c7d1d5')
    board.convert('RGB').save(R/'semantic-detail-board.png',optimize=True)
    variants={}
    for k,v in D['variants'].items():
        if k.startswith('class_12_enemy'):
            variants[k]={'total_ticks':len(v['frames']),
              'body_rle':[{'frame':f,'ticks':len(list(g))} for f,g in itertools.groupby(x['frame'] for x in v['frames'])],
              'contact_tick':v['contact_tick'],'contact_count':v['contact_count'],
              'sound_requests':[{'tick':i,'ids':f['sound_requests']} for i,f in enumerate(v['frames']) if f.get('sound_requests')],
              'projectile_ticks':[{'tick':i,'effects':f['effects']} for i,f in enumerate(v['frames']) if f.get('effects')],
              'actor_origin':v['actor_origin'],'formation':v['formation']}
    files=[]
    for p in sorted(R.glob('*.png')):
        im=Image.open(p);files.append({'path':p.name,'purpose':'original-pixel reference only','size':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    geometry=[]
    for i in [1,5,6]:
        im=Image.open(R/f'battle-pose-{i:03d}-source-native.png');bb=im.getbbox();roi=(29,60,43,64);foot=im.crop(roi).getbbox()
        absolute=[foot[0]+roi[0],foot[1]+roi[1],foot[2]+roi[0],foot[3]+roi[1]];center=[(absolute[0]+absolute[2])/2,absolute[3]]
        geometry.append({'frame':i,'source_bbox':bb,'target_4x_bbox':[v*4 for v in bb],'feet_roi':roi,'feet_bbox':absolute,'feet_anchor':center,'target_feet_anchor':[v*4 for v in center]})
    payload={'class_id':12,'side':'enemy','status':'source-preparation-only; no new character art generated',
      'battle':{'source':BODY['path'],'logical_frame_size':[80,64],'future_output_frame_size':[320,256],
        'source_anchor':[40,64],'future_output_anchor':[160,256],'required_frames':[1,5,6],'source_default_facing':'left',
        'pose_semantics':{'1':'neutral bow-ready; also source recovery/hold','5':'full draw, diagonal strings converge at drawing hand','6':'release/recoil, drawing arm extended and string rebounding'},
        'geometry':geometry,'registration_warning':'Long bow reaches near feet. Use explicit boot ROI, not lower full-sprite bbox, for foot-center registration.','variants':variants},
      'tactical_map':{'idle':{'source':source_paths['map-idle'],'frame_size':[24,24],'future_output_frame_size':[96,96],
          'anchor':[12,20],'exact_pixel_alias_groups':aliases['map-idle'],'cycle':[0,1,2,1],'ticks':[14,8,14,8],'static_facing':True},
        'walk':{'source':source_paths['map-walk'],'frame_size':[32,24],'future_output_frame_size':[128,96],'anchor':[16,24],
          'source_chr':26,'source_sprite_id':52,'source_oam':C['tactical_walk']['source_oam'],'exact_pixel_alias_groups':aliases['map-walk'],
          'slots':{'down':[0,1],'up':[2,3],'right':[4,5],'left':'mirror of side slots'},'frame_ticks':16,'cycle_ticks':32,'move_ticks_per_tile':16,
          'heading_warning':'Three direction slots repeat the same two native poses; no independent front/back/side native drawings.'},
        'acted':{'source':source_paths['map-acted'],'same_geometry_as_idle':True,'exact_pixel_alias_groups':aliases['map-acted'],'reference_palette_state_only':True}},
      'projectile':dict(arrow,id=arrow_id,future_output_frame_size=[192,64]),'detail_crops':crops,'files':files}
    (R/'reference-index.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'files':len(files),'max_bytes':max(f['bytes'] for f in files),'arrow_id':arrow_id,'map_aliases':aliases},ensure_ascii=False))

if __name__=='__main__':main()

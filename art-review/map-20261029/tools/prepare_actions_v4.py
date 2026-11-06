"""Register existing map/archer bitmap poses to a fixed tactical-map foot layer.

No new character artwork and no production assets are modified. Sword/casting
poses retain their native map pixels; bow poses reuse this hero's bow artwork.
"""
import hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

OUT=Path(__file__).resolve().parents[1]
f=OUT/'data.js'
data=json.loads(f.read_text().split('=',1)[1].strip().removesuffix(';'))
manifest=[]
review=Image.new('RGB',(6*192,5*236),'#15232d')
draw=ImageDraw.Draw(review)
font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',17)
for row,j in enumerate(data['jobs']):
    source=Image.open(OUT/j['hero_sprite']['path']).convert('RGBA')
    original=source.crop((0,0,96,96))
    feet=original.crop((0,68,96,96))
    atlas=Image.new('RGBA',(128*6,128))
    frames=[]
    if j.get('bow'):
        body=Image.open(OUT/j['body']['path']).convert('RGBA')
        poses=list(dict.fromkeys(x['frame'] for x in j['body']['frames']))
        # Ready, raising, full draw, release, follow-through, ready. All are
        # authored bow poses; no sword pose appears in this map action atlas.
        order=[poses[0],poses[0],poses[1],poses[2],poses[2],poses[0]]
        for pose in order:
            raw=body.crop((pose%8*160,pose//8*144,pose%8*160+160,pose//8*144+144))
            raw=raw.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            raw=raw.resize((128,115),Image.Resampling.NEAREST)
            cell=Image.new('RGBA',(128,128))
            cell.paste(raw,(16,-13))
            # Restore the exact original tactical boots/lower legs at the
            # original foot anchor in every pose, including draw/release.
            cell.paste(Image.new('RGBA',(128,44)),(0,84))
            cell.paste(feet,(16,84))
            frames.append(cell)
        kind='bow'
        timeline=[[0,0],[1.05,1],[1.30,2],[1.94,3],[2.12,4],[2.72,5],[3.15,0]]
    else:
        for pose in range(6):
            cell=Image.new('RGBA',(128,128))
            cell.paste(source.crop((pose*96,0,pose*96+96,96)),(16,16))
            cell.paste(feet,(16,84))
            frames.append(cell)
        kind='sword' if j['hero']=='hunapu' else 'casting'
        timeline=([[0,0],[.90,1],[1.18,2],[1.88,0],[1.96,3],[2.12,5],[2.60,4],[3.15,0]]
                  if kind=='sword' else
                  [[0,0],[.95,1],[1.20,2],[1.64,0],[1.80,3],[2.45,5],[2.85,4],[3.35,0]])
    for i,cell in enumerate(frames):
        atlas.paste(cell,(i*128,0))
    name=('胡纳普' if j['hero']=='hunapu' else '艾琳')+' · '+j['profession']+(' · 持弓' if kind=='bow' else '')
    draw.text((12,row*236+3),name,font=font,fill='#c7e3e5')
    display=([0,1,2,3,4,0] if kind=='bow' else [0,2,0,3,4,0])
    captions=(['持弓准备','抬弓','拉满弓弦','松弦放箭','收势','准备'] if kind=='bow' else
              ['准备','举剑蓄势','挥剑起手','挥出／释放','收势','准备'])
    caption_font=ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc',13)
    for col,(pose,caption) in enumerate(zip(display,captions)):
        draw.text((col*192+55,row*236+24),caption,font=caption_font,fill='#9fbac6')
        thumb=frames[pose].resize((192,192),Image.Resampling.NEAREST)
        review.paste(thumb,(col*192,row*236+39),thumb)
    target=OUT/'assets'/f"{j['key']}-map-action-v4.png"
    atlas.save(target,optimize=True)
    hashes=[hashlib.sha256(c.crop((0,84,128,128)).tobytes()).hexdigest() for c in frames]
    assert len(set(hashes))==1,('foot drift',j['key'])
    j['map_action']={'path':str(target.relative_to(OUT)),'frame_size':[128,128],
                     'frames':6,'columns':6,'tile_origin':[8,8],'native_density':4,
                     'kind':kind,'timeline':timeline,'foot_lock_y':84,'idle':0,
                     'source':j['body']['path'] if kind=='bow' else j['hero_sprite']['path']}
    manifest.append({'path':str(target.relative_to(OUT)),'purpose':kind+'地图上身动作／固定双脚',
                     'pixels':list(atlas.size),'bytes':target.stat().st_size,
                     'foot_hash':hashes[0],'foot_frames_equal':True,'source':j['map_action']['source'],
                     'note':'复用既有位图姿势；地图剑系不改变像素比例；弓姿改持弓并右向放箭。固定下肢取原地图同一层。'})
data['version']='MAP art review 2026-10-29 / planted-foot actions revision 4'
f.write_text('window.MAP_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
(OUT/'sources/actions-v4.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
review.save(OUT/'sources/actions-v4-review.png',optimize=True)
print(json.dumps(manifest,ensure_ascii=False))

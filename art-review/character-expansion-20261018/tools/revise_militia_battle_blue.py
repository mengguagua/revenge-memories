#!/usr/bin/env python3
"""Adjust existing indexed material colors; preserve every pose pixel/alpha."""
import argparse,copy,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT
from export_gallery import font

REV='militia-battle-blue-v1-20261022';OUT=ROOT/REV
MAP=ROOT/'professions/class-14-ally/battle/frame_mapping.json'
RGB=lambda h:tuple(bytes.fromhex(h))
COAT={0:[172,166,212,212],1:[166,176,198,212],2:[174,178,208,214],3:[166,176,196,212],4:[176,180,206,222],5:[166,194,206,228],6:[176,192,212,230],32:[182,160,214,212]}
PANTS={0:[180,204,220,238],1:[156,202,232,246],2:[172,202,218,246],3:[162,202,222,246],4:[142,214,240,250],5:[142,220,232,252],6:[142,222,242,254],32:[172,206,226,244]}
BOOTS={0:[[172,224,196,256],[202,224,224,256]],1:[[156,206,180,230],[204,222,234,256]],2:[[184,212,218,256]],3:[[164,206,192,230],[194,224,224,256]],4:[[142,224,170,256],[212,226,240,256]],5:[[144,232,170,256],[204,232,232,256]],6:[[142,238,164,256],[216,228,242,256]],32:[[172,226,196,256],[204,226,226,256]]}
HEAD={0:[180,130,212,166],1:[148,146,180,180],2:[158,150,196,182],3:[150,148,190,180],4:[166,152,196,188],5:[158,164,192,200],6:[158,164,194,200],32:[180,132,212,164]}
SWORD={0:[[124,228],[132,236],[186,190],[182,178]],6:[[124,246],[128,252],[190,220],[188,210]]}
COAT_COLORS={'493025':'172638','7d4e2e':'2a3444','b04e25':'3976b5','b17b43':'3976b5'}
PANTS_COLORS={'516072':'f2e3c6','2a3444':'d8ded8'}
BOOT_COLORS={'493025':'172638','7d4e2e':'2a3444','b04e25':'2a3444','b17b43':'3976b5','b87950':'2a3444','8b7867':'2a3444'}
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def edit(im,index):
    out=im.copy();px=out.load();source=im.load();changed=[]
    protected=Image.new('1',im.size);draw=ImageDraw.Draw(protected)
    head=HEAD[index];draw.rectangle([head[0],head[1],head[2]-1,head[3]-1],fill=1)
    # The low sword crosses the leg region in this lunging pose.
    if index in SWORD:draw.polygon([tuple(p) for p in SWORD[index]],fill=1)
    for boxes,colors,material in [([COAT[index]],COAT_COLORS,'blue vest and sash'),([PANTS[index]],PANTS_COLORS,'white trousers'),(BOOTS[index],BOOT_COLORS,'navy boots')]:
        table={RGB(a):RGB(b) for a,b in colors.items()}
        for box in boxes:
            for y in range(box[1],box[3]):
                for x in range(box[0],box[2]):
                    p=source[x,y]
                    if p[3] and p[:3] in table and not protected.getpixel((x,y)):
                        px[x,y]=(*table[p[:3]],p[3]);changed.append([x,y,material])
    assert out.getchannel('A').tobytes()==im.getchannel('A').tobytes()
    return out,changed
def build(publish=False):
    baseline=json.loads((OUT/'baseline.json').read_text());m=copy.deepcopy(baseline['mapping'])
    old={int(k):Image.open((MAP.parent/path).resolve()).convert('RGBA') for k,path in m['frame_mapping'].items()}
    frames={};edits={};assets=[]
    for i in COAT:frames[i],edits[str(i)]=edit(old[i],i)
    for i in [16,31]:frames[i]=frames[0].copy();edits[str(i)]=edits['0']
    frames[7]=old[7].copy();p=frames[7].load()
    for x,y,material in edits['6']:
        if old[7].getpixel((x,y))==old[6].getpixel((x,y)):p[x,y]=frames[6].getpixel((x,y))
    edits['7']=edits['6']
    def save(im,name,purpose):
        path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
        assets.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'size':list(im.size),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        return '../../../'+path.relative_to(ROOT).as_posix()
    atlas=Image.new('RGBA',(11*320,256))
    for n,i in enumerate(sorted(frames)):
        path=save(frames[i],f'ally/frame-{i:03}.png','same battle pose with approved idle blue/white clothing')
        m['frame_mapping'][str(i)]=path;atlas.alpha_composite(frames[i],(n*320,0))
    for record in m.get('records',[]):
        i=record['source_frame'];record['path']=m['frame_mapping'][str(i)];record['palette_size']=len({p[:3] for p in frames[i].getdata()if p[3]})
    m.update(revision=REV,status='review_candidate',runtime_integrated=False,
       output_atlas=save(atlas,'ally/battle-atlas.png','packed battle poses in existing source slot order'),
       display_name='乡勇（职业样板）',art_generator='existing indexed material palette parameters',
       review_note='乡勇战斗服饰沿用已确认地图待机的主蓝3976b5、深蓝暗部、白裤与深蓝靴；仅换衣料颜色，全部帧的透明轮廓、位置、头发、肤色、剑刃和刀光保持。普通攻击、雷剑及通用反应同步，原时序与结算保持。',
       qa_report='../../../'+REV+'/verification.json',runtime_integration={'status':'not_integrated_this_color_revision','previous_version':'0.10.1'})
    write(OUT/'mapping-draft.json',m)
    if publish:write(MAP,m)
    for light in [False,True]:
        bg=(220,222,216) if light else (32,45,53);fg=(30,43,56) if light else (235,243,242)
        board=Image.new('RGB',(1700,700),bg);d=ImageDraw.Draw(board)
        d.text((850,22),'乡勇 · 战斗服饰统一待机蓝白配色',anchor='mm',font=font(22),fill=fg)
        for n,i in enumerate([0,1,2,3,4,5,6,7,32]):
            x=n%5*340;y=48+n//5*300
            for col,im in enumerate([old[i],frames[i]]):
                crop=im.crop(im.getbbox());assert crop.width<=170;board.paste(crop,(x+col*170+(170-crop.width)//2,y+24),crop)
            d.text((x+170,y+264),f'姿势{i} · 修改前 / 新配色',anchor='mt',font=font(14),fill=fg)
        idle=Image.open(ROOT/'militia-idle-flat-archer-blue-v2-20261021/ally/frame-001.png').convert('RGBA').resize((192,192),Image.Resampling.NEAREST)
        board.paste(idle,(1434,400),idle);d.text((1530,650),'已确认待机配色',anchor='mm',font=font(16),fill=fg)
        save(board,f'poses-{"light" if light else "dark"}.png','all nine unique poses before/after with accepted idle reference')
    write(OUT/'material-palette.json',{'method':'editable indexed material colors and native pose material selections; no new drawing','coat':COAT,'pants':PANTS,'boots':BOOTS,'protected_heads':HEAD,'coat_colors':COAT_COLORS,'pants_colors':PANTS_COLORS,'boot_colors':BOOT_COLORS,'protected_sword_polygons':SWORD,'edits':edits})
    write(OUT/'asset-manifest.json',{'revision':REV,'runtime_integrated':False,'image_generation_invoked':False,'assets':assets})
    print(json.dumps({'status':'published' if publish else 'staged','frames':len(frames),'assets':len(assets)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--publish',action='store_true');build(p.parse_args().publish)

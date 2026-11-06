"""Prepare art-only assets; original map bodies/feet and game files stay intact."""
import hashlib
import json
import math
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageOps

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'source/healer-map-20261104'
manifest=[]

def record(p,purpose,source):
    im=Image.open(p)
    manifest.append({'path':str(p.relative_to(OUT)),'purpose':purpose,'pixels':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source':source})

data=json.loads((OUT/'sources/runtime.json').read_text())
for j in data['jobs']:
    for role in ['caster','target','friend','enemy']:
        s=j[role+'_sprite'];p=ROOT/'actual'/s['path'].removeprefix('res://');q=OUT/'assets'/f"{j['key']}-{role}.png"
        shutil.copyfile(p,q);s['path']=str(q.relative_to(OUT));record(q,'复用当前地图角色，保留原始像素',str(p.relative_to(ROOT)))
    panel=ROOT/'actual'/j['panel']['path'].removeprefix('res://');shutil.copyfile(panel,OUT/'assets/panel.png');j['panel']['path']='assets/panel.png'
    # Only a small native bitmap limb/tool is articulated, avoiding a new
    # character design, body rescaling, walking or changes to the locked hem.
    spec=j['caster_sprite'];im=Image.open(OUT/spec['path']).convert('RGBA');w,h=map(int,spec['frame_size']);original=im.crop((0,0,w,h))
    mask=Image.new('L',(w,h));md=ImageDraw.Draw(mask)
    if j['key']=='healer':
        md.polygon([(65,42),(95,42),(95,83),(67,83),(67,74),(57,71),(57,62),(65,62)],fill=255);pivot=(59,67);angles=[0,-12,-24,-14,0]
    else:
        md.polygon([(16,41),(37,41),(45,50),(46,61),(39,64),(29,59),(16,57)],fill=255);pivot=(42,56);angles=[0,12,24,12,0]
    empty=Image.new('L',(w,h));limb=original.copy();limb.putalpha(Image.composite(original.getchannel('A'),empty,mask));body=original.copy();body.putalpha(Image.composite(empty,original.getchannel('A'),mask))
    fixed=Image.new('RGBA',(128,128));fixed.alpha_composite(body,(16,16));part=Image.new('RGBA',(128,128));part.alpha_composite(limb,(16,16));idle=Image.new('RGBA',(128,128));idle.alpha_composite(original,(16,16))
    atlas=Image.new('RGBA',(128*len(angles),128));feet=idle.crop((0,100,128,128)).tobytes();poses=[]
    for i,angle in enumerate(angles):
        moved=part.rotate(angle,resample=Image.Resampling.NEAREST,center=(pivot[0]+16,pivot[1]+16));cell=fixed.copy();cell.alpha_composite(moved)
        assert cell.crop((0,100,128,128)).tobytes()==feet,('feet moved',j['key'],i)
        if angle==0:assert cell.tobytes()==idle.tobytes()
        atlas.alpha_composite(cell,(i*128,0));poses.append(cell)
    q=OUT/'assets'/f"{j['key']}-cast.png";atlas.save(q,optimize=True);record(q,'原地图手臂/法器单次举起、引导、收势；下摆和脚固定',spec['path'])
    j['cast']={'path':str(q.relative_to(OUT)),'frame_size':[128,128],'columns':5,'native_density':4,'tile_origin':[spec['tile_origin'][0]+4,spec['tile_origin'][1]+4],'timeline':[[0,0],[.04,1],[.14,2],[.30,3],[.72,4]],'flip':j['key']=='saint','foot_pixels_unchanged':True,'idle_pixels_unchanged':True}
    j['name']='济世·愈护之环' if j['key']=='saint' else '愈护之环';j['profession']='济世术师' if j['key']=='saint' else '疗愈师';j['heal_steps']=[2,6,10] if j['key']=='saint' else [0,3,6];j['hp_cost']=[0,.15,.25];j['effect']='assets/'+j['key']+'-fx.png'
    stage=json.loads((ROOT/'actual/data/stages'/f"{j['stage_code']}.json").read_text());j['map_size']=[stage['map']['width'],stage['map']['height']]

for key in ['healer','saint']:
    source=SOURCE/(key+'-fx-raw.png');raw=Image.open(source).convert('RGBA');cw,ch=raw.width//3,raw.height//2;sheet=Image.new('RGBA',(192*3,192*2));registration=[]
    for i in range(6):
        cell=raw.crop(((i%3)*cw,(i//3)*ch,(i%3+1)*cw,(i//3+1)*ch));bright=ImageChops.multiply(ImageOps.grayscale(cell),cell.getchannel('A'));pixels=list(bright.getdata());threshold=list(bright.point(lambda x:x if x>97 else 0).getdata())
        masses=[sum(threshold[y*cw:(y+1)*cw])for y in range(ch)];bottom=max(range(int(ch*.58),ch),key=lambda y:masses[y]);band=[sum(pixels[y*cw+x]for y in range(max(0,bottom-4),min(ch,bottom+5)))for x in range(cw)];center=round(sum(x*v for x,v in enumerate(band))/max(sum(band),1))
        shift=(round(cw*.5)-center,round(ch*.84)-bottom);registered=Image.new('RGBA',cell.size);registered.alpha_composite(cell,shift);registered=registered.resize((192,192),Image.Resampling.NEAREST)
        sheet.alpha_composite(registered,((i%3)*192,(i//3)*192));registration.append({'frame':i,'original_floor':[center,bottom],'shift':list(shift)})
    q=OUT/'assets'/(key+'-fx.png');sheet.save(q,optimize=True);record(q,'imagegen专用单人治疗特效六帧，按脚底注册',str(source.relative_to(ROOT)));(OUT/'sources'/(key+'-fx-registration.json')).write_text(json.dumps(registration,indent=2)+'\n')

icon=Image.open(SOURCE/'strong-body-raw.png').convert('RGBA');icon=icon.crop(icon.getchannel('A').point(lambda x:255 if x>20 else 0).getbbox());icon.thumbnail((40,40),Image.Resampling.NEAREST);small=Image.new('RGBA',(48,48));small.alpha_composite(icon,((48-icon.width)//2,(48-icon.height)//2));q=OUT/'assets/strong-body.png';small.save(q,optimize=True);record(q,'强身护甲图标，倒计时由UI独立叠加',str((SOURCE/'strong-body-raw.png').relative_to(ROOT)))
font=json.loads((ROOT/'actual/data/legacy/font_small_zh.json').read_text());shutil.copyfile(ROOT/'actual'/font['path'].removeprefix('res://'),OUT/'assets/font-small.png');font['path']='assets/font-small.png';data['font']=font
large=json.loads((ROOT/'actual/data/legacy/font_zh.json').read_text());raw_font=Image.open(ROOT/'actual'/large['path'].removeprefix('res://')).convert('RGBA');chars=list(dict.fromkeys('胡纳普强身奥托'));labels=Image.new('RGBA',(len(chars)*12,12));label_glyphs={}
for i,ch in enumerate(chars):
    g=large['glyphs'][ch];x,y,w,h=g['rect'];labels.alpha_composite(raw_font.crop((x,y,x+w,y+h)),(i*12,0));label_glyphs[ch]={'rect':[i*12,0,12,12],'advance':12}
labels.save(OUT/'assets/font-labels.png',optimize=True);data['label_font']={'path':'assets/font-labels.png','glyphs':label_glyphs}
data.update({'schema':1,'date':'2026-11-04','buff':{'name':'强身','physical_defence':2,'turns':2,'stacking':'refresh only'},'release':.30,'impact':.58,'preview_only':True,'fx_cell':192,'fx_anchor':[96,161]})
(OUT/'data.js').write_text('window.HEAL_MAP_DATA='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n');(OUT/'sources/asset-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
# A source pose board verifies both class identities and the locked lower body.
board=Image.new('RGB',(850,310),'#16252e')
for row,j in enumerate(data['jobs']):
    atlas=Image.open(OUT/j['cast']['path'])
    for col,index in enumerate([0,1,2,3,4]):
        p=atlas.crop((128*index,0,128*(index+1),128)).resize((150,150),Image.Resampling.NEAREST);board.paste(p,(col*170,row*155),p)
board.save(OUT/'sources/map-cast-poses.png',optimize=True)
print(json.dumps({'jobs':[(j['key'],j['caster_at'],j['target_at'])for j in data['jobs']],'assets':len(manifest),'body_and_feet_preserved':True}))

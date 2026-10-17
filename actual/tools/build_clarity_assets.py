#!/usr/bin/env python3
"""Native indexed-pixel palette edits: never resize or deform actor geometry."""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/hunapu-0.5.2'
REPORT=ROOT/'reports/clarity-0.5.2'
SOURCE=ROOT/'source/clarity-0.5.2'
COLORS={'outline':'#101c31','hair':'#377be8','hair_light':'#82c0ff','armor':'#348aa5','armor_light':'#98e0dd','cloak':'#fff1c9','skin':'#f4c394','boots':'#c5a17b','steel':'#e3eaf3','rest_mid':'#71868c','rest_light':'#b9c8ca','rest_dark':'#344650'}
C={k:tuple(bytes.fromhex(v[1:]))for k,v in COLORS.items()}
BLUE=(21,95,217);CYAN=(72,205,222);PINK=(254,204,197)
# Native head rectangles for poses whose raised sword hand is thicker than
# the face. These are palette labels only: no pixel is added, moved or removed.
HEADS={4:(45,37,52,43),11:(45,37,52,43),12:(45,37,52,43),16:(45,37,52,43),19:(45,37,53,44),120:(44,40,51,46),121:(44,39,51,45),122:(44,36,51,42)}
def save(im,path):
    path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)
    subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True)
def write(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def alpha(im):return im.getchannel('A').tobytes()
def battle_cell(old,frame):
    im=old.copy();p=old.load();box=old.getbbox()
    if box is None:return im
    # Thick skin clusters identify the face; thin disconnected sword/arc pixels
    # never affect the original geometry, feet, gaps or weapon trajectory.
    candidates=[]
    for y in range(old.height):
        for x in range(old.width):
            if p[x,y][:3]!=PINK or not p[x,y][3]:continue
            count=sum(0<=x+dx<80 and 0<=y+dy<72 and p[x+dx,y+dy][:3]==PINK and p[x+dx,y+dy][3]>0 for dx in [-1,0,1]for dy in [-1,0,1])
            if count>=4:candidates.append((count-y*.035,x,y))
    face=max(candidates,default=(0,(box[0]+box[2])//2,box[1]+4))
    _,fx,fy=face
    head_rect=HEADS.get(frame)
    if head_rect:fx=(head_rect[0]+head_rect[2])//2;fy=head_rect[1]+3
    for y in range(old.height):
        for x in range(old.width):
            rgba=p[x,y]
            if not rgba[3]:continue
            rgb=rgba[:3]
            head=abs(x-fx)<=4 and fy-5<=y<=fy+1
            if head_rect:head=head_rect[0]<=x<head_rect[2] and head_rect[1]<=y<head_rect[3]
            if rgb==BLUE:key='hair' if head else 'armor'
            elif rgb==CYAN:key='hair_light' if head else 'armor_light'
            elif rgb==PINK:
                near=any(0<=x+dx<80 and 0<=y+dy<72 and p[x+dx,y+dy][:3]in [BLUE,CYAN] and p[x+dx,y+dy][3]>0 for dx,dy in [(0,-1),(0,1),(-1,0),(1,0)])
                key='skin' if near or (abs(x-fx)<=3 and abs(y-fy)<=4) else 'steel'
            else:key='outline'
            if rgb==CYAN and fy+2<=y<=fy+5 and fx<=x<=fx+7:key='cloak'
            if rgb in [BLUE,CYAN] and y>=max(fy+16,box[3]-5):key='boots' if rgb==CYAN else 'armor'
            im.putpixel((x,y),(*C[key],255))
    assert alpha(im)==alpha(old)
    return im
def hub_cell(old,frame):
    im=old.copy()
    for y in range(old.height):
        for x in range(old.width):
            rgb=old.getpixel((x,y))
            if not rgb[3]:continue
            if rgb[:3]==(0,0,0):key='outline'
            elif y<=13:key='hair_light' if rgb[:3]==PINK and frame in [2,3] else 'skin' if rgb[:3]==PINK else 'hair'
            elif rgb[:3]==PINK:key='skin'
            elif y<=16:key='cloak'
            elif y>=21:key='boots'
            else:key='armor'
            im.putpixel((x,y),(*C[key],255))
    assert alpha(im)==alpha(old)
    return im
def plate(rows,cols,fw,fh,scale):
    im=Image.new('RGB',(cols*fw*scale,((len(rows)+cols-1)//cols)*(fh*scale+18)),(31,44,54));d=ImageDraw.Draw(im)
    for i,(name,cell) in enumerate(rows):
        x=i%cols*fw*scale;y=i//cols*(fh*scale+18);cell=cell.resize((fw*scale,fh*scale),Image.Resampling.NEAREST);im.paste(cell,(x,y),cell);d.text((x+4,y+fh*scale+2),str(name),fill='white')
    return im
def main():
    OUT.mkdir(parents=True,exist_ok=True);REPORT.mkdir(parents=True,exist_ok=True)
    original=ROOT/'assets/original/graphics/battle/class_21_ally.png';old=Image.open(original).convert('RGBA');sheet=Image.new('RGBA',old.size);frames=[]
    for f in range(133):
        cell=old.crop((f*80,0,(f+1)*80,72));new=battle_cell(cell,f)
        if f==8:
            base=old.crop((9*80,0,10*80,72));body=battle_cell(base,9)
            for y in range(72):
                for x in range(80):
                    if cell.getpixel((x,y))[3] and not base.getpixel((x,y))[3]:body.putpixel((x,y),(*C['steel'],255))
            new=body
        if f==124:
            for y in range(72):
                for x in range(80):
                    if cell.getpixel((x,y))[3]:new.putpixel((x,y),(*C['steel'],255))
        assert alpha(new)==alpha(cell)
        sheet.paste(new,(f*80,0));frames.append(new);save(new,OUT/'frames'/f'battle-{f}.png')
    assert alpha(sheet)==alpha(old);save(sheet,OUT/'battle.png')
    personal=Image.open(ROOT/'assets/original/graphics/map_units/personal_01.png').convert('RGBA');hub=Image.new('RGBA',personal.size);maps=[];hubs=[]
    for f in range(6):
        cell=personal.crop((f*32,0,(f+1)*32,24));new=hub_cell(cell,f);hub.paste(new,(f*32,0));hubs.append(new)
        # Exact integer cell registration; equivalent tile origins 8 vs 4.
        small=new.crop((4,0,28,24));maps.append(small)
        assert alpha(small)==alpha(cell.crop((4,0,28,24)))
        save(new,OUT/'frames'/f'hub-{f}.png');save(small,OUT/'frames'/f'map-{f}.png')
    assert alpha(hub)==alpha(personal);save(hub,OUT/'hub.png');map_sheet=Image.new('RGBA',(144,24))
    for f,cell in enumerate(maps):map_sheet.paste(cell,(f*24,0))
    save(map_sheet,OUT/'map.png')
    graphics=json.loads((ROOT/'data/legacy/graphics.json').read_text());prior=json.loads((ROOT/'data/hunapu_visuals.json').read_text())
    data=dict(prior,version='0.5.2',palette=COLORS,registration='Exact source alpha masks on all 133 battle frames and all six original personal village poses. Indexed color edits only; no character resampling, bbox fitting, outline filling or pose morphs.',map=dict(graphics['map_units']['class_21_ally'],path='res://assets/hunapu-0.5.2/map.png',source_note='Original personal-01 pixel skeleton, integer cell-origin conversion; original frame cadence.'),hub=dict(graphics['village_sprites']['1'],path='res://assets/hunapu-0.5.2/hub.png'),battle=dict(prior['battle'],path='res://assets/hunapu-0.5.2/battle.png'))
    data['map'].pop('acted_variant',None);data['native_battle_frames_preserved']=133
    critical=json.loads((SOURCE/'critical-timeline.json').read_text())
    data.pop('critical_timeline',None)
    data['authored_critical_reference']=critical['timeline'];data['critical_source']=critical['source_program']
    data['executed_melee']=json.loads((SOURCE/'executed-melee.json').read_text())['programs']
    data['source_contact_tick']=data['executed_melee']['normal']['contact_tick']
    data['source_total_ticks']=len(data['executed_melee']['normal']['frames'])
    data['source_critical_contact_tick']=data['executed_melee']['critical']['contact_tick']
    data['source_critical_total_ticks']=len(data['executed_melee']['critical']['frames'])
    data['source_timeline_sha256']=hashlib.sha256((SOURCE/'executed-melee.json').read_bytes()).hexdigest()
    data['active_battle_frames']=sorted(set(active for active in data['active_battle_frames'])|{int(f['frame'])for phase in ['before_contact','after_contact']for f in critical['timeline'][phase]})
    write(ROOT/'data/hunapu_visuals.json',data)
    save(plate(list(enumerate(hubs)),3,32,24,8),REPORT/'walk-design.png')
    active=data['active_battle_frames'];save(plate([(i,frames[i])for i in active],4,80,72,4),REPORT/'battle-design.png')
    manifest=[]
    for p in sorted(OUT.rglob('*.png')):
        im=Image.open(p).convert('RGBA');colors={p[:3]for p in im.getdata()if p[3]};assert colors<=set(C.values())
        manifest.append({'path':str(p.relative_to(ROOT)),'pixels':list(im.size),'bytes':p.stat().st_size,'colors':len(colors),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    write(REPORT/'asset-manifest.json',manifest)
    write(REPORT/'geometry-checks.json',{'passed':True,'source_battle':str(original.relative_to(ROOT)),'battle_frames_exact_alpha':133,'hub_frames_exact_alpha':6,'map_frame_integer_crop':[4,0,28,24],'resampled_actor_pixels':0,'palette':COLORS,'max_colors':12,'scope':'Geometry and source hand/leg negative-space preservation; motion and rendering checked separately.'})
    portraits=json.loads((ROOT/'data/portraits.json').read_text());portrait_records=[];portrait_preview=[]
    for phase in ['present','memory','victory']:
        key='hunapu_'+phase;raw=Image.open(SOURCE/(key+'-generated.png')).convert('RGB')
        native=raw.resize((48,48),Image.Resampling.NEAREST).quantize(colors=24,dither=Image.Dither.NONE).convert('RGB')
        path=ROOT/'assets/portraits-0.5.2'/(key+'.png');save(native,path)
        portraits['assets'][key]['path']='res://'+str(path.relative_to(ROOT));portraits['assets'][key]['facial_features']='Native dark closed-mouth line, nose and separate eyes; individually inspected at 48px.'
        portrait_records.append({'path':str(path.relative_to(ROOT)),'pixels':[48,48],'bytes':path.stat().st_size,'colors':len(native.getcolors()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        portrait_preview.append((key,native.convert('RGBA')))
    portraits['version']='0.5.2';write(ROOT/'data/portraits.json',portraits)
    write(REPORT/'portrait-manifest.json',portrait_records);save(plate(portrait_preview,3,48,48,8),REPORT/'portrait-design.png')
    print('Native actor geometry: 133 battle + six hub + six map frames, zero resampled pixels')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Recover every original FE2 class sheet, body program and personal map actor.

All shapes are decoded from the original CHR/OAM/nametable uploads; nothing is
redrawn. The separate source programs preserve special attacks for the native
player, instead of silently substituting another class's melee animation.
"""
from pathlib import Path
import argparse, copy, json, math, re, sys
from PIL import Image, ImageDraw
from extract_graphics import ROOT, OUT, DATA, blocks, decode, color, save, VILLAGE_TABLES, VILLAGE_PALETTE
from extract_archer import movement_program

FPS = 60.0988
NAMES = ['cavalier','knight','pegasus_knight','paladin','falcon_knight','soldier','gold_knight','mercenary','myrmidon','dread_fighter','priestess','archer','sniper','villager','mage','female_mage','saint','cleric','sage','bow_knight','fighter','baron']
ENEMY = {3:'gargoyle',5:'necrodragon',11:'revenant',14:'brigand',15:'arcanist',16:'witch',17:'bonewalker',18:'mogall',19:'cantor',21:'duma'}

def signed(v): return v-256 if v>=128 else v

class Source:
    def __init__(self, root):
        self.root=root; self.b={i:blocks(root/'src'/f'bank{i:03}.asm') for i in range(16)}
        self.rom=(root/'fe2.nes').read_bytes()
        self.tiles={c:decode((root/'src'/f'bank{c//2:03}.chr').read_bytes())[(c%2)*256:(c%2+1)*256] for c in range(32)}
    def rb(self,b,a):return self.rom[16+b*16384+a-0x8000]
    def rw(self,b,a):return self.rb(b,a)+256*self.rb(b,a+1)
    def label(self,b,a):return f'L{b:02X}{a:04X}'
    def ptr(self,b,a):return self.label(b,self.rw(b,a))
    def pose_program(self,i):
        p=self.rw(0,0x9ff1+i*2);t=self.rw(0,0xa051+i*2)
        poses=[];ticks=[];terminal=255
        for j in range(1024):
            v=self.rb(0,t+j)
            if v in [254,255]:terminal=v;break
            poses.append(self.rb(0,p+j));ticks.append(v or 256)
        return {'id':i,'poses':poses,'ticks':ticks,'terminal':terminal,
                'pose_source':self.label(0,p),'timer_source':self.label(0,t)}
    def commands(self,ref):
        a=int(ref[3:],16); cmds=[]
        for j in range(512):
            op=self.rb(5,a);a+=1
            if op==14:cmds.append({'opcode':op});break
            arg=self.rb(5,a);a+=1;cmds.append({'opcode':op,'argument':arg})
        else:raise AssertionError(('unterminated',ref))
        return cmds

def oam_entries(raw,tiles,pal):
    count=raw[0]; assert len(raw)>=1+count*4
    out=[]
    for i in reversed(range(count)):
        y,t,a,x=raw[1+i*4:5+i*4];im=color(tiles[t],pal)
        if a&64:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if a&128:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        out.append((signed(x),signed(y),im))
    return out

def bg_entries(raw,tiles,pal,mirror=False):
    assert raw[0]<=len(raw)-1,(raw[0],len(raw))
    raw=raw[:raw[0]+1] # Last block can include unlabeled alignment bytes.
    out=[];p=1;base=12*32+22
    while p<len(raw):
        delta=raw[p]+256*raw[p+1];delta=delta-65536 if delta>=32768 else delta
        cmd=raw[p+2];p+=3;count=cmd&63;step=32 if cmd&128 else 1
        # The source body upload path consumes count literal tiles. Bit6 is
        # absent in all these relative body blocks, unlike general PPU uploads.
        assert not cmd&64
        for j in range(count):
            absolute=base+delta+j*step;x=(absolute%32-22)*8;y=(absolute//32-12)*8
            tile=color(tiles[raw[p]],pal);p+=1
            if mirror:x=-x-8;tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            out.append((x,y,tile))
    assert p==len(raw)
    return out

def make_sheet(frames,ground=32,minimum=(80,64)):
    xs=[-minimum[0]//2,minimum[0]//2];ys=[ground-minimum[1],ground]
    for entries in frames:
        for x,y,tile in entries:
            box=tile.getbbox()
            if box:xs.extend([x+box[0],x+box[2]]);ys.extend([y+box[1],y+box[3]])
    half=math.ceil(max(abs(min(xs)),abs(max(xs)))/8)*8
    top=math.floor(min(ys)/8)*8;bottom=math.ceil(max(ys)/8)*8
    size=(half*2,bottom-top);anchor=[half,ground-top]
    sheet=Image.new('RGBA',(size[0]*len(frames),size[1]));bounds=[]
    for i,entries in enumerate(frames):
        im=Image.new('RGBA',size)
        for x,y,tile in entries:im.alpha_composite(tile,(x+half,y-top))
        bounds.append(im.getbbox());sheet.alpha_composite(im,(i*size[0],0))
    assert sheet.width<=16384,(sheet.size,'split frame atlas before import')
    return sheet,list(size),anchor,bounds

def standard_timeline(src,commands,oam_count,idle,initial_bg=True):
    """Native authored body timeline, omitting bytecode dispatch overhead.

    Motion and pose tables are advanced together for each authored wait. The
    original damage pause is the boundary between the two returned arrays.
    """
    phase='before_contact';out={'before_contact':[],'after_contact':[]}
    pose=idle;bg=initial_bg;flip=False;offset=[0,0];motion=[];mi=0;poseprog=None;pi=0;pt=0;paused=False;timer=0
    events=[]; warnings=[]
    def frame(): return {'frame':oam_count+pose if bg else pose,'offset':offset.copy(),'flip':flip}
    def tick():
        nonlocal pi,pt,mi,pose,poseprog
        out[phase].append(frame())
        if mi<len(motion):
            dx,dy=motion[mi];offset[0]+=dx;offset[1]+=dy;mi+=1
        if poseprog and not paused:
            pt-=1
            if pt<=0:
                pi+=1
                if pi>=len(poseprog['poses']):
                    if poseprog['terminal']==254:pi=0
                    else:poseprog=None;return
                pose=poseprog['poses'][pi];pt=poseprog['ticks'][pi]
    def wait(predicate,label):
        for _ in range(1200):
            if predicate():return
            tick()
        raise AssertionError(('body program stalled',label,pose,pi,phase))
    for c in commands:
        op=c['opcode'];arg=c.get('argument',0)
        if op==14:break
        if op==0:
            m=movement_program(src.rom,arg&63);motion=[[(-dx if arg&64 else dx),dy] for dx,dy in m['per_tick_delta']];mi=0
            events.append({'phase':phase,'tick':len(out[phase]),'kind':'motion','raw_argument':arg,**m})
            if not arg&128:wait(lambda:mi>=len(motion),'motion')
        elif op==2:timer=arg or 256
        elif op==3:
            if arg>=128:
                for _ in range(timer):tick()
                timer=0
            else:wait(lambda:pose==arg,'pose '+str(arg))
        elif op==4:bg=(arg&15) in [2,3]
        elif op==5:
            poseprog=src.pose_program(arg);pi=0;pt=poseprog['ticks'][0];pose=poseprog['poses'][0];paused=False
        elif op==6:flip=not flip
        elif op==8:paused=True
        elif op==9:paused=False
        elif op==12:
            out[phase].append(frame());phase='after_contact'
        elif op==16:pose=arg
        elif op==29:wait(lambda:poseprog is None,'pose program end')
        elif op in [7,10,11,13,27,28]:pass
        else:
            warnings.append(f'unsupported opcode {op:02X}');break
    if phase!='after_contact':warnings.append('no contact opcode reached')
    out['after_contact'].append(frame())
    out['events']=events;out['native_fps']=FPS;out['timing_note']='Exact authored pose timers and movement deltas; original interpreter dispatch/upload latency and damage-dependent pause excluded.'
    if warnings:out['unresolved']=warnings
    return out

def body_sheet(src,meta,c,side,palette_id=None,key_override=None):
    idx=c-1;b5=src.b[5];bank=src.b[15]['L0FE436']['db'][idx];typ=src.b[15]['L0FE44C']['db'][idx];b=src.b[bank]
    chr_id=b5['L058E98' if side=='ally' else 'L058EAE']['db'][idx]
    palid=b5['L058EC4' if side=='ally' else 'L058EDA']['db'][idx]&127
    if palette_id is not None:palid=palette_id
    palref=b5['L05BCF1']['dw'][palid];pal=b5[palref]['db'][:4];tiles=src.tiles[chr_id]
    table=src.ptr(bank,0xbfd0+2*typ);refs=b.get(table,{}).get('dw',[])
    # Pure background casters use a deliberately unused dummy OAM pointer.
    frames=[oam_entries(b[r]['db'],tiles,pal) for r in refs]
    oam_count=len(frames)
    bgbase=src.ptr(bank,0xbffa);bgmaps=src.ptr(bank,0xbffc+(0 if side=='ally' else 2))
    mapref=b[bgmaps]['dw'][typ];bgids=b[mapref]['db'];bgrefs=[]
    for bgid in bgids:
        ref=b[bgbase]['dw'][bgid];bgrefs.append(ref);frames.append(bg_entries(b[ref]['db'],tiles,pal,side=='enemy'))
    sheet,size,anchor,bounds=make_sheet(frames)
    key=key_override or f'class_{c}_{side}';path=OUT/'battle'/f'{key}.png'
    save(sheet,path,meta,kind='full_class_battle',class_id=c,side=side,frame_size=size,frame_count=len(frames),source_oam_table=table,source_oam=refs,source_background_map=mapref,source_background_uploads=bgrefs,chr_bank=chr_id,palette_indices=pal,palette_source=palref,pixel_bounds=bounds)
    programref=b5['L058EF0' if side=='ally' else 'L058F1C']['dw'][idx];programid=b5[programref]['db'][0]
    if side=='ally' and c in [15,16]:programid=b5[programref]['db'][0]
    if side=='ally' and c in [17,19]:programid=b5[programref]['db'][2]
    program=b5['L05B025']['dw'][programid];cmds=src.commands(program)
    idle_ref=b5['L058FB1' if side=='ally' else 'L058FDD']['dw'][idx];idle=b5[idle_ref]['db'][0]
    idle_frame=oam_count+idle
    entry={'path':'res://'+str(path.relative_to(ROOT)),'frame_size':size,'frames':len(frames),'anchor':anchor,'default_facing':'left','class_id':c,'side':side,'name':ENEMY.get(c,NAMES[idx]) if side=='enemy' else NAMES[idx],
      'source_oam_frame_count':oam_count,'background_frame_offset':oam_count,'background_pose_count':len(bgids),'idle_source_pose':idle,
      'oam_flip_origin_offset':[16,0],
      'sequences':{'idle':[idle_frame],'walk':[idle_frame],'attack':[idle_frame],'hit':[idle_frame],'death':[idle_frame]},'frame_seconds':1/FPS,
      'source_program':{'id':programid,'address':program,'commands':cmds},'feedback':{'death_palette_steps':4,'death_step_ticks':8},
      'source_palette_id':palid,'actor_origin':[184 if side=='ally' and c in [4,7] else 56 if side=='enemy' and c in [4,5,7] else 176 if side=='ally' else 64,128],
      'source_note':'Class/side lookup L0FE436/L0FE44C; original CHR and palette; BG left-normalized and OAM direct. Full frame extents retained.'}
    meta['battle'][key]=entry
    return entry

def tactical(src,meta,c,side,metas,acted=False):
    cycle=[24,25,21,25,24,25];pal=([15,16,0,26] if acted else [15,32,34,26] if side=='ally' else [15,54,37,26])
    metatile=112+c*2+(side=='enemy') if acted else c*2+(side=='enemy')
    ids=metas[metatile*4:metatile*4+4]
    sheet=Image.new('RGBA',(144,24))
    for i,bank in enumerate(cycle):
        for j,tid in enumerate(ids):
            raw=src.tiles[bank][tid];im=color(raw,pal,False)
            for y in range(8):
                for x in range(8):
                    if raw.getpixel((x,y))==3:im.putpixel((x,y),(0,0,0,0))
            sheet.alpha_composite(im,(i*24+4+j%2*8,4+j//2*8))
    key=f'class_{c}_{side}'+('_acted' if acted else '');path=OUT/'map_units'/f'{key}.png'
    save(sheet,path,meta,kind='full_class_map_acted' if acted else 'full_class_map',class_id=c,side=side,source_metatile=metatile,source_tile_indices=ids,source_chr_cycle=cycle,palette_indices=pal)
    meta['map_units'][key]={'path':'res://'+str(path.relative_to(ROOT)),'frame_size':[24,24],'frames':6,'anchor':[12,20],'tile_origin':[4,4],'directions':{'down':[0,1],'up':[2,3],'side':[4,5]},'class_id':c,'acted':acted,'source_palette':'L06852C palette1' if acted else 'L06852C palette0/3','source_note':'L0FD771/L0FD777: class*2+name_sign+(112 if acted); direct metatiles and original palette, without RGB tinting.'}

def personal(src,meta):
    b=src.b[10];meta['village_sprites']={};meta['portraits_by_index']={}
    for i in range(66):
        # Personal actor OAM palette bits select the source village sprite
        # palettes. Preserve all frames within a symmetric canvas.
        frames=[]
        for table in VILLAGE_TABLES:
            raw=b[b[table]['dw'][i]]['db'];entries=[]
            for j in reversed(range(raw[0])):
                y,t,a,x=raw[1+4*j:5+4*j];im=color(src.tiles[30][t],VILLAGE_PALETTE[a&3])
                if a&64:im=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if a&128:im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                entries.append((signed(x)-8,signed(y),im))
            frames.append(entries)
        sheet,size,anchor,bounds=make_sheet(frames,ground=8,minimum=(24,24))
        path=OUT/'map_units'/f'personal_{i+1:02}.png'
        save(sheet,path,meta,kind='full_personal_village',source_sprite_id=i+1,frame_size=size,frame_count=6,chr_bank=30,source_oam=[b[t]['dw'][i] for t in VILLAGE_TABLES],palette_indices=VILLAGE_PALETTE,pixel_bounds=bounds)
        meta['village_sprites'][str(i+1)]={'path':'res://'+str(path.relative_to(ROOT)),'frame_size':size,'frames':6,'anchor':anchor,'tile_origin':[anchor[0]-8,anchor[1]-16],'directions':{'down':[0,1],'up':[2,3],'side':[4,5]},'default_facing':'right','sprite_id':i+1,'chr_bank':30}
    for i in range(60):
        path=OUT/'portraits'/f'portrait_{i:02}.png'
        if path.exists():meta['portraits_by_index'][str(i)]={'path':'res://'+str(path.relative_to(ROOT)),'size':[48,48],'source_portrait_index':i}
    charportraits=src.b[9]['L09BDBF']['db'][:44]
    meta['character_portraits']={str(i):int(p) for i,p in enumerate(charportraits) if p}
    meta['character_portraits'].update({str(128+i):int(p) for i,p in enumerate(src.b[9]['L09BDEB']['db'][:45]) if p})

def main(root):
    src=Source(root);meta=json.loads(DATA.read_text());meta['assets']=[a for a in meta['assets'] if a.get('kind') not in ['full_class_battle','full_class_map','full_class_map_acted','full_personal_village','full_effect_oam']]
    meta.setdefault('full_class_animation',{})
    metas=[]
    for line in (root/'src/bank006.asm').read_text().split('L_METATILES_PALETTE_ID:')[0].splitlines():
        if line.strip().startswith('.db'):metas.extend(int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',line.split(';')[0]))
    failures=[]
    for c in range(1,23):
        for side in ['ally','enemy']:
            entry=body_sheet(src,meta,c,side);tactical(src,meta,c,side,metas);tactical(src,meta,c,side,metas,True)
            commands=entry['source_program']['commands'];ops={a['opcode'] for a in commands}
            if not ops.intersection({17,21,23,24,25}):
                try:
                    timeline=standard_timeline(src,commands,entry['source_oam_frame_count'],entry['idle_source_pose'])
                    if timeline.get('unresolved'):raise AssertionError(timeline['unresolved'])
                    for part in ['before_contact','after_contact']:
                        assert all(0<=f['frame']<entry['frames'] for f in timeline[part]),(c,side,'frame outside sheet')
                    entry['attack_schedule']={'kind':'melee','native_fps':FPS,'native_timeline':timeline,'attack_program_source':entry['source_program']['address'],'minimum_contact_pause_ticks':0,'poses':[f['frame'] for f in timeline['before_contact']],'ticks':[1]*len(timeline['before_contact'])}
                except AssertionError as e:failures.append({'class_id':c,'side':side,'error':str(e)})
            else:entry['attack_schedule']={'kind':'ranged' if c in [12,13,20] else 'magic','native_fps':FPS,'source_program':entry['source_program'],'body_only':True}
    personal(src,meta)
    # Enemy level>=10 and source named bosses select dedicated palettes in
    # L058E56, before the same body geometry is uploaded. Keep exact variants.
    palette_variants=[]
    for c in range(1,23):palette_variants.append((c,'enemy',c+92,f'class_{c}_enemy_elite'))
    named=src.b[5]['L058E85']['db'][:-1];campaign_path=ROOT/'data/campaign.json'
    if campaign_path.exists():
        campaign=json.loads(campaign_path.read_text());pairs=set()
        def visit(v):
            if isinstance(v,dict):
                if 'name_id' in v and 'class_id' in v:pairs.add((int(v['name_id']),int(v['class_id'])))
                for n in v.values():visit(n)
            elif isinstance(v,list):
                for n in v:visit(n)
        visit(campaign)
        for name,c in sorted(pairs):
            if name in named:palette_variants.append((c,'enemy',named.index(name)+4,f'class_{c}_enemy_name_{name}'))
    # Source character35 is a summoned Shadow, not Mycen(character3).
    for c in range(1,23):palette_variants.append((c,'ally',38,f'class_{c}_ally_name_35'))
    for c,side,palid,key in palette_variants:
        base=meta['battle'][f'class_{c}_{side}'];variant=body_sheet(src,meta,c,side,palid,key)
        variant['attack_schedule']=copy.deepcopy(base['attack_schedule']);variant['sequences']=copy.deepcopy(base['sequences'])
        base.setdefault('palette_variants',{})['elite' if key.endswith('_elite') else key.split('_name_')[-1]]=key
    # Original portrait selection uses promoted character IDs, while the class
    # stat storage maps the heroes back onto class21 and class11.
    for name,c,poseid,programid in [('promoted_alm',21,31,63),('promoted_celica',11,0,10)]:
        entry=copy.deepcopy(meta['battle'][f'class_{c}_ally']);entry['promoted']=True
        if name=='promoted_alm':
            entry['idle_source_pose']=poseid;entry['sequences']['idle']=[entry['background_frame_offset']+poseid]
            program=src.b[5]['L05B025']['dw'][programid];cmds=src.commands(program)
            entry['source_program']={'id':programid,'address':program,'commands':cmds}
            try:entry['attack_schedule']={'kind':'melee','native_fps':FPS,'native_timeline':standard_timeline(src,cmds,entry['source_oam_frame_count'],poseid),'attack_program_source':program}
            except AssertionError as e:failures.append({'variant':name,'error':str(e)})
        meta['battle'][name+'_ally']=entry
    DATA.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    result={'source_revision':meta['source_revision'],'class_count':22,'class_side_count':44,'personal_sprite_count':66,'failure_count':len(failures),'failures':failures,'assets':[a for a in meta['assets'] if a.get('kind','').startswith('full_')]}
    (ROOT/'data/full_animation_sources.json').write_text(json.dumps({'source_revision':meta['source_revision'],'programs':{r:src.commands(r) for r in src.b[5]['L05B025']['dw']},'pose_programs':[src.pose_program(i) for i in range(48)],'class_programs':{k:v['source_program'] for k,v in meta['battle'].items() if k.startswith('class_')},'effect_programs':{r:src.b[5][r]['db'] for r in src.b[5]['L05BAB8']['dw']},'limitations':['Source bytecode dispatch and PPU upload overhead omitted from authored body timelines.','Spell effect interpreter and class/weapon-specific selection require the native battle controller.']},ensure_ascii=False,indent=2)+'\n')
    (ROOT/'reports/full-graphics-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='assets'},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=Path('/private/tmp/fe2-analysis-20261012'));main(ap.parse_args().source)

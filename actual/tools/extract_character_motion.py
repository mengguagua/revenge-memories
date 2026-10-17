#!/usr/bin/env python3
"""Fresh offline FE2 ROM/CHR/ASM decoding; no previous art or authored timelines."""
from pathlib import Path
import sys,json,hashlib,copy,math
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];SOURCE=ROOT/'source/characters/original-motion';OUT=ROOT/'assets/party-0.6.1'
sys.path.insert(0,str(ROOT.parent/'tools'))
from extract_full_graphics import Source,oam_entries,bg_entries,make_sheet
from extract_full_effects import run_effect,effect_image
REV='956365ef33c63751e7afd03f05e600d7728549da'
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def digest(im):return hashlib.sha256(im.tobytes()).hexdigest()
class OriginalBody:
    def __init__(self,src,cid):
        self.src=src;self.cid=cid;idx=cid-1;b5=src.b[5];self.bank=src.b[15]['L0FE436']['db'][idx];typ=src.b[15]['L0FE44C']['db'][idx];b=src.b[self.bank]
        chrid=b5['L058E98']['db'][idx];palid=b5['L058EC4']['db'][idx]&127;pal=b5[b5['L05BCF1']['dw'][palid]]['db'][:4]
        self.tiles=src.tiles[chrid];self.pal=pal;table=src.ptr(self.bank,0xbfd0+2*typ);refs=b.get(table,{}).get('dw',[])
        oam=[oam_entries(b[r]['db'],self.tiles,pal)for r in refs];self.cutoff=len(oam);self.bgbase=src.ptr(self.bank,0xbffa)
        bgmap=src.ptr(self.bank,0xbffc);self.bgids=b[b[bgmap]['dw'][typ]]['db'];self.bgrefs=[b[self.bgbase]['dw'][p]for p in self.bgids]
        all_frames=oam+[bg_entries(b[p]['db'],self.tiles,pal)for p in self.bgrefs]
        raw,size,anchor,bounds=make_sheet(all_frames);self.size=size;self.anchor=anchor;w,h=size
        self.frames=[raw.crop((i*w,0,(i+1)*w,h))for i in range(len(all_frames))];self.native_count=len(self.frames);self.seen={digest(im):i for i,im in enumerate(self.frames)if i>=self.cutoff}
        idle_ref=b5['L058FB1']['dw'][idx];self.idle=src.b[5][idle_ref]['db'][0];self.maps={};self.transitions={}
        self.meta={'frame_size':size,'anchor':anchor,'frames':len(self.frames),'source_oam_frame_count':self.cutoff,'background_frame_offset':self.cutoff,'idle_source_pose':self.idle,'sequences':{'idle':[self.cutoff+self.idle]},'class_id':cid,'side':'ally','source_chr':chrid,'source_palette':pal,'original_shape_only':True}
    def compile(self,trace,start_idle=None):
        current=self.cutoff+(self.idle if start_idle is None else start_idle);last_pose=-1;bg=False;mapping=[];ax,ay=self.anchor
        for row in trace:
            pose=row['source_pose']
            if not row['background']:current=pose;bg=False;last_pose=-1
            elif not bg or pose!=last_pose:
                base=current if bg else self.cutoff+(self.idle if start_idle is None else start_idle);identity=(base,pose)
                if identity not in self.transitions:
                    canvas=self.frames[base].copy();tiles=bg_entries(self.src.b[self.bank][self.bgrefs[pose]]['db'],self.tiles,self.pal)
                    for x,y,tile in tiles:canvas.paste(tile,(x+ax,y+ay-32))
                    key=digest(canvas)
                    if key not in self.seen:self.seen[key]=len(self.frames);self.frames.append(canvas)
                    self.transitions[identity]=self.seen[key]
                current=self.transitions[identity];bg=True;last_pose=pose
            mapping.append(current)
        return mapping
    def export(self):
        w,h=self.size;sheet=Image.new('RGBA',(w*16,h*math.ceil(len(self.frames)/16)))
        for i,im in enumerate(self.frames):sheet.paste(im,((i%16)*w,(i//16)*h))
        p=SOURCE/f'class-{self.cid}.png';save(sheet,p)
        self.meta.update(frames=len(self.frames),columns=16,path=str(p.relative_to(ROOT)),native_base_frames=self.native_count)
        return self.meta
def program_for(src,cid,item=0,promoted=False,critical=False):
    b=src.b[5];ref=b['L058EF0']['dw'][cid-1];table=b[ref]['db'];idle_ref=b['L058FB1']['dw'][cid-1];idles=b[idle_ref]['db'];index=0;effect=0
    if cid==21:
        if item in [1,20,21,22]:return 56,0,0
        if item==15:return 22,1,0
        if promoted:return 63,0,31
        return (18 if critical else 17),0,0
    if cid in [1,2,3,4,5,6,7,22]and item in [4,7]:index=1
    elif cid in [8,9,10,11,14]and item==15:index=1;effect=2
    elif cid in [12,13,20]and item==21:index=1;effect=3 if cid==12 else 4
    elif cid in [11,15,16,17,18,19]and item>=23:
        if item>=40:
            index=2 if cid==11 else 1 if item==42 else 0
            effect=b['L058F93']['db'][item-40]
        else:index=2 if cid in [11,17,19]else 0;effect=b['L058F72']['db'][item-23]
    return table[index],effect,idles[index]if index<len(idles)else idles[0]
def main():
    src=Source(ROOT.parent/'.reference/fe2-source-956365ef');bodies={c:OriginalBody(src,c)for c in range(1,23)};sprites={};variants={};melee={};maps={};records=[]
    def extract(key,cid,item=0,formation='near',heavy=False,promoted=False,critical=False):
        pid,eid,idle=program_for(src,cid,item,promoted,critical);trace=run_effect(src,cid,'ally',pid,eid,item,idle,formation,4 if heavy else None)
        assert trace['contact_count']==1,(key,trace['contact_count'])
        body=bodies[cid];mapping=body.compile(trace['frames'],idle)
        for i,row in enumerate(trace['frames']):
            row['frame']=mapping[i]
            for effect in row['effects']:
                im,size,anchor,ref=effect_image(src,effect);identity=hashlib.sha256(im.tobytes()+str(anchor).encode()).hexdigest()[:14]
                if identity not in sprites:
                    p=OUT/'effects'/f'{identity}.png';save(im,p);sprites[identity]={'path':'res://'+str(p.relative_to(ROOT)),'frame_size':size,'frames':1,'anchor':anchor,'source_oam':ref,'default_facing':'left','flip_origin_offset':[16,0]}
                retained={k:effect[k]for k in ['position','flip','priority']};retained['sprite']=identity;effect.clear();effect.update(retained)
        trace['source_program_address']=src.b[5]['L05B025']['dw'][pid];trace['source_revision']=REV;variants[key]=trace;maps[key]=mapping
        records.append({'key':key,'class':cid,'item':item,'program':pid,'address':trace['source_program_address'],'ticks':len(trace['frames']),'contact_tick':trace['contact_tick'],'source':'fresh offline original ROM execution'})
        return trace
    for cid in range(1,23):
        if cid in [12,13,15,16,17,18,19,20]:continue
        key=f'original_class_{cid}_normal';melee[str(cid)]={'normal':extract(key,cid)}
        if cid==21:melee[str(cid)]['critical']=extract('original_class_21_critical',21,critical=True)
    melee['23']={'normal':extract('original_class_21_promoted',21,promoted=True)}
    jobs=[]
    for cid in [12,13,20]:jobs.append((f'class_{cid}_ally_bow',cid,0));jobs.append((f'class_{cid}_ally_silver_bow',cid,21))
    for cid in [1,2,3,4,5,6,7,22]:jobs.append((f'class_{cid}_ally_javelin',cid,4))
    for cid in [8,9,10,11,14,21]:jobs.append((f'class_{cid}_ally_levin',cid,15))
    jobs.append(('class_21_ally_bow',21,1))
    for cid in [11,15,16,17,19]:
        for item in [23,24,25,26,27,28,29,31,32]:jobs.append((f'class_{cid}_ally_item_{item}',cid,item))
    for cid in [11,17,18,19]:
        for item in ([40]if cid==11 else [40,41,42,43,44]):jobs.append((f'class_{cid}_ally_item_{item}',cid,item))
    for base,cid,item in jobs:
        for formation in ['near','far_ally','far_enemy']:
            for heavy in [False,True]:
                key=base+(''if formation=='near'else '_'+formation)+('_vs_heavy'if heavy else '')
                extract(key,cid,item,formation,heavy)
        print('SOURCE',base,flush=True)
    original={str(c):body.export()for c,body in bodies.items()}
    rom_hash=hashlib.sha256(src.rom).hexdigest();data={'source_revision':REV,'rom_sha256':rom_hash,'native_fps':60.0988,'variants':variants,'sprites':sprites,'melee':melee,'original_bodies':original,'source_note':'Direct original NES CPU execution and original CHR/OAM/PPU writes. No previous art atlases or approximate authored timeline is an input. Damage-dependent pauses occur at the native contact boundary in the Godot controller.'}
    write(SOURCE/'full-original-motion.json',data);write(SOURCE/'original-motion-audit.json',{'source_revision':REV,'rom_sha256':rom_hash,'records':records,'original_bodies':original,'previous_art_used':False,'previous_authored_timeline_used':False})
    print('ORIGINAL_SOURCE_READY',len(variants),'programs',len(sprites),'effect sprites',flush=True)
if __name__=='__main__':main()

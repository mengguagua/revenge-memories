#!/usr/bin/env python3
"""Run original battle effect routines offline and record their OAM frames.

The resulting Godot JSON/PNG contains only authored frames and placements.
Runtime is native; the extraction-only routine runner and ROM are excluded.
"""
from pathlib import Path
import copy,json,sys,hashlib,argparse
from PIL import Image
from extract_graphics import ROOT,OUT,DATA,save,color
from extract_full_graphics import Source,make_sheet,FPS,signed
from fe2_source_cpu import CPU

def run_effect(src,class_id,side,program_id,effect_id,item_id=23,idle=0,formation='near',opponent_class=None):
    cpu=CPU(src.rom);m=cpu.mem;attacker=0 if side=='ally' else 1
    m[0x306]=class_id if attacker==0 else 21;m[0x307]=class_id if attacker==1 else 14
    if opponent_class is not None:m[0x306+(1-attacker)]=opponent_class
    m[0x3e8]=attacker;m[0x3eb+attacker]=program_id;m[0x3ee+attacker]=effect_id
    m[0x320+attacker]=item_id;m[0x3c1]=176;m[0x3c2]=64;m[0x3c4]=96;m[0x3c5]=96
    if class_id==21 and side=='enemy' and item_id in [19,38,39]:
        m[0x3a6]=1 if item_id==39 else 0;m[0x3a8]={19:1,38:0,39:2}[item_id];m[0x30b]=51 if item_id==39 else 182
    m[0x3d0]=m[0x3d1]=1;m[0x33c]=m[0x33d]=30;m[0x30c]=m[0x30d]=30;m[0x34c+attacker]=1
    m[0x3be+attacker]=idle
    m[0x31e]=1 if formation=='far_ally' else 0;m[0x31f]=1 if formation=='far_enemy' else 0
    # Original entry routine sets both actor origins from the initiator's
    # distance flag. Manhattan distances2..5 share this far arrangement.
    cpu.call(5,0x812e);origin=m[0x3c1+attacker];origins=[m[0x3c1],m[0x3c2]]
    idx=class_id-1;b5=src.b[5]
    actorchr=b5['L058E98' if side=='ally' else 'L058EAE']['db'][idx]
    m[0x04ce+attacker]=actorchr;m[0x04d1+attacker]=idx
    palref=b5['L05BCF1']['dw'][b5['L058EC4' if side=='ally' else 'L058EDA']['db'][idx]&127]
    actorpal=b5[palref]['db'][:4]
    m[0x03b5]=m[0x03b6]=1
    for i in range(6):m[0x452+i]=m[0x45e+i]=255
    for i in range(4):m[0x3f8+i]=m[0x3fc+i]=255
    palette=b5['L05BCCD']['db'][3:35];m[0x7d80:0x7da0]=bytes(palette)
    for who in [0,1]:
        cl=m[0x306+who]-1;pr=b5['L05BCF1']['dw'][b5['L058EC4' if who==0 else 'L058EDA']['db'][cl]&127]
        p=bytes(b5[pr]['db'][:4]);m[0x7d80+who*4:0x7d84+who*4]=p;m[0x7d90+who*4:0x7d94+who*4]=p
    contacts=[];tick=0
    def advance(c):c.mem[0x3ea]=(c.mem[0x3ea]+1)&255;c.mem[0x3e9]=0
    def contact(c):contacts.append(tick);advance(c)
    def hpinit(c):
        address=c.mem[0]+256*c.mem[1];argument=c.read(address+c.mem[0x382]+1)
        if 40<=item_id<=44 and argument==0 and not contacts:contacts.append(tick)
        advance(c)
    # Damage-dependent visual pause belongs to the native damage event. Only
    # bypass those three handlers; source caster/effect/timer logic runs intact.
    cpu.hooks[(5,0x9bba)]=contact;cpu.hooks[(5,0x983a)]=hpinit;cpu.hooks[(5,0x99b5)]=advance
    frames=[];states=set()
    for tick in range(1600):
        m[0x36]=(m[0x36]+1)&255;m[0x27]=m[0x28]=0
        for timer in [0x31,0x32,0x33,0x34,0x35]:
            if m[timer]:m[timer]-=1
        cpu.call(0,0x9f36);cpu.call(0,0xa9b0);cpu.call(0,0xadfa)
        cpu.call(5,0x954e)
        cpu.call(0,0xbd7a)
        requests=[]
        for group in range(12):
            bits=m[0x6d0+group]
            for bit in range(8):
                if bits&(1<<bit):requests.append(group*16+bit)
            m[0x6d0+group]=0
        effects=[];typ=1 if effect_id<17 else 2
        for j in range(6):
            if m[0x45e+j]<128:
                effects.append({'source_pose':m[0x45e+j],'position':[m[0x464+j],m[0x46a+j]],'flip':bool(m[0x470+j]),'priority':m[0x476+j],'chr_bank':cpu.chr,'table_type':typ,'palettes':list(m[0x7d90:0x7da0])})
        if m[0x3cf]:
            # Projectile actor2 retains the shooter's class and CHR mapping.
            bank=src.b[15]['L0FE436']['db'][idx];typ=src.b[15]['L0FE44C']['db'][idx];table=src.ptr(bank,0xbfd0+typ*2)
            ref=src.b[bank][table]['dw'][m[0x3c0]]
            effects.append({'source_oam':ref,'source_bank':bank,'position':[m[0x3c3],m[0x3c6]],'flip':bool(m[0x3c9]),'priority':m[0x3cc],'chr_bank':m[0x4d0],'palettes':actorpal*4})
        frame={'source_pose':m[0x3be+attacker],'background':bool(m[0x3d0+attacker]),'offset':[signed((m[0x3c1+attacker]-origin)&255),signed((m[0x3c4+attacker]-96)&255)],'flip':bool(m[0x3c7+attacker]),'effects':effects}
        if requests:frame['sound_requests']=requests
        if item_id==43:
            frame['target_palette']=list(m[0x7d80+(1-attacker)*4:0x7d84+(1-attacker)*4]);frame['screen_emphasis']=(m[0xd2]>>5)&7
        frames.append(frame)
        if m[0x3e5]>0:break
    else:raise RuntimeError(f'effect{effect_id}/class{class_id}/{side} did not finish EA={m[0x3ea]},ED={m[0x3ed]},F0={m[0x3f0]}')
    return {'frames':frames,'contact_tick':contacts[0] if contacts else None,'contact_count':len(contacts),'native_fps':FPS,'source_program_id':program_id,'source_effect_id':effect_id,'source_item_id':item_id,'source_class_id':class_id,'source_side':side,'actor_origin':[origin,128],'formation':formation,'source_actor_origins':{'ally':[origins[0],128],'enemy':[origins[1],128]},'opponent_class_id':m[0x306+(1-attacker)]}

def effect_image(src,state):
    bank=state.get('source_bank',4)
    if 'source_oam' in state:ref=state['source_oam']
    else:table=src.b[4]['L04BFD0']['dw'][state['table_type']];ref=src.b[4][table]['dw'][state['source_pose']]
    raw=src.b[bank][ref]['db'];entries=[];tiles=src.tiles[state['chr_bank']]
    for i in reversed(range(raw[0])):
        y,t,a,x=raw[1+i*4:5+i*4];pal=state['palettes'][(a&3)*4:(a&3)*4+4];tile=color(tiles[t],pal)
        if a&64:tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if a&128:tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        entries.append((signed(x),signed(y),tile))
    sheet,size,anchor,bounds=make_sheet([entries],ground=0,minimum=(8,8))
    return sheet,size,anchor,f'bank{bank:03}:{ref}'

def main(root):
    src=Source(root);meta=json.loads(DATA.read_text());meta['assets']=[a for a in meta['assets'] if a.get('kind')!='full_effect_oam']
    results={};failures=[];assets={};variants={}
    # Item23..34 effect lookup is L058F72. Dark enemy defaults are selected by
    # their weapon/spell item in exactly the same table, not by a generic orb.
    spellids=src.b[5]['L058F72']['db']
    jobs=[]
    for c,side,program in [(11,'ally',29),(15,'ally',27),(16,'ally',27),(17,'ally',48),(19,'ally',47),(15,'enemy',35),(16,'enemy',27),(19,'enemy',34)]:
        for item,effect in enumerate(spellids,23):
            # Death/Medusa belong to enemy casters. Forcing those spells into
            # a priestess/sage-only casting program stalls the original VM.
            if effect and (side=='enemy' or item<33):jobs.append((c,side,program,effect,item,f'class_{c}_{side}_item_{item}'))
    for c in [12,13,20]:
        for side in ['ally','enemy']:
            entry=meta['battle'][f'class_{c}_{side}'];jobs.append((c,side,entry['source_program']['id'],0,0,f'class_{c}_{side}_bow'))
    # Native throwing motion and projectile graphics are class-specific.
    for c in [1,2,3,4,5,6,7,22]:
        for side in ['ally','enemy']:
            # Enemy gargoyle/necrodragon are not lance-wielding variants.
            if side=='enemy' and c in [3,5]:continue
            jobs.append((c,side,25,0,4,f'class_{c}_{side}_javelin'))
    for c in [8,9,10,11,14]:
        for side in ['ally','enemy']:
            if side=='enemy' and c in [11,14]:continue
            jobs.append((c,side,26,2,15,f'class_{c}_{side}_levin'))
    jobs.extend([(21,'ally',56,0,1,'class_21_ally_bow'),(21,'ally',22,1,15,'class_21_ally_levin')])
    for c,normal,drain in [(17,52,49),(18,23,46),(19,51,50)]:
        for item,effect in enumerate(src.b[5]['L058F93']['db'],40):
            jobs.append((c,'ally',drain if item==42 else normal,effect,item,f'class_{c}_ally_item_{item}'))
    # Priestess/Celica can learn Recover40. L058AAD -> L058BC3 ->
    # L058B39 keeps class11's program29 and selects white effect5.
    jobs.append((11,'ally',29,src.b[5]['L058F93']['db'][0],40,'class_11_ally_item_40'))
    # Duma's documented beam path and native eye/magic attack, kept distinct
    # from human mage casting. Other boss attacks remain source programs.
    jobs.extend([(21,'enemy',41,33,0,'class_21_enemy_beam'),(21,'enemy',37,13,0,'class_21_enemy_eye')])
    jobs.extend([(21,'enemy',37,13,19,'class_21_enemy_item_19'),(21,'enemy',68,29,38,'class_21_enemy_item_38'),(21,'enemy',41,33,39,'class_21_enemy_item_39')])
    for c,side,program,effect,item,basekey,formation,opponent in [(*job,f,o) for job in jobs for f in ['near','far_ally','far_enemy'] for o in [None,4]]:
            key=basekey+('' if formation=='near' else '_'+formation)+('_vs_heavy' if opponent==4 else '')
            try:
                entry=meta['battle'][f'class_{c}_{side}']
                result=run_effect(src,c,side,program,effect,item,entry['idle_source_pose'],formation,opponent)
                for frame in result['frames']:
                    frame['frame']=frame['source_pose']+(entry['background_frame_offset'] if frame['background'] else 0)
                    assert frame['frame']<entry['frames'],(key,frame['frame'],entry['frames'])
                    for state in frame['effects']:
                        identity=json.dumps([state.get('table_type'),state.get('source_pose'),state.get('source_oam'),state['chr_bank'],state['palettes']],separators=(',',':'));assetkey=hashlib.sha1(identity.encode()).hexdigest()[:14]
                        if assetkey not in assets:
                            image,size,anchor,ref=effect_image(src,state);path=OUT/'effects'/f'{assetkey}.png'
                            save(image,path,meta,kind='full_effect_oam',source_oam=ref,chr_bank=state['chr_bank'],palette_indices=state['palettes'],frame_size=size,frame_count=1)
                            assets[assetkey]={'path':'res://'+str(path.relative_to(ROOT)),'frame_size':size,'frames':1,'anchor':anchor,'source_oam':ref,'default_facing':'left','flip_origin_offset':[16,0]}
                        state['sprite']=assetkey
                        for k in ['palettes','chr_bank','table_type','source_pose','source_oam','source_bank']:state.pop(k,None)
                variants[key]=result
                if formation=='near' and opponent is None:
                    if c==15:results[f'item_{item}_{side}']=key
                    if item>=23:entry.setdefault('spell_variants',{})[str(item)]=key
                    elif c in [12,13,20]:entry['attack_schedule']={'kind':'ranged','effect_variant':key,'native_fps':FPS}
                    elif item in [1,4,15]:
                        entry.setdefault('weapon_variants',{})[str(item)]=key
                        if item==4:entry['weapon_variants']['7']=key
                        if item==1:
                            for bow in [20,21,22]:entry['weapon_variants'][str(bow)]=key
                    elif c==21 and side=='enemy' and item==19:entry.setdefault('weapon_variants',{})['19']=key
                    elif c==21 and key.endswith('beam'):entry['attack_schedule']={'kind':'magic','effect_variant':key,'native_fps':FPS}
            except Exception as exc:failures.append({'key':key,'item':item,'effect':effect,'side':side,'error':str(exc)})
    for c,side in [(15,'ally'),(16,'ally'),(17,'ally'),(19,'ally'),(15,'enemy'),(16,'enemy'),(19,'enemy')]:
        entry=meta['battle'][f'class_{c}_{side}'];entry['attack_schedule']={'kind':'magic','effect_variant':entry.get('spell_variants',{}).get('23',''),'native_fps':FPS}
    for key,entry in meta['battle'].items():
        if key.startswith('class_'):
            entry['oam_flip_origin_offset']=[16,0]
            base=meta['battle'][f'class_{entry["class_id"]}_{entry["side"]}']
            if entry is not base:
                for field in ['attack_schedule','spell_variants','weapon_variants']:
                    if field in base:entry[field]=copy.deepcopy(base[field])
        elif key.startswith('promoted_'):
            base=meta['battle'][f'class_{entry["class_id"]}_{entry["side"]}']
            for field in ['spell_variants','weapon_variants','oam_flip_origin_offset']:
                if field in base:entry[field]=copy.deepcopy(base[field])
    # Palette slots not used by an OAM frame must not multiply identical PNGs.
    # Deduplication is byte-for-byte; no quantization, scaling or image editing.
    canonical={};remap={};unique={}
    for key,sprite in assets.items():
        digest=hashlib.sha256((ROOT/sprite['path'].removeprefix('res://')).read_bytes()).hexdigest()
        identity=(digest,tuple(sprite['anchor']))
        if identity not in canonical:canonical[identity]=key;unique[key]=sprite
        remap[key]=canonical[identity]
    for variant in variants.values():
        for frame in variant['frames']:
            for effect in frame['effects']:effect['sprite']=remap[effect['sprite']]
    keep={v['path'] for v in unique.values()}
    meta['assets']=[a for a in meta['assets'] if a.get('kind')!='full_effect_oam' or a['path'] in keep]
    for p in (OUT/'effects').glob('*.png'):
        if 'res://'+str(p.relative_to(ROOT)) not in keep:p.unlink()
    assets=unique
    data={'source_revision':meta['source_revision'],'native_fps':FPS,'spells':results,'variants':variants,'sprites':assets,'failures':failures,'source_note':'Original bank005 caster/effect bytecode, bank000 pose timers/motion, bank001 effect trajectory, bank004 OAM; frame-by-frame offline original-routine execution. Damage pause omitted at event boundary. No CPU or ROM at runtime.'}
    (ROOT/'data/full_animation_effects.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    DATA.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    # Compile complete priestess recovery bodies after source upload frames;
    # the dedicated helper keeps partial BG writes from dropping body tiles.
    from patch_priestess_recovery import main as recover_priestess
    recover_priestess(root)
    print(json.dumps({'spells':len(results),'variants':len(variants),'sprites':len(assets),'failures':failures},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=Path('/private/tmp/fe2-analysis-20261012'));main(ap.parse_args().source)

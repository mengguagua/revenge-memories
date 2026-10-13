#!/usr/bin/env python3
"""Selectively recover FE2 archer background poses, tactical metatiles and arrow OAM.

Only adds/replaces archer assets and archer entries in graphics.json. Other
extracted graphics, village repairs and localization remain untouched.
"""
from pathlib import Path
import argparse, json, copy
from PIL import Image
from extract_graphics import ROOT, OUT, DATA, blocks, decode, color, save
FPS = 60.0988

def background_pose(raw, tiles, pal, mirrored=False):
    # L0FE4D6: count bytes then commands offset.lo/hi, length+orientation, tiles.
    # Each offset is relative to the actor's tile-aligned nametable anchor.
    # Decode at (22,12), the right actor's original (176,96) anchor; choose an
    # interior tile location so signed offsets do not wrap into another row.
    assert raw[0] == len(raw)-1
    base = 12*32+22
    entries=[]; p=1
    while p < len(raw):
        delta=raw[p]+256*raw[p+1]; delta=delta-65536 if delta>=32768 else delta
        cmd=raw[p+2]; p+=3
        count=cmd&63; step=32 if cmd&128 else 1
        assert not cmd&64, 'Unexpected repeat upload in archer pose'
        for i in range(count):
            absolute=base+delta+i*step
            x=(absolute%32-22)*8; y=(absolute//32-12)*8
            entries.append((x,y,raw[p])); p+=1
    assert p==len(raw)
    im=Image.new('RGBA',(80,64))
    for x,y,tid in entries:
        tile=color(tiles[tid],pal,True)
        # Godot's common sheet origin is source actor origin + (40,24).
        if mirrored:
            x=-x-8; tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        im.alpha_composite(tile,(x+40,y+24))
    # Mask covers exactly the source upload footprint; no raster resampling.
    return im, entries

def movement_program(rom, program):
    prg=rom[16:16+16384]
    def rb(a):return prg[a-0x8000]
    def rw(a):return rb(a)+256*rb(a+1)
    p=rw(0xae84+2*program); vectors=[]
    for _ in range(256):
        v=rb(p);p+=1
        if v==255:break
        vectors.append(v)
    else:raise AssertionError('Unterminated motion program')
    steps=[]
    for v in vectors:
        p=rw(0xb125+2*v)
        for _ in range(512):
            dx=rb(p)
            if dx==128:break
            dy=rb(p+1);steps.append([dx-256 if dx>=128 else dx,dy-256 if dy>=128 else dy]);p+=2
        else:raise AssertionError('Unterminated motion vector')
    return {'program_id':program,'vector_ids':vectors,'per_tick_delta':steps,
            'total_delta':[sum(s[0] for s in steps),sum(s[1] for s in steps)],
            'source_tables':['L00AE84','L00B125'],'native_fps':FPS}

def main(src):
    meta=json.loads(DATA.read_text())
    meta['assets']=[a for a in meta['assets'] if a.get('kind') not in ['archer_background_pose_sheet','archer_arrow_oam'] and not (a.get('kind')=='tactical_map_unit' and a.get('class_id')==12)]
    b1=blocks(src/'src/bank001.asm'); b5=blocks(src/'src/bank005.asm')
    class_index=11
    chr_id=b5['L058E98']['db'][class_index]; assert chr_id==6
    raw=(src/f'src/bank{chr_id//2:03}.chr').read_bytes()
    tiles=decode(raw)[(chr_id%2)*256:(chr_id%2+1)*256]
    motion=movement_program((src/'fe2.nes').read_bytes(),24)
    assert len(motion['per_tick_delta'])==14 and motion['total_delta']==[-173,0]
    arrow_raw=b1['L0195C5']['db'];assert arrow_raw==[3,0,0x7a,3,0,0,0x7b,3,8,0,0x7c,3,16]
    projectile={'path':'',
                'size':[24,8], 'frame_size':[24,8], 'anchor':[0,0], 'default_facing':'left',
                'launch_offset':[0,-25], 'native_origin_offset':[0,7], 'flip_origin_offset':[-8,0],
                'mirror_rule':'L0FCB12-L0FCB2A: each OAM x becomes8-x and each tile is horizontally flipped; normalized24px atlas origin shifts-8 for enemy',
                'motion':motion, 'per_tick_delta':motion['per_tick_delta'], 'contact_flight_tick':8,
                'source':'L059673/L0596C5/L0596FD: pose0,motion24,y103; L059D6D contact ±16; L0195C5 arrow OAM',
                'contact_note':'At standard body origins x176/x64, contact threshold is crossed after eight motion ticks (projectile x69/x171). Damage resolves at this event; remaining vector deltas are source projectile travel, not extra damage.'}
    schedule={'kind':'ranged','poses':[0,1,2,0], 'ticks':[16,16,1,0],
              'durations':[16/FPS,16/FPS,1/FPS,0], 'native_fps':FPS,
              'release_sequence_index':3, 'release_tick':33, 'release_seconds':33/FPS,
              'contact_tick':41,'contact_seconds':41/FPS,'contact_pose':0,
              'contact_sequence_index':3,'hold_at_contact':True,
              'approach':None,'retreat':None,'minimum_contact_pause_ticks':0,
              'recovery_ticks':20, 'release_sfx':'hit', 'release_sound_request':'0x03',
              'release_sound_source':'L05B27A opcode1B09 -> L00BD80[9]=L00BE1B -> $06D0=8 (request0x03)',
              'projectile':projectile,
              'attack_program_source':'bank005:L05B27A (normal), L05B2AB (critical)',
              'pose_source':'bank005:L05B27A opcode10, timer opcode02/03',
              'engine_source':'L059D33 body pose; L059673 arrow spawn; L059D6D contact gate',
              'timing_note':'16+16+1 authored wait ticks; bytecode dispatch/upload latency is omitted. Body returns to pose0 at release. Critical uses the same bow drawing script; existing damage feedback expresses critical damage. Recovery waits20 ticks after damage. No walking approach.'}
    for side, mapping, pal_table in [('ally','L01A13C','L058EC4'),('enemy','L01A1BC','L058EDA')]:
        palette_id=b5[pal_table]['db'][class_index]&127
        palette_ptr=b5['L05BCF1']['dw'][palette_id];pal=b5[palette_ptr]['db'][:4]
        # Projectile actor2 overrides OAM attr palette bits with shooter side
        # in L0FE49B; L058D85 copies actor palette to BG and sprite slots.
        arrow=Image.new('RGBA',(24,8))
        for i in range(3):
            y,t,a,x=arrow_raw[1+4*i:5+4*i]
            arrow.alpha_composite(color(tiles[t],pal), (x,y))
        arrow_path=OUT/'battle'/f'archer_arrow_{side}.png'
        save(arrow,arrow_path,meta,kind='archer_arrow_oam',source_oam='bank001:L0195C5',
             source_oam_table='bank001:L0180D6',chr_bank=chr_id,palette_indices=pal,
             palette_source=f'bank005:{palette_ptr}; bank015:L0FE49B overrides projectile OAM palette bits with shooter side')
        actor_projectile=copy.deepcopy(projectile)
        actor_projectile['path']=f'res://assets/original/graphics/battle/archer_arrow_{side}.png'
        actor_projectile['palette_indices']=pal
        actor_schedule=copy.deepcopy(schedule);actor_schedule['projectile']=actor_projectile
        pose_ids=b1[mapping]['db'];refs=[b1['L01A1CF']['dw'][i] for i in pose_ids]
        sheet=Image.new('RGBA',(len(refs)*80,64));placements=[]
        for i,ref in enumerate(refs):
            # Enemy upload art is authored facing right. Normalize to left to
            # match the shared Godot renderer's existing enemy UV reflection.
            frame,footprint=background_pose(b1[ref]['db'],tiles,pal,side=='enemy')
            sheet.alpha_composite(frame,(i*80,0));placements.append(footprint)
            assert frame.getbbox() is not None
        path=OUT/'battle'/f'archer_{side}.png'
        save(sheet,path,meta,kind='archer_background_pose_sheet',frame_size=[80,64],
             frame_count=len(refs),source_pose_map=mapping,source_background_ids=pose_ids,
             source_background_uploads=refs,source_relative_tiles=placements,
             chr_bank=chr_id,palette_source=palette_ptr,palette_indices=pal,
             normalization='enemy original BG tile upload reflected to left-facing renderer convention' if side=='enemy' else 'none')
        meta['battle'][f'archer_{side}']={'path':f'res://assets/original/graphics/battle/archer_{side}.png',
                'frame_size':[80,64], 'frames':len(refs),'anchor':[40,56],
                'default_facing':'left','sequences':{'idle':[0],'walk':[0], 'attack':[0,1,2,0], 'hit':[0],'death':[0]},
                'frame_seconds':0.08,'attack_schedule':actor_schedule,'projectile':actor_projectile,
                'feedback':{'hit':'Source current body pose, palette flash and screen displacement',
                            'death':'Current pose fades then actor removed','death_palette_steps':4,'death_step_ticks':8},
                'animation_note':'Exact CHR6 and original background-upload pose blocks; archer body is not an OAM melee sprite. Body origin176/64,y96 and feet128. Native per-tick arrow travel restored separately.'}
    # Tactical standing actors: class12 metatiles, original CHR animation cycle.
    metas=[]
    import re
    for line in (src/'src/bank006.asm').read_text().split('L_METATILES_PALETTE_ID:')[0].splitlines():
        if line.strip().startswith('.db'):metas.extend(int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',line.split(';')[0]))
    ids=metas[12*8:12*8+4];cycle=[24,25,21,25,24,25]
    banks={c:decode((src/f'src/bank{c//2:03}.chr').read_bytes())[(c%2)*256:(c%2+1)*256] for c in set(cycle)}
    for side,pal in [('ally',[0xf,0x20,0x22,0x1a]),('enemy',[0xf,0x36,0x25,0x1a])]:
        sheet=Image.new('RGBA',(144,24))
        for i,c in enumerate(cycle):
            for j,tid in enumerate(ids):
                rawtile=banks[c][tid];tile=color(rawtile,pal,False)
                for y in range(8):
                    for x in range(8):
                        if rawtile.getpixel((x,y))==3:tile.putpixel((x,y),(0,0,0,0))
                sheet.alpha_composite(tile,(i*24+4+j%2*8,4+j//2*8))
        path=OUT/'map_units'/f'archer_{side}.png'
        save(sheet,path,meta,kind='tactical_map_unit',frame_size=[24,24],frame_count=6,
             class_id=12,source_metatile=24,source_tile_indices=ids,source_chr_cycle=cycle,
             palette_indices=pal,palette_source='bank006:L06852C')
        meta['map_units'][f'archer_{side}']={'path':f'res://assets/original/graphics/map_units/archer_{side}.png',
             'frame_size':[24,24], 'frames':6, 'anchor':[12,20],
             'directions':{'down':[0,1],'up':[2,3],'side':[4,5]},'class_id':12,
             'mapping_note':'Exact tactical class12 metatile and CHR animation cycle; battlefield icons do not turn.'}
    legacy_arrow=OUT/'battle/archer_arrow.png'
    if legacy_arrow.exists():legacy_arrow.unlink()
    DATA.write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
    provenance={'source_revision':meta['source_revision'],'class_id':12,
        'battle':{s:meta['battle'][f'archer_{s}'] for s in ['ally','enemy']},
        'source_tables':{'body_class':'bank015:L0FE436/L0FE44C: PRG1,type7','body_upload_mapping':'bank001:L01A0A6/L01A0B8, type7 -> L01A13C/L01A1BC',
                         'body_upload_decoder':'bank015:L0FE4D6-L0FE575, offsets relative to tile anchor','chr':'bank005:L058E98/L058EAE[index11] = CHR6',
                         'palettes':'bank005:L058EC4[11]=60,L058EDA[11]=82; L05BCF1 palette pointers'},
        'assets':[a for a in meta['assets'] if a.get('kind') in ['archer_background_pose_sheet','archer_arrow_oam'] or a.get('class_id')==12],
        'limitations':['Original attack bytecode dispatch/upload overhead is not reproduced frame-for-frame; authored waits and projectile deltas are exact.',
                       'Original PPU battle entry/exit scrolling is handled by the native renderer, not this asset extraction.'],
        'verification':{'all_source_upload_blocks_consumed':True,'arrow_vectors':14,'contact_motion_ticks':8,'normal_pose_wait_ticks':33,'resampling':False}}
    (ROOT/'data/archer_animation.json').write_text(json.dumps(provenance,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({'assets':[{k:a[k] for k in ['path','width','height','bytes']} for a in provenance['assets']], 'schedule':schedule},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=Path('/private/tmp/fe2-analysis-20261012'))
    main(ap.parse_args().source)

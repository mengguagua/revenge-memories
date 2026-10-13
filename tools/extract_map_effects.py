#!/usr/bin/env python3
"""Decode original map magic/summon/warp OAM with source pose timing."""
from pathlib import Path
import json
from PIL import Image
from extract_full_graphics import Source,ROOT,DATA,OUT,make_sheet,signed,save,color,FPS

def main():
    src=Source(Path('/private/tmp/fe2-analysis-20261012'));meta=json.loads(DATA.read_text())
    meta['assets']=[a for a in meta['assets'] if a.get('kind')!='full_effect_map']
    fixed=src.b[15];b6=src.b[6];b8=src.b[8];programs={}
    for effect in range(1,12):
        pose_ref=fixed['L0FD85C']['dw'][effect];time_ref=fixed['L0FD874']['dw'][effect]
        poses=[]
        for v in fixed[pose_ref]['db']:
            if v==254:break
            poses.append(v)
        ticks=fixed[time_ref]['db'][:len(poses)]
        chr_id=b6['L06907A']['db'][effect];palette_id=b6['L06B458']['db'][effect]-1
        palref=b6['L_PALETTES']['dw'][palette_id];palraw=b6[palref]['db'];ppu=[15]*32
        initial=b6['L06852C']['db'];ppu[:initial[2]]=initial[3:3+initial[2]]
        address=(palraw[0]*256+palraw[1])-0x3f00;ppu[address:address+palraw[2]]=palraw[3:3+palraw[2]]
        pals=[ppu[16+i*4:20+i*4] for i in range(4)]
        frames=[];source_frames=[]
        unique=list(dict.fromkeys(poses))
        for pose in unique:
            ref=b8['L0881C2']['dw'][pose];a=int(ref[3:],16);geom=src.rw(8,a);entries=[];i=0
            while True:
                attr=src.rb(8,geom+3*i)
                if attr&240==240:break
                y=signed(src.rb(8,geom+3*i+1));x=signed(src.rb(8,geom+3*i+2));tile_id=src.rb(8,a+2+i)
                tile=color(src.tiles[chr_id][tile_id],pals[attr&3])
                if attr&64:tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if attr&128:tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                entries.append((x,y,tile));i+=1
                assert i<64,(effect,pose,'unterminated OAM')
            # First OAM entry wins overlaps, matching NES priority.
            frames.append(list(reversed(entries)));source_frames.append({'pose':pose,'source':ref,'geometry':f'L08{geom:04X}','tiles':i})
        sheet,size,anchor,bounds=make_sheet(frames,ground=0,minimum=(32,32));path=OUT/'effects'/f'map_program_{effect:02}.png'
        save(sheet,path,meta,kind='full_effect_map',source_effect=effect,frame_size=size,source_frames=source_frames,source_palette=palref,palette_indices=pals,chr_bank=chr_id,pixel_bounds=bounds)
        sequence=[unique.index(p) for p in poses];timeline=[]
        for frame,duration in zip(sequence,ticks):timeline.extend([frame]*duration)
        programs[str(effect)]={'path':'res://'+str(path.relative_to(ROOT)),'frame_size':size,'anchor':anchor,'frames':len(frames),'tile_origin_offset':[15,15],
            'poses':sequence,'source_poses':poses,'ticks':ticks,'cycle_ticks':len(timeline),'cycle_timeline':timeline,
            'native_fps':FPS,'sound_request':b6['L06906E']['db'][effect],'end_sound_request':48,
            'duration_by_timer_phase':{'spawn_or_remove':[51+i for i in range(10)],'target_feedback':[11+i for i in range(10)]},
            'source':{'pose':pose_ref,'timers':time_ref,'oam':'bank008 L0881C2','palette':palref,'duration':'L068FF6/L06B569; timer35 decreases every10 frames in L0FC336'},
            'body_draw_rule':'The map unit is removed before service10; service11 draws the appearance effect, then service12 restores the map unit. Target feedback keeps the map unit below the effect.'}
    quake={};x_steps=[-1,0,1,0]
    for phase in range(4):
        offsets=[];x=0;y=0
        for tick in range(400):
            remaining=40-tick//10;index=(phase+tick)&3
            if remaining<29:
                if remaining<2:x=0;y=0
                else:
                    amplitude=1 if remaining>=24 or remaining<8 else 2 if remaining>=20 or remaining<12 else 3
                    x+=x_steps[index];y+=[0,amplitude,0,-amplitude][index]
            offsets.append([-y,-x])
        quake[str(phase)]=offsets
    manifest={'source_revision':meta['source_revision'],'programs':programs,'routing':{
        'witch_appear':1,'witch_disappear':2,'recover':10,'fortify':10,'quake_target':9,
        'summon_appear_by_template':[3,11,5,7,255,255,1,1,1,1,11,11],
        'summon_disappear_by_template':[4,11,6,8,255,255,1,1,1,1,11,11],
        'invoke_flash':{'ticks':48,'even_remaining_ticks_ppumask_or':128,'end_ppumask_clear':128,'source':'L039315-L039333','sound_request':None},
        'expel_flash':{'ticks':48,'even_remaining_ticks_ppumask_or':32,'end_ppumask_clear':32,'source':'L03956A-L039596','sound_request':None},
        'quake':{'music_request':165,'duration_by_timer_phase':[391+i for i in range(10)],'timeline_by_initial_frame_counter_mod4':quake,'source':'L06A156-L06A20B; L06AFA0','axis_rule':'SourceD0 is vertical scroll andD1 horizontal; CanvasItem offsets negate scroll, so source accumulators[D0,D1] become[-D1,-D0].','note':'400-tick table assumes initial timer32=9; another initial phase shortens the first35=40 segment. Original PPU horizontal wrap handling is not rendered; signed scroll offsets are preserved.'}},
        'limitations':['Map program0 uses a different original OAM table and is not included; campaign summon/warp/healing use programs1..11.','NES full-screen PPUMASK emphasis is represented as original register metadata, not converted into an invented RGB tint.','Native PPU upload/NMI dispatch overhead and source sub-frame scroll wrapping are excluded.']}
    (ROOT/'data/full_map_effects.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+'\n')
    DATA.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'program_count':len(programs),'image_count':11,'source_programs':list(programs),'max_png_bytes':max((ROOT/p['path'].removeprefix('res://')).stat().st_size for p in programs.values())}))
if __name__=='__main__':main()

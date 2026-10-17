#!/usr/bin/env python3
"""Offline source-program execution, including native dispatch/wait ticks."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from extract_full_graphics import Source
from extract_full_effects import run_effect
source=Source(ROOT/'.reference/fe2-source-956365ef')
programs={}
for name,pid in [('normal',17),('critical',18)]:
    program=run_effect(source,21,'ally',pid,0,item_id=0,idle=0,opponent_class=14)
    heavy=run_effect(source,21,'ally',pid,0,item_id=0,idle=0,opponent_class=4)
    assert program['contact_count']==1 and heavy['contact_count']==1
    def body(record):return [{**f,'frame':(60 if f['background'] else 0)+f['source_pose']}for f in record['frames']]
    assert body(program)==body(heavy),'Heavy opponent changes body program; select separately'
    program['frames']=body(program);program['heavy_body_trace_equal']=True
    assert not any(f['effects']for f in program['frames'])
    program['source_program_address']='L05B37E' if pid==17 else 'L05B3A9'
    programs[name]=program
output=ROOT/'actual/source/clarity-0.5.2/executed-melee.json'
output.write_text(json.dumps({'source_revision':'956365ef33c63751e7afd03f05e600d7728549da','source_weapon_index':0,'programs':programs,'contact_hook':'Only damage-dependent HP/contact handlers replaced; native dispatch, pose, movement, timers and flip logic executed unchanged. No ROM/CPU runtime shipped.'},indent=2)+'\n')
print({k:{'ticks':len(v['frames']),'contact_tick':v['contact_tick'],'program':v['source_program_address']}for k,v in programs.items()})

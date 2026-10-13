#!/usr/bin/env python3
"""Read-only comparison of the native pose/movement loop with recovered source data."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[2]
main=(root/'core/main.gd').read_text();allmeta=json.loads((root/'data/graphics.json').read_text())
start=main.index('func _animate_strike(');end=main.index('\nfunc _contact(',start);body=main[start:end]
# Confirm the inspected loop's actual counter/translation policies.
parent_contact_ticks_counted='elif i >= contact_index:' in body or 'if i >= contact_index:' in body
parent_retreat_y_mirrored='combat_offsets[attacker_id] -= Vector2(float(delta[0]) * sign_x, float(delta[1]))' in body

def simulate(s,include_contact,invert_y,side):
 sign=1 if side=='player' else -1;approach=s['approach']['per_tick_delta'];retreat=s['retreat']['per_tick_delta'];movement_tick=0;approach_tick=0;retreat_tick=0;resume=0;offset=[0,0];trace=[];contact_pos=None;retreat_start=None
 for i,(pose,ticks) in enumerate(zip(s['poses'],s['ticks'])):
  if i==s['contact_sequence_index']:contact_pos=offset.copy()
  for tick in range(ticks):
   if i<s['contact_sequence_index'] and movement_tick>=s['approach_start_tick'] and approach_tick<len(approach):
    dx,dy=approach[approach_tick];offset[0]+=dx*sign;offset[1]+=dy;approach_tick+=1
   elif i>s['contact_sequence_index']:
    if resume>=s['retreat_start_after_contact_resume_ticks'] and retreat_tick<len(retreat):
     if retreat_start is None:retreat_start=movement_tick
     dx,dy=retreat[retreat_tick];offset[0]-=dx*sign;offset[1]+=(-dy if invert_y else dy);retreat_tick+=1
    resume+=1
   elif include_contact and i==s['contact_sequence_index']:
    resume+=1
   trace.append([movement_tick,pose,*offset]);movement_tick+=1
 return {'pose_ticks':movement_tick,'contact_tick':s['contact_tick'],'contact_offset':contact_pos,'approach_steps_played':approach_tick,'approach_steps_total':len(approach),'retreat_steps_played':retreat_tick,'retreat_steps_total':len(retreat),'retreat_start_pose_tick':retreat_start,'offset_before_final_reset':offset,'completed_return':retreat_tick==len(retreat) and offset==[0,0],'vertical_offset_range':[min(t[3] for t in trace),max(t[3] for t in trace)]}

checks=[]
for name in ['fighter','soldier','villager','brigand']:
 s=allmeta['battle'][name+'_ally']['attack_schedule'];item={'class':name,'source_pose':s['pose_source'],'source_timer':s['timer_source'],'source_contact_pose':s['contact_pose'],'inspected_native':{},'corrected_policy':{}}
 for side in ['player','enemy']:
  item['inspected_native'][side]=simulate(s,parent_contact_ticks_counted,parent_retreat_y_mirrored,side)
  item['corrected_policy'][side]=simulate(s,True,False,side)
  assert item['corrected_policy'][side]['completed_return']
 checks.append(item)
report={'main_sha256':hashlib.sha256(main.encode()).hexdigest(),'scope':'Read-only simulation of the inspected main.gd loop; original author pose arrays and ROM-decoded dx/dy form the reference. Damage/HP pause excluded from pose clock. No Godot window launched.','native_counter_counts_contact_pose':parent_contact_ticks_counted,'native_retreat_negates_y':parent_retreat_y_mirrored,'checks':checks,'source_feedback':{'camera_shake_horizontal_pixels':[3,1,2,1,3,1,2,4,2,1,0],'camera_shake_ticks':11,'camera_shake_source':'bank005:L059BBA-L059C33 writes D1; bank015:L0FC36A writes D1 as first PPU2005 (horizontal scroll), D0 as second (vertical). Clears D0/D1 at completion.','post_contact_minimum_wait_ticks':16,'post_contact_wait_source':'L05B37E/L05B18A/L05B2DC/L05B307 command02 10 -> command03 FF','hp_damage_countdown':'L0599F1 decrements displayed HP every active frame; recovery branch L0599D0 gated by frameCounter&3.','hp_damage_source':'bank005:L0599D0-L059A5B','death_palette_steps':4,'death_palette_step_period_ticks':8,'death_source':'bank005:L059F35-L059F73'}}
(root/'tools/graphics/native_frame_schedule_checks.json').write_text(json.dumps(report,indent=2)+'\n')
for c in checks:print(c['class'],c['inspected_native']['player'])

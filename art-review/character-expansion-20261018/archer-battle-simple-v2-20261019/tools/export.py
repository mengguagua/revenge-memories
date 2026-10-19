from pathlib import Path
import sys,json
from types import SimpleNamespace
V=Path(__file__).resolve().parents[1];R=V.parent
sys.path.insert(0,str(R/'tools'))
from export_gallery import export,render_frame
from build_gallery import build

data=build();targets=[a for a in data['actions']if a['profile']in ['professions-class-12-ally-battle','professions-class-12-enemy-battle']]
report=[]
for action in targets:
    args=SimpleNamespace(close=False,scale=2,light=False,stills_only=False)
    result=export(data,action,args);report.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
    if action['key']in ['class_12_ally_bow','class_12_ally_silver_bow','class_12_enemy_bow','idle']or action['key']=='reaction-idle':
        args.close=True;args.scale=4
        result=export(data,action,args);report.append(result);print(json.dumps(result,ensure_ascii=False),flush=True)
# Key moments expose all six poses, flying arrows and both background edge cases.
for action in targets:
    if action['key']not in ['class_12_ally_bow','class_12_enemy_bow']:continue
    profile=next(p for p in data['profiles']if p['id']==action['profile'])
    projectile_tick=next(i for i,row in enumerate(action['frames'])if any(e['sprite']in profile.get('revisedEffects',{})for e in row.get('effects',[])))
    ticks=sorted({0,projectile_tick,min(projectile_tick+8,len(action['frames'])-1),action['contactTick']})
    for tick in ticks:
        for light in [False,True]:
            path=V/'reviews'/f'{profile["side"]}-tick-{tick:02d}-{"light"if light else"dark"}.png'
            render_frame(data,profile,action,tick,3,light,False).save(path,optimize=True)
    if profile['side']=='ally':
        render_frame(data,profile,action,47,3,False,False).save(V/'reviews/ally-user-frame-48.png',optimize=True)
        drawn_tick=next(i for i,row in enumerate(action['frames'])if row['frame']==4)
        render_frame(data,profile,action,drawn_tick,4,False,True).save(V/'reviews/ally-full-draw-close.png',optimize=True)
(V/'export-report.json').write_text(json.dumps({'exports':report,'all_attack_timelines_and_reactions':len(targets)},ensure_ascii=False,indent=2)+'\n')
build()

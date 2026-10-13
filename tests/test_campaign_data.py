#!/usr/bin/env python3
"""Validate extracted campaign data invariants and known original edge cases."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
catalog=json.loads((ROOT/'data/campaign.json').read_text())
checks=0

def check(condition, message):
    global checks
    assert condition,message
    checks+=1

def stage(mid):
    return json.loads((ROOT/'data/stages'/f'stage_{mid:03d}.json').read_text())

check(len(catalog['stages'])==80,'80 original tactical map indices')
check(len(catalog['world_nodes'])==80,'80 world nodes in independent namespace')
check(len(catalog['characters'])==34,'all 34 original character template slots')
check(len(catalog['enemy_groups'])==89,'all 89 original enemy group table entries')
check(len(catalog['dungeon_encounters'])==32,'32 original dungeon battle triggers')
check(catalog['world_nodes']['49']['kind']=='hub','world49 is Ram village, not tactical cave49')
check(stage(49)['map']['source']=='maps/cave-room.tmx','tactical49 is an independent cave map')
check(stage(4)['player_positions'][0]==[7,17],'source x,y pair fits16x22 outpost')
check(stage(1)['player_positions'][0]==[5,6],'first battle x,y fixed')
check(stage(2)['enemies'][0]['position']==[14,3],'second battle x,y fixed')
for mid in (1,2):
    old=json.loads((ROOT/'data'/('first_battle.json' if mid==1 else 'second_battle.json')).read_text())
    check(old['player_positions']==stage(mid)['player_positions'],'legacy new battle deployment fixed')
    check(old['enemy_positions']==stage(mid)['enemy_positions'],'legacy new battle enemies fixed')
check(stage(7)['enemy_group_ids']==[7,49],'chapter1 equal-priority armies reverse for original deployment')
check(len(stage(7)['enemies'])==17,'declared 7+10 armies honored')
check(len(stage(4)['enemies'])==7,'ignore unused trailing Southern Outpost records')
check(len(catalog['enemy_groups']['31']['enemies'])==10,'source count excludes extra11th BowKnight group entry')
check(not catalog['enemy_groups']['66']['valid'],'malformed source group must not silently become playable')
check(catalog['enemy_groups']['66']['declared_count']==62,'preserve malformed original count')
check((stage(35)['map']['width'],stage(35)['map']['height'])==(32,30),'ROM corrects broken Fear Mountain TMX header')
check(stage(35)['map']['tiles']==stage(39)['map']['tiles'],'shared exact source map35/39')
check(stage(62)['enemies'][0]['name_zh']=='多玛','original final boss identity')
check(stage(62)['enemies'][0]['max_hp']==182,'Duma exception bypasses ordinary52HP cap')
check(len(stage(62)['enemies'])==20,'complete original final army')
check(len(stage(62)['player_positions_by_party'])==2,'both final party deployment tables retained')
check(catalog['characters']['clive_b']['id']==10,'duplicate original character slot retains source id')
check(catalog['characters']['clive_b']['slot_id']==11,'duplicate slot is separately identifiable')
check(catalog['characters']['alm']['resistance']==4,'player resistance is personal table, not class21=20')
check(catalog['characters']['celica']['magic_flags']==1,'original initial learned magic mask')
check(all(x['magic_level']==0 for x in catalog['characters'].values()),'magic learning counter starts0 independently from initial level')
check(catalog['classes']['24']['runtime_table_defined'] is False,'unused symbolic class24 must not read neighboring table garbage')
for mid in range(1,81):
    s=stage(mid);w=s['map']['width'];h=s['map']['height']
    check(len(s['map']['tiles'])==w*h,f'map{mid} rectangle matches source data')
    check(all(0<=t<256 for t in s['map']['tiles']),f'map{mid} valid original tile IDs')
    positions=[u['position'] for u in s['enemies']]
    check(len({tuple(p) for p in positions})==len(positions),f'map{mid} enemy positions unique')
    check(all(0<=x<w and 0<=y<h for x,y in positions),f'map{mid} enemies inside map')
    check(all(0<=x<w and 0<=y<h for x,y in s['player_positions']),f'map{mid} player positions inside map')
    check(all(u['name_ja'] and u['name_zh'] and 0<u['max_hp']<=182 for u in s['enemies']),f'map{mid} enemy identity/stats complete')
for g in catalog['enemy_groups'].values():
    if g['valid']:
        check(len(g['enemies'])==g['declared_count'],f'group{g["id"]} source-count bounded')
check(all(g['id']==66 or g['valid'] for g in catalog['enemy_groups'].values()),'only documented malformed group rejected')
check(all(0<x['parameter']<=255 for x in catalog['character_death_events'] if x['action_code']==3),'branch event parameters preserved')
report={'tests':checks,'failures':0,'source_commit':catalog['source_commit'],'counts':catalog['counts'],
        'runtime_scope':'Data extraction only; does not assert native campaign event implementation.',
        'documented_source_anomalies':catalog['data_anomalies']}
(ROOT/'reports').mkdir(exist_ok=True)
(ROOT/'reports/campaign-data-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(f'PASS {checks} campaign extraction checks')

"""Merge the completed play ledger without rerunning the source comparison matrix."""
import ast, csv, hashlib, json
from pathlib import Path

OUT=Path(__file__).resolve().parent.parent
ROOT=OUT.parents[3]
data=json.loads((OUT/'_support/datasets.json').read_text())
ledger_path=ROOT/'actual/reports/full-playtest-20261023/coverage-summary.json'
ledger=json.loads(ledger_path.read_text())
by_code={r['code']:r for r in ledger['battles']}
names=json.loads((ROOT/'actual/data/campaign.json').read_text())['characters']
assert ledger['passed'] and len(by_code)==40
table=data['data']['40关难度']
table['headers'][26]='实玩新濒死人数'
extra=['实玩新濒死名单','实玩NPC损失','实玩口径/补充说明','实玩来源']
table['headers']=table['headers'][:30]+extra
def name_of(value):
    if isinstance(value,dict):return value.get('name',value.get('id',''))
    return names.get(value,{}).get('name_zh',value)
play_results={}
for row in table['rows']:
    del row[30:]
    b=by_code[row[1]]
    assert b['result']=='victory' and b['battle_turn']>0
    dying=[name_of(x) for x in b.get('new_dying_members',[])]
    npcs=[name_of(x) for x in b.get('dead_npcs',[])]
    retries=int(b['attempts'])-1
    row[25]=b['battle_turn'];row[26]=len(dying);row[27]=retries
    row[28]='胜利；策略停滞后重跑' if row[1]=='F22' else '胜利；战败后重试' if retries else '胜利'
    note='真实历史检查点；当前地图、正常控制器输入；非新档一次连续五章通关。'
    if row[1]=='S41':note+='另从第8回合补做可选避难院/领奖分支，第11回合胜利；未计失败重试。'
    if row[1]=='F22':note+='首次自动策略到第91回合停滞；修正站位策略后第38回合成功，不是游戏战败。'
    if row[1]=='M42':note+='首次主角在第9回合濒死，正常战败；调整策略后第17回合成功。'
    if row[1]=='S11':note+='首次矿工被首领击杀而正常战败；调整护送策略后第11回合成功。'
    row.extend(['、'.join(dying) or '无','、'.join(npcs) or '无',note,b['report']+'; '+b['victory_save']])
    play_results[row[1]]={'turns':row[25],'dying':row[26],'retries':row[27],'result':row[28]}
    # Only refresh textual objectives after the parent agent's clarity fixes.
    current=json.loads((ROOT/f'actual/data/stages/{row[1]}.json').read_text())
    row[22]=current['goal']

# Make accessory effects explicitly comparable while preserving the verified numbers.
tree=ast.parse((OUT/'_support/analyze.py').read_text())
effects=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='effects' for t in n.targets))
for row in data['data']['装备对比']['rows']:
    if row[0] in effects:row[17]=effects[row[0]]
for row in data['data']['敌军明细']['rows']:
    if row[4]=='J54_boss' and '翼喙' not in row[19]:row[19]+='；翼喙重击（物，贴身反击）'
    if row[4]=='J54_boss':row[23]='0–1'
data['data']['外传80图']['headers'][9]='平均裸物防'
data['data']['外传80图']['headers'][10]='平均裸魔防'
data['stats']['play_summary']={'stages':40,'attempts':ledger['full_battle_attempts'],'extra_attempts':ledger['failed_or_stalled_attempts'],'new_dying_records':sum(len(b.get('new_dying_members',[]))for b in by_code.values()),'npc_losses':sum(len(b.get('dead_npcs',[]))for b in by_code.values()),'ledger':str(ledger_path.relative_to(ROOT)),'finalized':'2026-10-24'}
(OUT/'_support/play_results.json').write_text(json.dumps(play_results,ensure_ascii=False,indent=2))
(OUT/'_support/datasets.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
for name in ['40关难度','装备对比','敌军明细','外传80图']:
    t=data['data'][name]
    with (OUT/'csv'/f'{name}.csv').open('w',encoding='utf-8-sig',newline='')as f:
        w=csv.writer(f);w.writerow(t['headers']);w.writerows(t['rows'])
manifest=json.loads((OUT/'source-manifest.json').read_text())
paths=set(manifest['files'])
paths.update(['actual/core/chapter2_rules.gd','actual/core/chapter4_rules.gd','actual/core/chapter5_rules.gd','actual/core/legacy_game_state.gd','core/hub_controller.gd','core/unit_progression.gd',str(ledger_path.relative_to(ROOT))])
paths.update(str(p.relative_to(ROOT))for p in (ROOT/'data/stages').glob('*.json'))
manifest['finalized']='2026-10-24'
manifest['files']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()for p in sorted(paths)}
manifest['statistics']=data['stats']
(OUT/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps(data['stats']['play_summary'],ensure_ascii=False))

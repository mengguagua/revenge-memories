#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Summarize the new complete fifth-chapter ordinary-input run, without editing it."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022';P=O/'play/continuous-final'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
run=read(P/'continuous-final-play.json');state=read(P/'working-journey.json');ending_page_count=len(state['flags'].get('ending_pages',[]));codes=['M51','M52','F51','F52','S51','J53','J54'];battles=run['battles']
source=battles[0]['source'];source_hash=battles[0]['source_sha256'];source_path=R/source.removeprefix('res://');current={c:sha(R/f'data/stages/{c}.json')for c in codes}
checks={
 'seven_battles_in_order':[b['code']for b in battles]==codes,
 'seven_normal_victories':all(b['outcome']=='victory'and not b['failures']for b in battles),
 'all_final_map_hashes_match':all(b['entry_map_sha256']==b['map_sha256']==current[b['code']]for b in battles),
 'same_genuine_chapter4_source':all(b['source']==source and b['source_sha256']==source_hash for b in battles),
 'original_source_unchanged':sha(source_path)==source_hash,
 'complete_ending':state['flags'].get('ending_done',False)and state['flags'].get('campaign_complete',False)and state['flags'].get('chapter5_complete',False),
 'all_actual_ending_pages_confirmed':ending_page_count>0 and state['flags'].get('ending_index')==ending_page_count-1,
 'no_edits_or_forced_outcomes':not run['stat_edits']and not run['forced_victories']and not run['source_saves_modified'],
 'no_driver_failures':run['passed']and not run['failures']}
injuries=[]
for b in battles:
 ids=[u['id']for u in b['initial_players']if not u.get('neutral',False)and not u.get('temporary',False)]
 for member in ids:
  u=b['final_roster'][member]
  if u.get('dying',False):injuries.append({'stage':b['code'],'member':member,'name':u.get('name_zh',member),'hp':u['hp'],'recorded_as':'濒死，保留名册并接受照护；不是死亡'})
logs=[]
for kind,path in [('continuous','/private/tmp/ch5-spatial-continuous-final.log'),('rules','/private/tmp/ch5-spatial-rules-final.log')]:
 text=Path(path).read_text();errors=[s for s in text.splitlines()if any(key in s for key in ['SCRIPT ERROR','ERROR:','WARNING:'])];checks[kind+'_log_clean']=not errors;out=P/(kind+'-godot.log');shutil.copy2(path,out);logs.append({'kind':kind,'path':'res://'+str(out.relative_to(R)),'sha256':sha(out),'errors_or_warnings':errors})
description=f'从第四章真实完成记录重新开始第五章，连续完成七图及{ending_page_count}页完整结局，没有重试或跳关。M51/M52/F51/F52/S51/J53/J54分别在12/12/51/18/10/9/12回合胜利。F51中诺娅按普通战斗结果濒死并保留后续伤情；H55正常使用剩余救治份额救回希雅，终局10名正式出战成员全部存活。'
ending={'page_count':ending_page_count,'page_count_source':'len(flags.ending_pages), not the zero-based ending_index','done':state['flags']['ending_done'],'index':state['flags']['ending_index'],'campaign_complete':state['flags']['campaign_complete'],'chapter5_complete':state['flags']['chapter5_complete'],'mode':state['mode'],'checkpoint':'res://reports/chapter5-spatial-20261022/play/continuous-final/working-journey.json'}
report={'passed':all(checks.values()),'description':description,'battles':battles,'ending':ending,'source':source,'sourcehash':source_hash,'source_sha256':source_hash,'source_unchanged':checks['original_source_unchanged'],'source_report':'play/continuous-final/continuous-final-play.json','map_hashes':current,'checks':checks,'no_stat_edits':True,'stat_edits':False,'no_rng_edits':True,'forced_victories':False,'retry_count':0,'from_chapter_start':True,'injuries_retained':injuries,'ordinary_treatment': [x for x in run['operations']if x.get('kind')=='ordinary existing treatment resource'],'logs':logs,'scope':'Actual game input from the genuine fourth-chapter completion. Independent rules-probe fixtures are a separate report and are not playthrough evidence.'}
(O/'flow-continuation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
(P/'verification-summary.json').write_text(json.dumps({k:v for k,v in report.items()if k!='battles'},ensure_ascii=False,indent=2)+'\n')
(P/'reproduce.txt').write_text('From project root:\n/Applications/Godot.app/Contents/MacOS/Godot --headless --audio-driver Dummy --path actual --log-file /private/tmp/ch5-spatial-continuous-final.log --script res://tests/ch5_spatial_play.gd -- --label=continuous-final --continuous\n/Applications/Godot.app/Contents/MacOS/Godot --headless --audio-driver Dummy --path actual --log-file /private/tmp/ch5-spatial-rules-final.log --script res://tests/ch5_spatial_rules_probe.gd\npython3 actual/tools/summarize_ch5_spatial_flow.py\n')
print(json.dumps({'passed':report['passed'],'battles':len(battles),'ending':ending,'checks':checks},ensure_ascii=False))
raise SystemExit(0 if report['passed']else 1)

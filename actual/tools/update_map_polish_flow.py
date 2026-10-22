#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synchronize the affected map cards only; leave narrative and combat rules intact."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];path=R.parent/'docs2/完整游戏流程.md';s=path.read_text()
codes=['M12','M13','M14','M15','S11','S12','F21','F22','F23','F24','F25','F26','S21','S22']
s=s.replace('版本：流程同步稿1.7；更新日期：2026-10-21。','版本：流程同步稿1.8；更新日期：2026-10-22。')
note='2026-10-22地图修订：以M11为参照优化M12—M15、S11/S12，以及F21—F26、S21/S22共14图；M11保持原样。重点为路网、院落、林带、连续河桥、船形甲板、真实囚室和海岸。人物待机、移动与战斗动画沿用当前版本。完整场景、标注与操作格见[全部战斗地图](../art-review/battle-maps-20261021/index.html)，逐图改动、真实按键通关及后台截图见[本轮地图复查](../actual/reports/map-polish-20261022/index.html)。本轮不新增旧地图兼容副本。'
if note not in s:
 anchor='## 一、沿用设定与需要新做的部分'
 s=s.replace(anchor,note+'\n\n'+anchor,1)
for code in codes:
 d=json.loads((R/f'data/stages/{code}.json').read_text())
 start=s.index('#### '+code+' ');match=re.search(r'\n#### |\n### ',s[start+5:]);end=start+5+match.start() if match else len(s)
 card=s[start:end]
 card=re.sub(r'\*\*地图调整：\*\*[^\n]*\n\n','',card)
 line='**地图调整：**'+' '.join(d.get('tactical_notes',[]))+'\n\n'
 anchor=re.search(r'\*\*地点与地图：\*\*[^\n]*\n\n',card)
 assert anchor,code
 card=card[:anchor.end()]+line+card[anchor.end():]
 for o in d['objects']:
  front=o.get('approaches',[o['approach']]if 'approach'in o else [])
  action='指定门前格'+ '、'.join('('+','.join(map(str,p))+')'for p in front)+'确认' if front else '同格或四邻接确认' if o.get('adjacent',False)else'目标格确认'
  prefix='|'+o['id']+'／'
  rows=card.splitlines()
  for i,row in enumerate(rows):
   if row.startswith(prefix):
    cells=row.split('|');cells[-2]=action;rows[i]='|'.join(cells)
  card='\n'.join(rows)+'\n'
 if code=='F25':
  card=card.replace('幸存船员（sailors0）(10,28)','幸存船员（sailors0）(35,19)').replace('引航者（sailors1）(22,20)','引航者（sailors1）(37,19)')
 s=s[:start]+card.rstrip()+'\n\n'+s[end:].lstrip('\n')
path.write_text(s)
print('Updated current landscape notes and exact operation fronts for',len(codes),'cards.')

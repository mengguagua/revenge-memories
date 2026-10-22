#!/usr/bin/env python3
"""Synchronize only the twenty-five revised scene cards and current review links."""
from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];O=R/'reports/map-polish-late-20261022';P=R.parent/'docs2/完整游戏流程.md'
s=P.read_text();codes=json.loads((O/'codes.json').read_text())
s=s.replace('流程同步稿1.8','流程同步稿1.9').replace('前两章地图按2026-10-22修订更新。','五章地图按2026-10-22修订更新，M11保持原样。')
note='2026-10-22后续地图修订：第3—5章25图完成街区、运输大道、雪峡、盐原、沼泽干岛与神宫院落调整。保留现有剧情目标、战斗规则和人物动画；任务交互点、撤离路线与桥梁按当前运行地形复查。逐图前后对照与本轮实机记录见[后续25图复查](../actual/reports/map-polish-late-20261022/index.html)。'
if note not in s:s=s.replace('## 一、沿用设定与需要新做的部分',note+'\n\n## 一、沿用设定与需要新做的部分',1)
for c in codes:
 d=json.loads((R/f'data/stages/{c}.json').read_text());start=s.index('#### '+c+' ')
 m=re.search(r'\n#### |\n### |\n## ',s[start+5:]);end=start+5+m.start() if m else len(s)
 card=s[start:end];card=re.sub(r'\*\*地图调整：\*\*[^\n]*\n\n','',card)
 line='**地图调整：**'+' '.join(d['tactical_notes'])+'\n\n'
 anchor=re.search(r'\*\*(?:地点与地图|剧情与地图|剧情与缺席分支)：\*\*[^\n]*\n\n',card)
 if anchor:card=card[:anchor.end()]+line+card[anchor.end():]
 else:
  at=card.index('\n\n')+2;card=card[:at]+line+card[at:]
 s=s[:start]+card.rstrip()+'\n\n'+s[end:].lstrip('\n')
P.write_text(s);print('Updated',len(codes),'current map cards.')

#!/usr/bin/env python3
"""Compile quoted dialogue only; directions/conditions stay as source metadata.
Runtime explicitly chooses mutually exclusive groups. Never concatenate branches.
"""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'docs2/完整台词汇总.md'
s=p.read_text(); start=s.index('<a id="chapter-2">'); end=s.index('<a id="common">')
area='chapter2'; sub='开场'; branch=''; groups={}; current=None
for n,line in enumerate(s[:end].splitlines(),1):
 if n<=s[:start].count('\n'):continue
 if line.startswith('## '):
  area={'第二章':'chapter2','第三章':'chapter3','第四章':'chapter4','第五章':'chapter5','结局':'ending'}.get(line[3:6],area);sub='开场';branch='';current=None
 elif line.startswith('### '):
  area=line[4:].split(' · ')[0].split('〔')[0];sub='正文';branch='';current=None
 elif line.startswith('#### '):sub=line[5:];branch='';current=None
 elif line.startswith('**'):
  branch=line.split('**')[1];current=None
 elif line.startswith('> '):
  text=line[2:]
  if not text.strip() or '：' not in text:continue
  if current is None:
   current={'condition':branch,'source_line':n,'lines':[]}
   groups.setdefault(area,{}).setdefault(sub,[]).append(current)
  current['lines'].append(text)
 elif line.startswith('#'):current=None
out=ROOT/'actual/data/dialogue_ch2_5.json'
out.write_text(json.dumps({'source':'docs2/完整台词汇总.md','updated':'2026-11-07','sections':groups},ensure_ascii=False,indent=2)+'\n')
report=[]
for a,subs in groups.items():
 for h,gs in subs.items():
  for i,g in enumerate(gs):report.append(f'{a} | {h} | {i} {g["condition"]}\n  '+ ' ／ '.join(g['lines']))
(ROOT/'actual/reports/dialogue-ch2-5-20261107/source-index.txt').write_text('\n'.join(report)+'\n')
print(f'{sum(len(v) for v in groups.values())} sections, {sum(len(g) for v in groups.values() for g in v.values())} groups')

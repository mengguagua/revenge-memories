from pathlib import Path
import json,re,ast,struct,zipfile,hashlib,collections
ROOT=Path('/Users/gcc/gaocc/project/revenge-memories');OUT=ROOT/'actual/reports/dialogue-coverage-audit-20261026'
DOC=ROOT/'docs2/完整台词汇总.md';doc=DOC.read_text();section=doc.split('## 第四部分：',1)[1].split('## 来源、覆盖与交接',1)[0]
def norm(s):return re.sub(r'\s+','',s).replace('\\|','|')
def fragments(s):return [p for p in s.split('／') if p.strip()]
def check(s,target=doc):
 parts=fragments(s);return {'total':len(parts),'exact':sum(norm(p) in norm(target) for p in parts),'missing':[p for p in parts if norm(p) not in norm(target)]}
def strings(s):
 vals=[]
 for m in re.finditer(r'"(?:\\.|[^"\\])*"|\x27(?:\\.|[^\x27\\])*\x27',s):
  try:v=ast.literal_eval(m.group())
  except (ValueError,SyntaxError):continue
  vals.append((m,v))
 return vals
def func(src,name):
 m=re.search(r'^(?:static )?func '+re.escape(name)+r'\(',src,re.M);assert m,name
 end=re.search(r'^(?:static )?func ',src[m.end():],re.M)
 return src[m.start():m.end()+end.start() if end else len(src)]
def map_strings(src,name,var):
 body=func(src,name);pos=body.index('var '+var+'=') if 'var '+var+'=' in body else body.index('var '+var+' =')
 body=body[pos:];body=body[body.index('{')+1:];body=body[:body.rindex('}')]
 entries=list(re.finditer(r'(?<!\w)([345]\d{2}):',body));result={}
 for i,m in enumerate(entries):
  chunk=body[m.end():entries[i+1].start() if i+1<len(entries) else len(body)]
  result[int(m[1])]=[v for _,v in strings(chunk) if '：' in v and re.search('[\u4e00-\u9fff]',v.split('：',1)[1])]
 return result
stages=sorted([json.loads(p.read_text()) for p in (ROOT/'actual/data/stages').glob('*.json')],key=lambda d:d['id'])
main=[s for s in stages if not s['code'].startswith('S')];side=[s for s in stages if s['code'].startswith('S')]
entrycodes=re.findall(r'^#### 运行稿 (\w+) ',doc,re.M)
campaign=json.loads((ROOT/'actual/data/campaign.json').read_text());scenes=[]
for code,pages in campaign['scenes'].items():
 lines=[p['speaker']+'：'+p['text'] for p in pages]
 scenes.append({'code':code,'pages':len(pages),'whole_document':check('／'.join(lines)),'current_section':check('／'.join(lines),section)})
src={n:(ROOT/f'actual/core/{n}.gd').read_text() for n in ['chapter2_rules','chapter3_rules','chapter4_rules','chapter5_rules','story_hub','chapter3_hub','chapter4_hub','chapter5_hub']}
beforemaps={4:map_strings(src['chapter4_rules'],'before_lines','text'),5:map_strings(src['chapter5_rules'],'before_lines','text')}
endmaps={3:map_strings(src['chapter3_rules'],'on_victory','endings'),4:map_strings(src['chapter4_rules'],'on_victory','ending'),5:map_strings(src['chapter5_rules'],'on_victory','ending')}
# Normal living-speaker branch of the mandatory battle opening and victory sequence.
# Conditional variants and all optional events are indexed separately below.
battles=[]
for s in stages:
 ch=s['chapter'];id=s['id'];before=s['before'];after=s['after']
 if ch in [4,5]:before=beforemaps[ch][id][0]
 if id==303:before+='／工匠：工房里还收着被押走的旧军械。先守住码头、取回记录，战后我们会一件件认领。'
 if id==306:before+='／术士：工房里封存着看守者征用的旧魔剑。先救人、稳住阵台，再整理兵器。'
 if ch in [3,4,5]:after=endmaps[ch][id][0]
 if id==205:after='艾琳：先带引航者离开牢房。我去确认箱里的航图。'
 if id==206:after='舵手：居民船已经抵达西岸泊位，等候海峡城准许入港。／艾琳：先稳住船队。我去海峡城，争取让伤者上岸。'
 if id==211:after='渔民：风灯岛东侧还有一处避风泊位。你们救了船上的人，这条路我会给你们标清。'
 row={'code':s['code'],'id':id,'chapter':ch,'side':s['code'].startswith('S'),'has_current_battle_entry':s['code'] in entrycodes,'phases':{}}
 for key,value in [('before',before),('after',after)]:row['phases'][key]={'text':value,'whole_document':check(value),'current_section':check(value,section)}
 battles.append(row)
# Compare original JSON fields with their own documented running entry, independent of controller overrides.
field_compare=[]
for s in stages:
 pattern=re.compile(r'^#### 运行稿 '+s['code']+r' [^\n]*\n(.*?)(?=^#### |^### |\Z)',re.M|re.S);m=pattern.search(doc)
 if not m:continue
 for key in ['before','during','after']:
  if s.get(key):field_compare.append({'code':s['code'],'chapter':s['chapter'],'field':key,**check(s[key],m[1])})
# Fully extractable fixed hub narrative literals (lower bound; dynamic concatenations not expanded).
hub_literals=[]
for name in ['story_hub','chapter3_hub','chapter4_hub','chapter5_hub']:
 text=src[name]
 for match,value in strings(text):
  before=text[:match.start()];line=before.count('\n')+1;line_src=text.splitlines()[line-1]
  candidate=False
  if name=='story_hub':
   if '：' in value and len(value.split('：',1)[1])>5 and re.search('[\u4e00-\u9fff]',value):candidate=True
   if re.search(r'"text"\s*:\s*$',before):candidate=True
   if re.search(r'var (?:mine_line|clinic_line|line|text)=',line_src) and re.search('[\u4e00-\u9fff]',value) and len(value)>8:candidate=True
   if '"text":' in line_src and re.search('[\u4e00-\u9fff]',value) and len(value)>8:candidate=True
   if re.search(r'obj\(',line_src) and len(value)>15 and re.search('[。！…]',value):candidate=True
  else:
   if '：' in value and len(value.split('：',1)[1])>5 and re.search('[\u4e00-\u9fff]',value):candidate=True
  if not candidate or len(value)<6 or not re.search('[\u4e00-\u9fff]',value):continue
  # Exclude fragments that require a runtime prefix/suffix to become a whole utterance.
  if before.rstrip().endswith('+') or text[match.end():].lstrip().startswith('+'):continue
  sourcebody=value.split('：',1)[-1]
  hub_literals.append({'file':f'actual/core/{name}.gd','line':line,'literal':value,'in_document':norm(sourcebody) in norm(doc),'in_current_section':norm(sourcebody) in norm(section)})
# Read the last confirmed installed IPA, without contacting the iPhone or launching the app.
ipa=ROOT/'actual/dist/RevengeMemories-0.10.4-iPhone-Latest-20261025-213231.ipa'
with zipfile.ZipFile(ipa) as z:raw=z.read('Payload/RevengeMemories.app/RevengeMemories.pck')
assert raw[:4]==b'GDPC' and struct.unpack_from('<I',raw,4)[0]==4
base=struct.unpack_from('<Q',raw,24)[0];idx=struct.unpack_from('<Q',raw,32)[0];count=struct.unpack_from('<I',raw,idx)[0];pos=idx+4;pack={}
for _ in range(count):
 ln=struct.unpack_from('<I',raw,pos)[0];pos+=4;name=raw[pos:pos+ln].rstrip(b'\0').decode();pos+=ln
 offset,size=struct.unpack_from('<QQ',raw,pos);pos+=16;checksum=raw[pos:pos+16];pos+=16;flags=struct.unpack_from('<I',raw,pos)[0];pos+=4
 if name=='data/campaign.json' or name.startswith('data/stages/') and name.endswith('.json'):
  payload=raw[base+offset:base+offset+size];assert hashlib.md5(payload).digest()==checksum
  pack[name]=json.loads(payload)
assert pos==len(raw)
phone_diffs=[]
for s in stages:
 old=pack['data/stages/'+s['code']+'.json'];diff={k:{'installed':old.get(k),'current':s.get(k)} for k in ['cause','before','during','after','after_no_survivors','absent_branch'] if old.get(k)!=s.get(k)}
 if diff:phone_diffs.append({'code':s['code'],'fields':diff})
phone_scenes_same=campaign['scenes']==pack['data/campaign.json']['scenes']
summary={
 'runtime_stages':len(stages),'main_stages':len(main),'side_stages':len(side),'document_current_entries':len(entrycodes),
 'chapters':[],'campaign_scene_groups':len(scenes),'scene_pages':sum(s['pages'] for s in scenes),
 'scene_pages_exact_in_document':sum(s['whole_document']['exact'] for s in scenes),
 'scene_pages_exact_in_current_section':sum(s['current_section']['exact'] for s in scenes),
 'field_compare':{'fields':len(field_compare),'exact_fields':sum(r['total']==r['exact'] for r in field_compare),'utterances':sum(r['total'] for r in field_compare),'exact_utterances':sum(r['exact'] for r in field_compare)},
 'hub_literals':{'candidates':len(hub_literals),'exact_in_document':sum(r['in_document'] for r in hub_literals),'exact_in_current_section':sum(r['in_current_section'] for r in hub_literals)},
 'installed_snapshot':{'ipa':str(ipa),'pck_sha256':hashlib.sha256(raw).hexdigest(),'scene_data_matches_current':phone_scenes_same,'differing_stage_texts':[r['code'] for r in phone_diffs]},
}
for ch in range(1,6):
 selected=[r for r in battles if r['chapter']==ch];mandatory=[r for r in selected if not r['side']]
 phases=[p for r in mandatory for p in r['phases'].values()]
 summary['chapters'].append({'chapter':ch,'stages':len(selected),'main':len(mandatory),'side':sum(r['side'] for r in selected),'current_entries':sum(r['has_current_battle_entry'] for r in selected),'main_opening_victory_segments':len(phases),'segments_fully_in_document':sum(p['whole_document']['total']==p['whole_document']['exact'] for p in phases),'segments_fully_in_current_section':sum(p['current_section']['total']==p['current_section']['exact'] for p in phases),'utterances':sum(p['whole_document']['total'] for p in phases),'exact_utterances_in_document':sum(p['whole_document']['exact'] for p in phases)})
result={'scope':'Read-only source/installed-package/document comparison. No new gameplay or phone interaction. Primary battle segments mean normal living-speaker opening/victory branch only; no claim of every optional dialogue path. Hub literal counts are a fixed-string lower-bound, not all dynamically generated utterances.','summary':summary,'scenes':scenes,'battles':battles,'field_compare':field_compare,'hub_literals':hub_literals,'phone_text_differences':phone_diffs}
(OUT/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('SCENE MISMATCH',[(r['code'],r['pages'],r['whole_document']['missing']) for r in scenes if r['whole_document']['missing']])
print('FIELDS MISMATCH',[(r['code'],r['field'],r['exact'],r['total']) for r in field_compare if r['exact']<r['total']])
for name in ['story_hub','chapter3_hub','chapter4_hub','chapter5_hub']:
 rows=[r for r in hub_literals if Path(r['file']).stem==name];print('HUB',name,len(rows),sum(r['in_document'] for r in rows))

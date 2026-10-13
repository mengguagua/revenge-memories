#!/usr/bin/env python3
"""Validate complete native Chinese source-page translations and ending variants."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads((ROOT/p).read_text())
def main():
 failures=[]; entries=[]; hubs=read('data/hubs.json')['dialogues']; zh=read('data/dialogue_zh.json'); battle=read('data/battle_event_dialogues.json'); bz=read('data/battle_event_zh.json'); ending=read('data/ending_zh.json')
 for label,source,target in [('hubs',hubs,zh),('battle',battle['events'],bz['events']),('death',battle['death_quotes'],bz['death_quotes'])]:
  if set(source)!=set(target):failures.append(f'{label} ID mismatch')
  for key,pages in target.items():
   originals=source[key]['pages']
   if len(pages)!=len(originals):failures.append(f'{label}:{key} page count')
   for i,text in enumerate(pages):
    if not text.strip():failures.append(f'{label}:{key}:{i} empty')
    if re.search('[ぁ-ゖァ-ヺ]',text):failures.append(f'{label}:{key}:{i} untranslated kana')
    if sorted(re.findall(r'%\d',text))!=sorted(re.findall(r'%\d',originals[i]['text_ja'])):failures.append(f'{label}:{key}:{i} placeholder mismatch')
    entries.append((f'{label}:{key}:{i}',text))
 for k,v in ending['texts'].items():
  if not v['text_zh'].strip():failures.append(f'ending{k} empty')
  entries.append((f'ending:{k}',v['text_zh']))
 for kind in ['narration','final_words']:
  for i,entry in enumerate(ending[kind]):entries.append((f'{kind}:{i}',entry['text_zh']))
 font=read('data/font_zh.json')['glyphs'];missing={c for _,t in entries for c in t if ord(c)>127 and c not in font}
 if missing:failures.append('Missing font glyphs:'+''.join(sorted(missing)))
 def select(cid,alive):
  rule=ending['characters'][str(cid)]
  if rule['kind']=='fixed':return rule['ending_id']
  mask=sum(8>>i for i,id in enumerate(rule['related_character_ids']) if id in alive)
  return next((r['ending_id'] for r in rule['rules'] if r['living_mask']==mask),rule['default_ending_id'])
 examples=[(8,{7,9},8),(8,{9},9),(8,{7},10),(9,{8},11),(9,set(),12),(10,{19},13),(10,set(),14),(13,{16},15),(13,set(),16),(17,{23},21),(17,set(),22),(19,{10},24),(19,set(),25),(30,{34},35),(30,set(),36),(31,{32,33},37),(31,{33},38),(32,{31,33},39),(32,{31},40),(33,{31,32},41),(33,{32},42),(1,set(),45),(2,set(),44)]
 for cid,alive,expected in examples:
  if select(cid,alive)!=expected:failures.append(f'Ending condition {cid}:{alive}')
 counts={'hub_groups':len(zh),'hub_pages':sum(map(len,zh.values())),'battle_groups':len(bz['events']),'battle_pages':sum(map(len,bz['events'].values())),'death_groups':len(bz['death_quotes']),'death_pages':sum(map(len,bz['death_quotes'].values())),'ending_variants':len(ending['texts']),'ending_characters':len(ending['characters']),'narration_paragraphs':len(ending['narration']),'final_words_pages':len(ending['final_words']),'ending_condition_examples':len(examples),'non_ascii_characters':len({c for _,t in entries for c in t if ord(c)>127}),'missing_glyphs':sorted(missing),'failures':failures,'source_page_alignment':'Exact; display pagination may split longer Chinese source pages.','translation_notes':['Hub79 source contains truncated うさま and くだい; translated the remaining intended request without fabricating a title.','Death quote24 keeps original %2 dynamic-name placeholder.','Epilogue1 keeps native death location as {death_place}.','Nui Baba follows original Japanese male pronoun here, not later-remake characterization.'],'limitations':['This report validates source coverage, placeholders, font coverage and ending branch data; renderer pagination/safe-area checks belong to integrated runtime QA.']}
 (ROOT/'reports/full-translation-verification.json').write_text(json.dumps(counts,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(counts,ensure_ascii=False));assert not failures,failures
if __name__=='__main__':main()

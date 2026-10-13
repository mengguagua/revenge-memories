#!/usr/bin/env python3
"""Add exact NPC portraits and Shadow palettes without regenerating timelines."""
import copy,json
from pathlib import Path
from extract_full_graphics import Source,body_sheet
from extract_graphics import ROOT,DATA

src=Source(Path('/private/tmp/fe2-analysis-20261012'))
meta=json.loads(DATA.read_text())
meta['character_portraits']={str(i):int(p) for i,p in enumerate(src.b[9]['L09BDBF']['db'][:44]) if p}
meta['character_portraits'].update({str(128+i):int(p) for i,p in enumerate(src.b[9]['L09BDEB']['db'][:45]) if p})
meta['character_portrait_source']='L09AE13-L09AE46: nonnegative source id uses44-entryL09BDBF; high-bit id uses45-entryL09BDEB[id&127]; out-of-range high ids use0. A mapped0 means no portrait and is omitted.'
meta['portraits']['alm']['source_selection_rule']='L09AE13-L09AE33: source id1 usesportrait36; when$744A is set, source portrait identity36 usesportrait20.'
meta['portraits']['celica']['source_selection_rule']='L09AE28-L09AE33: source id2 usesportrait48; when$744B is set, source portrait identity37 usesportrait11.'
for c in range(1,23):
    base=meta['battle'][f'class_{c}_ally'];key=f'class_{c}_ally_name_35'
    meta['assets']=[a for a in meta['assets'] if a['path']!=f'res://assets/original/graphics/battle/{key}.png']
    entry=body_sheet(src,meta,c,'ally',38,key)
    for field in ['sequences','attack_schedule','weapon_variants','spell_variants']:
        if field in base:entry[field]=copy.deepcopy(base[field])
    entry['source_note']+=' Character35 Shadow overrideL058DFB selects palette38 before class palettes.'
    base.setdefault('palette_variants',{})['35']=key
temp=DATA.with_suffix('.tmp');temp.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');temp.replace(DATA)
print(json.dumps({'portrait_id_count':len(meta['character_portraits']),'shadow_class_count':22,'selected':{str(i):meta['character_portraits'].get(str(i)) for i in [35,36,37,38,39,43,134,141]}}))

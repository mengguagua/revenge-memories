#!/usr/bin/env python3
"""Add the source acted metatiles without touching extracted battle programs."""
import json,re
from pathlib import Path
from extract_full_graphics import Source,tactical,ROOT,DATA

def main():
    source=Path('/private/tmp/fe2-analysis-20261012');src=Source(source)
    meta=json.loads(DATA.read_text());raw=(source/'src/bank006.asm').read_text()
    raw=raw.split('L_METATILES_PALETTE_ID:')[0]
    metas=[]
    for line in raw.splitlines():
        if line.strip().startswith('.db'):metas.extend(int(v,16) for v in re.findall(r'\$([0-9A-F]{2})',line.split(';')[0]))
    meta['assets']=[a for a in meta['assets'] if a.get('kind')!='full_class_map_acted']
    for c in range(1,23):
        for side in ['ally','enemy']:
            tactical(src,meta,c,side,metas,True)
            meta['map_units'][f'class_{c}_{side}']['acted_variant']=f'class_{c}_{side}_acted'
    meta['tactical_palette_source']={'ready_player':[15,32,34,26],'ready_enemy':[15,54,37,26],'acted':[15,16,0,26],
        'neutral_rule':'L0FD777/L0FD77B computes class*2 + source_name_bit7; there is no separate green neutral map palette. Friendly source names below128 use blue palette0. L0FD771 adds112 for acted metatiles, which select grey palette1.',
        'source':'bank006 L_METATILES_PALETTE_ID/L06852C; bank015 L0FD771-L0FD789'}
    DATA.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'acted_class_sheets':44,'files':[{'path':a['path'],'pixels':[a['width'],a['height']],'bytes':(ROOT/a['path'].removeprefix('res://')).stat().st_size} for a in meta['assets'] if a.get('kind')=='full_class_map_acted']}))
if __name__=='__main__':main()

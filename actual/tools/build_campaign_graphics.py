#!/usr/bin/env python3
"""Build compatibility indexes from approved campaign art, never from source pixels."""
import copy
import json
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def read(path): return json.loads((ROOT / path).read_text())
def write(path, value): (ROOT / path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
def svg(name, width, height, body):
    folder = ROOT / 'assets/campaign-ui'
    folder.mkdir(exist_ok=True)
    (folder / (name + '.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" shape-rendering="crispEdges">{body}</svg>\n')
    return 'res://assets/campaign-ui/' + name + '.svg'

def build():
    source = read('data/legacy/graphics.json')
    reviewed = read('data/animation_runtime/reviewed.json')['metadata']
    party = read('data/party_visuals.json')
    people = read('data/campaign.json')['characters']
    portraits = read('data/portraits.json')['assets']
    small = read('data/legacy/font_small_zh.json')
    def portrait(key):
        key = {'hunapu':'hunapu_present','eileen':'eileen_present','noya':'lisa','celine':'mireille'}.get(key,key)
        return {'path': portraits[key]['path'], 'size': [48, 48], 'key': key}
    def profile(cid, side):
        key = ('eileen' if cid in [11, 24] else '23_ally') if cid in [23,24] else f'{cid}_{side}'
        if cid == 24: key = 'eileen_promoted'
        return key if key in reviewed['battle'] else f'{cid}_ally' if f'{cid}_ally' in reviewed['battle'] else f'6_{side}'
    def mapping(cid, side, kind='tactical-idle'):
        key = profile(cid, side)
        value = reviewed['maps'].get(key, {}).get(kind, {})
        if not value:
            value = reviewed['maps'].get(key, {}).get('tactical-idle', {})
        if not value:
            value = party['classes'].get(str(cid), party['classes']['civilian']).get('hub', {})
        value = copy.deepcopy(value)
        if 'directions' not in value:
            value['directions'] = {d: [0, 0] for d in ['up','right','down','left','side']}
        if 'side' not in value['directions']: value['directions']['side'] = value['directions'].get('right',[0,0])
        return value
    named = {'fighter':21,'soldier':6,'villager':14,'brigand':14,'mycen':4,'archer':12}
    def class_for(key, item):
        match = re.search(r'class_(\d+)',key)
        if match: return int(match.group(1))
        if 'celica' in key: return 24 if 'promoted' in key else 11
        if 'alm' in key: return 23 if 'promoted' in key else 21
        return int(item.get('class_id',item.get('visual_class', named.get(key.split('_')[0],6))))
    graphics = {'revision':'campaign-art-only-20261026', 'panel':{'path':'res://assets/journey-home/journal-panel.png','nine_patch_margins':[8,8,8,8],'content_padding':10},
                'font':{'path':small['path'],'glyphs':{k:v for k,v in small['glyphs'].items() if len(k)==1 and (32<=ord(k)<127 or 0xff01<=ord(k)<=0xff5e)},'char_codes':{chr(i):[i] for i in range(32,127)}},
                'battle':{},'map_units':{},'fallback_battle':{},'fallback_maps':{},'village_sprites':{},'village_units':{},'portraits':{},'portraits_by_index':{},'character_portraits':source['character_portraits'],
                'title':{'path':'res://assets/journey-home/snow-coast.png'},'compat_atlas':'res://assets/battle_tiles/battle-tiles.png'}
    for key, item in source['battle'].items():
        cid = class_for(key,item);side = 'enemy' if 'enemy' in key else 'ally'
        value = {k:copy.deepcopy(item[k]) for k in ['weapon_variants','spell_variants','palette_variants','spell_body_variants','background_frame_offset'] if k in item}
        value['attack_schedule'] = {k:copy.deepcopy(v) for k,v in item.get('attack_schedule',{}).items() if k in ['kind','effect_variant','native_fps']}
        value.update(copy.deepcopy(reviewed['battle'][profile(cid, side)]))
        value.pop('costume_variant_frames',None)
        graphics['battle'][key] = value
    for key,item in source['map_units'].items():
        cid = class_for(key,item);side='enemy' if 'enemy' in key else 'ally'
        value=mapping(cid,side)
        value['acted_variant']=item.get('acted_variant',key)
        graphics['map_units'][key]=value
    for cid,class_spec in party['classes'].items():
        if 'battle' in class_spec:
            art=class_spec['battle']
            graphics['fallback_battle'][cid]={k:copy.deepcopy(art[k]) for k in ['path','frame_size','frames','columns','anchor','native_density','logical_frame_size','sequences','default_facing'] if k in art}
        graphics['fallback_maps'][cid]={k:copy.deepcopy(v) for k,v in class_spec.items() if k in ['map','map_move','hub']}
    source_people={str(v['character_id']):k for k,v in people.items()}
    for key in source['village_sprites']:
        identity=source_people.get(key,'')
        cid=int(people[identity]['class_id']) if identity else 14
        value=mapping(cid,'ally','story')
        if not identity:
            value=copy.deepcopy(party['classes']['civilian']['hub'])
        graphics['village_sprites'][key]=value
    old_people={'alm':'hunapu','mycen':'herlan','lukas':'daan','kliff':'otto','tobin':'otto','gray':'otto','celica':'eileen'}
    for key in source['village_units']:
        identity=old_people.get(key,'hunapu');cid=int(people.get(identity,people['hunapu'])['class_id'])
        graphics['village_units'][key]=mapping(cid,'ally','story')
    for key in source['portraits']: graphics['portraits'][key]=portrait(old_people.get(key,'civilian_west'))
    for key in source['portraits_by_index']: graphics['portraits_by_index'][key]=portrait('civilian_west')
    for sid,index in source['character_portraits'].items():
        identity=source_people.get(sid,'')
        if identity:
            asset='hunapu_present' if identity=='hunapu' else 'eileen_present' if identity=='eileen' else identity
            graphics['portraits_by_index'][str(index)]=portrait(asset)
    graphics['battle_background']={'path':svg('battle-field',256,128,'<defs><linearGradient id="d" x2="0" y2="1"><stop stop-color="#070b13"/><stop offset="1" stop-color="#101a27"/></linearGradient></defs><path fill="url(#d)" d="M0 0h256v128H0z"/><path fill="#162331" d="M0 124h256v4H0z"/>')}
    # New simple navigation glyphs are vector-native; no copied tile pixels.
    arrows={'right':'M2 1h2v1h1v1h1v2H5v1H4v1H2V5H1V3h1z',
            'left':'M6 1H4v1H3v1H2v2h1v1h1v1h2V5h1V3H6z',
            'up':'M1 6V4h1V3h1V2h2v1h1v1h1v2H5v1H3V6z',
            'down':'M1 2v2h1v1h1v1h2V5h1V4h1V2H5V1H3v1z'}
    cursors={'revision':graphics['revision'],'arrows':{}}
    for key,path in arrows.items():cursors['arrows'][key]={'path':svg('cursor-'+key,8,8,f'<path fill="#eee8d2" d="{path}"/>'),'native_size':[8,8]}
    health={'revision':graphics['revision'],'cells':{},'layout':read('data/legacy/health_ui.json')['layout']}
    for side,color in [('ally','#6f9fc0'),('enemy','#bd7971')]:
        health['cells'][side]={}
        for state in ['filled','empty']:
            body='<path fill="#eee8d2" d="M0 1h3v5H0z"/><path fill="#b1c1c6" d="M0 6h3v1H0z"/>' if state=='filled' else f'<path fill="{color}" fill-opacity=".50" d="M0 1h3v6H0z"/>'
            health['cells'][side][state]={'path':svg('health-'+side+'-'+state,4,8,body),'native_size':[4,8]}
    effects=read('data/legacy/full_map_effects.json')
    effects['revision']=graphics['revision'];effects.pop('source_revision',None)
    for key,row in effects['programs'].items():
        care=key in ['9','10'];color='#9bdab5' if care else '#97b9d9'
        body=f'<path fill="{color}" fill-opacity=".25" d="M6 38h20v4H6z"/><path fill="{color}" d="M8 36h16v1H8zM4 38h4v1H4zM24 38h4v1h-4zM4 41h4v1H4zM24 41h4v1h-4zM8 43h16v1H8z"/>'
        if care:body+='<path fill="#d9f0cf" d="M15 23h2v4h4v2h-4v4h-2v-4h-4v-2h4z"/>'
        else:body+='<path fill="#c7dfeb" d="M9 25h2v5H9zM21 20h2v5h-2zM15 14h2v4h-2z"/>'
        row['path']=svg('map-care' if care else 'map-transition',32,48,body)
        row.update({'frame_size':[32,48],'frames':1,'columns':1,'anchor':[16,40],'tile_origin_offset':[8,8],'cycle_timeline':[0]*len(row['cycle_timeline'])})
    write('data/campaign_graphics.json',graphics);write('data/campaign_cursors.json',cursors);write('data/campaign_health.json',health);write('data/campaign_map_effects.json',effects)
    for file in ['campaign_graphics','campaign_cursors','campaign_health','campaign_map_effects']:
        assert 'res://assets/original/' not in (ROOT/f'data/{file}.json').read_text(),file
    print('Campaign visual indexes rebuilt without original texture paths.')
if __name__=='__main__':build()

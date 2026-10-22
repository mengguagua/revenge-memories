#!/usr/bin/env python3
"""Join individually inspected material evidence, checking current map hashes."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-spatial-20261022'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
records={}
sources=['material-audit/west10.json','material-audit/east13.json','material-audit/chapter4-10.json','material-audit/chapter5-east-finale-4.json']
for source in sources:
 d=read(O/source);assert d['passed'],source
 for row in d['maps']:
  c=row['code'];assert c not in records,c
  assert row['passed'] and row['map_sha256']==sha(R/f'data/stages/{c}.json'),c
  records[c]=dict(row,evidence_report=source)
for row in read(O/'west-spatial-audit.json')['maps']:
 c=row['code'];assert row['frozen'] and row['sha256']==sha(R/f'data/stages/{c}.json'),c
 records[c]={'code':c,'scene':'室外王都内廷与剖面病房' if c=='M51' else '室外跨水石桥与连续岩岸',
  'materials':row['material_review'],'findings':[row['diagnosis']],
  'image_reviewed':row['native_image'],'map_sha256':row['sha256'],'passed':True,
  'evidence_report':'west-spatial-audit.json'}
d=read(O/'library/visual-review.json');assert d['passed'] and d['map_sha256']==sha(R/'data/stages/S51.json')
records['S51']={'code':'S51','scene':'室内书库：独立拼木地、磨损石中厅与南楼梯间',
 'materials':read(O/'library/assets.json')['assets'],'image_reviewed':d['image'],
 'map_sha256':d['map_sha256'],'passed':True,'findings':d['checks'],'evidence_report':'library/visual-review.json'}
conclusions={
 'M51':'修正：病房呈现床位与室内方石，伤兵真实经过南门；院外草地与石路保留。',
 'M52':'修正：风化石桥、承台与厚岩岸相接；原三段桥跨度和敌我相对距离保持。',
 'F51':'地下粗石维修地保留；修正可走层间阶梯与人工渠沿。',
 'F52':'修正：去顶室内控制厅使用神宫大理石，取消厅内屋顶宫殿。',
 'S51':'修正：船板/大理石复用改为室内拼木与暖灰磨损石地，北档案室不再摆屋顶建筑。',
 'J53':'修正：前庭为室外铺石，跨人工内池使用同层石桥。',
 'J54':'修正：上层大理石神座与下层露天石坪区分，三阶口之间补真实高台边界。',
 'M13':'修正：两间牢室及开门后的门槛改为石地，院外保留土路。',
 'S11':'修正：矿道大厅的沼泽底纹改为洞穴碎石与压实矿道。',
 'F25':'修正：码头木栈改为风化灰木板，船体甲板保持。',
 'F31':'修正：岸侧木栈和跳板使用风化木材，船体甲板保持。',
 'F33':'修正：室外检修木桥使用风化木材，与船板区分。',
 'S31':'修正：剖面牢室内使用室内磨损石地，山村接近区的草地、土路保持。',
 'S32':'修正：剖面牢室内使用室内磨损石地，营地外盐土与道路保持。',
 'F41':'修正：岩石脚下移除洞窟底纹，改为对应沙地过渡。',
 'F42':'修正：岩石脚下移除洞窟底纹，改为对应盐原表面。',
}
baseline=read(O/'baseline/maps.json');codes=sorted(baseline,key=lambda c:read(R/f'data/stages/{c}.json')['id'])
assert set(records)==set(codes) and len(records)==40
maps=[]
for c in codes:
 row=records[c];row['name']=read(R/f'data/stages/{c}.json')['name_zh']
 row['baseline_sha256']=baseline[c];row['changed']=row['map_sha256']!=baseline[c]
 row['conclusion']=conclusions.get(c,'保留：实际纹理、材质来源与场景用途相符。')
 maps.append(row)
chapter5={'M51','M52','F51','F52','S51','J53','J54'}
result={'passed':True,'map_count':40,'changed_maps':[m['code'] for m in maps if m['changed']],
 'changed_outside_chapter5':[m['code'] for m in maps if m['changed'] and m['code'] not in chapter5],
 'unchanged_maps':[m['code'] for m in maps if not m['changed']], 'maps':maps,
 'scope':'40 maps individually inspected against native rendered images and actual atlas sources. Previous chapters change material art only; chapter five also corrects authorized spatial relationships. Core and animations unchanged.',
 'categories':['草地/雪地','沙地/盐地','船体甲板','户外风化木栈/木桥','室外石铺','室内拼木','室内磨损石地','神宫大理石']}
(O/'material-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'passed':True,'maps':40,'changed':len(result['changed_maps']),'material_only':len(result['changed_outside_chapter5']),'unchanged':len(result['unchanged_maps'])}))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record the ten individually viewed maps and four shared source atlases."""
from pathlib import Path
import json, hashlib
R=Path(__file__).resolve().parents[1]
O=R/'reports/chapter5-spatial-20261022/material-audit'
BASE=json.loads((O.parent/'baseline/maps.json').read_text())
CODES=['M41','M42','M43','M44','F41','F42','F43','F44','S41','S42']
changes=json.loads((O/'chapter4-rock-material-changes.json').read_text())
SCENES={
 'M41':'室外雪峡村落、两处河桥和撤离古道',
 'M42':'室外骑兵关口、木围营院及林缘侧路',
 'M43':'露天雪地塔院，土路接铺石检修道',
 'M44':'王都城门外的草地、医舍院与石砌主街',
 'F41':'沙地城镇、两处井台及山石边缘',
 'F42':'盐原观测设施、设备石台与海岸',
 'F43':'潮沼中的干岛、危险湿地和木栈道',
 'F44':'露天沉没祭所，多块石台由木维修桥相连',
 'S41':'雪地村落道路与钟塔、档案屋',
 'S42':'沼泽孤岛诊所、干岛、湿地与接船木台'}
TEXTURES={
 'M41':'snow 4..7 雪地；dirt 8..11 压实土路；sea 28..31 河流；木桥方向与跨河方向匹配，岩石直接站雪地。',
 'M42':'grass 0..3 草地、dirt 8..11 行军土路、cobble 20..23 门前作业石坪；营地为露天院落。',
 'M43':'snow 4..7 积雪；dirt/stone 两种道路；石道是有横向砌缝的石板而非木纹，完整塔堡是外观。',
 'M44':'grass/dirt 城郊地面；stone 城门主街；医舍草庭与土路属于室外，房舍保持完整外观。',
 'F41':'sand 36..39 沙地；dirt 压实路；cobble 井台防泥石地；岩根去除cave 12..15，回归sand。',
 'F42':'salt 40..43 盐壳；dirt 干道；cobble 设备作业石台；岩根去除cave 12..15，回归salt。',
 'F43':'grass/dirt 干岛；marsh 44..47 灰褐湿地；timber/bridge 木台和栈道；sea 连续开放水面。',
 'F44':'cobble/stone 露天祭所石台；木维修桥跨海水且落脚接石台，海水不是封闭室内池。',
 'S41':'snow 雪地与雪底山石；dirt 村道连屋门、钟塔、档案屋，完整房屋与室外语义一致。',
 'S42':'grass/dirt 诊所干岛与道路；marsh 北岛与湿地边缘；timber/bridge 接船台和桥梁，未铺进诊所室内。'}
rows=[]
for code in CODES:
 p=R/f'data/stages/{code}.json';d=json.loads(p.read_text());current=hashlib.sha256(p.read_bytes()).hexdigest();changed=code in ['F41','F42']
 source=d['art_atlas'].removeprefix('res://')
 image=f'actual/reports/chapter5-spatial-20261022/material-audit/chapter4/images/{code}.png' if changed else f'art-review/battle-maps-20261021/images/{code}.png'
 finding='旧bare_rock实际映射到cave，形成沙/盐地上的紫灰洞窟直边大块。' if changed else '逐图全景与对应原始atlas核对通过：用途、道路、建筑外观及纹理方向一致，未发现室内外地面混用。'
 action='仅岩根基础图块改为本地沙/盐纹理；完整岩石与阻挡保留。独立atlas是旧图集原像素副本，不覆盖共享文件；增加material_review_version。' if changed else '保持现有材质与地图完整不变；不做无依据的统一替换。'
 row={'code':code,'scene':SCENES[code],'materials':[{'purpose':'当前地面材质与结构用途','actual_source':source,'texture_definition':TEXTURES[code]}],'original_atlas_reviewed':'actual/'+('assets/chapter4-redesign-20261022/east/terrain.png' if changed else source),'findings':[finding],'changes':[action],'passed':True,'map_sha256':current,'image_reviewed':image,'tactical_review_version':d['tactical_review_version'],'material_revision':d.get('material_review_version'),'baseline_map_sha256':BASE[code],'unchanged':current==BASE[code]}
 if changed:
  delta=next(x for x in changes['maps'] if x['code']==code);row['changed_ground_cell_count']=len(delta['changed_ground_cells']);row['all_geometry_actors_objects_rules_story_natural_props_unchanged']=delta['all_geometry_actors_objects_rules_story_natural_props_unchanged']
 else:assert row['unchanged'],code
 rows.append(row)
report={'passed':True,'map_count':10,'maps':rows,'review_method':'All ten current whole-map PNGs viewed individually plus four distinct source atlases. F41/F42 rendered anew with the verified Godot background guard and viewed individually. Native-scale ground texture, repeating seams, bridge grain direction and scene usage checked.','changed_maps':['F41','F42'],'unchanged_maps':[c for c in CODES if c not in ['F41','F42']],'geometry_changed':False,'core_changed':False}
(O/'chapter4-10.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
four=json.loads((O.parent/'east-finale-spatial-audit.json').read_text())
(O/'chapter5-east-finale-4.json').write_text(json.dumps({'passed':True,'map_count':4,'maps':four['maps'],'material_generation':four['material_generation'],'spatial_audit':'east-finale-spatial-audit.json'},ensure_ascii=False,indent=2)+'\n')
print('Material review: 10 chapter-four maps and 4 chapter-five maps recorded.')

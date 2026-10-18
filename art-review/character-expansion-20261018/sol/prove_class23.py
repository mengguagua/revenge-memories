# -*- coding: utf-8 -*-
"""Read-only source and art-owner coverage proof, no duplicated sprite generation."""
from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parent.parent
read=lambda p:json.loads(p.read_text())
catalog=read(R/'catalog/class-catalog.json');classes={c['class_id']:c for c in catalog['classes']};units=read(R/'catalog/production-units.json')['units'];u=next(x for x in units if x['id']=='class-23-ally');hm=read(R/'hunapu/battle/frame_mapping.json');motion=read(R/'source-input/original-motion/full-original-motion.json');motion['variants'].update(read(R/'source-input/corrected-ally-motion/overlay.json').get('variants',{}))
checks=[]
for key in u['bound_action_keys']:
 v=motion['variants'][key];needed=sorted({r['frame']for r in v['frames']});missing=[f for f in needed if str(f)not in hm['frame_mapping']];assert not missing,(key,missing)
 resources=[]
 for f in needed:
  path=(R/'hunapu/battle'/hm['frame_mapping'][str(f)]).resolve();assert path.is_file();assert Image.open(path).size==(320,288);resources.append({'source_frame':f,'mapped_art':str(path.relative_to(R)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 checks.append({'action':key,'source_class_id':v['source_class_id'],'ticks':len(v['frames']),'contact_tick':v.get('contact_tick'),'missing_frames':missing,'frames':resources})
a=classes[21]['battle_profiles']['ally'];b=classes[23]['battle_profiles']['ally'];assert a['source_asset']['path']==b['source_asset']['path'];assert a['map_idle_source']['path']==b['map_idle_source']['path']
old21=Image.open(R/'source-input/original-motion/original-walk-21.png').convert('RGBA');old23=Image.open(R/'source-input/original-motion/original-walk-23.png').convert('RGBA');same_legacy=old21.size==old23.size and old21.tobytes()==old23.tobytes()
report={'revision':'sol','class_id':23,'name':'勇者','source_class_id':21,'existing_art_owner':'hunapu','battle_status':'covered_by_existing_approved_art','battle_programs_checked':len(checks),'battle_checks':checks,'canonical_drawings_newly_created':0,'existing_drawing_count_not_duplicated':35,'same_catalog_battle_source':True,'same_catalog_idle_source':True,'historical_walk21_23_complete_rgba_equal':same_legacy,'tactical_walk_status':'alias_resolution_requires_explicit_current_native_proof','note':'旧CHR26+village21/23 RGBA相同只证明旧源别名，不能替代正确CHR27 tactical源。当前仅确认战斗与静止源可复用；不把class23整组新增计为完成。','game_code_evidence':'actual/core/battle_animation.gd:_class maps23to21; promoted usesexisting21 promoted art','runtime_integrated':False}
(R/'sol/class-23-coverage-proof.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('class23:',len(checks),'battle programs covered; native map alias remains explicit pending.')

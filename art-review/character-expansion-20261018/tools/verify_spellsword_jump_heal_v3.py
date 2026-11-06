#!/usr/bin/env python3
"""Targeted pose continuity, native schedule and ally-heal playback verification."""
import ast,copy,json,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,matched_export,relative
from export_gallery import render_frame
from export_knight_complete import export_one
from revise_spellsword_jump_heal_v3 import REV,OUT,write,G,helper

def main():
 b=json.loads((OUT/'baseline.json').read_text());old={a['id']:a for a in b['gallery']['actions']};d=json.loads((ROOT/'demos/gallery-data.json').read_text());aa={a['id']:a for a in d['actions']};pp={p['id']:p for p in d['profiles']};contracts=json.loads((OUT/'healing-contracts.json').read_text())['actions'];hc={c['key']:c for c in contracts}
 expected={a['id']for a in b['gallery']['actions']if a['profile']=='professions-class-11-ally-maps-tactical-walk'and a['key']in['walk-right','idle-right','walk-left','idle-left']or a['key']=='original_class_11_normal'or a['key']in hc};assert len(expected)==23 and len(contracts)==18
 assert not d['validation']['structuralIssues']and all(aa[x]['ready']for x in expected)
 concurrent=[];unchanged=0
 for aid,a in aa.items():
  if aid not in old:concurrent.append({'action':aid,'reason':'new outside this revision'});continue
  if aid not in expected:
   if a['contentDigest']!=old[aid]['contentDigest']:concurrent.append({'action':aid,'reason':'resource changed outside this revision','profile':a['profile']})
   else:unchanged+=1
  else:
   previous=old[aid];assert a['frames']==previous['frames']and a['fps']==previous['fps']and a['duration']==previous['duration']and a['origin']==previous['origin']and a['contactTick']==previous['contactTick']
 for eid,meta in b['gallery']['effects'].items():assert d['effects'][eid]==meta
 # Protect unchanged female-spellsword actions even while other work is active.
 assert not any(c.get('profile','').startswith('professions-class-11-')for c in concurrent)
 poses={}
 p=pp['professions-class-11-ally-maps-tactical-walk']
 for i in[2,3,6,7]:poses[i]=Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA')
 assert poses[2].crop((0,0,128,68)).tobytes()==poses[3].crop((0,0,128,68)).tobytes()
 assert poses[6].crop((0,0,128,68)).tobytes()==poses[7].crop((0,0,128,68)).tobytes()
 for i,j in[(6,2),(7,3)]:assert poses[i].tobytes()==poses[j].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()
 previous=next(p for p in b['gallery']['profiles']if p['id']=='professions-class-11-ally-maps-tactical-walk')
 for i in[2,3,6,7]:assert poses[i].crop((0,68,128,96)).tobytes()==Image.open(ROOT/previous['newFrames'][str(i)]).convert('RGBA').crop((0,68,128,96)).tobytes()
 assert p['mapShadow']==previous['mapShadow']
 p=pp['professions-class-11-ally-battle'];jumps={i:Image.open(ROOT/p['newFrames'][str(i)]).convert('RGBA')for i in[2,3,4,5,6,7,8,9,25,26,27,28]}
 for ids,region in[([2,3,4,5,6,7],[160,128,270,288]),([8,9],[160,128,280,288]),([25,26],[140,196,280,288]),([27,28],[140,196,290,288])]:
  assert len({jumps[i].crop(region).tobytes()for i in ids})==1,('unstable leg region',ids)
 for i,im in jumps.items():
  cs=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cs)==1,(i,'detached')
 assert all(a['contactTick']==old[a['id']]['contactTick']for a in aa.values()if a['profile']=='professions-class-11-ally-battle')
 for key,c in hc.items():
  a=next(a for a in d['actions']if a['key']==key);base=old[a['id']];rows=a['revisedFrames'];assert len(rows)==len(a['frames'])and not a.get('reviewTailFrames')
  prior=base.get('revisedFrames',base['frames'])
  for t,(new,source)in enumerate(zip(rows,prior)):
   assert {k:v for k,v in new.items()if k!='effects'}=={k:v for k,v in source.items()if k!='effects'}
   if t<c['rain_start']:assert all(e['sprite'].startswith('ally_heal_green_v3_')for e in new['effects'])
   elif t<c['rain_end_exclusive']:assert len(new['effects'])==1 and new['effects'][0]['sprite']=='ally_heal_green_rain_v3_'+str((t-c['rain_start'])//6+1)and new['effects'][0]['position']==c['rain_target_center']
   else:assert not new['effects']
  assert c['additional_heals']==0 and c['rain_start']>c['native_contact']and c['rain_end_exclusive']<c['native_total_ticks']
 manifest=json.loads((OUT/'asset-manifest.json').read_text());assert len(manifest['new_vfx_effect_ids'])==19
 for eid in manifest['new_vfx_effect_ids']:
  im=Image.open(ROOT/d['effects'][eid]['path']).convert('RGBA');assert {p[:3]for p in im.getdata()if p[3]}<=set(G)and set(im.getchannel('A').getdata())<={0,255}
 for r in manifest['assets']:assert file_hash(ROOT/r['path'])==r['sha256']
 report={'status':'assets_passed','revision':REV,'changed_actions':len(expected),'unrelated_actions_unchanged':unchanged,'concurrent_outside_changes':concurrent,'fixed_side_walk_upper_body':True,'side_walk_lower_body_unchanged':True,'map_shadow_unchanged':True,'four_airborne_leg_groups_stable':True,'native_trajectories_frames_fps_contacts_and_durations_unchanged':True,'ally_heal_variants':18,'ally_heal_classes':[11,18,19],'existing_effect_metadata_unchanged':True,'green_effect_assets':19,'extra_heals':0,'rain_fits_original_recovery':True,'enemy_not_edited':True,'runtime_integrated':False,'browser_ui_checked':False,'visual_acceptance':'pending'}
 write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','changed':len(expected),'unrelated_unchanged':unchanged,'concurrent':len(concurrent)}),flush=True)
 exports=[];captures=[]
 for aid in sorted(expected):
  a=aa[aid];p=pp[a['profile']];normal=a['key']=='original_class_11_normal';canon=a['key']in['class_11_ally_item_40','class_18_ally_item_40','class_19_ally_item_40'];far=a['key']=='class_11_ally_item_40_far_ally_vs_heavy';walk=a['kind']=='map_walk';video=normal or canon or far or walk
  exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=not video)))
  if normal:exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  ticks=[0,16]if walk else[80,92,107,190,214,226]if normal else[a['contactTick'],hc[a['key']]['rain_start'],hc[a['key']]['rain_start']+12,hc[a['key']]['rain_start']+30]if canon or far else[]
  for t in ticks:
   for light in[False,True]:
    path=OUT/f'{a["key"]}-{t:03}-{"light"if light else"dark"}.png';render_frame(d,p,a,t,7 if walk else 5,light,normal).save(path,optimize=True);captures.append(relative(path))
  print('Exported '+a['key'],flush=True)
 decoded=[]
 for e in exports:
  if not e.get('video'):continue
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for a in latest['actions']:
  if a['id']not in expected:continue
  assert a['contentDigest']==aa[a['id']]['contentDigest']
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n')
 report.update(status='passed',decoded_videos=len(decoded),stills=len(expected),captures=captures);write(OUT/'verification.json',report);write(OUT/'export-report.json',{'exports':exports,'decoded':decoded})
 write(OUT/'action-effect-mapping.json',{'source_rules':['docs2/完整游戏设定.md:478','docs2/职业命名提案-0.9.0.md:18'],'card_id':'item_40','card_name':'恢复','actions':contracts,'normal_attack':{'actor_id':'class-11-ally','card':'普通剑击','contact':aa['professions-class-11-ally-battle--original_class_11_normal']['contactTick'],'additional_hits':0},'runtime_rules_changed':False})
 for n in['revise_spellsword_jump_heal_v3.py','verify_spellsword_jump_heal_v3.py']:ast.parse((ROOT/'tools'/n).read_text())
 print(json.dumps({'status':'passed','changed':len(expected),'videos':len(decoded),'green_heals':18}),flush=True)
if __name__=='__main__':main()

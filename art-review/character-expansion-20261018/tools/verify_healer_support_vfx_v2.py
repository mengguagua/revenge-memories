#!/usr/bin/env python3
"""Verify only the requested four support spells, then render representative playback."""
import argparse,json,re,subprocess,ast
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,relative,matched_export
from export_gallery import render_frame,playback_count
from export_knight_complete import export_one
from revise_healer_support_vfx_v2 import REV,OUT,write,G,R,B
def verify(export=False):
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());now={a['id']:a for a in d['actions']};before={a['id']:a for a in b['gallery']['actions']};pp={p['id']:p for p in d['profiles']};contracts=json.loads((OUT/'spell-contracts.json').read_text())['actions'];affected={f'professions-class-{c}-ally-battle--'+x['key']for x in contracts for c in[17,18]if x['key'].startswith(f'class_{c}_')};assert len(affected)==48 and len(contracts)==48
 assert not d['validation']['structuralIssues']and all(now[k]['ready']for k in affected)
 unchanged=[];external=[]
 for key,a in before.items():
  assert key in now
  if key not in affected:
   if a['contentDigest']!=now[key]['contentDigest']:
    assert not a['profile'].startswith(('professions-class-17-ally-','professions-class-18-ally-')),('unexpected own non-support change',key)
    external.append(key)
   else:unchanged.append(key)
 for eid,meta in b['gallery']['effects'].items():assert d['effects'][eid]==meta,('prior effect modified',eid)
 for path,digest in b['body_map_hashes'].items():assert file_hash(ROOT/path)==digest,('body/map art modified',path)
 bykey={x['key']:x for x in contracts};assets=json.loads((OUT/'asset-manifest.json').read_text());newids=set(assets['new_effect_ids']);assert newids<=set(d['effects'])
 for r in assets['assets']:assert file_hash(ROOT/r['path'])==r['sha256']
 for eid in newids:
  meta=d['effects'][eid];im=Image.open(ROOT/meta['path']).convert('RGBA');assert list(im.size)==[round(v*4)for v in meta['frame_size']];palette=G if'green_'in eid or'spring_'in eid else B if'pillar_'in eid else R;assert{p[:3]for p in im.getdata()if p[3]}<=set(palette);assert set(im.getchannel('A').getdata())<={0,255};assert(ROOT/meta['path']).stat().st_size<50000
 checks=[]
 for key in sorted(affected):
  a=now[key];old=before[key];c=bykey[a['key']];spell=c['spell_id'];p=pp[a['profile']];assert p['revision']==REV
  for field in['frames','fps','origin','contactTick']:assert a[field]==old[field],(key,field)
  revised=a['revisedFrames'];assert len(revised)==len(old['frames'])
  for row,original in zip(revised,old['frames']):assert{k:v for k,v in row.items()if k!='effects'}=={k:v for k,v in original.items()if k!='effects'}
  tail=a.get('reviewTailFrames',[]);assert len(tail)==c['review_tail_ticks']and len(tail)<=round(a['fps']*2)
  for row in tail:assert{k:v for k,v in row.items()if k!='effects'}=={k:v for k,v in old['frames'][-1].items()if k!='effects'}
  rows=revised+tail
  if spell==41:
   assert c['rain_ticks']==54 and c['rain_end']-c['rain_start']==54
   for row in rows[c['rain_start']:c['rain_end']]:assert len(row['effects'])==1 and row['effects'][0]['sprite'].startswith('ally_heal_green_rain_v3_')
   heal=now[key.replace('_item_41','_item_40')]
   for t in range(c['rain_start']):assert rows[t]['effects']==heal['revisedFrames'][min(t,len(heal['frames'])-1)]['effects']
  elif spell==42:
   assert not tail and c['flow_direction']=='target_to_caster'
   for row in rows:
    for e in row['effects']:assert e['sprite'].startswith(('support_v2_drain_','support_v2_extract_'))
   assert any(e['sprite']=='support_v2_extract_0'for e in rows[c['extraction_start']]['effects'])
   assert any(e['sprite'].startswith('support_v2_extract_')for e in rows[c['extraction_start']+12]['effects'])
  elif spell==43:
   assert not tail and all(row['effects']for row in rows[c['column_start']:c['column_end']])
   for row in rows[c['column_start']:c['column_end']]:assert row['effects'][0]['position']==c['target_ground']and row['effects'][0]['sprite'].startswith('support_v2_pillar_')
  elif spell==44:
   assert c['one_coalesced_basin']and len(c['original_visible_effect_slots'])>=3 and c['pool_start']==c['rain_end']
   for row in rows[c['rain_start']:c['rain_end']]:assert all(e['sprite'].startswith('ally_heal_green_rain_v3_')for e in row['effects'])
   for row in rows[c['pool_start']:c['pool_end']]:assert len(row['effects'])==1 and row['effects'][0]['sprite'].startswith('support_v2_spring_')and row['effects'][0]['position']==c['pool_ground']
  assert c['additional_resolutions']==0
  checks.append({'action':key,'spell_id':spell,'contact_tick':a['contactTick'],'native_ticks':len(a['frames']),'review_tail_ticks':len(tail),'display_ticks':playback_count(a),'native_actor_rows_exact':True})
 for script in['revise_healer_support_vfx_v2.py','verify_healer_support_vfx_v2.py']:ast.parse((ROOT/'tools'/script).read_text())
 report={'status':'assets_passed','revision':REV,'affected_actions':48,'prior_actions_unchanged':len(unchanged),'concurrent_external_art_changes_preserved':external,'body_maps_weapons_unchanged':True,'all_old_effect_metadata_unchanged':True,'new_effect_ids':len(newids),'source_actor_rows_fps_origins_contacts_exact':True,'support40_unchanged':True,'native_resolution_count_unchanged':True,'green_remote_rain_ticks':54,'max_review_tail_ticks':max(c['review_tail_ticks']for c in contracts),'runtime_integrated':False,'browser_ui_checked':False,'user_visual_acceptance':'pending','actions':checks};write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','affected':48,'unchanged':len(unchanged)}),flush=True)
 if not export:return
 exports=[];captures=[]
 for key in sorted(affected):exports.append(export_one(d,now[key],SimpleNamespace(close=False,scale=4,light=False,stills_only=True)))
 selected=[now[k]for k in sorted(affected)if not any(w in k for w in['far_','vs_heavy'])or'class_17_ally_item_'in k and k.endswith('_far_enemy_vs_heavy')]
 assert len(selected)==12
 for a in selected:
  exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)));p=pp[a['profile']];c=bykey[a['key']];spell=c['spell_id']
  if not any(w in a['key']for w in['far_','vs_heavy']):
   if spell==41:ticks=[next(t for t,f in enumerate(a['frames'])if f['effects']),a['contactTick'],c['rain_start']+12,c['rain_end']-5]
   elif spell==42:ticks=[c['extraction_start'],c['extraction_start']+12,c['extraction_start']+32,a['contactTick']]
   elif spell==43:ticks=[c['column_start'],c['column_start']+24,a['contactTick'],c['column_end']-4]
   else:ticks=[a['contactTick'],c['rain_start']+12,c['rain_end']-1,c['pool_start']+25,c['pool_end']-15]
   for tick in ticks:
    for light in[False,True]:
     path=OUT/(a['key']+f'-{tick:03}-'+('light.png'if light else'dark.png'));render_frame(d,p,a,tick,4,light,False).save(path,optimize=True);captures.append(relative(path))
  print('Exported '+a['key'],flush=True)
 decoded=[]
 for e in exports:
  if not e.get('video'):continue
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
 # Preserve any independent gallery additions produced during offline exports.
 latest=json.loads((ROOT/'demos/gallery-data.json').read_text())
 for a in latest['actions']:
  for field,kind,suffix,ext in[('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   path=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(path)if matched_export(path,a['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(latest,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(latest,ensure_ascii=False,separators=(',',':'))+'\n');report.update(status='passed',decoded_videos=len(decoded),offline_captures=captures,gallery_ready_actions=sum(a['ready']for a in latest['actions']));write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});print(json.dumps({'status':'passed','videos':len(decoded),'stills':48,'captures':len(captures)}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)

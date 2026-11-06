#!/usr/bin/env python3
"""Verify native female-mage timing, stable map registrations, and preview exports."""
import ast,copy,json,re,subprocess
from types import SimpleNamespace
from PIL import Image
from build_gallery import ROOT,file_hash,pack_frame,relative,matched_export,SPELL_NAMES
from export_gallery import render_frame
from export_knight_complete import export_one
from prepare_female_mage_complete import REV,OUT,write
from import_female_mage_complete import C,EC,helper,box

def verify(export=False):
 b=json.loads((OUT/'baseline.json').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());pp={p['id']:p for p in d['profiles']};now={a['id']:a for a in d['actions']};before={a['id']:a for a in b['gallery']['actions']};actions=[a for a in d['actions']if a['profile'].startswith('professions-class-16-')];contracts={c['key']:c for c in json.loads((OUT/'spell-sharing-contracts.json').read_text())['contracts']}
 assert len(actions)==146 and len(now)==1018 and len(pp)==106 and len(contracts)==108 and all(a['ready']for a in actions)
 assert not d['validation']['structuralIssues'] and set(now)-set(before)=={a['id']for a in actions}
 for k,a in before.items():assert a['contentDigest']==now[k]['contentDigest'],('unrelated action',k)
 assert d['effects']==b['gallery']['effects']
 schedules=[]
 for a in actions:
  p=pp[a['profile']];side=p['side'];assert p['classId']=='16' and p['revision']==REV and not a.get('reviewTailFrames')
  if a['kind']=='attack':
   v=b['variants'][side][a['key']];assert a['frames']==[pack_frame(f)for f in v['frames']] and a['fps']==v['native_fps'] and a['origin']==v['actor_origin'] and a['contactTick']==v['contact_tick']
   if a['key']in contracts:
    c=contracts[a['key']];parent=now[c['parent_action']];template=parent['revisedFrames']+parent.get('reviewTailFrames',[]);rows=a['revisedFrames'];assert len(rows)==len(a['frames'])
    assert c['source_tick_by_frame'][a['contactTick']]==a['contactTick']
    for row,old,n in zip(rows,a['frames'],c['source_tick_by_frame']):
     assert {k:v for k,v in row.items()if k!='effects'}=={k:v for k,v in old.items()if k!='effects'}
     assert row['effects']==(template[n]['effects']if n<len(template)else[])
   else:assert not a.get('revisedFrames')
   spell=v['source_item_id'];schedules.append({'actor_id':'class-16-'+side,'campaign_card_binding':['lisa','noya']if side=='ally'else None,'source_action':a['key'],'spell_id':spell,'spell_name':SPELL_NAMES[spell],'native_program':v['source_program_address'],'total_ticks':len(a['frames']),'native_release_tick':next(i for i,f in enumerate(a['frames'])if f['frame']==2),'effect_contact_tick':a['contactTick'],'contact_count':v['contact_count'],'native_actor_rows_exact':True,'note':'职业完整参考动作库。实际角色可用法术仍由个人法术表和解锁状态决定，未授予未学习法术或额外伤害。'})
  elif a['key']=='idle-cycle':assert [f['frame']for f in a['frames']]==[i for _ in range(2)for i,n in zip([0,1,2,1],[14,8,14,8])for _ in range(n)]
  elif a['kind']=='map_walk':
   start={'walk-up':0,'walk-right':2,'walk-down':4,'walk-left':6}[a['key']];assert [f['frame']for f in a['frames']]==[i for _ in range(3)for i in [start,start+1]for _ in range(16)]
   assert all(f['offset']==[0,0]and not f['flip']for f in a['frames'])
 assert len(schedules)==120
 for row in json.loads((OUT/'source-audit.json').read_text())['sources']:assert file_hash(ROOT/row['path'])==row['sha256']
 images={};checks=[]
 for side in ['ally','enemy']:
  colors=C if side=='ally'else EC
  for kind,count,size in [('tactical-idle',6,(96,96)),('tactical-walk',8,(128,96)),('battle',3,(320,256))]:
   paths=sorted((OUT/side/kind).glob('frame-*.png'));assert len(paths)==count
   for path in paths:
    i=int(path.stem.split('-')[-1]);im=Image.open(path).convert('RGBA');images[side,kind,i]=im
    assert im.size==size and set(im.getchannel('A').getdata())=={0,255} and {p[:3]for p in im.getdata()if p[3]}<=set(colors)
    cs=helper.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(cs)==1,(side,kind,i,'detached part',[(len(c),box(c))for c in cs[1:]])
    checks.append({'path':relative(path),'size':list(size),'bytes':path.stat().st_size,'sha256':file_hash(path),'connected_components':1,'colors':len({p[:3]for p in im.getdata()if p[3]})})
  for i,j in enumerate([0,1,2,1,0,1]):assert images[side,'tactical-idle',i].tobytes()==images[side,'tactical-idle',j].tobytes()
  for region in [[41,14,69,53],[40,70,70,81]]:assert all(images[side,'tactical-idle',i].crop(region).tobytes()==images[side,'tactical-idle',0].crop(region).tobytes()for i in [1,2])
  for ids,region in [([0,1],[36,25,92,72]),([2,3],[55,25,83,64]),([4,5],[47,25,82,63]),([6,7],[45,25,73,64])]:
   assert images[side,'tactical-walk',ids[0]].crop(region).tobytes()==images[side,'tactical-walk',ids[1]].crop(region).tobytes()
   assert images[side,'tactical-walk',ids[0]].crop((0,72,128,96)).tobytes()!=images[side,'tactical-walk',ids[1]].crop((0,72,128,96)).tobytes()
  # Front/back phases alternate the low supporting boot across the fixed waist.
  for ids in [[0,1],[4,5]]:
   means=[]
   for i in ids:
    im=images[side,'tactical-walk',i];pts=[(x,y)for y in range(91,96)for x in range(128)if im.getpixel((x,y))[3]];assert pts;means.append(sum(x for x,y in pts)/len(pts))
   assert means[0]<64<means[1],(side,ids,'support foot alternation',means)
 # Original factions use the same three silhouettes with a -16px BG origin.
 src=OUT/'source'
 for i in range(3):
  a=Image.open(src/f'native-ally-battle-{i:03}.png').convert('RGBA');e=Image.open(src/f'native-enemy-battle-{i:03}.png').convert('RGBA');q=Image.new('RGBA',a.size);q.alpha_composite(a,(-16,0));assert q.getchannel('A').tobytes()==e.getchannel('A').tobytes()
  a=images['ally','battle',i];e=images['enemy','battle',i];q=Image.new('RGBA',a.size);q.alpha_composite(a,(-64,0));assert q.getchannel('A').tobytes()==e.getchannel('A').tobytes()
 manifest=json.loads((OUT/'asset-manifest.json').read_text());assert all(x['clipped_pixels']==0 for x in manifest['registrations'])
 for row in manifest['assets']:assert file_hash(ROOT/row['path'])==row['sha256'] and (ROOT/row['path']).stat().st_size==row['bytes']
 for n in ['prepare_female_mage_complete.py','import_female_mage_complete.py','share_female_mage_spells.py','verify_female_mage_complete.py']:ast.parse((ROOT/'tools'/n).read_text())
 write(OUT/'action-effect-mapping.json',{'source_rules':['docs2/职业命名提案-0.9.0.md:18','docs2/完整游戏设定.md:367','docs2/完整游戏设定.md:897','actual/data/campaign.json:814'],'runtime_rules_changed':False,'ally_hero_spell_rules':{'lisa':{'initial':[23,24],'learned':[29,26]},'noya':{'initial':[23,24],'learned':[26,28]}},'actions':schedules})
 report={'status':'assets_passed','revision':REV,'new_profiles':6,'new_actions':146,'native_spell_variants':120,'existing_actions_unchanged':872,'all_native_actor_frames_fps_origins_contacts_and_lengths_exact':True,'shared_confirmed_spell_variants':108,'new_effect_images':0,'all_prior_effect_metadata_unchanged':True,'map_head_neck_torso_fixed':True,'map_idle_planted_feet_fixed':True,'front_back_support_feet_alternate':True,'all_34_body_images_connected':True,'source_assets_unchanged':True,'registrations_clipped_pixels':0,'assets':checks,'browser_ui_checked':False,'runtime_integrated':False,'user_visual_acceptance':'pending'}
 write(OUT/'verification.json',report);print(json.dumps({'status':'assets_passed','new_actions':146,'unchanged':872}),flush=True)
 if not export:return
 exports=[];captures=[]
 for a in actions:
  p=pp[a['profile']];side=p['side'];canonical=a['kind']=='attack'and not any(w in a['key']for w in ['far_','vs_heavy']);selected=canonical or a['kind']=='map_walk' or a['key'] in ['idle-cycle','idle']
  if not selected:continue
  exports.append(export_one(d,a,SimpleNamespace(close=False,scale=4,light=False,stills_only=False)))
  if canonical and a['key'].endswith(('_item_23','_item_28')):exports.append(export_one(d,a,SimpleNamespace(close=True,scale=4,light=False,stills_only=False)))
  ticks=[]
  if a['kind']=='map_walk':ticks=[0,16]
  elif a['key']=='idle-cycle':ticks=[0,14,22]
  elif canonical and a['key'].endswith(('_item_23','_item_28','_item_34')):ticks=[0,36,71,a['contactTick']]
  for tick in sorted(set(ticks)):
   for light in [False,True]:
    close=a['kind']=='attack';path=OUT/f'{side}-{a["key"]}-{tick:03}-{"light"if light else"dark"}.png';render_frame(d,p,a,tick,5 if close else 7,light,close).save(path,optimize=True);captures.append(relative(path))
  print('Exported '+side+' '+a['key'],flush=True)
 decoded=[]
 for e in exports:
  info=json.loads(subprocess.run(['/opt/homebrew/bin/ffprobe','-v','error','-count_frames','-select_streams','v:0','-show_entries','stream=width,height,nb_read_frames,duration','-of','json',str(ROOT/e['video'])],capture_output=True,text=True,check=True).stdout)['streams'][0];assert int(info['nb_read_frames'])==e['frames']and abs(float(info['duration'])-e['expected_duration'])<1/e['fps'];decoded.append({'path':e['video'],**info})
 for a in actions:
  for field,kind,suffix,ext in [('video','videos','','mp4'),('closeVideo','videos','--close','mp4'),('still','stills','','png')]:
   p=ROOT/f'demos/{kind}/{a["id"]}{suffix}.{ext}';a[field]=relative(p)if matched_export(p,a['contentDigest'])else None
 (ROOT/'gallery-data.js').write_text('window.GALLERY_DATA = '+json.dumps(d,ensure_ascii=False,separators=(',',':'))+';\n');(ROOT/'demos/gallery-data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':'))+'\n')
 report.update(status='passed',decoded_videos=len(decoded),offline_captures=captures);write(OUT/'verification.json',report);write(OUT/'export-report.json',{'status':'passed','exports':exports,'decoded_video_checks':decoded});print(json.dumps({'status':'passed','new_actions':146,'unchanged':872,'videos':len(decoded)}),flush=True)
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');verify(p.parse_args().export)

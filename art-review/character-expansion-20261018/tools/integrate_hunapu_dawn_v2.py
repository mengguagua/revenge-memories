#!/usr/bin/env python3
"""Scope gallery generation, export and merge to the revised Dawn Warrior."""
import argparse,contextlib,copy,hashlib,io,json,os,tempfile
from datetime import datetime,timezone
from pathlib import Path
from PIL import Image,ImageDraw,ImageOps
import import_hunapu_dawn_v2 as art
import integrate_hunapu_dawn_v1 as previous
import integrate_enemy_11_14_review as S
import export_gallery as E
import validate_gallery as V
ROOT=art.ROOT;OUT=art.OUT;PREFIX='hunapu-promoted-';FXPREFIX='review-hunapu-dawn-v2-spark-'
def own(row):return str(row.get('profile',row.get('id',''))).startswith(PREFIX)
def write(p,d):art.write(p,d)
def build():
 S.MAPS=[art.MP,art.BP];module=S.isolated_builder();live=json.loads((ROOT/'demos/gallery-data.json').read_text());effects={k:v for k,v in live['effects'].items()if not k.startswith(FXPREFIX)};read=module.read
 def scoped(path):
  value=read(path)
  if path==ROOT/'source-input/effects.json':value={**value,**copy.deepcopy(effects)}
  return value
 module.read=scoped;before=S.snapshot_shared()
 with contextlib.redirect_stdout(io.StringIO()):data=module.build()
 assert S.snapshot_shared()==before and len(data['profiles'])==5 and len(data['actions'])==43 and all(own(x)for x in data['profiles']+data['actions']);write(OUT/'gallery-data.json',data);return data
def verify(data):
 profiles={p['id']:p for p in data['profiles']};base={a['id']:a for a in art.olddata()['actions']};errors=[];checks=0;exact=[];revised=[]
 for p in profiles.values():
  assert p['heroProfession']=='dawn_warrior'and p['actor']=='hunapu'and p['className']=='破晓勇士'and not p['frameErrors']
  for value in p['newFrames'].values():
   im=V.image(value);assert list(im.size)==p['outputFrameSize']and im.getbbox();assert set(im.getchannel('A').getdata())<={0,255};checks+=1
 for a in data['actions']:
  n=base[a['id']];assert a['ready']and all(a[k]==n[k]for k in['frames','fps','origin','contactTick']);p=profiles[a['profile']];fw,fh=p['sourceFrameSize'];atlas=V.image(p['sourceAtlas']);exact.append(a['id'])
  if a.get('revisedFrames'):
   revised.append(a['key']);assert len(a['revisedFrames'])==len(a['frames'])
   assert all({k:v for k,v in x.items()if k not in['frame','effects']}=={k:v for k,v in y.items()if k not in['frame','effects']}for x,y in zip(a['frames'],a['revisedFrames']))
  for track,rows in[('native',a['frames']),('redraw',a.get('revisedFrames',a['frames']))]:
   for t,row in enumerate(rows):
    f=row['frame'];flip=(p['context']=='battle'and p.get('side')=='enemy')!=row.get('flip',False);off=row.get('offset',[0,0]);at=[a['origin'][i]+off[i]-p['anchor'][i]for i in[0,1]];at[0]+=row.get('shake',0)
    if flip and f<p['sourceOamCutoff']:at=[at[i]+p['flipOriginOffset'][i]for i in[0,1]]
    x=f%p['sourceColumns']*fw;y=f//p['sourceColumns']*fh;im=atlas.crop((x,y,x+fw,y+fh))if track=='native'else V.image(p['newFrames'][str(f)]);box=V.box_at(im,at,[fw,fh],flip);view=a.get('viewport',data['viewport']);checks+=1
    if V.outside(box,view):errors.append({'action':a['id'],'track':track,'tick':t,'body':box})
    cv=None
    if a.get('closeCamera'):
     c=a['closeCamera'];cv=[a['origin'][i]+off[i]+c['offset'][i]for i in[0,1]]+c['size'];checks+=1
     if V.outside(box,cv):errors.append({'action':a['id'],'track':track,'tick':t,'close_body':box})
    for e in row.get('effects',[]):
     meta=p.get('revisedEffects',{}).get(e['sprite'],data['effects'][e['sprite']])if track=='redraw'else data['effects'][e['sprite']];xy=[e['position'][i]-meta['anchor'][i]for i in[0,1]]
     if e.get('flip'):xy=[xy[i]+meta.get('flip_origin_offset',[0,0])[i]for i in[0,1]]
     eb=V.box_at(V.image(meta['path']),xy,meta['frame_size'],e.get('flip',False));checks+=1
     if V.outside(eb,view)or(e['sprite'].startswith(FXPREFIX)and cv and V.outside(eb,cv)):errors.append({'action':a['id'],'track':track,'tick':t,'effect':e['sprite'],'bounds':eb})
 assert sorted(revised)==['original_class_21_critical','original_class_21_promoted']
 checks_map=[]
 for kind,ids,y in[('story',[2,3],76),('story',[4,5],75),('tactical-walk',[0,1],73),('tactical-walk',[2,3],73),('tactical-walk',[6,7],73)]:
  ims=[Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA')for i in ids];assert ims[0].crop((0,0,128,y)).tobytes()==ims[1].crop((0,0,128,y)).tobytes();assert ims[0].tobytes()!=ims[1].tobytes();checks_map.append({'context':kind,'slots':ids,'fixed_upper_body_to_y':y,'upper_body_exact':True})
 for kind,ids,center in[('story',[2,3],65),('tactical-walk',[0,1],64)]:
  xs=[]
  for i in ids:
   im=Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA');points=[x for y in range(92,96)for x in range(128)if im.getpixel((x,y))[3]];xs.append(sum(points)/len(points))
  assert xs[0]<center<xs[1],(kind,xs);checks_map.append({'context':kind,'up_low_boot_centers_x':xs,'opposite_legs_confirmed':True})
 for kind,ids in[('story',[4,5]),('tactical-walk',[2,3]),('tactical-walk',[6,7])]:
  widths=[]
  for i in ids:
   im=Image.open(OUT/kind/f'frame-{i:03}.png').convert('RGBA').crop((0,87,128,96));bb=im.getbbox();widths.append(bb[2]-bb[0])
  assert widths[1]>widths[0]*1.4,(kind,ids,widths);checks_map.append({'context':kind,'slots':ids,'standing_and_stride_boot_spans':widths})
 assert ImageOps.mirror(Image.open(OUT/'tactical-walk/frame-002.png')).tobytes()!=Image.open(OUT/'tactical-walk/frame-006.png').tobytes()
 assert profiles['hunapu-promoted-maps-story']['newFrames']==profiles['hunapu-promoted-maps-world']['newFrames']
 shadow=profiles['hunapu-promoted-maps-tactical-walk']['mapShadow'];im=V.image(shadow['path']);components=art.H.parts((x,y)for y in range(im.height)for x in range(im.width)if im.getpixel((x,y))[3]);assert len(components)==1 and shadow['size']==[8,2]
 crit=next(a for a in data['actions']if a['key']=='original_class_21_critical');normal=next(a for a in data['actions']if a['key']=='original_class_21_promoted');assert[normal['revisedFrames'][t]['frame']for t in range(112,115)]==[6]*3;assert[crit['revisedFrames'][t]['frame']for t in range(183,186)]==[24]*3
 for t in[166,183]:assert any(e['sprite']==FXPREFIX+'1'for e in crit['revisedFrames'][t]['effects'])
 errors+=data['validation']['structuralIssues'];report={'passed':not errors,'checks':checks,'profiles':5,'actions':43,'original_rows_timings_contacts_preserved':exact,'only_two_attack_review_timelines_revised':revised,'map_checks':checks_map,'left_right_hand_layering_authored_separately':True,'tactical_shadow_size':[8,2],'tactical_shadow_connected_components':1,'second_slash_ticks_zero_based':{'normal':112,'critical':183},'critical_spark_peak_ticks':[166,183],'runtime_integrated':False,'errors':errors};write(OUT/'verification.json',report);assert not errors,errors[:5];return report
def boards(data):
 profiles={p['id']:p for p in data['profiles']}
 for key,ticks,label in[('original_class_21_promoted',[93,99,105,112,115,124,128,132],'normal-followup'),('original_class_21_critical',[162,166,171,176,183,186,194,199],'critical-followup')]:
  a=next(a for a in data['actions']if a['key']==key);p=profiles[a['profile']];rows=a['revisedFrames']
  for light in[False,True]:
   panels=[E.render_panel(data,p,a,rows[t],True,4,light,True).convert('RGB')for t in ticks];w,h=panels[0].size;out=Image.new('RGB',(w*4,(h+34)*2),(220,222,216)if light else(32,45,53));dr=ImageDraw.Draw(out)
   for n,(t,panel)in enumerate(zip(ticks,panels)):
    x=n%4*w;y=n//4*(h+34);out.paste(panel,(x,y));dr.text((x+w/2,y+h+17),f'第{t+1}帧 · 新姿势{rows[t]["frame"]}',font=E.font(17),anchor='mm',fill=art.H.NAVY if light else'white')
   out.save(OUT/(label+('-light.png'if light else'-dark.png')),optimize=True)
def export(data):
 previous.OUT=OUT;previous.boards=boards;previous.export(data)
def merge(data):
 paths=S.source_paths();before=S.snapshot_shared();live=json.loads(paths[1].read_text());assert S.parse_js(paths[0])==live;combined=copy.deepcopy(live)
 for field in['profiles','actions']:
  combined[field]=S.merge_rows(live[field],data[field],own);assert[x for x in live[field]if not own(x)]==[x for x in combined[field]if not own(x)]
 added=[]
 for a in data['actions']:
  for key in a['effectIds']:
   if key in live['effects']:assert data['effects'][key]==live['effects'][key],key
   else:assert key.startswith(FXPREFIX);combined['effects'][key]=data['effects'][key];added.append(key)
 assert all(combined['effects'][key]==value for key,value in live['effects'].items())
 combined['builtAt']=datetime.now(timezone.utc).isoformat();combined['summary']={**live['summary'],'profiles':len(combined['profiles']),'actions':len(combined['actions']),'ready':sum(a['ready']for a in combined['actions']),'pending':sum(not a['ready']for a in combined['actions'])};report=json.loads(paths[2].read_text());report.update(builtAt=combined['builtAt'],summary=combined['summary']);report['actions']=S.merge_rows(report['actions'],[{k:a[k]for k in['id','name','ready','missingFrames','missingEffects','duration']}for a in data['actions']],own);payload=json.dumps(combined,ensure_ascii=False,separators=(',',':'));staged=[]
 try:
  for p,text in[(paths[0],'window.GALLERY_DATA = '+payload+';\n'),(paths[1],payload+'\n'),(paths[2],json.dumps(report,ensure_ascii=False,indent=2)+'\n')]:
   fd,name=tempfile.mkstemp(prefix='.hunapu-dawn-v2-',dir=p.parent);os.close(fd);Path(name).write_text(text);staged.append((Path(name),p))
  assert S.snapshot_shared()==before,'Concurrent writer detected; retry against latest records'
  for temporary,p in staged:os.replace(temporary,p)
 finally:
  for temporary,_ in staged:temporary.unlink(missing_ok=True)
 assert S.parse_js(paths[0])==combined==json.loads(paths[1].read_text())and S.sha(paths[3])==before['index.html'];write(OUT/'merge-report.json',{'target_profiles':5,'target_actions':43,'unrelated_profiles_actions_preserved':True,'existing_effects_preserved':True,'added_spark_definitions':sorted(set(added)),'index_default_unchanged':True,'runtime_integrated':False})
def main():
 p=argparse.ArgumentParser();p.add_argument('--export',action='store_true');p.add_argument('--merge',action='store_true');args=p.parse_args();data=build();v=verify(data);print(json.dumps({'actions':43,'checks':v['checks']}),flush=True)
 if args.export:export(data);data=build()
 if args.merge:merge(data)
if __name__=='__main__':main()

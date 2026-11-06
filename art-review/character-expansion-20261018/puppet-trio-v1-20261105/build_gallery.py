# coding: utf-8
from pathlib import Path
from PIL import Image
import json,shutil,re
R=Path(__file__).resolve().parent;P=R.name+'/';M=json.loads((R/'asset-manifest.json').read_text());D=json.loads((R/'design.json').read_text());profiles=[];actions=[];effects={}
for key,f in M['effects'].items():effects['trio-'+key]={'path':P+f['path'],'frame_size':f['pixels'],'anchor':[f['pixels'][0]/2,f['pixels'][1]/2],'native_density':1}
shutil.copyfile(R.parent/'pseudo-titan-v1-20261105/assets/maps-00.png',R/'assets/ally-map.png')
hit=json.loads((R.parent/'water-monkey-v1-20261104/source/motion-v2-20261104/soldier-hit-reference.json').read_text())['frames']
state_names={'intact':'核心完整','broken':'核心破坏','fire-broken':'火核破坏','life-broken':'生命核破坏','both-broken':'双核破坏'}
for unit,u in D['units'].items():
 states=D['visuals']['states'][unit]
 for state in states:
  for scene in ['battle','maps']:
   group=f'{unit}-{state}-{scene}';entries=M['frames'][group];size=entries[0]['pixels'];battle=scene=='battle';pid='puppet-trio-'+group
   profiles.append({'id':pid,'actor':'puppet-trio-'+unit,'actorName':'敌方'+u['name'],'classId':'design-'+unit,'className':u['name']+'（'+state_names[state]+'）','context':'battle' if battle else 'tactical-walk','contextName':'战斗场景' if battle else '地图四向','side':'enemy','mappingStatus':'review_only_not_integrated','revision':'puppet-trio-v1-20261105','sourceAtlas':P+'assets/'+group+'-reference.png','sourceFrameSize':size,'sourceColumns':len(entries),'sourceFrameCount':len(entries),'sourceAtlasSize':[size[0]*len(entries),size[1]],'sourceOamCutoff':0,'flipOriginOffset':[0,0],'anchor':[size[0]/2,72 if not battle or unit=='cyclops' else 100],'outputFrameSize':[n*4 for n in size],'newFrames':{str(e['id']):P+e['path'] for e in entries},'reviewFrameSources':{str(e['id']):0 for e in entries},'reviewFrameLabels':{str(e['id']):'独立绘制 · 姿势'+str(e['id']+1) for e in entries},'mapping':P+'action-effect-mapping.json','links':[{'label':'三类数值与规则交互','href':P+'index.html?unit='+unit},{'label':'生图来源与提示词','href':P+'source/prompts.json'}]})
 def make(state,key,label,scene,segments,contact=None,companion=False,note=''):
  battle=scene=='battle';rows=[]
  for f,n in segments:rows.extend({'frame':f,'offset':[0,0],'flip':battle,'effects':[]} for i in range(n))
  a={'id':f'puppet-trio-{unit}-{state}-{key}','key':key,'unit':unit,'state':state,'name':state_names[state]+' · '+label,'profile':f'puppet-trio-{unit}-{state}-{scene}','context':'battle' if battle else 'tactical-walk','frames':rows,'fps':60.0988,'duration':len(rows)/60.0988,'origin':[176,128] if battle else [128,116],'viewport':[0,0,256,160],'closeCamera':{'offset':[-72,-108],'size':[144,112]},'contactTick':contact,'neededFrames':sorted({r['frame'] for r in rows}),'effectIds':[],'missingFrames':[],'ready':True,'referenceLabel':'新增设计 · 形象基准（无原作）','newLabel':'原生像素设计','notes':'仅美术与HTML规则预览，未接入游戏、未投放关卡。'+note}
  if companion:a['reviewCompanions']=[{'path':P+'assets/soldier-reference.png','origin':[64,128],'size':[80,64],'anchor':[40,64],'flip':True}]
  actions.append(a);return a
 def finalize(a):
  a['neededFrames']=sorted({r['frame'] for r in a['frames']});a['effectIds']=sorted({e['id'] for r in a['frames'] for e in r.get('effects',[])})
 def fx(row,name,pos,alpha=1):row['effects'].append({'id':'trio-'+name,'sprite':'trio-'+name,'position':pos,'flip':False,'alpha':alpha})
 for state in states:
  label=state_names[state];engine=unit=='owl' and state=='intact';fire=unit=='prometheus' and state in ['intact','life-broken'];life=unit=='prometheus' and state in ['intact','fire-broken']
  make(state,'idle','战斗待机','battle',[(0,120)],note=u['role'])
  a=make(state,'battle-walk','飞行移动' if unit=='owl' else '战斗行走','battle',[(i,10) for i in [1,0,2,0]*3]+[(0,12)])
  for i,row in enumerate(a['frames']):row['offset']=[-round(min(i,120)*.25),0]
  a=make(state,'attack',u['attack']['name']+(' · 1–2格魔法' if unit=='cyclops' else ' · 近距单次攻击'),'battle',[(0,126 if unit=='cyclops' else 172)],60 if unit=='cyclops' else 68,True,note='近战先靠近再攻击并回位；魔法原地准备、释放与收势。每次结算只表现一击，不附加伤害次数。')
  for i,row in enumerate(a['frames']):
   if unit=='cyclops':
    row['frame']=3 if 12<=i<36 else 4 if 36<=i<70 else 5 if 70<=i<96 else 0
    if 36<=i<60:fx(row,'violet-pulse',[round(154-(i-36)/24*90),114])
    if 60<=i<78:fx(row,'violet-hit',[64,114],1-(i-60)/18)
   else:
    speed=6 if unit=='owl' else 9
    if 8<=i<48:row.update(frame=[1,0,2,0][((i-8)//speed)%4],offset=[-round(76*(i-8)/40),0])
    elif 48<=i<68:row.update(frame=3,offset=[-76,0])
    elif 68<=i<96:row.update(frame=4,offset=[-76,0])
    elif 96<=i<118:row.update(frame=5 if unit=='owl' else 0,offset=[-76,0])
    elif 118<=i<164:row.update(frame=[1,0,2,0][((i-118)//speed)%4],offset=[-round(76*(164-i)/46),0],flip=False)
   j=i-a['contactTick']
   if unit=='prometheus' and 0<=j<16:fx(row,'physical-wave',[64,108],1-j/16)
   if 0<=j<len(hit):row.update(companionTint=hit[j].get('tint',1),companionShake=hit[j].get('shake',0))
  a['soundEvents']=[{'tick':a['contactTick'],'path':P+'assets/hit.ogg','volume':.35}];finalize(a)
  if unit=='prometheus':
   for key,name,magic in [('ranged','锚臂冲击 · 2–3格物理',False)]+([('fire','炽核灼流 · 1–3格必中魔法',True)] if fire else []):
    a=make(state,key,name,'battle',[(0,126)],66,True,note='锚臂释放物理压力波，武器不离手。' if not magic else '火核有效才可选择；真正必中，单次交锋与物理二选一。')
    for i,row in enumerate(a['frames']):
     row['frame']=(5 if magic else 3) if 10<=i<38 else (5 if magic else 4) if 38<=i<82 else 0
     if 38<=i<66:fx(row,'fire-bolt' if magic else 'physical-wave',[round(150-(i-38)/28*86),108])
     if 66<=i<86:fx(row,'fire-hit' if magic else 'physical-wave',[64,108],1-(i-66)/20)
     j=i-66
     if 0<=j<len(hit):row.update(companionTint=hit[j].get('tint',1),companionShake=hit[j].get('shake',0))
    a['soundEvents']=[{'tick':66,'path':P+'assets/hit.ogg','volume':.4}];finalize(a)
  a=make(state,'hit','普通受伤 · 士兵同姿势闪烁','battle',[(0,len(hit))],note='固定身体姿势、明暗闪烁、轻微位移与命中音。')
  for row,ref in zip(a['frames'],hit):row.update(tint=ref.get('tint',1),shake=ref.get('shake',0))
  a['soundEvents']=[{'tick':0,'path':P+'assets/hit.ogg','volume':.35}]
  a=make(state,'defeat','本体最终被击败','battle',[(0,12),(6,24),(7,48)],note='生命核心有效的普罗米修斯先按复苏程序处理；此处仅展示最终击败。')
  for i,row in enumerate(a['frames']):
   if i>=68:row['alpha']=max(0,1-(i-68)/15)
  idle=[0,2,0,2] if unit!='owl' else [0,1,2,3]
  make(state,'map-idle','地图待机','maps',list(zip(idle,[14,8,14,8])),note='地面待机沿敌方枪兵44帧频率；飞枭展示维持悬停的翼拍。原生图密度2，独眼／飞枭约24逻辑像素，Boss约30。')
  for direction,start in [('down',0),('right',4),('up',8),('left',12)]:make(state,'walk-'+direction,{'down':'向下','right':'向右','up':'向上','left':'向左'}[direction]+('飞行' if unit=='owl' else '行走'),'maps',[(start+i,8 if unit=='owl' else 12) for i in range(4)],note='完整人物四相动作；地面左右近腿／远腿交替，飞枭用翼拍，核心损毁持续保留。')
  a=make(state,'escape','撤离至边缘','maps',[(12+i%4,8) for i in range(28)],note=f'同阵营仅剩机械时移动{u["stats"]["move"]}→{u["stats"]["move"]+3}；此处只演示撤离外观，具体合法路径见下方示意地图。')
  for i,row in enumerate(a['frames']):row['offset']=[-round(min(170,i*.8)),0];row['alpha']=0 if i>=212 else 1
  if unit=='cyclops' and state=='intact':
   a=make(state,'aura','本方开始 · 八邻格恢复5HP','maps',[(0,96)],24,note='8邻格含斜角，同阵营存活队友恢复5HP，自己不回血；不复活或修复部位。')
   a['reviewCompanions']=[{'path':P+'assets/ally-map.png','origin':[128+dx*32,116+dy*32],'size':[64,64],'anchor':[32,60],'flip':False} for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]]
   for i,row in enumerate(a['frames']):
    if 24<=i<76:
     for dx,dy in [(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)]:fx(row,'heal',[128+dx*32,104+dy*32],1-(i-24)/52)
   finalize(a)
  if engine:
   a=make(state,'canto','交锋后 · 再移动3距离','maps',[(4+i%4,8) for i in range(16)],0,note='仅本方主动交锋结束后额外3距离一次，不可再次攻击；引擎失效立即取消。')
   a['origin']=[96,116]
   for i,row in enumerate(a['frames']):row['offset']=[round(min(96,i*.8)),0];fx(row,'boost',[80+row['offset'][0],94],.65)
   finalize(a)
  if life:
   a=make(state,'regen','本方结束 · 本体回复6HP','battle',[(0,84)],24,note='本方回合结束一次，只回本体6HP，核心不回血；生命核失效停止。')
   for i,row in enumerate(a['frames']):
    if 24<=i<72:fx(row,'regen',[176,92],1-(i-24)/48)
   finalize(a)
   target_state='life-broken' if state=='intact' else 'both-broken';profile=next(p for p in profiles if p['id']==f'puppet-trio-{unit}-{state}-battle');target=next(p for p in profiles if p['id']==f'puppet-trio-{unit}-{target_state}-battle')
   alias=len(profile['newFrames']);profile['newFrames'][str(alias)]=target['newFrames']['0'];profile['reviewFrameSources'][str(alias)]=0;profile['reviewFrameLabels'][str(alias)]='生命核心耗尽，复苏后本体'
   a=make(state,'revive','归零复苏 · 回复24并消耗生命核','battle',[(6,28),(alias,76)],28,note='即时回复24，不计击败，生命核自毁；火核当前状态保留，后续追击仍可继续。')
   for i,row in enumerate(a['frames']):
    if i>=28:row['state_override']=target_state
    if 24<=i<80:fx(row,'revive',[176,106],1-(i-24)/56)
   # Reference atlas includes the extra cross-state column without borrowing anatomy.
   first=Image.open(R/profile['newFrames']['0'].removeprefix(P));out=Image.new('RGBA',(first.width*(alias+1),first.height))
   for j in range(alias+1):out.paste(first,(j*first.width,0))
   out.save(R/profile['sourceAtlas'].removeprefix(P));profile.update(sourceColumns=alias+1,sourceFrameCount=alias+1,sourceAtlasSize=list(out.size));finalize(a)
# Cross-state break previews for every currently active auxiliary part.
for unit,u in D['units'].items():
 for state in D['visuals']['states'][unit]:
  state_parts= {'eye':state=='intact'} if unit=='cyclops' else {'engine':state=='intact'} if unit=='owl' else {'fire':state in ['intact','life-broken'],'life':state in ['intact','fire-broken']}
  for part,on in state_parts.items():
   if not on:continue
   next_state='broken' if unit!='prometheus' else ('fire-broken' if part=='fire' else 'life-broken') if state=='intact' else 'both-broken'
   profile=next(p for p in profiles if p['id']==f'puppet-trio-{unit}-{state}-battle');target=next(p for p in profiles if p['id']==f'puppet-trio-{unit}-{next_state}-battle');alias=len(profile['newFrames']);profile['newFrames'][str(alias)]=target['newFrames']['0'];profile['reviewFrameSources'][str(alias)]=0;profile['reviewFrameLabels'][str(alias)]='对应核心破坏，持续外观'
   rows=[{'frame':0 if i<20 else alias,'offset':[0,0],'flip':True,'tint':.4 if 8<=i<20 and i%6<3 else 1,'effects':[]} for i in range(64)]
   for i,row in enumerate(rows):
    if i>=20:row['state_override']=next_state
    if 18<=i<40:row['effects']=[{'id':'trio-core-break','sprite':'trio-core-break','position':[176,96],'flip':False,'alpha':1-(i-18)/22}]
   actions.append({'id':f'puppet-trio-{unit}-{state}-break-{part}','key':'break-'+part,'unit':unit,'state':state,'name':next(p['name'] for p in u['parts'] if p['id']==part)+'破坏','profile':profile['id'],'context':'battle','frames':rows,'fps':60.0988,'duration':64/60.0988,'origin':[176,128],'viewport':[0,0,256,160],'closeCamera':{'offset':[-72,-108],'size':[144,112]},'contactTick':20,'neededFrames':[0,alias],'effectIds':['trio-core-break'],'missingFrames':[],'ready':True,'referenceLabel':'新增设计 · 形象基准（无原作）','newLabel':'原生像素设计','notes':'仅设计预览。核心破坏只扣本部位，无溢出；切换为独立绘制的对应损坏状态，不误删其它核心。'})
   first=Image.open(R/profile['newFrames']['0'].removeprefix(P));out=Image.new('RGBA',(first.width*(alias+1),first.height))
   for j in range(alias+1):out.paste(first,(j*first.width,0))
   out.save(R/profile['sourceAtlas'].removeprefix(P));profile.update(sourceColumns=alias+1,sourceFrameCount=alias+1,sourceAtlasSize=list(out.size))
extra={'profiles':profiles,'actions':actions,'effects':effects}
(R/'gallery-extension.js').write_text("'use strict';\n(()=>{const extra = "+json.dumps(extra,ensure_ascii=False,separators=(',',':'))+";\nwindow.PUPPET_TRIO_DATA=extra;const d=window.GALLERY_DATA;if(d){d.profiles.push(...extra.profiles);d.actions.push(...extra.actions);Object.assign(d.effects,extra.effects);d.summary.profiles=d.profiles.length;d.summary.actions=d.actions.length;d.summary.ready=d.actions.filter(a=>a.ready).length;d.summary.pending=d.actions.length-d.summary.ready;}})();\n")
(R/'action-effect-mapping.json').write_text(json.dumps({'status':'preview_only','mapping':[{'unit':a['unit'],'state':a['state'],'action':a['key'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'effects':a['effectIds'],'notes':a['notes']} for a in actions]},ensure_ascii=False,indent=2)+'\n')
# Recount images after reference atlases and teammate registration.
M['images']=[]
for p in sorted((R/'assets').glob('*.png')):
 im=Image.open(p);M['images'].append({'path':'assets/'+p.name,'pixels':list(im.size),'bytes':p.stat().st_size,'use':'preview-only sprite / bitmap FX / registration reference','quality':'Native pixels and complete alpha contour preserved.'})
(R/'asset-manifest.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'profiles':len(profiles),'actions':len(actions),'effects':len(effects)}))

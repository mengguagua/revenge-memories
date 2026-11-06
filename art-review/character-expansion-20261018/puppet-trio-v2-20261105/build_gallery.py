# coding: utf-8
from pathlib import Path
from PIL import Image
import json,shutil,subprocess
R=Path(__file__).resolve().parent;P=R.name+'/';M=json.loads((R/'asset-manifest.json').read_text());D=json.loads((R/'design.json').read_text());profiles=[];actions=[];effects={}
for key,f in M['effects'].items():effects['trio-'+key]={'path':P+f['path'],'frame_size':f['pixels'],'anchor':[f['pixels'][0]/2,f['pixels'][1]/2],'native_density':1}
hit=json.loads((R.parent/'water-monkey-v1-20261104/source/motion-v2-20261104/soldier-hit-reference.json').read_text())['frames']
state_names={'intact':'核心完整','broken':'核心破坏','fire-broken':'火核破坏','life-broken':'生命核破坏','both-broken':'双核破坏'}
for unit,u in D['units'].items():
 states=D['visuals']['states'][unit]
 for state in states:
  for scene in ['battle','maps']:
   group=f'{unit}-{state}-{scene}';entries=M['frames'][group];size=entries[0]['pixels'];battle=scene=='battle';pid='puppet-trio-'+group
   profiles.append({'id':pid,'actor':'puppet-trio-'+unit,'actorName':'敌方'+u['name'],'classId':'design-'+unit,'className':u['name']+'（'+state_names[state]+'）','context':'battle' if battle else 'tactical-walk','contextName':'战斗场景' if battle else '地图四向','side':'enemy','mappingStatus':'review_only_not_integrated','revision':'puppet-trio-v2-20261105','sourceAtlas':P+'assets/'+group+'-reference.png','sourceFrameSize':size,'sourceColumns':len(entries),'sourceFrameCount':len(entries),'sourceAtlasSize':[size[0]*len(entries),size[1]],'sourceOamCutoff':0,'flipOriginOffset':[0,0],'anchor':[size[0]/2,72 if not battle or unit=='cyclops' else 100],'outputFrameSize':[n*4 for n in size],'newFrames':{str(e['id']):P+e['path'] for e in entries},'reviewFrameSources':{str(e['id']):0 for e in entries},'reviewFrameLabels':{str(e['id']):'独立绘制 · 姿势'+str(e['id']+1) for e in entries},'mapping':P+'action-effect-mapping.json','links':[{'label':'三类数值与规则交互','href':P+'index.html?unit='+unit},{'label':'生图来源与提示词','href':P+'source/prompts.json'}]})
 def make(state,key,label,scene,segments,contact=None,companion=False,note=''):
  battle=scene=='battle';rows=[]
  for f,n in segments:rows.extend({'frame':f,'offset':[0,0],'flip':battle,'effects':[]} for i in range(n))
  a={'id':f'puppet-trio-{unit}-{state}-{key}','key':key,'unit':unit,'state':state,'name':state_names[state]+' · '+label,'profile':f'puppet-trio-{unit}-{state}-{scene}','context':'battle' if battle else 'tactical-walk','frames':rows,'fps':60.0988,'duration':len(rows)/60.0988,'origin':[176,128] if battle else [128,116],'viewport':[0,0,256,160],'closeCamera':{'offset':[-72,-108],'size':[144,112]},'contactTick':contact,'neededFrames':sorted({r['frame'] for r in rows}),'effectIds':[],'missingFrames':[],'ready':True,'referenceLabel':'新增设计 · 形象基准（无原作）','newLabel':'原生像素重绘 · 低饱和','notes':'仅美术与HTML规则预览，未接入游戏、未投放关卡。'+note}
  if companion:a['reviewCompanions']=[{'path':P+'assets/soldier-reference.png','origin':[64,128],'size':[80,64],'anchor':[40,64],'flip':True}]
  actions.append(a);return a
 def finalize(a):
  a['neededFrames']=sorted({r['frame'] for r in a['frames']});a['effectIds']=sorted({e['id'] for r in a['frames'] for e in r.get('effects',[])})
 def fx(row,name,pos,alpha=1,size=None,layer='front'):
  e={'id':'trio-'+name,'sprite':'trio-'+name,'position':pos,'flip':False,'alpha':alpha,'layer':layer}
  if size:e['size']=size
  row['effects'].append(e)
 for state in states:
  label=state_names[state];engine=unit=='owl' and state=='intact';fire=unit=='prometheus' and state in ['intact','life-broken'];life=unit=='prometheus' and state in ['intact','fire-broken']
  make(state,'idle','战斗待机','battle',[(0,120)],note=u['role'])
  a=make(state,'battle-walk','飞行移动' if unit=='owl' else '战斗行走','battle',[(i,10) for i in [1,0,2,0]*3]+[(0,12)])
  for i,row in enumerate(a['frames']):row['offset']=[-round(min(i,120)*.25),0]
  a=make(state,'attack',u['attack']['name']+(' · 1–2格魔法' if unit=='cyclops' else ' · 爬升俯冲爪击' if unit=='owl' else ' · 近距单次攻击'),'battle',[(0,126 if unit=='cyclops' else 208 if unit=='owl' else 172)],60 if unit=='cyclops' else 92 if unit=='owl' else 68,True,note=('爬升→高点收翼→俯冲→双爪命中→回位；引擎完整才有喷焰，破损仍能靠翼组俯冲。' if unit=='owl' else '单次结算；近战靠近、攻击并回位，独眼魔法原地施放。'))
  for i,row in enumerate(a['frames']):
   if unit=='cyclops':
    row['frame']=3 if 12<=i<36 else 4 if 36<=i<70 else 5 if 70<=i<96 else 0
    if 36<=i<60:fx(row,'violet-pulse',[round(154-(i-36)/24*90),114])
    if 60<=i<78:fx(row,'violet-hit',[64,114],1-(i-60)/18)
   elif unit=='owl':
    if 12<=i<50:
     t=(i-12)/38;row.update(frame=3,offset=[-round(33*t),-round(50*(1-(1-t)**1.5))])
     if engine and 16<=i<44:fx(row,'jet-climb',[176+row['offset'][0]+34,128+row['offset'][1]-17],.92,layer='back')
    elif 50<=i<62:row.update(frame=4,offset=[-33,-50])
    elif 62<=i<92:
     t=((i-62)/30)**(1.68 if engine else 1.23);row.update(frame=5,offset=[-33-round(45*t),-50+round(50*t)])
     if engine and 69<=i<91:fx(row,'jet-dive',[176+row['offset'][0]+32,128+row['offset'][1]-47],.9,layer='back')
    elif 92<=i<111:
     row.update(frame=6,offset=[-78,0]);fx(row,'talon-slash',[66,107],1-(i-92)/19,[45,48])
    elif 111<=i<144:
     t=(i-111)/33;row.update(frame=7,offset=[-78+round(31*t),-round(26*t)],flip=False)
    elif 144<=i<190:
     t=(i-144)/46;row.update(frame=[1,0,2,0][((i-144)//7)%4],offset=[-round(47*(1-t)),-round(26*(1-t))],flip=False)
   else:
    if 8<=i<48:row.update(frame=[1,0,2,0][((i-8)//9)%4],offset=[-round(73*(i-8)/40),0])
    elif 48<=i<68:row.update(frame=3,offset=[-73,0])
    elif 68<=i<96:row.update(frame=4,offset=[-73,0])
    elif 96<=i<118:row.update(frame=0,offset=[-73,0])
    elif 118<=i<164:row.update(frame=[1,0,2,0][((i-118)//9)%4],offset=[-round(73*(164-i)/46),0],flip=False)
   j=i-a['contactTick']
   if unit=='prometheus' and 0<=j<16:fx(row,'physical-wave',[64,111],1-j/16,[46,42])
   if 0<=j<len(hit):row.update(companionTint=hit[j].get('tint',1),companionShake=hit[j].get('shake',0))
  a['soundEvents']=[{'tick':a['contactTick'],'path':P+'assets/hit.ogg','volume':.35}];finalize(a)
  if unit=='prometheus':
   for key,name,magic in [('ranged','锚臂冲击 · 2–3格物理',False)]+([('fire','炽核灼流 · 长焰冲击',True)] if fire else []):
    a=make(state,key,name,'battle',[(0,158 if magic else 132)],68,True,note='火核供能：锚臂喷出白热长焰，推进、卷焰冲击、烟尘余烬；仍只在第69帧结算一次必中伤害。' if magic else '锚臂释放较宽的钢灰压力波，武器不离手。')
    for i,row in enumerate(a['frames']):
     if magic:
      row['frame']=3 if 10<=i<26 else 5 if 26<=i<117 else 0
      if 28<=i<44:
       w=35+round((i-28)*1.15);fx(row,'flame-ignite',[153-w/2,96],.7+(i-28)*.018,[w,round(w*30/57)],layer='back')
      elif 44<=i<68:
       w=54+round((i-44)*1.43);fx(row,'flame-stream',[153-w/2,96],1,[w,round(w*68/134)],layer='back')
      elif 68<=i<91:fx(row,'flame-crest',[153-71,91],1-(i-68)/78,layer='front')
      elif 91<=i<128:fx(row,'flame-embers',[85,93-round((i-91)*.13)],1-(i-91)/37,layer='front')
     else:
      row['frame']=3 if 10<=i<38 else 5 if 38<=i<87 else 0
      if 38<=i<68:fx(row,'physical-wave',[round(150-(i-38)/30*86),106],1,[44,44])
      if 68<=i<88:fx(row,'physical-wave',[64,109],1-(i-68)/20,[60,52])
     j=i-68
     if 0<=j<len(hit):row.update(companionTint=hit[j].get('tint',1),companionShake=hit[j].get('shake',0))
    a['soundEvents']=[{'tick':68,'path':P+'assets/hit.ogg','volume':.4}];finalize(a)
  a=make(state,'hit','普通受伤 · 士兵同姿势闪烁','battle',[(0,len(hit))],note='固定身体姿势、明暗闪烁、轻微位移与命中音。')
  for row,ref in zip(a['frames'],hit):row.update(tint=ref.get('tint',1),shake=ref.get('shake',0))
  a['soundEvents']=[{'tick':0,'path':P+'assets/hit.ogg','volume':.35}]
  if unit=='prometheus':
   a=make(state,'defeat','最终击败 · 原地爆炸','battle',[(0,112)],note='本体原地短暂过载，爆炸峰值时站姿本体消失；碎片与烟尘散尽。无倒地、无额外攻击或伤害。生命核有效时先走独立复苏动作。')
   a['disappearTick']=28
   for i,row in enumerate(a['frames']):
    if 8<=i<28:row['tint']=1.38 if (i//4)%2 else .68
    if i>=28:row['alpha']=0
    if 19<=i<28:fx(row,'blast-flash',[176,88],.55+(i-19)*.048)
    elif 28<=i<45:fx(row,'blast-peak',[176,85],1-(i-28)/60)
    elif 45<=i<71:fx(row,'blast-debris',[176,82],1-(i-45)/46)
    elif 71<=i<106:fx(row,'blast-smoke',[176,80-round((i-71)*.15)],.68*(1-(i-71)/35))
   a['soundEvents']=[{'tick':28,'path':P+'assets/hit.ogg','volume':.4}];finalize(a)
  else:
   a=make(state,'defeat','本体最终被击败','battle',[(0,12),(8 if unit=='owl' else 6,24),(9 if unit=='owl' else 7,48)],note='仅本体最终被击败时退场。')
   for i,row in enumerate(a['frames']):
    if i>=68:row['alpha']=max(0,1-(i-68)/15)
  idle=[16,17,18,19] if unit=='cyclops' else [0,1,2,3] if unit=='owl' else [0,2,0,2]
  a=make(state,'map-idle','地图待机 · 双侧同动' if unit=='cyclops' else '地图待机','maps',list(zip(idle,[14,8,14,8])),note='独眼使用独立的双侧同步待机姿势，双脚固定，无单边抽动。' if unit=='cyclops' else '地图原生2倍密度；飞枭翼拍，普罗米修斯地面待机。')
  a['referenceFrame']=idle[0]
  for direction,start in [('down',0),('right',4),('up',8),('left',12)]:
   a=make(state,'walk-'+direction,{'down':'向下','right':'向右','up':'向上','left':'向左'}[direction]+('飞行' if unit=='owl' else '行走'),'maps',[(start+i,8 if unit=='owl' else 12) for i in range(4)],note='向上全程为真背面，形象基准也使用背向姿势。' if direction=='up' else '四相移动；地面交替步态，飞枭双翼拍动。')
   a['referenceFrame']=start
  a=make(state,'escape','撤离至边缘','maps',[(12+i%4,8) for i in range(28)],note=f'同阵营仅剩机械时移动{u["stats"]["move"]}→{u["stats"]["move"]+3}；此处只演示撤离外观，具体合法路径见下方示意地图。')
  for i,row in enumerate(a['frames']):row['offset']=[-round(min(170,i*.8)),0];row['alpha']=0 if i>=212 else 1
  if unit=='cyclops':
   presets=[('aura','治疗 · 部分空格',[0,1,3,4,6,7],[0,1,3,6,7]),('aura-full','治疗 · 八名受伤枪兵',list(range(8)),list(range(8))),('aura-empty','治疗 · 空地无特效',[],[])] if state=='intact' else [('aura','核心破坏 · 无治疗',[0,1,3,4,6,7],[])]
   for key,label,occupied,healed in presets:
    a=make(state,key,label,'maps',[(16,96)],24 if healed else None,note='当前 F25 实机图块与敌军枪兵；只有在场且实际恢复HP的队友有治疗特效。空格、满血枪兵、独眼本体不出特效。')
    a.update(origin=[144,96],referenceFrame=16,reviewGround=P+'assets/healing-ground-f25.png',healLayout=key)
    a['healSlots']=[{'id':'ally'+str(i),'grid':[dx,dy],'origin':[144+dx*32,96+dy*32],'fxPosition':[144+dx*32,84+dy*32],'path':P+'assets/ally-map.png','size':[64,64],'anchor':[32,60],'flip':False} for i,(dx,dy) in enumerate([(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1)])]
    a['reviewCompanions']=[a['healSlots'][i] for i in occupied];a['healedSlots']=healed
    for i,row in enumerate(a['frames']):
     if 24<=i<76:
      for slot in healed:fx(row,'heal',a['healSlots'][slot]['fxPosition'],1-(i-24)/52,[24,24])
    finalize(a)
  if engine:
   a=make(state,'canto','交锋后 · 引擎加速3格','maps',[(4+i%4,8) for i in range(13)],None,note='短喷预热→尾喷拉长加速→收短熄火，整段移动恰为3格。核心破坏后不能使用。')
   a.update(origin=[94,116],referenceFrame=4)
   for i,row in enumerate(a['frames']):
    x=0 if i<12 else round(23*((i-12)/22)**2) if i<34 else 23+round((i-34)*67/50) if i<84 else 90+round(6*min(1,(i-84)/12))
    row['offset']=[x,0]
    if 8<=i<25:fx(row,'jet-small',[94+x-29,93],.88,layer='back')
    elif 25<=i<83:fx(row,'jet-main',[94+x-45,92],.96,layer='back')
    elif 83<=i<96:fx(row,'jet-small',[94+x-29,93],(96-i)/13,layer='back')
   finalize(a)
  if life:
   a=make(state,'regen','本方结束 · 本体回复6HP','battle',[(0,84)],24,note='本方回合结束一次，只回本体6HP，核心不回血；生命核失效停止。')
   for i,row in enumerate(a['frames']):
    if 24<=i<72:fx(row,'regen',[176,92],1-(i-24)/48)
   finalize(a)
   target_state='life-broken' if state=='intact' else 'both-broken';profile=next(p for p in profiles if p['id']==f'puppet-trio-{unit}-{state}-battle');target=next(p for p in profiles if p['id']==f'puppet-trio-{unit}-{target_state}-battle')
   alias=len(profile['newFrames']);profile['newFrames'][str(alias)]=target['newFrames']['0'];profile['reviewFrameSources'][str(alias)]=0;profile['reviewFrameLabels'][str(alias)]='生命核心耗尽，复苏后本体'
   a=make(state,'revive','归零复苏 · 回复24并消耗生命核','battle',[(0,28),(alias,76)],28,note='保持站姿复苏：即时回复24，生命核自毁；不播放倒地或最终爆炸，保留火核当前状态。')
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
   actions.append({'id':f'puppet-trio-{unit}-{state}-break-{part}','key':'break-'+part,'unit':unit,'state':state,'name':next(p['name'] for p in u['parts'] if p['id']==part)+'破坏','profile':profile['id'],'context':'battle','frames':rows,'fps':60.0988,'duration':64/60.0988,'origin':[176,128],'viewport':[0,0,256,160],'closeCamera':{'offset':[-72,-108],'size':[144,112]},'contactTick':20,'neededFrames':[0,alias],'effectIds':['trio-core-break'],'missingFrames':[],'ready':True,'referenceLabel':'新增设计 · 形象基准（无原作）','newLabel':'原生像素重绘 · 低饱和','notes':'仅设计预览。核心破坏只扣本部位，无溢出；切换为独立绘制的对应损坏状态，不误删其它核心。'})
   first=Image.open(R/profile['newFrames']['0'].removeprefix(P));out=Image.new('RGBA',(first.width*(alias+1),first.height))
   for j in range(alias+1):out.paste(first,(j*first.width,0))
   out.save(R/profile['sourceAtlas'].removeprefix(P));profile.update(sourceColumns=alias+1,sourceFrameCount=alias+1,sourceAtlasSize=list(out.size))
for profile in profiles:
 size=profile['sourceFrameSize'];count=profile['sourceColumns'];out=Image.new('RGBA',(size[0]*count,size[1]))
 for i in range(count):
  src=profile['newFrames'].get(str(i),profile['newFrames']['0']);out.paste(Image.open(R/src.removeprefix(P)),(i*size[0],0))
 out.save(R/profile['sourceAtlas'].removeprefix(P))
for a in actions:
 a.setdefault('referenceFrame',0)
 if a.get('reviewGround'):a['referenceLabel']='实机图块 · 形象基准'
extra={'profiles':profiles,'actions':actions,'effects':effects}
(R/'gallery-extension.js').write_text("'use strict';\n(()=>{const extra = "+json.dumps(extra,ensure_ascii=False,separators=(',',':'))+";\nwindow.PUPPET_TRIO_DATA=extra;const d=window.GALLERY_DATA;if(d){d.profiles.push(...extra.profiles);d.actions.push(...extra.actions);Object.assign(d.effects,extra.effects);d.summary.profiles=d.profiles.length;d.summary.actions=d.actions.length;d.summary.ready=d.actions.filter(a=>a.ready).length;d.summary.pending=d.actions.length-d.summary.ready;}})();\n")
(R/'action-effect-mapping.json').write_text(json.dumps({'status':'preview_v2_only','mapping':[{'unit':a['unit'],'state':a['state'],'action':a['key'],'frames':len(a['frames']),'contact_tick':a['contactTick'],'effects':a['effectIds'],'notes':a['notes']} for a in actions]},ensure_ascii=False,indent=2)+'\n')
# Recount images after reference atlases and teammate registration.
pngs=sorted((R/'assets').glob('*.png'))
optimizer=shutil.which('oxipng') or (str(f) if (f:=Path('/opt/homebrew/bin/oxipng')).is_file() else None)
if optimizer:subprocess.run([optimizer,'-o','2','--strip','safe','--quiet',*(str(p) for p in pngs)],check=True)
M['images']=[]
for p in pngs:
 im=Image.open(p)
 use=('F25 实机地图图块' if p.name=='healing-ground-f25.png' else '固定尺寸对照图集' if p.name.endswith('-reference.png') else '独立效果位图' if p.name.startswith('fx-') else '角色帧／实机单位参考')
 M['images'].append({'path':'assets/'+p.name,'pixels':list(im.size),'bytes':p.stat().st_size,'use':use,'quality':'保留原生像素与完整透明轮廓。' if p.stat().st_size<50000 else '保留完整图集或实机图块的原生像素与登记位置，未为压缩降分辨率。'})
(R/'asset-manifest.json').write_text(json.dumps(M,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'profiles':len(profiles),'actions':len(actions),'effects':len(effects)}))

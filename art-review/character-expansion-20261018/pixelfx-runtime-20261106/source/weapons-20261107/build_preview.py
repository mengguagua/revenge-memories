from pathlib import Path
from PIL import Image,ImageChops
import json,hashlib,math,bisect
ROOT=Path(__file__).resolve().parents[2];CAP=ROOT/'source/captures';OUT=ROOT/'assets/runtime'
data=json.loads((ROOT/'data.js').read_text().split(' = ',1)[1].rstrip(';\n'))
new_fx=json.loads((ROOT/'source/weapons-20261107/fx-manifest.json').read_text())['effects'];data['effects'].update(new_fx)
inventory=json.loads((ROOT/'asset-manifest.json').read_text());inventory=[e for e in inventory if not any(e['path'].startswith('assets/runtime/'+k) for k in ['archery','dash-strike']) and e['path'] not in ['assets/fx/arrow.png','assets/fx/slash.png']]
new_cases=[];checks=[]
def add(path,purpose):inventory.append({'path':str(path.relative_to(ROOT)),'purpose':purpose,'dimensions':list(Image.open(path).size),'bytes':path.stat().st_size})
for key in ['archery','dash-strike']:
 d=json.loads((CAP/key/'capture.json').read_text());times=[f['t'] for f in d['frames']];unique=[];seen={};timeline=[];raw_indices=[];tips=[];positions=[];bad=[];diff_count=0
 for n in range(math.ceil(d['duration']*60)+1):
  t=min(n/60,d['duration']);i=max(0,bisect.bisect_right(times,t)-1);f=d['frames'][i];p=CAP/key/f'{i:04d}.png';clean=CAP/key/'clean'/p.name;actor=CAP/key/'actor'/p.name
  parts=[p.read_bytes(),(clean if key=='archery' else actor).read_bytes()];h=hashlib.sha256(b''.join(parts)).digest()
  if h not in seen:seen[h]=len(unique);unique.append(i)
  timeline.append(seen[h]);raw_indices.append(i);positions.append(f['actor_position'])
  delta=ImageChops.difference(Image.open(p).convert('RGB'),Image.open(clean).convert('RGB'));box=delta.getbbox()
  if box:
   diff_count+=1
   if key=='dash-strike' or box[1]<0 or box[3]>128:bad.append(n)
  tips.append([box[2]-1,(box[1]+box[3]-1)//2] if box and key=='archery' else None)
 layers={}
 for layer in (['current','clean'] if key=='archery' else ['current','actor']):
  paths=[]
  for start in range(0,len(unique),16):
   ids=unique[start:start+16];im=Image.new('RGBA' if layer=='actor' else 'RGB',(2368,240*math.ceil(len(ids)/4)),(0,0,0,0) if layer=='actor' else (0,0,0))
   for j,i in enumerate(ids):
    p=CAP/key/(('' if layer=='current' else layer+'/')+f'{i:04d}.png');im.paste(Image.open(p),((j%4)*592,(j//4)*240))
   path=OUT/f'{key}-{layer}-{len(paths):02d}.png';im.save(path,optimize=True);paths.append(str(path.relative_to(ROOT)));add(path,'Actual Godot weapon comparison / '+layer)
  layers[layer]=paths
 contact=d['contact_time'];event=d['source']['event'];actor=d['source']['actor'];target=d['source']['target']
 c={'key':key,'title':'弓箭射击' if key=='archery' else '冲刺剑击','tag':'Arrow shot' if key=='archery' else 'Dash strike','effect':'hit','trigger':contact,'contact':contact,'duration':d['duration'],'flip':key=='dash-strike','alpha':.8 if key=='archery' else .9,'anchor':[d['target_origin'][0]+(10 if key=='dash-strike' else 0),122],
 'atlases':layers['current'],'atlasCols':4,'atlasFrames':16,'timeline':timeline,'uniqueFrames':len(unique),'sourceFrames':len(d['frames']),'nativeFps':d['source']['native_fps'],'contactTick':d['source']['contact_tick'],'variant':d['source']['variant'],'contactCalls':d['contact_calls'],
 'weaponKind':key,'description':str(actor['name_zh'])+' → '+str(target['name_zh']),'candidateLabel':'PixelFX 箭矢 · 气流尾迹' if key=='archery' else '真实角色残影 · 挥砍弧光',
 'treatment':'保留原拉弓与放箭动作，替换为 PixelFX 箭矢，补充气流尾迹与短促命中反馈。' if key=='archery' else '使用卡洛当前冲刺动作的真实轮廓制作残影，衔接 PixelFX 挥砍弧光与一次命中反馈。',
 'notice':f"原攻击仅命中一次，生命 {event['hp_before']} → {event['hp_after']}，伤害 {event['damage']}；人物、武器和结算保持原样。"}
 if key=='archery':
  c['cleanAtlases']=layers['clean'];c['arrowTips']=tips;c['extraEffects']=['arrow'];c['flightStart']=next(n/60 for n,p in enumerate(tips) if p is not None);c['actionTime']=c['flightStart']+.10
 else:
  c['actorAtlases']=layers['actor'];c['actorPositions']=positions;c['extraEffects']=['slash'];c['slashStart']=contact-.06;c['slashAnchor']=positions[min(len(positions)-1,math.floor(contact*60))];c['actionTime']=contact-.28
 new_cases.append(c);checks.append({'case':key,'current_clean_difference_frames':diff_count,'unexpected_render_difference_frames':bad,'contact_calls':d['contact_calls'],'unique_frames':len(unique),'gameplay_event':event})
 print(key,'unique',len(unique),'delivery',len(timeline),'new layers',[(k,len(v)) for k,v in layers.items()],'unexpected differences',bad)
data['cases']=new_cases+[c for c in data['cases'] if c['key'] not in ['archery','dash-strike']];data['defaultCase']='archery'
(ROOT/'data.js').write_text('window.PIXELFX_PREVIEW = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
for k,v in new_fx.items():add(ROOT/v['path'],'PixelFX native weapon effect')
(ROOT/'asset-manifest.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
(ROOT/'qa/weapons-capture-checks.json').write_text(json.dumps({'passed':all(not c['unexpected_render_difference_frames'] and c['contact_calls']==1 for c in checks),'cases':checks},ensure_ascii=False,indent=2))

from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math,bisect,shutil

ROOT=Path(__file__).resolve().parents[1]
CAP=ROOT/'source/captures'
OUT=ROOT/'assets/runtime'
OUT.mkdir(parents=True,exist_ok=True)
QA=ROOT/'qa';QA.mkdir(exist_ok=True)
FX=json.loads((ROOT/'assets/fx/manifest.json').read_text())
specs=[
 dict(key='hit',title='普通剑击',tag='命中反馈',effect='hit',delay=0,offset=[10,-22],height=16,flip=True,alpha=.95,description='艾琳普通剑击 → 水猴傀儡',treatment='命中处增加短促的米白火花与少量金属碎屑。',notice='本体生命 22 → 17；保留原有挥剑、受击闪烁与扣血节奏。'),
 dict(key='cannon-break',title='背炮破坏',tag='部件失效',effect='cannon',delay=20/60.0988,offset=[-9,-29],height=16,flip=True,alpha=.95,description='艾琳攻击背炮 → 水猴背炮失效',treatment='炮管断裂的一刻，增加向外散开的旧黄铜火花。',notice='演示前将背炮置于 1 / 10 耐久，沿现有规则破坏；本体保持 22 HP。'),
 dict(key='core-break',title='核心破坏',tag='部件失效',effect='core',delay=20/60.0988-.05,offset=[0,-25],height=0,flip=False,alpha=.9,description='艾琳攻击核心 → 伪泰坦防护核心失效',treatment='核心破裂时增加局部灰紫放电，随后自然熄灭。',notice='演示前将核心置于 1 / 16 耐久；本体保持 42 HP，原有双防加成与反伤停用。'),
 dict(key='water',title='水炮命中',tag='水花反馈',effect='water',delay=0,offset=[0,-8],height=0,flip=False,alpha=.9,description='水猴水炮 → 艾琳',treatment='保留原飞行水弹与命中动作，增加落点水冠、散落水滴和短波纹。',notice='生命 20 → 16，速度 −1；候选只补充视觉反馈，不增加攻击或状态。'),
]
data={'title':'PixelFX · 实机动画对照','scope':'当前 Godot 手机布局后台渲染；受控战斗样例，非 iPhone 真机录屏。','captureSize':[592,240],'crop':[191,0,256,240],'fps':60,'effects':FX['effects'],'cases':[]}
inventory=[]
def item(path,purpose):
 im=Image.open(path)
 inventory.append({'path':str(path.relative_to(ROOT)),'purpose':purpose,'dimensions':list(im.size),'bytes':path.stat().st_size})
def pose_frame(d,t):
 return max(0,bisect.bisect_right([r['t'] for r in d['frames']],t)-1)
for spec in specs:
 d=json.loads((CAP/spec['key']/'capture.json').read_text())
 unique=[];seen={};timeline=[]
 # Resample the recorded 120-Hz viewport to 60-Hz delivery, matching the original action ticks.
 for n in range(math.ceil(d['duration']*60)+1):
  t=min(n/60,d['duration']);i=pose_frame(d,t)
  p=CAP/spec['key']/f'{i:04d}.png'
  blob=p.read_bytes();h=hashlib.sha256(blob).digest()
  if h not in seen:
   seen[h]=len(unique);unique.append(p)
  timeline.append(seen[h])
 atlases=[];count=16;cols=4
 for start in range(0,len(unique),count):
  chunk=unique[start:start+count];sheet=Image.new('RGB',(592*cols,240*math.ceil(len(chunk)/cols)))
  for j,p in enumerate(chunk):sheet.paste(Image.open(p).convert('RGB'),((j%cols)*592,(j//cols)*240))
  path=OUT/f'{spec["key"]}-{len(atlases):02d}.png';sheet.save(path,optimize=True)
  atlases.append(str(path.relative_to(ROOT)));item(path,'Godot current animation atlas')
 contact=float(d['contact_time'])
 anchor=[round(d['target_origin'][0]+spec['offset'][0]),round(d['target_origin'][1]+spec['offset'][1]+spec['height'])]
 out={**spec,'duration':d['duration'],'contact':contact,'trigger':contact+spec['delay'],'anchor':anchor,'atlases':atlases,'atlasCols':cols,'atlasFrames':count,'timeline':timeline,'uniqueFrames':len(unique),'sourceFrames':len(d['frames']),'nativeFps':d['source']['native_fps'],'contactTick':d['source']['contact_tick'],'variant':d['source']['variant'],'contactCalls':d['contact_calls']}
 data['cases'].append(out)
 # Paired QA sample on the same captured underlying frame. No painted game content.
 t=out['trigger']+(.1 if spec['effect'] in ['water','core'] else .016)
 source=Image.open(CAP/spec['key']/f'{pose_frame(d,t):04d}.png').convert('RGBA')
 after=source.copy();fx=FX['effects'][spec['effect']];w,h=fx['frameSize'];f=min(fx['frames']-1,max(0,round((t-out['trigger'])*fx['fps'])))
 sprite=Image.open(ROOT/fx['path']).crop(((f%fx['columns'])*w,(f//fx['columns'])*h,(f%fx['columns']+1)*w,(f//fx['columns']+1)*h)).convert('RGBA')
 px,py=fx['pivot'];left=anchor[0]-px
 if spec['flip']:sprite=sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT);left=anchor[0]-(w-px)
 sprite.putalpha(sprite.getchannel('A').point(lambda a:round(a*spec['alpha'])))
 layer=Image.new('RGBA',after.size);layer.alpha_composite(sprite,(left,anchor[1]-py))
 # Battle effects must stay above the existing interface boundary.
 layer.paste((0,0,0,0),(0,128,592,240));after=Image.alpha_composite(after,layer)
 combined=Image.new('RGB',(1024,480),(12,20,28))
 combined.paste(source.crop((191,0,447,240)).resize((512,480),Image.Resampling.NEAREST),(0,0))
 combined.paste(after.crop((191,0,447,240)).resize((512,480),Image.Resampling.NEAREST),(512,0))
 combined.save(QA/(spec['key']+'-contact.png'),optimize=True)
 item(QA/(spec['key']+'-contact.png'),'comparison QA at 2× native pixels')
 print(spec['key'],len(unique),'unique',len(atlases),'atlases',len(timeline),'delivery frames', 'anchor',anchor)
(ROOT/'data.js').write_text('window.PIXELFX_PREVIEW = '+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';\n')
for p in (ROOT/'assets/fx').glob('*.png'):item(p,'PixelFX mobile-native effect atlas')
(ROOT/'asset-manifest.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
print('Preview assets',sum(x['bytes'] for x in inventory),'bytes; max image',max(x['bytes'] for x in inventory))

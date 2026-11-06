# coding: utf-8
"""Record approved-pixel fidelity, deployment boundaries and current runtime evidence."""
from pathlib import Path
from PIL import Image, ImageChops
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
import json,hashlib,html,re
ROOT=Path(__file__).resolve().parents[2];R=ROOT/'actual/reports/pseudo-titan-20261105';ART=ROOT/'art-review/character-expansion-20261018';REVIEW=ART/'pseudo-titan-v1-20261105'
checks=[]
def check(ok,label):
 checks.append({'passed':bool(ok),'label':label})
 if not ok:raise AssertionError(label)
def same_pixels(a,b):return a.size==b.size and a.tobytes()==b.tobytes()
def read(path):return json.loads(path.read_text())
atlas=Image.open(ROOT/'actual/assets/pseudo-titan-20261105/battle.png').convert('RGBA')
for state,offset in [('battle',0),('battle-broken',10)]:
 for i in range(10):
  source=Image.open(REVIEW/f'assets/{state}-{i:02}.png').convert('RGBA')
  check(same_pixels(source,atlas.crop(((offset+i)*96,0,(offset+i+1)*96,88))),f'Approved {state} pose{i} packed without changing pixels')
for group in ['maps','maps-broken']:
 atlas=Image.open(ROOT/f'actual/assets/pseudo-titan-20261105/{group}.png').convert('RGBA')
 for i in range(16):
  source=Image.open(REVIEW/f'assets/{group}-{i:02}.png').convert('RGBA')
  check(same_pixels(source,atlas.crop((i*64,0,(i+1)*64,64))),f'Approved V2 {group} pose{i} packed exactly')
 for i in range(4):
  a=atlas.crop(((4+i)*64,0,(5+i)*64,64)).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  b=atlas.crop(((12+i)*64,0,(13+i)*64,64))
  check(same_pixels(a,b),f'{group} left/right whole-pose mirror phase{i}')
for state,name in [('battle','portrait'),('battle-broken','portrait-broken')]:
 a=Image.open(REVIEW/f'assets/{state}-00.png').convert('RGBA').crop((20,24,76,88))
 check(same_pixels(a,Image.open(ROOT/f'actual/assets/pseudo-titan-20261105/{name}.png').convert('RGBA')),f'{name} native intact silhouette, no scaling')
art=read(ROOT/'actual/data/pseudo_titan_art.json')
for key,v in art['variants'].items():
 check(all(0<=row['frame']<20 for row in v['frames']),f'Runtime animation {key} only references approved atlas poses')
 check(all(not row.get('reviewCompanions') and not row.get('companionTint') and not row.get('companionShake') for row in v['frames']),f'Runtime {key} excludes review companions')
for state in ['intact','broken']:
 m=art['maps'][state]
 check(m['cycle_ticks']==[14,8,14,8] and m['native_cycle']==[0,1,2,1],state+' idle cadence exactly matches enemy spearman')
 check(60/m['native_density']-m['tile_origin'][1]==16,state+' native map foot anchor lands at tile bottom')
before=read(R/'before/actual/data/stages/F25.json');after=read(ROOT/'actual/data/stages/F25.json')
check(after['enemies'][:-1]==before['enemies'],'F25 previous15 enemies retain stats, identity, position and flags')
check({k:v for k,v in after.items() if k!='enemies'}=={k:v for k,v in before.items() if k!='enemies'},'F25 terrain, NPCs, objects, reinforcements, boss and goals unchanged')
check(after['enemies'][-1]['position']==[18,9] and len(after['enemies'])==16,'Only one approved elite added at [18,9]')
class Links(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.resources=[];self.history=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if a.get('id'):self.ids.append(a['id'])
  if tag=='a' and a.get('href'):self.links.append(a['href'])
  if tag in ['img','script','link']:
   if a.get('src') or a.get('href'):self.resources.append(a.get('src',a.get('href')))
  if tag=='details' and a.get('id')=='revision-history':self.history.append(a)
def parse(path):
 p=Links();p.feed(path.read_text());return p
old=parse(R/'before/art-review/character-expansion-20261018/index.html');new=parse(ART/'index.html')
check(set(old.ids)<=set(new.ids),'Every existing main-gallery anchor preserved')
check(set(old.links)<=set(new.links),'Every existing main-gallery link preserved')
check(len(new.ids)==len(set(new.ids)),'Main gallery IDs unique')
check(len(new.history)==1 and 'open' not in new.history[0],'One default-closed revision history')
for page in [REVIEW/'index.html']:
 p=parse(page)
 for link in p.links+p.resources:
  u=urlsplit(link)
  if u.scheme or link.startswith('#'):continue
  if 'pseudo-titan-20261105/index.html' in u.path:continue # Report built below.
  check((page.parent/unquote(u.path)).exists(),'Local preview resource resolves: '+link)
check('Math.min(180,ceil(ordinary*1.5))' in (REVIEW/'preview.js').read_text(),'HTML demo caps after mechanical multiplier')
check('user_accepted_runtime_integrated' in (REVIEW/'gallery-extension.js').read_text(),'Confirmed art is marked accepted in gallery')
check('id="pseudo-titan-runtime-20261105"' in (ART/'index.html').read_text(),'Integration record lives in revision history')
(R/'static-checks.json').write_text(json.dumps({'passed':True,'checks':len(checks),'labels':checks},ensure_ascii=False,indent=2)+'\n')
logic=read(R/'logic-checks.json');visual=read(R/'visual-checks.json');exp=read(R/'experience-regression/logic.json');js=read(R/'html-experience-checks.json');assets=read(R/'runtime-assets.json')
for d in [logic,visual,js]:assert d.get('passed',False)
assert not exp['errors']
# Lossless review PNGs retain background/portrait edges. Existing native PNGs are already small.
shots=visual['shots'];image_inventory=[]
for row in shots:
 p=R/row['file'];im=Image.open(p)
 image_inventory.append({'path':row['file'],'pixels':list(im.size),'bytes':p.stat().st_size,'use':'Offscreen runtime verification screenshot','quality':'Native resolution, lossless PNG; no resize or smoothing.'})
(R/'screenshots.json').write_text(json.dumps(image_inventory,ensure_ascii=False,indent=2)+'\n')
ledger=[]
for beforefile in sorted((R/'before').rglob('*')):
 if not beforefile.is_file():continue
 rel=beforefile.relative_to(R/'before');current=ROOT/rel
 if not current.exists():continue
 digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 ledger.append({'path':str(rel),'before':digest(beforefile),'after':digest(current),'changed':beforefile.read_bytes()!=current.read_bytes()})
(R/'changed-files.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
counts={'logic':logic['checks'],'experience_regression':exp['checks'],'runtime_ui':visual['checks'],'runtime_screenshots':len(shots),'approved_pixel_and_static':len(checks),'html_experience':js['checks'],'water_monkey_regression':59,'casualty_regression':read(R/'casualty-regression/logic.json')['checks']}
(R/'summary.json').write_text(json.dumps({'passed':True,'counts':counts,'device_updated':False,'background_guard':True,'scope':'Controlled actual-game F25 checkpoint, controller, combat, MAP, death, save/retry, retreat and EXP tests. No natural full-map balance playthrough or device installation.','combat_experience_cap':180,'mechanical_multiplier_before_cap':True},ensure_ascii=False,indent=2)+'\n')
casualty=read(R/'casualty-regression/logic.json');assert not casualty['errors']
intro=f'逻辑{logic["checks"]}项、经验回归{exp["checks"]}项、实际控制器／界面{visual["checks"]}项、像素与静态{len(checks)}项、HTML经验{js["checks"]}项通过；水猴既有59项、濒死流程{casualty["checks"]}项检查通过。'
readme=f'''# 伪泰坦傀儡与180经验接入（2026-11-05）\n\n已接入本地运行工程。{intro}\n\nF25新部署增加1只非首领伪泰坦，位于零起算[18,9]（第19列第10行）；原15名敌军及地形、首领、牢门、箱子、NPC和胜利目标逐项保持。旧的进行中F25不插入新敌人，新开战／重试启用。没有更新手机安装。\n\n等级5、生命42、力量12、技巧5、速度1、幸运0、基础物防4、魔防2、移动4。重臂锤击为1格物理，威力2加力量共14，负重0、基础命中80、武器必杀0。防护核心独立16耐久、物防3／魔防2；有效时本体物防14／魔防12，每次被直接攻击后固定反伤2HP，未命中、0伤和致命攻击也触发。攻击核心不反伤，不享受核心双防加成，不伤本体。核心击破立即去除双防加成与反伤，同次追击锁定已坏核心则取消，不转打本体。\n\n反伤可致死，保留原濒死头像留言、归零／退场及主角失败。MAP每次释放每个目标只触发一次并显示HP，毒与场景持续伤害不触发。仅剩机械傀儡时移动4→7，沿合法路径向最近可达边缘撤离，无新增涉水能力；不计击杀或击败经验，不阻挡原胜利目标。\n\n敌方经验基础价值70，等级5的V=98。全敌军单次战斗经验最终上限180；普通值不先按100截断，机械傀儡×1.5向上取整后再封顶。每跨100逐级抽取六项成长并学习法术，保留余数；80+180升2级余60，99+180升2级余79。满级20不继续抽成长，经验最多99。治疗、通关、训练及固定事件奖励金额保持。\n\n完整／破损共20个战斗姿势、两套各16个地图姿势逐像素对应已确认V2。左右四相交替、枪兵同频待机14/8/14/8、跑近锤击、原地闪烁、倒地和撤离均使用已确认素材。状态头像也区分核心破损。只打包运行需要的PNG，源图、被否决研究和演示陪演单位不入包。5张运行图最大32373字节，原生像素和透明边缘均无损保留。\n\n共{len(shots)}张运行截图由Cocoa后台防护＋离屏SubViewport生成，覆盖406×240与256×240，并检查文字／核心耐久条安全区。验证使用实际游戏状态与控制器配合受控参数，未进行完整自然通关、手机真机试玩或平衡承诺。\n\n[查看运行画面](index.html) · [逻辑](logic-checks.json) · [经验回归](experience-regression/logic.json) · [界面](visual-checks.json) · [像素与静态](static-checks.json) · [素材尺寸与字节](runtime-assets.json) · [修改前后哈希](changed-files.json)\n'''
(R/'README.md').write_text(readme)
titles={'01-f25-deployment':'F25实际投放','02-intact-status':'完整核心与双防14／12','03-core-choice':'本体／防护核心选择','04-body-preview':'攻击本体显示反伤提示','05-core-preview':'独立16耐久核心预览','06-broken-status':'破损头像与双防4／2','17-reflection-feedback':'反伤闪烁与HP反馈','18-exp180-two-levels':'180经验连续升级','19-mobile-intact-status':'窄屏完整状态','20-mobile-core-choice':'窄屏部位选择','21-mobile-core-preview':'窄屏核心预览','22-mobile-body-preview':'窄屏本体预览','23-mobile-exp180':'窄屏两级成长与余数60','24-mobile-map-reflection-preview':'MAP反伤与结算HP预告','25-mobile-map-reflection-hit':'MAP命中与单次反伤','26-mobile-reflection-casualty':'反伤归零后原有头像留言','27-mobile-reflection-fatal':'反伤退场与主角失败'}
cards=[]
for shot in shots:
 name=Path(shot['file']).stem;title=titles.get(name,name.replace('intact-melee-','完整·锤击第').replace('broken-melee-','破损·锤击第')+'帧')
 cards.append(f'<figure><a href="{shot["file"]}"><img src="{shot["file"]}" alt="{html.escape(title)}" width="{shot["size"][0]}" height="{shot["size"][1]}" loading="lazy"></a><figcaption>{html.escape(title)} · {shot["size"][0]}×{shot["size"][1]}</figcaption></figure>')
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>伪泰坦傀儡 · 运行接入验收</title><style>*{box-sizing:border-box}body{margin:0;background:#17242b;color:#e6efed;font:16px/1.8 system-ui,sans-serif}main{max-width:1320px;margin:auto;padding:28px 20px}h1{font-size:28px;line-height:1.5}h2{font-size:21px}a{color:#a6d9cd;text-underline-offset:4px}a:focus-visible{outline:none;box-shadow:0 0 0 5px #aadccc55;border-radius:5px}nav{display:flex;flex-wrap:wrap;gap:14px 24px}.panel{padding:22px 26px;background:#23333d;border-radius:13px;margin:20px 0}.shots{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,360px),1fr));gap:18px}figure{margin:0;padding:18px;background:#23333d;border-radius:12px;text-align:center}figure a{display:block}img{max-width:100%;height:auto;image-rendering:pixelated;display:block;margin:auto;background:#101b21}figcaption{margin-top:12px;color:#afc4c8}table{width:100%;border-collapse:collapse}td,th{text-align:center;padding:10px 16px;border-bottom:1px solid #52646b}summary{cursor:pointer;padding:14px}code{font-size:14px}footer{margin:26px 0;color:#b2c5c8}@media(max-width:600px){main{padding:18px 14px}.panel{padding:18px}h1{font-size:24px}}</style></head><body><main><nav><a href="../../../art-review/character-expansion-20261018/index.html#pseudo-titan-review">← 角色全动作对照</a><a href="../../../art-review/character-expansion-20261018/pseudo-titan-v1-20261105/index.html">核心与经验交互示例</a></nav><h1>伪泰坦傀儡 · 已接入运行工程</h1><p>2026-11-05 · 全敌军战斗经验最终上限180 · 没有更新手机安装</p><section class="panel"><h2>本次生效内容</h2><p>F25「潮狩军港」新部署新增1只，第19列第10行。旧战斗保持原编成，新开战／重试启用；首领、神教箱、牢门和原目标保留。只在第二章投放。</p><table><tr><th>等级／生命</th><th>力量／技巧／速度／幸运</th><th>基础双防／移动</th></tr><tr><td>5／42</td><td>12／5／1／0</td><td>4／2／4</td></tr></table><p>重臂锤击：1格物理、合计威力14、负重0、命中基础80、武器必杀0。核心16耐久、独立双防3／2；有效时本体双防14／12，被直接攻击后固定反伤2HP，未命中及致命攻击也触发。攻击核心无反伤、无溢出；破坏立即去除本体防护与反伤。完整／破损的待机、左右交替行走、跑近锤击、闪烁、倒地、撤离及状态头像均已接入。</p><p>机械傀儡经验×1.5后再统一封顶180；基础价值70，等级5价值98，实际经验按友方职业与等级计算。每满100逐级成长并保留余数：80＋180 → 升2级、剩余60。仅剩机械傀儡时移动4→7，沿合法路径撤离到最近可达边缘，无击败经验，不阻挡胜利。</p></section><section class="panel"><h2>验证结果与范围</h2><p>COUNTS</p><p>实际游戏状态、控制器和受控战斗参数；覆盖核心破坏、魔防、未命中反伤、双亡、主角失败、MAP、存档／重试、撤离及连续升级。截图通过不抢焦点的后台防护和离屏视口生成。未进行整关自然通关、手机安装或真机试玩。</p><nav><a href="logic-checks.json">核心逻辑</a><a href="experience-regression/logic.json">经验回归</a><a href="visual-checks.json">控制器／布局</a><a href="static-checks.json">像素与静态</a><a href="runtime-assets.json">素材尺寸／字节</a><a href="README.md">完整说明</a></nav></section><section class="shots">CARDS</section><footer>运行PNG均保留原生像素、透明边缘与已确认配色；演示陪演单位及原始研究图不打包。</footer></main></body></html>'''.replace('COUNTS',intro).replace('CARDS',''.join(cards))
(R/'index.html').write_text(page)
# Current README entry; previous historical deliveries remain intact.
p=ROOT/'actual/README.md';s=p.read_text();entry='2026-11-05 伪泰坦傀儡与180经验：F25新部署增加1只精英机械傀儡；防护核心16耐久，本体双防＋10、被直接攻击后固定反伤2HP，破坏立即停用。完整／破损已确认V2动作、部位选择、撤离、存档与重试均接入。全敌军战斗经验最终封顶180，机械傀儡倍率在封顶前计算，连续升级逐级成长并保留余数。'+intro+'[运行画面、数值与验证范围](reports/pseudo-titan-20261105/index.html)。未安装或更新iPhone。\n\n'
if '2026-11-05 伪泰坦傀儡与180经验：' in s:
 s=re.sub(r'2026-11-05 伪泰坦傀儡与180经验：[^\n]*\n\n',lambda m:entry,s,count=1)
else:
 pos=s.index('\n\n')+2;s=s[:pos]+entry+s[pos:]
p.write_text(s)
for row in ledger:
 if row['path']=='actual/README.md':row['after']=hashlib.sha256(p.read_bytes()).hexdigest();row['changed']=True
(R/'changed-files.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
# Check newly delivered report references after writing it.
for link in parse(R/'index.html').links+parse(R/'index.html').resources:
 u=urlsplit(link)
 if not u.scheme:assert (R/unquote(u.path)).exists(),link
print(json.dumps(counts,ensure_ascii=False))

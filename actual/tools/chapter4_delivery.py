#!/usr/bin/env python3
"""Evidence index, resource footprint and lossless screenshot delivery for chapter four."""
from pathlib import Path
import json,hashlib,html,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1];OUT=R/'reports/chapter4'
def read(p):return json.loads((R/p).read_text())
def save(p,v):(OUT/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
package=read('reports/chapter4/package-checks.json');checks=read('reports/chapter4/state-checks.json');hubs=read('reports/chapter4/hub-checks.json');play=read('reports/chapter4/play/round2.json');capital=read('reports/chapter4/play/round2-capital.json');visual=read('reports/chapter4/visual/captures.json');real=read('reports/chapter4/screenshots/captures.json')
assert all(d['passed'] for d in [checks,hubs,play,capital,visual,real,package])
assert len(play['battles'])==10 and all(b['outcome']=='victory' for b in play['battles'])
final=read('reports/chapter4/play/round2-chapter-end.json');assert final['flags']['chapter4_closed'] and final['flags']['D42_done'];assert 'celine' in final['parties']['celica']
images=[]
for folder in ['visual','screenshots']:
 for p in sorted((OUT/folder).glob('*.png')):
  before=Image.open(p).convert('RGBA').tobytes()
  subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
  im=Image.open(p);assert im.convert('RGBA').tobytes()==before
  images.append({'path':str(p.relative_to(R)),'width':im.width,'height':im.height,'bytes':p.stat().st_size,'purpose':'真实试玩存档视口' if folder=='screenshots' else '地图/据点/目标文字定向视口','lossless':True})
# No new bitmap art. Record the exact existing modules used, without recompressing originals.
assets=set(['assets/chapter2/chapter2-tiles.png'])
for code in ['M41','M42','M43','M44','F41','F42','F43','F44','S41','S42']:
 d=read('data/stages/'+code+'.json')
 for v in d.get('art_props',[]):assets.add(v['path'].removeprefix('res://'))
 for o in d['objects']:assets.add(o.get('sprite_path','res://assets/battle_tiles/modules/'+o['sprite']+'.png').removeprefix('res://'))
for room in read('data/chapter4_hubs.json')['rooms'].values():
 for item in room['scenery']:assets.add(item['sprite_path'].removeprefix('res://'))
assets.update(['assets/original/graphics/portraits/portrait_17.png','assets/party-0.7.0/17/hub.png','assets/party-0.7.0/17/map.png'])
records=[]
for name in sorted(assets):
 p=R/name;assert p.exists(),name
 im=Image.open(p);records.append({'path':name,'dimensions':list(im.size),'bytes':p.stat().st_size,'reuse':True,'quality_note':'原有图集/素材原尺寸复用；未重压缩既有资源'})
save('asset-footprint.json',records)
chain=['round1d','round1g','round1h','round1final']
summary={'passed':True,'version':'0.9.0','package_checks':len(package['checks']),'state_checks':len(checks['checks']),'hub_checks':len(hubs['checks']),'hub_inputs':hubs['inputs'],'round1':'修复后按真实检查点接续的十场存档链，保留失败记录','round1_chain':chain,'round2_battles':[{k:b[k] for k in ['code','final_turn','outcome']} for b in play['battles']],'round2_inputs':play['inputs'],'capital_final_sample':{'passed':capital['passed'],'inputs':capital['inputs'],'turn':capital['battles'][0]['final_turn']},'no_stat_edits':not play['stat_edits'],'no_forced_victories':not play['forced_victories'],'screenshots':images,'visual_errors':visual['errors']+real['errors'],'final_sources':final['flags']['treatment_sources'],'source_sha256':hashlib.sha256((R/'reports/chapter3/play/round1final-chapter-end.json').read_bytes()).hexdigest(),'remaining_scope':'第五章未开放；未重新制作或验收人物移动与战斗动画；图形仅后台SubViewport，非移动真机测试'}
pack=R/'dist/RevengeMemories-0.9.0-Chapter4-20261020.app/Contents/Resources/RevengeMemories.pck'
if pack.exists():summary['pck_sha256']=hashlib.sha256(pack.read_bytes()).hexdigest();summary['pck_bytes']=pack.stat().st_size
save('delivery-summary.json',summary)
rows=''.join('<tr><td>'+b['code']+'</td><td>'+str(b['final_turn'])+'</td><td>胜利</td></tr>' for b in play['battles'])
cards=''.join('<figure><a href="screenshots/'+Path(x['path']).name+'"><img loading="lazy" src="screenshots/'+Path(x['path']).name+'" alt="'+html.escape(x['description'])+'"></a><figcaption>'+html.escape(x['description'])+' · 真实存档</figcaption></figure>' for x in real['shots'])
(OUT/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第四章 · 实机交付</title><style>body{margin:0;background:#101b25;color:#e4e9e6;font:16px/1.75 system-ui,sans-serif}main{max-width:1280px;margin:auto;padding:36px 24px}h1{font-size:32px;color:#f3dcb1}a{color:#bdd9e8}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,500px),1fr));gap:24px}figure{margin:0;padding:12px;background:#1b2b35;border-radius:12px}img{display:block;width:100%;height:auto;image-rendering:pixelated}figcaption{padding:12px 8px}table{border-collapse:collapse;margin:24px 0}td,th{padding:8px 32px 8px 0;text-align:left;border-bottom:1px solid #3f535c}small{color:#adc2c9}</style><main><h1>故人的另一面</h1><p>第四章8场主线、2场支线，实际队伍从第三章接续。道路、建筑门前、井台与调节点使用一致的可通行规则。</p><p>第一轮边试玩边修复，沿真实存档链收束；第二轮从头十场连续通过，共'''+str(play['inputs'])+'''次键盘输入。没有改属性或强制胜利。后续王都城墙连通调整另复测通过。</p><p><a href="delivery-summary.json">检查摘要</a> · <a href="asset-footprint.json">复用素材尺寸与体积</a> · <a href="visual/captures.json">定向截图审计</a></p><table><tr><th>战场</th><th>第二轮结束回合</th><th>结果</th></tr>'''+rows+'''</table><section>'''+cards+'''</section><p><small>截图由Godot后台视口捕获。窗口在创建前即被禁止显示和激活；图片只做无损压缩。沿用现有动作，赛琳复用现有圣女身体与参考肖像。第五章尚未开放。</small></p></main></html>''')
print(json.dumps({'passed':True,'screenshots':len(images),'max_image_bytes':max(x['bytes'] for x in images),'package_checks':len(package['checks']),'state_checks':len(checks['checks']),'hub_checks':len(hubs['checks']),'round2_inputs':play['inputs']},ensure_ascii=False))

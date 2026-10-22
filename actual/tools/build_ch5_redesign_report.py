#!/usr/bin/env python3
"""seven current maps, immutable before images and verifiable ordinary-input evidence."""
from pathlib import Path
from PIL import Image
import json,html,hashlib,re,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/chapter5-redesign-20261022'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();e=html.escape
codes=['M51', 'M52', 'F51', 'F52', 'S51', 'J53', 'J54'];notes={m['code']:m for m in read(O/'design-notes.json')['maps']}
selection=read(O/'selected-play.json');rules=read(O/'rules-probe.json');capture=read(O/'screenshots/captures.json');package=read(O/'package-checks.json');end=read(O/'flow-continuation.json')
assert all(r['passed']for r in [rules,capture,package,end])
current={c:sha(R/f'data/stages/{c}.json')for c in codes};before=read(O/'baseline/hashes.json');unchanged={c:h for c,h in before.items()if c not in codes};assert all(sha(R/f'data/stages/{c}.json')==h for c,h in unchanged.items())
assert len(end['battles'])==7 and all(b['outcome']=='victory' and b['map_sha256']==current[b['code']] for b in end['battles']), 'Continuous evidence must match every final map'
plays={};attempts=[]
for code in codes:
 plays[code]=[]
 for label in selection[code]:
  path=O/f'play/{label}/{label}-play.json';record=read(path);b=next(b for b in record['battles']if b['code']==code)
  assert b['outcome']=='victory'and not b['failures']and b['entry_map_sha256']==b['map_sha256']==current[code]
  assert not record['stat_edits']and not record['forced_victories']
  victory=read(O/f'play/{label}/{label}-{code}-victory.json');formal=[u for u in victory['units']if u['id']in set(victory['parties']['alm']+victory['parties']['celica'])and not u.get('temporary')];npc=[u for u in victory['units']if u.get('quest_kind')]
  plays[code].append({'label':label,'turns':b['final_turn'],'inputs':b['key_inputs'],'source':str(path.relative_to(O)),'formal_count':len(formal),'formal_alive':sum(u['hp']>0 for u in formal),'formal_dying':[u['name_zh']for u in formal if u.get('dying')],'quest':b['quest'],'npc':[{'id':u['id'],'hp':u['hp'],'side':u['side']}for u in npc]})
for path in sorted((O/'play').glob('*/*-play.json')):
 r=read(path);attempts.append({'file':str(path.relative_to(O)),'passed':r['passed'],'battles':[{'code':b['code'],'outcome':b['outcome'],'turn':b['final_turn'],'failures':b['failures'],'current_map':b.get('entry_map_sha256')==b.get('map_sha256')==current.get(b['code'])}for b in r['battles']]})
images=[]
for path in list((O/'before').glob('*.png'))+list((O/'images').glob('*.png'))+list((O/'screenshots').glob('*.png')):
 pixels=Image.open(path).convert('RGBA').tobytes();subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(path)],check=True);im=Image.open(path);assert im.convert('RGBA').tobytes()==pixels
 images.append({'path':str(path.relative_to(O)),'size':list(im.size),'bytes':path.stat().st_size,'sha256':sha(path)})
summary={'passed':True,'revision':'0.10.9-ch5','maps':current,'unchanged_maps':unchanged,'plays':plays,'attempts':attempts,'images':images,'rules_checks':rules.get('check_count',0),'package':package,'flow_continuation':end,'layout_errors':capture['layout_errors'],'limitations':['Actual input uses isolated genuine development records, not live user saves. No unit attributes, random results or victories are forced.','Two per-map rounds do not mean two new-game playthroughs; continuous flow scope is recorded separately.','No iPhone installation. HTML link/script tests do not claim browser layout-engine verification.']}
(O/'delivery-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
css='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#10191f;color:#e9f0f2;font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1380px;margin:auto;padding:42px 30px 70px}h1{font-size:37px;line-height:1.3}h2{font-size:24px;margin:0 0 12px}h3{font-size:17px;margin:0 0 8px}p{color:#b8c9d1;margin:10px 0}.eyebrow{font-size:12px;letter-spacing:.14em;color:#a3cbbd}.tag{display:inline-block;padding:7px 13px;background:#354841;border-radius:8px;color:#d9ece3;font-size:13px}.links,.controls{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}a{color:#b4ddcc;text-underline-offset:4px}.links a,button{display:inline-flex;justify-content:center;align-items:center;min-height:44px;padding:11px 17px;border:0;border-radius:9px;background:#293b44;color:#dce9ed;font:inherit;font-size:14px;text-decoration:none;cursor:pointer}button[aria-pressed=true]{background:#36514e;box-shadow:inset 0 0 18px #9cd9be16,0 4px 18px #0004}a:focus-visible,button:focus-visible{outline:none;box-shadow:0 0 0 5px #a4d6c32c,0 0 24px #a4d6c32c}.panel{padding:24px;background:#1a2932;border-radius:16px;box-shadow:0 14px 38px #0002;margin-top:30px}.pair,.cards,.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}.cards{margin:20px 0}.cards article{padding:17px 20px;border-radius:10px;background:#22353e}figure{margin:0;min-width:0}figcaption{font-size:14px;padding:8px 2px 12px}.image{display:block;background:#22333d;border-radius:8px;overflow:hidden}.image img{width:100%;height:auto;display:block;image-rendering:pixelated}.small{font-size:12px;color:#9bb1bc}.board{position:relative;max-width:900px;margin:auto}.board img{display:block;width:100%;image-rendering:pixelated}.board svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}.overlay{display:none}.overlay.active{display:block}.legend{min-height:28px;font-size:13px}.shots{margin-top:20px}.note,details{padding:16px 19px;border-radius:10px;background:#24363f;margin:20px 0}summary{cursor:pointer}.stats{font-size:22px;color:#d5e9e0}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;padding:9px 12px;border-bottom:1px solid #ffffff0b}footer{font-size:12px;color:#8ca4b0;margin-top:28px}@media(max-width:800px){main{padding:24px 14px}.panel{padding:16px}.pair,.cards,.shots{grid-template-columns:1fr}h1{font-size:28px}}'''
body=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第五章七图 · 构图与战术重设计</title><style>'+css+'</style></head><body><main>','<div class="eyebrow">REVENGE MEMORIES / CHAPTER FIVE</div><h1>第五章七图 · 构图与战术重设计</h1><span class="tag">延续已确认方法 · 第五章全七图</span><p>王都内廷的伤兵后撤、三段登天桥、地下修复设施、日宫两翼门阵、旧书库、两军合流前庭与最终神座分别组织构图。街区、院落、道路和水域先形成真实关系，再安排部署与任务点；保留剧情、数值规则和现有动画。</p><nav class="links">']
for c in codes:body.append(f'<a href="#{c}">{c} · {e(notes[c]["name"])}</a>')
body+=['<a href="#verification">试玩与复查</a><a href="../../../art-review/battle-maps-20261021/index.html?map=M51#map-viewer">全部地图目录</a><a href="../../dist/RevengeMemories-Chapter5-Redesign-20261022.app">独立桌面包</a></nav>','<p class="small">前后地图均来自游戏原生渲染器；各图按任务重组空间，左右按各自完整边界展示，并非同像素比例的面积对比。点击原图可放大检查。</p>']
for code in codes:
 d=read(R/f'data/stages/{code}.json');old=read(O/f'baseline/{code}.json');n=notes[code];im=Image.open(O/f'images/{code}.png');w,h=im.size
 body.append(f'<section class="panel" id="{code}"><div class="eyebrow">{code} / {old["map"]["width"]}×{old["map"]["height"]} → {d["map"]["width"]}×{d["map"]["height"]}</div><h2>{e(n["title"])}</h2><p>{e(n["composition"])}</p><div class="pair">')
 for path,title in [(f'before/{code}.png','修改前 · 前一轮版本'),(f'images/{code}.png','重设计后 · 当前Godot场景')]:body.append(f'<figure><figcaption>{title}</figcaption><a class="image" href="{path}" target="_blank"><img src="{path}" loading="lazy" alt="{code} {title}"></a></figure>')
 body.append(f'</div><div class="cards"><article><h3>主路线</h3><p>{e(n["main_route"])}</p></article><article><h3>侧路与取舍</h3><p>{e(n["side_route"])}</p><p>{e(n["tradeoff"])}</p></article></div><details><summary>查看路线、部署与任务标注</summary><div class="controls">')
 for mode,title in [('plain','纯场景'),('routes','道路与支路'),('actors','部署与任务')]:body.append(f'<button data-map="{code}" data-layer="{mode}" aria-pressed="{str(mode=="plain").lower()}">{title}</button>')
 body.append(f'</div><div class="board"><img src="images/{code}.png" alt="{code}地形说明"><svg viewBox="0 0 {w} {h}" aria-hidden="true"><g class="overlay" data-map="{code}" data-overlay="routes">')
 routes=n.get('routes',[])[:4]

 for i,route in enumerate(routes):
  points=route.get('waypoints',[]);color=['#ce9c4c','#67bed1','#a6b887','#ad91c7','#53d1df','#cfa0ee'][i%6]
  coords=' '.join(f'{40+p[0]*16},{40+p[1]*16}'for p in points)
  body.append(f'<polyline points="{coords}" fill="none" stroke="#10202a99" stroke-width="7" stroke-linejoin="round"/><polyline points="{coords}" fill="none" stroke="{color}" stroke-width="3.5" stroke-linejoin="round"/>')
 body.append(f'</g><g class="overlay" data-map="{code}" data-overlay="actors">')
 for group,color in [(d['player_positions'],'#3872ca'),([u['position']for u in d['enemies']],'#bd4756'),([u['position']for u in d['npc_units']],'#d3af4a'),([o['position']for o in d['objects']],'#46976e'),([d['exit']],'#a784cc')]:
  for p in group:body.append(f'<circle cx="{40+p[0]*16}" cy="{40+p[1]*16}" r="6" fill="{color}" stroke="#eee" stroke-width="1.3"/>')
 body.append('</g></svg></div><p class="legend">蓝：候选部署；红：守军；金：剧情友军；绿：交互；紫：出口。路线仅为本页解释，不加入实机画面。实际通行以游戏地形为准。</p></details><div class="cards">')
 for i,p in enumerate(plays[code]):
  body.append(f'<article><h3>第{i+1}轮 · 实际输入复测</h3><div class="stats">第{p["turns"]}回合完成</div><p>结算时正式队员 {p["formal_alive"]}/{p["formal_count"]} 存活；{("濒死："+"、".join(p["formal_dying"])) if p["formal_dying"] else "无人濒死"}。</p><p class="small">{p["inputs"]:,}次按键，含出入场与战后操作。<a href="{p["source"]}">原始记录</a></p></article>')
 body.append('</div><div class="shots">')
 for shot in capture['shots']:
  if shot['stage']!=code:continue
  path='screenshots/'+Path(shot['path']).name;title=shot.get('title',shot['name']);body.append(f'<figure><a class="image" href="{path}" target="_blank"><img src="{path}" loading="lazy" alt="{e(title)}"></a><figcaption>{e(title)} · 第{shot["turn"]}回合</figcaption></figure>')
 body.append('</div></section>')
body+=['<section class="panel" id="verification"><h2>试玩与复查</h2><p>七图完成两轮逐关实际输入复测，检查战后据点、救援、工班修复、门阵控制和主线接续。'+e(end['description'])+'</p><div class="note"><strong>复查后的修正</strong><p>'+e(read(O/'review-notes.json')['summary'])+'</p></div>',f'<p>{rules.get("check_count",0)}项独立规则、连通与保存检查通过；{len(capture["shots"])}张实机视口文字安全区检查无错误。前四章33张地图（含已确认M41）保持原样，战斗规则与人物动画沿用；附带修复目标失效时的战斗预览报错。</p>','<details><summary>原始尝试、失败记录与验证范围</summary><p>两轮逐关检查使用真实开发记录的隔离副本；测试程序通过普通按键驱动实际游戏，完成移动、战斗、交互和结算，没有修改属性、随机结果或强制胜利。表内回合数受路线、命中和伤情影响，不代表固定难度。</p><p>'+e(read(O/'review-notes.json').get('attempts_note','早期尝试与修正记录保留，最终选用记录均对应当前地图。'))+'</p><p>未重新安装手机包；HTML资源与脚本检查不等同浏览器布局验收。</p><ul>']

for a in attempts:body.append(f'<li><a href="{a["file"]}">{e(a["file"].split("/")[-1])}</a>：'+ '、'.join(f'{b["code"]} {"通过" if b["outcome"]=="victory" and not b["failures"] else "未完成／失败"}'for b in a['battles'])+'</li>')
body+=['</ul></details><nav class="links"><a href="delivery-summary.json">完整交付记录</a><a href="rules-probe.json">独立规则检查</a><a href="flow-continuation.json">主线接续记录</a><a href="document-sync.json">流程文档同步</a><a href="runtime-log-review.json">运行日志复核</a><a href="visual-play-review.json">实机画面目检</a><a href="invariants-audit.json">剧情与其他地图不变量</a></nav></section><footer>第五章地图专项 · 2026-10-22 · 原生像素材质、专用书库陈设与现有动画。<a href="../m41-redesign-20261022/index.html">已确认的M41样板</a></footer>']
js='''function selectLayer(code,mode){document.querySelectorAll('button[data-map="'+code+'"]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.layer===mode)));document.querySelectorAll('.overlay[data-map="'+code+'"]').forEach(g=>g.classList.toggle('active',g.dataset.overlay===mode));}document.querySelectorAll('button[data-layer]').forEach(b=>b.addEventListener('click',()=>selectLayer(b.dataset.map,b.dataset.layer)));'''
body.append('<script>'+js+'</script></main></body></html>');(O/'index.html').write_text('\n'.join(body));(O/'comparison-controls.js').write_text(js+'\n');print(json.dumps({'passed':True,'maps':7,'shots':len(capture['shots']),'images':len(images),'unchanged_maps':len(unchanged)},ensure_ascii=False))

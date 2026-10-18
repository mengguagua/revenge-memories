#!/usr/bin/env python3
"""Inventory reused runtime images and build a clearly sourced local review gallery."""
from pathlib import Path
import json, hashlib, html, subprocess
from PIL import Image
R=Path(__file__).resolve().parents[1]; O=R/'reports/chapter3'
def read(p):return json.loads((R/p).read_text())
def write(p,data):(R/p).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def optimize(path):subprocess.run(['/opt/homebrew/bin/oxipng','-o','2','--quiet',str(path)],check=True)
codes=['M31','M32','M33','F31','F32','F33','S31','S32']; paths=set();maps=[]
for code in codes:
    d=read('data/stages/'+code+'.json');paths.add(d['art_atlas']);w=d['map']['width'];h=d['map']['height']
    assert all(len(layer)==h and all(len(row)==w for row in layer) for layer in d['art_layers'])
    for p in d.get('art_props',[]):paths.add(p['path'])
    nature={s['key']:s for s in read('assets/nature/nature.json')['sprites']}
    for p in d['natural_props']:paths.add(nature[p['key']]['path'])
    for o in d['objects']:
        if o['kind'] not in ['visit','control']:paths.add(o.get('sprite_path','res://assets/battle_tiles/modules/'+o['sprite']+'.png'))
        for key in ['open_sprite_path','sprite_path']:
            if key in o:paths.add(o[key])
        if o['kind']=='door':paths.add('res://assets/battle_tiles/modules/open_jail.png')
    for u in d['npc_units']:
        if 'sprite_path' in u:paths.add(u['sprite_path'])
    maps.append({'code':code,'name':d['name_zh'],'tiles':[w,h],'enemies':len(d['enemies']),'reinforcements':len(d['reinforcements']),'notes':d['visual_notes']})
for room in read('data/chapter3_hubs.json')['rooms'].values():
    for p in room['scenery']:paths.add(p['sprite_path'])
    for obj in room['objects']:
        if obj['sprite']!='actor':paths.add('res://assets/battle_tiles/modules/'+obj['sprite']+'.png')
paths.add('res://assets/original/graphics/portraits/portrait_41.png')
assets=[]
for ref in sorted(paths):
    p=R/ref.removeprefix('res://');assert p.exists(),ref
    im=Image.open(p)
    assets.append({'path':ref,'purpose':'existing native atlas/module/portrait reused without stretch or alteration','dimensions':list(im.size),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
write('reports/chapter3/reused-assets.json',assets)

captures=read('reports/chapter3/screenshots/captures.json');assert captures['passed']
final_shots=[]
for s in captures['shots']:
    p=R/s['path'].removeprefix('res://');optimize(p)
    im=Image.open(p);scaled=p.with_stem(p.stem+'-3x');im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(scaled);optimize(scaled)
    final_shots.append({**s,'original_dimensions':list(im.size),'original_bytes':p.stat().st_size,'display_path':'res://'+str(scaled.relative_to(R)),'display_dimensions':[im.width*3,im.height*3],'display_bytes':scaled.stat().st_size})
write('reports/chapter3/screenshots/delivery-images.json',final_shots)
# Successful continuous chain across genuine pre/post battle checkpoints.
chain=[('round1b',['M31']),('round1c',['F31','F32']),('round1final',['S32','F33','M32','S31','M33'])]
first=[]
for attempt,wanted in chain:
    record=read('reports/chapter3/play/'+attempt+'.json')
    for b in record['battles']:
        if b['code'] in wanted:
            assert b['outcome']=='victory'
            first.append({'code':b['code'],'turn':b['final_turn'],'source':'play/'+attempt+'.json','stat_edits':record['stat_edits'],'forced_victories':record['forced_victories']})
assert len(first)==8
second=[]
for name in ['M31','M32','F33']:
    prefix='round2-' if name=='M31' else 'round2final-'
    record=read('reports/chapter3/play/'+prefix+name+'.json');assert record['passed']
    second.append({'code':name,'turn':record['battles'][0]['final_turn'],'inputs':record['inputs'],'source':'play/'+prefix+name+'.json'})
state=read('reports/chapter3/state-checks.json');hubs=read('reports/chapter3/round2-hub-checks.json');visual=read('reports/chapter3/visual/captures.json')
final_save=read('reports/chapter3/play/round1final-chapter-end.json')
assert state['passed'] and hubs['passed'] and visual['passed'] and final_save['flags']['chapter3_complete']
summary={'version':'0.8.0','passed':True,'chapter':3,'main_battles':6,'side_battles':2,'rooms':9,'first_round':first,'second_round':second,'state_checks':len(state['checks']),'hub_checks':len(hubs['checks']),'hub_inputs':hubs['inputs'],'visual_fixture_shots':len(visual['shots']),'real_play_shots':len(final_shots),'layout_errors':visual['errors']+captures['errors'],'source_checkpoint_sha256':hashlib.sha256((R/'reports/chapter2/play/natural-chapter-end-save.json').read_bytes()).hexdigest(),'real_final_checkpoint':'play/round1final-chapter-end.json','reused_runtime_images':len(assets),'maps':maps,'known_limitations':['Play uses scripted actual keyboard/controller input and the original combat rules, not human playtesting or every tactical strategy.','The authentic old chapter2 checkpoint predates the injury system and is migrated in test copies; original file is untouched.','First-round repairs resume genuine checkpoints; abandoned and superseded attempts remain in play/.','Offscreen capture processes still report ObjectDB/resource cleanup warnings on exit.','Movement and combat animations are reused; no animation art or timing changes were made.','Chapter four content is not implemented.'],'fixed_issues':['Unmarked cobble damage inherited from reference terrain category 16.','Fast confirmation could outrun result settlement and return to the result page.','Prison geometry now has visible rails, a real southern gate, and matching opened tiles.','Correct silver/holy shield IDs and Noya class-compatible starter focus.','Third-chapter room module paths and native ground material names.','Real west gate, clear boarding exit, visible continuous transport road and route-specific city entrances.']}
write('reports/chapter3/delivery-summary.json',summary)
cards=[]
for s in final_shots:
    p=s['display_path'].removeprefix('res://reports/chapter3/')
    cards.append(f'<figure><img src="{html.escape(p)}" alt="{html.escape(s["description"])}"><figcaption>{html.escape(s["description"])}<small>真实试玩存档 · {s["stage"]} · 第{s["turn"]}回合 · 后台 Godot 视口</small></figcaption></figure>')
rows=''.join(f'<tr><td>{x["code"]}</td><td>{x["turn"]}</td><td><a href="{x["source"]}">实际输入记录</a></td></tr>' for x in first)
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>第三章 · 另一种胜利 · 实机截图</title><style>
body{margin:0;background:#0c181c;color:#e3e5de;font:16px/1.75 system-ui,sans-serif}main{max-width:1100px;margin:auto;padding:36px 22px}h1{font-size:30px;color:#ead7a7}p{max-width:850px;color:#c3ceca}figure{margin:28px 0;background:#16272c;border-radius:10px;overflow:hidden}img{display:block;width:100%;image-rendering:pixelated}figcaption{padding:16px 22px}small{display:block;color:#95aaa8}a{color:#9ed1ca}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:10px 15px;border-bottom:1px solid #30454a}details{margin:22px 0}summary{cursor:pointer;color:#ead7a7}</style><main><h1>第三章 · 另一种胜利</h1>
<p>0.8.0 · 西街与码头脱围、两路调查、两条救援支线、沿海营站会谈。以下8张来自真实按键试玩存档的游戏视口；保留当前人物动画与实际伤情，没有改属性或强制判胜。</p>
<p>第一轮走通8场，修复后从真实检查点续接；第二轮重玩西街、截运与提炼院，并检查营站交接、共享救治和标题续玩。另有33张明确标记的地图/据点视觉夹具，未把它们算作自然试玩。</p>'''+''.join(cards)+f'<details><summary>通关记录与验证范围</summary><table><tr><th>关卡</th><th>首轮胜利回合</th><th>证据</th></tr>{rows}</table><p><a href="delivery-summary.json">验收汇总</a> · <a href="reused-assets.json">素材尺寸与实际大小</a> · <a href="visual/captures.json">视觉夹具记录</a> · <a href="state-checks.json">规则与存档检查</a> · <a href="round2-hub-checks.json">第二轮据点检查</a></p><p>后台捕获退出时仍有资源引用清理警告。本次未改人物移动与战斗动画，也未实现第四章。</p></details></main></html>'
(O/'index.html').write_text(page)
print(json.dumps({'passed':summary['passed'],'maps':len(maps),'assets':len(assets),'real_shots':len(final_shots),'max_screenshot_bytes':max(s['display_bytes'] for s in final_shots)},ensure_ascii=False))

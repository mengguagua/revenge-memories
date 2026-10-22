#!/usr/bin/env python3
"""Publish map comparisons and explicitly separated play/fixture evidence."""
from pathlib import Path
from PIL import Image
import hashlib,html,json,shutil,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/map-polish-late-20261022';G=R.parent/'art-review/battle-maps-20261021'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=read(O/'selected-playthroughs.json');capture=read(O/'screenshots/captures.json')
geometry=read(O/'geometry.json');state=read(O/'state.json');package=read(O/'package-checks.json')
fixtures=[read(O/f'fixtures/chapter{n}-state-checks.json') for n in [3,4,5]]
assert all(d['passed']for d in [capture,geometry,state,package]+fixtures)
codes=sorted(read(O/'codes.json'),key=lambda c:read(R/f'data/stages/{c}.json')['id'])
assert set(selected)==set(codes)
maps=[];attempts=[];assets=[];inputs=0
(O/'after').mkdir(exist_ok=True)
for c in codes:
 d=read(R/f'data/stages/{c}.json');label=selected[c];p=O/f'play/{label}/{label}-play.json';report=read(p)
 b=next(b for b in report['battles']if b['code']==c)
 assert b['outcome']=='victory'and not b['failures']and not report['stat_edits']and not report['forced_victories']
 assert b['entry_map_sha256']==b['map_sha256']==sha(R/f'data/stages/{c}.json'),c
 assert b.get('return_view')=='world'if c!='J54'else b.get('ending_done'),c
 inputs+=b['key_inputs'];shutil.copy2(G/f'images/{c}.png',O/f'after/{c}.png')
 maps.append({'code':c,'chapter':d['chapter'],'name':d['name_zh'],'size':[d['map']['width'],d['map']['height']],'notes':d['tactical_notes'],'goal':d['goal'],'turn':b['final_turn'],'inputs':b['key_inputs'],'quest':b['quest'],'map_sha256':b['map_sha256'],'source':str(p.relative_to(O)),'result':b['outcome'],'return_view':b.get('return_view','ending'),'ending_done':b.get('ending_done',False)})
for p in sorted((O/'play').glob('*/*-play.json')):
 d=read(p)
 if d.get('entry_only'):continue
 attempts.append({'label':p.parent.name,'source':str(p.relative_to(O)),'passed':d['passed'],'battles':[{'code':b['code'],'outcome':b['outcome'],'turn':b['final_turn'],'failures':b['failures']}for b in d['battles']]})
for folder in ['before','after','screenshots']:
 for p in sorted((O/folder).glob('*.png')):
  raw=Image.open(p).convert('RGBA').tobytes();subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
  im=Image.open(p);assert im.convert('RGBA').tobytes()==raw
  assets.append({'file':str(p.relative_to(O)),'purpose':folder,'size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'compression':'lossless oxipng'})
preserved={c:sha(R/f'data/stages/{c}.json')==h for c,h in read(O/'baseline/hashes.json').items()if c not in codes}
assert all(preserved.values())
all_battles=[b for a in attempts for b in a['battles']]
summary={'passed':True,'date':'2026-10-22','map_revision':'0.10.3','maps':maps,'map_count':len(maps),'real_key_inputs_final_round':inputs,'screenshots':len(capture['shots']),'checks':{'geometry':geometry['checks'],'runtime_reachability_and_saves':state['checks'],'chapter_contract_fixtures':sum(len(f['checks'])for f in fixtures),'exported_app':package['checks'],'runtime_text_layout_errors':len(capture['layout_errors'])},'two_rounds':{'first':'Iteration play on all25 scenes; F43 escort loss retained, then normal input escort-first retry won. First-round art was still under review.','second':'All25 finalized maps reentered and won with unchanged map hashes from entry through result; ordinary post-battle hubs returned to world, J54 ending completed.'},'attempt_count':len(all_battles),'winning_attempts':sum(b['outcome']=='victory'and not b['failures']for b in all_battles),'attempts':attempts,'preserved_first_two_chapters':preserved,'source_saves_modified':False,'new_compatibility_maps':False,'animation_changes_by_this_task':False,'assets':assets,'limitations':['按真实开发部署记录逐关重入与通关，未宣称从新游戏连续重跑全部五章。','剧情判定fixture与实际输入试玩分开记录，fixture的状态安排不计为实机通关。','未重新导出或安装iPhone包。','未完成浏览器布局引擎验收；页面数据交互检查与Godot实际视口检查分别记录。']}
summary['runtime_asset_reviews']=['chapter3/assets.json','chapter4/asset-review.json','chapter5/asset-checks.json']
summary['environment_notes']=['Initial exported probe lacked an explicit writable log path and failed under the filesystem sandbox; the identical app passed all510 checks with /private/tmp log output.','Graphical capture completed all55 jobs with no layout errors; process teardown still reported12 ObjectDB references and3 resources, as in the existing capture helper.','Headless editor import completed; user editor-settings write was denied outside the workspace.']
summary['desktop_app']={'path':'dist/RevengeMemories-LateMaps-20261022.app','program_version':package['version'],'pck_sha256':sha(R/'dist/RevengeMemories-LateMaps-20261022.app/Contents/Resources/RevengeMemories.pck')}
(O/'delivery-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
e=html.escape
css='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#10171c;color:#e7eeee;font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1500px;margin:auto;padding:38px 28px 64px}h1{font-size:34px;line-height:1.4;margin:6px 0 18px}h2{font-size:22px;margin:0}h3{font-size:16px;margin:0}p{color:#adbdc5;max-width:1100px}a{color:#aad4c6;text-underline-offset:4px}.eyebrow{font-size:12px;letter-spacing:.13em;color:#aad4c6}.pills,nav{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}.pills span,nav a{background:#25363f;padding:10px 16px;border-radius:9px}nav a{text-decoration:none;display:flex;align-items:center;justify-content:center;min-height:44px}a:focus-visible{outline:none;box-shadow:0 0 0 5px #a8d6c82b,0 0 24px #a8d6c82b}article{padding:22px;margin-top:24px;background:#1a252d;border-radius:15px;box-shadow:0 12px 34px #0003;scroll-margin-top:20px}.head{display:flex;gap:18px;justify-content:space-between;align-items:center;margin-bottom:18px}.head small,.fine{font-size:12px;color:#98afb9}.pair,.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}figure{margin:0;min-width:0}figcaption{padding:0 4px 10px;color:#c6d5d4;font-size:13px}.picture{display:block;background:#26353b;border-radius:9px;overflow:hidden}.picture img{width:100%;height:auto;display:block;image-rendering:pixelated}.notes{display:grid;grid-template-columns:1.4fr 1fr;gap:24px;margin-top:18px}ul{padding-left:20px;color:#b9cad0;font-size:13px}li+li{margin-top:7px}.shots{margin-top:18px}.shots figcaption{padding-top:10px}details{margin-top:18px}summary{cursor:pointer;padding:12px 16px;background:#2b3d46;border-radius:8px}.goal{padding:14px 17px;background:#a8d6c80a;border-radius:9px;color:#d0e2da;font-size:13px}.toc a{font-size:12px;padding:8px 13px}@media(max-width:800px){main{padding:24px 14px}.pair,.notes,.shots{grid-template-columns:1fr}article{padding:16px}.head{align-items:start;flex-direction:column;gap:8px}h1{font-size:27px}}'''
body=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>后续25图 · 场景与实机复查</title><style>'+css+'</style></head><body><main>','<p class="eyebrow">REVENGE MEMORIES / CHAPTERS 3–5</p><h1>后续25张地图 · 场景与实机复查</h1><p>延续M11清楚的路网、建筑入口与自然地形关系，重排城市街区、运输大道、雪峡、盐原、沼泽干岛和神宫院落。新增图集只组合现有原生像素材质，保持低饱和风格。M11和前两章已完成的14图保持原样。</p>',f'<div class="pills"><span>25张定稿地图</span><span>2轮实际输入检查</span><span>{inputs:,}次最终轮按键</span><span>{len(capture["shots"])}张实机视口</span></div>','<nav><a href="../../../art-review/battle-maps-20261021/index.html">全部40张地图与行动标注</a><a href="../map-polish-20261022/index.html">前两章对照</a><a href="delivery-summary.json">本轮完整检查记录</a><a href="state.json">通行与保存检查</a></nav>','<p class="fine">左侧为本轮改动前，右侧为定稿后的Godot后台场景。展开每关可查看当前版真实按键试玩截图。每关从真实开发记录返回整备后重新进入，沿用真实成长、装备和原目标，未改写随机结果；这是逐关复查，不是全新存档连续五章通关。判定fixture不计为试玩。</p>','<nav class="toc">'+''.join(f'<a href="#{m["code"]}">{m["code"]} {e(m["name"])}</a>'for m in maps)+'</nav>']
for m in maps:
 c=m['code'];body.append(f'<article id="{c}"><div class="head"><h2>{c} · {e(m["name"])}</h2><small>第{m["chapter"]}章 · {m["size"][0]} × {m["size"][1]}格 · 第{m["turn"]}回合通关</small></div><div class="pair">')
 for folder,label in [('before','优化前'),('after','优化后 · 当前运行场景')]:body.append(f'<figure><figcaption>{label}</figcaption><a class="picture" href="{folder}/{c}.png" target="_blank"><img src="{folder}/{c}.png" alt="{c}{label}" loading="lazy"></a></figure>')
 body.append('</div><div class="notes"><section><h3>空间与行动</h3><ul>'+''.join('<li>'+e(n)+'</li>'for n in m['notes'])+'</ul></section><section><h3>原任务</h3><p class="goal">'+e(m['goal'])+'</p><p class="fine">'+('胜利后逐页完成后日谈。'if c=='J54'else'胜利后完成对应据点交互并返回世界地图。')+f' <a href="{m["source"]}">真实输入与接续记录</a></p></section></div>')
 shots=[s for s in capture['shots']if s['stage']==c]
 body.append(f'<details><summary>展开本轮实机视口 · {len(shots)}张</summary><div class="shots">')
 for shot in shots:
  f=Path(shot['path']).name;body.append(f'<figure><a class="picture" href="screenshots/{f}" target="_blank"><img src="screenshots/{f}" alt="{c}实际试玩视口" loading="lazy"></a><figcaption>{c} · 第{shot["turn"]}回合 · {shot["size"][0]} × {shot["size"][1]}原生视口</figcaption></figure>')
 body.append('</div></details></article>')
body.append('<article><h2>复查中解决的问题</h2><p>补齐水岸与桥台关系；移开三处木台上的装饰小艇并设置真实泊位；清理道路旁孤立石砖和被道路切到的树冠；将雪地、沙地岩石的深色底块改为对应环境地面。</p><p>F43首轮驱动追击西北敌人，未及时保护中央居民而失败。采用沿中央便桥推进、飞行单位分担护送的普通行动后通关，原失败与重试均保留。人物属性、伤害和任务条件没有为通过检查而修改。</p><p class="fine">所有Godot渲染均使用后台窗口保护，不激活用户窗口。运行截图逐项检查文字安全区域；本轮未更新iPhone安装包。完整素材尺寸、字节数、无损压缩记录及检查限制见交付记录。</p></article></main></body></html>')
(O/'index.html').write_text('\n'.join(body))
print(json.dumps({'passed':True,'maps':len(maps),'shots':len(capture['shots']),'final_round_inputs':inputs,'attempts':len(all_battles)},ensure_ascii=False))

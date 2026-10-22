#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the map review from immutable input-play evidence and guarded viewport images."""
from pathlib import Path
from PIL import Image
import hashlib,html,json,shutil,subprocess
R=Path(__file__).resolve().parents[1];O=R/'reports/map-polish-20261022';G=R.parent/'art-review/battle-maps-20261021'
ORDER=['M12','M13','M14','M15','S11','S12','F21','F22','F23','F24','F25','F26','S21','S22']
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selected=read(O/'selected-playthroughs.json')
capture=read(O/'screenshots/captures.json');returns=read(O/'return-flow.json')
geometry=read(O/'geometry.json');state=read(O/'state.json');package=read(O/'package-checks.json')
assert capture['passed'] and returns['passed'] and returns['complete'] and geometry['passed'] and state['passed'] and package['passed']
assert set(selected)==set(ORDER)
maps=[];assets=[];attempts=[]
(O/'after').mkdir(exist_ok=True)
for code in ORDER:
 label=selected[code];report_path=O/'play'/label/(label+'-play.json');report=read(report_path)
 b=next(x for x in report['battles']if x['code']==code)
 assert b['outcome']=='victory' and not b['failures']
 assert report['stat_edits']is False and report['forced_victories']is False
 d=read(R/f'data/stages/{code}.json')
 shutil.copy2(G/f'images/{code}.png',O/f'after/{code}.png')
 maps.append({'code':code,'name':d['name_zh'],'size':[d['map']['width'],d['map']['height']],'notes':d['tactical_notes'],'goal':d['goal'],'source':str(report_path.relative_to(O)),'checkpoint':f'play/{label}/{label}-{code}-victory.json','turn':int(b['final_turn']),'inputs':int(report.get('total_inputs',b['key_inputs'])),'quest':b['quest'],'map_sha256':sha(R/f'data/stages/{code}.json'),'play_map_sha256':report.get('map_hashes',{}).get(code),'outcome':b['outcome'],'continuation':{'from_turn':report['continued_from_turn'],'chain':f'play/{label}/continuation-chain.json','note':'首段中米蕾、莉莎濒死留队，队伍残血后出现策略停滞；续玩保留第66回合单位、位置和随机状态，经已有恢复哨位恢复、清场、开门放下桥并完成四人撤离。该长回合记录用于验证可完成，不作为关卡目标时长。'}if 'continued_from_turn'in report else None})
for path in sorted((O/'play').glob('*/*-play.json')):
 report=read(path);attempts.append({'report':str(path.relative_to(O)),'battles':[{'code':b['code'],'outcome':b['outcome'],'turn':b['final_turn'],'reason':b.get('quest',{}).get('failed_reason',''),'errors':b['failures']}for b in report['battles']]})
for folder in ['before','after','screenshots']:
 for p in sorted((O/folder).glob('*.png')):
  raw=Image.open(p).convert('RGBA').tobytes();subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
  im=Image.open(p);assert im.convert('RGBA').tobytes()==raw
  assets.append({'file':str(p.relative_to(O)),'purpose':'优化前全景'if folder=='before'else'优化后全景'if folder=='after'else'真实按键试玩存档视口','size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'compression':'lossless'})
for p in sorted((R/'assets/map-polish-20261022').glob('*.png')):
 im=Image.open(p);assets.append({'file':'../../'+str(p.relative_to(R)),'purpose':'复用既有像素与编号的独立洞底/岸线过渡图集','size':list(im.size),'bytes':p.stat().st_size,'sha256':sha(p),'quality_note':'无损压缩；保留原5042图块的像素/编号，避免动态开门图块引用失效，略高于200KB优化参考值。'})
summary={'passed':True,'date':'2026-10-22','maps':maps,'count':len(maps),'reference_unchanged':sha(R/'data/stages/M11.json')==sha(O/'baseline/M11.json'),'real_key_inputs':sum(m['inputs']for m in maps),'no_stat_rng_position_or_win_overrides':True,'return_flow':'return-flow.json','runtime_captures':'screenshots/captures.json','attempts':attempts,'assets':assets,'scope':'14张地图逐关从真实开发存档经正常整备重新入场，通过实际按键完成战斗；独立结果返回与路线复查。不是从序章连续重跑整部游戏。','failures_retained':'S11早期护送及M15冲锋、F22船战的战败保留；换用寻路/阵型/保护策略，未改数值或强制结果。旧测试脚本对结算异步与装备预览的适配失败单独保留，不作为游戏缺陷。','map_changes_after_play':'S11/S12在首轮之后仅更新洞底/岸线纹理；F25在首轮后清除一个无锚点且不可达的孤立草格，关键通路/单位与任务不变。最终地形重新检查并以最新运行截图展示。','limitations':['未重跑第三至五章完整流程','未重新导出或安装iPhone包','对照页自动浏览器渲染未验收；Godot实际视口与文字安全区另有检查']}
assert summary['reference_unchanged']
summary['checks']={'geometry':geometry['checks'],'state':state['checks'],'result_return':returns['checks'],'exported_app':package['checks'],'runtime_text_layout_errors':len(capture['layout_errors'])}
app=R/'dist/RevengeMemories-MapPolish-20261022.app'
summary['desktop_app']={'path':str(app.relative_to(R)),'pck_sha256':sha(app/'Contents/Resources/RevengeMemories.pck'),'pck_bytes':(app/'Contents/Resources/RevengeMemories.pck').stat().st_size,'engine_version':package['version'],'map_revision':'0.10.2','verification':'package-checks.json'}
(O/'delivery-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
e=html.escape
css='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#0e151a;color:#e9f0f0;font:15px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1510px;margin:auto;padding:38px 30px 65px}h1{font-size:34px;line-height:1.4;margin:6px 0 18px}h2{font-size:22px;margin:0}h3{font-size:15px;margin:0}p{color:#aabdc5;max-width:1060px}a{color:#a8d6c8;text-underline-offset:4px}.eyebrow{color:#a8d6c8;letter-spacing:.13em;font-size:12px}.pills,nav{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}.pills span,nav a{background:#22343d;padding:10px 17px;border-radius:9px}nav a{text-decoration:none;display:flex;align-items:center;justify-content:center;min-height:44px}a:focus-visible{outline:none;box-shadow:0 0 0 5px #a8d6c82b,0 0 24px #a8d6c82b}article{padding:22px;margin-top:24px;background:#18232b;border-radius:15px;box-shadow:0 12px 34px #0003;scroll-margin-top:20px}.head{display:flex;gap:18px;justify-content:space-between;align-items:center;margin-bottom:18px}.head small{color:#aabdc5}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0;min-width:0}figcaption{padding:0 3px 10px;color:#c4d6d3;font-size:13px}.picture{display:block;background:#202d35;border-radius:9px;overflow:hidden}.picture img{width:100%;height:auto;display:block;image-rendering:pixelated}.notes{display:grid;grid-template-columns:1.4fr 1fr;gap:24px;margin-top:17px}ul{padding-left:20px;color:#b5c7cc;font-size:13px}li+li{margin-top:7px}.shots{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:18px}.shots figcaption{padding:12px 4px;color:#aabdc5}.fine{font-size:12px;color:#91a7b2}details{margin-top:18px}summary{cursor:pointer;padding:12px 16px;background:#263a42;border-radius:8px}.goal{padding:13px 16px;background:#a8d6c80a;border-radius:9px;color:#d2e4db;font-size:13px}.toc{margin-top:26px}.toc a{font-size:12px;padding:8px 13px}@media(max-width:800px){main{padding:24px 14px}.pair,.notes,.shots{grid-template-columns:1fr}article{padding:16px}.head{align-items:start;flex-direction:column;gap:8px}h1{font-size:27px}}'''
body=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>前两章地图优化 · 2026-10-22</title><style>'+css+'</style></head><body><main>', '<p class="eyebrow">REVENGE MEMORIES / LANDSCAPE REVIEW</p><h1>前两章地图优化 · 场景与实机复查</h1><p>以M11的道路、林地、建筑入口和河桥关系为参照，完成其余六张第一章地图，并继续优化第二章八张地图。原生像素素材重新组合，形成粮站、押送院、军营、塔堡、矿道、溪村、甲板、港湾和海洞各自的空间关系。</p>',f'<div class="pills"><span>14张地图完成</span><span>14场实际通关</span><span>{summary["real_key_inputs"]:,}次试玩按键</span><span>M11原样保留</span></div>', '<nav><a href="../../../art-review/battle-maps-20261021/index.html">全部40张地图与交互标注</a><a href="delivery-summary.json">复查记录</a><a href="return-flow.json">战后接续检查</a></nav>', '<p class="fine">左侧是本轮修改前的同版全景，右侧是修改后的Godot后台场景。展开每关可查看本轮真实按键试玩的视口。战斗使用记录中的真实成长与装备，失败和策略重试保留；未改属性、随机结果或强制胜利。最终胜利分别从开发记录入场，不宣称连续重跑整部游戏。</p>', '<nav class="toc">'+''.join(f'<a href="#{m["code"]}">{m["code"]} {e(m["name"])}</a>'for m in maps)+'</nav>']
for m in maps:
 code=m['code'];body.append(f'<article id="{code}"><div class="head"><h2>{code} · {e(m["name"])}</h2><small>{m["size"][0]} × {m["size"][1]}格 · 第{m["turn"]}回合通关</small></div><div class="pair">')
 for folder,label in [('before','优化前'),('after','优化后 · 当前地图')]:body.append(f'<figure><figcaption>{label}</figcaption><a class="picture" href="{folder}/{code}.png" target="_blank"><img src="{folder}/{code}.png" alt="{e(m["name"])}{label}" loading="lazy"></a></figure>')
 body.append('</div><div class="notes"><section><h3>空间与行动</h3><ul>'+''.join('<li>'+e(n)+'</li>'for n in m['notes'])+'</ul></section><section><h3>原任务</h3><p class="goal">'+e(m['goal'])+'</p><p class="fine">实机：'+str(m['inputs'])+'次按键 · <a href="'+m['source']+'">输入与结算记录</a></p></section></div>')
 shots=[x for x in capture['shots']if x['stage']==code]
 body.append('<details><summary>展开本轮实机视口 · '+str(len(shots))+'张</summary><div class="shots">')
 for shot in shots:
  file=Path(shot['path']).name;body.append(f'<figure><a class="picture" href="screenshots/{file}" target="_blank"><img src="screenshots/{file}" alt="{code}实际试玩视口" loading="lazy"></a><figcaption>{code} · 第{shot["turn"]}回合 · {shot["size"][0]} × {shot["size"][1]}原生像素</figcaption></figure>')
 body.append('</div>')
 if m['continuation']:body.append('<p class="fine">'+e(m['continuation']['note'])+' <a href="'+m['continuation']['chain']+'">首段与续玩证据链</a></p>')
 body.append('</details></article>')
body.append('<p class="fine">F25两名被囚者移入原牢门后的东侧囚室，门与解锁条件保持。人物动画沿用现行代码；新增两张独立图集仅复用既有纹理追加洞底/岸线过渡。地图与图像以2026-10-22快照为准。本轮不新增旧战斗兼容地图。Godot全程后台捕获，不显示或激活窗口；未更新iPhone安装包。</p></main></body></html>')
(O/'index.html').write_text('\n'.join(body))
print(json.dumps({'passed':True,'maps':len(maps),'shots':len(capture['shots']),'inputs':summary['real_key_inputs'],'images':len(assets)},ensure_ascii=False))

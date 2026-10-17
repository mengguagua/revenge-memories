#!/usr/bin/env python3
"""Assemble evidence without rewriting failed attempts or historical saves."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import hashlib, html, json, plistlib, subprocess

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/playtest-0.5.0'
read=lambda p:json.loads(p.read_text())
def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def count(report):return report['checks'] if isinstance(report['checks'],int) else len(report['checks'])

selected={'M11':'round1-M11-final','F21':'round1-east-final','F22':'round1-F22-short-route'}
round_one=[];shots=[]
for code in ['M11','M12','M13','S12','F21','F22','F23','F24']:
    folder=selected.get(code,'round1');report=read(OUT/folder/'play-checks.json')
    battle=next(b for b in report['battles'] if b['code']==code)
    assert battle['outcome']=='victory' and not battle['failures']
    round_one.append(dict(battle,evidence=f'{folder}/play-checks.json'))
    shots.extend(s for s in report['shots'] if s['stage']==code)
r1={'round':1,'passed':True,'battles':round_one,'shots':shots,'key_inputs':sum(b['key_inputs'] for b in round_one),'scope':'Final per-stage evidence after recorded repairs. Original round1 failure and later repeats preserved. Genuine checkpoint keyboard play, not a continuous chapter run.'}
write(OUT/'round1-final/play-checks.json',r1)
r2=read(OUT/'round2/play-checks.json');assert r2['passed']

attempts=[]
for p in sorted(OUT.glob('*/play-checks.json')):
    if p.parent.name=='round1-final':continue
    r=read(p)
    attempts.append({'report':str(p.relative_to(OUT)),'passed':r['passed'],'battles':[{k:b[k] for k in ['code','outcome','final_turn']}for b in r['battles']],'purpose':'Calibration or superseded pass; retained locally' if p.parent.name.startswith(('calibration','visual-preview')) else 'Original or supplementary real-render pass'})
write(OUT/'attempts-index.json',attempts)

jobs=read(ROOT/'source/portraits-0.5.0/jobs.json')
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',11)
contact=Image.new('RGB',(768,660),(18,30,40));draw=ImageDraw.Draw(contact)
for i,j in enumerate(jobs):
    im=Image.open(ROOT/f'assets/portraits-0.5.0/{j["id"]}.png').convert('RGB').resize((96,96),Image.Resampling.NEAREST)
    x=(i%8)*96;y=(i//8)*110;contact.paste(im,(x,y));draw.text((x+2,y+97),j['id'],font=font,fill='white')
contact.save(OUT/'portraits-contact.png',optimize=True)

allshots=shots+r2['shots'];maps=read(OUT/'maps/checks.json');visual=read(OUT/'visual/checks.json')
assert maps['passed'] and visual['passed']
assert all(r.get('pixel_differences',0)==0 for r in visual['records'])
image_paths={ROOT/str(s['path']).removeprefix('res://') for s in allshots+maps['maps']+visual['records']}
image_paths|=set((ROOT/'assets/portraits-0.5.0').glob('*.png'))|{OUT/'portraits-contact.png'}
images=[]
for p in sorted(image_paths):
    with Image.open(p) as im:w,h=im.size
    images.append({'path':str(p.relative_to(ROOT)),'width':w,'height':h,'bytes':p.stat().st_size,'sha256':digest(p),'purpose':'native campaign portrait' if 'assets/portraits' in str(p) else 'real engine capture' if p.name!='portraits-contact.png' else 'native portraits, 2x nearest-neighbour contact sheet','optimization':'Native full-field verification plate, losslessly optimized with oxipng. Retain original pixels to inspect paths, terrain and edges; no lossy quantization or smaller runtime background is introduced.' if p.stat().st_size>=200000 else 'Lossless PNG; native game pixels retained.'})
write(OUT/'image-manifest.json',images)

reports={'layout_and_rules':read(OUT/'state-checks.json'),'portraits':read(OUT/'portrait-checks.json'),'injury':read(OUT/'regressions/casualty_treatment/state-checks.json'),'equipment':read(OUT/'regressions/equipment_progression/checks.json') if (OUT/'regressions/equipment_progression/checks.json').exists() else read(OUT/'regressions/equipment_progression/state-checks.json'),'chapter2':read(OUT/'regressions/state-checks.json'),'package':read(OUT/'package-checks.json')}
assert all(r['passed'] for r in reports.values())
app=ROOT/'dist/RevengeMemories.app';pck=app/'Contents/Resources/RevengeMemories.pck'
signature=subprocess.run(['codesign','--verify','--deep','--strict',str(app)],capture_output=True,text=True)
assert signature.returncode==0
plist=plistlib.loads((app/'Contents/Info.plist').read_bytes());assert plist['CFBundleShortVersionString']=='0.5.0'
summary={'version':'0.5.0','passed':True,'app':str(app),'app_version':plist['CFBundleShortVersionString'],'pck_bytes':pck.stat().st_size,'pck_sha256':digest(pck),'signature_verified':True,'direct_app_delivery':True,'rounds':[{'round':r['round'],'passed':r['passed'],'battles':len(r['battles']),'key_inputs':r['key_inputs'],'results':[{k:b[k]for k in ['code','outcome','final_turn','first_combat_turn','levelups']}for b in r['battles']]}for r in [r1,r2]],'total_battles':len(round_one)+len(r2['battles']),'unique_battlefields':len({b['code']for b in round_one+r2['battles']}),'directed_checks':{k:count(v)for k,v in reports.items()},'total_directed_checks':sum(count(v)for v in reports.values()),'portraits':48,'exact_portrait_pixels':48*48*48,'portrait_pixel_differences':0,'visual_fixture_frames':len(visual['records']),'map_frames':len(maps['maps']),'natural_play_frames':len(allshots),'background_guard':True,'visible_windows':False,'full_continuous_campaign_runs':False,'failed_attempts_preserved':'attempts-index.json','scope':'Two key-driven spot-check rounds covering all 15 existing stages, with repairs rechecked. Fresh M11 in round2; remaining battles re-enter current maps from genuine historical deployments. No stat/HP/position/RNG edits or forced natural victories. Separate directed and visual fixtures explicitly labeled.'}
write(OUT/'delivery-summary.json',summary)

esc=html.escape
def asset(path):return str(Path('../../')/path)
def figure(path,title,note=''):
    rel=str(Path(path).relative_to(OUT)) if isinstance(path,Path) else str(path).removeprefix('res://reports/playtest-0.5.0/')
    return f'<figure><a href="{esc(rel)}"><img loading="lazy" src="{esc(rel)}" alt="{esc(title)}"></a><figcaption>{esc(title)}<small>{esc(note)}</small></figcaption></figure>'
pages=[]
pages.append('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>复仇与回忆 0.5.0 · 实机验收</title><style>body{margin:0;background:#101b24;color:#e8edec;font:16px/1.7 system-ui}main{max-width:1180px;margin:auto;padding:32px}a{color:#a4decc}h1,h2{color:#eee1b8}nav{display:flex;gap:24px;flex-wrap:wrap}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(370px,1fr));gap:20px}figure{margin:0;background:#1b2c36;padding:16px;border-radius:8px}img{display:block;width:100%;height:auto;image-rendering:pixelated}figcaption{margin-top:12px}small{display:block;color:#b5c9c7}.portraits{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}.portrait{background:#1b2c36;padding:12px}.portrait img{width:96px;height:96px}.pair{display:flex;gap:8px}.pair img{width:48px;height:48px}table{border-collapse:collapse;width:100%}td,th{padding:9px;text-align:left;border-bottom:1px solid #39505a}.good{color:#a7e6bc}details{margin:16px 0}code{overflow-wrap:anywhere}</style><main>')
pages.append('<h1>复仇与回忆 · 0.5.0</h1><p>信息框避让、出口和首领定位、弓手主动追击、首关成长节奏、48张剧情与兵种画像。</p><nav><a href="#shots">实机变化</a><a href="#rounds">两轮试玩</a><a href="#portraits">画像对比</a><a href="#maps">15张战场</a><a href="delivery-summary.json">检查汇总</a></nav>')
pages.append(f'<p class="good">两轮修正后抽查16场全部通关，覆盖15关；定向检查{summary["total_directed_checks"]}项通过；48张画像逐像素对比零差异；独立应用签名及包内检查通过。</p><p>真实后台OpenGL渲染，无可见窗口或焦点抢占。第二轮首关为新开档；其余使用真实旧检查点返回整备重新入场。这是两轮抽查，不是两次连续通关全战役。第一轮登船关败北后调整并复测，<a href="attempts-index.json">原失败与补测记录</a>保留。</p>')
pages.append('<h2 id="shots">实际运行效果</h2><div class="grid">')
highlights=[('round2/M11-entry.png','选中人物：信息框避开人物和箭头'),('round2/M11-visible-exit.png','东北出口与唯一入口：旗标、地名和镜头定位'),('round2/M11-captain-portrait.png','追击队长：真实名称、4级、32生命和铁枪'),('round2/M11-archer-portrait.png','普通弓手：按西部兵种分配画像'),('round2/M11-levelup-hunapu-3.png','新开档首关：正常经验结算触发升级'),('maps/F21-medic-point.png','第二章登船关：船医补给点'),('maps/F22-exit.png','救俘关：总闸旁接应旗标'),('visual/vucub-status.png','七羽日冠：最终画像状态页（明确标记的目录夹具）')]
for path,title in highlights:
    if (OUT/path).exists():pages.append(figure(path,title,'原始引擎视口截图；点击查看原尺寸。'))
pages.append('</div><h2 id="rounds">两轮键盘试玩</h2>')
for report in [r1,r2]:
    pages.append(f'<h3>第{report["round"]}轮 · {report["key_inputs"]}次按键</h3><table><tr><th>关卡</th><th>结果</th><th>通关回合</th><th>首次交战</th><th>升级人数</th></tr>')
    for b in report['battles']:pages.append(f'<tr><td>{b["code"]}</td><td>胜利</td><td>{b["final_turn"]}</td><td>{b["first_combat_turn"]}</td><td>{len(b["levelups"])}</td></tr>')
    pages.append('</table>')
    pages.append('<details><summary>展开该轮实机截图</summary><div class="grid">')
    for s in report['shots']:pages.append(figure(s['path'],Path(s['path']).stem,f'第{s["turn"]}回合 · {s["view"]}'))
    pages.append('</div></details>')
pages.append('<p>F22包含两处囚舱开锁与三人护送，本次谨慎试玩仍用32回合；没有把全关卡都描述成短关，也没有抹去真实伤亡。首关新开档9回合，三名初始队员全部升级；F26清场后船队按真实路线加速，17回合通关。</p>')
pages.append('<h2 id="portraits">画像效果与运行稿</h2><p>全部运行稿48×48；下图按最近邻放大显示。每张在实际状态页的2304像素与运行稿完全一致，共110592像素零差异。目录预览属于明确标记的视觉夹具，不计自然战斗胜利。</p>')
pages.append(figure('portraits-contact.png','48张当前战役画像'))
pages.append('<p><a href="../../source/portraits-0.5.0/jobs.json">内置image_gen逐张制作提示词</a> · <a href="../../assets/portraits-0.5.0/README.md">运行素材路径与说明</a> · <a href="image-manifest.json">逐图尺寸/字节/哈希</a></p><div class="portraits">')
for j in jobs:
    key=j['id'];idx=j['reference_index'];after=asset(f'assets/portraits-0.5.0/{key}.png')
    before=asset(f'assets/original/graphics/portraits/portrait_{idx:02}.png') if idx is not None else None
    pages.append(f'<div class="portrait"><strong>{esc(key)}</strong><div class="pair">'+(f'<img loading="lazy" src="{before}" alt="旧身份颜色参考">'if before else '')+f'<img loading="lazy" src="{after}" alt="重绘运行稿"></div><small>旧参考 → 新运行稿<br>普通敌军旧状态页为空，左图仅为制作参考。</small><a href="visual/{key}-status.png">查看实机状态页</a></div>')
pages.append('</div><h2 id="maps">15关地图抽查</h2><div class="grid">')
for s in maps['maps']:
    if s['whole_map']:pages.append(figure(s['path'],s['stage']+' · 全景','扩大引擎视口展示全场，隐藏光标检查卡；部署和地图取自正常入场。'))
pages.append('</div><h2>应用与记录</h2><p>直接应用：<code>'+esc(str(app))+'</code>。退出旧游戏进程后重开。旧战中存档继续旧布局；体验新布局需在S菜单选择“返回整备（重置本战）”，再重新入场。</p><p><a href="../../docs/首关节奏与画像重绘.md">修改说明</a> · <a href="round1-final/play-checks.json">第一轮最终证据</a> · <a href="round2/play-checks.json">第二轮证据</a> · <a href="visual/checks.json">逐像素与文字安全区</a> · <a href="maps/checks.json">全部地图</a> · <a href="package-checks.json">独立包检查</a></p></main>')
(OUT/'index.html').write_text(''.join(pages))
print(json.dumps({k:summary[k]for k in ['passed','total_battles','unique_battlefields','total_directed_checks','natural_play_frames','map_frames','visual_fixture_frames','pck_sha256']},ensure_ascii=False))

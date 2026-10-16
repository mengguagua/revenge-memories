#!/usr/bin/env python3
"""Publish current runtime captures and final two-round acceptance evidence."""
from pathlib import Path
import hashlib,html,json,subprocess,zipfile
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'reports/battlefield-0.3.0';S=O/'screenshots'
ORDER=['M11','M12','M13','M14','M15','S11','S12','F21','F22','F23','F24','F25','F26','S21','S22']
def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 shore_fix=read(O/'coast-walkway-fix.json') if (O/'coast-walkway-fix.json').exists() else None
 camp_fix=read(O/'camp-checkpoint-fix.json') if (O/'camp-checkpoint-fix.json').exists() else None
 scale_fix=read(O/'building-scale-fix.json') if (O/'building-scale-fix.json').exists() else None
 terrain_fix=read(O/'terrain-indicator-fix.json') if (O/'terrain-indicator-fix.json').exists() else None
 entrance_fix=read(O/'building-entrance-fix.json') if (O/'building-entrance-fix.json').exists() else None
 river_fix=read(O/'m11-river-fix.json') if (O/'m11-river-fix.json').exists() else None
 version='0.3.6' if shore_fix else '0.3.5' if camp_fix else '0.3.4' if scale_fix else '0.3.3' if terrain_fix else '0.3.2' if entrance_fix else '0.3.1' if river_fix else '0.3.0'
 captures=read(S/'captures.json');assert captures['passed'] and len(captures['shots'])==(81 if shore_fix else 72 if camp_fix else 68 if scale_fix else 67 if terrain_fix else 65 if entrance_fix else 50)
 rounds=[]
 for n in [1,2]:
  selected={}
  for part in ['west','east','chambers']:
   label=f'acceptance{n}-{part}';path=O/'play'/label/f'{label}-play.json';run=read(path)
   for battle in run['battles']:
    selected[battle['code']]={k:v for k,v in battle.items() if k!='actions'}
    selected[battle['code']]['evidence']=str(path.relative_to(R))
  assert set(selected)==set(ORDER) and all(b['outcome']=='victory' and not b['failures'] for b in selected.values())
  rounds.append({'round':n,'passed':True,'battles':[selected[c] for c in ORDER]})
 attempts=[]
 for path in sorted((O/'play').glob('*/*-play.json')):
  d=read(path);attempts.append({'label':path.parent.name,'passed':d['passed'],'battles':[{'code':b['code'],'outcome':b['outcome'],'turn':b['final_turn'],'failed_reason':b['quest'].get('failed_reason','')} for b in d['battles']],'summary':str(path.relative_to(R))})
 write(O/'attempts-index.json',{'attempts':attempts,'note':'Initial failures are retained. Final acceptance uses west/east with the three final chamber/coast rechecks overriding M15/S11/S22. Raw isolated checkpoints remain local and ignored by Git.'})
 # Lossless only: native viewport dimensions and all pixels are retained.
 for path in sorted(S.glob('*.png')):subprocess.run(['/opt/homebrew/bin/oxipng','-o','3','--quiet',str(path)],check=True)
 images=[]
 for shot in captures['shots']:
  p=R/shot['path'].removeprefix('res://');im=Image.open(p)
  images.append(dict(shot,pixels=list(im.size),bytes=p.stat().st_size,sha256=digest(p)))
 write(O/'image-manifest.json',{'images':images,'compression':'oxipng lossless, native runtime canvas retained','max_bytes':max(i['bytes'] for i in images)})
 stages=[]
 for code in ORDER:
  p=R/f'data/stages/{code}.json';d=read(p);logic=d['logic_grid'];ground=sum(q not in '~^#' for row in logic for q in row);stone=sum(q in 'c=' for row in logic for q in row)
  stages.append({'code':code,'name':d['name_zh'],'chapter':1 if code in ORDER[:7] else 2,'size':[d['map']['width'],d['map']['height']],'theme':d['location_theme'],'stone_of_ground':round(stone/ground,3),'sites':d.get('building_sites',[]),'visits':[o for o in d['objects'] if o['kind']=='visit'],'map_sha256':digest(p)})
 summary={'version':version,'passed':True,'scope':'Two rounds of all 15 battles, independently re-entered from genuine campaign deployments through real keyboard menus. Not a new continuous campaign run. No stat/RNG/HP/position edits or forced victories in playthroughs. Directed state fixtures are reported separately.', 'rounds':rounds,'stages':stages,'geometry':read(O/'geometry.json'),'state':read(O/'state-checks.json'),'capture_count':len(images),'capture_layout_errors':captures['layout_errors'],'package':read(O/'package-check.json') if (O/'package-check.json').exists() else None}
 if (O/'m11-snow-bank-fix.json').exists():summary['visual_patches']=[read(O/'m11-snow-bank-fix.json')]
 if river_fix:summary.update(baseline_rounds_version='0.3.0',river_layout_retest=river_fix,baseline_package=summary['package'],package=read(O/'m11-river-package-check.json'))
 if entrance_fix:summary.update(building_entrance_fix=entrance_fix,package=read(O/'entrance-package-check.json') if (O/'entrance-package-check.json').exists() else summary['package'])
 if terrain_fix:summary.update(terrain_indicator_fix=terrain_fix,package=read(O/'terrain-package-check.json'))
 if scale_fix:summary.update(building_scale_fix=scale_fix,package=read(O/'building-scale-package-check.json'),scope='Historical 0.3.0 acceptance: two independent real-input rounds of 15 battles. Current 0.3.4: full-cell tactical sprites, eleven site relocations in six maps, directed reachability/save/occupation checks, one genuine M13 replay, and refreshed runtime captures. No repeat claim for all 30 battles.')
 if camp_fix:summary.update(camp_checkpoint_fix=camp_fix,package=read(O/'camp-checkpoint-package-check.json'),scope='Historical 0.3.0 two-round acceptance and later focused patches retained separately. Current 0.3.5: M14 road checkpoints, one genuine ten-turn replay, directed collision/ownership/save checks and eight refreshed M14 runtime captures. Other fourteen map files unchanged.')
 if shore_fix:summary.update(coast_walkway_fix=shore_fix,package=read(O/'coast-walkway-package-check.json'),scope='Historical acceptance and focused geometry replays retained separately. Current 0.3.6: visual terrain and terrain-name changes only across 15 maps. All nonvisual fields identical, 81 runtime captures refreshed, targeted art/state/package checks passed. No additional full battle replay for this display-only patch.')
 assert summary['geometry']['passed'] and summary['state']['passed']
 write(O/'delivery-summary.json',summary)
 write(O/'final-map-hashes.json',{s['code']:s['map_sha256'] for s in stages})
 css='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#12252b;color:#eee9d8;font:16px/1.75 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}main{max-width:1720px;margin:auto;padding:38px 28px 70px}h1{font-size:clamp(26px,3vw,38px);line-height:1.4;margin:10px 0 18px}h2{margin:34px 0 18px}p{max-width:1000px;color:#b9cbca}.eyebrow,.code{color:#d5c48f;font-family:monospace}nav{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}a{color:#e4d09b;text-underline-offset:4px}nav a,.link{display:inline-block;padding:11px 20px;background:#2c4448;border-radius:7px;text-decoration:none;box-shadow:0 4px 12px #08171d66}a:focus-visible{outline:none;box-shadow:0 0 0 5px #d4c68e40,0 0 20px #e4d09b55}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{min-width:0;overflow:hidden;border-radius:12px;background:#223a40;box-shadow:0 7px 20px #07191f66;scroll-margin-top:20px}header{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:20px 24px}h3{font-size:21px;margin:0}.code{margin-right:15px;font-size:18px}.tag{background:#344d4e;padding:5px 12px;border-radius:7px;white-space:nowrap;font-size:14px}img{display:block;width:100%;height:auto;image-rendering:pixelated}.picture{display:block;background:#102127}.details{padding:18px 24px 25px}.details p{margin:6px 0;font-size:14px}.shots{display:flex;flex-wrap:wrap;gap:14px;margin-top:10px;font-size:14px}.review{display:grid;grid-template-columns:1fr 1fr;gap:24px}.review figure{margin:0;background:#223a40;border-radius:10px;overflow:hidden}.review figcaption{padding:17px 22px;color:#c4d0c8}.fine{font-size:14px}@media(max-width:950px){main{padding:24px 16px 45px}.grid,.review{grid-template-columns:1fr}header,.details{padding:18px}h3{font-size:19px}}'''
 body=['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>前两章战场 · 0.3.0 实机画廊</title><style>'+css+'</style></head><body><main>',
 '<div class="eyebrow">REVENGE MEMORIES · 0.3.0</div><h1>前两章 · 全部战场实机画廊</h1><p>15 个战场重新编排地形与通路。普通建筑是可占据的单格地形；较大的访问建筑保留完整外观、明确门口和门前交互。每张全景均由 Godot 实际视口捕获，点击可查看完整原图。</p>',
 '<nav><a href="#chapter1">第一章 · 7 场</a><a href="#chapter2">第二章 · 8 场</a><a href="#visits">门前访问实机</a><a href="../../dist/chapter-1-2-battlefields-0.3.0.zip">下载全部截图</a><a href="delivery-summary.json">两轮验收记录</a></nav>',
 '<p class="fine">两轮逐关按键试玩共 30 次胜利；首次主动接战在第 3—5 回合。试玩从真实战役存档经整备重新入场，保留原属性和随机结果。50 张实机图的文字安全区检查为 0 错误。</p>']
 for chapter in [1,2]:
  body.append(f'<section id="chapter{chapter}"><h2>第{chapter}章</h2><div class="grid">')
  for stage in [s for s in stages if s['chapter']==chapter]:
   code=stage['code'];name=html.escape(stage['name']);image=next(i for i in images if i['name']==code+'-whole');w,h=image['pixels'];t=[next(b for b in r['battles'] if b['code']==code)['final_turn'] for r in rounds]
   visit=' · '+str(len(stage['visits']))+' 处门前访问' if stage['visits'] else ''
   body.append(f'<article id="{code}"><header><h3><span class="code">{code}</span>{name}</h3><span class="tag">'+('支线' if code.startswith('S') else '主线')+f'</span></header><a class="picture" href="screenshots/{code}-whole.png" target="_blank" aria-label="打开{name}完整战场"><img src="screenshots/{code}-whole.png" width="{w}" height="{h}" alt="{name}完整战场实机图" loading="lazy"></a><div class="details"><p>{html.escape(stage["theme"])}</p><p>{stage["size"][0]} × {stage["size"][1]} 格 · 两轮通关 {t[0]} / {t[1]} 回合{visit}</p><div class="shots"><a href="screenshots/{code}-whole.png" target="_blank">完整全景 ↗</a><a href="screenshots/{code}-deployment.png" target="_blank">横屏开战视口 ↗</a><a href="screenshots/{code}-terrain.png" target="_blank">地形细节视口 ↗</a></div></div></article>')
   if code=='M11' and (O/'m11-snow-bank-fix.json').exists():
    body[-1]=body[-1].replace('<p>'+html.escape(stage['theme'])+'</p>','<p>'+html.escape(stage['theme'])+'</p><p>已修正雪地河岸误贴的黄色沙滩底色及桥头白色接缝。</p>')
  body.append('</div></section>')
 body.extend(['<section id="visits"><h2>门前访问 · 实际菜单与对话</h2><p>从建筑正面门前选择“访问”，读取信息并领取一次性奖励。单格营垒、舵楼哨位等可以站人，双方使用相同地形规则；恢复地形显示回合恢复量。</p><div class="review">'])
 for code in ['F21','F22']:
  for mode,label in [('menu','门前行动菜单'),('dialogue','带画像的访问对话')]:
   body.append(f'<figure><a href="screenshots/{code}-visit-{mode}.png" target="_blank"><img src="screenshots/{code}-visit-{mode}.png" width="426" height="240" alt="{code} {label}" loading="lazy"></a><figcaption>{code} · {label}</figcaption></figure>')
 body.append('</div></section><p class="fine">完整全景使用与地图匹配的实际视口，正常横屏视口为 426 × 240 原生像素。旧版进行中的战斗保留旧布局；返回整备重新进场或重试后采用本版地图。</p></main></body></html>')
 if river_fix:
  body=[part.replace('前两章战场 · 0.3.0 实机画廊','前两章战场 · 0.3.1 实机画廊').replace('REVENGE MEMORIES · 0.3.0','REVENGE MEMORIES · 0.3.1').replace('chapter-1-2-battlefields-0.3.0.zip','chapter-1-2-battlefields-0.3.1.zip') for part in body]
  for i,part in enumerate(body):
   if part.startswith('<p class="fine">两轮'):
    body[i]=part.replace('两轮逐关按键试玩共 30 次胜利','0.3.0 两轮逐关按键试玩共 30 次胜利').replace('</p>','本次 0.3.1 仅重做 M11 河道，补测第 '+str(river_fix['final_turn'])+' 回合完成护送；其他14关布局未改。</p>')
   if '<article id="M11"' in part:
    body[i]=part
    # M11's prior round values are retained in the JSON baseline evidence.
    import re
    body[i]=re.sub(r'两轮通关 \d+ / \d+ 回合','河道修正后通关 '+str(river_fix['final_turn'])+' 回合',body[i])
    body[i]=body[i].replace('已修正雪地河岸误贴的黄色沙滩底色及桥头白色接缝。','河道现已连续贯通，两处木桥真正跨河；消除缺角与路面水色碎块。')
 if entrance_fix:
  body=[part.replace('0.3.1 实机画廊','0.3.2 实机画廊').replace('REVENGE MEMORIES · 0.3.1','REVENGE MEMORIES · 0.3.2').replace('chapter-1-2-battlefields-0.3.1.zip','chapter-1-2-battlefields-0.3.2.zip').replace('50 张实机图','65 张实机图') for part in body]
  for i,part in enumerate(body):
   if '<article id=' in part and any(b['stage'] in part.split('>')[0] for b in entrance_fix['buildings']):
    code=part.split('id="')[1].split('"')[0]
    body[i]=part.replace('</div></div></article>','<a href="screenshots/'+code+'-entrance.png" target="_blank">原生建筑入口 ↗</a></div></div></article>')
   if part.startswith('<p class="fine">0.3.0'):
    body[i]=body[i].replace('</p>','0.3.2 已移除14处访问建筑的叠加门，并核对原生入口交互；地形和战斗参数未改。</p>')
  body[-1]=body[-1].replace('</main>','<p class="fine">建筑自带门洞，按入口位置设置一至两个门前交互格。海灯岛避难所采用自带入口的完整单格小屋。</p></main>')
 if terrain_fix:
  body=[part.replace('0.3.2 实机画廊','0.3.3 实机画廊').replace('REVENGE MEMORIES · 0.3.2','REVENGE MEMORIES · 0.3.3').replace('chapter-1-2-battlefields-0.3.2.zip','chapter-1-2-battlefields-0.3.3.zip').replace('65 张实机图','67 张实机图') for part in body]
  body.insert(2,'<p>0.3.3：山地采用灰褐色碎岩底纹与坡脚过渡；建筑地面、海崖背后的水面与碰撞分开处理，消除紫色碎块。全景不显示操作光标，实机白色箭头仅表示当前操作位置；常驻任务箭头已移除，目标用途在地块说明和行动菜单中显示。</p>')
  for i,part in enumerate(body):
   if '<article id="M12"' in part:body[i]=part.replace('</div></div></article>','<a href="screenshots/M12-objective.png" target="_blank">粮仓目标说明 ↗</a></div></div></article>')
   elif '<article id="M15"' in part:body[i]=part.replace('</div></div></article>','<a href="screenshots/M15-escape.png" target="_blank">北门敌军退路 ↗</a></div></div></article>')
  body[-1]=body[-1].replace('</main>','<p class="fine">本轮更新全部战场的视觉图层和光标显示，并补查目标说明；道路、碰撞、单位位置及战斗参数未变。原两轮通关记录为0.3.0验收，M11河道为0.3.1补测，本轮未重复完整通关。</p></main>')
 if scale_fix:
  body=[part.replace('0.3.3 实机画廊','0.3.4 实机画廊').replace('REVENGE MEMORIES · 0.3.3','REVENGE MEMORIES · 0.3.4').replace('chapter-1-2-battlefields-0.3.3.zip','chapter-1-2-battlefields-0.3.4.zip').replace('67 张实机图','68 张实机图').replace('本轮更新全部战场的视觉图层','0.3.3更新全部战场的视觉图层').replace('本轮未重复完整通关','0.3.3未重复完整通关') for part in body]
  body.insert(2,'<p>0.3.4：营垒、军帐、舵楼哨位改用完整单格战场素材，普通建筑统一16×16画布并充满主要轮廓。重排6关的11处营垒/屋舍，22处可占据建筑均连通现有道路或甲板。南岗三处岗堡分别守护西囚区、东囚区和内庭，已按真实输入补测14回合胜利。</p>')
  for i,part in enumerate(body):
   if '<article id="M13"' in part:
    import re
    part=re.sub(r'两轮通关 \d+ / \d+ 回合','岗堡重排后通关14回合',part)
    body[i]=part.replace('</div></div></article>','<a href="screenshots/M13-building-terrain.png" target="_blank">岗堡尺寸与地形效果 ↗</a></div></div></article>')
  body[-1]=body[-1].replace('</main>','<p class="fine">0.3.4补查843项存档/交互规则、1557项地图资源检查；旧版进行中的6关保留原布局，正常重试或整备重新入场后采用新岗堡位置。原战斗数值、部署、主目标与道路宽度未改。</p></main>')
 if camp_fix:
  body=[part.replace('0.3.4 实机画廊','0.3.5 实机画廊').replace('REVENGE MEMORIES · 0.3.4','REVENGE MEMORIES · 0.3.5').replace('chapter-1-2-battlefields-0.3.4.zip','chapter-1-2-battlefields-0.3.5.zip').replace('68 张实机图','72 张实机图') for part in body]
  body.insert(2,'<p>0.3.5：旧塔外营改为南营、东营两处道路哨卡。两侧木栅明确阻挡，南路保留三格宽、东路两格宽通行口；站到军旗格选择控制，红旗会变蓝旗。移除树林中孤立栅栏，控制点均落在真实道路上。本关补测第10回合通关，其余14张地图未改。</p>')
  for i,part in enumerate(body):
   if '<article id="M14"' in part:
    import re
    part=re.sub(r'两轮通关 \d+ / \d+ 回合','道路哨卡修正后通关10回合',part)
    body[i]=part.replace('</div></div></article>','<a href="screenshots/M14-south-checkpoint.png" target="_blank">南营哨卡 ↗</a><a href="screenshots/M14-east-checkpoint.png" target="_blank">东营哨卡 ↗</a><a href="screenshots/M14-palisade.png" target="_blank">木栅通行说明 ↗</a><a href="screenshots/M14-controlled.png" target="_blank">真实夺旗后蓝旗 ↗</a></div></div></article>')
  body[-1]=body[-1].replace('</main>','<p class="fine">0.3.5：本关8张运行图更新，包含第5回合实际控制后离开旗点的蓝旗画面；没有修改人物位置或强制控制。859项状态检查、1585项地图资源检查、独立包27项检查通过。旧0.3.4外营战斗保持原布局，正常重试/整备重新入场采用新哨卡。</p></main>')
 if shore_fix:
  body=[part.replace('0.3.5 实机画廊','0.3.6 实机画廊').replace('REVENGE MEMORIES · 0.3.5','REVENGE MEMORIES · 0.3.6').replace('chapter-1-2-battlefields-0.3.5.zip','chapter-1-2-battlefields-0.3.6.zip').replace('72 张实机图','81 张实机图') for part in body]
  body.insert(2,'<p>0.3.6：旧塔堡使用草岸与岩岸，移除误铺的断续沙色边条；真正的沙滩补上沙地到草地的像素过渡。木栈道、码头和木桥增加木板方向、边梁与端头，地形说明按实际用途命名。本轮全部15关仅修改显示，通行、碰撞、移动消耗和人物位置不变。</p>')
  detail_links={'M15':[('coast','草岸与岩岸'),('walkway','港侧木栈道')],'F23':[('beach','沙滩到草地过渡')],'F24':[('beach','沙滩到草地过渡')],'F25':[('walkway','港口木码头')],'F26':[('walkway','修补木桥')],'M11':[('bridge','跨河木桥')],'S12':[('bridge','溪谷木桥')],'S22':[('coast','潮水与岩岸')]}
  for i,part in enumerate(body):
   for code,links in detail_links.items():
    if '<article id="'+code+'"' in part:
     added=''.join('<a href="screenshots/'+code+'-'+mode+'.png" target="_blank">'+label+' ↗</a>' for mode,label in links)
     body[i]=part.replace('</div></div></article>',added+'</div></div></article>');break
  body[-1]=body[-1].replace('</main>','<p class="fine">0.3.6重新捕获81张运行图；1645项地图资源和859项状态检查通过。全部15关除视觉字段外相同，旧图集3530格像素/编号完整保留；本轮没有重复完整战斗试玩。</p></main>')
 (O/'index.html').write_text('\n'.join(body))
 stable=R/'reports/battlefield-gallery';stable.mkdir(exist_ok=True)
 (stable/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=../battlefield-0.3.0/index.html"><title>最新战场画廊</title><a href="../battlefield-0.3.0/index.html">打开最新全战场实机画廊</a></html>\n')
 write(stable/'manifest.json',{'version':version,'canonical':'../battlefield-0.3.0/index.html','images':'../battlefield-0.3.0/image-manifest.json','acceptance':'../battlefield-0.3.0/delivery-summary.json'})
 archive=R/f'dist/chapter-1-2-battlefields-{version}.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(S.glob('*.png')):z.write(p,p.name)
  z.write(O/'image-manifest.json','image-manifest.json');z.write(O/'delivery-summary.json','delivery-summary.json')
 print(json.dumps({'rounds':len(rounds),'wins':sum(len(r['battles']) for r in rounds),'images':len(images),'archive_bytes':archive.stat().st_size,'geometry_checks':summary['geometry']['checks'],'state_checks':summary['state']['checks']}))
if __name__=='__main__':main()

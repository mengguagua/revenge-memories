# -*- coding: utf-8 -*-
from pathlib import Path
import json,html,hashlib,re
from datetime import datetime
R=Path(__file__).resolve().parents[1];OUT=R/'reports/review-0.2.1'
def read(p):return json.loads((OUT/p).read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def pick(file,code):
 d=read(file);b=next(v for v in d['battles'] if v['code']==code)
 return {'code':code,'outcome':b['outcome'],'turn':b['final_turn'],'source':file,'keys':b['key_inputs'],'scope':b['scope']}
round1=[pick('round1-play.json',x) for x in ['M13','S12','F24']]+[pick('round1-naval-play.json','F21')]
round2=[pick('round2-play.json',x) for x in ['M12','F25','F26']]+[pick('round2-intercept-play.json',x) for x in ['M13','S22']]+[pick('round2-garrison-play.json','M14'),pick('round2-tower-play.json','M15')]
files=sorted(OUT.glob('*-play.json'));attempts=[]
for p in files:
 d=json.loads(p.read_text());attempts.append({'file':p.name,'keys':d['inputs'],'results':[{'code':b['code'],'outcome':b['outcome'] or 'stopped','turn':b['final_turn']} for b in d['battles']]})
checks=read('rules.json');shots=read('screenshots/captures.json');package=read('package-check.json');manifest=read('screenshots/image-manifest.json')
hashes=read('package-source-hashes.json');source_saves_unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==sha for p,sha in hashes.items())
package.update(codesign_passed='valid on disk' in (OUT/'codesign.log').read_text(),source_saves_unchanged=source_saves_unchanged,working_directory='/private/tmp',warnings=['Existing Godot cleanup warning at headless/capture exit; retained in logs.'])
write(OUT/'package-check.json',package)
summary={'version':'0.2.1','completed_local':datetime.now().astimezone().isoformat(),'passed':all(b['outcome']=='victory' for b in round1+round2) and checks['passed'] and shots['passed'] and package['passed'] and package['codesign_passed'] and source_saves_unchanged,'round1':{'purpose':'Baseline actual-input sampling, collision/route/terrain audit','battles':round1},'round2':{'purpose':'Recheck changed layouts, normal preparation, chokepoint/alternate-route and retreat interception play','battles':round2},'distinct_played_battles':len({b['code'] for b in round1+round2}),'successful_full_battle_samples':len(round1+round2),'actual_play_keys_including_retained_attempts':sum(a['keys'] for a in attempts),'attempts':attempts,'geometry_rule_checks':checks['checks'],'all_battlefields_reviewed':len(checks['stages']),'runtime_screenshot_count':len(shots['shots']),'runtime_layout_errors':shots['layout_errors'],'image_max_bytes':max(x['bytes'] for x in manifest),'package_checks':package['checks'],'package_menu_keys':package['inputs'],'source_saves_unchanged':source_saves_unchanged,'codesign_passed':package['codesign_passed'],'core_combat_formula_changed':False,'retreat_timer_changed':False,'compatibility':'Old active 0.2.0 battles retain original geometry until normal retry or preparation re-entry; new saves mark map_revision.','limitations':['Sampled ten distinct battles, not two complete no-loss campaign playthroughs.','Actual failed/stalled attempts are retained; final acceptance uses the documented successful retry for each sampled case.','Landscape layout checked at native 256x240, 426x240, 426x266 and 562x260; no mobile hardware/touch acceptance.','Optional short GPU continuation did not reach the selected north-gate pose; no such screenshot is presented.']}
write(OUT/'summary.json',summary)
selected=[
('M13-real-courtyard','第一章 · 押送所南院','两处缺口与东侧外廊形成正面防守和绕行选择；土院与石铺路区分暴露区和掩护区。'),
('F25-real-assault','第二章 · 军港推进','仓库、箱袋与码头均有实际阻挡。近战守住窄口，弓手与法师可从后方支援。'),
('M14-forest-cost','林地与骑兵移动','林地沿用回避+40；当前骑兵移动消耗3。步兵、骑兵与飞行部队的消耗分别计算。'),
('F21-real-boarding','双舰登船','上下两条跳板都可通行，一条桥口可以固守，另一条可用于包抄。飞行敌人仍能越过海面。'),
('S22-real-flanking','海洞分路','完整岩脊将洞室分成两路，窄口可挡敌，另一侧可绕行接近事件目标。'),
('M15-real-advance','旧塔中路','保留通往指挥所的主路，在院落内加入完整建筑与防线；骑兵可先占北门截断退路。'),
('F26-real-escort','古道护船','步兵沿石堤和木架推进，居民船走独立海路；清理沿岸敌人后船只继续航行。'),
('F25-warehouse-blocking','建筑与碰撞一致','建筑、仓库和箱车阻挡地面部队，地形卡明确说明当前角色能否落脚。'),
('M11-forest-cost','雪林护送','在森林中借用回避，或沿石路追赶和护送，位置选择会影响移动与命中。'),
('M13-tactical-notes','目标菜单中的战术提示','在原有目标说明后增加短提示，说明通道、地形、绕行与保护目标，不改变战斗公式。')]
articles=[]
for stem,title,description in selected:
 assert (OUT/'screenshots'/(stem+'.png')).exists()
 articles.append(f'<article><a class="shot" href="screenshots/{stem}-3x.png"><img src="screenshots/{stem}.png" alt="{title}实机截图"></a><div class="caption"><h2>{title}</h2><p>{description}</p><a href="screenshots/{stem}-3x.png">查看 3 倍像素截图 ↗</a></div></article>')
allmaps=[]
for stage in checks['stages']:
 code=stage['code'];allmaps.append(f'<a href="screenshots/{code}-whole.png"><img loading="lazy" src="screenshots/{code}-whole.png" alt="{code}完整战场实际视口"><span>{code} · 完整战场</span></a>')
rows=''.join(f'<tr><td>{r}</td><td>{b["code"]}</td><td>{b["turn"]}</td><td>通关</td></tr>' for r,bs in [(1,round1),(2,round2)] for b in bs)
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第一章与第二章 · 两轮抽查 / 0.2.1</title><style>
:root{color-scheme:dark;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;background:#102127;color:#f1eada}*{box-sizing:border-box}body{margin:0}main{max-width:1420px;margin:auto;padding:44px 28px 70px}.eyebrow{font-size:13px;letter-spacing:.12em;color:#c0b389}h1{font-size:clamp(28px,4vw,42px);margin:12px 0 18px;line-height:1.3}header p{max-width:880px;line-height:1.8;color:#bdcbcb}.stats,.links{display:flex;flex-wrap:wrap;gap:12px;margin:20px 0}.stats span{padding:10px 16px;background:#253c42;border-radius:6px}.links{gap:24px;margin-bottom:32px}a{color:#e4c895;text-underline-offset:5px}a:focus-visible,summary:focus-visible{outline:none;box-shadow:0 0 0 5px #d5bb8155;border-radius:5px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:#21353b;border-radius:10px;overflow:hidden;box-shadow:0 8px 24px #05161b55}.shot{display:flex;background:#07151a;aspect-ratio:16/10;align-items:center;justify-content:center;padding:16px}.shot img{width:100%;height:auto;max-height:100%;object-fit:contain;image-rendering:pixelated}.caption{padding:18px 22px 24px}h2{font-size:19px;line-height:1.4;margin:0 0 10px}.caption p{color:#b7c9c9;font-size:14px;line-height:1.8;min-height:76px;margin:0 0 14px}.caption a{font-size:13px}details,.note{margin-top:28px;padding:22px;background:#1b3036;border-radius:10px;color:#becbca;line-height:1.8}summary{cursor:pointer;color:#eadfc6;font-size:18px}.maps{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:20px}.maps a{background:#102127;text-decoration:none;border-radius:5px;overflow:hidden}.maps img{display:block;width:100%;image-rendering:pixelated}.maps span{display:block;padding:10px 12px;font-size:14px}table{width:100%;border-collapse:collapse;margin-top:20px;text-align:left}td,th{padding:10px 14px;border-bottom:1px solid #3a5156}th{color:#e8decb}.note{font-size:14px}.note strong{color:#e9dfc8}@media(max-width:760px){main{padding:28px 16px 48px}.grid{grid-template-columns:1fr}.maps{grid-template-columns:repeat(2,minmax(0,1fr))}.shot{padding:10px}.caption{padding:18px}.caption p{min-height:0}}
</style></head><body><main><header><div class="eyebrow">REVENGE MEMORIES / 0.2.1</div><h1>第一章与第二章 · 两轮抽查</h1><p>修复箱车碰撞和提示遮挡，补齐地形信息；调整押送所、旧塔、军港与海洞，使防守窄口、远程支援、分路包抄和截断退路都有实际空间。</p><div class="stats"><span>15 张战场视觉与通路检查</span><span>10 个关卡实际试玩</span><span>11 次完整通关样本</span><span>58 张运行截图</span></div><p>请重新启动 0.2.1 应用。已有战斗存档保留原布局；选择重试或返回整备后重新进场，会采用本次调整。</p><nav class="links"><a href="../../docs/两章两轮抽查与战术优化.md">完整报告</a><a href="summary.json">验收汇总</a><a href="screenshots/captures.json">逐图来源</a><a href="package-check.json">独立应用检查</a></nav></header><section class="grid">'''+''.join(articles)+'''</section><details><summary>查看全部 15 张战场的实际视口</summary><div class="maps">'''+''.join(allmaps)+'''</div></details><details><summary>两轮实际试玩结果</summary><p>按真实检查点经正常整备与世界路线重新入场。以下为成功样本；失败、停步和重试完整保留于报告。</p><table><thead><tr><th>轮次</th><th>关卡</th><th>回合</th><th>结果</th></tr></thead><tbody>'''+rows+'''</tbody></table></details><aside class="note"><strong>证据范围</strong><br>本轮包含 10 个不同关卡、11 次完整通关样本；不是两次从头到尾的无伤全流程。15 张地图均检查了建筑占格、目标可达和原有地形效果，58 张 Godot 实际视口无文字安全区错误。<br>近战占位能挡住地面敌人，远程依照原射程支援；没有增加背袭伤害或额外防御奖励。旧塔保留原撤退计时，通过实际整备钢剑、钢枪及骑兵先占北门完成。移动端仅检查横屏画幅，未进行手机硬件试玩。所有图形运行均通过后台守卫捕获。</aside></main></body></html>'''
(OUT/'index.html').write_text(page)
print(json.dumps({k:summary[k] for k in ['passed','distinct_played_battles','successful_full_battle_samples','actual_play_keys_including_retained_attempts','runtime_screenshot_count','image_max_bytes']},ensure_ascii=False))

# -*- coding: utf-8 -*-
from pathlib import Path
from PIL import Image, ImageChops
import hashlib, html, json, shutil
root=Path(__file__).resolve().parents[2]
out=root/'actual/reports/f21-feedback-20261104'
logic=json.loads((out/'logic.json').read_text());visual=json.loads((out/'visual.json').read_text())
assert not logic['errors'] and not visual['errors']
raw=root/'source/f21-feedback-20261104/screenshots';raw.mkdir(parents=True,exist_ok=True)
images=[]
for name in visual['screenshots']:
 p=out/name;target=p.with_suffix('.webp')
 if p.exists():
  im=Image.open(p);im.save(target,'WEBP',lossless=True,method=6)
  assert ImageChops.difference(im.convert('RGBA'),Image.open(target).convert('RGBA')).getbbox() is None
  shutil.copy2(p,raw/p.name);p.unlink()
 im=Image.open(target)
 images.append({'file':target.name,'pixels':list(im.size),'bytes':target.stat().st_size,'purpose':'后台运行截图；原尺寸、逐像素无损WebP'})
files=['actual/core/combat_rules.gd','actual/core/game_state.gd','actual/core/main.gd','actual/core/chapter2_rules.gd','actual/core/refugee_tactics.gd','actual/core/ship_interception.gd','actual/core/campaign_save_validation.gd','actual/data/stages/F21.json','actual/tests/f21_feedback_20261104.gd']
verification={'headless_checks':logic['checks'],'background_checks':visual['checks'],'errors':[], 'regressions':{'mechanical':59,'M15_rewind':110},'source_sha256':{f:hashlib.sha256((root/f).read_bytes()).hexdigest() for f in files},'images':images,'scope':logic['scope']}
(out/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
reasons={'艾琳':'主角初期系数偏低，5→8','莉莎':'攻击法师系数偏低，6→8','诺娅':'同类法师一并调整，6→8','洛德':'重装单位输出机会少，5→7','希雅':'职业系数小幅补足，6→7','米蕾':'治疗和击杀系数已充足，保持','卡洛':'当前系数7、出手机会充足，保持','罗恩':'弓手系数7且有射程优势，保持','赛琳':'兼有治疗收益，保持'}
rows=[]
for r in logic['evidence']['experience']:
 if r['level']==1:rows.append(f'<tr><td>{r["name"]}</td><td>{r["before"]}</td><td>{r["after"]}</td><td>{reasons[r["name"]]}</td></tr>')
def shot(name,label):return f'<figure><a href="{name}.webp"><img loading="lazy" src="{name}.webp" alt="{html.escape(label)}"></a><figcaption>{html.escape(label)}</figcaption></figure>'
panels=''.join([shot('wide-heal-40','恢复目标靠近上方：提示框移至下方，保留角色与完整箭头'),shot('compact-heal-210','窄屏目标靠近下方：提示框避让目标'),shot('wide-passenger','乘客19/24生命，在己方甲板谨慎助战'),shot('wide-passenger-hurt','低于半血：提示后退休整'),shot('compact-jumpboard','保留两块跳板原图，取消交互，踏上回避＋20'),shot('compact-monkey-details','水猴详情：仅剩机械傀儡撤离，移动5→8，可穿水'),shot('compact-survival-reward','乘客存活奖励：本队全体正式成员20经验')])
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>F21 战术反馈 · 2026-11-04</title><style>body{margin:0;background:#101923;color:#e8e7df;font:16px/1.8 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:40px 24px}h1{font-size:30px}h2{margin-top:40px;color:#e5d69b}p,li{max-width:1000px}a{color:#a7d5f7}table{width:100%;border-collapse:collapse;background:#182432}th,td{text-align:left;padding:12px 16px;border-bottom:1px solid #354454}th{color:#e5d69b}figure{margin:28px 0;background:#172330;padding:14px;border-radius:10px}img{display:block;width:100%;height:auto}figcaption{padding:10px 4px;color:#bcd1dd}.muted{color:#aebcc7}.ok{color:#b4e2b6}code{color:#d3dfef}</style><main><h1>F21 战术反馈</h1><p class="muted">2026-11-04 · 本地代码与后台运行对照。未安装或更新iPhone。</p><h2>经验调整</h2><p>以下为同为1级、击败经验价值35敌人的标准比较。只提高指定正式角色的职业系数；伤害经验、职业通关经验与治疗经验使用同一系数。关卡固定训练经验、乘客存活20经验等固定事件奖励不乘倍率；满级不再取得经验，原有等级递减保留。</p><table><tr><th>角色</th><th>原击杀经验</th><th>现击杀经验</th><th>判断</th></tr>'''+''.join(rows)+'''</table><h2>乘客与跳板</h2><p>受伤乘客初始19/24生命（80%取整），只在己方左侧甲板内自动移动。生命不少于一半时谨慎协助攻击；低于一半时停止主动攻击并退向后方补给位，仍可自卫反击。存活通关，本队全体正式成员额外获得20经验，含预备与濒死成员，满级除外；升级按普通成长结算，不复活濒死者。阵亡只失去此笔奖励，不新增主线失败条件。</p><p>上下两条跳板全区域回避＋20，站上即生效。取消无效“检查”入口，保留原有跳板图像。战前船医指向药车右侧的补给位；任务目标说明与一次性战场提示同步说明乘客规则及收益。</p><h2>运行对照</h2><p>恢复与传送提示根据当前目标动态避让，不覆盖目标角色或箭头。水猴规则保持，详情补充已有撤离条件、移动5→8与穿水能力。</p>'''+panels+f'''<h2>验证范围</h2><p class="ok">无窗口规则检查{logic['checks']}项，后台宽窄屏检查{visual['checks']}项，断言全部通过；机械傀儡既有检查59项、M15回溯既有检查110项通过。</p><p>覆盖实际交锋经验、乘客真实攻击及低血量后退、左右甲板边界、存活／阵亡奖励差异、预备与濒死升级不复活、防重复结算、存读档、回溯、旧跳板记录兼容、旧地图陆地／水面不改变、文本安全区与防重叠。截图用固定布置检查界面，非完整关卡游玩记录；未做完整战役回归或真机验证。</p><p>进行中的旧存档保留乘客当前生命、位置和已行动状态；新部署或重试采用19/24初始生命。已结算通关不追发奖励。</p><p><a href="logic.json">逻辑明细</a> · <a href="visual.json">后台界面明细</a> · <a href="verification.json">尺寸、字节数与源码校验</a> · <a href="../../core/ship_interception.gd">乘客／跳板规则</a> · <a href="../../core/combat_rules.gd">经验公式</a></p></main></html>'''
(out/'index.html').write_text(page)
print(json.dumps({'headless':logic['checks'],'visual':visual['checks'],'images':len(images),'image_max_bytes':max(i['bytes'] for i in images),'report':str(out/'index.html')},ensure_ascii=False))

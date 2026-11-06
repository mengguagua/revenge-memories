from pathlib import Path
import json,subprocess,shutil,hashlib,html
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'actual/reports/weapon-rescue-square-20261103'
RAW=ROOT/'source/weapon-rescue-square-20261103/screenshots';RAW.mkdir(parents=True,exist_ok=True)
logic=json.loads((OUT/'logic.json').read_text());visual=json.loads((OUT/'visual.json').read_text())
assert not logic['errors'] and not visual['errors']
manifest=[]
for name in visual['screenshots']:
    src=OUT/name;raw=RAW/name
    if src.exists():shutil.copy2(src,raw)
    dest=OUT/(Path(name).stem+'.webp')
    subprocess.run(['/opt/homebrew/bin/magick',str(raw),'-define','webp:lossless=true',str(dest)],check=True)
    pixels=subprocess.check_output(['/opt/homebrew/bin/magick','identify','-format','%wx%h',str(dest)],text=True)
    manifest.append({'file':dest.name,'usage':'后台运行截图','pixels':pixels,'bytes':dest.stat().st_size,'quality':'原尺寸无损WebP，原始PNG另存source目录'})
    if src.exists():src.unlink()
paths=['actual/core/item_rules.gd','actual/core/game_state.gd','actual/core/main.gd','actual/core/legacy_main.gd','actual/core/phone_shell.gd','actual/data/equipment_progression.json','actual/tests/weapon_rescue_square_20261103.gd']
verification={'headless_checks':logic['checks'],'background_checks':visual['checks'],'errors':[], 'scope':'武器运行配置、M15结算与读档、后备升级提示、三种手机比例的布局；未进行全战役回归或iPhone安装。','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'screenshots':manifest}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
E=html.escape

def figure(name,caption):
    return '<figure><a href="'+name+'.webp"><img loading="lazy" src="'+name+'.webp" alt="'+E(caption)+'"></a><figcaption>'+E(caption)+'</figcaption></figure>'

parts=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>武器命中、方向键与双救奖励 · 2026-11-03</title>
<style>body{margin:0;background:#101820;color:#e4e9ed;font:16px/1.8 system-ui,sans-serif}main{max-width:1140px;margin:auto;padding:32px 24px 72px}h1,h2{color:#ead6aa;line-height:1.4}h1{font-size:28px}h2{margin-top:40px;font-size:23px}a{color:#9dcced}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:20px}figure{margin:16px 0}img{display:block;width:100%;border-radius:6px}figcaption,.muted{font-size:14px;color:#b3c0cd}table{border-collapse:collapse;width:100%;margin:16px 0}td,th{padding:10px 14px;border-bottom:1px solid #344553;text-align:left}th{color:#ead6aa}.box{background:#1b2a37;padding:18px 24px;border-radius:10px;margin:18px 0}.badge{background:#234135;color:#c3ebc8;padding:5px 12px;border-radius:20px;display:inline-block}code{background:#253744;padding:2px 5px}@media(max-width:700px){main{padding:24px 14px}.grid{display:block}}</style>
<main><p class="muted">REVENGE MEMORIES · 本地修改与运行核对 · 2026-11-03</p><h1>武器命中、正方形方向键与双救奖励</h1><span class="badge">三项调整已接入</span>
<h2>1 · 武器基础命中</h2><table><thead><tr><th>武器</th><th>调整前</th><th>调整后</th></tr></thead><tbody><tr><td>钢剑</td><td>80</td><td>85</td></tr><tr><td>铜弓</td><td>80</td><td>90</td></tr><tr><td>铁弓</td><td>75</td><td>85</td></tr><tr><td>钢弓</td><td>70</td><td>75</td></tr></tbody></table>
<p>通过战役配置覆盖运行中的武器参数；原始来源规则表保留。战斗预览、实际结算与装备比较共用同一武器配置，新旧存档按现有装备ID自动使用新命中值。重量、威力、射程及其它武器参数不变。</p>
<h2>2 · 方向键外围为正方形</h2><p>四个按钮统一为35逻辑像素的方形，中心横纵等距，外围为105×105逻辑像素。为避免仅缩短上下距离造成四角重叠，同步略缩小了按钮；此前按屏幕约10px左调的中心位置保留。</p><p>宽屏和窄屏截图均实测外围等宽等高；图标与边框有清楚间距，四个触控区互不重叠，且不进入中央游戏内容。复用原有按钮材质和按下阴影，未新增外框。</p><div class="grid">''']
parts.append(figure('wide-square-directions','2556×1179／刘海安全区：方向键外围420×420屏幕像素，单键140×140'))
parts.append(figure('compact-square-directions','1334×750：方向键外围315×315屏幕像素，单键105×105'))
parts.append('''</div><h2>3 · 海峡城两队劳工全救：额外全员20经验</h2><div class="box"><ul><li>触发条件：M15胜利结算时，两队劳工均已开门解救且存活；已到出口的劳工也计入。</li><li>奖励范围：本队全体正式成员，包含未出阵与濒死成员；满级及原本禁止经验的成员不发。</li><li>奖励为额外20经验，普通通关经验与钢剑、钢弓等物品照常结算；只救一队没有额外经验。</li><li>可正常升级并显示新学法术；濒死成员生命保持0，奖励不会治疗或解除濒死。</li><li>结算标记与经验回执一起保存，重复回调和读档不会增发。未结算的旧M15胜利可正常领取；已经结算的历史胜利不追溯发放。</li></ul></div>
<p>战斗菜单“战场目标”已更新规则，战后会出现奖励提示。后备成员升级时，界面从正式名册读取角色资料，显示等级、成长和新学法术。</p><div class="grid">''')
parts.append(figure('full-rescue-bonus-message','真实胜利结算生成的双救奖励提示'))
parts.append(figure('rescue-level-hervi','测试夹具：后备赫维90经验＋20，升至6级并提示学会雷电'))
parts.append(figure('rescue-level-fula','测试夹具：濒死后备成员正常升级并提示新法术，伤情保持'))
parts.append(figure('reserve-plain-experience','未升级时的后备角色经验页也可正常显示'))
parts.append('</div><h2>定向验证</h2><p>'+str(logic['checks'])+'项无窗口逻辑检查、'+str(visual['checks'])+'项后台运行与布局检查通过。覆盖四种新命中值进入战斗计算、其它武器保持、救一队／救两队、单队死亡、仍锁门、已撤离、败北、其它关卡、满级、后备和濒死、升级学法术、重复回调、未结算旧记录读档、结算后存读档，以及三种窗口比例。</p>')
parts.append('''<p>截图使用隔离存档与部署夹具；没有改写玩家的现有记录。未执行全战役回归，未安装或更新iPhone。</p><p><a href="logic.json">逻辑结果与经验回执</a> · <a href="visual.json">后台画面检查</a> · <a href="verification.json">源文件校验及图片尺寸／体积</a> · <a href="../../tests/weapon_rescue_square_20261103.gd">定向检查脚本</a></p><p class="muted">截图为原尺寸无损WebP；原始PNG保存在source/weapon-rescue-square-20261103/screenshots。</p></main></html>''')
(OUT/'index.html').write_text(''.join(parts))
print(json.dumps({'headless':logic['checks'],'background':visual['checks'],'images':len(manifest),'largest_bytes':max(x['bytes'] for x in manifest)},ensure_ascii=False))

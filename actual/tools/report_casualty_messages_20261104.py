# -*- coding: utf-8 -*-
from pathlib import Path
import json,hashlib,shutil,subprocess,html
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'actual/reports/casualty-messages-20261104'
RAW=ROOT/'source/casualty-messages-20261104/screenshots';RAW.mkdir(parents=True,exist_ok=True)
logic=json.loads((OUT/'logic.json').read_text());visual=json.loads((OUT/'visual.json').read_text());assert not logic['errors'] and not visual['errors']
lines=json.loads((ROOT/'actual/data/casualty_messages_20261104.json').read_text());characters=json.loads((ROOT/'actual/data/campaign.json').read_text())['characters']
notes={'hunapu':'对兄长的牵挂与不愿倒下的心情','daan':'仍盼着攒钱开一家店','otto':'老兵先稳住同伴、护住伤员','fula':'救济者惦记伤者有人接手','lena':'把护送责任托付给同伴','lance':'骑兵重视队伍秩序与撤下安排','beck':'矿工学徒惦记乡亲','hervi':'年轻学徒仍想继续求学','german':'曾替神军做事，仍要留下作证','eileen':'引航学徒惦记船团中的人','mireille':'害怕战斗，仍关心伤员','lisa':'性急，不甘心退下','carlo':'旧护卫不愿再次失约','lord':'工匠仍想回去修船','roan':'渔民仍想回海上生活','shia':'护岛骑士惦记航灯','noya':'仍记着对船团的亏欠','celine':'医者不愿落下无法行走的病人'}
images=[]
for name in visual['screenshots']:
 p=OUT/name;raw=RAW/name
 if p.exists():shutil.copy2(p,raw)
 dest=OUT/(Path(name).stem+'.webp');subprocess.run(['/opt/homebrew/bin/magick',str(raw),'-define','webp:lossless=true',str(dest)],check=True)
 pixels=subprocess.check_output(['/opt/homebrew/bin/magick','identify','-format','%wx%h',str(dest)],text=True)
 images.append({'file':dest.name,'pixels':pixels,'bytes':dest.stat().st_size,'usage':'后台实际运行截图，原尺寸无损WebP'})
 if p.exists():p.unlink()
paths=['actual/core/casualty_rules.gd','actual/core/main.gd','actual/core/legacy_main.gd','actual/data/casualty_messages_20261104.json','actual/tests/casualty_messages_20261104.gd']
verification={'headless_checks':logic['checks'],'background_checks':visual['checks'],'errors':[],'scope':'18名正式角色的数据与头像；普通受击、反噬、地图伤害、掩护；战斗中退场前暂停及结算、待播事件存读档；宽窄屏。非完整战役回归，未安装iPhone。','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'images':images}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n')
E=html.escape
def fig(name,caption):return '<figure><a href="'+name+'.webp"><img loading="lazy" src="'+name+'.webp" alt="'+E(caption)+'"></a><figcaption>'+E(caption)+'</figcaption></figure>'
rows=''.join('<tr><td>'+E(characters[cid]['name_zh'])+'</td><td>'+E(text)+'</td><td>'+E(notes[cid])+'</td></tr>' for cid,text in lines.items())
parts=['''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>友方濒死头像与留言 · 2026-11-04</title><style>body{margin:0;background:#101820;color:#e4e8ed;font:16px/1.8 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:32px 24px 70px}h1,h2{color:#ead6a7;line-height:1.4}h1{font-size:28px}h2{font-size:23px;margin-top:38px}a{color:#9ccbef}.box{padding:18px 24px;background:#1b2b38;border-radius:9px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(380px,1fr));gap:22px}figure{margin:16px 0}img{display:block;width:100%;border-radius:6px}figcaption,.muted{font-size:14px;color:#b5c0cc}table{width:100%;border-collapse:collapse}th,td{padding:10px 13px;border-bottom:1px solid #354453;text-align:left}th{color:#ead6a7}.scroll{overflow-x:auto}summary{cursor:pointer;color:#ead6a7}@media(max-width:700px){main{padding:24px 14px}.grid{display:block}th,td{padding:8px}}</style><main><p class="muted">REVENGE MEMORIES · 2026-11-04 · 本地接入与运行核对</p><h1>友方濒死：本人头像＋一句短留言</h1><div class="box"><p>18名正式队员均已接入。普通战斗生命归零后、退场淡出前，显示本人当前故事阶段的头像和一句留言；确认后继续退场，随后出现撤至照护处的提示。</p><p>文字保持简短、直白，以人物的牵挂和反应表现性格。每条不超过12字符；覆盖宽屏和窄屏，不出现省略号单独占一行。地图伤害产生的濒死沿战场事件显示相同内容。</p></div><h2>战斗退场前的实际画面</h2><div class="grid">''']
parts.append(fig('combat-before-exit-daan','达恩：受击归零后，人物尚未淡出，先显示头像与短句'))
parts.append(fig('combat-before-exit-mireille','米蕾：害怕战斗，仍惦记伤员'))
parts.append(fig('combat-before-exit-hunapu','胡纳普：本人留言先显示，随后仍按原有规则判定本场失败'))
parts.append(fig('combat-before-exit-otto-cover','奥托：掩护时濒死，即使被保护者没有损失生命，也会显示他的留言'))
parts.append('</div><h2>全部18条文案</h2><p>人设依据：<a href="../../../docs2/完整故事剧情.md">《完整故事剧情》第九节</a>与现有战役对白。头像沿用当前角色及故事阶段的资源。</p><div class="scroll"><table><thead><tr><th>角色</th><th>留言</th><th>人设依据</th></tr></thead><tbody>'+rows+'</tbody></table></div><h2>窄屏与后续提示</h2><div class="grid">')
parts.append(fig('compact-carlo','卡洛：在窄屏也完整显示短句，保留图文内边距'))
parts.append(fig('compact-noya','诺娅：惦记欠下的责任，文案适用于现有招募分支'))
parts.append(fig('withdrawal-notice-daanfalse','个人留言之后，保留原有撤至照护处提示'))
parts.append('</div><h2>触发与存档</h2><ul><li>按一次新伤情触发一次；重复处理同一个零生命角色不重复弹出。</li><li>伤情、物品转移及主角失败规则继续使用原结算流程；演习倒地使用原有演习规则。</li><li>战斗中的个人留言属于当前攻击演出，期间不保存尚未完成的攻击。正常结算后保存伤情和后续提示；中断后按现有动作检查点继续。</li><li>已保存的待播个人留言可正常读回，不会因角色已经处于濒死状态而丢失头像或重复加入新留言。</li></ul>')
parts.append('<h2>验证范围</h2><p>'+str(logic['checks'])+'项无窗口逻辑检查、'+str(visual['checks'])+'项后台画面／布局检查通过。18名角色均检查本人头像、短句、重复回调与宽窄屏；代表场景通过实际攻击和掩护行动验证退场前时机、完整结算、系统提示与存档。另检查地图伤害、反噬、未招募人物及演习分支。未运行完整战役回归，未安装或更新iPhone。</p>')
parts.append('<p><a href="logic.json">逻辑结果</a> · <a href="visual.json">后台检查结果</a> · <a href="verification.json">源文件校验与截图尺寸／体积</a> · <a href="../../data/casualty_messages_20261104.json">运行文案数据</a> · <a href="../../tests/casualty_messages_20261104.gd">定向检查脚本</a></p><p class="muted">截图使用隔离的伤害与部署夹具，不代表自然通关记录。原始PNG保存在source/casualty-messages-20261104/screenshots；本页使用原尺寸无损WebP。</p><details><summary>更多运行画面</summary><div class="grid">')
selected={'combat-before-exit-daan','combat-before-exit-mireille','combat-before-exit-hunapu','combat-before-exit-otto-cover','compact-carlo','compact-noya','withdrawal-notice-daanfalse'}
for name in visual['screenshots']:
 stem=Path(name).stem
 if stem not in selected:parts.append(fig(stem,stem))
parts.append('</div></details></main></html>');(OUT/'index.html').write_text(''.join(parts))
print(json.dumps({'headless':logic['checks'],'background':visual['checks'],'messages':len(lines),'max_characters':max(map(len,lines.values())),'images':len(images),'largest_bytes':max(i['bytes'] for i in images)},ensure_ascii=False))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a traceable delivery index from actual play, separate fixtures and guarded captures."""
from pathlib import Path
from PIL import Image
import json,hashlib,html,subprocess
R=Path(__file__).resolve().parents[1];OUT=R/'reports/chapter5'
def read(p):return json.loads((R/p).read_text())
def save(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
state=read('reports/chapter5/state-checks.json');hubs=read('reports/chapter5/hub-checks.json');package=read('reports/chapter5/package-checks.json');visual=read('reports/chapter5/visual/captures.json');real=read('reports/chapter5/screenshots/captures.json')
real['shots'].sort(key=lambda x:x['path'])
rounds=[read('reports/chapter5/play/'+r+'.json') for r in ['round1','round2']];sample=read('reports/chapter5/play/round2finalsafe.json')
assert all(d['passed'] for d in [state,hubs,package,visual,real,sample]+rounds)
assert all(len(d['battles'])==7 and all(b['outcome']=='victory' for b in d['battles']) for d in rounds)
final=read('reports/chapter5/play/round2-ending-complete.json');assert final['flags']['ending_done'] and final['flags']['campaign_complete'] and 534 in final['cleared_stages']
images=[]
for folder in ['visual','screenshots']:
 for p in sorted((OUT/folder).glob('*.png')):
  before=Image.open(p).convert('RGBA').tobytes();subprocess.run(['/opt/homebrew/bin/oxipng','-q','-o','3',str(p)],check=True)
  im=Image.open(p);assert im.convert('RGBA').tobytes()==before
  images.append(dict(path=str(p.relative_to(R)),size=list(im.size),bytes=p.stat().st_size,lossless=True,purpose='真实试玩存档视口' if folder=='screenshots' else '地图／目标／据点定向视口'))
assets=[]
purposes={'palace':'神宫／王都主体','infirmary':'伤兵病房','archive':'旧书库','sun_gate':'神宫门廊','regulator':'地方循环装置','stair':'祭所北侧阶梯','column':'神宫柱廊与桥柱','throne':'七羽神座','temple-tiles':'完整共享图集＋16种新铺地','ending-coast':'结局专用海岸全景，固定16:9'}
for p in sorted((R/'assets/chapter5').glob('*.png')):
 im=Image.open(p);assets.append(dict(path=str(p.relative_to(R)),purpose=purposes[p.stem],size=list(im.size),bytes=p.stat().st_size,quality_note='保留512×288完整色彩与日出渐层，视觉质量优先；无损压缩后303380字节，高于200KB参考值，不牺牲画质' if p.stem=='ending-coast' else '完整原比例位图／16像素原生图块；无损压缩'))
save('asset-footprint.json',assets)
pack=R/'dist/RevengeMemories-0.10.0-Chapter5-20261021.app/Contents/Resources/RevengeMemories.pck'
summary=dict(passed=True,version='0.10.0',chapter5_battles=7,total_battles=40,state_checks=len(state['checks']),hub_checks=len(hubs['checks']),hub_inputs=hubs['inputs'],package_checks=len(package['checks']),rounds=[dict(round=d['round'],inputs=d['inputs'],battles=[{k:b[k] for k in ['code','final_turn','outcome']}for b in d['battles']],stat_edits=d['stat_edits'],forced_victories=d['forced_victories'])for d in rounds],final_sample=dict(passed=sample['passed'],inputs=sample['inputs'],turn=sample['battles'][0]['final_turn']),additional_sample_failure='round2final：终战截图复打时艾琳被击倒，真实失败保留；调整试玩的后排保护策略后round2finalsafe通过，未改游戏数值或强制胜利。',fixes=['修正新增数组的GDScript类型转换','合流结算保留两队归属、成长与装备','完成结局菜单从旧翻页分支分离，支持重看与继续','柱身切片剔除相邻碎片，保持整柱轮廓','神宫院落、岸线、墙柱与据点建筑补齐，入口和出生格连通复检'],screenshots=images,visual_errors=visual['errors']+real['errors'],new_art=assets,source_sha256=hashlib.sha256((R/'reports/chapter4/play/round2-chapter-end.json').read_bytes()).hexdigest(),pck_sha256=hashlib.sha256(pack.read_bytes()).hexdigest(),pck_bytes=pack.stat().st_size,remaining_treatment=4-sum(final['flags']['treatment_used'].values()),limitations=['前四章未在本轮重跑完整流程；读取真实第四章存档并验证章节过渡','角色待机、移动、战斗动画沿用现有代码，未作为本次动画验收对象','图形由Mac Godot后台视口捕获，未进行移动设备实机测试'])
palette_file=R/'reports/chapter5/palette-checks.json'
if palette_file.exists():
 summary['palette_revision']='muted-v2'
 summary['palette_checks']=read('reports/chapter5/palette-checks.json')
 summary['palette_package_checks']=read('reports/chapter5/palette-package-checks.json')
 assert summary['palette_checks']['passed'] and summary['palette_package_checks']['passed']
 summary['palette_scope']='本次仅八张建筑／装置调色、11张既有试玩视口更新和导出纹理校验；既有两轮战役检查未重跑。visual目录保留初版定向检查。'
save('delivery-summary.json',summary)
rows=''.join('<tr><td>'+b['code']+'</td><td>'+str(next(x['final_turn'] for x in rounds[0]['battles'] if x['code']==b['code']))+'</td><td>'+str(b['final_turn'])+'</td><td>通过</td></tr>'for b in rounds[1]['battles'])
cards=''.join('<figure><a href="screenshots/'+Path(x['path']).name+'"><img loading="lazy" src="screenshots/'+Path(x['path']).name+'?art=muted-v2" alt="'+html.escape(x['description'])+'"></a><figcaption>'+html.escape(x['description'])+'<small>真实试玩存档 · '+str(x['stage'])+' · 回合'+str(x['turn'])+'</small></figcaption></figure>'for x in real['shots'])
(OUT/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>第五章 · 日光仍在</title><style>*{box-sizing:border-box}body{margin:0;background:#112a30;color:#edf0df;font:16px/1.8 system-ui,sans-serif}main{max-width:1320px;margin:auto;padding:44px 28px}h1{font-size:42px;line-height:1.2;color:#ead5a2}h2{font-size:23px;color:#ead5a2;margin-top:42px}a{color:#8fccc8}header{max-width:860px}section{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,510px),1fr));gap:22px}figure{margin:0;background:#1a353a;border-radius:12px;overflow:hidden}img{display:block;width:100%;height:auto;image-rendering:pixelated;background:#0b171a}figcaption{padding:14px 18px}small{display:block;color:#a5c0bd;font-size:13px}table{border-collapse:collapse;margin:20px 0;width:min(100%,650px)}td,th{text-align:left;padding:10px 18px;border-bottom:1px solid #3d5355}.meta{letter-spacing:.12em;color:#9fb8b2}code{color:#dbc799}</style><main><header><p class="meta">复仇与回忆 · 0.10.0 · CHAPTER V</p><h1>日光仍在</h1><p>素材调色更新：神宫金饰改为旧黄铜，屋顶与布幔改为低饱和灰青色，石墙偏灰米色。下方实机预览与当前运行包已同步。<a href="palette-checks.json">颜色与尺寸检查</a> · <a href="../../assets/chapter5/palette-revision.json">素材路径及编辑提示</a></p><p>王都伤兵撤离、登天桥、祭所修复、日宫与旧书库，最终通向两军前庭和神座。七场战斗、六个据点与实际人物后日谈已接通。</p><p>两轮均从未修改的第四章真实结束档开始：首轮西线先行，第二轮东线先行。分别执行10,166与10,467次按键操作，两轮七战和结局全部通过。人物动作沿用现有代码。</p><p><a href="delivery-summary.json">验证摘要与版本指纹</a> · <a href="asset-footprint.json">新素材尺寸与体积</a> · <a href="../../docs/第五章交付与两轮验收.md">完整交付记录</a></p></header><h2>两轮试玩</h2><table><tr><th>战场</th><th>第一轮结束回合</th><th>第二轮结束回合</th><th>结果</th></tr>'''+rows+'''</table><p>另完成430项定向状态检查、31项据点／结局检查及53项独立运行包检查。终战截图复打曾出现一次真实战败；保留失败记录，调整后排保护策略后再次通关，没有改属性或强制胜利。</p><h2>实机截图</h2><section>'''+cards+'''</section><h2>地图与交互边界</h2><p>完整建筑与碰撞占地一致，装置从南面操作；医舍前路连接南口，桥柱不侵入桥面，水池不允许步行。两队分别确认名单后才合流；旧书库关闭前提供明确提醒。普通攻击与法术可全阶段伤害终战实体，半血仅一波援军。结局保留濒死照护与真实未招募状态。</p><p><small>截图使用禁止窗口显示与激活的后台Godot视口捕获，只做无损压缩。未在本轮重跑前四章全流程或进行移动设备实机测试。新建筑、铺地和结局原图保留在离线source/chapter5，导出包已验证排除原图。</small></p></main></html>''')
print(json.dumps(dict(passed=True,images=len(images),real_screenshots=len(real['shots']),assets=len(assets),state_checks=len(state['checks']),hub_checks=len(hubs['checks']),package_checks=len(package['checks'])),ensure_ascii=False))

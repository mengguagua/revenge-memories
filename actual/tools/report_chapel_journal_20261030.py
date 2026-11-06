from pathlib import Path
from collections import defaultdict
from html import escape as esc
import json
import subprocess
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'actual/reports/chapel-journal-20261030'
data=json.loads((OUT/'balance-data.json').read_text())
logic=json.loads((OUT/'logic.json').read_text());visual=json.loads((OUT/'visual.json').read_text())
assert not logic['errors'] and not visual['errors']
fields=['max_hp','strength','skill','speed','luck','defence','resistance','move']
labels=['生命上限','力量','技巧','速度','幸运','物防','魔防','移动']
rules=json.loads((ROOT/'actual/data/legacy/rules_full.json').read_text())
def name(cid):return data['classes'][str(int(cid))]['name_zh']
def number(n):return str(int(n))
def table(head,rows,cls=''):
    return '<div class="scroll"><table class="'+cls+'"><thead><tr>'+''.join('<th>'+esc(str(x))+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(str(x))+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'
images=[]
def figure(file,title):
    p=OUT/file
    if p.stat().st_size>=200000:
        out=p.with_suffix('.webp');subprocess.run(['/opt/homebrew/bin/magick',str(p),'-define','webp:lossless=true',str(out)],check=True);p=out
    with Image.open(p) as im:size=list(im.size)
    images.append({'path':p.name,'dimensions':size,'bytes':p.stat().st_size,'quality':'Full runtime pixels, lossless optimized when useful.'})
    return f'<figure><a href="{p.name}"><img loading="lazy" src="{p.name}" alt="{esc(title)}"></a><figcaption>{esc(title)}</figcaption></figure>'
shots=''.join(figure(f,t)for f,t in [('world-menu.png','当前任务位于部队整备下方'),('current-task.png','日记依据当前进度给出下一步'),('lena-pegasus.png','蕾娜：正式天马骑士素材'),('old-chapel.png','旧塔教堂：室内中殿、长椅、彩窗、祭台和救治点'),('promotion-list.png','调查祭台，先选择成员'),('promotion-locked.png','未达到条件：明确缺少等级'),('promotion-preview.png','按当前成员显示八项数值前后变化'),('promotion-confirm.png','独立二次确认，默认返回预览'),('promotion-done.png','确认后提交并保存'),('compact-preview.png','紧凑手机布局的进阶预览')])
promotion_rows=[];delta_rows=[]
for r in data['promotions']:
    a,b=int(r['from']),int(r['to']);base=r['bases']
    promotion_rows.append([name(a)+' → '+name(b),number(r['level'])]+[number(base[k]) for k in fields[:6]]+[('-15职业加成' if a==10 else '+15职业加成' if b==10 else '个人魔防不变'),f'{number(r["move_before"])} → {number(r["move_after"])}'])
    old=rules['promotion_bases'][str(a)];d={k:max(int(old[k]),int(base[k]))-int(old[k])for k in fields[:6]}
    if not any(d.values()) and int(old['max_hp'])<52:d['max_hp']=1
    delta_rows.append([name(a)+' → '+name(b)]+[('+' if d[k]>0 else '')+str(d[k])for k in fields[:6]]+[(-15 if a==10 else 15 if b==10 else 0),int(r['move_after'])-int(r['move_before'])])
promotions=table(['进阶路线','所需等级']+labels[:6]+['魔防规则','移动前后'],promotion_rows)
deltas=table(['示例路线']+labels,delta_rows)
hero_rows=[]
for actor,spec in data['hero_professions'].items():
    hero_rows.append(['胡纳普' if actor=='hunapu' else '艾琳',spec['name']]+[str(int(spec['bases'][k])) if k in spec['bases'] else '保留' for k in fields[:7]]+[number(spec['move']),'西塔安全停用后' if actor=='hunapu' else '祭所验证／D42推进时'])
heroes=table(['角色','剧情进阶']+labels+['触发'],hero_rows)
groups=defaultdict(list)
for e in data['enemies']:groups[(int(e['unit']['class_id']),int(e['unit']['level']))].append(e)
enemy_rows=[];profiles=[]
for (cid,level),entries in sorted(groups.items()):
    ranges=[]
    for k in fields:
        values=[int(e['unit'].get(k,0))for e in entries];lo,hi=min(values),max(values);ranges.append(str(lo) if lo==hi else f'{lo}–{hi}')
    enemy_rows.append([name(cid)+f' (ID {cid})',level,len(entries)]+ranges)
    exact=defaultdict(list)
    for e in entries:exact[tuple(int(e['unit'].get(k,0))for k in fields)+ (int(e['unit'].get('item_id',0)),)].append(e)
    for values,records in exact.items():profiles.append([name(cid)+f' (ID {cid})',level]+list(values)+['、'.join(e['stage']+'/'+e['unit']['id'] for e in records)])
enemy_table=table(['实际职业','等级','单位数']+labels,enemy_rows,'filterable')
profile_table=table(['实际职业','等级']+labels+['装备ID','关卡／单位ID'],profiles,'filterable')
heavy_alias=[e for e in data['enemies'] if e['unit'].get('name_zh')=='重装兵' and int(e['unit']['class_id'])!=2]
examples=table(['关卡／单位','显示名','真实职业','等级']+labels,[[e['stage']+'/'+e['unit']['id'],e['unit']['name_zh'],name(e['unit']['class_id']),number(e['unit']['level'])]+[number(e['unit'].get(k,0))for k in fields]for e in heavy_alias])
art=[]
for f,purpose in [('interior.webp','H04专用室内地图；896×576，完整等比显示于224×144，非九宫格背景'),('altar.png','独立低祭台；128×64，显示32×16，透明轮廓完整')]:
    p=ROOT/'actual/assets/old-chapel-20261030'/f
    with Image.open(p) as im:size=list(im.size)
    art.append({'path':str(p.relative_to(ROOT)),'dimensions':size,'bytes':p.stat().st_size,'purpose':purpose})
(OUT/'image-sizes.json').write_text(json.dumps({'runtime_assets':art,'screenshots':images},ensure_ascii=False,indent=2)+'\n')
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>任务日记、旧教堂与职业进阶</title><style>
:root{{color-scheme:dark;font:16px/1.8 system-ui,-apple-system,sans-serif;color:#e1e8ed;background:#10181f}}body{{max-width:1500px;margin:auto;padding:30px 24px 70px}}h1,h2,h3{{color:#ead8ac;line-height:1.4}}h2{{margin-top:44px}}p{{max-width:1100px}}a{{color:#e2c486}}nav{{display:flex;gap:20px;flex-wrap:wrap}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}figure{{margin:0}}img{{width:100%;display:block}}figcaption{{padding:10px 0 20px;color:#b8c8d2}}.scroll{{overflow:auto;margin:22px 0}}table{{border-collapse:collapse;min-width:100%;font-size:14px}}th,td{{padding:10px 13px;text-align:left;border-bottom:1px solid #354450;white-space:nowrap}}th{{color:#e5cd9a;background:#1b2b37}}td:last-child{{white-space:normal;min-width:90px}}.badge{{display:inline-block;padding:8px 16px;background:#234031;border-radius:24px}}input{{padding:12px 16px;width:min(85%,560px);background:#213441;color:white;border:0;border-radius:6px;box-shadow:0 0 0 2px #516371}}.note{{background:#20313b;padding:18px 22px;border-radius:12px}}details{{margin:24px 0}}summary{{cursor:pointer;color:#e5cd9a}}@media(max-width:850px){{.grid{{grid-template-columns:1fr}}body{{padding:18px 14px}}}}
</style><h1>任务日记、旧教堂与职业进阶</h1><p>2026-10-30 · 修改、运行验证与数值说明。以下截图来自电脑上的 Godot 后台手机布局渲染，本次未更新 iPhone。</p><span class="badge">{logic['checks']}项逻辑检查 · {visual['checks']}项后台检查通过</span><nav><a href="#changes">六项修改</a><a href="#shots">运行截图</a><a href="#promotion">全部进阶数值</a><a href="#enemy">敌军同级同职业数据</a><a href="#checks">验证与来源</a></nav>
<h2 id="changes">已实施的修改</h2><p>大世界菜单在“部队整备”下方新增“当前任务”，以旅程日记呈现下一步。第一章明确识别分粮、取军令、教堂合作等道路门槛；后续章节根据当前队伍、战斗完成和交接状态更新提示，包括第四章需要切换东队取得观测步骤的情况。</p><p>蕾娜确实是天马骑士（职业3），已使用对应职业地图形象；招募后也按当前职业取图。兰斯是骑兵（职业1），显示骑乘形象。赫兰直接复用序章修长版素材，不再使用年轻通用人物。</p><p>旧塔教堂改为室内中殿，补入石墙、彩窗、长椅、中央通道、低祭台和救治侧龛。场景碰撞按长椅与墙壁设置，祭台、赫兰、兰斯、救治点都有可达的相邻交互格。旧存档若落在新长椅内，会回到入口空地。</p><p>祭台现在依次为：选择成员 → 查看条件与八项数值变化 → 继续确认 → 明确确认进阶。未达等级、濒死、阵亡或没有进阶路线都会说明原因。默认二次确认选择“返回预览”；取消不改数值，提交前重新核对状态，保存失败会回滚。其他据点的普通职业进阶入口也复用此流程。</p>
<h2 id="shots">运行截图</h2><div class="grid">{shots}</div>
<h2 id="promotion">全部普通职业进阶路线与数值</h2><p><strong>进阶是“补足目标下限”，不是固定加点。</strong>生命上限、力量、技巧、速度、幸运和物防分别取 max（当前值，目标下限）。已有高值保留；若这六项均没有增长，生命上限额外+1，最高52。普通进阶等级归1、经验归0，当前生命回满；个人成长率和持有装备保留，装备是否适用由新职业重新判断。移动直接改成目标职业的基础移动。</p><p>魔防通常保留个人值；进阶剑豪附加15职业魔防，剑豪回乡勇时移除这15点。乡勇转术法师会重新设置法术与个人训练计数；转女魔剑士、济世术师、博学术师时保留既有标记并补入职业通用标记。其他普通进阶保持训练计数。</p><p>下表的六项能力是<strong>目标职业最低值</strong>。因此“力量16”表示不足16时补到16，不是每次增加16。</p>{promotions}
<details><summary>展开：以原职业下限为起点，逐路线计算的增量示例</summary><p>为了可比，假设角色当前六项属性恰为原职业下限，尚未计算练级所得；实际队员在游戏预览中按自身数值计算。魔防列仅列职业加成变化。</p>{deltas}</details>
<h3>两位主角的剧情进阶</h3><p>主角采用单独的剧情职业规则：补足下列基础值，保留当前等级、经验、当前生命、训练、装备及成长率；不会因进阶自动回满当前生命。胡纳普进阶后剑弓兼用；艾琳已掌握的攻击法术生命消耗减少1，最低1。它们不是祭台的普通等级转职，也不使用旧“勇者／公主”ID直接替换当前职业。</p>{heroes}
<h2 id="enemy">敌方同等级、同职业如何设计</h2><p>当前敌军是<strong>关卡定值配置，再叠加已登记的平衡修订</strong>。等级不是一条统一公式的输入，敌军也不按我方的职业进阶下限生成。因此同职业同等级可以因关卡、首领身份或特定职责而数值不同。早期生成器曾按章节与首领身份设置生命、力量、技巧、速度、物防，后续关卡又有独立配置；本表以当前加载后的数据为准。</p><div class="note"><strong>关于“1级重装兵”：</strong>实际职业ID 2的重装兵在当前关卡配置中没有1级样本，最低为3级。常见3级样本是生命26、力量9、技巧4、速度3、幸运0、物防6、魔防1、移动4。相比之下，我方士兵转职得到的1级重装兵最低生命34、力量16、技巧2、速度2、幸运0、物防12、移动4，个人魔防保留。两套生成方式不同，所以不能直接按等级横比强弱。</div>
<p>此外，M15有历史命名不一致：以下单位显示名为“重装兵”，但真实职业ID是7，即大骑士。统计按真实职业ID归类；本次记录这项问题，没有据此改动敌军强度。</p>{examples}
<h3>按真实职业与等级汇总</h3><p>共统计{len(data['enemies'])}个当前关卡敌军及预设援军实例。范围表示该分组的最小值至最大值；单值表示一致。均为裸属性，未叠加武器威力、装备防御、地形或状态。动态召唤单位依其召唤模板生成，未计入关卡预设实例。</p><input id="filter" placeholder="筛选职业、等级或单位ID，例如：重装兵、M15_e6" aria-label="筛选数值表">{enemy_table}<details><summary>展开全部实际属性组合及关卡单位ID</summary>{profile_table}</details>
<h2 id="checks">验证与来源</h2><p>已检查任务门槛更新、世界菜单入口、普通进阶全部18条路线、未达等级原因、八项预览、取消无修改、重复确认与过期预览拦截、濒死限制、确认后保存与读取、教堂全部交互点可达、旧位置迁移、三位人物素材，以及两种手机布局的文字安全区。图形进程在启动前加载防激活保护，使用引擎视口后台捕获。本轮没有全关卡战斗回归或真机触控验收。</p><p>新教堂与低祭台使用内置 imagegen 制作，原图和提示词保留在 source/old-chapel-20261030；背景专用于896×576源尺寸、224×144逻辑尺寸，完整等比显示。运行图和截图尺寸、字节数均有记录。</p><p><a href="logic.json">逻辑结果</a> · <a href="visual.json">呈现结果</a> · <a href="balance-data.json">全部提取数据</a> · <a href="image-sizes.json">图片记录</a> · <a href="../../../source/old-chapel-20261030/prompt.json">生成提示词</a> · <a href="../../core/unit_progression.gd">普通进阶规则</a> · <a href="../../core/hero_professions.gd">主角进阶规则</a> · <a href="../../data/enemy_balance_20261025.json">敌军平衡修订</a></p>
<script>document.getElementById('filter').addEventListener('input',e=>{{let q=e.target.value.trim().toLowerCase();document.querySelectorAll('.filterable tbody tr').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));}});</script></html>'''
(OUT/'index.html').write_text(page)
print(json.dumps({'page':str(OUT/'index.html'),'routes':len(promotion_rows),'enemy_instances':len(data['enemies']),'enemy_groups':len(groups),'profiles':len(profiles)},ensure_ascii=False))

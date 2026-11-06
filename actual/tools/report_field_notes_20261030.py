from pathlib import Path
from html import escape
from PIL import Image
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'actual/reports/field-notes-20261030'
ASSETS = ROOT / 'actual/assets/field-notes-20261030'
logic = json.loads((OUT / 'logic.json').read_text())
visual = json.loads((OUT / 'visual.json').read_text())
assert not logic['errors'] and not visual['errors']
assets = []
for name, purpose in [('diary.webp', '旅程日记专用纸页；固定 8:5 等比显示，不作九宫格拉伸'), ('chapel-open.webp', 'H04 专用地图；224×144 逻辑像素等比显示，救治侧龛右侧开放')]:
    path = ASSETS / name
    with Image.open(path) as im: size = list(im.size)
    assets.append({'file': name, 'pixels': size, 'bytes': path.stat().st_size, 'purpose': purpose,
                   'source': 'source/field-notes-20261030/', 'processing': 'ImageMagick proportional resize, WebP quality 94; alpha preserved for diary'})
(ASSETS / 'manifest.json').write_text(json.dumps({'assets': assets, 'visual_check': 'Source and runtime screenshots inspected. No ornament stretching; complete borders and alpha edges.'}, ensure_ascii=False, indent=2))
(ROOT / 'source/field-notes-20261030/generation.json').write_text(json.dumps({
    'tool': 'built-in imagegen',
    'chapel': {'source': 'chapel-opening-source.png', 'reference': 'actual/assets/old-chapel-20261030/interior.webp', 'brief': 'Keep church geometry and lighting; remove lower east wall of southwest healing alcove. Connect its floor directly to the aisle; no door or low barrier.'},
    'diary': {'source': 'diary-source.png', 'brief': 'Wide blank ivory parchment folio inside navy leather, restrained gold corner caps, left binding, transparent exterior. Clear central writing area. Fixed 8:5 use.'},
    'originals': 'Generated originals remain separate from runtime assets.'
}, ensure_ascii=False, indent=2))
images = []
def figure(name, title):
    p = OUT / (name + '.png')
    q = p.with_suffix('.webp')
    subprocess.run(['/opt/homebrew/bin/magick', str(p), '-define', 'webp:lossless=true', str(q)], check=True)
    with Image.open(q) as im: size = list(im.size)
    images.append({'file': q.name, 'pixels': size, 'bytes': q.stat().st_size, 'purpose': title, 'quality': 'Full-resolution engine viewport; lossless WebP, original PNG retained.'})
    return f'<figure><a href="{q.name}"><img src="{q.name}" alt="{escape(title)}" loading="lazy"></a><figcaption>{escape(title)}</figcaption></figure>'

journal = figure('current-task', '旅程日记：纸页材质、较大正文、按语意换行，保留当前世界作为背景')
chapel = figure('fountain-entrance', '沿南侧通道走到泉水右边，朝左面对泉水') + figure('fountain-interaction', '按确认后进入救治选择；这是实际输入路径产生的运行截图')
flow = ''.join(figure(n, t) for n, t in [
    ('promotion-list', '调查祭台：260×184 的紧凑选人弹框，每页最多三项'),
    ('promotion-preview', '选择同伴：当前职业 → 目标职业，左右战斗身体和八项属性变化'),
    ('promotion-locked', '等级不足仍可看结果，并明确显示所需等级、当前等级和差额'),
    ('promotion-confirm', '第二次确认默认选中返回预览，明确等级、经验和生命的变化')])
small = ''.join(figure(n, t) for n, t in [
    ('minimum-journal', '最小 256 逻辑像素视口：日记保持字号，长文分页'),
    ('minimum-journal-next', '点按下页可继续阅读完整任务'),
    ('minimum-preview', '窄屏预览：兵种在上，八项属性排成两列'),
    ('minimum-confirm', '窄屏二次确认，按钮与文字保留内容安全区')])
data = json.loads((OUT / 'balance-data.json').read_text())
routes = []
for route in data['promotions']:
    a, b = int(route['from']), int(route['to'])
    name = data['classes'][str(a)]['name_zh'] + ' → ' + data['classes'][str(b)]['name_zh']
    routes.append((f'route-{a}-{b}', name))
route_gallery = ''.join('<article class="route" data-route="'+escape(title)+'">'+figure(name, title)+'</article>' for name,title in routes)
preview = json.loads((OUT / 'promotion-preview.json').read_text())['record']
statrows = ''.join(f'<tr><td>{escape(row["label"])}</td><td>{row["before"]}</td><td>{row["after"]}</td><td class="gain">{row["delta"]:+d}</td></tr>' for row in preview['rows'])
assetrows = ''.join(f'<tr><td>{escape(a["file"])}</td><td>{a["pixels"][0]}×{a["pixels"][1]}</td><td>{a["bytes"]:,} B</td><td>{escape(a["purpose"])}</td></tr>' for a in assets)
checks = ''.join('<li>'+escape(t)+'</li>' for t in visual['labels'])
page = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>旅程日记与职业进阶 · 运行验收</title>
<style>
:root{{color-scheme:dark;--bg:#0d1720;--paper:#ede5cf;--ink:#d9e0e7;--muted:#a6b4c1;--gold:#dfc38b}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.8 system-ui,-apple-system,"PingFang SC",sans-serif}}main{{max-width:1200px;margin:auto;padding:44px 24px 80px}}header{{max-width:880px;margin-bottom:32px}}h1{{font-size:clamp(28px,4vw,46px);line-height:1.3;color:var(--paper);margin:12px 0}}h2{{font-size:26px;color:var(--paper);margin:44px 0 12px}}h3{{font-size:18px;margin:0 0 8px;color:var(--gold)}}p{{max-width:900px;margin:12px 0}}.eyebrow{{font-size:13px;letter-spacing:.15em;color:var(--gold)}}.muted,figcaption{{color:var(--muted)}}a{{color:var(--gold);text-underline-offset:4px}}a:focus-visible,select:focus-visible{{outline:none;box-shadow:0 0 0 5px #dbc28d44}}nav{{display:flex;gap:18px;flex-wrap:wrap;padding:18px 0}}.cards,.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.cards{{grid-template-columns:repeat(3,minmax(0,1fr))}}.card{{background:#1a2834;padding:22px;border-radius:12px;box-shadow:0 12px 30px #0002}}figure{{margin:20px 0;background:#0a1119;border-radius:12px;overflow:hidden}}img{{display:block;width:100%;height:auto}}figcaption{{padding:14px 18px;font-size:14px}}table{{width:100%;border-collapse:collapse;font-size:15px}}th,td{{padding:12px 16px;text-align:left;border-bottom:1px solid #33414a}}th{{color:var(--gold);background:#1a2834}}.gain{{color:#b2d9bf}}.scroll{{overflow:auto}}.callout{{padding:18px 24px;border-radius:12px;background:#24362f;color:#cbe3d2}}select{{font:inherit;color:var(--paper);background:#24323f;border:0;border-radius:8px;padding:12px 18px;min-width:240px}}.route[hidden]{{display:none}}details{{background:#172631;border-radius:10px;padding:18px 24px;margin-top:18px}}summary{{cursor:pointer;color:var(--gold)}}li{{margin:6px 0}}code{{font-size:13px;color:#c8d4dd}}footer{{margin-top:48px;color:var(--muted);font-size:14px}}@media(max-width:760px){{main{{padding:28px 16px 50px}}.cards,.grid{{grid-template-columns:1fr}}}}
</style><main><header><span class="eyebrow">REVENGE MEMORIES · 2026.10.30</span><h1>翻开日记，看清下一步。<br>进阶之前，看见变化。</h1><p>本轮完成任务日志重设计、教堂泉水通路修正和职业进阶界面重做。以下全部游戏画面来自修改后的 Godot 运行视口。</p><p class="muted">使用桌面后台渲染与手机尺寸模拟；本轮未安装或更新 iPhone。</p></header>
<nav><a href="#journal">旅程日记</a><a href="#fountain">泉水入口</a><a href="#promotion">进阶流程</a><a href="#small">小屏幕</a><a href="#routes">全部兵种外形</a><a href="#checks">验证记录</a></nav>
<div class="cards"><div class="card"><h3>日志像一本日记</h3>纸页与装订材质、深色大字正文、按语意换行，内容过长可翻页。</div><div class="card"><h3>泉水有可见入口</h3>右侧墙面留出通道，画面入口与实际行走、朝向交互对齐。</div><div class="card"><h3>先看清，再进阶</h3>小弹框选人 → 职业与属性预览 → 独立二次确认。</div></div>
<section id="journal"><h2>01 · 旅程日记</h2><p>保留现有剧情进度判断。正文从原来的 8 像素改为 12 像素中文字体，按句意与可用宽度排版。纸页按固定 8:5 比例显示，装订、角饰和书签不参与拉伸；小屏幕通过分页容纳全文。</p>{journal}</section>
<section id="fountain"><h2>02 · 泉水入口</h2><p>开放西南侧龛的东侧墙口。从教堂南门进入后，沿下侧走道向左，再向上到泉水右边，朝左按确认即可调查。合作完成后按原有份额与濒死条件打开救治选择。</p><div class="grid">{chapel}</div></section>
<section id="promotion"><h2>03 · 职业进阶</h2><p>入口按内容收紧；列表直接显示同伴、目标职业和等级进度。预览展示当前职业与目标职业的正式战斗素材，完整保留长枪、坐骑、翅膀等轮廓，并按等比例缩放。八项属性同时列出当前值、目标值与增减量，等级与经验的归零变化也明确标出。</p><div class="grid">{flow}</div><div class="callout">选择成员、预览或返回都不会改动角色。条件满足后还要进入第二个弹框，默认选中“返回预览”；只有明确选中“确认进阶”才提交并保存。</div>
<h3 style="margin-top:26px">运行示例：奥托 · 士兵 → 重装兵</h3><p>以下数字直接取自本次运行预览。进阶仍按既有职业下限计算，因此实际增幅取决于该成员的现有属性。</p><div class="scroll"><table><tr><th>属性</th><th>当前</th><th>进阶后</th><th>变化</th></tr>{statrows}</table></div><p><a href="../chapel-journal-20261030/index.html">完整职业下限、进阶规则及敌方同职业数值说明</a> · <a href="promotion-preview.json">本次预览原始记录</a></p></section>
<section id="small"><h2>04 · 小屏幕布局</h2><p>覆盖 2556×1179、1334×750 与 884×480 三种画幅。最窄的游戏区域为 256 逻辑像素；保留两幅职业模型与全部八项属性，按钮使用材质背景和柔和选中光晕。</p><div class="grid">{small}</div></section>
<section id="routes"><h2>05 · 18 条普通进阶路线</h2><p>逐条检查当前与目标职业素材。下面可切换查看最窄视口下的全部路线截图；主角的剧情进阶仍提示剧情条件，不会在祭台直接执行。</p><label for="route">选择路线　</label><select id="route">{''.join(f'<option value="{i}">{escape(title)}</option>' for i,(_,title) in enumerate(routes))}</select>{route_gallery}</section>
<section id="checks"><h2>06 · 验证与素材记录</h2><div class="callout">无窗口检查 {logic['checks']} 项通过；后台运行与布局检查 {visual['checks']} 项通过。文字安全区、文字互相遮挡、完整兵种轮廓、真实泉水交互、取消不改数据和二次确认均已检查。</div><p>测试使用独立临时存档。没有变更进阶数值规则，也没有执行全战役回归。本次检查与截图脚本：<code>actual/tests/field_notes_20261030.gd</code>。</p><div class="scroll"><table><tr><th>素材</th><th>尺寸</th><th>体积</th><th>使用方式</th></tr>{assetrows}</table></div><p>生成原图独立保存在 <code>source/field-notes-20261030/</code>；预览复用现有职业素材，没有另画替代人物。运行素材检查透明边缘、完整边角和等比显示，报告截图保留完整像素并以无损 WebP 提供。</p><p><a href="logic.json">无窗口检查</a> · <a href="visual.json">运行检查</a> · <a href="image-sizes.json">交付图片尺寸与体积</a></p><details><summary>展开运行检查明细（{visual['checks']} 项）</summary><ol>{checks}</ol></details></section><footer>复仇与回忆 · 本地实现与验收报告 · 点击截图可查看原尺寸。</footer></main><script>const routes=[...document.querySelectorAll('.route')];function showRoute(){{routes.forEach((r,i)=>r.hidden=i!==Number(document.getElementById('route').value));}}document.getElementById('route').addEventListener('change',showRoute);showRoute();</script></html>'''
(OUT / 'index.html').write_text(page)
(OUT / 'image-sizes.json').write_text(json.dumps({'assets':assets,'screenshots':images},ensure_ascii=False,indent=2))
print(json.dumps({'html':str(OUT/'index.html'),'images':len(images),'max_image_bytes':max(i['bytes'] for i in images),'logic':logic['checks'],'visual':visual['checks']},ensure_ascii=False))

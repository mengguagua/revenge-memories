"""Build the local acceptance page from recorded logic and offscreen UI checks."""
import html
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/story-accessories-20261023"
logic = json.loads((OUT / "checks.json").read_text())
visual = json.loads((OUT / "captures.json").read_text())
assert logic["passed"] and visual["passed"]
manifest = []
for shot in visual["shots"]:
    path = OUT / (shot["name"] + ".png")
    raw = path.read_bytes()
    width, height = struct.unpack(">II", raw[16:24])
    manifest.append({"file": path.name, "purpose": "后台界面验收截图", "width": width,
                     "height": height, "bytes": len(raw), "native_width": shot["native_width"],
                     "compression": "oxipng lossless; native rendering size preserved"})
(OUT / "image-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

sections = []
for native in [426, 256]:
    cards = []
    for record in manifest:
        if record["native_width"] != native:
            continue
        name = html.escape(record["file"])
        cards.append(f'<figure><a href="{name}"><img src="{name}" loading="lazy" alt="{name}"></a>'
                     f'<figcaption>{name}<br>{record["width"]}×{record["height"]} · {record["bytes"]:,} B</figcaption></figure>')
    sections.append(f'<h2>{native} 像素原生宽度</h2><div class="grid">{"".join(cards)}</div>')

page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>护途盾与续愿戒 · 接入验收</title><style>
body{margin:0;background:#111822;color:#e9e5db;font:16px/1.7 system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:32px 20px}h1{font-size:28px;color:#e5c888}h2{margin-top:36px}
a{color:#adcff2}section{padding:18px 24px;background:#1d2838;border-radius:12px;margin:20px 0}
table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:12px;border-bottom:1px solid #3d4c5b}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,360px),1fr));gap:22px}
figure{margin:0;padding:12px;background:#1b2533;border-radius:10px}img{display:block;width:100%;height:auto;image-rendering:pixelated}
figcaption{font-size:13px;color:#b7c2cf;padding:10px 4px;overflow-wrap:anywhere}small{color:#b7c2cf}
</style><main><h1>护途盾与续愿戒 · 接入验收</h1>
<p>2026-10-23 · 源码与 docs2 已同步；未更新安装包。两件独立饰品，六件守途兵装保持独立。</p>
<section><strong>LOGIC_COUNT 项定向检查通过 · SHOT_COUNT 张后台截图通过 · NPC 路径均可达</strong>
<p>使用真实部署存档构造目标与结算边界，不代表完整自然通关。宽屏与窄屏截图覆盖 NPC、交付、装备对比、完整分页说明及待领取提醒。自动检查文字安全区与重叠，另人工抽查实际画面。Godot 4.7.1；保护脚本禁止显示窗口与抢焦点，全部存档写入临时目录。</p>
<a href="README.md">接入与验证说明</a> · <a href="checks.json">逻辑记录</a> · <a href="captures.json">布局与路径记录</a> · <a href="image-manifest.json">逐图尺寸与字节数</a></section>
<table><tr><th>饰品</th><th>保留能力</th><th>固定获取条件</th></tr>
<tr><td>护途盾（53）</td><td>物防+13、抗性+13，阶段恢复5HP</td><td>M51 两处病房开门、两组伤兵均存活并实际撤到南口，击败队长胜利；回 H51 找固定军械官。</td></tr>
<tr><td>续愿戒（55）</td><td>有效幸运40，成功成长由+1变+2，阶段恢复5HP</td><td>S41 烧毁前保护名册、确认避难院，击败焚毁队长胜利；回 H49 找固定保管人。</td></tr></table>
<p>各一件，收入西队行囊；满包保留、装备不替换。战场事实与领取标记独立保存，仅通关不会误发。未满足可选条件仍按原规则通关，重复交谈不能补记；离章／合流前提醒。</p>
SECTIONS<small>截图为无损压缩的验收输出；运行素材复用既有资源，无新增位图。点击图片查看原图。</small></main></html>
'''
page = page.replace("LOGIC_COUNT", str(len(logic["checks"]))).replace("SHOT_COUNT", str(len(visual["shots"]))).replace("SECTIONS", "".join(sections))
(OUT / "index.html").write_text(page)
print(f"Report: {len(logic['checks'])} checks, {len(manifest)} images; max PNG {max(r['bytes'] for r in manifest):,} B")

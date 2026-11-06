from pathlib import Path
import html
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'actual/reports/opening-feedback-20261026'
MAGICK = '/opt/homebrew/bin/magick'
report = json.loads((OUT / 'verification.json').read_text())
assets = json.loads((ROOT / 'source/story-intro-20261026/manifest.json').read_text())
images = []
for name in report['screenshots']:
    path = OUT / name
    if path.stat().st_size >= 200000:
        optimized = path.with_suffix('.webp')
        subprocess.run([MAGICK, str(path), '-define', 'webp:lossless=true', str(optimized)], check=True)
        path = optimized
    dimensions = subprocess.check_output([MAGICK, 'identify', '-format', '%wx%h', str(path)], text=True)
    images.append({'source': name, 'display': path.name, 'dimensions': dimensions, 'bytes': path.stat().st_size,
                   'reason': '完整运行截图保留原始像素与文字，采用无损压缩；不为参考体积降低验收清晰度。' if path.stat().st_size >= 200000 else '完整运行截图，原始像素。'})

refs = [
    ('counter-before', '/var/folders/r8/8zr_7l9x51g8gym_ptjpzfx40000gp/T/codex-clipboard-3c94858d-02d4-4131-8399-871c822e74cb.jpg'),
    ('status-before', '/var/folders/r8/8zr_7l9x51g8gym_ptjpzfx40000gp/T/codex-clipboard-0ebb95fc-ad18-4bbb-9459-2b5be2914ec3.jpg'),
    ('world-before', '/var/folders/r8/8zr_7l9x51g8gym_ptjpzfx40000gp/T/codex-clipboard-06a9b17d-671a-468e-bf46-80b7766c2df6.jpg'),
    ('fula-before', '/var/folders/r8/8zr_7l9x51g8gym_ptjpzfx40000gp/T/codex-clipboard-509d3a8c-f261-444d-bc59-ab02ed564af8.jpg'),
]
references = []
for name, source in refs:
    destination = OUT / 'before' / (name + '.jpg')
    shutil.copy2(source, destination)
    references.append({'purpose': '用户提供的修改前反馈截图', 'path': 'before/' + destination.name, 'bytes': destination.stat().st_size,
                       'dimensions': subprocess.check_output([MAGICK, 'identify', '-format', '%wx%h', str(destination)], text=True),
                       'reason': '保留用户原始反馈截图，供完整画面前后核对。'})

(OUT / 'image-sizes.json').write_text(json.dumps({'runtime_art': assets, 'screenshots': images, 'references': references}, ensure_ascii=False, indent=2) + '\n')
by_name = {row['source']: row['display'] for row in images}

def figure(name, caption):
    return f'<figure><a href="{by_name[name]}"><img loading="lazy" src="{by_name[name]}" alt="{html.escape(caption)}"></a><figcaption>{html.escape(caption)}</figcaption></figure>'

gallery = ''.join(figure(f'intro-scene-{n}.png', title) for n, title in enumerate(['大断裂', '神幕与日冠教团', '征粮与战乱', '日返庆典']))
comparisons = ''
for title, old, new in [
    ('确认与返回增加上下内边距；三格攻击可以反击', 'counter-before', 'commander-counter-3.png'),
    ('丘堡指挥官：物防 4→6，魔防 0→2', 'status-before', 'commander-status.png'),
    ('粮站胜利后东行受阻：胡纳普说明先分粮', 'world-before', 'grain-east-guidance.png'),
    ('芙拉使用疗愈师形象，亲口提示下一步', 'fula-before', 'fula-grain-guidance.png'),
]:
    comparisons += f'<section><h3>{html.escape(title)}</h3><div class="comparison"><figure><a href="before/{old}.jpg"><img loading="lazy" src="before/{old}.jpg" alt="用户反馈截图"></a><figcaption>修改前 · 用户提供</figcaption></figure>{figure(new, "修改后 · 本次后台运行截图")}</div></section>'

rows = ''.join(f'<tr><td>{html.escape(x["scene"])}</td><td>{x["dimensions"]}</td><td>{x["bytes"]:,} B</td></tr>' for x in assets)
page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>开场与粮站反馈 · 2026-10-26</title>
<style>
:root{color-scheme:dark;font:16px/1.7 system-ui,-apple-system,sans-serif;color:#e4e5e7;background:#11181e}body{max-width:1400px;margin:0 auto;padding:32px 24px 72px}h1,h2,h3{line-height:1.35;color:#f1e3bf}h1{font-size:32px;margin:0 0 12px}h2{margin-top:48px}h3{font-size:19px;margin-top:32px}p{max-width:960px;color:#c6cdd3}a{color:#d6bd80;text-decoration-thickness:1px;text-underline-offset:4px}nav{display:flex;gap:24px;flex-wrap:wrap;margin:24px 0}figure{margin:0}img{display:block;width:100%;height:auto;background:#000}figcaption{padding:10px 0 18px;color:#b8c1c9}section{margin:30px 0}.grid,.comparison{display:grid;grid-template-columns:1fr 1fr;gap:20px}.badge{display:inline-block;padding:6px 13px;background:#20372e;border-radius:20px;color:#c6e6c5}table{border-collapse:collapse;max-width:760px;width:100%;margin:20px 0}td,th{text-align:left;padding:10px 18px;border-bottom:1px solid #33404a}audio{display:block;max-width:100%;margin:20px 0}details{margin:20px 0}summary{cursor:pointer;color:#d6bd80}@media(max-width:900px){.grid,.comparison{grid-template-columns:1fr}body{padding:24px 16px}h1{font-size:26px}}
</style><h1>开场与粮站反馈</h1><p>2026-10-26 · 本地源码已完成六项修改。未导出或更新 iPhone。</p><span class="badge">CHECKS 项定向检查通过 · 后台离屏渲染</span>
<nav><a href="#opening">开场图文</a><a href="#compare">四组前后对照</a><a href="#rules">规则与存档</a><a href="#assets">素材记录</a></nav>
<h2 id="opening">开始旅程，先了解这个世界</h2><p>取自 <a href="../../../docs2/完整台词汇总.md">完整台词汇总 · 序章前：故事背景旁白</a>，四段原文逐字保留。上方插画四边渐黑，等比完整显示；点击确认，每次读下一行，优先按完整句子与分句断行。文字逐字出现并播放短促的打字机声。切图采用 0.65 秒淡入；最后一行确认后进入海峡城庆典。未读完的介绍可从旅程记录继续。</p><div class="grid">GALLERY</div>
<details><summary>查看逐字状态、淡入中间帧与紧凑手机布局</summary>EXTRAS</details>
<p>本地制作的短打字机音效（40 毫秒、单声道、24kHz；峰值约 −11.4dBFS）。已检查电平、格式与运行调用；没有将无声截图验证描述为人耳试听。</p><audio controls src="../../assets/sfx/story-type.wav"></audio>
<h2 id="compare">玩家反馈与本次运行对照</h2>COMPARISONS
<h2 id="rules">规则与存档</h2><ul>
<li>确认、返回按钮高度从 34 增至 42 个逻辑像素，上下各增加 4；保留原菜单高度，战斗按钮间距调为 6，避免超出短屏安全区。正常、按下、禁用和两种手机布局均已检查。</li>
<li>默认守卫在原位等待，靠近或打开攻击预览不会引走；实际遭到我方攻击后才追击，未命中也会记住。原有关卡明确下达的推进命令、召唤与科兰撤退事件继续按各自脚本执行。</li>
<li>守卫的交锋反击至少覆盖 1—3 格，保持已有更远射程；主动攻击仍使用原武器射程，不额外增加伤害或次数。1／2／3 格实际规划与预览可反击，4 格长弓攻击不能让普通枪兵反击。</li>
<li>只给 M12 丘堡粮站指挥官增加物防 2、魔防 2。按已知旧值迁移，存档及重试快照只更新一次，已有伤势、位置、回合和随机状态保留，不复活已败单位。旧版仅因靠近产生、且满血的警戒会重置；受伤守卫视为已经受袭。</li>
<li>丘堡胜利后确实需要先在战后据点面对粮车确认分粮，之后便能向东去押送所；邀请芙拉为可选。大地图东行与据点出口受阻时均由胡纳普开口提醒。</li>
<li>芙拉使用当前职业对应的疗愈师形象，分粮前亲口提醒去粮车，分粮后的邀请与同行流程保持。</li></ul>
<p>验证包括新建旅程、介绍中途保存与继续、逐字音效请求、所有开场原文字序、场景淡入中间帧、守卫反击边界与攻击触发、双防迁移、分粮前后道路和邀请、完整对白字形安全区，以及 2556×1179／1334×750 的后台布局。未进行五章完整重玩或 iPhone 真机触摸试玩。</p>
<p><a href="verification.json">完整检查结果</a> · <a href="domain.json">最终规则复核</a> · <a href="../../tests/opening_feedback.gd">定向检查脚本</a></p>
<h2 id="assets">素材与制作记录</h2><p>四幅插画均由内置 imagegen 制作。原始 PNG 保存在工程外层 source 目录，运行使用独立 WebP 副本；素材按专用开场横图使用，不作为九宫格通用背景。运行配图均小于 200,000 字节。</p><table><thead><tr><th>场景</th><th>像素尺寸</th><th>实际体积</th></tr></thead><tbody>ASSET_ROWS</tbody></table>
<p><a href="../../../source/story-intro-20261026/manifest.json">完整提示词、原图与运行路径</a> · <a href="image-sizes.json">逐图尺寸、字节与压缩理由</a> · <a href="../../data/story_intro.json">运行旁白数据</a></p><p>完整运行截图保留原始像素。大图截图另提供无损 WebP，超过参考体积时保留清晰度，未缩小、裁切或破坏文字。点击图片可查看原尺寸。</p></html>'''
extras = ''.join(figure(name, title) for name, title in [('intro-typing.png', '逐字出现'), ('intro-transition.png', '画面淡入的中间帧'), ('intro-compact.png', '紧凑手机 · 一行文字'), ('controls-1334.png', '紧凑手机 · 增高按钮')])
page = page.replace('CHECKS', str(report['checks'])).replace('GALLERY', gallery).replace('EXTRAS', extras).replace('COMPARISONS', comparisons).replace('ASSET_ROWS', rows)
(OUT / 'index.html').write_text(page)
print(json.dumps({'checks': report['checks'], 'page': str(OUT / 'index.html'), 'art_bytes': [r['bytes'] for r in assets], 'screenshots': len(images)}, ensure_ascii=False))

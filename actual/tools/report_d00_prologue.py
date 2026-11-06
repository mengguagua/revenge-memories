from pathlib import Path
from html import escape
import json
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'actual/reports/d00-prologue-20261026'
logic = json.loads((OUT / 'logic.json').read_text())
visual = json.loads((OUT / 'visual.json').read_text())
movie = json.loads((OUT / 'movie.json').read_text())
expected = json.loads((ROOT / 'actual/reports/dialogue-sync-20261026/expected-dialogue.json').read_text())
assets = json.loads((ROOT / 'actual/assets/prologue-d00-20261026/manifest.json').read_text())
assets['assets'] = [row for row in assets['assets'] if Path(row['path']).name in ['wrist-knot.webp','east-evacuation.webp','rowboat.png']]
assets['assets'] += json.loads((ROOT / 'actual/assets/prologue-small-20261026/manifest.json').read_text())['assets']
small_cast = json.loads((OUT / 'small-cast.json').read_text())
small_logic = json.loads((OUT / 'small-cast-logic.json').read_text())
assert not small_cast['errors']
assert not small_logic['errors']
assert not logic['errors'] and not visual['errors']
images = []
names = list(dict.fromkeys(visual['screenshots'] + small_cast['screenshots'] + ['poses-dark.png', 'poses-light.png', 'H01-arrival.png']))
for name in names:
    path = OUT / name
    if path.stat().st_size >= 200000:
        optimized = path.with_suffix('.webp')
        subprocess.run(['/opt/homebrew/bin/magick', str(path), '-define', 'webp:lossless=true', str(optimized)], check=True)
        path = optimized
    with Image.open(path) as image:
        size = list(image.size)
    images.append({'source': name, 'display': path.name, 'dimensions': size, 'bytes': path.stat().st_size,
                   'reason': '保持完整运行像素和文字，无损WebP不降低清晰度；大于参考体积时按视觉质量优先规则保留。' if path.stat().st_size >= 200000 else '完整像素，无损压缩。'})
(OUT / 'image-sizes.json').write_text(json.dumps({'runtime_assets': assets['assets'], 'review_images': images}, ensure_ascii=False, indent=2) + '\n')
by_name = {row['source']: row['display'] for row in images}

def figure(name, title):
    return f'<figure><a href="{by_name[name]}"><img loading="lazy" src="{by_name[name]}" alt="{escape(title)}"></a><figcaption>{escape(title)}</figcaption></figure>'

storyboard = ''.join(figure(name, title) for name, title in [
    ('prepared-plaza.png', '入场前已布置拘押、粮车与领粮居民'),
    ('old_knot.png', '先看见旧绳结，独立特写'),
    ('recognize_face.png', '再回到艾琳的脸'),
    ('recognition-page-0.png', '三人相认与冲突'),
    ('cast-0.4.png', '挣开守卫，守卫让出位置'),
    ('cast-1.1.png', '朝赫兰施法，胡纳普上前'),
    ('cast-1.65.png', '胡纳普挡在赫兰前方，单次碰撞与音效'),
    ('mutual_questions-page-0.png', '恢复对白，保留双方的不解'),
    ('projection-1.7.png', '神幕里正在撤离的东群岛'),
    ('projection-3.5.png', '船在驶过，居民沿栈桥登船'),
    ('projection-4.5.png', '切回庆典广场的日光与残雪'),
    ('projection-5.7.png', '再切回同一条时间线上的昏暗海面'),
    ('where_and_stop-page-0.png', '人物确认眼前所见'),
    ('hand_and_look.png', '胡纳普伸手，艾琳仍看向他身后的赫兰'),
    ('hold_same_instant.png', '停在伸手与回望，画面不叠加角落小图'),
    ('six_months_earlier.png', '独立黑场字幕：半年前，西大陆。'),
    ('H01-arrival.png', '接入雪原村，保留墓前事件供玩家触发'),
])
dialogue = ''.join(f'<tr><td>{index+1}</td><td>{escape(row["speaker"])}</td><td>{escape(row["text"])}</td></tr>' for index, row in enumerate(expected['D00']))
asset_rows = ''.join(f'<tr><td>{escape(Path(row["path"]).name)}</td><td>{row["dimensions"][0]}×{row["dimensions"][1]}</td><td>{row["bytes"]:,} B</td></tr>' for row in assets['assets'])
page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>D00 · 庆典上的拘押与冲突</title><style>
:root{color-scheme:dark;font:16px/1.7 system-ui,-apple-system,sans-serif;background:#10181f;color:#dfe4e8}body{max-width:1440px;margin:auto;padding:32px 24px 72px}h1,h2,h3{color:#eadbb7;line-height:1.35}h1{font-size:32px;margin:0 0 12px}h2{margin-top:48px}p{max-width:1020px;color:#c0cbd4}a{color:#dac38e;text-underline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:24px;margin:22px 0}.badge{display:inline-block;background:#20392f;color:#c4e5cb;border-radius:24px;padding:7px 16px}video{width:100%;background:#000;max-height:80vh}figure{margin:0}img{display:block;width:100%;height:auto;background:#000}figcaption{padding:10px 0 18px;color:#b9c5cf}.grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}table{border-collapse:collapse;width:100%;margin:22px 0}td,th{text-align:left;padding:10px 14px;border-bottom:1px solid #33434f}summary{cursor:pointer;color:#dac38e}details{margin:24px 0}.small{font-size:14px;color:#9eafb9}@media(max-width:850px){.grid{grid-template-columns:1fr}body{padding:20px 14px}h1{font-size:26px}td,th{padding:8px}}
</style><h1>D00 · 庆典上的拘押与冲突</h1><p>这是电脑上 Godot 按手机布局后台渲染的游戏画面，不是 iPhone 真机录屏。</p><p>2026-10-26 · 最新优化：入场与剧情动作统一小体型，每位角色8帧；赫兰重新生成修长轮廓，三名士兵换为现有蓝紫色壁垒卫士。未导出或更新 iPhone。</p><span class="badge">序章开发验证：LOGIC 项逻辑检查 + VISUAL 项后台呈现检查通过</span>REVISION
<nav><a href="#movie">完整演出</a><a href="#shots">逐镜检查</a><a href="#dialogue">12句现行对白</a><a href="#resume">续读与接续</a><a href="#art">素材与验证</a></nav>
<h2 id="movie">游戏引擎演出预览 · 约46秒</h2><video controls preload="metadata" poster="POSTER"><source src="MOVIE_FILE" type="video/mp4"></video>
<p class="small">实际游戏引擎视口按30FPS逐帧渲染，确认键在每页文字读完后自动按下；不是手持真机录像。预览音轨按运行时音效触发日志，使用游戏相同的序章音乐、火球、碰撞与显形音效离线合成。没有生成角色配音；未作人耳试听声明。</p>
<h2 id="shots">逐镜检查</h2><p>场景先呈现艾琳已被押到传光台旁、赫兰准备表彰胡纳普。玩家面对艾琳或赫兰确认，进入同一场 D00；动作段暂停自由操作并收起对话框，演出说明不出现在对白中。</p><div class="grid">STORYBOARD</div>
<h2 id="dialogue">12句对白逐字沿用新稿</h2><p>对白沿用当前修订稿的顺序与原句（“先停手。”）。旧版重复押解说明、旧“胡纳普挡住法术……”旁白，以及“她来自同一个世界的另一岸”解释均已移除。神幕只呈现当下正在进行的撤离与两岸日光差别。</p><table><thead><tr><th>序号</th><th>人物</th><th>台词</th></tr></thead><tbody>DIALOGUE</tbody></table>
<p><a href="../../../docs2/完整台词汇总.md">现行完整台词汇总</a> · <a href="../dialogue-sync-20261026/expected-dialogue.json">现行原文核对数据</a> · <a href="before/actual/data/campaign.json">修改前的运行对白</a></p>
<h2 id="resume">续读与第三章接续</h2><p>演出仍保存在原有 hub 记录中，保留当前镜头、时间和已触发的音效。各镜头的保存／读取已核对；人物对白、阻挡后、撤离与转场字幕四类断点通过实际界面续读。旧版线性 D00 的中途记录会从新相认镜头重新进入，保留队伍和进度。演出不会改动生命、物品、战斗单位或招募，也不会提前完成雪原村墓前事件。</p>
<p>D31 开头已按修订稿同步；回到相同的伸手与回望姿势，之后接回既有第三章流程。后续广场对白、伸手停点及D31均不叠加右上角东群岛小图。</p><div class="grid">REPRISE</div>
<h2 id="art">素材与验证范围</h2><p>三位人物统一约16逻辑像素的小地图身高，胡纳普以小体型抬臂挡击，每位人物各有8帧实际绘制姿势，起步、抬手、接触与收势按时间衔接。赫兰重新生成窄肩、收拢披肩和直垂袍摆，站立宽度约为此前的78%，身高保持一致。三名守卫复用现有敌方壁垒卫士（职业22）的蓝紫色待机／步行图，演出中保留第三名卫士。</p><p>新图由内置 imagegen 制作；本轮源图和完整提示词保存在 source/prologue-small-20261026，运行采用独立优化副本。人物图集均小于20KB，按脚点统一对齐。检查深浅底透明边缘、手机布局中的比例和完整轮廓。</p><div class="grid">POSES</div>
<table><thead><tr><th>运行素材</th><th>像素尺寸</th><th>实际字节数</th></tr></thead><tbody>ASSETS</tbody></table>
<p><a href="../../../source/prologue-d00-20261026/generation.json">初始提示词与来源</a> · <a href="../../../source/prologue-small-20261026/prompts.json">小体型与修长赫兰的完整提示词</a> · <a href="../../assets/prologue-small-20261026/manifest.json">24帧小地图人物清单与用途</a> · <a href="image-sizes.json">逐图尺寸、字节与压缩理由</a></p>
<p>检查覆盖两处真实确认入口、12句完整对白、动作不可被确认键跳过、自由操作冻结、一次施法与一次阻挡、实时船只和登船、独立转场字幕、角色数据保持、镜头断点及旧D00续读、D31接续和两种手机布局的完整文字安全区。新增的镜头存档字段会校验类型、范围、有限数值和音效标记，异常数据不会进入运行状态。本轮没有重玩40关或执行iPhone真机触摸测试。</p>
<p><a href="logic.json">逻辑结果</a> · <a href="visual.json">后台呈现结果</a> · <a href="movie.json">逐帧演出与声音触发日志</a> · <a href="../../tests/d00_prologue.gd">定向检查脚本</a></p>
<details><summary>历史检查脚本的已知限制</summary><p>旧 round1 脚本曾按7句D00和旧首关7／9名敌兵断言。本轮将相关D00断言同步为12句；首关兵力与援军的三个旧断言涉及此前已经变更的部署，本轮未改动兵力，未将该脚本宣称为全量回归通过。保留<a href="historical-round1-observation.json">最初观察记录</a>，并恢复了该旧脚本写出的报告样本。</p></details>
<p class="small">全部图形进程均在启动前加载已验证的防激活／防窗口显示保护，使用引擎视口离屏捕获。测试记录仅写入独立临时目录。</p></html>'''
page = page.replace('LOGIC', str(logic['checks'])).replace('VISUAL', str(visual['checks'])).replace('POSTER', by_name['cast-1.65.png']).replace('STORYBOARD', storyboard).replace('DIALOGUE', dialogue).replace('ASSETS', asset_rows)
page = page.replace('REPRISE', figure('D31-same-instant.png', '第三章回到同一停点') + figure('compact-held.png', '紧凑手机上的相同演出')).replace('POSES', figure('poses-dark.png', '深色底 · 从上到下为胡纳普、艾琳、赫兰，各8帧') + figure('poses-light.png', '浅色底 · 完整轮廓、透明边缘与统一脚点'))
inbetweens = ''.join(figure('small-cast-'+str(time)+'.png', title) for time,title in [(.12,'0.12秒 · 挣脱起势'),(.32,'0.32秒 · 挣开束缚'),(.56,'0.56秒 · 施法准备'),(.78,'0.78秒 · 抬手与起步'),(1.1,'1.1秒 · 释放与上前'),(1.4,'1.4秒 · 阻挡准备'),(1.65,'1.65秒 · 法术碰到抬起的双臂'),(1.9,'1.9秒 · 挡击后回稳'),(2.2,'2.2秒 · 收势'),(2.55,'2.55秒 · 站定')])
page = page.replace('<h2 id="art">', '<details><summary>查看动作衔接的10个运行时刻</summary><div class="grid">'+inbetweens+'</div></details><h2 id="art">')
revision_path = OUT / 'no-inset.json'
revision = json.loads(revision_path.read_text()) if revision_path.exists() else None
page = page.replace('MOVIE_FILE', movie.get('delivery_video', 'D00-runtime.mp4'))
page = page.replace('REVISION', f'<p>本轮体型与动作：<a href="small-cast.json">{small_cast["checks"]}项后台定向检查</a>及<a href="small-cast-logic.json">{small_logic["checks"]}项无窗口素材检查</a>通过，覆盖24帧的真实尺寸、完整轮廓、脚点、三名壁垒卫士、挡击接触点、D31和两种手机布局。后续右上角小图继续移除，保留前面的独立东群岛切镜。</p>')
(OUT / 'index.html').write_text(page)
print(json.dumps({'logic': logic['checks'], 'visual': visual['checks'], 'page': str(OUT / 'index.html'), 'images': len(images)}, ensure_ascii=False))

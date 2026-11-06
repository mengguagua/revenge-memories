# -*- coding: utf-8 -*-
from pathlib import Path
from html import escape
from PIL import Image
import json,subprocess
R=Path(__file__).resolve().parents[2];O=R/'actual/reports/tactical-readability-20261031'
logic=json.loads((O/'logic.json').read_text());visual=json.loads((O/'visual.json').read_text());assert not logic['errors'] and not visual['errors']
images=[]
def figure(name,title):
 p=O/(name+'.png');q=p.with_suffix('.webp');subprocess.run(['/opt/homebrew/bin/magick',str(p),'-define','webp:lossless=true',str(q)],check=True)
 with Image.open(q) as im:size=list(im.size)
 images.append({'file':q.name,'pixels':size,'bytes':q.stat().st_size,'purpose':title,'quality':'完整运行像素、无损WebP；较大截图保留字体与像素细节'})
 return f'<figure><a href="{q.name}"><img src="{q.name}" loading="lazy" alt="{escape(title)}"></a><figcaption>{escape(title)}</figcaption></figure>'
ui=''.join(figure(n,t) for n,t in [('promotion-list','进阶列表：清楚的说明、页码、翻页提示与底部留白'),('promotion-confirm','进阶确认：中间说明改用12像素中文正文'),('promotion-preview','进阶预览：条件与等级重置说明同步放大'),('compact-confirm','最窄256逻辑像素画幅下的确认说明')])
actors=''.join(figure(n,t) for n,t in [('allies-ready','我方待行动：重装兵、疗愈师、骑兵、天马骑士朝右，脚底落在格底'),('allies-waiting','我方已待机：保留相同朝向与脚底位置'),('enemies-ready','敌方待行动：朝左，弓箭手朝向已修正'),('enemies-waiting','敌方已待机：朝向与位置保持一致')])
ranges=''.join(figure(n,t) for n,t in [('enemy-red-range','确认敌人后显示红色可移动位置'),('enemy-from-player-move','从我方移动预览切到敌人：清除我方蓝色/绿色范围'),('enemy-status','使用状态按钮仍能查看敌方完整详情')])
asset=R/'actual/assets/tactical-readability-20261031/healer-idle.png'
with Image.open(asset) as im:size=list(im.size)
manifest={'runtime':{'path':str(asset.relative_to(R)),'pixels':size,'bytes':asset.stat().st_size,'logical_frame':[24,24],'visible_body_height':15,'poses':4,'purpose':'疗愈师战术地图待机与已行动，面朝右，身体更矮更宽'},'source':'source/tactical-readability-20261031/healer-source.png','generation':'built-in imagegen; connected silhouette bounds for complete cutting; proportional ImageMagick sizing','alignment':'脚底线16、脚底横向中心8；独立保留行走方向帧'}
(asset.parent/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(O/'image-sizes.json').write_text(json.dumps({'asset':manifest,'screenshots':images},ensure_ascii=False,indent=2))
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>进阶文字与地图待机优化</title><style>*{box-sizing:border-box}body{margin:0;background:#111c25;color:#dce5e8;font:16px/1.8 system-ui,-apple-system,"PingFang SC",sans-serif}main{max-width:1280px;margin:auto;padding:40px 24px 70px}h1{font-size:38px;color:#ead9b6;line-height:1.3}h2{color:#d9c493;margin-top:42px}p{max-width:980px}a{color:#e1c38e;text-underline-offset:4px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}figure{margin:14px 0;background:#0b141c;border-radius:10px;overflow:hidden}img{display:block;width:100%;height:auto}figcaption{padding:12px 18px;color:#aabdc9;font-size:14px}.note{background:#253c35;padding:18px 24px;border-radius:10px}.muted{color:#aabdc9}nav{display:flex;gap:22px;flex-wrap:wrap}.sprite{width:192px;height:192px;background-color:#28414e;background-image:url('../../assets/tactical-readability-20261031/healer-idle.png');background-size:768px 192px;image-rendering:pixelated;animation:idle .93s steps(4,end) infinite;border-radius:10px}#light:checked~.sprite{background-color:#e1dacc}@keyframes idle{to{background-position:-768px 0}}a:focus-visible,input:focus-visible{outline:none;box-shadow:0 0 10px #e4ce8f88}@media(prefers-reduced-motion:reduce){.sprite{animation:none}}@media(max-width:750px){main{padding:25px 14px}.grid{grid-template-columns:1fr}h1{font-size:29px}}</style><main><p class="muted">复仇与回忆 · 2026-10-31</p><h1>说明看得清，脚底站得稳</h1><p>完成进阶文字和下边距、双方待机朝向、角色脚底位置、疗愈师比例以及敌方移动范围的优化。下方游戏画面来自 Godot 后台运行视口。</p><nav><a href="#ui">进阶文字</a><a href="#actors">朝向与落点</a><a href="#range">敌方移动范围</a><a href="#verify">验证</a></nav>
<section id="ui"><h2>进阶说明与底部留白</h2><p>确认框中间说明由8像素小字改为12像素中文正文，并提高对比度。列表底部额外增加12个逻辑像素，页码、“确认预览”和翻页文字同步放大；最窄画幅也保留完整说明与按钮间距。</p>'''+ '<div class="grid">'+ui+'</div></section>'
page+='''<section id="actors"><h2>待行动与待机使用同一朝向和落点</h2><p>我方统一朝右、敌方统一朝左。两种状态共享同一位置校准，按人物实际脚底而不是整张透明画布定位；骑兵、执令术师的悬空位置下移，重装兵按脚底中心居中，允许长武器伸出所在格。</p><p>移动时继续使用原有上下左右行走帧。新校准仅作用于战术地图待机显示，不改变格子坐标、移动力或战斗数值。</p><h3>疗愈师四帧素材预览</h3><p>保留白色头巾、蓝白衣袍与法杖，重绘为更短、更宽的比例。可见主体高15逻辑像素，完整落在一格高度内。</p><label><input id="light" type="checkbox">浅色背景</label><div class="sprite" role="img" aria-label="疗愈师四帧待机循环"></div>'''+ '<div class="grid">'+actors+'</div></section>'
# Checkbox must be a sibling of sprite for CSS background switching.
page=page.replace('<label><input id="light" type="checkbox">浅色背景</label>','<input id="light" type="checkbox"><label for="light">浅色背景</label>')
page+='''<section id="range"><h2>选敌人，查看红色可移动范围</h2><p>确认或点选敌人会保留地图，显示该敌人的可停留移动格。从我方移动预览切过去时，会清除我方蓝色、绿色范围，不消耗行动。</p><div class="note">悬浮信息框将所有红色移动格作为不可遮挡区域。若剩余空间放不下，暂时收起信息框；“状态”按钮仍可查看完整属性。</div>'''+ '<div class="grid">'+ranges+'</div></section>'
page+=f'''<section id="verify"><h2>验证范围</h2><p>无窗口检查 {logic['checks']} 项、后台运行与布局检查 {visual['checks']} 项通过。其中包括48套待机配置在四个时间点的脚底、阵营朝向、已行动一致性检查，以及敌方范围遮挡、从我方移动切换、状态入口和窄屏文字安全区域。</p><p>检查了实际截图中的疗愈师比例和完整轮廓；运行素材为 {size[0]}×{size[1]}，{asset.stat().st_size:,} 字节。原始生成图保存在工程外的运行素材隔离目录 source/ 中。截图使用无损WebP，较大文件保留清晰度。</p><p>本轮为相关界面和显示逻辑验证，未重跑全战役，也未安装或更新iPhone。</p><p><a href="logic.json">逻辑结果</a> · <a href="visual.json">运行结果</a> · <a href="profiles.json">待机配置清单</a> · <a href="image-sizes.json">素材尺寸记录</a></p></section></main></html>'''
page=page.replace('工程外的运行素材隔离目录 source/','工程中的离线源图目录 source/')
(O/'index.html').write_text(page)
print(O/'index.html')

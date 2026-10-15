# -*- coding: utf-8 -*-
from pathlib import Path
import json, html
root = Path(__file__).resolve().parents[1]
out = root / 'reports/chapter2'
scenes = [
('07-black-day-lighthouse','黑昼 · 海灯岛防卫','高灯塔与暖色航灯保持辨识，铺石路通向守卫目标。'),
('03-naval-boarding','海上拦截','船舷、桅杆、船舱与跳板使用完整模块，甲板和海面清楚分开。'),
('08-military-harbor','潮狩军港','木码头、装卸区、铺石主路与牢门组成不同层次的战场。'),
('09-ancient-passage','断航古道 · 居民船护送','居民船沿海路前进，部队走古道；船只拥有独立的完整度和抵达状态。'),
('04-prison-bridge','押送舰 · 备用跳板开启','操作后出现连续木板通路；囚舱总闸另行控制两个围舱出口。'),
('06-sea-cave','碎石海洞','完整岩峰与不规则岩壁形成洞室和潮池，留下清楚的行走通道。'),
('02-departure-dialogue','风灯岛 · 启航对白','人物对白显示画像，叙述页面使用完整正文区域。'),
('05-reef-village','礁岛 · 渔村岸边','港口、住屋、草地与沙岸通过同一组海事模块连接。'),
('01-windlamp-harbor','半年前 · 风灯岛','从第一章章末继续，进入艾琳的东线旅程。'),
('11-near-combat','近身战斗演出','沿用外传的人物、职业与战斗动作，命中和伤害使用既有规则。'),
('10-chapter-complete','第二章章末','抵达西岸后完成剧情，两支队伍的成长、装备和伤亡分别保存。')]
items=[]
for key,title,desc in scenes:
 p=out/'screenshots'/f'{key}.png'
 assert p.exists(),p
 items.append(f'''<article><a class="image-link" href="screenshots/{key}-3x.png"><img src="screenshots/{key}.png" alt="{html.escape(title)} 实机截图"></a><div class="caption"><h2>{title}</h2><p>{desc}</p><a href="screenshots/{key}-3x.png">查看 3 倍像素截图 ↗</a></div></article>''')
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>复仇与回忆 · 第二章实机</title><style>
:root{color-scheme:dark;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;background:#102127;color:#f1eada}*{box-sizing:border-box}body{margin:0}main{max-width:1420px;margin:0 auto;padding:46px 28px 70px}.eyebrow{color:#c0b389;font-size:13px;letter-spacing:.14em}h1{font-size:clamp(28px,4vw,44px);line-height:1.25;margin:12px 0 18px}header p{max-width:820px;color:#b7c9c9;line-height:1.8;margin:10px 0}.stats{display:flex;gap:12px;flex-wrap:wrap;margin:22px 0}.stats span{padding:10px 16px;border-radius:6px;background:#253c42;color:#e2e6d7}.links{display:flex;gap:22px;flex-wrap:wrap;margin:18px 0 32px}a{color:#e4c895;text-decoration-thickness:1px;text-underline-offset:5px}a:focus-visible{outline:none;box-shadow:0 0 0 5px #d5bb8155;background:#374c50;border-radius:4px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:#21353b;border-radius:10px;overflow:hidden;box-shadow:0 8px 24px #05161b55}.image-link{display:flex;background:#07151a;aspect-ratio:16/10;align-items:center;justify-content:center;padding:16px}.image-link img{display:block;width:100%;height:auto;max-height:100%;object-fit:contain;image-rendering:pixelated}.caption{padding:18px 22px 24px}h2{font-size:19px;line-height:1.4;margin:0 0 10px}.caption p{color:#b7c9c9;font-size:14px;line-height:1.8;min-height:50px;margin:0 0 14px}.caption a{font-size:13px}.note{margin-top:36px;padding:24px;background:#1b3036;border-radius:10px;color:#b7c9c9;font-size:14px;line-height:1.9}.note strong{color:#e8dfc9} @media(max-width:760px){main{padding:28px 16px 48px}.grid{grid-template-columns:1fr}.image-link{padding:10px}.caption{padding:18px}.links{gap:16px}}
</style></head><body><main><header><div class="eyebrow">REVENGE MEMORIES / 0.2.0</div><h1>第二章 · 没有归来的船</h1><p>6 场主线、2 场支线，连接风灯岛、押送舰、礁岛、海灯岛、潮狩军港与断航古道。以下图片均来自 Godot 运行视口和实际试玩检查点。</p><div class="stats"><span>8 / 8 场战斗通关</span><span>3 轮检查完成</span><span>11 张实机截图</span><span>横屏适配</span></div><p>启动新版 macOS 程序，在第一章章末选择「开始第二章」。已兼容现有第一章存档。</p><nav class="links"><a href="../../docs/第二章交付与验收.md">交付与验收</a><a href="play/round3-report.md">完整试玩记录</a><a href="visual-fixtures/index.html">全部战场视觉抽查</a><a href="../../assets/chapter2/README.md">海事瓦片与模块说明</a></nav></header><section class="grid">'''+''.join(items)+'''</section><aside class="note"><strong>验证范围</strong><br>第一轮检查目标、存档与交互，第二轮检查 8 张战场和据点的视觉与通路，第三轮通过真实按键输入完成 8 场战斗及章末。试玩保留失败、重试和实际伤亡：米蕾、莉莎在支线中阵亡，F21 与 S22 各有一名伤员未能获救；没有修改属性或强制判胜。西队原有状态完整保留。<br>截图为本机 macOS 后台视口捕获；覆盖桌面和手机横屏画幅，未在手机硬件上运行。图片点击可查看最近邻放大的 3 倍副本。</aside></main></body></html>'''
(out/'index.html').write_text(page)
print(out/'index.html')

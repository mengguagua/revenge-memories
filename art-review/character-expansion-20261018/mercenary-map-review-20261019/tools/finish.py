# -*- coding: utf-8 -*-
from pathlib import Path
import json, subprocess

V = Path(__file__).resolve().parents[1]
R = V.parent
G = '/opt/homebrew/bin/magick'
for name in ['M11-before', 'M11-mercenary-refugees-sample']:
    subprocess.run([G, str(V/f'reviews/{name}.png'), '-crop', '400x225+450+510', '+repage', str(V/f'reviews/{name}-detail.png')], check=True)
for name in ['lineup-idle-0', 'lineup-idle-22']:
    subprocess.run([G, str(V/f'reviews/{name}.png'), '-crop', '900x160+520+270', '+repage', str(V/f'reviews/{name}-detail.png')], check=True)

p = R/'index.html'
s = p.read_text()
s = s.replace('data-default-action="professions-class-6-ally-maps-tactical-idle--idle-cycle"', 'data-default-action="professions-class-8-ally-maps-tactical-idle--idle-cycle"')
s = s.replace('双方弓箭手／枪兵 · 0.8.7 测试包', '佣兵地图 · 待验收')
s = s.replace('v=body-volume-motion-20261018', 'v=mercenary-map-review-20261019')
if 'aria-label="本轮佣兵动作"' not in s:
    a = s.index('<nav class="links" aria-label="本轮身体增厚与动画"')
    b = s.index('<details ', a)
    previous = s[a:b]
    new = '''<nav class="links" aria-label="本轮佣兵动作" style="margin-bottom:12px">
<a href="?action=professions-class-8-ally-maps-tactical-idle--idle-cycle">友方佣兵 · 待机</a>
<a href="?action=professions-class-8-enemy-maps-tactical-idle--idle-cycle">敌方佣兵 · 待机</a>
<a href="?action=professions-class-8-ally-maps-tactical-walk--walk-up">向上</a>
<a href="?action=professions-class-8-ally-maps-tactical-walk--walk-right">向右</a>
<a href="?action=professions-class-8-ally-maps-tactical-walk--walk-down">向下</a>
<a href="?action=professions-class-8-ally-maps-tactical-walk--walk-left">向左</a>
<a href="mercenary-map-review-20261019/index.html">首关村民复用与角色大小对照</a>
<a href="mercenary-map-review-20261019/overview.mp4">佣兵完整动作演示</a>
<a href="mercenary-map-review-20261019/README.md">制作与检查记录</a></nav>
<p class="action-note" style="margin:0 0 22px">本轮佣兵采用与已验收角色一致的体量、简洁四色和连续脚下阴影。待机固定头身与双脚，持剑整臂和直剑局部变化；四向行走保持各方向原有持剑侧，交替支撑腿或区分站直与跨腿。首关村民复用样例已放入实际地图对照。本轮等待验收，尚未接入测试包。</p>
'''
    s = s[:a]+new+s[b:]
    i = s.index('</summary>')+len('</summary>')
    s = s[:i]+'\n'+previous+s[i:]
p.write_text(s)

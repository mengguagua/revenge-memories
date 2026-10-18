# -*- coding: utf-8 -*-
from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'index.html';s=p.read_text()
nav='''<nav class="links" aria-label="本轮弓箭手结构修订" style="margin-bottom:12px"><a href="?action=professions-class-12-ally-maps-tactical-idle--idle-cycle">友军弓箭手 · 待机修订</a><a href="?action=professions-class-12-enemy-maps-tactical-idle--idle-cycle">敌军弓箭手 · 待机修订</a><a href="?action=professions-class-12-ally-maps-tactical-walk--walk-down">弓箭手 · 向下</a><a href="?action=professions-class-12-ally-maps-tactical-walk--walk-right">弓箭手 · 向右</a><a href="?action=professions-class-12-ally-maps-tactical-walk--walk-left">弓箭手 · 向左</a><a href="archer-bow-review-v2-20261018/overview.mp4">弓箭手本轮 · 动画总览</a><a href="archer-bow-review-v2-20261018/README.md">弓箭手本轮 · 制作记录</a></nav><p class="action-note" style="margin:0 0 22px">本轮仅修双方弓箭手：完整弓身放在人物前景，两段弓弦与斜向箭杆保留；待机时拉弦前臂、弓箭和后方持弓手臂一起上下移动。左右行走的人物脸部与腿脚朝向已纠正。友军剧情静止形象同步使用新待机首帧。向上行走、男主和枪兵保留，等待本轮验收。</p>
'''
if 'aria-label="本轮弓箭手结构修订"'not in s:s=s.replace('<nav class="links" aria-label="本轮弓箭手和枪兵"',nav+'<nav class="links" aria-label="本轮弓箭手和枪兵"')
s=s.replace('本轮动作 · 动画总览','上轮四组总览 · 留档').replace('本轮制作与核对记录','上轮制作记录')
s=s.replace('弓箭手行走只动腿脚，待机只动持弓手臂和弓箭；','弓箭手行走只动腿脚；待机按上方本轮修订说明；')
s=s.replace('?v=archer-spearman-map-20261018','?v=archer-bow-v2-20261018').replace('本轮兵种样板 · 待验收','弓箭手结构修订 · 待验收')
p.write_text(s)

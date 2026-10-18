# -*- coding: utf-8 -*-
from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'index.html';s=p.read_text()
nav='''<nav class="links" aria-label="本轮弓箭手手臂与步态修订" style="margin-bottom:12px"><a href="?action=professions-class-12-ally-maps-tactical-idle--idle-cycle">友军弓箭手 · 本轮待机</a><a href="?action=professions-class-12-enemy-maps-tactical-idle--idle-cycle">敌军弓箭手 · 本轮待机</a><a href="?action=professions-class-12-ally-maps-tactical-walk--walk-down">向下 · 手臂检查</a><a href="?action=professions-class-12-ally-maps-tactical-walk--walk-right">向右 · 站直／前跨</a><a href="?action=professions-class-12-ally-maps-tactical-walk--walk-left">向左 · 站直／前跨</a><a href="archer-arms-step-v3-20261018/reviews/side-neutral-and-step.png">侧向两帧对照图</a><a href="archer-arms-step-v3-20261018/overview.mp4">本轮动画总览</a><a href="archer-arms-step-v3-20261018/README.md">本轮制作记录</a></nav><p class="action-note" style="margin:0 0 22px">本轮仅修双方弓箭手：补出弓后可见的持弓手臂，拉弦前臂去掉分隔黑线并轻微上斜；两段弓弦在实际小图中保持连续。侧向首帧为站直，第二帧为前跨，上身和弓箭固定。友军剧情静止形象同步更新。未接入测试包，待验收。</p>
'''
if 'aria-label="本轮弓箭手手臂与步态修订"'not in s:s=s.replace('<nav class="links" aria-label="本轮弓箭手结构修订"',nav+'<nav class="links" aria-label="本轮弓箭手结构修订"')
s=s.replace('弓箭手本轮 · 动画总览','上轮弓形修订 · 留档').replace('弓箭手本轮 · 制作记录','上轮弓形制作记录')
s=s.replace('弓箭手结构修订 · 待验收','弓箭手手臂／步态 · 待验收').replace('?v=archer-bow-v2-20261018','?v=archer-arms-step-v3-20261018')
p.write_text(s)

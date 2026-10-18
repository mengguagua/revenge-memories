# -*- coding: utf-8 -*-
from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'index.html';s=p.read_text()
nav='''<nav class="links" aria-label="本轮向下拉弦手遮挡修正" style="margin-bottom:12px"><a href="?action=professions-class-12-ally-maps-tactical-walk--walk-down">友军弓箭手 · 向下拉弦手</a><a href="?action=professions-class-12-enemy-maps-tactical-walk--walk-down">敌军弓箭手 · 向下拉弦手</a><a href="archer-down-hand-v4-20261018/overview.mp4">更新后的完整总览</a><a href="archer-down-hand-v4-20261018/README.md">本轮修正记录</a></nav><p class="action-note" style="margin:0 0 22px">本轮仅修向下行走：拉弦手覆盖弓弦交点，清楚显示握住并拉弦。双方两个向下姿势已同步修正，其余方向、待机和脚下阴影保留。未接入测试包，待验收。</p>
'''
if 'aria-label="本轮向下拉弦手遮挡修正"'not in s:s=s.replace('<nav class="links" aria-label="本轮弓箭手手臂与步态修订"',nav+'<nav class="links" aria-label="本轮弓箭手手臂与步态修订"')
s=s.replace('href="archer-arms-step-v3-20261018/overview.mp4">本轮动画总览','href="archer-arms-step-v3-20261018/overview.mp4">上轮手臂／步态总览 · 留档')
s=s.replace('弓箭手手臂／步态 · 待验收','向下拉弦手修正 · 待验收')
s=s.replace('data-default-action="professions-class-12-ally-maps-tactical-idle--idle-cycle"','data-default-action="professions-class-12-ally-maps-tactical-walk--walk-down"')
s=s.replace('?v=archer-arms-step-v3-20261018','?v=archer-down-hand-v4-20261018')
p.write_text(s)

# -*- coding: utf-8 -*-
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'index.html';s=p.read_text()
s=s.replace('data-default-action="professions-class-12-ally-maps-tactical-walk--walk-down"','data-default-action="professions-class-6-ally-maps-tactical-idle--idle-cycle"')
nav='''<nav class="links" aria-label="枪兵待机与迈腿修正" style="margin-bottom:12px"><a href="?action=professions-class-6-ally-maps-tactical-idle--idle-cycle">友军枪兵 · 正面待机</a><a href="?action=professions-class-6-enemy-maps-tactical-idle--idle-cycle">敌军枪兵 · 正面待机</a><a href="?action=professions-class-6-ally-maps-tactical-walk--walk-right">枪兵 · 向右迈腿</a><a href="?action=professions-class-6-ally-maps-tactical-walk--walk-left">枪兵 · 向左迈腿</a><a href="?action=hunapu-maps-world--walk-down">男主 · 大地图连续阴影</a><a href="spearman-map-v2-20261018/overview.mp4">本轮动作总览</a><a href="spearman-map-v2-20261018/README.md">本轮制作记录</a></nav><p class="action-note" style="margin:0 0 22px">本轮枪兵：待机改为正面脸、一根长枪与连续的持枪手臂；左右走区分支撑、向后抬脚和前跨，保留原作头部固定与手臂、武器运动。双方已同步，友军剧情仅同款静止形象。枪兵尚未接入游戏，待验收。男主大地图同步剧情地图连续阴影，测试包为 0.8.5；弓箭手保持已接入版本。以下为历史修订记录。</p>
'''
anchor='<nav class="links" aria-label="本轮向下拉弦手遮挡修正"'
if 'aria-label="枪兵待机与迈腿修正"' not in s:s=s.replace(anchor,nav+anchor,1)
s=s.replace('双方两个向下姿势已同步修正，其余方向、待机和脚下阴影保留。未接入测试包，待验收。','双方两个向下姿势已同步修正，其余方向、待机和脚下阴影保留。已接入 0.8.4 及后续测试包。')
s=s.replace('剧情脚下阴影已收拢为连续投影。','剧情和大地图脚下阴影已统一收拢为连续投影。')
s=s.replace('?v=archer-down-hand-v4-20261018','?v=spearman-map-v2-20261018')
s=s.replace('向下拉弦手修正 · 待验收','枪兵待机与迈腿修正 · 待验收')
p.write_text(s)

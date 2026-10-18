# -*- coding: utf-8 -*-
from pathlib import Path
R=Path(__file__).resolve().parents[2];p=R/'index.html';s=p.read_text()
nav='''<nav class="links" aria-label="枪兵侧身姿势与简化步态" style="margin-bottom:12px"><a href="?action=professions-class-6-ally-maps-tactical-idle--idle-cycle">友军枪兵 · 侧身持枪待机</a><a href="?action=professions-class-6-enemy-maps-tactical-idle--idle-cycle">敌军枪兵 · 侧身持枪待机</a><a href="?action=professions-class-6-ally-maps-tactical-walk--walk-right">向右 · 站直／跨腿</a><a href="?action=professions-class-6-ally-maps-tactical-walk--walk-left">向左 · 站直／跨腿</a><a href="spearman-stance-v3-20261018/overview.mp4">本轮动作总览</a><a href="spearman-stance-v3-20261018/reviews/standing-stride-4x.png">站直与跨腿两帧</a><a href="spearman-stance-v3-20261018/README.md">本轮制作与检查记录</a></nav><p class="action-note" style="margin:0 0 22px">待机恢复侧身前后跨腿：头身与双脚固定，单手在胸前握住枪杆，手臂与完整长枪一起移动，枪杆位于身体前方。左右行走采用本轮确认的简化方案：双腿站直一帧＋跨腿一帧。双方同步，友军剧情仅同款静止形象；待验收，尚未接入游戏。</p>
'''
if 'aria-label="枪兵侧身姿势与简化步态"' not in s:
 start=s.index('<nav class="links" aria-label="枪兵待机与迈腿修正"')
 end=s.index('<div class="selectors">',start)
 old=s[start:end]
 s=s[:start]+nav+'<details style="margin-bottom:20px"><summary style="padding:10px 0;cursor:pointer;color:var(--muted)">历史修订记录</summary>\n'+old+'</details>\n'+s[end:]
s=s.replace('枪兵待机与迈腿修正 · 待验收','枪兵侧身持枪／站直跨腿 · 待验收')
s=s.replace('?v=spearman-map-v2-20261018','?v=spearman-stance-v3-20261018')
p.write_text(s)

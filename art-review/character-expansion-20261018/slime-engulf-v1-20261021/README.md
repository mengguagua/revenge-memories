# 史莱姆 · 膨胀、吞噬与消失

本轮只更新角色重绘全动作对照，美术未接入游戏或测试包。鬼火已获用户目测确认，沿用原稿。

- 史莱姆的生成、原地跳动和移动段仅换色：敌方暗蓝为主，友军蓝白。原帧图透明度、外形、位置、速度与节奏保持。
- 抵达目标后的最后攻击由原螺旋叠层改为胶体逐渐膨胀、从脚边包覆目标；外轮廓、阴影、液体反光和开口逐步变大，脚底锚点保持不动。
- 原结算前闭合开口，结算时完整包覆参照目标，随后短暂停留，再收缩渐隐，结束前四帧不再显示史莱姆。
- 灰色士兵复用现有士兵待机图，仅作为最后攻击段的可视验收参照，不是新增作战单位或新受击动作。史莱姆消失后目标恢复可见，不表达永久移除、即死或额外伤害。友军的最后攻击安排在施法者对面的目标位置。
- 双方近距、远距和重甲参考共12个变体同步。原人物姿势、总帧数、总时长、结算时刻与法术编号32全部保留。
- 光环、鬼火、箭雨、风刃、圣光、火球、雷电、诸神黄昏和地图动作保持。

## 验收入口

- [返回全动作对照](../index.html)
- [敌军史莱姆](../index.html?action=professions-class-15-enemy-battle--class_15_enemy_item_32#motion-player)
- [友军史莱姆](../index.html?action=professions-class-15-ally-battle--class_15_ally_item_32#motion-player)
- [双方四阶段 · 深浅底](engulf-stages.png)
- [敌军：膨胀包覆](enemy-growth-frame-307.png)
- [敌军：结算时刻完整吞噬](enemy-contact-frame-349.png)
- [敌军：史莱姆消失](enemy-gone-frame-389.png)
- [友军：结算时刻完整吞噬](ally-contact-frame-307.png)
- [友军：史莱姆消失](ally-gone-frame-330.png)
- [敌军完整视频](../demos/videos/professions-class-15-enemy-battle--class_15_enemy_item_32.mp4)
- [友军完整视频](../demos/videos/professions-class-15-ally-battle--class_15_ally_item_32.mp4)

## 制作与检查

保留原前段位图进行换色，最后攻击为同像素网格的胶体体积、液体反光、开口闭合和收缩序列。未调用自动附图流程。

- [素材用途、尺寸、体积及哈希](asset-manifest.json)
- [角色与法术结算对应](spell-action-contract.json)
- [针对性数据与像素检查](verification.json)
- [播放器检查](player-check.json)
- [视频导出记录](export-report.json)

仅进行离线数据、像素、合成和播放器模拟检查；浏览器目测验收由用户在对照页完成。聊天不展示图片。

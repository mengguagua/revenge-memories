# 壁垒卫士 · 正面盾牌与固定身体待机

双方战斗地图待机改为完整盾牌正面朝外，可见蓝色／蓝紫色盾面、浅色盾沿和菱形纹样。头部、躯干、双腿、盾牌使用同一张固定底图，每个相位都不移动，只让持枪手臂与完整长枪运动。

- [盟军待机](../index.html?action=professions-class-22-ally-maps-tactical-idle--idle-cycle#motion-player)
- [敌方待机](../index.html?action=professions-class-22-enemy-maps-tactical-idle--idle-cycle#motion-player)
- [双方三相 · 深底](poses-dark.png) · [浅底](poses-light.png)

此次使用内置 ImageGen 制作一张固定身体及三张独立的完整手臂动画层，[源图](source/static-body-arm-layers-master-v1.png)与[提示词](source/imagegen-prompt.json)保留。手臂在固定肩甲下方连接，仅在限定的手臂活动区域叠加；不再使用三张各自有细微差异的全身图。头部和身体没有逐相重绘、平移、缩放或整体抖动。

每方身体活动区之外的2300个不透明像素均与同一张固定底图逐像素一致，覆盖头发、脸、头部、躯干、腿脚和完整盾牌。身体偏移始终为0、0。长枪沿用上一稿同一张8×76像素完整素材，仅平移，不改变长度；本帧手套原位覆盖握持处，枪尖、枪杆与枪尾完整。

保留原96×96画布、48×80锚点，六个原作图槽仍为0／1／2／1／0／1别名。播放按0→1→2→1、14／8／14／8帧循环，完整导出88帧。配色沿用盟军蓝白、敌方蓝紫14色，头发纯色、衣料哑光。

本轮只更新双方战斗地图待机，行走和战斗动画保持。仅供对照页验收，未接入游戏或测试包。

- [素材大小、固定身体与动作层记录](asset-manifest.json)
- [针对性检查结果](verification.json)
- [播放导出与视频解码记录](export-report.json)

验收采用离线对照渲染、深浅底姿势板和原作／新版播放帧。未通过其它方式绕过浏览器本地文件访问限制，未启动Godot可见窗口。

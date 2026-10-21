# 敌方骑兵 · 战斗地图待机与四向行走

按敌方自身素材重新对齐骑手、头部和身体中心。固定上半主体，待机只交换前腿和后腿区域；行走保留原腿部相位，左右围绕明确的身体轴镜像，消除整体左右、上下晃动。

待机与四向行走使用同一套最多16色的暗蓝紫调色板：暗蓝甲胄、蓝紫衣料、冷蓝灰战马，保留少量自然肤色与冷色金属高光。褐色和红色杂色归入蓝紫色阶，肤色仅保留在骑手面部。保留可辨的色彩饱和度，避免灰暗发闷，同时以明暗区分马匹、人物和装备。

原待机0／1／2／1、14／8／14／8帧节奏和四向两姿势各16帧的时间轴保持，四向停止姿势同步。盟军骑兵已确认的动作与配色保持。本轮只更新全动作对照页，未接入游戏或测试包。

## 验收入口

- [敌方骑兵待机](../index.html?action=professions-class-1-enemy-maps-tactical-idle--idle-cycle#motion-player)
- [向上](../index.html?action=professions-class-1-enemy-maps-tactical-walk--walk-up#motion-player)
- [向右](../index.html?action=professions-class-1-enemy-maps-tactical-walk--walk-right#motion-player)
- [向下](../index.html?action=professions-class-1-enemy-maps-tactical-walk--walk-down#motion-player)
- [向左](../index.html?action=professions-class-1-enemy-maps-tactical-walk--walk-left#motion-player)
- [待机和四向姿势 · 深底](poses-dark.png)
- [待机和四向姿势 · 浅底](poses-light.png)

## 制作与检查

- [原图来源、对齐位置、调色板、尺寸与体积](asset-manifest.json)
- [固定主体、腿部衔接与时序检查](verification.json)
- [五组动画导出](export-report.json)

使用已有敌方像素素材制作，原图保留。未调用自动附图流程，聊天不展示图片，视觉效果由用户进入对照页验收。

# 盟军骑兵 · 战斗地图待机与四向行走

固定骑手、头部和上半主体，按方向校准身体中心；待机只交换原前腿、后腿抬起区域，行走只让下方腿部相位变化。左右围绕身体轴镜像，取消整个人左右或上下跳动。

待机与行走共用最多16色：蓝白服装、灰白战马、少量米金与自然肤色。先将原颜色饱和度降低20%，再映射到统一的柔和调色板，不使用抖色；中性色限制在灰阶，避免马匹和金属阴影变成肤色碎点。

保留原待机0／1／2／1、14／8／14／8帧节奏，以及四向两姿势各16帧的步态顺序。停止姿势同步。只更新全动作对照页，未接入游戏或测试包，敌方骑兵与战斗场景美术保持。

## 验收入口

- [待机](../index.html?action=professions-class-1-ally-maps-tactical-idle--idle-cycle#motion-player)
- [向上](../index.html?action=professions-class-1-ally-maps-tactical-walk--walk-up#motion-player)
- [向右](../index.html?action=professions-class-1-ally-maps-tactical-walk--walk-right#motion-player)
- [向下](../index.html?action=professions-class-1-ally-maps-tactical-walk--walk-down#motion-player)
- [向左](../index.html?action=professions-class-1-ally-maps-tactical-walk--walk-left#motion-player)
- [待机和四向姿势 · 深底](poses-dark.png)
- [待机和四向姿势 · 浅底](poses-light.png)

## 制作与检查

- [素材用途、尺寸、实际大小与定位](asset-manifest.json)
- [固定区域、腿部连通、调色板与时间轴检查](verification.json)
- [五组视频导出](export-report.json)

原图保留在上一版目录。使用已有像素素材修改和离线合成，未调用自动附图流程；聊天不展示图片。视觉效果由用户进入对照页验收。

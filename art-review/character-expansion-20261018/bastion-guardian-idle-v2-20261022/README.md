# 壁垒卫士 · 侧持盾牌与长枪摩擦待机

纠正双方战斗地图待机：盾牌横在身前侧持，仅显示窄边，不再露出整块正面盾面。双臂屈肘，持枪手随三个原作相位抬低，另一手支撑侧持盾牌。长枪完整显示钢制枪头、连续木杆与枪尾，沿盾边往复摩擦。

- [盟军待机](../index.html?action=professions-class-22-ally-maps-tactical-idle--idle-cycle#motion-player)
- [敌方待机](../index.html?action=professions-class-22-enemy-maps-tactical-idle--idle-cycle#motion-player)
- [双方三相 · 深底](poses-dark.png) · [浅底](poses-light.png)
- [原作三相参考](source/native-idle-three-poses.png)

制作使用内置 ImageGen 重绘三张包含双臂和侧持盾牌的完整身体，另绘一根完整长枪。[原始源图](source/idle-shield-edge-master-v1.png)和[提示词](source/imagegen-prompt.json)保留。盟军沿用柔白甲、3976b5主蓝与纯色头发，敌方沿用蓝紫色材质；双方均使用上一稿14色表。

每方三相共用同一张8×76像素长枪素材，仅作整数平移，不旋转、不缩放、不分段重画。整根枪在身体前方绘制，再由本帧自己的手套原位遮住握持位置；没有跨帧拼接手臂。枪尖与枪尾始终可见，消除旧稿短杆长短变化的问题。

身体按固定头部参照登记，保持原96×96画布、48×80锚点和六个原作图槽；三相采用0→1→2→1循环，每相14／8／14／8帧。只更新双方地图待机，行走、战斗、原作帧序及其它人物保持。本轮仅供对照页视觉验收，未接入游戏。

- [素材大小、定位和同枪层记录](asset-manifest.json)
- [针对性检查结果](verification.json)
- [播放导出与解码记录](export-report.json)

检查采用本地离线对照渲染与深浅底图片；未使用被环境限制的浏览器本地文件访问，也未启动Godot可见窗口。

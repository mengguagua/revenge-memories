# 骑兵 · 战斗与投枪配色

友军飞行投枪使用重绘手持武器的木色枪杆和金属枪头原色，取消原生蓝色枪杆。枪杆与金属基色取自友军举枪姿势的武器区域。

敌方骑兵全部战斗姿势、人物装备、战马与飞行投枪统一蓝紫色主体，与已确认地图使用同一套暗蓝、蓝紫、冷蓝灰调色板，保留少量自然肤色。原身体像素位置、透明轮廓和尺寸保持。

投枪仅逐像素换色，原尺寸、透明轮廓、朝向、翻转补偿、飞行轨迹、释放时间和命中结算均保持。近距、远距和重甲目标沿用各自原动画。友军人物形象、双方已确认地图动作及其它职业的共享原始投枪素材保持。

## 验收入口

- [友军 · 原色投枪](../index.html?action=professions-class-1-ally-battle--class_1_ally_javelin#motion-player)
- [敌军 · 蓝紫投枪](../index.html?action=professions-class-1-enemy-battle--class_1_enemy_javelin#motion-player)
- [敌军 · 普通攻击](../index.html?action=professions-class-1-enemy-battle--original_class_1_enemy_normal#motion-player)
- [敌军 · 战斗待机](../index.html?action=professions-class-1-enemy-battle--reaction-idle#motion-player)
- [投枪配色修改前后](lance-colors.png)
- [敌方姿势 · 深底](enemy-poses-dark.png)
- [敌方姿势 · 浅底](enemy-poses-light.png)

## 制作与检查

- [素材来源、调色板、尺寸与体积](asset-manifest.json)
- [角色、既有武器动作与效果时刻对应](action-contract.json)
- [局部配色、透明轮廓、方向与时间轴检查](verification.json)
- [代表性动画导出](export-report.json)

只更新全动作对照页，未接入游戏或测试包，不新增攻击、命中或武器能力。未调用自动附图流程，聊天不展示图片，视觉效果由用户进入对照页验收。

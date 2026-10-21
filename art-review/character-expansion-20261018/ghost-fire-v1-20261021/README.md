# 鬼火 · 双眼、爆炸与上飘收尾

「多拉」更名为「鬼火」。本轮更新全动作对照，双方美术未接入游戏或测试包。

- 名称同步至完整游戏设定、当前法术表的中文名称与对照页；保留编号31、日本原名及全部法术属性。原提取文件与历史原名记录保留。
- 敌方使用暗蓝色主体、深蓝阴影与少量灰蓝亮部；友军使用蓝白色。双眼以深色眼窝衬托明亮瞳点，飞行四相中位置固定。
- 原有火焰形态、生成位置、飞行方向、速度、轨迹和释放时刻保持。双眼在蓄力与飞行时可见。
- 爆炸以原可见中心等比放大约15%；不同小尺寸帧按整像素取整。原爆炸阶段、各帧停留及结算时刻保持，不追加爆炸或伤害。
- 原动画结束后追加30帧（约0.5秒）鬼火上飘、轻微摆尾与渐隐，约上升18原生像素。复用原火焰头部、双眼和尾焰纹理，脸部保持直立；原作播完后停帧并标注「新稿鬼火上飘」。
- 双方近距、远距与重甲参考共12个变体同步。此前光环、箭雨、风刃、圣光、火球、雷电、诸神黄昏与地图动作保留。

## 验收入口

- [返回角色重绘 · 全动作对照](../index.html)
- [敌军鬼火](../index.html?action=professions-class-15-enemy-battle--class_15_enemy_item_31#motion-player)
- [友军鬼火](../index.html?action=professions-class-15-ally-battle--class_15_ally_item_31#motion-player)
- [飞行四相双眼 · 双方深浅底](flight-eyes.png)
- [敌军飞行](enemy-flight-frame-89.png)
- [友军飞行](ally-flight-frame-89.png)
- [敌军爆炸](enemy-blast-frame-138.png)
- [友军爆炸](ally-blast-frame-120.png)
- [敌军上飘收尾](enemy-rise-frame-174.png)
- [友军上飘收尾](ally-rise-frame-141.png)
- [敌军完整对照视频](../demos/videos/professions-class-15-enemy-battle--class_15_enemy_item_31.mp4)
- [友军完整对照视频](../demos/videos/professions-class-15-ally-battle--class_15_ally_item_31.mp4)

## 制作与检查

基于现有原生火焰位图进行精确换色、双眼修订、最近邻等比放大与尾焰重排；未调用自动附图流程。

- [素材用途、尺寸及字节记录](asset-manifest.json)
- [角色、法术、动作与结算对应](spell-action-contract.json)
- [针对性检查](verification.json)
- [播放器收尾检查](player-check.json)
- [视频导出检查](export-report.json)

离线核对数据、像素、透明轮廓和合成；浏览器可视验收由用户在对照页完成，聊天不展示图片。

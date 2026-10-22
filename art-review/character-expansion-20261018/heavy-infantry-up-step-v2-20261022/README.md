# 重装兵 · 向上行走左右腿交替

修正上一版两相都由左腿支撑的问题。双方当前向上行走依次为：

1. 左腿弯曲抬起，右腿伸下支撑。
2. 右腿弯曲抬起，左腿伸下支撑。

保持原每相16帧、两相循环、96帧审查播放。新两相的靴底高低关系相反，抬起侧比支撑侧高10个输出像素。

- [盟军向上行走](../index.html?action=professions-class-2-ally-maps-tactical-walk--walk-up#motion-player)
- [敌方向上行走](../index.html?action=professions-class-2-enemy-maps-tactical-walk--walk-up#motion-player)
- [双方两相 · 深底](up-pair-dark.png) · [浅底](up-pair-light.png)
- [检查结果](verification.json) · [播放导出](export-report.json)

内置ImageGen根据上一版精确像素参考修正相反腿部姿势，保留[原始生成图](source/opposite-up-master-v1.png)及[提示词](source/imagegen-prompt.json)。导入时只接入新腿部区域，裙甲以上、盾牌、双臂及整支长枪共用已确认的固定像素；上半身与武器不会跟着换腿跳动。敌方沿用同一相位结构的蓝紫配色。

仅替换向上行走0／1两张姿势及其停止方向预览；其它六张方向姿势、地图待机、全部战斗程序和素材保持。验证范围为双方向上行走和对应静止朝向共4项，比较其它623项内容摘要，并检查原时序、靴底高度、实际播放画面差异区域和视频解码。未启动可见Godot窗口，未绕过浏览器本地文件访问限制。

所有候选姿势为128×96像素，素材尺寸及实际字节数见[素材清单](asset-manifest.json)。仅更新美术对照，未接入游戏或重新打包。

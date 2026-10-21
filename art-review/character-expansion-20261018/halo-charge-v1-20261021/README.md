# 光环 · 头顶蓄力与光点收尾

本轮只更新「角色重绘 · 全动作对照」，未接入游戏或测试包。

- 初始成环改在角色头顶固定中心；沿用原形成过程与原蓄力停留，在第80～94帧逐渐放大至原圆环的1.5倍，然后停留至原释放时刻（第105帧）。
- 敌方全程为暗蓝三色：深蓝阴影、暗蓝主体及少量灰蓝亮部；友军保留原绿、白及深绿。原图与其它法术不改色。
- 释放后的目标位置、逐层环绕、缩小过程、人物动作和第189帧结算保持原样。
- 原最后一层光环消失后，延续该环的像素位置散成光点，向外轻散、上浮并渐隐，历时24帧（约0.4秒）。仅为视觉收尾，不追加命中、伤害或结算。
- 敌方原结尾有6帧空白，光点在该段开始并另加18帧；友军原结尾仍有残余环，播完后接24帧光点。对照页保留原作全部帧，原作结束后停在末帧，并标注「原作结束，新稿光点收尾」。
- 双方近距、远距及重甲参考共12个光环变体同步；此前火球、雷电、诸神黄昏、圣光、风刃、箭雨与地图动作保留。

## 验收入口

- [返回全动作对照](../index.html)
- [敌军光环](../index.html?action=professions-class-15-enemy-battle--class_15_enemy_item_29#motion-player)
- [友军光环](../index.html?action=professions-class-15-ally-battle--class_15_ally_item_29#motion-player)
- [敌军：头顶蓄力放大完成](enemy-charge-frame-100.png)
- [友军：头顶蓄力放大完成](ally-charge-frame-100.png)
- [敌军：光点收尾](enemy-scatter-frame-234.png)
- [友军：光点收尾](ally-scatter-frame-223.png)
- [敌军完整对照视频](../demos/videos/professions-class-15-enemy-battle--class_15_enemy_item_29.mp4)
- [友军完整对照视频](../demos/videos/professions-class-15-ally-battle--class_15_ally_item_29.mp4)

## 制作与检查

沿用现有光环位图，裁去透明留白后居中重排、最近邻缩放和精确换色；光点从最后的原光环像素采样，未调用会自动附图的生成流程。

- [素材用途、尺寸和文件体积](asset-manifest.json)
- [角色、法术、动作与触发时刻](spell-action-contract.json)
- [针对性验证记录](verification.json)
- [视频导出记录](export-report.json)

仅进行离线数据、像素与合成检查；浏览器可视验收由用户在对照页完成，聊天不展示图片。

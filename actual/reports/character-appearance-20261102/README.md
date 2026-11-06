# 三类角色战斗外观运行接入 · 2026-11-02

此前这两轮修改只更新了美术对照，运行工程仍使用旧图集。本次只同步盟军骑兵、天马骑士和弓箭手的战斗外观。

- 骑兵：`cavalry-battle-lance-colors-v1-20261021` → `mount-consistency-v2-20261101`，白色马身、蓝白衣甲、深色鬃毛、尾毛及蹄子。
- 天马骑士：`pegasus-battle-red-hair-v3-20261023` → `mount-consistency-v2-20261101`，统一骑手发型与飞马体型。
- 弓箭手：`archer-battle-scale-v4-20261019` → `battle-appearance-v1-20261031`，已确认的狙击手蓝白配色与板寸。

## 运行资源

新增 `actual/assets/character-appearance-20261102/` 内3张共用动画图集，保留原槽位、锚点、列数和逻辑尺寸，替换27个现用姿势。图片按原始RGBA8像素无损保存；3张`.import`关闭默认透明边缘重写，保证半透明骑兵轮廓像素一致。图集保留原生分槽与全部姿势，体积按共用图集记录，不降低单帧分辨率。

更新 `actual/data/reviewed_animations.json` 的三项战斗资源，以及运行时实际读取的 `actual/data/animation_runtime/reviewed.json` 元数据和 `manifest.json` 来源指纹。1078条动作程序及 `reviewed.bin` 逐字节保持不变；地图、效果、其他职业与规则数据保留。

原文件备份为本目录的 `before-*.json.gz`。[完整接入清单](import.json)记录源素材、原版本、新版本、图集用途/尺寸/字节和每个姿势哈希。

## 验证

Godot 4.7.1无窗口验证通过，见[runtime-checks.json](runtime-checks.json)：

- 229项检查，27个实际导入姿势与对照可见RGBA哈希一致。
- 实际懒加载索引生效，未走来源不一致时的回退。
- 26条普通攻击、投枪、弓箭、圣弓及近远距/重甲变体选择正确，38条相关动作时序和结算点保持。
- 三类角色各实际播放一次，只有一次生命值结算，动画效果和位移正确清理。
- 未改动存档、地图、奖励与战斗规则；未重新打包，也未安装或更新iPhone。

[返回「角色重绘 · 全动作对照」](../../../art-review/character-expansion-20261018/index.html)

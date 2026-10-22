# 双方重装兵 · 全动作重新设计

重装兵位于“士兵（6）→重装兵（2）→壁垒卫士（22）”中间。本轮替换旧盟军职业样板，增加敌方重装兵，完成双方战斗地图待机、四向行走、停止方向、战斗待机、普通攻击、投枪及原有通用反应，共6个场景配置、40个动作。

- [盟军地图待机](../index.html?action=professions-class-2-ally-maps-tactical-idle--idle-cycle#motion-player) · [敌方地图待机](../index.html?action=professions-class-2-enemy-maps-tactical-idle--idle-cycle#motion-player)
- [盟军行走](../index.html?action=professions-class-2-ally-maps-tactical-walk--walk-right#motion-player) · [敌方行走](../index.html?action=professions-class-2-enemy-maps-tactical-walk--walk-right#motion-player)
- [盟军普通攻击](../index.html?action=professions-class-2-ally-battle--original_class_2_normal#motion-player) · [敌方普通攻击](../index.html?action=professions-class-2-enemy-battle--original_class_2_enemy_normal#motion-player)
- [三级装甲对照](progression-comparison.png)
- [盟军地图姿势 · 深底](ally-maps-dark.png) · [浅底](ally-maps-light.png)
- [敌方地图姿势 · 深底](enemy-maps-dark.png) · [浅底](enemy-maps-light.png)
- [盟军战斗姿势 · 深底](ally-battle-dark.png) · [浅底](ally-battle-light.png)
- [敌方战斗姿势 · 深底](enemy-battle-dark.png) · [浅底](enemy-battle-light.png)

## 形象与颜色

以新的中阶板甲形象替换旧绿金样板：开放面部钢盔、短盔缨、中型肩甲、胸甲、护臂与护胫，比士兵覆盖更多，比壁垒卫士的多层甲和大盾轻。盟军采用白色板甲、弓箭手色系的柔和蓝衣与少量必要冷色阴影；敌方采用蓝紫色。每阵营14色，头发归一纯色，蓝色衣料只保留基础色与必要暗褶，没有高光色。

## 原作部位与动作

先按原作图块和姿势逐相辨认头盔、盔缨、肩甲、手臂、前后枪杆与腿部。地图方盾绑在左前臂，随手臂一起运动；战斗的大片弧形是头盔与肩部装甲，保留双手持枪的动作。长枪始终是连续枪杆，收枪和刺出均保留后柄；投出后使用空手姿势32，飞行枪由原程序的外置效果控制。

战斗姿势0与4～10对应原始迈步相位；11为收枪准备，12为一次前刺；30举起一支水平投枪，32为投出后的空手随势。16／29复用原待机；敌方背景槽及投枪槽保留原来的负16逻辑像素登记差；投枪／空手槽原生阵营调色另有1个面部像素的透明差，已单独记录核对。左右地图步态按原生图块证据整帧镜像，不拼接四肢。

每组完整姿势使用同一个缩放比例，以面部或后视头盔作为固定定位点；仅做整体等比缩放和整数登记，不拉伸身体、不切身体拼腿。原作攻击接近、回位的必要位移保留，不额外增加全身摇摆。

## 原节奏与验证

地图待机仍为0→1→2→1，14／8／14／8帧；每向行走两相，每相16帧。普通攻击335帧，界面第154帧结算；投枪近距、远距、重甲目标保留双方各自原有程序，不新增连击、伤害、护盾或结算次数。卡牌和武器定义核对现行完整游戏设定的枪系、攻击与投枪规则，参见[角色→卡牌／武器→动作→触发时刻](card-action-map.json)。

[针对性检查](verification.json)记录原始帧序、命中时刻、人物定位、透明边缘、原生敌方背景槽差、左右镜像及其它动作保持结果；[播放导出记录](export-report.json)包含40张静帧、原速与近看视频。使用离线对照渲染检查，没有启动抢占焦点的Godot窗口，也未绕过浏览器的本地文件访问限制。

所有全姿势由内置ImageGen生成；[提示词](source/imagegen-prompts.json)、[步态修正提示词](source/walk-phase-correction-prompt.json)及`source/`中的原始大图保留离线。运行候选帧、定位与实际文件体积见[素材清单](asset-manifest.json)。仅更新美术对照，等待本轮验收；未接入游戏业务代码或重新打包。

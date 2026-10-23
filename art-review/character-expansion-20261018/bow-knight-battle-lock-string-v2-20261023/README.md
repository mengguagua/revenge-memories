# 弓骑士 · 战斗攻击修正 v2

本轮仅更新双方弓骑士战斗美术和对照预览，尚未接入游戏运行工程。待机与四向行走保留上一轮版本。

- 固定马匹：10张战斗姿势共用上一版同一张马匹、马鞍与骑手下肢底图。马腿、马尾区域逐像素一致，其他马匹部分仅受弓和手臂的自然遮挡。
- 完整弓弦：通过 ImageGen 分离完整骑手／武器层，保留上下两段弓臂。弓弦从实际弓梢连续连接，拉弦时经后手搭箭点；浅色弦配深色轮廓，在深浅背景均可辨认。
- 箭矢衔接：满弓箭与第一帧外置飞行箭在世界坐标中逐像素重合，包含敌方镜像后的偏移。只校准箭矢图片内部位置，原作效果坐标、锚点、运动速度与时序保持。
- 配色：沿用六色哑光材质、盟军蓝白／敌方蓝紫，保留肤色与眼睛、纯色头发。

## 预览

[返回全动作对照](../index.html) · [盟军近距](../index.html?action=professions-class-20-ally-battle--class_20_ally_bow#motion-player) · [盟军圣弓](../index.html?action=professions-class-20-ally-battle--class_20_ally_silver_bow#motion-player) · [敌方攻击](../index.html?action=professions-class-20-enemy-battle--class_20_enemy_bow#motion-player)

[盟军全姿态（浅底）](ally-battle-light.png) · [盟军全姿态（深底）](ally-battle-dark.png) · [敌方全姿态（浅底）](enemy-battle-light.png) · [敌方全姿态（深底）](enemy-battle-dark.png)

## 验证范围

覆盖双方18条近远距攻击，以及共用身体素材的8条待机／受击等反应。775项动作中，仅26项战斗画面更新，其余749项内容指纹不变。全部原始帧序列、FPS、身体／效果坐标、播放时长与结算帧相同；地图素材与映射逐文件校验不变。

满弓箭的贴图行112–115在逻辑空间占据y92–93；飞行箭矢贴图第2行经原锚点与原效果位置合成后同样占据y92–93。双方各自校准图片内部水平位置，因此第一帧飞行箭的全部34个有效像素都与搭箭位置一致。

执行资源完整性、六色调色板、透明度、身体连通性、马身稳定区域、原动作时序、箭矢搭接及视频解码帧数检查。使用与页面相同资源和坐标的离线渲染器检查深浅底画面和文字安全区；浏览器页面视觉检查受访问限制，未声称已执行。用户视觉验收待确认。

原始生成图、分层图片与配准记录保存在 `source/`；生成源图离线保留，不作为运行素材。详细结果见 [验证记录](verification.json)、[视频导出记录](export-report.json)、[配准记录](registration.json)。

## 修改素材大小

全部角色运行候选图为320 × 256，透明边缘保持无损索引色；单张低于50KB参考值。

| 素材 | 像素尺寸 | 字节 |
| --- | --- | ---: |
| ally/flying-arrow.png | 64 × 16 | 883 |
| ally/battle/frame-001.png | 320 × 256 | 3,450 |
| ally/battle/frame-013.png | 320 × 256 | 3,447 |
| ally/battle/frame-014.png | 320 × 256 | 3,463 |
| ally/battle/frame-015.png | 320 × 256 | 3,623 |
| ally/battle/frame-016.png | 320 × 256 | 3,619 |
| ally/battle/frame-017.png | 320 × 256 | 3,625 |
| ally/battle/frame-018.png | 320 × 256 | 3,615 |
| enemy/flying-arrow.png | 64 × 16 | 883 |
| enemy/battle/frame-001.png | 320 × 256 | 3,620 |
| enemy/battle/frame-005.png | 320 × 256 | 3,626 |
| enemy/battle/frame-006.png | 320 × 256 | 3,615 |

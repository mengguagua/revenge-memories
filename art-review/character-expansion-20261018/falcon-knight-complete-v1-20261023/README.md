# 我方隼骑士：完整动作对照

本轮重做我方隼骑士的视觉配色和武器，并以它自己的原作姿势、动作程序完成待机、四向行走、四向停止及战斗，共20项。原有素材和原始生成母图保留；未接入游戏运行场景，等待用户视觉验收。

## 形象与武器

- 相比已确认的天马骑士，使用开放式米白头盔、分层肩甲、完整前臂／胫甲，以及坐骑额甲；翼相、身体比例与职业轮廓来自隼骑士自己的姿势。
- 继承天马骑士五色：深蓝 `#172638`、蓝色 `#3976b5`、米白 `#e4e1c8`、肤色 `#dda77d`、纯色柔和红发 `#b96369`。只增加一种橙色 `#c98953`，用于小面积盔边、甲片扣饰和鞍布饰边。头发与衣料不用高光色。
- 依照用户参考图生成骑枪：针形尖端、渐宽锥形枪身、外扩护手、短握柄和尾饰。普通攻击保持相同武器长度与原握点；举枪准备姿势单独重绘并登记，释放姿势保留空手，飞行骑枪与手持外观一致。
- 地图正背面可见的竖枪按原方向与握点替换；侧向与静止姿势中被身体遮挡的部分保持遮挡，不添加新的摆臂动作。

[地图浅底](ally-maps-light.png) · [地图深底](ally-maps-dark.png) · [战斗浅底](ally-battle-light.png) · [战斗深底](ally-battle-dark.png)

## 原作动作与定位

- 职业编号5，与天马骑士编号3分开。地图用本类原生 CHR19 的8槽四向图；每相16 tick，3次循环共96帧。左右严格镜像，正背面两翼同步改变扑动阶段；原飞行投影为21至23行，四倍后固定在84至95行。
- 待机使用本类右朝向三相，按 `0→1→2→1`、`14／8／14／8 tick` 循环，保留扑翼与屈腿关系。每个方向用同一头盔定位点去除整体平移，保留翼、腿与马尾的姿势变化。
- 普通攻击保留自身8姿势的扑翼、接近、前刺和收势程序，共158帧，原结算为第80帧（零基79）。六个投枪变体保留各自释放、飞行及结算，只有原程序的一次投射事件。25／48与0为精确像素别名。
- 原姿势3左下方分离小片是远翼羽端，不是额外马蹄；保留原位置。举枪49按原翼顶108、前蹄212／384登记。除新武器范围和该独立重绘姿势外，战斗羽翼、身体和四肢的原登记位置不变。

[原始参考与时序](native-reference-audit.json) · [定位与材质记录](registration.json) · [角色→动作→结算对应](action-effect-mapping.json) · [验证](verification.json) · [预览导出](export-report.json)

游戏设定为枪系飞行职业，隼骑士的对指定魔物规则不通过本次美术添加新技能或额外攻击表现。本套是职业动作样板，无具体英雄卡牌绑定；未修改伤害、被动、卡牌或运行结算代码。

## 制作与验证范围

使用内置 imagegen 制作材质设计参考、独立骑枪，以及举枪姿势；[完整提示词与使用方式](source/generation-record.json)。原始母图在 `source/` 离线保留，页面引用经过原尺寸登记、透明边缘检查与无损索引压缩的副本。原图未被覆盖。

本轮检查原生参考文件哈希、动作帧顺序、时长、偏移、结算、六色二值透明、完整路径、地图定位和投影、左右镜像、战斗源帧别名，以及同源离线对照截图和导出视频解码。仅20项目标动作更新，其他755项内容指纹保持。浏览器页面未实测，沿用此前访问限制；没有启动前台Godot窗口。

## 运行副本尺寸与体积

| 文件 | 像素尺寸 | 字节 |
| --- | --- | --- |
| source/lance-clean.png | 1808 × 267 | 5033 |
| ally/tactical-walk/frame-000.png | 128 × 96 | 1717 |
| ally/tactical-walk/frame-001.png | 128 × 96 | 1716 |
| ally/tactical-walk/frame-002.png | 128 × 96 | 1734 |
| ally/tactical-walk/frame-003.png | 128 × 96 | 1747 |
| ally/tactical-walk/frame-004.png | 128 × 96 | 1805 |
| ally/tactical-walk/frame-005.png | 128 × 96 | 1919 |
| ally/tactical-walk/frame-006.png | 128 × 96 | 1740 |
| ally/tactical-walk/frame-007.png | 128 × 96 | 1732 |
| ally/tactical-idle/frame-000.png | 96 × 96 | 1715 |
| ally/tactical-idle/frame-001.png | 96 × 96 | 1633 |
| ally/tactical-idle/frame-002.png | 96 × 96 | 1658 |
| ally/tactical-idle/frame-003.png | 96 × 96 | 1633 |
| ally/tactical-idle/frame-004.png | 96 × 96 | 1715 |
| ally/tactical-idle/frame-005.png | 96 × 96 | 1633 |
| ally/battle/frame-000.png | 384 × 544 | 5026 |
| ally/battle/frame-001.png | 384 × 544 | 4805 |
| ally/battle/frame-002.png | 384 × 544 | 4351 |
| ally/battle/frame-003.png | 384 × 544 | 4133 |
| ally/battle/frame-004.png | 384 × 544 | 4011 |
| ally/battle/frame-005.png | 384 × 544 | 5405 |
| ally/battle/frame-006.png | 384 × 544 | 5093 |
| ally/battle/frame-007.png | 384 × 544 | 5118 |
| ally/battle/frame-025.png | 384 × 544 | 5026 |
| ally/battle/frame-048.png | 384 × 544 | 5026 |
| ally/battle/frame-049.png | 384 × 544 | 5145 |
| ally/battle/frame-050.png | 384 × 544 | 4916 |
| ally/flying-lance.png | 64 × 16 | 911 |
| ally-maps-dark.png | 1360 × 956 | 40052 |
| ally-maps-light.png | 1360 × 956 | 40392 |
| ally-battle-dark.png | 1680 × 1856 | 96646 |
| ally-battle-light.png | 1680 × 1856 | 96538 |
| ally/tactical-walk-atlas.png | 1024 × 96 | 7502 |
| ally/tactical-idle-atlas.png | 576 × 96 | 3476 |
| ally/battle-atlas.png | 4608 × 544 | 38623 |

超过50KB参考值的文件为整套姿势检查图或合并图集，保留四倍坐标、羽翼和文字清晰度；独立角色帧使用同尺寸六色无损压缩。

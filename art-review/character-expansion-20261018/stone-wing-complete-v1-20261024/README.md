# 敌方石翼兽：待机、行走与战斗

2026-10-24，完整美术对照候选，待用户验收。[返回角色重绘 · 全动作对照](../index.html#stone-wing-progress)。

## 形象与动作理解

沿用本篇已经建立的四足石翼兽：角状石首、钩颚、四只爪足、分节石甲、两片蝠翼与长石尾。配色参考敌方剑豪，采用柔和明亮的蓝紫石面、靛蓝翼膜与深海军蓝轮廓，十一色归一，小面积柔琥珀眼睛。石质面只保留必要体积阴影；没有头发、衣服、人类武器、金色裂纹或闪亮高光。

原作是另一套双足体形。本篇已采用四足身体及独立身体攻击，因此保留可对应的翼相、动作顺序、循环、节奏和原程序位移，并按四足骨架重绘，不能将其称为原作解剖轮廓逐像素一致。原作姿势9为低位警戒，10／11／12为中位／上振／下振，14收身准备，15伸爪过渡并带原作短暂挥击轨迹，13为接触后的伸爪姿势；随后振翼回到起点。

地图沿用原作CHR28方向及每相16帧、待机14／8／14／8帧。头胸用自身解剖基准登记，双翼变化不参与整体位置计算；前后爪分别连接肩部与骨盆，远侧肢体在后。左右按原作镜像关系复用。整个人物完整制作，不切成上下两段替换。

## 动作入口

- [地图待机](../index.html?action=professions-class-3-enemy-maps-tactical-idle--idle-cycle#motion-player)
- [向上](../index.html?action=professions-class-3-enemy-maps-tactical-walk--walk-up#motion-player)、[向右](../index.html?action=professions-class-3-enemy-maps-tactical-walk--walk-right#motion-player)、[向下](../index.html?action=professions-class-3-enemy-maps-tactical-walk--walk-down#motion-player)、[向左](../index.html?action=professions-class-3-enemy-maps-tactical-walk--walk-left#motion-player)
- [外传振翼与扑击节奏](../index.html?action=professions-class-3-enemy-battle--original_class_3_enemy_normal#motion-player)
- [本篇裂石爪](../index.html?action=professions-class-3-enemy-battle--stone-claw#motion-player)、[碎岩喷吐](../index.html?action=professions-class-3-enemy-battle--stone-spit#motion-player)、[远距喷吐](../index.html?action=professions-class-3-enemy-battle--stone-spit-far#motion-player)
- [战斗待机](../index.html?action=professions-class-3-enemy-battle--idle#motion-player)、[受击](../index.html?action=professions-class-3-enemy-battle--hit#motion-player)、[未命中](../index.html?action=professions-class-3-enemy-battle--miss#motion-player)、[退场](../index.html?action=professions-class-3-enemy-battle--exit#motion-player)、[S22厚石甲形象](../index.html?action=professions-class-3-enemy-battle--thick-stone#motion-player)
- [地图全姿势 · 浅底](maps-light.png)、[深底](maps-dark.png)
- [战斗全姿势 · 浅底](battle-light.png)、[深底](battle-dark.png)
- [导出视频抽帧](decoded-actions.png)、[战斗连续姿势](sequence-check.png)

## 攻击与触发对应

| 角色／变体 | 定义与动作 | 视觉接触时刻 | 效果 |
|---|---|---|---|
| class-3-enemy普通个体 | 1001裂石爪；收翼、压身、俯冲伸爪、回收 | 本篇46帧／50fps，第27帧（零起26） | 一次物理1格命中；随后碎石反馈不增加伤害 |
| 明确配置的远程变体 | 1002碎岩喷吐；收颈、张颚、喷一枚岩芯、闭颚 | 本篇54帧／50fps，第35帧（零起34） | 一枚物理岩芯命中一次；不附加裂石爪伤害 |
| 原作节奏复刻对照 | 原作208帧及全部帧行／偏移原样保留 | 第104帧（零起103） | 仅作为原作翼动、准备、释放、回位节奏的对照 |
| S22厚石甲 | 既有天然石甲的外观变体 | 静态警戒姿势 | 不增加新出牌、护盾或格挡能力 |

来源为现行docs2完整游戏设定5.5.6、actual/core/innate_attacks.gd、actual/core/innate_attack_animation.gd。完整机器记录见[动作与触发对应](action-effect-mapping.json)。对照中的两个时序入口明确区分：本篇固有攻击沿现行源码，原作208帧单独展示，不把美术预览称作已接入运行场景。

## 制作与验收范围

使用内置image_gen制作地图、待机、战斗、喷吐／受击／厚甲和岩芯／碎片效果，原始图与[完整提示词](source/generation-prompts.json)保存在source/。最终人物做固定色板、透明边缘、统一等比最近邻缩放、头胸基准与原槽位登记；投射物和碎石效果为独立位图。源图离线保留。

检查包括原作地图CPU帧哈希、208帧程序逐行一致、固有攻击单次触发、地图定位误差、左右镜像、透明轮廓、深浅底画面、所有视频帧数／时长、普通与近景完整边界及标题内边距。记录见[验证](verification.json)、[导出](export-report.json)、[交付图片尺寸和字节数](delivery-image-inventory.json)。

本轮仅更新美术对照和目录；运行游戏资源与业务代码保持，未打包、安装或更新iPhone。浏览器本地文件访问受环境限制，采用离线合成和导出视频解码检查，未声称完成浏览器运行截图。

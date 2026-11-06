# 破晓勇士：战斗地图统一形象

2026-10-24，以已确认的左右横移为人物基准，同步向上、向下行走和待机，待用户验收。[返回角色重绘 · 全动作对照](../index.html#hunapu-dawn-progress)。

## 本轮修改

- 统一纯色蓝发、脸型和头身比例，沿用新版较厚的浅蓝肩甲、胸甲、护臂与护膝、深蓝衣靴、蓝芯银剑和小盾。
- 向上、向下各制作两个完整人物姿势，交替支撑腿与抬腿，保留手臂、衣摆与躯干的自然配合及肢体前后遮挡。
- 待机制作斜举、平举、过顶三个完整姿势，按原作14／8／14／8帧举剑循环播放。使用完整发型定位，避免平举时把遮挡脸部的手误作脸部，导致人物大小变化。
- 全部地图人物使用同一64输出像素的发顶至脚底高度；待机与行走按各自原锚点定位，脚底基准一致。对照图将待机与行走置于相同地面，方便直接比较。

## 查看

- [统一人物对照 · 浅底](model-comparison-light.png)、[深底](model-comparison-dark.png)
- [向上行走](../index.html?action=hunapu-promoted-maps-tactical-walk--walk-up#motion-player)、[向下行走](../index.html?action=hunapu-promoted-maps-tactical-walk--walk-down#motion-player)、[待机循环](../index.html?action=hunapu-promoted-maps-tactical-idle--idle-cycle#motion-player)
- [向上连续帧](up-dark.png)、[向下连续帧](down-dark.png)、[待机连续帧](idle-dark.png)、[视频首尾与换相抽帧](decoded-vertical-idle.png)
- [针对性检查](verification.json)、[视频帧数与时长](export-report.json)、[图片尺寸与字节数](delivery-image-inventory.json)
- [已确认左右横移记录](../hunapu-dawn-strafe-v4-20261024/README.md)

## 制作与验证

使用内置 image_gen，以上轮已确认左右横移源图作为严格形象参考，原作图作为动作参考；[完整提示词](source/generation-prompts.json)与原始输出保存在source/，不作为运行角色图加载。七个完整新姿势仅作既有十色调色板归一、纯色头发处理、统一最近邻缩放、透明边缘整理与整数登记；未分割上下半身拼接。

本轮仅更新两个战斗地图Profile，共九项行走／方向停止／待机对照。已确认的左右横移四个图像路径与像素保持，剧情／大地图和全部战斗场景动作保持。原行走每相16帧、待机循环、位置偏移、原帧率及集中阴影保持。共享页面按最新数据局部合并，保留其他角色和默认动作。

检查包括深浅背景、同地面形象对照、上下换腿和待机连续帧、视频解码、人物透明边界与标题内边距。浏览器本地文件访问受环境限制，未声称完成浏览器实际运行截图。最终视觉确认以用户验收为准。本轮未接入游戏运行资源，未安装或更新设备。

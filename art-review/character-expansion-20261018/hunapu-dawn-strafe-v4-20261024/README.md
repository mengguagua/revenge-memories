# 破晓勇士：按确认姿势重做战斗地图横移

2026-10-24，完成对照候选稿，待用户验收。[返回角色重绘 · 全动作对照](../index.html#hunapu-dawn-progress)。

## 本轮姿势

- 脸朝屏幕前方，略向移动方向转，胸面可见，肩胯保留轻微错位。
- 以向右为例：持剑手位于画面右侧腹前，握住剑柄；蓝色圆形护手在拳头上方，剑斜跨胸前向画面左上举起。前臂、拳头、剑柄和剑刃形成连续的持械关系。
- 另一手持盾，盾贴住画面左腹前侧低位，保持小而清楚的轮廓。
- 原作右向2／3为收腿略重叠、屈膝跨步两相；左向6／7分别使用右向3／2的镜像。完整人物统一制作，衣摆、肘部和下肢共同参与步态；保留原作每相16帧、96帧演示循环及原位置数据。

## 查看

- [向右循环](../index.html?action=hunapu-promoted-maps-tactical-walk--walk-right#motion-player)、[向左循环](../index.html?action=hunapu-promoted-maps-tactical-walk--walk-left#motion-player)
- [四个完整姿势 · 浅底](poses-light.png)、[深底](poses-dark.png)
- [向右连续帧 · 地图背景](tactical-right-dark.png)、[浅底](tactical-right-light.png)
- [向左连续帧 · 地图背景](tactical-left-dark.png)、[浅底](tactical-left-light.png)
- [原作槽位放大](native-reference.png)、[视频首尾与换步抽帧](decoded-horizontal.png)
- [检查记录](verification.json)、[视频帧数与时长](export-report.json)、[图片尺寸与实际字节数](delivery-image-inventory.json)

## 制作与范围

使用内置 image_gen 制作两个向右完整姿势，选择修正持剑、持盾关系后的版本；[完整提示词](source/generation-prompts.json)、原始图与最初候选保存在 source/。地图输出仅进行既有调色板归一、纯色头发处理、最近邻统一缩放、透明边缘整理和整数位置登记；向左遵循原作的反相镜像。最终独立人物为128×96透明PNG，十色配色；原始源图离线保留。

本轮仅替换战斗地图行走组的2、3、6、7四个角色槽位，同时刷新该组左右行走和方向停止的对照。向上、向下图像、集中阴影、剧情／大地图、战斗待机、普通攻击与必杀第二剑及火花保持原稿。共享页面按最新数据局部合并，其他角色和页面默认动作保持。本轮未接入游戏运行资源，未安装或更新设备。

检查采用深浅背景完整姿势、地图连续帧和导出视频解码。浏览器本地文件访问受环境限制，没有声称完成浏览器实际运行检查。最终视觉确认以用户验收为准。

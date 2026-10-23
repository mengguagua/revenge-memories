# 天马骑士：待机前腿与向下双翼修正

本轮按用户反馈局部修正盟军天马。敌方继续暂缓，未接入游戏运行场景。

- 待机三种姿势补全另一只前腿，分别露出蹄子；原骑手、头发、长枪、马身、翅膀与原前腿像素保留。
- 向下移动抬翼帧移除原向下的左翼，补成与右翼同步抬起的左翼。回落帧双翼同步向下，沿用已确认帧。
- 仍用蓝、米白、深蓝轮廓、肤色和柔和红发五色。骑手定位点不变，向下移动的马身、长枪及地面投影像素不变。
- 原作逐帧顺序、每帧时长、循环、帧偏移与效果保持。影响待机循环、向下移动和向下停止三项；其他772项内容指纹不变。

[浅底检查](review-light.png) · [深底检查](review-dark.png) · [验证记录](verification.json) · [全战斗姿势（沿用）](../pegasus-knight-complete-v1-20261023/ally-battle-light.png)

[生成提示词与原图记录](source/generation-record.json)。使用内置 imagegen 局部补画；原始生成母图和编辑输入保留在 `source/`，未作为页面运行素材。补画区域以 `patch-registration.json` 为准，经最近邻缩放、五色归并与局部遮罩合入；未替换整个人物。

验证范围：深浅底逐姿势检查、离线同源对照渲染、三项预览视频实际解码、帧数与时长、资源路径、中心定位与受保护像素检查。浏览器页面未实测，等待用户视觉验收。

## 素材尺寸与体积

| 文件 | 像素尺寸 | 字节 |
| --- | --- | --- |
| ally/tactical-idle/frame-000.png | 96 × 96 | 1672 |
| ally/tactical-idle/frame-001.png | 96 × 96 | 1582 |
| ally/tactical-idle/frame-002.png | 96 × 96 | 1592 |
| ally/tactical-idle/frame-003.png | 96 × 96 | 1582 |
| ally/tactical-idle/frame-004.png | 96 × 96 | 1672 |
| ally/tactical-idle/frame-005.png | 96 × 96 | 1582 |
| ally/tactical-walk/frame-004.png | 128 × 96 | 1679 |
| review-dark.png | 1000 × 620 | 22648 |
| review-light.png | 1000 × 620 | 22777 |
| ally/tactical-walk-atlas.png | 1024 × 96 | 6855 |
| ally/tactical-idle-atlas.png | 576 × 96 | 3364 |

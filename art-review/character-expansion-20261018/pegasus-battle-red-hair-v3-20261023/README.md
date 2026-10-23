# 天马骑士：战斗全帧红发修正

修正普通攻击、投枪及通用战斗反应所用的全部12个源姿势。头顶、鬓发和马尾统一为已确认的 `#b96369` 柔和红色，保留肤色、眼睛和头饰；原轮廓、透明度、人物位置、翅膀、马腿与武器形状不变。

原通用颜色识别在源姿势3误把腰带当作头发，导致头部全蓝、腰带误红；本次改为逐姿势明确头部与脸部范围，按既有原图材质连通区域修正，同时恢复误红腰带的蓝色。

[浅底全姿势](review-light.png) · [深底全姿势](review-dark.png) · [验证记录](verification.json) · [预览导出记录](export-report.json) · [已确认的地图前腿与双翼](../pegasus-forelegs-wing-sync-v2-20261023/README.md)

使用内置 imagegen 制作局部颜色参考，原始图保留在 `source/`。最终按原图材质区域重新分配既定五色，保留源像素位置和透明度，未用整幅生成图替换角色。[完整生成提示词](source/generation-record.json)。

验证范围：逐姿势检查头顶、鬓发、马尾、头饰、肤色、眼睛及深浅底边缘；检查12帧的原透明轮廓、帧尺寸与定位；原动作序列、帧时长、偏移、结算及投枪特效参数保持。更新11项战斗动作的预览，另764项内容指纹不变，包含已确认的地图修正。浏览器页面未实测，使用同源离线渲染与视频解码检查；未接入游戏运行场景。敌方按用户选择继续暂缓。

## 素材尺寸与体积

| 文件 | 像素尺寸 | 字节 |
| --- | --- | --- |
| ally/battle/frame-000.png | 320 × 384 | 4303 |
| ally/battle/frame-001.png | 320 × 384 | 4085 |
| ally/battle/frame-002.png | 320 × 384 | 3804 |
| ally/battle/frame-003.png | 320 × 384 | 3511 |
| ally/battle/frame-004.png | 320 × 384 | 3264 |
| ally/battle/frame-005.png | 320 × 384 | 4199 |
| ally/battle/frame-006.png | 320 × 384 | 4296 |
| ally/battle/frame-007.png | 320 × 384 | 4371 |
| ally/battle/frame-016.png | 320 × 384 | 4303 |
| ally/battle/frame-033.png | 320 × 384 | 4303 |
| ally/battle/frame-034.png | 320 × 384 | 4378 |
| ally/battle/frame-035.png | 320 × 384 | 4328 |
| ally/battle-atlas.png | 3840 × 384 | 31834 |
| review-dark.png | 1520 × 1376 | 84846 |
| review-light.png | 1520 × 1376 | 84868 |

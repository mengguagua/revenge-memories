# 狙击手攻击箭矢配色修正

2026-10-23。双方狙击手飞行箭矢统一为柔和木色箭杆、米白箭头和尾羽，与重绘武器及箭袋的材质配色一致。原作盟军紫色、敌方青黄色只在左侧原作参考中保留。

本轮为颜色小修复。使用内置 ImageGen 完成[箭矢改色源稿](source/natural-arrow-master.png)，再将两种材质颜色登记到原作箭矢的逐像素透明轮廓；保留48×16画布、全部27个可见像素、原锚点、方向翻转、飞行轨迹和结算时刻。最终[飞行箭矢](flying-arrow.png)为120字节。

通过狙击手各自的 effect_overrides 引用同一中性箭矢，适用于普通弓、圣弓及双方近远距离攻击。保留圣弓自身的原有火焰效果。角色身体、持弓动作与已确认的地图行走稿保持。

- [双方改色前后](arrow-colors-light.png)
- [盟军弓箭攻击 · 深底](class_13_ally_bow-dark.png) / [浅底](class_13_ally_bow-light.png)
- [敌方弓箭攻击 · 深底](class_13_enemy_bow-dark.png) / [浅底](class_13_enemy_bow-light.png)
- [盟军圣弓攻击](class_13_ally_silver_bow-dark.png)
- [完整提示词](source/generation-prompt.json)、[素材与原作摘要](asset-manifest.json)、[针对性验证](verification.json)
- [返回全动作对照](../index.html)

验证范围：18项攻击的箭矢引用、原动作与效果逐帧向量、锚点、透明轮廓、近远距离和双方配色；更新相关播放文件并解码核对帧数与时长。现有缓存规则使8项无箭矢的通用反应预览摘要同步变化，已逐帧证明画面保持并刷新缓存；其余705项动作摘要保持。画面检查使用离线同步合成器，浏览器未重新渲染。只更新美术对照，等待用户确认。

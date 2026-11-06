# 角色重绘运行接入 · 2026-10-24

当前对照页的固定快照已接入 `actual` 游戏运行源码。没有安装或更新 iPhone，没有重新导出历史测试应用。

本次包含151组形象配置：47组战斗形象、104组地图形象。胡纳普战士／破晓勇士、艾琳女魔剑士／引光剑使分别选择对应形象；其余双方职业、地图待机与四向行走也同步。石翼兽地图采用新版，战斗八姿势严格保留用户选择的旧版。

导入888条攻击演出和190条通用反应。现行游戏选择其中886条攻击路径；另外两条是男主基础页的旧进阶参考和骸翼兽原作飞移参考。正式进阶使用独立破晓勇士；骸翼兽按既有骸颚撕咬／蚀息规则使用新版形象。召唤的战斗对照演示仍供参考，实际召唤在地图上进行，召唤出的骸卫使用新版地图形象；没有新增召唤次数、数量或伤害。

接入内容包括角色图集、脚底阴影、独立左右帧、行走循环、攻击／施法轨道、已确认的视觉收尾、受击／未命中／退场，以及相应特效。修正了进阶职业与个人身份选择、怪物旧图覆盖新图、左右帧重复镜像和银弓被误选为普通弓的调用。卡牌数值、法术权限、装备、召唤规则、存档结构及唯一伤害结算没有改动。

运行素材与检查图均记录尺寸、字节数、用途和哈希。角色图集无损保存已确认的RGBA像素；16位特效源转换为对照渲染器实际使用的RGBA8，避免两种PNG解码器出现末位色差。少数微小碎片保留对照页独立的横纵显示尺寸，运行渲染支持显式逻辑尺寸。

验证结果：

- [运行检查](runtime-checks.json)：535775项检查通过；886条实际攻击路径正确选择，47组战斗形象各验证一次HP结算与清理，另验证三组完整时钟播放及死亡淡出。
- 固有攻击既有专项检查150项通过，原攻击平衡、HP消耗、掉落与召唤权限保持。
- [后台截图检查](screenshots/checks.json)：70张实际运行截图，无布局错误。使用已有原生窗口保护，在启动前阻止窗口显示和应用激活；没有切换用户窗口。抽查地图待机、四向行走、主角进阶、敌方近战、雷电落地冲击、旧版石翼兽和魔物固有攻击。
- [运行抽查图](screenshots/runtime-contact-sheet.png) · [导入清单与角色→动作→结算时刻](import.json) · [全部图片体积记录](image-inventory.json) · [完成记录](completion.json)

主要入口：`data/reviewed_animations.json`、`core/reviewed_animations.gd`、`core/party_sprites.gd`、`core/battle_animation.gd` 和 `core/innate_attack_animation.gd`。本次图集位于 `assets/character-art-sync-20261024/`，工程导出规则会包含这些运行资源，排除本目录的检查材料。

复现使用 `tools/import_character_art_sync.py`，它固定读取本目录保存的 `source-gallery.json.gz`；后续美术版本需另建快照／版本记录，避免混入其他对话正在制作的内容。运行检查：

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path actual --log-file /private/tmp/character-art-headless.log --script res://tests/character_art_sync.gd
```

[返回「角色重绘 · 全动作对照」](../../../art-review/character-expansion-20261018/index.html#runtime-sync-20261024)

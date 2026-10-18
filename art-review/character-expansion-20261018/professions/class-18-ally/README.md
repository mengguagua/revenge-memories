# 修女（职业样板）

已完成 2 张独立战斗姿势、2 张战术行走步相、2 张战术待机变化。深青长袍、象牙肩领与短头纱、棕色发辫沿同一身份制作；原本存在的细杖与握持、举升动作保留，腿部按原袍遮挡处理。该包是职业样板，不给芙拉或其他角色新增已解锁能力。

- 战斗入口：`battle/frame_mapping.json`，原帧 7 / 8 覆盖生产目录的 30 条白魔法场景变体，特效继续使用原外置图。
- 地图入口：`maps/frame_mapping.json`。行走原 6 槽只有 2 个独立步相；待机原 6 槽只有 2 张独立图，均保留真实别名与原时序。原行走用通用 sprite 50，重绘保留过步、跨步与可见落脚位置，衣装遵循修女身份。
- 对照：`battle/reviews/battle-final-original-vs-new-dark.png` 与浅底版本；`maps/reviews/map-original-vs-new-light.png` 与深底版本。
- 原图、提示词、未选中迭代均保留在各自 `source/`、`prompts/` 和候选目录。`manifest.json` 说明各版用途；`image-inventory.json` 逐图记录尺寸、字节、SHA-256。
- 分帧 4 倍像素，按可见头纱、鞋/袍底登记，未用武器包围盒夹移身体。仅作隔离美术交付，未修改或接入游戏代码。`qa-report.json` 区分人工复核和结构校验。

生成使用内置 image_gen；整理仅作裁切、等比缩放、锚点登记、方向镜像和无损 PNG 压缩。构建统一演示时读取上述映射即可。

## 原生战术移动来源纠正

当前行走已替换为 class18 原CPU确认的CHR27四方向8槽（6个新绘、2个严格镜像），每相16tick。旧两相混源稿与映射只作历史保留，不再作为正确战术行走。战斗和静态待机保持已通过版本。当前对照见 `maps/reviews/tactical-native/native-v2-dark.png` 与 `native-v2-light.png`；源证据来自 `source-input/corrected-tactical-walk`。

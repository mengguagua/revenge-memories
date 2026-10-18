# 男魔道士（职业样板）

已完成 3 张独立战斗姿势、2 个原生地图步相与 3 个战术待机变化。酒紫尖帽、敞披风、银灰里衬、铜棕头发与深色裤靴构成独立身份；没有沿用敌方老年妖术师的兜帽长袍。

- 战斗入口 `battle/frame_mapping.json`：原帧 0 / 1 / 2，覆盖生产清单 54 条法术场景变体；原外置效果独立播放，身体图不烘焙光效。旋转横展部分是披风，原仅显露的一条支撑腿保留。
- 地图入口 `maps/frame_mapping.json`：原行走相 1 精确等于相 0 水平镜像后右移 1 原像素，新稿执行相同 4 输出像素变换。保留原循环、方向程序与别名，不另造同向步行。待机第二相的手保留衣料遮挡。
- 对照位于 `battle/reviews/battle-v2-original-vs-new-*.png`、`maps/reviews/map-original-vs-new-*.png`。最终战斗与地图深浅板已由主任务复核。
- `source-inspection.json` 记录衣物与动作判断；`qa-report.json` 记录实际校验范围；`image-inventory.json` 逐图记录尺寸、字节与 SHA-256。
- 原始 ImageGen 输出、提示词及未选中迭代均保留。三个战斗帧各低于 50KB；组合图集约 64KB，经无损优化后保留清晰度，不为软体积参考缩小四倍像素规格。

仅为隔离职业美术样板，不修改游戏代码，不给赫尔维、卡洛等角色新增已解锁法术。统一动作演示读取映射即可。

## 原生战术移动来源纠正

当前行走已替换为 class15 原CPU确认的CHR26四方向8槽（6个新绘、2个严格镜像），每相16tick。旧两相混源稿与映射只作历史保留，不再作为正确战术行走。战斗和静态待机保持已通过版本。当前对照见 `maps/reviews/tactical-native/native-v1-dark.png` 与 `native-v1-light.png`；源证据来自 `source-input/corrected-tactical-walk`。

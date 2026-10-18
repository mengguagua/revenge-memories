# 盟军天马骑士 · class 3 / ally

战斗十张独立姿势、地图三张待机、真实战术四向八槽已完成，全部获 root 视觉复核通过，包括地图枪端方向纠正。旧 `original-walk-3.png` 是错误混用 village/world 选表与固定 CHR26 的参考，未用来生成本套天马移动；旧源和旧记录保留追溯。

入口：`battle/frame_mapping.json`、`maps/frame_mapping.json`。身份 `ally-pegasus-rider`，显示名“盟军天马骑士”。栗色发、银额饰、银轻甲、蓝灰骑装、棕手套靴；象牙白天马、深蹄、棕缰具与暗红鞍垫。所有实际重绘使用内置 ImageGen，原始生成图和所有提示词留在各 `source/`；技术处理仅裁切、等比缩放、整体登记、原规则镜像及原特效合成。

战斗逻辑 80×96，输出 320×384，源锚点 [40,72]。独立源帧 0–7、34、35；16、33 与0经尺寸与逐 RGBA 字节验证完全相同，交付别名也完全相同。0、6、7是相同高V翼下的平持、收枪、低位单次刺出；1–5为原飞行翼/腿相；34横举投枪，35空手释放。原常规攻击187 ticks、接触108；六个投枪变体使用各自74–87 ticks原时序，均单次接触，无新增攻击能力或额外投射物。原 `3d558f7aa86343` 外置飞枪像素和坐标逐tick保留，见 `battle/timing-qa.json` 与释放前后深浅对照。

翼蹄辨形证据保留在 `reference/pegasus-poses-2-3-4-tiles.png` 和 `battle-oam-layer-inspection.json`：3下左孤立斜段是被马身遮住的远翼尖，不是脚；同一CHR48在4变为鼻前的水平小翼尖。不能用全图最下alpha作为蹄锚，也不能把翼根、鞍和骑手靴误作马腿。地图idle左下斜段与右上枪尖按同一被遮挡枪线处理，不计入蹄部登记。

地图待机逻辑24×24，输出96×96，锚点[12,20]，六槽[0,1,2,1,0,1]，原循环[0,1,2,1]、[14,8,14,8] ticks，60.0988 FPS。0近翼上收/前腿抬，1近翼水平/前后腿垂直，2近翼下落/后腿收起。三个独立帧都保留完整轮廓，深浅底通过。

登记QA中的≤0.5输出像素仅描述明确选定蹄ROI锚点的X取整误差；Y当前0。它不表示每只脚、关节或翼尖的坐标全部精确复刻。其他肢体和遮挡由原/新图逐项视觉检查，未非等比压缩人物、未为了武器边界整体clamp身体。已确认的0/3/7关键帧SHA保持不变。

现29张交付PNG，独立帧最大59,873字节；十帧战斗汇总图集549,464字节。遵循视觉质量优先，羽毛层次、脸、缰具与透明边缘保留无损，root明确接受超过50KB参考值的羽翼角色。`qa-report.json`、`image-inventory.json` 记录尺寸、字节、hash和范围；原生成大图离线隔离，不用作运行图。

真实战术移动使用 `source-input/corrected-tactical-walk/overlay.json`：bank011:L0BB5B1按类/阵营选择动作与CHR，class3为CHR19，8槽顺序up0/1、right0/1、down0/1、left0/1。catalog完成352组CPU/OAM与独立ROM布局交叉验证。CPU已做镜像，scenario无额外镜像。六张独立方向相由ImageGen绘制；right2/3与left6/7在源和新图均通过完整尺寸与逐RGBA镜像相等验证。输出 `maps/tactical-native-frames/`、`maps/frames/tactical-native-walk.png`；逻辑32×24 → 128×96，原tile锚点[16,24]，每相16 ticks。原投影ROI[0,22,32,24]在每帧独立按4倍最近邻合成到[0,88]，像素hash与输出区域相等，不用投影作脚锚。

背向第1相的尾端是身体登记点，明确标 `anchor_is_anatomical_foot=false`；其后蹄被尾部部分遮挡，只做视觉腿相核查，不报告虚假的单蹄精度。其他明确可见蹄使用记录的ROI；全部主体保持悬空高度。

地图枪端按本类原像素纠正为上/右上钝帽、下/左下钢刃，背面下端只保留遮挡外的小刃。证据为本类CHR19原动作125/126/129/130与侧向128，以及静态metatile6、CHR24/25/21循环；详见 `reference/map-spear-endpoint-native-evidence.png`。最初“枪尖朝上”的惯性画法已撤销。端部新部件由ImageGen生成，仅在记录的端部遮罩内技术合成，`maps/source/spear-end-patch-qa.json`验证遮罩外RGBA完全相同，主体、翼相与投影保持。战斗枪姿不受这次地图更正影响。

`gallery-action-ids.json`共20条（7攻击、4反应、四方向行走/静止8条、静态待机1条）。地图循环GIF为10ms量化预览，统一gallery按60.0988 FPS导出最终视频。两份mapping均有 `parent_visual_review_passed=true`。

本代理未改actual、未接入游戏、未启动Godot。完整统一gallery和最终视频由root收尾。

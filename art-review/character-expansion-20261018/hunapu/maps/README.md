# 胡纳普地图形象 · 2026-10-18

独立美术交付，未接入游戏。保持已确认的蓝发、象牙上衣、深蓝分片裙甲、皮革腰带护腕、铜剑与小护盾身份。裙甲覆盖骨盆及上腿，不作裤裆或裤腿解释；四倍仅增加像素数，逻辑占格与0.25绘制倍率不变。

当前播放入口为 `frame_mapping.json`。旧 `mapping.json` 和 `source/previous-map-frame_mapping.json` 为历史批次记录，旧战术移动混源解释已撤销，不再作为当前战术动画入口。

| 场景 | 核定原源 | 单帧原/新 | 当前图集 |
| --- | --- | --- | --- |
| 剧情 | personal_01，原村庄CHR30 | 32×24 / 128×96 | deliverables/story-world-walk.png |
| 大地图 | 本项目明确复用剧情形态，单列映射/演示 | 32×24 / 128×96 | 复用剧情图集 |
| 战术移动 | 原CPU bank011:L0BB5B1，class21 ally CHR27 | 32×24 / 128×96 | frames/tactical-native-walk.png |
| 战术待机 | class_21_ally，metatile42 | 24×24 / 96×96 | deliverables/tactical-idle.png |

剧情/大地图源与冻结personal_01逐文件字节相同。原bank7 L079136/L079158/L078E4F在默认26之后明确切换CHR30；主角slot0/1使用L0791BA[1,2]。详见 `reference/story-world-source-audit.json`。本次战术修订没有改动剧情、世界或静态待机的16张PNG，原SHA逐项通过。

真实战术移动来自 `source-input/corrected-tactical-walk/overlay.json` 的class-21-ally记录，已通过CPU/OAM与独立ROM布局交叉验证。8槽为up[0,1]、right[2,3]、down[4,5]、left[6,7]；每相16 ticks，60.0988 FPS，连续相位，一格16 tick/每tick1像素。6必须对应mirror3，7对应mirror2，源和新图均完整尺寸/逐RGBA字节验证相等，不能误按同相号镜像。CPU镜像已烘焙进源图与输出帧，scenario的direction_mirror_x为空。

6张独立图由ImageGen按真实原动作重绘，2张左向依已证明的交叉镜像生成，交付在 `tactical-native-frames/`。正面铜剑斜向右上、侧面斜向左上、背面只露头左短刃。侧向源x21–22,y13是脸/鼻凸块；紧凑护盾是screen-left x9–11,y14–17方块，按原遮挡保留，不套旧personal01位置，不补未可见的手部关节。没有把源方向标签当成翻转武器的理由。

`native-walk-qa-report.json`记录原源、尺寸、字节/hash、选定支撑靴底XY、等比缩放与登记偏移。8槽X取整误差≤0.5输出像素、Y为0；该数字仅指选定靴锚，不声称全部肢体逐像素相同。当前真实移动独立帧最大6,851字节，图集42,225字节；全程oxipng无损，未颜色量化、未非等比拉伸、未为容纳武器clamp身体。

静态待机保留已通过的3独立姿势，六槽[0,1,2,1,0,1]，循环[0,1,2,1]/[14,8,14,8]ticks。之前待机1及重复3/5的剑长与脚XY修正保持；剧情/世界继续各自四方向原时序演示。

旧战术移动的CHR26+village表是历史混合提取，不是真实战术原作，也不因这次发现自动判坏正确的CHR30剧情资源。旧 `deliverables/tactical-walk*`、所有原始生成图和旧映射仍保留，未覆盖。当前实际引用16张旧非移动PNG加9张新战术PNG；物理目录还含旧历史交付。

源提示词在 `source/native-walk-prompts.md`，原始两帧生成图及未选版本保留。`register_native_walk.py`仅裁切、等比采样与刚性登记；`complete_native_walk.py`做路径/大小/脚位/镜像/保留SHA检查及图集合并。深浅四向对照与GIF在 `reviews/tactical-native-*`，GIF为10ms量化预览，最终视频由统一gallery按60.0988FPS导出。`native-walk-gallery-action-ids.json`列此次更新的8条行走/静止动作ID。

Root已复核四向浅底，小盾、裙甲、持剑方向与步相通过；本代理逐图补看四向深底、透明边缘和完整轮廓通过。未启动Godot，未修改actual，未做游戏接入。

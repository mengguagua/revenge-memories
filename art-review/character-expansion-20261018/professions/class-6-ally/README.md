## 原生战术行走修订（2026-10-18）

当前地图入口 `maps/frame_mapping.json` 已改用独立CPU/OAM审计的CHR19真四向8槽。6张ImageGen新绘+2张尺寸与RGBA严格证明的镜像（2←6、3←7），128×96输出保持32×24逻辑，无额外方向flip。单帧最高7691字节，图集48794字节，均无损压缩；15张battle/idle PNG保持原哈希。新walk已通过代理深浅/脚ROI/完整轮廓自检及root最终视觉复核，当前版本冻结。

up0高拳与up1低臂分别保留；down为低/高空手摆动。侧向NE短尾→SW浅色枪刃，中段可被身体遮挡。上向顶部仅有短浅色端，未扩画为大枪头；不推断不可见枪端细节。旧CHR26混用village表造成的缺头判断现已撤销，旧稿只留作历史。

量化精度只指选定主靴锚点X≤0.5/Y0，不能等同全部关节/脚点零误差。下方此前walk结论由本节及 `maps/native-walk-qa-report.json` 取代。

# 盟军枪兵 · class 6 / ally

七张独立战斗姿势、两张地图行走步相与三张固定待机相已完成。全部战斗与地图姿势均获 root 视觉通过，包含 walk v5 原侧斜段修正；所有素材已自检原语义、透明完整性、深浅背景、脚 XY 与原时序。没有修改 actual/、接入游戏或启动 Godot。

入口：`battle/frame_mapping.json`、`maps/frame_mapping.json`。身份 `ally-spearman`，显示名“盟军枪兵”。低开面钢盔、短深发、清楚眼睛、对称银钢胸甲、小肩甲、浅灰绗缝短衣与蓝灰侧布、棕皮护腕和靴，保持源露膝范围；结构区别于敌方暗红斜襟战袍，非换色。

战斗原 80×64 → 320×256。独立源帧 0、1、2、3、4、5、12，23 是 12 的逐 RGBA 像素别名。0–3 为四个跑动腿相，4 宽步腰平蓄枪，5 肩高水平单次平刺，12/23 紧凑站姿腰平持枪。全部枪杆连续穿过双手，无弯杆、第二把枪或投射物。

只绑定当前可触发 `original_class_6_normal`，219 ticks、contact_tick=82、contact_count=1、无外置效果。六条提取出的 javelin 变体已由可用性审计列为 reference_unreachable（class6 不能使用 item4/7），没有作为可用投枪能力展示。通用待机/未命中/受击/退场使用原 12 姿势。完整近景检查 GIF 在 `battle/reviews/normal-full-219ticks-{dark,light}.gif`；相机跟随原位移，GIF 10ms 量化后 3.64 秒，最终完整场景由统一 gallery 按 60.0988 FPS 导出。

地图行走原 32×24 → 128×96，六槽 `[0,1,0,1,0,1]`，每相 16 ticks。字段 right 仅代表原程序未镜像基准，不能反推脸或武器朝右；最终 v5 保留原第0槽左上到右下斜段与握点，运行 left 才按原规则镜像。原第二步 OAM `L0AA3A4` 的上右 8×8 tile 是 FF，头肩确有缺块；已按授权由 ImageGen 用完整第一步身份补全，不修改冻结原图，也不声称缺失部分是原始像素复刻。第一步支撑/抬脚次序经原图复核修正。

地图待机原 24×24 → 96×96，六槽 `[0,1,2,1,0,1]`，循环 `[0,1,2,1]` / `[14,8,14,8] ticks`。固定左前朝向，单根右上—左下斜枪，原枪两端在 `x+y=22` 同一直线上。前左靴低于后右靴，保留原静态透视，未镜像为行走朝向。

脚位使用明确 ROI：战斗按各源姿势最下靴部带，所有 X 误差 ≤0.5 输出像素、Y 误差 0；地图行走原下部双靴范围中心/基线 `[62,96]`，待机原前左支撑靴中心/基线 `[42,80]`，新待机为 `[41.5,80]`。实际 ROI、等比尺寸与整体登记偏移逐帧记录在映射中，不用全图枪端包围盒代替脚。

实际美术全由内置 ImageGen。各 `source/prompts.md` 保存全部 prompts 与原始生成图；最后选中 battle keyposes/run-a/run-b v1、maps walk v5、idle v3，早期地图稿离线保留。技术处理仅为裁切、等比缩放、整体平移、原规则镜像、原时序合成和无损压缩。

`qa-report.json` 记录 25 张交付 PNG 的尺寸/字节/hash、脚位、源别名和唯一普通动作。独立帧最大 25,287 字节；地图图集各小于 20KB；七姿势战斗图集 154,659 字节，为完整汇集七帧并保留细节采用无损 PNG。`image-inventory.json` 另列所有原稿、参考和预览；`gallery-action-ids.json` 列 14 条统一动作 ID。

对照：`battle/reviews/keyposes-original-vs-new-*.png`、`battle/reviews/run-four-original-vs-new-*.png`、`maps/reviews/tactical-walk-*.png`、`maps/reviews/tactical-idle-*.png`。源语义与 FF 限制详见 `reference/source-semantic-audit.json`。

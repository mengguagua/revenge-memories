# 盟军隼骑士（class-5-ally）暂停交接

2026-10-18：用户明确中断并要求切换其他 Sol 尝试。当前代理已停止全部制作、生成、修订；本文件是中断后的唯一交接写入。未接入游戏，未修改 actual/。

## 当前完成与根审状态

- 当前制作范围是本目录的 class-5-ally（盟军隼骑士）完整 battle + maps。
- 战斗关键姿势 0、3、7 已完成。root 已逐张检查深、浅底并明确通过；保留现版，不重开设计。
- `battle/frames/frame-000.png`：384×544，68,315 B。开放银白盔、金色边饰、完整臂胫甲、白天马额甲、深蓝金边鞍布；近蹄登记通过。
- `battle/frames/frame-003.png`：384×544，49,056 B。下降近翼、折叠前蹄和左下分离远翼末端通过；左下孤立小片是远翼，不能作为蹄。
- `battle/frames/frame-007.png`：384×544，67,838 B。高 V 翼及更低、更前伸的枪位通过。
- 根审板：`battle/reviews/keyposes-original-vs-new-light.png`、`battle/reviews/keyposes-original-vs-new-dark.png`。
- 原始生成图及全部实际关键图 prompts 保留在 `battle/source/`，登记数据为 `battle/source/keypose-registration.json`。
- 已通过 raw：0 用 `pose-000-generated-v4.png`；3 用 `pose-003-generated-v3.png`；7 用 `pose-007-generated-v1.png`。早期候选也保留，不替换通过版本。
- `battle/source/approved-keypose-000-sha256.json` 已有。中断前曾写 `approved-keyposes-sha256.json`（覆盖 0/3/7），最后工具输出被截断；接手时只读确认该文件是否落盘即可。
- 超过 50 KB 的 0/7 已获 root 同意按羽翼、金属细节质量保留，体积是优化参考，不为达标破坏画质。

## 正在等待／已中断的生成

- 姿势 1 第一次 ImageGen 调用被用户于约 10.9 秒时中断，工具返回 `aborted by user`，没有返回生成结果或文件路径。
- 本代理没有轮询结果、重试、复制或加工该调用的输出。不能宣称姿势 1 已生成完成。
- 调用输入是 `reference/pose-001-geometry-8x.png` 与已通过的 `battle/source/pose-000-generated-v4.png`，透明背景。
- 若后续工具自动给出该次调用结果，仅先保存原始输出与路径；是否继续由接手代理依据用户的新授权决定。
- 原始工具输出通常位于 `/Users/gcc/.codex/generated_images/01a14afa-1fa4-7113-95b5-f9ee6c3bdc79/exec-*.png`，但本次没有可确认的具体文件名，勿猜测或误领其他代理结果。

该次未完成调用的 prompt：

> Use case: identity-preserve. New flying battle pose1, same ALLIED advanced Falcon Knight from image2. Image1 exact CLASS5 original geometry governs pose. One complete transparent pixel-art sprite.
> Different wing phase from reference: NEAR wing on screen-RIGHT is lifted almost STRAIGHT VERTICAL, very tall narrow feather column from flank to top, only slight outward lean. FAR wing behind rider on screen-LEFT is also raised but shorter/more curved, much of its root hidden by body. This is a narrow raised-wing silhouette, not broad V. Original overall visible bbox37×68 native, narrower than pose0 53×69. Rider and horse occupy LOWER portion beneath those tall wings. Preserve actual source folded/stepping horse legs: near foreleg extends downward to lowest hoof, other foreleg bends, visible hind leg bends behind to right. Do not use a wing as hoof.
> Same helmeted female identity: ivory-silver open helmet with fine gold brow, auburn braid, readable eyes, white-gold full cuirass/pauldrons/forearm/shin plates, navy short cloth, brown gloves/boots. White pegasus, silver forehead guard, ash mane/tail, brown reins, navy-gold saddlecloth. One lance horizontal LEFT at source shoulder/horse-head level, other hand reins. Horse/rider/wing roots and saddle must remain distinct.
> Fine crisp pixel-art feather clusters and metal detail as approved image2. Same anatomical scale of rider/horse, source1 wing-to-body ratio and limb positions. Complete long raised wing tips and lance, generous transparent margins, no text/shadow/effects or extra legs.

## 未完成／待复核

- 战斗 canonical 共 10 张：`[0,1,2,3,4,5,6,7,49,50]`；尚未完成 1、2、4、5、6、49、50。
- Required 另有 25→0、48→0 的精确 alias。不要另画假动作。
- 尚未制作本类 static idle 和真实四向 tactical walk；参考与审计已备好。
- 尚未建立本类完整 `battle/frame_mapping.json`、`maps/frame_mapping.json`、最终 QA、尺寸字节清单和交付 manifest，因此本类不得标整包 ready。
- 姿势 1 是窄幅近翼直上、短远翼上举；姿势 2 是向右后掠、末端上卷的翼相，不能直接复制 0 的宽 V 翼。
- 49 为横举投枪，50 为释放后空手；仅保留原程序一次外置投射物，不新增发射次数。

## 本类源与登记要点

- 自身源 atlas：`../../source-input/original-motion/class-5.png`（相对本目录）；本目录副本 `reference/battle-native-atlas.png`。单格 96×136，16 列；输出宽高各 ×4，即 384×544，逻辑尺寸不变。
- 原锚点 `[48,96]`，四倍 `[192,384]`。按本类原蹄 ROI 登记，不用 class3 的画面或假定同几何代替。
- production 单位与能力：`reference/production-unit.json`。普通攻击 `original_class_5_normal` 158 ticks、contact 79；投枪 6 个可用变体，最终 variant_keys 以 production 中实际键为准。
- class3/class5 外轮廓包围盒尺寸虽相应，alpha 有差异，不能宣称完全相同或复用 class3 新画面。证据在 `reference/class3-class5-geometry-comparison.json`、`class3-class5-alpha-differences.json`。
- pose3 原 OAM `L018C10`、CHR8 的 tile48/4A/49 证明左下孤立段为远翼；证据 `reference/class3-class5-pose3-far-wing.json`。
- 已通过 pose3 真蹄 ROI `[51,87,53,88]`，输出目标 `[208,352]`、实际 `[208.5,352]`。0/7 自身 ROI `[51,94,55,96]`，目标 `[212,384]`。误差口径只指选定登记锚点取整，不是所有关节／蹄逐点相同。
- 登记工具 `battle/registration_tools.py`：技术裁切、等比缩放、统一平移、无损压缩；不允许 clamp 整人入框导致身体漂移，不进行艺术性代码绘制。

## 地图已知证据与风险

- 正确 tactical walk 是 CHR19、32×24、8 槽 CPU 输出。参考 `reference/corrected-tactical-walk-record.json`、`corrected-tactical-walk-source-atlas.png`、`native-walk-four-directions-light.png`。
- 四向槽为 up[0,1]、right[2,3]、down[4,5]、left[6,7]；本类已证明 2=mirror6、3=mirror7。PNG 已包含 CPU 镜像，scenario 不另加方向镜像。每相 16 ticks。
- 正确 source_audit.status 必须为 `verified_native_tactical`，引用 overlay 与独立验证证据。不能回到旧固定 CHR26 + village 表的错误 walk。
- 本类原飞行投影从 native y21 开始：保留 ROI `[0,21,32,24]`，四倍后在 `[0,84]` 独立技术合成。不能套 class3 只取最后两行的规则。
- up0 的 CHR19 tile2F row4，即 native y20 独立黑像素，仍是主体末端，必须保留；row5–7 才是下方展开投影。其他方向的相关 tile 证据已由 source_catalog 发出，见下项。
- side0 底 AC/AD：rows1–4 透明，rows5–7 黑投影；AE row6 黑横线。side1 DC/DD rows5–7 黑投影，DE row7 黑线。up1 中心5E/5F rows0–3 主体、rows4–5 透明、rows6–7 黑投影。up0 两侧7E row0 是翼端、row6 是影线。当前 `reference/native-walk-shadow-audit.json` 还是初步行统计，最终应补入这些经源 tile 核实的结论。
- 不以阴影作蹄锚。枪的两端、可见蹄与羽翼须按本类 CHR/OAM 和轮廓单独辨认，不凭颜色或方向标签倒推；本类地图尚未完成枪端审核。

## 接手后的顺序（须等待新的继续授权）

1. 保持已根审通过的 0／3／7 和设计不变，先确认中断调用是否确有可归属的原始结果。
2. 按自身源完成 1／2，输出深浅对照后发 root；随后 4／5、6／49／50。
3. 按本类源完成 static idle 和真实四向 walk，主体与原投影独立登记，逐向检查枪端、羽翼与马蹄。
4. 完成标准 mapping、原始 prompts、字节／尺寸／哈希、深浅预览与 QA，通知 root 统一 gallery/export；不自行接入游戏。
5. 原排班后续为 class-13-ally → class-20-ally → class-24-ally → class-11-enemy；此处仅记录排班，不代表中断后可以自行开始。

此前本代理负责的男主 maps、enemy12、ally12、ally6、ally3 均已完成且经 root 冻结；本次中断不重新打开这些已通过资源。第一章 14 组已由 root 宣告美术完成。

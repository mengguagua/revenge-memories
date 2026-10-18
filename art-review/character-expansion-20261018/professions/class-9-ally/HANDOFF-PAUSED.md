# 已暂停：交接给其他 Sol

用户明确中断并切换模型尝试。自收到暂停指令起，不再制作、生成、修订、登记或导出。以下仅记录已有状态。

## 范围与约束

- 本目录：`art-review/character-expansion-20261018/professions/class-9-ally/`，盟9剑士职业样板。
- 仅隔离美术；不得改 `actual/`、原游戏业务、旧已确认男主样板或其他代理素材。
- Root 已接管全局 catalog / gallery / export。
- 已有浏览器 file URL 安全拒绝，不得用 HTTP、其他浏览器或 Playwright 绕过。
- 后续队列原为盟10 → 盟16 → 盟17 → 敌3；目前都尚未在本代理启动。
- imagegen 使用内置工具；原始生成图保留。技术裁切、统一 NEAREST 缩放、登记、精确原特效合成可用，不能代码画人体。

## 已完成并根审通过：全部战斗

`battle/frame_mapping.json` 为 `complete_art_review_passed`，Root 已加入画廊并开始增量导出11条含反应动作。

- 15 个 required source slots，13 个 canonical，12 张独立新人体，7 条绑定攻击程序。
- Canonical：0–11、24。12 / 23 精确别名到0。
- 6 = 新7同坐标 + 原6独立剑弧；原7的3344个已占据 RGBA 像素与原6同坐标严格相等。没有合成代码人物。
- 输出规格320×256，源80×64，源anchor40,64，OAM cutoff12，idle12。
- 最大独立帧17,785字节；无损图集172,295字节，保留视觉质量，属于软体积目标的说明项。
- 完整深浅对照：`battle/reviews/final-canonical-dark.png`、`final-canonical-light.png`。
- 映射、QA、原弧证明、图集、全部分帧已落盘；`image-inventory.json` 当前包含已存在的参考/历史/交付PNG。
- Root 明确要求：地图制作不得再改已通过的战斗图。

### 战斗最终选择（不要误用历史候选）

| 帧 | 规范候选来源 |
|---|---|
| 0、7、24 | `battle/candidate-keys-v3/` |
| 1、4 | `battle/candidate-local-v5/` |
| 2、3 | `battle/candidate-motion-v1/` |
| 5 | `battle/candidate-motion45-v3/` |
| 8、9、10、11 | `battle/candidate-recovery-v3/` |
| 6 | `battle/frames/frame-006.png`，源弧合成 |
| 12、23 | `battle/frames/frame-000.png` 的别名 |

规范交付始终是 `battle/frames/` 和 `battle/deliverables/battle-canonical.png`，生成原稿不是运行图。

### 已接受的几何差异

这些是选定登记点之外的剑型/轮廓残差，不能声称每个关节逐像素一致：

- 7剑尖约11输出px横向残差；24剑尖约6px竖向残差。
- 4最终握点约(191,118)对原(192,112)；根审确认举臂、支撑脚、左收膝关系恢复。剑尖约13px X / 9px Y残差获准保留。
- 8剑尖约4px X；9约13px X；10约14px X / 11px Y；11约8px Y。
- 8/9必须左高靴、右低靴；10/11必须双低靴。历史v1生成的单膝跪姿已废弃。
- 4历史v1–v4存在握点左偏、长伸腿与身体关系错误；只用最终v5。

### 工具与历史

- `tools/package_battle.py --review-passed` 已执行，输出成功、无结构错误。
- 登记工具：`register_keys.py`、`register_motion.py`、`register_motion45.py`、`register_recovery.py`、`register_recovery_v3.py`。有些只复现历史版本；当前完整选择以 `package_battle.py` 的 selection 为准。
- `candidate-local-v5` 的1/4登记通过单次技术脚本完成，已保存 `registration.json`。
- 8/9 v3图集分帧使用两个独立alpha连通角色分离，避免邻帧剑刃串入；保留原raw、分帧cut及 `battle/source/recovery-v3-sheet-cut-audit.json`。没有擦掉人体来修姿势。
- 全部提示词在 `battle/prompts/`，各次原稿在 `battle/source/`，不要清理历史。

## 地图：仅源参考与三组未登记生成原稿，尚未通过验收

**没有地图 frame_mapping.json，没有已通过的新地图交付，不得记为完成。**

已建立：`maps/reference/`、`source/`、`prompts/`、`reviews/`、`frames/`、`deliverables/`、`tactical-native-frames/`。

### 已核源

- 真实战术移动源为 `source-input/corrected-tactical-walk/class-9-ally.png`，CHR26，32×24，8个独立槽，没有镜像别名。
- 槽顺序0/1 up、2/3 right、4/5 down、6/7 left；CPU已处理方向镜像，不能额外镜像。
- 每相16 native ticks，完整两相32 ticks。
- `maps/reference/corrected-tactical-walk-record.json` 保存完整源记录。
- `native-source.png`、`native-000.png`…`native-007.png`、四组 `*-pair-light.png` 和 `native-all-light.png` 可用。
- 正确静止源为 `source-input/legacy-assets/assets/original/graphics/map_units/class_9_ally.png`，已复制 `maps/reference/static-source.png`。
- 静止3独立相，6槽别名序列0、1、2、1、0、1；已切 `idle-000.png`…`idle-005.png`，参考板 `idle-three-light.png`。
- 旧 original-walk-9.png 是旧混合来源，不得拿来作为当前真实战术行走输入。

### 源语义与根审意见

- front/right/left：屏幕左短竖剑、屏幕右矩形盾。up：屏幕右竖剑、屏幕左盾背/持盾臂宽块。
- Root 已允许按 up 左宽块的本类盾背/持盾臂保守处理，不能添加长披风；仍以自身八槽轮廓为准。
- 本类八独立槽，不能套盟8的图，也不能把left当right镜像。
- 新设计沿战斗：栗棕短发、琥珀眼、深青铜边分片甲、象牙袖、酒红短腰带、炭灰裤、钢蓝护胫、深棕靴、矩形青盾。

### 已返回但未复制到项目、未登记的地图原稿

以下路径都确实由内置ImageGen返回；仅原始候选，未做后续视觉验收。

1. right slots2/3，提示词 `maps/prompts/native-right-v1.txt`
   - `/Users/gcc/.codex/generated_images/01a14af9-c12b-7160-8595-1c432794fedb/exec-1ca937f1-e872-4c8f-909f-1641a6900c91.png`
   - 已目视原稿，未登记。潜在问题：脸仍明显向左，需与本类right源实际脸形独立比较；第一相低靴/高靴可能被常规走路习惯颠倒；剑尖可能高于源头顶约数输出像素。不得凭提示词认定通过。
2. down slots4/5，提示词 `maps/prompts/native-down-v1.txt`
   - `/Users/gcc/.codex/generated_images/01a14af9-c12b-7160-8595-1c432794fedb/exec-9daa6130-0013-4007-8343-2b48440b29e8.png`
   - 已目视原稿：前脸、盾高低、交替靴相可读；未登记，尚无原/新同尺寸对照或根审。
3. up slots0/1，提示词 `maps/prompts/native-up-v1.txt`
   - `/Users/gcc/.codex/generated_images/01a14af9-c12b-7160-8595-1c432794fedb/exec-4ebb78f6-3606-4b9c-b530-0bd6a1fa81e2.png`
   - 已目视原稿：背影、左盾背/右剑、交替脚可读；未登记。护胫背面是否过于像前面膝甲须检查，不把原稿当通过。

### 用户中断时的调用

- 正在调用 left slots6/7 的内置ImageGen；提示词已经保存 `maps/prompts/native-left-v1.txt`。
- 输入：`maps/reference/left-pair-light.png` 和 `battle/source/style-neutral-reference.png`。
- 工具返回 **aborted by user after 21.2s**，没有返回图片或文件路径。
- 是否在默认生成目录留下部分结果未知；未调查、未重试、未启动新生成。接手者如获继续授权，可先检查是否已有结果，不能假称已完成。
- 静止3相新图尚未生成。

## 下一步（需用户恢复后执行）

1. 仅恢复本类地图：把上述三组已知raw复制到本目录保留，检查被中断left调用是否有已完成输出，再决定是否重试。
2. 按源实际可见靴/头登记128×96；保留原武器/盾轮廓位置，禁止按武器整体bbox居中/clamp。
3. 深浅底同尺寸八槽对照，优先核right头向、各相真实低靴、剑尖高度、up盾背；只局部修问题。
4. 生成静止3相并独立审查其短剑位置和盾高低，不能用预设循环替代源。
5. 根审通过后才写 maps/frame_mapping.json，source_audit.status须为 verified_native_tactical，引用源验证证据；保持battle哈希不变。
6. 完成本类顶层manifest、QA、source-inspection、README及全PNG inventory。目前这些顶层整包文件尚未完成，仅battle QA完整。
7. 再按既定队列推进盟10→16→17→敌3。

## 其他未完只读待办

- Root 请求核 class23 勇者是否完全由男主现成35姿势与地图覆盖，制作alias覆盖证明。**尚未调查/完成**，不得把23自动记作独立完成；不应重复绘制35帧。
- 其他已完成自有包盟18、盟15、盟14、盟8已在各目录冻结，当前不修改。
- 近期已发出的有限源审计结论（盟7投枪握点、盟2静止短护臂、盟5远翼与投影）已通过协作消息交给对应代理；本交接不新增调查。

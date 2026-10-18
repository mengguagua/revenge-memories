# PAUSED — 用户明确中断，交其他 Sol 尝试

> 历史快照：后续 `sol` 批次已选定 21／22 新稿并补齐地图。当前结果以 [manifest.json](manifest.json) 与 [QA](qa-report.json) 为准；下文保留原暂停现场。

2026-10-18。此文件只记录停止时状态，不授权继续生产。Astra 已停止所有生成、修订及后续队列。最后返回的两份原始输出仅复制留存，没有规范化、裁切、压缩或采用。

## 隔离范围与约束

工作目录：`art-review/character-expansion-20261018/professions/class-7-ally/`。
不得改 `actual`、游戏代码/资产/数据、冻结源或已经用户确认的男主样板。当前没有接入游戏。后续须以新负责人/用户指示为准。之前队列 class-4-ally → class-22-ally → class-2-enemy 尚未开始。

美术使用内置 ImageGen，原始图及提示词在各 `source/`。技术仅裁切、等比缩放、整帧平移、严格证明的别名/镜像/相同部位复用和无损压缩。禁止程序绘制/换色/骨骼近似或非等比拉伸。必须实看原动作中盔甲、衣裙、手和腿的遮挡；不可由衣甲底边推隐藏关节。

## Battle 当前状态

- 本类为盟方黄金骑士，骑乘；计划 ID `ally-gold-knight`，name `盟方黄金骑士`，class7，source_side ally。
- 112×80 原格，输出448×320，原anchor56,80→224,320，OAM cutoff26。
- 27 required 源槽：0–22、26、49、50、52；25 canonical：0–22、50、52。盟方0==26==49是完整RGBA别名，不能套敌7的BG -64px偏移。尚未制作最终26/49别名文件或最终manifest。
- `battle/normalize_selected.py` 是当前技术登记脚本，输出 `battle/frames/frame-xxx.png`、`source/selected-registration.json`、各批深浅板。已存在25个canonical规范帧，但21/22尚未通过，不能视整包完成。
- **root根审已通过**：0–20（含14修蹄v4，15–20最终旋枪）以及50、52。13中央短遮挡段不能断言第三独立马蹄。14保留右向马头/骑手回望/远侧窄盾。50横举投枪；52空手释放。
- **21/22待继续修订与根审**。当前落盘规范帧采用 `spin-21-22-generated-v4.png`，只是临时候选，绝非已通过。
- 最终 `battle/frame_mapping.json`、`qa-summary.json`、README/最终总板尚未创建。可参考敌7 `battle/build_manifest.py` 的结构，需改成盟方并删除敌方 -64px逻辑，不能照抄敌方语义或根审状态。

### 已通过选择与重要文件

- 0/13/50：`source/keyposes-generated-v1.png`。
- 1：gallop-1-3 v3；2：同组v2；3：同组v1。2/3裁切边界用1416而非1448，防邻格枪尖串入/截断；见脚本。
- 4–6：gallop-4-6 v1。
- 7：gallop-7-9 v2；8/9：同组v3，共同比例196/555。
- 10/11：gallop-10-11 v1。
- 12：turn-12 v1。
- 14：turn-release-14-52 v4左格；52仍v1右格。14两外蹄中心165/270.5，对原166/270。
- 15：`spin-015-generated-v6.png`，单格1044×1507；helmet基准y694，脚本body-top:694。两蹄165/271.5。
- 17/18：`spin-15-17-18-generated-v5.png`，保留整幅新绘轮廓；外蹄分别171/264与170/264.5，对源166/270，残差5–6px，根审通过。
- 16/19/20：`spin-16-19-20-selected-technical.png`。这是v3原上部 + v4 ImageGen收蹄下部；原15–22 y>=58全RGBA一致。v4透明空处有意外灰色幽影，v5背景清理反而删掉真实枪段，故未采用。先将v3每整格按未变头/马颈刚体位移[2,0]、[1,0]、[-21,0]对齐v4，再从原图raw y470使用已修下部。此复用由root明确授权，最终深浅板实看没有接缝/幽影；记录 `source/spin-common-lower-reuse.json`。不得取之前未登记的粗糙拼接候选作为交付。
- `source/spin-final-independent-hoof-audit.json`：14–22逐外蹄X记录。注意此表在21/22改握点之前写，21/22后来候选已变，最终需重测；15–20数据仍对应通过帧。
- `source/spin-lower-body-proof.json`、`ally-enemy-geometry-audit.json`、`source-analysis.json`。

### 21/22明确问题与最近迭代

原几何已由catalog逐像素核实，证据 `../../../demos/source-audit/ally7-weapon-21-22-light.png`：
- 21竖段原x48–49,y10–25，中心约194输出；握接x48–50,y30–32（目标手约196输出）。源26–29行有透明间隔，是释放态，不能补长杆连接拳。
- 22握接x48–51,y40–42（目标手约196,164输出）；上方x51–54,y34–37白段是前臂，不是握点。
- 早期21竖段/手约171输出，偏左约25；22真正握点约154输出，偏左约42。root要求仅局部改手/前臂/杆，不动通过的马腿与头身。
- v3：21向右改善但仍偏左约10–13；22几乎没有充分收回手臂。
- **当前规范帧v4**：21竖段中心212.6、拳约211.1,119.5，右移过头；22握点约184.9,166.2，仍左约11。21拳变成略斜举；22变成更紧的弯肘。实际尺度0.497297；21登记[-38,-66]，22[-23,-66]。不应宣称通过。
- 最新v5刚返回时用户中断。只保存原图为 `source/spin-21-22-generated-v5-UNREVIEWED-PAUSED.png`，没有登记或采用。工具显示人物整体被重新放大/细节变化，21短竖段似与拳之间间隔被缩没，**必须视未审/可能不合格，不能自动替换**。
- v1–v4原稿及各提示词均保留。v4深浅板：`reviews/spin-21-22-selected-dark-light.png`。15–20不用再重画。

### Battle 质量/登记口径

用真实蹄ROI，X看alpha>=128的脚底，Y看alpha>4的可见底；不能按枪端或远处alpha1噪声登记。保留画布内原alpha，不阈值抠掉透明边。允许画布外alpha1..4微弱噪声被技术裁区省略，必须记录；零alpha>4可见轮廓裁切。hiddenRGB只在alpha0清零。图集边界需实际查透明间隔，不能默认均分截断武器。整套未做最终无损压缩/字节清单；体积是质量后的软目标。

16/20是原旋枪分段残形，原4小段新图合为3材料组，不能说三支投枪/多次攻击；武器端点有约十至数十输出像素绘制残差。21独立短段不能改魔法或完整新枪。

## Maps 当前状态：已有原稿，尚未规范化、根审或冻结

全部正确源为 `../../../source-input/corrected-tactical-walk/overlay.json` 中 class-7-ally，CHR19，8个CPU合成槽；6←mirror2、7←mirror3为严格整帧RGBA证明，其他0–5独立。CPU已施加方向翻转，禁止额外direction_mirror；right标签不用于自行改变源朝向。旧village/world+CHR26参考不适用。

当前 `maps/reference/` 已备8槽native、放大正/背/侧参考、static idle 0..5及 `source/source-geometry-audit.json`。静态idle 24×24→96×96，3独立相，aliases [0,1,2,1,0,1]，周期0,1,2,1 / ticks14,8,14,8；固定源朝向，不能按walk镜像。

原稿（均未打包/未根审）：
- `maps/source/tactical-up-generated-v1.png`，1774×887，2格。背面完整灰白马、金甲/深青马衣；右侧杆上钝帽、下短钢尖。看起来可用，尚未定ROI/尺度。
- `tactical-right-generated-v1.png` 历史；`tactical-right-generated-v2.png` 候选，1774×887。只局部抬左格原先错误落地的前蹄，保留后左蹄最低支撑；第二格收拢。上左露木质钝端，不是钢尖。原第一相前侧白端native(20,20)/(23,19)，最低后蹄(8,23)，底部大片黑色不能全部当脚底。v2尚待实际小图验证。
- `tactical-down-generated-v1.png`，1774×887。正向窄马体，两步交替；左侧枪上钝端/下钢尖，尖高于脚底；待小图比例/端点核验。
- `idle-generated-v1.png`，2172×724，3格，**刚返回只原图保存**。抬前蹄/共同支撑/抬后蹄可见，但远侧腿是否多落地/下端枪与脚区仍需实核，未规范化。
- 所有相应prompt-v1/v2.txt已保存。

建议接手后先小图登记再审，不能凭大图宣称源几何通过。预估适当统一缩放仅为起点：up整格约108px（native可见84px高），right约90px（native可见64px高），down约96px；每格须按实际可见蹄和原脚相定位，不依武器包围盒居中。可参考已完成敌7 `maps/build_native_walk.py`/`build_idle.py`的技术结构及源蹄ROI，但不要复制敌身份、原稿尺寸或通过状态。盟7 maps 没有build脚本、frame_mapping或最终输出。

## 已完成旧范围（保持不动）

男主战斗与已确认0–9样板、敌6/敌8/敌7 battle与static/native maps此前均已根审。敌6 corrected-native up0高拳/up1低手语义纠正已记录；敌8八槽无严格镜像；敌7六绘加两镜像。此前已完成包不因本暂停重做。

## 已返回输出与是否仍有运行调用

停止时没有已知仍等待的ImageGen调用；最后一次已返回v5。只做以下原始复制，未做后处理：
- 最新battle v5：`/Users/gcc/.codex/generated_images/01a14add-95fb-79d0-8e75-7c0fbca039e4/exec-76fb13c1-1a64-40c4-8238-d206a1960590.png` → battle/source/spin-21-22-generated-v5-UNREVIEWED-PAUSED.png。
- map idle v1：`/Users/gcc/.codex/generated_images/01a14add-95fb-79d0-8e75-7c0fbca039e4/exec-14164e97-e146-42d1-afdf-ef4585502e1b.png` → maps/source/idle-generated-v1.png。

## 新负责人可用的明确下一步（须按用户新指示）

1. 不动根审通过0–20/50/52；独立检查21/22原握点并选择最合适旧稿作局部修订基底，保持21透明间隔。
2. 根审21/22后完善盟方25canonical/27source的battle mapping、别名0→26/49、字节/alpha/登记/限制记录；保持原动作时序和效果。
3. Maps已有6+3原稿先规范化与深浅小图对照、逐蹄XY复核；校验6/7整帧镜像后再登记正确source_audit及根审状态。现阶段绝不能写已通过。
4. 交root统一导出/gallery，不接游戏。只有新负责人接获继续指示再进入之后职业队列。

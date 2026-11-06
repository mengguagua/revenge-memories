# 蚀躯 / 断路匪 · 敌方全动作对照

断路匪地图待机已追加颈肩衔接、较小扭肩幅度及下颌线修订：[最新待机制作记录](../brigand-idle-jaw-v3-20261023/README.md)。下文保留首版全动作制作记录。

本轮仅制作敌方11号蚀躯、14号断路匪的美术对照，未接入actual游戏。新稿保持审核候选状态；素材和程序检查不能代替用户的视觉验收。

[打开同一对照页](../index.html#enemy-revenant-brigand-progress) · [蚀躯普通攻击](../index.html?action=professions-class-11-enemy-battle--original_class_11_enemy_normal#motion-player) · [断路匪普通攻击](../index.html?action=professions-class-14-enemy-battle--original_class_14_enemy_normal#motion-player)

## 条目与时序

每个角色3个场景配置、14个页面条目；两角色共6个配置、28个条目。28包含停止姿势和系统反应，不是28套独立新动作。

| 每个角色的页面内容 | 条目数 | 原生节奏 |
|---|---:|---|
| 战棋地图待机循环 | 1 | 0→1→2→1，各14／8／14／8ticks；对照连续展示两轮。 |
| 上、右、下、左步行 | 4 | 各两姿势，每姿势16ticks，连续展示三轮。 |
| 四个方向停止姿势 | 4 | 取对应方向第一姿势，展示32ticks。 |
| 敌方原生普通攻击程序 | 1 | 蚀躯472ticks，接触tick274；断路匪181ticks，接触tick84。 |
| 战斗待机、未命中停留、受击、战败退场 | 4 | 系统通用反馈分别60／27／28／32ticks；未命中不新增闪避姿势。 |

统一采用60.0988fps。两个普通攻击程序分别绑定`original_class_11_enemy_normal`和`original_class_14_enemy_normal`；保留原始位移、翻面、命中时刻、效果与持续时间，不混用友方女魔剑士／乡勇同编号动作，不添加雷剑、法术、额外攻击或新玩法。

蚀躯frame49是冻结原作中的全透明潜伏区间，保留透明，不填入身体。83／98依原登记复用33并左移16个源像素；47由48身体与55个原生爪弧像素合成。以上都有[原生来源记录](../enemy-revenant-brigand-v1-20261023/source/native-baseline.json)，不是缺图回退。

## 六色身体与中心稳定

| 角色 | 身体调色板（RGB） | 肤色与发型边界 |
|---|---|---|
| 蚀躯 | 172638、4f4f7d、bbc1d6、aaa6bc、373e64、a394b1 | 灰紫皮肤、克制蓝紫衣块；秃头形象不凭空增加头发高光。 |
| 断路匪 | 172638、4f4f7d、bbc1d6、dda77d、373e64、a394b1 | 蓝紫衣块、暖肤色、单纯发色；持斧轮廓须在两步腿相中完整。 |

“六色”指新重绘身体。蚀躯47号合成帧因保留原生爪弧而实际有7个可见RGB色；49号为全透明。原始生成图离线保留，输出按实际尺寸与透明轮廓检查后优化，不用文件体积替代清晰度要求。

中心稳定按独立测量的头颈与服装腰胯点校准，排除摆臂、移动双脚，不用全图包围盒质心代替身体中心。仅整体等比缩放与整数平移，不拉扯肢体。四倍输出测量阈值为头部漂移1px、腰胯漂移2.1px、头部尺寸差3px；换算原生尺度为其四分之一，并保留人工取点约1输出px的不确定性。

蚀躯的待机与四向连续帧已通过独立测量：最大头部漂移约0.902输出px，最大腰胯漂移约1.136输出px；对应约0.226／0.284原生px。断路匪待机与四向五组头颈／腰胯安全核心的实际像素保持一致，核心漂移与头部尺寸差为0；同向斧头轮廓与尺寸变化为0，采用同一参考斧刃作刚性平移，保留各相手脚解剖。该方法与蚀躯的独立人工地标测量分别记录，不能混成相同算法。

- [蚀躯113项独立检查](../enemy-revenant-brigand-v1-20261023/revenant/verification.json)
- [蚀躯中心测量记录](../enemy-revenant-brigand-v1-20261023/revenant/map-registration-checks.json)
- [蚀躯深底连续帧](../enemy-revenant-brigand-v1-20261023/revenant/map-continuous-dark.png) · [浅底连续帧](../enemy-revenant-brigand-v1-20261023/revenant/map-continuous-light.png)
- [蚀躯原生足踝相位证据](../enemy-revenant-brigand-v1-20261023/revenant/native-foot-phase-checks.json) · [同slot深底对照](../enemy-revenant-brigand-v1-20261023/revenant/native-foot-phase-dark.png) · [浅底对照](../enemy-revenant-brigand-v1-20261023/revenant/native-foot-phase-light.png)
- [蚀躯素材清单](../enemy-revenant-brigand-v1-20261023/revenant/asset-manifest.json)
- [断路匪362项独立检查与精确原生时序](../enemy-revenant-brigand-v1-20261023/brigand/verification.json)
- [断路匪深底连续帧](../enemy-revenant-brigand-v1-20261023/brigand/map-loop-dark.png) · [浅底连续帧](../enemy-revenant-brigand-v1-20261023/brigand/map-loop-light.png)
- [断路匪完整图像相位交换证明](../enemy-revenant-brigand-v1-20261023/brigand/phase-order-fix-proof.json) · [下行原生相位对照](../enemy-revenant-brigand-v1-20261023/brigand/front-walk-native-phase-order.png)
- [断路匪素材清单](../enemy-revenant-brigand-v1-20261023/brigand/asset-manifest.json)

## 对照页集成与导出

两类mapping齐备后进行局部构建，检查源帧／新帧、场景与近看实际alpha范围、透明区间、效果路径、方向、原生节奏和全部动作齐备性。每个页面条目导出静帧与MP4，普通攻击另导出近看版；深浅检查图单独保存。视频解码帧数、fps和持续时间分别核对。

两类mapping均已发布，局部构建得到6个配置／28个条目，6253项几何、完整性与时序检查通过；最终定向导出完成：28个条目主视频＋2个攻击近看视频，共30个视频，逐一通过解码帧数与时长检查；深浅静帧各28张。两角色前后方向已按原生小腿／脚踝位置逐相核对支撑脚。蚀躯上行0左／1右支撑、下行4右／5左支撑；断路匪上行0左／1右支撑、下行4右／5左支撑。初版对应倒置的地方交换完整新帧与固定slot的像素内容，未重画肢体掩盖相位；相关步行和停止姿势按digest重导，其他导出保留。不能只凭两张图不同判断步态正确。两角色已合并到最新共享gallery数据，6个配置／28个条目均完整可播放。合并只替换两类敌方profiles/actions及必要统计，读取最新共享数据后核对非目标记录保持；最新疗愈师、济世术师等并行内容、全局默认选中和JS默认逻辑保持。主页面只增加本轮小型快捷入口。

[独立集成操作与安全边界](INTEGRATION.md)

本轮集成记录：[6253项局部检查](verification.json) · [定向导出与视频解码](export-report.json) · [精确合并与非目标内容保留](merge-report.json) · [小型快捷入口插入记录](page-insertion.json)。页面已合并供实际浏览器复核，用户视觉验收状态仍单独记录。

## 本轮浏览器抽查

主执行者已在后台浏览器打开最终对照页，抽查蚀躯普通攻击第275帧（原接触tick274）、第420帧透明潜伏区间及修正后的前行首相；抽查断路匪普通攻击第85帧（原接触tick84），并逐帧查看前行第1／17帧，确认与原slot4右腿支撑、slot5左腿支撑一致。已实际检查深浅底轮廓、角色与武器完整性，以及新增快捷入口的文字间距，浏览器控制台无错误。这是本轮代表性位置的浏览器抽查，不表示整站或每一帧均已人工验收；用户视觉确认仍待进行。本轮不修改历史整站检查页脚。

[职业总览目标链接检查](catalog-link-checks.json)：11号保持，14号敌方单元格已补待机／行走／战斗入口，目标href均指向当前ready条目，全局默认保留。

# 首页与五槽记录 · 0.8.13

2026-10-19 开始，2026-10-20 完成；等待用户视觉确认。

新增雪海首页、开始游戏、继续游戏、五个独立记录槽，显示记录时间、章节与地点；宽屏另显示队伍与游玩时长。首页使用西大陆雪路、无字纪念石和东群岛航灯的故事意象，采用现有朴素复古像素方向、深蓝灰和旧铜材质。新动效包括飘雪、航灯明暗、选中光晕与0.32秒渐显。

## 确认入口

- [角色重绘 · 全动作对照](../../../art-review/character-expansion-20261018/index.html#journey-home)：最上方加入本轮确认区，原人物动作目录保留。
- [全部设计稿与实机对照](../../../art-review/character-expansion-20261018/journey-home-20261019/index.html)：10个界面/状态，支持设计、实机与并排查看。
- [12秒动画演示](../../../art-review/character-expansion-20261018/journey-home-20261019/overview.mp4)。
- [0.8.13 macOS测试包](../../dist/RevengeMemories-0.8.13-JourneyHome-20261020-macOS.zip)。

## 记录行为

开始游戏先选槽；占用槽位需要确认覆盖，默认选中「返回」。继续游戏先查看五槽，空槽和损坏记录都显示明确说明。S菜单「保存进度」可以另存到其他槽，保存成功后自动保存跟随该槽。取消和写入失败不改变当前目的槽或已有文件。

本机游戏的独立用户目录沿用 `revenge-memories-actual-campaign`，五槽文件为 `journey-slot-1.json` 至 `journey-slot-5.json`。旧 `revenge-memories-ch1.json` 在槽位1文件尚不存在时显示为「旧记录」；续玩后写入槽位1文件，旧文件保留。旧schema 1/2/3逻辑继续验证、迁移；新增记录时间/游玩时长是可选元数据，不放宽剧情、单位或重试快照校验。

保存先写 `.tmp`、检查写入状态，再原子替换。上一个有效版本保留为 `.bak`。仅列出记录或读取据点不会重写存档时间。损坏记录不载入，也不会部分覆盖当前队伍。对白从记录页继续，敌方回合按已行动标记继续，不重复出手。

## 两轮验证

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 第一轮状态 | 38项通过 | [round1-state.json](round1-state.json) |
| 第一轮后台画面 | 10张，无文字/位图安全区越界 | [round1-visual.json](round1-visual.json) |
| 第二轮真实键鼠路径 | 42项通过 | [round2-flow.json](round2-flow.json) |
| 第二轮后台画面 | 10张，无越界 | [round2-visual.json](round2-visual.json) |
| 冻结设计与第二次渲染 | 10组像素一致 | [fidelity.json](fidelity.json) |
| 伤情与旧档兼容 | 56项通过 | [regression-casualty.json](regression-casualty.json) |
| 第三章状态与存档兼容 | 517项通过 | [regression-chapter3.json](regression-chapter3.json) |
| 显示与旧夹具入口回归 | 191项通过 | [regression-display.json](regression-display.json) |
| 工程外PCK/菜单/五槽读写 | 18项通过 | [package-checks.json](package-checks.json) |

状态、交互、兼容与包内检查合计862项。另验证应用签名与ZIP完整性。旧自动截图/探针的夹具启动入口同步改为显式初始化游戏状态，避免误把新选槽页当作据点；没有重拍历史角色截图。旧显示夹具的首关24格假设改为读取现行地图定义，恢复对真实地图内边缘格的鼠标选择检查。

全部测试使用工程缓存或/private/tmp中的隔离记录，没有写入真实用户存档。敌方回合使用已行动敌人的合法检查点，验证回合继续和无重复结算；这不是自然战斗胜利证明。本轮没有重跑全篇自然通关，也没有交付移动端安装包或开展手机真机验收。

Godot图形检查通过项目已有 `background_guard.m` 在进程启动前禁止窗口显示、置前和获取焦点，然后在SubViewport中渲染。宽屏逻辑画布426×240、紧凑256×240；按位图实际边框收紧内容区域，记录行34像素、两行8像素文字均距材质边缘至少8像素。背景按比例覆盖，边框固定8像素四角、中心平铺，未非等比拉伸整图。

确认页已在内置浏览器抽查首页、五槽并排对照和上级入口。预览服务只读允许指定设计目录、本轮报告和单个测试包，禁止目录列表与工程源码/存档路径。

## 美术与源文件

内置 `image_gen` 生成两张原图，再按用途制作运行副本。完整最终提示词集：[prompts.json](../../../art-review/character-expansion-20261018/journey-home-20261019/prompts.json)。原图：[雪海背景](../../source/journey-home-20261019/coast-source.png)、[面板材质](../../source/journey-home-20261019/panel-source.png)，保存在带 `.gdignore` 隔离的 source/ 下，不进入游戏包。

运行文件：[snow-coast.png](../../assets/journey-home/snow-coast.png)，426×240，172730字节；[journal-panel.png](../../assets/journey-home/journal-panel.png)，94×96，12048字节。前者为专用首页场景，按等比覆盖适应画幅；后者为可复用九宫格材质。审阅副本采用无损WebP，逐图像素与字节记录见 [assets.json](../../../art-review/character-expansion-20261018/journey-home-20261019/assets.json)。首页审阅副本204572字节，略超200KB参考值，保留1704×960完整中文字形和像素细节；运行图低于参考值。

设计与实现使用同一冻结原生像素布局渲染器，第二轮独立进程在相同声明内容、相同动画时刻下比较RGBA像素；10组一致不等于所有动态游戏状态均被截图穷举。实际记录读取、按钮、覆盖和续接另由真实输入检查覆盖。

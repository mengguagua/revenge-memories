# 敌方佣兵 class 8 美术样板

已完成原程序所需 10 张 canonical 战斗帧（含 8 个人体重绘）、11 个引用槽，以及地图 8 张独立原生战术行走姿势和 3 张独立固定待机相。造型为暖灰短发、苔绿斜扣短夹袄、皮胸带、少量旧铁护肩、短层叠下摆、炭灰护腿、绑腿暗靴和窄直刃钢剑。

验收入口：

- `battle/reviews/all-ten-original-dark-light.png`：十张战斗姿势原图／新深底／新浅底。
- `battle/reviews/slash-connection-tip-comparison.png`：收势钢剑端点局部修订及原挥剑弧关系。
- `maps/previews/tactical-native-original-dark-light.png`：正确八槽原图／新深底／新浅底。
- `maps/previews/tactical-native-actual-size-dark-light.png`：128×96 实际尺寸八槽。
- `maps/previews/tactical-native-walk-dark.gif` 与 light：四向两步相循环。
- `maps/previews/all-map-original-dark-light.png`：历史总对照，只有其中固定待机三相继续有效，旧行走已替换。

战斗输出 320×256。原帧 0 整帧左移 64 输出像素与 8 逐像素一致，15 是 8 的别名；新 8／15 因此复用新 0 的整帧位移。原 7 左移 4 输出像素的全部 1888 个占据像素均与 6 相同，6 的额外挥剑弧独立提取并原样复用。证明保存在 `battle/source/pixel-reuse-proof.json`。原弧与剑尖本有微小空隙，没有将原效果拉伸接实。敌方雷剑沿已核准 program 26／effect 2／idle 8，不烘焙雷电，也不新增攻击能力。

地图行走现按正确 bank011:L0BB5B1 战术入口、class/side 表、CHR26 CPU 八槽输出重绘，128×96。顺序 up 0/1、right 2/3、down 4/5、left 6/7，每相 16 tick；没有任意两帧严格镜像，八张均独立 ImageGen 绘制。CPU 已施加方向翻转，播放不再额外镜像。旧村镇 OAM 与固定 CHR26 拼出的两相并非本次真实战术源，原稿与旧 mapping 已保留作历史。固定待机三相和战斗文件保持已审版本。

0/1 头侧两浅点分列头两边，上半部不变，按本类证据保留耳/脸边；左侧连续衣袖遮挡不误画成举拳。2/3 源眼鼻与下颌更正面，已局部改正初稿随 idle 画成左侧脸的问题；6/7 保留向左突出鼻/下脸。竖剑在 up 的画面右侧，在其余三向的画面左侧；没有为了方向字段把剑翻到另一侧。

2 的收步右脚支撑、3 的非对称宽步左脚支撑经 ImageGen 局部修订；其余方向也按各自源脚相独立绘制。整帧登记使用原可见靴 ROI，衣摆不当隐藏关节。2/3 头身横向还约有 5–6 输出像素的绘制差异，正向剑尖约高于源头顶 4 输出像素；明确保留残差，不以拉伸或任意移体掩盖。八槽 alpha>4 可见轮廓无画布裁切，原 alpha 保留；画布外最多 alpha1 微弱噪声随登记截去。无代码抠背景或换肢体。

战斗单帧约 13–18 KB，新行走单帧 5,477–6,388 字节，固定待机约 6–7 KB，均无损压缩。`battle/frame_mapping.json`、`maps/frame_mapping.json` 和各 `qa-summary.json` 包含源帧、别名、时序、路径、尺寸、字节、哈希、提示词及靴锚登记；原始生成图和修订历史完整保留。只使用 ImageGen 绘制、技术裁切、等比缩放、整帧平移、原程序镜像和原效果复用；未修改游戏代码、冻结源图或接入运行资源。

八张真实四向姿势已通过主代理深浅总板复核并冻结；残差如实保留，不声称全部关节精确对齐。

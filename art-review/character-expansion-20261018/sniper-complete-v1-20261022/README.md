# 狙击手 · 双方待机、行走与战斗

为双方狙击手重新设计进阶形象并补齐全部原作对照动作。较弓箭手增加整片米白胸肩防护、护臂与护胫，以及更有分量的长弓和箭袋；保持敏捷的弓手轮廓、可见肤色与眼睛。头发为纯色深蓝，服饰哑光，不添加高光碎点。

盟军严格沿用现有弓箭手四色 `172638 / 3976b5 / e4e1c8 / dda77d`，只增加一种柔和棕色 `8c6b45` 用于握把、箭袋和皮带。敌方采用蓝紫衣甲 `4f4f7d / bbc1d6`，保留肤色与自然木皮色。地图和战斗身体均为同一套五色材料。

- [盟军待机](../index.html?action=professions-class-13-ally-maps-tactical-idle--idle-cycle#motion-player)
- [盟军四向行走](../index.html?action=professions-class-13-ally-maps-tactical-walk--walk-up#motion-player)
- [盟军弓箭攻击](../index.html?action=professions-class-13-ally-battle--class_13_ally_bow#motion-player)
- [盟军圣弓攻击](../index.html?action=professions-class-13-ally-battle--class_13_ally_silver_bow#motion-player)
- [敌方待机](../index.html?action=professions-class-13-enemy-maps-tactical-idle--idle-cycle#motion-player)
- [敌方四向行走](../index.html?action=professions-class-13-enemy-maps-tactical-walk--walk-up#motion-player)
- [敌方弓箭攻击](../index.html?action=professions-class-13-enemy-battle--class_13_enemy_bow#motion-player)
- [盟军地图 · 浅底](ally-maps-light.png) / [深底](ally-maps-dark.png)
- [敌方地图 · 浅底](enemy-maps-light.png) / [深底](enemy-maps-dark.png)
- [盟军战斗 · 浅底](ally-battle-light.png) / [深底](ally-battle-dark.png)
- [敌方战斗 · 浅底](enemy-battle-light.png) / [深底](enemy-battle-dark.png)
- [原作时序、资源与稳定性检查](verification.json)
- [全部播放导出与解码检查](export-report.json)
- [运行图片尺寸、字节数、哈希与整姿态定位](asset-manifest.json)
- [绘图提示与参考用途](source/generation-prompts.json)
- [方向／支撑腿修补提示](source/repair-prompts.json)
- [放低弓的持有侧修补提示](source/rest-side-prompt.json)
- [敌方释放后弓体透视修补提示](source/recoil-prompt.json)
- [职业、武器程序与触发对应](source/action-effect-mapping.json)

地图使用原作职业 13 的原生 CPU/OAM 方向槽：上 0/1、右 2/3、下 4/5、左 6/7。每相 16 帧，32 帧一循环；待机按 0→1→2→1、14/8/14/8 帧循环。头部与腰胯固定，四肢与持弓姿势保留自己的运动；上下两相按原作末端落脚像素核对左右支撑脚，不凭第一帧的主观方向排序。

双方战斗分别使用自身程序，保留不同准备流程。盟军先放低弓在画面右侧，迈开站姿，再转到前方举弓、搭箭、拉弦、单次释放和收势。敌方先抬弓，再向前转弓，按原作水平投影蓄力后释放，释放后转回较短的侧向弧形投影。完整保留普通弓、圣弓、近／远距离和重甲目标变体的源帧、停留、箭矢位置、翻转、效果和结算。没有增加连射或额外攻击次数。

原作近距普通弓：盟军程序 42，共 267 帧，结算 tick165；盟军圣弓程序 43，共 235 帧，结算 tick166；敌方程序 33，共 292 帧，结算 tick198。其余距离／目标变体分别保留各自延时。浏览器帧数显示从 1 开始，结算界面数字比 tick 多 1。

本轮新增 6 个场景条目、44 个动作：双方地图各 9 项，盟军战斗 16 项，敌方战斗 10 项。已存在的 687 个动作内容摘要保持。原生箭矢、圣弓效果沿用原素材与原轨迹；仅新绘身体、弓与随身装备。地图单帧 96×96／128×96，战斗单帧 320×256，运行图采用无损索引 PNG，源图离线保留。

内置 ImageGen 完成角色和完整姿态绘制；本地脚本负责分离完整人物、材料归一化、整体等比缩放、整数定位和固定中心。初稿中左向第二相、下向支撑腿和盟军放低弓的持有侧未通过检查，已单独重绘修正。未把旧弓箭手换色冒充新职业，也未用整图镜像代替独立方向槽。

深浅底姿态板与同源时间线的原作／新稿同步截图用于目视检查，含脸部方向、持弓手、弓尖、弦、护具连接和图中文字间距。自动检查覆盖五色材料、透明轮廓、固定中心、原作支撑脚、全部 18 条攻击程序、结算与外部效果、44 项完整播放和视频帧数／时长。浏览器本地页面渲染沿用此前环境访问限制，未通过替代服务器或浏览器绕行。

本轮仅更新美术对照，未接入运行游戏、测试应用或存档。素材齐备与检查通过不等于用户已确认，新形象和姿态仍待视觉验收。

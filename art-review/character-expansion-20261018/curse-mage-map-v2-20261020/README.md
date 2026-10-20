# 咒法师 · 三姿势待机与四向行走

仅更新「角色重绘 · 全动作对照」，未接入游戏。

- 待机：画面左臂抬起／右臂放下 → 双臂放下 → 画面左臂放下／右臂抬起 → 双臂放下。整段袖袍绕肩位抬放，两侧由同一图层镜像；兜帽、头部和中央衣襟固定。保留暗脸与双眼明暗循环。
- 向上：固定头颈、肩部与中轴，左右袍摆交替摆动。
- 向下：完整复用新待机三姿势，像素不变，仅登记到行走画框；动作节奏同为14／8／14／8帧。
- 左右：保留原下摆与侧袖步态，固定头部和躯干；左右互为镜像，面部隐入兜帽。
- 四向与待机共用六色低饱和蓝紫调色板和冷色衣饰。

## 查看

[待机](../index.html?action=professions-class-15-enemy-maps-tactical-idle--idle-cycle#motion-player) · [向上](../index.html?action=professions-class-15-enemy-maps-tactical-walk--walk-up#motion-player) · [向下](../index.html?action=professions-class-15-enemy-maps-tactical-walk--walk-down#motion-player) · [向右](../index.html?action=professions-class-15-enemy-maps-tactical-walk--walk-right#motion-player) · [向左](../index.html?action=professions-class-15-enemy-maps-tactical-walk--walk-left#motion-player)

[连续演示](overview.mp4) · [三姿势深浅底](idle-poses.png) · [四向姿势](walk-poses.png) · [制作参数](asset-manifest.json) · [针对性检查](verification.json)

## 参考与验证范围

原作向下行走只有两帧，本轮按用户要求改为复用完整待机。因此仅在本轮对照参考图集末尾追加三张真实原作待机帧，并明确标注“原作待机 · 向下复用参考”；原行走参考0—7逐像素保留，原始源文件没有修改。

向下展示两个44帧循环，与待机一致；其余方向仍为16帧／姿势、三个循环。对照工具增加了可选的分方向节奏设置，未设置的其他角色保持原逻辑。

沿用现有像素素材分层修改，没有调用图片生成工具，也不在对话回传图片。程序检查固定部位、左右对称、面部遮蔽、调色板、完整待机复用、姿势连续性、时间线和影响范围；美术效果等待用户在对照页验收。

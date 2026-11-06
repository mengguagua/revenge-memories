# 引光剑使 · 后跳落地身前持剑

2026-10-24，依据用户本轮确认：后跳落地后剑应一直保持在身前。之前第30／31、11／23姿势把剑放到了身后，接回待机时又切到身前，形成方向抽动。

本轮只替换这4个普通攻击帧槽。持剑手保持身前低位，剑尖持续指向左下；后侧手臂自然放松，不再握持第二把剑。沿用第29姿势已经绘好的完整握剑手、剑格与剑刃作为同一图层，注册到各姿势前侧手腕，避免剑的长度、厚度、角度或轮廓在连续帧变化。各姿势腿部仍保留自身落地、缓冲与放松站立的区别。

四个完整姿势使用内置 imagegen 编辑，[编辑目标](source/edit-target.png)、[身前持剑参考](source/front-carry-reference.png)、[提示词](source/edit-prompt.txt)、[生成源图](source/edit-master.png)均保留。按真实头颅统一30像素尺度，并精确保留各姿势原有落脚高度；透明图按原调色板登记。剑刃图层复用既有像素原画，未使用代码生成新的几何剑形。

原312帧、60.0988fps、所有位移和第129帧唯一结算保持。角色艾琳的普通攻击仍沿用现有动作与结算对应，不新增攻击、连击或效果。已确认的空中稳定相位、完整蹲地衣服与双腿、地图动作和全部法术保留。本轮不接入游戏运行场景或设备。

- [普通攻击 · 当前动画](../index.html?action=eileen-promoted-battle--original_class_11_normal#motion-player)
- [后跳至待机连续细节](recovery-detail-light.png)、[原作并列连续帧](recovery-continuous-light.png)、[导出视频抽帧](decoded-video-recovery.png)
- [身前持剑 · 浅底](front-carry-sequence-light.png)、[深底](front-carry-sequence-dark.png)
- [当前战斗全姿势](battle-current-light.png)、[深色全姿势](battle-current-dark.png)
- [素材与注册](asset-manifest.json)、[尺寸和体积](image-inventory.json)、[针对性检查](verification.json)

针对性检查覆盖：同一完整剑层、身前方向、无身后残留长剑、握剑手与人物轮廓连接、原体型及落脚高度、原时序与结算、其余动作不变，正常／近景视频帧数与时长，以及页面链接和导出文字间距。通过离线画面与视频抽帧检查，不声明浏览器界面已验收；用户视觉验收待定。

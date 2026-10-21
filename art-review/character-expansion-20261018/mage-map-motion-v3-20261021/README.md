# 术法师 · 四向长袍行走

沿用已确认待机的红棕长袍、金色饰边、自然肤色与七色调色板。四向均为闭袖长袍、双臂藏袍，只让下半袍子摆动；原待机稿保持。

- 向上：原向上首帧的背面尖帽与头部统一注册，所有相位完全复用同一上身；下半袍摆在固定中轴两侧小幅循环，不露手、不抬腿，不整体晃动。
- 向下：逐像素复用已确认待机的左右袍摆，平移至行走画布的相同头顶与脚底位置。
- 向右：保留侧向头部，重绘同款闭袖长袍；头部、肩颈和躯干在两帧间不变，仅下摆移动。
- 向左：按身体中心像素x=64镜像向右，避免按画布边缘镜像引入半像素偏移。
- 四向统一中心线x=64、头顶y=32、脚底y=96（输出像素），下摆从y=77开始、最大摆动2像素；中央x=62～66衣缝固定。逻辑32×24、输出128×96保持。
- 保留原两姿势、每帧16个tick、三轮共96帧的时间轴；四个方向的停止姿势也同步。
- 只更新全动作对照，美术未接入游戏或测试包。已确认待机、战斗法术和其它角色保持。

## 验收入口

- [向上行走](../index.html?action=professions-class-15-ally-maps-tactical-walk--walk-up#motion-player)
- [向右行走](../index.html?action=professions-class-15-ally-maps-tactical-walk--walk-right#motion-player)
- [向下行走](../index.html?action=professions-class-15-ally-maps-tactical-walk--walk-down#motion-player)
- [向左行走](../index.html?action=professions-class-15-ally-maps-tactical-walk--walk-left#motion-player)
- [已确认待机](../index.html?action=professions-class-15-ally-maps-tactical-idle--idle-cycle#motion-player)
- [四向姿势 · 深底](walk-poses-dark.png)
- [四向姿势 · 浅底](walk-poses-light.png)
- [向上原作／新版](up-frame-71.png)

## 制作与检查

原朝向头部统一注册，精确收敛至已确认调色板；重绘同款长袍并仅弯曲下摆。未调用自动附图流程。

- [素材用途、尺寸、体积与定位](asset-manifest.json)
- [针对性像素与时间轴检查](verification.json)
- [播放器检查](player-check.json)
- [四向视频导出](export-report.json)

离线检查固定上身、中轴、脚底、透明轮廓、少色一致、逐像素向下复用与左右镜像、标题安全区。用户在对照页目测验收，聊天不展示图片。

# 壁垒卫士 · 左右行走摆臂带盾

双方壁垒卫士向左、向右行走时，盾牌与持盾手臂作为一个连接完整的动作层，围绕固定肩部共同前后摆动。盾牌不再停在原处。头部、躯干、持枪手臂和长枪共用一张固定上身底图，腿部仍按原作两相步态循环。

- [盟军向右](../index.html?action=professions-class-22-ally-maps-tactical-walk--walk-right#motion-player) · [向左](../index.html?action=professions-class-22-ally-maps-tactical-walk--walk-left#motion-player)
- [敌方向右](../index.html?action=professions-class-22-enemy-maps-tactical-walk--walk-right#motion-player) · [向左](../index.html?action=professions-class-22-enemy-maps-tactical-walk--walk-left#motion-player)
- [双方左右姿势 · 深底](poses-dark.png) · [浅底](poses-light.png)

内置 ImageGen 按原左右行走参考制作了四个专用动作层：固定上身与持枪手、两相腰腿步态、连接完整的持盾手臂与盾牌。[生成源图](source/side-walk-rig-master-v1.png)和[提示词](source/imagegen-prompt.json)保留。

持盾手臂与盾牌共用同一素材及同一变换，肩部连接点固定在输出画布48、48。两相分别向后、向前小幅转动，盾牌跟随前臂，盾面保持可见。固定肩甲覆盖连接处，避免接缝或盾牌脱手。左右整幅镜像，蓝白／蓝紫14色材质保持。

行走仍为每相16帧、32帧周期，对照播放三个周期共96帧。只替换图槽2、3、6、7，对应左右行走及左右停止姿势。已确认的正面盾牌固定身体待机、向上和向下行走、战斗动作保持。仅更新美术对照，未接入游戏。

- [素材尺寸、大小、定位及手臂与盾牌整体记录](asset-manifest.json)
- [针对性检查结果](verification.json)
- [播放导出及视频解码记录](export-report.json)

使用离线原作／新版对照渲染与深浅底姿势板检查，未启动Godot可见窗口，未绕过浏览器本地文件访问限制。

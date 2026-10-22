# 壁垒卫士 · 普通攻击长枪后柄连续

纠正双方普通攻击中长枪后柄时有时无的问题。前段各姿势不再交替使用短尾和长柄；准备、出枪、收势均保留完整后柄及可见钝尾帽，允许配合原姿势轻微摆动。

- [盟军普通攻击](../index.html?action=professions-class-22-ally-battle--original_class_22_normal#motion-player)
- [敌方普通攻击](../index.html?action=professions-class-22-enemy-battle--original_class_22_enemy_normal#motion-player)
- [盟军全姿势 · 深底](ally-poses-dark.png) · [浅底](ally-poses-light.png)
- [敌方全姿势 · 深底](enemy-poses-dark.png) · [浅底](enemy-poses-light.png)

内置 ImageGen 参照已有后柄单独绘制一张连续木杆与圆钝钢制尾帽，[生成源图](source/rear-shaft-master-v1.png)及[提示词](source/imagegen-prompt.json)保留。生产后柄为110×7像素，普通攻击各相共用同一张素材，仅旋转和平移，不逐相缩放、切短或隐藏。沿前段枪杆的原有方向登记，清除旧短尾及旧长柄的残余轮廓。

接近、回位等姿势中后柄绘制在原人物后方，露出肩后的尾帽；出枪时长枪位于胸前，手套覆盖握持处。原人物图、面部、四肢及位置保留，变化集中于枪柄及其遮挡关系。盟军保持木色与钢色，敌方沿用蓝紫配色，整体14色材质不变。

普通攻击仍为535帧，界面显示第246帧结算（原始0起算索引245），原动作顺序、位移、接触次数与节奏保持。普通攻击使用的战斗待机身体及通用反应同步后柄外观；投枪准备、释放及飞行效果不变。已确认的地图待机、四向行走保持。

- [每相后柄、可见尾帽、素材尺寸与大小记录](asset-manifest.json)
- [针对性检查结果](verification.json)
- [原速与近看播放导出](export-report.json)

仅更新美术对照，待本轮验收，未接入游戏或重新打包。检查使用离线对照渲染、深浅底姿势板及视频解码；未启动Godot可见窗口，未绕过浏览器本地文件访问限制。

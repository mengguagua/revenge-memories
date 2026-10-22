# 剑豪左右行走 · 躯干转向修订

本轮仅更新双方剑豪战斗地图的左右行走及对应停止姿势。向右时，近侧肩臂展开、远侧肩线收进，胸口、领口、腰带和持剑臂一起转向右方；向左采用独立绘制的反向透视，保留原作持剑与披风的位置关系。两相分别表现展步和交叉换步，保留另一只脚的轮廓。

两相以上身和腰带为固定基准，不随腿部换步整体上下或左右移动。沿用已确认的六色材料：盟军蓝、米白、深蓝与少量柔和金色，敌方蓝紫，保留肤色、眼睛与纯色深发。这里的转身为重新绘制的肩胸、腰胯和手臂透视，不是将旧正面身体做二维倾斜。

- [对照页 · 盟军向右](../index.html?action=professions-class-10-ally-maps-tactical-walk--walk-right#motion-player)
- [对照页 · 盟军向左](../index.html?action=professions-class-10-ally-maps-tactical-walk--walk-left#motion-player)
- [对照页 · 敌方向右](../index.html?action=professions-class-10-enemy-maps-tactical-walk--walk-right#motion-player)
- [对照页 · 敌方向左](../index.html?action=professions-class-10-enemy-maps-tactical-walk--walk-left#motion-player)
- [双方两相 · 浅底检查](side-turn-light.png)
- [双方两相 · 深底检查](side-turn-dark.png)
- [盟军全地图姿态](ally-maps-light.png)
- [敌方全地图姿态](enemy-maps-light.png)
- [验证与视频记录](verification.json)
- [运行素材尺寸、字节数与哈希](asset-manifest.json)
- [绘图提示与参考用途](source/generation-prompts.json)
- [整姿态缩放与腰带定位记录](source/registration.json)

使用内置 ImageGen 绘制新姿态。第一批参考了旧服饰整图，仍过于正面且左行朝向错误，已弃用，原图离线保存在 `source/rejected-*-v1.png`。第二批以原作方向姿势作为动作参考重新绘制，保留完整源图，再进行整姿态等比缩放、六色材料归一化和整数定位。两相使用同一新上身保持帧，腰部以下保留各自换步；不扭曲四肢，也不镜像整个右向姿态来代替左向。

原作方向槽保持为右 2/3、左 6/7，每相 16 个原作时钟帧、32 帧循环，60.0988 fps；播放器仍展示三个循环。源帧、偏移、翻转、动作时长和结算数据保持。双方左右停止同步使用各方向第一姿势。其他 679 个动作的内容摘要不变；本轮待机、上下行走和战斗动画不改。

已对深浅底姿态板和原作／新稿离线播放截图进行目视检查；检查完整剑刃、持剑臂连接、肩线远近、两相脚步、纯色头发、肤色与眼睛，以及图中文字与脚部之间的留白。自动检查包括稳定上身、腿部两相差异、六色材料、透明轮廓连通、无画布裁切、阵营材料替换、8 条相关动作的视频帧数／时长和资源路径。生成源图保留离线，运行单帧为 128×96 索引 PNG，逐图体积见素材记录。

浏览器本地页面因之前的环境访问限制未执行页面渲染，使用同源时间线的离线合成截图检查。本轮仅更新美术对照，不接入游戏运行代码或测试包。视觉验收仍待用户确认。

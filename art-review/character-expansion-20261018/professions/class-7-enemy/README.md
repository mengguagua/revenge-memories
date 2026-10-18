# 敌方黄金骑士（class 7）隔离美术

战斗部分已完成，可由 `battle/frame_mapping.json` 读取全部 27 个引用槽：26 个原作独立外观，25 组 ImageGen 人马重绘，另以原像素证据复用待机。输出为 448×320 RGBA；没有修改 `actual`、冻结输入或接入游戏。

造型为金铜分片铠甲、深紫短马衣、紧凑栗色甲马、长窄盾和单根木杆钢尖枪。原作始终是骑乘，不改成徒步重甲。14–22 的马向右、骑手回身及侧盾遮挡分别按源动作处理，不能用整图镜像0代替。分片马甲、骑手靴和马腿按可见连续轮廓区分，不推断隐藏关节。

战斗映射保留现有普通攻击和六个投枪变体；50是横举投枪准备，52为空手释放，飞枪仍由原程序单独播放。16/20是原转枪中的分段残形，源四个小区间在新图合为三组材质轮廓；它们不是三支投枪、多次攻击或新增能力。21保留与手之间有间隔的短竖残形。部分枪端位置较原图仍有约20–28输出像素差异，已由主代理审阅并记录，不为对齐枪尖移动整个人马。

原0左移64输出像素后，与26完全同轮廓，骑手和马体RGBA一致，只有枪杆上的2个原生像素（4倍后32像素）调色不同。新设计使用一致木杆材质复用该人体；49与26原图逐像素完全一致。证明见 `battle/source/pixel-reuse-proof.json`，不把0与26声称为完整RGBA相同。

所有生成原图、失败稿、提示词和选择记录保留在各自 `source/`。技术处理仅矩形裁切、等比缩放、整帧平移、已证实别名复用、不可见alpha0 RGB归零与oxipng无损压缩。没有程序绘制角色、按颜色换装、非等比变形或手臂拼接。

登记使用真实可见蹄ROI：横向按alpha≥128蹄底，纵向按完整可见alpha>4轮廓。ImageGen在远离轮廓处可带alpha1编码噪声，不能把它当成蹄底。画布内部原alpha不改；原画框外最多裁掉alpha1–4（低于2%不透明度）的噪声，alpha>4可见轮廓裁切数为0。每帧保存了具体噪声数量和最大alpha。之前试用“所有非零alpha最低点”的登记已撤回；它会误使部分收腿帧上浮，最终映射不再使用。

战斗PNG无损压缩后约42–59KB。部分超过50KB软参考，原因是同时保留骑手、马体、完整长枪、甲片层次与透明边缘；不为了数字对精绘进行有损量化。精确尺寸、字节数和哈希在 `battle/qa-summary.json` 与映射中。

静态地图待机为3个独立相、6槽别名、96×96 RGBA，保留抬前蹄／双支撑／抬后蹄与固定朝向。原黑底横条包含轮廓/阴影，不当作四只脚；左下细斜段属于同一根枪。入口 `maps/previews/idle-original-dark-light.png`，实际尺寸见 `maps/previews/idle-actual-size-dark-light.png`。

战术行走已按已由CPU与ROM索引交叉验证的 `corrected-tactical-walk` CHR19来源完成八槽，并获主代理逐姿深浅底复核通过；整包冻结供隔离导出。入口 `maps/previews/tactical-native-original-dark-light.png`。顺序为up0/1、right2/3、down4/5、left6/7。前六槽分别ImageGen绘制，6/7按原RGBA全画布镜像证明派生自2/3；`direction_mirror_x`为空，不再额外镜像。输出 `maps/tactical-native-frames/` 与 `maps/frames/tactical-native-walk.png`，128×96，约7.6–8.6KB/帧。真实actor anchor为[16,24]，它与人工可见蹄点登记分开记录。背面右杆为上钝帽/下小刃，侧面只露木尾，正面左杆下端钢刃；杆遮挡区域不人为画穿身体。

旧 `original-walk-7.png` 是CHR26与村庄OAM的历史混合提取，不是实际战术移动来源；这里只保留参考，未据此生成新walk。旧映射保存在 `maps/source/previous-map-frame_mapping.json`。不拿static idle套用新步相，校正源的完整验证路径记录在 `tactical-walk.source_audit`。

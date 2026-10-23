# 天马骑士 · 盟军全动作 v1

本轮依用户澄清，仅完成盟军天马。原作同编号敌方为石像鬼，敌方天马暂不制作，保留原始敌方资料。

## 形象与配色

沿用已与原作对位的天马、骑手、长枪和羽翼姿态，使用弓箭手的深海军蓝 `#172638`、蓝 `#3976b5`、暖白 `#e4e1c8`、肤色 `#dda77d`，仅新增一种柔和红 `#b96369`。头发统一红色，保留深色外轮廓；衣甲和羽翼采用哑光色块，减少灰色和高光碎点，保留面部、眼睛与必要的阴影。

本轮通过 ImageGen 制作形象／材质参考，并复用现有 ImageGen 原作对位稿的完整轮廓。新材质参考的第一个背面姿势被生成器转成正脸，故仅作材质参考，未用于动画几何；生产姿态保持原来背面朝向，不用错误的新姿态替代。

## 动作与中心

- 待机保留原作 `0 → 1 → 2 → 1`，每相位 `14／8／14／8` 原生时钟帧。
- 移动保留各方向两个原姿态，每相位16帧，维持扑翼、收腿的对应；向右为原作已验证的向左整帧镜像。
- 地图角色按同一头部定位点进行整个人物的整数平移配准，保留四肢、羽翼、马身和武器的相对姿势；原地面投影独立保留，不随人物配准一起移动。没有切断腿或把翅膀贴成服饰。
- 战斗保持12个必要图块槽位，包含10个独立姿态及待机别名。普通攻击保留连续扑翼、接近、前刺、收势和回位；投枪保留抬枪和释放。战斗轮廓透明度与既有原作对位稿相同，没有拉伸或重新拼接身体部位。
- 7条战斗程序的帧顺序、各帧时长、位移、效果轨迹及单次结算相同。投枪效果仅改为与手持武器一致的蓝／暖白，原像素透明轮廓和锚点保持。

## 验收入口

[返回全动作对照](../index.html) · [待机](../index.html?action=professions-class-3-ally-maps-tactical-idle--idle-cycle#motion-player) · [普通攻击](../index.html?action=professions-class-3-ally-battle--original_class_3_normal#motion-player) · [投枪](../index.html?action=professions-class-3-ally-battle--class_3_ally_javelin#motion-player)

[地图全姿态（浅底）](ally-maps-light.png) · [地图全姿态（深底）](ally-maps-dark.png) · [战斗全姿态（浅底）](ally-battle-light.png) · [战斗全姿态（深底）](ally-battle-dark.png)

20项盟军动作完成资源、调色板、透明轮廓、固定定位点、原生帧序／位移／结算与视频解码帧数检查。其余755项动作内容指纹不变。画面通过与页面相同资源和坐标的离线渲染器检查，并核对文字安全区；浏览器UI检查受访问限制未执行。仅更新美术对照，未接入游戏运行工程；用户视觉验收待确认。

详细记录：[验证结果](verification.json) · [原作参考](native-reference-audit.json) · [定位／材质记录](registration.json) · [动作与结算](action-effect-mapping.json) · [视频导出](export-report.json)

生成原图与参考保存在 `source/`，不作为运行素材。独立候选角色图保持无损索引色，均低于50KB参考值。

| 素材 | 像素尺寸 | 字节 |
| --- | --- | ---: |
| ally/tactical-walk/frame-000.png | 128 × 96 | 1,479 |
| ally/tactical-walk/frame-001.png | 128 × 96 | 1,532 |
| ally/tactical-walk/frame-002.png | 128 × 96 | 1,790 |
| ally/tactical-walk/frame-003.png | 128 × 96 | 1,717 |
| ally/tactical-walk/frame-004.png | 128 × 96 | 1,646 |
| ally/tactical-walk/frame-005.png | 128 × 96 | 1,661 |
| ally/tactical-walk/frame-006.png | 128 × 96 | 1,786 |
| ally/tactical-walk/frame-007.png | 128 × 96 | 1,715 |
| ally/tactical-idle/frame-000.png | 96 × 96 | 1,648 |
| ally/tactical-idle/frame-001.png | 96 × 96 | 1,556 |
| ally/tactical-idle/frame-002.png | 96 × 96 | 1,569 |
| ally/tactical-idle/frame-003.png | 96 × 96 | 1,556 |
| ally/tactical-idle/frame-004.png | 96 × 96 | 1,648 |
| ally/tactical-idle/frame-005.png | 96 × 96 | 1,556 |
| ally/battle/frame-000.png | 320 × 384 | 4,284 |
| ally/battle/frame-003.png | 320 × 384 | 3,491 |
| ally/battle/frame-007.png | 320 × 384 | 4,344 |
| ally/battle/frame-001.png | 320 × 384 | 4,110 |
| ally/battle/frame-002.png | 320 × 384 | 3,845 |
| ally/battle/frame-004.png | 320 × 384 | 3,289 |
| ally/battle/frame-005.png | 320 × 384 | 4,211 |
| ally/battle/frame-006.png | 320 × 384 | 4,274 |
| ally/battle/frame-034.png | 320 × 384 | 4,354 |
| ally/battle/frame-035.png | 320 × 384 | 4,340 |
| ally/battle/frame-016.png | 320 × 384 | 4,284 |
| ally/battle/frame-033.png | 320 × 384 | 4,284 |
| ally/flying-javelin.png | 64 × 16 | 890 |

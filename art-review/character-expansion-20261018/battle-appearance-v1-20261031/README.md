# 天马、骑兵、弓箭手 · 攻击外观修订

本轮于2026-10-31开始，2026-11-01完成。只更新「角色重绘 · 全动作对照」，等待用户视觉验收。

- 天马骑士：12个战斗源姿势统一红发头冠、鬓发与马尾厚度。共用固定尺寸头部层，在原脸部位置平移定位，避免换姿势时发量忽大忽小。飞马、翅膀、身体和投枪动作保留。
- 骑兵：12个战斗源姿势统一白色战马、鬃毛与马尾；身体提高中蓝与米白比例，蓝色基准取盟军剑豪的 `#3976b5`，米白基准 `#e4e1c8`。保留全部原像素位置、透明度、长枪、肤色和皮革细节。
- 弓箭手：3个战斗源姿势重制为狙击手的中蓝、米白、深蓝、肤色与少量棕色五种材质；原蓬松棕发改为贴头深蓝板寸。覆盖直立空弓、满弓搭箭与松弦空弓。

## 查看

[返回全动作对照](../index.html)

[天马普通攻击](../index.html?action=professions-class-3-ally-battle--original_class_3_normal#motion-player) · [骑兵普通攻击](../index.html?action=professions-class-1-ally-battle--original_class_1_normal#motion-player) · [弓箭手攻击](../index.html?action=professions-class-12-ally-battle--class_12_ally_bow#motion-player)

[天马全部姿势](review/class-3-light.png) · [骑兵全部姿势](review/class-1-light.png) · [弓箭手全部姿势](review/class-12-light.png) · [天马头部逐姿势放大检查](review/pegasus-heads-light.png)

## 制作来源与检查

使用内置 imagegen 进行局部重绘，随后完成原生像素定位、五材质归一与图层复用。生成源图保存在 `source/`，不作为运行素材；[提示词与输入记录](source/prompt-set.json)、[定位记录](registration.json)、[逐图用途／尺寸／字节记录](image-inventory.json)均保留。

- 27个源姿势，38条相关动作；1530条无关动作内容摘要保持一致。
- 原攻击帧序、位移、特效、时长与命中结算点一致，未增加攻击或改变规则。
- 天马12个姿势的红发形状与像素数相同，每组364个红发像素，按原脸部基准平移。
- 骑兵全部原始透明度与像素轮廓保留；弓箭手使用五种材质和二值透明度，脚底保持原定位线。
- 1880项实际透明轮廓与完整场景／近景画幅检查通过；核对深浅底、武器状态、完整轮廓、透明边缘及标题和标签安全区。
- 已更新并解码核对24个演示视频，帧数与时长通过检查。播放截图保存在 `review/playback-*.png`。
- 独立动作帧PNG为2,556～45,467字节；无损优化保存，未为体积降低分辨率。图集与检查图为离线多姿势资料，生成原图继续单独保留。

内置浏览器拒绝 `file:` 协议，未通过其他服务器或浏览器绕过；页面交互未作浏览器验收，画面由现有本地播放器渲染器核对。本轮不修改游戏运行资源或安装包。

[针对性验证结果](verification.json) · [导出与解码检查](export-report.json) · [角色动作和结算对应](action-contract.json)

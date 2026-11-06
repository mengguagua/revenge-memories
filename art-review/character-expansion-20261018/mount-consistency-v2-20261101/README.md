# 飞马体型与骑兵毛蹄 · 2026-11-01修订

[返回「角色重绘 · 全动作对照」](../index.html)

## 本轮修改

- 飞马：以马头、颈胸和躯干为定位基准，修正源姿势2偏大、源姿势3偏小及相邻姿势差异。身体采用原生像素注册校准，保持四肢与躯干的相对比例；骑手已确认的红发头部仍按原尺寸叠放，所有红发像素位置保持一致。低位外翼在肩部连续衔接，保留完整羽尖，避免修正体型后切断或重复翼缘。
- 骑兵：白色马身、蓝白衣甲保留，鬃毛、额毛、尾毛和蹄子恢复为原有深色。以imagegen材质修订稿作区域引导，从不可变的原重绘图恢复对应暗色像素；生产图片没有新增马毛，也没有改变任何透明度或轮廓位置。
- 弓箭手：用户已确认蓝白配色与板寸。确认记录见[acceptance.json](acceptance.json)，本轮不修改其图片。

本轮只更新美术对照，坐骑修订等待视觉验收。

## 动作入口与检查图

[飞马普通攻击](../index.html?action=professions-class-3-ally-battle--original_class_3_normal#motion-player) · [飞马投枪](../index.html?action=professions-class-3-ally-battle--class_3_ally_javelin#motion-player) · [骑兵普通攻击](../index.html?action=professions-class-1-ally-battle--original_class_1_normal#motion-player) · [骑兵投枪](../index.html?action=professions-class-1-ally-battle--class_1_ally_javelin#motion-player)

[飞马全姿势 · 浅底](review/class-3-light.png) · [飞马全姿势 · 深底](review/class-3-dark.png) · [骑兵全姿势 · 浅底](review/class-1-light.png) · [骑兵全姿势 · 深底](review/class-1-dark.png)

## 制作与验证记录

[原生定位与比例参数](registration.json) · [逐图用途、尺寸与实际字节](image-inventory.json) · [材质生成提示词与来源](source/prompt-set.json) · [验证结果](verification.json) · [演示导出和视频解码](export-report.json)

新增24个动作源姿势。原时序、位移、攻击特效和结算点保持，攻击、投枪、待机及通用反应同步使用本轮素材。所有图片按实际显示尺寸检查深浅背景、毛发与蹄子、完整轮廓、透明边缘、翼根衔接及标题和标签内容安全区。相关播放截图保存在 `review/playback-*.png`。

图片以无损方式保存；超出参考体积的一帧使用本机oxipng进一步无损压缩，并验证解码后的RGBA逐字节相同。生成原图保留在 `source/`，不作为生产帧。

此前浏览器自动化拒绝file协议，因此本轮沿用本地播放器渲染器与离线导出来核对画面，不通过其他服务器或浏览器绕过。用户已经确认该本地HTML入口可以手动打开。页面交互未作新的自动浏览器验收；未修改游戏运行资源或安装包。

## 已完成的针对性检查

- 24个源姿势、22条相关动作；1546条无关动作内容摘要保持不变。
- 全部12组飞马姿势保留已确认红发的364个像素及其原位置；马头检查区域的可见面积从835～1585像素收敛到1206～1312像素。该指标用于检查体型漂移，展翼与收腿仍保留自然姿势差异。
- 骑兵全部透明度、像素位置和原亮色马身／米白衣甲保留；变化像素均来自原始深色材质。
- 弓箭手图片哈希保持一致，战斗配置已记录用户确认，播放器显示“已确认”。
- 1498项实际透明轮廓与场景／近景画幅检查通过；16个演示视频经解码核对帧数和时长。
- 独立动作帧PNG为3071～47855字节，详见逐图清单。

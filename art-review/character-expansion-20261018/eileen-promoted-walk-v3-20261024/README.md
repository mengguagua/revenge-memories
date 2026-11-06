# 引光剑使 · 四向行走修正

2026-10-24，仅更新艾琳引光剑使的隔离美术对照。

上行：持剑臂位于身前，由完整后脑、头发、身体遮挡，从背面只露出肩后的剑刃。另一只放松手自然留在身体侧面。下行：左右脚分别在自己的窄通道中前后交替，高低与膝盖弯曲互换；上衣和完整衣摆不移动、不切开、不反转。

左右行走：把持剑前臂、肘、腕和握剑手完整放在胸前，握柄降至下胸，银白剑朝前上方；两相为并腿经过与自然跨步。每个方向采用同一解剖比例，腿部不因跨步单独拉长或变细。左行与右行逐像素镜像。

使用内置 imagegen 分别制作三个方向的完整头／躯干／长衣／武器层，以及每方向的两副关节腿层。衣摆完整覆盖腿根，图层间按前后遮挡合成；没有把人物下半身连同衣服水平翻转，也没有在画面横向切缝处拼接。保持纯色深红发、清楚的深色眼线和柔和琥珀眼睛、蓝白长衣与靛蓝双靴。

保持原始8帧槽、16 ticks每相、60.0988fps、96帧行走预览、32帧方向停步预览、中心锚点和持续地面阴影。待机修正、剧情／大地图、女魔剑士和双方战斗场景均保留，不接入游戏运行场景或设备。

- [上行](../index.html?action=eileen-promoted-maps-tactical-walk--walk-up#motion-player)、[下行](../index.html?action=eileen-promoted-maps-tactical-walk--walk-down#motion-player)、[左行](../index.html?action=eileen-promoted-maps-tactical-walk--walk-left#motion-player)、[右行](../index.html?action=eileen-promoted-maps-tactical-walk--walk-right#motion-player)
- [浅色全姿势](poses-light.png)、[深色全姿势](poses-dark.png)
- 连续相位：[上行](up-continuous-light.png)、[下行](down-continuous-light.png)、[左行](left-continuous-light.png)、[右行](right-continuous-light.png)
- [当前引光剑使地图全姿势](maps-current-light.png)
- 提示词：[背面](source/up-prompt.txt)、[背面交替腿修正](source/up-correction-prompt.txt)、[正面](source/down-prompt.txt)、[侧面](source/side-prompt.txt)
- [素材登记](asset-manifest.json)、[图像尺寸与体积](image-inventory.json)、[针对性检查](verification.json)

验证四向动作及对应停步入口，检查前后脚高度确实互换、整件长衣／头部像素固定、侧向并腿与跨步、上行持剑手遮挡、四向阴影、视频帧数时长、路径及导出文字间距。采用离线画面检查，不声明浏览器界面已验收；用户视觉验收待定。

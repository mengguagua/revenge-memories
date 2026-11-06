# 断路匪待机 · 下颌线与颈部轮廓

在上一版连续颈色基础上补入细的深色弧形下颌线，区分下巴与颈部。颈部侧缘和V领在三相中小幅变化；上半张脸、头发以及修订区域外的身体像素沿用上一版，保持头部中心、肩臂动作与脚底稳定。

仅编辑96×96待机帧中的下颌、颈部和上领口区域。使用内置 `image_gen.imagegen` 绘制，随后按脸部地标对齐并接入局部。原始生成图及完整提示词见[制作记录](source/generation-record.json)。原三相顺序、14/8/14/8 ticks与88帧演示循环保留。

已查看深浅底四连帧、修改前后以及实际导出的代表帧。检查确认下颌线存在、三相颈部形状不同、颈部肤色可见、透明轮廓完整；六张运行帧均为96×96，约1.3KB。单动作14项集成检查及88帧视频解码通过，其余配置和动作内容哈希保持一致。本轮采用离线检查。

- [角色重绘 · 全动作对照](../index.html?action=professions-class-14-enemy-maps-tactical-idle--idle-cycle)
- [修改前后](before-after-light.png) · [深底四连帧](loop-dark.png) · [浅底四连帧](loop-light.png)
- [实际尺寸](loop-native-light.png)
- [素材清单](asset-manifest.json) · [定向检查](checks.json) · [导出检查](export-report.json) · [合并记录](merge-report.json)

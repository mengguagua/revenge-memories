# 村民职业样板（class14 / ally）

战斗 9 个原生独立姿势（8 份新人体，斩击帧7复用6加原弧），11 个源帧引用；7 条当前可达攻击绑定。战术地图为 2 个行走步相、3 个待机姿势。原别名、原帧时序与外置雷电保持。

入口：`battle/frame_mapping.json`、`maps/frame_mapping.json`。所有图像只在本隔离目录，未修改或接入游戏。形象是职业样板，不给卡洛等角色新增能力。

原作短衣与可见腿部按层识别，新增卷袖衬衣、短皮背心、橙色腰巾、灰裤和布绑腿。地图待机第三相的白刃原本仍可见，已按 x8、y7–13 的原像素补回；深浅底均复核。

登记使用可见靴底与头高，统一比例缩放，不按刀尖居中。保留的新刀轮廓和少量脚部透视差异详见 `source-inspection.json`，不声称逐像素锁定。最终对照在 `battle/reviews/final-canonical-*.png`、`maps/reviews/map-original-vs-new-*.png`。提示词、原始生成稿和全部局部修订均保留。

## 原生战术移动来源纠正

当前行走已替换为 class14 原CPU确认的CHR26四方向8槽（6个新绘、2个严格镜像），每相16tick。旧两相混源稿与映射只作历史保留，不再作为正确战术行走。战斗和静态待机保持已通过版本。当前对照见 `maps/reviews/tactical-native/native-v4-dark.png` 与 `native-v4-light.png`；源证据来自 `source-input/corrected-tactical-walk`。

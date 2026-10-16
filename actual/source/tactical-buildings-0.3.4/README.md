# 单格战场建筑 · 0.3.4

通过内置 imagegen 分别生成营垒、军帐、舵楼哨位。完整提示词保存在 [prompts.json](prompts.json)；三个透明原稿分别为 fort-source.png、tent-source.png、deck-source.png，本目录隔离导入，不直接打入游戏。

运行素材位于 `../../assets/battlefield-0.3.0/modules/`：tactical_fort.png、tactical_tent.png、tactical_deck_post.png。`../../tools/build_battlefield_modules.py` 保留整个透明轮廓，等比缩放至16×16原生格，最近邻采样、20色调色板、二值透明、oxipng无损压缩。房屋、雪屋和仓房沿用完整旧源图，按同一占格规格适配。

六类素材主轮廓至少一边16像素、短边12—16像素；不将世界图横向小符号拉高。深浅背景及实际地形上的轮廓已核对，像素尺寸、实际字节数、旧/新轮廓与布局改动见 `../../reports/battlefield-0.3.0/building-scale-fix.json`。

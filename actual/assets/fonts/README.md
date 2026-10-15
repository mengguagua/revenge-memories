# 中文像素字库

运行字库来自 [Fusion Pixel Font](https://github.com/TakWolf/fusion-pixel-font) 的官方 `2026.09.25` 发行，选用 `12px-monospaced-zh_hans.bdf`。使用 SIL Open Font License 1.1；本目录保留完整 OFL 与上游许可。

`fusion-pixel-12px-zh-hans.png` 将源 BDF 字形逐位复制到 12×12 格内，没有缩放、抗锯齿或丢弃可见笔画。汉字及全角标点前进 12 像素，半角字符前进 6 像素。游戏继续使用原作字体显示英文与数字。

运行纹理 1536×2412，包含 25,614 个字形，326,109 字节；尺寸保留完整常用汉字覆盖和原生可读性，已使用 1-bit 调色板及 `oxipng` 无损压缩。`data/font_zh.json` 记录字符矩形、真实笔画范围、源文件摘要及布局度量，纹理必须使用 nearest 采样。

复现：下载上游 BDF ZIP，使用带 Pillow 的 Python 执行 `tools/build_chinese_font.py --archive ZIP路径`。`tools/build_chinese_font_audit.py` 检查当前中文文本覆盖、字形边界、透明度与实际体积。

仅排除韩文专用区及 6 个超出 12 像素格的特殊纵排/私用符号；保留所有源字库中的简体、繁体 CJK 及中文标点。诊断图片 `font-preview.png` 不用于游戏界面。

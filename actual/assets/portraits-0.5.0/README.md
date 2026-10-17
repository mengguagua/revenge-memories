# 当前战役画像 · 0.5.0

48张48×48运行PNG，使用内置image_gen独立生成的源图制作，oxipng无损压缩。保持像素最近邻整数缩放，不将高分辨率原图打包。所有画像在真实状态页做2304像素逐点比较，最终运行资源与效果基准一致。

人物、地域兵种和剧情阶段由 `../../core/portrait_library.gd` 分配，定义与身份说明在 `../../data/portraits.json`。男女主各3张，17岁胡纳普和16岁艾琳保持相同年龄及身份；其余包括正式同伴、具名人物、区域NPC、普通兵种及两种魔物。

[逐张制作规格与提示词](../../source/portraits-0.5.0/jobs.json) · [原始生成与编辑记录](../../source/portraits-0.5.0/README.md) · [运行效果及前后对比](../../reports/playtest-0.5.0/index.html)

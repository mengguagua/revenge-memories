# 清晰度修复源文件 · 0.5.2（不导出）

三张 `hunapu_*-guide.png` 为旧48px画像的20倍最近邻放大稿。三张 `hunapu_*-generated.png` 使用内置image_gen参考图编辑生成；逐组提示词、输入文件和默认生成结果路径保存在 `*-generation.json`。只修复面部像素簇、嘴线和眼鼻对比，保留17岁蓝发剑士的身份、服饰与剧情阶段。

地图/据点和战斗动作复用原版已经提取的原生像素骨架，仅做索引颜色标注，不使用生成大图缩小来重造动作。运行版由 `actual/tools/build_clarity_assets.py` 组装；旧0.5.1资源继续保留作对比。

`critical-timeline.json` 保存原动作表参考；`executed-melee.json` 保存完整离线执行的普通17、必杀18程序，包括原解释器的切换等待。`actual/tools/extract_hunapu_motion.py` 可由项目固定修订源文件复现，运行时仅使用其普通JSON输出。

本目录由 `.gdignore` 与导出排除规则隔离。生成原图及原版代码/ROM不进入应用。

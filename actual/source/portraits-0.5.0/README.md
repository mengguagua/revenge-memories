# 0.5.0 画像源文件

48张独立画像通过内置 image_gen 逐张生成，无收费CLI或外部API替代。`jobs.json`保存逐角色的制作规格与提示词，`generation-log.json`保存输出来源。首张胡纳普回忆稿作为统一画风参考，其余同时参考旧画像的身份与发色，按现行剧情校正年龄和服饰。

每个同名PNG是保留的高分辨率生成源图；`vucub-attempt1.png`、`vucub-attempt2.png`为未采纳的日冠稿，定向修订提示和最终输出来源在 `vucub-edit*.json`。最终稿具有完整七羽日冠。少量起始样式稿/重试的逐字调用文本未单独保留，`jobs.json`记录最终制作规格，不冒充所有历史调用的完整日志。

运行稿在 `../../assets/portraits-0.5.0/`，48×48，最近邻制作并经oxipng无损压缩。源图由 `.gdignore` 排除Godot导入，PNG本地离线保留，不随Git和应用交付；提示词与来源记录保留入库。最终尺寸、大小和SHA256见 `../../reports/playtest-0.5.0/image-manifest.json`。原先的参考画像继续保留，当前可见人物、敌军状态和对白由新画像注册表提供资源。

# 第三章地图重设计 · 2026-10-22

入口：index.html。覆盖 M31/M32/M33、F31/F32/F33、S31/S32 八图。

- baseline 保存修改前的地图配置与全部40图/core指纹；before 是修改前原生场景。
- images 是最终 Godot 原生地图全景，screenshots 是实际按键试玩的视口。
- selected-play.json 指明最终两轮逐关结果。原始尝试保留在 play 下，失败和旧版尝试不计入两轮。
- flow-continuation.json 单独记录真实上一章完成状态到第四章入口的连续链。
- rules-probe.json 与 final-anchor-probe.json 使用明确的测试场景，只证明规则、实际通行及保存，不冒充完整通关。
- invariants-audit.json 比较剧情、单位属性、核心代码与其他32图。
- package-checks.json 验证独立桌面包中的40张关卡和美术资源；文档同步结果见 document-sync.json。

测试使用开发记录的隔离副本，不修改用户存档；没有新增旧地图兼容副本。沿用既有动画。

复现主入口：tests/ch3_redesign_play.gd；参数 --label=独立输出名 --codes=M31,M32 或 --continuous。
规则检查复现见 rules-probe-reproduce.txt。截图仅通过 tools/capture_campaign.sh 后台窗口保护器启动。

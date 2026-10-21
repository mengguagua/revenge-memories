# 战后HP恢复修复 · 2026-10-21

正常正式成员应在胜利结算后恢复满血。此前 `start_battle()` 会在下一战部署时恢复HP，但 `complete_battle()` 把战后受伤HP直接写入名册；世界和据点的“部队状态”读取名册，因此显示16/28。这是持久状态缺少恢复，不只是血条画错。

胜利结算先处理成长、濒死、奖励和成员归属，再将两队正常正式成员恢复至当前最大生命，并同步战斗单位副本。后备成员也恢复；敌军、临时／中立友军和未入队模板不恢复。濒死者仍为0HP，经验、装备、救治次数与份额保留，重试快照不变。

兼容读取旧世界、据点、章节结束、结局和已结算胜利记录；战斗中途、失败与尚未结算胜利记录保留伤势。仍先完整验证存档再进行兼容处理，不修改记录格式，不直接写入玩家记录。

验证：68项定向检查通过；去除本次修复的原逻辑在同组检查中出现24项失败；56项已有濒死／救治检查通过。五张后台截图检查生命数字、血条格数和文字安全区域，均通过，并已人工查看。使用状态夹具和独立临时记录，不代表完整自然流程回归。

画面中的主角等级3、经验45、最大生命28为重现用户截图的夹具；“修复前”展示旧记录中16/28的状态，“修复后”实际调用修复版读档并显示28/28。濒死和战斗中途截图分别保留0/23和16/28。

- [画面对照](index.html)
- [定向检查](checks.json)
- [原逻辑对照](before-checks.json)
- [已有救治检查](casualty-checks.json)
- [画面与布局检查](captures.json)
- [汇总及图片尺寸、字节数](summary.json)

运行定向检查：在工程根目录执行 `/Applications/Godot.app/Contents/MacOS/Godot --headless --path actual --audio-driver Dummy --script res://tests/postbattle_hp.gd`。记录全部写入 `/private/tmp/revenge-postbattle-hp-20261021/`。随后通过 `CAMPAIGN_CAPTURE_LOG=/private/tmp/revenge-postbattle-hp-20261021/visual.log bash actual/tools/capture_campaign.sh res://reports/postbattle-hp-20261021/capture.gd` 复核画面，保留后台防抢焦点保护。

本次更新源码与规则说明，未重新导出既有0.10.0安装包。

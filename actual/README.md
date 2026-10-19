# 复仇与回忆 · 序章至第三章

当前开发入口：`scenes/main.tscn`。当前工程版本 **0.8.12**，当前测试包：`dist/RevengeMemories-PlaytestFixes-20261019.app`。目录中的旧 `RevengeMemories.app` 为历史版本，不能据此判断最新效果。

当前接入状态以 `data/reviewed_animations.json`、`data/party_visuals.json` 和 `data/portraits.json` 为准。人物视觉验收以用户最近反馈为准；旧版“预览认可”、旧演示和自动检查计数不代表所有角色均已验收。

2026-10-19 清理覆盖当天五次提交和当前工作区，保留正在修改、新增的美术资源及原稿、帧图、交付文件，只删除确认过期且与提交一致的演示、对照图和导入前备份。没有回退玩法或美术改动，没有重写 Git 历史；记录见 `reports/cleanup-20261019-evening/summary.json`。

## 当前内容

正式世界图 39 据点、40 路线；可操作序章、第一章7场、第二章8场、第三章8场战斗，共23场。第三章包括两队各3场主线、2条救援支线、两路独立切换、重逢与营站会谈、共享救治及当面物资交接。第四章及后续尚未实施。剧情设定以 `../docs2/` 为准。独立存档保留成长、经验、装备及濒死救治规则，不覆盖根目录参考复刻工程。

当前角色运行资源由 `data/reviewed_animations.json`、`data/party_visuals.json`、`data/m11_party_motion.json`、`data/portraits.json` 管理。主角大世界使用同一套剧情地图资源；职业战斗身体共享。此处只说明当前接入状态，不认定画面已获验收。

第二章完成菜单可选择“开始第三章”。西街脱围后按S切换队伍；两队完成调查并分别抵达营站后进行会谈。原第二章存档可直接接续，两队成长、装备和伤情保留。

[第三章两轮验收](docs/第三章交付与两轮验收.md) · [第三章实机截图](reports/chapter3/index.html)。本章沿用既有移动与战斗动画；诺娅静态画像复用现有参考资源。

## 可复用输入与工具

- `source/characters/original-motion/`：保留原始战斗程序和职业身体帧。战术行走采用 `../art-review/character-expansion-20261018/source-input/corrected-tactical-walk/overlay.json`；早期混用 CHR26 的 original-walk 不可作为真实战术动作依据。战斗提取的修正见同级 `corrected-ally-motion/overlay.json`。
- `source/characters/portrait-bases.json`、`portrait-bases/`、`portraits-generated/`：可复用画像输入、生成原图与记录。
- `source/characters/map-bases.json`、`map-bases/`：仅用于重建当前未验收的发色绑定，不作为新的动作参考。
- `tools/extract_character_motion.py`：原始战斗程序提取；修正参考见上述 source-input。
- `tools/build_map_identities.py`：现有地图角色发色绑定；不改四肢或动作时序。
- `tests/map_identities.gd`、`tests/map_identity_play.gd`、`tools/capture_map_identities.gd`：当前资源检查与后台复核。

运行：双击本地测试包或 `运行游戏.command`。逻辑检查优先 headless；图形检查仅使用 `bash tools/capture_campaign.sh`，必须保留防抢焦点保护。`tools/package_local.sh` 导出本地测试包。

横屏按实际窗口扩展逻辑视口，像素等比整数缩放；移动端仍为画幅模拟，未交付移动端安装包或真机验收。

## 当前规则与保留说明

- [前两章武器与投放设定](docs/前两章武器与投放设定.md)
- [第一章升级属性规则](docs/第一章升级属性规则.md)
- [濒死与前两章泉水救治](docs/濒死与前两章泉水救治.md)
- [第二章交付与验收](docs/第二章交付与验收.md)
- [仓库文件保留说明](../docs/仓库文件保留说明.md)
- [本次清理范围和数量](reports/cleanup-20261018/summary.json)

废弃人物试验、旧接入脚本、旧连续截图和重复应用备份已清理。已提交内容仍可从 Git 历史恢复；不重写历史，也不把旧画面的自动检查结果当作当前视觉验收。

# 复仇与回忆 · 序章至第四章

当前开发入口：`scenes/main.tscn`。当前运行版本 **0.9.0**，本轮测试包：`dist/RevengeMemories-0.9.0-Chapter4-20261020.app`。

2026-10-20源码命名修订：完整已确认方案的11个己方新名与3个敌方新名已全部接入，包括乡勇、壁垒卫士、术法师→博学术师、疗愈师→济世术师和三条修订确认路线；敌方使用咒法师、移形术师、召魔师。统一配置为 data/class_names.json，职业显示与转职使用同一表，旧存档无需迁移。普通村民、宗教身份、剧情神官称号与原版资料保留，数值和转职条件保持现状。已有0.9.0安装包未重新导出。

0.9.0接入第四章8场主线、2场支线及10个战后据点。地图按连续道路、实际门前交互、取水台、干地与修复环廊制作；支持先夺塔后等东岸步骤、投送援军快照、赛琳招募与D42后最后一份共享救治。完成两轮输入试玩与后台画面检查，详见[第四章交付与两轮验收](docs/第四章交付与两轮验收.md)和[实机截图](reports/chapter4/index.html)。现有动画不变，保留五槽记录和装备预览。

0.8.15为行囊领取增加职业、当前装备、适配条件与换装前后属性比较；增加与降低分别显示带符号的数值，确认后旧装备退回本队行囊。盾、戒指和法器的条件特性可单独查看，不适配时禁止换装。见[行囊换装预览](reports/equipment-preview-20261020/README.md)。

0.8.14修复护送单位遇险截短路径后停在友军格内、两组流民重叠而看似少一人的问题。读入旧战斗记录时自动将重叠的护送单位移至就近可达空格，保留血量、行动状态、回合与任务进度；同样修正第二章护送分支。说明与针对性检查见[流民重叠修复](reports/m11-overlap-20261020/README.md)。

0.8.13新增雪海首页、开始／继续游戏和五个独立记录槽，显示记录时间；S菜单可选槽保存，旧单文件原件保留。对白与敌方回合续接、覆盖取消、写入失败和旧档兼容已完成两轮针对性检查。设计、动画、实机截图与测试包供本轮确认，详见[首页与五槽记录交付](reports/journey-home-20261019/README.md)及[角色重绘确认页](../art-review/character-expansion-20261018/index.html#journey-home)。

以下为此前的开发记录。

当前接入状态以 `data/reviewed_animations.json`、`data/party_visuals.json` 和 `data/portraits.json` 为准。人物视觉验收以用户最近反馈为准；旧版“预览认可”、旧演示和自动检查计数不代表所有角色均已验收。

2026-10-19 清理覆盖当天五次提交和当前工作区，保留正在修改、新增的美术资源及原稿、帧图、交付文件，只删除确认过期且与提交一致的演示、对照图和导入前备份。没有回退玩法或美术改动，没有重写 Git 历史；记录见 `reports/cleanup-20261019-evening/summary.json`。

## 当前内容

正式世界图 39 据点、40 路线；可操作序章、第一章7场、第二章8场、第三章8场、第四章10场战斗，共33场。第三章包括两队各3场主线、2条救援支线、两路独立切换、重逢与营站会谈、共享救治及当面物资交接。第四章完成后可返回本章整备，第五章尚未实施。剧情设定以 `../docs2/` 为准。独立存档保留成长、经验、装备及濒死救治规则，不覆盖根目录参考复刻工程。

当前角色运行资源由 `data/reviewed_animations.json`、`data/party_visuals.json`、`data/m11_party_motion.json`、`data/portraits.json` 管理。主角大世界使用同一套剧情地图资源；职业战斗身体共享。此处只说明当前接入状态，不认定画面已获验收。

第二章完成菜单可选择“开始第三章”。西街脱围后按S切换队伍；两队完成调查并分别抵达营站后进行会谈。原第二章存档可直接接续，两队成长、装备和伤情保留。第三章完成菜单可开始第四章，两队从会合营站独立出发；安全停塔、王都胜利和祭所验证齐备后，由营站信使确认收束。

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

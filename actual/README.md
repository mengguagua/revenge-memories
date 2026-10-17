# 复仇与回忆 · 序章至第二章

当前开发入口：`scenes/main.tscn`。当前运行版本 **0.7.2**，本地测试包：`dist/RevengeMemories.app`，窗口标题含版本号。

**当前角色画面未达到用户预期，尚未通过视觉验收。** 资源加载、像素一致性或试玩通过均不代表人物造型和动作效果达标；后续判断应以用户要求和原作 NES/CHR/OAM/ASM 动作为依据，不以旧半成品、已否决对照图或旧报告为参考。

## 当前内容

正式世界图 39 据点、40 路线；可操作序章、第一章 7 场与第二章 8 场战斗，共 15 场。第三章及后续尚未实施。剧情设定以 `../docs2/` 为准。独立存档保留成长、经验、装备及濒死救治规则，不覆盖根目录参考复刻工程。

当前角色运行资源由 `data/party_visuals.json`、`data/m11_party_motion.json`、`data/portraits.json` 管理。主角大世界使用同一套剧情地图资源；职业战斗身体共享。此处只说明当前接入状态，不认定画面已获验收。

## 可复用输入与工具

- `source/characters/original-motion/`：直接解码原作的程序、职业身体及行走帧；是后续动作修改依据。
- `source/characters/portrait-bases.json`、`portrait-bases/`、`portraits-generated/`：可复用画像输入、生成原图与记录。
- `source/characters/map-bases.json`、`map-bases/`：仅用于重建当前未验收的发色绑定，不作为新的动作参考。
- `tools/extract_character_motion.py`、`extract_character_walk.py`：原作动作提取。
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

# 护途盾与续愿戒 · 源码接入记录

2026-10-23。名称、数值说明、固定 NPC、交付事件、战场事实与领取保存已接入，docs2 设定、流程、故事、台词及命名记录同步。未更新安装包。

- 护途盾（53，原龙盾）：M51 两处病房开门，两组伤兵均存活并实际撤到南口，击败队长胜利后，回 H51 伤兵照护处面对固定军械官领取。保留物防+13、抗性+13、阶段恢复5HP。
- 续愿戒（55，原天使戒）：S41 烧毁前保护名册、确认避难院、击败焚毁队长并胜利，回 H49 避难院面对固定保管人领取。保留有效幸运40、升级成功增长由+1变+2、阶段恢复5HP。失败成长不会逐项补满，不改实际幸运，不追溯成长；原有全失败保底与数值上限沿用。

两件各一份，独立于六件守途兵装，排除旧稀有掉落，普通池不含两件。领取先进入西队行囊，超过手动40件上限也保留，不替换当前装备、不改变生命或另一队物资。原有银弓与补给独立。只救出一组、名册烧毁或未确认避难院仍允许原有胜利，但不获得对应饰品。

实现位于 `core/story_accessories.gd` 与 `data/story_accessories.json`。仅在真实胜利结算记录病房、伤兵生死、实际撤离，或名册保护、完整状态、避难院确认与首领击败。`story_accessory_results` 保存事实，`story_accessories_claimed` 保存交付；两者随现有 flags 和战前快照保存。缺失事实的旧通关不推定成功，不沿用银弓按通关补发的分支。重复对话与事后状态变动不重写已记录事实；重试随快照回滚。第四章章末仍允许返回地图整备，因此已满足条件的续愿戒在第四章内仍可领取；开始第五章后无法回领。

H49 保管人在 (4,5)，H51 军械官在 (5,5)，均复用现有角色素材，与普通队员生死／入队独立。后台截图用运行据点碰撞检查从 (6,7) 到 NPC 相邻格的路径，并核对不落入建筑占地。战前与 S41 邀请写明条件，第四章收束／第五章合流前给出待领取或未满足提示，允许继续主线。

258 项定向检查通过，覆盖真实交互、出口撤离、连续点火烧毁、成功与缺条件结算、满包、存读档、切队、重试、重复对话、原数值与成长上限、旧稀有排除、历史通关不误发、事实与领取的严格类型检查。原六件守途兵装 319 项检查也通过。

26 张后台截图覆盖 426／256 原生宽度的 NPC、交付分页、装备比较、窄屏完整说明及待领取提醒；文字安全区与防重叠检查无错误，并人工抽查 NPC、交付与装备页。图片尺寸、字节数及无损压缩方式见 `image-manifest.json`。没有新增运行位图资源。

验证使用真实部署存档上的受控位置与目标状态，真实调用交互、胜负、结算和交付，未重新自然试玩整个第四／第五章。存档仅写 `/private/tmp/revenge-story-accessories-20261023/`，未写用户旅程记录。图形验证通过既有 `capture_campaign.sh` 后台保护脚本，不显示窗口、不抢焦点。

复现（Godot 4.7.1）：

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path actual --log-file /private/tmp/revenge-accessories-tests.log --script res://tests/story_accessories.gd
bash actual/tools/capture_campaign.sh res://tools/capture_story_accessories.gd
/opt/homebrew/bin/oxipng -o 2 --strip safe --quiet actual/reports/story-accessories-20261023/*.png
python3 actual/tools/build_story_accessories_report.py
```

[界面与验收页面](index.html)

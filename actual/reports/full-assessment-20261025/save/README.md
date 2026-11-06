# 存档、重试与流程中断可靠性 · 2026-10-25

当前源码已修复并验证；没有连接、安装、启动或更新 iPhone。所有故障注入、进程中断及读写都使用隔离目录或历史检查点副本。

[恢复入口画面](index.html) · [定向检查](checks.json) · [修前失败证据](baseline/checks.json) · [进程中断](process-interruptions.json) · [既有专项回归](regression-summary.json)

## 修复

| 问题 | 修复与行为 |
| --- | --- |
| 重试没有撤回本关击杀数 | `retry_battle` 与回合、阶段一起把 `kills` 清零。快照恢复此前成长、伤情、装备、行囊与随机状态；本关收益撤销。 |
| 非法内存状态仍可覆盖好档 | 先序列化，再用实际读取器相同的完整校验检查将要写出的 JSON。失败不触碰主档。先序列化是为了把运行时 StringName 键按 JSON 规范转为字符串，避免误拒合法的奖励事实。 |
| 恢复副本写入不是原子替换 | 先复制到 `.bak.tmp`，再同目录重命名为 `.bak`。主档继续用 `.tmp` 原子替换；复制或重命名失败保留原主档与上次有效恢复副本。 |
| 主档损坏或丢失后，有好副本也无法继续 | 五槽选择器只在主档无效时检查同槽 `.bak`。有效副本显示“恢复副本”及其自身时间，正常确认后继续该检查点。损坏副本不会被选用，也不会读取未提交的 `.tmp`。 |
| 恢复后的自动保存可能丢掉损坏原件 | 首次覆盖前，将损坏主档按内容摘要留为 `.damaged-…`；不同坏档不互相覆盖。旧格式恢复副本的首次升级也保留 `.pre-casualty.bak`。 |
| 对话续读状态缺少返回界面也被判有效 | 拒绝缺失／未知 `return`、非字符串回调；先验证 flags 类型再访问其字段。AI新增的 `guard_alerted` 必须为布尔值。 |

恢复副本是上一次完整检查点，因此可能早于损坏主档；选择界面明确显示恢复来源和时间，没有静默假装恢复最新进度。

## 验证

- 修前237项定向检查出现9项相关失败；修后241项通过。恢复成功后才执行的4项检查使总数增加，断言数不等于独立游戏场景数。
- 包含临时文件阻塞、恢复副本目标阻塞、无父目录、截断 JSON、坏主档／坏副本、反复读取与保存、单次交锋中途与完成后的恢复、击杀／经验／物品／旗标回滚，以及第一至第五章历史边界副本。
- **6次真实进程中断**：由 Python 启动并只终止自己的 headless Godot 写入进程，分别在主档 `.tmp` 和恢复副本 `.bak.tmp` 可观察窗口发送 SIGKILL。每次主档和恢复副本均是完整 JSON，并由实际游戏读取器确认可加载。为稳定观察窗口，使用约500KB的隔离压力夹具，不冒充玩家存档。
- **831项既有专项回归通过**：旅程界面43、伤情与旧档56、主角进阶155、六兵装319、两饰品258。覆盖一次性奖励、满行囊、转职不叠加、重试撤回奖励、跨队归属、旧伤保留、对话页续读、已行动敌军不重复行动。
- 两个旧测试夹具已修正：旅程测试尊重当前首页默认“继续”和取消战中手动保存后的菜单；旧伤情迁移直接构造 schema-2 夹具，不再先让正式 writer 写入非法 schema-3。没有放宽正式读取校验以迁就夹具。
- **13项后台界面检查通过**：256与364逻辑像素下恢复副本提示均实际渲染，逐字形安全区无错误；实际确认可恢复正确槽位，随后保存保留损坏原件。两张图经 oxipng 压缩，逐像素RGBA一致，见[尺寸与字节记录](image-manifest.json)。

## 边界

- 战斗逐击动画在内存中推进，完整交锋才落盘。进程在尚未提交的动画中结束，恢复到上一完整检查点，而非保存半次伤害／半次经验。定向检查验证了这一边界；本次没有在暂停通知中强行保存半完成状态。
- 真实 iPhone 锁屏、电话打断、系统内存回收、磁盘延迟以及突然断电的 fsync 持久化均未在设备上测量。macOS进程中断不等同于这些条件。
- 后台图形检查由启动前生效的 guard 禁止窗口显示和激活。首次普通沙箱图形进程中止；获准的后台进程完成实际渲染。最后退出有既有 ObjectDB/资源清理告警，未计作运行页面通过证据；最终页面绘制和安全区检查完成。

## 复现

```sh
/Applications/Godot.app/Contents/MacOS/Godot --headless --path actual --script res://tests/full_assessment_save.gd
python3 actual/tests/save_process_interruptions.py
/Applications/Godot.app/Contents/MacOS/Godot --headless --path actual --script res://tests/full_assessment_save_ui.gd
bash tools/background_capture/run.sh res://tests/full_assessment_save_ui.gd --path actual
```

主要代码：`actual/core/game_state.gd`、`campaign_save_validation.gd`、`journey_slots.gd`、`journey_screen.gd`、`journey_art.gd`。测试入口保留在 `actual/tests/`。

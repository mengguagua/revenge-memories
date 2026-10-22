# 手机据点提示与战斗返回菜单 · 独立验收

50项状态／真实输入检查和1824个提示位置探针全部通过，覆盖256、406、426逻辑宽度。P00每种宽度验证74个实际方向输入可达格的四个朝向；H09每种宽度验证77个可达格的四个朝向。另检查出生点、沿实际方向键走到赫兰身旁、提示缩短，以及半步移动中的整段人物扫掠。

遮挡检查独立根据 `_draw_frame` 的真实尺寸计算人物矩形（frame_size除以native_density，tile_origin仍为逻辑值），直接核对提示框与NPC、物件、主角、移动扫掠、当前交互箭头及出口箭头均不相交。文字边框安全区同时检查。独立review发现并反馈了初稿保护矩形遗漏native_density的问题，已由主任务修正后重新通过。

战斗菜单使用真实键盘输入打开、选中“保存并返回主菜单”，在三个宽度下均可完整显示。保存到当前第3槽后回标题，随后通过五槽“继续”读入第3槽：第4回合、己方阶段、主角16HP、队员已行动标志、单位位置、随机状态、战前重试快照均保留。无战斗重置，邻近第1槽字节不变。模拟写入失败时留在战场并显示失败提示，内存战局与既有记录完整保留。

全部检查在headless子视口与 `/private/tmp/revenge-phone-hud-menu-20261022/` 临时记录中完成，没有操作玩家记录。本报告为输入／几何与保存续读验收，不宣称iPhone真机操作；集成手机画面由主任务单独核对。

- [检查、房间探针与代表状态](phone-hud-menu-checks.json)
- [引擎日志](phone-hud-menu-engine.log)

复核：`/Applications/Godot.app/Contents/MacOS/Godot --headless --path actual --audio-driver Dummy --script res://tests/phone_hud_menu.gd`。

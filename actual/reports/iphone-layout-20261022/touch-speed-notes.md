# 手机长按加速 · 2026-10-22

根因：触控壳将合成按键直接传给UI输入函数，未改变引擎的物理键状态；旧加速只读取物理Z／空格，因此手机没有可用的长按加速。

新增 `set_touch_fast_forward(bool)`，只在战斗动画 `combat` 画面接受按下，松开始终清除。`effective_animation_speed()` 为普通动画等待和原生帧时钟统一返回倍率：按住3倍，松开正常。API不产生确认事件，奖励页和其他页面不能开启触控加速。失焦、暂停与离开战斗画面清除状态。

战斗内的长等待逐帧消耗源时长，因此在等待中途按下或松开也能改变剩余播放速度。短源帧仍按原帧周期聚合，非战斗等待保持既有方式。原生动作的deadline循环每个源帧读取统一倍率，接触点与实际结算调用保持原顺序。

39项定向检查通过：按住／松开／失焦／暂停／场景切换、等待中途按下与松开、两种动作时钟、动作中途松开、完整源帧顺序和一次真实HP接触。测试使用203帧真实主角攻击程序；普通等待分支由测试夹具将同一素材的 `original_motion` 标记切换为false以隔离验证。播放不使用instant_mode，实际测量墙钟耗时。

所有夹具在隐藏的headless视口运行，不写入玩家记录。真实触控按键、多指释放与页面切换由触控壳测试单独验证，此报告不宣称iPhone真机试玩。引擎沙箱有macOS系统证书提示，脚本断言全部通过，无脚本运行错误。

- [计时、帧顺序与结算检查](touch-speed-checks.json)
- [本次引擎日志](touch-speed-engine.log)

复核：`/Applications/Godot.app/Contents/MacOS/Godot --headless --path actual --audio-driver Dummy --script res://tests/touch_fast_forward.gd`。

extends "res://tests/polish_play.gd"
## Two directed real-input rounds. Only Hunapu's first two attack actions
## use complete, normal-speed source animation; gameplay data is untouched.
var hero_round=1
var timed_actions=0
var native_frames=[]
var animation_shots=[]
var seen_poses={}
var watch_ui_seen=false
var sample_clock=0
func _initialize() -> void:
	if DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	hero_round=int(OS.get_environment("HUNAPU_ROUND")) if not OS.get_environment("HUNAPU_ROUND").is_empty() else 1
	polish_round=2;polish_label="hunapu-round"+str(hero_round)
	polish_codes=["M11"] if hero_round==1 else ["M15"]
	review_out="res://reports/hunapu-0.5.1/round"+str(hero_round)+"/"
	call_deferred("run")
func run() -> void:
	_observe()
	await super.run()
func act(id: String) -> void:
	var slow=id=="hunapu" and timed_actions<2
	var before=animation_shots.size()
	ui.instant_mode=not slow
	await super.act(id)
	ui.instant_mode=true
	if slow and animation_shots.size()>before:timed_actions+=1
func _observe() -> void:
	while true:
		await process_frame
		if not is_instance_valid(ui):
			if watch_ui_seen:return
			continue
		watch_ui_seen=true
		if not allow_capture or ui.view!="combat" or ui.instant_mode:continue
		sample_clock+=1
		if sample_clock%3!=0:continue
		await RenderingServer.frame_post_draw
		if not is_instance_valid(ui) or ui.view!="combat":continue
		var path=review_out+"animation-"+str(native_frames.size()).pad_zeros(4)+".png"
		viewport.get_texture().get_image().save_png(path)
		var event=ui.battle_animation.active_event;var frame=int(ui.combat_poses.get("hunapu",60))
		var record={"path":path,"stage":ui.game.battle_data.code,"turn":ui.game.turn,"hero_pose":frame,"offset":str(ui.combat_offsets.get("hunapu",Vector2.ZERO)),"attacker":event.get("attacker",""),"contact_calls":ui.battle_animation.contact_calls,"view":"combat","fixture":false,"layout_errors":ui.layout_errors.duplicate()}
		native_frames.append(record)
		if not ui.layout_errors.is_empty():record_failure("Timed combat text safety")
		var key_=str(ui.game.turn)+":"+str(event.get("attacker",""))+":"+str(frame)
		if event.get("attacker","")=="hunapu" and not seen_poses.has(key_):
			seen_poses[key_]=true;animation_shots.append(record)
func write_review() -> void:
	super.write_review()
	var path=review_out+"play-checks.json";var report=State.read_json(path)
	report.round=hero_round;report.version="0.5.1";report.timed_hero_actions=timed_actions
	report.animation_shots=animation_shots;report.native_animation_frames=native_frames
	report.animation_scope="First two Hunapu actions with actual combat are rendered with original full 60.0988-fps source programs at normal speed. Other play is accelerated presentation only; no gameplay stat, HP, position or RNG edits."
	if animation_shots.is_empty() or timed_actions<2:report.passed=false;report.failures.append("Two full personal attack actions were not captured")
	var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()

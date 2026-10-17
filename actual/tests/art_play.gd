extends "res://tests/polish_play.gd"
## Normal input play from genuine historical deployment saves; presentation
## alone is accelerated after each profession has shown a complete action.
const PartyArt=preload("res://core/party_sprites.gd")
var party_round=1
var timed_classes={}
var native_frames=[]
var animation_shots=[]
var seen_poses={}
var watch_ui_seen=false
var last_sample_ms=0
var last_signature=""
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	party_round=int(OS.get_environment("PARTY_ROUND")) if not OS.get_environment("PARTY_ROUND").is_empty() else 1
	polish_round=1;polish_label="party-round"+str(party_round)
	polish_codes=["M15","F24"] if party_round==1 else ["M14","F26"]
	review_out="res://reports/current-art/round"+str(party_round)+"/"
	call_deferred("run")
func run():
	_observe();await super.run()
func settle():
	# The offscreen renderer can exceed1000 process frames/sec. A frame
	# budget expires before a legitimate multi-strike exchange finishes.
	# Use wall time for normal-speed animations, not an artificial frame cap.
	var deadline=Time.get_ticks_msec()+180000
	while Time.get_ticks_msec()<deadline:
		if abort:return
		if ui.view in ["plot","reward"]:
			if ui.view=="reward" and ui.reward.get("leveled",false):
				var stamp=str(ui.game.stage_id)+":"+str(ui.reward.unit)+":"+str(ui.reward.get("level_after",0))
				if not captured_levels.has(stamp):captured_levels[stamp]=true;await shot(str(ui.game.battle_data.code)+"-levelup-"+str(ui.reward.unit)+"-"+str(ui.reward.get("level_after",0)))
			key(KEY_Z)
		elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
		if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
		await process_frame
	record_failure("Input owner failed to release within180 seconds: "+ui.view)
func act(id: String):
	var actor=ui.game.find_unit(id)
	var role=PartyArt.class_key(actor)
	var slow=not timed_classes.has(role)
	ui.instant_mode=not slow
	await super.act(id)
	ui.instant_mode=true
func _observe():
	while true:
		await process_frame
		if not is_instance_valid(ui):
			if watch_ui_seen:return
			continue
		watch_ui_seen=true
		if not allow_capture or ui.view!="combat" or ui.instant_mode:continue
		var now=Time.get_ticks_msec()
		var signature=str(ui.combat_poses)+str(ui.combat_offsets)+str(ui.combat_hp)+str(ui.combat_shake)
		if signature==last_signature and now-last_sample_ms<50:continue
		last_signature=signature;last_sample_ms=now
		await RenderingServer.frame_post_draw
		if not is_instance_valid(ui) or ui.view!="combat":continue
		var event=ui.battle_animation.active_event
		var actor=ui.game.find_unit(str(event.get("attacker","")))
		if not PartyArt.applies(actor):continue
		var pose=int(ui.combat_poses.get(actor.id,0))
		# A wait can trigger enemy phase and a teammate's counterattack.
		# Attribute observed animation to its actual actor, not the key owner.
		timed_classes[PartyArt.class_key(actor)]=actor.id
		var record={"path":"","clock_ms":Time.get_ticks_msec(),"stage":ui.game.battle_data.code,"turn":ui.game.turn,"actor":actor.id,"class_key":PartyArt.class_key(actor),"pose":pose,"offset":str(ui.combat_offsets.get(actor.id,Vector2.ZERO)),"source_tick":ui.battle_animation.active_tick,"source_variant":ui.battle_animation.active_variant,"contacts":ui.battle_animation.contact_calls,"fixture":false,"layout_errors":ui.layout_errors.duplicate()}
		native_frames.append(record)
		if not ui.layout_errors.is_empty():record_failure("Timed combat text safety")
		var unique=str(ui.game.battle_data.code)+":"+str(actor.id)+":"+str(pose)
		if not seen_poses.has(unique):
			seen_poses[unique]=true
			record.path=review_out+"animation-"+str(animation_shots.size()).pad_zeros(4)+".png"
			viewport.get_texture().get_image().save_png(record.path);animation_shots.append(record)
func write_review():
	super.write_review()
	var path=review_out+"play-checks.json";var report=State.read_json(path)
	var observed={}
	for row in native_frames:observed[row.class_key]=row.actor
	report.round=party_round;report.version=str(ProjectSettings.get_setting("application/config/version"));report.timed_classes=observed
	report.animation_shots=animation_shots;report.native_animation_frames=native_frames
	report.animation_scope="Representative actual actions and counterattacks use full normal-speed native animation; timed_classes is derived from the actual combat-event actors. Historical saves are read only. All choices, movement and victories use ordinary keys and game rules. Other presentation is accelerated."
	if animation_shots.is_empty():report.passed=false;report.failures.append("No complete profession action observed")
	var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()

func plan(unit: Dictionary) -> Dictionary:
	if ui.game.stage_id!=101:return super.plan(unit)
	var best=super.plan(unit)
	var escorts=ui.game.living("player").filter(func(u):return u.get("quest_kind","")=="escort")
	for cell in ui.game.reachable(unit).costs:
		if not ui.game.can_stop(unit,cell):continue
		var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
		for enemy in ui.game.targets(candidate):
			var urgency=0.0
			for npc in escorts:
				var d=distance(State.pos(enemy),State.pos(npc));urgency+=maxf(0.0,12.0-float(d))
				if Rules.can_attack(enemy,d):urgency+=30.0+float(npc.max_hp-npc.hp)*2.0
			var stats=Rules.attack_stats(candidate,enemy,ui.game.terrain_avoid(State.pos(enemy)))
			var score=120.0+minf(stats.damage,enemy.hp)*4.0+urgency*8.0-risk(candidate,cell)*2.0
			if stats.damage>=enemy.hp:score+=100.0
			if score>best.score:best={"kind":"attack","cell":cell,"score":score,"target":str(enemy.id),"spell":-1}
	return best

extends "res://tests/battlefield_redesign_play.gd"
## Actual input/checkpoints in an offscreen viewport. No actor/stat/turn edits.
const SHOTS = "res://reports/playtest-0.3.7/screenshots/"
var feedback_shots: Array = []
var sound_events: Array = []
var live_preview := false
var live_combat := false
var live_reward := false

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1": quit(1); return
	call_deferred("run")

func source_load(path: String) -> void:
	ui.game.save_path=path
	var loaded=ui.game.load_game()
	ui.game.save_path="res://.cache/player-feedback-capture-working.json"
	if not loaded: record_failure("Capture source does not load: "+path); return
	ui.view=ui.game.mode; ui.ui_mode="inspect"; ui.busy=false; ui.batch_running=false; ui._clear_menu(); ui.phase_time=0; ui.notice_time=0
	ui.instant_mode=true; ui.held_direction=Vector2i.ZERO
	if ui.view=="hub":ui.hub_controller.resume()
	if ui.view=="battle":ui._focus_battle(ui.game.cursor,true)

func shot(name: String, source: String) -> void:
	ui.queue_redraw()
	for i in range(4): await process_frame
	await RenderingServer.frame_post_draw
	var path=SHOTS+name+".png"
	viewport.get_texture().get_image().save_png(path)
	feedback_shots.append({"name":name,"path":path,"source":source,"fixture":false,"view":ui.view,"mode":ui.ui_mode,"stage":ui.game.battle_data.get("code",""),"turn":ui.game.turn,"canvas":[viewport.size.x,viewport.size.y],"layout_errors":ui.layout_errors.duplicate(),"text_checks":ui.text_checks.duplicate(true),"presentation":ui.presentation_audit.duplicate(true),"cursor":[ui.game.cursor.x,ui.game.cursor.y],"status_id":ui.status_id})
	print("FEEDBACK_SHOT ",name," ",ui.layout_errors)

func current_stage(code: String) -> void:
	var prefix="res://reports/campaign/" if code.begins_with("M") or code in ["S11","S12"] else "res://reports/chapter2/play/"
	source_load(prefix+"natural-"+code+"-deployment-save.json")
	var target=ui.game.world_node
	key(KEY_S); choose("new:prepare"); await settle(); await go(target)
	key(KEY_Z); choose("new:battle"); await settle()
	while ui.phase_time>0:await process_frame

func live_exchange() -> void:
	var source="res://reports/battlefield-0.3.0/play/ui-0.3.7-round1/ui-0.3.7-round1-M11-field.json"
	source_load(source)
	for turn_index in range(4):
		var actor="";var action={}
		refresh_threats()
		for id in ui.game.party:
			var unit=ui.game.find_unit(str(id))
			if unit.is_empty() or int(unit.hp)<=0 or unit.acted:continue
			var next=plan(unit)
			if next.kind=="attack":actor=str(id);action=next;break
		if actor.is_empty():
			var turn_=ui.game.turn
			for id in ui.game.party.duplicate():
				if ui.game.turn!=turn_:break
				await act(str(id))
			if ui.game.turn==turn_:key(KEY_S);choose("end_turn");await settle()
			continue
		var unit=ui.game.find_unit(actor)
		cursor_to(State.pos(unit));key(KEY_Z);cursor_to(action.cell);key(KEY_Z);await settle()
		if int(action.spell)>=0:choose("magic");choose("spell:"+str(action.spell))
		else:choose("attack")
		for i in range(50):
			if str(ui.target_ids[ui.target_index])==str(action.target):break
			key(KEY_RIGHT)
		ui._focus_battle(ui.game.cursor,true)
		await shot("08-preview-over-cursor",source+"; legal movement and attack target, camera framing only")
		live_preview=true;ui.instant_mode=false;ui.animation_speed=1.0;key(KEY_Z)
		await shot("09-combat-clean-hud",source+"; actual live exchange through confirm input")
		live_combat=ui.view=="combat"
		var deadline=Time.get_ticks_msec()+45000
		while Time.get_ticks_msec()<deadline:
			if ui.view=="reward" and ui.reward_elapsed>=minf(.25,float(ui.reward.get("gain",1))/60.0):
				await shot("10-experience-cells",source+"; actual experience awarded by the live exchange")
				live_reward=true;key(KEY_Z);break
			if ui.view=="plot":key(KEY_Z)
			await process_frame
		if not live_reward:record_failure("Live exchange reward was not captured: "+str(ui.reward)+" view="+ui.view)
		ui.instant_mode=true;await settle()
		key(KEY_S);choose("end_turn");await settle()
		while ui.phase_time>0:await process_frame
		await shot("11-next-turn-protagonist",source+"; next player phase after normal enemy actions")
		if ui.game.cursor!=State.pos(ui.game.find_unit(ui.game.leader_id())):record_failure("New player phase did not focus the protagonist")
		return
	record_failure("No legal live attack found for feedback capture")

func run() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SHOTS))
	review_out="res://.cache/feedback-capture/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(review_out))
	viewport=SubViewport.new();viewport.size=Vector2i(426,240);viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();viewport.add_child(ui);await process_frame;ui.instant_mode=true
	ui.audio.sfx_played.connect(func(name):sound_events.append({"name":name,"view":ui.view,"reward_elapsed":ui.reward_elapsed}))
	source_load("res://reports/campaign/natural-prologue-save.json")
	walk_to(Vector2i(7,3));key(KEY_UP);key(KEY_Z);await settle()
	await shot("01-snow-village-caption","Actual prologue completion through facing interaction and dialogue")
	key(KEY_Z);await shot("02-caption-and-notice","Actual empty-facing confirmation notice in snow village")
	key(KEY_TAB);choose("camp:status:"+str(ui.game.party[0]));key(KEY_RIGHT)
	await shot("03-hub-status-next","Actual hub member menu and right key; own army only")
	key(KEY_X)
	source_load("res://reports/campaign/natural-chapter-end-save.json");key(KEY_Z);choose("new:chapter2");await settle()
	await shot("04-east-caption","Actual second-chapter transition from genuine first-chapter completion")
	await current_stage("M11")
	key(KEY_E);key(KEY_E);await shot("05-ready-ally-cycle","Two E inputs cycle available allies on current M11 deployment")
	key(KEY_TAB);key(KEY_RIGHT);await shot("06-battle-status-next","Right key changes current army member in battle status")
	key(KEY_X)
	var enemy=ui.game.living("enemy").filter(func(u):return int(u.class_id) in [12,13,20])[0]
	cursor_to(State.pos(enemy));ui._focus_battle(ui.game.cursor,true)
	await shot("07-enemy-red-movement","Cursor key hover over archer; actual movement graph, walls and occupants respected")
	await live_exchange()
	var resting=ui.game.living("enemy").filter(func(u):return bool(u.acted))
	if not resting.is_empty():
		cursor_to(State.pos(resting[0]));ui._focus_battle(ui.game.cursor,true)
		await shot("12-enemy-red-grey","Enemy resting state reached through normal phase, not manually greyed")
	await current_stage("F26")
	key(KEY_S);choose("new:prepare");await settle();key(KEY_S);choose("new:camp")
	await shot("13-equipment-menu","Actual world preparation menu with existing inventory")
	choose("camp:roster");choose("camp:status:roan")
	await shot("14-archer-equipment","Actual second-chapter archer equipment from genuine F26 checkpoint")
	key(KEY_X);key(KEY_S);choose("new:camp");choose("new:equipment");key(KEY_Z)
	await shot("15-equipment-help","Equipment explanation reached through preparation menu")
	await settle()
	# Recheck representative states at two additional modern landscape ratios.
	viewport.size=Vector2i(384,240);await process_frame
	source_load("res://reports/campaign/natural-world-start-save.json");key(KEY_Z);choose("new:hub");await settle()
	await shot("16-caption-16-10","Actual snow village entered from world checkpoint at 16:10")
	viewport.size=Vector2i(560,240);await process_frame
	await current_stage("F24");key(KEY_TAB)
	await shot("17-status-ultrawide","Current second-chapter battle status at ultrawide landscape ratio")
	var layout=[]
	for item in feedback_shots:layout.append_array(item.layout_errors)
	var exp_sounds=sound_events.filter(func(e):return e.name=="hp_tick" and e.view=="reward")
	var report={"passed":not abort and layout.is_empty() and live_preview and live_combat and live_reward and not exp_sounds.is_empty(),"scope":"Actual input and checkpoint captures; no position/stat/reward/turn/victory edits. Camera framing and viewport size may differ.","background_guard":true,"visible_windows":false,"shots":feedback_shots,"layout_errors":layout,"live_preview":live_preview,"live_combat":live_combat,"live_reward":live_reward,"reward_sound_events":exp_sounds,"failures":failures}
	var f=FileAccess.open("res://reports/playtest-0.3.7/captures.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("FEEDBACK_CAPTURE ",report.passed," shots ",feedback_shots.size()," layout ",layout)
	ui.queue_free();await process_frame;ui=null;viewport.queue_free();await process_frame;viewport=null
	quit(0 if report.passed else 1)

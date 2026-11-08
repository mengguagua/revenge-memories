extends SceneTree
## Captures the production phone scene, real strike coroutine and actual audio bus.
## A fixture supplies units and a resolved strike, with all journals in temp.
class ObservedGame extends "res://core/game_state.gd":
	var commits := 0
	func commit_strike(event: Dictionary) -> void:
		commits += 1
		super.commit_strike(event)

const SIZE := Vector2i(592, 240)
const CAPTURE_FPS := 60
var phone
var ui
var viewport: SubViewport
var recorder: AudioEffectRecord
var playing := false
var errors: Array[String] = []
var cues: Array = []
var start_us := 0
var out := ""
var records: Array = []

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		push_error("Background guard required")
		quit(1)
		return
	call_deferred("run")

func run() -> void:
	Engine.max_fps = 60
	out = OS.get_environment("REVIEW_CAPTURE_OUT")
	var jobs = JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("REVIEW_CAPTURE_JOBS")))
	if out.is_empty() or not jobs is Array:
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(out)
	viewport = SubViewport.new()
	viewport.size = SIZE * 2
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	phone = load("res://scenes/phone.tscn").instantiate()
	phone.safe_area_override = Rect2(Vector2.ZERO, Vector2(SIZE * 2))
	phone.journal_directory_override = out.path_join("journals")
	viewport.add_child(phone)
	await process_frame
	ui = phone.game_ui
	ui.game = ObservedGame.new()
	ui.game.save_path = out.path_join("fixture.json")
	ui.game.slot_directory = out.path_join("journals")
	ui.game.new_game()
	ui.game.stage_id = 201
	ui.game.battle_data = ui.game.stages[201].duplicate(true)
	ui.game.mode = "battle"
	ui.game.flags.quest = {"objects":{}, "evacuated":[], "freed":[], "burn_streak":0, "reinforced":false, "mid_done":false}
	ui.set_physics_process(false)
	ui.audio.sfx_played.connect(func(key): cues.append([seconds(), key]))
	ui.audio.playback_failed.connect(func(key, reason): errors.append(key+": "+reason))
	var index := AudioServer.bus_count
	AudioServer.add_bus()
	AudioServer.set_bus_name(index, "BattleReviewCapture")
	recorder = AudioEffectRecord.new()
	recorder.format = AudioStreamWAV.FORMAT_16_BITS
	AudioServer.add_bus_effect(index, recorder)
	for child in ui.audio.get_children():
		if child is AudioStreamPlayer:
			child.bus = "BattleReviewCapture"
	for job in jobs:
		if not FileAccess.file_exists(out.path_join(str(job.id)+".json")):
			if job.family == "map":
				await capture_map(job)
			else:
				await capture(job)
	var report := FileAccess.open(out.path_join("run.json"), FileAccess.WRITE)
	report.store_string(JSON.stringify({"records":records, "errors":errors}))
	ui.audio.stop_all()
	phone.queue_free()
	await process_frame
	viewport.queue_free()
	await process_frame
	print("REVIEW_ERRORS ", errors)
	quit(0 if errors.is_empty() else 1)

func setup(job: Dictionary) -> Dictionary:
	ui.battle_animation.reset()
	ui.audio.stop_all()
	ui.game.units = [job.actor.duplicate(true), job.target.duplicate(true)]
	ui.game.story_events.clear()
	ui.game.flags.erase("active_plot")
	ui.game.kills = 0
	ui.game.commits = 0
	ui.view = "combat"
	ui.ui_mode = "inspect"
	ui.busy = true
	ui.batch_running = false
	ui.instant_mode = false
	ui.animation_speed = 1.0
	ui.combat = job.exchange.duplicate(true)
	ui.combat_poses.clear()
	ui.combat_offsets.clear()
	ui.combat_hp.clear()
	ui.combat_fades.clear()
	ui._clear_menu()
	ui.combat_hit_time = 0.0
	ui.combat_hit_id = ""
	ui.combat_message = ""
	ui.combat_shake = 0.0
	ui.combat_wait_accumulated = 0.0
	ui.elapsed = 0.0
	var event: Dictionary = job.event.duplicate(true)
	event.erase("feedback_only")
	ui.battle_animation.active_event = event.duplicate(true)
	for unit in ui.game.units:
		var id := str(unit.id)
		var graphic: Dictionary = ui.battle_animation.sprite(unit)
		ui.combat_poses[id] = int(graphic.sequences.idle[0])
		ui.combat_offsets[id] = Vector2.ZERO
		ui.combat_hp[id] = int(unit.hp)
		ui.combat_fades[id] = 1.0
	phone._sync_controls()
	ui.queue_redraw()
	phone.queue_redraw()
	return event

func seconds() -> float:
	return float(Time.get_ticks_usec() - start_us) / 1000000.0

func strike(event: Dictionary) -> void:
	playing = true
	await ui.battle_animation.play(event)
	playing = false

func map_unit(cid: int, side: String, id: String, at: Array) -> Dictionary:
	var unit: Dictionary = ui.game._initial_character("daan").duplicate(true)
	unit.merge({"id":id,"class_id":cid,"character_id":0,"name_id":0,"side":side,
		"position":at,"acted":false,"hp":30,"max_hp":30,"strength":10,"defence":4,
		"resistance":3,"item_id":0,"magic_flags":255,"no_experience":true},true)
	unit.name_zh=ui.game.catalog.classes[str(cid)].get("name_zh","角色")
	return unit

func map_fixture(job: Dictionary) -> Dictionary:
	ui.battle_animation.reset()
	ui.hero_map_animation.reset()
	ui.map_effects.reset()
	ui.audio.stop_all()
	ui.game.new_game()
	var stage := int(job.get("stage",101))
	ui.game.stage_id=stage
	ui.game.battle_data=ui.game.stages[stage].duplicate(true)
	ui.game.world_node=int(ui.game.battle_data.node)
	ui.game.chapter=int(ui.game.battle_data.chapter)
	ui.game.route=str(ui.game.battle_data.route)
	ui.game.mode="battle"
	ui.game.phase="player"
	ui.game.turn=1
	ui.game.units=[]
	ui.game.story_events.clear()
	ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
	ui.game.ChapterTwo.initialize(ui.game)
	if ui.game.chapter==4:ui.game.ChapterFour.initialize(ui.game)
	ui.view="battle"
	ui.ui_mode="whole_capture"
	ui.busy=true
	ui.notice_time=0.0
	ui.phase_time=0.0
	ui._clear_menu()
	if job.kind == "hero-map":
		var hero: Dictionary
		var ally: Dictionary
		var center: Vector2i
		if job.get("support",false):
			hero=map_unit(17,"player","map_healer",[5,13])
			ally=map_unit(6,"player","map_friend",[7,13])
			ally.hp=8
			center=Vector2i(7,13)
			ui.game.units=[hero,ally,map_unit(14,"enemy","map_enemy",[10,15])]
		else:
			hero=job.hero_data.duplicate(true)
			hero.merge({"side":"player","position":job.hero_at,"acted":false,"no_experience":true},true)
			ui.game.MapSkills.clear(hero)
			if job.advanced:
				ui.game.HeroProfessions.apply(hero)
				hero.hp=hero.max_hp
			if job.bow:hero.item_id=22
			ally=map_unit(6,"player","map_friend",job.friend)
			ui.game.units=[hero,ally]
			for row in job.enemies_data:ui.game.units.append(row.unit.duplicate(true))
			center=Vector2i(job.center[0],job.center[1])
		ui.game.party=[hero.id,ally.id]
		ui.game.selected_id=hero.id
		ui.game.cursor=center
		ui._focus_battle(center,true)
		return ui.game.MapSkills.apply(ui.game,hero.id,center,Vector2i.RIGHT)
	var unit := map_unit(int(job.class_id),str(job.get("unit_side","enemy")),"map_target",[6,13])
	var caster := map_unit(18,"player","map_caster",[4,13])
	ui.game.units=[unit,caster]
	ui.game.party=[caster.id]
	ui.game.selected_id=""
	ui.game.cursor=Vector2i(6,13)
	ui._focus_battle(ui.game.cursor,true)
	if job.get("spawn",false):ui.map_actor_alpha[unit.id]=0.0
	if job.get("disappear",false):unit.hp=0
	return {"target":unit}

func play_map(job: Dictionary, value: Dictionary) -> void:
	playing=true
	match str(job.kind):
		"hero-map":await ui.hero_map_animation.play(value)
		"teleport":await ui.map_effects.teleport(value.target,Vector2i(8,13))
		"quake":
			await ui.map_effects.flash("quake")
			await ui.map_effects.play_program(9,value.target)
		_:
			await ui.map_effects.play_program(int(job.program),value.target)
	if job.get("spawn",false):ui.map_actor_alpha.erase(value.target.id)
	playing=false

func capture_map(job: Dictionary) -> void:
	var value := map_fixture(job)
	if job.kind=="hero-map" and not value.get("valid",false):
		errors.append(str(job.id)+": "+str(value.get("reason","invalid map skill")))
		return
	var frames: Array[PackedByteArray]=[]
	var timestamps: Array[float]=[]
	var contact := -1.0
	var contacts: Array=[]
	var layout: Array[String]=[]
	var played_until := -1.0
	cues.clear()
	recorder.set_recording_active(true)
	start_us=Time.get_ticks_usec()
	await create_timer(.28).timeout
	play_map(job,value)
	while played_until<0.0 or seconds()<played_until+.32:
		await process_frame
		await RenderingServer.frame_post_draw
		var t := seconds()
		if not playing and played_until<0:played_until=t
		if job.kind=="hero-map":
			contacts=ui.hero_map_animation.audit.get("contacts",[]).duplicate()
			if contact<0 and not contacts.is_empty():contact=t
		elif contact<0 and ui.map_effects._active:contact=t
		for message in ui.layout_errors+phone.layout_errors:
			if message not in layout:layout.append(message)
		var image := viewport.get_texture().get_image()
		image.resize(SIZE.x,SIZE.y,Image.INTERPOLATE_NEAREST)
		image.convert(Image.FORMAT_RGB8)
		frames.append(image.get_data())
		timestamps.append(t)
		if t>15.0:
			errors.append(str(job.id)+": map capture timed out")
			break
	recorder.set_recording_active(false)
	var prefix := out.path_join(str(job.id))
	var recording := recorder.get_recording()
	if recording==null or recording.save_to_wav(prefix+".wav")!=OK:
		errors.append(str(job.id)+": no map audio")
	var file := FileAccess.open(prefix+".rgb",FileAccess.WRITE)
	for frame in frames:file.store_buffer(frame)
	file.close()
	var outcomes := {}
	for unit in ui.game.units:
		outcomes[unit.id]=[int(unit.hp),unit.position]
	var summary := {"key":job.id,"title":job.title,"family":"map","source":job.kind,"duration":seconds(),
		"contact":contact,"contacts":contacts.size(),"commits":0,"hp_steps":[],"layout":layout,
		"cues":cues.duplicate(true),"times":timestamps,"view":[SIZE.x,SIZE.y],"map_outcome":outcomes}
	file=FileAccess.open(prefix+".json",FileAccess.WRITE)
	file.store_string(JSON.stringify(summary))
	records.append(summary)
	print("REVIEW ",job.id," ",frames.size()," map frames, contact ",contact,", ",layout)

func capture(job: Dictionary) -> void:
	var event := setup(job)
	var chosen: Dictionary = ui.battle_animation.selection(event)
	var target_id := str(event.defender)
	var last_hp := int(ui.combat_hp[target_id])
	var frames: Array[PackedByteArray] = []
	var timestamps: Array[float] = []
	var hp_steps: Array = []
	var native_visibility: Array = []
	var last_effects: Array = []
	var last_tick := -1
	var first_contact := -1.0
	var layout: Array[String] = []
	var prefix := out.path_join(str(job.id))
	cues.clear()
	recorder.set_recording_active(true)
	start_us = Time.get_ticks_usec()
	await create_timer(.28).timeout
	strike(event)
	while playing or (first_contact >= 0 and seconds() - first_contact < .40):
		await process_frame
		await RenderingServer.frame_post_draw
		var t := seconds()
		if t > 24.0:
			errors.append(str(job.id)+": capture timed out")
			break
		if ui.battle_animation.contact_calls > 0 and first_contact < 0:
			first_contact = t
		var hp := int(ui.combat_hp[target_id])
		if hp != last_hp:
			hp_steps.append([t,hp])
			last_hp = hp
		var anim = ui.battle_animation
		if anim.active_tick >= 0:
			if anim.active_tick < last_tick:
				errors.append(str(job.id)+": attack source jumped backwards")
			last_tick = anim.active_tick
		var visible_effects: Array = []
		if not anim.review_fx.replaces_native():
			for effect in anim.effects:
				if not anim.review_fx.replaces_sprite(str(effect.sprite)):
					visible_effects.append(str(effect.sprite))
		if visible_effects != last_effects:
			native_visibility.append([t,anim.active_tick,visible_effects])
			last_effects = visible_effects
		for message in ui.layout_errors + phone.layout_errors:
			if message not in layout:
				layout.append(message)
		if frames.is_empty() or t - timestamps[-1] >= (0.70 / CAPTURE_FPS):
			var image := viewport.get_texture().get_image()
			image.resize(SIZE.x, SIZE.y, Image.INTERPOLATE_NEAREST)
			image.convert(Image.FORMAT_RGB8)
			frames.append(image.get_data())
			timestamps.append(t)
	recorder.set_recording_active(false)
	var recording := recorder.get_recording()
	if recording == null or recording.save_to_wav(prefix+".wav") != OK:
		errors.append(str(job.id)+": no engine audio")
	var file := FileAccess.open(prefix+".rgb", FileAccess.WRITE)
	for frame in frames:
		file.store_buffer(frame)
	file.close()
	var expected_commits := 0 if event.get("visual_only", false) else 1
	var hp_target := int(ui.game.find_unit(target_id).hp)
	if ui.battle_animation.contact_calls != 1 or ui.game.commits != expected_commits:
		errors.append(str(job.id)+": wrong contact or commit count")
	if not event.get("visual_only", false) and hp_target != int(event.hp_after):
		errors.append(str(job.id)+": wrong target HP")
	var summary := {"key":job.id, "title":job.title, "family":job.family, "source":chosen.get("key",""),
		"duration":seconds(), "contact":first_contact, "contacts":ui.battle_animation.contact_calls,
		"commits":ui.game.commits, "expected_hp":int(event.hp_after), "actual_hp":hp_target,
		"source_hp":int(ui.game.find_unit(str(event.attacker)).hp), "hp_steps":hp_steps, "layout":layout,
		"native_visibility":native_visibility,
		"cues":cues.duplicate(true), "times":timestamps, "view":[SIZE.x,SIZE.y], "event":event}
	file = FileAccess.open(prefix+".json", FileAccess.WRITE)
	file.store_string(JSON.stringify(summary))
	records.append(summary)
	print("REVIEW ", job.id, " ", frames.size(), " frames, contact ", first_contact, ", ", layout)

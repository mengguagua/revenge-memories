extends SceneTree
## A single new decoded recovery frame. No battle/action or prior screen replay.
const State = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-round7-capture-save.json"
var ui
var viewport: SubViewport

func _initialize() -> void:
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE") != "1":
		quit(1)
		return
	call_deferred("run")

func run() -> void:
	viewport = SubViewport.new()
	viewport.size = Vector2i(256,240)
	viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(viewport)
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = "res://reports/round7-late-playthrough-save.json"
	viewport.add_child(ui)
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	if not ui.game.load_game():
		quit(1)
		return
	ui.game.save_path = SAVE
	var caster: Dictionary = ui.game.find_unit("celica")
	var target: Dictionary = ui.game.find_unit("palla")
	ui.view = "combat"
	ui.combat = {"attacker":"celica","defender":"palla","distance":1,"initiative_side":"player","support":true}
	ui.combat_poses.clear()
	ui.combat_offsets.clear()
	ui.combat_fades.clear()
	for unit in [caster,target]:
		ui.combat_poses[str(unit.id)] = int(ui._battle_sprite(unit).sequences.idle[0])
		ui.combat_offsets[str(unit.id)] = Vector2.ZERO
		ui.combat_fades[str(unit.id)] = 1.0
	ui.combat_hp = {"celica":19,"palla":36}
	ui.combat_message = "恢复"
	var event := {"attacker":"celica","defender":"palla","weapon_index":40,"visual_only":true}
	if not ui.battle_animation.show_frame(event,100):
		quit(1)
		return
	ui.queue_redraw()
	for _i in range(3): await process_frame
	RenderingServer.force_draw(false)
	var pixels: Image = viewport.get_texture().get_image()
	var path := "res://reports/screenshots/round7-celica-recovery.png"
	var error := pixels.save_png(path)
	var file := FileAccess.open("res://reports/round7-recovery-visual-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"path":path,"pixels":[256,240],"bytes":FileAccess.get_file_as_bytes(path).size(),"safe_area_errors":ui.layout_errors.duplicate(),
		"variant":ui.battle_animation.active_variant,"source_tick":100,"source_contact_tick":89,"sprite_count":ui.battle_animation.effects.size(),
		"background_guard":true,"visible_window":false,"user_save_accessed":false,"screenshots":1,"prior_screens_recaptured":0,
		"scope":"One deterministic source frame validates new caster pose/effect and existing panels; actual spell input/settlement verified separately."},"  ")+"\n")
	file.close()
	var ok: bool = error == OK and ui.layout_errors.is_empty()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	print("ROUND7 RECOVERY CAPTURE:1 new screen, safe=",ok)
	quit(0 if ok else 1)

extends SceneTree
## One new real-input heal at the preserved map47 checkpoint, no battle replay.
const State = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-round7-recovery-save.json"
const CHECKPOINT := "res://reports/round7-late-playthrough-save.json"
var ui
var checks := 0
var failures: Array[String] = []
var selected_variant := ""
var referenced_sprites: Dictionary = {}

func _initialize() -> void: call_deferred("run")

func check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures.append(message)
		push_error(message)

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	ui._input(event)

func cursor_to(at: Vector2i) -> void:
	var steps := 0
	while ui.game.cursor != at and steps < 100:
		steps += 1
		if ui.game.cursor.x != at.x: key(KEY_RIGHT if ui.game.cursor.x < at.x else KEY_LEFT)
		else: key(KEY_DOWN if ui.game.cursor.y < at.y else KEY_UP)
	check(ui.game.cursor == at, "Real keys reach " + str(at))

func choose(action: String) -> void:
	check(ui.menu_actions.has(action), "Actual menu offers " + action)
	if not ui.menu_actions.has(action): return
	var steps := 0
	while str(ui.menu_actions[ui.menu_selected]) != action and steps < 30:
		key(KEY_DOWN)
		steps += 1
	key(KEY_Z)

func settle() -> void:
	var frames := 0
	while (ui.busy or ui.batch_running) and frames < 2000:
		frames += 1
		await process_frame
	check(not ui.busy and not ui.batch_running, "Timed operation releases input owner")

func verify_variants() -> void:
	var source: Dictionary = ui.battle_animation._source()
	var body_key: String = ui.graphics.battle.class_11_ally.spell_body_variants["40"]
	var body: Dictionary = ui.graphics.battle[body_key]
	check(body.recovery_body and body.frames == 9 and ResourceLoader.exists(body.path), "Complete cumulative body atlas loads nine original poses")
	for formation in ["", "_far_ally", "_far_enemy"]:
		for heavy in ["", "_vs_heavy"]:
			var id: String = "class_11_ally_item_40" + formation + heavy
			var variant: Dictionary = source.variants.get(id,{})
			check(not variant.is_empty(), "New source layout exists: " + id)
			if variant.is_empty(): continue
			check(variant.source_class_id == 11 and variant.source_program_id == 29 and variant.source_effect_id == 5 and variant.source_item_id == 40, "Recovery uses priestess29/white5, not another class or Fire")
			check(variant.contact_count == 1 and variant.contact_tick == 89 and variant.frames.size() == 152, "New layout retains original contact and duration")
			var frame_ok := true
			for frame in variant.frames:
				if int(frame.frame) < 0 or int(frame.frame) >= int(body.frames): frame_ok = false
				for effect in frame.effects: referenced_sprites[str(effect.sprite)] = true
			check(frame_ok, "Every source pose is inside priestess sheet")
	for sprite_id in referenced_sprites:
		check(ResourceLoader.exists(str(source.sprites[sprite_id].path)), "Existing effect sprite loads: " + sprite_id)
	var caster: Dictionary = ui.game.find_unit("celica").duplicate(true)
	for promoted in [false,true]:
		caster.promoted = promoted
		check(ui.battle_animation.sprite(caster).spell_variants.get("40") == "class_11_ally_item_40", "Normal/promoted portrait body retains exact recovery mapping")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = CHECKPOINT
	root.add_child(ui)
	await process_frame
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	check(ui.game.load_game(), "Read only the preserved isolated retry checkpoint")
	ui.game.save_path = SAVE
	ui.animation_speed = 100.0
	ui.instant_mode = false
	ui._begin_existing_battle()
	await settle()
	check(ui.game.stage_id == 47 and ui.game.turn == 1, "Preserved playable checkpoint avoids earlier battle replay")
	verify_variants()
	var caster: Dictionary = ui.game.find_unit("celica")
	var target: Dictionary = ui.game.find_unit("palla")
	# Isolate a wound from the recorded previous battle; this is not a new win.
	var play: Dictionary = State.read_json("res://reports/round7-late-playthrough.json")
	for unit in play.battles[2].final_players:
		if unit.id == "palla": target.hp = int(unit.hp)
	var hp_before := int(target.hp)
	var caster_before := int(caster.hp)
	var next := State.pos(caster)
	var found := false
	for cell in ui.game.reachable(caster).costs:
		if ui.game.can_stop(caster, cell) and absi(cell.x - int(target.position[0])) + absi(cell.y - int(target.position[1])) == 1:
			next = cell
			found = true
			break
	check(found and hp_before < int(target.max_hp), "Preserved source map offers legal adjacent recovery and a recorded wound")
	if found:
		cursor_to(State.pos(caster))
		key(KEY_Z)
		cursor_to(next)
		key(KEY_Z)
		await settle()
		choose("magic")
		choose("spell:40")
		var steps := 0
		while not ui.target_ids.is_empty() and str(ui.target_ids[ui.target_index]) != "palla" and steps < 20:
			key(KEY_RIGHT)
			steps += 1
		check(not ui.target_ids.is_empty() and str(ui.target_ids[ui.target_index]) == "palla", "Displayed recovery recipient is actual Palla")
		key(KEY_Z)
		selected_variant = ui.battle_animation.active_variant
		await settle()
		check(selected_variant == "class_11_ally_item_40_vs_heavy", "Native input selects correct caster and mounted-recipient layout")
		check(target.hp == mini(int(target.max_hp),hp_before + int(caster.strength)), "Real spell heals exactly once")
		check(caster.hp == caster_before - ui.Items.cost(40) and caster.acted and not target.acted, "Recovery spends one caster cost/action and leaves recipient available")
		check(ui.battle_animation.contact_calls == 1 and ui.battle_animation.missing_animations.is_empty(), "Original playback has one contact and no missing fallback")
		check(ui.battle_animation.sprite(caster).recovery_body, "Active caster uses the complete original recovery body")
		check(ui.view == "battle" and ui.ui_mode == "inspect" and ui.game.phase == "player", "Completed action returns to continuing player input")
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets.celica == Vector2.ZERO, "Playback restores effects and actor position")
		key(KEY_S)
		check(ui.menu_context == "system", "System menu still works after recovery")
		key(KEY_X)
		cursor_to(State.pos(target))
		key(KEY_Z)
		check(ui.ui_mode == "move", "Recipient remains selectable after heal")
		key(KEY_X)
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var file := FileAccess.open("res://reports/round7-recovery-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks":checks,"failures":failures,"selected_variant":selected_variant,"referenced_existing_sprites":referenced_sprites.size(),
		"scope":"Six new layouts and one real-input recovery at read-only map47 retry checkpoint.","earlier_battles_replayed":[],"user_save_accessed":false,"visible_window":false,
		"limits":"One wound checkpoint isolates the previously missing action; no whole-campaign regression."},"  ")+"\n")
	file.close()
	print("ROUND7 RECOVERY: ",checks," checks, ",failures.size()," failures")
	quit(0 if failures.is_empty() else 1)

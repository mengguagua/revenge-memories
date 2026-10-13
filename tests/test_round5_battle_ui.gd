extends SceneTree
## Actual Main input on source maps. Learned Warp and wounded-HP checkpoints
## isolate UI choices; they do not claim natural campaign leveling or victories.
const State = preload("res://core/game_state.gd")
const Items = preload("res://core/item_rules.gd")
const Progression = preload("res://core/unit_progression.gd")
const SAVE := "res://reports/test-round5-battle-ui-save.json"
var ui
var checks := 0
var failures: Array[String] = []
var scenarios: Array[String] = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	event.pressed = false
	ui._input(event)

func click(point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.position = point
	ui._input(event)

func cursor_to(at: Vector2i) -> void:
	var steps := 0
	while ui.game.cursor != at and steps < 100:
		steps += 1
		if ui.game.cursor.x != at.x: key(KEY_RIGHT if ui.game.cursor.x < at.x else KEY_LEFT)
		else: key(KEY_DOWN if ui.game.cursor.y < at.y else KEY_UP)
	check(ui.game.cursor == at, "Real directional keys reach requested source-map cursor")

func choose(action: String, mouse: bool = false) -> void:
	check(ui.menu_actions.has(action), "Rendered action has matching handler: " + action)
	if not ui.menu_actions.has(action): return
	var index: int = ui.menu_actions.find(action)
	if mouse:
		var rect: Rect2 = ui._menu_rect()
		click(rect.position + Vector2(40, 20 + 16 * (index - ui.menu_scroll)))
	else:
		while ui.menu_selected != index: key(KEY_DOWN)
		key(KEY_Z)

func setup() -> void:
	ui.game.new_game()
	for id in ["lukas", "silque", "gray"]: ui.game.recruit(id)
	ui.game.roster.silque = Progression.learn_spells(ui.game.roster.silque, 7).unit
	ui.game.give_item(57)
	ui.game.world_node = 1
	ui.game.previous_world_node = 49
	ui.game.route_positions.alm = 1
	ui.instant_mode = true
	ui.busy = false
	ui.batch_running = false
	ui._enter_battle(1)
	ui.phase_time = 0
	ui.game.story_events.clear()
	ui._clear_menu()
	ui.ui_mode = "inspect"
	ui.held_direction = Vector2i.ZERO
	check(ui.view == "battle" and ui.game.mode == "battle", "Actual source stage 1 opens interactive battle")
	check(Items.spells(ui.game.find_unit("silque")).has(43), "Source training table supplies learned Warp checkpoint")

func select_and_move(id: String, destination: Vector2i) -> Vector2i:
	var unit: Dictionary = ui.game.find_unit(id)
	var origin: Vector2i = State.pos(unit)
	cursor_to(origin)
	key(KEY_Z)
	check(ui.ui_mode == "move" and ui.game.selected_id == id, "Confirm selects actual source unit " + id)
	cursor_to(destination)
	key(KEY_Z)
	check(State.pos(unit) == destination and ui.menu_context == "unit_action", "Source movement reaches native action menu")
	return origin

func test_status_intent() -> void:
	setup()
	for id in ["silque", "lukas", str(ui.game.living("enemy")[0].id)]:
		cursor_to(State.pos(ui.game.find_unit(id)))
		key(KEY_S)
		choose("roster")
		check(ui.ui_mode == "status" and ui.status_id == id, "System character-status follows focused unit " + id)
		key(KEY_X)
		check(ui.ui_mode == "inspect" and ui.menu_items.is_empty(), "Status cancel returns to the same source-map focus")
		key(KEY_TAB)
		check(ui.ui_mode == "status" and ui.status_id == id, "Status shortcut and system menu identify the same unit " + id)
		key(KEY_Z)
	cursor_to(Vector2i(0, 0))
	key(KEY_S)
	choose("roster", true)
	check(ui.ui_mode == "status" and ui.status_id == ui.game.leader_id(), "Empty-cell status falls back to this route's leader")
	key(KEY_X)
	scenarios.append("Source battle system/status label -> focused ally/enemy data; Tab matches; empty-cell fallback")

func test_exchange_and_cancel() -> void:
	setup()
	var origin := select_and_move("alm", Vector2i(5, 7))
	choose("exchange", true)
	check(ui.menu_context == "exchange", "Mouse action selection opens actual adjacent exchange list")
	var before: String = JSON.stringify(ui.game.units)
	key(KEY_X)
	check(ui.menu_context == "unit_action" and JSON.stringify(ui.game.units) == before, "Exchange cancellation preserves all actual units and held items")
	key(KEY_X)
	check(ui.ui_mode == "inspect" and State.pos(ui.game.find_unit("alm")) == origin, "Movement cancellation returns exact source origin")
	check(not ui.game.find_unit("alm").acted and ui.game.selected_id.is_empty(), "Cancelled exchange/movement spends no action and releases selection")
	select_and_move("alm", Vector2i(5, 7))
	choose("exchange", true)
	choose("exchange:lukas", true)
	check(ui.game.find_unit("alm").item_id == 0 and ui.game.find_unit("lukas").item_id == 57, "Actual selected recipient receives exactly the displayed source item")
	check(ui.game.find_unit("alm").acted and not ui.game.find_unit("lukas").acted, "Exchange spends only selected source unit's action")
	check(ui.ui_mode == "inspect" and not ui.busy and ui.game.selected_id.is_empty(), "Completed exchange releases keyboard and pointer input")
	key(KEY_S)
	choose("save")
	check(ui.notice == "进度已保存", "Actual system save succeeds after exchanged-item action")
	ui._show_title()
	ui.title_menu = true
	ui.title_selected = 1
	key(KEY_Z)
	check(ui.view == "battle" and ui.game.find_unit("lukas").item_id == 57, "Title continue preserves the recipient and committed exchange")
	check(ui.game.find_unit("alm").acted and ui.ui_mode == "inspect", "Title continue restores committed action and selectable map state")
	scenarios.append("Keyboard move -> mouse exchange list/recipient -> action settlement -> actual save/title continue")

func test_warp_targets() -> void:
	setup()
	var caster: Dictionary = ui.game.find_unit("silque")
	var origin := select_and_move("silque", Vector2i(5, 7))
	choose("magic")
	choose("spell:43")
	check(ui.ui_mode == "support_target" and not ui.target_ids.is_empty(), "Warp first asks for an adjacent source ally")
	var target_id: String = str(ui.target_ids[0])
	var target: Dictionary = ui.game.find_unit(target_id)
	var target_origin := State.pos(target)
	var before_hp: int = caster.hp
	check(ui.target_ids.size() >= 2, "Actual adjacent formation offers distinct Warp recipients")
	var second_id: String = str(ui.target_ids[1]) if ui.target_ids.size() > 1 else target_id
	key(KEY_DOWN)
	check(str(ui.target_ids[ui.target_index]) == second_id and ui.game.cursor == State.pos(ui.game.find_unit(second_id)), "Directional recipient choice keeps selected ID and map focus aligned")
	click(ui._battle_cell_screen(State.pos(caster)) + Vector2(8, 8))
	check(ui.ui_mode == "support_target" and caster.hp == before_hp, "Pointer click on ineligible caster cannot confirm a Warp recipient")
	key(KEY_Z)
	check(ui.ui_mode == "warp" and ui.support_target == second_id, "Confirming displayed ally opens destination choice for that exact ally")
	ui.queue_redraw()
	await process_frame
	await process_frame
	var recipient_instruction := "传送" + str(ui.game.find_unit(second_id).name_zh) + "至选定格"
	check(ui.text_checks.any(func(entry): return str(entry.text) == recipient_instruction), "Rendered Warp destination instruction retains the confirmed recipient name")
	key(KEY_X)
	check(ui.menu_context == "unit_action" and caster.hp == before_hp and not caster.acted, "Cancelling destination never charges HP or spends caster action")
	key(KEY_X)
	check(State.pos(caster) == origin and State.pos(target) == target_origin, "Full Warp cancellation restores caster and preserves chosen ally")
	select_and_move("silque", Vector2i(5, 7))
	choose("magic", true)
	choose("spell:43", true)
	# Pointer confirms an eligible ally by map position, through the native input.
	click(ui._battle_cell_screen(target_origin) + Vector2(8, 8))
	check(ui.ui_mode == "warp" and ui.support_target == target_id, "Pointer target selects the ally under the source-map cursor")
	# An occupied destination must be recoverable, never consume an action.
	cursor_to(State.pos(caster))
	key(KEY_Z)
	check(ui.menu_context == "unit_action" and caster.hp == before_hp and not caster.acted, "Invalid occupied landing returns to action menu without mutation")
	choose("magic")
	choose("spell:43")
	while str(ui.target_ids[ui.target_index]) != target_id: key(KEY_DOWN)
	key(KEY_Z)
	var destination := Vector2i(-1, -1)
	for y in range(2, int(ui.game.battle_data.map.height) - 2):
		for x in range(2, int(ui.game.battle_data.map.width) - 2):
			var at := Vector2i(x, y)
			if ui.game.can_stop(target, at) and ui.game.movement_cost(target, at) < 255 and ui.game.unit_at(at).is_empty():
				destination = at
				break
		if destination.x >= 0: break
	check(destination.x >= 0, "Original source map provides a legal empty Warp landing")
	cursor_to(destination)
	key(KEY_Z)
	check(State.pos(target) == destination and caster.hp == before_hp - Items.cost(43), "Displayed ally reaches exactly confirmed destination and pays native HP cost once")
	check(caster.acted and not target.acted and ui.game.selected_id.is_empty(), "Warp consumes caster action while transported ally stays actionable")
	check(ui.view == "battle" and ui.ui_mode == "inspect" and not ui.busy, "Native Warp feedback returns to actionable battle")
	ui._show_title()
	ui.title_menu = true
	ui.title_selected = 1
	key(KEY_Z)
	check(ui.view == "battle" and State.pos(ui.game.find_unit(target_id)) == destination, "Title continue retains actual Warp destination")
	check(ui.game.find_unit("silque").acted and ui.game.find_unit("silque").hp == before_hp - Items.cost(43), "Title continue retains one Warp cost/action settlement")
	scenarios.append("Source learned-Warp checkpoint -> ally/destination choice/cancel -> occupied rejection -> exact landing -> title continue")

func test_attack_target_confirmation() -> void:
	setup()
	var attacker: Dictionary = ui.game.find_unit("alm")
	var origin: Vector2i = State.pos(attacker)
	var destination := Vector2i(-1, -1)
	for cell in ui.game.reachable(attacker).costs:
		if not ui.game.can_stop(attacker, cell): continue
		var candidate := attacker.duplicate(true)
		candidate.position = [cell.x, cell.y]
		if not ui.game.targets(candidate).is_empty():
			destination = cell
			break
	check(destination.x >= 0, "Original battle contains a reachable native attack target")
	if destination.x < 0: return
	select_and_move("alm", destination)
	choose("attack")
	check(ui.ui_mode == "target" and ui.target_ids.size() > 0, "Attack label opens target preview before commitment")
	var target: Dictionary = ui.game.find_unit(str(ui.target_ids[ui.target_index]))
	var target_hp: int = target.hp
	key(KEY_X)
	check(ui.menu_context == "unit_action" and target.hp == target_hp and not attacker.acted, "Preview cancel leaves damage/action uncommitted")
	key(KEY_X)
	check(State.pos(attacker) == origin, "Attack preview cancellation restores native movement origin")
	select_and_move("alm", destination)
	choose("attack", true)
	var confirmed: String = str(ui.target_ids[ui.target_index])
	click(ui._battle_cell_screen(State.pos(ui.game.find_unit(confirmed))) + Vector2(8, 8))
	check(ui.game.find_unit("alm").acted and ui.game.selected_id.is_empty(), "Pointer confirmation commits selected attacker exactly once")
	check(ui.game.battle_outcome.is_empty() and ui.view in ["battle", "reward"], "Actual ordinary source combat leaves a continuing battle/reward")
	if ui.view == "reward": key(KEY_Z)
	check(ui.view == "battle" and ui.ui_mode == "inspect" and not ui.busy, "Ordinary combat/reward completion releases battle interaction")
	scenarios.append("Actual source movement/attack preview -> cancel rollback; pointer target confirmation -> native combat/reward")

func setup_final(prepared: bool = false) -> void:
	ui.game.new_game()
	for transition in [1, 2, 3, 4]:
		check(ui.game.next_chapter(transition), "Final milestone follows source chapter transition %d" % transition)
	ui.game.world_node = 78
	ui.game.route_positions.alm = 78
	ui.game.previous_world_node = 42
	ui.game.mode = "hub"
	ui.game.hub_id = 37
	ui.game.hub_position = Vector2i(11, 23)
	if prepared: ui.game.roster.alm.item_id = 17
	ui.game.apply_hub_flag(82)
	check(ui.game.enter_dungeon_battle(22), "Legacy final checkpoint reconstructs original source encounter 22")
	ui.instant_mode = true
	ui.busy = false
	ui.batch_running = false
	ui.result_sequence_running = false
	ui._begin_existing_battle()
	ui.phase_time = 0
	ui.game.story_events.clear()
	check(ui.view == "battle" and ui.game.stage_id == 62 and ui.game.flags.get("final_parties_merged", false), "Final checkpoint has actual merged-route deployment and battle UI")
	check(ui.game.party == ["alm"] and ui.game.parties.celica == ["celica"] and ui.game.living("player").size() == 2, "Optional recruitments remain skipped while original final merge deploys both route leaders")

func continue_title() -> void:
	ui._show_title()
	ui.title_menu = true
	ui.title_selected = 1
	key(KEY_Z)
	await process_frame

func test_old_final_recovery() -> void:
	for defeat in [false, true]:
		setup_final()
		check(ui.game.can_return_to_final_preparation(), "Unprepared source final checkpoint qualifies for targeted rescue")
		if defeat:
			ui.game.commit_strike({"attacker": ui.game.living("enemy")[0].id, "defender": "alm", "hp_after": 0})
			check(ui.game.battle_outcome == "defeat", "Real leader death records final battle defeat")
			ui._show_result()
		check(ui.game.save_game(), "Unprepared old final battle/defeat writes isolated production checkpoint")
		await continue_title()
		check(ui.view == ("defeat" if defeat else "battle") and ui.game.can_return_to_final_preparation(), "Actual title continue restores old final checkpoint and recovery eligibility")
		if defeat: key(KEY_Z)
		else: key(KEY_S)
		check(ui.menu_actions.has("final_prepare"), "Battle system/defeat result exposes targeted return-to-preparation action")
		check(ui.menu_items[ui.menu_actions.find("final_prepare")] == "返回准备（重置本战）", "Recovery label clearly states this battle will be reset")
		choose("final_prepare", defeat)
		check(ui.view == "hub" and ui.game.mode == "hub" and ui.game.hub_id == 37 and ui.game.hub_position == Vector2i(11, 25), "Real selected recovery action opens valid original altar preparation side")
		check(ui.game.units.is_empty() and ui.game.battle_start_snapshot.is_empty() and not ui.game.flags.get("final_parties_merged", false), "Recovery UI releases stale battle transaction and merged-route state")
		check(not ui.game.roster.alm.dead and int(ui.game.roster.alm.hp) > 0, "Recovery restores opening leader health for both battle and defeat checkpoint")
		check(not ui.busy and not ui.batch_running and ui.menu_items.is_empty(), "Recovery menu completion releases normal exploration input")
		key(KEY_LEFT)
		check(ui.game.hub_position == Vector2i(10, 25) and ui.view == "hub", "First real keyboard step exits preparation landing without final-trigger loop")
		check(ui.game.save_game(), "Recovered playable hub position writes a valid checkpoint")
		await continue_title()
		check(ui.view == "hub" and ui.game.hub_id == 37 and ui.game.hub_position == Vector2i(10, 25), "Title continue resumes actual recovered hub and first movement")
		key(KEY_RIGHT)
		check(ui.game.hub_position == Vector2i(11, 25) and ui.view == "hub", "Recovered hub remains interactive after another production save/load")
	setup_final(true)
	check(not ui.game.can_return_to_final_preparation(), "Prepared source final army keeps normal source commitment")
	key(KEY_S)
	check(not ui.menu_actions.has("final_prepare"), "Prepared final system menu does not offer old-save rescue")
	key(KEY_X)
	ui.game.commit_strike({"attacker": ui.game.living("enemy")[0].id, "defender": "alm", "hp_after": 0})
	ui._show_result()
	key(KEY_Z)
	check(not ui.menu_actions.has("final_prepare") and ui.menu_actions.has("retry"), "Prepared final defeat retains normal retry and does not enable special rollback")
	scenarios.append("Old unprepared final battle/defeat save -> actual title continue -> labelled system/result recovery -> legal hub37 first step -> save/title continue; prepared final keeps normal retry")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	root.add_child(ui)
	await process_frame
	ui.set_process(false)
	ui.set_physics_process(false)
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	test_status_intent()
	test_exchange_and_cancel()
	await test_warp_targets()
	test_attack_target_confirmation()
	await test_old_final_recovery()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp"]: DirAccess.remove_absolute(SAVE + suffix)
	var report := {"checks": checks, "failure_count": failures.size(), "failures": failures, "scenarios": scenarios,
		"scope": "Real Main key/pointer input and original battles 1/62, native action menus/combat/support/exchange, rendered Warp recipient text, production save/title continue and old-final preparation recovery UI.",
		"limits": "Instant animation timing; source-learned Warp and chapter milestone checkpoints. No natural full-campaign playthrough or pixel inspection.",
		"user_save_accessed": false, "visible_window_created": false}
	var file := FileAccess.open("res://reports/round5-battle-ui-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	print("ROUND 5 BATTLE UI: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

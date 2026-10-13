extends SceneTree
## Source-script50 handoff and legitimate retreat/retry checkpoints.
## Late-game positions are source milestones, not claimed natural victories.
const State = preload("res://core/game_state.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Validator = preload("res://core/campaign_save_validation.gd")
const SAVE := "res://reports/test-round4-route-context-save.json"
var checks := 0
var failures: Array[String] = []
var ui

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func fresh(chapter: int = 3):
	var game = State.new()
	game.save_path = SAVE
	game.new_game()
	game.recruit("lukas")
	for transition in range(1, chapter):
		check(game.next_chapter(transition), "Source chapter milestone initializes route context")
		if transition == 1: game.recruit("mae")
	game.mode = "world"
	return game

func run() -> void:
	_test_retreat_and_retry()
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	ui.instant_mode = true
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.set_process(false)
	ui.set_physics_process(false)
	_test_second_capture_handoff()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	for suffix in ["", ".tmp", ".bak"]: DirAccess.remove_absolute(SAVE + suffix)
	var file := FileAccess.open("res://reports/round4-route-context-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"checks": checks, "failures": failures,
		"scope": "Actual player retreat, known self-origin suspend/load/route roundtrip, casualty retry and snapshot origin; source bank013 L0DB8E3 script50 through the real NPC keyboard controller, automatic capture handoff and reload; typed optional route metadata.",
		"limits": "Late-game checkpoint positions are source-derived fixtures. No natural late-game victory claim or real user save access."}, "\t") + "\n")
	print("ROUND4 ROUTE CONTEXT: %d checks, %d failures" % [checks, failures.size()])
	quit(0 if failures.is_empty() else 1)

func _test_retreat_and_retry() -> void:
	var game = fresh()
	check(game.travel_to(16) and game.travel_to(17), "Actual chapter3 travel enters occupied road17")
	game.rng_state = 201
	check(game.start_battle(17) and Inventory.refresh_retreat(game, 0), "Source roll0 permits native player retreat")
	check(Inventory.retreat(game) and game.world_node == 16 and game.previous_world_node == 16, "Actual retreat produces a legitimate self-origin at road16")
	check(game.save_game(), "Legitimate self-origin checkpoint saves")
	var resumed = State.new()
	resumed.save_path = SAVE
	check(resumed.load_game() and resumed.previous_world_node == 16, "Load preserves known self-origin instead of inferring a false road")
	check(not resumed.flags.get("world_route_approach_recovered_alm", false), "Known retreat origin is not classified as legacy recovery")
	check(resumed.switch_route() and resumed.travel_to(19) and resumed.switch_route(), "Actual other-route travel and return remains available")
	check(resumed.world_node == 16 and resumed.previous_world_node == 16 and resumed.world_neighbors().has(17), "Route roundtrip preserves self-origin and next battle road")
	check(resumed.travel_to(17) and resumed.start_battle(17), "Retreated party can begin the same encounter again")
	check(resumed.battle_start_snapshot.previous_world_node == 16, "Battle snapshot stores its actual road16 origin")
	resumed.commit_strike({"attacker": resumed.living("enemy")[0].id, "defender": "alm", "hp_after": 0})
	check(resumed.battle_outcome == "defeat" and resumed.save_game(), "Actual leader casualty checkpoint saves")
	check(resumed.load_game() and resumed.retry_battle() and resumed.select_unit("alm"), "Saved casualty retry restores actionable leader")
	check(resumed.previous_world_node == 16 and Inventory.retreat_destination(resumed) == 16, "Retry restores the battle origin and source retreat road")
	var checkpoint: Dictionary = State.read_json(SAVE)
	check(Validator.valid(resumed, checkpoint), "New route metadata passes production preflight")
	var damaged := checkpoint.duplicate(true)
	damaged.flags.world_route_previous_nodes = []
	check(not Validator.valid(resumed, damaged), "Malformed route-history type is refused before load")
	damaged = checkpoint.duplicate(true)
	damaged.flags.world_route_encounters = {"alm": {"inventory_enemy_initiated": "yes"}}
	check(not Validator.valid(resumed, damaged), "Malformed per-route initiative type is refused before load")

func _test_second_capture_handoff() -> void:
	ui.game = fresh(5)
	ui.hub_controller.game = ui.game
	# Source late-game checkpoint: Alm at occupied Rigel forest42 from41,
	# Celica at the final altar48 from47, before final parties have merged.
	ui.game.world_node = 42
	ui.game.previous_world_node = 41
	ui.game.route_positions.alm = 42
	ui.game.remember_world_approach()
	check(ui.game.switch_route(), "Source chapter5 milestone still permits the independent Celica route")
	ui.game.world_node = 48
	ui.game.previous_world_node = 47
	ui.game.route_positions.celica = 48
	check(ui.hub_controller.enter(43, Vector2i(14, 4)), "Actual source altar43 room loads")
	ui.hub_controller.facing = Vector2i.UP
	check(ui.game.hub_script(2) == 50, "Source actor2 exposes L0DB8E3 capture script50")
	ui._accept()
	check(ui.view == "hub_dialogue" and ui.hub_controller.script_id == 50, "Native confirm talks to the facing altar actor and starts script50")
	var pages := 0
	while ui.view == "hub_dialogue" and pages < 100:
		ui.hub_controller.reveal = 10000
		ui._accept()
		pages += 1
	check(pages < 100 and ui.view == "world" and not ui.busy, "Source capture VM finishes with world controls")
	check(ui.game.route == "alm" and ui.game.world_node == 42 and ui.game.previous_world_node == 41, "Special4 restores Alm's original forest entrance instead of Celica's road47")
	check(ui.game.flags.get("source_flag_74", false) and ui.game.flags.get("celica_captive", false), "Source script50 capture flags still settle")
	check(ui.game.world_neighbors().has(41) and not ui.game.can_switch_route(), "Captured-route handoff retains Alm's legal exit and source party lock")
	var resumed = State.new()
	resumed.save_path = SAVE
	check(resumed.load_game() and resumed.route == "alm" and resumed.previous_world_node == 41, "Actual VM autosave reloads with Alm's correct origin")
	check(resumed.start_battle(42) and Inventory.retreat_destination(resumed) == 41, "Handoff checkpoint continues into native battle with correct retreat destination")

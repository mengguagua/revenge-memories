extends SceneTree
## Bounded legitimate checkpoint matrix: source milestones, production saves,
## then actual title-continue/retry/action. Never reads the user's save.
const State = preload("res://core/game_state.gd")
const Validator = preload("res://core/campaign_save_validation.gd")
const SAVE := "res://reports/test-round4-resume-save.json"
var scene
var checks := 0
var failures: Array[String] = []
var scenarios: Array[String] = []

func _initialize() -> void: call_deferred("run")

func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok:
		failures.append(label)
		push_error(label)

func fresh():
	var game = State.new()
	game.save_path = SAVE
	game.new_game()
	game.recruit("lukas")
	return game

func advance(game, chapter: int) -> void:
	for transition in range(1, chapter):
		check(game.next_chapter(transition), "source chapter transition %d" % transition)
		if transition == 1: game.recruit("mae")
	if chapter >= 3 and game.route != "alm": check(game.switch_route(), "milestone restores Alm route")

func loaded(game, label: String):
	check(game.save_game(), label + " production checkpoint writes")
	check(Validator.valid(game, State.read_json(SAVE)), label + " legitimate source state passes preflight")
	var next = State.new()
	next.save_path = SAVE
	check(next.load_game(), label + " production checkpoint loads")
	return next

func new_scene() -> void:
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
		await process_frame
	scene = load("res://scenes/main.tscn").instantiate()
	scene.game.save_path = SAVE
	scene.instant_mode = true
	root.add_child(scene)
	await process_frame
	scene.audio.set_music_enabled(false)
	scene.audio.set_sfx_enabled(false)
	scene.set_process(false)
	scene.set_physics_process(false)

func continue_title() -> void:
	scene._show_title()
	scene.title_menu = true
	scene.title_selected = 1
	scene._accept()
	await process_frame

func run() -> void:
	_test_chapter_milestones()
	_test_battle_checkpoints()
	_test_casualties_and_npcs()
	_test_full_alliance_checkpoint()
	_test_legacy_retry()
	await _test_legacy_title_continue()
	if is_instance_valid(scene):
		scene.audio.stop_all()
		scene.queue_free()
		await process_frame
	for suffix in ["", ".tmp", ".v1.bak", ".v2.bak"]:
		DirAccess.remove_absolute(SAVE + suffix)
	var report := {"checks": checks, "failures": failures, "scenarios": scenarios,
		"scope": "bounded legitimate chapter/hub/world/battle/defeat/final-victory checkpoints; production save/load; historical v2 first/second-battle structure then retry/resave; actual title-continue and wait",
		"issues_observed_before_fix": [],
		"limits": "source-derived milestone fixtures, not natural full-campaign playthroughs; no graphics; no real user save read or written"}
	var file := FileAccess.open("res://reports/round4-resume-verification.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	print("ROUND 4 RESUME: %d checks, %d failures" % [checks, failures.size()])
	await create_timer(0.1).timeout
	quit(0 if failures.is_empty() else 1)

func _test_chapter_milestones() -> void:
	var game = fresh()
	for transition in [1, 2, 3, 4]:
		check(game.next_chapter(transition), "chapter milestone %d follows source transition" % transition)
		if transition == 1: game.recruit("mae")
		var next = loaded(game, "chapter %d hub" % game.chapter)
		check(next.chapter == game.chapter and next.party == game.party and next.hub_id == game.hub_id, "chapter checkpoint retains active route and source room")
		check(next.enter_world_hub() or not next.hubs.world_entries.has(str(next.world_node)), "chapter checkpoint source hub remains enterable")
		game = next
	scenarios.append("source chapter 2/3/4/5 hub checkpoints retain route and can continue")

func _test_battle_checkpoints() -> void:
	for fixture in [[1, 1, []], [2, 1, []], [29, 3, []], [32, 3, []], [34, 4, [34, 35]], [36, 4, [78]], [42, 4, []]]:
		var game = fresh()
		advance(game, int(fixture[1]))
		game.world_node = int(fixture[0])
		game.route_positions[game.route] = game.world_node
		if int(fixture[0]) == 34: game.apply_hub_flag(31)
		check(game.start_battle(int(fixture[0]), fixture[2]), "source stage %d constructs tactical state" % fixture[0])
		var next = loaded(game, "stage %d start" % fixture[0])
		check(next.retry_battle() and next.battle_outcome == "" and next.phase == "player", "resumed stage %d restarts to actionable player phase" % fixture[0])
		check(next.select_unit(next.leader_id()), "resumed stage %d leader can select" % fixture[0])
		next.mark_wait(next.leader_id())
		check(bool(next.find_unit(next.leader_id()).acted), "resumed stage %d leader can complete action" % fixture[0])
		next = loaded(next, "stage %d acted" % fixture[0])
		check(next.retry_battle() and not bool(next.find_unit(next.leader_id()).acted), "resumed stage %d retry clears previous spent action" % fixture[0])
	scenarios.append("stages 1/2/29/32/34/36/42 production suspend, retry, select, wait, resave")

func _test_casualties_and_npcs() -> void:
	var game = fresh()
	game.world_node = 1
	check(game.start_battle(1), "death checkpoint source battle starts")
	game.commit_strike({"attacker": game.living("enemy")[0].id, "defender": "alm", "hp_after": 0})
	check(game.battle_outcome == "defeat", "normal leader death marks defeat")
	var next = loaded(game, "leader casualty defeat")
	check(next.retry_battle() and int(next.find_unit("alm").hp) > 0 and next.select_unit("alm"), "resumed leader casualty has working retry and action")
	game = fresh()
	advance(game, 3)
	game.world_node = 29
	check(game.start_battle(29), "rescue checkpoint source battle starts")
	game.commit_strike({"attacker": game.living("enemy")[0].id, "defender": "mathilda", "hp_after": 0})
	next = loaded(game, "rescue NPC casualty")
	check(next.retry_battle() and int(next.find_unit("mathilda").hp) > 0 and not next.roster.has("mathilda"), "resumed failed rescue rolls back NPC death and blocked recruitment")
	game = fresh()
	advance(game, 5)
	game.apply_hub_flag(82)
	game.world_node = 48
	check(game.enter_dungeon_battle(22), "final source trigger constructs both routes")
	var duma: Dictionary = {}
	for unit in game.units:
		if int(unit.get("character_id", 0)) == 167: duma = unit
	check(not duma.is_empty(), "final checkpoint contains source Duma")
	if duma.is_empty(): return
	game.commit_strike({"attacker": "alm", "defender": duma.id, "hp_after": 0})
	check(game.complete_battle(), "source boss death commits final settlement")
	next = loaded(game, "settled final victory")
	check(next.flags.get("campaign_complete", false) and next.story_events.any(func(event): return event.kind == "ending"), "settled victory resume retains ending continuation")
	check(next.retry_battle() and not next.flags.get("campaign_complete", false) and int(next.find_unit(str(duma.id)).hp) == 182, "settled final resume can restart both routes without stale completion")
	scenarios.append("real leader/NPC casualty -> load -> retry; source final boss death -> settlement -> load -> retry")

func legacy_from_production(game, version: int) -> void:
	check(game.save_game(), "historical fixture begins with production checkpoint")
	var old: Dictionary = State.read_json(SAVE)
	old.version = version
	for target in [old, old.battle_start_snapshot]:
		for field in Validator.EXTENDED_FIELDS: target.erase(field)
		for flag in ["world_army_instances", "world_army_next_id", "world_random_army_instance", "battle_army_instances", "dungeon_army_instances", "inventory_attacking_instance_id"]:
			target.flags.erase(flag)
		for unit in target.units: unit.erase("army_instance")
	if version == 1:
		for field in ["stage_id", "world_node", "roster", "cleared_stages", "battle_start_snapshot", "victory_rewards"]: old.erase(field)
	var file := FileAccess.open(SAVE, FileAccess.WRITE)
	file.store_string(JSON.stringify(old))
	file.close()

func _test_full_alliance_checkpoint() -> void:
	var game = fresh()
	advance(game, 4)
	# Source Alm-route recruits available before Zeke's village. Only ten
	# formal soldiers deploy here, plus all ten source allied Zeke soldiers.
	for id in ["gray", "tobin", "kliff", "clair", "clive", "forsyth", "silque", "python", "tatiana"]:
		game.recruit(id)
	game.world_node = 34
	game.route_positions.alm = 34
	game.apply_hub_flag(31)
	check(game.start_battle(34, [34, 35]), "full source Alm/Zeke alliance begins")
	check(game.living("player").size() == 20 and game.units.any(func(unit): return unit.side == "player" and int(unit.get("player_slot", -1)) == 19), "full source alliance occupies legal player slot 19")
	var next = loaded(game, "twenty-member source alliance")
	check(next.living("player").size() == 20 and next.retry_battle() and next.living("player").size() == 20, "full allied deployment loads and retries without slot loss")
	check(next.select_unit("alm"), "full allied deployment accepts a formal soldier action")
	next.mark_wait("alm")
	check(next.find_unit("alm").acted, "full allied deployment can finish a formal action")
	scenarios.append("full source Alm ten-member deployment plus Zeke ten-member NPC alliance remains saveable and actionable")

func _test_legacy_retry() -> void:
	for fixture in [[1, 1], [1, 2], [2, 2]]:
		var game = fresh()
		game.world_node = int(fixture[0])
		check(game.start_battle(int(fixture[0])), "legacy source stage begins")
		legacy_from_production(game, int(fixture[1]))
		var next = State.new()
		next.save_path = SAVE
		check(next.load_game(), "historical v%d stage%d loads" % [fixture[1], fixture[0]])
		check(next.retry_battle() and next.party == ["alm", "lukas"], "historical v%d retry retains recruited members" % fixture[1])
		next = loaded(next, "upgraded v%d stage%d retry" % [fixture[1], fixture[0]])
		check(next.select_unit("alm"), "resaved legacy retry remains selectable")
		next.mark_wait("alm")
		check(next.find_unit("alm").acted, "resaved legacy retry spends a legal action")
	scenarios.append("historical v1 stage1, v2 stages1/2 -> load -> retry -> v3 save/load -> select/wait")

func _test_legacy_title_continue() -> void:
	var game = fresh()
	game.world_node = 2
	check(game.start_battle(2), "legacy controller second battle begins")
	legacy_from_production(game, 2)
	await new_scene()
	await continue_title()
	check(scene.view == "battle" and scene.game.stage_id == 2, "actual title Continue restores legacy second battle")
	check(scene.game.retry_battle(), "actual loaded controller supports legacy retry")
	scene._begin_existing_battle()
	check(scene.view == "battle" and not scene.busy and scene.ui_mode == "inspect", "retried legacy controller returns to free battle inspection")
	check(scene.game.select_unit("alm"), "retried legacy controller accepts a unit selection")
	scene.game.mark_wait("alm")
	check(scene.game.find_unit("alm").acted and scene.game.save_game(), "retried legacy controller accepts wait and checkpoint")
	await new_scene()
	await continue_title()
	check(scene.view == "battle" and scene.game.stage_id == 2 and scene.game.find_unit("alm").acted, "actual title Continue restores spent action after migrated retry")
	scenarios.append("actual title Continue v2 second-battle -> retry -> wait -> resave -> title Continue")

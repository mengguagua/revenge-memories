extends SceneTree
## Reused real-key input and tactical planning helper. New run overrides all preparation.
## No enemy edits, forced deaths/victories, direct movement or replayed RNG rolls.
const State = preload("res://core/game_state.gd")
const Rules = preload("res://core/combat_rules.gd")
const Items = preload("res://core/item_rules.gd")
const Progression = preload("res://core/unit_progression.gd")
const SAVE := "res://reports/round7-late-playthrough-save.json"
var ui
var failures: Array[String] = []
var battles: Array = []
var operations: Array = []
var preparation: Array = []
var inputs := 0
var waits := 0
var abort := false
var threats: Array = []
var battle_record: Dictionary = {}

func _initialize() -> void: call_deferred("run")

func record_failure(message: String) -> void:
	failures.append(message)
	abort = true
	push_error(message)
	ui.game.save_game()

func key(code: int) -> void:
	inputs += 1
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.pressed = true
	ui._input(event)
	event = InputEventKey.new()
	event.physical_keycode = code
	ui._input(event)

func choose(action: String) -> void:
	if not ui.menu_actions.has(action):
		record_failure("Prompt/action missing: " + action + " in " + ui.menu_context)
		return
	var steps := 0
	while str(ui.menu_actions[ui.menu_selected]) != action and steps < 50:
		key(KEY_DOWN)
		steps += 1
	key(KEY_Z)

func tick() -> void:
	waits += 1
	await process_frame

func settle() -> void:
	var frames := 0
	while frames < 10000 and not abort:
		frames += 1
		if ui.view in ["battle_story", "hub_dialogue", "reward", "chapter"]:
			key(KEY_Z)
		elif ui.view == "hub_choice" and ui.hub_controller.choice_title.contains("记录进度"):
			key(KEY_DOWN)
			key(KEY_Z)
		elif ui.view in ["loot", "loot_confirm"]:
			# Existing item is retained. Full stores use explicit discard-new confirmation.
			choose("store" if ui.menu_actions.has("store") else ("discard_new" if ui.view == "loot" else "confirm"))
		if not ui.busy and not ui.batch_running and ui.view not in ["battle_story", "hub_dialogue", "reward", "chapter", "loot", "loot_confirm"]:
			if not ui.view.begins_with("hub") or (ui.hub_controller.motion_left <= 0 and ui.hub_controller.timer <= 0 and ui.hub_controller.script_id < 0):
				return
		await tick()
	if not abort: record_failure("Timed input owner did not release: " + ui.view)

func cursor_to(at: Vector2i) -> void:
	var steps := 0
	while ui.game.cursor != at and steps < 100 and not abort:
		steps += 1
		if ui.game.cursor.x != at.x: key(KEY_RIGHT if ui.game.cursor.x < at.x else KEY_LEFT)
		else: key(KEY_DOWN if ui.game.cursor.y < at.y else KEY_UP)
	if ui.game.cursor != at: record_failure("Real cursor keys cannot reach " + str(at))

func distance(a: Vector2i, b: Vector2i) -> int:
	return absi(a.x - b.x) + absi(a.y - b.y)

func refresh_threats() -> void:
	threats.clear()
	for enemy in ui.game.living("enemy"):
		threats.append({"unit": enemy, "cells": ui.game.reachable(enemy).costs.keys()})

func risk(unit: Dictionary, cell: Vector2i, skip: String = "") -> float:
	var values: Array[float] = []
	for threat in threats:
		var enemy: Dictionary = threat.unit
		if str(enemy.id) == skip or int(enemy.hp) <= 0: continue
		var reach: Vector2i = Rules.attack_range(enemy)
		var exposed := false
		for from in threat.cells:
			var d := distance(from, cell)
			if d >= reach.x and d <= reach.y:
				exposed = true
				break
		if not exposed: continue
		var stats := Rules.attack_stats(enemy, unit, ui.game.terrain_avoid(cell))
		var strikes := 2 if int(stats.attack_speed) > int(stats.defender_attack_speed) else 1
		values.append(float(stats.damage * strikes) * float(stats.hit) / 100.0)
	values.sort()
	values.reverse()
	var amount := 0.0
	for i in range(values.size()): amount += values[i] * (1.0 if i < 2 else 0.25)
	return amount

func plan(unit: Dictionary) -> Dictionary:
	return combat_plan(unit)

func combat_plan(unit: Dictionary) -> Dictionary:
	var origin := State.pos(unit)
	var graph: Dictionary = ui.game.reachable(unit)
	var nearest := 999
	for enemy in ui.game.living("enemy"): nearest = mini(nearest, distance(origin, State.pos(enemy)))
	var best := {"kind": "wait", "cell": origin, "score": -risk(unit, origin), "target": "", "spell": -1}
	var weapons: Array = [-1]
	for spell in Items.spells(unit):
		if not Items.is_support(spell) and Items.can_use(unit, spell): weapons.append(spell)
	for cell in graph.costs:
		if not ui.game.can_stop(unit, cell): continue
		var candidate: Dictionary = unit.duplicate(true)
		candidate.position = [cell.x, cell.y]
		var danger := risk(candidate, cell)
		var next_nearest := 999
		for enemy in ui.game.living("enemy"): next_nearest = mini(next_nearest, distance(cell, State.pos(enemy)))
		var score := 2.0 * (nearest - next_nearest) - danger
		if danger >= int(unit.hp) - 3: score -= 100.0 if str(unit.id) == ui.game.leader_id() else 40.0
		if score > best.score: best = {"kind": "wait", "cell": cell, "score": score, "target": "", "spell": -1}
		for spell in Items.spells(unit):
			if spell not in [40, 41] or not Items.can_use(unit, spell): continue
			candidate.erase("weapon_index")
			for target in ui.game.support_targets(candidate, spell):
				var missing := int(target.max_hp) - int(target.hp)
				if missing < 5: continue
				var healed := mini(missing, int(unit.strength))
				var urgent := 25.0 if int(target.hp) < int(target.max_hp) / 2 else 0.0
				var heal_score := healed * 3.0 + urgent - Items.cost(spell) * 2.0 - danger
				if danger >= int(unit.hp) - Items.cost(spell) - 3: heal_score -= 150.0
				if heal_score > best.score: best = {"kind": "heal", "cell": cell, "score": heal_score, "target": str(target.id), "spell": spell}
		for weapon in weapons:
			candidate.erase("weapon_index")
			if weapon >= 0: candidate.weapon_index = weapon
			for enemy in ui.game.targets(candidate):
				var guarded: Dictionary = enemy.duplicate(true)
				guarded.story_invulnerable = Rules.boss_guard(guarded, ui.game.turn)
				if Rules.attack_blocked(candidate, guarded): continue
				var d := distance(cell, State.pos(enemy))
				var reply := Rules.default_counter(guarded, d)
				var stats := Rules.attack_stats(candidate, reply, ui.game.terrain_avoid(State.pos(enemy)))
				var strikes := 2 if int(stats.attack_speed) > int(stats.defender_attack_speed) else 1
				var expected: float = float(stats.damage * strikes) * stats.hit / 100.0
				var kill: bool = expected >= int(enemy.hp) * 0.95
				var counter := 0.0
				if Rules.can_attack(reply, d):
					var response := Rules.attack_stats(reply, candidate, ui.game.terrain_avoid(cell))
					counter = float(response.damage) * response.hit / 100.0 * (2 if response.attack_speed > response.defender_attack_speed else 1)
				var after_risk := risk(candidate, cell, str(enemy.id) if kill else "")
				var attack_score := minf(expected, enemy.hp) * 2.0 + (30.0 if kill else 0.0) - counter - after_risk * 0.7 - Items.cost(Rules.weapon_index(candidate))
				if after_risk + counter >= int(unit.hp) - 3: attack_score -= 200.0 if str(unit.id) == ui.game.leader_id() else 50.0
				if attack_score > best.score: best = {"kind": "attack", "cell": cell, "score": attack_score, "target": str(enemy.id), "spell": weapon}
	return best

func act(id: String) -> void:
	var unit: Dictionary = ui.game.find_unit(id)
	if unit.is_empty() or int(unit.hp) <= 0 or bool(unit.acted) or abort: return
	refresh_threats()
	var action := plan(unit)
	var before := {"unit": id, "turn": ui.game.turn, "hp": unit.hp, "cell": unit.position.duplicate(), "action": action.duplicate(true)}
	before.action.cell = [action.cell.x, action.cell.y]
	cursor_to(State.pos(unit))
	key(KEY_Z)
	if ui.ui_mode != "move":
		record_failure("Displayed controllable unit cannot enter move: " + id)
		return
	cursor_to(action.cell)
	key(KEY_Z)
	await settle()
	if abort: return
	if ui.menu_context != "unit_action":
		record_failure("Move failed to open actions for " + id)
		return
	match action.kind:
		"attack", "heal":
			if int(action.spell) >= 0:
				choose("magic")
				choose("spell:" + str(action.spell))
			else: choose("attack")
			var steps := 0
			while not abort and not ui.target_ids.is_empty() and str(ui.target_ids[ui.target_index]) != action.target and steps < 50:
				key(KEY_RIGHT)
				steps += 1
			if ui.target_ids.is_empty() or str(ui.target_ids[ui.target_index]) != action.target:
				record_failure("Preview does not match requested actual target " + action.target)
				return
			key(KEY_Z)
		_: choose("wait")
	await settle()
	before.after_hp = int(unit.hp)
	before.after_cell = unit.position.duplicate()
	before.target_after_hp = ui.game.find_unit(str(action.target)).get("hp", -1)
	operations.append(before)

func battle() -> void:
	var stage: int = ui.game.stage_id
	battle_record = {"stage": stage, "name": ui.game.battle_data.name_zh, "entry_enemies": ui.game.living("enemy").duplicate(true), "entry_players": ui.game.living("player").duplicate(true), "turns": []}
	var guard := 0
	while ui.view == "battle" and ui.game.battle_outcome.is_empty() and guard < 60 and not abort:
		guard += 1
		var turn: int = ui.game.turn
		# Healers act after front-line decisions, with the commander held for last.
		var members: Array = ui.game.living("player").filter(func(u): return bool(u.get("controllable", true)))
		members.sort_custom(func(a,b): return rank(a) < rank(b))
		for unit in members:
			if not ui.game.battle_outcome.is_empty() or ui.game.turn != turn or abort: break
			await act(str(unit.id))
		if ui.game.turn == turn and ui.game.battle_outcome.is_empty() and not abort:
			key(KEY_S)
			choose("end_turn")
			await settle()
		battle_record.turns.append({"turn": ui.game.turn, "outcome": ui.game.battle_outcome, "player_alive": ui.game.living("player").size(), "enemy_alive": ui.game.living("enemy").size(), "kills": ui.game.kills})
		print("ROUND7_PLAY ", stage, " turn ", ui.game.turn, " allies ", ui.game.living("player").size(), " enemies ", ui.game.living("enemy").size(), " ", ui.game.battle_outcome)
		if ui.game.turn == turn and ui.game.battle_outcome.is_empty() and not abort: record_failure("Turn did not advance after completed actions")
	if guard >= 60 and ui.game.battle_outcome.is_empty(): record_failure("No natural outcome after60 turns on map" + str(stage))
	battle_record.outcome = ui.game.battle_outcome
	battle_record.final_turn = ui.game.turn
	battle_record.final_players = ui.game.living("player").duplicate(true)
	battle_record.settled = ui.game.battle_settled
	battles.append(battle_record)
	if ui.view == "victory" and not abort:
		key(KEY_Z)
		choose("continue_world")
		await settle()
		operations.append({"kind": "continue_result", "stage": stage, "view": ui.view, "world_node": ui.game.world_node, "hub_id": ui.game.hub_id})
	elif ui.view == "defeat" and not abort:
		# A tactical defeat is recorded separately from an input/progression stall.
		print("TACTICAL_DEFEAT ", stage)
		abort = true

func rank(unit: Dictionary) -> int:
	if str(unit.id) == ui.game.leader_id(): return 3
	if int(unit.class_id) in [17,18]: return 2
	return 0 if int(unit.class_id) in [5,10] else 1

func move_world(destination: int) -> void:
	if not ui.game.world_neighbors().has(destination):
		record_failure("World prompt offers no legal continuation to " + str(destination))
		return
	var at: Array = ui.game.catalog.world_nodes[str(ui.game.world_node)].position
	var target: Array = ui.game.catalog.world_nodes[str(destination)].position
	var delta := Vector2(target[0] - at[0], target[1] - at[1])
	var directions := [Vector2i.RIGHT,Vector2i.LEFT,Vector2i.DOWN,Vector2i.UP]
	directions.sort_custom(func(a,b): return delta.normalized().dot(Vector2(a)) > delta.normalized().dot(Vector2(b)))
	for dir in directions:
		key(KEY_RIGHT if dir == Vector2i.RIGHT else KEY_LEFT if dir == Vector2i.LEFT else KEY_DOWN if dir == Vector2i.DOWN else KEY_UP)
		if ui.game.world_node == destination: return
		if ui.game.world_node != int(ui.game.route_positions.get("celica", ui.game.world_node)): break
	record_failure("Directional world input cannot reach the displayed adjacent location " + str(destination))

func hub_path(at: Vector2i) -> Array:
	var hub = ui.hub_controller
	var start: Vector2i = ui.game.hub_position
	var queue: Array = [start]
	var previous: Dictionary = {start: start}
	while not queue.is_empty():
		var cell: Vector2i = queue.pop_front()
		if cell == at:
			var path: Array = []
			while cell != start:
				path.push_front(cell)
				cell = previous[cell]
			return path
		for dir in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var next: Vector2i = cell + dir
			if not hub._inside(next) or previous.has(next) or hub._actor_at(next) > 0: continue
			if not hub._ground(next) and not hub._door(next): continue
			previous[next] = cell
			queue.append(next)
	return []

func walk_hub(at: Vector2i) -> void:
	var room_id: int = ui.game.hub_id
	var steps := 0
	while ui.game.hub_id == room_id and ui.view == "hub" and ui.game.hub_position != at and steps < 500 and not abort:
		steps += 1
		var path := hub_path(at)
		if path.is_empty():
			record_failure("No real walkable path in room%d to%s" % [room_id,at])
			return
		var dir: Vector2i = path[0] - ui.game.hub_position
		key(KEY_RIGHT if dir == Vector2i.RIGHT else KEY_LEFT if dir == Vector2i.LEFT else KEY_DOWN if dir == Vector2i.DOWN else KEY_UP)
		await settle()
	if steps >= 500: record_failure("Hub walk does not advance in room" + str(room_id))

func cross_hub(dir: Vector2i) -> void:
	var hub = ui.hub_controller
	var best: Array = []
	var goal := Vector2i(-1,-1)
	for y in range(int(hub.room.height)):
		for x in range(int(hub.room.width)):
			var cell := Vector2i(x,y)
			if dir == Vector2i.UP and y != 0 or dir == Vector2i.DOWN and y != int(hub.room.height)-1: continue
			if dir == Vector2i.LEFT and x != 0 or dir == Vector2i.RIGHT and x != int(hub.room.width)-1: continue
			if not hub._ground(cell): continue
			var path := hub_path(cell)
			if path.is_empty(): continue
			if best.is_empty() or path.size() < best.size():
				best = path
				goal = cell
	if goal.x < 0:
		record_failure("Visible source exit cannot be walked in room" + str(ui.game.hub_id))
		return
	var before: int = ui.game.hub_id
	await walk_hub(goal)
	if ui.view == "hub_choice":
		key(KEY_Z)
		await settle()
	operations.append({"kind":"hub_exit","from":before,"to":ui.game.hub_id,"view":ui.view,"world":ui.game.world_node})

func continue_forest() -> void:
	move_world(74)
	key(KEY_Z)
	await settle()
	if ui.game.hub_id != 26 or ui.view != "hub":
		record_failure("Defeated fortress cannot be entered for onward exploration")
		return
	await walk_hub(Vector2i(11,6))
	if ui.game.hub_id != 25: record_failure("Fortress doorway did not reach its inner room")
	if abort: return
	await cross_hub(Vector2i.UP)
	if ui.game.hub_id != 115: record_failure("Inner fortress north exit did not reach forest passage")
	if abort: return
	await cross_hub(Vector2i.UP)
	if ui.game.hub_id != 28: record_failure("Forest passage did not reach outer forest room")
	if abort: return
	await cross_hub(Vector2i.LEFT)
	if ui.view != "world" or ui.game.world_node != 46: record_failure("Forest's exit did not return to the expected Celica road")
	if abort: return
	move_world(47)
	key(KEY_Z)
	await settle()
	if ui.view == "battle": await battle()
	if not abort and ui.view == "world":
		move_world(48)
		key(KEY_Z)
		await settle()
		if ui.view == "battle": await battle()

func prepare() -> void:
	ui.game.new_game()
	ui.game.chapter = 4
	ui.game.route = "celica"
	ui.game.party = []
	ui.game.parties.celica = []
	for id in ["celica","palla","catria","genny","saber","noma","boey","mae","deen","est"]: ui.game.recruit(id)
	for spec in [["palla",12,5],["catria",12,5],["genny",12,17],["saber",7,9],["saber",10,10],["boey",12,19],["mae",20,11],["deen",10,10],["est",12,5]]:
		var unit: Dictionary = ui.game.roster[spec[0]]
		var gained := maxi(0, int(spec[1]) - int(unit.level))
		unit.level = int(spec[1])
		var trained := Progression.learn_spells(unit, gained)
		var promoted := Progression.promote(trained.unit, int(spec[2]))
		if not promoted.valid: record_failure("Invalid prepared source promotion")
		ui.game.roster[spec[0]] = promoted.unit
		preparation.append({"unit": spec[0], "prior_level_checkpoint": spec[1], "source_promotion_to": spec[2], "growth_rolls_added": 0})
	ui.game.roster.celica.level = 15
	ui.game.roster.celica = Progression.learn_spells(ui.game.roster.celica,14).unit
	ui.game._setup_chapter_armies()
	ui.game.world_node = 43
	ui.game.previous_world_node = 63
	ui.game.route_positions.celica = 43
	ui.game.remember_world_approach()
	ui.game.mode = "world"
	ui.view = "world"
	ui.game.save_game()

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = SAVE
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.animation_speed = 100.0
	ui.instant_mode = false
	if OS.get_cmdline_user_args().has("--retry-only"):
		var previous := State.read_json("res://reports/round7-late-playthrough.json")
		battles = previous.get("battles",[])
		operations = previous.get("operations",[])
		preparation = previous.get("preparation",[])
		inputs = int(previous.get("input_events",0))
		waits = int(previous.get("waited_frames",0))
		key(KEY_DOWN)
		key(KEY_Z)
		await settle()
		if ui.view != "defeat" or ui.game.stage_id != 47: record_failure("Actual title continue must show recorded tactical defeat")
		if not abort:
			key(KEY_Z)
			choose("retry")
			await settle()
			if ui.view != "battle" or ui.game.turn != 1 or ui.game.phase != "player" or ui.busy or ui.batch_running: record_failure("Real retry did not restore playable turn1")
			var before_selection: String = str(ui.game.find_unit("celica").id)
			cursor_to(State.pos(ui.game.find_unit(before_selection)))
			key(KEY_Z)
			if ui.ui_mode != "move": record_failure("Retried commander cannot be selected")
			key(KEY_X)
			operations.append({"kind":"actual_defeat_retry","stage":47,"view":ui.view,"turn":ui.game.turn,"player_alive":ui.game.living("player").size(),"enemy_alive":ui.game.living("enemy").size(),"commander_hp":ui.game.find_unit("celica").hp,"select_and_cancel":ui.ui_mode=="inspect"})
	elif OS.get_cmdline_user_args().has("--continue"):
		var previous := State.read_json("res://reports/round7-late-playthrough.json")
		battles = previous.get("battles",[])
		operations = previous.get("operations",[])
		preparation = previous.get("preparation",[])
		inputs = int(previous.get("input_events",0))
		waits = int(previous.get("waited_frames",0))
		key(KEY_DOWN)
		key(KEY_Z)
		await settle()
		if ui.view != "world" or ui.game.world_node != 45: record_failure("Continue must restore the three already completed battles at fortress45")
		if not abort: await continue_forest()
	else:
		prepare()
		key(KEY_Z)
		await settle()
		if ui.view == "battle": await battle()
		if not abort and ui.view == "world":
			move_world(44)
			if ui.game.world_has_battle(44):
				key(KEY_Z)
				await settle()
				await battle()
			if not abort:
				move_world(45)
				key(KEY_Z)
				await settle()
				if ui.view == "battle": await battle()
	ui.game.save_game()
	var file := FileAccess.open("res://reports/round7-late-playthrough.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"failures":failures,"battles":battles,"operations":operations,"input_events":inputs,"waited_frames":waits,
		"preparation":preparation,"scope":"Independent chapter4 preparation checkpoint; real keyboard input, native timers/AI/combat/HP/EXP/death/result and linked world travel.",
		"limits":"Prior recruitment, levels and source-minimum promotions are checkpoint setup, not a natural opening-to-end campaign. No stat growth added; enemies and post-entry outcomes never edited.",
		"natural_after_checkpoint":true,"user_save_accessed":false,"visible_window":false,"screenshots":0,"final_view":ui.view,"final_world":ui.game.world_node},"  ")+"\n")
	file.close()
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	print("ROUND7_PLAY_DONE battles=",battles.size()," failures=",failures," inputs=",inputs)
	quit(0 if failures.is_empty() and (OS.get_cmdline_user_args().has("--retry-only") or battles.all(func(b):return b.outcome=="victory")) else 1)

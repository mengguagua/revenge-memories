extends SceneTree
## Targeted behavior checks with independent source fixtures, no real save file.
const GameState = preload("res://core/game_state.gd")
const SAVE := "res://reports/test-save.json"
var checks := 0
var failures := 0

func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute("res://reports")
	_test_opening_and_deployment()
	_test_weighted_movement()
	_test_brigand_recovery_ai()
	_test_combat_and_growth()
	_test_recovery_and_outcome()
	_test_save_transactions()
	DirAccess.remove_absolute(SAVE)
	DirAccess.remove_absolute(SAVE + ".tmp")
	print("FE2 state: %d checks, %d failures" % [checks, failures])
	quit(1 if failures else 0)

func _check(ok: bool, message: String) -> void:
	checks += 1
	if not ok:
		failures += 1
		push_error(message)

func _fresh(all_recruited: bool = false):
	var game = GameState.new()
	game.save_path = SAVE
	game.new_game()
	if all_recruited:
		for key in ["lukas_report", "mycen_refusal", "alm_volunteers", "gray_joins", "tobin_joins", "kliff_joins"]:
			game.complete_dialogue(key)
	return game

func _test_opening_and_deployment() -> void:
	var game = _fresh()
	_check(game.mode == "chapter" and game.party == ["alm"] and not game.flags.get("heard_lukas", false) and int(game.flags.world_gate_bits) == 22, "New game begins before recruitment")
	_check(game.village_position == Vector2i(5, 10), "Original opening spawn is x5/y10")
	_check(game.dialogue_for_npc("mycen") == "training", "Mycen trains before Lukas report")
	_check(game.dialogue_for_npc("lukas") == "lukas_report", "Lukas first explains the coup")
	game.complete_dialogue("lukas_report")
	_check(game.flags.get("heard_lukas", false) and game.party == ["alm"], "Report changes story flag without recruitment")
	_check(game.dialogue_for_npc("mycen") == "mycen_refusal", "Mycen refusal follows report")
	game.complete_dialogue("mycen_refusal")
	_check(game.dialogue_for_npc("lukas") == "alm_volunteers", "Return to Lukas after Mycen refusal")
	game.complete_dialogue("alm_volunteers")
	_check(game.party == ["alm", "lukas"] and game.flags.get("joined_deliverance", false), "Alm volunteering recruits Lukas")
	_check(game.dialogue_for_npc("lukas") == "lukas_join_repeat", "Repeat Lukas dialogue cannot recruit twice")
	for id in ["gray", "tobin", "kliff"]:
		_check(game.dialogue_for_npc(id) == id + "_joins", "Friend becomes recruitable: " + id)
		game.complete_dialogue(id + "_joins")
		game.complete_dialogue(id + "_joins")
	_check(game.party == ["alm", "lukas", "gray", "tobin", "kliff"], "Village recruitment is ordered and idempotent")
	game.start_battle()
	var source_positions = [[5, 6], [5, 8], [4, 7], [3, 7], [3, 8]]
	for i in range(5):
		_check(GameState.pos(game.units[i]) == Vector2i(source_positions[i][0], source_positions[i][1]), "Original deployment slot %d" % i)
	var alm = game.find_unit("alm")
	_check([int(alm.hp), int(alm.strength), int(alm.skill), int(alm.speed), int(alm.defence), int(alm.move)] == [28, 10, 7, 6, 6, 5], "Alm original initial combat values")
	_check(game.living("enemy").size() == 5, "First battle has five original brigands")
	var enemy_positions = [[11, 4], [10, 10], [13, 8], [10, 6], [14, 4]]
	for i in range(5):
		var enemy = game.find_unit("brigand_%d" % (i+1))
		_check(GameState.pos(enemy) == Vector2i(enemy_positions[i][0], enemy_positions[i][1]), "Original brigand deployment %d" % i)
		_check([int(enemy.hp), int(enemy.strength), int(enemy.skill), int(enemy.speed), int(enemy.defence), int(enemy.move)] == [26, 7, 1, 2, 2, 4], "Original Lv1 brigand stats %d" % i)
	game.new_game()
	_check(not game.flags.get("joined_deliverance", false) and int(game.flags.world_gate_bits) == 22 and game.units.is_empty() and game.party == ["alm"] and game.kills == 0, "New game clears a prior campaign")

func _corridor():
	var game = _fresh(true)
	game.start_battle()
	game.battle_data = game.battle_data.duplicate(true)
	game.battle_data.map.width = 5
	game.battle_data.map.height = 3
	game.battle_data.map.tiles = [46,46,46,46,46, 46,48,49,48,46, 46,46,46,46,46]
	game.units = [game.find_unit("alm").duplicate(true)]
	game.units[0].position = [1, 1]
	return game

func _test_weighted_movement() -> void:
	var game = _corridor()
	var alm = game.find_unit("alm")
	alm.move = 2
	var graph = game.reachable(alm)
	_check(game.movement_cost(alm, Vector2i(2, 1)) == 2, "Entering forest costs two points")
	_check(graph.costs.get(Vector2i(2, 1), -1) == 2 and not graph.costs.has(Vector2i(3, 1)), "Budget two reaches forest but not the far plain")
	alm.move = 3
	_check(game.reachable(alm).costs.get(Vector2i(3, 1), -1) == 3, "Weighted path plain->forest->plain totals three")
	var friend = alm.duplicate(true)
	friend.id = "friend"
	friend.position = [2, 1]
	game.units.append(friend)
	_check(game.reachable(alm).costs.has(Vector2i(3, 1)), "Friendly unit may be crossed")
	_check(not game.can_stop(alm, Vector2i(2, 1)), "Cannot finish movement on a friend")
	_check(game.select_unit("alm") and not game.move_selected(Vector2i(2, 1)), "Movement API rejects friendly destination")
	friend.side = "enemy"
	_check(not game.reachable(alm).costs.has(Vector2i(3, 1)), "Enemy blocks the only corridor")
	friend.hp = 0
	_check(game.reachable(alm).costs.has(Vector2i(3, 1)), "A defeated enemy no longer blocks passage")
	_check(game.move_selected(Vector2i(3, 1)), "Legal weighted movement is accepted")
	game.cancel_move()
	_check(GameState.pos(alm) == Vector2i(1, 1) and game.selected_id.is_empty() and not alm.acted, "Cancel restores origin and preserves the action")
	_check(not game.select_unit("missing"), "Invalid selection rejected")
	alm.acted = true
	_check(not game.select_unit("alm"), "Acted unit cannot act again")

func _recovery_ai_fixture():
	var game = _fresh()
	game.start_battle()
	game.battle_data = game.battle_data.duplicate(true)
	game.battle_data.map.width = 7
	game.battle_data.map.height = 5
	game.battle_data.map.tiles = [
		46,46,46,46,46,46,46,
		46,48,49,48,218,48,46,
		46,46,46,48,46,46,46,
		46,48,48,48,48,48,46,
		46,46,46,46,46,46,46,
	]
	var enemy = game.find_unit("brigand_1").duplicate(true)
	var alm = game.find_unit("alm").duplicate(true)
	enemy.position = [3, 3]
	enemy.move = 2
	enemy.hp = 12
	alm.position = [2, 3]
	game.units = [enemy, alm]
	game.frame_counter = 0
	return game

func _test_brigand_recovery_ai() -> void:
	var game = _recovery_ai_fixture()
	var enemy = game.find_unit("brigand_1")
	var action = game.ai_action(enemy)
	_check(action.destination == Vector2i(3, 1) and action.target == "", "HP12/26 brigand retreats toward recovery rather than attacking adjacent Alm")
	_check((int(enemy.ai_flags) & 3) == 1 and int(enemy.raw_ai_flags) == 192, "Recovery mode is persistent while the source flags stay immutable")
	enemy.hp = 13
	action = game.ai_action(enemy)
	_check(action.target == "" and (int(enemy.ai_flags) & 3) == 1, "Half HP remains in recovery on an even original-loop counter")
	game.frame_counter = 1
	action = game.ai_action(enemy)
	_check(action.target == "alm" and (int(enemy.ai_flags) & 3) == 0, "Half HP resumes original offensive mode on an odd loop counter")
	enemy.ai_flags = 193
	enemy.hp = 26
	game.frame_counter = 0
	_check(game.ai_action(enemy).target == "alm" and (int(enemy.ai_flags) & 3) == 0, "Full HP resumes offense even on an even loop counter")
	game = _recovery_ai_fixture()
	enemy = game.find_unit("brigand_1")
	enemy.hp = 13
	_check(game.ai_action(enemy).target == "alm", "Exactly half HP does not enter recovery from normal mode")
	enemy.hp = 12
	enemy.position = [1, 1]
	action = game.ai_action(enemy)
	_check(action.destination == Vector2i(2, 1) and action.target == "", "Recovery route pays two points to enter forest, rather than using Manhattan distance")
	enemy.move = 3
	_check(game.ai_action(enemy).destination == Vector2i(3, 1), "Three movement points cross the forest but do not reach recovery")
	enemy.move = 4
	_check(game.ai_action(enemy).destination == Vector2i(4, 1), "Four movement points reach the category15 recovery tile")
	enemy.position = [4, 1]
	_check(game.ai_action(enemy).destination == Vector2i(4, 1), "A recovering brigand stays on the recovery tile")
	enemy.position = [1, 1]
	var friend = enemy.duplicate(true)
	friend.id = "friend"
	friend.position = [2, 1]
	game.units.append(friend)
	enemy.move = 2
	_check(game.ai_action(enemy).destination == Vector2i(1, 1), "Recovery movement cannot finish on a friendly occupied forest")
	enemy.move = 3
	_check(game.ai_action(enemy).destination == Vector2i(3, 1), "Recovery movement can pass through a friend to a legal destination")
	game = _recovery_ai_fixture()
	enemy = game.find_unit("brigand_1")
	enemy.position = [1, 1]
	game.find_unit("alm").position = [2, 1]
	action = game.ai_action(enemy)
	_check(action.destination == Vector2i(1, 1) and action.target == "", "Opposing unit blocks the only recovery route; recovery search waits this action")
	_check((int(enemy.ai_flags) & 131) == 0, "Failed recovery search restores offense and disables recovery as L038ACC does")
	_check(game.ai_action(enemy).target == "alm", "A failed recovery search resumes ordinary offense on the next action")
	game = _recovery_ai_fixture()
	enemy = game.find_unit("brigand_1")
	friend = enemy.duplicate(true)
	friend.id = "friend"
	friend.position = [4, 1]
	game.units.append(friend)
	action = game.ai_action(enemy)
	_check(action.destination == Vector2i(3, 3) and action.target == "", "Friendly occupation prevents selecting the recovery tile as a destination")

func _combat_fixture():
	var game = _fresh()
	game.start_battle()
	var alm = game.find_unit("alm").duplicate(true)
	var enemy = game.find_unit("brigand_1").duplicate(true)
	alm.position = [6, 7]
	enemy.position = [7, 7]
	game.units = [alm, enemy]
	return game

func _test_combat_and_growth() -> void:
	var game = _combat_fixture()
	var alm = game.find_unit("alm")
	var enemy = game.find_unit("brigand_1")
	alm.skill = 0
	alm.speed = 0
	enemy.speed = 100
	var exchange = game.plan_combat("alm", "brigand_1")
	_check(not exchange.is_empty() and not exchange.events[0].hit and exchange.events[0].damage == 0, "Hit rate zero never hits, including random roll zero")
	_check(alm.hp == 28 and enemy.hp == 26, "Planning combat does not apply strikes to live units")
	game = _combat_fixture()
	alm = game.find_unit("alm")
	enemy = game.find_unit("brigand_1")
	alm.skill = 255
	alm.luck = 0
	alm.exp = 90
	alm.hp = 18
	alm.growths = {"hp": 100, "defence": 100, "luck": 100, "speed": 100, "skill": 100, "strength": 100}
	enemy.hp = 1
	exchange = game.plan_combat("alm", "brigand_1")
	_check(exchange.events.size() == 1 and exchange.events[0].hp_after == 0, "A lethal first strike suppresses counterattack and follow-up")
	game.commit_strike(exchange.events[0])
	game.commit_strike(exchange.events[0])
	_check(game.kills == 1, "Committing an already lethal strike does not count another kill")
	var reward = game.finish_exchange(exchange)
	_check(reward.gain == 15 and reward.leveled and alm.level == 2 and alm.exp == 5, "Alm kill EXP15 crosses100 once and keeps remainder5")
	_check(alm.max_hp == 29 and alm.hp == 19 and alm.strength == 11 and alm.defence == 7, "Growth applies to current HP, maximum HP and distinct stats")
	_check(game.battle_outcome == "victory", "Final enemy death produces victory")
	game = _combat_fixture()
	alm = game.find_unit("alm")
	enemy = game.find_unit("brigand_1")
	alm.hp = 1
	enemy.skill = 255
	enemy.strength = 40
	exchange = game.plan_combat("brigand_1", "alm")
	_check(exchange.events.size() == 1, "Lethal enemy attack suppresses dead player's counter")
	game.commit_strike(exchange.events[0])
	reward = game.finish_exchange(exchange)
	_check(reward.is_empty() and game.battle_outcome == "defeat", "Dead Alm receives no EXP and fails the battle")

func _test_recovery_and_outcome() -> void:
	var game = _combat_fixture()
	var alm = game.find_unit("alm")
	var enemy = game.find_unit("brigand_1")
	# Original map has recovery tile218 at x1/y2.
	alm.position = [1, 2]
	alm.hp = 20
	enemy.position = [2, 2]
	game.next_phase()
	_check(alm.hp == 20, "Player recovery does not fire at enemy phase start")
	game.next_phase()
	_check(alm.hp == 25, "Recovery tile heals the owning side by five at phase start")
	game.next_phase()
	game.next_phase()
	_check(alm.hp == 28, "Recovery is capped at original maximum")
	for unit in game.units:
		unit.hp = 0
	_check(game.check_outcome() == "defeat", "Simultaneous final enemy and Alm death is defeat")
	var terminal_turn = game.turn
	var terminal_phase = game.phase
	game.next_phase()
	_check(game.turn == terminal_turn and game.phase == terminal_phase, "Terminal battle cannot advance another phase")

func _test_save_transactions() -> void:
	var game = _fresh(true)
	game.start_battle()
	game.rng_state = 137
	game.frame_counter = 29
	game.turn = 3
	game.flags.extra_flag = true
	_check(game.save_game(), "Isolated atomic save succeeds")
	var loaded = GameState.new()
	loaded.save_path = SAVE
	_check(loaded.load_game(), "Isolated save can be reloaded")
	_check(_equivalent(loaded.units, game.units) and loaded.party == game.party and _equivalent(loaded.flags, game.flags), "Reload preserves roster, HP, flags and deployment")
	_check(loaded.rng_state == 137 and loaded.frame_counter == 29 and loaded.turn == 3, "Reload preserves deterministic RNG and turn")
	_check(not FileAccess.file_exists(SAVE + ".tmp"), "Atomic rename leaves no temporary save")
	var origin = GameState.pos(game.find_unit("alm"))
	_check(game.select_unit("alm") and game.move_selected(Vector2i(7, 5)), "Move preview enters a legal square")
	_check(game.save_game() and loaded.load_game(), "Save during pending move can be read")
	_check(GameState.pos(loaded.find_unit("alm")) == origin, "Autosave cannot commit a pending move without its action")
	game.cancel_move()
	_check(GameState.pos(game.find_unit("alm")) == origin, "Save leaves original pending move cancellable")
	var before_party = loaded.party.duplicate()
	var file = FileAccess.open(SAVE, FileAccess.WRITE)
	file.store_string('{"version":2}')
	file.close()
	_check(not loaded.load_game() and loaded.party == before_party, "Unsupported save rejected without changing live state")

# JSON intentionally parses all numbers as floats; compare persisted values,
# not the intermediate Variant storage type or string formatting.
func _equivalent(left: Variant, right: Variant) -> bool:
	if typeof(left) in [TYPE_INT, TYPE_FLOAT] and typeof(right) in [TYPE_INT, TYPE_FLOAT]:
		return float(left) == float(right)
	if left is Array and right is Array:
		if left.size() != right.size():
			return false
		for i in range(left.size()):
			if not _equivalent(left[i], right[i]):
				return false
		return true
	if left is Dictionary and right is Dictionary:
		if left.size() != right.size():
			return false
		for key in left:
			if not right.has(key) or not _equivalent(left[key], right[key]):
				return false
		return true
	return left == right

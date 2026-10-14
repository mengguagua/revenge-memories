extends "res://tests/play_round7_late.gd"
## First chapter's not-yet-naturally-won maps only. Inherit real input helpers.
const Worlds = preload("res://core/world_armies.gd")
const CHAPTER_SAVE := "res://reports/round8-chapter1-save.json"
const CHAPTER_REPORT := "res://reports/round8-chapter1-playthrough.json"
var milestones: Array = []
var defensive_anchor := Vector2i.ZERO

func battle() -> void:
	if OS.get_cmdline_user_args().has("--native-auto"):
		var stage: int = ui.game.stage_id
		var record := {"stage":stage,"name":ui.game.battle_data.name_zh,"entry_enemies":ui.game.living("enemy").duplicate(true),"entry_players":ui.game.living("player").duplicate(true),"turns":[]}
		var batches := 0
		while ui.view == "battle" and ui.game.battle_outcome.is_empty() and batches < 60 and not abort:
			batches += 1
			key(KEY_S)
			choose("assault")
			await settle()
			record.turns.append({"turn":ui.game.turn,"outcome":ui.game.battle_outcome,"player_alive":ui.game.living("player").size(),"enemy_alive":ui.game.living("enemy").size()})
			print("ROUND8_NATIVE_AUTO ",stage," turn ",ui.game.turn," allies ",ui.game.living("player").size()," enemies ",ui.game.living("enemy").size()," ",ui.game.battle_outcome)
		record.outcome = ui.game.battle_outcome
		record.final_turn = ui.game.turn
		record.final_players = ui.game.living("player").duplicate(true)
		record.settled = ui.game.battle_settled
		record.operation = "Actual S -> auto-assault; native player and enemy AI, unchanged units"
		battles.append(record)
		if ui.view == "victory" and not abort:
			key(KEY_Z)
			choose("continue_world")
			await settle()
		else:
			abort = true
		return
	var positions: Array = ui.game.living("player").map(func(u): return State.pos(u))
	var total := Vector2i.ZERO
	for cell in positions: total += cell
	defensive_anchor = Vector2i(roundi(float(total.x)/positions.size()),roundi(float(total.y)/positions.size()))
	await super.battle()

func rank(unit: Dictionary) -> int:
	if str(unit.id) == "alm": return 0
	if int(unit.class_id) in [17,18]: return 3
	return 1 if str(unit.id) in ["gray","lukas"] else 2

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
	for i in range(values.size()): amount += values[i]
	return amount

func plan(unit: Dictionary) -> Dictionary:
	var origin := State.pos(unit)
	var graph: Dictionary = ui.game.reachable(unit)
	var opponents: Array = ui.game.living("enemy")
	# Map3: clear the isolated western mercenary together before the east group.
	var mercenary: Dictionary = ui.game.find_unit("g03_02")
	if ui.game.stage_id == 3 and not mercenary.is_empty() and int(mercenary.hp) > 0:
		opponents = [mercenary]
	var nearest := 999
	for enemy in opponents: nearest = mini(nearest, distance(origin, State.pos(enemy)))
	var best := {"kind": "wait", "cell": origin, "score": -INF, "target": "", "spell": -1}
	var weapons: Array = [-1]
	for spell in Items.spells(unit):
		if not Items.is_support(spell) and Items.can_use(unit, spell): weapons.append(spell)
	for cell in graph.costs:
		if not ui.game.can_stop(unit, cell): continue
		var candidate: Dictionary = unit.duplicate(true)
		candidate.position = [cell.x, cell.y]
		var danger := risk(candidate, cell)
		var next_nearest := 999
		for enemy in opponents: next_nearest = mini(next_nearest, distance(cell, State.pos(enemy)))
		var hold := false
		var score: float = 2.0 * (nearest - next_nearest) - danger + ui.game.terrain_avoid(cell) * 0.12
		var raw_tile: int = ui.game.battle_data.map.tiles[cell.y * int(ui.game.battle_data.map.width) + cell.x]
		if raw_tile == 218: score += (int(unit.max_hp) - int(unit.hp)) * 2.0
		if int(unit.class_id) in [17,18]:
			var tank_distance := 999
			for tank in ui.game.living("player"):
				if str(tank.id) in ["alm","lukas","gray"]: tank_distance = mini(tank_distance,distance(cell,State.pos(tank)))
			score = -danger - tank_distance * 2.0
		if danger >= int(unit.hp) - 3: score -= 1000.0
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
				if str(target.id) == "alm" and int(target.hp) < 22: heal_score += 80.0
				if danger >= int(unit.hp) - Items.cost(spell) - 4: heal_score -= 1000.0
				if heal_score > best.score: best = {"kind": "heal", "cell": cell, "score": heal_score, "target": str(target.id), "spell": spell}
		for weapon in weapons:
			candidate.erase("weapon_index")
			if weapon >= 0: candidate.weapon_index = weapon
			for enemy in ui.game.targets(candidate):
				if not opponents.has(enemy): continue
				if ui.game.stage_id == 7 and int(enemy.get("character_id",0)) == 155: continue
				var guarded: Dictionary = enemy.duplicate(true)
				guarded.story_invulnerable = Rules.boss_guard(guarded, ui.game.turn)
				if Rules.attack_blocked(candidate, guarded): continue
				var d := distance(cell, State.pos(enemy))
				if int(unit.class_id) in [17,18] and d < 2: continue
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
				if hold: attack_score -= distance(cell,defensive_anchor) * 2.0
				if ui.game.stage_id == 7 and int(enemy.get("character_id",0)) == 147: attack_score += 80.0
				if ui.game.stage_id == 3 and str(enemy.id) == "g03_02":
					attack_score += 100.0 if int(unit.class_id) in [17,18] else 20.0
					if counter * 2 >= int(unit.hp) - 4: attack_score -= 1000.0
				elif after_risk + counter + Items.cost(Rules.weapon_index(candidate)) * strikes >= int(unit.hp) - 4: attack_score -= 1000.0
				if attack_score > best.score: best = {"kind": "attack", "cell": cell, "score": attack_score, "target": str(enemy.id), "spell": weapon}
	return best

func hub_choose(value: Variant) -> void:
	var hub = ui.hub_controller
	var steps := 0
	while ui.view == "hub_choice" and steps < 50:
		if hub.choices[hub.choice_index].value == value:
			key(KEY_Z)
			await settle()
			return
		key(KEY_DOWN)
		steps += 1
	record_failure("Visible hub choices do not contain " + str(value))

func interact_at(at: Vector2i) -> void:
	var room: int = ui.game.hub_id
	for direction in [Vector2i.DOWN,Vector2i.UP,Vector2i.LEFT,Vector2i.RIGHT]:
		var cell: Vector2i = at + direction
		if ui.hub_controller._ground(cell) and (cell == ui.game.hub_position or not hub_path(cell).is_empty()):
			await walk_hub(cell)
			if abort or ui.game.hub_id != room: return
			var face: Vector2i = at - cell
			key(KEY_RIGHT if face.x > 0 else KEY_LEFT if face.x < 0 else KEY_DOWN if face.y > 0 else KEY_UP)
			key(KEY_Z)
			await settle()
			return
	record_failure("Actual source room has no path to interaction " + str(at))

func talk_actor(id: int) -> void:
	var actor: Dictionary = ui.hub_controller.actors.get(id,{})
	if actor.is_empty() or actor.get("hidden",false):
		record_failure("Required visible actor missing: " + str(id))
		return
	await interact_at(Vector2i(actor.position[0],actor.position[1]))

func checkpoint(name: String) -> void:
	ui.game.save_game()
	milestones.append({"name":name,"view":ui.view,"chapter":ui.game.chapter,"world":ui.game.world_node,"room":ui.game.hub_id,
		"party":ui.game.party.duplicate(),"battles_won":battles.filter(func(b):return b.outcome == "victory").map(func(b):return b.stage)})
	var file := FileAccess.open(CHAPTER_REPORT,FileAccess.WRITE)
	file.store_string(JSON.stringify({"preparation":preparation,"battles":battles,"operations":operations,"milestones":milestones,
		"failures":failures,"aborted":abort,"input_events":inputs,"waited_frames":waits,
		"previous_passed_battles_replayed":0,"screenshots":0,"user_save_accessed":false},"  ")+"\n")
	print("ROUND8 CHECKPOINT ",name," view=",ui.view," chapter=",ui.game.chapter)

func prepare_first_chapter() -> void:
	ui.game.new_game()
	for id in ["lukas","gray","tobin","kliff"]: ui.game.recruit(id)
	ui.game.flags.heard_lukas = true
	ui.game.flags.mycen_refused = true
	ui.game.flags.joined_deliverance = true
	ui.game._bridge_opening_flags()
	for node in [1,2]:
		for identity in Worlds.instance_ids_at(ui.game,node).duplicate(): Worlds.remove(ui.game,str(identity))
	ui.game.cleared_stages = [1,2]
	ui.game.world_node = 2
	ui.game.previous_world_node = 1
	ui.game.route_positions.alm = 2
	ui.game.remember_world_approach()
	ui.game.mode = "world"
	ui.view = "world"
	preparation.append({"scope":"Source initial five-member chapter1 checkpoint at cleared road2",
		"reused_evidence":"reports/second-stage-flow-verification.json natural stages1/2 wins",
		"early_growth_or_exp_added":0,"enemy_changes":0,
		"limit":"Previous early battle stats were not preserved; use conservative initial character templates instead of replaying passed battles."})
	checkpoint("initial_checkpoint_after_previously_passed_maps1_2")

func thief_shrine() -> void:
	move_world(80)
	key(KEY_Z)
	await settle()
	await cross_hub(Vector2i.UP)
	if ui.view == "battle": await battle()
	if abort: return
	await cross_hub(Vector2i.UP)
	await talk_actor(2)
	if not ui.game.party.has("silque"): record_failure("Thief shrine dialogue did not recruit Silque")
	await interact_at(Vector2i(11,3))
	await hub_choose("gray")
	await hub_choose(8)
	if int(ui.game.roster.gray.class_id) != 8: record_failure("Displayed mercenary promotion did not apply")
	await cross_hub(Vector2i.DOWN)
	await cross_hub(Vector2i.DOWN)
	await cross_hub(Vector2i.DOWN)
	checkpoint("thief_shrine_recruitment_promotion_and_return")

func fortress() -> void:
	move_world(50)
	key(KEY_Z)
	await settle()
	await talk_actor(2)
	if not ui.game.party.has("clair"): record_failure("Fortress captive conversation did not recruit Clair")
	await interact_at(Vector2i(18,3))
	await cross_hub(Vector2i.DOWN)
	checkpoint("southern_fortress_recruitment_treasure_and_exit")

func base() -> void:
	move_world(51)
	key(KEY_Z)
	await settle()
	await cross_hub(Vector2i.UP)
	if ui.view == "battle": await battle()
	if abort: return
	await cross_hub(Vector2i.UP)
	await talk_actor(2)
	await talk_actor(3)
	if not ui.game.party.has("clive") or not ui.game.party.has("forsyth"):
		record_failure("Source liberation base conversations did not recruit leaders")
	await cross_hub(Vector2i.DOWN)
	await cross_hub(Vector2i.DOWN)
	await talk_actor(2)
	if not ui.game.party.has("python"): record_failure("Base entrance conversation did not recruit Python")
	await cross_hub(Vector2i.DOWN)
	checkpoint("liberation_base_recruits_and_actual_return")

func castle() -> void:
	move_world(52)
	key(KEY_Z)
	await settle()
	await interact_at(Vector2i(15,17))
	await walk_hub(Vector2i(3,1))
	await talk_actor(3)
	if ui.game.chapter != 2 or ui.game.route != "celica" or ui.game.hub_id != 5:
		record_failure("Actual first chapter castle stairs/conversation failed to enter chapter2")
	checkpoint("chapter1_completed_actual_castle_stairs_and_transition")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = CHAPTER_SAVE
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.animation_speed = 100.0
	ui.instant_mode = false
	var first_stage := 3
	if OS.get_cmdline_user_args().has("--continue"):
		var previous := State.read_json(CHAPTER_REPORT)
		battles = previous.get("battles",[])
		operations = previous.get("operations",[])
		preparation = previous.get("preparation",[])
		milestones = previous.get("milestones",[])
		inputs = int(previous.get("input_events",0))
		waits = int(previous.get("waited_frames",0))
		key(KEY_DOWN)
		key(KEY_Z)
		await settle()
		first_stage = ui.game.stage_id
		if ui.view == "defeat":
			key(KEY_Z)
			choose("retry")
			await settle()
		if ui.view != "battle": record_failure("Continue did not restore the unfinished chapter1 battle")
		checkpoint("resume_unwon_battle_without_replaying_prior_wins")
		if OS.get_cmdline_user_args().has("--prepare-mage"):
			# The previous two wins lack a preserved growth roster. Isolate one
			# achievable early training level instead of replaying those maps.
			# Promotion itself is through the real source statue and input.
			ui.game.roster.tobin.level = 3
			ui.game.world_node = 2
			ui.game.previous_world_node = 1
			ui.game.route_positions.alm = 2
			ui.game.hub_used.dungeon_visited = 1
			ui.hub_controller.enter(32,Vector2i(11,4))
			await interact_at(Vector2i(11,3))
			await hub_choose("tobin")
			await hub_choose(15)
			preparation.append({"unit":"tobin","early_training_level_checkpoint":3,"random_growth_stats_added":0,
				"promotion":"real statue input -> source Mage minima","reason":"Preceding maps1/2 growth stats were not retained; this preparation is explicitly a fixture, not an earned-growth claim."})
			await cross_hub(Vector2i.DOWN)
			await cross_hub(Vector2i.DOWN)
			await cross_hub(Vector2i.DOWN)
			checkpoint("explicit_source_early_mage_preparation_no_old_battle_replay")
	else:
		prepare_first_chapter()
		await thief_shrine()
	for stage in range(first_stage,8):
		if abort: break
		if ui.view != "battle":
			move_world(stage)
			key(KEY_Z)
			await settle()
		if ui.view != "battle" or ui.game.stage_id != stage:
			record_failure("New first-chapter road did not open its actual battlefield " + str(stage))
			break
		await battle()
		checkpoint("new_natural_battle_" + str(stage))
		if abort: break
		if stage == 4: await fortress()
		if stage == 6: await base()
		if stage == 7: await castle()
	checkpoint("finished" if not abort else "needs_analysis")
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	quit(0 if not abort and failures.is_empty() else 1)

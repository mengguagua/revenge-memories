extends "res://tests/play_round8_chapter1.gd"
## Continuous second chapter from the real round8 monastery save. All actions are keys.
const R9_SAVE := "res://reports/round9-chapter2-save.json"
const R9_REPORT := "res://reports/round9-chapter2-playthrough.json"
var next_step := 0
var source_save_sha := "5b4ee476c8d9ad96544ae3e53a1b37ea5fe16988c49b2f2b780c379760e48dc7"

func rank(unit: Dictionary) -> int:
	if str(unit.id) == "celica": return 0 if ui.game.stage_id == 12 else 2
	if str(unit.id) == "genny": return 3
	return 0 if str(unit.id) in ["saber","valbar","kamui"] else 1

func navigation_to(unit: Dictionary, goal: Vector2i) -> Dictionary:
	# Tactical planning follows ship passages; actual destinations still use game.reachable.
	var costs: Dictionary = {goal:0}
	var queue: Array = [goal]
	while not queue.is_empty():
		queue.sort_custom(func(a,b):return int(costs[a]) < int(costs[b]))
		var cell: Vector2i = queue.pop_front()
		for direction in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var next: Vector2i = cell + direction
			if not ui.game.in_bounds(next) or ui.game.movement_cost(unit,next) >= 255: continue
			var value: int = int(costs[cell]) + ui.game.movement_cost(unit,cell)
			if not costs.has(next) or value < int(costs[next]):
				costs[next] = value
				if not queue.has(next): queue.append(next)
	return costs

func plan(unit: Dictionary) -> Dictionary:
	var origin := State.pos(unit)
	var graph: Dictionary = ui.game.reachable(unit)
	var opponents: Array = ui.game.living("enemy")
	var mercenary: Dictionary = ui.game.find_unit("g10_02")
	if ui.game.stage_id == 10 and not mercenary.is_empty() and int(mercenary.hp) > 0: opponents = [mercenary]
	var nearest := 999
	for enemy in opponents: nearest = mini(nearest, distance(origin, State.pos(enemy)))
	var cantor: Dictionary = ui.game.find_unit("g12_01")
	var navigation: Dictionary = navigation_to(unit,State.pos(cantor)) if ui.game.stage_id == 12 and not cantor.is_empty() else {}
	if ui.game.stage_id == 12 and not cantor.is_empty() and int(cantor.hp) > 0: nearest = int(navigation.get(origin,999))
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
		if ui.game.stage_id == 12 and not cantor.is_empty() and int(cantor.hp) > 0: next_nearest = int(navigation.get(cell,999))
		var hold := false
		var score: float = 3.0 * (nearest - next_nearest) - danger * 0.7 + ui.game.terrain_avoid(cell) * 0.12
		if str(unit.id) != "celica": score -= distance(cell,State.pos(ui.game.find_unit("celica"))) * 0.7
		var raw_tile: int = ui.game.battle_data.map.tiles[cell.y * int(ui.game.battle_data.map.width) + cell.x]
		if raw_tile == 218: score += (int(unit.max_hp) - int(unit.hp)) * 2.0
		if int(unit.class_id) in [17,18]:
			var tank_distance := 999
			for tank in ui.game.living("player"):
				if str(tank.id) == "celica": tank_distance = mini(tank_distance,distance(cell,State.pos(tank)))
			score = -danger - tank_distance * 2.0
		if danger >= int(unit.hp) - 3: score -= 1000.0 if str(unit.id) == "celica" else 60.0
		if ui.game.stage_id == 12 and str(unit.id) != "genny": score += (nearest - next_nearest) * 6.0
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
				if str(target.id) == "celica" and int(target.hp) < int(target.max_hp) * 3 / 4: heal_score += 80.0
				if danger >= int(unit.hp) - Items.cost(spell) - 1: heal_score -= 1000.0
				if heal_score > best.score: best = {"kind": "heal", "cell": cell, "score": heal_score, "target": str(target.id), "spell": spell}
		if str(unit.id) == "genny": continue
		for weapon in weapons:
			candidate.erase("weapon_index")
			if weapon >= 0: candidate.weapon_index = weapon
			for enemy in ui.game.targets(candidate):
				if not opponents.has(enemy): continue
				if weapon == 26 and int(enemy.class_id) not in [3,5,11,17]: continue
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
				if ui.game.stage_id == 10 and str(enemy.id) == "g10_02": attack_score += 80.0
				if ui.game.stage_id == 12:
					attack_score += 150.0 if str(enemy.id) == "g12_01" else (nearest-int(navigation.get(cell,999))) * 6.0
				if after_risk + counter + Items.cost(Rules.weapon_index(candidate)) * strikes >= int(unit.hp) - 4: attack_score -= 1000.0 if str(unit.id) == "celica" else 60.0
				if attack_score > best.score: best = {"kind": "attack", "cell": cell, "score": attack_score, "target": str(enemy.id), "spell": weapon}
	return best

func checkpoint(name: String) -> void:
	ui.game.save_game()
	milestones.append({"name":name,"next_step":next_step,"view":ui.view,"chapter":ui.game.chapter,"world":ui.game.world_node,"room":ui.game.hub_id,
		"party":ui.game.party.duplicate(),"living_party":ui.game.party.filter(func(id):return not ui.game.roster[id].get("dead",false)),
		"battles_won":battles.filter(func(b):return b.outcome == "victory").map(func(b):return b.stage)})
	var file := FileAccess.open(R9_REPORT,FileAccess.WRITE)
	file.store_string(JSON.stringify({"source_save_sha256":source_save_sha,"next_step":next_step,"preparation":preparation,"battles":battles,"operations":operations,"milestones":milestones,
		"failures":failures,"aborted":abort,"input_events":inputs,"waited_frames":waits,
		"previous_passed_battles_replayed":0,"screenshots":0,"user_save_accessed":false},"  ")+"\n")
	print("ROUND9 CHECKPOINT ",name," next=",next_step," view=",ui.view," chapter=",ui.game.chapter)

func new_map(stage: int) -> void:
	if battles.any(func(b):return b.stage == stage and b.outcome == "victory"):
		record_failure("Duplicate passed stage guarded: " + str(stage))
		return
	if ui.view != "battle":
		move_world(stage)
		key(KEY_Z)
		await settle()
	if ui.view != "battle" or ui.game.stage_id != stage:
		record_failure("Actual chapter2 world keys failed to enter new map " + str(stage))
		return
	if stage == 12 and int(ui.game.find_unit("genny").get("item_id",0)) == 11:
		var nurse: Dictionary = ui.game.find_unit("genny")
		cursor_to(State.pos(nurse)); key(KEY_Z); key(KEY_Z)
		await settle()
		choose("exchange"); choose("exchange:saber")
		await settle()
		operations.append({"kind":"actual_battle_item_exchange","from":"genny","to":"saber","item":11})
	if stage == 15 and int(ui.game.find_unit("valbar").get("item_id",0)) == 16:
		var leader: Dictionary = ui.game.find_unit("celica")
		cursor_to(State.pos(leader)); key(KEY_Z)
		cursor_to(Vector2i(19,15)); key(KEY_Z)
		await settle()
		choose("exchange"); choose("exchange:valbar")
		await settle()
		operations.append({"kind":"actual_battle_item_exchange","from":"valbar","to":"celica","item":16})
	await battle()
	if not battles.is_empty() and str(battles[-1].outcome) != "victory": abort = true

func enter_place(node: int) -> void:
	move_world(node)
	key(KEY_Z)
	await settle()
	if ui.view != "hub": record_failure("World confirm failed to enter actual room at " + str(node))

func monastery() -> void:
	for actor in [3,4,5]:
		if ui.hub_controller.actors.get(actor,{}).get("hidden",true): continue
		await talk_actor(actor)
		if abort: return
	if not ui.game.party.has("genny") or not ui.game.party.has("boey") or not ui.game.party.has("mae"):
		record_failure("Monastery source dialogues did not recruit the original companions")
		return
	for i in range(int(ui.game.hub_used.get("spring_1",3))):
		await interact_at(Vector2i(3,3) if i < 2 else Vector2i(12,3))
		await hub_choose("celica")
	preparation.append({"scope":"Actual monastery springs","unit":"celica","strength_uses":2,"speed_uses":1,"synthetic_growth":0})
	await cross_hub(Vector2i.UP)

func port() -> void:
	if ui.view != "hub" or ui.game.hub_id != 6: await enter_place(54)
	if abort: return
	if not ui.game.party.has("saber"): await talk_actor(4)
	if not ui.game.party.has("saber"): record_failure("Novis port dialogue did not recruit Saber")
	await walk_hub(Vector2i(17,2))
	if abort: return
	key(KEY_LEFT)
	await settle()
	if ui.view != "world" or ui.game.world_node != 9: record_failure("Walking onto the Novis boat did not sail to actual sea map9")

func pirates() -> void:
	await enter_place(55)
	if abort: return
	for actor in [4,2,3]:
		if not ui.hub_controller.actors.get(actor,{}).get("hidden",true): await talk_actor(actor)
		if abort: return
	operations.append({"kind":"rescued_pirate_allies","recruited":ui.game.party.filter(func(id):return id in ["valbar","kamui","leo"]),"dead":ui.game.roster.keys().filter(func(id):return id in ["valbar","kamui","leo"] and ui.game.roster[id].get("dead",false))})
	await interact_at(Vector2i(15,3))
	await cross_hub(Vector2i.DOWN)

func sea_shrine() -> void:
	await enter_place(56)
	if abort: return
	await cross_hub(Vector2i.UP)
	if ui.view == "battle": await battle()
	if abort: return
	checkpoint("sea_shrine_first_cave_natural_win")
	await cross_hub(Vector2i.UP)
	# Both displayed spring choices share three source uses; choose actual HP blessing.
	for i in range(3):
		await interact_at(Vector2i(15,2))
		await hub_choose("celica")
	await cross_hub(Vector2i.UP)
	if ui.view == "battle": await battle()
	if abort: return
	checkpoint("sea_shrine_treasure_cave_natural_win")
	await interact_at(Vector2i(4,11))
	for i in range(4):
		await cross_hub(Vector2i.DOWN)
		if abort: return
	if ui.view != "world" or ui.game.world_node != 13: record_failure("Sea shrine internal return failed to reach the same world13")
	move_world(12)

func sofia_port() -> void:
	await enter_place(57)
	if abort: return
	for actor in [2,3]: await talk_actor(actor)
	await cross_hub(Vector2i.DOWN)
	if ui.view != "world" or ui.game.world_node != 7: record_failure("Actual harbor south road failed to reach already-cleared castle gate")

func reunion() -> void:
	await enter_place(52)
	if abort: return
	await talk_actor(2)
	await walk_hub(Vector2i(3,1))
	await talk_actor(2)
	if ui.game.chapter != 3: record_failure("Actual Alm reunion did not finish chapter2")

func run() -> void:
	ui = load("res://scenes/main.tscn").instantiate()
	ui.game.save_path = R9_SAVE
	root.add_child(ui)
	await process_frame
	ui.audio.set_music_enabled(false)
	ui.audio.set_sfx_enabled(false)
	ui.animation_speed = 100.0
	ui.instant_mode = false
	if OS.get_cmdline_user_args().has("--continue"):
		var previous := State.read_json(R9_REPORT)
		battles = previous.get("battles",[])
		operations = previous.get("operations",[])
		preparation = previous.get("preparation",[])
		milestones = previous.get("milestones",[])
		next_step = int(previous.get("next_step",0))
		if next_step == 8 and not battles.any(func(b):return b.stage == 12 and b.outcome == "victory"): next_step = 7
		inputs = int(previous.get("input_events",0))
		waits = int(previous.get("waited_frames",0))
	key(KEY_DOWN)
	key(KEY_Z)
	await settle()
	if ui.view == "defeat":
		key(KEY_Z)
		choose("retry")
		await settle()
	checkpoint("resume_actual_second_chapter_checkpoint")
	var names := ["monastery_recruitment_and_springs","graveyard8","novis_port_and_boarding","sea9","sea10","pirate_fortress11","pirate_recruitment_and_treasure","sea12","sea_temple13","sea_shrine_and_return","sea14","sea15","sofia_port_and_castle_road","actual_reunion_chapter3"]
	while next_step < names.size() and not abort:
		match next_step:
			0: await monastery()
			1:
				# Monastery's actual north exit already arrives at cemetery8.
				if ui.view == "world" and ui.game.world_node == 8:
					key(KEY_Z)
					await settle()
				await new_map(8)
			2: await port()
			3:
				if ui.view == "world" and ui.game.world_node == 9:
					key(KEY_Z)
					await settle()
				await new_map(9)
			4: await new_map(10)
			5: await new_map(11)
			6: await pirates()
			7: await new_map(12)
			8: await new_map(13)
			9: await sea_shrine()
			10: await new_map(14)
			11: await new_map(15)
			12: await sofia_port()
			13: await reunion()
		if not abort: next_step += 1
		checkpoint(str(names[next_step-1]) if not abort else "needs_analysis")
	checkpoint("second_chapter_completed" if not abort else "unfinished_checkpoint_preserved")
	ui.audio.stop_all()
	ui.queue_free()
	await process_frame
	quit(0 if not abort and failures.is_empty() else 1)

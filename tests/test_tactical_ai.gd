extends SceneTree
const AI = preload("res://core/tactical_ai.gd")
const State = preload("res://core/game_state.gd")

class ControlledGame extends "res://core/game_state.gd":
	var rolls: Array = []
	func random_bounded(upper: int) -> int:
		return clampi(int(rolls.pop_front()), 0, upper - 1) if not rolls.is_empty() else upper - 1

var checks = 0
var failures: Array = []
func check(value: bool, message: String) -> void:
	checks += 1
	if not value:
		failures.append(message)
		push_error(message)
func unit(id: String, cid: int, cell: Vector2i, side: String = "enemy") -> Dictionary:
	return {"id": id, "class_id": cid, "class": "class_%d" % cid, "name_id": 176 + cid if side == "enemy" else 1,
		"character_id": 176 + cid if side == "enemy" else 1, "side": side, "hp": 30, "max_hp": 30,
		"position": [cell.x, cell.y], "acted": false, "move": 4, "strength": 10, "defence": 4,
		"resistance": 0, "speed": 5, "skill": 5, "luck": 0, "item_id": 0, "magic_flags": 0, "ai_flags": 0}
func setup(g, actors: Array) -> void:
	g.units = actors
	g.rolls = []
	g.frame_counter = 0
	g.battle_data = g.stages[1].duplicate(true)
	g.battle_data.map.width = 16
	g.battle_data.map.height = 16
	g.battle_data.map.tiles = []
	g.battle_data.map.tiles.resize(256)
	g.battle_data.map.tiles.fill(0)
	g.battle_data.terrain.tile_categories["0"] = 0
	g.battle_data.terrain.tile_categories["1"] = 15
	g.battle_data.terrain.tile_categories["2"] = 8
	for cid in range(1, 23):
		var costs = []
		costs.resize(32); costs.fill(1)
		g.battle_data.terrain.movement_by_class_and_category[str(cid)] = costs
func tile(g, at: Vector2i, id: int) -> void:
	g.battle_data.map.tiles[at.y * 16 + at.x] = id
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var g = ControlledGame.new()
	var a = unit("a", 14, Vector2i(3, 3))
	var b = unit("b", 21, Vector2i(8, 3), "player")
	setup(g, [a, b])
	var result = AI.action(g, a)
	check(result.target == "b" and result.spell_id == -1, "physical attack and physical sentinel")
	check(g.reachable(a).costs.has(result.destination) and g.can_stop(a, result.destination), "physical destination legally reachable")
	check(a.position == [3, 3] and a.hp == 30, "planner does not move or damage actor")
	a.ai_flags = 8
	result = AI.action(g, a)
	check(result.target == "" and result.destination == Vector2i(3, 3) and a.ai_flags == 0, "source skip-one flag is cleared")
	for cid in range(1, 23):
		a = unit("a", cid, Vector2i(4, 4))
		a.magic_flags = 1
		b = unit("b", 21, Vector2i(7, 4), "player")
		setup(g, [a, b])
		result = AI.action(g, a)
		check(g.can_stop(a, result.destination) and g.reachable(a).costs.has(result.destination), "class %d legal destination" % cid)
		check(str(result.target).is_empty() or result.target == "a" or result.target == "b", "class %d live known target" % cid)
	a = unit("mage", 15, Vector2i(4, 4)); a.magic_flags = 6
	b = unit("b", 21, Vector2i(6, 4), "player")
	setup(g, [a, b]); result = AI.action(g, a)
	check(result.spell_id == 32 and result.target == "b", "enemy mage selects first lower active spell bit")
	a.hp = AI.Items.cost(32); a.magic_flags = 2; a.move = 0
	result = AI.action(g, a)
	check(result.target == "", "spell HP must be strictly greater than its cost")
	a = unit("bow", 20, Vector2i(4, 4)); a.move = 0
	b = unit("b", 21, Vector2i(9, 4), "player")
	setup(g, [a, b]); result = AI.action(g, a)
	check(result.target == "b", "bow knight source five-tile range")
	a = unit("lancer", 1, Vector2i(4, 4)); a.move = 0; a.item_id = 4
	b.position = [6, 4]; setup(g, [a, b]); result = AI.action(g, a)
	check(result.target == "b" and result.spell_id == -1, "javelin selection uses held weapon, not magic")
	a = unit("injured", 2, Vector2i(3, 3)); a.hp = 8; a.ai_flags = 128
	b = unit("b", 21, Vector2i(4, 3), "player")
	setup(g, [a, b]); tile(g, Vector2i(3, 7), 1); result = AI.action(g, a)
	check((a.ai_flags & 3) == 1 and result.target == "" and result.destination == Vector2i(3, 7), "all-class source healing retreat overrides adjacent attack")
	a.position = [3, 7]; a.hp = 20; g.frame_counter = 1
	result = AI.action(g, a)
	check((a.ai_flags & 3) == 0, "source odd-frame half-health resumes prior mode")
	a = unit("follower", 2, Vector2i(3, 3)); a.ai_flags = 2
	var leader = unit("enemy_leader", 1, Vector2i(3, 10))
	b = unit("b", 21, Vector2i(14, 3), "player")
	setup(g, [leader, a, b]); result = AI.action(g, a)
	check(result.destination == Vector2i(3, 7), "mode2 follows own commander rather than Alm")
	leader.hp = 0; result = AI.action(g, a)
	check((a.ai_flags & 3) == 0, "dead commander restores attack mode")
	a = unit("guard", 2, Vector2i(3, 3)); a.ai_flags = 3
	setup(g, [a, b]); tile(g, Vector2i(5, 5), 2); result = AI.action(g, a)
	check(result.destination == Vector2i(5, 5), "mode3 seeks source defensive terrain")
	a = unit("witch", 16, Vector2i(2, 2)); a.magic_flags = 1
	b = unit("b", 21, Vector2i(10, 10), "player")
	setup(g, [a, b]); g.rolls = [0, 0]; result = AI.action(g, a)
	check(result.teleport and result.teleport_position == Vector2i(6, 6), "witch source joint-byte landing offset")
	check(a.position == [2, 2], "witch plan leaves actual position to game settlement")
	a.hp = 10; g.rolls = [0, 0]; result = AI.action(g, a)
	check(not result.teleport and g.rolls.size() == 2, "low HP witch does not consume teleport randomness")
	a.hp = 30; a.name_id = 142; g.rolls = [200, 8]; result = AI.action(g, a)
	check(result.get("special") == "summon" and result.source_summon.class_id == 16 and result.source_summon.count == 5 and not result.teleport, "named witch conjures witches instead of teleporting")
	check(result.source_summon.magic_flags == 1 and result.source_summon.ai_flags == 200 and not result.source_summon.no_experience, "witch summon keeps original spell/flags/experience")
	a = unit("cantor", 19, Vector2i(3, 3)); a.magic_flags = 128
	b = unit("b", 21, Vector2i(4, 3), "player")
	setup(g, [a, b]); g.rolls = [128, 6]; result = AI.action(g, a)
	check(result.get("special") == "summon" and result.source_summon.class_id == 5 and result.source_summon.hp_cost == 6 and result.source_summon.count == 4, "cantor high-bit class, HP cost and quantity")
	check(result.destination == Vector2i(3, 3) and a.hp == 30, "summon replaces attack and leaves HP settlement to game")
	a.magic_flags = 4; g.rolls = [128, 6]; result = AI.action(g, a)
	check(result.source_summon.level == 5 and result.source_summon.ai_flags == 8 and result.source_summon.source_template_index == 11, "cantor with no high spell bits uses level5 template11")
	a.magic_flags = 128
	a.hp = 6; g.rolls = [128, 6]; result = AI.action(g, a)
	check(result.target == "" and not result.support, "cantor cannot spend last HP")
	a.hp = 30; g.rolls = [127]; result = AI.action(g, a)
	check(result.target == "", "cantor never initiates ordinary attack")
	for i in range(19): g.units.append(unit("extra%d" % i, 1, Vector2i(8 + i % 5, 8 + i / 5)))
	g.rolls = [255, 6]; result = AI.action(g, a)
	check(not result.support and g.rolls.size() == 2, "twenty-enemy cap prevents conjure and does not draw RNG")
	a = unit("mogall", 18, Vector2i(2, 2)); a.move = 0
	b.position = [12, 12]; setup(g, [a, b]); g.rolls = [2]; result = AI.action(g, a)
	check(result.get("special") == "summon" and result.source_summon.count == 3 and result.source_summon.class_id == 18, "idle Mogall splits source 1..4")
	b.position = [3, 2]; result = AI.action(g, a)
	check(result.target == "b" and not result.support, "Mogall attacks when target reachable")
	a = unit("duma", 21, Vector2i(3, 3)); a.name_id = 167; a.character_id = 167; a.hp = 40; a.max_hp = 182
	b.position = [4, 3]; setup(g, [a, b]); g.rolls = [31]; result = AI.action(g, a)
	check(result.get("special") == "quake" and result.quake.hp_floor == 1 and result.quake.player_base == 10, "Duma Gaia source chance and nonlethal rule")
	g.rolls = [32, 3]; result = AI.action(g, a)
	check(result.get("special") == "summon" and result.source_summon.level == 5 and result.source_summon.count == 4, "Duma lower form waits/splits level5 Mogalls")
	a = unit("healer", 15, Vector2i(3, 3)); a.magic_flags = 16; a.move = 0
	var wounded = unit("wounded", 2, Vector2i(3, 4)); wounded.hp = 2
	b.position = [13, 13]; setup(g, [a, wounded, b]); result = AI.action(g, a)
	check(result.support and result.spell_id == 35 and result.target == "wounded", "source arcanist heals adjacent ally")
	a.magic_flags = 48; g.rolls = [64]; result = AI.action(g, a)
	check(not result.support, "Fortify chance failure does not fall through to Recover")
	g.rolls = [63]; result = AI.action(g, a)
	check(result.support and result.spell_id == 36, "Fortify source quarter chance")
	var report = {"checks": checks, "failures": failures, "failure_count": failures.size()}
	var f = FileAccess.open("res://reports/tactical-ai-tests.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  ") + "\n"); f.close()
	print(JSON.stringify(report))
	quit(0 if failures.is_empty() else 1)

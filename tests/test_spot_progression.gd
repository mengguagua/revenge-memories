extends SceneTree
const State = preload("res://core/game_state.gd")
const Rules = preload("res://core/combat_rules.gd")
const Items = preload("res://core/item_rules.gd")
const Progression = preload("res://core/unit_progression.gd")
var checks := 0
var errors: Array[String] = []
var details: Dictionary = {}
func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: errors.append(label); push_error(label)

func adjacent(game, actor: Dictionary, target: Dictionary, distance: int = 1) -> void:
	for direction in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		var at = game.pos(target) + direction * distance
		if game.in_bounds(at) and game.can_stop(actor, at) and game.movement_cost(actor, at) < 255:
			actor.position = [at.x, at.y]
			return
	check(false, "fixture has a legal in-bounds position")

func run() -> void:
	var game = State.new()
	game.new_game()
	game.chapter = 2
	game.route = "celica"
	game.party = []
	game.recruit("celica"); game.recruit("mae")
	game.world_armies.clear(); game.world_node = 15
	game.start_battle(15, [], true)
	var mage: Dictionary = game.find_unit("mae")
	var target: Dictionary = game.find_unit("g15_02")
	adjacent(game, mage, target, 3)
	mage.hp = 5; mage.weapon_index = 24
	game.rng_state = 20
	var exchange: Dictionary = game.plan_combat("mae", "g15_02")
	check(exchange.events.size() == 2 and exchange.events.all(func(e): return e.attacker == "mae"), "source Mae doubles with Thunder at range3 without enemy counter")
	check(exchange.events.any(func(e): return not e.hit), "seeded natural exchange includes a missed spell")
	check(exchange.events[0].source_hp_after == 3 and exchange.events[1].source_hp_after == 1, "each Thunder strike including a miss costs2 HP")
	for event in exchange.events: game.commit_strike(event)
	check(mage.hp == 1, "actual native settlement preserves last HP")
	mage.hp = 4; mage.acted = false; mage.weapon_index = 24
	var limited: Dictionary = game.plan_combat("mae", "g15_02")
	check(limited.events.size() == 1 and limited.events[0].source_hp_after == 2, "follow-up stops when another cast would spend final HP")
	mage.hp = 2
	check(game.plan_combat("mae", "g15_02").is_empty(), "cannot initiate a spell with exactly its HP cost")
	details.thunder = exchange.events.duplicate(true)

	game.new_game(); game.recruit("silque"); game.world_armies.clear(); game.world_node = 1
	game.start_battle(1, [], true)
	var healer: Dictionary = game.find_unit("silque")
	var ally: Dictionary = game.find_unit("alm")
	adjacent(game, healer, ally)
	healer.hp = 3; ally.hp = 1; game.rng_state = 201
	var healed: Dictionary = game.use_support("silque", 40, "alm")
	check(not healed.is_empty() and ally.hp == 17 and healer.hp == 1, "source Recover repeats twice and spends2 HP when3 are available")
	check(healer.exp == 0 and healer.level == 1 and healer.acted, "white magic spends the action and does not grant combat EXP")
	healer.hp = 2; healer.acted = false; ally.hp = 1; game.rng_state = 201
	game.use_support("silque", 40, "alm")
	check(ally.hp == 9 and healer.hp == 1, "Recover cannot repeat when only one cast is payable")
	healer.hp = 18; healer.acted = false; ally.hp = int(ally.max_hp) - 1; game.rng_state = 201
	game.use_support("silque", 40, "alm")
	check(ally.hp == ally.max_hp and healer.hp == 17, "fully healed target prevents redundant second cost")
	healer.acted = false; var before_rng: int = game.rng_state
	check(game.use_support("silque", 40, "alm").is_empty() and healer.hp == 17 and not healer.acted and game.rng_state == before_rng, "invalid full-HP recovery spends no HP/action/RNG")
	var enemy: Dictionary = game.living("enemy")[0]
	adjacent(game, healer, enemy)
	healer.hp = 5; healer.weapon_index = 42; enemy.hp = 3
	game.rng_state = 0
	var drain: Dictionary = game.plan_combat("silque", str(enemy.id))
	check(not drain.events.is_empty() and drain.events[0].hit, "seeded source Nosferatu lands")
	check(drain.events[0].damage == 3 and drain.events[0].heal == 3 and drain.events[0].hp_cost == 0, "Nosferatu heals actual HP taken without overkill healing")
	for event in drain.events: game.commit_strike(event)
	check(healer.hp == 8 and enemy.hp == 0, "actual drain settlement restores exactly3 HP")
	details.nosferatu = drain.events.duplicate(true)

	# All six maxima are reachable by ordinary growth and the Alm story
	# promotion. Use the boundary directly, without altering growth rules.
	ally.level = 19; ally.exp = 99; ally.max_hp = 52; ally.hp = 52; ally.promoted = true
	for stat in ["strength", "skill", "speed", "luck", "defence"]: ally[stat] = 40
	enemy = game.living("enemy")[0]; enemy.hp = 1
	adjacent(game, ally, enemy)
	game.rng_state = 0
	var cap_exchange: Dictionary = game.plan_combat("alm", str(enemy.id))
	for event in cap_exchange.events: game.commit_strike(event)
	var reward: Dictionary = game.finish_exchange(cap_exchange)
	check(reward.leveled and ally.level == 20 and ally.exp < 100, "Lv19 EXP99 advances exactly once to Lv20 with residual EXP below100")
	check(ally.max_hp == 52 and ["strength", "skill", "speed", "luck", "defence"].all(func(stat): return int(ally[stat]) == 40), "growth at stat maxima cannot overflow52/40")
	check(Rules.experience_gain(ally, enemy, 1, 0, true) == 0 and Rules.victory_experience_gain(ally) == 0, "Lv20 gains neither combat nor victory EXP")
	details.cap_reward = reward

	for promotion in Items.data().promotions:
		var unit: Dictionary = game.characters.kliff.duplicate(true)
		unit.class_id = int(promotion.from_class)
		unit.level = int(promotion.level) - 1
		unit.magic_level = 7; unit.magic_flags = 3; unit.resistance = 23 if unit.class_id == 10 else 8
		check(not Progression.promote(unit, int(promotion.to_class)).valid, "class%d rejects promotion below required level" % unit.class_id)
		unit.level += 1
		var result: Dictionary = Progression.promote(unit, int(promotion.to_class))
		check(result.valid and result.unit.level == 1 and result.unit.exp == 0, "class%d promotion threshold accepted and resets level/EXP" % unit.class_id)
		check(result.unit.magic_level == 7, "ordinary promotion preserves personal spell training")
		check(result.unit.resistance == (23 if int(promotion.to_class) == 10 else 8), "class resistance is added/removed once")
	var kliff: Dictionary = game.characters.kliff.duplicate(true)
	kliff.level = 3
	var promoted: Dictionary = Progression.promote(kliff, 15).unit
	var trained: Dictionary = Progression.learn_spells(promoted, 6)
	check(trained.unit.magic_level == 6 and Items.spells(trained.unit) == [23,24,27], "villager->Mage resets then learns Thunder4 and Excalibur7 once")
	trained.unit.level = 12
	var sage: Dictionary = Progression.promote(trained.unit, 19).unit
	check(sage.magic_level == 6 and 40 in Items.spells(sage), "Mage->Sage keeps training and adds recovery bit")
	var advanced: Dictionary = Progression.learn_spells(sage, 4)
	check(advanced.learned == [28] and advanced.unit.magic_level == 10, "promoted Mage learns Arrow at cumulative training11")
	var legal: Dictionary = game.characters.alm.duplicate(true)
	legal.side = "player"; legal.item_id = 20
	check(not Items.can_use(legal,20) and Rules.weapon_index(legal) == 0, "unpromoted Alm cannot equip carried bow")
	legal.promoted = true
	check(Items.can_use(legal,20) and Rules.weapon_index(legal) == 20, "promoted Alm may equip the same bow")
	var carried: Dictionary = game.characters.mae.duplicate(true)
	carried.item_id = 14
	check(not Items.can_use(carried,14) and Rules.weapon_index(carried) == 23, "Mage carrying a sword retains her legal default Fire")
	var report := {"checks": checks, "errors": errors, "details": details,
		"scope": "Original maps15/1 and source actors with reachable HP/growth states; actual plan/commit/support/level settlement; all13 promotion thresholds and spell-training continuity; no saves or visible windows.",
		"source": ["bank009 L09877E HP cost per strike", "bank009 L09896E repeated Recover", "bank009 L0986AA actual Nosferatu damage healing", "bank009 L098858 stat growth and Lv20", "bank008 L08A804/L08A96C promotion", "bank001 L01ADDE spell training"]}
	var out := FileAccess.open("res://reports/spot-progression-verification.json", FileAccess.WRITE)
	out.store_string(JSON.stringify(report, "  ") + "\n"); out.close()
	print(JSON.stringify({"checks":checks,"errors":errors}))
	quit(0 if errors.is_empty() else 1)

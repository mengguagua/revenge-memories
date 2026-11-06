extends SceneTree
## Read-only game-state probes. No player journal is written.
const State = preload("res://core/game_state.gd")
const OUT = "/private/tmp/revenge-balance-hero-probe.json"
var checks: Array[String] = []
var errors: Array[String] = []

func check(condition: bool, label: String):
	checks.append(label)
	if not condition:
		errors.append(label)
		push_error(label)

func _initialize():
	call_deferred("run")

func run():
	var g = State.new()
	g.new_game()
	g.save_path = "/private/tmp/revenge-balance-hero-unused.json"
	var result = {"trade_probe": [], "compatibility": [], "matchups": [], "healing": [], "spell_budgets": []}
	# Trading intentionally permits carrying an incompatible weapon. Its combat
	# effects must be checked independently of permitted ownership.
	var rider = g._initial_character("lance")
	var caster = g._initial_character("eileen")
	g.HeroProfessions.apply(caster)
	caster.magic_flags = 255
	caster.hp = 20
	rider.item_id = 10
	rider.position = [5, 5]
	caster.position = [6, 5]
	g.roster = {"lance": rider.duplicate(true), "eileen": caster.duplicate(true)}
	g.units = [rider, caster]
	g.mode = "battle"
	g.phase = "player"
	var trade = g.Inventory.exchange(g, "lance", "eileen")
	check(trade and caster.item_id == 10 and rider.item_id == 60, "battle trade can still carry incompatible equipment")
	check(rider.acted and not caster.acted, "trade costs the initiator's action without refreshing or consuming the recipient's action")
	var enemy = g.stages[534].enemies.filter(func(u):return str(u.id)=="J54_boss")[0].duplicate(true)
	for id in [23, 24, 25, 26, 27]:
		caster.weapon_index = id
		var held = g.Rules.attack_stats(caster, enemy, 0)
		var empty = caster.duplicate(true)
		empty.item_id = 0
		var plain = g.Rules.attack_stats(empty, enemy, 0)
		result.trade_probe.append({"trade_succeeded": trade, "spell": id, "compatible": g.Items.can_use(caster, 10), "held_item": caster.item_id, "hit_with_incompatible_lance": held.hit, "baseline_hit": plain.hit, "cost": held.hp_cost, "damage": held.damage, "healing": g.Items.phase_effect(caster, 0).heal})
		check(held.hit == plain.hit and held.damage == plain.damage, "incompatible Tide lance cannot improve learned spell " + str(id))
		check(held.hp_cost == g.Items.cost_for(empty,id), "incompatible item does not alter profession cost for spell " + str(id))
	check(g.Items.phase_effect(caster,0).heal == 0, "incompatible Tide lance grants no item recovery")
	var shielded = enemy.duplicate(true)
	shielded.erase("innate_attack_profile")
	shielded.item_id = 52
	caster.weapon_index = 24
	check(g.Rules.attack_stats(caster,shielded,0).hit == 10, "incompatible Tide lance cannot bypass anti-magic shield")
	# Both branches use the actual battle planner, so defender automatic Fire
	# must not accidentally regain the carried lance's guaranteed hit.
	enemy.position = [7,5]
	g.units.append(enemy)
	var attack = g.plan_combat("eileen",str(enemy.id))
	check(not attack.is_empty() and int(attack.stats.eileen.hit) < 100, "real active spell plan does not inherit incompatible lance hit")
	var spell_events = attack.events.filter(func(e):return e.attacker == "eileen")
	check(spell_events.size() == 2 and spell_events.all(func(e):return e.hp_cost == 1 and e.weapon_index == 24), "active spell and follow-up retain discounted per-cast cost")
	enemy.position = [8,5]
	var counter_plan = g.plan_combat(str(enemy.id),"eileen")
	check(not counter_plan.is_empty() and int(counter_plan.stats.eileen.hit) < 100, "real distant counter plan does not inherit incompatible lance hit")
	var counter_events = counter_plan.events.filter(func(e):return e.attacker == "eileen")
	check(counter_events.size() == 2 and counter_events.all(func(e):return e.hp_cost == 1 and e.weapon_index == 23), "distant counter and follow-up keep automatic Fire and its cost")
	var valid_rider = g._initial_character("lance")
	valid_rider.item_id = 10
	valid_rider.hp = 10
	check(g.Rules.attack_stats(valid_rider,enemy,240).hit == 100 and g.Rules.attack_stats(g.Rules.default_counter(valid_rider),enemy,240).hit == 100, "legal Tide lance keeps guaranteed hit on attacks and counters")
	check(g.Items.phase_effect(valid_rider,0).heal == 5, "legal Tide lance retains five-HP recovery")
	var healer = g._initial_character("mireille")
	healer.item_id = 10
	healer.hp = 10
	var plain_healer = healer.duplicate(true)
	plain_healer.item_id = 0
	check(g.Rules.weapon_index(healer) == 42 and g.Rules.attack_stats(healer,enemy,0).hit == g.Rules.attack_stats(plain_healer,enemy,0).hit, "incompatible Tide lance cannot make zero-cost life drain guaranteed")
	check(g.Rules.strike_effect(healer,enemy,false,false).heal == 0, "missed life drain still gives no healing")
	for pair in [["lance",17],["lance",18],["eileen",7],["eileen",9],["eileen",10],["mireille",10],["eileen",17],["hunapu",18]]:
		var unit = g._initial_character(pair[0])
		unit.hp = 10
		unit.item_id = pair[1]
		result.compatibility.append({"unit": pair[0], "item": pair[1], "can_use": g.Items.can_use(unit,pair[1]), "healing": g.Items.phase_effect(unit,0).heal, "description": g.EquipmentComparison.description(unit)})
		var compatible = g.Items.can_use(unit,pair[1])
		check(g.Items.phase_effect(unit,0).heal == (5 if compatible else 0), "item recovery obeys user restriction: " + str(pair))
		check(g.Items.phase_effect(unit,218).heal == 5 and g.Items.phase_effect(unit,0,-1,true).heal == 5, "terrain and saint recovery independent of held weapon: " + str(pair))
		check(g.Items.phase_effect(unit,218,-1,true).heal == 5, "multiple recovery sources do not stack: " + str(pair))
	var sage = g._initial_character("lisa")
	sage.class_id = 19
	sage.item_id = 10
	sage.hp = 10
	check(not g.Items.can_use(sage,10) and g.Items.phase_effect(sage,0).heal == 5, "class 19 innate recovery survives incompatible equipment")
	var dead = valid_rider.duplicate(true)
	dead.hp = 0
	check(g.Items.phase_effect(dead,218,-1,true).heal == 0, "recovery never revives zero-HP carriers")
	var low = caster.duplicate(true)
	low.hp = 1
	low.weapon_index = 24
	check(not g.Rules.can_attack(low), "discounted Thunder still needs HP strictly above its one-HP cost")
	low.hp = 2
	check(g.Rules.strike_effect(low,enemy,false,false).hp_cost == 1, "a missed affordable Thunder pays the reduced cost")
	var sword_user = caster.duplicate(true)
	sword_user.erase("weapon_index")
	sword_user.item_id = 17
	var shield_user = sword_user.duplicate(true)
	shield_user.item_id = 53
	check(g.Rules.weapon_index(sword_user) == 17 and g.Rules.weapon_index(shield_user) == 0, "shield replaces the personal sword in the only equipment slot")
	check(g.Items.physical_defence_bonus(sword_user) == 0 and g.Items.physical_defence_bonus(shield_user) == 5, "personal sword and shield defence cannot stack")
	# Minimum profession bases isolate the guaranteed advancement benefit.
	for hero in ["eileen", "hunapu"]:
		var unit = g._initial_character(hero)
		g.HeroProfessions.apply(unit)
		unit.hp = unit.max_hp
		unit.magic_flags = 255 if hero == "eileen" else 0
		for item in ([0,17,53,55,57,66] if hero == "eileen" else [0,18,22,53,55]):
			unit.item_id = item
			for stage in [501,502,503,504,533,534]:
				for target in g.stages[stage].enemies:
					if not (str(target.id).ends_with("boss") or target.get("campaign_role", "") != "" or int(target.class_id) in [9,10,13,16,19,20,22]): continue
					for weapon in ([-1,23,24,26,27,25] if hero == "eileen" else [-1]):
						unit.erase("weapon_index")
						if weapon >= 0: unit.weapon_index = weapon
						var info = g.Rules.attack_stats(unit, target, 0)
						var counter = g.Rules.attack_stats(g.Rules.default_counter(target,1),unit,0)
						result.matchups.append({"hero":hero,"item":item,"weapon":g.Rules.weapon_index(unit),"target":target.id,"target_hp":target.hp,"damage":info.damage,"hit":info.hit,"critical":info.critical,"cost":info.hp_cost,"speed":info.attack_speed,"enemy_speed":info.defender_attack_speed,"counter_damage":counter.damage,"counter_hit":counter.hit,"enemy_class":target.class_id})
			unit.erase("weapon_index")
			unit.hp = 10
			for saint in [false,true]:
				result.healing.append({"hero":hero,"item":item,"adjacent_saint":saint,"normal":g.Items.phase_effect(unit,0,-1,saint),"heal_tile":g.Items.phase_effect(unit,218,-1,saint),"poison":g.Items.phase_effect(unit,0,16,saint)})
			unit.hp = unit.max_hp
		if hero == "eileen":
			for id in [23,24,26,27,25]:
				result.spell_budgets.append({"spell":id,"hp":unit.max_hp,"before_cost":g.Items.cost(id),"after_cost":g.Items.cost_for(unit,id),"before_max_casts":int((unit.max_hp-1)/g.Items.cost(id)),"after_max_casts":int((unit.max_hp-1)/g.Items.cost_for(unit,id))})
	var file = FileAccess.open(OUT, FileAccess.WRITE)
	result.checks = checks
	result.errors = errors
	result.passed = errors.is_empty()
	file.store_string(JSON.stringify(result,"  "))
	file.close()
	print("BALANCE_HERO_PROBE ", checks.size(), " checks; errors=", errors, " matchup rows=", result.matchups.size(), " output=", OUT)
	quit(0 if errors.is_empty() else 1)

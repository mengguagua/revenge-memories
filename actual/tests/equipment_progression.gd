extends SceneTree
const State = preload("res://core/game_state.gd")
const Items = preload("res://core/item_rules.gd")
const Rules = preload("res://core/combat_rules.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Supply = preload("res://core/equipment_supply.gd")
var checks: Array = []
var failures: Array = []
const OUT = "res://reports/equipment-0.3.9/"
const CACHE = "res://.cache/equipment-0.3.9/"

func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(CACHE))
	call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks.append(label)
	if not ok: failures.append(label); push_error(label)
func fresh():
	var g = State.new(); g.new_game(); g.save_path = CACHE + "working-save.json"; return g
func all_west(g) -> void:
	for id in ["fula", "lena", "lance", "beck", "hervi"]: g.recruit(id)
func all_east(g) -> void:
	g.cleared_stages.append(105); g.flags.chapter1_complete = true; g.begin_chapter_two()
	g.flags.east_recruit_ready = {"lord":true,"roan":true,"shia":true}
	for id in ["lord", "roan", "shia"]: g.recruit(id)
func total(g, route: String, item: int) -> int:
	var n = g.convoy[route].count(item)
	for id in g.parties[route]:
		if int(g.roster[id].item_id) == item: n += 1
	return n
func run() -> void:
	check(Items.data().items.size() == 67, "source item IDs retained; eight campaign weapons appended")
	var source = Items._integer_tables(State.read_json("res://data/legacy/rules_full.json"))
	for i in range(59): check(Items.item(i) == source.items[i], "original definition preserved " + str(i))
	var g = fresh(); var dummy = g._initial_character("otto"); dummy.side = "enemy"; dummy.defence = 0; dummy.speed = 0
	for row in [["hunapu",59,60,11],["otto",61,62,2],["daan",63,64,20]]:
		var u = g._initial_character(row[0]); u.item_id = 0; var base = Rules.attack_stats(u,dummy,0)
		for rank in range(1,3):
			u.item_id = row[rank]
			var stats = Rules.attack_stats(u,dummy,0)
			check(Items.can_use(u,u.item_id) and not stats.magic and stats.damage == base.damage + rank, str(row[0])+" bronze/iron physical damage rank "+str(rank))
			check(Rules.weapon_index(u) == (1 if row[0] == "daan" else 0), "new weapon reuses correct physical animation alias "+str(u.item_id))
			u.weapon_index = 23
			check(Items.weapon_profile(u,23) == Items.item(23), "physical weapon never augments explicitly selected magic")
			u.erase("weapon_index")
		var iron = Rules.attack_range(u); u.item_id = row[3]
		check(Rules.attack_stats(u,dummy,0).damage > base.damage + 2, str(row[0])+" steel remains an upgrade")
		if row[0] == "daan": check(iron == Vector2i(1,3) and Rules.attack_range(u) == Vector2i(1,5), "bronze/iron bows retain short range; steel bow is long range")
	var mage = g._initial_character("hervi"); mage.item_id = 0
	var plain = Rules.attack_stats(mage,dummy,0); var reach = Rules.attack_range(mage); var cost = Rules.magic_cost(mage)
	mage.item_id = 66
	check(Rules.attack_stats(mage,dummy,0).damage == plain.damage+2 and Rules.attack_stats(mage,dummy,0).magic, "iron focus enhances existing attack spell by two")
	check(Rules.magic_cost(mage)==cost and Rules.attack_range(mage)==reach, "focus preserves magic HP cost and reach")
	var healer = g._initial_character("fula"); var patient = g._initial_character("hunapu"); patient.hp=1; healer.item_id=0
	var archer = g._initial_character("daan"); archer.item_id=63
	var flyer = dummy.duplicate(true); flyer.class_id=3
	check(Rules.attack_stats(archer,flyer,0).effective, "new copper bow retains anti-flying effectiveness")
	archer.item_id=64
	check(Rules.attack_stats(archer,flyer,0).effective, "new iron bow retains anti-flying effectiveness")
	var healing = Items.support_effect(healer,patient,35,99); healer.item_id=66
	check(Items.support_effect(healer,patient,35,99)==healing, "focus does not buff healing or invent a new spell")
	check(not Items.can_use(g._initial_character("otto"),59) and not Items.can_use(g._initial_character("daan"),65) and not Items.can_use(healer,62), "sword bow lance and focus restrictions preserved")
	all_west(g)
	check(g.party.size()==8, "first chapter maximum recruitable party has eight members")
	for id in g.party: check(Items.can_use(g.roster[id],g.roster[id].item_id) and Items.item(g.roster[id].item_id).kind=="weapon", "western starter usable: "+id)
	for stage in [101,102,103,104,105]: Supply.award_clear(g,stage,false)
	check(total(g,"alm",49)==1, "one additional fixed western steel shield")
	var west = {"roster":g.roster.duplicate(true),"convoy":g.convoy.alm.duplicate()}
	all_east(g)
	check(g.party.size()==7, "second chapter maximum recruitable party has seven members")
	for id in g.party: check(Items.can_use(g.roster[id],g.roster[id].item_id) and Items.item(g.roster[id].item_id).kind=="weapon", "eastern starter usable: "+id)
	for stage in [201,202,203,204,205,206]: Supply.award_clear(g,stage,false)
	check(total(g,"celica",49)==1, "one additional fixed eastern steel shield")
	check(g.convoy.alm==west.convoy, "eastern rewards cannot take western weapons")
	for id in g.parties.alm: check(g.roster[id]==west.roster[id], "western gear growth and death unchanged on east entry: "+id)
	var stock = g.convoy.duplicate(true)
	for stage in [101,102,103,104,105,201,202,204]: Supply.award_clear(g,stage,false)
	check(g.convoy==stock, "fixed rewards cannot be farmed through repeated settlement")
	for stage in g.stages.values():
		for u in stage.enemies:
			if int(u.item_id)==0: continue
			check(Items.can_use(u,int(u.item_id)), "enemy actually uses carried equipment: "+u.id)
			check(int(u.get("drop_chance",0))==100, "enemy carried equipment declares guaranteed drop: "+u.id)
			check(Inventory.carried_drop(u,0)==int(u.item_id) and Inventory.carried_drop(u,99)==int(u.item_id), "carried equipment is independent of random roll: "+u.id)
	# Real death pipeline, deterministic RNG fixtures, independent from supply.
	var d = fresh(); d.world_node=2; d.start_battle(101)
	var enemy=d.find_unit("M11_e5"); var killer=d.find_unit("hunapu"); killer.item_id=0; d.rng_state=201; enemy.hp=0
	var loot=Inventory.on_death(d,enemy,killer)
	check(not loot.is_empty() and int(loot.item_id)==63 and loot.destination=="convoy", "incompatible empty-handed killer stores declared loot in own convoy")
	check(Inventory.on_death(d,enemy,killer).is_empty(), "duplicate death cannot reroll or duplicate loot")
	d=fresh(); d.world_node=2; d.start_battle(101); enemy=d.find_unit("M11_e1"); killer=d.find_unit("hunapu"); d.rng_state=132; enemy.hp=0
	check(Inventory.on_death(d,enemy,killer).is_empty(), "actual failed ordinary 10 percent roll produces no loot")
	d.rng_state=201
	check(Inventory.on_death(d,enemy,killer).is_empty(), "failed ordinary roll cannot be retried through death processing")
	d=fresh(); d.world_node=2; d.start_battle(101); enemy=d.find_unit("M11_e5"); killer=d.find_unit("hunapu"); enemy.hp=0; enemy.drop_chance=100
	check(not Inventory.on_death(d,enemy,killer).is_empty(), "historical unmodified 100 percent held drops remain compatible")
	# Old save conversion: use an unarmed v0.3.7-like roster with chosen shields.
	var old=fresh(); all_west(old); old.flags.erase("equipment_starter_checked"); old.flags.erase("equipment_clear_rewards")
	for id in old.party: old.roster[id].item_id=0
	old.roster.otto.item_id=48
	old.roster.hervi.hp=0; old.roster.hervi.dead=true
	old.convoy.alm=[]
	var before_old=old.roster.duplicate(true)
	Supply.reconcile(old)
	check(old.roster.otto.item_id==48 and old.convoy.alm.has(61), "old shield choice retained with a usable weapon in reserve")
	check(old.roster.hervi==before_old.hervi, "dead member receives no gear or revival")
	var count=old.convoy.alm.size()
	var roster_once=old.roster.duplicate(true)
	Supply.reconcile(old)
	check(old.roster==roster_once and old.convoy.alm.size()==count, "migration is idempotent")
	old.roster.daan.item_id=0
	Supply.reconcile(old)
	check(old.roster.daan.item_id==0, "later manual unequip does not create free replacement weapons")
	var ancient=fresh(); ancient.save_path="res://reports/campaign/natural-chapter-end-save.json"
	check(ancient.load_game(), "real historical chapter-end save migrates")
	var migrated=ancient.roster.duplicate(true); var supplies=ancient.convoy.duplicate(true)
	ancient.save_path=CACHE+"migrated-save.json"
	check(ancient.save_game(), "migrated historical save writes atomically")
	var loaded=fresh(); loaded.save_path=ancient.save_path
	check(loaded.load_game() and Items._integer_tables(loaded.roster)==Items._integer_tables(migrated) and Items._integer_tables(loaded.convoy)==Items._integer_tables(supplies), "migrated gear persists without duplicate supply after reload")
	d.save_path=CACHE+"battle-save.json"
	check(d.save_game(), "new weapons and enemy probabilities save in actual battle snapshot")
	var resumed=fresh(); resumed.save_path=d.save_path
	check(resumed.load_game() and Items._integer_tables(resumed.units)==Items._integer_tables(d.units) and Items._integer_tables(resumed.convoy)==Items._integer_tables(d.convoy), "in-progress reload preserves exact actors and inventory")
	check(resumed.retry_battle() and int(resumed.find_unit("hunapu").item_id)==59, "retry restores new equipped item instead of farming a grant")
	var base=State.read_json(d.save_path); base.units[0].item_id=67
	var bad=FileAccess.open(CACHE+"invalid-save.json",FileAccess.WRITE); bad.store_string(JSON.stringify(base)); bad.close()
	resumed.save_path=CACHE+"invalid-save.json"; var untouched=resumed.roster.duplicate(true)
	check(not resumed.load_game() and resumed.roster==untouched, "undefined equipment ID rejected before mutation")
	base=State.read_json(d.save_path); base.units[0].drop_chance=101
	bad=FileAccess.open(CACHE+"invalid-save.json",FileAccess.WRITE); bad.store_string(JSON.stringify(base)); bad.close()
	check(not resumed.load_game(), "out-of-range enemy drop chance rejected")
	var report={"version":"0.3.9","passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"scope":"Equipment formulas, full eight/seven-member supply without RNG, all 15 enemy loadouts, guaranteed carried drops, failed ordinary rolls, real historical-save migration, reload/retry and invalid-item rejection. Deterministic boundary fixtures, not a natural playthrough."}
	var file=FileAccess.open(OUT+"checks.json",FileAccess.WRITE); file.store_string(JSON.stringify(report,"  ")); file.close()
	print("EQUIPMENT_PROGRESSION ",JSON.stringify(report)); quit(0 if failures.is_empty() else 1)

extends SceneTree
## Round-two save robustness. Each fixture writes only isolated disposable paths.
const State = preload("res://core/game_state.gd")
const Validator = preload("res://core/campaign_save_validation.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Worlds = preload("res://core/world_armies.gd")
const SAVE := "res://reports/test-save-robustness.json"
var checks := 0
var failures: Array[String] = []
var rejected_cases: Array[String] = []

func _initialize() -> void: call_deferred("run")
func check(ok: bool, label: String) -> void:
	checks += 1
	if not ok: failures.append(label);push_error(label)

func fresh():
	var g = State.new()
	g.save_path = SAVE
	g.new_game();g.recruit("lukas");g.world_node = 1;g.start_battle(1)
	g.story_events.clear()
	return g

func write(value: Variant, raw := false) -> void:
	var f := FileAccess.open(SAVE,FileAccess.WRITE)
	f.store_string(str(value) if raw else JSON.stringify(value));f.close()

func fingerprint(g) -> String:
	var state := {}
	for key in ["stage_id","chapter","route","mode","flags","party","units","roster","phase","turn","rng_state","frame_counter","kills","battle_outcome","world_node","cleared_stages","battle_start_snapshot","victory_rewards","parties","route_positions","previous_world_node","convoy","hub_id","hub_flags","hub_changes","hub_used","battle_return","battle_settled","story_events","encounter_groups","world_armies"]:
		state[key] = g.get(key)
	state.village_position = str(g.village_position)
	state.hub_position = str(g.hub_position)
	return JSON.stringify(state)

func reject(g, value: Variant, label: String, raw := false) -> void:
	write(value,raw)
	var before := fingerprint(g)
	check(g.load_game() == false, label + " returns false")
	check(fingerprint(g) == before, label + " leaves current game untouched")
	rejected_cases.append(label)

func run() -> void:
	var g = fresh()
	g.save_game()
	var base: Dictionary = State.read_json(SAVE)
	for field in {"village_position":[{},0],"turn":{},"phase":[],"battle_outcome":{},"mode":[],"rng_state":[],"frame_counter":"12","kills":-1}:
		var bad: Dictionary = base.duplicate(true)
		bad[field] = {"village_position":[{},0],"turn":{},"phase":[],"battle_outcome":{},"mode":[],"rng_state":[],"frame_counter":"12","kills":-1}[field]
		reject(g,bad,"wrong top-level type/range " + field)
	for field in {"class_id":{},"level":"1","hp":[],"acted":1,"strength":{},"position":[{},0],"id":{},"item_id":999,"exp":-1,"player_slot":42}:
		var bad: Dictionary = base.duplicate(true)
		bad.units[0][field] = {"class_id":{},"level":"1","hp":[],"acted":1,"strength":{},"position":[{},0],"id":{},"item_id":999,"exp":-1,"player_slot":42}[field]
		reject(g,bad,"wrong tactical unit type/range " + field)
		bad = base.duplicate(true)
		bad.battle_start_snapshot.units[0][field] = {"class_id":{},"level":"1","hp":[],"acted":1,"strength":{},"position":[{},0],"id":{},"item_id":999,"exp":-1,"player_slot":42}[field]
		reject(g,bad,"wrong retry unit type/range " + field)
	for field in {"pending_loot":{},"loot_notifications":[null],"world_mobile_armies":[{}],"inventory_processed_deaths":[],"celica_captive_hp":{"celica":{}}}:
		var bad: Dictionary = base.duplicate(true)
		bad.flags[field] = {"pending_loot":{},"loot_notifications":[null],"world_mobile_armies":[{}],"inventory_processed_deaths":[],"celica_captive_hp":{"celica":{}}}[field]
		reject(g,bad,"wrong resumable queue " + field)
	var duplicate: Dictionary = base.duplicate(true)
	duplicate.units.append(duplicate.units[0].duplicate(true))
	reject(g,duplicate,"duplicate tactical unit identity")
	var outside: Dictionary = base.duplicate(true)
	outside.units[0].position = [100,100]
	reject(g,outside,"tactical coordinate outside current map")
	var text := JSON.stringify(base)
	for length in [0,1,10,text.length()/2,text.length()-1]: reject(g,text.substr(0,length),"truncated JSON at %d" % length,true)
	for raw in ["[]","null","not a save"]: reject(g,raw,"invalid JSON document " + raw,true)
	for field in {"version":[],"stage_id":{},"source_revision":{},"parties":{"alm":[{}],"celica":[]}}:
		var bad: Dictionary = base.duplicate(true)
		bad[field] = {"version":[],"stage_id":{},"source_revision":{},"parties":{"alm":[{}],"celica":[]}}[field]
		reject(g,bad,"invalid preflight " + field)
	# A partially written temp file must never supersede the last complete save.
	write(base)
	var f := FileAccess.open(SAVE + ".tmp",FileAccess.WRITE);f.store_string("{\"version\":");f.close()
	check(g.load_game(),"interrupted temp file leaves previous complete checkpoint loadable")
	check(g.save_game() and not FileAccess.file_exists(SAVE + ".tmp"),"next save atomically replaces stale temp file")
	_test_legacy(base)
	_test_legacy_victory(base)
	_test_legacy_v3_instances(base)
	_test_instance_metadata(base)
	_test_world_cache()
	_test_retreat()
	for suffix in ["",".tmp",".v1.bak",".v2.bak"]: DirAccess.remove_absolute(SAVE + suffix)
	var report := {"checks":checks,"failures":failures,"rejected_cases":rejected_cases,
		"scope":"invalid/truncated local saves must return false without changing live state; authentic v1/v2 and pre-instance v3 migration, retry identities, stale v3 world route cache, retreat checkpoints and interrupted atomic save",
		"user_save_accessed":false}
	var file := FileAccess.open("res://reports/save-robustness-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("SAVE ROBUSTNESS: %d checks, %d failures" % [checks,failures.size()])
	quit(0 if failures.is_empty() else 1)

func strip_instance_metadata(state: Dictionary) -> void:
	# Before independent armies existed, old checkpoints had neither these
	# flag tables nor unit identities. Keeping only one makes a hybrid fixture.
	for field in ["world_army_instances","world_army_next_id","world_random_army_instance","battle_army_instances","dungeon_army_instances","inventory_attacking_instance_id"]:
		state.flags.erase(field)
	for unit in state.units: unit.erase("army_instance")
	for unit in state.get("roster", {}).values(): unit.erase("army_instance")

func _test_legacy(base: Dictionary) -> void:
	for version in [1,2]:
		var old := base.duplicate(true)
		old.version = version
		strip_instance_metadata(old)
		strip_instance_metadata(old.battle_start_snapshot)
		for field in Validator.EXTENDED_FIELDS: old.erase(field)
		for field in Validator.EXTENDED_FIELDS: old.battle_start_snapshot.erase(field)
		old.units[0].level = 3;old.units[0].exp = 61;old.units[0].max_hp = 30;old.units[0].hp = 13
		for unit in old.units:
			for field in ["character_id","resistance","magic_level","name_id","group_id","record_index","player_slot","enemy_slot"]: unit.erase(field)
		if version == 1:
			for field in ["stage_id","world_node","roster","cleared_stages","battle_start_snapshot","victory_rewards"]: old.erase(field)
		write(old)
		var original := FileAccess.get_file_as_string(SAVE)
		var g = State.new();g.save_path = SAVE
		check(g.load_game(),"legacy v%d suspend loads" % version)
		check(int(g.find_unit("alm").level) == 3 and int(g.find_unit("alm").exp) == 61 and int(g.find_unit("alm").hp) == 13,"legacy v%d tactical progression retained" % version)
		check(g.find_unit("alm").has("resistance") and g.find_unit("alm").has("player_slot"),"legacy v%d missing full-game fields migrated" % version)
		check(FileAccess.get_file_as_string(SAVE + ".v%d.bak" % version) == original,"legacy v%d backup is original bytes" % version)
		check(g.save_game() and int(State.read_json(SAVE).version) == 3,"legacy v%d upgraded checkpoint writes v3" % version)
		var loaded = State.new();loaded.save_path = SAVE
		check(loaded.load_game() and int(loaded.find_unit("alm").exp) == 61,"upgraded v%d checkpoint reloads without reward duplication" % version)
		check(loaded.retry_battle(),"upgraded v%d original retry snapshot remains executable" % version)
		check(loaded.units.filter(func(u):return u.side == "enemy").all(func(u):return loaded.flags.battle_army_instances.has(u.get("army_instance",""))),"upgraded v%d retry binds all legacy enemy records to encounter identities" % version)
		check(loaded.save_game(),"upgraded v%d retried checkpoint saves" % version)
		var retried = State.new();retried.save_path = SAVE
		check(retried.load_game() and retried.flags.battle_army_instances == loaded.flags.battle_army_instances,"upgraded v%d retry identity survives the next suspend" % version)
		# Subsequent loads may never replace the user's original migration backup.
		check(FileAccess.get_file_as_string(SAVE + ".v%d.bak" % version) == original,"legacy v%d backup is retained after round trip" % version)

func _test_legacy_v3_instances(base: Dictionary) -> void:
	var old: Dictionary = base.duplicate(true)
	strip_instance_metadata(old)
	strip_instance_metadata(old.battle_start_snapshot)
	var victim: Dictionary = old.units.filter(func(u):return u.side == "enemy")[0]
	victim.hp = 0
	var legacy_key := "%d:%d" % [int(victim.group_id),int(victim.record_index)]
	old.flags.inventory_defeated_enemy_records = {legacy_key:true}
	write(old)
	var g = State.new();g.save_path = SAVE
	check(g.load_game(),"pre-instance v3 checkpoint loads without requiring new optional metadata")
	var identity := str(g.find_unit(str(victim.id)).get("army_instance",""))
	check(g.flags.battle_army_instances.has(identity) and g.flags.world_army_instances["1"].has(identity),"pre-instance v3 binds the surviving army and its battle records to one identity")
	check(not g.flags.inventory_defeated_enemy_records.has(legacy_key) and g.flags.inventory_defeated_enemy_records.has(identity+":"+str(int(victim.record_index))),"pre-instance v3 moves the casualty mask to its own identity once")
	check(g.save_game(),"pre-instance v3 migrated checkpoint saves")
	var loaded = State.new();loaded.save_path = SAVE
	check(loaded.load_game() and loaded.flags.battle_army_instances == g.flags.battle_army_instances,"pre-instance v3 second load preserves identity allocation")
	check(loaded.retry_battle() and int(loaded.find_unit(str(victim.id)).hp) > 0 and loaded.flags.inventory_defeated_enemy_records.is_empty(),"pre-instance v3 retry restores its original roster and removes later casualty state")
	check(loaded.units.filter(func(u):return u.side == "enemy").all(func(u):return loaded.flags.battle_army_instances.has(u.get("army_instance",""))),"pre-instance v3 retry binds every old enemy to restored encounter identities")
	check(loaded.save_game(),"pre-instance v3 retry remains saveable")
	var retried = State.new();retried.save_path = SAVE
	check(retried.load_game() and retried.flags.battle_army_instances == loaded.flags.battle_army_instances,"pre-instance v3 retried suspend retains its identity mapping")

func _test_world_cache() -> void:
	var g = fresh()
	g.chapter = 3;g.mode = "world";g.route = "celica";g.world_node = 18
	g.party = ["celica","mae"]
	g.parties = {"alm":["alm","lukas"],"celica":["celica","mae"]}
	g.roster.celica = g._initial_character("celica");g.roster.mae = g._initial_character("mae")
	g.roster.celica.exp = 37;g.roster.mae.item_id = 53
	g.route_positions = {"alm":16,"celica":18}
	check(g.units.any(func(u):return u.id == "alm") and not g.units.any(func(u):return u.id == "celica"),"fixture reflects 0.6 prior-route tactical cache")
	g.save_game()
	var loaded = State.new();loaded.save_path = SAVE
	check(loaded.load_game() and loaded.mode == "world" and loaded.units.is_empty(),"v3 world route switch clears stale tactical cache on load")
	check(loaded.party == ["celica","mae"] and int(loaded.roster.celica.exp) == 37 and int(loaded.roster.mae.item_id) == 53,"world repair retains actual party progression and equipment")
	check(loaded.switch_route() and loaded.party == ["alm","lukas"] and loaded.world_node == 16,"repaired world checkpoint can switch back to first route")

func _test_retreat() -> void:
	var g = fresh()
	g.world_node = 4;g.start_battle(4)
	g.previous_world_node = 3;g.world_armies.erase("3");Worlds.ensure(g)
	g.find_unit("alm").exp = 33
	g.turn += 1
	check(Inventory.refresh_retreat(g,0) and Inventory.retreat(g),"legal manual retreat is available and committed")
	g.save_game()
	var loaded = State.new();loaded.save_path = SAVE
	check(loaded.load_game() and loaded.mode == "world" and loaded.world_node == 3 and loaded.units.is_empty(),"manual retreat immediate checkpoint resumes on world")
	check(loaded.world_has_battle(4) and int(loaded.roster.alm.exp) == 33,"retreat checkpoint keeps surviving army and experience")
	g = fresh();g.world_node = 51;g.battle_return = {"mode":"hub","world_node":51,"hub_id":3,"position":[7,9]}
	g.start_battle(49,[],true);g.phase = "enemy";g.turn = 40
	check(Inventory.forced_retreat(g).get("triggered",false),"underground timeout commits source hub retreat")
	g.save_game()
	loaded = State.new();loaded.save_path = SAVE
	check(loaded.load_game() and loaded.mode == "hub" and loaded.hub_id == 3 and loaded.hub_position == Vector2i(7,9),"timeout immediate checkpoint restores exact source room and position")

func _test_instance_metadata(base: Dictionary) -> void:
	var state: Dictionary = base.duplicate(true)
	state.world_armies = {"1":[1,1],"4":[4]}
	state.encounter_groups = [1,1]
	state.flags.world_army_instances = {"1":["army_1","army_2"],"4":["army_3"]}
	state.flags.battle_army_instances = ["army_1","army_2"]
	state.flags.world_army_next_id = 5
	state.flags.world_random_army_instance = ""
	state.flags.dungeon_army_instances = {"3:49:48:0":"army_4"}
	state.flags.world_mobile_armies = [{"node":1,"group_id":1,"previous_node":2,"instance_id":"army_2"}]
	var g = fresh()
	check(Validator.valid(g,state),"two armies may share one source group while identities remain distinct")
	for field in {"world_army_instances":{"1":["army_1","army_1"],"4":["army_3"]},"world_army_next_id":0,"battle_army_instances":["army_1"],"world_random_army_instance":{},"dungeon_army_instances":{"3:49:48:0":[]}}:
		var bad: Dictionary = state.duplicate(true)
		bad.flags[field] = {"world_army_instances":{"1":["army_1","army_1"],"4":["army_3"]},"world_army_next_id":0,"battle_army_instances":["army_1"],"world_random_army_instance":{},"dungeon_army_instances":{"3:49:48:0":[]}}[field]
		reject(g,bad,"invalid army instance metadata " + field)
	var bad: Dictionary = state.duplicate(true)
	bad.flags.world_army_instances["4"] = ["army_2"]
	reject(g,bad,"army instance reused across two live nodes")
	bad = state.duplicate(true)
	bad.flags.world_army_instances.erase("4")
	reject(g,bad,"army instance table missing live node")
	bad = state.duplicate(true)
	bad.flags.world_army_instances["1"] = ["army_1"]
	reject(g,bad,"army instance count differs from source group list")
	bad = state.duplicate(true)
	bad.flags.world_mobile_armies[0].instance_id = "army_bad"
	reject(g,bad,"malformed mobile army instance identifier")
	for retry in [false,true]:
		bad = base.duplicate(true)
		var checkpoint: Dictionary = bad.battle_start_snapshot if retry else bad
		checkpoint.units.filter(func(u):return u.side == "enemy")[0].army_instance = "army_bad"
		reject(g,bad,"malformed %s enemy army identity" % ("retry" if retry else "suspend"))
		bad = base.duplicate(true)
		checkpoint = bad.battle_start_snapshot if retry else bad
		checkpoint.units.filter(func(u):return u.side == "enemy")[0].army_instance = "army_999"
		reject(g,bad,"orphan %s enemy army identity" % ("retry" if retry else "suspend"))
		bad = base.duplicate(true)
		checkpoint = bad.battle_start_snapshot if retry else bad
		checkpoint.units.filter(func(u):return u.side == "enemy")[0].group_id = 4
		reject(g,bad,"%s enemy template differs from its own army" % ("retry" if retry else "suspend"))
	bad = base.duplicate(true)
	bad.battle_start_snapshot.flags.world_army_instances["1"] = ["army_1","army_1"]
	reject(g,bad,"retry army instance table count differs from source groups")
	var settled: Dictionary = state.duplicate(true)
	settled.world_armies.erase("1")
	settled.flags.world_army_instances.erase("1")
	check(Validator.valid(g,settled),"settled battle may retain historical identities after live army removal")

func _test_legacy_victory(base: Dictionary) -> void:
	for version in [1,2]:
		var old: Dictionary = base.duplicate(true)
		old.version = version;old.mode = "victory";old.battle_outcome = "victory"
		old.flags.first_battle_complete = true;old.cleared_stages = [1]
		old.units[0].level = 3;old.units[0].exp = 83;old.units[0].hp = 13
		for unit in old.units:
			if unit.side == "enemy": unit.hp = 0
			else: old.roster[str(unit.id)] = unit.duplicate(true)
		strip_instance_metadata(old)
		strip_instance_metadata(old.battle_start_snapshot)
		for field in Validator.EXTENDED_FIELDS: old.erase(field)
		for field in Validator.EXTENDED_FIELDS: old.battle_start_snapshot.erase(field)
		if version == 1:
			for field in ["stage_id","world_node","roster","cleared_stages","battle_start_snapshot","victory_rewards"]: old.erase(field)
		write(old)
		var g = State.new();g.save_path = SAVE
		check(g.load_game() and g.battle_settled,"legacy v%d completed battle restores settled state" % version)
		check(g.stage_cleared(1) and not g.world_has_battle(1),"legacy v%d victory keeps defeated army cleared" % version)
		check(int(g.roster.alm.exp) == 83 and int(g.roster.alm.level) == 3,"legacy v%d completed progression retained" % version)
		check(not g.complete_battle() and int(g.roster.alm.exp) == 83,"legacy v%d victory cannot award a second bonus" % version)
		check(g.save_game(),"legacy v%d completed checkpoint upgrades" % version)
		var loaded = State.new();loaded.save_path = SAVE
		check(loaded.load_game() and loaded.battle_settled and int(loaded.roster.alm.exp) == 83,"legacy v%d completed v3 round trip remains settled" % version)

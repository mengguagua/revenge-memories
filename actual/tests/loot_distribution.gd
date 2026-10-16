extends SceneTree
const State = preload("res://core/game_state.gd")
const Items = preload("res://core/item_rules.gd")
const Inventory = preload("res://core/battle_inventory.gd")
const Loot = preload("res://core/campaign_loot.gd")
const OUT = "res://reports/equipment-0.3.9/"
const CACHE = "res://.cache/equipment-0.3.9/"
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(CACHE));call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func battle():
	var g=State.new();g.new_game();g.world_node=2;g.start_battle(101);g.save_path=CACHE+"loot-save.json";return g
func run() -> void:
	var g=battle();var held_count=0;var unheld_count=0;var reinforcement_count=0
	for stage in g.stages.values():
		for category in ["enemies","reinforcements"]:
			for u in stage[category]:
				if category=="reinforcements":reinforcement_count+=1
				check(not u.get("no_drop",false),"every real combat enemy is loot eligible: "+u.id)
				if int(u.item_id)>0:
					held_count+=1
					check(Loot.chance(u)==100 and Inventory.carried_drop(u,99)==int(u.item_id),"explicit equipment always drops: "+u.id)
				else:
					unheld_count+=1
					check(Loot.chance(u)==10,"ordinary ten-percent chance includes every unheld enemy: "+u.id)
					check(Loot.ordinary_drop(u,9,99)>0 and Loot.ordinary_drop(u,10,0)==0,"ordinary gate exact boundary: "+u.id)
	check(held_count==11 and unheld_count==148 and reinforcement_count==10,"all 159 enemies and reinforcements covered, with 11 explicit carriers")
	# Enumerate every weighted selection, including tiers not yet encountered.
	var roles={"sword":8,"lance":6,"bow":12,"focus":15,"monster":11}
	var levels=[1,3,6,10]
	var banned: Array=Loot.config().legendary_exclusions.map(func(v):return int(v))
	for role in roles:
		for tier in range(4):
			var u={"side":"enemy","class_id":roles[role],"level":levels[tier],"item_id":0,"character_id":187 if role=="monster" else 182}
			check(Loot.tier(u)==tier and Loot.role(u)==role,"level/role selects correct pool: "+role+"/"+str(tier))
			var entries=Loot.pool(u);var total=0;var hits={}
			for entry in entries:
				total+=int(entry.weight)
				check(Items.item(int(entry.item_id)).get("kind","") in ["weapon","accessory"] and not banned.has(int(entry.item_id)),"ordinary pool contains valid nonlegendary equipment: "+str(entry.item_id))
				if tier==0:check(int(entry.item_id) in [48,59,60,61,62,63,64,65,66],"low-level enemies cannot drop advanced equipment")
			check(total==100,"weighted pool sums to 100: "+role+"/"+str(tier))
			for roll in range(100):
				var item=Loot.ordinary_drop(u,0,roll);hits[item]=int(hits.get(item,0))+1
			for entry in entries:check(int(hits.get(int(entry.item_id),0))==int(entry.weight),"selection weights exact: "+role+"/"+str(tier)+"/"+str(entry.item_id))
	check(Loot.tier({"level":1,"class_id":7,"objective_boss":true})==0,"low-level boss still uses basic pool")
	check(Loot.tier({"level":3,"class_id":6,"objective_boss":true})==1,"early ordinary boss cannot jump into advanced equipment pool")
	check(Loot.tier({"level":5,"class_id":6,"objective_boss":true})==2,"higher-level boss can drop advanced equipment")
	check(Loot.tier({"level":3,"class_id":13})==2,"advanced class at level three uses advanced pool")
	# Guaranteed drops use no random number, even with stale saved percentages.
	var enemy=g.find_unit("M11_e5");var killer=g.find_unit("hunapu");enemy.hp=0;enemy.drop_chance=1;g.rng_state=132
	var loot=Inventory.on_death(g,enemy,killer)
	check(int(loot.get("item_id",0))==63 and g.rng_state==132,"old carried-percentage metadata cannot defeat the guarantee or advance RNG")
	check(Inventory.on_death(g,enemy,killer).is_empty(),"guaranteed death cannot duplicate")
	# Unheld low-level soldier succeeds and persists an actual pending new-ID loot.
	g=battle();enemy=g.find_unit("M11_e1");killer=g.find_unit("otto");enemy.hp=0;g.rng_state=201;g.frame_counter=0
	loot=Inventory.on_death(g,enemy,killer)
	check(int(loot.get("item_id",0))==61 and loot.get("destination")=="pending","successful ordinary kill uses basic soldier pool and opens occupied-slot choice")
	check(int(g.flags.get("inventory_rare_drop_count",0))==0,"ordinary equipment does not consume legendary-drop quota")
	check(g.save_game(),"pending ordinary new-ID loot saves")
	var resumed=State.new();resumed.save_path=g.save_path
	check(resumed.load_game() and int(resumed.flags.pending_loot[0].item_id)==61,"pending ordinary loot survives actual save validation and reload")
	check(Inventory.resolve_loot(resumed,"store") and resumed.convoy.alm.any(func(v):return int(v)==61),"ordinary loot choice stores only in current army")
	check(resumed.retry_battle() and resumed.flags.get("pending_loot",[]).is_empty() and not resumed.convoy.alm.any(func(v):return int(v)==61),"retry restores pre-kill stock instead of farming loot")
	g=battle();enemy=g.find_unit("M11_e1");killer=g.find_unit("hunapu");enemy.hp=0;g.rng_state=132
	check(Inventory.on_death(g,enemy,killer).is_empty(),"failed ten-percent gate produces nothing")
	g.rng_state=201
	check(Inventory.on_death(g,enemy,killer).is_empty(),"failed death cannot be rerolled by repeat processing")
	# Prove the actual 8-bit RNG reaches all weighted entries, rather than only
	# the first one through correlated consecutive gate/selection samples.
	g=battle();enemy=g.find_unit("M11_e1");killer=g.find_unit("hunapu");enemy.hp=0;enemy.level=10
	var seen={}
	for frame in range(256):
		g.flags.inventory_processed_deaths={};g.flags.pending_loot=[];g.rng_state=201;g.frame_counter=frame;killer.item_id=0
		var result=Inventory.on_death(g,enemy,killer);seen[int(result.get("item_id",0))]=true
	for entry in Loot.pool(enemy):check(seen.has(int(entry.item_id)),"actual post-gate RNG can reach advanced pool item "+str(entry.item_id))
	check(not seen.has(0),"successful ordinary gate always awards exactly one item")
	# Real reinforcement through the same death pipeline.
	g=battle();enemy=g.battle_data.reinforcements[0].duplicate(true);enemy.hp=0;g.units.append(enemy);g.rng_state=201;g.frame_counter=0
	check(not Inventory.on_death(g,enemy,g.find_unit("hunapu")).is_empty(),"reinforcement receives ordinary loot eligibility")
	# Legacy ultra-rare rolls retain priority and cannot award a second item.
	g=battle();enemy=g.find_unit("M11_e1");enemy.character_id=179;enemy.hp=0;g.rng_state=201;g.frame_counter=201
	loot=Inventory.on_death(g,enemy,g.find_unit("hunapu"))
	check(int(loot.get("item_id",0))==8 and int(g.flags.inventory_rare_drop_count)==1,"legacy legendary success awards only the original rare item")
	check(g.flags.pending_loot.size()<=1 and Inventory.on_death(g,enemy,g.find_unit("hunapu")).is_empty(),"legendary and ordinary pools cannot both produce loot")
	g=battle();enemy=g.find_unit("M11_e1");enemy.character_id=179;enemy.hp=0;g.flags.inventory_rare_drop_count=10;g.rng_state=201;g.frame_counter=0
	check(not Inventory.on_death(g,enemy,g.find_unit("hunapu")).is_empty(),"exhausted legendary quota never suppresses ordinary ten-percent loot")
	g=battle();enemy=g.find_unit("M11_e1");enemy.hp=0;enemy.side="neutral";g.rng_state=201
	check(Inventory.on_death(g,enemy,g.find_unit("hunapu")).is_empty(),"surrender or neutral cleanup cannot create equipment")
	g=battle();enemy=g.find_unit("M11_e1");enemy.hp=0;g.rng_state=201
	check(Inventory.on_death(g,enemy,{}).is_empty(),"event removal without normal player kill gives no loot")
	var report={"version":"0.3.9","passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"explicit_carriers":held_count,"unheld":unheld_count,"reinforcements":reinforcement_count,"scope":"All actual enemy/ reinforcement eligibility; exhaustive weighted pools and gate boundaries; post-gate RNG reachability; actual death, new-ID pending loot save/reload/retry and legendary single-item priority. Directed fixtures, not natural playthrough."}
	var file=FileAccess.open(OUT+"loot-checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close();print("LOOT_DISTRIBUTION ",JSON.stringify(report));quit(0 if failures.is_empty() else 1)

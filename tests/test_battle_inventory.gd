extends SceneTree
const Inventory = preload("res://core/battle_inventory.gd")
class Fixture:
	extends RefCounted
	var flags: Dictionary = {}
	var convoy := {"alm":[], "celica":[]}
	var units: Array = []
	var roster: Dictionary = {}
	var route := "alm"
	var chapter := 1
	var stage_id := 4
	var turn := 1
	var phase := "player"
	var mode := "battle"
	var battle_outcome := ""
	var battle_settled := false
	var previous_world_node := 3
	var world_node := 4
	var world_armies := {"4":[4]}
	var route_positions := {"alm":4,"celica":18}
	var parties := {"alm":["alm","lukas"],"celica":[]}
	var party: Array = ["alm","lukas"]
	var battle_return: Dictionary = {}
	var hub_id:=1
	var hub_position:=Vector2i.ZERO
	var encounter_groups: Array = [4]
	var rng_state := 0
	var frame_counter := 0
	var selected_id := "alm"
	func find_unit(id: String) -> Dictionary:
		for unit in units:
			if str(unit.id) == id: return unit
		return {}
	func random_bounded(upper: int) -> int:
		rng_state = (rng_state + 55) & 255
		return (rng_state * upper) >> 8
	func world_has_battle(node: int) -> bool:
		return not world_armies.get(str(node),[]).is_empty()
	func enter_hub(id:int,at:Vector2i) -> bool:
		hub_id=id;hub_position=at;mode="hub"
		return true

var checks := 0
var failures: Array[String] = []
func check(value: bool, description: String) -> void:
	checks += 1
	if not value: failures.append(description)

func player(id: String, at: Array, item: int = 0) -> Dictionary:
	return {"id":id,"position":at,"item_id":item,"character_id":1 if id=="alm" else 5,"class_id":21,"side":"player","hp":28,"max_hp":28,"level":1,"exp":17,"acted":false}

func enemy(id: String, item: int = 53) -> Dictionary:
	return {"id":id,"position":[6,6],"item_id":item,"character_id":130,"class_id":1,"side":"enemy","hp":0,"max_hp":40,"group_id":4,"record_index":0}

func _initialize() -> void:
	var game := Fixture.new()
	var alm := player("alm",[2,2])
	var lukas := player("lukas",[2,3],15)
	game.units = [alm,lukas]
	game.roster = {"alm":alm.duplicate(true),"lukas":lukas.duplicate(true)}
	var boss := enemy("boss")
	var result := Inventory.on_death(game,boss,alm)
	check(int(alm.item_id)==53 and result.destination=="unit", "Dragon shield guaranteed from held item, directly to empty killer")
	check(int(game.roster.alm.item_id)==53 and boss.item_id==0,"persistent item synced and corpse cleared")
	check(Inventory.on_death(game,boss,alm).is_empty(),"same corpse cannot award twice")
	boss=enemy("boss2",12)
	result=Inventory.on_death(game,boss,alm)
	check(result.destination=="pending" and game.flags.pending_loot.size()==1,"occupied killer asks before replacing held item")
	check(Inventory.resolve_loot(game,"new"),"new selection resolves")
	check(alm.item_id==12 and game.convoy.alm==[53] and game.flags.pending_loot.is_empty(),"new item equipped and displaced Dragon shield safely stored")
	boss=enemy("boss3",53)
	Inventory.on_death(game,boss,alm)
	check(Inventory.resolve_loot(game,"keep") and alm.item_id==12 and game.convoy.alm==[53,53],"keep held item stores incoming loot")
	boss=enemy("boss4",7)
	Inventory.on_death(game,boss,alm)
	var saved: Dictionary = JSON.parse_string(JSON.stringify(game.flags))
	game.flags = saved
	check(Inventory.resolve_loot(game,"store") and game.convoy.alm[-1]==7,"pending loot survives JSON save roundtrip")
	var phantom := player("phantom",[3,3]);phantom.character_id=35;phantom.temporary=true
	result=Inventory.on_death(game,enemy("boss5",55),phantom)
	check(result.destination=="convoy" and phantom.item_id==0 and game.convoy.alm[-1]==55,"illusion kill sends loot to route convoy")
	lukas.hp=0
	result=Inventory.on_death(game,lukas)
	check(result.kind=="death_storage" and lukas.item_id==0 and game.convoy.alm[-1]==15,"formal ally death recovers carried item")
	check(game.roster.lukas.item_id==0,"dead persistent ally has no duplicate carried item")
	var celica:=player("celica",[4,4],57);celica.route="celica";celica.hp=0
	Inventory.on_death(game,celica)
	check(game.convoy.celica==[57],"merged final army death recovers item to unit's own route")
	var other_army:=player("other_army",[4,4],7);other_army.route="celica"
	game.units.append(other_army)
	Inventory.on_death(game,enemy("celica_loot",55),other_army)
	check(game.flags.pending_loot[0].route=="celica" and Inventory.resolve_loot(game,"store") and game.convoy.celica==[57,55],"merged final battle loot follows killer's route")
	for i in range(40-game.convoy.celica.size()):game.convoy.celica.append(2)
	Inventory.on_death(game,enemy("full_convoy",53),other_army)
	check(not Inventory.resolve_loot(game,"store") and game.flags.pending_loot.size()==1,"manual full convoy keeps unresolved loot without overwriting or loss")
	check(Inventory.resolve_loot(game,"discard_old") and other_army.item_id==53 and game.convoy.celica.size()==40,"explicit discard-old choice preserves incoming critical loot at full capacity")
	var neutral:=player("neutral",[4,4],16);neutral.neutral=true;neutral.hp=0
	var count: int=game.convoy.alm.size()
	check(Inventory.on_death(game,neutral).is_empty() and game.convoy.alm.size()==count,"neutral ally death not added to player inventory")
	var escaped:=enemy("escape");escaped.no_drop=true
	check(Inventory.on_death(game,escaped,alm).is_empty(),"scripted retreat never drops carried item")
	check(Inventory.on_death(game,enemy("expelled")).is_empty(),"map removal without killer does not invent combat loot")
	for rare in Inventory.data().rare_drops:
		var unit: Dictionary={"character_id":int(rare.character_id),"item_id":0}
		var p:=int(rare.roll_threshold)
		check(Inventory.rare_drop(unit,1,0,0,0)==int(rare.item_id),"rare source character mapping")
		check(Inventory.rare_drop(unit,1,0,p,0)==0 and Inventory.rare_drop(unit,1,0,0,p)==0,"both rare rolls are strict threshold comparisons")
		check(Inventory.rare_drop(unit,1,2,0,0)==0 and Inventory.rare_drop(unit,2,2,0,0)>0,"rare chapter cap is cumulative")
		check(Inventory.rare_drop(unit,4,10,0,0)==0 and Inventory.rare_drop(unit,5,0,0,0)==0,"global rare cap and chapter five exclusion")
		unit.item_id=2
		check(Inventory.rare_drop(unit,1,0,0,0)==0,"held item takes precedence over rare drop")
	var rare_monster:=enemy("rare",0);rare_monster.character_id=181
	game.rng_state=201;game.frame_counter=201
	result=Inventory.on_death(game,rare_monster,alm)
	check(int(result.item_id)==53 and int(game.flags.inventory_rare_drop_count)==1,"rare native RNG first gate and frame reseed second gate")
	game.chapter=5;game.flags.scenario_source_chapter_counter=4;game.rng_state=201;game.frame_counter=201
	rare_monster=enemy("chapter5_rare",0);rare_monster.character_id=181
	result=Inventory.on_death(game,rare_monster,alm)
	check(int(result.item_id)==53 and int(game.flags.inventory_rare_drop_count)==2,"narrative final chapter uses retained original counter4 for rare drops")
	game.chapter=1;game.flags.erase("scenario_source_chapter_counter")
	game.flags.pending_loot=[]
	lukas.hp=28;lukas.item_id=0;alm.acted=false
	check(Inventory.can_exchange(alm,lukas),"adjacent formal allied trade allowed")
	lukas.position=[3,3]
	check(not Inventory.can_exchange(alm,lukas),"diagonal trade forbidden")
	lukas.position=[2,3];lukas.acted=true
	check(Inventory.exchange(game,"alm","lukas"),"acted target can receive trade")
	check(alm.item_id==0 and lukas.item_id==12 and alm.acted and lukas.acted,"trade swaps one slot and ends only initiating action")
	check(game.roster.lukas.item_id==12 and game.selected_id.is_empty(),"trade syncs persistent item and clears selection")
	check(not Inventory.exchange(game,"alm","lukas"),"cannot trade twice after acting")
	alm.acted=false;lukas.item_id=0
	check(not Inventory.can_exchange(alm,lukas),"two empty hands cannot trade")
	alm.item_id=7;lukas.neutral=true
	check(not Inventory.can_exchange(alm,lukas),"trade excludes neutral allied target")
	lukas.neutral=false
	for stage in range(1,81):
		var chance:=Inventory.retreat_chance(stage)
		check(chance>=0 and chance<=100 and (stage<49 or chance==0),"all retreat percentages source bounded; dungeons disabled")
	game.turn=1
	check(Inventory.refresh_retreat(game,9),"map4 source retreat chance10 accepts roll9")
	check(Inventory.refresh_retreat(game,99),"reopening menu cannot reroll phase availability")
	game.turn=2
	check(not Inventory.refresh_retreat(game,10),"next player phase rolls again, chance threshold exclusive")
	game.turn=3;game.world_armies['3']=[5]
	check(not Inventory.refresh_retreat(game,0),"occupied return point blocks retreat regardless roll")
	game.world_armies.erase('3');game.turn=4
	check(Inventory.refresh_retreat(game,0),"unoccupied previous node allows retreat")
	game.phase="enemy"
	check(not Inventory.can_retreat(game),"enemy phase cannot invoke retreat")
	game.phase="player"
	game.flags.inventory_enemy_initiated=true;game.stage_id=29;game.chapter=3
	check(Inventory.retreat_destination(game)==28,"enemy initiated retreat uses last matching source sequence")
	game.chapter=2
	check(Inventory.retreat_destination(game)==-1,"chapter2 enemy initiated branch cannot retreat")
	game.flags.inventory_enemy_initiated=false;game.chapter=1;game.stage_id=4;game.turn=5
	Inventory.refresh_retreat(game,0)
	var dead:=enemy("dead");dead.record_index=0
	var survivor:=enemy("alive",0);survivor.record_index=1;survivor.hp=7
	game.units.append_array([dead,survivor])
	check(Inventory.retreat(game),"confirmed permitted retreat changes state")
	check(game.mode=="world" and game.world_node==3 and game.world_armies['4']==[4],"retreat returns previous node without clearing enemy army")
	check(game.roster.alm.exp==17 and game.battle_settled and game.battle_outcome=="retreat", "retreat retains progression and grants no victory bonus")
	dead=enemy("different_runtime_id");dead.record_index=0;dead.hp=40
	survivor.hp=40
	game.units=[dead,survivor]
	Inventory.restore_enemy_survivors(game)
	check(game.units.size()==1 and game.units[0].record_index==1 and game.units[0].hp==40,"retreat persists dead army records but survivors restart at full HP")
	game.flags.inventory_defeated_enemy_records['5:0']=true
	Inventory.on_victory(game)
	check(not game.flags.inventory_defeated_enemy_records.has('4:0') and game.flags.inventory_defeated_enemy_records.has('5:0'),"victory releases only defeated army group masks for later fresh reinforcements")
	game=Fixture.new();alm=player("alm",[2,2],7)
	game.units=[alm];game.roster={"alm":alm.duplicate(true)}
	game.phase="enemy";game.turn=39
	check(not Inventory.forced_retreat(game).triggered,"forced retreat waits for source threshold")
	game.turn=40
	var timeout:=Inventory.forced_retreat(game)
	check(timeout.triggered and timeout.side=="player" and game.world_node==3,"player initiated battle forces player retreat after40 turns")
	check(game.roster.alm.exp==17 and game.world_armies.has('4'),"timeout retains progress and enemy army, no victory bonus")
	game=Fixture.new();alm=player("alm",[2,2],7)
	game.units=[alm];game.roster={"alm":alm.duplicate(true)}
	game.flags={"inventory_enemy_initiated":true,"inventory_attacking_group_id":4,"inventory_attacker_previous_node":5,"world_mobile_armies":[{"node":4,"group_id":4,"previous_node":5}]}
	game.world_armies={"4":[4,6],"5":[7]};game.turn=40;game.phase="enemy"
	timeout=Inventory.forced_retreat(game)
	check(timeout.triggered and timeout.side=="enemy" and game.world_node==4,"enemy initiated timeout leaves defending player on same map")
	check(game.world_armies['4']==[6] and game.world_armies['5']==[7,4],"only attacking army retreats to recorded origin, other armies preserved")
	check(game.flags.world_mobile_armies[0].node==5 and game.mode=="world" and game.battle_outcome=="enemy_retreat","world mobile record and battle state reflect enemy retreat")
	game=Fixture.new();game.stage_id=8;game.turn=200;game.phase="enemy"
	check(not Inventory.forced_retreat(game).triggered,"source255 excludes forced retreat")
	game.stage_id=21;game.turn=59
	check(not Inventory.forced_retreat(game).triggered and Inventory.forced_retreat_turn(21)==60,"source map21 timeout is60")
	game.stage_id=4;game.turn=40;game.flags.inventory_enemy_initiated=true
	check(Inventory.forced_retreat(game).reason=="missing_attacking_army_origin" and game.mode=="battle","missing source origin is explicit and never invents a destination")
	game=Fixture.new();game.stage_id=49;game.turn=40;game.phase="enemy";game.world_node=51;game.previous_world_node=51
	game.battle_return={"mode":"hub","hub_id":3,"position":[7,9],"world_node":51}
	check(Inventory.forced_retreat(game).triggered and game.mode=="hub" and game.hub_id==3 and game.hub_position==Vector2i(7,9),"exceptional map49 timeout returns original hub room/cell")
	var report: Dictionary={"checks":checks,"failures":failures,"source_tables":Inventory.data().source,"scope":"held and rare drops, death recovery, persistent pending decisions, adjacent trade, phase-scoped retreat eligibility, casualty persistence"}
	var file:=FileAccess.open("res://reports/battle-inventory-verification.json",FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	print("FE_BATTLE_INVENTORY_CHECK ",checks," checks; failures=",failures)
	quit(0 if failures.is_empty() else 1)

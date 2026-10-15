extends SceneTree
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var errors: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fixture(id: int):
	var g=State.new();g.new_game();g.world_node=int(g.stages[id].node);g.previous_world_node=1
	g.start_battle(id);return g
func kill_boss(g) -> void:g.find_unit(str(g.battle_data.boss_id)).hp=0
func interact_all(g) -> void:
	for o in g.battle_data.objects:
		var hero=g.find_unit("hunapu");hero.acted=false
		var p=Vector2i(o.position[0],o.position[1]);hero.position=[p.x,p.y+1] if o.adjacent else [p.x,p.y]
		g.selected_id="hunapu";check(g.interact(str(o.id)),str(g.stage_id)+" explicit interaction "+str(o.id))
func run() -> void:
	var g=State.new();g.new_game();g.save_path="res://reports/campaign/round1-save.json"
	check(g.party==["hunapu","daan","otto"] and g.mode=="hub","new campaign starts in prologue with exact initial party")
	check(g.campaign.scenes.D00.size()==7 and not g.flags.get("prologue_done",false),"prologue dialogue and timeline marker")
	check(g.world_neighbors().is_empty(),"village departure blocked before introduction")
	g.flags.village_ready=true;check(g.world_neighbors()==[2],"departure unlocks correct first route")
	check(g.travel_to(2) and g.world_has_battle(2),"travel into first encounter")
	check(g.start_battle(101),"first encounter starts")
	check(g.living("enemy").size()==7,"first encounter exact initial enemies")
	check(g.living("player").size()==5,"initial party plus two temporary refugee groups")
	for id in [101,102,103,104,105,111,112]:
		var f=fixture(id)
		check(f.battle_outcome.is_empty(),str(id)+" starts unresolved")
		check(f.units.size()<=40 and f.living("enemy").size()<=20 and f.living("player").size()<=20,str(id)+" slot capacities")
		var positions={}
		for u in f.units:
			var p=State.pos(u);check(f.in_bounds(p),str(id)+" in-bounds "+str(u.id))
			check(f.movement_cost(u,p)<255,str(id)+" every deployed class can stand on its own ground "+str(u.id))
			check(not positions.has(p),str(id)+" unique deployment "+str(u.id));positions[p]=true
		kill_boss(f);check(f.check_outcome().is_empty(),str(id)+" boss death alone does not bypass objective")
		if id in [102,103,104,105]:interact_all(f)
		if id in [101,111]:
			for u in f.units:
				if u.get("quest_kind","")=="escort":u.position=f.battle_data.exit.duplicate();f.mark_wait(str(u.id))
		if id==112:
			f.find_unit("medicine_wagon").position=f.battle_data.targets[0].duplicate();f.mark_wait("medicine_wagon")
		check(f.check_outcome()=="victory",str(id)+" explicit full goal can settle")
		check(f.complete_battle(),str(id)+" victory settlement")
		var inventory=f.convoy.duplicate(true);var rewards=f.roster.duplicate(true)
		check(not f.complete_battle() and f.convoy==inventory and f.roster==rewards,str(id)+" rewards do not duplicate")
		check(f.cleared_stages.has(id),str(id)+" completion recorded")
		check(f.retry_battle() and not f.cleared_stages.has(id) and f.battle_outcome.is_empty(),str(id)+" retry restores opening snapshot")
		check(f.flags.quest.objects.is_empty() and f.flags.quest.evacuated.is_empty(),str(id)+" retry restores quest objects and escort state")
	check(int(g.battle_data.terrain.tile_categories["172"])==1,"forest visuals map to forest rules")
	check(int(g.battle_data.terrain.tile_categories["208"])==8,"stone floor retains original physical avoidance")
	check(int(g.battle_data.terrain.tile_categories["196"])==12,"masonry wall blocks foot units")
	var burn=fixture(102);burn.flags.quest.burn_streak=1;check(burn.check_outcome().is_empty(),"one burn confirmation is warning only")
	var escort=fixture(101)
	var first=escort.find_unit("M11_refugees0");var second=escort.find_unit("M11_refugees1")
	first.position=escort.battle_data.exit.duplicate();escort.mark_wait(str(first.id))
	check(escort.unit_at(State.pos(first)).is_empty() and escort.can_stop(second,State.pos(first)),"evacuated group no longer occupies shared exit")
	var cargo_fixture=fixture(112);var cargo=cargo_fixture.find_unit("medicine_wagon")
	check(cargo.get("event_object",false) and not cargo_fixture.Rules.can_attack(cargo,1),"cargo has durability and cannot attack/counter")
	var prepared=fixture(102);prepared.find_unit("hunapu").hp=1;prepared.flags.quest.burn_streak=1
	check(prepared.return_to_preparation() and prepared.mode=="world" and int(prepared.roster.hunapu.hp)>1 and prepared.flags.quest.burn_streak==0,"preparation return rolls back this battle only")
	burn.flags.quest.burn_streak=2;check(burn.check_outcome()=="defeat","two burn confirmations fail")
	var escape=fixture(105);escape.find_unit("M15_boss").position=escape.battle_data.exit.duplicate()
	check(escape.check_outcome()=="defeat","Korlan reaching visible exit fails")
	var lost=fixture(103);lost.find_unit("lena").hp=0;lost.story_on_death(lost.find_unit("lena"));kill_boss(lost);interact_all(lost)
	check(lost.check_outcome()=="victory" and lost.roster.lena.dead,"Lena casualty does not block main rescue")
	var all_lost=fixture(105)
	for u in all_lost.units:
		if str(u.id).begins_with("M15_workers"):u.hp=0
	check(all_lost.check_outcome()=="defeat","both worker groups dying cannot be called rescue")
	var reinforce=fixture(101);reinforce.turn=4;reinforce.next_phase()
	check(reinforce.living("enemy").size()==9 and reinforce.flags.quest.reinforced,"fourth enemy phase brings one two-unit wave")
	reinforce.next_phase();reinforce.turn=4;reinforce.next_phase()
	check(reinforce.living("enemy").size()==9,"reinforcement cannot repeat")
	g.flags.grain_shared=true;g.recruit("fula");g.cleared_stages=[101,111];g.mode="world"
	check(g.save_game(),"independent atomic campaign save")
	var fresh=State.new();fresh.save_path=g.save_path
	check(fresh.load_game() and fresh.party.has("fula") and fresh.cleared_stages==[101,111],"campaign reload retains roster and nonempty integer clear IDs")
	var corrupt=State.read_json(g.save_path);corrupt.campaign_id="original-fe2"
	var f=FileAccess.open(g.save_path,FileAccess.WRITE);f.store_string(JSON.stringify(corrupt));f.close()
	var before=fresh.roster.duplicate(true)
	check(not fresh.load_game() and fresh.roster==before,"foreign campaign save is rejected without mutation")
	corrupt.campaign_id=State.CAMPAIGN_ID;corrupt.units=[null]
	f=FileAccess.open(g.save_path,FileAccess.WRITE);f.store_string(JSON.stringify(corrupt));f.close()
	check(not fresh.load_game() and fresh.roster==before,"malformed tactical units rejected before live state changes")
	var report={"round":1,"scope":"Directed state and objective fixtures; not natural combat wins","checks":checks.size(),"errors":errors,"passed":errors.is_empty()}
	var out=FileAccess.open("res://reports/campaign/round1.json",FileAccess.WRITE);out.store_string(JSON.stringify(report,"  "));out.close()
	print("ROUND1 ",JSON.stringify(report));quit(0 if errors.is_empty() else 1)

extends SceneTree
## Victory recovery and compatibility use isolated files, never player journals.
var State=load(OS.get_environment("POSTBATTLE_HP_STATE") if not OS.get_environment("POSTBATTLE_HP_STATE").is_empty() else "res://core/game_state.gd")
const CACHE="/private/tmp/revenge-postbattle-hp-20261021/"
var checks=[]
var errors=[]
var serial=0

func _initialize():
	DirAccess.make_dir_recursive_absolute(CACHE)
	call_deferred("run")

func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)

func fresh():
	var g=State.new();g.new_game();g.world_node=2
	check(g.start_battle(101),"first battle starts")
	return g

func settle(g):
	for unit in g.units:
		if unit.get("quest_kind","")=="escort":
			unit.position=g.battle_data.exit.duplicate();g.mark_wait(str(unit.id))
	g.find_unit(str(g.battle_data.boss_id)).hp=0
	check(g.check_outcome()=="victory","actual first-battle objectives complete")
	check(g.complete_battle(),"victory settles")

func checkpoint(g):
	serial+=1;g.save_path=CACHE+"checkpoint-"+str(serial)+".json"
	check(g.save_game(),"isolated checkpoint writes")
	return State.read_json(g.save_path)

func reload_raw(raw):
	serial+=1
	var path=CACHE+"reload-"+str(serial)+".json"
	var f=FileAccess.open(path,FileAccess.WRITE);f.store_string(JSON.stringify(raw));f.close()
	var g=State.new();g.save_path=path
	check(g.load_game(),"validated checkpoint reloads")
	return g

func run():
	var g=fresh();var hero=g.find_unit("hunapu");hero.hp=16
	var npc=g.units.filter(func(u):return u.get("temporary",false) or u.get("neutral",false))[0];npc.hp=3
	var enemy=g.units.filter(func(u):return u.side=="enemy" and str(u.id)!=str(g.battle_data.boss_id))[0];enemy.hp=2
	var snapshot=g.battle_start_snapshot.duplicate(true)
	g.roster.beck=g._initial_character("beck");g.roster.beck.hp=4
	settle(g)
	check(int(g.roster.hunapu.hp)==int(g.roster.hunapu.max_hp) and hero.hp==hero.max_hp,"victory restores persistent and tactical HP")
	check(npc.hp==3 and enemy.hp==2 and g.roster.beck.hp==4,"NPCs enemies and unrecruited templates are unchanged")
	check(g.battle_start_snapshot==snapshot,"victory recovery leaves retry snapshot untouched")
	var settled=g.roster.duplicate(true);var stock=g.convoy.duplicate(true)
	check(not g.complete_battle() and g.roster==settled and g.convoy==stock,"repeated settlement does not change HP EXP or rewards")
	check(g.retry_battle() and g.roster==snapshot.roster and g.units==snapshot.units,"retry restores exact pre-battle units and roster")

	g=fresh();hero=g.find_unit("hunapu");hero.hp=1;hero.exp=99;hero.growths.hp=100
	var maximum=int(hero.max_hp);settle(g)
	check(int(hero.max_hp)==maximum+1 and hero.hp==hero.max_hp and g.roster.hunapu.hp==hero.max_hp,"recovery uses maximum HP after victory level growth")

	g=fresh();g.find_unit("hunapu").hp=16
	g.find_unit("daan").hp=0;g.Casualties.enter_dying(g,g.find_unit("daan"));g.Inventory.on_death(g,g.find_unit("daan"))
	var casualty=g.roster.daan.duplicate(true);var quota=g.flags.treatment_used.duplicate(true)
	var raw=checkpoint(g);var active=reload_raw(raw)
	check(active.find_unit("hunapu").hp==16 and active.roster.daan==JSON.parse_string(JSON.stringify(casualty)),"active battle reload retains wounds and dying member")
	raw.mode="defeat";raw.battle_outcome="defeat";var failed=reload_raw(raw)
	check(failed.find_unit("hunapu").hp==16,"defeat reload does not heal")
	raw.mode="victory";raw.battle_outcome="victory";var pending=reload_raw(raw)
	check(not pending.battle_settled and pending.find_unit("hunapu").hp==16,"unsettled victory reload does not bypass settlement")
	settle(g)
	check(g.roster.daan==casualty and g.find_unit("daan").hp==0 and not g.can_deploy(g.roster.daan),"victory never revives or deploys dying member")
	check(g.flags.treatment_used==quota and not g.victory_rewards.any(func(r):return r.unit=="daan"),"recovery neither spends treatment nor awards casualty EXP")
	g.mode="world";raw=checkpoint(g)
	# Reproduce the old post-battle save, including an outdated tactical copy.
	raw.roster.hunapu.hp=16
	for unit in raw.units:
		if unit.id=="hunapu":unit.hp=16
	for mode in ["world","hub","victory"]:
		var old=raw.duplicate(true);old.mode=mode
		if mode=="hub":old.hub_record="H02"
		var restored=reload_raw(old)
		check(restored.roster.hunapu.hp==restored.roster.hunapu.max_hp and restored.find_unit("hunapu").hp==restored.find_unit("hunapu").max_hp,"old "+mode+" checkpoint recovers HP")
		check(restored.roster.daan==JSON.parse_string(JSON.stringify(casualty)) and restored.flags.treatment_used==JSON.parse_string(JSON.stringify(quota)),"old "+mode+" checkpoint preserves casualty and treatment")
		check(restored.battle_start_snapshot==old.battle_start_snapshot and restored.victory_rewards==old.victory_rewards,"old "+mode+" checkpoint preserves retry and reward state")
		check(restored.save_game() and restored.load_game() and restored.roster.hunapu.hp==restored.roster.hunapu.max_hp,"recovered "+mode+" checkpoint round-trips")
	var peace=raw.duplicate(true);peace.battle_settled=false;peace.battle_outcome="";peace.units=[];peace.battle_start_snapshot={}
	var prepared=reload_raw(peace)
	check(prepared.roster.hunapu.hp==prepared.roster.hunapu.max_hp,"peaceful checkpoint still heals after old result flags were cleared")

	# Real final-chapter checkpoint supplies both armies, reserves and casualties.
	g=State.new();g.save_path="res://reports/chapter4/play/round2-chapter-end.json"
	check(g.load_game() and g.begin_chapter_five(),"authentic two-army checkpoint enters chapter five")
	g.cleared_stages.append_array([501,502,503,504]);g.flags.west_palace_gate=true;g.flags.east_palace_gate=true
	g.route_positions={"alm":15,"celica":15};g.flags.chapter5_ready={"alm":true,"celica":true}
	var west=g.ChapterFive.selection(g,"alm");g.ChapterFive.selection(g,"celica")
	var reserve=str(west[-1]);west.erase(reserve)
	check(g.ChapterFive.merge(g),"two armies merge at the shared preparation area")
	g.world_node=15
	check(g.start_battle(533),"joint deployment starts without changing ownership")
	g.roster[reserve].hp=2
	check(g.find_unit(reserve).is_empty(),"formal reserve remains outside joint deployment")
	var owners=g.parties.duplicate(true)
	for unit in g.units:
		if unit.side=="player" and not unit.get("temporary",false) and not unit.get("neutral",false):unit.hp=1
	g.battle_outcome="victory";check(g.complete_battle(),"joint victory settles")
	check(g.roster.hunapu.hp==g.roster.hunapu.max_hp and g.roster.eileen.hp==g.roster.eileen.max_hp,"joint victory restores both protagonists")
	check(g.roster[reserve].hp==g.roster[reserve].max_hp,"victory also restores formal reserve HP")
	check(g.parties==owners,"joint recovery retains original army ownership")
	for id in g.parties.alm+g.parties.celica:
		var unit=g.roster[id]
		check(int(unit.hp)==(0 if g.is_dying(unit) else int(unit.max_hp)),"joint member recovery respects casualty state: "+str(id))
	var out=OS.get_environment("POSTBATTLE_HP_REPORT")
	if out.is_empty():out="res://reports/postbattle-hp-20261021/checks.json"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out.get_base_dir()))
	var f=FileAccess.open(out,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"isolated_saves":CACHE},"  "));f.close()
	print("POSTBATTLE_HP ",checks.size()," checks; errors: ",errors)
	quit(0 if errors.is_empty() else 1)

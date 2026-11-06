extends SceneTree
const State=preload("res://core/game_state.gd")
var checks=[]
var failures=[]
var sources=[]
var out="res://reports/full-assessment-20261025/story/"
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append({"label":label,"passed":ok})
	if not ok:failures.append(label);push_error(label)
func fixture(code:String):
	var chapter=3 if code in ["M33","S32"] else 4 if code in ["S41","S42","M44","F44"] else 5
	var path="res://reports/full-playtest-20261023/ch%d/current/current-%s-deployment.json"%[chapter,code]
	var g=State.new();g.save_path=path;var before=FileAccess.get_sha256(path)
	check(g.load_game() and g.retry_battle(),code+" actual historical deployment loads and retries")
	g.save_path="/private/tmp/revenge-late-story-"+code+".json";g.story_events.clear()
	sources.append({"path":path,"sha256":before});return g
func words(g)->String:
	var lines=[]
	for event in g.story_events:
		for page in event.get("pages",[]):lines.append(str(page.speaker)+"："+str(page.text))
	return "／".join(lines)
func boss_down(g):g.find_unit(g.battle_data.boss_id).hp=0
func settle(g):
	check(g.check_outcome()=="victory",str(g.battle_data.code)+" permitted objective branch reaches victory")
	check(g.complete_battle(),str(g.battle_data.code)+" objective branch settles once")
func german():
	var g=fixture("M33");boss_down(g);g.check_outcome()
	check(g.find_unit("german").get("offering_surrender",false),"M33 commander defeat opens German parley")
	check(not words(g).contains("带部下"),"M33 parley offer promises only the actor that actually stops fighting")
	var remaining=g.living("enemy").filter(func(u):return u.id!="german").map(func(u):return u.id)
	g.story_events.clear();g.ChapterThree.interact(g,"german_disarm")
	check(g.find_unit("german").side=="neutral" and remaining.all(func(id):return g.find_unit(id).side=="enemy"),"M33 disarming German leaves unrelated guards as enemies")
	check(not words(g).contains("带部下"),"M33 accepted parley does not falsely announce group surrender")
	g.flags.quest.objects.dock_control=true
	check(g.check_outcome()=="","M33 dock and boss alone cannot skip workshop records")
	check(str(g.battle_data.goal).contains("工房") and str(g.battle_data.goal).contains("交涉"),"M33 objective explicitly states workshop records and living German parley")
	g.flags.quest.objects.workshop=true;settle(g)
	check(not g.flags.chapter3_recruits.german,"M33 disarm-only choice does not silently recruit German")
func casualties():
	for survivor in [true,false]:
		var g=fixture("S32");boss_down(g);g.flags.quest.objects={"mage_barrack":true,"civilian_barrack":true}
		g.find_unit("noya").hp=20 if survivor else 0
		settle(g)
		check(g.flags.chapter3_recruits.noya==survivor,"S32 recruit eligibility reflects actual Noya survival "+str(survivor))
		check(words(g).contains("诺娅，你要")==survivor,"S32 victory addresses Noya only when she survived "+str(survivor))
		if not survivor:check(words(g).contains("未能获救"),"S32 lost Noya is explicitly recorded without reviving her")
		g=fixture("S42");boss_down(g);g.flags.quest.objects.landing=true;g.flags.quest.evacuated=["island_group0","island_group1"]
		g.find_unit("celine").hp=20 if survivor else 0
		settle(g)
		check(g.flags.celine_ready==survivor,"S42 recruit eligibility reflects actual Celine survival "+str(survivor))
		check(words(g).contains("与赛琳交谈")==survivor,"S42 victory offers Celine conversation only when she survived "+str(survivor))
		if not survivor:check(words(g).contains("留守医者"),"S42 lost Celine hands care to surviving local staff")
func register():
	var g=fixture("S41");boss_down(g)
	check(g.check_outcome()=="","S41 intact unprotected register must still be collected after boss defeat")
	check(str(g.battle_data.goal).contains("尚存") and str(g.battle_data.goal).contains("焚毁"),"S41 objective distinguishes intact and destroyed record branches")
	g.flags.quest.record_lost=true;settle(g)
	check(not g.flags.S41_register_saved and not g.Accessories.eligible(g,55),"S41 destroyed register never grants protected-record flag or ring")
	check(words(g).contains("名册被烧掉") and not words(g).contains("完整名册保住"),"S41 lost-record victory uses eyewitness branch")
	g=fixture("S41");boss_down(g);g.flags.quest.objects.black_register=true;settle(g)
	check(g.flags.S41_register_saved and not g.Accessories.eligible(g,55),"S41 protected record alone does not replace refuge confirmation for ring")
func fourth_fifth_contracts():
	var g=fixture("M44");boss_down(g);g.check_outcome()
	var commander=g.find_unit(g.battle_data.boss_id)
	check(commander.hp==1 and commander.surrendered and commander.side=="neutral","M44 defeated commander surrenders alive")
	check(g.living("enemy").is_empty() and g.battle_data.reinforcements.is_empty(),"M44 surrender ends hostile guard and reinforcement actions")
	check(g.check_outcome()=="","M44 surrender alone does not skip gatehouse")
	g.flags.quest.objects.gatehouse=true;settle(g)
	g=fixture("F44");boss_down(g)
	for key in ["regulator_1","regulator_2","regulator_3"]:g.flags.quest.objects[key]=true
	check(g.check_outcome()=="","F44 all three handovers still require one full phase boundary")
	var started=g.turn;g.turn+=1
	check(g.check_outcome()=="victory" and g.flags.quest.repair_since==started,"F44 next player turn allows completed isolation test")
	g=fixture("F51");boss_down(g);g.flags.quest.objects={"repair_1":true,"repair_2":true};g.flags.quest.repair_since={"repair_1":g.turn-1,"repair_2":g.turn}
	check(g.check_outcome()=="","F51 completing one crew does not skip second crew protection")
	g.turn+=1;check(g.check_outcome()=="victory","F51 both independent crew timers complete on following turn")
	g=fixture("F51");g.find_unit("repair_team1").hp=0
	check(g.check_outcome()=="defeat","F51 losing either crew fails actual repair objective")
	g=fixture("S51");g.ChapterFive.interact(g,"archive_exit")
	check(not g.flags.quest.objects.get("archive_exit",false),"S51 cannot hand over missing records")
	g.flags.quest.objects.old_record=true;g.ChapterFive.interact(g,"archive_exit")
	check(not g.flags.quest.objects.get("archive_exit",false),"S51 cannot bypass living archive guard")
	boss_down(g);g.ChapterFive.interact(g,"archive_exit");settle(g)
	check(g.flags.S51_records_saved and g.Armaments.claimed(g,7),"S51 completed handover records archive and grants promised armament")
func run():
	if not OS.get_environment("LATE_STORY_OUT").is_empty():out=OS.get_environment("LATE_STORY_OUT")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
	german();casualties();register();fourth_fifth_contracts()
	for source in sources:check(FileAccess.get_sha256(source.path)==source.sha256,"unchanged historical source "+str(source.path))
	var f=FileAccess.open(out.path_join("late-story-checks.json"),FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"sources":sources,"scope":"Controlled survival/objective branches over copied historical deployments. Numeric fixtures are not claimed as natural victories."},"  "));f.close()
	print("LATE_STORY ",checks.size()," failures: ",failures);quit(0 if failures.is_empty() else 1)

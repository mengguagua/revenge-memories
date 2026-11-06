extends SceneTree
## Controlled objective fixtures, real settlement and handover; isolated saves.
const State=preload("res://core/game_state.gd")
const Fourth=preload("res://core/chapter4_hub.gd")
const Fifth=preload("res://core/chapter5_hub.gd")
const OUT="res://reports/story-accessories-20261023/"
const CACHE="/private/tmp/revenge-story-accessories-20261023/"
var checks=[]
var errors=[]
class Recorder extends RefCounted:
	var game
	var pages=[]
	var menu=[]
	func play_pages(value,_back,_callback):pages.append_array(value)
	func _open_menu(_kind,labels,_actions,_at):menu=labels
	func _notice(_text,_seconds=0):pass
class Room extends RefCounted:
	var ui
func _initialize():
	DirAccess.make_dir_recursive_absolute(CACHE)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fixture(stage:int):
	var g=State.new()
	g.save_path="res://reports/"+("chapter4/play/round2-S41-deployment.json" if stage==411 else "chapter5/play/round2-M51-deployment.json")
	check(g.load_game(),"deployment fixture loads: "+str(stage))
	g.save_path=CACHE+str(stage)+".json";g.story_events.clear();return g
func room(g):
	var h=Room.new();h.ui=Recorder.new();h.ui.game=g;return h
func use(g,id:String):
	var hero=g.find_unit(g.leader_id());hero.acted=false
	for o in g.battle_data.objects:
		if str(o.id)!=id:continue
		var at=o.get("approach",o.position)
		if not o.has("approach") and o.get("adjacent",false):at=[int(at[0]),int(at[1])+1]
		hero.position=at.duplicate();g.selected_id=hero.id
		check(g.interact(id),str(g.stage_id)+" real interaction "+id);return
	check(false,"missing authored object "+id)
func prepare(g,variant:String="success"):
	if g.stage_id==411:
		if variant=="burned":
			var burner=g.units.filter(func(u):return u.get("ch4_burner",false))[0]
			burner.position=g.battle_data.burn_target.duplicate();g.turn=int(g.battle_data.burn_start)
			g.ChapterFour.after_wait(g,burner);check(not g.flags.quest.record_lost,"first fire does not burn register")
			g.ChapterFour.after_wait(g,burner);check(g.flags.quest.record_lost,"second consecutive fire burns register")
		else:use(g,"black_register")
		if variant!="no_refuge":use(g,"refuge_court")
	else:
		use(g,"ward_1");use(g,"ward_2")
		for i in range(2 if variant=="success" else 1):
			var u=g.find_unit("royal_wounded"+str(i));u.position=g.battle_data.exit.duplicate();u.acted=false
			g.mark_wait(str(u.id));check(g.flags.quest.evacuated.has(str(u.id)),"actual exit records wounded group "+str(i))
		if variant=="one_dead":g.find_unit("royal_wounded1").hp=0
	g.find_unit(str(g.battle_data.boss_id)).hp=0
func settle(g):
	check(g.check_outcome()=="victory","existing victory condition permits result: "+str(g.stage_id))
	check(g.complete_battle(),"real settlement: "+str(g.stage_id))
func hub(g):
	g.mode="hub";g.hub_record="H49" if g.stage_id==411 else "H51";g.story_events.clear()
func count_item(g,id:int) -> int:return g.convoy.alm.filter(func(v):return int(v)==id).size()
func run():
	var g=State.new();g.new_game();g.save_path=CACHE+"chapter1.json"
	check(g.save_game() and g.load_game() and not g.flags.has("story_accessory_results"),"first chapter saves need no accessory migration")
	check(g.Items.armaments().items.size()==6,"Guarding armaments remain six separate weapons")
	var source=g.Items._integer_tables(State.read_json("res://data/legacy/rules_full.json"))
	for id in [53,55]:
		check(g.Items.item(id).name_zh==("护途盾" if id==53 else "续愿戒"),"adapted display name: "+str(id))
		for key in ["might","weight","hit","critical","effective","target_flags","effect_kind","hp_cost"]:
			check(g.Items.item(id).get(key)==source.items[id].get(key),"unchanged numeric rule: "+str(id)+" / "+key)
		for member in g.characters:check(g.Items.can_use(g._initial_character(str(member)),id),"accessory compatible with "+str(member)+" / "+str(id))
		check(not g.Accessories.claim(g,id),"not granted in first chapter: "+str(id))
	for sid in [181,190]:check(g.Inventory.rare_drop({"character_id":sid,"item_id":0},2,0,0,0)==0,"fixed accessory excluded from old rare source "+str(sid))
	check(g.Inventory.rare_drop({"character_id":179,"item_id":0},2,0,0,0)==8,"existing meteor rare drop retained")
	for role in g.Equipment.data().random_loot.pools:
		for pool in g.Equipment.data().random_loot.pools[role]:
			check(pool.all(func(e):return int(e.item_id) not in [53,55]),"ordinary pool excludes accessories: "+str(role))
	var u=g._initial_character("hunapu");u.hp=10;u.max_hp=52;u.resistance=7;u.luck=8
	u.item_id=53
	check(g.Items.physical_defence_bonus(u)==5 and g.Items.magic_defence(u)==12,"shield adds five to both defences")
	u.item_id=55
	check(g.Items.effective_luck(u)==40 and u.luck==8,"ring overrides effective luck without changing real luck")
	u.growths={"hp":50,"defence":50,"luck":50,"speed":50,"skill":50,"strength":50}
	u.max_hp=40;u.strength=20
	var delta=g.Rules.growth_result(u,[1,99,99,99,99,1])
	check(delta.hp==2 and delta.strength==2 and delta.luck==0 and delta.defence==0,"ring doubles successful growth only")
	check(g.Rules.growth_result(u,[99,99,99,99,99,99]).hp==2,"all failed rolls retain existing guaranteed HP rule")
	u.max_hp=51;u.strength=39;delta=g.Rules.growth_result(u,[1,99,99,99,99,1])
	check(delta.hp==1 and delta.strength==1,"ring respects HP52 and stat40 caps")
	u.max_hp=52;u.strength=40;delta=g.Rules.growth_result(u,[1,99,99,99,99,1])
	check(delta.hp==0 and delta.strength==0,"capped successes grant no extra growth")
	for id in [53,55]:
		u.item_id=id;u.hp=10;check(g.Items.phase_effect(u,0).heal==5,"phase recovery five HP: "+str(id))
		u.hp=50;check(g.Items.phase_effect(u,0).hp_after==52,"recovery capped: "+str(id))
		u.hp=0;check(g.Items.phase_effect(u,0).heal==0,"no revival: "+str(id))
	u.item_id=0
	check(g.Items.effective_luck(u)==8 and g.Items.physical_defence_bonus(u)==0 and g.Items.magic_defence(u)==7,"removal restores natural stats")
	for stage in [411,501]:
		var id=55 if stage==411 else 53
		for variant in (["success","no_refuge","burned"] if stage==411 else ["success","one_only","one_dead"]):
			g=fixture(stage);prepare(g,variant);settle(g)
			check(g.Accessories.eligible(g,id)==(variant=="success"),"exact saved reward eligibility: "+str(stage)+" / "+variant)
			check(count_item(g,id)==0,"no automatic clear reward: "+str(stage)+" / "+variant)
			hub(g);var h=room(g);var held={}
			for key in g.roster:held[key]=g.roster[key].item_id
			g.convoy.alm.clear();for i in range(40):g.convoy.alm.append(49)
			var other=g.convoy.celica.duplicate();var before_hp=g.roster.hunapu.hp
			if stage==411:await Fourth.action(h,"fourth_ring_keeper")
			else:await Fifth.action(h,"fifth_shield_keeper")
			check(count_item(g,id)==(1 if variant=="success" else 0),"NPC grants only qualifying result: "+str(stage)+" / "+variant)
			check(g.convoy.alm.size()==(41 if variant=="success" else 40),"full convoy preserves handover: "+str(stage)+" / "+variant)
			check(g.convoy.celica==other and g.roster.hunapu.hp==before_hp and g.roster.keys().all(func(key):return g.roster[key].item_id==held[key]),"handover preserves gear, HP and other convoy: "+str(stage)+" / "+variant)
			if stage==411:await Fourth.action(h,"fourth_ring_keeper")
			else:await Fifth.action(h,"fifth_shield_keeper")
			check(h.ui.pages.filter(func(p):return str(p.text).contains("已收入西队行囊")).size()==(1 if variant=="success" else 0),"repeat NPC dialogue never repeats receipt: "+str(stage)+" / "+variant)
			if variant!="success":
				var facts_before=g.flags.story_accessory_results.duplicate(true)
				for key in g.flags.quest.objects:g.flags.quest.objects[key]=true
				g.flags.quest.record_lost=false
				g.flags.quest.evacuated=["royal_wounded0","royal_wounded1"] if stage==501 else []
				g.Accessories.record_victory(g)
				check(g.flags.story_accessory_results==facts_before and not g.Accessories.eligible(g,id),"post-battle edits cannot manufacture missing facts: "+str(stage)+" / "+variant)
			g.Accessories.record_victory(g);g.Equipment.reconcile(g)
			check(not g.Accessories.claim(g,id),"repeat handover/reconcile cannot award again: "+str(stage)+" / "+variant)
			if variant=="success":g.save_path=CACHE+"success-"+str(stage)+".json"
			check(g.save_game(),"settled facts and claim save: "+str(stage)+" / "+variant)
			var loaded=State.new();loaded.save_path=g.save_path
			check(loaded.load_game() and loaded.Accessories.eligible(loaded,id)==(variant=="success") and count_item(loaded,id)==(1 if variant=="success" else 0),"facts and claim round trip: "+str(stage)+" / "+variant)
			check(not loaded.Accessories.claim(loaded,id),"load does not duplicate or repair failed result")
			if variant=="success":
				var switched=State.new();switched.save_path=g.save_path;check(switched.load_game(),"switch fixture reloads")
				check(switched.switch_route() and switched.switch_route() and count_item(switched,id)==1,"switching armies preserves one reward: "+str(id))
				check(loaded.retry_battle() and count_item(loaded,id)==0 and not loaded.flags.get("story_accessory_results",{}).has(str(id)),"retry restores pre-battle facts and inventory: "+str(id))
				prepare(loaded);settle(loaded);hub(loaded)
				check(loaded.Accessories.claim(loaded,id) and count_item(loaded,id)==1,"retry success yields one reward: "+str(id))
				var raw=State.read_json(g.save_path);raw.flags.story_accessories_claimed[str(id)]="yes"
				check(not g.SaveValidation.campaign_valid(g,raw,g.SAVE_FIELDS),"malformed claim bool rejected: "+str(id))
				for malformed in ["yes",{}, {"unknown":true}]:
					raw=State.read_json(g.save_path);raw.flags.story_accessory_results[str(id)]=malformed
					check(not g.SaveValidation.campaign_valid(g,raw,g.SAVE_FIELDS),"malformed facts rejected: "+str(id)+" / "+str(malformed))
				for key in g.Items.accessories().items[str(id)].facts:
					raw=State.read_json(g.save_path);raw.flags.story_accessory_results[str(id)][key]=false
					check(not g.SaveValidation.campaign_valid(g,raw,g.SAVE_FIELDS),"claim without required saved fact rejected: "+str(id)+" / "+str(key))
		# A historical clear or silver-bow reconciliation must never invent facts.
		g=fixture(stage);g.cleared_stages.append(stage);hub(g);g.Equipment.reconcile(g)
		check(not g.Accessories.eligible(g,id) and not g.Accessories.claim(g,id),"clear alone cannot create accessory eligibility: "+str(id))
		check(g.save_game() and g.load_game() and not g.Accessories.eligible(g,id),"old clear remains unrewarded after reload: "+str(id))
	# Wrong room, route and early claim guards, before and after permanent closure.
	for stage in [411,501]:
		g=fixture(stage);var id=55 if stage==411 else 53
		prepare(g);check(not g.Accessories.claim(g,id),"unsettled battle cannot claim: "+str(id));settle(g)
		hub(g);g.hub_record="H10";check(not g.Accessories.claim(g,id),"wrong room cannot claim: "+str(id))
		hub(g);g.route="celica";check(not g.Accessories.claim(g,id),"wrong army cannot claim: "+str(id));g.route="alm"
		var reminder=g.Accessories.closing_reminder(g,id)
		check(reminder.contains("尚未领取") and reminder.contains("黑钟村避难院" if id==55 else "王都内廷伤兵照护处"),"closure reminder points to unclaimed NPC: "+str(id))
		g.flags["chapter4_closed" if id==55 else "chapter5_merged"]=true
		if id==55:
			g.chapter=5;check(not g.Accessories.claim(g,id),"cannot claim ring after leaving chapter four")
			g.chapter=4;check(g.Accessories.claim(g,id),"chapter-end return to preparation can still claim ring")
		else:check(not g.Accessories.claim(g,id),"merged route cannot late claim shield")
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"isolated_saves":CACHE,"fixtures":"Controlled positions/objectives over authored deployment saves; not a full natural playthrough."},"  "));f.close()
	print("STORY_ACCESSORIES ",checks.size()," checks; errors: ",errors)
	quit(0 if errors.is_empty() else 1)

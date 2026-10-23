extends SceneTree
## Controlled settlement fixtures, real authored objectives and isolated saves.
const State=preload("res://core/game_state.gd")
const FourthHub=preload("res://core/chapter4_hub.gd")
const FifthHub=preload("res://core/chapter5_hub.gd")
const OUT="res://reports/story-armaments-20261023/"
const CACHE="/private/tmp/revenge-story-armaments-20261023/"
const SOURCES={303:"chapter3/play/round1final-M33-deployment.json",306:"chapter3/play/round1final-F33-deployment.json",412:"chapter4/play/round2-S42-deployment.json",408:"chapter4/play/round2-F44-deployment.json",502:"chapter5/play/round2-M52-deployment.json",511:"chapter5/play/round2-S51-deployment.json"}
var checks=[]
var errors=[]
var outcomes=[]
class FakeUI extends RefCounted:
	var game
	var pages=[]
	var menu=[]
	func play_pages(value,_back,_callback):pages.append_array(value)
	func _open_menu(_kind,labels,_actions,_at):menu=labels
	func _notice(_text,_seconds=0):pass
class FakeHub extends RefCounted:
	var ui
func _initialize():
	DirAccess.make_dir_recursive_absolute(CACHE)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	call_deferred("run")
func check(ok: bool,label: String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fixture(stage: int):
	var g=State.new();g.save_path="res://reports/"+SOURCES[stage]
	check(g.load_game(),"authentic deployment loads: "+str(stage))
	g.save_path=CACHE+str(stage)+".json";g.story_events.clear()
	return g
func room(g):
	var h=FakeHub.new();h.ui=FakeUI.new();h.ui.game=g;return h
func use(g,id: String):
	var hero=g.find_unit(g.leader_id());hero.acted=false
	for o in g.battle_data.objects:
		if str(o.id)!=id:continue
		var at=o.get("approach",o.position)
		if not o.has("approach") and o.get("adjacent",false):at=[int(at[0]),int(at[1])+1]
		hero.position=at.duplicate();g.selected_id=hero.id
		check(g.interact(id),str(g.stage_id)+" authored interaction "+id);return
	check(false,"missing interaction "+id)
func settle(g):
	g.find_unit(str(g.battle_data.boss_id)).hp=0
	if g.stage_id==303:g.find_unit("german").hp=0
	if g.stage_id==412:g.find_unit("celine").hp=0
	for o in g.battle_data.objects:
		if not o.get("optional",false):use(g,str(o.id))
	if g.stage_id==412:
		for i in range(2):
			var u=g.find_unit("island_group"+str(i));u.position=g.battle_data.exit.duplicate();u.acted=false;g.mark_wait(str(u.id))
	if g.stage_id==408:g.turn+=1
	check(g.check_outcome()=="victory",str(g.stage_id)+" real objective contract succeeds")
	check(g.complete_battle(),str(g.stage_id)+" victory settles")
func run():
	var g=State.new();g.new_game();g.save_path=CACHE+"first-chapter.json"
	check(g.save_game() and g.load_game() and not g.flags.has("story_armaments_claimed"),"first-chapter record grants no new armaments")
	var source=g.Items._integer_tables(State.read_json("res://data/legacy/rules_full.json"))
	var expected={7:"镇关枪",9:"曜锋枪",10:"定潮枪",15:"引霆剑",17:"引光剑",18:"守约剑"}
	for id in expected:
		check(g.Items.item(id).name_zh==expected[id],"adapted name "+str(id))
		for key in ["might","weight","hit","critical","effective","target_flags","effect_kind","hp_cost"]:
			check(int(g.Items.item(id).get(key,0))==int(source.items[id].get(key,0)),str(id)+" preserves source numeric rule "+key)
		check(not g.Armaments.claim(g,id),str(id)+" cannot be claimed before its event")
	var west=g._initial_character("hunapu");var east=g._initial_character("eileen")
	check(g.Items.can_use(east,17) and not g.Items.can_use(west,17),"Guiding Light sword belongs to Eileen")
	check(g.Items.can_use(west,18) and not g.Items.can_use(east,18),"Oathkeeper remains Hunapu-only")
	for id in g.characters:
		var unit=g._initial_character(str(id))
		check(g.Items.can_use(unit,17)==(id=="eileen"),"light sword exclusive owner: "+str(id))
		check(g.Items.can_use(unit,18)==(id=="hunapu"),"oath sword exclusive owner: "+str(id))
	check(g.EquipmentComparison.compare(west,17,g.catalog.classes).reason.contains("艾琳"),"incompatible light sword explains correct owner")
	check(g.EquipmentComparison.compare(east,18,g.catalog.classes).reason.contains("胡纳普"),"incompatible oath sword explains correct owner")
	var soldier=g._initial_character("german");soldier.class_id=6
	check(not g.Items.can_use(soldier,7),"Bastion lance retains soldier restriction")
	var knight=g._initial_character("lance")
	check(g.Items.can_use(knight,7) and g.Items.can_use(knight,9) and g.Items.can_use(knight,10),"existing lance classes retain new lance permissions")
	var defender={"id":"target","character_id":200,"side":"enemy","class_id":6,"hp":100,"max_hp":100,"strength":0,"skill":0,"speed":0,"luck":0,"defence":100,"resistance":4,"item_id":0}
	var actor=east.duplicate(true);actor.item_id=15;actor.strength=1
	var low=g.Rules.attack_stats(actor,defender,0);actor.strength=40
	check(low.damage==11 and g.Rules.attack_stats(actor,defender,0).damage==11,"Thunder sword remains fixed power fifteen against resistance")
	check(g.Rules.attack_range(actor)==Vector2i(1,2) and g.Rules.magic_cost(actor)==0,"Thunder sword keeps range and no spell HP cost")
	for id in [7,9,10,17,18]:
		actor=(east if id==17 else west if id==18 else knight).duplicate(true);actor.item_id=id;actor.hp=10;actor.max_hp=52
		check(g.Items.phase_effect(actor,0).heal==5,str(id)+" phase recovery remains five HP")
		check(g.Rules.magic_cost(actor)==0,str(id)+" weapon never charges source personal-restriction byte as HP")
	actor=knight.duplicate(true);actor.item_id=9;actor.hp=10;actor.max_hp=52
	check(g.Rules.attack_range(actor)==Vector2i(1,1) and g.Rules.strike_effect(actor,defender,true,false).heal==0,"Solar lance keeps melee range and grants no drain")
	actor.item_id=10
	check(g.Rules.attack_stats(actor,defender,240).hit==100 and g.Rules.attack_stats(actor,defender,0).damage==1,"Tide lance guarantees original hit rule but does not ignore defence")
	actor.item_id=7
	check(g.Rules.attack_range(actor)==Vector2i(1,2),"Bastion lance retains two-cell range")
	actor=east.duplicate(true);actor.item_id=17;var monster=defender.duplicate(true);monster.class_id=11
	check(g.Rules.attack_stats(actor,monster,0).effective,"Light sword retains monster effectiveness")
	for source_id in [194,199]:check(g.Inventory.rare_drop({"character_id":source_id,"item_id":0},2,0,0,0)==0,"unique armament excluded from old rare table: "+str(source_id))
	check(g.Inventory.rare_drop({"character_id":179,"item_id":0},2,0,0,0)==8,"Meteor lance retains existing rare source")
	for role in g.Equipment.data().random_loot.pools:
		for pool in g.Equipment.data().random_loot.pools[role]:
			for entry in pool:check(not g.Items.is_story_armament(int(entry.item_id)),"ordinary pool excludes unique armament: "+str(role)+" / "+str(entry.item_id))

	for spec in [[303,18],[306,15],[412,10],[502,9],[511,7]]:
		g=fixture(spec[0]);var id=int(spec[1]);var side=str(g.Items.armaments().items[str(id)].route)
		var other="celica" if side=="alm" else "alm";var other_before=g.convoy[other].duplicate()
		var held={};for key in g.roster:held[key]=int(g.roster[key].get("item_id",0))
		g.convoy[side].clear();for i in range(40):g.convoy[side].append(49)
		check(g.convoy[side].count(id)==0,"reward absent before clear: "+str(id))
		settle(g)
		check(g.Armaments.claimed(g,id) and g.convoy[side].count(id)==1 and g.convoy[side].size()>40,"one reward retained above manual capacity: "+str(id))
		check(g.convoy[other]==other_before,"reward preserves other army convoy: "+str(id))
		check(g.roster.keys().all(func(key):return int(g.roster[key].get("item_id",0))==int(held[key])),"reward never replaces carried gear: "+str(id))
		if id==18:check(not g.parties.alm.has("german"),"Oathkeeper independent of German recruitment")
		if id==10:check(not g.parties.celica.has("celine") and g.convoy.celica.count(16)==1,"Tide lance independent of Celine; holy sword retained")
		if id==9:check(g.convoy.alm.count(12)==1,"Solar lance preserves silver sword supply")
		if id==7:check(g.convoy.celica.count(49)==41,"Bastion lance preserves steel shield supply")
		var stock=g.convoy.duplicate(true);var events=g.story_events.size()
		g.Equipment.award_clear(g,int(spec[0]));check(not g.complete_battle() and g.convoy==stock and g.story_events.size()==events,"repeat clear is idempotent: "+str(id))
		check(g.save_game(),"settled reward checkpoint writes: "+str(id))
		var loaded=State.new();loaded.save_path=g.save_path
		check(loaded.load_game() and loaded.convoy[side].filter(func(value):return int(value)==id).size()==1 and loaded.Armaments.claimed(loaded,id),"reward round trip: "+str(id))
		var raw=State.read_json(g.save_path);raw.flags.story_armaments_claimed[str(id)]="yes"
		check(not g.SaveValidation.campaign_valid(g,raw,g.SAVE_FIELDS),"malformed reward marker rejected: "+str(id))
		check(loaded.retry_battle() and loaded.convoy[side].filter(func(value):return int(value)==id).size()==0 and not loaded.Armaments.claimed(loaded,id),"retry restores reward state before victory: "+str(id))
		settle(loaded);check(loaded.convoy[side].filter(func(value):return int(value)==id).size()==1,"retry victory still yields exactly one: "+str(id))
		outcomes.append({"stage":spec[0],"item_id":id,"route":side,"checkpoint":g.save_path})

	g=fixture(408);var h=room(g)
	await FourthHub.action(h,"fourth_obs_report")
	check(not g.Armaments.claimed(g,17),"observation report does not grant Light sword")
	settle(g);check(not g.Armaments.claimed(g,17) and g.convoy.celica.count(22)>0,"F44 retains silver bow and does not grant sword early")
	g.mode="hub";g.hub_record="H48";g.story_events.clear();var current_hp=int(g.roster.eileen.hp);var held_east=int(g.roster.eileen.item_id)
	await FourthHub.action(h,"fourth_island_verify")
	check(g.HeroProfessions.advanced(g.roster.eileen) and g.Armaments.claimed(g,17) and g.convoy.celica.count(17)==1,"local cycle progression grants Light sword once")
	check(int(g.roster.eileen.hp)==current_hp and int(g.roster.eileen.item_id)==held_east,"sword handover neither heals nor replaces carried gear")
	await FourthHub.action(h,"fourth_island_verify")
	check(g.convoy.celica.count(17)==1 and h.ui.pages.filter(func(page):return str(page.text).contains("引光剑已收入")).size()==1,"repeated local verification does not repeat handover")
	g.flags.west_tower_safe=true;await FourthHub.action(h,"fourth_d42")
	check(g.convoy.celica.count(17)==1,"D42 fallback does not duplicate Light sword")
	check(g.save_game(),"local-cycle reward saves")
	var light_reload=State.new();light_reload.save_path=g.save_path
	check(light_reload.load_game() and light_reload.Armaments.claimed(light_reload,17) and light_reload.convoy.celica.filter(func(value):return int(value)==17).size()==1,"local-cycle sword persists through hub load")

	g=fixture(412);h=room(g);g.cleared_stages.append_array([404,408]);g.flags.west_tower_safe=true;g.flags.island_loop_safe=true;g.flags.D42_done=true
	await FourthHub.action(h,"third_messenger")
	check(h.ui.pages.any(func(page):return str(page.text).contains("定潮枪尚未取得")) and h.ui.menu.has("确认第四章收束"),"fourth-chapter warning names missing lance while preserving choice")
	g=fixture(511);h=room(g);g.mode="hub";g.flags.west_palace_gate=true;g.flags.east_palace_gate=true;g.route_positions={"alm":15,"celica":15};g.flags.chapter5_ready={"alm":true,"celica":true}
	g.ChapterFive.selection(g,"alm");g.ChapterFive.selection(g,"celica")
	await FifthHub.action(h,"fifth_merge")
	check(h.ui.pages.any(func(page):return str(page.text).contains("镇关枪尚未取得")),"fifth-chapter warning names unclaimed archive lance")
	check(g.ChapterFive.merge(g) and not g.Armaments.claimed(g,7),"skipping optional archive still permits merge")
	var boss=g.stages[534].enemies.filter(func(unit):return str(unit.id)==str(g.stages[534].boss_id))[0]
	west.item_id=59
	check(not g.Rules.attack_blocked(west,boss) and g.Rules.attack_stats(west,boss,0).can_attack,"ordinary weapon remains valid against final boss")
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"settlement_fixtures":outcomes,"isolated_saves":CACHE,"scope":"six fixed rewards, numeric rules, permissions, full convoys, real objectives, repeat/retry/save, warning choices"},"  "));f.close()
	print("STORY_ARMAMENTS ",checks.size()," checks; errors: ",errors)
	quit(0 if errors.is_empty() else 1)

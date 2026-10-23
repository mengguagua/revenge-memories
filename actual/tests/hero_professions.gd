extends SceneTree
## Targeted profession/HP-cost checks; all writes use a temporary directory.
const State = preload("res://core/game_state.gd")
const Heroes = preload("res://core/hero_professions.gd")
const Hub = preload("res://core/chapter4_hub.gd")
const CACHE = "/private/tmp/revenge-hero-professions-20261023/"
var checks = []
var errors = []

class FakeUI extends RefCounted:
	var game
	var pages = []
	func play_pages(value, _back, _callback):pages.append_array(value)
class FakeHub extends RefCounted:
	var ui

func _initialize():
	DirAccess.make_dir_recursive_absolute(CACHE)
	call_deferred("run")
func check(ok: bool, label: String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh():
	var g = State.new();g.new_game();g.save_path=CACHE+"working.json"
	return g
func fourth():
	var g = State.new();g.save_path="res://reports/chapter3/play/round1final-chapter-end.json"
	check(g.load_game() and g.begin_chapter_four(),"chapter-three checkpoint enters fourth chapter")
	g.save_path=CACHE+"fourth.json"
	return g
func run():
	var g = fresh()
	var first = g.roster.duplicate(true)
	check(g.save_game() and g.load_game(),"first-chapter journal reads without granting professions")
	for id in first:
		for key in ["class_id","level","exp","hp","max_hp","strength","skill","speed","luck","defence","resistance","move","magic_level","magic_flags","item_id"]:
			check(g.roster[id][key]==first[id][key],"first-chapter journal preserves "+str(id)+" "+key)
	check(not Heroes.advanced(g.roster.hunapu) and g.roster.hunapu.move==5,"initial west leader remains fighter with move five")
	check(g.save_game(),"unadvanced checkpoint saves")
	var malformed = State.read_json(g.save_path)
	malformed.roster.hunapu.hero_profession="light_guide"
	check(not g.SaveValidation.campaign_valid(g,malformed,g.SAVE_FIELDS),"mismatched profession marker is rejected before load")
	var existing=State.new();existing.save_path="res://reports/campaign/natural-M11-deployment-save.json"
	check(existing.load_game() and not Heroes.advanced(existing.roster.hunapu) and existing.roster.hunapu.move==5,"existing first-chapter battle record retains original profession")

	g=fourth()
	# Use low permanent stats plus equipment bonuses to exercise real minima.
	for id in ["hunapu","eileen"]:
		var u = g.roster[id]
		u.level=9;u.exp=57;u.hp=7;u.magic_level=7;u.item_id=53
		u.max_hp=28;u.strength=8;u.skill=6;u.speed=6;u.luck=7;u.defence=4
		u.resistance=4 if id=="hunapu" else 7
		var before=u.duplicate(true)
		g.ChapterFour.promote_hero(g,id)
		u=g.roster[id]
		check(Heroes.advanced(u),id+" gains exclusive profession")
		for key in ["level","exp","hp","growths","magic_flags","magic_level","item_id","class_id"]:
			check(u[key]==before[key],id+" preserves "+key)
		for key in Heroes.DEFINITIONS[id].bases:
			check(int(u[key])==int(Heroes.DEFINITIONS[id].bases[key]),id+" reaches permanent "+str(key)+" minimum")
		check(u.move==Heroes.DEFINITIONS[id].move,id+" gains exact base movement")
		var advanced=u.duplicate(true);g.ChapterFour.promote_hero(g,id)
		check(g.roster[id]==advanced,id+" repeated progression grants nothing")
		check(g.EquipmentComparison.profession_name(u,g.catalog.classes)==Heroes.name(u),id+" equipment and status share profession name")
		check(g.Progression.promotion_options(u).is_empty(),id+" has no ordinary shrine promotion")
	check(g.roster.hunapu.resistance==4,"west progression preserves original resistance")
	var high=g._initial_character("eileen")
	for key in Heroes.DEFINITIONS.eileen.bases:high[key]=40
	high.hp=15;high.item_id=56
	check(Heroes.apply(high) and high.max_hp==40 and high.strength==40 and high.resistance==40 and high.hp==15,"higher stats and current HP never decrease")
	check(g.Items.movement(high)==10,"equipment movement bonus remains separate from base five")
	for id in ["hunapu","eileen"]:
		var wounded=g._initial_character(id);wounded.hp=0;wounded.dying=true
		check(not Heroes.apply(wounded) and wounded.hp==0 and wounded.dying,"progression does not revive "+id)
	var ordinary=g._initial_character("lisa");ordinary.class_id=11;ordinary.promoted=true
	check(not Heroes.apply(ordinary) and not Heroes.advanced(ordinary),"another sword mage cannot inherit protagonist profession")
	var enemy=g.roster.eileen.duplicate(true);enemy.side="enemy"
	check(not Heroes.advanced(enemy),"enemy cannot use protagonist trait")

	var west=g.roster.hunapu
	for bow in [20,21,22,63,64]:check(g.Items.can_use(west,bow),"advanced west leader can equip bow "+str(bow))
	var bow_user=west.duplicate(true);bow_user.item_id=63;bow_user.erase("weapon_index")
	check(g.Rules.attack_range(bow_user).y==3,"copper bow keeps its own range without bow-knight extension")
	check(not g.Items.can_use(west,1+1) and not g.Items.can_use(west,65),"west profession gains neither lance nor focus permission")
	var east=g.roster.eileen
	var original_flags=int(east.magic_flags)
	check(not 25 in g.Items.spells(east),"progression does not grant unlearned Ragnarok")
	for spec in [[23,1],[24,1],[26,3],[27,2],[25,9]]:
		var actor=east.duplicate(true);actor.magic_flags=255;actor.hp=30;actor.weapon_index=int(spec[0])
		check(g.Items.cost_for(actor,int(spec[0]))==int(spec[1]) and g.Rules.magic_cost(actor)==int(spec[1]),"actual attack cost matches UI for spell "+str(spec[0]))
		actor.hp=int(spec[1]);check(not g.Rules.can_attack(actor),"strict HP gate at exact cost "+str(spec[0]))
		actor.hp+=1;check(g.Items.can_use(actor,int(spec[0])) and g.Rules.can_attack(actor),"reduced cost enables legal attack "+str(spec[0]))
		var missed=g.Rules.strike_effect(actor,enemy,false,false)
		check(missed.valid and missed.hp_cost==int(spec[1]) and missed.damage==0,"miss still spends actual cost "+str(spec[0]))
	check(east.magic_flags==original_flags,"cost checks grant no learned magic")
	var unlearned=east.duplicate(true);unlearned.magic_flags=1
	check(g.Items.cost_for(unlearned,25)==10 and not g.Items.can_use(unlearned,25),"unlearned attack remains unavailable")
	check(g.Items.cost_for(east,42)==0,"original zero cost stays zero")
	for spell in [35,36,37,40,41,43]:check(g.Items.cost_for(east,spell)==g.Items.cost(spell),"support keeps original cost "+str(spell))
	var plain=g._initial_character("eileen");plain.magic_flags=255
	check(g.Items.cost_for(plain,24)==2 and g.Items.cost_for(enemy,24)==2,"unadvanced and enemy costs remain unchanged")
	var training=g.Progression.learn_spells(east,12)
	check(25 in g.Items.spells(training.unit) and training.unit.magic_level==int(east.magic_level)+12,"personal training still learns Ragnarok at its existing threshold")

	# Exercise the real planner/committer, including enemy initiated counters.
	g.route="celica";g.party=g.parties.celica.duplicate();g.world_node=26
	check(g.start_battle(405),"advanced east leader deploys on a real battlefield")
	var actor=g.find_unit("eileen");actor.magic_flags=255;actor.weapon_index=24;actor.hp=8;actor.speed=30;actor.position=[6,7]
	var foe=g.find_unit("F41_e1");foe.position=[7,7];foe.max_hp=255;foe.hp=255;foe.strength=1;foe.skill=0;foe.speed=0;foe.luck=0;foe.resistance=100;foe.item_id=0
	var hp_before=int(actor.hp)
	var planned=g.plan_combat("eileen",str(foe.id))
	var own=planned.events.filter(func(event):return event.attacker=="eileen")
	check(own.size()==2 and own.all(func(event):return event.hp_cost==1),"active attack and follow-up each pay discounted Thunder cost")
	check(int(actor.hp)==hp_before,"planning and cancellation spend no HP")
	for event in planned.events:g.commit_strike(event)
	check(actor.hp==planned.events[-1].source_hp_after,"committer applies planned per-cast HP")
	actor.hp=2
	planned=g.plan_combat("eileen",str(foe.id));own=planned.events.filter(func(event):return event.attacker=="eileen")
	check(own.size()==1 and own[0].hp_cost==1,"follow-up stops when remaining HP cannot pay again")
	actor.hp=8;actor.weapon_index=24;actor.position=[6,7];foe.position=[8,7];foe.weapon_index=24;foe.magic_flags=255;foe.class_id=15;foe.strength=1;foe.resistance=100
	planned=g.plan_combat(str(foe.id),"eileen");own=planned.events.filter(func(event):return event.attacker=="eileen")
	check(own.size()==2 and own.all(func(event):return event.weapon_index==23 and event.hp_cost==1),"counter and counter follow-up retain existing Fire choice and cost floor")

	# Checkpoint round trip and retry retain the profession with original HP.
	g=fourth();g.ChapterFour.promote_hero(g,"hunapu");g.ChapterFour.promote_hero(g,"eileen");g.world_node=10
	check(g.start_battle(401),"advanced west leader deploys")
	g.find_unit("hunapu").hp=11;g.save_path=CACHE+"advanced-battle.json"
	check(g.save_game(),"advanced battle checkpoint saves")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game() and Heroes.advanced(loaded.find_unit("hunapu")) and loaded.find_unit("hunapu").hp==11,"battle checkpoint retains profession and current HP")
	check(loaded.retry_battle() and Heroes.advanced(loaded.find_unit("hunapu")) and loaded.find_unit("hunapu").move==6,"retry preserves advanced deployment")

	# Existing room actions own the trigger; eastern observations do not promote.
	g=fourth();var h=FakeHub.new();h.ui=FakeUI.new();h.ui.game=g
	await Hub.action(h,"fourth_tower_shutdown")
	check(not Heroes.advanced(g.roster.hunapu),"tower without observation steps does not promote")
	g.flags.obs_steps_ready=true
	await Hub.action(h,"fourth_tower_shutdown")
	check(Heroes.advanced(g.roster.hunapu) and g.flags.west_tower_safe,"safe shutdown action promotes west leader")
	var after=g.roster.hunapu.duplicate(true);await Hub.action(h,"fourth_tower_shutdown")
	check(g.roster.hunapu==after,"repeat tower action does not grant extra stats")
	await Hub.action(h,"fourth_obs_report")
	check(not Heroes.advanced(g.roster.eileen),"F42 observation report does not promote east leader")
	await Hub.action(h,"fourth_island_verify")
	check(Heroes.advanced(g.roster.eileen) and g.flags.eileen_local_cycle_understood,"H48 local-cycle action promotes east leader")
	after=g.roster.eileen.duplicate(true);await Hub.action(h,"fourth_island_verify")
	check(g.roster.eileen==after,"repeat local-cycle action does not grant extra stats")
	check(h.ui.pages.filter(func(page):return str(page.text).contains("进阶为引光剑使")).size()==1,"east progression announcement appears only once")
	var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"isolated_saves":CACHE,"scope":"first-chapter journal, progression nodes, stats, weapon permissions, training, planner and per-cast HP"}
	var f=FileAccess.open("res://reports/hero-professions-20261023/checks.json",FileAccess.WRITE)
	if f==null:
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/hero-professions-20261023"));f=FileAccess.open("res://reports/hero-professions-20261023/checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify(report,"  "));f.close()
	print("HERO_PROFESSIONS ",checks.size()," checks; errors: ",errors)
	quit(0 if errors.is_empty() else 1)

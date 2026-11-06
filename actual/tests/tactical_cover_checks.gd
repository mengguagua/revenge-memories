extends SceneTree
const State=preload("res://core/game_state.gd")
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label)
func fixture():
	var g=State.new();g.new_game();g.world_node=2;g.start_battle(101)
	g.save_path="/private/tmp/tactical-cover-fixture.json"
	g.story_events.clear()
	return g
func run():
	var g=fixture();var a=g.find_unit("hunapu")
	var b=g.living("player").filter(func(u):return not u.get("neutral",false) and u.id!=a.id)[0]
	a.position=[6,13];b.position=[7,13];b.acted=true;g.selected_id=a.id
	check(g.begin_cover(b.id),"physical ally can cover adjacent teammate")
	check(a.acted and g.selected_id=="","cover consumes the action")
	check(not g.begin_cover(b.id),"spent actor cannot repeat cover")
	check(g.save_game(),"active cover can be saved")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game(),"active cover checkpoint reloads")
	check(loaded.Cover.guard_for(loaded,loaded.find_unit(b.id)).get("id","")==a.id,"load preserves active neighbour protection")
	var shadow={};var split=g.Cover.split(g,b,9,shadow)
	check(split.damage==5 and split.remaining_damage==4,"odd damage divides with guard taking the larger half")
	check(int(a.hp)==int(split.hp_before) and a.has("cover_target"),"planning does not consume real guard or HP")
	check(g.Cover.split(g,b,9,shadow).is_empty(),"one guard cannot absorb a second planned hit")
	var enemy=g.living("enemy")[0];var before_a=int(a.hp);var before_b=int(b.hp)
	g.apply_tactical_damage(enemy,b,9,"physical")
	check(int(a.hp)==before_a-5 and int(b.hp)==before_b-4,"special attack uses the same shared-damage rule")
	check(not a.has("cover_target"),"actual hit consumes cover")
	g.apply_tactical_damage(enemy,b,3,"magic")
	check(int(b.hp)==before_b-7,"next damage is no longer shared")
	g=fixture();a=g.find_unit("hunapu");b=g.living("player").filter(func(u):return not u.get("neutral",false) and u.id!=a.id)[0]
	a.position=[6,13];b.position=[7,13];b.acted=true;a.hp=1;g.selected_id=a.id;g.begin_cover(b.id)
	before_b=int(b.hp);enemy=g.living("enemy")[0]
	g.apply_tactical_damage(enemy,b,10,"physical")
	check(int(a.hp)==0 and int(b.hp)==before_b-9,"one-HP guard cannot erase lethal overflow")
	check(g.is_dying(a),"guard reaching zero HP enters ordinary casualty system")
	g=fixture();a=g.find_unit("hunapu");b=g.living("player").filter(func(u):return not u.get("neutral",false) and u.id!=a.id)[0]
	a.position=[6,13];b.position=[7,13];b.acted=true;g.selected_id=a.id;g.begin_cover(b.id)
	check(g.Cover.split(g,b,0,{}).is_empty() and a.has("cover_target"),"miss or zero damage retains cover")
	check(not g.select_unit(b.id) and a.has("cover_target"),"spent covered target cannot start another move")
	b.position=[10,13];g.Cover.refresh(g)
	check(not a.has("cover_target"),"confirmed separation ends protection")
	a.acted=false;b.position=[7,13];b.acted=true;g.selected_id=a.id;g.begin_cover(b.id)
	g.next_phase();check(a.has("cover_target"),"cover remains through enemy phase")
	g.next_phase();check(not a.has("cover_target"),"cover expires at next player phase")
	a.acted=false;b.acted=true;g.selected_id=a.id;g.begin_cover(b.id)
	var partner=g.living("player").filter(func(u):return not u.get("neutral",false) and u.id!=a.id and u.id!=b.id)[0]
	b.position=[10,13];partner.position=[11,13]
	check(g.Inventory.exchange(g,partner.id,b.id),"ready partner may exchange with a spent covered target")
	b.position=[7,13]
	check(not a.has("cover_target"),"later returning adjacent cannot reactivate cover after committed separation")
	var bow=b.duplicate(true);bow.class_id=12
	check(not g.Cover.eligible(bow),"adjacent bow range is not physical melee capability")
	var sword_mage=b.duplicate(true);sword_mage.class_id=11
	check(g.Cover.eligible(sword_mage),"sword-capable mage can cover")
	# Exercise the real randomised exchange planner, not only the damage helper.
	g=fixture();a=g.find_unit("hunapu");b=g.living("player").filter(func(u):return not u.get("neutral",false) and u.id!=a.id)[0]
	a.position=[6,13];b.position=[7,13];b.acted=true;enemy=g.living("enemy")[0];enemy.position=[7,12]
	var exchange={}
	for seed in range(256):
		a.acted=false;g.selected_id=a.id;g.begin_cover(b.id);g.rng_state=seed
		exchange=g.plan_combat(enemy.id,b.id)
		if exchange.events.any(func(e):return not e.get("cover",{}).is_empty()):break
	check(not exchange.is_empty() and exchange.events.any(func(e):return not e.get("cover",{}).is_empty()),"normal exchange generates a shared damage event")
	var saved_a=int(a.hp)
	for event in exchange.get("events",[]):g.commit_strike(event)
	g.finish_exchange(exchange)
	check(int(a.hp)<saved_a and not a.has("cover_target"),"normal exchange commits shared damage without extra counter")
	check(g.retry_battle(),"normal retry remains available")
	check(g.units.all(func(u):return not u.has("cover_target")),"retry removes later tactical state")
	check(g.save_game(),"retry checkpoint remains valid")
	var bad=JSON.parse_string(FileAccess.get_file_as_string(g.save_path))
	bad.units[0].class_id=[];bad.units[0].cover_target="daan";bad.units[0].cover_turn=1
	check(not g.SaveValidation.campaign_valid(g,bad,g.SAVE_FIELDS),"malformed covered class type is rejected before conversion")
	var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"scope":"Controlled rule fixtures, save/reload and actual exchange planner; separate from normal-input playthroughs."}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://reports/tactical-expansion-20261025"))
	var f=FileAccess.open("res://reports/tactical-expansion-20261025/cover-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("COVER_CHECKS ",checks.size()," ",errors);quit(0 if errors.is_empty() else 1)

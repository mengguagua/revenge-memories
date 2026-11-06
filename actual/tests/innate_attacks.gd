extends SceneTree
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")
const Inventory=preload("res://core/battle_inventory.gd")
const Loot=preload("res://core/campaign_loot.gd")
const Validation=preload("res://core/campaign_save_validation.gd")
const BodyAnimation=preload("res://core/innate_attack_animation.gd")
var checks=[]
var errors=[]
func _initialize():call_deferred("run")
func check(value:bool,label:String):
	checks.append(label)
	if not value:errors.append(label);push_error(label)
func stage(code:String) -> Dictionary:return State.read_json("res://data/stages/"+code+".json")
func boss(code:String) -> Dictionary:
	var d=stage(code);return d.enemies.filter(func(u):return u.id==d.boss_id)[0].duplicate(true)
func player() -> Dictionary:
	var g=State.new();var u=g._initial_character("hunapu");u.position=[16,9];u.hp=52;u.max_hp=52;u.defence=8;u.resistance=2;u.strength=10;u.speed=4;u.skill=10;u.luck=0;u.item_id=0;return u
func setup(code:String):
	var g=State.new();g.new_game();g.battle_data=stage(code);g.stage_id=int(g.battle_data.id);g.chapter=int(g.battle_data.chapter)
	g.mode="battle";g.battle_outcome="";g.units=[player(),boss(code)];g.units[0].position=[int(g.units[1].position[0]),int(g.units[1].position[1])+1]
	g.flags.inventory_processed_deaths={};g.flags.pending_loot=[];g.save_path="/private/tmp/innate-attacks-test.json"
	return g
func run():
	var target=player();var stone=boss("S22");var spit=boss("S21");var god=boss("J54")
	var bone=stone.duplicate(true);bone.id="bone";bone.class_id=5;bone.erase("body_armour");bone.erase("recoverable_item_id")
	check(Rules.weapon_index(stone)==1001,"stone default is independent claw")
	check(Rules.weapon_index(spit)==1002,"S21 uses independent rock spit")
	check(Rules.attack_range(stone)==Vector2i(1,1) and Rules.attack_range(spit)==Vector2i(1,2),"only configured stone variant gains range two")
	check(int(stone.item_id)==0 and int(spit.item_id)==0,"S21/S22 bodies hold no human equipment")
	check(Items.physical_defence_bonus(stone)==5 and int(stone.defence)+Items.physical_defence_bonus(stone)==12,"thick stone retains effective physical defence twelve")
	for pair in [[stone,0],[spit,4]]:
		var old_attack=pair[0].duplicate(true);old_attack.side="player";old_attack.character_id=1;old_attack.item_id=pair[1]
		var old_stats=Rules.attack_stats(old_attack,target,0);var new_stats=Rules.attack_stats(pair[0],target,0)
		for key in ["damage","hit","attack_speed","hp_cost","magic"]:check(old_stats[key]==new_stats[key],str(pair[0].id)+" retains original attack balance "+key)
	for u in [stone,spit,bone,god]:
		for item in [4,49,55,59,62,66]:check(not Items.can_use(u,item),str(u.id)+" cannot equip human item "+str(item))
		check(Items.spells(u).is_empty(),str(u.id)+" has no borrowed human spell menu")
		check(Validation._campaign_unit(State.new(),u,true),str(u.id)+" new body fields validate")
	for id in Rules.Body.PROFILES:
		check(not Items.can_use(target,id),"innate ID is not player equipment "+str(id))
		check(not Validation._carried_item(id),"innate ID is not saveable inventory "+str(id))
		check(Items.item(id).kind=="innate_attack","independent profile kind "+str(id))
	var near=Rules.attack_context(bone,1);var far=Rules.attack_context(bone,2)
	check(Rules.weapon_index(near)==1003 and Rules.weapon_index(far)==1004,"bone attack selects jaw near and breath far")
	check(not Rules.attack_stats(near,target,0).magic and Rules.attack_stats(far,target,0).magic,"jaw physical and breath magical")
	check(Rules.attack_stats(near,target,0).defender_defence==8 and Rules.attack_stats(far,target,0).defender_defence==2,"body modes use actual physical/magic defence")
	check(Rules.magic_cost(near)==0 and Rules.magic_cost(far)==1,"only breath spends health")
	check(not Rules.attack_stats(near,target,0).effective,"enemy bone never inherits friendly falcon monster effectiveness")
	bone.hp=1;check(Rules.can_attack(bone,1) and not Rules.can_attack(bone,2),"exhausted bone can bite but cannot breathe")
	check(int(god.class_id)==21 and int(god.character_id)==169,"J54 uses divine class without Duma source")
	check(Rules.weapon_index(Rules.attack_context(god,1))==1006,"J54 initiates with crown even adjacent")
	check(Rules.weapon_index(Rules.default_counter(god,1))==1005,"J54 adjacent counter is beak")
	check(Rules.weapon_index(Rules.default_counter(god,2))==1006,"J54 distance two counter is crown")
	var original=god.duplicate(true);original.class_id=15;original.magic_flags=1;original.erase("campaign_final_boss")
	var before=Rules.attack_stats(original,target,0);var after=Rules.attack_stats(god,target,0)
	for key in ["damage","hit","attack_speed","hp_cost","magic"]:check(before[key]==after[key],"crown retains old ghost-fire balance "+key)
	check(Loot.role(god)==Loot.role(original) and Loot.pool(god)==Loot.pool(original),"J54 old ordinary loot pool retained")
	god.hp=10;check(not Rules.attack_blocked(target,god),"ordinary attacks still damage wounded J54")
	check(Items.phase_effect(god,0).heal==0,"J54 does not receive Duma healing")
	var old=god.duplicate(true);old.character_id=167;old.erase("campaign_final_boss")
	check(Rules.attack_blocked(target,old),"source167 final weapon restriction remains separate")
	for code in ["S21","S22"]:
		for variant in ["normal","no_drop","event"]:
			var g=setup(code);var enemy=g.units[1];var killer=g.units[0];enemy.hp=0;killer.item_id=12
			if variant=="no_drop":enemy.no_drop=true
			var rng=int(g.rng_state);var result=Inventory.on_death(g,enemy,{} if variant=="event" else killer)
			check(g.rng_state==rng,code+" fixed recovery consumes no random loot roll "+variant)
			if variant=="normal":
				check(int(result.item_id)==(4 if code=="S21" else 49) and result.destination=="pending",code+" fixed nest recovery preserves held player gear")
				check(Inventory.on_death(g,enemy,killer).is_empty() and g.flags.pending_loot.size()==1,code+" processed once")
				check(Inventory.resolve_loot(g,"store") and g.convoy.alm.size()==1 and int(killer.item_id)==12,code+" store retains current equipment")
			else:check(result.is_empty(),code+" no fixed recovery for "+variant)
		check(Inventory.rare_drop(boss(code),2,0,0,0)==0,code+" excluded from rare roll after held item removed")
		check(Loot.ordinary_drop(boss(code),0,0)==0,code+" excluded from ordinary loot roll")
	var wild=stone.duplicate(true);wild.erase("recoverable_item_id");wild.erase("body_armour")
	check(Inventory.rare_drop(wild,2,0,0,0)==8,"unarmed wild stone retains eligible meteor loot")
	var skeleton=wild.duplicate(true);skeleton.class_id=17;skeleton.character_id=193;check(Loot.role(skeleton)=="monster","new skeletal guard uses monster loot rather than human magic focus")
	for code in ["S21","S22","J54"]:
		var g=setup(code);var p=g.units[0];var enemy=g.units[1]
		var plan=g.plan_combat(enemy.id,p.id)
		check(not plan.is_empty() and plan.events.size()>0,code+" real combat builds event sequence")
		var expected=1002 if code=="S21" else 1001 if code=="S22" else 1006
		check(plan.events.filter(func(e):return e.attacker==enemy.id).all(func(e):return int(e.weapon_index)==expected),code+" planned strikes select independent attack")
		var reverse=g.plan_combat(p.id,enemy.id)
		check(reverse.events.filter(func(e):return e.attacker==enemy.id).all(func(e):return int(e.weapon_index)==(1005 if code=="J54" else expected)),code+" actual adjacent counter selects correct mode")
		if code=="J54":
			g.ChapterFive.initialize(g);enemy.hp=56;g.ChapterFive.check_outcome(g)
			check(g.flags.quest.final_phase and int(enemy.strength)==18,"J54 half-health strength gains exactly three")
			check(g.units.filter(func(u):return str(u.id).begins_with("J54_summon")).size()==3,"J54 one existing wave of three")
			g.ChapterFive.check_outcome(g)
			check(int(enemy.strength)==18 and g.units.size()==5,"J54 repeat outcome cannot strengthen or summon twice")
			check(g.units.filter(func(u):return str(u.id).begins_with("J54_summon")).all(func(u):return u.no_drop and int(u.item_id)==0 and Rules.weapon_index(u)==1001),"J54 reinforcements are unarmed claw bodies with no loot")
	for id in Rules.Body.PROFILES:
		var graphic={"frames":8,"pose_map":{"idle":0,"prepare":1,"release":2,"recover":3,"bite_prepare":4,"bite_contact":5}}
		var selected=BodyAnimation.selection(graphic,{"weapon_index":id},Vector2(64,128),Vector2(176,128),true)
		check(selected.kind=="source" and int(selected.variant.contact_tick)>0 and int(selected.variant.contact_tick)<selected.variant.frames.size(),"valid one-contact timeline "+str(id))
		check(selected.variant.frames.all(func(f):return int(f.frame)>=0 and int(f.frame)<8),"all key poses available "+str(id))
	var invalid=stone.duplicate(true);invalid.body_armour="plate";check(not Validation._body_fields(invalid),"reject unknown armour")
	invalid=stone.duplicate(true);invalid.recoverable_item_id=1001;check(not Validation._body_fields(invalid),"reject body attack as recovery")
	invalid=god.duplicate(true);invalid.innate_attack_index=1001;check(not Validation._body_fields(invalid),"reject wrong species attack in save")
	invalid=target.duplicate(true);invalid.body_attack="stone_spit";check(not Validation._body_fields(invalid),"reject body marker on human")
	for role in ["short_blink","bounded_summoner","bounded_divider","summoned_minion"]:
		invalid=target.duplicate(true);invalid.campaign_role=role;check(not Validation._body_fields(invalid),"reject enemy AI role on player "+role)
	invalid=stone.duplicate(true);invalid.campaign_role="short_blink";check(not Validation._body_fields(invalid),"reject wrong class AI role")
	invalid=wild.duplicate(true);invalid.class_id=18;invalid.campaign_role="bounded_divider";invalid.role_summons_used=2;check(not Validation._body_fields(invalid),"reject divider count beyond one")
	invalid.role_summons_used=1;check(Validation._body_fields(invalid),"one divider use valid")
	invalid=wild.duplicate(true);invalid.role_last_turn=3;check(not Validation._body_fields(invalid),"reject role counter without role")
	var right_art={"frame_size":[256,256],"anchor":[64,112],"native_density":2,"default_facing":"right"}
	check(not BodyAnimation.horizontal_flip(right_art,true),"right-facing body at left faces its opponent without mirror")
	check(BodyAnimation.horizontal_flip(right_art,false),"right-facing body at right mirrors toward opponent")
	var left_art=right_art.duplicate(true);left_art.default_facing="left"
	check(BodyAnimation.horizontal_flip(left_art,true),"legacy left-facing body at left mirrors toward opponent")
	check(BodyAnimation.safe_origin(right_art,Vector2(32,128))==Vector2(72,128),"ranged large body keeps eight pixel horizontal field inset")
	check(BodyAnimation.safe_origin(right_art,Vector2(208,128))==Vector2(184,128),"right-side large body stays inside field")
	check(BodyAnimation.effect_sprites().innate_glow.path.ends_with("cde5d1cef16d92.png"),"crown light uses inspected pure light orb, no insects")
	check(preload("res://core/portrait_library.gd").unit(State.new(),god).get("key","")=="vucub","named final boss uses its own portrait")
	var dir="res://reports/enemy-deployment-20261023/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(dir))
	var f=FileAccess.open(dir+"innate-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks.size(),"errors":errors,"labels":checks},"\t"));f.close()
	print("INNATE_ATTACK_CHECKS ",checks.size()," errors=",errors);quit(1 if not errors.is_empty() else 0)

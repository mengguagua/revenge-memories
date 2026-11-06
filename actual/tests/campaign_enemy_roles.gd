extends SceneTree
const State=preload("res://core/game_state.gd")
const Roles=preload("res://core/campaign_enemy_roles.gd")
const OUT="res://reports/enemy-deployment-20261023/role-checks.json"
const CACHE="/private/tmp/revenge-enemy-role-checks/"
var checks=[]
var errors=[]
var observations={}
func _initialize():
	DirAccess.make_dir_recursive_absolute(CACHE)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT.get_base_dir()))
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fixture(code:String):
	var g=State.new()
	g.save_path="res://reports/chapter4/play/round2-"+code+"-deployment.json"
	check(g.load_game(),"real deployment fixture loads "+code)
	g.save_path=CACHE+code+".json";g.story_events.clear()
	var id=g.stage_id;check(g.start_battle(id),"restart against current authored deployment "+code)
	g.story_events.clear();return g
func act(g,u:Dictionary):
	u.acted=false
	var a=g.ai_action(u)
	if a.has("special"):return g.apply_ai_special(u,a)
	return {}
func run():
	var g=State.new();g.new_game()
	var deployed=[]
	for key in g.stages:
		var d=g.stages[key]
		for u in d.enemies+d.get("reinforcements",[]):
			if not deployed.has(int(u.class_id)):deployed.append(int(u.class_id))
	for cid in [4,5,9,10,13,14,16,17,18,19,21]:check(deployed.has(cid),"campaign really deploys missing enemy class "+str(cid))
	check(not deployed.has(23) and not deployed.has(24),"reserved hero/princess not forced into maps")
	for cid in [3,5,11,14,15,16,17,18,19,21]:
		check(str(g.catalog.classes[str(cid)].enemy_name_zh) in ["石翼兽","骸翼兽","蚀躯","断路匪","执令术师","隙行术师","骸卫","裂目兽","驭魔师","神躯"],"new enemy display name "+str(cid))
	g=fixture("F43");var cantor=g.find_unit("F43_e8");var divider=g.find_unit("F43_e3")
	check(cantor.class_id==19 and cantor.magic_flags==17,"F43 separate cantor configured to summon bonewalkers")
	check(g.find_unit("F43_boss").class_id==15 and g.battle_data.summon_template.class_id==6,"original boss and one-off soldier wave remain separate")
	g.turn=2
	check(not g.ai_action(cantor).has("special"),"no cantor summons before announced turn three")
	g.turn=3;var first=act(g,cantor)
	check(first.get("spawned",[]).size()==2,"first cantor use produces at most two skull guards")
	check(cantor.hp==25 and cantor.role_summons_used==1,"successful summon pays two HP once")
	var childids=first.get("spawned",[]).duplicate()
	for id in childids:
		var child=g.find_unit(id)
		check(child.max_hp==24 and child.strength==9 and child.speed==4,"finite child stays within F43 stat budget "+id)
		check(child.acted and child.no_experience and child.no_drop,"newborn cannot attack or yield rewards "+id)
		check(not Roles.protected_cell(g,g.pos(child)),"newborn avoids objective cells "+id)
		check(child.summoner_id==cantor.id and child.class_id==17,"newborn bound to correct summoner "+id)
	g.turn=4;cantor.acted=false;check(not g.ai_action(cantor).has("special"),"summoner three-turn cooldown")
	g.turn=6;var second=act(g,cantor)
	check(second.get("spawned",[]).size()==2 and cantor.role_summons_used==2,"second and final summon succeeds")
	childids.append_array(second.get("spawned",[]))
	g.turn=12;cantor.acted=false;check(not g.ai_action(cantor).has("special"),"healing or waiting cannot produce third wave")
	var split=act(g,divider)
	check(split.get("spawned",[]).size()==1 and divider.role_summons_used==1,"original mogall divides only once into one body")
	var child=g.find_unit(str(split.get("spawned",[""])[0]));child.acted=false
	check(not g.ai_action(child).has("special"),"offspring cannot start recursive splitting")
	check(child.speed==4 and child.strength==9,"split offspring does not inherit source speed18 promotion minimum")
	check(g.Rules.attack_range(child)==Vector2i(1,1) and not g.Rules.attack_stats(child,divider,0).magic,"split body only makes ordinary physical melee")
	g.turn=20;divider.acted=false;check(not g.ai_action(divider).has("special"),"original mogall cannot split a second time")
	var natural=g.stages[306].enemies.filter(func(u):return int(u.class_id)==17)[0].duplicate(true)
	natural.id="natural_bonewalker";natural.position=[7,7];g.units.append(natural)
	var unrelated=g.find_unit(str(childids[0])).duplicate(true);unrelated.id="other_summoner_child";unrelated.summoner_id="other_cantor";g.units.append(unrelated)
	cantor.hp=0;var removed=g.Summons.cleanup(g,cantor)
	check(removed.size()==4,"defeated cantor removes exactly its own four skull guards")
	check(natural.hp>0 and unrelated.hp>0 and child.hp>0,"natural guards, another caster's child and divided body survive cleanup")
	observations.cantor={"spawned":childids,"removed":removed}

	g=fixture("F43");cantor=g.find_unit("F43_e8");g.turn=3
	var reward_child_ids=act(g,cantor).spawned
	var reward_child=g.find_unit(str(reward_child_ids[0]));reward_child.hp=1
	# Use the leader's legal personal sword; an unusable lance must not grant
	# perfect hit merely because it is being carried.
	var killer=g.find_unit(g.leader_id());killer.item_id=18;killer.strength=40;killer.skill=40
	killer.position=[int(reward_child.position[0]),int(reward_child.position[1])+1]
	var exp_before=int(killer.exp);var loot_before=g.flags.get("pending_loot",[]).size()
	var exchange=g.plan_combat(str(killer.id),str(reward_child.id))
	check(not exchange.is_empty(),"summoned guard can enter real planned combat")
	for event in exchange.get("events",[]):g.commit_strike(event)
	var earned=g.finish_exchange(exchange)
	check(int(reward_child.hp)==0 and earned.is_empty() and int(killer.exp)==exp_before,"real summoned guard kill grants no combat XP")
	check(g.flags.get("pending_loot",[]).size()==loot_before and g.Inventory.on_death(g,reward_child,killer).is_empty(),"real summoned guard kill and repeated death processing grant no loot")
	cantor.hp=1;killer.acted=false;killer.position=[int(cantor.position[0]),int(cantor.position[1])+1]
	exchange=g.plan_combat(str(killer.id),str(cantor.id))
	for event in exchange.get("events",[]):g.commit_strike(event)
	earned=g.finish_exchange(exchange)
	check(int(cantor.hp)==0 and not earned.is_empty(),"summoner itself retains ordinary one-time combat XP")
	check(int(g.find_unit(str(reward_child_ids[1])).hp)==0 and g.find_unit(str(reward_child_ids[1])).get("vanished",false),"real summoner death pipeline clears own surviving minion")

	g=fixture("F43");cantor=g.find_unit("F43_e8");g.turn=3
	for i in range(20-g.living("enemy").size()):
		var full=cantor.duplicate(true);full.id="capacity_"+str(i);full.enemy_slot=g.units.filter(func(u):return str(u.side)=="enemy").size();full.position=[2+i,2];g.units.append(full)
	check(not g.ai_action(cantor).has("special"),"twenty-slot capacity blocks new summons")
	g=fixture("F43");cantor=g.find_unit("F43_e8");g.turn=3;cantor.hp=2
	check(not g.ai_action(cantor).has("special"),"summon cannot spend final HP")
	g=fixture("F43");cantor=g.find_unit("F43_e8");g.turn=3;act(g,cantor)
	check(g.save_game(),"summon usage and newborns save through campaign serializer")
	var loaded=State.new();loaded.save_path=g.save_path
	check(loaded.load_game(),"summon usage and newborns reload")
	check(int(loaded.find_unit("F43_e8").get("role_summons_used",0))==1,"reload preserves consumed summon budget")
	check(loaded.retry_battle() and not loaded.find_unit("F43_e8").has("role_summons_used"),"retry restores original finite budget and original deployment")

	g=fixture("F42");var witch=g.find_unit("F42_e3")
	check(witch.class_id==16 and g.find_unit("F42_e1").get("ch4_burner",false),"new witch leaves authored burner identity intact")
	check(g.battle_data.enemy_role_hint.contains("第2回合") and g.battle_data.enemy_role_hint.contains("四格"),"entry warning states first turn, radius and wasted action")
	g.turn=2;var origin=g.pos(witch);var before=g.units.duplicate(true);var a=g.ai_action(witch)
	check(a.get("special","")=="campaign_blink","short-range witch produces announced relocation")
	check(g.units==before,"planning relocation does not mutate units or consume cooldown")
	if a.get("special","")=="campaign_blink":
		check(Roles.distance(origin,a.teleport_position)<=4 and not Roles.protected_cell(g,a.teleport_position),"blink bounded to four tiles and avoids record doors")
		check(a.target=="" and not a.support,"blink action cannot carry an attack or cast")
		for p in g.living("player"):check(Roles.distance(a.teleport_position,g.pos(p))>=3,"blink leaves response distance to "+str(p.id))
		g.apply_ai_special(witch,a);check(witch.acted and witch.role_last_turn==2,"blink consumes whole action and records cooldown")
		g.turn=3;witch.acted=false;check(not g.ai_action(witch).has("special"),"witch cannot bypass new cooldown with old random teleport")
	observations.blink={"origin":str(origin),"result":str(a)}
	g=fixture("S42");var dragon=g.find_unit("S42_e1")
	check(g.save_game(),"authored S42 deployment with bone dragon saves")
	var dragon_load=State.new();dragon_load.save_path=g.save_path
	check(dragon_load.load_game() and int(dragon_load.find_unit("S42_e1").class_id)==5,"bone dragon S42 checkpoint round trip")
	g.turn=2;var early=g.ai_action(dragon);check(early.destination==g.pos(dragon),"bone dragon retains turn-three advance gate")
	check(dragon.hp==30 and dragon.strength==9 and dragon.speed==4 and dragon.move==8,"bone dragon tuned as slow, mobile one-unit threat")
	check(g.Rules.attack_range(dragon).y==2,"bone dragon AI sees its breath range")
	check(g.TacticalAI._source_range(dragon)==2,"legacy range filter does not suppress breath")
	var last_hp=dragon.duplicate(true);last_hp.hp=1
	var target=g.find_unit(g.leader_id()).duplicate(true);target.position=[int(last_hp.position[0])+1,int(last_hp.position[1])]
	check(g.can_attack(last_hp,target),"HP1 bone dragon still makes cost-free adjacent bite through game targets")
	target.position[0]+=1;check(not g.can_attack(last_hp,target),"HP1 bone dragon cannot spend its last HP on ranged breath")
	var j=g.stages[534].enemies.filter(func(u):return str(u.id)=="J54_boss")[0].duplicate(true)
	j.hp=20;j.side="enemy";j.position=dragon.position.duplicate();j.acted=false
	check(j.class_id==21 and j.get("campaign_final_boss",false),"final boss has independent god-body marker")
	var hero=g.find_unit(g.leader_id()).duplicate(true);j.move=0;j.acted=false
	var landed=false
	for y in range(1,int(g.battle_data.map.height)-1):
		for x in range(1,int(g.battle_data.map.width)-2):
			if landed:continue
			if g.movement_cost(j,Vector2i(x,y))>=255 or g.movement_cost(hero,Vector2i(x+1,y))>=255:continue
			j.position=[x,y];hero.position=[x+1,y];landed=true
	g.units=[j,hero];var god_action=g.TacticalAI.action(g,j)
	check(str(god_action.target)==str(hero.id) and not god_action.has("special"),"low-HP new god body keeps attacking and never invokes old split logic")
	var un=State.new();un.new_game();un.world_node=int(un.stages[111].node);check(un.start_battle(111),"early mining detour still starts")
	check(un.find_unit("S11_e4").class_id==14 and un.find_unit("S11_e1").class_id==22,"two brigands replace selected raiders, remaining armoured guards retained")
	var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"observations":observations,"scope":"Headless authored deployment fixtures, controlled AI, bounded generation, save/retry; not full natural campaign play."}
	var f=FileAccess.open(OUT,FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("CAMPAIGN_ENEMY_ROLES ",checks.size()," checks; errors: ",errors);quit(0 if errors.is_empty() else 1)

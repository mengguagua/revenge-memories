extends SceneTree
## Targeted campaign enemy/equipment interactions, using isolated historical parties.
## Writes only /private/tmp; controlled placements are not natural playthrough evidence.
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const CACHE="/private/tmp/revenge-balance-enemy-audit/"
var checks=[]
var failures=[]
var observations={}
func _initialize():
	DirAccess.make_dir_recursive_absolute(CACHE)
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func fixture(code:String):
	var g=State.new()
	var source="res://reports/chapter4/play/round2-"+code+"-deployment.json" if code in ["F42","F43","S42"] else "res://reports/chapter5-environment-20261023/play/final-round2/final-round2-"+code+"-deployment.json"
	g.save_path=source
	check(g.load_game(),code+" historical deployment loads")
	g.save_path=CACHE+code+".json"
	check(g.start_battle(g.stage_id),code+" current deployment starts")
	g.story_events.clear()
	return g
func targets(g,enemy:Dictionary,shield:Dictionary,bare:Dictionary):
	var commander=g.find_unit("hunapu").duplicate(true)
	commander.position=[4,28];commander.acted=false
	g.units=[commander,shield,bare,enemy]
	var cells=[]
	for delta in g.DIRECTIONS:
		var cell=g.pos(enemy)+delta
		if g.in_bounds(cell) and g.movement_cost(shield,cell)<255 and g.movement_cost(bare,cell)<255:cells.append(cell)
	check(cells.size()>=2,"two legal target cells at "+str(enemy.id))
	if cells.size()<2:return
	shield.position=[cells[0].x,cells[0].y];shield.item_id=53;shield.player_slot=1;shield.acted=false
	bare.position=[cells[1].x,cells[1].y];bare.item_id=0;bare.player_slot=2;bare.acted=false
	enemy.acted=false;enemy.move=0
func target_observation(g,enemy,shield,bare):
	var result={"enemy":enemy.id,"action":g.ai_action(enemy),"shield":{},"bare":{}}
	for pair in [["shield",shield],["bare",bare]]:
		var u:Dictionary=pair[1]
		var actor=Rules.attack_context(enemy,1)
		var attack_spell=g.TacticalAI._attack_spell(actor)
		if attack_spell>=0:actor.weapon_index=attack_spell
		result[pair[0]]={"id":u.id,"hp":u.hp,"defence":u.defence,"resistance":u.resistance,"item":u.item_id,"score":g.TacticalAI._score(g,actor,u,g.pos(enemy),1,false),"actual":Rules.attack_stats(actor,u,g.terrain_avoid(g.pos(u)))}
	return result
func run():
	var g=fixture("J53")
	var enemy=g.find_unit("J53_e14").duplicate(true)
	var shield=g.find_unit("roan").duplicate(true)
	var bare=g.find_unit("otto").duplicate(true)
	targets(g,enemy,shield,bare)
	var physical=target_observation(g,enemy,shield,bare)
	observations.physical_shield=physical
	check(physical.shield.actual.damage<physical.bare.actual.damage,"new swordmaster actually damages unshielded Otto more than shielded Roan")
	check(str(physical.action.target)==str(bare.id),"swordmaster respects shield when choosing between live campaign defenders")
	g=fixture("J53");enemy=g.find_unit("J53_e8").duplicate(true);shield=g.find_unit("daan").duplicate(true);bare=g.find_unit("roan").duplicate(true)
	targets(g,enemy,shield,bare)
	var magical=target_observation(g,enemy,shield,bare)
	observations.magic_shield=magical
	check(magical.shield.actual.damage<magical.bare.actual.damage,"actual spell respects shield magic defence")
	check(str(magical.action.target)==str(bare.id),"campaign caster respects shield when choosing between live campaign defenders")
	g=fixture("S42");var dragon=g.find_unit("S42_e1");var patient=g.find_unit("island_group0")
	observations.patient_matchup={}
	for distance in [1,2]:
		var actor=Rules.attack_context(dragon,distance);var stats=Rules.attack_stats(actor,patient,0)
		observations.patient_matchup[str(distance)]={"attack":stats,"sequence":Rules.strike_sequence(actor,patient,distance),"patient_hp":patient.hp}
		check(stats.damage==7,"bone dragon deals seven to unarmoured patient at distance "+str(distance))
		check(Rules.strike_sequence(actor,patient,distance).count("attacker")==1,"slow bone dragon cannot double patient at distance "+str(distance))
	for turn in [1,2]:
		g.turn=turn;check(g.ai_action(dragon).destination==g.pos(dragon),"bone dragon waits before third turn "+str(turn))
	g=fixture("F43");g.phase="enemy";g.turn=3;g.ChapterFour.after_phase(g)
	var cantor=g.find_unit("F43_e8");var divider=g.find_unit("F43_e3");var generated=[]
	for actor in [cantor,divider]:
		actor.acted=false;var action=g.ai_action(actor);var result=g.apply_ai_special(actor,action);generated.append_array(result.get("spawned",[]))
	g.turn=6;cantor.acted=false;generated.append_array(g.apply_ai_special(cantor,g.ai_action(cantor)).get("spawned",[]))
	check(g.living("enemy").size()==18,"F43 authored maximum is eighteen including old and new summon waves")
	check(generated.size()==5,"finite roles create exactly four guards and one divider child")
	var slots={}
	for u in g.living("enemy"):
		check(int(u.enemy_slot)>=0 and int(u.enemy_slot)<20 and not slots.has(int(u.enemy_slot)),"F43 unique scheduled enemy slot "+str(u.id));slots[int(u.enemy_slot)]=true
	for id in generated:
		var child=g.find_unit(id)
		check(child.acted and child.no_drop and child.no_experience,"F43 newborn has no immediate action or rewards "+str(id))
		check(not g.EnemyRoles.protected_cell(g,g.pos(child)),"F43 newborn avoids objective "+str(id))
	observations.f43={"living":g.living("enemy").size(),"generated":generated}
	g=fixture("F42");var witch=g.find_unit("F42_e3");g.turn=2
	var origin=g.pos(witch);var blink=g.ai_action(witch)
	check(blink.get("special","")=="campaign_blink","F42 current role plans short blink on turn two")
	check(g.EnemyRoles.distance(origin,blink.teleport_position)<=4 and not g.EnemyRoles.protected_cell(g,blink.teleport_position),"F42 blink stays bounded and avoids record objectives")
	for player in g.living("player"):check(g.EnemyRoles.distance(blink.teleport_position,g.pos(player))>=3,"F42 blink leaves response space to "+str(player.id))
	g.apply_ai_special(witch,blink)
	check(witch.acted and witch.role_last_turn==2,"F42 blink consumes complete action")
	g.turn=3;witch.acted=false;check(not g.ai_action(witch).has("special"),"F42 cannot bypass cooldown via source teleport")
	g=fixture("J54");var boss=g.find_unit("J54_boss");var hero=g.find_unit("hunapu").duplicate(true);hero.item_id=0
	boss.hp=56;g.check_outcome()
	check(g.living("enemy").size()==13 and boss.strength==18 and boss.hp==56,"J54 half-health exactly three extra bodies and three strength, no healing")
	g.check_outcome();check(g.living("enemy").size()==13 and boss.strength==18,"J54 phase cannot duplicate")
	for hp in [56,51,1]:
		boss.hp=hp;check(not Rules.attack_blocked(hero,boss),"J54 unarmed ordinary sword remains valid at HP "+str(hp))
	check(g.Items.phase_effect(boss,0).heal==0,"J54 has no old Duma regeneration")
	var report={"passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"observations":observations,"scope":"Controlled headless placements/current enemy deployments with historical real party attributes; not natural clear or whole-campaign difficulty proof."}
	var f=FileAccess.open(CACHE+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("BALANCE_ENEMY_PROBE ",checks.size()," failures=",failures)
	quit(0 if failures.is_empty() else 1)

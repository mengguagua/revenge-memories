extends "res://tests/assessment_ai.gd"
## Scripted objectives, migration and genuine planned combat, without player saves.
func run():
	var g=fixture(204);var occupier=g.battle_data.enemies.filter(func(u):return u.get("objective_role","")=="seize_beacon")[0].duplicate(true)
	occupier.position=g.battle_data.targets[0].duplicate();occupier.acted=false
	var at=at_distance(g,occupier,3);var player=shooter(g);player.position=[at.x,at.y];g.units=[occupier,player]
	var hold=g.ai_action(occupier)
	check(hold.destination==g.pos(occupier) and str(hold.target).is_empty(),"healthy beacon occupier prioritizes control")
	occupier.hp-=1
	var response=g.ai_action(occupier);observations.append({"kind":"beacon_ranged_response","from":occupier.position.duplicate(),"to":str(response.destination),"target":response.target})
	check(response.destination!=g.pos(occupier),"wounded beacon occupier answers ranged fire with ordinary movement")
	occupier.position=[response.destination.x,response.destination.y];g.flags.quest.beacon_since=3;g.flags.quest.beacon_contested=true;g.check_outcome()
	check(g.flags.quest.beacon_since==-1 and not g.flags.quest.beacon_contested,"leaving beacon immediately cancels occupation timer")
	for spec in [[406,"observatory_record"],[411,"black_register"]]:
		g=fixture(spec[0]);g.flags.quest.record_lost=false;g.flags.quest.objects[spec[1]]=true
		var burner=g.battle_data.enemies.filter(func(u):return u.get("ch4_burner",false))[0].duplicate(true);burner.acted=false
		var result=action_observation(g,burner,3);observations.append(result)
		check(result.reacts,"burner fights after its arson objective is protected: "+str(spec[0]))
	# Source migration is exact, repeatable, and does not heal or teleport.
	g=fixture(534);var original=g.battle_data.enemies.filter(func(u):return u.id=="J54_boss")[0].duplicate(true)
	var old=original.duplicate(true);old.move=0;old.hp=37;old.position=[16,10];old.enemy_balance_revision=2
	g.EnemyBalance.prepare(534,[old])
	check(int(old.move)==4 and old.hp==37 and old.position==[16,10],"old final-boss movement migrates without healing or moving it")
	var once=old.duplicate(true);g.EnemyBalance.prepare(534,[old]);check(old==once,"movement migration does not stack")
	var custom=original.duplicate(true);custom.move=2;custom.enemy_balance_revision=2;g.EnemyBalance.prepare(534,[custom]);check(custom.move==2,"unknown custom boss movement survives migration")
	# New movement is executed through the real combat planner; no added range.
	var row=action_observation(g,original,5);observations.append(row)
	check(row.reacts and not row.counter_before,"final boss closes a five-tile approach rather than inventing a five-tile counter")
	var action=g.ai_action(original);original.position=[action.destination.x,action.destination.y]
	var exchange=g.plan_combat(str(original.id),str(action.target))
	check(not exchange.is_empty() and int(exchange.distance)<=2,"final-boss attack planner accepts only its true one/two-tile strike")
	check(exchange.events.all(func(e):return int(e.weapon_index) in [1005,1006,1,22]),"planned combat uses existing body and bow profiles")
	# Formal combatants may trigger guards; civilians alone cannot empty a post.
	g=fixture(101);var guard=g.battle_data.enemies[0].duplicate(true);guard.acted=false
	at=at_distance(g,guard,2);player=shooter(g);player.position=[at.x,at.y];player.neutral=true;player.no_counter=true;g.units=[guard,player]
	check(g.ai_action(guard).destination==g.pos(guard),"civilian at range two alone cannot provoke a melee guard's pursuit")
	player.neutral=false;player.no_counter=false;check(g.ai_action(guard).destination==g.pos(guard),"mere proximity outside melee reach does not activate a whole garrison")
	var warning=g.plan_combat(str(player.id),str(guard.id))
	check(not warning.is_empty(),"ranged warning uses real combat planner")
	for event in warning.get("events",[]):g.commit_strike(event)
	check(g.ai_action(guard).destination!=g.pos(guard) and bool(guard.guard_alerted),"actual ranged attack raises persistent alert")
	player.position=g.battle_data.player_positions[0].duplicate();guard.acted=false
	check(g.ai_action(guard).destination!=g.pos(guard),"alerted guard does not reset when the attacker backs away")
	var threatened=g.RefugeeTactics.evaluate(g,player,g.pos(guard)+Vector2i(2,0))
	check(int(threatened.threats)>0,"escort forecast includes a guard's ordinary movement")
	# Preserved scripted escape has precedence over the new guard reaction.
	g=fixture(105);g.turn=8;var fleeing=g.battle_data.enemies.filter(func(u):return u.id=="M15_boss")[0].duplicate(true);fleeing.acted=false
	g.units=[fleeing];var escape=g.ai_action(fleeing)
	check(escape.destination!=g.pos(fleeing) and str(escape.target).is_empty(),"M15 commander keeps its scripted eighth-turn escape")
	# The actual failed first-battle checkpoint keeps its wounded refugees;
	# inspect the next decision without changing any saved HP or positions.
	var source="res://reports/full-assessment-20261025/campaign-final/ch1/chain-M11-turn-4.json"
	if FileAccess.file_exists(source):
		var live=State.new();live.save_path=source;check(live.load_game(),"authentic first-battle turn-four checkpoint loads")
		live.save_path="/private/tmp/revenge-assessment-ai-refugee-copy.json"
		for id in ["M11_refugees0","M11_refugees1"]:
			var refugee=live.find_unit(id);var old_acted=bool(refugee.acted);refugee.acted=false
			var safety=live.ai_action(refugee);refugee.acted=old_acted
			observations.append({"kind":"authentic_refugee_next_action","id":id,"hp":refugee.hp,"position":refugee.position,"action":safety,"acted_reset_for_next_action_only":true})
	# A wounded armed escort has a legal route back to its formal screen.
	g=fixture(101);var escort=g.battle_data.npc_units[0].duplicate(true);escort.hp=8;escort.position=[9,10];escort.acted=false
	var pursuer=g.battle_data.enemies[1].duplicate(true);pursuer.position=[9,8];pursuer.acted=false
	var cover=g.characters.hunapu.duplicate(true);cover.side="player";cover.position=[9,14];cover.hp=cover.max_hp;cover.acted=false
	g.units=[escort,pursuer,cover];var retreat=g.ai_action(escort)
	check(retreat.get("reason","")=="escort_disengage" and retreat.destination!=g.pos(escort),"wounded armed refugee retreats from an exposed position")
	check(int(retreat.get("risk_after",999))<int(retreat.get("risk_before",0)),"refugee retreat strictly reduces forecast enemy-phase damage")
	check(g.reachable(escort).costs.has(retreat.destination) and g.can_stop(escort,retreat.destination),"refugee retreat obeys ordinary movement and occupancy")
	var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"observations":observations,"scope":"Controlled objective/HP/position fixtures and one real combat plan, not a natural stage-clear record."}
	var f=FileAccess.open(OUT+"edge-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("ASSESSMENT_AI_EDGES ",checks.size()," errors=",errors)
	quit(0 if errors.is_empty() else 1)

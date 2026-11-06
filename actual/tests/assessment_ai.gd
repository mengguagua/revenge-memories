extends SceneTree
## Controlled AI counterexamples on the authored maps; not a campaign playthrough.
const State=preload("res://core/game_state.gd")
const Rules=preload("res://core/combat_rules.gd")
const OUT="res://reports/full-assessment-20261025/ai/"
var errors=[]
var checks=[]
var observations=[]
var baseline=false
var attack_first=true
func _initialize():
	baseline=OS.get_cmdline_user_args().has("--baseline")
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label)
func fixture(stage:int):
	var g=State.new();g.new_game();g.stage_id=stage;g.chapter=int(g.stages[stage].chapter)
	g.battle_data=g.stages[stage].duplicate(true);g.route=str(g.battle_data.route);g.world_node=int(g.battle_data.node)
	g.mode="battle";g.phase="enemy";g.turn=8;g.flags.quest={"objects":{},"evacuated":[],"freed":[],"reinforced":true}
	g.units=[];g.story_events.clear();g.save_path="/private/tmp/revenge-assessment-ai-unused.json"
	return g
func shooter(g):
	var u=g.characters.roan.duplicate(true);u.id="probe_archer";u.side="player";u.hp=u.max_hp;u.acted=false;u.dead=false;u.item_id=22;u.player_slot=0
	return u
func at_distance(g,unit:Dictionary,distance:int)->Vector2i:
	var candidates=[];var origin=g.pos(unit);var player=shooter(g)
	for y in range(int(g.battle_data.map.height)):
		for x in range(int(g.battle_data.map.width)):
			var p=Vector2i(x,y)
			if absi(x-origin.x)+absi(y-origin.y)==distance and g.movement_cost(player,p)<255 and g.movement_cost(unit,p)<255:candidates.append(p)
	# Prefer a connected approach from the same authored map.
	g.units=[unit];var graph=g.reachable(unit,true)
	for p in candidates:
		if graph.costs.has(p):return p
	return Vector2i(-1,-1)
func action_observation(g,enemy:Dictionary,range_value:int):
	var at=at_distance(g,enemy,range_value)
	if at==Vector2i(-1,-1):return {}
	var player=shooter(g);player.position=[at.x,at.y];g.units=[enemy,player]
	var origin=g.pos(enemy);var committed=[]
	if attack_first:
		var exchange=g.plan_combat(str(player.id),str(enemy.id))
		for event in exchange.get("events",[]):
			g.commit_strike(event);committed.append({"hit":event.hit,"damage":event.damage,"hp_after":event.hp_after,"weapon_index":event.weapon_index})
	var action=g.ai_action(enemy)
	var destination:Vector2i=action.get("destination",origin)
	return {"stage":g.battle_data.code,"enemy":enemy.id,"distance":range_value,"origin":[origin.x,origin.y],"shooter":[at.x,at.y],"destination":[destination.x,destination.y],"target":action.get("target",""),"spell_id":action.get("spell_id",-1),"special":action.get("special",""),"reacts":destination!=origin or not str(action.get("target","")).is_empty(),"defeated":int(enemy.hp)<=0,"response_or_defeated":int(enemy.hp)<=0 or destination!=origin or not str(action.get("target","")).is_empty(),"combat_events":committed,"counter_before":Rules.can_attack(Rules.default_counter(enemy,range_value),range_value),"guard_alerted":enemy.get("guard_alerted",false)}
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var inventory=[]
	var seed=State.new()
	for stage in seed.stages:
		for original in seed.stages[stage].enemies:
			if str(original.get("behavior","")) not in ["guard","guard_exit"]:continue
			var g=fixture(stage);var enemy=original.duplicate(true);enemy.acted=false
			if enemy.get("campaign_role","")=="bounded_summoner":enemy.role_summons_used=2
			var reach=Rules.attack_range(enemy).y
			var row=action_observation(g,enemy,mini(5,maxi(2,reach+1)))
			if row.is_empty():continue
			inventory.append(row)
			if not baseline:check(bool(row.response_or_defeated),str(g.battle_data.code)+" "+str(enemy.id)+" responds to reachable long-range attack or is legitimately defeated")
	# A distant guard should not abandon its post merely because civilians exist.
	var g=fixture(101);var guard=g.battle_data.enemies[0].duplicate(true);guard.acted=false
	var player=shooter(g);player.position=g.battle_data.player_positions[0].duplicate();g.units=[guard,player]
	var idle=g.ai_action(guard)
	check(idle.destination==g.pos(guard) and str(idle.target).is_empty(),"distant M11 commander holds initial post")
	# Scripted S42 grace period is explicit and finite.
	g=fixture(412);var beast=g.battle_data.enemies.filter(func(u):return str(u.id)=="S42_e1")[0].duplicate(true)
	for turn in [1,2]:
		g.turn=turn;beast.acted=false;g.units=[beast]
		check(g.ai_action(beast).destination==g.pos(beast),"S42 announced delay remains on turn "+str(turn))
	g=fixture(407);var cantor=g.battle_data.enemies.filter(func(u):return str(u.id)=="F43_e8")[0].duplicate(true)
	cantor.role_summons_used=2;cantor.acted=false
	var spell=action_observation(g,cantor,3);observations.append(spell)
	if not baseline:check(spell.reacts and int(spell.spell_id)==31,"exhausted campaign cantor uses existing ghost-fire spell")
	var stagnant=inventory.filter(func(r):return not r.response_or_defeated)
	var report={"baseline":baseline,"checks":checks.size(),"errors":errors,"stationary_cases":inventory.size(),"stagnant":stagnant.size(),"cases":inventory,"observations":observations,"scope":"Controlled isolated enemy plus legal long-range archer placements on current authored maps. Preserves enemy stats, role and map. Not natural playthrough or whole-stage success proof."}
	var f=FileAccess.open(OUT+("baseline.json" if baseline else "checks.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("ASSESSMENT_AI checks=",checks.size()," stationary=",inventory.size()," stagnant=",stagnant.size()," errors=",errors)
	quit(0 if errors.is_empty() else 1)

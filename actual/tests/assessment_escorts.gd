extends "res://tests/assessment_ai.gd"
## Isolated, real-map escort decisions. Does not change player progress.
func run():
	var original_source="res://reports/full-assessment-20261025/campaign-final-r1/ch1/chain-S11-turn-4.json"
	var g=State.new();g.save_path=original_source
	check(g.load_game(),"authentic S11 turn-four party and miner state loads")
	g.save_path="/private/tmp/revenge-assessment-escort-unused.json"
	for id in ["S11_miners0","S11_miners1","beck"]:
		var u=g.find_unit(id);u.acted=false
		var before=g.RefugeeTactics.evaluate(g,u,g.pos(u));var a=g.ai_action(u);var after=g.RefugeeTactics.evaluate(g,u,a.destination)
		observations.append({"kind":"authentic_S11_decision","id":id,"hp":u.hp,"origin":u.position.duplicate(),"destination":str(a.destination),"action":a,"incoming_before":before.incoming,"incoming_after":after.incoming})
		check(g.reachable(u).costs.has(a.destination) and g.can_stop(u,a.destination),"S11 ordinary legal landing: "+id)
		if id=="S11_miners1":check(int(after.incoming)<=int(before.incoming),"exposed miner never chooses a more dangerous tile; a blocked retreat still requires player cover")
	# On a clear route, the same injured groups resume evacuation without healing.
	for enemy in g.living("enemy"):enemy.hp=0
	g.flags.quest.reinforced=true
	for id in ["S11_miners0","S11_miners1"]:
		var u=g.find_unit(id);u.acted=false;var hp=int(u.hp);var a=g.ai_action(u)
		check(a.destination!=g.pos(u) and int(u.hp)==hp,"cleared route resumes ordinary escort movement without free healing: "+id)
	# Mobile ranged threats must be considered beyond the old four-tile radius.
	g=fixture(111);var miner=g.battle_data.npc_units[0].duplicate(true);miner.position=[12,17];miner.move=2;miner.acted=false
	var boss=g.battle_data.enemies[0].duplicate(true);boss.position=[12,11];boss.acted=false
	g.units=[miner,boss]
	var old_candidate=g._toward(miner,Vector2i(12,10));var old_risk=g.RefugeeTactics.evaluate(g,miner,old_candidate.destination)
	var safe=g._safe_escort_move(miner,Vector2i(12,10));var safe_risk=g.RefugeeTactics.evaluate(g,miner,safe.destination)
	observations.append({"kind":"mobile_threat","previous_toward":str(old_candidate.destination),"previous_incoming":old_risk.incoming,"safe_destination":str(safe.destination),"safe_incoming":safe_risk.incoming})
	check(int(old_risk.incoming)>0 and int(safe_risk.incoming)==0,"automatic path never walks from safety into the mobile boss attack zone")
	# Check each authored mobile civilian in its own full initial map layout.
	var seed=State.new();var checked=0
	for stage in seed.stages:
		g=fixture(stage);g.turn=1;g.flags.quest.record_lost=false
		g.units=g.battle_data.enemies.duplicate(true)+g.battle_data.npc_units.duplicate(true)
		for raw in g.battle_data.npc_units:
			if raw.get("locked",false) or raw.get("battle_guard",false):continue
			if str(raw.get("quest_kind","")) not in ["escort","medicine","prisoner","patient","sailor","guide"]:continue
			var u=g.find_unit(str(raw.id));u.acted=false
			var before=g.RefugeeTactics.evaluate(g,u,g.pos(u));var a=g.ai_action(u)
			check(g.reachable(u).costs.has(a.destination) and g.can_stop(u,a.destination),str(g.battle_data.code)+" civilian landing remains legal: "+str(u.id))
			if str(a.get("target","")).is_empty():
				var after=g.RefugeeTactics.evaluate(g,u,a.destination)
				check(int(after.incoming)<=int(before.incoming),str(g.battle_data.code)+" civilian does not choose more incoming damage: "+str(u.id))
			checked+=1
	var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"mobile_civilian_cases":checked,"observations":observations,"scope":"Actual failed S11 checkpoint inspected without changing HP/positions, plus explicitly controlled mobile-threat and authored initial-map fixtures. Not a guaranteed-survival claim or natural campaign victory."}
	var f=FileAccess.open(OUT+"escort-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("ASSESSMENT_ESCORTS ",checks.size()," cases=",checked," errors=",errors)
	quit(0 if errors.is_empty() else 1)

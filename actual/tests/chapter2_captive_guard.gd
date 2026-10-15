extends SceneTree
## Reproduce the shipped-entry failure through actual tactical decisions and
## combat calculations. No HP/defence edits and no victory injection.
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var failures: Array=[]
var enemy_decisions: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func actual_entry():
	var g=State.new();g.save_path="res://reports/chapter2/play/natural-F22-deployment-save.json"
	check(g.load_game(),"actual F22 entry checkpoint loads")
	var roster=g.roster.duplicate(true)
	check(g.return_to_preparation(),"return-to-preparation retains true previous growth")
	check(g.travel_to(19) and g.start_battle(202),"re-enter by real world road using current deployment")
	check(g.roster==roster,"no previous character growth or items changed")
	return g
func run() -> void:
	var g=actual_entry();var held={}
	for u in g.units:
		if u.get("locked",false):held[str(u.id)]=int(u.hp)
	check(held.size()==4,"four actually held prisoners present")
	for round_ in range(3):
		if not g.battle_outcome.is_empty():break
		for u in g.living("player"):g.mark_wait(str(u.id))
		g.next_phase()
		check(g.phase=="enemy","enemy phase starts normally")
		for slot in range(20):
			for u in g.living("enemy"):
				if int(u.get("enemy_slot",-1))!=slot or bool(u.acted):continue
				var action=g.ai_action(u);var path=g.path_to(u,action.destination)
				check(not held.has(str(action.target)),"guard decision ignores still-held prisoner")
				check(not path.is_empty(),"guard follows a legal current-map path")
				enemy_decisions.append({"turn":g.turn,"unit":u.id,"from":u.position.duplicate(),"to":[action.destination.x,action.destination.y],"target":action.target})
				check(g.select_unit(str(u.id)) and g.move_selected(action.destination),"normal engine movement applies guard choice")
				if str(action.target).is_empty():g.mark_wait(str(u.id))
				else:
					if int(action.get("spell_id",-1))>=0:u.weapon_index=action.spell_id
					else:u.erase("weapon_index")
					var exchange=g.plan_combat(str(u.id),str(action.target))
					check(not exchange.is_empty(),"ordinary selected attack resolves")
					for event in exchange.get("events",[]):g.commit_strike(event)
					g.finish_exchange(exchange)
				if not g.battle_outcome.is_empty():break
			if not g.battle_outcome.is_empty():break
		for id in held:check(int(g.find_unit(id).hp)==held[id],"round %d prisoner %s not automatically executed" % [round_+1,id])
		check(g.living("player").any(func(u):return held.has(str(u.id))),"AI filtering does not hide prisoners from phase or objective state")
		if not g.battle_outcome.is_empty():break
		g.next_phase()
	check(g.turn>=4 and g.battle_outcome.is_empty(),"three full unattended enemy rounds no longer fail rescue before door")
	# Opening the actual gate restores ordinary target legality. The snapshot
	# below is a targeted adjacency fixture, not a played victory.
	var opened=actual_entry();var prisoner=opened.find_unit("prisoners_0");var guard=opened.find_unit("F22_e1")
	guard.position=[int(prisoner.position[0])+1,int(prisoner.position[1])]
	check(not opened.can_attack(guard,prisoner),"held prisoner excluded from guard attack intent")
	var door=opened.battle_data.objects.filter(func(o):return o.id=="prison_door")[0]
	var hero=opened.find_unit("eileen");hero.position=[int(door.position[0]),int(door.position[1])+1];hero.acted=false;opened.selected_id="eileen"
	check(opened.interact("prison_door"),"actual gate interaction releases assigned prisoners")
	check(not prisoner.locked and opened.can_attack(guard,prisoner),"released prisoner immediately becomes an ordinary threatened escort")
	var hp_before=int(prisoner.hp);var exchange=opened.plan_combat(str(guard.id),str(prisoner.id));check(not exchange.is_empty(),"released prisoner has normal combat resolution")
	for event in exchange.get("events",[]):opened.commit_strike(event)
	opened.finish_exchange(exchange)
	check(int(prisoner.hp)<hp_before,"released prisoner takes actual unmodified guard damage")
	var report={"scope":"Three real enemy-AI rounds from actual F22 entry and targeted release/attack check; no HP edits or forced victories","passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"turn_after":g.turn,"enemy_decisions":enemy_decisions}
	var f=FileAccess.open("res://reports/chapter2/captive-guard-check.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("CAPTIVE_GUARD ",JSON.stringify({"passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"turn_after":g.turn}));quit(0 if failures.is_empty() else 1)

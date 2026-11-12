extends "res://tests/ch2_environment_play.gd"
const PLAY_ROOT="/private/tmp/map-ambient-20261112/"
func run():
	var sources=State.read_json("/Users/gcc/gaocc/project/revenge-memories/art-review/map-ambient-20261112/source/sources.json")
	var records=[]
	for code in sources:
		ui=load("res://scenes/main.tscn").instantiate()
		ui.game.slot_directory=PLAY_ROOT+"play"
		ui.game.save_path=PLAY_ROOT+"play-working.json"
		root.add_child(ui);await process_frame
		ui.instant_mode=true
		ui.game.save_path=sources[code]
		var loaded=ui.game.load_game()
		ui.game.save_path=PLAY_ROOT+"play-working.json"
		if not loaded or (code!="M15" and not ui.game.retry_battle()):record_failure("Cannot enter "+code);break
		ui._resume_journey();await settle()
		ui.set_physics_process(false)
		var actor=ui.game.living("player").filter(func(u):return u.get("controllable",true))[0]
		var start=State.pos(actor)
		var to=start
		for step in ui.game.DIRECTIONS:
			var candidate=start+step
			if ui.game.reachable(actor).costs.has(candidate) and ui.game.can_stop(actor,candidate):to=candidate;break
		if to==start:record_failure("No ordinary movement landing "+code);break
		cursor_to(start);key(KEY_Z);cursor_to(to);key(KEY_Z);await settle()
		choose("wait");await settle()
		if State.pos(actor)!=to:record_failure("Ordinary movement failed "+code);break
		key(KEY_S);choose("new:goal");await settle()
		if ui.view!="battle":record_failure("Objective pages did not return "+code);break
		key(KEY_S);choose("end_turn");await settle()
		if ui.game.turn<2 or not ui.game.battle_outcome.is_empty():record_failure("Phase transition failed "+code);break
		records.append({"code":code,"moved_from":[start.x,start.y],"moved_to":[to.x,to.y],"returned_from_objectives":true,"turn":ui.game.turn,"effects_enabled":ui.map_ambient.enabled})
		print("AMBIENT_PLAY ",records[-1])
		ui.queue_free();await process_frame;ui=null
	var file=FileAccess.open(PLAY_ROOT+"play-check.json",FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":not abort and records.size()==40,"checks":records,"failures":failures,"scope":"40 genuine checkpoints; ordinary movement, wait, objective pages, and one end-turn cycle on each map. Not full campaign completion."},"  "));file.close()
	quit(0 if not abort and records.size()==40 else 1)

extends "res://tests/play_base.gd"
## Two rounds through actual menus and key input, using copies of historical
## victorious rosters. No unit, RNG, position, outcome or progression edits.
const TRAINING_OUT="res://reports/tactical-expansion-20261025/training/"
const SOURCES={
	"early":"res://reports/full-assessment-20261025/campaign-final-r1/ch1/chain-M13-victory.json",
	"late":"res://reports/full-assessment-20261025/campaign-final-r4/ch4/chain-M41-victory.json"}
var round_index=1
var current_label=""
var extra_checks=[]
var round_battles=[]
var observed_dialogue=[]
func _initialize():call_deferred("run")
func verify(ok:bool,label:String):
	extra_checks.append({"label":label,"passed":ok})
	if not ok:record_failure(label)
func settle()->void:
	for i in range(10000):
		if abort:return
		if ui.view in ["plot","reward"]:
			if ui.view=="plot" and not ui.plot_pages.is_empty():
				var text=JSON.stringify(ui.plot_pages)
				if not observed_dialogue.has(text):observed_dialogue.append(text)
			key(KEY_Z)
		elif ui.view in ["loot","loot_confirm"]:choose("store" if ui.menu_actions.has("store") else "discard_new" if ui.view=="loot" else "confirm")
		if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:
			await process_frame
			if not ui.busy and not ui.batch_running and not ui.result_sequence_running and ui.view not in ["plot","reward","loot","loot_confirm"]:return
		await process_frame
	record_failure("Training input did not release: "+ui.view)
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--round="):round_index=int(arg.trim_prefix("--round="))
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(TRAINING_OUT))
	for label in ["early","late"]:
		if abort:break
		current_label=label
		var folder=TRAINING_OUT+"round%d-%s/"%[round_index,label]
		DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(folder))
		ui=load("res://scenes/main.tscn").instantiate()
		ui.game.slot_directory=folder;ui.game.save_path=folder+"working.json"
		root.add_child(ui);await process_frame;ui.instant_mode=true
		ui.audio.set_music_enabled(false);ui.audio.set_sfx_enabled(false)
		DirAccess.copy_absolute(ProjectSettings.globalize_path(SOURCES[label]),ProjectSettings.globalize_path(ui.game.save_path))
		verify(ui.game.load_game(),"load untouched historical victory "+label)
		if abort:break
		ui._resume_journey();await settle()
		verify(ui.view=="victory","resume main-story victory before training "+label)
		if abort:break
		key(KEY_Z);choose("continue_world");await settle()
		verify(ui.view=="world","ordinary victory confirmation reaches world "+label)
		if abort:break
		var original_stage=ui.game.stage_id;var original_node=ui.game.world_node
		var original_clears=ui.game.cleared_stages.duplicate()
		var original_dying=[]
		for id in ui.game.roster:
			if ui.game.is_dying(ui.game.roster[id]):original_dying.append(id)
		var ids=[191,192] if label=="early" else [481,482]
		if round_index==2:ids.reverse()
		# Exercise entry and exit before committing a success, through the same
		# menus players use; the second entry must remain available afterwards.
		await enter_training(int(ids[0]))
		if abort:break
		key(KEY_S);choose("training:leave");await settle()
		verify(ui.view=="world" and ui.game.stage_id==original_stage and ui.game.world_node==original_node,"exit before completion returns to original location "+label)
		verify(ui.game.Training.remaining(ui.game)==2,"voluntary exit consumes no training success "+label)
		for stage_id in ids:
			if abort:break
			await enter_training(int(stage_id))
			if abort:break
			var entry_path=folder+str(stage_id)+"-entry.json"
			var old=ui.game.save_path;ui.game.save_path=entry_path;verify(ui.game.save_game(),"entry checkpoint saved "+str(stage_id));ui.game.save_path=old
			await exercise_battle()
			if abort:break
			verify(ui.game.battle_outcome=="victory" and ui.game.battle_settled,"natural training victory settled "+str(stage_id))
			if abort:break
			var victory_path=folder+str(stage_id)+"-victory.json"
			old=ui.game.save_path;ui.game.save_path=victory_path;verify(ui.game.save_game(),"victory checkpoint saved "+str(stage_id));ui.game.save_path=old
			key(KEY_Z);choose("training:leave");await settle()
			verify(ui.view=="world" and ui.game.stage_id==original_stage and ui.game.world_node==original_node,"training victory returns to original stage/node "+str(stage_id))
			verify(ui.game.cleared_stages==original_clears,"training never changes story clears "+str(stage_id))
			verify(original_dying.all(func(id):return ui.game.is_dying(ui.game.roster[id])),"training never revives prior casualties "+str(stage_id))
		if not abort:verify(ui.game.Training.remaining(ui.game)==0,"success cap reached through normal gameplay "+label)
		if not abort:
			key(KEY_S);choose("new:camp");choose("training:open");choose("training:detail:"+str(ids[0]));await settle()
			verify(not ui.menu_actions.has("training:start:"+str(ids[0])),"third training has no start action "+label)
			choose("training:open");key(KEY_X);await settle()
			if not ui.menu_items.is_empty():key(KEY_X)
			# The normal world and hub route remain available after training.
			key(KEY_Z);verify(ui.menu_actions.has("new:hub"),"main-story hub remains reachable "+label)
			if not abort:choose("new:hub");await settle();verify(ui.view=="hub","main-story hub enters normally after finite training "+label)
		write_report()
		ui.queue_free();await process_frame;ui=null
	write_report();quit(0 if not abort else 1)
func enter_training(id:int)->void:
	key(KEY_S);choose("new:camp");choose("training:open");choose("training:detail:"+str(id));await settle()
	if abort:return
	verify(ui.menu_context=="training_confirm" and ui.menu_actions.has("training:start:"+str(id)),"training details lead to explicit start "+str(id))
	if abort:return
	choose("training:start:"+str(id));await settle()
	verify(ui.view=="battle" and ui.game.stage_id==id and ui.game.Training.active(ui.game),"training starts through UI "+str(id))
func plan(unit:Dictionary)->Dictionary:
	var base=combat_plan(unit)
	var goal=Vector2i(ui.game.battle_data.training_target[0],ui.game.battle_data.training_target[1])
	if ui.game.can_stop(unit,goal) and ui.game.reachable(unit).costs.has(goal):
		if ui.game.battle_data.training_variant=="capture":return {"kind":"wait","cell":goal,"score":9999,"target":"","spell":-1}
		# Preserve a defender at the flag unless it is already in immediate
		# danger; all other units use ordinary attack/heal positioning.
		if State.pos(unit)==goal and risk(unit,goal)<int(unit.hp)-2:
			if base.cell==goal:return base
			return {"kind":"wait","cell":goal,"score":999,"target":"","spell":-1}
		if ui.game.unit_at(goal).is_empty() and risk(unit,goal)<int(unit.hp)-2:
			return {"kind":"wait","cell":goal,"score":999,"target":"","spell":-1}
	return base
func exercise_battle()->void:
	var record={"round":round_index,"stage":ui.game.stage_id,"code":ui.game.battle_data.code,"start_inputs":inputs,"entry_players":ui.game.living("player").duplicate(true),"turns":[]}
	for step in range(12):
		if abort or not ui.game.battle_outcome.is_empty():break
		var turn=ui.game.turn
		var members=ui.game.living("player").filter(func(u):return bool(u.get("controllable",true)))
		members.sort_custom(func(a,b):return rank(a)<rank(b))
		for member in members:
			if abort or not ui.game.battle_outcome.is_empty() or ui.game.turn!=turn:break
			await act(str(member.id))
		if not abort and ui.game.battle_outcome.is_empty() and ui.game.turn==turn:
			key(KEY_S);choose("end_turn");await settle()
		record.turns.append({"turn":ui.game.turn,"alive":ui.game.living("player").size(),"enemies":ui.game.living("enemy").size(),"held":ui.game.flags.quest.get("training_held",0),"outcome":ui.game.battle_outcome})
		print("TRAINING_PLAY ",record.code," turn=",ui.game.turn," outcome=",ui.game.battle_outcome)
	record.outcome=ui.game.battle_outcome;record.final_turn=ui.game.turn;record.inputs=inputs-int(record.start_inputs)
	record.final_players=ui.game.living("player").duplicate(true);round_battles.append(record)
	if ui.game.battle_outcome!="victory":record_failure("Training driver did not win naturally: "+str(record.code)+" "+ui.game.battle_outcome)
func write_report()->void:
	var report={"round":round_index,"passed":not abort,"failures":failures,"checks":extra_checks,"battles":round_battles,"inputs":inputs,"operations":operations,"observed_dialogue":observed_dialogue,"native_graphics":false,"scope":"Headless UI with actual key/menu inputs; original historical victorious rosters copied and resumed normally. No gameplay stats, moves, RNG, outcomes or story flags edited."}
	var f=FileAccess.open(TRAINING_OUT+"play-round%d.json"%round_index,FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()

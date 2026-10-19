extends SceneTree
## Focused M11 decision and real automatic-turn regression, with independent saves.
const State=preload("res://core/game_state.gd")
const IDS=["M11_refugees0","M11_refugees1"]
class ObservedMain extends "res://core/main.gd":
	var observed_attacks:Array=[]
	func _play_combat(attacker_id:String,defender_id:String)->void:
		observed_attacks.append({"attacker":attacker_id,"defender":defender_id})
		await super._play_combat(attacker_id,defender_id)
var checks:Array=[]
var errors:Array=[]
var results:Dictionary={}
var ui
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func fresh(id:int=101):
	var game=State.new();game.new_game();game.world_node=int(game.stages[id].node)
	game.save_path="/private/tmp/m11-refugee-ai-independent-save.json"
	check(game.start_battle(id),"start stage "+str(id));game.story_events.clear();return game
func legal_attack(game,unit:Dictionary,action:Dictionary):
	var target=game.find_unit(str(action.get("target","")))
	var path=game.path_to(unit,action.destination)
	return (not target.is_empty() and target.side=="enemy" and not path.is_empty()
		and game.reachable(unit).costs.has(action.destination) and game.can_stop(unit,action.destination)
		and game.Rules.can_attack(unit,absi(action.destination.x-State.pos(target).x)+absi(action.destination.y-State.pos(target).y)))
func prepare_ui():
	ui.game=fresh();ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.batch_running=false
	ui._clear_menu();ui.observed_attacks.clear();ui.instant_mode=true
func observe():
	while is_instance_valid(ui):
		if ui.view=="plot":ui._accept()
		await process_frame
func run():
	var game=fresh();var initial=game.units.duplicate(true);var actions=[]
	for id in IDS:
		var unit=game.find_unit(id);var action=game.ai_action(unit)
		check(legal_attack(game,unit,action),id+" independently approaches a legal target this turn")
		check(action.destination!=State.pos(unit),id+" moves toward the enemy before attacking")
		actions.append({"id":id,"destination":str(action.destination),"target":action.target})
	check(game.units==initial,"attack selection keeps identity, faction, stats, movement and positions unchanged")
	results.opening_actions=actions
	var clear=fresh()
	for e in clear.living("enemy"):
		if not e.get("objective_boss",false):e.hp=0
	for id in IDS:
		var unit=clear.find_unit(id);var action=clear.ai_action(unit)
		check(str(action.target).is_empty() and action.destination!=State.pos(unit),id+" continues evacuation without an attack in reach")
	var scoped=fresh();var actor=scoped.find_unit(IDS[0]).duplicate(true)
	actor.id="another-escort"
	check(str(scoped.ai_action(actor).target).is_empty(),"other escort IDs keep the existing wait rule")
	actor=scoped.find_unit(IDS[0]).duplicate(true);actor.locked=true
	check(str(scoped.ai_action(actor).target).is_empty(),"locked refugee does not attack")
	check(str(scoped.ai_action(scoped.find_unit(IDS[0]),true).target).is_empty(),"gather mode does not initiate combat")
	scoped.stage_id=111
	check(str(scoped.ai_action(scoped.find_unit(IDS[0])).target).is_empty(),"M11 exception does not apply to other stages")
	var exit_game=fresh();var evacuee=exit_game.find_unit(IDS[0]);evacuee.position=exit_game.battle_data.exit.duplicate()
	var exit_action=exit_game.ai_action(evacuee)
	check(str(exit_action.target).is_empty() and exit_action.destination==State.pos(evacuee),"refugee already at exit stays for evacuation")
	exit_game.mark_wait(IDS[0])
	check(exit_game.flags.quest.evacuated.has(IDS[0]) and evacuee.side=="evacuated","ordinary escort arrival still records evacuation")
	var loss=fresh();loss.find_unit(IDS[0]).hp=0
	check(loss.check_outcome()=="defeat","refugee death still fails M11")
	var win=fresh();win.find_unit(str(win.battle_data.boss_id)).hp=0
	check(win.check_outcome().is_empty(),"boss defeat alone does not bypass escort goal")
	for id in IDS:win.find_unit(id).position=win.battle_data.exit.duplicate();win.mark_wait(id)
	check(win.check_outcome()=="victory","both groups arriving and boss defeated still completes M11")
	ui=load("res://scenes/main.tscn").instantiate();ui.set_script(ObservedMain);root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);observe();prepare_ui()
	await ui._enemy_phase()
	results.complete_turn_attacks=ui.observed_attacks.duplicate(true)
	for id in IDS:
		check(ui.observed_attacks.any(func(a):return a.attacker==id),id+" really attacks through the automatic friendly phase")
	check(not ui.busy and not ui.batch_running and ui.game.turn==2 and ui.game.phase=="player","complete friendly and enemy phases release input for turn two")
	prepare_ui();ui.instant_mode=false;ui.animation_speed=8.0;ui.batch_running=true;ui.busy=true;ui.set_process(true)
	var start_ms=Time.get_ticks_msec();await ui._run_ai_unit(ui.game.find_unit(IDS[0]))
	results.normal_speed_action={"elapsed_ms":Time.get_ticks_msec()-start_ms,"attacks":ui.observed_attacks.duplicate(true),"position":ui.game.find_unit(IDS[0]).position.duplicate()}
	check(ui.observed_attacks.any(func(a):return a.attacker==IDS[0]) and ui.moving_id.is_empty() and ui.game.find_unit(IDS[0]).acted,"real timers complete movement and combat with accepted art")
	ui.set_process(false)
	var checkpoint=OS.get_environment("M11_AI_CHECKPOINT")
	if not checkpoint.is_empty():
		ui.game=State.new();ui.game.save_path=checkpoint
		check(ui.game.load_game(),"existing 0.8.8 M11 checkpoint loads without migration")
		ui.game.save_path="/private/tmp/m11-refugee-ai-independent-save.json"
		if ui.game.phase=="enemy":ui.game.next_phase()
		ui.game.story_events.clear();ui.view="battle";ui.instant_mode=true;ui.busy=true;ui.batch_running=true;ui.observed_attacks.clear()
		var saved_actions=[]
		for id in IDS:
			var unit=ui.game.find_unit(id);var action=ui.game.ai_action(unit)
			check(legal_attack(ui.game,unit,action),id+" can initiate combat from existing turn-three checkpoint")
			saved_actions.append({"id":id,"target":action.target,"destination":str(action.destination)})
		for id in IDS:await ui._run_ai_unit(ui.game.find_unit(id))
		for id in IDS:check(ui.observed_attacks.any(func(a):return a.attacker==id),id+" actually attacks after loading the existing checkpoint")
		results.existing_checkpoint={"actions":saved_actions,"actual_attacks":ui.observed_attacks.duplicate(true)}
	var report={"passed":errors.is_empty(),"checks":checks.size(),"errors":errors,"version":ProjectSettings.get_setting("application/config/version"),"results":results,"scope":"Directed real-stage decisions and actual UI automatic turn; headless, no device-play claim"}
	var output=OS.get_environment("M11_AI_REPORT")
	if output.is_empty():output="res://reports/m11-villager-behavior-20261019/ai-test.json"
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("M11_REFUGEE_AI ",JSON.stringify(report));ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

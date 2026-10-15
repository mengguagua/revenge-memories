extends SceneTree
## Directed regression at the exact final-turn position recorded by real input.
## Only settlement state is reopened to inspect its trigger timing; unit HP,
## stats, movement, positions and acted order remain the real checkpoint values.
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func recorded_position():
	var g=State.new();g.save_path="res://reports/chapter2/play/natural-F22-victory-save.json"
	check(g.load_game(),"recorded turn-38 F22 victory checkpoint loads")
	g.battle_outcome="";g.battle_settled=false;g.mode="battle";g.cleared_stages.erase(202)
	g.flags.east_recruit_ready.lord=false
	return g
func run() -> void:
	var g=recorded_position();var lord=g.find_unit("lord")
	check(g.turn==38 and State.pos(lord)==Vector2i(3,17) and int(lord.hp)==30 and not lord.acted,"actual unacted final slot remains two cells from shared exit")
	check(g.flags.quest.evacuated.size()==3,"three ordinary captives already evacuated")
	check(g.check_outcome().is_empty() and g.flags.quest.get("pending_friendly_actions",false),"goal waits for remaining ordinary friendly action")
	var ai=g.ai_action(lord);var path=g.path_to(lord,ai.destination)
	check(ai.destination==Vector2i(3,19) and path.size()==3,"normal escort AI chooses its real two-cell exit path")
	check(g.select_unit("lord")==false,"Lord remains an uncontrollable rescued person")
	# Same position update performed by UI _animate_move, following every legal
	# path step; this is a targeted engine fixture, not the user's replay.
	for at in path:
		check(g.in_bounds(at) and g.movement_cost(lord,at)<255,"remaining escort step is legal")
		lord.position=[at.x,at.y]
	g.mark_wait("lord")
	check(g.flags.quest.evacuated.has("lord") and g.battle_outcome=="victory","remaining slot evacuates before objective settles")
	check(g.complete_battle() and g.flags.east_recruit_ready.lord,"normal settlement records actual Lord evacuation")
	var not_arrived=recorded_position();var other=not_arrived.find_unit("lord")
	check(not_arrived.check_outcome().is_empty(),"incomplete remaining action initially defers")
	not_arrived.mark_wait("lord")
	check(not_arrived.battle_outcome=="victory" and not not_arrived.flags.quest.evacuated.has("lord"),"waiting without arrival still wins once the ordinary action completes")
	check(not_arrived.complete_battle() and not not_arrived.flags.east_recruit_ready.lord,"no forced relocation or fabricated recruitment")
	var dead=recorded_position();dead.find_unit("lord").hp=0
	check(dead.check_outcome()=="victory","optional Lord casualty never becomes an extra victory requirement")
	var report={"scope":"Directed real-checkpoint final-slot settlement timing, no natural replay claim","passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"source":"natural-F22-victory-save.json turn38 Lord[3,17] unacted"}
	var f=FileAccess.open("res://reports/chapter2/rescue-order-check.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("RESCUE_ORDER ",JSON.stringify(report));quit(0 if failures.is_empty() else 1)

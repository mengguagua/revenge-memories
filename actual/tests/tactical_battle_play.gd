extends "res://tests/assessment_ch5.gd"
## Two independent reviews from immutable genuine campaign checkpoints.
## New mechanics are exercised using the ordinary visible controller actions.
const Battlefield=preload("res://core/battlefield_tactics.gd")
class WatchedState extends "res://core/game_state.gd":
	var special_observations:Array=[]
	func apply_ai_special(caster:Dictionary,action:Dictionary)->Dictionary:
		var result=super.apply_ai_special(caster,action)
		if action.get("special","")=="battlefield_release":special_observations.append({"turn":turn,"actor":caster.id,"result":result.duplicate(true)})
		return result
var review_round=1
var review_code="M42"
var source_hash=""

func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--round="):review_round=int(arg.trim_prefix("--round="))
		if arg.begins_with("--code="):review_code=arg.trim_prefix("--code=")
	late_label="round"+str(review_round)
	late_folder="res://reports/tactical-expansion-20261025/play/"+review_code+"-"+late_label+"/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
	source_checkpoint="res://reports/full-assessment-20261025/campaign-final-r4/ch4/chain-M42-entry.json" if review_code=="M42" else "res://reports/full-assessment-20261025/campaign-final-r5/ch5/chain-J54-entry.json"
	source_hash=FileAccess.get_file_as_string(source_checkpoint).sha256_text()
	var working=late_folder+"working.json"
	DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
	ui=load("res://scenes/main.tscn").instantiate();ui.game=WatchedState.new();ui.game.slot_directory=late_folder;ui.game.save_path=working
	root.add_child(ui);await process_frame;ui.instant_mode=true
	if not ui.game.load_game():record_failure("Historical checkpoint cannot load")
	if not abort:
		ui._resume_journey();await settle()
		var node=ui.game.world_node
		key(KEY_S);choose("new:prepare");await settle()
		await go(node)
		if not abort:key(KEY_Z);choose("new:battle");await settle()
		if not abort and str(ui.game.battle_data.code)!=review_code:record_failure("Unexpected reentry battle")
		await snapshot("entry")
	if not abort:await battle(false)
	if not abort and review_code=="J54":await finish_ending()
	# Let signal-based page/result continuations return before freeing their UI.
	# The input driver can observe the final view one frame before its coroutine ends.
	for _frame in range(8):await process_frame
	if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=source_hash:record_failure("Immutable source changed")
	write_progress()
	ui.queue_free();await process_frame;ui=null
	quit(1 if abort else 0)

func snapshot(name:String)->void:
	if abort:return
	var old=ui.game.save_path;var path=late_folder+name+".json";ui.game.save_path=path
	if not ui.game.save_game():record_failure("Tactical review snapshot rejected: "+name)
	ui.game.save_path=old
	checkpoints.append({"name":name,"path":path,"turn":ui.game.turn,"view":ui.view})
	write_progress()

func write_progress()->void:
	if ui==null or late_folder.is_empty():return
	var record={"passed":not abort and not battles.is_empty() and battles[-1].outcome=="victory","round":review_round,"code":review_code,
		"failures":failures,"inputs":inputs,"source":source_checkpoint,"source_sha256":source_hash,"battles":battles,"operations":operations,
		"special_actions":ui.game.special_observations,"checkpoints":checkpoints,"content":audit_content,"quest":ui.game.flags.quest.duplicate(true),
		"scope":"Headless actual scene/controller keyboard input from an immutable genuine historical checkpoint, ordinary preparation return and new deployment; no HP/attributes/RNG/position/outcome injections. Not human or iPhone play.","stat_edits":false,"source_saves_modified":false}
	var f=FileAccess.open(late_folder+"report.json",FileAccess.WRITE);f.store_string(JSON.stringify(record,"  "));f.close()

func risk(unit:Dictionary,cell:Vector2i,skip:String="")->float:
	var value=super.risk(unit,cell,skip)
	for mark in Battlefield.warning_cells(ui.game):
		if Battlefield._point(mark.position)!=cell or str(mark.actor)==skip:continue
		var intent=ui.game.flags.quest.battlefield.intents[str(mark.actor)]
		value+=maxi(1,int(intent.power)-Items.magic_defence(unit) if intent.kind=="magic" else int(intent.power)-int(unit.defence))
	return value

func plan(unit:Dictionary)->Dictionary:
	if review_round==2 and ui.game.stage_id==402 and Battlefield.can_break(unit):
		for cell in ui.game.reachable(unit).costs:
			if not ui.game.can_stop(unit,cell):continue
			var candidate=unit.duplicate(true);candidate.position=[cell.x,cell.y]
			var options=Battlefield.interactions_for(ui.game,candidate)
			if not options.is_empty() and risk(candidate,cell)<float(unit.hp)*.5:
				return {"kind":"interact","cell":cell,"score":300.0,"target":str(options[0].id),"spell":-1}
	return super.plan(unit)

func settle()->void:
	await super.settle()
	if not abort and ui.menu_context=="breakable_confirm":
		operations.append({"kind":"read destruction confirmation","items":ui.menu_items.duplicate(),"notice":ui.notice,"turn":ui.game.turn})
		choose(str(ui.menu_actions[0]));await super.settle()

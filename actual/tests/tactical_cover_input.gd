extends "res://tests/tactical_rescue_play.gd"
## Short genuine-checkpoint input sample: expose a legal covered formation.
## This deliberately verifies one enemy phase, not a complete stage victory.
func run()->void:
	late_folder="res://reports/tactical-expansion-20261025/cover-input/"
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(late_folder))
	source_checkpoint="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F22-deployment.json"
	var digest=FileAccess.get_file_as_string(source_checkpoint).sha256_text()
	var working=late_folder+"working.json"
	DirAccess.copy_absolute(ProjectSettings.globalize_path(source_checkpoint),ProjectSettings.globalize_path(working))
	ui=load("res://scenes/main.tscn").instantiate();ui.game=ObservedState.new();ui.game.slot_directory=late_folder;ui.game.save_path=working
	root.add_child(ui);await process_frame;ui.instant_mode=true
	if not ui.game.load_game():record_failure("Cover input source failed")
	if not abort:ui._resume_journey();await settle()
	if not abort:await wait_at("mireille",Vector2i(8,15));await wait_at("lisa",Vector2i(9,14))
	if not abort:await extra_action(ui.game.find_unit("eileen"),Vector2i(8,14),"cover:choose","cover:target:lisa","cover:commit:lisa")
	if not abort:await extra_action(ui.game.find_unit("carlo"),Vector2i(7,15),"cover:choose","cover:target:mireille","cover:commit:mireille")
	if not abort and ui.game.turn==1:key(KEY_S);choose("end_turn");await settle()
	var hits=ui.game.tactical_events.filter(func(e):return e.kind=="cover_hit")
	if hits.is_empty():record_failure("Natural enemy phase did not exercise a covered hit")
	if FileAccess.get_file_as_string(source_checkpoint).sha256_text()!=digest:record_failure("Cover source modified")
	var after=[]
	for u in ui.game.units:
		if str(u.id) in ["eileen","carlo","lisa","mireille"]:after.append({"id":u.id,"hp":u.hp,"position":u.position,"cover_target":u.get("cover_target","")})
	var f=FileAccess.open(late_folder+"report.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":not abort,"errors":failures,"inputs":inputs,"source":source_checkpoint,"source_sha256":digest,"turn":ui.game.turn,"events":ui.game.tactical_events,"cover_hits":hits,"extra_actions":extras,"after":after,"scope":"Short actual-input sample from an untouched historical F22 deployment. Ordinary move/wait/cover confirmation and an enemy phase. No HP/stats/RNG/position injection; not a whole-stage playthrough."},"  "));f.close()
	print("COVER_INPUT hits=",hits.size()," errors=",failures)
	ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)

func wait_at(id:String,at:Vector2i)->void:
	cursor_to(State.pos(ui.game.find_unit(id)));key(KEY_Z);cursor_to(at);key(KEY_Z);await settle()
	if not abort:choose("wait");await settle()

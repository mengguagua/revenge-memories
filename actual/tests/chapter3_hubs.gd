extends "res://tests/chapter3_play.gd"
## Round-two actual key/menu checks from the naturally reached meeting camp.
var checks=[]
func ensure(ok,label):
	checks.append(label)
	if not ok:record_failure(label)
func run():
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame;ui.instant_mode=true
	var source="res://reports/chapter3/play/round1final-chapter-end.json"
	var copy_path="res://reports/chapter3/round2-hub-working.json";DirAccess.copy_absolute(ProjectSettings.globalize_path(source),ProjectSettings.globalize_path(copy_path))
	ui.game.save_path=copy_path;key(KEY_Z)
	if ui.title_selected!=1:key(KEY_DOWN)
	key(KEY_Z);await settle()
	ensure(ui.view=="chapter_end","natural chapter-end continues from title")
	key(KEY_Z);choose("new:world");await settle();enter_hub();await settle()
	var count=ui.game.treatment_remaining();await hub_action("third_council")
	ensure(ui.game.treatment_remaining()==count,"revisiting D33 does not refresh medicine")
	await hub_action("third_training");choose("hub:third_exchange");await settle()
	var before=ui.game.convoy.duplicate(true);var other="alm" if ui.game.route=="celica" else "celica";var route=ui.game.route
	choose("hub:third_transfer_0");await settle()
	ensure(ui.game.convoy[other].size()==before[other].size()-1 and ui.game.convoy[route].size()==before[route].size()+1,"menu handoff moves exactly one actual item")
	await hub_action("third_training");choose("hub:third_promotions");await settle()
	if not ui.menu_items.is_empty():key(KEY_X)
	ensure(ui.view=="hub","training cancel returns to camp")
	await switch_team();enter_hub();await settle()
	await hub_action("treatment");choose("hub:treat_choose_fula");key(KEY_X)
	ensure(ui.game.treatment_remaining()==count and ui.game.roster.fula.dying,"cancel does not consume treatment or change injury")
	await hub_action("treatment");choose("hub:treat_choose_fula");choose("hub:treat_confirm_fula");await settle()
	ensure(not ui.game.roster.fula.dying and ui.game.treatment_remaining()==count-1,"actual western treatment consumes same shared supply")
	key(KEY_S);choose("new:save");await settle();key(KEY_S);choose("title");await settle()
	key(KEY_Z)
	if ui.title_selected!=1:key(KEY_DOWN)
	key(KEY_Z);await settle()
	ensure(ui.view=="hub" and ui.game.hub_record=="H10" and ui.game.route=="alm","title reload restores active camp route")
	ensure(ui.game.roster.has("fula") and not ui.game.roster.fula.dying and ui.game.treatment_remaining()==count-1,"treatment persists across title reload")
	var working=ui.game.save_path;ui.game.save_path="res://reports/chapter3/round2-treatment.json";ui.game.save_game();ui.game.save_path=working
	# Visual rooms use real walk input, while room selection is an explicit geometry fixture.
	var visits=0
	for room in ui.game.ChapterThree.ROOMS:
		ui.hub_controller.enter_room(room);await settle()
		for object in ui.hub_controller.objects:
			var point=Vector2i(object.position[0],object.position[1]);var found=false
			for d in ui.game.DIRECTIONS:
				var path=_hub_route(point+d)
				if not path.is_empty():walk_to(point+d);found=true;visits+=1;break
			ensure(found,room+" walkable approach "+str(object.action))
		walk_to(Vector2i(6,7));ensure(ui.game.hub_position==Vector2i(6,7),room+" exit connected")
	var f=FileAccess.open("res://reports/chapter3/round2-hub-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":not abort,"checks":checks,"inputs":inputs,"visited_objects":visits,"failures":failures,"source":source,"geometry_room_selection_fixture":true},"  "));f.close()
	print("CH3_HUB_RESULT ",checks.size()," checks ",inputs," inputs ",failures)
	ui.queue_free();await process_frame;ui=null;quit(0 if not abort else 1)

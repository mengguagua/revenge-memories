extends "res://tests/round3.gd"
var checks := 0
func ensure(value: bool,label: String) -> void:
	checks+=1
	if not value:record_failure(label)
func walk_to(at: Vector2i) -> void:
	var start=ui.game.hub_position;var q: Array[Vector2i]=[start];var seen={start:start}
	while not q.is_empty() and not seen.has(at):
		var p=q.pop_front()
		for d in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
			var n=p+d
			if n.x<1 or n.x>12 or n.y<1 or n.y>7 or seen.has(n) or not ui.hub_controller.east_walkable(n):continue
			seen[n]=p;q.append(n)
	if not seen.has(at):record_failure("Hub destination blocked: "+str(at));return
	var path: Array=[];var p=at
	while p!=start:path.push_front(p);p=seen[p]
	for n in path:
		var d=n-ui.game.hub_position;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP)
		if ui.game.hub_position!=n:record_failure("Hub input disagrees with visual floor: "+str(n));return
func visit(action: String) -> void:
	var target={}
	for o in ui.hub_controller.objects:
		if o.action==action:target=o;break
	if target.is_empty():record_failure("Object unavailable "+action);return
	var at=Vector2i(target.position[0],target.position[1]);var found=false
	for direction in [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]:
		if ui.hub_controller.east_walkable(at+direction):
			walk_to(at+direction)
			var d=-direction;key(KEY_RIGHT if d.x>0 else KEY_LEFT if d.x<0 else KEY_DOWN if d.y>0 else KEY_UP);found=true;break
	ensure(found,"Interactable has adjacent floor "+action)
	if not abort:key(KEY_Z);await settle()
func run() -> void:
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.game.save_path="/private/tmp/revenge-ch2-hub-test-save.json";ui.game.new_game();ui.instant_mode=true
	ui.game.cleared_stages.append(105);ui.game.flags.chapter1_complete=true
	ensure(ui.game.begin_chapter_two(),"chapter two migration")
	ui.hub_controller.enter_room("H21")
	await visit("east_departure");ensure(ui.game.flags.get("east_departure_ready",false),"D21 departure confirmation")
	var original_party=ui.game.party.duplicate();await visit("east_departure");ensure(ui.game.party==original_party,"D21 repeat no duplicate recruit")
	ui.game.flags.east_recruit_ready={"lord":true,"roan":true,"shia":true}
	ui.game.cleared_stages.append_array([201,202,203,204,205,211,212])
	ui.game.flags.F22_confirmed=true;ui.game.flags.islanders_settled=true
	for id in ["lord","roan","shia"]:ui.game.recruit(id)
	var objects_count=0
	for room in ["H21","H22","H23","H24","H25","H26","H27"]:
		ui.hub_controller.enter_room(room)
		for o in ui.hub_controller.objects:
			var at=Vector2i(o.position[0],o.position[1]);var found=false
			for d in [Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT,Vector2i.UP]:
				if ui.hub_controller.east_walkable(at+d):walk_to(at+d);found=true;break
			ensure(found,"All actual room objects approachable "+room+":"+o.action);objects_count+=1
			if abort:break
		walk_to(Vector2i(6,7));ensure(ui.game.hub_position==Vector2i(6,7),"Exit connected "+room)
		if abort:break
	ui.hub_controller.enter_room("H25");var resistance=int(ui.game.roster.eileen.resistance)
	await visit("resistance_spring");choose("hub:east_spring_eileen");await settle()
	ensure(int(ui.game.roster.eileen.resistance)==resistance+1,"Resistance +1")
	await visit("resistance_spring");ensure(int(ui.game.roster.eileen.resistance)==resistance+1,"Spring cannot repeat")
	ensure(ui.game.save_game(),"Save spring");ensure(ui.game.load_game(),"Load spring");ensure(ui.game.flags.get("lighthouse_spring_used",false),"Spring persisted")
	ui.hub_controller.enter_room("H24");await visit("holy_sword")
	ensure(ui.game.flags.get("F23_holy_sword_taken",false),"Holy sword claimed")
	var before=ui.game.convoy.duplicate(true);var roster=ui.game.roster.duplicate(true);await visit("holy_sword")
	ensure(before==ui.game.convoy and roster==ui.game.roster,"Holy sword not duplicated")
	ui.hub_controller.enter_room("H26");await visit("chart_recover");ensure(ui.game.flags.get("sea_chart_collected",false),"Chart callback persisted")
	await visit("harbor_patients");await visit("ancient_departure");ensure(ui.menu_actions.has("hub:east_sail_confirm"),"Explicit departure choice")
	choose("hub:east_sail_confirm");await settle();ensure(ui.game.flags.get("east_departure_confirmed",false),"Departure closes side trips")
	ui.hub_controller.enter_room("H27");ui.game.cleared_stages.append(206)
	await visit("east_finale");ensure(ui.game.flags.get("chapter2_complete",false),"Second chapter complete");ensure(ui.game.chapter==2 and ui.view=="chapter_end","Stops before Chapter 3")
	var report={"passed":not abort,"checks":checks,"objects":objects_count,"real_key_inputs":inputs,"failures":failures,"scope":"Directed progression fixtures, real keyboard hub walking/interaction; no combat win claim."}
	var file=FileAccess.open("res://reports/chapter2/hub-checks.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close();print(JSON.stringify(report))
	ui.queue_free();await process_frame;quit(0 if not abort else 1)

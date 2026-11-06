extends SceneTree
## Guarded offscreen UI fixtures; no player journals or visible windows.
const OUT="res://reports/story-accessories-20261023/"
const CACHE="/private/tmp/revenge-story-accessories-20261023/"
var viewport
var ui
var shots=[]
var errors=[]
var reachability=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name:String,expected:String):
	ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var issues=ui.layout_errors.duplicate();var text=ui.text_checks.duplicate(true)
	if not text.any(func(line):return str(line.text).contains(expected)):issues.append("expected label absent: "+expected)
	var path=OUT+name+".png";viewport.get_texture().get_image().save_png(path)
	shots.append({"name":name,"path":path,"native_width":viewport.size_2d_override.x,"view":ui.view,"text":text,"errors":issues})
	for issue in issues:errors.append(name+": "+str(issue))
	print("STORY_ACCESSORY_SHOT ",name," ",issues)
func page(value:Dictionary,name:String):
	ui._clear_menu();ui.view="plot";ui.plot_return="hub";ui.game.mode="hub"
	ui.plot_pages=ui._paginate_plot(value)
	for i in range(ui.plot_pages.size()):
		ui.plot_index=i;ui.dialogue_reveal=str(ui.plot_pages[i].text).length()
		await shot(name+"-"+str(i),str(ui.plot_pages[i].text).split("\n")[0])
func load_fixture(stage:int):
	ui.game.save_path=CACHE+"success-"+str(stage)+".json"
	if not ui.game.load_game():errors.append("source fixture failed: "+str(stage));return false
	ui.game.save_path=CACHE+"capture-working.json";ui.game.story_events.clear();ui.notice_time=0;ui._clear_menu()
	return true
func check_room(action:String):
	var h=ui.hub_controller
	var object=h.objects.filter(func(o):return str(o.action)==action)[0]
	var target=Vector2i(int(object.position[0]),int(object.position[1]))
	var pending=[Vector2i(6,7)];var seen={Vector2i(6,7):true};var access=Vector2i(-1,-1)
	while not pending.is_empty():
		var p:Vector2i=pending.pop_front()
		if absi(p.x-target.x)+absi(p.y-target.y)==1:access=p;break
		for d in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:
			var at=p+d
			if at.x<1 or at.x>12 or at.y<1 or at.y>7 or seen.has(at) or not h.east_walkable(at):continue
			seen[at]=true;pending.append(at)
	var safe=not h.scenery.any(func(d):return bool(d.get("blocking",true)) and d.rect.has_point(target))
	var valid=access!=Vector2i(-1,-1) and safe
	reachability.append({"room":h.room,"npc":object.name,"target":[target.x,target.y],"approach":[access.x,access.y],"reachable":valid})
	if not valid:errors.append("unreachable/overlapping NPC in "+h.room)
	ui.game.hub_position=access;h.facing=target-access;h.render_position=Vector2(access)*16
func gear(id:int):
	ui.game.route="alm";ui.game.party=ui.game.parties.alm.duplicate();ui.game.mode="world";ui.view="world"
	ui.game.convoy.alm=[id];ui._clear_menu();ui.equipment_screen.open(0)
	ui.equipment_screen.selected=ui.equipment_screen.members.find("hunapu");ui.equipment_screen.accept()
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=CACHE+"unused-slots"
	viewport.add_child(ui);await process_frame;ui.set_process(false);ui.set_physics_process(false)
	ui.instant_mode=true;ui.busy=false;ui.batch_running=false;ui.notice_time=0;ui.phase_time=0
	for width in [426,256]:
		viewport.size=Vector2i(width*3,720);viewport.size_2d_override=Vector2i(width,240)
		for stage in [411,501]:
			if not load_fixture(stage):continue
			var id=55 if stage==411 else 53;var spec:Dictionary=ui.Items.accessories().items[str(id)]
			ui.hub_controller.enter_room(str(spec.room),false,false)
			check_room("fourth_ring_keeper" if id==55 else "fifth_shield_keeper")
			await shot(str(width)+"-npc-"+str(id),"确认:"+str(spec.speaker))
			for i in range(ui.game.Accessories.delivery_pages(id).size()):
				await page(ui.game.Accessories.delivery_pages(id)[i],str(width)+"-handover-"+str(id)+"-"+str(i))
			gear(id);await shot(str(width)+"-equipment-"+str(id),str(spec.name_zh))
			if width==256:
				ui.equipment_screen.toggle_details()
				for i in range(ui.equipment_screen.details_page_count()):
					ui.equipment_screen.details_page=i;await shot(str(width)+"-details-"+str(id)+"-"+str(i),str(spec.name_zh))
			ui.game.flags.story_accessories_claimed.erase(str(id))
			await page({"speaker":"信使","text":ui.game.Accessories.closing_reminder(ui.game,id)},str(width)+"-unclaimed-"+str(id))
	var f=FileAccess.open(OUT+"captures.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"reachability":reachability,"errors":errors,"controlled_fixtures":true,"background_guard":true,"visible_windows":false,"user_saves_touched":false},"  "));f.close()
	ui.queue_free();viewport.queue_free();await process_frame
	print("STORY_ACCESSORIES_VISUAL ",shots.size()," screenshots; errors: ",errors)
	quit(0 if errors.is_empty() else 1)

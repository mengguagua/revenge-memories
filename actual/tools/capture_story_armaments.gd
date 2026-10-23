extends SceneTree
## Existing UI, guarded offscreen fixtures. Never writes player journals.
const OUT="res://reports/story-armaments-20261023/"
class Recorder extends RefCounted:
	var game
	var pages=[]
	var menu=[]
	func play_pages(value,_back,_callback):pages.append_array(value)
	func _open_menu(_kind,labels,_actions,_at):menu=labels
	func _notice(_text,_seconds=0):pass
class Room extends RefCounted:
	var ui
var viewport
var ui
var shots=[]
var errors=[]
var animation_check={}
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name: String, expected: String):
	ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var issues=ui.layout_errors.duplicate();var text=ui.text_checks.duplicate(true)
	if not text.any(func(line):return str(line.text).contains(expected)):issues.append("expected label absent: "+expected)
	var path=OUT+name+".png";viewport.get_texture().get_image().save_png(path)
	shots.append({"name":name,"path":path,"native_width":viewport.size_2d_override.x,"view":ui.view,"text":text,"errors":issues})
	for issue in issues:errors.append(name+": "+str(issue))
	print("STORY_ARMAMENT_SHOT ",name," ",issues)
func show_page(page: Dictionary, name: String):
	ui._clear_menu();ui.view="plot";ui.plot_return="world";ui.game.mode="world"
	ui.plot_pages=ui._paginate_plot(page)
	for i in range(ui.plot_pages.size()):
		ui.plot_index=i;ui.dialogue_reveal=str(ui.plot_pages[i].text).length()
		await shot(name+"-"+str(i),str(ui.plot_pages[i].text).split("\n")[0])
func route(side: String):
	ui.game.route=side;ui.game.party=ui.game.parties[side].duplicate();ui.game.mode="world";ui.view="world"
	ui.game.world_node=9;ui._clear_menu();ui.notice_time=0
func gear(id: int, wrong: bool=false):
	var spec: Dictionary=ui.Items.armaments().items[str(id)]
	var side=str(spec.route)
	var member="eileen" if id in [15,17] else "hunapu" if id==18 else ""
	if member.is_empty():
		for key in ui.game.parties[side]:
			if ui.game.can_deploy(ui.game.roster[key]) and ui.Items.can_use(ui.game.roster[key],id):member=str(key);break
	if wrong:member="hunapu" if id==17 else "eileen";side="alm" if id==17 else "celica"
	route(side);ui.game.convoy[side]=[id];ui.equipment_screen.open(0)
	var selected=ui.equipment_screen.members.find(member)
	if selected<0:errors.append("no compatible member for "+str(id));return
	ui.equipment_screen.selected=selected;ui.equipment_screen.accept()
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/revenge-story-armaments-20261023/unused-slots"
	viewport.add_child(ui);await process_frame;ui.set_process(false);ui.set_physics_process(false)
	ui.game.save_path="res://reports/chapter4/play/round2-chapter-end.json"
	if not ui.game.load_game():errors.append("source checkpoint failed");quit(1);return
	ui.game.save_path="/private/tmp/revenge-story-armaments-20261023/capture-working.json"
	ui.instant_mode=true;ui.busy=false;ui.batch_running=false;ui.notice_time=0;ui.phase_time=0;ui.game.story_events.clear()
	var h=Room.new();h.ui=Recorder.new();h.ui.game=ui.game
	var cleared=ui.game.cleared_stages.duplicate();ui.game.cleared_stages.erase(412)
	await ui.hub_controller.FourthHub.action(h,"third_messenger")
	var fourth_warning=h.ui.pages.filter(func(page):return str(page.text).contains("定潮枪尚未取得"))
	ui.game.cleared_stages=cleared
	if fourth_warning.is_empty():errors.append("fourth-chapter warning absent")
	var warning_game=ui.GameState.new();warning_game.save_path="res://reports/chapter4/play/round2-chapter-end.json";warning_game.load_game();warning_game.begin_chapter_five()
	warning_game.save_path="/private/tmp/revenge-story-armaments-20261023/warning-working.json"
	warning_game.route_positions={"alm":15,"celica":15};warning_game.flags.chapter5_ready={"alm":true,"celica":true}
	h.ui.game=warning_game;h.ui.pages.clear();await ui.hub_controller.FifthHub.action(h,"fifth_merge")
	var fifth_warning=h.ui.pages.filter(func(page):return str(page.text).contains("镇关枪尚未取得"))
	if fifth_warning.is_empty():errors.append("fifth-chapter warning absent")
	for width in [426,256]:
		viewport.size=Vector2i(width*3,720);viewport.size_2d_override=Vector2i(width,240)
		for id in [15,18,10,17,9,7]:
			gear(id);await shot(str(width)+"-equipment-"+str(id),str(ui.Items.item(id).name_zh))
			if width==256 and id in [17,7]:
				ui.equipment_screen.toggle_details()
				for page in range(ui.equipment_screen.details_page_count()):
					ui.equipment_screen.details_page=page
					await shot(str(width)+"-details-"+str(id)+"-"+str(page),str(ui.Items.item(id).name_zh))
			route(str(ui.Items.armaments().items[str(id)].route))
			var pages=ui.game.Armaments.delivery_pages(id)
			await show_page(pages[-1],str(width)+"-receipt-"+str(id))
			if width==256 and id in [18,7]:await show_page(pages[0],str(width)+"-handover-"+str(id))
		for id in [17,18]:
			gear(id,true);await shot(str(width)+"-wrong-owner-"+str(id),"仅"+("艾琳" if id==17 else "胡纳普")+"可使用")
		if width==256:
			for page in fourth_warning:await show_page(page,"256-close-S42")
			for page in fifth_warning:await show_page(page,"256-close-S51")
	# Eileen's newly allowed sword uses her existing class/personal animation.
	var old_units=ui.game.units.duplicate(true)
	var actor=ui.game.roster.eileen.duplicate(true);actor.item_id=17;actor.position=[5,5]
	var enemy=ui.game.stages[408].enemies[0].duplicate(true);enemy.id="armament_animation_target";enemy.position=[6,5]
	ui.game.units=[actor,enemy];ui.combat={"attacker":"eileen","defender":enemy.id,"distance":1,"initiative_side":"player"}
	var selected=ui.battle_animation.selection({"attacker":"eileen","defender":enemy.id,"weapon_index":17,"distance":1,"hit":true,"critical":false})
	animation_check={"kind":selected.get("kind","missing"),"key":selected.get("key",""),"class_id":actor.class_id,"character_id":actor.character_id}
	if selected.get("kind","missing")=="missing":errors.append("Eileen light-sword animation unavailable")
	ui.game.units=old_units
	var f=FileAccess.open(OUT+"captures.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"animation":animation_check,"fixture":true,"background_guard":true,"visible_windows":false,"user_saves_touched":false},"  "));f.close()
	ui.queue_free();viewport.queue_free();await process_frame
	print("STORY_ARMAMENTS_VISUAL ",shots.size()," screenshots; errors: ",errors)
	quit(0 if errors.is_empty() else 1)

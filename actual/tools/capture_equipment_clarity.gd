extends SceneTree
const OUT="res://reports/equipment-clarity-20261021/"
const CACHE="/private/tmp/revenge-equipment-clarity-20261021/"
var ui
var viewport
var shots=[]
var checks=[]
var errors=[]
var baseline=false

func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func shot(name:String):
	ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var audit=ui.equipment_screen.audit.duplicate(true) if ui.equipment_screen.active() else ui.journey.audit.duplicate(true) if ui.view.begins_with("journal") else ui.text_checks.duplicate(true)
	var layout=ui.layout_errors.duplicate()
	if not baseline and ui.equipment_screen.active():
		for entry in audit:
			if entry.font<12:layout.append("Equipment Chinese still uses a tiny font: "+str(entry.text))
			for ch in str(entry.text):
				if ch!="\n" and ch.unicode_at(0)>127 and ui._zh_glyph(ch).is_empty():layout.append("Missing native glyph: "+ch)
	viewport.get_texture().get_image().save_png(OUT+name+".png")
	shots.append({"name":name,"before":baseline,"size":[viewport.size.x,viewport.size.y],"view":ui.view,"text":audit,"errors":layout})
	for error in layout:errors.append(name+": "+str(error))
func open_for(item:int,id:String,details:bool=false):
	ui.view="world";ui._clear_menu();ui.game.convoy.alm=[item];ui._camp_action("withdraw_item:0")
	ui.equipment_screen.selected=ui.equipment_screen.members.find(id);ui.equipment_screen.accept()
	ui.equipment_screen.more=details
func members():
	ui.view="world";ui._clear_menu();ui.game.convoy.alm=[60];ui._camp_action("withdraw_item:0")

func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	DirAccess.make_dir_recursive_absolute(CACHE+"visual-slots")
	viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory=CACHE+"visual-slots";viewport.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=3;ui.busy=false;ui.game.new_game();ui.game.mode="world";ui.game.world_node=32;ui.game.save_path=CACHE+"visual-unused.json"
	for id in ["fula","lena","lance","beck","hervi"]:ui.game.recruit(id)
	ui.game.roster.hervi.class_id=19
	ui.world_actor=Vector2(ui.world.nodes["32"].position[0],ui.world.nodes["32"].position[1])*16
	# Optional source copy renders the exact old 8px UI for comparison.
	var old=CACHE+"before_equipment_screen.gd"
	if FileAccess.file_exists(old):
		baseline=true;ui.equipment_screen=load(old).new(ui)
		members();await shot("before-members-wide")
		ui.game.roster.daan.item_id=64;open_for(20,"daan");await shot("before-comparison-wide")
		ui.game.roster.hunapu.item_id=62;open_for(60,"hunapu",true);await shot("before-details-wide")
		baseline=false
	ui.equipment_screen=load("res://core/equipment_screen.gd").new(ui)
	ui.game.roster.hunapu.item_id=59;ui.game.roster.daan.item_id=64
	members();ui.equipment_screen.selected=4
	viewport.size=Vector2i(768,720);viewport.size_2d_override=Vector2i(256,240)
	await shot("after-resized-members-compact")
	check(ui.equipment_screen.first<=4 and ui.equipment_screen.first+ui.equipment_screen.page_size()>4,"resizing retains visible keyboard selection")
	for width in [426,256]:
		viewport.size=Vector2i(width*3,720);viewport.size_2d_override=Vector2i(width,240)
		var size="wide" if width==426 else "compact"
		members();await shot("after-members-"+size)
		var screen=ui.equipment_screen
		while screen.selected<screen.members.size()-1:screen.direction(Vector2i.DOWN)
		check(screen.first+screen.page_size()>screen.selected,"last member is visible "+size)
		await shot("after-last-members-"+size)
		open_for(20,"daan");await shot("after-comparison-"+size)
		open_for(62,"hunapu");await shot("after-incompatible-"+size)
		ui.game.roster.hunapu.item_id=62;open_for(60,"hunapu",true)
		var stock=ui.game.convoy.duplicate(true);var roster=ui.game.roster.duplicate(true)
		var pages=screen.details_page_count();check(pages>1,"large descriptions paginate "+size)
		for page in range(pages):
			check(screen.details_page==page,"detail page keyboard position "+size+str(page))
			await shot("after-details-"+size+"-"+str(page+1))
			if page+1<pages:screen.direction(Vector2i.DOWN)
		check(ui.game.convoy==stock and ui.game.roster==roster,"reading all details is read-only "+size)
		screen.mouse(screen.details_page_rect(-1).get_center())
		check(screen.details_page==maxi(0,pages-2),"mouse detail previous page "+size)
		screen.toggle_details();check(not screen.more and screen.details_page==0,"Tab-style toggle restores comparison "+size)
		ui.game.roster.hunapu.item_id=59
	# Error feedback is also readable at the narrowest size.
	open_for(60,"hunapu");ui.equipment_screen.message="保存失败，原装备与行囊已保留";await shot("after-equipment-save-error")
	viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240)
	ui.view="world";ui.game.mode="world";ui._clear_menu();ui.game.save_to_slot(1)
	ui._open_camp_menu();await shot("after-preparation-menu")
	check(not ui.menu_actions.has("title"),"preparation menu contains no return-to-title action")
	ui._menu_action("camp:save","camp");ui.elapsed=ui.journey.opened_at+1.0;await shot("after-preparation-save-picker")
	check(ui.view=="journal" and ui.journey.intent=="save","preparation save presents five records")
	ui.journey.accept();await shot("after-save-overwrite-confirm")
	var f=FileAccess.open(OUT+"visual.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"shots":shots,"background_guard":true,"visible_windows":false,"fixture":true,"user_saves_touched":false},"  "));f.close()
	print("EQUIPMENT_CLARITY ",shots.size()," screenshots; ",checks.size()," checks; errors: ",errors)
	ui.queue_free();viewport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

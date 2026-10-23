extends SceneTree
## Guarded offscreen fixtures: no visible window and no player-journal writes.
const OUT="res://reports/hero-professions-20261023/"
class Recorder extends RefCounted:
	var game
	var pages=[]
	func play_pages(value,_back,_callback):pages.append_array(value)
class Room extends RefCounted:
	var ui
var viewport
var ui
var shots=[]
var errors=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func shot(name: String, expected: String):
	ui.queue_redraw()
	for i in range(3):await process_frame
	await RenderingServer.frame_post_draw
	var issues=ui.layout_errors.duplicate()
	var text=ui.text_checks.duplicate(true)
	if ui.view=="camp_status":
		# World labels are drawn earlier and completely covered by this panel.
		for i in range(text.size()):
			if str(text[i].text).begins_with("队伍 "):text=text.slice(i);break
	if not text.any(func(line):return str(line.text).contains(expected)):issues.append("expected label absent: "+expected)
	# Text bounds already include real glyph metrics; check foreground lines
	# against each other as well as the panel's measured content-safe area.
	if ui.view=="camp_status":
		for i in range(text.size()):
			for bar in ui.health_checks:
				if text[i].bounds.intersects(bar.bounds):issues.append("status text overlaps HP cells: "+str(text[i].text))
			for j in range(i):
				if text[i].bounds.intersects(text[j].bounds):issues.append("status text overlap: "+str(text[i].text)+" / "+str(text[j].text))
	var path=OUT+name+".png"
	viewport.get_texture().get_image().save_png(path)
	shots.append({"name":name,"path":path,"native_width":viewport.size_2d_override.x,"view":ui.view,"text":text,"errors":issues})
	for issue in issues:errors.append(name+": "+str(issue))
	print("HERO_PROFESSION_SHOT ",name," ",issues)
func route(name: String):
	ui.game.route=name;ui.game.party=ui.game.parties[name].duplicate();ui.game.mode="world";ui.view="world"
	ui.game.world_node=9;ui._clear_menu();ui.notice_time=0
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	viewport=SubViewport.new();viewport.size=Vector2i(1278,720);viewport.size_2d_override=Vector2i(426,240);viewport.size_2d_override_stretch=true
	viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	ui=load("res://scenes/main.tscn").instantiate();ui.game.slot_directory="/private/tmp/revenge-hero-professions-20261023/unused-slots"
	viewport.add_child(ui);await process_frame;ui.set_process(false);ui.set_physics_process(false)
	ui.game.save_path="res://reports/chapter3/play/round1final-chapter-end.json"
	if not ui.game.load_game() or not ui.game.begin_chapter_four():errors.append("source fixture failed");quit(1);return
	ui.game.save_path="/private/tmp/revenge-hero-professions-20261023/visual-working.json"
	ui.instant_mode=true;ui.busy=false;ui.batch_running=false;ui.phase_time=0;ui.notice_time=0;ui.game.story_events.clear()
	ui.game.ChapterFour.promote_hero(ui.game,"hunapu");ui.game.ChapterFour.promote_hero(ui.game,"eileen")
	var h=Room.new();h.ui=Recorder.new();h.ui.game=ui.GameState.new()
	h.ui.game.save_path="res://reports/chapter3/play/round1final-chapter-end.json";h.ui.game.load_game();h.ui.game.begin_chapter_four()
	h.ui.game.save_path="/private/tmp/revenge-hero-professions-20261023/dialogue-working.json";h.ui.game.flags.obs_steps_ready=true
	await ui.hub_controller.FourthHub.action(h,"fourth_tower_shutdown")
	await ui.hub_controller.FourthHub.action(h,"fourth_island_verify")
	var announcements=h.ui.pages.filter(func(page):return str(page.speaker)=="旁白" and (str(page.text).contains("进阶为") or str(page.text).contains("术法精熟") or str(page.text).contains("进阶按最低基底")))
	for width in [426,256]:
		viewport.size=Vector2i(width*3,720);viewport.size_2d_override=Vector2i(width,240)
		for id in ["hunapu","eileen"]:
			route("alm" if id=="hunapu" else "celica")
			ui._camp_action("status:"+id)
			await shot(str(width)+"-status-"+id,ui.game.HeroProfessions.name(ui.game.roster[id]))
			if id=="eileen":
				var original=ui.game.roster[id].duplicate(true)
				ui.game.roster[id].max_hp=52;ui.game.roster[id].hp=51;ui.game.roster[id].level=20;ui.game.roster[id].exp=99
				await shot(str(width)+"-status-maximums",ui.game.HeroProfessions.name(ui.game.roster[id]))
				ui.game.roster[id]=original
			route("alm" if id=="hunapu" else "celica")
			ui._camp_members("status")
			await shot(str(width)+"-roster-"+id,ui.game.HeroProfessions.name(ui.game.roster[id]))
			route("alm" if id=="hunapu" else "celica")
			ui.game.convoy[ui.game.route]=[63 if id=="hunapu" else 65]
			ui.equipment_screen.open(0)
			await shot(str(width)+"-equipment-"+id,ui.game.HeroProfessions.name(ui.game.roster[id]))
			ui.equipment_screen.accept()
			await shot(str(width)+"-preview-"+id,ui.game.HeroProfessions.name(ui.game.roster[id]))
		route("celica");ui.game.world_node=26;ui.game.start_battle(405);ui.game.story_events.clear()
		ui.view="battle";ui.ui_mode="inspect";ui.game.selected_id="eileen";ui.game.find_unit("eileen").magic_flags=159
		ui._menu_action("magic","")
		await shot(str(width)+"-magic-costs","雷电 1HP")
		ui._clear_menu();ui.plot_return="world";ui.game.mode="world"
		for i in range(announcements.size()):
			ui.plot_pages=ui._paginate_plot(announcements[i]);ui.view="plot"
			for page in range(ui.plot_pages.size()):
				ui.plot_index=page;ui.dialogue_reveal=str(ui.plot_pages[page].text).length()
				await shot(str(width)+"-announcement-"+str(i)+"-"+str(page),str(ui.plot_pages[page].text).split("\n")[0])
	var f=FileAccess.open(OUT+"captures.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"shots":shots,"errors":errors,"background_guard":true,"visible_windows":false,"fixture":true,"user_saves_touched":false},"  "));f.close()
	ui.queue_free();viewport.queue_free();await process_frame
	print("HERO_PROFESSIONS_VISUAL ",shots.size()," screenshots; errors: ",errors)
	quit(0 if errors.is_empty() else 1)

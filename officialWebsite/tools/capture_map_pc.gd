extends SceneTree
## Official website: production PC scene, directed demonstration fixtures.
const OUT="/Users/gcc/gaocc/project/revenge-memories/officialWebsite/source/map-captures/"
const MOVIE="/private/tmp/revenge-website-map-pc-frames/"
var vp
var ui
var records=[]
var segments=[]
var errors=[]
var movie_frame=0
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func picture(path:String=""):
	ui.queue_redraw()
	await process_frame;await RenderingServer.frame_post_draw
	for e in ui.layout_errors:
		if not errors.has(str(e)):errors.append(str(e))
	if not path.is_empty():vp.get_texture().get_image().save_png(path)
func fixture(job:Dictionary):
	ui.hero_map_animation.reset();ui.game.new_game();ui.game.save_path="/private/tmp/revenge-map-skills-20261029/visual.json"
	ui.game.world_node=int(ui.game.stages[int(job.stage)].node);ui.game.stage_id=int(job.stage)
	ui.game.battle_data=ui.game.stages[int(job.stage)].duplicate(true);ui.game.chapter=int(ui.game.battle_data.chapter);ui.game.route=str(ui.game.battle_data.route);ui.game.mode="battle"
	ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
	ui.game.ChapterTwo.initialize(ui.game)
	if ui.game.chapter==4:ui.game.ChapterFour.initialize(ui.game)
	ui.game.story_events.clear()
	var hero=job.hero_data.duplicate(true);hero.side="player";hero.position=job.hero_at;hero.acted=false;hero.no_experience=true
	ui.game.MapSkills.clear(hero)
	if job.advanced:ui.game.HeroProfessions.apply(hero);hero.hp=hero.max_hp
	if str(job.key)=="hunapu-bow":hero.item_id=22
	var friend=ui.game.characters.otto.duplicate(true);friend.id="map_preview_friend";friend.side="player";friend.position=job.friend;friend.acted=false
	ui.game.units=[hero,friend]
	for item in job.enemies_data:
		var enemy=item.unit.duplicate(true);enemy.acted=false;ui.game.units.append(enemy)
	ui.game.party=[hero.id,friend.id];ui.game.phase="player";ui.game.turn=1;ui.game.selected_id=hero.id;ui.game.cursor=Vector2i(job.hero_at[0],job.hero_at[1])
	ui.game.move_origin=ui.game.cursor
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui.elapsed=.4;ui._clear_menu()
	ui._focus_battle(Vector2i(job.center[0],job.center[1]),true)
	return hero
func run():
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT));DirAccess.make_dir_recursive_absolute(MOVIE)
	DirAccess.make_dir_recursive_absolute("/private/tmp/revenge-map-skills-20261029/slots")
	vp=SubViewport.new();vp.size=Vector2i(1278,720);vp.size_2d_override=Vector2i(426,240);vp.size_2d_override_stretch=true;vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame
	ui.game.slot_directory="/private/tmp/revenge-website-map-pc/slots";ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=false
	var jobs=JSON.parse_string(FileAccess.get_file_as_string("res://reports/map-skills-20261029/visual-fixtures.json"))
	for job in jobs:
		var hero=fixture(job);ui._unit_action_menu();await picture(OUT+str(job.key)+"-menu.png")
		ui._choose_map_skill();ui.game.cursor=Vector2i(job.center[0],job.center[1]);ui.map_facing=Vector2i.RIGHT;ui._refresh_map_forecast();ui.battle_camera=Vector2(job.center[0]*16-130,job.center[1]*16-65)
		await picture(OUT+str(job.key)+"-target-free.png")
		hero.map_uses=2;ui._refresh_map_forecast();await picture(OUT+str(job.key)+"-target-third.png")
		hero.map_uses=0;ui._clear_menu();ui.busy=true;ui.ui_mode="whole_capture";ui.notice_time=0;ui.phase_time=0
		var receipt=ui.game.MapSkills.apply(ui.game,str(hero.id),Vector2i(job.center[0],job.center[1]),Vector2i.RIGHT)
		if not receipt.get("valid",false):errors.append(str(job.key)+": "+str(receipt.get("reason","invalid")));continue
		ui._focus_battle(Vector2i(job.center[0],job.center[1]),true)
		ui.hero_map_animation.prepare(receipt)
		var duration=float(ui.hero_map_animation.spec.duration);var start=movie_frame
		for frame in range(ceili(duration*30)):
			var t=frame/30.0;ui.hero_map_animation._step(t)
			await picture(MOVIE+"frame-%05d.png"%movie_frame)
			if frame in [0,5,11,18,24]:vp.get_texture().get_image().save_png(OUT+str(job.key)+"-motion-%02d.png"%frame)
			movie_frame+=1
		ui.hero_map_animation._step(duration)
		segments.append({"key":str(receipt.key),"name":str(receipt.name),"frame_start":start,"frames":movie_frame-start,"start_seconds":start/30.0,"seconds":(movie_frame-start)/30.0,"sounds":ui.hero_map_animation.audit.sounds.duplicate(true),"contacts":ui.hero_map_animation.audit.contacts.duplicate()})
		records.append({"key":str(receipt.key),"targets":receipt.targets.map(func(t):return {"id":t.id,"damage":t.damage,"center_bonus":t.center_bonus}),"planned_seconds":duration,"contacts":ui.hero_map_animation.audit.contacts.duplicate(),"cost":receipt.cost})
		ui.hero_map_animation.reset();print("MAP_VISUAL ",job.key)
	var report={"passed":errors.is_empty(),"errors":errors,"guard":true,"fps":30,"frames":movie_frame,"seconds":movie_frame/30.0,"segments":segments,"cases":records,"frame_directory":MOVIE,"scope":"Production Godot PC scene, real MAP rules/renderer, directed fixture placements, current 2026-11-02 muted-red damage numbers. 1278x720 PC viewport, isolated save path, background guard."}
	var f=FileAccess.open(OUT+"visual.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	ui.hero_map_animation.reset();ui.audio.stop_all();ui.queue_free();await process_frame;vp.queue_free();await process_frame
	print("MAP_VISUAL_ERRORS ",errors);quit(0 if errors.is_empty() else 1)

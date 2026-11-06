extends "res://tests/m15_story_20261101.gd"
## Actual timed native-renderer playback of an isolated fatal-hit fixture.
func run():
	if DisplayServer.get_name()=="headless" or OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(2);return
	DirAccess.make_dir_recursive_absolute(TEMP+"movie")
	screen=SubViewport.new();screen.size=Vector2i(1334,750);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(0,0,1334,750);phone.journal_directory_override=TEMP+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.game=battle();ui.game.story_events.clear();death(ui.game)
	var event=ui.game.story_events.pop_front();ui.view="battle";ui.instant_mode=false;ui.phase_time=0;ui.notice_time=0;ui.m15_scene.start(event,"battle")
	var start=Time.get_ticks_msec();var previous_page="";var page_started=start;var frames=0
	while ui.m15_scene.active and Time.get_ticks_msec()-start<40000:
		if ui.view=="plot":
			ui.dialogue_reveal=10000
			var identity=str(ui.m15_scene.state.step)+":"+str(ui.plot_index)
			if identity!=previous_page:previous_page=identity;page_started=Time.get_ticks_msec()
			if Time.get_ticks_msec()-page_started>=1600:ui._accept()
		ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
		screen.get_texture().get_image().save_png(TEMP+"movie/frame-%04d.png"%frames);frames+=1
		var wait=maxf(0.001,(start+frames*100-Time.get_ticks_msec())/1000.0)
		await create_timer(wait).timeout
	var file=FileAccess.open(OUT+"movie.json",FileAccess.WRITE);file.store_string(JSON.stringify({"frames":frames,"fps":10,"seconds":(Time.get_ticks_msec()-start)/1000.0,"native_rendering":true,"fixture_playback":true,"death_completed":ui.game.flags.get("korlan_dead",false)},"  "));file.close()
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;await create_timer(0.25).timeout
	print("M15_MOVIE ",frames," frames");quit()

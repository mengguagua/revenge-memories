extends "res://tests/d00_prologue.gd"
const MOVIE_CACHE="/private/tmp/revenge-d00-movie-20261026/"
var frame_number=0
var sound_events=[]
var movie_events=[]
func on_sound(cue:String):sound_events.append({"cue":cue,"frame":frame_number,"seconds":frame_number/30.0})
func run():
	rendered=true;record_checkpoints=false
	DirAccess.make_dir_recursive_absolute(CACHE+"slots");DirAccess.make_dir_recursive_absolute(MOVIE_CACHE)
	await setup();screen.size=Vector2i(1280,592);phone.safe_area_override=Rect2(89,0,1102,558);phone._layout();await process_frame
	begin("艾琳");ui.elapsed=0
	var previous_page="";var page_time=0.0;var previous_step=-1
	while ui.prologue_scene.active and frame_number<2400:
		var scene=ui.prologue_scene
		if int(scene.state.step)!=previous_step:
			previous_step=int(scene.state.step);movie_events.append({"step":str(scene.spec.steps[previous_step].id),"frame":frame_number,"seconds":frame_number/30.0})
		ui._process(1.0/30.0)
		if ui.view=="plot":
			var identity=str(scene.state.step)+":"+str(ui.plot_index)
			if identity!=previous_page:previous_page=identity;page_time=0
			page_time+=1.0/30.0
			var text=str(ui.plot_pages[ui.plot_index].text)
			if ui.dialogue_reveal>=text.length() and page_time>=maxf(2.0,text.length()/28.0+1.0):key(KEY_Z)
		ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
		await process_frame;await RenderingServer.frame_post_draw
		screen.get_texture().get_image().save_png(MOVIE_CACHE+"frame-%05d.png"%frame_number)
		frame_number+=1
	# Include the actual arrival, without opening the later grave conversation.
	for n in range(30):
		ui.queue_redraw();phone.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
		screen.get_texture().get_image().save_png(MOVIE_CACHE+"frame-%05d.png"%frame_number);frame_number+=1
	var report={"frames":frame_number,"fps":30,"seconds":frame_number/30.0,"events":movie_events,"sounds":sound_events,"final_room":ui.game.hub_record,"frame_directory":MOVIE_CACHE,"scope":"Actual engine offline viewport frames, automated confirmation after each readable dialogue hold. Soundtrack is assembled from the runtime cue log and the same game audio assets; not a microphone/screen recording."}
	var file=FileAccess.open(OUT+"movie.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
	print("D00_MOVIE ",frame_number," frames, room ",report.final_room)
	quit(0 if frame_number<2400 and report.final_room=="H01" else 1)

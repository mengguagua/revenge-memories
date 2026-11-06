extends "res://tests/walk_counter_20261029.gd"
const MOVIE="/private/tmp/revenge-walk-counter-movie-20261029/"
var movie_frame=0
var segments=[]
func capture():
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	screen.get_texture().get_image().save_png(MOVIE+"frame-%05d.png"%movie_frame);movie_frame+=1
func segment(name:String):segments.append({"name":name,"frame":movie_frame,"seconds":movie_frame/30.0})
func run():
	visual=true;DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(MOVIE)
	await setup();screen.size=Vector2i(1280,592);phone.safe_area_override=Rect2(89,0,1102,558);phone._layout()
	ui.game.new_game();ui.game.save_path=cache+"movie.json";ui.hub_controller.enter_room("P00");ui.prologue_scene.state={"clock":999.0};ui.prologue_scene.active=false
	segment("P00 · 短按与连续迈步")
	for pair in [[Vector2i.RIGHT,27],[Vector2i.UP,27],[Vector2i.LEFT,18],[Vector2i.DOWN,27],[Vector2i.ZERO,9]]:
		ui.held_direction=pair[0]
		for n in range(pair[1]):ui._process(1.0/30.0);await capture()
	ui.held_direction=Vector2i.ZERO
	var scene=ui.prologue_scene;scene.active=true;ui.view="prologue_scene"
	for pair in [[3,"D00 · 上前阻挡时迈步",80],[7,"D00 · 走近后伸手",40]]:
		segment(pair[1]);scene.state={"version":1,"step":pair[0],"time":0.0,"clock":4.0,"sounds":{}}
		for n in range(pair[2]):ui._process(1.0/30.0);await capture()
	scene.active=false
	for cid in [6,2,8]:
		segment({6:"敌方枪兵 · 投枪反击",2:"敌方重装兵 · 投枪反击",8:"敌方剑兵 · 引霆剑（雷电剑）反击"}[cid])
		ui.game=fixture(cid,3);ui.view="combat";ui.busy=true;ui.combat=ui.game.plan_combat("daan","M12_boss");ui.combat_hp={"daan":52,"M12_boss":52}
		var event=ui.combat.events.filter(func(e):return str(e.attacker)=="M12_boss")[0]
		ui.battle_animation.reset();ui.battle_animation.active_event=event
		var chosen=ui.battle_animation.selection(event);var committed=false
		for n in range(ceili(chosen.variant.frames.size()/2.0)):
			var tick=mini(n*2,chosen.variant.frames.size()-1)
			ui.battle_animation.show_frame(event,tick)
			if not committed and tick>=int(chosen.variant.contact_tick):
				ui.game.commit_strike(event);ui.combat_hp.daan=int(event.hp_after);ui.combat_hp.M12_boss=int(event.source_hp_after);committed=true
			await capture()
		for n in range(12):await capture()
	var file=FileAccess.open(OUT+"movie.json",FileAccess.WRITE);file.store_string(JSON.stringify({"frames":movie_frame,"fps":30,"seconds":movie_frame/30.0,"segments":segments,"frame_directory":MOVIE,"scope":"Actual background Godot viewport; P00/D00 production controller movement, real selected ranged-counter animation frames and one commit at its contact. Silent review footage, not iPhone capture."},"  "));file.close()
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame;print("WALK_COUNTER_MOVIE ",movie_frame);quit()

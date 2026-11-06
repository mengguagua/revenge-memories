extends SceneTree
const State=preload("res://core/game_state.gd")
const Professions=preload("res://core/hero_professions.gd")
const OUT="/Users/gcc/gaocc/project/revenge-memories/art-review/map-20261029/"
var vp
var phone
var ui
var records=[]
var jobs=[
	{"key":"hunapu-base","stage":101,"hero":"hunapu","advanced":false,"hero_at":[5,13],"center":[6,13],"enemies":[[6,12],[6,13],[7,14]],"friend":[7,13]},
	{"key":"hunapu-advanced","stage":401,"hero":"hunapu","advanced":true,"hero_at":[10,10],"center":[12,10],"enemies":[[11,9],[11,11],[12,10],[13,9],[14,11]],"friend":[13,10]},
	{"key":"eileen-base","stage":201,"hero":"eileen","advanced":false,"hero_at":[18,12],"center":[21,12],"enemies":[[21,12],[20,12],[21,13]],"friend":[22,12]},
	{"key":"eileen-advanced","stage":405,"hero":"eileen","advanced":true,"hero_at":[11,14],"center":[14,14],"enemies":[[14,14],[13,14],[15,14],[14,12],[14,16]],"friend":[14,13]}
]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func picture(path:String):
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
	for n in range(4):await process_frame
	await RenderingServer.frame_post_draw
	vp.get_texture().get_image().save_png(OUT+path)
func point(at:Array)->Array:
	var p=(ui._battle_cell_screen(Vector2i(at[0],at[1]))+ui._canvas_offset()+Vector2(8,8))*phone.pixel_scale+phone.game_rect.position
	return [p.x,p.y]
func sprite_spec(u:Dictionary)->Dictionary:
	return ui._map_unit_sprite(u).duplicate(true)
func run():
	DirAccess.make_dir_recursive_absolute("/private/tmp/revenge-map-design-slots")
	vp=SubViewport.new();vp.size=Vector2i(1280,592);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(89,0,1102,558);phone.journal_directory_override="/private/tmp/revenge-map-design-slots";vp.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false)
	for job in jobs:
		ui.game.new_game();ui.game.save_path="/private/tmp/revenge-map-design-unused.json";ui.game.world_node=int(ui.game.stages[job.stage].node)
		# Visual fixture only: select the current map data without story progression,
		# campaign unlocks, combat, rewards or persistent state writes.
		ui.game.stage_id=job.stage;ui.game.battle_data=ui.game.stages[job.stage].duplicate(true);ui.game.chapter=int(ui.game.battle_data.chapter);ui.game.route=str(ui.game.battle_data.route);ui.game.mode="battle"
		ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
		ui.game.ChapterTwo.initialize(ui.game)
		if ui.game.chapter==4:ui.game.ChapterFour.initialize(ui.game)
		ui.game.story_events.clear()
		var hero=ui.game.characters[job.hero].duplicate(true);hero.side="player";hero.position=job.hero_at;hero.acted=false
		if job.advanced:Professions.apply(hero);hero.hp=hero.max_hp
		var friend=ui.game.characters.otto.duplicate(true);friend.id="preview_friend";friend.side="player";friend.position=job.friend
		var template=ui.game.battle_data.enemies[1].duplicate(true)
		var members=[hero,friend]
		for i in range(job.enemies.size()):
			var e=template.duplicate(true);e.id="preview_enemy_"+str(i);e.position=job.enemies[i];e.side="enemy";e.behavior="guard";e.acted=false;members.append(e)
		ui.game.units=members;ui.game.party=[hero.id,friend.id];ui.game.phase="player";ui.game.turn=1;ui.game.selected_id="";ui.game.cursor=Vector2i(job.hero_at[0],job.hero_at[1])
		ui.view="battle";ui.ui_mode="whole_capture";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui.elapsed=0.4;ui._clear_menu();ui._focus_battle(Vector2i(job.center[0],job.center[1]),true)
		await picture("reference/"+job.key+"-runtime.png")
		var record=job.duplicate(true);record.hero_point=point(job.hero_at);record.center_point=point(job.center);record.tile=16*phone.pixel_scale;record.hero_data=hero;record.hero_sprite=sprite_spec(hero);record.friend_sprite=sprite_spec(friend);record.enemy_sprite=sprite_spec(template)
		record.enemies_data=[]
		for e in members.slice(2):record.enemies_data.append({"point":point(e.position),"unit":e})
		record.friend_point=point(job.friend);record.camera=[ui.battle_camera.x,ui.battle_camera.y];record.game_rect=[phone.game_rect.position.x,phone.game_rect.position.y,phone.game_rect.size.x,phone.game_rect.size.y];record.logical_size=[phone.game_view.size_2d_override.x,phone.game_view.size_2d_override.y]
		record.layout_errors=ui.layout_errors.duplicate()+phone.layout_errors.duplicate();record.stage_code=ui.game.battle_data.code;record.stage_name=ui.game.battle_data.name_zh
		ui.game.units=[]
		await picture("assets/"+job.key+"-terrain.png")
		records.append(record);print("MAP_REFERENCE ",job.key," ",record.layout_errors)
	var file=FileAccess.open(OUT+"sources/runtime.json",FileAccess.WRITE);file.store_string(JSON.stringify({"guard":true,"scope":"Current production Godot phone scene, background SubViewport. Directed preview fixtures reposition current units on unchanged maps. No MAP gameplay execution, no real iPhone capture, no save writes.","jobs":records},"  "));file.close()
	ui.audio.stop_all();phone.queue_free();await process_frame;vp.queue_free();await process_frame;quit()

extends SceneTree
## Production MAP rules, renderer and UI on background SubViewport fixtures.
const OUT="/Users/gcc/gaocc/project/revenge-memories/art-review/healer-map-20261104/"
const Map=preload("res://core/map_skills.gd")
var vp
var phone
var ui
var records=[]
var errors=[]
var jobs
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	jobs=JSON.parse_string(FileAccess.get_file_as_string(OUT+"sources/runtime.json")).jobs
	call_deferred("run")
func picture(name:String):
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
	for n in range(2):await process_frame
	await RenderingServer.frame_post_draw
	vp.get_texture().get_image().save_png(OUT+"integration/"+name+".png")
	for e in ui.layout_errors+phone.layout_errors:
		if not errors.has(str(e)):errors.append(str(e));push_error(str(e))
	var entry={"name":name,"text_checks":ui.text_checks.size(),"errors":ui.layout_errors.duplicate(),"viewport":[vp.size.x,vp.size.y]}
	for field in ["strong_body","hero_map_forecast","status_stats"]:
		if ui.presentation_audit.has(field):entry[field]=ui.presentation_audit[field].duplicate(true)
	entry.card_valid=ui.battle_card_audit.get("valid",false)
	records.append(entry)
func setup(job:Dictionary,tier:int):
	ui.hero_map_animation.reset();ui.presentation_audit.clear()
	ui.game.new_game();ui.game.save_path="/private/tmp/revenge-healer-map-integration-20261104/fixture.json"
	ui.game.stage_id=int(job.stage);ui.game.world_node=int(ui.game.stages[int(job.stage)].node);ui.game.battle_data=ui.game.stages[int(job.stage)].duplicate(true);ui.game.chapter=int(ui.game.battle_data.chapter);ui.game.route=str(ui.game.battle_data.route);ui.game.mode="battle"
	ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false};ui.game.ChapterTwo.initialize(ui.game)
	if ui.game.chapter==4:ui.game.ChapterFour.initialize(ui.game)
	var caster=job.caster.duplicate(true);caster.position=job.caster_at;caster.acted=false;caster.hp=caster.max_hp;caster.no_experience=true;Map.clear(caster);caster.map_uses=tier
	var target=job.target.duplicate(true);target.position=job.target_at;target.hp=3;Map.clear(target)
	var friend=job.friend.duplicate(true);friend.position=job.other_at;Map.clear(friend)
	var enemy=job.enemy.duplicate(true);enemy.position=job.enemy_at
	ui.game.units=[caster,target,friend,enemy];ui.game.party=[caster.id,target.id,friend.id];ui.game.phase="player";ui.game.turn=3;ui.game.selected_id=caster.id;ui.game.cursor=ui.game.pos(target);ui.game.move_origin=ui.game.pos(caster);ui.game.story_events.clear()
	ui.view="battle";ui.ui_mode="map_target";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui.elapsed=.4;ui._clear_menu();ui._focus_battle(Vector2i(job.focus[0],job.focus[1]),true)
	ui._refresh_map_forecast()
func run():
	DirAccess.make_dir_recursive_absolute("/private/tmp/revenge-healer-map-integration-20261104")
	vp=SubViewport.new();vp.size=Vector2i(1280,592);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(89,0,1102,558);phone.journal_directory_override="/private/tmp/revenge-healer-map-integration-20261104/slots";vp.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
	for job in jobs:
		for tier in range(3):
			setup(job,tier)
			if tier==0:
				ui._unit_action_menu();await picture(str(job.key)+"-action-menu")
				ui._clear_menu();ui.ui_mode="map_target";ui.game.cursor=ui.game.pos(ui.game.units[1]);ui._focus_battle(Vector2i(job.focus[0],job.focus[1]),true);ui._refresh_map_forecast()
			await picture(str(job.key)+"-forecast-"+str(tier+1))
			var receipt=Map.apply(ui.game,ui.game.selected_id,ui.game.cursor)
			if not receipt.get("valid",false):errors.append(str(receipt));continue
			ui._clear_menu();ui.busy=true;ui.ui_mode="whole_capture";ui.hero_map_animation.prepare(receipt)
			if tier==0:
				for frame in range(roundi(float(job.duration)*30)+1):
					ui.hero_map_animation._step(minf(float(job.duration),float(frame)/30.))
					await picture("frames/"+str(job.key)+"-%03d"%frame)
			ui.hero_map_animation._step(.64);await picture(str(job.key)+"-impact-"+str(tier+1))
			ui.hero_map_animation.reset();ui.busy=false;ui.ui_mode="inspect";ui.game.selected_id="";await picture(str(job.key)+"-strong-2-"+str(tier+1))
			ui.ui_mode="status";ui.status_id=str(ui.game.units[1].id);await picture(str(job.key)+"-status-"+str(tier+1));ui.ui_mode="inspect"
			ui.game.cursor=ui.game.pos(ui.game.units[0]);await picture(str(job.key)+"-caster-"+str(tier+1))
			if tier==0:
				ui.game.cursor=ui.game.pos(ui.game.units[1]);ui.game.turn=4;Map.StrongBody.expire_at_player_start(ui.game);await picture(str(job.key)+"-strong-1")
				ui.game.turn=5;Map.StrongBody.expire_at_player_start(ui.game);await picture(str(job.key)+"-strong-0")
	# Minimum desktop and a phone with one-pixel logical scale.
	for size in [Vector2i(844,390),Vector2i(512,300)]:
		vp.size=size;phone.safe_area_override=Rect2(Vector2.ZERO,Vector2(size));await process_frame;await process_frame
		setup(jobs[0],2);await picture("compact-"+str(size.x)+"-forecast")
		var result=Map.apply(ui.game,ui.game.selected_id,ui.game.cursor);ui.hero_map_animation.reset();ui.game.selected_id="";ui.ui_mode="inspect";await picture("compact-"+str(size.x)+"-strong")
	var f=FileAccess.open(OUT+"integration/capture.json",FileAccess.WRITE);f.store_string(JSON.stringify({"guard":true,"passed":errors.is_empty(),"errors":errors,"records":records,"scope":"Production Godot rules and renderer; directed fixtures in background SubViewport, isolated temporary saves; not an iPhone capture."},"  "));f.close()
	ui.audio.stop_all();ui.story_intro.ui=null;ui.story_intro=null
	ui.equipment_screen.art.ui=null;ui.equipment_screen.art=null;ui.equipment_screen.ui=null;ui.equipment_screen=null
	ui.journey.art.ui=null;ui.journey.art=null;ui.journey.ui=null;ui.journey=null
	phone.queue_free();await process_frame;vp.queue_free();await process_frame
	print("HEALER_INTEGRATION ",records.size()," ERRORS=",errors);quit(0 if errors.is_empty() else 1)

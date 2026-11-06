extends SceneTree
## Read-only art fixtures on the production phone viewport; no MAP business code.
const OUT="/Users/gcc/gaocc/project/revenge-memories/art-review/healer-map-20261104/"
var vp
var phone
var ui
var jobs=[
	{"key":"healer","hero":"fula","stage":102,"caster_at":[9,15],"target_at":[15,13],"other_at":[15,14],"enemy_at":[16,13],"focus":[12,14],"reach":8,"duration":1.2},
	{"key":"saint","hero":"celine","stage":405,"caster_at":[7,16],"target_at":[15,14],"other_at":[15,15],"enemy_at":[16,14],"focus":[11,15],"reach":10,"duration":1.4}
]
var errors=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func picture(path:String):
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
	for n in range(3):await process_frame
	await RenderingServer.frame_post_draw
	vp.get_texture().get_image().save_png(OUT+path)
	for e in ui.layout_errors+phone.layout_errors:
		if not errors.has(str(e)):errors.append(str(e))
func point(p:Array)->Array:
	var v=(ui._battle_cell_screen(Vector2i(p[0],p[1]))+ui._canvas_offset()+Vector2(8,8))*phone.pixel_scale+phone.game_rect.position
	return [v.x,v.y]
func run():
	DirAccess.make_dir_recursive_absolute("/private/tmp/revenge-healer-map-design-20261104/slots")
	vp=SubViewport.new();vp.size=Vector2i(1280,592);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(89,0,1102,558);phone.journal_directory_override="/private/tmp/revenge-healer-map-design-20261104/slots";vp.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true
	for job in jobs:
		ui.game.new_game();ui.game.save_path="/private/tmp/revenge-healer-map-design-20261104/unused.json"
		ui.game.stage_id=int(job.stage);ui.game.world_node=int(ui.game.stages[job.stage].node);ui.game.battle_data=ui.game.stages[job.stage].duplicate(true);ui.game.chapter=int(ui.game.battle_data.chapter);ui.game.route=str(ui.game.battle_data.route);ui.game.mode="battle"
		ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false};ui.game.ChapterTwo.initialize(ui.game)
		if ui.game.chapter==4:ui.game.ChapterFour.initialize(ui.game)
		ui.game.story_events.clear()
		var caster=ui.game.characters[job.hero].duplicate(true);caster.side="player";caster.acted=false;caster.position=job.caster_at
		var target=ui.game.characters.hunapu.duplicate(true);target.side="player";target.acted=false;target.position=job.target_at;target.hp=3
		var friend=ui.game.characters.otto.duplicate(true);friend.side="player";friend.acted=false;friend.position=job.other_at;friend.hp=7
		var enemy=ui.game.battle_data.enemies[1].duplicate(true);enemy.id="preview_enemy";enemy.side="enemy";enemy.acted=false;enemy.position=job.enemy_at
		# Prefer clear walkable ground for the demonstration; preserve exact
		# eight/ten-tile reach while avoiding an impossible mountain placement.
		var pair=[]
		var score=INF
		for y in range(6,ui.game.battle_data.map.height-5):
			for x in range(5,ui.game.battle_data.map.width-12):
				var from=Vector2i(x,y);var to=from+Vector2i(int(job.reach)-1,-1)
				if not ui.game.in_bounds(to) or ui.game.movement_cost(caster,from)!=1 or ui.game.movement_cost(target,to)!=1 or ui.game.movement_cost(friend,to+Vector2i.DOWN)!=1 or ui.game.movement_cost(enemy,to+Vector2i.RIGHT)!=1:continue
				var value=from.distance_squared_to(Vector2i(job.caster_at[0],job.caster_at[1]))
				if value<score:score=value;pair=[from,to]
		if not pair.is_empty():
			job.caster_at=[pair[0].x,pair[0].y];job.target_at=[pair[1].x,pair[1].y];job.other_at=[pair[1].x,pair[1].y+1];job.enemy_at=[pair[1].x+1,pair[1].y];job.focus=[roundi((pair[0].x+pair[1].x)*.5),roundi((pair[0].y+pair[1].y)*.5)]
			caster.position=job.caster_at;target.position=job.target_at;friend.position=job.other_at;enemy.position=job.enemy_at
		ui.game.units=[caster,target,friend,enemy];ui.game.party=[caster.id,target.id,friend.id];ui.game.phase="player";ui.game.turn=3;ui.game.selected_id="";ui.game.cursor=Vector2i(job.target_at[0],job.target_at[1]);ui.game.move_origin=ui.game.cursor
		ui.view="battle";ui.ui_mode="whole_capture";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui.elapsed=.4;ui._clear_menu();ui._focus_battle(Vector2i(job.focus[0],job.focus[1]),true)
		await picture("reference/"+str(job.key)+"-runtime.png")
		job.caster=caster;job.target=target;job.friend=friend;job.enemy=enemy
		job.caster_point=point(job.caster_at);job.target_point=point(job.target_at);job.friend_point=point(job.other_at);job.enemy_point=point(job.enemy_at);job.tile=16*phone.pixel_scale
		job.caster_sprite=ui._map_unit_sprite(caster).duplicate(true);job.target_sprite=ui._map_unit_sprite(target).duplicate(true);job.friend_sprite=ui._map_unit_sprite(friend).duplicate(true);job.enemy_sprite=ui._map_unit_sprite(enemy).duplicate(true)
		job.stage_code=ui.game.battle_data.code;job.stage_name=ui.game.battle_data.name_zh;job.panel=ui.graphics.panel;job.pixel_scale=phone.pixel_scale
		job.detail_footer={"target":ui._terrain_name(ui.game.pos(target))+" 回避+"+str(ui.game.terrain_avoid(ui.game.pos(target))),"friend":ui._terrain_name(ui.game.pos(friend))+" 回避+"+str(ui.game.terrain_avoid(ui.game.pos(friend)))}
		job.detail_tactical={"target":"MAP剩余3/3","friend":"主动近战命中可击退1格" if ui.game.Knockback.capable(ui.game,friend) else "移动"+str(friend.move)+"格"}
		job.game_rect=[phone.game_rect.position.x,phone.game_rect.position.y,phone.game_rect.size.x,phone.game_rect.size.y];job.canvas_offset=[ui._canvas_offset().x,ui._canvas_offset().y];job.camera=[ui.battle_camera.x,ui.battle_camera.y]
		ui.ui_mode="inspect";await picture("reference/"+str(job.key)+"-detail-before.png")
		job.detail_audit=ui.battle_card_audit.duplicate(true)
		ui.ui_mode="whole_capture";ui.game.units=[];await picture("assets/"+str(job.key)+"-terrain.png")
		print("HEALER_REFERENCE ",job.key," ",job.caster_point," ",job.target_point)
	var f=FileAccess.open(OUT+"sources/runtime.json",FileAccess.WRITE);f.store_string(JSON.stringify({"guard":true,"scope":"Current production Godot phone scene, background SubViewport; directed placements on unchanged real maps. Visual reference only: no new healing rules, live saves, combat or device installation.","jobs":jobs,"errors":errors},"  "));f.close()
	ui.audio.stop_all()
	ui.story_intro.ui=null;ui.story_intro=null
	ui.equipment_screen.art.ui=null;ui.equipment_screen.art=null;ui.equipment_screen.ui=null;ui.equipment_screen=null
	ui.journey.art.ui=null;ui.journey.art=null;ui.journey.ui=null;ui.journey=null
	phone.queue_free();await process_frame;vp.queue_free();await process_frame
	print("HEALER_REFERENCE_ERRORS ",errors);quit(0 if errors.is_empty() else 1)

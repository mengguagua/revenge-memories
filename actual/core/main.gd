extends "res://core/legacy_main.gd"
## Original native combat controller, new world / story / hub presentation.
const EnvironmentBorder = preload("res://core/environment_border.gd")
const BattlePanels = preload("res://core/battle_panel_layout.gd")
const SpellInfo=preload("res://core/spell_info.gd")
const Portraits = preload("res://core/portrait_library.gd")
const PartySprites = preload("res://core/party_sprites.gd")
const TacticalIdle=preload("res://core/tactical_idle.gd")
const PostbattleNpcs = preload("res://core/postbattle_npcs.gd")
const JourneyScreen = preload("res://core/journey_screen.gd")
const EquipmentScreen = preload("res://core/equipment_screen.gd")
const HubCaption = preload("res://core/hub_caption_layout.gd")
const StoryIntro = preload("res://core/story_intro.gd")
const PrologueScene = preload("res://core/prologue_scene.gd")
const M15Scene = preload("res://core/m15_scene.gd")
const HeroMapAnimation=preload("res://core/map_skill_animation.gd")
var hero_map_animation
var map_facing:=Vector2i.RIGHT
var story_intro
var prologue_scene
var m15_scene
var field_notes
const OVERVIEW_IMAGE = preload("res://assets/world_tiles/formal-world-overview.png")
var chapter_one_world_climate: Dictionary = {}
var chapter_three_world_environment: Dictionary = {}
var chapter_four_world_environment: Dictionary = {}
var chapter_five_world_environment: Dictionary = {}
var overview_zoom := 1
var overview_center := Vector2(0.5,0.5)
var overview_mouse_drag := false
var overview_audit: Dictionary = {}
var phone_hub_caption := Rect2()
var phone_hub_caption_room := ""
var journey
var equipment_screen
var battle_card_audit: Dictionary={}
var battle_preview_audit: Dictionary={}
var mechanical_target_id:=""
var mechanical_target_part:=""
var mechanical_target_confirmed:=false
var training_reward_open := false
var objective_badge_rect := Rect2()
var battle_pack: Dictionary
var nature_layouts: Dictionary
var nature_sprites: Dictionary={}
var world_actor := Vector2.ZERO
var world_path: Array = []
var world_destination := 0
var world_step := 0.0
var plot_pages: Array = []
var plot_index := 0
var plot_return := "hub"
var plot_callback := ""
var plot_finished := true
var plot_persistent := true
var world_facing := Vector2i.DOWN
var previous_canvas_size := Vector2.ZERO
var plot_layout_audit: Dictionary = {}
var small_font: Dictionary = {}
const NPC_PORTRAITS := {"赫兰":35,"艾琳":48,"科兰":37,"乌库布·卡基":50,
	"村民":17,"运药员":17,"管理员":30,"矿工":47,"医者":13,"教团守卫":26,"教团兵":26,
	"指挥官":26,"士兵":26,"守军":26,"焚毁兵":26,"流民":17,"劳工":47,
	"居民":17,"投降兵":26,"斥候":26,"裴萨":37,"船长":26,"舵手":26,
	"甲板护卫":26,"船员":47,"引航者":47,"渔民":17,"渔村长者":17,
	"岛上医者":13,"地方医者":13,"留守骑士":26,"学舍导师":30,"俘虏":17,
	"固定舵手":26,"旧船员":47,"求救船员":47,"伤者":17,
	"仓吏":30,"记录员":30,"文书":30,"医师":13,"守灯人":47,"账房":30,"洞民":17}
const NARRATOR_SPEAKERS := ["旁白", "", "叙述", "战场提示", "界面提示", "提示", "旧记录", "堡内记录"]

func _ready() -> void:
	super._ready()
	_bind_recruitment_signal()
	journey=JourneyScreen.new(self);journey.refresh();title_menu=true
	title_selected=1 if journey.records.any(func(record):return record.valid) else 0
	equipment_screen=EquipmentScreen.new(self)
	small_font=GameState.read_json("res://data/legacy/font_small_zh.json")
	get_window().title="revenge-memories · 序章至第三章 · "+str(ProjectSettings.get_setting("application/config/version",""))
	world=game.formal_world;battle_pack=GameState.read_json("res://assets/battle_tiles/battle-tiles.json")
	nature_layouts=GameState.read_json("res://data/nature-layouts.json")
	for sprite in GameState.read_json("res://assets/nature/nature.json").get("sprites",[]):nature_sprites[str(sprite.key)]=sprite
	hub_controller=load("res://core/story_hub.gd").new(self)
	story_intro=StoryIntro.new(self)
	prologue_scene=PrologueScene.new(self)
	m15_scene=M15Scene.new(self)
	field_notes=load("res://core/field_notes.gd").new(self)
	hero_map_animation=HeroMapAnimation.new(self)
	world_actor=Vector2(world.nodes["1"].position[0],world.nodes["1"].position[1])*16
	if get_viewport() is Window:
		get_window().size_changed.connect(_resize_window_viewport)
		_resize_window_viewport()

func _resize_window_viewport() -> void:
	# EXPAND with a fixed 256x240 minimum can still leave sizeable integer
	# letterboxing (e.g. 64px at 1280x800). Expand the actual logical canvas
	# to the integer scale first, leaving at most scale-1 physical pixels.
	var window=get_window();var pixels=window.size
	var scale=maxi(1,floori(minf(pixels.x/256.0,pixels.y/240.0)))
	var logical=Vector2i(maxi(256,pixels.x/scale),maxi(240,pixels.y/scale))
	if window.content_scale_size!=logical:window.content_scale_size=logical

func _process(delta: float) -> void:
	if recruitment_paused():
		queue_redraw();return
	if view=="story_intro" and story_intro!=null:story_intro.process(delta)
	if prologue_scene!=null and prologue_scene.active:prologue_scene.process(delta)
	if m15_scene!=null and m15_scene.active:m15_scene.process(delta)
	if view not in ["title","journal","journal_confirm"]:game.play_seconds+=delta
	if journey!=null:journey.saved_left=maxf(0.0,journey.saved_left-delta)
	super._process(delta)
	if view=="overview" and held_direction!=Vector2i.ZERO:
		repeat_timer-=delta
		if repeat_timer<=0.0:
			repeat_timer=0.14;_direction(held_direction)
	if previous_canvas_size!=get_viewport_rect().size:
		previous_canvas_size=get_viewport_rect().size
		if view=="plot":_reflow_plot()
		if view=="battle" and not game.battle_data.is_empty():_focus_battle(game.cursor)
	if not world_path.is_empty():
		world_step+=delta*8.0
		var index=mini(int(world_step),world_path.size()-1)
		var at=world_path[index];var next=world_path[mini(index+1,world_path.size()-1)]
		if at!=next:world_facing=Vector2i(int(next[0])-int(at[0]),int(next[1])-int(at[1]))
		world_actor=Vector2(at[0],at[1]).lerp(Vector2(next[0],next[1]),fmod(world_step,1.0))*16
		if world_step>=world_path.size()-1:
			game.travel_to(world_destination);world_path=[];busy=false;game.mode="world";game.save_game()
		queue_redraw()
	_maybe_training_unlock()

func _maybe_training_unlock() -> void:
	# Old journals receive their one-time introduction only when idle in a
	# peaceful view, after any saved dialogue, movement or result has finished.
	if view not in ["hub","world"] or busy or batch_running or result_sequence_running:return
	if held_direction!=Vector2i.ZERO or (view=="hub" and hub_controller!=null and hub_controller.motion_left>0.0):return
	if not menu_items.is_empty() or not world_path.is_empty() or not game.story_events.is_empty() or game.flags.has("active_plot"):return
	if game.Training.queue_unlock(game):_play_story_events()

func _canvas_offset() -> Vector2:
	return ((get_viewport_rect().size-NATIVE)/2.0).floor()

func _visible_native_rect() -> Rect2:
	return Rect2(-_canvas_offset(),get_viewport_rect().size)

func _footer_shift() -> Vector2:
	return Vector2(0,get_viewport_rect().size.y-240-_canvas_offset().y)

func _mouse_accept(point: Vector2) -> void:
	if recruitment_paused():return
	var local=point-_canvas_offset()
	if view=="field_notes":field_notes.mouse(local);return
	if view=="battle" and ui_mode=="map_target" and not busy:
		var cell=_battle_screen_cell(local)
		if not game.in_bounds(cell):return
		var actor=game.find_unit(game.selected_id);var spec=game.MapSkills.profile(actor)
		if spec.get("male",false):
			var delta=cell-game.pos(actor)
			if delta!=Vector2i.ZERO:map_facing=Vector2i(signi(delta.x),0) if absi(delta.x)>=absi(delta.y) else Vector2i(0,signi(delta.y))
		else:game.cursor=cell;_focus_battle(game.cursor)
		_refresh_map_forecast();queue_redraw();return
	if equipment_screen!=null and equipment_screen.active():equipment_screen.mouse(local);return
	if view in ["journal","journal_confirm"]:journey.mouse(local);return
	if view=="story_intro":story_intro.accept();return
	if view=="prologue_scene":prologue_scene.accept();return
	if view=="plot":_accept();return
	if view=="overview":return
	if view=="chapter_end" and menu_items.is_empty():_accept();return
	if view=="title" and title_menu:
		for i in range(2):
			if journey.title_button(i).has_point(local):title_selected=i;_accept();return
		return
	if _status_open() and not busy and menu_items.is_empty():
		if _status_members().size()>1:
			if Rect2(16,20,24,20).has_point(local):_cycle_status(-1);return
			if Rect2(216,20,24,20).has_point(local):_cycle_status(1);return
		# Status is a reading surface. Only explicit return/confirm controls close it.
		return
	if view=="battle" and not busy and menu_items.is_empty() and ui_mode not in ["status","action"]:
		var cell=_battle_screen_cell(local)
		# Extended mountains are visual-only; in_bounds remains the authority.
		if not game.in_bounds(cell):return
		if ui_mode in ["target","support_target"]:
			var candidate=game.unit_at(cell)
			if not candidate.is_empty() and target_ids.has(candidate.id):
				if target_ids[target_index]!=candidate.id:mechanical_target_confirmed=false;mechanical_target_part=""
				target_index=target_ids.find(candidate.id);game.cursor=cell;_focus_battle(cell);_accept()
		else:game.cursor=cell;_focus_battle(cell);_accept()
		return
	super._mouse_accept(local)

func _new_game() -> void:
	journey.open("new")

func _new_journey_in_slot() -> void:
	_bind_recruitment_signal()
	_clear_menu();held_direction=Vector2i.ZERO;busy=false;batch_running=false;ui_mode="inspect";world_path=[]
	# A fresh journal owns the opening checkpoint; old journals start as before.
	game.flags.story_intro_pending=true;game.flags.story_intro_offset=-1
	story_intro.start()

func _resume_journey() -> void:
	_bind_recruitment_signal()
	_clear_menu();busy=false;batch_running=false;ui_mode="inspect";view=game.mode;held_direction=Vector2i.ZERO;world_path=[]
	if view=="battle" and not game.battle_outcome.is_empty():view=game.battle_outcome;game.mode=view
	world_actor=Vector2(world.nodes[str(game.world_node)].position[0],world.nodes[str(game.world_node)].position[1])*16
	if game.flags.get("story_intro_pending",false):story_intro.start();return
	if view=="hub":hub_controller.resume()
	elif view=="battle":_focus_battle(game.cursor,true);_play_phase_music()
	elif view=="world":audio.play_world(game.chapter)
	elif view=="ending":_start_ending();return
	if prologue_scene.can_resume():prologue_scene.resume();return
	if m15_scene.can_resume():
		m15_scene.resume()
		while m15_scene.active:await get_tree().process_frame
		busy=false
		if view=="battle" and not game.battle_outcome.is_empty():view=game.battle_outcome;game.mode=view
	if game.chapter==3 and str(game.flags.get("active_plot",{}).get("callback",""))=="third_prologue":prologue_scene.resume_reprise()
	if game.flags.has("active_plot"):
		_resume_plot()
		while not plot_finished:await get_tree().process_frame
	if view=="hub":await hub_controller.resume_east_departure()
	if not game.story_events.is_empty():await _play_story_events()
	if view in ["victory","defeat"]:_show_result()
	elif view=="battle":
		await _resolve_pending_loot()
		# Continue the persisted enemy phase once, honoring already acted units.
		if game.phase=="enemy" and view=="battle":_enemy_phase()

func _show_title() -> void:
	# Keep the gameplay checkpoint mode intact when returning to the homepage.
	view="title";title_menu=true;elapsed=0.0;held_direction=Vector2i.ZERO
	_clear_menu();audio.play_music("title")
	if journey!=null:journey.refresh()
	title_selected=1 if journey!=null and journey.records.any(func(record):return record.valid) else 0

func _begin_existing_battle() -> void:
	notice_time=0
	super._begin_existing_battle()

func _accept() -> void:
	if view=="battle" and game.phase=="player" and ui_mode=="target" and not busy and menu_items.is_empty() and not target_ids.is_empty():
		var id=str(target_ids[target_index]);var enemy=game.find_unit(id)
		if game.Mechanical.is_puppet(enemy) and game.Mechanical.part_keys(enemy).any(func(key):return game.Mechanical.valid_part(enemy,key)):
			if mechanical_target_id!=id or not mechanical_target_confirmed:
				mechanical_target_id=id;mechanical_target_part="";mechanical_target_confirmed=false
				var labels=["本体 %d/%d"%[int(enemy.hp),int(enemy.max_hp)]];var actions=["mechanical:body"]
				for key in game.Mechanical.part_keys(enemy):
					if game.Mechanical.valid_part(enemy,key):labels.append("%s %d/%d"%[game.Mechanical.part_name(enemy,false,key),game.Mechanical.part_hp(enemy,key),game.Mechanical.part_max(enemy,key)]);actions.append("mechanical:part:"+key)
				_open_menu("mechanical_part",labels,actions,Vector2(44,36));return
			var part=mechanical_target_part;mechanical_target_confirmed=false
			_play_combat(game.selected_id,id,part);return
		mechanical_target_confirmed=false;mechanical_target_part=""
	if view=="field_notes":field_notes.accept();return
	if view=="battle" and ui_mode in ["inspect","move"] and not busy and not batch_running and menu_items.is_empty():
		var enemy=game.unit_at(game.cursor)
		if enemy.get("side","")=="enemy":
			game.selected_id="";status_id=str(enemy.id);ui_mode="inspect";queue_redraw();return
	if recruitment_paused():return
	if view=="story_intro":story_intro.accept();return
	if view=="prologue_scene":prologue_scene.accept();return
	if equipment_screen!=null and equipment_screen.active():equipment_screen.accept();return
	if view in ["journal","journal_confirm"]:journey.accept();return
	if view in ["victory","defeat"] and result_sequence_running:return
	if view in ["victory","defeat"] and game.Training.active(game) and menu_items.is_empty():
		var labels=["返回营地","保存进度","返回标题"];var actions=["training:leave","new:save","title"]
		if view=="defeat":labels.push_front("重试演习");actions.push_front("retry")
		_open_menu("training_result",labels,actions,Vector2(44,124));return
	if view=="reward" and training_reward_open:
		training_reward_open=false;view="victory";return
	if view=="ending":
		if not menu_items.is_empty():
			var action=str(menu_actions[menu_selected]);var context=menu_context;_clear_menu();_menu_action(action,context);return
		if ending_index+1<ending_pages.size():
			ending_index+=1;game.flags.ending_index=ending_index;game.save_game()
		else:
			game.flags.ending_done=true;game.save_game();_open_menu("ending",["重看结局","返回标题"],["new:replay_ending","title"],Vector2(48,164))
		return
	if view=="plot":_advance_plot();return
	if view=="overview":
		held_direction=Vector2i.ZERO;overview_mouse_drag=false;view="world";return
	if view=="chapter_end" and menu_items.is_empty():
		var entries=["返回世界地图","保存进度","返回标题"]
		var actions=["new:world","new:save","title"]
		if game.chapter==1 and game.flags.get("chapter1_complete",false):
			entries.push_front("开始第二章");actions.push_front("new:chapter2")
		if game.chapter==4 and game.flags.get("chapter4_closed",false):
			entries.push_front("开始第五章");actions.push_front("new:chapter5")
		if game.chapter==3 and game.flags.get("chapter3_complete",false):
			entries.push_front("开始第四章");actions.push_front("new:chapter4")
		if game.chapter==2 and game.flags.get("chapter2_complete",false):
			entries.push_front("开始第三章");actions.push_front("new:chapter3")
		_open_menu("chapter_end",entries,actions,Vector2(44,120));return
	if view=="title":
		if title_selected==0:_new_game()
		else:journey.open("load")
		return
	if view=="world" and menu_items.is_empty() and not busy:
		var entries: Array=[];var actions: Array=[]
		if game.world_has_battle(game.world_node):entries.append("进入战场");actions.append("new:battle")
		else:entries.append("进入据点");actions.append("new:hub")
		for n in game.world_neighbors():entries.append("前往"+str(world.nodes[str(n)].name_zh));actions.append("travel:"+str(n))
		entries.append("部队整备");actions.append("new:camp")
		if game.can_switch_route():entries.append("切换队伍");actions.append("new:switch")
		_open_menu("world_routes",entries,actions,Vector2(24,56));return
	super._accept()

func _direction(direction: Vector2i) -> void:
	if view=="battle" and ui_mode=="target" and menu_items.is_empty():mechanical_target_confirmed=false;mechanical_target_part=""
	if view=="field_notes":field_notes.direction(direction);return
	if recruitment_paused():return
	if view=="battle" and ui_mode=="map_target" and not busy:
		var actor=game.find_unit(game.selected_id);var spec=game.MapSkills.profile(actor)
		if spec.get("male",false):map_facing=direction
		elif game.in_bounds(game.cursor+direction):game.cursor+=direction;_focus_battle(game.cursor)
		_refresh_map_forecast();queue_redraw();return
	if view=="story_intro":return
	if prologue_scene!=null and prologue_scene.active:return
	if equipment_screen!=null and equipment_screen.active():equipment_screen.direction(direction);return
	if view in ["journal","journal_confirm"]:journey.direction(direction);return
	if view=="overview":
		_overview_pan_pixels(-Vector2(direction)*24);return
	if view=="plot" or view=="chapter_end":
		if not menu_items.is_empty():super._direction(direction)
		return
	if view=="world" and menu_items.is_empty() and not busy:
		var candidates=[]
		for n in game.world_neighbors():
			var cells=_oriented_route(n)
			if cells.size()<2:continue
			var d=Vector2(cells[1][0]-cells[0][0],cells[1][1]-cells[0][1])
			if d.dot(Vector2(direction))>0:candidates.append(n)
		if candidates.size()==1:_travel(int(candidates[0]))
		elif candidates.size()>1:_open_menu("fork",candidates.map(func(n):return world.nodes[str(n)].name_zh),candidates.map(func(n):return "travel:"+str(n)),Vector2(32,64))
		elif game.chapter==1 and game.world_node==3 and direction==Vector2i.RIGHT and game.stage_cleared(102) and not game.flags.get("grain_shared",false):
			await play_pages([{"speaker":"胡纳普","text":"先回丘堡粮站，把粮送回雪原村。再往东去南岗押送所。"}],"world")
		else:_notice("这个方向没有开放道路")
		return
	super._direction(direction)

func _oriented_route(node: int) -> Array:
	var r=game.route_between(game.world_node,node)
	if r.is_empty():return []
	var cells: Array=r.cells.duplicate(true)
	if r.a!=str(world.nodes[str(game.world_node)].id):cells.reverse()
	return cells
func _travel(node: int) -> void:
	if not node in game.world_neighbors() or busy:return
	world_path=_oriented_route(node);world_destination=node;world_step=0.0;busy=true
	if instant_mode:
		world_actor=Vector2(world_path[-1][0],world_path[-1][1])*16;game.travel_to(node);world_path=[];busy=false;game.save_game()

func _menu_action(action: String,context: String) -> void:
	if context=="mechanical_part":
		mechanical_target_part=action.trim_prefix("mechanical:part:") if action.begins_with("mechanical:part:") else (game.Mechanical.part_key(game.find_unit(mechanical_target_id)) if action=="mechanical:part" else "")
		mechanical_target_confirmed=true;_clear_menu();ui_mode="target";queue_redraw();return
	if action=="new:rewind":
		var reason=game.Rewind.reason(game)
		if not reason.is_empty():_open_system_menu();_notice(reason,3.0);return
		_open_menu("rewind_confirm",["确认回溯（第%d回合初）" % (int(game.turn)-1),"取消"],["new:rewind_commit","new:rewind_cancel"],Vector2(32,88))
		_notice("回到上回合我方尚未行动时",4.0);return
	if action=="new:rewind_cancel":_open_system_menu();return
	if action=="new:rewind_commit":
		if busy or batch_running or view!="battle":return
		if not game.Rewind.reason(game).is_empty():_notice(game.Rewind.reason(game),3.0);return
		if not game.Rewind.commit(game):_notice("保存失败，回溯未生效且不消耗次数",3.0);return
		_clear_menu();ui_mode="inspect";status_id="";held_direction=Vector2i.ZERO
		if hero_map_animation!=null:hero_map_animation.forecast={}
		phase_banner="我方回合";phase_time=1.2;_focus_battle(game.cursor,true);_play_phase_music()
		await _play_story_events()
		_notice("已回到第%d回合初 · 剩余%d次" % [int(game.turn),game.Rewind.remaining(game)],3.0);return
	if action=="new:tasks":field_notes.open_tasks();return
	if action=="map:choose":_choose_map_skill();return
	if action=="training:open":
		var labels=["收益与次数"];var actions=["training:rules"]
		for choice in game.Training.choices(game):
			labels.append(str(choice.label));actions.append("training:detail:"+str(choice.id))
		labels.append("返回整备");actions.append("new:camp")
		_open_menu("training_choices",labels,actions,Vector2(24,64));return
	if action=="training:rules":
		await play_pages(game.Training.rules_pages(),game.mode,"",false)
		_menu_action("training:open","training_choices");return
	if action.begins_with("training:detail:"):
		var id=int(action.trim_prefix("training:detail:"))
		var choices=game.Training.choices(game).filter(func(c):return int(c.id)==id)
		if choices.is_empty():_open_camp_menu();return
		await play_pages([{"speaker":"战场提示","text":str(choices[0].detail)}],game.mode,"",false)
		var labels=["返回"];var actions=["training:open"]
		if choices[0].enabled:labels.push_front("开始演习");actions.push_front("training:start:"+str(id))
		_open_menu("training_confirm",labels,actions,Vector2(48,92));return
	if action.begins_with("training:start:"):
		if game.Training.start(game,int(action.trim_prefix("training:start:"))):_begin_existing_battle()
		else:_notice("当前无法开始演习");_open_camp_menu()
		return
	if action=="training:leave":
		if game.Training.leave(game):
			game.save_game();_resume_journey()
		return
	if action=="cover:choose":
		var labels=[];var actions=[]
		for target in game.cover_targets(game.find_unit(game.selected_id)):
			labels.append("保护"+str(target.name_zh));actions.append("cover:target:"+str(target.id))
		labels.append("返回");actions.append("cover:cancel")
		_open_menu("cover_targets",labels,actions,Vector2(40,64));return
	if action.begins_with("cover:target:"):
		var id=action.trim_prefix("cover:target:");var target=game.find_unit(id)
		if not game.cover_targets(game.find_unit(game.selected_id)).any(func(u):return str(u.id)==id):
			_notice("只能掩护相邻且本回合已行动的队友");_unit_action_menu();return
		_open_menu("cover_confirm",["确认掩护"+str(target.name_zh),"返回"],["cover:commit:"+id,"cover:cancel"],Vector2(48,92));return
	if action.begins_with("cover:commit:"):
		if game.begin_cover(action.trim_prefix("cover:commit:")):
			ui_mode="inspect";game.save_game();_notice("掩护就位 · 保持邻接",2.0);_finish_turn_action()
		else:_notice("目标需相邻且本回合已行动");_unit_action_menu()
		return
	if action=="cover:cancel":_unit_action_menu();return
	if action=="tactics:unit_info":
		var actor=game.find_unit(game.selected_id);var pages=[]
		if game.Cover.eligible(actor):pages.append({"speaker":"战场提示","text":"掩护：放弃攻击，保护一名相邻且本回合已行动的队友至下次己方回合。首次命中时分担一半伤害；掩护者生命不足时，余量仍由原目标承担。"})
		var detail=game.Knockback.description(game,actor)
		if not detail.is_empty():pages.append({"speaker":"战场提示","text":detail})
		if not pages.is_empty():await play_pages(pages,"battle","",false)
		_unit_action_menu();return
	if action.begins_with("travel:"):_travel(int(action.get_slice(":",1)));return
	if action.begins_with("interact:"):
		var id=action.substr(9)
		var options=game.interactions_for(game.find_unit(game.selected_id)).filter(func(o):return str(o.id)==id)
		if not options.is_empty() and options[0].get("kind","")=="breakable":
			await play_pages([{"speaker":"战场提示","text":str(options[0].confirm_text)}],"battle","",false)
			_open_menu("breakable_confirm",["确认破坏","返回"],["breakable:commit:"+id,"cover:cancel"],Vector2(48,92));return
		if game.interact(action.substr(9)):ui_mode="inspect";await _play_story_events();_finish_turn_action()
		elif not game.story_events.is_empty():await _play_story_events()
		return
	if action.begins_with("breakable:commit:"):
		if game.interact(action.trim_prefix("breakable:commit:")):
			ui_mode="inspect";game.save_game();await _play_story_events();_finish_turn_action()
		else:_unit_action_menu()
		return
	if action.begins_with("hub:"):hub_controller.action(action.substr(4));return
	match action:
		"new:replay_ending":
			game.flags.ending_index=0;_start_ending()
		"new:chapter5":
			if game.begin_chapter_five():
				busy=false;batch_running=false;ui_mode="inspect";_continue_world()
		"new:chapter4":
			if game.begin_chapter_four():
				busy=false;batch_running=false;ui_mode="inspect";_continue_world()
		"new:chapter3":
			if game.begin_chapter_three():
				busy=false;batch_running=false;ui_mode="inspect";hub_controller.enter_room("H30")
		"new:switch":
			if game.switch_route():_continue_world();_notice("已切换为"+("东队 · 艾琳" if game.route=="celica" else "西队 · 胡纳普"))
		"new:focus_exit":
			_clear_menu();ui_mode="inspect";var marker=game.exit_marker()
			if not marker.is_empty():game.cursor=Vector2i(marker.position[0],marker.position[1]);_focus_battle(game.cursor,true)
		"new:focus_boss":
			_clear_menu();ui_mode="inspect";var boss=game.find_unit(str(game.battle_data.boss_id))
			if not boss.is_empty() and int(boss.hp)>0:game.cursor=game.pos(boss);_focus_battle(game.cursor,true)
		"new:chapter2":
			if game.begin_chapter_two():
				busy=false;batch_running=false;ui_mode="inspect";held_direction=Vector2i.ZERO
				hub_controller.enter_room("H21")
				await play_pages(preload("res://core/late_dialogue.gd").pages(game,preload("res://core/late_dialogue.gd").lines("chapter2","开场")),"hub")
		"new:battle":_enter_battle(game.stage_for_node(game.world_node))
		"new:hub":hub_controller.enter_world()
		"new:world":_continue_world()
		"new:camp":_open_camp_menu()
		"new:equipment":
			await play_pages([
				{"speaker":"提示","text":"每人携带一件装备：武器、盾或戒指共用一个位置。职业相容时自动生效；空手仍可使用职业的普通武器。"},
				{"speaker":"提示","text":"铜、铁级剑枪弓供对应职业使用。法器只增强已学会的攻击法术，不改变治疗、射程或生命消耗。"},
				{"speaker":"提示","text":"在部队整备中选择交换装备或装备行囊，可交换、存放和领取。战中只能与相邻队员交换，发起者会结束行动。"},
				{"speaker":"提示","text":"状态页底部显示当前装备；左右方向键切换本队成员。装备没有耐久，不必另按装备按钮。"}],view)
		"new:prepare":
			if game.return_to_preparation():_continue_world();_notice("已重置本战，保留此前进度")
		"new:save","save":journey.open("save")
		"new:battle_title":
			# Resume the current battle instead of silently discarding this turn.
			if game.save_game():_show_title()
			else:_notice("保存失败，仍停留在当前战场",3.0)
		"new:goal":
			var text=str(game.battle_data.goal)
			if not game.exit_marker().is_empty():text+="\n出口有旗标。"+("菜单" if get_meta("phone",false) else "S菜单")+"可定位出口与首领。"
			else:text+="\n首领有橙色旗标。"+("菜单" if get_meta("phone",false) else "S菜单")+"可定位首领。"
			if game.battle_data.code=="M15":text+="\n科兰第6回合半血撤离，最晚第8回合；沿东侧栈道尽头封住北门退路。"
			var pages=[{"speaker":"战场提示","text":text}]
			if game.stage_id==105:
				pages.append({"speaker":"战场提示","text":"至少开门解救一队劳工，并让其存活，再击败或劝降科兰即可获胜。劳工不必走到出口。两队劳工都开门解救且存活时，本队全体正式成员战后额外获得20经验，含未出阵成员；满级除外。"})
				pages.append({"speaker":"战场提示","text":"开门后，劳工会在我方阶段结束时自动移动。他们会避开敌军能攻击到的路线；若仍停在原地，请清除沿途敌人，并让出通路。"})
			if game.stage_id>=200:
				for status in game.objective_status():pages.append({"speaker":"战场提示","text":status})
			for note in game.battle_data.get("tactical_notes",[]):pages.append({"speaker":"战场提示","text":str(note)})
			await play_pages(pages,"battle")
		"new:overview":
			overview_zoom=1;overview_center=Vector2(0.5,0.5);overview_mouse_drag=false;held_direction=Vector2i.ZERO;view="overview"
		_:super._menu_action(action,context)

func _draw_reward() -> void:
	var names:Array[String]=[]
	for id in reward.get("learned",[]):
		var spell=Items.spell(int(id));var label=str(spell.get("name_zh",""))
		if not label.is_empty() and not names.has(label):names.append(label)
	if not reward.get("leveled",false) or names.is_empty():
		presentation_audit.erase("learned_spells");super._draw_reward();return
	var unit=game.find_unit(str(reward.unit))
	if unit.is_empty():unit=game.roster.get(str(reward.unit),{})
	_panel(Rect2(20,4,216,232))
	_center_text("连续升级 ×%d"%int(reward.levels_gained) if int(reward.get("levels_gained",0))>1 else "等级提升",Rect2(30,16,196,18))
	_center_text("%s 等级%d升至%d" % [str(unit.name_zh),int(reward.get("level_before",unit.level)),int(unit.level)],Rect2(30,40,196,14))
	_center_text("经验%d +%d 剩余%d" % [int(reward.get("exp_before",0)),int(reward.gain),int(reward.get("exp_after",unit.get("exp",0)))],Rect2(30,60,196,12))
	var progress=1.0 if instant_mode else clampf(reward_elapsed*60.0/maxf(1.0,float(reward.gain)),0.0,1.0)
	var displayed=int(reward.get("exp_before",0))+int(roundf(float(reward.gain)*progress))
	displayed=displayed%100
	_draw_exp_progress(displayed,Vector2(30,78),196)
	var rows=[]
	var stats=[["生命","hp",int(unit.max_hp)],["攻击","strength",int(unit.strength)],["技巧","skill",int(unit.skill)],["速度","speed",int(unit.speed)],["幸运","luck",int(unit.luck)],["物防","defence",int(unit.defence)]]
	for i in range(stats.size()):
		var x=34+100*(i%2);var y=96+18*int(i/2);var stat=stats[i]
		_text(str(stat[0]),Vector2(x,y));_text(str(stat[2]),Vector2(x+40,y))
		var gain=int(reward.growths.get(str(stat[1]),0))
		if gain>0:_text("+%d" % gain,Vector2(x+66,y),Color(.8,1,.8))
		rows.append(Rect2(x,y,82,12))
	var learned_lines=_wrapped_lines("学会："+"、".join(names),188);var learned_bounds=[]
	for i in range(learned_lines.size()):
		var rect=Rect2(34,158+i*16,188,14);_center_text(learned_lines[i],rect,Color(.98,.94,.8));learned_bounds.append(rect)
	_center_text("确认继续",Rect2(30,210,196,16))
	presentation_audit.learned_spells={"names":names,"lines":learned_lines,"bounds":learned_bounds,"stats":rows,"panel":Rect2(20,4,216,232)}

func play_victory_rewards() -> void:
	for record in game.victory_rewards:
		if not record.get("leveled",false):continue
		reward=record.duplicate(true);reward_elapsed=0.0;training_reward_open=true;view="reward";busy=false
		audio.play_jingle("levelup")
		while training_reward_open:await get_tree().process_frame
	view="victory"

func _support_experience_feedback(result: Dictionary) -> bool:
	var receipt=result.get("reward",{})
	if receipt.is_empty() or int(receipt.get("gain",0))<=0:return false
	reward=receipt;reward_elapsed=0.0;reward_dismissed=false;busy=false;view="reward"
	if bool(reward.leveled):audio.play_jingle("levelup")
	game.save_game();return true

func _unit_action_menu() -> void:
	mechanical_target_confirmed=false;mechanical_target_part=""
	super._unit_action_menu()
	var actor=game.find_unit(game.selected_id)
	if hero_map_animation!=null:hero_map_animation.forecast={}
	if game.MapSkills.eligible(actor):
		var spec=game.MapSkills.profile(actor);var at=mini(1,menu_items.size())
		menu_items.insert(at,"MAP "+str(spec.name)+" "+str(3-int(spec.tier))+"/3")
		menu_actions.insert(at,"map:choose")
	if not game.cover_targets(actor).is_empty():
		var cover_index=menu_actions.find("attack")+1
		menu_items.insert(cover_index,"掩护");menu_actions.insert(cover_index,"cover:choose")
	if game.Cover.eligible(actor) or not game.Knockback.description(game,actor).is_empty():
		menu_items.append("战术说明");menu_actions.append("tactics:unit_info")
	var options=game.interactions_for(game.find_unit(game.selected_id))
	for o in options:menu_items.push_front(str(o.label));menu_actions.push_front("interact:"+str(o.id))
	var priority := ["wait"]
	if game.MapSkills.Healing.eligible(actor):
		for id in Items.spells(actor):
			if str(Items.spell(id).get("action", "")) not in ["recover", "physic", "fortify"]:
				continue
			if game.support_targets(actor, id).any(func(target): return int(target.hp) < int(target.max_hp)):
				priority.append("magic")
				break
	priority.append("attack")
	for action in priority:
		var index := menu_actions.find(action)
		if index <= 0:
			continue
		var label = menu_items.pop_at(index)
		menu_actions.remove_at(index)
		menu_items.push_front(label)
		menu_actions.push_front(action)

func _choose_map_skill()->void:
	var actor=game.find_unit(game.selected_id);var spec=game.MapSkills.profile(actor)
	if spec.is_empty():return
	if int(spec.tier)>=3:_notice("本场MAP三次额度已用尽");_unit_action_menu();return
	if int(actor.hp)<=int(spec.cost):_notice("支付后至少需要保留1HP");_unit_action_menu();return
	_clear_menu();ui_mode="map_target";held_direction=Vector2i.ZERO
	game.cursor=game.pos(actor);map_facing=Vector2i.RIGHT
	var support=bool(spec.get("support",false))
	var candidates=game.living("player" if support else "enemy").filter(func(u):return not u.get("event_object",false) and not u.get("hidden",false))
	if support:candidates=candidates.filter(func(u):return game.MapSkills.Healing.preview(game,str(actor.id),game.pos(u)).get("valid",false))
	candidates.sort_custom(func(a,b):return (game.pos(a)-game.pos(actor)).length_squared()<(game.pos(b)-game.pos(actor)).length_squared())
	if not candidates.is_empty():
		var delta=game.pos(candidates[0])-game.pos(actor)
		if spec.male:map_facing=Vector2i(signi(delta.x),0) if absi(delta.x)>=absi(delta.y) else Vector2i(0,signi(delta.y))
		elif absi(delta.x)+absi(delta.y)<=int(spec.reach):game.cursor=game.pos(candidates[0])
	_refresh_map_forecast();_focus_battle(game.cursor);queue_redraw()

func _refresh_map_forecast()->void:
	hero_map_animation.forecast=game.MapSkills.preview(game,game.selected_id,game.cursor,map_facing)
	player_range_key=""

func _battle_accept()->void:
	if ui_mode=="map_target":
		if not busy:_play_map_skill()
		return
	super._battle_accept()

func _play_map_skill()->void:
	var result=game.MapSkills.apply(game,game.selected_id,game.cursor,map_facing)
	if not result.get("valid",false):_notice(str(result.get("reason","无法释放MAP")));_refresh_map_forecast();return
	busy=true;held_direction=Vector2i.ZERO;_clear_menu();ui_mode="whole_capture";notice_time=0.0;phase_time=0.0
	# Cost, uses, damage, loot and one action's EXP are checkpointed together.
	game.save_game()
	await hero_map_animation.play(result)
	ui_mode="inspect";reward=result.reward
	await _resolve_pending_loot();await _play_story_events();busy=false
	if not reward.is_empty() and reward.get("leveled",false):
		view="reward";reward_elapsed=0.0;reward_dismissed=false;audio.play_jingle("levelup")
	else:
		if not reward.is_empty():_notice(str(result.name)+" · 经验+"+str(int(reward.gain)),.8)
		_finish_turn_action()
	queue_redraw()

func _draw_map_skill_ranges()->void:
	if hero_map_animation!=null and (hero_map_animation.active or ui_mode=="map_target"):hero_map_animation.draw_ranges()

func _draw_map_forecast()->void:
	var value=hero_map_animation.forecast
	if value.is_empty():return
	if value.get("support",false):_draw_healing_map_forecast(value);return
	var bounds=_visible_native_rect();var width=minf(224,bounds.size.x-16)
	var rows=[]
	var actor=game.find_unit(game.selected_id)
	rows.append("HP "+str(int(actor.hp))+" > "+str(int(actor.hp)-int(value.cost))+"  额外威力+"+str(int(value.power)))
	var damages=value.targets.map(func(t):return int(t.damage))
	if damages.is_empty():rows.append(str(value.get("reason","选择目标")))
	else:
		rows.append("目标"+str(damages.size())+"名  伤害"+str(damages.min())+("~"+str(damages.max()) if damages.min()!=damages.max() else "")+(" · 中心+4" if value.magic and value.advanced else ""))
	if int(value.get("reflection_damage",0))>0:rows.append("反伤%dHP · 结算后HP%d"%[int(value.reflection_damage),int(value.hp_after_reflection)])
	if int(value.tier)==2:rows.append("本次后虚脱：移动-2 伤害-25%")
	rows.append("方向选"+("朝向" if value.male else "落点")+" · 确认释放／返回")
	var height=44+rows.size()*12
	var rect=Rect2(Vector2(bounds.get_center().x-width/2,bounds.end.y-height-5),Vector2(width,height))
	_panel(rect)
	_center_text(str(value.name)+" 第"+str(int(value.tier)+1)+"/3次",Rect2(rect.position+Vector2(12,10),Vector2(width-24,14)))
	for i in range(rows.size()):_center_text(str(rows[i]),Rect2(rect.position+Vector2(12,31+i*12),Vector2(width-24,10)),Color(1,.8,.6) if i==2 and int(value.tier)==2 else Color(.8,.88,.92))
	presentation_audit.hero_map_forecast={"panel":rect,"rows":rows,"valid":value.valid,"target_count":value.targets.size()}

func _draw_healing_map_forecast(value:Dictionary)->void:
	var actor=game.find_unit(game.selected_id);var bounds=_visible_native_rect();var width=minf(224,bounds.size.x-16)
	var rows=["HP "+str(int(actor.hp))+" > "+str(int(actor.hp)-int(value.cost))+" · 最远"+str(value.reach)+"格／对单"]
	if value.targets.is_empty():rows.append(str(value.get("reason","请选择友军")))
	else:
		var hit=value.targets[0]
		rows.append(str(hit.unit.name_zh)+" 生命 "+str(hit.hp_before)+" > "+str(hit.hp_after)+"（+"+str(hit.heal)+"）")
	rows.append("强身：物防+2，持续2回合")
	if int(value.tier)==2:rows.append("本次后移动-2，至下个己方回合结束")
	rows.append("方向选友军 · 确认释放／返回")
	var height=48+rows.size()*14
	var rect=Rect2(Vector2(bounds.get_center().x-width/2,bounds.end.y-height-5),Vector2(width,height))
	_panel(rect);_center_text(str(value.name)+" 第"+str(int(value.tier)+1)+"/3次",Rect2(rect.position+Vector2(12,10),Vector2(width-24,14)))
	for i in range(rows.size()):_center_text(str(rows[i]),Rect2(rect.position+Vector2(12,31+i*14),Vector2(width-24,12)),Color("a9dfb6") if i==2 else Color(.8,.88,.92))
	presentation_audit.hero_map_forecast={"panel":rect,"rows":rows,"valid":value.valid,"target_count":value.targets.size(),"support":true}

func _open_system_menu() -> void:
	if view=="field_notes":return
	if equipment_screen!=null and equipment_screen.active():return
	if view in ["plot","title","journal","journal_confirm"]:return
	# Leaving an uncommitted action must roll back its tentative movement before
	# a save/retry/system command can persist a free extra move.
	if view=="battle" and not busy and not batch_running and not game.selected_id.is_empty() and ui_mode in ["action","move","target","support_target","warp","map_target"]:
		game.cancel_move();ui_mode="inspect";_clear_menu()
		if hero_map_animation!=null:hero_map_animation.forecast={}
	if view=="world" and not busy and game.can_switch_route():
		_open_menu("world_system",["部队整备","当前任务","切换队伍","世界全图","保存进度","返回标题"],["new:camp","new:tasks","new:switch","new:overview","new:save","title"],Vector2(40,56));return
	if view=="world" and not busy:
		_open_menu("world_system",["部队整备","当前任务","世界全图","保存进度","返回标题"],["new:camp","new:tasks","new:overview","new:save","title"],Vector2(48,64));return
	super._open_system_menu()
	if view=="battle" and menu_context=="system" and not menu_items.is_empty():
		var save_index=menu_actions.find("save")
		if save_index>=0:menu_actions.remove_at(save_index);menu_items.remove_at(save_index)
		var end_index=menu_actions.find("end_turn")
		if end_index>=0:menu_items[end_index]="结束回合（第%d回合）" % game.turn
		menu_items.insert(1,"回溯到上回合（剩余%d次）" % game.Rewind.remaining(game));menu_actions.insert(1,"new:rewind")
		menu_items.append("战场目标");menu_actions.append("new:goal")
		if not game.exit_marker().is_empty():menu_items.append("定位出口或目的地");menu_actions.append("new:focus_exit")
		var boss=game.find_unit(str(game.battle_data.boss_id))
		if not boss.is_empty() and int(boss.hp)>0:menu_items.append("定位首领："+str(boss.name_zh));menu_actions.append("new:focus_boss")
		menu_items.append("返回整备（重置本战）");menu_actions.append("new:prepare")
		if game.Training.active(game):
			menu_items[-1]="退出演习（无收益）";menu_actions[-1]="training:leave"
		menu_items.append("保存并返回主菜单");menu_actions.append("new:battle_title")

func _show_status() -> void:
	if view=="field_notes":return
	if equipment_screen!=null and equipment_screen.active():equipment_screen.toggle_details();return
	if view in ["plot","overview","chapter_end","title","journal","journal_confirm"]:return
	if view=="hub":
		camp_context="hub";_camp_members("status");return
	super._show_status()

func _open_camp_menu() -> void:
	super._open_camp_menu()
	var title_index=menu_actions.find("title")
	if title_index>=0:menu_items.remove_at(title_index);menu_actions.remove_at(title_index)
	var save_index=menu_actions.find("camp:save")
	if save_index>=0:menu_items.remove_at(save_index);menu_actions.remove_at(save_index)
	menu_items.insert(3,"装备说明");menu_actions.insert(3,"new:equipment")
	var ready=game.party.filter(func(id):return game.can_deploy(game.roster[id])).size()
	menu_items[0]="部队状态 · "+str(ready)+"/"+str(game.party.size())+"可出阵"
	if not game.Training.choices(game).is_empty():
		menu_items.append("战术补练 · 剩余%d次"%game.Training.remaining(game));menu_actions.append("training:open")
	_open_menu("camp",menu_items.duplicate(),menu_actions.duplicate(),Vector2(32,48))

func _camp_members(action: String, except_id: String = "") -> void:
	super._camp_members(action,except_id)
	if action!="status" or menu_context!="camp_members":return
	for i in range(menu_actions.size()):
		var id = str(menu_actions[i]).get_slice(":",2)
		var unit: Dictionary = game.roster.get(id,{})
		if game.HeroProfessions.advanced(unit):
			menu_items[i]=str(unit.name_zh)+" · "+game.HeroProfessions.name(unit)+(" 濒死" if game.is_dying(unit) else "")

func _camp_action(action: String) -> void:
	if action=="save":journey.open("save");return
	if action=="withdraw":
		var grouped=Items.inventory_groups(game.convoy.get(game.route,[]))
		if grouped.is_empty():_notice("仓库没有道具");return
		_open_menu("stored_items",grouped.map(func(g):return g.label),grouped.map(func(g):return "camp:withdraw_item:"+str(g.index)),Vector2(64,32))
		return
	if action.begins_with("withdraw_item:"):
		camp_first=action.get_slice(":",1);equipment_screen.open(int(camp_first));return
	# Old camp action strings also lead to a preview, never a direct transfer.
	if action.begins_with("withdraw_member:"):
		equipment_screen.open(int(camp_first))
		var index=equipment_screen.members.find(action.get_slice(":",1))
		if index>=0:equipment_screen.selected=index;equipment_screen.accept()
		return
	super._camp_action(action)

func _small_text_width(text: String) -> float:
	var width=0.0
	for ch in text:width+=float(small_font.get("glyphs",{}).get(ch,{}).get("advance",8))
	return width

func _highlighted_spell() -> int:
	if menu_context!="magic" or menu_selected<0 or menu_selected>=menu_actions.size():return -1
	return int(str(menu_actions[menu_selected]).get_slice(":",1))

func _magic_list_width() -> float:
	var width=112.0
	for item in menu_items:width=maxf(width,_text_width(str(item))+40)
	return width

func _magic_side_by_side() -> bool:
	return _magic_list_width()+216<=_visible_native_rect().size.x-16

func _menu_capacity() -> int:
	if menu_context!="magic" or _magic_side_by_side():return super._menu_capacity()
	var phone=bool(get_meta("phone",false));var available=_visible_native_rect().size.y-16
	for count in range(super._menu_capacity(),0,-1):
		var height=mini(count,menu_items.size())*_menu_row_height()+(24 if phone else 28)+108
		if menu_items.size()>count:height+=20 if phone else 16
		if height<=available:return count
	return 1

func _magic_layout() -> Dictionary:
	var phone=bool(get_meta("phone",false));var capacity=_menu_capacity();var side=_magic_side_by_side()
	var width=_magic_list_width() if side else maxf(224,_magic_list_width())
	var height=mini(capacity,menu_items.size())*_menu_row_height()+(24 if phone else 28)
	if menu_items.size()>capacity:height+=20 if phone else 16
	var total=Vector2(width+216,maxf(height,100)) if side else Vector2(width,height+108)
	var bounds=_visible_native_rect().grow(-8)
	var at=Vector2(bounds.get_center().x-total.x/2,clampf(menu_position.y,bounds.position.y,bounds.end.y-total.y)).round()
	var caster=game.find_unit(game.selected_id)
	if side and not caster.is_empty():at.y=bounds.position.y if _battle_cell_screen(game.pos(caster)).y>=bounds.get_center().y else bounds.end.y-total.y
	var detail=Rect2(at+Vector2(width+8,0),Vector2(208,100)) if side else Rect2(at+Vector2(0,height+8),Vector2(width,100))
	return {"menu":Rect2(at,Vector2(width,height)),"detail":detail,"side_by_side":side}

func _menu_rect() -> Rect2:
	return _magic_layout().menu if menu_context=="magic" else super._menu_rect()

func _draw_menu() -> void:
	super._draw_menu()
	if menu_context!="magic" or menu_items.is_empty():presentation_audit.erase("spell_info");return
	var caster=game.find_unit(game.selected_id);var id=_highlighted_spell()
	if caster.is_empty() or id<0:return
	var info=SpellInfo.describe(game,caster,id);var layout=_magic_layout();var rect:Rect2=layout.detail
	_panel(rect)
	_center_text(str(info.title),Rect2(rect.position+Vector2(12,12),Vector2(rect.size.x-24,12)),Color(.93,.87,.67))
	var lines=[info.effect,info.stats,info.range,info.availability]
	for i in range(lines.size()):
		_center_text(str(lines[i]),Rect2(rect.position+Vector2(12,28+i*16),Vector2(rect.size.x-24,12)),Color(.72,1,.78) if i>=2 else Color.WHITE)
	presentation_audit.spell_info=info;presentation_audit.spell_layout=layout

func _small_lines(text: String,width: float) -> Array[String]:
	var lines: Array[String]=[];var line=""
	for ch in text:
		if ch=="\n":lines.append(line);line="";continue
		if not line.is_empty() and _small_text_width(line+ch)>width:lines.append(line);line=""
		line+=ch
	if not line.is_empty():lines.append(line)
	return lines

func _small_text(text: String,at: Vector2,color: Color=Color.WHITE) -> void:
	var point=at.round()
	for ch in text:
		var glyph: Dictionary=small_font.glyphs.get(ch,{})
		if glyph.is_empty():
			layout_errors.append("Missing 8px glyph: "+ch);point.x+=8;continue
		var r=glyph.rect
		draw_texture_rect_region(_tex(small_font.path),Rect2(point,Vector2(8,8)),Rect2(r[0],r[1],8,8),color)
		point.x+=glyph.advance
	var bounds=Rect2(at.round(),Vector2(_small_text_width(text),8))
	text_checks.append({"text":text,"bounds":bounds,"font_px":8})
	if not safe_panels.is_empty() and not safe_panels[-1].encloses(bounds):layout_errors.append("Small text outside content-safe rectangle: "+text)

func _hub_caption_protected() -> Array:
	var protected=[]
	for object in hub_controller.objects:
		var at=hub_controller.ORIGIN+Vector2(object.position[0],object.position[1])*16
		if object.sprite=="actor":
			var sprite=_party_hub_sprite(object,graphics.village_sprites.get(str(int(object.source)),graphics.village_sprites["1"]))
			protected.append(Rect2(at-Vector2(sprite.tile_origin[0],sprite.tile_origin[1]),Vector2(sprite.frame_size[0],sprite.frame_size[1])/maxf(1.0,float(sprite.get("native_density",1)))).grow(4))
		else:
			var texture=_tex(str(object.get("sprite_path","res://assets/battle_tiles/modules/"+str(object.sprite)+".png")))
			protected.append(Rect2(at-Vector2(0,texture.get_height()-16),texture.get_size()).grow(4))
		if game.hub_position+hub_controller.facing==Vector2i(object.position[0],object.position[1]):protected.append(Rect2(at+Vector2(0,-12),Vector2(16,16)))
	var hero=_personal_hub_sprite(graphics.village_sprites["2" if game.route=="celica" else "1"])
	var hero_size=Vector2(hero.frame_size[0],hero.frame_size[1])/maxf(1.0,float(hero.get("native_density",1)));var origin=hub_controller.ORIGIN-Vector2(hero.tile_origin[0],hero.tile_origin[1])
	var hero_rect=Rect2(hub_controller.render_position+origin,hero_size)
	if hub_controller.motion_left>0:
		hero_rect=hero_rect.merge(Rect2(hub_controller.motion_origin+origin,hero_size)).merge(Rect2(hub_controller.motion_target+origin,hero_size))
	protected.append(hero_rect.grow(4))
	protected.append(Rect2(hub_controller.ORIGIN+Vector2(6,8)*16+Vector2(0,-6),Vector2(16,16)))
	return protected

func _draw_hub_caption(title: String,hint: String) -> void:
	if game.chapter==5 and menu_context=="fifth_selection" and not menu_items.is_empty():
		presentation_audit.hub_caption=Rect2();return
	# Full native 12px glyphs preserve strokes in complex Chinese place names.
	var limit=minf(280.0 if bool(get_meta("phone",false)) else 240.0,get_viewport_rect().size.x-40.0)
	var title_lines=_wrapped_lines(title,limit);var lines=_wrapped_lines(hint,limit)
	var widest=0.0
	for line in title_lines+lines:widest=maxf(widest,_text_width(line))
	var rect=Rect2(_visible_native_rect().position+Vector2(8,8),Vector2(widest+24,24+16*(title_lines.size()+lines.size())))
	if bool(get_meta("phone",false)):
		if phone_hub_caption_room!=hub_controller.room:phone_hub_caption=Rect2();phone_hub_caption_room=hub_controller.room
		var protected=_hub_caption_protected()
		var placed=HubCaption.place(rect.size,_visible_native_rect(),protected,phone_hub_caption)
		presentation_audit.hub_protected=protected
		if placed.has_area():rect=placed;phone_hub_caption=rect
		else:layout_errors.append("No unobstructed phone hub caption position")
	_panel(rect)
	for i in range(title_lines.size()):_center_text(title_lines[i],Rect2(rect.position+Vector2(12,12+i*16),Vector2(widest,12)),Color(.93,.87,.67))
	for i in range(lines.size()):_center_text(lines[i],Rect2(rect.position+Vector2(12,12+(title_lines.size()+i)*16),Vector2(widest,12)))
	presentation_audit.hub_caption=rect

func _continue_world() -> void:
	view="world";game.mode="world";busy=false;_clear_menu();ui_mode="inspect";held_direction=Vector2i.ZERO
	world_actor=Vector2(world.nodes[str(game.world_node)].position[0],world.nodes[str(game.world_node)].position[1])*16
	audio.play_world(1);game.save_game()

func _play_casualty_messages() -> void:
	if view!="combat":return
	var personal=[]
	for event in game.story_events:
		if event.get("kind","")!="new_story":continue
		var remaining=[]
		for page in event.get("pages",[]):
			if not str(page.get("casualty_id","")).is_empty():personal.append(page)
			else:remaining.append(page)
		event.pages=remaining
	if personal.is_empty():return
	game.story_events=game.story_events.filter(func(event):return event.get("kind","")!="new_story" or not event.get("pages",[]).is_empty())
	# A strike is not settled yet. Do not save an incomplete exchange or a
	# return-to-combat plot without its animation state. Normal settlement
	# owns persistence; the ordinary withdrawal notice remains queued.
	await play_pages(personal,"combat","",false)

func _play_prometheus_revival() -> void:
	var rows=[];var pending=[]
	for event in game.story_events:
		if event.get("key","")=="F44-REVIVE":rows.append_array(event.get("pages",[]))
		else:pending.append(event)
	game.story_events=pending
	if not rows.is_empty():await play_pages(rows,"combat","",false)

func _play_story_events() -> void:
	var was_busy=busy;busy=true
	while not game.story_events.is_empty():
		var event: Dictionary=game.story_events.pop_front()
		if game.stage_id==105 and not str(event.get("m15_scene","")).is_empty():
			m15_scene.start(event,view)
			while m15_scene.active:await get_tree().process_frame
		else:await play_pages(event.get("pages",[]),view,str(event.get("callback","")))
	busy=was_busy;game.save_game()

func _run_ai_unit(unit:Dictionary,gather:bool=false) -> void:
	# The turn/whisper must precede the real northbound move. ai_action() also
	# queues this for simulations, while the seen flag keeps playback singular.
	if int(unit.get("hp",0))>0 and not unit.get("acted",false) and game.M15Story.escaping(game,unit):
		game.M15Story.announce_escape(game)
		await _play_story_events()
	await super._run_ai_unit(unit,gather)

func play_pages(pages: Array,return_view: String,callback: String="",persist:bool=true) -> void:
	var previous_busy=busy;busy=true;held_direction=Vector2i.ZERO
	# Keep the successful invitation frame for the entire cue, even when
	# ordinary animation waits are accelerated. Do not leave busy latched.
	while recruitment_paused():await get_tree().process_frame
	plot_pages.clear()
	for page in pages:
		plot_pages.append_array(_paginate_plot(page))
	if plot_pages.is_empty():busy=previous_busy;return
	plot_index=0;plot_return=return_view;plot_callback=callback;plot_finished=false;dialogue_reveal=0.0
	plot_persistent=persist
	if persist:game.flags.active_plot={"pages":plot_pages,"index":0,"return":return_view,"callback":callback}
	view="plot"
	if persist:game.save_game()
	while not plot_finished:await get_tree().process_frame
	busy=previous_busy

func _resume_plot() -> void:
	plot_persistent=true
	var p: Dictionary=game.flags.active_plot
	plot_pages=PostbattleNpcs.refresh_saved_dialogue(game,p.pages);plot_index=int(p.index);plot_return=p["return"];plot_callback=p.get("callback","")
	plot_finished=false;dialogue_reveal=0.0;view="plot";_reflow_plot()

func _speaker_portrait(speaker: String,emotion: String="") -> Dictionary:
	if speaker in NARRATOR_SPEAKERS:return {}
	return Portraits.speaker(game,speaker,emotion)

func _unit_portrait(unit: Dictionary) -> Dictionary:
	if game.Mechanical.is_puppet(unit):return {"path":preload("res://core/mechanical_art.gd").portrait(unit)}
	return Portraits.unit(game,unit)

func _portrait(source_id: int) -> Dictionary:
	var face=Portraits.source(game,source_id)
	if not face.is_empty():return face
	return {} if source_id<=0 else Portraits.entry("east_infantry" if game.chapter==2 else "west_infantry")

func _plot_layout(speaker: String) -> Dictionary:
	var canvas=get_viewport_rect().size
	var panel=Rect2(-_canvas_offset().x+4,240+_footer_shift().y-96,canvas.x-8,92)
	var has_face=not _speaker_portrait(speaker).is_empty()
	var left=panel.position.x+(76.0 if has_face else 16.0)
	return {"panel":panel,"portrait":Rect2(panel.position+Vector2(16,28),Vector2(48,48)),
		"text":Rect2(left,panel.position.y+30,panel.end.x-20-left,48),"has_portrait":has_face}

func _paginate_plot(page: Dictionary) -> Array:
	# Pending and paused dialogue pages may come from an older journal.
	var speaker=str(page.get("speaker","旁白")).replace("提炼院","研究院");var out: Array=[]
	var emotion=Portraits.dialogue_emotion(page)
	var text=str(page.text).replace("\n","").replace("提炼院","研究院")
	var lines=_wrapped_lines(text,_plot_layout(speaker).text.size.x)
	for start in range(0,lines.size(),3):
		var chunk=page.duplicate(true)
		chunk.speaker=speaker;chunk.text="\n".join(lines.slice(start,mini(start+3,lines.size())))
		if not emotion.is_empty():chunk.emotion=emotion
		out.append(chunk)
	return out

func _reflow_plot() -> void:
	if plot_pages.is_empty() or plot_index>=plot_pages.size():return
	var rebuilt=plot_pages.slice(0,plot_index)
	for page in plot_pages.slice(plot_index):rebuilt.append_array(_paginate_plot(page))
	plot_pages=rebuilt
	dialogue_reveal=minf(dialogue_reveal,str(plot_pages[plot_index].text).length())
	if game.flags.has("active_plot"):game.flags.active_plot.pages=plot_pages
func _advance_plot() -> void:
	if plot_pages.is_empty():return
	var line=str(plot_pages[plot_index].text)
	if int(dialogue_reveal)<line.length():dialogue_reveal=line.length();return
	plot_index+=1;dialogue_reveal=0.0
	if plot_index<plot_pages.size():
		if plot_persistent:game.flags.active_plot.index=plot_index;game.save_game()
		return
	view=plot_return
	if plot_persistent:game.flags.erase("active_plot")
	plot_finished=true
	if plot_callback=="m15_next":m15_scene.dialogue_finished()
	elif not plot_callback.is_empty():hub_controller.finish_story(plot_callback)
	if plot_persistent:game.save_game()

func _draw() -> void:
	draw_set_transform(_canvas_offset())
	if m15_scene!=null and m15_scene.active and view in ["m15_scene","plot"]:
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear()
		m15_scene.draw()
		if view=="plot":_draw_plot()
		return
	if view=="field_notes":
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear();field_notes.draw();return
	if prologue_scene!=null and prologue_scene.active and view in ["prologue_scene","plot"]:
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear()
		prologue_scene.draw()
		if view=="plot":_draw_plot()
		return
	if view=="story_intro":
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear()
		story_intro.draw();return
	if equipment_screen!=null and equipment_screen.active():
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear()
		equipment_screen.draw();return
	if view in ["title","journal","journal_confirm"] and journey!=null:
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear()
		journey.draw();return
	if view in ["plot","overview","chapter_end"]:
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear()
		if view=="overview":_draw_overview();return
		if view=="chapter_end":_draw_chapter_end()
		elif plot_return=="hub":hub_controller.draw()
		elif plot_return=="combat":_draw_combat(false)
		elif plot_return in ["battle","victory","defeat"]:_draw_battle()
		else:_draw_world()
		if view=="plot":_draw_plot()
		if not menu_items.is_empty():_draw_menu()
		return
	super._draw()
	if journey!=null:journey.draw_saved()

func _draw_title() -> void:
	journey.draw()

func _draw_layers(layers: Array,columns: int,atlas: Texture2D,origin: Vector2,tint: Color=Color.WHITE,skip_cells: Dictionary={}) -> void:
	var bounds=_visible_native_rect().grow(16)
	for layer in layers:
		for y in range(layer.size()):
			if y*16+origin.y < bounds.position.y or y*16+origin.y >bounds.end.y:continue
			for x in range(layer[y].size()):
				if skip_cells.has(Vector2i(x,y)):continue
				if x*16+origin.x < bounds.position.x or x*16+origin.x >bounds.end.x:continue
				var id=layer[y][x]
				if id==null or int(id)<0:continue
				draw_texture_rect_region(atlas,Rect2(Vector2(x,y)*16+origin,Vector2(16,16)),Rect2(int(id)%columns*16,int(id)/columns*16,16,16),tint)

func _clamp_map_camera(camera: Vector2,map_pixels: Vector2) -> Vector2:
	var canvas=get_viewport_rect().size;var offset=_canvas_offset()
	for axis in range(2):
		if map_pixels[axis]<=canvas[axis]:camera[axis]=(map_pixels[axis]-NATIVE[axis])/2.0
		else:camera[axis]=clampf(camera[axis],offset[axis],map_pixels[axis]+offset[axis]-canvas[axis])
	return camera.round()

func _focus_battle(cell: Vector2i,force: bool=false) -> void:
	if game.battle_data.is_empty():return
	var pixel=Vector2(cell)*16;var bounds=_visible_native_rect()
	if force:battle_camera=pixel-Vector2(120,112)
	else:
		var local=pixel-battle_camera
		if local.x<bounds.position.x+48:battle_camera.x=pixel.x-bounds.position.x-48
		elif local.x>bounds.end.x-64:battle_camera.x=pixel.x-bounds.end.x+64
		if local.y<bounds.position.y+48:battle_camera.y=pixel.y-bounds.position.y-48
		elif local.y>bounds.end.y-64:battle_camera.y=pixel.y-bounds.end.y+64
	battle_camera=_clamp_map_camera(battle_camera,Vector2(game.battle_data.map.width,game.battle_data.map.height)*16)

func _draw_atlas_cell(atlas: Texture2D,id: int,at: Vector2,tint: Color=Color.WHITE) -> void:
	draw_texture_rect_region(atlas,Rect2(at,Vector2(16,16)),Rect2(id%32*16,id/32*16,16,16),tint)

func _draw_ocean(origin: Vector2) -> void:
	var bounds=_visible_native_rect();var atlas=_tex(world.atlas)
	for y in range(floori((bounds.position.y-origin.y)/16),ceili((bounds.end.y-origin.y)/16)):
		for x in range(floori((bounds.position.x-origin.x)/16),ceili((bounds.end.x-origin.x)/16)):
			_draw_atlas_cell(atlas,4+posmod(x+y,4),origin+Vector2(x,y)*16)

func _draw_nature_props(props: Array,origin: Vector2,tint: Color=Color.WHITE) -> void:
	for p in EnvironmentBorder.visible_props(props,nature_sprites,origin,_visible_native_rect()):
		var sprite: Dictionary=nature_sprites[str(p.key)]
		var at=Vector2(p.position[0],p.position[1])+origin
		var dimensions=p.get("size",sprite.size)
		var size=Vector2(dimensions[0],dimensions[1])
		if p.get("flip",false):size.x=-size.x
		draw_texture_rect(_tex(str(sprite.path)),Rect2(at,size),false,tint)

func _draw_surroundings(origin: Vector2,footprint: Vector2i,layout: Dictionary) -> void:
	var atlas=_tex("res://assets/battle_tiles/battle-tiles.png")
	var biome=str(layout.get("biome","grass"))
	var material=biome if biome in ["snow","salt","marsh"] else "cave" if biome=="rock" else "grass"
	var bounds=_visible_native_rect()
	for y in range(floori((bounds.position.y-origin.y)/16),ceili((bounds.end.y-origin.y)/16)):
		for x in range(floori((bounds.position.x-origin.x)/16),ceili((bounds.end.x-origin.x)/16)):
			if x>=0 and y>=0 and x<footprint.x and y<footprint.y:continue
			var at=origin+Vector2(x,y)*16
			var hash_value=(x*73856093)^(y*19349663)
			var variant=posmod(hash_value^(hash_value>>13),4)
			_draw_atlas_cell(atlas,int(battle_pack.base[material][variant]),at)
	_draw_nature_props(layout.get("props",[]),origin)

func _draw_hub_surroundings(room: String,origin: Vector2) -> void:
	if game.chapter>=4 and hub_controller.chapter2_rooms.has(room):
		_draw_surroundings(origin,Vector2i(14,9),{"biome":hub_controller.chapter2_rooms[room].get("biome_override","grass")});return
	var layout=hub_controller.climate_surroundings(room,nature_layouts.get("hubs",{}).get(room,{}))
	_draw_surroundings(origin,Vector2i(14,9),layout)

func _draw_natural_grove(room: String,name: String,origin: Vector2,rect: Rect2i) -> bool:
	for group in nature_layouts.get("hubs",{}).get(room,{}).get("groves",[]):
		if str(group.source_name)==name and Vector2(group.rect[0],group.rect[1])==Vector2(rect.position)*16:
			_draw_nature_props(group.props,origin);return true
	return false

func _draw_battle_surroundings(origin: Vector2,tint: Color=Color.WHITE) -> void:
	var surroundings=str(game.battle_data.get("surroundings",""))
	if surroundings=="sea":
		var bounds=_visible_native_rect();var atlas=_tex("res://assets/battle_tiles/battle-tiles.png")
		for y in range(floori((bounds.position.y-origin.y)/16),ceili((bounds.end.y-origin.y)/16)):
			for x in range(floori((bounds.position.x-origin.x)/16),ceili((bounds.end.x-origin.x)/16)):
				_draw_atlas_cell(atlas,int(battle_pack.base.sea[posmod((x*31)^(y*17),4)]),origin+Vector2(x,y)*16,tint)
		return
	_draw_surroundings(origin,Vector2i(game.battle_data.map.width,game.battle_data.map.height),game.battle_data.get("nature_layout",nature_layouts.get("battles",{}).get(str(game.battle_data.code),{})))

func _draw_art_props(props: Array,origin: Vector2,tint: Color=Color.WHITE) -> void:
	for prop in props:
		var tex=_tex(str(prop.path));var size=tex.get_size()
		if prop.has("size"):size=Vector2(prop.size[0],prop.size[1])
		var at=origin+Vector2(prop.position[0],prop.position[1]);var rect=Rect2(at,size)
		# Architecture remains visible while scrolling past a viewport edge.
		# Culling the entire keep until every pixel fits creates invisible walls.
		if not _visible_native_rect().intersects(rect):continue
		if prop.get("flip",false):rect.size.x=-rect.size.x
		draw_texture_rect(tex,rect,false,tint)

func _draw_map(map: Dictionary,atlas: Texture2D,origin: Vector2) -> void:
	if game.mode in ["battle","victory","defeat"] or view in ["battle","combat","reward","victory","defeat","loot","loot_confirm"]:
		var values=game.battle_data.get("map_tint",[1.0,1.0,1.0,1.0]);var tint=Color(values[0],values[1],values[2],values[3])
		_draw_battle_surroundings(origin,tint)
		_draw_layers(game.battle_data.art_layers,int(game.battle_data.get("art_columns",32)),_tex(str(game.battle_data.get("art_atlas","res://assets/battle_tiles/battle-tiles.png"))),origin,tint)
		_draw_nature_props(game.battle_data.get("natural_props",[]),origin,tint)
		_draw_art_props(game.VisitBuildings.props(game.battle_data),origin,tint)
		_draw_art_props(game.VisitBuildings.entrances(game.battle_data),origin,tint)
		presentation_audit.erase("spell_attack")
		if view=="battle" and menu_context=="magic" and not menu_items.is_empty():
			var caster=game.find_unit(game.selected_id);var spell_id=_highlighted_spell()
			if not caster.is_empty() and spell_id>=0:
				var cells=SpellInfo.attack_cells(game,caster,spell_id)
				for cell in cells:draw_rect(Rect2(_battle_cell_screen(cell),Vector2(16,16)),Color(.18,.85,.40,.30))
				presentation_audit.spell_attack=cells
		objective_badge_rect=Rect2()
		var marker=game.exit_marker()
		if not marker.is_empty():
			var at=Vector2(marker.position[0],marker.position[1])*16+origin
			_draw_camp_control_flag(at-Vector2(0,16),true,Color(.35,.85,.58))
			if _visible_native_rect().grow(32).has_point(at):
				var label=str(marker.label);var width=_small_text_width(label)+24
				var occupied=[Rect2(_battle_cell_screen(game.cursor)+Vector2(-6,-12),Vector2(28,36))]
				for actor in game.units:
					if int(actor.hp)>0 and actor.side!="evacuated" and not actor.get("hidden",false):
						var actor_at=moving_position-battle_camera if moving_id==str(actor.id) else Vector2(actor.position[0],actor.position[1])*16+origin
						occupied.append(Rect2(actor_at+Vector2(-10 if str(actor.id)=="medicine_wagon" else -4,-8),Vector2(36 if str(actor.id)=="medicine_wagon" else 24,28)))
				for offset in [Vector2(8-width/2,-44),Vector2(32,-12),Vector2(-width-16,-12),Vector2(8-width/2,32)]:
					var badge=Rect2(at+offset,Vector2(width,28))
					if not _visible_native_rect().grow(-4).encloses(badge) or occupied.any(func(rect):return badge.intersects(rect)):continue
					objective_badge_rect=badge;_panel(badge)
					_small_text(label,badge.position+Vector2(12,10),Color(.76,1.0,.82));break
		var boss=game.find_unit(str(game.battle_data.boss_id))
		if not boss.is_empty() and int(boss.hp)>0 and not boss.get("surrendered",false):
			var at=Vector2(boss.position[0],boss.position[1])*16+origin
			_draw_camp_control_flag(at+Vector2(12,-12),false,Color(1,.55,.28))
		for obj in game.battle_data.objects:
			# Visit entrances belong to the complete building artwork. This also
			# suppresses the old generic door and arrow in compatible old saves.
			if obj.get("kind","")=="visit":continue
			if obj.has("follows_unit"):
				var followed=game.find_unit(str(obj.follows_unit))
				if not followed.is_empty():obj.position=followed.position.duplicate()
			var at=Vector2(obj.position[0],obj.position[1])*16+origin
			var done=game.flags.quest.objects.get(str(obj.id),false)
			if game.stage_id==405 and game.flags.quest.wells.has(str(obj.id)):done=bool(game.flags.quest.wells[str(obj.id)])
			if game.stage_id in [406,411] and game.flags.quest.get("record_lost",false) and obj.id in ["observatory_record","black_register"]:
				draw_texture(_tex("res://assets/battle_tiles/modules/brazier.png"),at);continue
			if obj.kind=="control":
				_draw_camp_control_flag(at,done);continue
			if done:
				for cell in obj.get("open_art_cells",[]):
					_draw_atlas_cell(_tex(str(game.battle_data.get("art_atlas","res://assets/battle_tiles/battle-tiles.png"))),int(cell.base_tile),origin+Vector2(cell.position[0],cell.position[1])*16)
				_draw_art_props(obj.get("open_art_props",[]),origin)
			var name="open_jail" if done and obj.kind=="door" else "open_gate" if done and obj.kind=="rescue" else str(obj.sprite)
			var path=str(obj.get("open_sprite_path",obj.get("sprite_path","res://assets/battle_tiles/modules/"+name+".png"))) if done else str(obj.get("sprite_path","res://assets/battle_tiles/modules/"+name+".png"))
			var legacy_shelter=obj.kind=="shelter" and name=="clinic_door"
			if legacy_shelter:path="res://assets/battlefield-0.3.0/modules/tactical_house.png"
			var tex=_tex(path);var offset=Vector2(0,tex.get_height()-16)
			if obj.has("sprite_offset"):offset=-Vector2(obj.sprite_offset[0],obj.sprite_offset[1])
			if legacy_shelter or obj.kind in ["door","rescue"] or obj.get("persistent_visual",false) or not done:draw_texture(tex,at-offset)
		if game.stage_id>=200:
			for boat in game.event_boats():
				if int(boat.hp)<=0 or boat.get("arrived",false) or boat.get("waiting",false):continue
				var texture=_tex(str(game.battle_data.get("event_boat_sprite","res://assets/world_tiles/modules/galleon.png")))
				var at=origin+Vector2(boat.position[0],boat.position[1])*16
				draw_texture(texture,at-Vector2((texture.get_width()-16)/2,texture.get_height()-16))
		return
	super._draw_map(map,atlas,origin)

func _draw_camp_control_flag(at: Vector2,controlled: bool,marker_colour: Color=Color.TRANSPARENT) -> void:
	# Reuse the complete native flag and keep its wooden pole unchanged.
	# Only its cloth region is modulated; capture changes ownership colour,
	# never the opening's collision or the road beneath the flag.
	var texture=_tex("res://assets/battle_tiles/modules/white_flag.png")
	draw_texture(texture,at)
	var cloth=Rect2(7,3,5,8)
	var colour=marker_colour if marker_colour.a>0 else Color(.35,.65,1.0) if controlled else Color(1.0,.32,.25)
	draw_texture_rect_region(texture,Rect2(at+cloth.position,cloth.size),cloth,colour)

func _first_chapter_winter() -> bool:
	return game.chapter==1 and not game.flags.get("chapter1_complete",false)

func _world_uses_winter() -> bool:
	# Chapter two rewinds the same half-year: completed western progress is
	# retained in the save, but the western season follows this story time.
	return _first_chapter_winter() or (game.chapter==2 and not _second_chapter_blackday())

func _fourth_world_environment_active() -> bool:
	# Chapter five follows immediately: changing chapters does not thaw the highlands
	# or undo the already verified local protection. The finale has its own sky state.
	return game.chapter==4 or (game.chapter==5 and game.flags.get("chapter4_complete",false) and not game.flags.get("campaign_complete",false))

func _world_visual_data() -> Dictionary:
	if game.chapter==5:
		if chapter_five_world_environment.is_empty():chapter_five_world_environment=GameState.read_json("res://data/chapter5_world_environment.json")
		return chapter_five_world_environment
	if _fourth_world_environment_active():
		if chapter_four_world_environment.is_empty():chapter_four_world_environment=GameState.read_json("res://data/chapter4_world_environment.json")
		return chapter_four_world_environment
	if game.chapter==3:
		if chapter_three_world_environment.is_empty():chapter_three_world_environment=GameState.read_json("res://data/chapter3_world_environment.json")
		return chapter_three_world_environment
	if not _world_uses_winter():return world
	if chapter_one_world_climate.is_empty():
		chapter_one_world_climate=GameState.read_json("res://data/chapter1_world_climate.json")
	return chapter_one_world_climate

# Chapter two's eastern black day is display-only and follows the existing story flag.
func _second_chapter_blackday() -> bool:
	return game.chapter==2 and bool(game.flags.get("F22_confirmed",false))

func _world_has_eastern_blackday() -> bool:
	return _second_chapter_blackday() or game.chapter==3 or _fourth_world_environment_active() or (game.chapter==5 and not game.flags.get("campaign_complete",false))

func _second_chapter_world_tint(at: Vector2) -> Color:
	if not _world_has_eastern_blackday():return Color.WHITE
	# The old western passage lies outside the dimmed islands, beyond the local veil.
	var west_edge=lerpf(42.0,30.0,clampf((at.y-42.0)/8.0,0.0,1.0))
	var strength=smoothstep(west_edge,west_edge+3.0,at.x)*smoothstep(29.0,32.0,at.y)
	var tint=Color(.82,.86,.94)
	var beacon=1.0-smoothstep(2.0,7.0,at.distance_to(Vector2(51,42)))
	var harbor=1.0-smoothstep(2.0,6.0,at.distance_to(Vector2(49,34)))
	tint=tint.lerp(Color(.66,.72,.84),beacon).lerp(Color(.75,.8,.9),harbor)
	var result=Color.WHITE.lerp(tint,strength)
	if game.chapter in [3,5] or _fourth_world_environment_active():
		# The present-day eastern salt routes remain outside western protection.
		var salt_strength=smoothstep(31.5,35.5,at.x)*smoothstep(7.0 if game.chapter==5 or _fourth_world_environment_active() else 14.0,11.0 if game.chapter==5 or _fourth_world_environment_active() else 20.0,at.y)*(1.0-smoothstep(33.0,39.0,at.y))
		result=result.lerp(Color(.80,.84,.92),salt_strength)
	if (game.chapter==5 or _fourth_world_environment_active()) and game.flags.get("island_loop_safe",false):
		# Only the repaired shrine and nearby islands recover; the wider blackday remains.
		var radius=6.0 if game.flags.get("D42_done",false) else 3.0
		result=result.lerp(Color.WHITE,1.0-smoothstep(radius-1.5,radius,at.distance_to(Vector2(44,15))))
	if game.chapter==5 and game.flags.get("east_network_ready",false):
		# The extended local repair protects the palace approach and archive district.
		for site in [Vector2(40,11),Vector2(48,9)]:result=result.lerp(Color.WHITE,1.0-smoothstep(1.5,3.5,at.distance_to(site)))
	return result

func _draw_second_chapter_world_cell(atlas: Texture2D,id: int,origin: Vector2,cell: Vector2) -> void:
	var corners=[Vector2.ZERO,Vector2.RIGHT,Vector2.ONE,Vector2.DOWN]
	var vertices=PackedVector2Array();var colors=PackedColorArray();var uvs=PackedVector2Array()
	var source=Vector2(id%32,floori(id/32.0))*16.0
	for corner in corners:
		vertices.append(origin+(cell+corner)*16.0)
		colors.append(_second_chapter_world_tint(cell+corner-Vector2(.5,.5)))
		uvs.append((source+corner*16.0)/atlas.get_size())
	draw_polygon(vertices,colors,uvs,atlas)

func _draw_second_chapter_world(visual: Dictionary,origin: Vector2,skip_cells: Dictionary={}) -> void:
	var atlas=_tex(str(visual.atlas));var bounds=_visible_native_rect().grow(16)
	for layer_index in range(visual.layers.size()):
		var layer=visual.layers[layer_index]
		for y in range(layer.size()):
			if y*16+origin.y<bounds.position.y or y*16+origin.y>bounds.end.y:continue
			for x in range(layer[y].size()):
				if layer_index==visual.layers.size()-1 and skip_cells.has(Vector2i(x,y)):continue
				if x*16+origin.x<bounds.position.x or x*16+origin.x>bounds.end.x:continue
				if layer[y][x]==null or int(layer[y][x])<0:continue
				_draw_second_chapter_world_cell(atlas,int(layer[y][x]),origin,Vector2(x,y))
	for prop in visual.get("natural_props",[]):
		var cell=Vector2(prop.position[0],prop.position[1])/16.0
		_draw_nature_props([prop],origin,_second_chapter_world_tint(cell))

func _world_overview_texture() -> Texture2D:
	if game.chapter==5:
		var phase="clear" if game.flags.get("campaign_complete",false) else "network" if game.flags.get("east_network_ready",false) else "arrival"
		return _tex("res://assets/chapter5-environment-20261023/world/overview-"+phase+".png")
	if _fourth_world_environment_active():
		var phase="verified" if game.flags.get("D42_done",false) else "trial" if game.flags.get("island_loop_safe",false) else "before"
		return _tex("res://assets/chapter4-environment-20261023/world/overview-"+phase+".png")
	if game.chapter==3:return _tex(str(_world_visual_data().overview))
	if _world_uses_winter():return _tex(str(_world_visual_data().overview))
	if _second_chapter_blackday():return _tex("res://assets/chapter2-environment-20261023/world/overview-blackday.png")
	return OVERVIEW_IMAGE

func _draw_world() -> void:
	if camp_context=="hub" and view=="camp_status":hub_controller.draw();return
	var camera=world_actor-Vector2(120,96)
	camera=_clamp_map_camera(camera,Vector2(world.width,world.height)*16)
	var origin=-camera.round();_draw_ocean(origin)
	# A one-tile camp sits directly under the world leader. Its tent poles
	# were showing through the new sprite as extra hands/feet. Show the road
	# at the occupied camp; restore its landmark when the leader leaves.
	var occupied_camps={}
	if game.chapter==1 and game.route=="alm":
		var actor_cell=Vector2i((world_actor/16).round())
		for node in world.nodes.values():
			if node.get("symbol","")=="camp" and actor_cell==Vector2i(node.position[0],node.position[1]):occupied_camps[actor_cell]=true
	var visual=_world_visual_data()
	if _world_has_eastern_blackday():_draw_second_chapter_world(visual,origin,occupied_camps)
	else:
		_draw_layers(visual.layers.slice(0,visual.layers.size()-1),32,_tex(visual.atlas),origin)
		_draw_layers([visual.layers.back()],32,_tex(visual.atlas),origin,Color.WHITE,occupied_camps)
		_draw_nature_props(visual.get("natural_props",[]),origin)
	var sp: Dictionary=graphics.map_units.class_11_ally if game.route=="celica" else graphics.map_units.class_21_ally
	var class_actor=PartySprites.sprite("world",game.roster.get(game.leader_id(),{}),game.chapter)
	if class_actor.is_empty():class_actor=PartySprites.sprite("map",game.roster.get(game.leader_id(),{}),game.chapter)
	if not class_actor.is_empty():sp=class_actor
	var walk_direction="up" if world_facing.y<0 else "side" if world_facing.x!=0 else "down"
	if world_facing.x!=0 and sp.directions.has("left"):walk_direction="left" if world_facing.x<0 else "right"
	var tile_origin=sp.get("tile_origin",[4,4])
	var flip_=world_facing.x>0 if sp.get("default_facing","right")=="left" else world_facing.x<0
	if sp.directions.has("left"):flip_=false
	var world_frame=PartySprites.Reviewed.travel_frame(sp,walk_direction,elapsed,not world_path.is_empty())
	_draw_frame(sp,world_frame,world_actor+origin-Vector2(tile_origin[0],tile_origin[1]),flip_)
	for n in game.world_neighbors():
		var p=_oriented_route(n)
		if p.size()<2:continue
		var d=Vector2(p[1][0]-p[0][0],p[1][1]-p[0][1]);var direction="right" if d.x>0 else "left" if d.x<0 else "down" if d.y>0 else "up"
		_draw_map_indicator(direction,world_actor+origin+d*20+Vector2(4,4))
	var bottom=_footer_shift()
	_panel(Rect2(Vector2(8,164)+bottom,Vector2(240,68)));var node=world.nodes[str(game.world_node)]
	_center_text((str(game.stages[game.stage_for_node(game.world_node)].name_zh) if game.chapter>=3 and game.world_has_battle(game.world_node) else str(node.name_zh)),Rect2(Vector2(20,174)+bottom,Vector2(216,16)))
	_center_text((("第五章 · " if game.chapter==5 else "第四章 · " if game.chapter==4 else "第三章 · ")+("东队" if game.route=="celica" else "西队")) if game.chapter>=3 else "第二章 · 东群岛" if game.chapter==2 else "第一章 · 西大陆",Rect2(Vector2(20,192)+bottom,Vector2(216,16)),Color(.87,.84,.7))
	_center_text("确认:地点与道路 S:整备",Rect2(Vector2(20,206)+bottom,Vector2(216,14)))

func _draw_plot() -> void:
	if plot_pages.is_empty():return
	var page=plot_pages[plot_index];var layout=_plot_layout(str(page.speaker));var panel: Rect2=layout.panel
	_panel(panel)
	var speaker_label=str(page.speaker)+(str(page.get("delivery","")))
	_center_text(speaker_label,Rect2(panel.position+Vector2(16,10),Vector2(panel.size.x-32,16)),Color(.94,.88,.67))
	var face=_speaker_portrait(str(page.speaker),Portraits.dialogue_emotion(page))
	if not face.is_empty():draw_texture(_tex(face.path),layout.portrait.position)
	_text(str(page.text).substr(0,int(dialogue_reveal)),layout.text.position,Color.WHITE,true,layout.text.size.x)
	_draw_indicator("down",panel.end-Vector2(20,18))
	plot_layout_audit={"speaker":page.speaker,"emotion":Portraits.dialogue_emotion(page),"portrait_key":face.get("key",""),"has_portrait":layout.has_portrait,"text":layout.text,"portrait":layout.portrait,"panel":panel}

func _draw_result() -> void:
	if game.Training.active(game):
		_panel(Rect2(24,36,208,124))
		_center_text("演习完成" if view=="victory" else "演习结束",Rect2(36,48,184,24))
		var text="所有参训者获得%d经验\n本次倒地不留伤势\n剩余%d次成功演习"%[int(game.Training.config().completion_experience),game.Training.remaining(game)] if view=="victory" else "本次没有经验收益\n未消耗演习次数\n可重试或返回营地"
		_center_text(text,Rect2(36,84,184,48))
		if menu_items.is_empty():
			_panel(Rect2(56,176,144,40));_center_text("确认返回营地",Rect2(68,188,120,16))
		return
	if view=="victory":
		_panel(Rect2(24,40,208,112));_center_text("战斗胜利",Rect2(34,50,188,32))
		_center_text(str(game.battle_data.name_zh)+"\n战场目标已达成\n过关经验与成长已保存",Rect2(34,86,188,48))
		if menu_items.is_empty():
			_panel(Rect2(56,166,144,44));_center_text("确认继续前进",Rect2(68,180,120,16))
		return
	_panel(Rect2(24,44,208,104));_center_text("任务未完成",Rect2(36,58,184,20),Color(.95,.8,.7))
	var reason=str(game.flags.get("quest",{}).get("failed_reason","本次战斗未能取胜"))
	_center_text("\n".join(_wrapped_lines(reason,184)),Rect2(36,84,184,32))
	_center_text("确认选择重试或返回",Rect2(36,122,184,16))

func _personal_battle_sprite(unit: Dictionary,original: Dictionary) -> Dictionary:
	return PartySprites.battle(unit,original,game.chapter)

func _personal_hub_sprite(original: Dictionary) -> Dictionary:
	var shared=PartySprites.sprite("hub",game.roster.get(game.leader_id(),{}),game.chapter)
	return shared if CampaignArt.valid(shared) else CampaignArt.map_sprite("hub",game.roster.get(game.leader_id(),{}))

func _party_hub_sprite(object: Dictionary,original: Dictionary) -> Dictionary:
	if game.hub_record=="H06" and str(object.get("action",""))=="treat":
		return PartySprites.Reviewed.metadata().maps["18_ally"]["tactical-idle"].duplicate(true)
	if game.hub_record=="H21":
		var ids={"east_departure":"carlo","east_mireille":"mireille","east_lisa":"lisa"}
		var id=str(ids.get(str(object.get("action","")),""))
		if not id.is_empty() and str(object.get("name",""))==str(game.characters[id].name_zh):
			var actor:Dictionary=game.roster.get(id,game.characters[id])
			return PartySprites.Reviewed.metadata().maps[PartySprites.Reviewed.key(actor)]["tactical-idle"].duplicate(true)
	if str(object.get("name",""))=="赫兰":
		var art=GameState.read_json("res://data/prologue_cast.json").actors.herlan.duplicate(true)
		art.directions={"down":[0,0],"up":[0,0],"side":[0,0]};art.tile_origin=[8,8];return art
	if str(object.get("action","")) in ["lena","lance"]:
		var id=str(object.action);var actor:Dictionary=game.roster.get(id,game.characters[id])
		return PartySprites.Reviewed.metadata().maps[PartySprites.Reviewed.key(actor)]["tactical-idle"].duplicate(true)
	var civilian=PostbattleNpcs.hub(game,object)
	if CampaignArt.valid(civilian):return civilian
	var id=str(object.get("action",""))
	if id=="transport":return CampaignArt.map_or(PartySprites.Reviewed.metadata().maps["14_ally"]["tactical-idle"],"hub",{"id":id,"class_id":14,"side":"player"})
	if id=="fula" and game.hub_record=="H02":
		var actor:Dictionary=game.roster.get("fula",game.characters.fula)
		return CampaignArt.map_or(PartySprites.Reviewed.metadata().maps[PartySprites.Reviewed.key(actor)]["tactical-idle"],"hub",actor).duplicate(true)
	if id=="hervi" and game.hub_record=="H09":return CampaignArt.map_or(PartySprites.Reviewed.metadata().maps["15_ally"]["tactical-idle"],"hub",{"id":id,"class_id":15,"side":"player"})
	if id=="staff" and game.hub_record=="H09":return CampaignArt.map_or(PartySprites.Reviewed.metadata().maps["18_ally"]["tactical-idle"],"hub",{"id":id,"class_id":18,"side":"player"})
	if id=="guard" or str(object.get("name","")) in ["教团守卫","教团兵","教团守军"]:
		var guard: Dictionary=PartySprites.data().get("story_npc_profiles",{}).get("guard",{}).get("hub",{})
		if CampaignArt.valid(guard):return guard
	if not game.characters.has(id):
		id=""
		for candidate in game.characters:
			if str(game.characters[candidate].name_zh)==str(object.get("name","")).trim_suffix(" · 濒死"):id=candidate;break
	# This surrendered soldier is a friendly story NPC without a roster ID.
	# Do not infer profession from source=5: civilians and captains reuse it too.
	if id.is_empty() and str(object.get("name",""))=="投降兵":
		return PartySprites.sprite("hub",{"class_id":6,"side":"player"},game.chapter)
	if id.is_empty():return CampaignArt.map_sprite("hub",{"class_id":14,"side":"player","neutral":true,"id":str(object.get("name",""))})
	var art=PartySprites.sprite("hub",game.roster.get(id,game.characters[id]),game.chapter)
	return art if CampaignArt.valid(art) else CampaignArt.map_sprite("hub",game.roster.get(id,game.characters[id]))

var recruit_pause_until_ms := 0
const RECRUIT_PAUSE_MS := 2000

func recruitment_paused() -> bool:
	return Time.get_ticks_msec()<recruit_pause_until_ms

func _physics_process(delta: float) -> void:
	if not recruitment_paused():super._physics_process(delta)

func _bind_recruitment_signal() -> void:
	if not game.character_recruited.is_connected(_on_character_recruited):game.character_recruited.connect(_on_character_recruited)

func _on_character_recruited(_id:String)->void:
	held_direction=Vector2i.ZERO;recruit_pause_until_ms=Time.get_ticks_msec()+RECRUIT_PAUSE_MS
	audio.play_jingle("rm_jingle_recruit")

func _map_unit_sprite(unit: Dictionary) -> Dictionary:
	var moving=str(unit.get("id",""))==moving_id
	var art=PartySprites.sprite("map_move" if moving else "map",unit,game.chapter)
	if art.is_empty() and moving:art=PartySprites.sprite("map",unit,game.chapter)
	if not CampaignArt.valid(art):art=CampaignArt.map_sprite("map_move" if moving else "map",unit)
	if not moving and not game.Mechanical.is_puppet(unit):art=TacticalIdle.sprite(art,unit,elapsed)
	if moving and art.has("direction_cycles"):
		var facing="up" if moving_direction.y<0 else "left" if moving_direction.x<0 else "right" if moving_direction.x>0 else "down"
		var cycle:Dictionary=art.direction_cycles[facing]
		art.native_cycle=cycle.frames
		art.cycle_ticks=cycle.ticks
	if not unit.get("acted",false):return art
	var enemy=unit.get("side","")=="enemy"
	var key=str(art.path)+(":enemy_rest" if enemy else ":rest")
	if not textures.has(key):
		var image=_tex(art.path).get_image();image.convert(Image.FORMAT_RGBA8)
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var color=image.get_pixel(x,y)
				if color.a<=0:continue
				var light=color.r*.299+color.g*.587+color.b*.114
				var shade=(Color8(74,37,44) if light<.23 else Color8(153,76,77) if light<.55 else Color8(222,143,135)) if enemy else (Color8(52,70,80) if light<.23 else Color8(113,134,140) if light<.55 else Color8(185,200,202))
				shade.a=color.a;image.set_pixel(x,y,shade)
		textures[key]=ImageTexture.create_from_image(image)
	art.path=key;return art

func _draw_medicine_transport(unit: Dictionary,at: Vector2) -> void:
	var walking=moving_id==str(unit.id)
	var sprite: Dictionary=PartySprites.Reviewed.metadata().maps["14_ally"]["tactical-walk" if walking else "tactical-idle"]
	var direction="up" if walking and moving_direction.y<0 else "left" if walking and moving_direction.x<0 else "right" if walking and moving_direction.x>0 else "down"
	var frame=_native_map_pose(sprite)
	if walking:
		var cycle: Dictionary=sprite.get("direction_cycles",{}).get(direction,{})
		if not cycle.is_empty():
			sprite=sprite.duplicate(false);sprite.native_cycle=cycle.frames;sprite.cycle_ticks=cycle.ticks
			frame=_native_map_pose(sprite)
		else:frame=int(sprite.directions[direction][moving_frame])
	var origin=sprite.get("tile_origin",[4,4])
	_draw_frame(sprite,frame,at+Vector2(-10,0)-Vector2(origin[0],origin[1]))
	draw_texture(_tex("res://assets/battle_tiles/modules/medicine_wagon.png"),at-Vector2(1,0))
	presentation_audit.medicine_transport={"worker":str(sprite.path),"moving":walking,"unit_id":str(unit.id),"bounds":Rect2(at+Vector2(-10,-8),Vector2(36,24))}

func _attack_preview_placement() -> Dictionary:
	var neighbours=[];var combatants=[]
	for actor in game.units:
		if int(actor.hp)>0 and not actor.get("hidden",false):
			neighbours.append(Rect2(_battle_cell_screen(game.pos(actor))+Vector2(-4,-10),Vector2(24,30)))
	for id in [game.selected_id,str(target_ids[target_index]) if not target_ids.is_empty() else ""]:
		var actor=game.find_unit(str(id))
		if actor.is_empty():continue
		var sprite=_map_unit_sprite(actor);var origin=sprite.get("tile_origin",[4,4]);var size=sprite.get("frame_size",[24,24])
		var bounds=Rect2(_battle_cell_screen(game.pos(actor))-Vector2(origin[0],origin[1]),Vector2(size[0],size[1])/maxf(1.0,float(sprite.get("native_density",1))))
		combatants.append(bounds.grow(2))
	var result=BattlePanels.forecast(_battle_cell_screen(game.cursor),_visible_native_rect(),neighbours,combatants)
	result.combatants=combatants
	result.attacker_occluded=result.valid and not combatants.is_empty() and result.panel.intersects(combatants[0])
	return result

func _preview_glyph(character: String) -> Dictionary:
	# Use the existing native 12px digits, preserving their full vertical ink.
	# Only empty horizontal columns are removed; no fractional resampling.
	var digits="0123456789";var index=digits.find(character)
	if index>=0 or character=="%":
		var source="０１２３４５６７８９".substr(index,1) if index>=0 else "％"
		var glyph: Dictionary=chinese_font.glyphs[source].duplicate(true)
		var crop=2 if index>=0 else 1;var advance=7 if index>=0 else 9
		glyph.rect[0]+=crop;glyph.rect[2]=advance;glyph.advance=advance
		return glyph
	return _zh_glyph(character)

func _preview_text_width(value: String) -> float:
	var width=0.0
	for character in value:
		var glyph=_preview_glyph(character)
		width+=float(glyph.advance) if not glyph.is_empty() else 4.0 if character==" " else 8.0
	return width

func _preview_text(value: String,at: Vector2,color: Color=Color.WHITE) -> void:
	var start=at.round();var cursor=start
	for character in value:
		var glyph=_preview_glyph(character)
		if not glyph.is_empty():
			var r: Array=glyph.rect
			draw_texture_rect_region(_tex(chinese_font.path),Rect2(cursor,Vector2(r[2],r[3])),Rect2(r[0],r[1],r[2],r[3]),color)
			cursor.x+=float(glyph.advance)
		elif character==" ":cursor.x+=4
		else:
			for code in graphics.font.char_codes.get(character,[0x9c]):_glyph(int(code),cursor+Vector2(0,2),color)
			cursor.x+=8
	var bounds=Rect2(start,Vector2(_preview_text_width(value),12))
	text_checks.append({"text":value,"bounds":bounds,"font_px":12,"native_digits":true})
	if not safe_panels.is_empty() and not safe_panels[-1].encloses(bounds):layout_errors.append("Forecast text outside content-safe rectangle: "+value)

func _draw_preview_health(hp: int,maximum: int,at: Vector2,side: String,largest_maximum: int) -> void:
	# A shared density for both combatants prevents different cell heights.
	var columns=52 if largest_maximum>52 else 26
	var cell_size=Vector2(2,2) if largest_maximum>52 else Vector2(4,4)
	var count=clampi(maximum,1,255);var filled=clampi(hp,0,count)
	var bounds=Rect2(at,Vector2(mini(count,columns)*cell_size.x,ceili(float(count)/columns)*cell_size.y))
	if not safe_panels.is_empty() and not safe_panels[-1].encloses(bounds):layout_errors.append("Forecast HP cells outside content-safe rectangle")
	for index in range(count):
		var cell="filled" if index<filled else "empty"
		var position=at+Vector2(index%columns,index/columns)*cell_size
		draw_texture_rect(_tex(health_ui.cells[side][cell].path),Rect2(position,cell_size),false)
	health_checks.append({"hp":filled,"maximum":count,"cells":count,"filled_cells":filled,"bounds":bounds,"cell_size":cell_size,"columns":columns,"forecast":true})

func _draw_preview() -> void:
	battle_preview_audit={}
	if target_index<0 or target_index>=target_ids.size():return
	var attacker=game.find_unit(game.selected_id)
	var defender=game.find_unit(str(target_ids[target_index]))
	# Combat completion can clear either selection before target mode redraws.
	if attacker.is_empty() or defender.is_empty():return
	attacker=attacker.duplicate(true)
	var distance=absi(game.pos(attacker).x-game.pos(defender).x)+absi(game.pos(attacker).y-game.pos(defender).y)
	attacker=Rules.attack_context(attacker,distance)
	var reply=Rules.default_counter(defender,distance)
	var part_selected=mechanical_target_confirmed and mechanical_target_id==str(defender.id) and game.Mechanical.valid_part(defender,mechanical_target_part)
	var placement=_attack_preview_placement();battle_preview_audit=placement
	if not placement.valid:return
	var rect: Rect2=placement.panel
	_panel(rect)
	# Reuse the panel material and its intact frame. The two inner fields use
	# the same faction colors as combat, independent of attacker/defender order.
	battle_preview_audit.factions=[]
	var material=_tex(graphics.panel.path)
	for i in range(2):
		var unit=attacker if i==0 else reply
		var field=Rect2(rect.position+Vector2(8+i*112,8),Vector2(112,rect.size.y-16)) if not placement.stacked else Rect2(rect.position+Vector2(8,8+i*82),Vector2(rect.size.x-16,82))
		var tint=Color(.7,1.15,2.1) if unit.side=="player" else Color(2.8,.8,.8)
		draw_texture_rect_region(material,field,Rect2((material.get_size()/2).floor(),Vector2.ONE),tint)
		battle_preview_audit.factions.append({"unit":str(unit.id),"side":str(unit.side),"bounds":field,"tint":tint})
	var largest_maximum=maxi(int(attacker.max_hp),int(reply.max_hp))
	battle_preview_audit.text_font_px=12;battle_preview_audit.hp_cell_size=Vector2(2,2) if largest_maximum>52 else Vector2(4,4)
	battle_preview_audit.text_rows=[]
	for unit in [attacker,reply]:
		if int(unit.get("character_id",0))==167:unit.weapon_index=Rules.boss_weapon(unit,game.frame_counter)
	for i in range(2):
		var unit=attacker.duplicate(true) if i==0 else reply.duplicate(true)
		var other=(reply if i==0 else attacker).duplicate(true)
		if i==0 and part_selected:other=game.Mechanical.defence_context(other,mechanical_target_part)
		unit.triangle_attack=Rules.combat_support(unit,other,game.living(str(unit.side)),distance)
		other.story_invulnerable=Rules.boss_guard(other,game.turn)
		var stats=Rules.attack_stats(unit,other,game.terrain_avoid(game.pos(other)))
		var guard=game.Cover.guard_for(game,other)
		var shared=mini(int(guard.get("hp",0)),ceili(float(stats.damage)/2.0)) if not guard.is_empty() else 0
		stats.damage-=shared
		var can_attack=Rules.can_attack(unit,distance);var blocked=Rules.attack_blocked(unit,other)
		var x=rect.position.x+12+(0 if placement.stacked else i*112);var y=rect.position.y+(i*88 if placement.stacked else 0)
		_preview_text(str(unit.name_zh),Vector2(x,y+(10 if placement.compact else 12)))
		var lines=["生命%d/%d"%[int(unit.hp),int(unit.max_hp)],"攻击无效" if blocked else ("伤害"+str(stats.damage)+" 命中"+str(stats.hit)+"%" if can_attack else "无法反击"),"不能造成伤害" if blocked else ("必杀"+str(stats.critical)+"%" if can_attack else "超出攻击范围")]
		if i==1 and part_selected:lines[0]="%s%d/%d"%[game.Mechanical.part_name(defender,false,mechanical_target_part),game.Mechanical.part_hp(defender,mechanical_target_part),game.Mechanical.part_max(defender,mechanical_target_part)]
		if i==1 and can_attack and not blocked:lines[2]+=" "+Rules.weapon_name(unit)
		if shared>0 and can_attack and not blocked:lines[2]="首击掩护分担"+str(shared)
		if i==0 and game.Knockback.capable(game,unit):
			var push=game.Knockback.preview(game,unit,other)
			battle_preview_audit.knockback=push
			lines[2]="必杀"+str(stats.critical)+"% "+("推1格" if push.valid and int(stats.damage)>0 else "不击退")
		if i==0 and not part_selected and game.Mechanical.core_active(defender):lines[2]="攻击后反伤2HP"
		for row in range(3):
			var line=str(lines[row])
			if _preview_text_width(line)>104:line=line.replace(" ","")
			_preview_text(line,Vector2(x,y+(24+row*14 if placement.compact else 32+row*16)))
			battle_preview_audit.text_rows.append({"unit":str(unit.id),"text":line})
		_draw_preview_health(game.Mechanical.part_hp(defender,mechanical_target_part) if i==1 and part_selected else int(unit.hp),game.Mechanical.part_max(defender,mechanical_target_part) if i==1 and part_selected else int(unit.max_hp),Vector2(x,y+(66 if placement.compact else 82)),"ally" if unit.side=="player" else "enemy",largest_maximum)
		if i==1 and game.Mechanical.is_puppet(defender):battle_preview_audit.mechanical_target={"part":mechanical_target_part if part_selected else "body","body_hp":int(defender.hp),"part_hp":game.Mechanical.part_hp(defender,mechanical_target_part)}
	if target_ids.size()>1:
		if placement.stacked:
			var sprite=_map_unit_sprite(defender);var arrow_y=-int(sprite.get("tile_origin",[4,4])[1])-9
			_draw_map_indicator("left",_battle_cell_screen(game.cursor)+Vector2(-8,arrow_y))
			_draw_map_indicator("right",_battle_cell_screen(game.cursor)+Vector2(16,arrow_y))
		else:
			_draw_indicator("left",rect.position+Vector2(110,14))
			_draw_indicator("right",rect.position+Vector2(220,14))
	# The whole panel is outside this protected sprite/arrow rectangle.
	var target_sprite=_map_unit_sprite(defender)
	_draw_map_indicator("down",_battle_cell_screen(game.cursor)+Vector2(4,-int(target_sprite.get("tile_origin",[4,4])[1])-9))

func _draw_support_preview() -> void:
	var anchor=_battle_cell_screen(game.cursor)
	var arrow_y=-4
	var hovered=game.unit_at(game.cursor)
	if not hovered.is_empty():arrow_y=-int(_map_unit_sprite(hovered).get("tile_origin",[4,4])[1])-9
	var neighbours=[]
	for other in game.living("player"):
		if game.pos(other)!=game.cursor:neighbours.append(Rect2(_battle_cell_screen(game.pos(other))-Vector2(8,12),Vector2(32,32)))
	var protected=[objective_badge_rect] if objective_badge_rect.has_area() else []
	protected.append(Rect2(anchor+Vector2(2,arrow_y-2),Vector2(14,14)))
	var placement=BattlePanels.place(anchor,Vector2(224,64),_visible_native_rect(),neighbours,protected)
	presentation_audit.support_preview=placement
	if not placement.valid:return
	var rect:Rect2=placement.panel
	_panel(rect)
	var spell=Items.spell(chosen_spell)
	_center_text(str(spell.name_zh)+" 消耗生命"+str(Items.cost(chosen_spell)),Rect2(rect.position+Vector2(12,12),Vector2(200,16)))
	var instruction="选择传送目的地" if ui_mode=="warp" else "选择支援对象"
	var target=game.find_unit(support_target) if ui_mode=="warp" else game.find_unit(str(target_ids[target_index])) if not target_ids.is_empty() else {}
	if not target.is_empty():instruction="传送"+str(target.name_zh)+"至选定格" if ui_mode=="warp" else "%s %d/%d"%[target.name_zh,int(target.hp),int(target.max_hp)]
	_center_text(instruction,Rect2(rect.position+Vector2(12,36),Vector2(200,16)))
	_draw_map_indicator("down",anchor+Vector2(4,arrow_y))
	presentation_audit.support_preview.arrow=protected[-1]

func _draw_unit_card(unit: Dictionary) -> void:
	if busy or notice_time>0 or phase_time>0:return
	var screen=_battle_cell_screen(game.cursor);var neighbours=[]
	var recovery=game.category(game.cursor)==15
	var hint=game.interaction_hint(game.cursor)
	var footer=str(hint.text) if not hint.is_empty() else _terrain_name(game.cursor)+" 回避+"+str(game.terrain_avoid(game.cursor))
	var footer_lines=_small_lines(footer,120)
	for other in game.units:
		if int(other.hp)>0 and str(other.id)!=str(unit.id):neighbours.append(Rect2(_battle_cell_screen(game.pos(other))-Vector2(8,12),Vector2(32,32)))
	var tactical=[]
	if game.MapSkills.eligible(unit):tactical.append("MAP剩余"+str(3-game.MapSkills.used(unit))+"/3")
	if int(unit.get("map_fatigue_until_turn",0))>0:
		tactical.append("虚脱：移动-2 伤害-25%")
		tactical.append("至下个己方回合结束")
	if int(unit.get("map_move_penalty_until_turn",0))>0:
		tactical.append("施法负荷：移动-2")
		tactical.append("至下个己方回合结束")
	var strong_turns=game.MapSkills.StrongBody.remaining(unit,int(game.turn))
	var cover=game.Cover.description(game,unit)
	if not cover.is_empty():tactical.append_array(_small_lines(cover,120))
	if game.Knockback.capable(game,unit):tactical.append("主动近战命中可击退1格")
	var extra_footer=maxi(0,footer_lines.size()-1)*12
	var protected=[objective_badge_rect] if objective_badge_rect.has_area() else []
	if unit.get("side","")=="enemy":
		for cell in presentation_audit.get("enemy_range",[]):protected.append(Rect2(_battle_cell_screen(cell),Vector2(16,16)).grow(1))
	var placement=BattlePanels.place(screen,Vector2(144,(108 if recovery else 92)+tactical.size()*12+extra_footer+(4 if not tactical.is_empty() else 0)+(32 if strong_turns>0 else 0)),_visible_native_rect(),neighbours,protected)
	battle_card_audit=placement
	presentation_audit.range_card_hidden=not placement.valid and unit.get("side","")=="enemy"
	if not placement.valid:return
	var rect: Rect2=placement.panel;var x=rect.position.x;var y=rect.position.y
	_panel(rect);_text(str(unit.name_zh),Vector2(x+12,y+12))
	var label="等级"+str(int(unit.level))
	if unit.get("objective_boss",false):label="首领 · "+label
	if bool(unit.get("neutral",false)):
		label="船体检查点" if unit.get("quest_kind","")=="ship" else "等待救援" if unit.get("locked",false) else "岗位守卫" if unit.get("battle_guard",false) else "自动护送" if unit.get("quest_kind","") in ["escort","medicine","prisoner","patient","sailor"] else "非战斗友军"
		if game.stage_id==112 and game.Medicine.is_staff(unit):label="药品已到 · 准备交接" if game.Medicine.delivered(game) else "核对药单 · 照护伤者"
		elif game.MineEscort.applies(game,unit):label="随矿工推进 · 安全弓援"
		elif game.ShipInterception.applies(game,unit):label=game.ShipInterception.hint(unit)
		elif str(unit.get("quest_kind",""))=="medicine" or (game.stage_id==105 and str(unit.id).begins_with("M15_workers")):label=game.escort_hint(unit)
	elif unit.side=="player":label+=" 经验"+str(int(unit.get("exp",0)))
	_small_text(label,Vector2(x+12,y+30));_small_text(("耐久" if unit.get("event_object",false) else "生命")+str(int(unit.hp))+"/"+str(int(unit.max_hp)),Vector2(x+12,y+42))
	_draw_health(int(unit.hp),int(unit.max_hp),Vector2(x+12,y+54),"ally" if unit.side in ["player","neutral"] else "enemy")
	for i in range(footer_lines.size()):_small_text(footer_lines[i],Vector2(x+12,y+74+i*12),Color(.78,.85,.71))
	if recovery:
		var recovery_text="下次己方阶段恢复5生命" if unit.side=="player" else "所属阵营阶段开始恢复5生命"
		_small_text(recovery_text,Vector2(x+12,y+90+extra_footer),Color(.72,1.0,.78))
	for i in range(tactical.size()):_small_text(str(tactical[i]),Vector2(x+12,y+(106 if recovery else 90)+extra_footer+i*12),Color(.82,.91,1))

	if strong_turns>0:
		var by=y+(106 if recovery else 90)+extra_footer+tactical.size()*12
		_draw_strong_body_icon(Vector2(x+12,by),strong_turns)
		_text("强身",Vector2(x+40,by))
		_small_text("剩余"+str(strong_turns)+"回合",Vector2(x+70,by+2),Color(.72,.8,.82))
		_small_text("物防+2  合计"+str(Rules._defence(unit)+Items.physical_defence_bonus(unit)),Vector2(x+40,by+16),Color("a9dfb6"))
	presentation_audit.strong_body={"unit":str(unit.id),"remaining":strong_turns,"bonus":game.MapSkills.StrongBody.bonus(unit),"icon_visible":strong_turns>0,"panel":rect}

func _draw_strong_body_icon(at:Vector2,turns:int)->void:
	draw_texture_rect(_tex(game.MapSkills.StrongBody.ICON),Rect2(at,Vector2(19,19)),false)
	var badge=StyleBoxFlat.new();badge.bg_color=Color("172a34");badge.set_corner_radius_all(2)
	draw_style_box(badge,Rect2(at+Vector2(13,12),Vector2(9,10)))
	_small_text(str(turns),at+Vector2(14,13))

func _contact(event:Dictionary)->void:
	await super._contact(event)
	var cover:Dictionary=event.get("cover",{})
	if not cover.is_empty():
		combat_message=str(game.find_unit(str(cover.unit)).get("name_zh","同伴"))+"掩护分担"+str(int(cover.damage))+"伤害"
		# The critical timeline already owns its impact hold and synchronized audio.
		if not battle_animation.cinema.accepts_contact(event):await _wait(0.45)
	if int(event.get("reflection_damage",0))>0:
		await battle_animation.reaction(str(event.defender),"reflection")
		# Feedback only: the original contact already committed both HP changes once.
		await super._contact({"attacker":str(event.defender),"defender":str(event.attacker),"hit":true,"critical":false,
			"damage":int(event.reflection_damage),"hp_before":int(event.reflection_hp_before),"hp_after":int(event.source_hp_after),
			"feedback_only":true,"reflection_feedback":true})

func _terrain_name(cell: Vector2i) -> String:
	if not game.in_bounds(cell):return "地图边界"
	if game.ShipInterception.plank(game,cell):return "登舰跳板"
	var visit=game.VisitBuildings.visit_at(game.battle_data,cell)
	if not visit.is_empty():return str(visit.label).trim_prefix("访问")
	for site in game.battle_data.get("recovery_sites",[]):
		if cell==Vector2i(site.position[0],site.position[1]):return str(site.label)
	if game.battle_data.code=="M15" and cell==Vector2i(game.battle_data.exit[0],game.battle_data.exit[1]):return "北门敌军退路"
	for site in game.battle_data.get("building_sites",[]):
		if cell==Vector2i(site.position[0],site.position[1]):return str(site.label)
	for module in game.battle_data.get("art_modules",[]):
		if module.name=="camp_palisade" and module.cells.any(func(p):return cell==Vector2i(p[0],p[1])):return "营地木栅"
	for obj in game.battle_data.objects:
		if cell==Vector2i(obj.position[0],obj.position[1]):
			if game.stage_id==405:return ("北井" if obj.id=="well_n" else "南井")+("受控" if game.flags.quest.wells[str(obj.id)] else "失守，可夺回")
			if game.stage_id in [406,411] and game.flags.quest.get("record_lost",false) and obj.id in ["observatory_record","black_register"]:return "记录已焚毁"
		if obj.has("completed_label") and game.flags.quest.objects.get(str(obj.id),false) and cell==Vector2i(obj.position[0],obj.position[1]):return str(obj.completed_label)
		if obj.get("kind","")=="visit" and game.visit_fronts(obj).has(cell):return "访问门前"
		if obj.get("kind","")=="control" and cell==Vector2i(obj.position[0],obj.position[1]):
			return str(obj.get("name_zh","道路哨卡"))+("已控制" if game.flags.quest.objects.get(str(obj.id),false) else "待控制")
		if not obj.get("optional",false) and cell==Vector2i(obj.position[0],obj.position[1]):return str(obj.label)
	if game.chapter==3 and game.category(cell) in [0,6,8]:
		var ground=str(game.battle_data.visual_ground[cell.y][cell.x])
		if game.battle_data.code=="F33" and cell.x>=6 and cell.x<=10 and cell.y>=13 and cell.y<=17:return "室内石地"
		if ground=="a":return "盐地"
		if ground=="c" and str(game.battle_data.code) in ["S31","S32"]:return "室内石地"
		if ground=="s":return "船体甲板" if game.battle_data.code=="F31" and cell.x<7 else "木栈道"
		if ground=="=" or ground=="b":return "室外石铺"
		if ground=="p" or ground==",":return "土路"
		if ground==".":return "草地"
	if game.chapter==5 and game.category(cell)==7:
		if game.battle_data.code=="F51":return "人工水渠"
		if game.battle_data.code=="F52":return "室内蓄水池"
		if str(game.battle_data.code) in ["M51","J53","J54"]:return "庭院水池"
	if game.chapter==5 and game.category(cell) in [0,6,8]:
		var ground=str(game.battle_data.visual_ground[cell.y][cell.x])
		match str(game.battle_data.code):
			"F51":
				if ground in ["b","c","="]:return "室内石地"
				if ground=="s":return "检修木桥"
			"F52":
				if ground in ["b","c","="]:return "神宫大理石地"
			"S51":
				if ground=="w":return "室内木地"
				if ground=="b":return "室内石地"
			"M51":
				if ground=="b":return "病房石地"
				if ground=="=":return "室外石铺"
			"M52":
				if ground in ["b","c","="]:return "露天石桥"
			"J53","J54":
				if ground in ["b","="]:return "神宫大理石地" if game.battle_data.code=="J54" and cell.y<=15 else "庭院石铺"
	if game.chapter==4 and game.category(cell) in [0,6,8]:
		var ground=str(game.battle_data.visual_ground[cell.y][cell.x])
		if ground in ["=","b"]:return "室外石铺"
		if ground=="u":return "露天石台"
		if ground in ["p",","]:return "土路"
		if ground=="s":return "木栈道"
		if ground==".":return "草质干地" if game.stage_id in [407,412] else "草地"
	if game.stage_id>=400:
		var material=str(game.battle_data.logic_grid[cell.y]).substr(cell.x,1)
		if material=="n":return "雪地"
		if material=="a":return "盐地"
		if material=="s":return "木栈台"
		if material=="," and game.stage_id in [407,412]:return "干地通路"
	match game.category(cell):
		0:return "雪地" if game.battle_data.code=="M11" else "洞内平地" if game.battle_data.code in ["S11","S22"] else "平地"
		1:return "林地"
		2:return "沙滩" if game.battle_data.code in ["F23","F24"] else "沙地"
		5:return "山岩"
		6:return "港侧木栈道" if game.battle_data.code=="M15" else "港口木码头" if game.battle_data.code=="F25" else "修补木桥" if game.battle_data.code=="F26" else "跨河木桥" if game.battle_data.code in ["M11","S12"] else "甲板"
		7:return "河流" if game.battle_data.code in ["M11","S12"] else "潮水" if game.battle_data.code=="S22" else "海面"
		8:return "石铺地"
		10:return "碎石"
		12:
			var building_name=game.VisitBuildings.name_at(game.battle_data,cell)
			return building_name if not building_name.is_empty() else "建筑障碍"
		15:return "恢复地形"
		16:return "湿地"
	return "地面"

func _draw_terrain_card() -> void:
	var screen=_battle_cell_screen(game.cursor)
	var recovery=game.category(game.cursor)==15
	var hint=game.interaction_hint(game.cursor)
	var hint_lines=_wrapped_lines(str(hint.get("text","")),152) if not hint.is_empty() else []
	var height=68+(16 if recovery else 0)+hint_lines.size()*16
	var neighbours=[]
	for actor in game.units:
		if int(actor.hp)>0:neighbours.append(Rect2(_battle_cell_screen(game.pos(actor))-Vector2(4,8),Vector2(24,28)))
	var placement=BattlePanels.place(screen,Vector2(176,height),_visible_native_rect(),neighbours,[objective_badge_rect] if objective_badge_rect.has_area() else [])
	if not placement.valid:return
	var rect: Rect2=placement.panel;var x=rect.position.x;var y=rect.position.y
	var unit=game.find_unit(game.selected_id) if ui_mode=="move" else game.roster.get(game.leader_id(),{})
	var cost=game.movement_cost(unit,game.cursor) if not unit.is_empty() else 255
	_panel(rect)
	_center_text(_terrain_name(game.cursor),Rect2(x+12,y+12,152,12),Color(.93,.87,.67))
	_center_text("回避+"+str(game.terrain_avoid(game.cursor)),Rect2(x+12,y+28,152,12))
	var movement="不能在此落脚" if cost>=255 else str(unit.get("name_zh","部队"))+"移动消耗"+str(cost)
	_center_text(movement,Rect2(x+12,y+44,152,12),Color(.78,.85,.71))
	if recovery:_center_text("己方阶段开始恢复5生命",Rect2(x+12,y+60,152,12),Color(.78,.85,.71))
	if not hint.is_empty():
		_center_text("\n".join(hint_lines),Rect2(x+12,y+(76 if recovery else 60),152,hint_lines.size()*16),Color(.72,1.0,.78))
		presentation_audit.interaction_hint=hint

func _draw_battle() -> void:
	super._draw_battle()
	if hero_map_animation!=null and hero_map_animation.active:
		hero_map_animation.draw();return
	if ui_mode=="map_target":_draw_map_forecast();return
	if view=="battle" and ui_mode=="inspect" and menu_items.is_empty() and not busy and phase_time<=0 and notice_time<=0:
		_draw_exit_direction()
	if view!="battle" or ui_mode not in ["inspect","move"] or not menu_items.is_empty() or busy or phase_time>0 or notice_time>0:return
	if ui_mode=="move":_draw_terrain_card();return
	if not game.unit_at(game.cursor).is_empty():return
	for boat in game.event_boats():
		if game.cursor!=Vector2i(boat.position[0],boat.position[1]):continue
		var placement=BattlePanels.place(_battle_cell_screen(game.cursor),Vector2(128,88),_visible_native_rect(),[],[objective_badge_rect] if objective_badge_rect.has_area() else [])
		if not placement.valid:return
		var rect: Rect2=placement.panel;var x=rect.position.x;var y=rect.position.y
		_panel(rect);_text("居民船队",Vector2(x+12,y+12))
		var status="已抵达西岸" if boat.get("arrived",false) else "等待航路安全" if boat.get("stopped",false) else "沿水路前进"
		_small_text(status,Vector2(x+12,y+30));_small_text("船体"+str(int(boat.hp))+"/"+str(int(boat.max_hp)),Vector2(x+12,y+44))
		_draw_health(int(boat.hp),int(boat.max_hp),Vector2(x+12,y+58),"ally")
		return
	_draw_terrain_card()

func _draw_tactical_marks()->void:
	var marks=game.Battlefield.warning_cells(game)
	presentation_audit.tactical_warnings=marks
	for mark in marks:
		var cell=Vector2i(mark.position[0],mark.position[1])
		var at=_battle_cell_screen(cell)
		draw_rect(Rect2(at,Vector2(16,16)),Color(1,.28,.08,.34+.08*sin(elapsed*4)))
		# Native glyph, beneath units: a warning differs from move/attack shading.
		_text("!",at+Vector2(5,2),Color(1,.94,.71),false)

func _draw_exit_direction() -> void:
	var marker=game.exit_marker()
	if marker.is_empty():return
	var point=_battle_cell_screen(Vector2i(marker.position[0],marker.position[1]));var bounds=_visible_native_rect()
	if bounds.grow(-20).has_point(point):return
	var delta=point-bounds.get_center();var direction="东" if absf(delta.x)>absf(delta.y) and delta.x>0 else "西" if absf(delta.x)>absf(delta.y) else "南" if delta.y>0 else "北"
	var text=str(marker.label)+" · "+direction+"方 · S菜单定位"
	var width=_small_text_width(text)+20;var rect=Rect2(bounds.position+Vector2(8,8),Vector2(width,28))
	# Keep the selected unit and its nearby information panel unobstructed.
	var focus=Rect2(_battle_cell_screen(game.cursor)+Vector2(-6,-12),Vector2(28,36))
	if rect.intersects(focus) or (battle_card_audit.get("panel",Rect2()).has_area() and rect.intersects(battle_card_audit.panel)):
		rect.position.y=bounds.end.y-rect.size.y-8
	if rect.intersects(focus):return
	if battle_card_audit.get("panel",Rect2()).has_area() and rect.intersects(battle_card_audit.panel):return
	_panel(rect);_small_text(text,rect.position+Vector2(10,10),Color(.76,1,.82))

func _input(event: InputEvent) -> void:
	if recruitment_paused():return
	if prologue_scene!=null and prologue_scene.active and view in ["prologue_scene","plot"]:
		if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_Z,KEY_ENTER,KEY_SPACE]:_accept()
		elif event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_LEFT:_accept()
		return
	if view=="story_intro":
		if event is InputEventKey and event.pressed and not event.echo and event.physical_keycode in [KEY_Z,KEY_ENTER,KEY_SPACE]:story_intro.accept()
		elif event is InputEventMouseButton and event.pressed and event.button_index==MOUSE_BUTTON_LEFT:story_intro.accept()
		return
	if view=="overview":
		if event is InputEventKey and event.pressed and not event.echo:
			if event.physical_keycode in [KEY_EQUAL,KEY_KP_ADD]:_overview_change_zoom(1);return
			if event.physical_keycode in [KEY_MINUS,KEY_KP_SUBTRACT]:_overview_change_zoom(-1);return
			if event.physical_keycode==KEY_R:
				overview_zoom=1;overview_center=Vector2(0.5,0.5);queue_redraw();return
		if event is InputEventMouseButton:
			if event.button_index==MOUSE_BUTTON_LEFT:
				overview_mouse_drag=event.pressed and _overview_area().has_point(event.position-_canvas_offset());return
			if event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
				_overview_change_zoom(1 if event.button_index==MOUSE_BUTTON_WHEEL_UP else -1);return
		if event is InputEventMouseMotion and overview_mouse_drag:
			_overview_pan_pixels(event.relative);return
	super._input(event)

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_FOCUS_OUT,NOTIFICATION_APPLICATION_PAUSED]:overview_mouse_drag=false
	super._notification(what)

func _overview_area() -> Rect2:
	var bounds=_visible_native_rect()
	return Rect2(bounds.position+Vector2(8,8),Vector2(bounds.size.x-16,196))

func _overview_geometry() -> Dictionary:
	var area=_overview_area();var texture_size=_world_overview_texture().get_size()
	var scale=minf(area.size.x/texture_size.x,area.size.y/texture_size.y)*overview_zoom
	var shown=Vector2(minf(area.size.x,texture_size.x*scale),minf(area.size.y,texture_size.y*scale))
	var source_size=shown/scale
	var half=source_size/texture_size/2
	overview_center=overview_center.clamp(half,Vector2.ONE-half)
	var source=Rect2(overview_center*texture_size-source_size/2,source_size)
	return {"area":area,"dest":Rect2((area.get_center()-shown/2).round(),shown),"source":source,"scale":scale,"zoom":overview_zoom}

func _overview_change_zoom(step:int) -> void:
	overview_zoom=clampi(overview_zoom+step,1,3);_overview_geometry();queue_redraw()

func _overview_pan_pixels(delta:Vector2) -> void:
	var geometry=_overview_geometry()
	overview_center-=delta/(_world_overview_texture().get_size()*float(geometry.scale))
	_overview_geometry();queue_redraw()

func _draw_overview() -> void:
	draw_rect(_visible_native_rect(),Color(.08,.12,.15))
	overview_audit=_overview_geometry()
	draw_texture_rect_region(_world_overview_texture(),overview_audit.dest,overview_audit.source)
	var bounds=_visible_native_rect()
	var heading="世界全图 · %d倍" % overview_zoom
	_preview_text(heading,Vector2(roundf(bounds.get_center().x-_preview_text_width(heading)/2),210),Color(.94,.88,.67))
	var hint="方向或拖动查看 · 返回退出" if get_meta("phone",false) else "方向移动 · 滚轮缩放 · 返回退出"
	_center_text(hint,Rect2(bounds.position.x+8,226,bounds.size.x-16,12))

func _draw_chapter_end() -> void:
	draw_rect(Rect2(0,0,256,240),Color(.06,.1,.13));_panel(Rect2(12,20,232,196))
	_center_text("第四章完成" if game.chapter==4 else "第三章完成" if game.chapter==3 else "第二章完成" if game.chapter==2 else "第一章完成",Rect2(24,38,208,24),Color(.94,.88,.67))
	_center_text("故人的另一面" if game.chapter==4 else "另一种胜利" if game.chapter==3 else "没有归来的船" if game.chapter==2 else "庆典前夜",Rect2(24,74,208,20))
	_center_text("两岸保住了部分住处，\n仍有人不能回家。" if game.chapter==4 else "两队分别前往北境与盐原。" if game.chapter==3 else "船团抵达西岸。" if game.chapter==2 else "科兰已败，日光重返西大陆。",Rect2(24,108,208,32))
	_center_text("两队成长与伤情已保存" if game.chapter>=2 else "成长与伤亡已保存",Rect2(24,158,208,20))
	_center_text("确认打开菜单",Rect2(24,186,208,16))

func _cancel() -> void:
	if view=="battle" and menu_context=="mechanical_part":_clear_menu();mechanical_target_confirmed=false;ui_mode="target";queue_redraw();return
	if view=="battle" and ui_mode=="target":mechanical_target_confirmed=false;mechanical_target_part=""
	if view in ["camp_status","village_status"] and not busy and not batch_running and menu_items.is_empty():
		view=camp_context if view=="camp_status" else "village";return
	if view=="field_notes":field_notes.cancel();return
	if view=="story_intro":return
	if view=="battle" and ui_mode=="map_target" and not busy:
		hero_map_animation.forecast={};_unit_action_menu();return
	if prologue_scene!=null and prologue_scene.active:return
	if view=="battle" and not busy and menu_context in ["cover_targets","cover_confirm","breakable_confirm"]:
		_clear_menu();_unit_action_menu();return
	if equipment_screen!=null and equipment_screen.active():equipment_screen.cancel();return
	if view in ["journal","journal_confirm"]:journey.cancel();return
	if view=="title":return
	if view=="plot":return
	if view=="overview":
		held_direction=Vector2i.ZERO;overview_mouse_drag=false;view="world";return
	super._cancel()


func _show_result() -> void:
	# A completed action may resume after a result dialogue was dismissed.
	# Only the battle/result controller owns settlement, never a later world/hub.
	if game.mode not in ["battle","victory","defeat"] or game.battle_outcome.is_empty():return
	await super._show_result()
	if game.stage_id==534 and game.battle_settled and game.flags.get("campaign_complete",false) and view=="victory":_start_ending()

func _status_members() -> Array:
	if view=="battle" and game.find_unit(status_id).get("side","")=="enemy":return _enemy_status_members()
	if game.stage_id in [533,534] and game.mode in ["battle","victory","defeat"]:
		if game.Casualties.owner({"parties":game.parties},status_id).is_empty():return []
		return game.units.filter(func(u):return u.side=="player" and not u.get("temporary",false) and not u.get("neutral",false)).map(func(u):return str(u.id))
	return super._status_members()

func _draw_status(unit: Dictionary) -> void:
	if unit.is_empty():return
	var advanced=game.HeroProfessions.advanced(unit)
	var enemy=unit.get("side","player")=="enemy"
	_panel(Rect2(8,12,240,220))
	var members = _status_members()
	if members.size()>1 or enemy:
		_center_text(("敌军" if enemy else "队伍")+" %d/%d"%[members.find(status_id)+1,members.size()],Rect2(40,24,176,12))
	if members.size()>1:
		_draw_indicator("left",Vector2(24,24));_draw_indicator("right",Vector2(224,24))
	var portrait = _unit_portrait(unit)
	if not portrait.is_empty():draw_texture(_tex(portrait.path),Vector2(24,40))
	_text(str(unit.name_zh),Vector2(96,40))
	var profession=game.HeroProfessions.name(unit) if advanced else str(game.catalog.classes.get(str(int(unit.class_id)),{}).get("name_zh",unit.get("class_name_zh","")))
	if enemy:profession=str(game.catalog.classes.get(str(int(unit.class_id)),{}).get("enemy_name_zh",unit.get("class_name_zh",profession)))
	_text("职业："+profession,Vector2(96,56),Color(.94,.88,.67))
	presentation_audit.status_profession=profession
	_text("等级%d 经验%d"%[int(unit.level),int(unit.get("exp",0))],Vector2(96,72))
	_text("生命%d/%d"%[int(unit.hp),int(unit.max_hp)],Vector2(96,88))
	_draw_health(int(unit.hp),int(unit.max_hp),Vector2(96,104),"enemy" if enemy else "ally")
	var strong_turns=game.MapSkills.StrongBody.remaining(unit,int(game.turn))
	if strong_turns>0:
		_draw_strong_body_icon(Vector2(212,82),strong_turns)
		_small_text("强身 "+str(strong_turns)+"回合 · 物防+2",Vector2(96,114),Color("a9dfb6"))
	var equipped=StatusStats.stats(unit)
	presentation_audit.status_stats=equipped;presentation_audit.status_unit=str(unit.id)
	var stats = [["攻击",equipped.power],["技巧",int(unit.skill)],
		["速度",equipped.speed],["幸运",equipped.luck],
		["物防",equipped.defence],["魔防",equipped.resistance],
		["移动",equipped.move],["训练" if advanced else "射程",int(unit.get("magic_level",0)) if advanced else StatusStats.range_name(equipped.reach)]]
	for i in range(stats.size()):
		var x = 32+104*(i%2);var y = 120+14*int(i/2) if game.Mechanical.is_puppet(unit) else 124+16*int(i/2)
		_text(str(stats[i][0]),Vector2(x,y));_text(str(stats[i][1]),Vector2(x+64,y),Color("a9dfb6") if i==4 and strong_turns>0 else Color.WHITE)
	var held = int(unit.get("item_id",0))
	var footer = "装备："+str(Items.item(held).get("name_zh","")) if held>0 else "未携带装备（职业默认）"
	if Rules.Body.is_body(unit):footer="固有："+str(Items.item(Rules.weapon_index(unit)).name_zh)
	if game.Mechanical.is_puppet(unit):footer="撤离中 · 移动%d"%int(unit.move) if unit.get("mechanical_retreating",false) else "机械傀儡 · 经验×1.5"
	if advanced and unit.get("water_slow",false):footer="水滞 · 速度－1"
	if game.is_dying(unit):
		_center_text("濒死 · 不可出阵",Rect2(24,190,208,14))
		_center_text("已救治过，无法再次救治" if int(unit.get("treatment_count",0))>0 else "可使用本队救治泉",Rect2(24,206,208,14));return
	if game.Mechanical.is_puppet(unit):
		var summary=[]
		for key in game.Mechanical.part_keys(unit):summary.append("%s%d/%d"%[game.Mechanical.part_name(unit,true,key),game.Mechanical.part_hp(unit,key),game.Mechanical.part_max(unit,key)])
		_center_text(" · ".join(summary),Rect2(24,182,208,12))
		var effect="核心有效：双防+10 · 反伤2HP" if game.Mechanical.core_active(unit) else "核心已破坏" if game.Mechanical.is_titan(unit) else "掌击1格 · 水炮2–3格"
		if game.Mechanical.is_cyclops(unit):effect="核心：本体命中减半 · 邻格回5" if game.Mechanical.active(unit,"eye") else "独眼核心损毁 · 治疗已停"
		if game.Mechanical.is_owl(unit):effect="引擎：穿透2物防 · 战后移动3" if game.Mechanical.active(unit,"engine") else "引擎损毁 · 仍可飞行"
		if game.Mechanical.is_prometheus(unit):effect="火核：必中魔法 · 生命核：回复"
		_center_text(effect,Rect2(24,196,208,12))
		_center_text("不撤离 · 生命核可复苏一次" if game.Mechanical.is_prometheus(unit) else "仅剩傀儡撤离 · 移动%d→%d"%[game.Mechanical.base_move(unit),game.Mechanical.base_move(unit)+3],Rect2(24,210,208,12))
		return
	_center_text(footer,Rect2(24,190 if advanced else 206,208,14))
	if advanced:_center_text(game.HeroProfessions.summary(unit),Rect2(24,206,208,14))
	elif unit.get("water_slow",false):_center_text("水滞 · 速度－1",Rect2(24,190,208,14))
	elif enemy and str(unit.get("behavior","")) in ["guard","guard_exit"]:
		var reply=Rules.default_counter(unit,3)
		_center_text("远反："+Rules.weapon_name(reply)+" "+StatusStats.range_name(Rules.attack_range(reply))+"格",Rect2(24,190,208,14))

func _draw_mechanical_part_meter(unit:Dictionary,x:float)->void:
	var keys=game.Mechanical.part_keys(unit);var bounds=[]
	for index in range(keys.size()):
		var key=str(keys[index]);var hp=game.Mechanical.part_hp(unit,key);var maximum=game.Mechanical.part_max(unit,key)
		var y=166+index*10 if keys.size()>1 else 166
		_small_text("%s%d/%d"%[game.Mechanical.part_name(unit,false,key),hp,maximum],Vector2(x,y),Color(.8,.94,.98))
		bounds.append(text_checks[-1].bounds)
		for i in range(maximum):
			var state="filled" if i<hp else "empty"
			draw_texture_rect(_tex(health_ui.cells.enemy[state].path),Rect2(x+76+i,y+3,1,4),false)
	presentation_audit.mechanical_parts=unit.get("parts",{}).duplicate(true)
	presentation_audit.mechanical_part_rows=keys.size()
	presentation_audit.mechanical_part_bounds=bounds
	for i in range(bounds.size()):
		for j in range(i+1,bounds.size()):
			if bounds[i].intersects(bounds[j]):layout_errors.append("Core HP labels overlap")

func _start_ending() -> void:
	if not game.flags.get("campaign_complete",false):return
	busy=false;batch_running=false;_clear_menu();ending_pages.clear()
	if game.flags.get("ending_pages",[]).is_empty():
		for page in preload("res://core/chapter5_endings.gd").entries(game):_ending_page(page.title,page.text,int(page.source_id))
		game.flags.ending_pages=ending_pages.duplicate(true)
	else:ending_pages=game.flags.ending_pages.duplicate(true)
	ending_index=clampi(int(game.flags.get("ending_index",0)),0,ending_pages.size()-1)
	game.flags.ending_index=ending_index;view="ending";game.mode="ending";audio.play_ending();game.save_game()

func _draw_ending() -> void:
	if ending_pages.is_empty():return
	var page:Dictionary=ending_pages[clampi(ending_index,0,ending_pages.size()-1)]
	# Dedicated 16:9 panorama retains its aspect ratio; the text uses an opaque safe panel.
	draw_texture_rect(_tex("res://assets/chapter5/ending-coast.png"),Rect2(0,0,256,144),false)
	var face=_portrait(int(page.source_id))
	if not face.is_empty():draw_texture(_tex(face.path),Vector2(104,42))
	_panel(Rect2(8,96,240,136))
	_center_text(str(page.title),Rect2(24,107,208,20),Color(.94,.88,.67))
	_center_text(str(page.text),Rect2(24,134,208,68))
	_center_text("确认继续 · %d/%d"%[ending_index+1,ending_pages.size()],Rect2(24,208,208,14))

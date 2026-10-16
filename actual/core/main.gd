extends "res://core/legacy_main.gd"
## Original native combat controller, new world / story / hub presentation.
const EnvironmentBorder = preload("res://core/environment_border.gd")
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
var world_facing := Vector2i.DOWN
var previous_canvas_size := Vector2.ZERO
var plot_layout_audit: Dictionary = {}
var small_font: Dictionary = {}
const NPC_PORTRAITS := {"赫兰":35,"艾琳":48,"科兰":37,"乌库布·卡基":50,
	"村民":17,"管理员":30,"矿工":47,"医者":13,"教团守卫":26,"教团兵":26,
	"指挥官":26,"士兵":26,"守军":26,"焚毁兵":26,"流民":17,"劳工":47,
	"居民":17,"投降兵":26,"斥候":26,"裴萨":37,"船长":26,"舵手":26,
	"甲板护卫":26,"船员":47,"引航者":47,"渔民":17,"渔村长者":17,
	"岛上医者":13,"地方医者":13,"留守骑士":26,"学舍导师":30,"俘虏":17,
	"固定舵手":26,"旧船员":47,"求救船员":47,"伤者":17,
	"仓吏":30,"记录员":30,"文书":30,"医师":13,"守灯人":47,"账房":30,"洞民":17}
const NARRATOR_SPEAKERS := ["旁白", "", "叙述", "战场提示", "提示", "旧记录"]

func _ready() -> void:
	super._ready()
	small_font=GameState.read_json("res://data/legacy/font_small_zh.json")
	get_window().title="revenge-memories · 序章至第二章"
	world=game.formal_world;battle_pack=GameState.read_json("res://assets/battle_tiles/battle-tiles.json")
	nature_layouts=GameState.read_json("res://data/nature-layouts.json")
	for sprite in GameState.read_json("res://assets/nature/nature.json").get("sprites",[]):nature_sprites[str(sprite.key)]=sprite
	hub_controller=load("res://core/story_hub.gd").new(self)
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
	super._process(delta)
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

func _canvas_offset() -> Vector2:
	return ((get_viewport_rect().size-NATIVE)/2.0).floor()

func _visible_native_rect() -> Rect2:
	return Rect2(-_canvas_offset(),get_viewport_rect().size)

func _footer_shift() -> Vector2:
	return Vector2(0,get_viewport_rect().size.y-240-_canvas_offset().y)

func _mouse_accept(point: Vector2) -> void:
	var local=point-_canvas_offset()
	if view=="plot":_accept();return
	if view=="overview" or (view=="chapter_end" and menu_items.is_empty()):_accept();return
	if view=="title" and title_menu:
		if Rect2(52,138,152,48).has_point(local):title_selected=0 if local.y<160 else 1;_accept()
		return
	if view=="battle" and not busy and menu_items.is_empty() and ui_mode not in ["status","action"]:
		var cell=_battle_screen_cell(local)
		# Extended mountains are visual-only; in_bounds remains the authority.
		if not game.in_bounds(cell):return
		if ui_mode in ["target","support_target"]:
			var candidate=game.unit_at(cell)
			if not candidate.is_empty() and target_ids.has(candidate.id):target_index=target_ids.find(candidate.id);game.cursor=cell;_focus_battle(cell);_accept()
		else:game.cursor=cell;_focus_battle(cell);_accept()
		return
	super._mouse_accept(local)

func _new_game() -> void:
	game.new_game();_clear_menu();hub_controller.enter_room("P00")

func _begin_existing_battle() -> void:
	notice_time=0
	super._begin_existing_battle()

func _accept() -> void:
	if view=="plot":_advance_plot();return
	if view=="overview":view="world";return
	if view=="chapter_end" and menu_items.is_empty():
		var entries=["返回世界地图","保存进度","返回标题"]
		var actions=["new:world","new:save","title"]
		if game.chapter==1 and game.flags.get("chapter1_complete",false):
			entries.push_front("开始第二章");actions.push_front("new:chapter2")
		_open_menu("chapter_end",entries,actions,Vector2(44,120));return
	if view=="title":
		if not title_menu:title_menu=true;return
		if title_selected==0:_new_game()
		elif game.load_game():
			_clear_menu();busy=false;batch_running=false;ui_mode="inspect";view=game.mode
			world_actor=Vector2(world.nodes[str(game.world_node)].position[0],world.nodes[str(game.world_node)].position[1])*16
			if view=="hub":hub_controller.resume()
			elif view=="battle":_focus_battle(game.cursor,true);_play_phase_music()
			elif view in ["victory","defeat"]:_show_result()
			if game.flags.has("active_plot"):_resume_plot()
			elif not game.story_events.is_empty():_play_story_events()
		else:_notice("存档无法读取" if FileAccess.file_exists(game.save_path) else "暂无存档")
		return
	if view=="world" and menu_items.is_empty() and not busy:
		var entries: Array=[];var actions: Array=[]
		if game.world_has_battle(game.world_node):entries.append("进入战场");actions.append("new:battle")
		else:entries.append("进入据点");actions.append("new:hub")
		for n in game.world_neighbors():entries.append("前往"+str(world.nodes[str(n)].name_zh));actions.append("travel:"+str(n))
		entries.append("部队整备");actions.append("new:camp")
		_open_menu("world_routes",entries,actions,Vector2(24,56));return
	super._accept()

func _direction(direction: Vector2i) -> void:
	if view=="plot" or view=="overview" or view=="chapter_end":
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
	if action.begins_with("travel:"):_travel(int(action.get_slice(":",1)));return
	if action.begins_with("interact:"):
		if game.interact(action.substr(9)):ui_mode="inspect";await _play_story_events();_finish_turn_action()
		elif not game.story_events.is_empty():await _play_story_events()
		return
	if action.begins_with("hub:"):hub_controller.action(action.substr(4));return
	match action:
		"new:chapter2":
			if game.begin_chapter_two():
				busy=false;batch_running=false;ui_mode="inspect";held_direction=Vector2i.ZERO
				hub_controller.enter_room("H21")
				await play_pages([{"speaker":"旁白","text":"半年前，东群岛的风灯岛。艾琳守着船团的航灯，等待一条没有归来的船的消息。"}],"hub")
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
		"new:save","save":_notice("进度已保存" if game.save_game() else "保存失败")
		"new:goal":
			var text=str(game.battle_data.goal)
			if game.battle_data.code=="M15":text+="\n科兰第6回合半血撤离，最晚第8回合；沿东侧栈道尽头封住北门退路。"
			var pages=[{"speaker":"战场提示","text":text}]
			if game.stage_id>=200:
				for status in game.objective_status():pages.append({"speaker":"战场提示","text":status})
			for note in game.battle_data.get("tactical_notes",[]):pages.append({"speaker":"战场提示","text":str(note)})
			await play_pages(pages,"battle")
		"new:overview":view="overview"
		_:super._menu_action(action,context)

func _unit_action_menu() -> void:
	super._unit_action_menu()
	var options=game.interactions_for(game.find_unit(game.selected_id))
	for o in options:menu_items.push_front(str(o.label));menu_actions.push_front("interact:"+str(o.id))

func _open_system_menu() -> void:
	if view=="plot":return
	if view=="world" and not busy:
		_open_menu("world_system",["部队整备","世界全图","保存进度","返回标题"],["new:camp","new:overview","new:save","title"],Vector2(48,64));return
	super._open_system_menu()
	if view=="battle" and not menu_items.is_empty():
		menu_items.append("战场目标");menu_actions.append("new:goal")
		menu_items.append("返回整备（重置本战）");menu_actions.append("new:prepare")

func _show_status() -> void:
	if view=="plot" or view=="overview" or view=="chapter_end":return
	if view=="hub":
		camp_context="hub";_camp_members("status");return
	super._show_status()

func _open_camp_menu() -> void:
	super._open_camp_menu()
	menu_items.insert(3,"装备说明");menu_actions.insert(3,"new:equipment")

func _small_text_width(text: String) -> float:
	var width=0.0
	for ch in text:width+=float(small_font.get("glyphs",{}).get(ch,{}).get("advance",8))
	return width

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

func _draw_hub_caption(title: String,hint: String) -> void:
	# Place location/time at the actual top-left of every landscape canvas.
	var lines=_small_lines(hint,184.0)
	var width=minf(204.0,maxf(_small_text_width(title),lines.map(func(line):return _small_text_width(line)).max() if not lines.is_empty() else 0.0)+20.0)
	var rect=Rect2(_visible_native_rect().position+Vector2(8,8),Vector2(width,32+lines.size()*12))
	_panel(rect)
	_small_text(title,rect.position+Vector2(10,10),Color(.93,.87,.67))
	for i in range(lines.size()):_small_text(lines[i],rect.position+Vector2(10,24+i*12))
	presentation_audit.hub_caption=rect

func _continue_world() -> void:
	view="world";game.mode="world";busy=false;_clear_menu();ui_mode="inspect";held_direction=Vector2i.ZERO
	world_actor=Vector2(world.nodes[str(game.world_node)].position[0],world.nodes[str(game.world_node)].position[1])*16
	audio.play_world(1);game.save_game()

func _play_story_events() -> void:
	var was_busy=busy;busy=true
	while not game.story_events.is_empty():
		var event: Dictionary=game.story_events.pop_front()
		await play_pages(event.get("pages",[]),view)
	busy=was_busy;game.save_game()

func play_pages(pages: Array,return_view: String,callback: String="") -> void:
	var previous_busy=busy;busy=true;held_direction=Vector2i.ZERO
	plot_pages.clear()
	for page in pages:
		plot_pages.append_array(_paginate_plot(page))
	if plot_pages.is_empty():busy=previous_busy;return
	plot_index=0;plot_return=return_view;plot_callback=callback;plot_finished=false;dialogue_reveal=0.0
	game.flags.active_plot={"pages":plot_pages,"index":0,"return":return_view,"callback":callback}
	view="plot";game.save_game()
	while not plot_finished:await get_tree().process_frame
	busy=previous_busy

func _resume_plot() -> void:
	var p: Dictionary=game.flags.active_plot
	plot_pages=p.pages;plot_index=int(p.index);plot_return=p["return"];plot_callback=p.get("callback","")
	plot_finished=false;dialogue_reveal=0.0;view="plot";_reflow_plot()

func _speaker_portrait(speaker: String) -> Dictionary:
	if speaker in NARRATOR_SPEAKERS:return {}
	for id in game.characters:
		if str(game.characters[id].name_zh)==speaker:return _portrait(int(game.characters[id].character_id))
	return graphics.portraits_by_index.get(str(NPC_PORTRAITS.get(speaker,26)),{})

func _plot_layout(speaker: String) -> Dictionary:
	var canvas=get_viewport_rect().size
	var panel=Rect2(-_canvas_offset().x+4,240+_footer_shift().y-96,canvas.x-8,92)
	var has_face=not _speaker_portrait(speaker).is_empty()
	var left=panel.position.x+(76.0 if has_face else 16.0)
	return {"panel":panel,"portrait":Rect2(panel.position+Vector2(16,28),Vector2(48,48)),
		"text":Rect2(left,panel.position.y+30,panel.end.x-20-left,48),"has_portrait":has_face}

func _paginate_plot(page: Dictionary) -> Array:
	var speaker=str(page.get("speaker","旁白"));var out: Array=[]
	var lines=_wrapped_lines(str(page.text).replace("\n",""),_plot_layout(speaker).text.size.x)
	for start in range(0,lines.size(),3):
		out.append({"speaker":speaker,"text":"\n".join(lines.slice(start,mini(start+3,lines.size())))})
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
	if plot_index<plot_pages.size():game.flags.active_plot.index=plot_index;game.save_game();return
	view=plot_return;game.flags.erase("active_plot");plot_finished=true
	if not plot_callback.is_empty():hub_controller.finish_story(plot_callback)
	game.save_game()

func _draw() -> void:
	draw_set_transform(_canvas_offset())
	if view in ["plot","overview","chapter_end"]:
		safe_panels.clear();text_checks.clear();layout_errors.clear();health_checks.clear()
		if view=="overview":_draw_overview();return
		if view=="chapter_end":_draw_chapter_end()
		elif plot_return=="hub":hub_controller.draw()
		elif plot_return in ["battle","victory","defeat"]:_draw_battle()
		else:_draw_world()
		if view=="plot":_draw_plot()
		if not menu_items.is_empty():_draw_menu()
		return
	super._draw()

func _draw_title() -> void:
	_draw_ocean(Vector2.ZERO)
	_draw_layers(world.layers,32,_tex(world.atlas),Vector2(128-world.width*8,120-world.height*8))
	draw_texture_rect_region(_tex("res://assets/world_tiles/formal-world-overview.png"),Rect2(0,0,256,240),Rect2(0,600,512,480))
	draw_rect(Rect2(0,0,256,240),Color(0.05,0.08,0.1,.62))
	_panel(Rect2(24,40,208,152))
	_center_text("复仇与回忆",Rect2(36,56,184,24),Color(.93,.89,.74))
	_center_text("雪下的名字",Rect2(36,86,184,20))
	_center_text("序章至第二章",Rect2(36,112,184,16))
	if title_menu:
		_center_text("开始旅程",Rect2(52,138,152,16));_center_text("继续旅程",Rect2(52,162,152,16))
		_draw_menu_arrow(Vector2(40,140+title_selected*24))
	else:_center_text("确认开启旅程",Rect2(36,150,184,20))
	_panel(Rect2(8,200,240,36))
	_center_text("方向行走 Z确认 X返回 S菜单",Rect2(18,210,220,16))

func _draw_layers(layers: Array,columns: int,atlas: Texture2D,origin: Vector2,tint: Color=Color.WHITE) -> void:
	var bounds=_visible_native_rect().grow(16)
	for layer in layers:
		for y in range(layer.size()):
			if y*16+origin.y < bounds.position.y or y*16+origin.y >bounds.end.y:continue
			for x in range(layer[y].size()):
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
	var material="snow" if layout.get("biome","")=="snow" else "cave" if layout.get("biome","")=="rock" else "grass"
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
	_draw_surroundings(origin,Vector2i(14,9),nature_layouts.get("hubs",{}).get(room,{}))

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
		_draw_art_props(game.battle_data.get("art_props",[]),origin,tint)
		for obj in game.battle_data.objects:
			# Visit entrances belong to the complete building artwork. This also
			# suppresses the old generic door and arrow in compatible old saves.
			if obj.get("kind","")=="visit":continue
			var at=Vector2(obj.position[0],obj.position[1])*16+origin
			var done=game.flags.quest.objects.get(str(obj.id),false)
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

func _draw_camp_control_flag(at: Vector2,controlled: bool) -> void:
	# Reuse the complete native flag and keep its wooden pole unchanged.
	# Only its cloth region is modulated; capture changes ownership colour,
	# never the opening's collision or the road beneath the flag.
	var texture=_tex("res://assets/battle_tiles/modules/white_flag.png")
	draw_texture(texture,at)
	var cloth=Rect2(7,3,5,8)
	var colour=Color(.35,.65,1.0) if controlled else Color(1.0,.32,.25)
	draw_texture_rect_region(texture,Rect2(at+cloth.position,cloth.size),cloth,colour)

func _draw_world() -> void:
	if camp_context=="hub" and view=="camp_status":hub_controller.draw();return
	var camera=world_actor-Vector2(120,96)
	camera=_clamp_map_camera(camera,Vector2(world.width,world.height)*16)
	var origin=-camera.round();_draw_ocean(origin);_draw_layers(world.layers,32,_tex(world.atlas),origin)
	_draw_nature_props(world.get("natural_props",[]),origin)
	var sp: Dictionary=graphics.map_units.class_11_ally if game.route=="celica" else graphics.map_units.class_21_ally
	var walk_direction="up" if world_facing.y<0 else "side" if world_facing.x!=0 else "down"
	var step=(int(elapsed*60.0988)>>4)&1 if not world_path.is_empty() else 0
	var at=Vector2i((world_actor/16).round())
	var on_sea=at.y>=0 and at.y<int(world.height) and at.x>=0 and at.x<int(world.width) and str(world.ground[at.y][at.x])=="sea"
	if game.route=="celica" and on_sea:draw_texture(_tex("res://assets/world_tiles/modules/cutter.png"),world_actor+origin)
	else:_draw_frame(sp,int(sp.directions[walk_direction][step]),world_actor+origin-Vector2(4,4),world_facing.x<0)
	for n in game.world_neighbors():
		var p=_oriented_route(n)
		if p.size()<2:continue
		var d=Vector2(p[1][0]-p[0][0],p[1][1]-p[0][1]);var direction="right" if d.x>0 else "left" if d.x<0 else "down" if d.y>0 else "up"
		_draw_indicator(direction,world_actor+origin+d*20+Vector2(4,4))
	var bottom=_footer_shift()
	_panel(Rect2(Vector2(8,164)+bottom,Vector2(240,68)));var node=world.nodes[str(game.world_node)]
	_center_text(str(node.name_zh),Rect2(Vector2(20,174)+bottom,Vector2(216,16)))
	_center_text("第二章 · 东群岛" if game.chapter==2 else "第一章 · 西大陆",Rect2(Vector2(20,192)+bottom,Vector2(216,16)),Color(.87,.84,.7))
	_center_text("确认:地点与道路 S:整备",Rect2(Vector2(20,206)+bottom,Vector2(216,14)))

func _draw_plot() -> void:
	if plot_pages.is_empty():return
	var page=plot_pages[plot_index];var layout=_plot_layout(str(page.speaker));var panel: Rect2=layout.panel
	_panel(panel)
	_center_text(str(page.speaker),Rect2(panel.position+Vector2(16,10),Vector2(panel.size.x-32,16)),Color(.94,.88,.67))
	var face=_speaker_portrait(str(page.speaker))
	if not face.is_empty():draw_texture(_tex(face.path),layout.portrait.position)
	_text(str(page.text).substr(0,int(dialogue_reveal)),layout.text.position,Color.WHITE,true,layout.text.size.x)
	_draw_indicator("down",panel.end-Vector2(20,18))
	plot_layout_audit={"speaker":page.speaker,"has_portrait":layout.has_portrait,"text":layout.text,"portrait":layout.portrait,"panel":panel}

func _draw_result() -> void:
	if view=="victory":super._draw_result();return
	_panel(Rect2(24,44,208,104));_center_text("任务未完成",Rect2(36,58,184,20),Color(.95,.8,.7))
	var reason=str(game.flags.get("quest",{}).get("failed_reason","本次战斗未能取胜"))
	_center_text("\n".join(_wrapped_lines(reason,184)),Rect2(36,84,184,32))
	_center_text("确认选择重试或返回",Rect2(36,122,184,16))

func _draw_unit_card(unit: Dictionary) -> void:
	if notice_time>0:return
	var screen=_battle_cell_screen(game.cursor);var x=104 if screen.x<128 else 8;var y=8 if screen.y>80 else 120
	_panel(Rect2(x,y,144,112));_text(str(unit.name_zh),Vector2(x+12,y+14))
	var label="等级"+str(int(unit.level))
	if bool(unit.get("neutral",false)):
		label="船体检查点" if unit.get("quest_kind","")=="ship" else "等待救援" if unit.get("locked",false) else "岗位守卫" if unit.get("battle_guard",false) else "自动护送" if unit.get("quest_kind","") in ["escort","medicine","prisoner","patient","sailor"] else "非战斗友军"
	elif unit.side=="player":label+=" 经验"+str(int(unit.get("exp",0)))
	_text(label,Vector2(x+12,y+30));_text(("耐久" if unit.get("event_object",false) else "生命")+str(int(unit.hp))+"/"+str(int(unit.max_hp)),Vector2(x+12,y+46))
	_draw_health(int(unit.hp),int(unit.max_hp),Vector2(x+12,y+66),"ally" if unit.side=="player" else "enemy")
	_text(_terrain_name(game.cursor)+" 回避+"+str(game.terrain_avoid(game.cursor)),Vector2(x+12,y+86),Color(.78,.85,.71))

func _terrain_name(cell: Vector2i) -> String:
	if not game.in_bounds(cell):return "地图边界"
	if game.battle_data.code=="M15" and cell==Vector2i(game.battle_data.exit[0],game.battle_data.exit[1]):return "北门敌军退路"
	for site in game.battle_data.get("building_sites",[]):
		if cell==Vector2i(site.position[0],site.position[1]):return str(site.label)
	for module in game.battle_data.get("art_modules",[]):
		if module.name=="camp_palisade" and module.cells.any(func(p):return cell==Vector2i(p[0],p[1])):return "营地木栅"
	for obj in game.battle_data.objects:
		if obj.get("kind","")=="visit" and game.visit_fronts(obj).has(cell):return "访问门前"
		if obj.get("kind","")=="control" and cell==Vector2i(obj.position[0],obj.position[1]):
			return str(obj.get("name_zh","道路哨卡"))+("已控制" if game.flags.quest.objects.get(str(obj.id),false) else "待控制")
		if not obj.get("optional",false) and cell==Vector2i(obj.position[0],obj.position[1]):return str(obj.label)
	match game.category(cell):
		0:return "雪地" if game.battle_data.code=="M11" else "洞内平地" if game.battle_data.code in ["S11","S22"] else "平地"
		1:return "林地"
		2:return "沙滩" if game.battle_data.code in ["F23","F24"] else "沙地"
		5:return "山岩"
		6:return "港侧木栈道" if game.battle_data.code=="M15" else "港口木码头" if game.battle_data.code=="F25" else "修补木桥" if game.battle_data.code=="F26" else "跨河木桥" if game.battle_data.code in ["M11","S12"] else "甲板"
		7:return "河流" if game.battle_data.code in ["M11","S12"] else "潮水" if game.battle_data.code=="S22" else "海面"
		8:return "石铺地"
		10:return "碎石"
		12:return "建筑障碍"
		15:return "恢复地形"
		16:return "湿地"
	return "地面"

func _draw_terrain_card() -> void:
	var bounds=_visible_native_rect();var screen=_battle_cell_screen(game.cursor)
	var x=bounds.end.x-184 if screen.x<bounds.get_center().x else bounds.position.x+8
	var recovery=game.category(game.cursor)==15
	var height=84 if recovery else 68
	var y=bounds.end.y-height-8;var rect=Rect2(x,y,176,height)
	var unit=game.find_unit(game.selected_id) if ui_mode=="move" else game.roster.get(game.leader_id(),{})
	var cost=game.movement_cost(unit,game.cursor) if not unit.is_empty() else 255
	_panel(rect)
	_center_text(_terrain_name(game.cursor),Rect2(x+12,y+12,152,12),Color(.93,.87,.67))
	_center_text("回避+"+str(game.terrain_avoid(game.cursor)),Rect2(x+12,y+28,152,12))
	var movement="不能在此落脚" if cost>=255 else str(unit.get("name_zh","部队"))+"移动消耗"+str(cost)
	_center_text(movement,Rect2(x+12,y+44,152,12),Color(.78,.85,.71))
	if recovery:_center_text("每回合恢复5生命",Rect2(x+12,y+60,152,12),Color(.78,.85,.71))

func _draw_battle() -> void:
	super._draw_battle()
	if view!="battle" or ui_mode not in ["inspect","move"] or not menu_items.is_empty() or busy or phase_time>0 or notice_time>0:return
	if ui_mode=="move":_draw_terrain_card();return
	if not game.unit_at(game.cursor).is_empty():return
	for boat in game.event_boats():
		if game.cursor!=Vector2i(boat.position[0],boat.position[1]):continue
		var screen=_battle_cell_screen(game.cursor);var x=120 if screen.x<128 else 8;var y=8 if screen.y>80 else 136
		_panel(Rect2(x,y,128,96));_text("居民船队",Vector2(x+12,y+14))
		var status="已抵达西岸" if boat.get("arrived",false) else "等待航路安全" if boat.get("stopped",false) else "沿水路前进"
		_text(status,Vector2(x+12,y+30));_text("船体"+str(int(boat.hp))+"/"+str(int(boat.max_hp)),Vector2(x+12,y+46))
		_draw_health(int(boat.hp),int(boat.max_hp),Vector2(x+12,y+66),"ally")
		return
	_draw_terrain_card()

func _draw_overview() -> void:
	draw_rect(Rect2(0,0,256,240),Color(.08,.12,.15))
	draw_texture_rect(_tex("res://assets/world_tiles/formal-world-overview.png"),Rect2(42,8,172,196),false)
	_center_text("西大陆 · 东群岛 · 神宫",Rect2(4,207,248,16))
	_center_text("确认返回当前地点",Rect2(4,225,248,12))

func _draw_chapter_end() -> void:
	draw_rect(Rect2(0,0,256,240),Color(.06,.1,.13));_panel(Rect2(12,20,232,196))
	_center_text("第二章完成" if game.chapter==2 else "第一章完成",Rect2(24,38,208,24),Color(.94,.88,.67))
	_center_text("没有归来的船" if game.chapter==2 else "庆典前夜",Rect2(24,74,208,20))
	_center_text("船团抵达西岸。\n艾琳被带往庆典广场。" if game.chapter==2 else "科兰已败，日光重返西大陆。",Rect2(24,108,208,32))
	_center_text("两队成长与伤亡已保存" if game.chapter==2 else "成长与伤亡已保存",Rect2(24,158,208,20))
	_center_text("确认打开菜单",Rect2(24,186,208,16))

func _cancel() -> void:
	if view=="plot":return
	if view=="overview":view="world";return
	super._cancel()


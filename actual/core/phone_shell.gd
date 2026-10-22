extends Control
## Phone controls occupy their own rails; the game keeps native integer pixels.
const GAME_SCENE = preload("res://scenes/main.tscn")
const MATERIAL = preload("res://assets/journey-home/journal-panel.png")
const FAST_KEY := -1
const LEFT_RAIL := 116
const RIGHT_RAIL := 70
const DIRECTION_KEYS := [KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT]
var game_view: SubViewport
var game_ui
var pixel_scale := 1
var game_rect := Rect2()
var safe_area := Rect2()
# Deterministic notch/home-indicator fixtures; actual devices use DisplayServer.
var safe_area_override := Rect2()
var buttons: Array = []
var fingers: Dictionary = {}
var contacts: Dictionary = {}
var blocked_contacts: Dictionary = {}
var layout_errors: Array = []
var last_size := Vector2.ZERO
var last_context := ""
var map_contacts: Dictionary = {}

func _ready() -> void:
	game_view = SubViewport.new()
	game_view.size = Vector2i(1704, 960)
	game_view.size_2d_override = Vector2i(426, 240)
	game_view.size_2d_override_stretch = true
	game_view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	game_view.handle_input_locally = true
	add_child(game_view)
	game_ui = GAME_SCENE.instantiate();game_ui.set_meta("phone",true);game_view.add_child(game_ui)
	game_ui.set_process_input(false)
	_layout()

func _process(_delta: float) -> void:
	if get_viewport_rect().size != last_size or _available_area() != safe_area:
		_release_all();_layout()
	_sync_controls()
	queue_redraw()

func _available_area() -> Rect2:
	var full=Rect2(Vector2.ZERO,get_viewport_rect().size)
	var requested=safe_area_override
	if not requested.has_area() and OS.has_feature("ios"):
		requested=Rect2(DisplayServer.get_display_safe_area())
	if requested.has_area():
		var visible=full.intersection(requested)
		if visible.size.x>full.size.x*.6 and visible.size.y>full.size.y*.6:return visible
	return full

func _layout() -> void:
	last_size = get_viewport_rect().size
	safe_area = _available_area()
	pixel_scale = maxi(1, floori(safe_area.size.y / 240.0))
	while pixel_scale > 1 and safe_area.size.x / pixel_scale < 256+LEFT_RAIL+RIGHT_RAIL: pixel_scale -= 1
	var width = clampi(floori(safe_area.size.x / pixel_scale) - LEFT_RAIL-RIGHT_RAIL, 256, 512)
	var logical = Vector2i(width, 240)
	game_view.size = logical * pixel_scale
	game_view.size_2d_override = logical
	var spare = safe_area.size.x - (width+LEFT_RAIL+RIGHT_RAIL)*pixel_scale
	game_rect = Rect2(Vector2(floorf(safe_area.position.x+LEFT_RAIL*pixel_scale+spare/2),floorf(safe_area.get_center().y-game_view.size.y/2.0)),game_view.size)
	last_context=_control_context();_build_buttons()

func _control_context() -> String:
	if game_ui.view=="combat":return "combat"
	if game_ui.view=="overview":return "overview"
	return "battle" if game_ui.view=="battle" else "general"

func _sync_controls() -> void:
	var context=_control_context()
	if context==last_context:return
	# A finger that confirmed an attack cannot become a held speed gesture.
	_release_all();last_context=context;_build_buttons()

func _add_button(key:int,rect:Rect2,text_:String="",arrow:String="") -> void:
	rect.position=rect.position.round()
	buttons.append({"key":key,"rect":rect,"hit_rect":rect if key in DIRECTION_KEYS else rect.grow(2),"arrow":arrow,"text":text_})

func _build_buttons() -> void:
	buttons.clear()
	var size=safe_area.size/pixel_scale
	var left_end=(game_rect.position.x-safe_area.position.x)/pixel_scale
	var right_begin=(game_rect.end.x-safe_area.position.x)/pixel_scale
	var left=left_end/2.0
	var right=(right_begin+size.x)/2.0
	if last_context=="combat":
		_add_button(FAST_KEY,Rect2(right-32,size.y/2.0-16,64,64),"按住\n加速")
		return
	var center=Vector2(left,size.y/2.0+12)
	for row in [[KEY_UP,Vector2(0,-36),"up"],[KEY_DOWN,Vector2(0,36),"down"],[KEY_LEFT,Vector2(-36,0),"left"],[KEY_RIGHT,Vector2(36,0),"right"]]:
		_add_button(row[0],Rect2(center+row[1]-Vector2(18,18),Vector2(36,36)),"",row[2])
	var actions=[[KEY_Z,"确认"],[KEY_X,"返回"]]
	if last_context=="battle":actions.append([KEY_E,"切换我方"])
	actions.append_array([[KEY_S,"菜单"],[KEY_TAB,"状态"]])
	if last_context=="overview":actions=[[KEY_EQUAL,"放大"],[KEY_MINUS,"缩小"],[KEY_R,"复位"],[KEY_X,"返回"]]
	var heights=[];var total=0.0
	for action in actions:
		var height=60.0 if last_context=="battle" and action[0]==KEY_S else 34.0
		heights.append(height);total+=height
	total+=(actions.size()-1)*8
	var top=(size.y-total)/2.0
	for i in range(actions.size()):
		_add_button(actions[i][0],Rect2(right-32,top,64,heights[i]),actions[i][1]);top+=heights[i]+8

func _can_cycle() -> bool:
	if game_ui.view!="battle" or game_ui.busy or game_ui.batch_running or game_ui.game.phase!="player" or not game_ui.menu_items.is_empty():return false
	return game_ui.ui_mode=="inspect" or (game_ui.ui_mode=="status" and game_ui.game.party.has(game_ui.status_id))

func _button_enabled(key:int) -> bool:
	if key==KEY_EQUAL:return game_ui.view=="overview" and game_ui.overview_zoom<3
	if key==KEY_MINUS:return game_ui.view=="overview" and game_ui.overview_zoom>1
	if key==KEY_E:return _can_cycle()
	if key==FAST_KEY:return game_ui.view=="combat"
	return true

func _send(key: int, pressed: bool) -> void:
	if key==FAST_KEY:
		game_ui.set_touch_fast_forward(pressed)
		return
	if key==KEY_E:
		if pressed and _can_cycle():
			if game_ui.ui_mode=="status":game_ui._cycle_status(1)
			else:game_ui._cycle_ready_unit(1)
		return
	var event = InputEventKey.new();event.physical_keycode = key;event.pressed = pressed
	game_ui._input(event)

func _button_at(position_: Vector2) -> int:
	var local = (position_ - safe_area.position) / pixel_scale
	for button in buttons:
		if button.hit_rect.has_point(local) and _button_enabled(int(button.key)):return int(button.key)
	return 0

func _release_finger(index:int) -> void:
	var key=int(fingers.get(index,0));fingers.erase(index)
	if key!=0 and key not in fingers.values():_send(key,false)

func _finger(index: int, position_: Vector2, pressed: bool, drag: bool=false) -> void:
	_sync_controls()
	if not pressed:
		_release_finger(index);contacts.erase(index);blocked_contacts.erase(index);map_contacts.erase(index);queue_redraw();return
	if not contacts.has(index):
		if drag:return
		contacts[index]=_button_at(position_);blocked_contacts.erase(index)
	elif not drag:
		# Ignore duplicate down events, including emulated mouse delivery.
		return
	if blocked_contacts.has(index):return
	if game_ui.view=="overview" and int(contacts[index])==0:
		if not drag and game_ui._overview_area().has_point((position_-game_rect.position)/pixel_scale-game_ui._canvas_offset()) and game_rect.has_point(position_):
			if map_contacts.is_empty():map_contacts[index]=position_
		elif drag and map_contacts.has(index):
			game_ui._overview_pan_pixels((position_-map_contacts[index])/pixel_scale);map_contacts[index]=position_
		return
	var origin=int(contacts[index]);var old=int(fingers.get(index,0));var key=_button_at(position_)
	if drag:
		if origin in DIRECTION_KEYS:
			if key not in DIRECTION_KEYS:key=0
		elif origin==FAST_KEY:
			if key!=FAST_KEY:key=0
		else:
			# Discrete actions fire once. Dragging across confirm/back/menu
			# never invokes another action or creates a map tap.
			if key!=origin:
				_release_finger(index);blocked_contacts[index]=true
			return
	if old!=key and old!=0:_release_finger(index)
	if key!=0 and old!=key:
		var already_held=key in fingers.values()
		fingers[index]=key
		if not already_held:_send(key,true)
	elif not drag and origin==0 and game_rect.has_point(position_):
		game_ui._mouse_accept((position_-game_rect.position)/pixel_scale)
	_sync_controls()
	queue_redraw()

func _release_all() -> void:
	if game_ui == null: return
	var keys=[]
	for key in fingers.values():
		if not keys.has(key):keys.append(key)
	fingers.clear();map_contacts.clear()
	for key in keys:_send(int(key),false)
	game_ui.set_touch_fast_forward(false);game_ui.held_direction=Vector2i.ZERO
	for index in contacts:blocked_contacts[index]=true

func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_APPLICATION_PAUSED]:
		_release_all();contacts.clear();blocked_contacts.clear()

func _input(event: InputEvent) -> void:
	if game_ui == null: return
	if event is InputEventScreenTouch:
		_finger(event.index,event.position,event.pressed);get_viewport().set_input_as_handled()
	elif event is InputEventScreenDrag:
		_finger(event.index,event.position,true,true);get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.device != InputEvent.DEVICE_ID_EMULATION:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_finger(-1,event.position,event.pressed);get_viewport().set_input_as_handled()
	elif event is InputEventKey:
		game_ui._input(event);get_viewport().set_input_as_handled()

func _panel(rect: Rect2, pressed: bool, enabled:bool=true) -> void:
	if pressed:
		var glow = StyleBoxFlat.new();glow.bg_color = Color.TRANSPARENT
		glow.shadow_color = Color(0.8,0.65,0.35,0.35);glow.shadow_size = 4
		draw_style_box(glow,rect.grow(-3))
	var tint = Color(1.1,1.05,0.92) if pressed else Color(0.72,0.8,0.9) if enabled else Color(0.43,0.49,0.56)
	var dx = [rect.position.x,rect.position.x+8,rect.end.x-8]
	var dy = [rect.position.y,rect.position.y+8,rect.end.y-8]
	var dw = [8,rect.size.x-16,8];var dh = [8,rect.size.y-16,8]
	for y in range(3):
		for x in range(3):
			var sx = 40 if x == 1 else 0 if x == 0 else MATERIAL.get_width()-8
			var sy = 40 if y == 1 else 0 if y == 0 else MATERIAL.get_height()-8
			draw_texture_rect_region(MATERIAL,Rect2(dx[x],dy[y],dw[x],dh[y]),Rect2(sx,sy,1 if x==1 else 8,1 if y==1 else 8),tint)

func _label(value:String,rect:Rect2,enabled:bool) -> void:
	var lines=value.split("\n");var height=12+(lines.size()-1)*16
	var y=roundf(rect.get_center().y-height/2.0)
	for line in lines:
		var ink=Rect2(Vector2(roundf(rect.get_center().x-game_ui._preview_text_width(line)/2.0),y),Vector2(game_ui._preview_text_width(line),12))
		if not rect.grow(-8).encloses(ink):layout_errors.append("text safe area "+value)
		var cursor=ink.position
		for character in line:
			var glyph:Dictionary=game_ui._preview_glyph(character)
			if glyph.is_empty():layout_errors.append("missing control glyph "+character);continue
			var r:Array=glyph.rect
			draw_texture_rect_region(game_ui._tex(game_ui.chinese_font.path),Rect2(cursor,Vector2(r[2],r[3])),Rect2(r[0],r[1],r[2],r[3]),Color("eee8d2") if enabled else Color("8d9aaa"))
			cursor.x+=float(glyph.advance)
		y+=16

func _draw() -> void:
	draw_rect(get_viewport_rect(),Color("0c151f"))
	if game_view == null: return
	draw_texture_rect(game_view.get_texture(),game_rect,false)
	draw_set_transform(safe_area.position,0,Vector2(pixel_scale,pixel_scale))
	layout_errors.clear()
	for i in range(buttons.size()):
		var button:Dictionary=buttons[i];var rect:Rect2=button.rect;var key=int(button.key);var enabled=_button_enabled(key)
		var physical=Rect2(safe_area.position+button.hit_rect.position*pixel_scale,button.hit_rect.size*pixel_scale)
		if not safe_area.encloses(physical):layout_errors.append("touch outside safe area "+str(key))
		if game_rect.intersects(physical):layout_errors.append("touch covers game "+str(key))
		for j in range(i):
			if button.hit_rect.intersects(buttons[j].hit_rect):layout_errors.append("touch targets overlap "+str(key))
		_panel(rect,key in fingers.values(),enabled)
		if not str(button.arrow).is_empty():
			var texture = game_ui._tex(game_ui.cursors.arrows[button.arrow].path)
			var ink = Rect2((rect.get_center()-texture.get_size()/2).round(),texture.get_size())
			if not rect.grow(-8).encloses(ink): layout_errors.append("arrow safe area "+str(button.arrow))
			draw_texture(texture,ink.position)
		else:
			var value="加速中\n松开恢复" if key==FAST_KEY and key in fingers.values() else str(button.text)
			if key==KEY_S and game_ui.view=="battle":value="菜单\n"+str(game_ui.game.turn)+"回合" if game_ui.game.turn<1000 else "菜单\n回合\n"+str(game_ui.game.turn)
			_label(value,rect,enabled)
	draw_set_transform(Vector2.ZERO)

extends Control

const MapCanvas = preload("res://scripts/map_canvas.gd")
var world: Dictionary
var by_id: Dictionary = {}
var selected := "W06"
var chapter := "all"
var map: Control
var detail: VBoxContainer
var directory: VBoxContainer
var chapter_select: OptionButton
var font: SystemFont
var selectable: Dictionary = {}

func material(color: Color, padding := 14, glow := false) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = color
	style.set_corner_radius_all(7)
	style.content_margin_left = padding
	style.content_margin_right = padding
	style.content_margin_top = padding
	style.content_margin_bottom = padding
	style.shadow_color = Color(.55,.83,.8,.3) if glow else Color(0,0,0,.18)
	style.shadow_size = 9 if glow else 3
	return style

func label(text: String, size_px := 16, color := Color("e7e9da")) -> Label:
	var node := Label.new()
	node.text = text
	node.add_theme_font_size_override("font_size",size_px)
	node.add_theme_color_override("font_color",color)
	return node

func button(text: String, action: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size.y = 40
	b.add_theme_stylebox_override("normal",material(Color("203c43"),12))
	b.add_theme_stylebox_override("hover",material(Color("2c4c51"),12))
	b.add_theme_stylebox_override("pressed",material(Color("385654"),12))
	b.add_theme_stylebox_override("focus",material(Color(0,0,0,0),12,true))
	b.pressed.connect(action)
	return b

func _ready() -> void:
	world = JSON.parse_string(FileAccess.get_file_as_string("res://data/world_map.json"))
	for n in world.nodes: by_id[n.id] = n
	font = SystemFont.new()
	font.font_names = PackedStringArray(["PingFang SC","Heiti SC","Noto Sans CJK SC"])
	var ui_theme := Theme.new()
	ui_theme.default_font = font
	ui_theme.default_font_size = 14
	theme = ui_theme
	var margin := MarginContainer.new()
	margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	for side in ["left","right","top","bottom"]: margin.add_theme_constant_override("margin_"+side,28)
	add_child(margin)
	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation",18)
	margin.add_child(root)
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation",20)
	root.add_child(header)
	var titles := VBoxContainer.new()
	titles.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(titles)
	titles.add_child(label("REVENGE MEMORIES",12,Color("e3bd78")))
	titles.add_child(label("西大陆与东群岛",29))
	header.add_child(label("现代像素 · 世界地图审阅 01",14,Color("99b5b9")))
	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation",24)
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(columns)
	var left := VBoxContainer.new()
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.add_theme_constant_override("separation",12)
	columns.add_child(left)
	var toolbar := HBoxContainer.new()
	toolbar.add_theme_constant_override("separation",10)
	left.add_child(toolbar)
	chapter_select = OptionButton.new()
	for text in ["完整世界","第一章 · 雪下的名字","第二章 · 没有归来的船","第三章 · 另一种胜利","第四章 · 故人的另一面","第五章 · 完整的天空"]: chapter_select.add_item(text)
	chapter_select.custom_minimum_size = Vector2(245,42)
	chapter_select.add_theme_stylebox_override("normal",material(Color("203c43"),14))
	chapter_select.add_theme_stylebox_override("hover",material(Color("2c4c51"),14))
	chapter_select.add_theme_stylebox_override("focus",material(Color(0,0,0,0),14,true))
	chapter_select.item_selected.connect(set_chapter)
	toolbar.add_child(chapter_select)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	toolbar.add_child(spacer)
	var roads := button("显示路线",func(): map.show_routes = not map.show_routes; map.queue_redraw())
	roads.toggle_mode = true
	toolbar.add_child(roads)
	var names := button("地点名称",func(): map.show_names = not map.show_names; map.queue_redraw())
	names.toggle_mode = true
	toolbar.add_child(names)
	map = MapCanvas.new()
	map.world = world
	map.font = font
	map.terrain = load("res://assets/world/world-geography.png")
	map.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map.place_selected.connect(select_place)
	left.add_child(map)
	var footer := label("西大陆 · 胡纳普         东群岛 · 艾琳         神宫 · 第五章合军",13,Color("b4ccc9"))
	footer.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	footer.custom_minimum_size.y = 30
	left.add_child(footer)
	var right := VBoxContainer.new()
	right.custom_minimum_size.x = 316
	right.add_theme_constant_override("separation",16)
	columns.add_child(right)
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel",material(Color("18343d"),24))
	right.add_child(card)
	detail = VBoxContainer.new()
	detail.add_theme_constant_override("separation",12)
	card.add_child(detail)
	right.add_child(label("旅途地点 · 39 处",16,Color("b4ccc9")))
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(scroll)
	directory = VBoxContainer.new()
	directory.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	directory.add_theme_constant_override("separation",5)
	scroll.add_child(directory)
	var note := label("当前为画风与地图预览。\n战斗和剧情流程将在后续接入。",12,Color("99b5b9"))
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	right.add_child(note)
	build_directory()
	select_place(selected)

func clear_children(container: Node) -> void:
	for child in container.get_children():
		container.remove_child(child)
		child.queue_free()

func set_chapter(index: int) -> void:
	chapter = "all" if index == 0 else str(index)
	map.chapter = chapter
	build_directory()
	if not map.eligible(by_id[selected]):
		for n in world.nodes:
			if map.eligible(n): select_place(n.id); break
	map.queue_redraw()

func build_directory() -> void:
	clear_children(directory)
	selectable.clear()
	for n in world.nodes:
		if not map.eligible(n): continue
		var id: String = n.id
		var b := button(n.id+"   "+n.name,func(): select_place(id))
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.toggle_mode = true
		b.tooltip_text = n.region+" · 第"+n.chapter+"章"
		directory.add_child(b)
		selectable[id] = b

func select_place(id: String) -> void:
	selected = id
	map.selected = id
	map.queue_redraw()
	var n: Dictionary = by_id[id]
	clear_children(detail)
	detail.add_child(label(n.region+" · "+id,12,Color("e3bd78")))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation",12)
	detail.add_child(row)
	if not str(n.sprite).is_empty():
		var art := TextureRect.new()
		art.texture = load("res://"+n.sprite)
		art.custom_minimum_size = Vector2(88,88)
		art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		row.add_child(art)
	var names := VBoxContainer.new()
	names.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	names.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_child(names)
	var name_label := label(n.name,23)
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	names.add_child(name_label)
	var kind_label := label(n.kind,12,Color("99b5b9"))
	kind_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	names.add_child(kind_label)
	var description := label(n.description,14,Color("d2dbd6"))
	description.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	description.add_theme_constant_override("line_spacing",7)
	detail.add_child(description)
	detail.add_child(label(("可选支线" if id.begins_with("S") else "主线地点")+" · 第"+n.chapter+"章",12,Color("96d3d1")))
	detail.add_child(label("相连道路",12,Color("99b5b9")))
	for e in world.edges:
		if e.a != id and e.b != id: continue
		var other: String = e.b if e.a == id else e.a
		var b := button(by_id[other].name+" · "+e.mode,func():
			if not map.eligible(by_id[other]): chapter_select.select(0); set_chapter(0)
			select_place(other))
		b.tooltip_text = e.gate
		detail.add_child(b)
	for key in selectable: selectable[key].button_pressed = key == id

extends Control

signal place_selected(id: String)
var world: Dictionary
var terrain: Texture2D
var glow: GradientTexture2D
var selected := "W06"
var chapter := "all"
var show_routes := false
var show_names := false
var font: Font
var map_rect := Rect2()
var label_rects: Array[Rect2] = []

func _ready() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	var gradient := Gradient.new()
	gradient.set_color(0, Color(1, .81, .4, .6))
	gradient.set_color(1, Color(1, .81, .4, 0))
	glow = GradientTexture2D.new()
	glow.gradient = gradient
	glow.fill = GradientTexture2D.FILL_RADIAL
	glow.fill_from = Vector2(.5, .5)
	glow.fill_to = Vector2(1, .5)
	resized.connect(queue_redraw)

func eligible(n: Dictionary) -> bool:
	if chapter == "all": return true
	var parts: PackedStringArray = str(n.chapter).split("—")
	if parts.size() == 2:
		return int(chapter) >= int(parts[0]) and int(chapter) <= int(parts[1])
	return str(n.chapter) == chapter

func map_position(n: Dictionary) -> Vector2:
	return map_rect.position + Vector2(n.position[0], n.position[1]) * map_rect.size / Vector2(1176, 1344)

func _draw() -> void:
	if not terrain: return
	var scale_factor := minf(size.x / 1176.0, size.y / 1344.0)
	var map_size := Vector2(1176, 1344) * scale_factor
	map_rect = Rect2((size-map_size)*.5, map_size)
	draw_texture_rect(terrain, map_rect, false)
	if show_routes:
		for e in world.edges:
			if chapter != "all" and str(e.chapter) != chapter: continue
			var pts := PackedVector2Array()
			for p in e.points: pts.append(map_rect.position + Vector2(p[0],p[1])*scale_factor)
			var color := Color("e7c186")
			if e.style == "sea": color = Color("b9e7e5")
			if e.style == "sacred": color = Color("ffe5a1")
			color.a = .65
			if e.a == selected or e.b == selected: color.a = .95
			if e.style == "land": draw_polyline(pts,color,2)
			else:
				var distance := 0.0
				for i in range(pts.size()-1):
					var length := pts[i].distance_to(pts[i+1])
					for j in range(int(length)):
						if int(distance+j)%8<2:
							draw_circle(pts[i].lerp(pts[i+1],j/maxf(length,1)),1,color)
					distance += length
	label_rects.clear()
	var ordered: Array = world.nodes.duplicate()
	ordered.sort_custom(func(a,b): return a.id == selected and b.id != selected)
	for n in ordered:
		if not eligible(n): continue
		var pos := map_position(n)
		if n.id == selected:
			draw_texture_rect(glow,Rect2(pos-Vector2(29,41),Vector2(58,58)),false)
		if not show_names and n.id != selected: continue
		var text_size := font.get_string_size(n.name,HORIZONTAL_ALIGNMENT_LEFT,-1,13)
		var rect := Rect2(pos+Vector2(-text_size.x*.5-10,5),Vector2(text_size.x+20,27))
		var blocked := not map_rect.encloses(rect)
		for previous in label_rects:
			if previous.grow(4).intersects(rect): blocked = true
		if blocked and n.id != selected: continue
		var style := StyleBoxFlat.new()
		style.bg_color = Color(.035,.12,.16,.94)
		style.set_corner_radius_all(4)
		style.shadow_color = Color(0,0,0,.3)
		style.shadow_size = 4
		draw_style_box(style,rect)
		draw_string(font,Vector2(rect.position.x+10,rect.position.y+(27-font.get_height(13))*.5+font.get_ascent(13)),n.name,HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("f1ecd7"))
		label_rects.append(rect)

func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var closest := ""
		var distance := 32.0
		for n in world.nodes:
			if not eligible(n): continue
			var d := (map_position(n)-Vector2(0,13)).distance_to(event.position)
			if d < distance: distance = d; closest = n.id
		if not closest.is_empty(): place_selected.emit(closest)
		accept_event()

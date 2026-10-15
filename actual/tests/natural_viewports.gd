extends SceneTree
const Border=preload("res://core/environment_border.gd")
var errors: Array=[]
var checks=0
func check(ok: bool,label: String) -> void:
	checks+=1
	if not ok:errors.append(label)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false)
	var dimensions=[Vector2i(256,240),Vector2i(384,240),Vector2i(426,240),Vector2i(426,266),Vector2i(562,260)]
	for group in ["hubs","battles"]:
		for code in ui.nature_layouts[group]:
			var layout: Dictionary=ui.nature_layouts[group][code]
			for canvas in dimensions:
				var visible=Rect2((Vector2(256,240)-Vector2(canvas))/2,Vector2(canvas))
				for origin in [Vector2(16,24),Vector2(-8,-16)]:
					var props=Border.visible_props(layout.props,ui.nature_sprites,origin,visible)
					var expected=0
					for source_prop in layout.props:
						var source_sprite=ui.nature_sprites[str(source_prop.key)]
						var source_rect=Rect2(Vector2(source_prop.position[0],source_prop.position[1])+origin,Vector2(source_sprite.size[0],source_sprite.size[1]))
						if visible.encloses(source_rect):expected+=1
					check(props.size()==expected,code+" complete objects visible, partial objects omitted "+str(canvas))
					for prop in props:
						var sprite=ui.nature_sprites[str(prop.key)]
						var rect=Rect2(Vector2(prop.position[0],prop.position[1])+origin,Vector2(sprite.size[0],sprite.size[1]))
						check(visible.encloses(rect),code+" full silhouette in viewport "+str(canvas))
	for canvas in dimensions:
		var visible=Rect2((Vector2(256,240)-Vector2(canvas))/2,Vector2(canvas))
		var origin=Vector2(-160,-768)
		var props=Border.visible_props(ui.world.natural_props,ui.nature_sprites,origin,visible)
		check(not props.is_empty(),"world landscape contains nature objects "+str(canvas))
		for prop in props:
			var sprite=ui.nature_sprites[str(prop.key)];var size=prop.get("size",sprite.size)
			var rect=Rect2(Vector2(prop.position[0],prop.position[1])+origin,Vector2(size[0],size[1]))
			check(visible.encloses(rect),"world complete geographic silhouette "+str(canvas))
	var f=FileAccess.open("res://reports/natural-0.1.3/viewport-checks.json",FileAccess.WRITE)
	f.store_string(JSON.stringify({"passed":errors.is_empty(),"checks":checks,"errors":errors,"canvas_sizes":dimensions,"scope":"Actual renderer visibility function, all 17 exterior plans plus scaled world symbols, two camera positions and five landscape sizes"},"  "));f.close()
	print("NATURAL_VIEWPORTS ",checks," checks; ",errors)
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

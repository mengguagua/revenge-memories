extends SceneTree
const Party=preload("res://core/party_sprites.gd")
const Reviewed=preload("res://core/reviewed_animations.gd")
var checks:=0
var errors:Array=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks+=1
	if not ok:errors.append(label);push_error(label)
func pixels(art:Dictionary)->Image:
	var image=load(art.path).get_image();image.convert(Image.FORMAT_RGBA8)
	# Texture import may fill RGB beneath zero alpha; compare visible pixels and alpha.
	for y in range(image.get_height()):
		for x in range(image.get_width()):
			if image.get_pixel(x,y).a==0:image.set_pixel(x,y,Color(0,0,0,0))
	return image
func run():
	var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/mercenary-map-test-unused-save.json";ui.game.new_game()
	ui.game.world_node=int(ui.game.stages[101].node)
	check(ui.game.start_battle(101),"real M11 starts")
	var units_before=ui.game.units.duplicate(true)
	var roster_before=ui.game.roster.duplicate(true)
	var quest_before=ui.game.flags.quest.duplicate(true)
	var actors:Array=[]
	for side in ["player","enemy"]:
		var actor:Dictionary=ui.game.find_unit("hunapu").duplicate(true)
		actor.id="mercenary-test-"+side;actor.class_id=8;actor.side=side
		actors.append(actor)
	for id in ["M11_refugees0","M11_refugees1"]:
		var actor:Dictionary=ui.game.find_unit(id)
		check(not actor.is_empty(),"real escort exists "+id)
		check(int(actor.class_id)==14 and actor.neutral and actor.temporary and not actor.controllable,"escort remains neutral class14 "+id)
		check(actor.quest_kind=="escort" and int(actor.move)==3,"escort task and movement points retained "+id)
		actors.append(actor)
	for actor in actors:
		var id=str(actor.id)
		var idle=Party.sprite("map",actor,1)
		var walk=Party.sprite("map_move",actor,1)
		check(idle.art_revision=="mercenary-eyes-v2-20261019" and walk.art_revision=="mercenary-left-neck-v3-20261019",id+" accepted art revisions")
		check(idle.static_facing and not walk.static_facing,id+" separate idle and walk")
		check(PackedInt32Array(idle.native_cycle)==PackedInt32Array([0,1,2,1]) and PackedInt32Array(idle.cycle_ticks)==PackedInt32Array([14,8,14,8]),id+" native idle timing")
		for sample in [[0,0],[14,1],[22,2],[36,1]]:
			ui.elapsed=(float(sample[0])+0.01)/60.0988
			check(ui._native_map_pose(idle)==int(sample[1]),id+" runtime idle phase "+str(sample[0]))
		var is_refugee=bool(actor.get("neutral",false))
		var palette="8f986fff" if is_refugee else "ae5148ff" if actor.side=="enemy" else "3976b5ff"
		for art in [idle,walk]:
			var image=pixels(art)
			check(int(art.native_density)==4 and image.get_width()==int(art.frame_size[0])*int(art.frames),id+" four-times registered atlas")
			check(Vector2(art.anchor[0],art.anchor[1])-Vector2(art.tile_origin[0],art.tile_origin[1])==Vector2(8,16),id+" foot anchor")
			check(art.ground_shadow.path.ends_with("/mercenary-ground-shadow.png") and PackedInt32Array(art.ground_shadow.size)==PackedInt32Array([11,3]) and is_equal_approx(float(art.ground_shadow.alpha),0.38),id+" continuous shadow")
			var colors:Dictionary={}
			for y in range(image.get_height()):
				for x in range(image.get_width()):
					var color=image.get_pixel(x,y)
					if color.a>0:colors[color.to_html(true)]=true
			check(colors.size()==4 and colors.has(palette),id+" four colors and correct faction")
		var walking=pixels(walk)
		for direction in ["up","right","down","left"]:
			var expected={"up":[0,1],"right":[2,3],"down":[4,5],"left":[6,7]}[direction]
			check(PackedInt32Array(walk.directions[direction])==PackedInt32Array(expected),id+" directional phases "+direction)
		check(walking.get_region(Rect2i(768,0,128,82)).get_data()==walking.get_region(Rect2i(896,0,128,82)).get_data(),id+" left head neck and upper body fixed")
		check(walking.get_region(Rect2i(768,82,128,14)).get_data()!=walking.get_region(Rect2i(896,82,128,14)).get_data(),id+" left straight and stride legs")
		for point in [[2,69,43],[3,69,43],[4,64,46],[4,70,46],[5,64,46],[5,70,46],[6,65,47],[7,65,47]]:
			check(walking.get_pixel(int(point[0])*128+int(point[1]),int(point[2])).to_html(true)=="172638ff",id+" accepted eye "+str(point))
		var standing=pixels(idle)
		for x in [44,50]:check(standing.get_pixel(x,31).to_html(true)=="172638ff",id+" two idle eyes "+str(x))
		if is_refugee:
			var previous=Party.data().classes.civilian.map_move
			check(int(walk.native_move_ticks)==int(previous.native_move_ticks) and int(walk.native_move_ticks)==16,id+" escort animation speed retained")
			ui.moving_id=id;check(ui._map_unit_sprite(actor).path==walk.path,id+" real moving UI selector")
			ui.moving_id="";check(ui._map_unit_sprite(actor).path==idle.path,id+" real idle UI selector")
		else:check(not walk.has("native_move_ticks"),id+" existing mercenary movement controller retained")
	var refugee:Dictionary=ui.game.find_unit("M11_refugees0").duplicate(true)
	for change in [{"id":"M12_refugees0"},{"id":"unrelated-civilian"},{"class_id":8},{"side":"enemy"},{"event_object":true}]:
		var actor:Dictionary=refugee.duplicate(true);actor.merge(change,true)
		check(Reviewed.map_sprite("map",actor).is_empty() and Reviewed.map_sprite("map_move",actor).is_empty(),"neutral alias is restricted "+str(change))
	for kind in ["hub","world"]:check(Reviewed.map_sprite(kind,refugee).is_empty(),"escort alias excludes "+kind)
	var ordinary:Dictionary=refugee.duplicate(true);ordinary.id="ordinary-villager";ordinary.neutral=false
	check(Reviewed.map_sprite("map",ordinary).path==Reviewed.data().maps["14_ally"]["tactical-idle"].path,"ordinary villagers keep their own art")
	for cid in [6,12,21]:
		var actor:Dictionary=ui.game.find_unit("hunapu").duplicate(true);actor.class_id=cid
		check(Party.sprite("map",actor,1).path==Reviewed.data().maps[str(cid)+"_ally"]["tactical-idle"].path,"accepted class retained "+str(cid))
	check(ui.game.units==units_before and ui.game.roster==roster_before and ui.game.flags.quest==quest_before,"visual selection leaves actors and quest data untouched")
	var result={"passed":errors.is_empty(),"checks":checks,"errors":errors,"version":ProjectSettings.get_setting("application/config/version")}
	var output=OS.get_environment("MERCENARY_MAP_REPORT")
	if output.is_empty():output="res://reports/mercenary-map-test-20261019/runtime.json"
	var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(result,"  "));file.close()
	print("MERCENARY_MAP_TEST ",JSON.stringify(result))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

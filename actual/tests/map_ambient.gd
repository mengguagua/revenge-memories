extends SceneTree
const State=preload("res://core/game_state.gd")
const Ambient=preload("res://core/map_ambient.gd")
var errors:Array[String]=[]
func check(ok:bool,message:String)->void:
	if not ok:errors.append(message);push_error(message)
func _initialize()->void:
	var g=State.new()
	var fx=Ambient.new()
	var ui={"game":g}
	var tested=0
	for id in g.stages:
		var stage=g.stages[id]
		if stage.get("training",false):continue
		g.stage_id=id;g.battle_data=stage.duplicate(true)
		var tiles=g.battle_data.map.tiles.duplicate()
		var rng=g.rng_state
		check(fx.prepare(ui),"all battle maps have an environment profile "+stage.code)
		for at in fx.water:check(g.in_bounds(at) and g.category(at)==7,"water effects remain on water "+stage.code+str(at))
		for strip in fx.ground:
			for x in range(int(strip.position.x),int(strip.end.x),16):
				check(not fx._indoors(Vector2(x+8,strip.position.y+8)),"cloud shadows exclude interior rooms "+stage.code)
		check(tiles==g.battle_data.map.tiles and rng==g.rng_state,"profile preparation preserves terrain and RNG "+stage.code)
		if stage.code=="M11":check(fx.water.size()==40,"M11 uses the live22x18map instead of the stale36x28visual helper")
		if stage.code in ["S11","S22","F51","F52","S51"]:check(not fx.profile.has("flakes") and not fx.profile.get("shadows",false) and not fx.profile.get("trees",false),"underground rooms exclude exterior weather "+stage.code)
		if stage.code in ["F43","S42","F52","S51"]:check(not fx.profile.get("shore",false),"wetlands and interior rooms have no beach surf "+stage.code)
		for at in fx.wind_cells:check(not fx._indoors(Vector2(at)*16+Vector2(8,8)),"salt/sand wind excludes indoor floors "+stage.code)
		if stage.code=="S51":check(fx.lamps.size()==4 and fx.water.is_empty(),"library light uses four existing lamps and no exterior water")
		for cell in fx.profile.get("wall_torches",[]):
			check(g.category(Vector2i(cell[0],cell[1])) in [5,12],"wall torches stay outside walkable passages "+stage.code)
		tested+=1
	g.stage_id=202;g.battle_data=g.stages[202].duplicate(true)
	fx.prepare(ui)
	var bridge=g.battle_data.objects.filter(func(o):return o.id=="reserve_bridge")[0]
	for cell in bridge.opens:check(fx.water.has(Vector2i(cell[0],cell[1])),"closed reserve bridge is water")
	g.ChapterTwo.open_object(g,bridge)
	fx.prepare(ui)
	for cell in bridge.opens:check(not fx.water.has(Vector2i(cell[0],cell[1])),"lowered reserve bridge sheds water animation")
	check(tested==40,"all40battle maps are covered")
	print("MAP_AMBIENT ",tested," maps ", "PASS" if errors.is_empty() else errors)
	quit(0 if errors.is_empty() else 1)

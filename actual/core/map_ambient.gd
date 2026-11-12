extends RefCounted
## Presentation only. Coordinates are native map pixels, independent of camera
## and game RNG. PixelFX-derived sprite sheets and loop techniques are MIT.
const ROOT="res://assets/map-ambient-20261112/"
const DIRECTIONS=[Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]
var enabled:=true
var profiles:Dictionary={}
var effects:Dictionary={}
var profile:Dictionary={}
var cache_key:=""
var water:Array[Vector2i]=[]
var shores:Array=[]
var ground:Array[Rect2]=[]
var interior:Array[Rect2]=[]
var fires:Array[Vector2]=[]
var lamps:Array[Vector2]=[]
var wind_cells:Array[Vector2i]=[]
var footprint:=Vector2.ZERO
var profile_code:=""

func prepare(ui) -> bool:
	if not enabled:return false
	var stage:Dictionary=ui.game.battle_data
	if profiles.is_empty():
		profiles=ui.game.read_json(ROOT+"profiles.json")
		effects=ui.game.read_json(ROOT+"effects.json")
	profile=profiles.get(str(stage.get("code","")),{})
	profile_code=str(stage.get("code",""))
	if profile.is_empty():return false
	var key=str([stage.code,stage.map.width,stage.map.height,stage.map.tiles.hash(),stage.get("tactical_review_version","")])
	if key==cache_key:return true
	cache_key=key
	water.clear();shores.clear();ground.clear();interior.clear();fires.clear();lamps.clear();wind_cells.clear()
	var width=int(stage.map.width);var height=int(stage.map.height)
	footprint=Vector2(width,height)*16
	for b in profile.get("inside",[]):
		interior.append(Rect2(b[0]*16,b[1]*16,(b[2]-b[0]+1)*16,(b[3]-b[1]+1)*16))
	var materials:Array=stage.get("visual_ground",[])
	for y in range(mini(height,materials.size())):
		for x in range(mini(width,str(materials[y]).length())):
			if str(materials[y])[x] in profile.get("interior_materials",[]):
				interior.append(Rect2(x*16,y*16,16,16))
	for y in range(height):
		var run=-1
		for x in range(width+1):
			var at=Vector2i(x,y)
			var category=ui.game.category(at) if x<width else -1
			var outside=x<width and not _indoors(Vector2(at)*16+Vector2(8,8))
			var surface=outside and category not in [-1,5,12]
			if surface and y<materials.size() and x<str(materials[y]).length() and str(materials[y])[x] in profile.get("wind_materials",[]):wind_cells.append(at)
			if surface and run<0:run=x
			if not surface and run>=0:
				ground.append(Rect2(run*16,y*16,(x-run)*16,16));run=-1
			if category!=7:continue
			water.append(at)
			if not profile.get("shore",false):continue
			for side in range(4):
				var next=at+DIRECTIONS[side]
				if ui.game.in_bounds(next) and ui.game.category(next)==2:
					shores.append({"cell":at,"side":side})
	for prop in stage.get("art_props",[]):
		if profile.get("fire",false) and str(prop.path).ends_with("/brazier.png"):
			fires.append(Vector2(prop.position[0]+8,prop.position[1]+3))
		if profile.get("lamps",false) and str(prop.path).ends_with("/ritual_lamp.png"):
			lamps.append(Vector2(prop.position[0]+8,prop.position[1]+7))
	return true

func _indoors(at:Vector2) -> bool:
	return interior.any(func(rect):return rect.has_point(at))

func _sheet(ui,name:String,at:Vector2,time:float,tint:Color=Color.WHITE) -> void:
	var spec:Dictionary=effects[name]
	var size=Vector2(spec.size[0],spec.size[1])
	var frame=posmod(int(floor(time*float(spec.fps))),int(spec.frames))
	var columns=int(spec.columns)
	var region=Rect2(Vector2(frame%columns,floori(float(frame)/columns))*size,size)
	if ui._visible_native_rect().intersects(Rect2(at,size)):
		ui.draw_texture_rect_region(ui._tex(str(spec.path)),Rect2(at.round(),size),region,tint)

func draw_surface(ui,origin:Vector2,tint:Color) -> void:
	if not prepare(ui):return
	var time=ui.elapsed
	var visible=ui._visible_native_rect()
	# Water is sampled from the current collision categories, including opened
	# bridges. Effects are below architecture, boats, bridges and all units.
	for cell in water:
		var seed=posmod(cell.x*37+cell.y*19,13)
		var at=origin+Vector2(cell)*16
		if not visible.intersects(Rect2(at,Vector2(16,16))):continue
		if profile.get("water_style","")=="still" or profile.climate in ["cave","interior","marsh","salt"]:
			if seed<2:
				var frame=posmod(int(floor((time+seed*.31)*16)),32)
				var source=Rect2((frame%8)*32+8,floori(float(frame)/8)*16,16,16)
				ui.draw_texture_rect_region(ui._tex(str(effects.ripple.path)),Rect2(at,Vector2(16,16)),source,tint*Color(1,1,1,.8))
		elif seed<4:
			_sheet(ui,"sheen",at,time+seed*.19,tint)
	# Keep surface motion around ocean maps when the camera exposes their border.
	if ui.game.battle_data.get("surroundings","")=="sea" and profile.climate!="marsh":
		for y in range(floori((visible.position.y-origin.y)/16),ceili((visible.end.y-origin.y)/16)):
			for x in range(floori((visible.position.x-origin.x)/16),ceili((visible.end.x-origin.x)/16)):
				if x>=0 and y>=0 and x<footprint.x/16 and y<footprint.y/16:continue
				if posmod(x*37+y*19,13)<4:_sheet(ui,"sheen",origin+Vector2(x,y)*16,time+posmod(x+y,7)*.19,tint)
	for edge in shores:
		var at=origin+Vector2(edge.cell)*16
		if not visible.intersects(Rect2(at,Vector2(16,16))):continue
		var frame=posmod(int(floor((time+posmod(edge.cell.x+edge.cell.y,4)*.13)*16)),32)+int(edge.side)*32
		var source=Rect2((frame%8)*16,floori(float(frame)/8)*16,16,16)
		ui.draw_texture_rect_region(ui._tex(str(effects.foam.path)),Rect2(at,Vector2(16,16)),source,tint)
	if profile.get("shadows",false):
		var texture=ui._tex(str(effects.shadow.path))
		for index in range(3):
			var phase=time*TAU/8+index*2.1
			var left=Vector2(footprint.x*(.12+index*.27)+sin(phase)*24,footprint.y*(.17+index*.2)+cos(phase)*10).floor()
			var rect=Rect2(left,Vector2(192,96))
			for strip in ground:
				var clip=rect.intersection(strip)
				if not clip.has_area() or not visible.intersects(Rect2(clip.position+origin,clip.size)):continue
				ui.draw_texture_rect_region(texture,Rect2(clip.position+origin,clip.size),Rect2((clip.position-left)/2,clip.size/2),Color(1,1,1,1))

func draw_tree(ui,prop:Dictionary,sprite:Dictionary,origin:Vector2,tint:Color) -> bool:
	if not enabled or profile.is_empty() or not profile.get("trees",false):return false
	if ui.game.mode not in ["battle","victory","defeat"] or str(ui.game.battle_data.get("code",""))!=profile_code:return false
	if str(sprite.get("kind","")) not in ["forest","snow_forest"]:return false
	var texture=ui._tex(str(sprite.path))
	var size=Vector2(prop.get("size",sprite.size)[0],prop.get("size",sprite.size)[1])
	var at=origin+Vector2(prop.position[0],prop.position[1])
	if not ui._visible_native_rect().intersects(Rect2(at-Vector2(1,0),size+Vector2(2,0))):return true
	var phase=ui.elapsed*TAU/6+float(prop.position[0]+prop.position[1])*.037
	# Only the treetop breathes from rest to one adjacent pixel and back.
	# Its total excursion is halved (1px rather than -1px to +1px), with
	# the lower crown, trunk and roots fixed. No subpixel blur or stretching.
	var crown=int(size.y*.42)
	var direction=1 if posmod(int(prop.position[0])+int(prop.position[1]),3)==0 else -1
	for y in range(0,int(size.y),4):
		var h=mini(4,int(size.y)-y)
		var shift=0
		if y<crown:
			var sway=sin(phase-float(y)*.035)*(1.0-float(y)/size.y)
			shift=direction if sway>.58 else 0
		var dest=Rect2(at+Vector2(shift,y),Vector2(size.x,h))
		if prop.get("flip",false):dest.size.x=-dest.size.x
		var ratio=texture.get_size()/size
		ui.draw_texture_rect_region(texture,dest,Rect2(Vector2(0,y)*ratio,Vector2(size.x,h)*ratio),tint)
	return true

func draw_air(ui,origin:Vector2,tint:Color) -> void:
	if not prepare(ui):return
	var time=ui.elapsed
	var visible=ui._visible_native_rect()
	var count=int(profile.get("flakes",0))
	if profile.get("dust",false):count=12
	for i in range(count):
		var seed=posmod(i*127+31,997)
		var x=fposmod(seed*13.7+time*5+sin(time*TAU/8+i)*3,footprint.x)
		var y=fposmod(seed*7.1+time*(8+posmod(i,3)*4),footprint.y)
		var world=Vector2(floor(x),floor(y))
		if _indoors(world) or not visible.has_point(origin+world):continue
		if profile.get("dust",false):
			# Sparse suspended interior dust, never exterior snowfall.
			var cell=Vector2i(world/16)
			if ui.game.category(cell) in [5,12]:continue
			ui.draw_rect(Rect2(origin+world,Vector2(2,1)),Color(.8,.79,.72,.45+.15*sin(time+i)))
		else:
			var alpha=.55 if i%3 else .8
			ui.draw_rect(Rect2(origin+world,Vector2(2,1)),Color(.84,.9,.96,alpha))
			if i%4==0:ui.draw_rect(Rect2(origin+world+Vector2(0,-1),Vector2(1,3)),Color(.94,.97,1,.65))
	if profile.get("drips",false):
		for cell in water:
			if posmod(cell.x*31+cell.y*17,29)!=3:continue
			var age=fposmod(time+cell.x*.17+cell.y*.31,4)
			if age>.65:continue
			var point=origin+Vector2(cell)*16+Vector2(8,floor(age*20))
			if visible.has_point(point):ui.draw_rect(Rect2(point,Vector2(1,2)),Color(.68,.8,.84,.7))
	# Short, sparse grains on exposed salt/sand only; never a screen wash,
	# grass, stone, bridges, rooms, or a visual change to walkable terrain.
	for i in range(mini(18,wind_cells.size())):
		var cell=wind_cells[posmod(i*37+17,wind_cells.size())]
		var age=fposmod(time+float(i)*.73,4)
		if age>1.7:continue
		var point=origin+Vector2(cell)*16+Vector2(2+floor(age*5),6+posmod(i*3,5))
		if visible.has_point(point):
			var color=Color(.71,.66,.53,.50*sin(age/1.7*PI)) if profile.climate=="sand" else Color(.77,.8,.8,.46*sin(age/1.7*PI))
			ui.draw_rect(Rect2(point,Vector2(3+posmod(i,3),1)),color)
	for cell in profile.get("wall_torches",[]):
		var at=origin+Vector2(cell[0]*16,cell[1]*16-12)
		_sheet(ui,"torch",at,time+float(cell[0])*.13,tint)
	for fire in fires:
		var at=origin+fire
		_sheet(ui,"flame",at-Vector2(8,18),time,tint)
		var strength=.5+.15*sin(time*TAU*2)
		ui.draw_circle(at+Vector2(0,2),8,Color(.9,.5,.18,.035*strength))
	for lamp in lamps:
		_sheet(ui,"lamplight",origin+lamp-Vector2(8,8),time+lamp.x*.013,tint)

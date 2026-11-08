extends RefCounted
## Short map-only presentation of an already committed MAP receipt.
const Healing=preload("res://core/healing_map_animation.gd")
const ReviewFx=preload("res://core/reviewed_battle_fx.gd")
const DATA="res://data/map_skills_20261029.json"
static var _data:Dictionary={}
var _owner:WeakRef
var active=false
var elapsed=0.0
var receipt:Dictionary={}
var spec:Dictionary={}
var forecast:Dictionary={}
var audit:Dictionary={}
var _saved:Dictionary={}
var _token=0
var _sounds:Dictionary={}
var _contacts:Dictionary={}

func _init(owner):_owner=weakref(owner)
func _ui():return _owner.get_ref() if _owner!=null else null
static func data()->Dictionary:
	if _data.is_empty():_data=JSON.parse_string(FileAccess.get_file_as_string(DATA))
	return _data
func reset()->void:
	_token+=1
	var ui=_ui()
	if ui!=null:
		for id in _saved:
			if _saved[id].had:ui.map_actor_alpha[id]=_saved[id].value
			else:ui.map_actor_alpha.erase(id)
		ui.queue_redraw()
	_saved.clear();active=false;receipt={};spec={};forecast={}
func prepare(value:Dictionary)->void:
	reset();receipt=value;spec=(Healing.data() if value.get("support",false) else data()).cases[str(value.key)];active=true;elapsed=0.0
	_sounds.clear();_contacts.clear()
	audit={"case":str(value.key),"duration":float(spec.duration),"sounds":[],"contacts":[],"pose":0,"time":0.0}
	var ui=_ui()
	for id in [str(value.actor)]+value.targets.map(func(t):return str(t.id)):
		_saved[id]={"had":ui.map_actor_alpha.has(id),"value":ui.map_actor_alpha.get(id,1.0)}
		ui.map_actor_alpha[id]=0.0
func hit_time(hit:Dictionary)->float:
	if receipt.get("support",false) or receipt.magic:return float(spec.impact)
	var origin=Vector2i(receipt.actor_unit.position[0],receipt.actor_unit.position[1])
	var p=Vector2i(hit.position[0],hit.position[1]);var d=Vector2i(receipt.facing[0],receipt.facing[1])
	var delta=p-origin;var depth=delta.x*d.x+delta.y*d.y
	return float(spec.impact)+float(depth)*(.025 if receipt.bow else .045)
func _cue(key:String, reviewed := false)->void:
	if _sounds.has(key):return
	_sounds[key]=true;audit.sounds.append({"key":key,"time":elapsed})
	var ui=_ui()
	if ui!=null and not ui.instant_mode:
		if reviewed:ReviewFx.play_sound(ui,key)
		else:ui.audio.play_sfx(key)
func _step(t:float)->void:
	elapsed=minf(t,float(spec.duration));audit.time=elapsed;audit.pose=pose()
	if receipt.get("support",false):
		if elapsed>=float(spec.release):_cue("heal-charge",true)
		if elapsed>=float(spec.impact):_cue("heal-resolve",true)
		for hit in receipt.targets:
			if elapsed>=float(spec.impact) and not _contacts.has(str(hit.id)):
				_contacts[str(hit.id)]=true;audit.contacts.append(str(hit.id))
		return
	if receipt.bow and elapsed>=.10:_cue("map_bow_draw")
	if receipt.magic:
		if elapsed>=float(spec.release):_cue("fieldfire-charge",true)
		if elapsed>=float(spec.impact):_cue("fieldfire-resolve",true)
	elif elapsed>=float(spec.release):_cue(str(spec.sfx))
	for hit in receipt.targets:
		if elapsed>=hit_time(hit) and not _contacts.has(str(hit.id)):
			_contacts[str(hit.id)]=true;audit.contacts.append(str(hit.id))
			# One impact cue for the whole wave, never one loud layer per cell.
			if not receipt.magic and int(hit.damage)>0:_cue("hit")
			if int(hit.get("reflection_damage",0))>0:_cue("hit")
func play(value:Dictionary)->void:
	prepare(value)
	var ui=_ui();var token=_token
	if ui.instant_mode:
		_step(float(spec.duration));reset();return
	var previous=Time.get_ticks_usec()
	while active and elapsed<float(spec.duration):
		await ui.get_tree().process_frame
		if _ui()==null or token!=_token:return
		var now=Time.get_ticks_usec()
		_step(elapsed+float(now-previous)/1000000.0*ui.effective_animation_speed());previous=now
		ui.queue_redraw()
	reset()
func pose()->int:
	var frame=0
	for point in spec.actor.timeline:
		if elapsed<float(point[0]):break
		frame=int(point[1])
	return frame
func _base_transform()->void:
	var ui=_ui();ui.draw_set_transform(ui._canvas_offset()+ui.map_offset)
func _point(p:Array)->Vector2:
	return _ui()._battle_cell_screen(Vector2i(p[0],p[1]))+Vector2(8,8)
func _fx(index:int,point:Vector2,size:float,alpha:float=1.,angle:float=0.)->void:
	if index<0 or index>5 or alpha<=0:return
	var ui=_ui();var texture=ui._tex(str(spec.fx));var cell=texture.get_size()/Vector2(3,2)
	size*=float(spec.get("fx_scale",1.0))
	ui.draw_set_transform(ui._canvas_offset()+ui.map_offset+point,angle)
	ui.draw_texture_rect_region(texture,Rect2(Vector2(-size/2,-size/2),Vector2(size,size)),Rect2(Vector2(index%3,floori(float(index)/3))*cell,cell),Color(1,1,1,clampf(alpha,0,1)))
	_base_transform()
func _blend(phase:float,point:Vector2,size:float,alpha:float=1.,angle:float=0.)->void:
	phase=clampf(phase,0,5);var n=floori(phase);var fraction=phase-n
	_fx(n,point,size,alpha*(1.-fraction),angle)
	if n<5:_fx(n+1,point,size,alpha*fraction,angle)
func _hp(point:Vector2,hp:int,maximum:int,color:Color)->void:
	var ui=_ui()
	ui.draw_rect(Rect2(point+Vector2(-7,3.5),Vector2(14,3)),Color(.03,.07,.10,.95))
	if hp>0:ui.draw_rect(Rect2(point+Vector2(-6.5,4),Vector2(13.*hp/maxi(1,maximum),2)),color)
func draw_ranges()->void:
	var ui=_ui()
	if ui==null:return
	var preview=receipt if active else forecast
	if preview.is_empty():return
	if preview.get("support",false):Healing.ranges(self,preview);return
	for cell in preview.get("cells",[]):
		ui.draw_rect(Rect2(ui._battle_cell_screen(cell)+Vector2.ONE,Vector2(14,14)),Color(.35,.72,.85,.13 if active else .28) if preview.get("male",false) else Color(.95,.45,.2,.12 if active else .25))
	if preview.get("magic",false) and preview.get("advanced",false):
		ui.draw_rect(Rect2(ui._battle_cell_screen(Vector2i(preview.center[0],preview.center[1]))+Vector2(2,2),Vector2(12,12)),Color(1,.8,.4,.28))
func draw()->void:
	var ui=_ui()
	if ui==null or not active:return
	if receipt.get("support",false):Healing.draw(self);return
	_base_transform()
	var hero=_point(receipt.actor_unit.position);var center=_point(receipt.center)
	var facing=Vector2(receipt.facing[0],receipt.facing[1]);var angle=facing.angle()
	for hit in receipt.targets:
		var dt=elapsed-hit_time(hit);var opacity=1.0
		if int(hit.hp_after)==0 and dt>.12:opacity=clampf(1.-(dt-.12)/.24,0,1)
		var at=ui._battle_cell_screen(Vector2i(hit.position[0],hit.position[1]))
		if dt>=0 and dt<.13:at.x+=roundf(sin(dt*100)*1.2)
		var sprite=ui._map_unit_sprite(hit.unit);var origin=sprite.get("tile_origin",[4,4])
		ui._draw_frame(sprite,0,at-Vector2(origin[0],origin[1]),false,Color(1,1,1,opacity))
		if opacity>.01:_hp(_point(hit.position),int(hit.hp_before) if dt<0 else int(hit.hp_after),int(hit.unit.max_hp),Color(.8,.55,.52))
	if elapsed>=.06 and elapsed<float(spec.release) and not receipt.bow:
		_blend(clampf((elapsed-.06)/.24,0,1)*1.3,hero+Vector2(4.5,-4.5),21 if receipt.magic else 27.5,.6)
	if receipt.bow:
		for hit in receipt.targets:
			var start=float(spec.release);var impact=hit_time(hit)
			if elapsed>=start and elapsed<impact:
				var from=hero+Vector2(8*facing.x,-2.5)
				var to=_point(hit.position)+Vector2(0,-4.5);var p=from.lerp(to,(elapsed-start)/(impact-start))
				ui.draw_set_transform(ui._canvas_offset()+ui.map_offset+p,(to-from).angle()+PI)
				ui.draw_texture_rect(ui._tex("res://assets/map-skills-20261029/arrow.png"),Rect2(-7,-2,14,4),false)
				_base_transform()
	elif not receipt.magic and elapsed>=float(spec.release):
		var u=clampf((elapsed-float(spec.release))/.38,0,1)
		var end=hero+facing*float(receipt.depth)*16
		var p=(hero+facing*5).lerp(end,u)+Vector2(0,-5.5)
		var phase=lerpf(1.4,3.,u) if elapsed<.68 else lerpf(3.,5.,clampf((elapsed-.68)/.55,0,1))
		_blend(phase,p,75 if receipt.advanced else 59,clampf((float(spec.duration)-elapsed)/.18,0,1),angle)
	elif receipt.magic:
		if elapsed>=.3 and elapsed<.58:
			var u=clampf((elapsed-.3)/.28,0,1)
			var p=(hero+Vector2(4,-7)).lerp(center+Vector2(0,-4.5),u)-Vector2(0,sin(u*PI)*10)
			_fx(0,p,20 if receipt.advanced else 15)
		if elapsed>=.48:
			var phase=lerpf(1.,3.,(elapsed-.48)/.10) if elapsed<.58 else lerpf(3.,5.,clampf((elapsed-.58)/.7,0,1))
			_blend(phase,center-Vector2(0,19 if receipt.advanced else 8),92.5 if receipt.advanced else 58,clampf((float(spec.duration)-elapsed)/.18,0,1))
	# Approved map actor remains in front of its own FX; no leg or world motion.
	var hero_hp=int(receipt.hp_before)-int(receipt.cost);var hero_tint=Color.WHITE
	for hit in receipt.targets:
		var reflection=int(hit.get("reflection_damage",0));var dt=elapsed-hit_time(hit)
		if reflection>0 and dt>=0:
			hero_hp=int(hit.source_hp_after)
			if dt<.28:hero_tint=Color(1,.4,.4,.45 if int(dt*36)%2==0 else 1.)
	ui._draw_frame(spec.actor,pose(),ui._battle_cell_screen(Vector2i(receipt.actor_unit.position[0],receipt.actor_unit.position[1]))-Vector2(8,8),facing.x<0,hero_tint)
	_hp(hero,hero_hp,int(receipt.actor_unit.max_hp),Color(.60,.82,.73))
	for hit in receipt.targets:
		var dt=elapsed-hit_time(hit)
		if int(hit.damage)>0:
			ReviewFx.draw_effect(ui,"r2-map-hero-bow" if receipt.bow else "map-hit",
				dt,_point(hit.position)+Vector2(0,-2),facing.x<0,.9,ui._visible_native_rect())
		if dt>=0 and dt<.44:
			var at=_point(hit.position)+Vector2(-3,-18-minf(5.,dt*14.))
			var label=str(int(hit.damage));var bounds=ui._visible_native_rect();var w=ui._small_text_width(label)
			at.x=clampf(at.x,bounds.position.x+2,bounds.end.x-w-2);at.y=clampf(at.y,bounds.position.y+2,bounds.end.y-10)
			# Floating battlefield numbers do not belong to the last HUD panel.
			# Keep their own viewport bounds check and restore the panel scope.
			var previous:Array[Rect2]=[];previous.assign(ui.safe_panels);ui.safe_panels.clear()
			# Muted red stays distinct from snow and blade light; a one-pixel
			# dark edge keeps the small bitmap digits readable on varied terrain.
			for edge in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
				ui._small_text(label,at+edge,Color("38262d"))
			ui._small_text(label,at,Color("e8aaa5") if int(hit.center_bonus)>0 else Color("d98f8c"))
			ui.safe_panels.assign(previous)
	ui.draw_set_transform(ui._canvas_offset())
	if elapsed<.52:
		var bounds=ui._visible_native_rect();var panel=Rect2(Vector2(bounds.get_center().x-92,bounds.position.y+5),Vector2(184,32))
		ui._panel(panel);ui._center_text("MAP · "+str(receipt.name)+("／持弓" if receipt.bow else ""),panel.grow(-10),Color(.78,.9,1.) if not receipt.magic else Color(1.,.82,.62))

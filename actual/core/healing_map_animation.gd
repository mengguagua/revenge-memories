extends RefCounted
## Accepted map poses and foot-registered healing art. No gameplay mutations.
const DATA="res://data/healer_map_20261104.json"
static var _data:Dictionary={}
static func data()->Dictionary:
	if _data.is_empty():_data=JSON.parse_string(FileAccess.get_file_as_string(DATA))
	return _data

static func ranges(player,value:Dictionary)->void:
	var ui=player._ui()
	if not player.active:
		for cell in value.get("range_cells",[]):
			ui.draw_rect(Rect2(ui._battle_cell_screen(cell)+Vector2.ONE,Vector2(14,14)),Color(.5,.75,.63,.13))
	for cell in value.get("cells",[]):
		ui.draw_rect(Rect2(ui._battle_cell_screen(cell)+Vector2.ONE,Vector2(14,14)),Color(.62,.85,.7,.32))

static func effect(player,phase:float,point:Vector2,size:float,alpha:float=1.)->void:
	var ui=player._ui();var texture=ui._tex(str(player.spec.fx));var cell=Vector2(192,192)
	phase=clampf(phase,0,5);var n=floori(phase);var f=phase-n
	for pair in [[n,1.-f],[mini(5,n+1),f]]:
		if float(pair[1])<=0:continue
		var index=int(pair[0]);var at=point-Vector2(.5,161./192.)*size
		ui.draw_texture_rect_region(texture,Rect2(at,Vector2.ONE*size),Rect2(Vector2(index%3,floori(float(index)/3))*cell,cell),Color(1,1,1,alpha*float(pair[1])))

static func draw(player)->void:
	var ui=player._ui();var value=player.receipt;var t=float(player.elapsed);var spec=player.spec
	player._base_transform()
	var caster=player._point(value.actor_unit.position);var hit=value.targets[0];var target=player._point(hit.position)
	var at=ui._battle_cell_screen(Vector2i(hit.position[0],hit.position[1]));var sprite=ui._map_unit_sprite(hit.unit);var origin=sprite.get("tile_origin",[4,4])
	ui._draw_frame(sprite,0,at-Vector2(origin[0],origin[1]),bool(sprite.get("idle_flip",false)))
	player._hp(target,int(hit.hp_after) if t>=float(spec.impact) else int(hit.hp_before),int(hit.unit.max_hp),Color("9bd3b7"))
	var actor_spec=spec.actor.duplicate(true);var actor_origin=actor_spec.tile_origin
	var original=ui._map_unit_sprite(value.actor_unit)
	var flip_delta=16+2*float(actor_origin[0])-float(actor_spec.frame_size[0])/float(actor_spec.native_density) if actor_spec.flip else 0.
	if original.has("ground_shadow"):
		actor_spec.ground_shadow=original.ground_shadow
		actor_spec.anchor=[float(original.anchor[0])-float(original.tile_origin[0])+float(actor_origin[0])-flip_delta,float(original.anchor[1])-float(original.tile_origin[1])+float(actor_origin[1])]
	var actor_at=ui._battle_cell_screen(Vector2i(value.actor_unit.position[0],value.actor_unit.position[1]))-Vector2(actor_origin[0],actor_origin[1])
	if actor_spec.flip:actor_at.x+=16+2*float(actor_origin[0])-float(actor_spec.frame_size[0])/float(actor_spec.native_density)
	ui._draw_frame(actor_spec,player.pose(),actor_at,bool(actor_spec.flip))
	player._hp(caster,int(value.hp_after),int(value.actor_unit.max_hp),Color("9bd3b7"))
	if t>=.04 and t<.32:effect(player,minf(1.5,(t-.04)*5),caster+Vector2(7.5,-9),19,.7)
	if t>=float(spec.release) and t<float(spec.impact):
		var u=clampf((t-float(spec.release))/(float(spec.impact)-float(spec.release)),0,1)
		for k in range(4,-1,-1):
			var z=clampf(u-k*.055,0,1);var p=(caster+Vector2(7,-8.5)).lerp(target+Vector2(0,-6),z)-Vector2(0,sin(z*PI)*12)
			effect(player,0,p,12.5-k,.88-k*.14)
	if t>=.46:
		var frame=lerpf(0,2,(t-.46)/.12) if t<.58 else lerpf(2,3,(t-.58)/.2) if t<.78 else lerpf(3,5,clampf((t-.78)/(float(spec.duration)-.78),0,1))
		effect(player,frame,target+Vector2(0,7),54 if value.advanced else 42,clampf((float(spec.duration)-t)/.13,0,1))
	var dt=t-float(spec.impact)
	if dt>=0 and dt<.44 and int(hit.heal)>0:
		var label="+"+str(int(hit.heal));var bounds=ui._visible_native_rect();var p=target+Vector2(-ui._small_text_width(label)/2,-24-minf(4.5,dt*11.5))
		p.x=clampf(p.x,bounds.position.x+2,bounds.end.x-ui._small_text_width(label)-2);p.y=clampf(p.y,bounds.position.y+2,bounds.end.y-10)
		var previous:Array[Rect2]=[];previous.assign(ui.safe_panels);ui.safe_panels.clear()
		for edge in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:ui._small_text(label,p+edge,Color("243b31"))
		ui._small_text(label,p,Color("b2e6bc"));ui.safe_panels.assign(previous)
	ui.draw_set_transform(ui._canvas_offset())

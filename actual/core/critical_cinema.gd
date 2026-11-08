extends RefCounted
## Approved native critical presentation. Combat owns HP, cost, kills and rewards.
const DATA="res://data/critical_cinema.json"
const Professions=preload("res://core/hero_professions.gd")
const Rules=preload("res://core/combat_rules.gd")
const ReviewFx=preload("res://core/reviewed_battle_fx.gd")
const FIELD := Rect2(0,40,640,280)
static var _data:Dictionary={}
var _owner:WeakRef
var active=false
var elapsed=0.0
var spec:Dictionary={}
var event:Dictionary={}
var program:Dictionary={}
var audit:Dictionary={}
var background_key=""
var target_texture:Texture2D
var _target_flash: Texture2D
var _token=0
var _did_contact=false
var _textures:Dictionary={}
var _target_flip=false
var _hp_pending := false
var _reaction_delay := 0.0
var _fx: ReviewFx

func _init(owner):
	_owner=weakref(owner)
	_fx=ReviewFx.new(owner)
func _ui():return _owner.get_ref() if _owner!=null else null
static func data()->Dictionary:
	if _data.is_empty():_data=JSON.parse_string(FileAccess.get_file_as_string(DATA))
	return _data
static func case_for(actor:Dictionary,value:Dictionary)->String:
	if not value.get("critical",false) or not value.get("hit",false) or value.get("visual_only",false) or value.get("blocked",false) or int(value.get("self_damage",0))>0:return ""
	if int(value.get("hp_before",0))<=int(value.get("hp_after",0)):return ""
	if not is_hero(actor):return ""
	var hero=str(actor.id)
	var weapon=int(value.get("weapon_index",Rules.weapon_index(actor)));var suffix="-advanced" if Professions.advanced(actor) else ""
	if hero=="eileen" and weapon in [23,24,26,27]:return "eileen-"+{23:"fire",24:"thunder",26:"holy",27:"wind"}[weapon]+suffix
	if hero=="hunapu" and weapon in [1,20,21,22]:return "hunapu-bow"+suffix
	# Ranged Thunder Sword and unapproved spells keep their existing programs.
	if weapon in [0,11,12,13,14,16,17,18] or (weapon==15 and int(value.get("distance",1))<=1):return hero+"-sword"+suffix
	return ""

static func is_hero(actor: Dictionary) -> bool:
	var hero := str(actor.get("id",""))
	return actor.get("side","") == "player" and not actor.get("temporary",false) and (
		(hero == "hunapu" and int(actor.get("character_id",0)) == 1)
		or (hero == "eileen" and int(actor.get("character_id",0)) == 2))

static func background_for(stage:Dictionary,actor:Dictionary={})->String:
	var code=str(stage.get("code",""))
	if code=="F31" and not actor.is_empty() and int(actor.get("position",[99,0])[0])<7:return "ship"
	if data().stage_backgrounds.has(code):return str(data().stage_backgrounds[code])
	var biome=str(stage.get("nature_layout",{}).get("biome","grass"))
	return str({"snow":"snow","forest":"forest","sea":"coast","rock":"cave","sand":"arid","salt":"arid","marsh":"marsh","cobble":"castle"}.get(biome,"plains"))
func _background_tint()->Color:
	var values=_ui().game.battle_data.get("map_tint",[1,1,1,1])
	return Color(float(values[0]),float(values[1]),float(values[2]),1).lerp(Color.WHITE,.35)
func _snapshot_target(unit:Dictionary)->void:
	var ui=_ui();var graphic=ui.battle_animation.sprite(unit);var texture=ui._tex(str(graphic.path))
	var size=Vector2i(int(graphic.frame_size[0]),int(graphic.frame_size[1]));var frame=int(graphic.get("sequences",{}).get("idle",[0])[0]);var columns=int(graphic.get("columns",graphic.get("frames",1)))
	var image=texture.get_image()
	if image.is_compressed():image.decompress()
	var rect=Rect2i(Vector2i((frame%columns)*size.x,int(frame/columns)*size.y),size).intersection(Rect2i(Vector2i.ZERO,image.get_size()))
	var cell=image.get_region(rect);var used=cell.get_used_rect()
	if used.has_area():cell=cell.get_region(used)
	target_texture=ImageTexture.create_from_image(cell)
	if _fx.plan.has("stock_impact"):
		cell.convert(Image.FORMAT_RGBA8)
		var pixels: PackedByteArray = cell.get_data()
		for i in range(0,pixels.size(),4):
			pixels[i]=255
			pixels[i+1]=255
			pixels[i+2]=255
		_target_flash=ImageTexture.create_from_image(Image.create_from_data(
			cell.get_width(),cell.get_height(),false,Image.FORMAT_RGBA8,pixels))
	_target_flip=Rules.Body.is_body(unit) and ui.battle_animation.Innate.horizontal_flip(graphic,false,bool(graphic.get("idle_flip",false))) or (not Rules.Body.is_body(unit) and bool(graphic.get("idle_flip",false)))
	audit.target={"id":str(unit.id),"path":str(graphic.path),"frame":frame,"size":[cell.get_width(),cell.get_height()],"static":true}

func prepare(value:Dictionary)->bool:
	reset();var ui=_ui()
	if ui==null:return false
	var actor=ui.game.find_unit(str(value.attacker));var key=case_for(actor,value)
	if key.is_empty() or not data().cases.has(key):return false
	event=value.duplicate(true);spec=data().cases[key]
	var packed=FileAccess.get_file_as_bytes(str(spec.program));var decoded=packed.decompress_dynamic(32*1024*1024,FileAccess.COMPRESSION_GZIP)
	program=JSON.parse_string(decoded.get_string_from_utf8())
	if program.is_empty():return false
	active=true;elapsed=0.0;_did_contact=false;background_key=background_for(ui.game.battle_data,actor)
	audit={"case":key,"contacts":[],"hp_steps":[],"background":background_key,"time":0.,"target_drawn":false,"program_frames":program.frames.size(),"defeated":int(event.hp_after)<=0}
	var target: Dictionary = ui.game.find_unit(str(value.defender))
	_fx.prepare(ReviewFx.data().cinema.get(key,{}),event)
	_snapshot_target(target)
	_reaction_delay = ui.battle_animation.hit_reaction_duration(target)
	for index in spec.used_images:_textures[int(index)]=ui._tex(str(data().images[int(index)].path))
	ui.queue_redraw();return true
func reset()->void:
	_token+=1
	var ui=_ui()
	if ui!=null and active and ui.audio!=null and ui.audio.has_method("finish_critical_audio"):ui.audio.finish_critical_audio()
	if ui != null and active:ui.audio.stop_reviewed_sfx()
	active=false;elapsed=0.0;event={};spec={};program={};target_texture=null;_textures.clear();_did_contact=false
	_target_flash=null
	_hp_pending=false
	_fx.reset()
	if ui!=null:ui.queue_redraw()
func duration()->float:
	var hit := float(spec.hit)
	var original := hit+1.05 if int(event.hp_after)<=0 else float(spec.duration)
	var health_end := hit+_reaction_delay+_loss()*2.0/60.0988+.32
	return maxf(original,health_end)
func accepts_contact(value:Dictionary)->bool:
	return active and str(value.attacker)==str(event.get("attacker","")) and str(value.defender)==str(event.get("defender",""))
func on_contact(value:Dictionary)->void:
	var ui=_ui()
	audit.contacts.append({"time":elapsed,"hp_before":int(value.hp_before),"hp_after":int(value.hp_after),"id":str(value.defender)})
	ui.combat_message="必杀";ui.combat_hit_id="";ui.combat_shake=0.0
	var id := str(value.defender)
	if ui.instant_mode:
		ui.combat_hp[id]=int(value.hp_after)
		if int(value.hp_after)<=0:ui.combat_fades[id]=0.0
	else:
		_drain_health(id,int(value.hp_before),int(value.hp_after),_token)

func _drain_health(id: String, before: int, after: int, token: int) -> void:
	var ui = _ui()
	_hp_pending = true
	await ui._wait(_reaction_delay)
	for hp in range(before-1,after-1,-1):
		if token != _token or _ui() == null:
			return
		audit.hp_steps.append([elapsed,hp])
		await ui._combat_hp_tick(id,hp)
	if token != _token or _ui() == null:
		return
	if after <= 0:
		ui.combat_fades[id] = 0.0
	_hp_pending = false

func _loss() -> int:
	return maxi(0,int(event.hp_before)-int(event.hp_after))
func _music_gain()->float:
	var gain=pow(10.,-8./20.)*minf(1.,elapsed/.06)*clampf((duration()-elapsed)/.28,0,1);var duck=1.0
	for cue in spec.audio_events:
		var key=str(cue.stem)
		if not ("slash" in key or "sword_hit" in key or "bow_release" in key or "arrow_hit" in key or "thunder_hit" in key or "flame_burst" in key):continue
		var dt=elapsed-float(cue.seconds)
		if dt>=-.012 and dt<.65:duck=minf(duck,1.-.68*exp(-maxf(dt,0)/.18))
	return gain*duck
func play(value:Dictionary)->bool:
	if not prepare(value):return false
	var ui=_ui();var token=_token
	if not ui.instant_mode and ui.audio.has_method("begin_critical_audio"):
		var effects: AudioStream = null if _fx.plays_audio() else load(str(spec.sfx))
		ui.audio.begin_critical_audio(effects,load(str(data().themes[str(spec.hero)])),float(spec.audio_gain))
	var previous=Time.get_ticks_usec()
	while active and token==_token and (elapsed<duration() or _hp_pending):
		if ui.instant_mode:elapsed=float(spec.hit)
		else:
			await ui.get_tree().process_frame
			if _ui()==null or not active or token!=_token:return true
			if ui.view!="combat":reset();return true
			var now=Time.get_ticks_usec();elapsed=minf(duration(),elapsed+float(now-previous)/1000000.*ui.effective_animation_speed());previous=now
		audit.time=elapsed
		_fx.seek(elapsed-float(spec.hit))
		if elapsed>=float(spec.hit) and not _did_contact:
			_did_contact=true
			await ui.battle_animation._contact(event)
			if _ui()==null or token!=_token:return true
			previous=Time.get_ticks_usec()
		if ui.instant_mode:elapsed=duration()
		elif ui.audio.has_method("sync_critical_audio"):ui.audio.sync_critical_audio(elapsed,ui.effective_animation_speed(),_music_gain())
		ui.queue_redraw()
	reset();return true

func _ease(x:float)->float:return 1.-pow(1.-clampf(x,0,1),3)
func _target_visible()->bool:return int(event.hp_after)>0 or elapsed<=float(spec.hit)+.35
func _draw_target(point:Vector2,opacity:float,action:Transform2D,impact:Array)->void:
	audit.target_drawn=false
	if target_texture==null or not _target_visible():return
	var ui=_ui();var size=target_texture.get_size();var scale=minf(139./size.y,166./size.x);size*=scale
	var texture := target_texture
	var at := point-Vector2(size.x/2,size.y)
	if not impact.is_empty():
		var tilt := Transform2D(Vector2.RIGHT,Vector2(-float(impact[3]),1),point)
		ui.draw_set_transform_matrix(action*tilt)
		at = -Vector2(size.x/2,size.y)
		if impact[2]:texture = _target_flash
	ui.draw_texture_rect(texture,Rect2(at,Vector2(-size.x if _target_flip else size.x,size.y)),false,Color(1,1,1,opacity))
	if not impact.is_empty():ui.draw_set_transform_matrix(action)
	audit.target_drawn=true

func _stock_impact_frame(stock:Dictionary)->Array:
	if stock.is_empty():return []
	var index := floori((_fx.clock-float(stock.start))*ReviewFx.REVIEW_FPS+.00001)
	return stock.frames[index] if index>=0 and index<stock.frames.size() else []

static func cutin_text_layout(scene_tick:float,width:float)->Vector2:
	# X is the left edge of the full glyph run; Y is its opacity.
	var enter := smoothstep(20.0,25.0,scene_tick)
	var leave := smoothstep(49.0,55.0,scene_tick)
	return Vector2(160.0-18.0*(1.0-enter)-12.0*leave-width*.5,enter*(1.0-leave))

func _draw_scene(origin:Vector2,scale:float,opacity:float)->void:
	var ui=_ui();var bg=ui._tex(str(data().backgrounds[background_key]));var pan=-(elapsed-3.8)*12. if spec.weapon=="弓" and elapsed>3.8 and elapsed<float(spec.hit) else 0.
	var upright := Transform2D(0.0,origin).scaled_local(Vector2.ONE*scale)
	# The authored action runs left to right. Reflect its layers so the hero
	# fights from the same side as the ordinary battle and HP cards.
	_fx.clock = elapsed-float(spec.hit)
	var stock: Dictionary = _fx.plan.get("stock_impact",{})
	var impact := _stock_impact_frame(stock)
	var shake := Vector2.ZERO if impact.is_empty() else Vector2(float(impact[0]),float(impact[1]))*float(stock.scale)
	var action := Transform2D(-upright.x,upright.y,upright*Vector2(FIELD.end.x,0)).translated_local(shake)
	ui.draw_set_transform_matrix(upright)
	ui.draw_texture_rect_region(bg,Rect2(0,0,640,360),Rect2((640.-640./1.05)/2.+pan+shake.x,(360.-360./1.05)/2.-shake.y,640./1.05,360./1.05),_background_tint()*Color(1,1,1,opacity))
	ui.draw_set_transform_matrix(action)
	var scene_tick: float = elapsed*float(program.fps)
	var frame := clampi(floori(scene_tick),0,program.frames.size()-1)
	var staged := _fx.actor_pose()
	var replace := _fx.replaces_native()
	var target := Vector2(502,290)
	_fx.draw_layer(ui,"back",FIELD,opacity)
	var ops: Array = program.frames[frame]
	for index in range(ops.size()):
		var op: Array = ops[index]
		match int(op[0]):
			0:
				if replace and index>0 and elapsed>=2.65 and (
					(float(op[2])>=39.0 and float(op[2])<316.0)
					or (float(op[3])>=628.0 and float(op[4])>=345.0)):
					continue
				var color=Color.hex(int(op[5]));color.a*=opacity;ui.draw_rect(Rect2(float(op[1]),float(op[2]),float(op[3]),float(op[4])),color)
			1:
				var texture: Texture2D = _textures[int(op[1])]
				var source := str(data().images[int(op[1])].source)
				if not staged.is_empty() and source.begins_with("assets/") and ("hunapu-" in source or "eileen-" in source):
					continue
				if replace and ("spell-" in source or "fire-flight-" in source or "/impact-" in source):
					continue
				var label := source.begins_with("Cinematic label:")
				var at := Vector2(float(op[2]),float(op[3]))
				var size := Vector2(float(op[4]),float(op[5]))
				var region := Rect2(float(op[6]),float(op[7]),float(op[8]),float(op[9]))
				var alpha := float(op[11])*opacity
				if label:
					if at.y>=FIELD.position.y and at.y<FIELD.end.y:
						# Keep the opening seal centered and clear it before
						# the portrait and its three lines are visible.
						if source == "Cinematic label: 必 杀":
							if scene_tick >= 19.0:continue
						else:
							var placement := cutin_text_layout(scene_tick,texture.get_width())
							alpha *= placement.y
							if alpha<=0.0:continue
							# Restore the whole glyph run. The original slide
							# baked cropped source rectangles at the edges.
							size = texture.get_size()
							region = Rect2(Vector2.ZERO,size)
							at.x = placement.x
					ui.draw_set_transform_matrix(upright)
				elif int(op[10])==1:size.x=-size.x
				ui.draw_texture_rect_region(texture,Rect2(at,size),region,Color(1,1,1,alpha))
				if label:ui.draw_set_transform_matrix(action)
			2:
				target=Vector2(float(op[1]),float(op[2]))
				_draw_target(target,float(op[3])*opacity,action,impact)
	_fx.draw_actor(ui,staged,FIELD,opacity)
	_fx.draw_layer(ui,"front",FIELD,opacity)
	ui.draw_set_transform_matrix(upright)
	if _did_contact:
		var pixel := 1.0/float(_fx.plan.get("density",.609375))
		var damage_at := Vector2(FIELD.end.x-target.x,target.y)+Vector2(4,-84)*pixel
		var impact_hold := float(stock.hits[1].stop) if not stock.is_empty() else 0.0
		ReviewFx.draw_damage(ui,_loss(),elapsed-float(spec.hit)-impact_hold,damage_at,FIELD,maxf(pixel,1.0/scale),opacity)

func draw()->bool:
	if not active:return false
	var ui=_ui();var canvas=ui.get_viewport_rect();var show=_ease((elapsed-.08)/.29)*(1.-_ease((elapsed-(duration()-.35))/.31))
	if show<=0:return false
	var stage := Vector2(canvas.size.x,canvas.size.y-66.0)
	var scale=minf((stage.x-16)/640.,(stage.y-12)/360.)*(.91+.09*show);var size=Vector2(640,360)*scale;var area=Rect2(canvas.position+(stage-size)/2,size)
	ui.draw_set_transform(Vector2.ZERO);ui.draw_rect(canvas,Color(0.01,.025,.04,show*.71))
	for spread in [6,4,2]:ui.draw_rect(area.grow(spread),Color(0,0,0,show*.13))
	ui.draw_rect(area.grow(1),Color(.43,.51,.54,show));_draw_scene(area.position,scale,show)
	ui.draw_set_transform(Vector2.ZERO);ui.draw_rect(Rect2(area.position,Vector2(area.size.x,1)),Color(.72,.69,.58,show))
	ui._draw_cinema_health(Vector2(canvas.get_center().x-128.0,canvas.end.y-64.0))
	return true

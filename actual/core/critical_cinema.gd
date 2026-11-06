extends RefCounted
## Approved native critical presentation. Combat owns HP, cost, kills and rewards.
const DATA="res://data/critical_cinema.json"
const Professions=preload("res://core/hero_professions.gd")
const Rules=preload("res://core/combat_rules.gd")
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
var _token=0
var _did_contact=false
var _textures:Dictionary={}
var _target_flip=false
var _target_name=""
var _target_max_hp=1

func _init(owner):_owner=weakref(owner)
func _ui():return _owner.get_ref() if _owner!=null else null
static func data()->Dictionary:
	if _data.is_empty():_data=JSON.parse_string(FileAccess.get_file_as_string(DATA))
	return _data
static func case_for(actor:Dictionary,value:Dictionary)->String:
	if not value.get("critical",false) or not value.get("hit",false) or value.get("visual_only",false) or value.get("blocked",false) or int(value.get("self_damage",0))>0:return ""
	if int(value.get("hp_before",0))<=int(value.get("hp_after",0)):return ""
	var hero=str(actor.get("id",""));var cid=int(actor.get("character_id",0))
	if actor.get("side","")!="player" or actor.get("temporary",false) or hero not in ["hunapu","eileen"] or cid!=(1 if hero=="hunapu" else 2):return ""
	var weapon=int(value.get("weapon_index",Rules.weapon_index(actor)));var suffix="-advanced" if Professions.advanced(actor) else ""
	if hero=="eileen" and weapon in [23,24,26,27]:return "eileen-"+{23:"fire",24:"thunder",26:"holy",27:"wind"}[weapon]+suffix
	if hero=="hunapu" and weapon in [1,20,21,22]:return "hunapu-bow"+suffix
	# Ranged Thunder Sword and unapproved spells keep their existing programs.
	if weapon in [0,11,12,13,14,16,17,18] or (weapon==15 and int(value.get("distance",1))<=1):return hero+"-sword"+suffix
	return ""

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
	var ui=_ui();_target_name=str(unit.get("name_zh","目标"));_target_max_hp=maxi(1,int(unit.get("max_hp",1)));var graphic=ui.battle_animation.sprite(unit);var texture=ui._tex(str(graphic.path))
	var size=Vector2i(int(graphic.frame_size[0]),int(graphic.frame_size[1]));var frame=int(graphic.get("sequences",{}).get("idle",[0])[0]);var columns=int(graphic.get("columns",graphic.get("frames",1)))
	var image=texture.get_image()
	if image.is_compressed():image.decompress()
	var rect=Rect2i(Vector2i((frame%columns)*size.x,int(frame/columns)*size.y),size).intersection(Rect2i(Vector2i.ZERO,image.get_size()))
	var cell=image.get_region(rect);var used=cell.get_used_rect()
	if used.has_area():cell=cell.get_region(used)
	target_texture=ImageTexture.create_from_image(cell)
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
	audit={"case":key,"contacts":[],"background":background_key,"time":0.,"target_drawn":false,"program_frames":program.frames.size(),"defeated":int(event.hp_after)<=0}
	_snapshot_target(ui.game.find_unit(str(value.defender)))
	for index in spec.used_images:_textures[int(index)]=ui._tex(str(data().images[int(index)].path))
	ui.queue_redraw();return true
func reset()->void:
	_token+=1
	var ui=_ui()
	if ui!=null and active and ui.audio!=null and ui.audio.has_method("finish_critical_audio"):ui.audio.finish_critical_audio()
	active=false;elapsed=0.0;event={};spec={};program={};target_texture=null;_textures.clear();_did_contact=false
	if ui!=null:ui.queue_redraw()
func duration()->float:
	return float(spec.hit)+1.05 if int(event.get("hp_after",1))<=0 else float(spec.get("duration",0))
func accepts_contact(value:Dictionary)->bool:
	return active and str(value.attacker)==str(event.get("attacker","")) and str(value.defender)==str(event.get("defender",""))
func on_contact(value:Dictionary)->void:
	var ui=_ui();ui.combat_hp[str(value.defender)]=int(value.hp_after)
	if int(value.hp_after)<=0:ui.combat_fades[str(value.defender)]=0.0
	audit.contacts.append({"time":elapsed,"hp_before":int(value.hp_before),"hp_after":int(value.hp_after),"id":str(value.defender)})
	ui.combat_message="必杀";ui.combat_hit_id="";ui.combat_shake=0.0
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
		ui.audio.begin_critical_audio(load(str(spec.sfx)),load(str(data().themes[str(spec.hero)])),float(spec.audio_gain))
	var previous=Time.get_ticks_usec()
	while active and token==_token and elapsed<duration():
		if ui.instant_mode:elapsed=float(spec.hit)
		else:
			await ui.get_tree().process_frame
			if _ui()==null or not active or token!=_token:return true
			if ui.view!="combat":reset();return true
			var now=Time.get_ticks_usec();elapsed=minf(duration(),elapsed+float(now-previous)/1000000.*ui.effective_animation_speed());previous=now
		audit.time=elapsed
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
func _shown_hp()->int:
	return roundi(lerpf(float(event.hp_before),float(event.hp_after),_ease((elapsed-float(spec.hit)-.12)/.55)))
func _draw_target(point:Vector2,opacity:float)->void:
	audit.target_drawn=false
	if target_texture==null or not _target_visible():return
	var ui=_ui();var size=target_texture.get_size();var scale=minf(139./size.y,166./size.x);size*=scale
	var at=point-Vector2(size.x/2,size.y)
	ui.draw_texture_rect(target_texture,Rect2(at,Vector2(-size.x if _target_flip else size.x,size.y)),false,Color(1,1,1,opacity))
	audit.target_drawn=true
func _label(op:Array,origin:Vector2,scale:float,opacity:float)->void:
	var ui=_ui();var kind=str(op[1]);var value=_target_name if kind=="name" else "%d / %d"%[_shown_hp(),_target_max_hp] if kind=="hp" else "-"+str(maxi(0,int(event.hp_before)-int(event.hp_after)))
	var font_scale=float(op[4])/maxf(1.,ui._text_height(value));var width=204. if kind=="name" else 146. if kind=="hp" else 136.
	if ui._text_width(value)*font_scale>width:font_scale*=width/(ui._text_width(value)*font_scale)
	var at=origin+Vector2(float(op[2]),float(op[3]))*scale
	ui.draw_set_transform(at,0,Vector2.ONE*scale*font_scale)
	var color=Color.hex(int(op[5]));color.a*=opacity
	ui._center_text(value,Rect2(-width/(2*font_scale),-float(op[4])/font_scale,width/font_scale,2*float(op[4])/font_scale),color,false)
	ui.draw_set_transform(origin,0,Vector2.ONE*scale)
func _draw_scene(origin:Vector2,scale:float,opacity:float)->void:
	var ui=_ui();var bg=ui._tex(str(data().backgrounds[background_key]));var pan=-(elapsed-3.8)*12. if spec.weapon=="弓" and elapsed>3.8 and elapsed<float(spec.hit) else 0.
	ui.draw_set_transform(origin,0,Vector2.ONE*scale)
	# Scenery is frozen for this strike; actors/VFX remain separate native layers.
	ui.draw_texture_rect_region(bg,Rect2(0,0,640,360),Rect2((640.-640./1.05)/2.-pan,(360.-360./1.05)/2.,640./1.05,360./1.05),_background_tint()*Color(1,1,1,opacity))
	var frame=clampi(floori(elapsed*float(program.fps)),0,program.frames.size()-1)
	for op in program.frames[frame]:
		match int(op[0]):
			0:
				var color=Color.hex(int(op[5]));color.a*=opacity;ui.draw_rect(Rect2(float(op[1]),float(op[2]),float(op[3]),float(op[4])),color)
			1:
				var size=Vector2(float(op[4]),float(op[5]));if int(op[10])==1:size.x=-size.x
				ui.draw_texture_rect_region(_textures[int(op[1])],Rect2(Vector2(float(op[2]),float(op[3])),size),Rect2(float(op[6]),float(op[7]),float(op[8]),float(op[9])),Color(1,1,1,float(op[11])*opacity))
			2:_draw_target(Vector2(float(op[1]),float(op[2])),float(op[3])*opacity)
			3:_label(op,origin,scale,opacity)
			4:
				ui.draw_rect(Rect2(float(op[1]),float(op[2]),float(op[3]),float(op[4])),Color("#3b3543")*Color(1,1,1,opacity))
				ui.draw_rect(Rect2(float(op[1]),float(op[2]),float(op[3])*maxf(0.,float(_shown_hp()))/maxi(1,_target_max_hp),float(op[4])),Color("#d7857d" if elapsed>=float(spec.hit) else "#c0a0ab")*Color(1,1,1,opacity))
func draw()->void:
	if not active:return
	var ui=_ui();var canvas=ui.get_viewport_rect();var show=_ease((elapsed-.08)/.29)*(1.-_ease((elapsed-(duration()-.35))/.31))
	if show<=0:return
	var scale=minf((canvas.size.x-16)/640.,(canvas.size.y-16)/360.)*(.91+.09*show);var size=Vector2(640,360)*scale;var area=Rect2((canvas.size-size)/2,size)
	ui.draw_set_transform(Vector2.ZERO);ui.draw_rect(canvas,Color(0.01,.025,.04,show*.71))
	for spread in [6,4,2]:ui.draw_rect(area.grow(spread),Color(0,0,0,show*.13))
	ui.draw_rect(area.grow(1),Color(.43,.51,.54,show));_draw_scene(area.position,scale,show)
	ui.draw_set_transform(Vector2.ZERO);ui.draw_rect(Rect2(area.position,Vector2(area.size.x,1)),Color(.72,.69,.58,show))
	ui.draw_set_transform(ui._canvas_offset())

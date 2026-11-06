extends RefCounted
## D00 is a visual sequence over an ordinary P00 checkpoint, never a battle.
## Dialogue uses the shared pager; timed shots never expose director's notes.
const DATA="res://data/prologue_scene.json"
const Checkpoint=preload("res://core/prologue_checkpoint.gd")
const ART="res://assets/prologue-d00-20261026/"
const ORIGIN=Vector2(16,8)
const VERSION=1
var _owner:WeakRef
var ui:
	get:return _owner.get_ref()
var spec:Dictionary={}
var active=false
var reprise_mode=false
var state:Dictionary={}
var advance_pending=false
var checkpoint_second=-1
var audit:Dictionary={}
var islands_audit:Dictionary={}
var guard_art:Dictionary={}
var guard_walk_art:Dictionary={}
var cast_art:Dictionary={}

func _init(owner) -> void:
	_owner=weakref(owner);spec=owner.GameState.read_json(DATA)
	guard_art=owner.PartySprites.Reviewed.metadata().maps["22_enemy"]["tactical-idle"]
	guard_walk_art=owner.PartySprites.Reviewed.metadata().maps["22_enemy"]["tactical-walk"]
	cast_art=owner.GameState.read_json("res://data/prologue_cast.json").actors

func can_resume() -> bool:
	if ui.game.chapter!=1 or ui.game.hub_record!="P00" or ui.game.flags.get("prologue_done",false):return false
	return ui.game.flags.has("prologue_scene") or str(ui.game.flags.get("active_plot",{}).get("callback",""))=="prologue"

func start() -> void:
	if active or ui.game.chapter!=1 or ui.game.hub_record!="P00" or ui.game.flags.get("prologue_done",false):return
	ui.game.flags.erase("active_plot")
	active=true;reprise_mode=false;advance_pending=false
	state={"version":VERSION,"step":0,"time":0.0,"clock":0.0,"sounds":{}}
	_enter(0)

func resume() -> void:
	# A retired linear D00 checkpoint restarts the new scene at recognition.
	# No units, rewards, route progress or injury data are changed.
	var saved=ui.game.flags.get("prologue_scene",{})
	if not Checkpoint.valid(saved):
		active=false;start();return
	state=saved.duplicate(true)
	state.step=clampi(int(state.get("step",0)),0,spec.steps.size()-1)
	state.time=maxf(0.0,float(state.get("time",0.0)));state.clock=maxf(0.0,float(state.get("clock",0.0)))
	if not state.get("sounds",{}) is Dictionary:state.sounds={}
	active=true;reprise_mode=false;advance_pending=false;_enter(int(state.step),true)

func _persist() -> void:
	if reprise_mode:return
	ui.game.flags.prologue_scene=state.duplicate(true);ui.game.save_game()

func _enter(index:int,restoring:bool=false) -> void:
	if index>=spec.steps.size():_finish();return
	state.step=index
	if not restoring:state.time=0.0
	checkpoint_second=int(state.time)
	ui.busy=true;ui.held_direction=Vector2i.ZERO;ui._clear_menu();ui.view="prologue_scene"
	var shot:Dictionary=spec.steps[index]
	_persist()
	if str(shot.kind)=="dialogue":
		if restoring and str(ui.game.flags.get("active_plot",{}).get("callback",""))=="d00_next":ui._resume_plot()
		else:ui.play_pages(ui.game.campaign.scenes.D00.slice(int(shot.from),int(shot.to)),"hub","d00_next")
	ui.queue_redraw()

func dialogue_finished() -> void:
	# Let the previous play_pages coroutine finish before opening its successor.
	ui.view="prologue_scene";advance_pending=true

func process(delta:float) -> void:
	if not active:return
	if reprise_mode:
		state.clock=float(state.get("clock",0.0))+delta;ui.game.flags.prologue_reprise_clock=state.clock;ui.queue_redraw();return
	if advance_pending:advance_pending=false;_enter(int(state.step)+1);return
	state.clock+=delta
	var shot:Dictionary=spec.steps[int(state.step)]
	if str(shot.kind)!="dialogue":
		state.time+=delta
		if str(shot.kind)=="cast_block":
			if state.time>=0.72:_sound("cast","rm_sfx_06")
			if state.time>=1.58:_sound("block","rm_sfx_03")
		if str(shot.kind)=="projection" and state.time>=0.2:_sound("curtain","rm_sfx_23")
		if int(state.time)>checkpoint_second:checkpoint_second=int(state.time);_persist()
		if state.time>=float(shot.duration):_enter(int(state.step)+1)
	ui.queue_redraw()

func _sound(key:String,cue:String) -> void:
	if state.sounds.get(key,false):return
	state.sounds[key]=true;ui.audio.play_sfx(cue);_persist()

func accept() -> void:
	# Confirm never skips the cast, interception, evacuation or held gesture.
	if not active or reprise_mode:return
	var shot:Dictionary=spec.steps[int(state.step)]
	if str(shot.kind)=="flashback" and state.time>=float(shot.get("minimum",1.0)):_finish()

func _finish() -> void:
	active=false;advance_pending=false;ui.plot_finished=true;ui.busy=false
	ui.game.flags.erase("active_plot");ui.game.flags.erase("prologue_scene")
	ui.game.flags.prologue_done=true;ui.game.world_node=1;ui.hub_controller.enter_room("H01")

func reprise() -> void:
	resume_reprise()
	await ui.play_pages(ui.game.campaign.scenes.D31,"hub","third_prologue")

func resume_reprise() -> void:
	active=true;reprise_mode=true;advance_pending=false
	state={"clock":float(ui.game.flags.get("prologue_reprise_clock",0.0))}

func end_reprise() -> void:
	active=false;reprise_mode=false;ui.game.flags.erase("prologue_reprise_clock")

func _sprite(art:Dictionary,foot:Vector2,frame:int=0,scale:float=1.0,tint:Color=Color.WHITE) -> void:
	if art.is_empty():return
	var density=float(art.get("native_density",1.0));var size=Vector2(art.frame_size[0],art.frame_size[1]);var columns=int(art.get("columns",maxi(1,frame+1)))
	var source=Rect2(Vector2(frame%columns,floori(float(frame)/columns))*size,size)
	var anchor=Vector2(art.get("anchor",[size.x/density/2.0,size.y/density])[0],art.get("anchor",[size.x/density/2.0,size.y/density])[1])
	ui.draw_texture_rect_region(ui._tex(str(art.path)),Rect2((foot-anchor*scale).round(),size/density*scale),source,tint)

func _hero(id:String,foot:Vector2,direction:String="right",walking:bool=false,travel_clock:float=-1.0) -> int:
	# Present-time identities are fixed; never borrow later recruited companions.
	var actor:Dictionary=ui.game.characters[id].duplicate(true);actor.side="player"
	var art=ui.PartySprites.sprite("hub",actor,1)
	# An old cinematic checkpoint must never freeze a restarted P00 walk.
	var clock=travel_clock if travel_clock>=0 else float(state.get("clock",0.0)) if active else ui.hub_controller.clock*2.0
	var frame=ui.PartySprites.Reviewed.travel_frame(art,direction,clock,walking)
	_sprite(art,foot,frame)
	return frame

func _pose(id:String,pose:int,foot:Vector2) -> void:
	# Fixed map scale through idle, travel, casting, interception and D31.
	_sprite(cast_art[id],foot,pose)

func _civilian(foot:Vector2,scale:float=1.0,tint:Color=Color.WHITE) -> void:
	var art:Dictionary=ui.PostbattleNpcs.data().profiles.village_man.hub
	_sprite(art,foot,0,scale,tint)

func _herlan(foot:Vector2,pose:int=0) -> void:
	_pose("herlan",pose,foot)

func _guard(foot:Vector2,direction:String="right",walking:bool=false) -> void:
	var clock=float(state.get("clock",ui.elapsed))
	if walking:
		_sprite(guard_walk_art,foot,ui.PartySprites.Reviewed.travel_frame(guard_walk_art,direction,clock,true));return
	var cycle:Array=guard_art.native_cycle;var ticks:Array=guard_art.cycle_ticks
	var tick=int(clock*60.0988)%44;var frame=int(cycle[0])
	for n in range(cycle.size()):
		if tick<int(ticks[n]):frame=int(cycle[n]);break
		tick-=int(ticks[n])
	_sprite(guard_art,foot,frame)

func _floor() -> void:
	ui.draw_rect(ui._visible_native_rect(),Color("15242a"))
	var atlas=ui._tex("res://assets/battle_tiles/battle-tiles.png")
	for y in range(9):
		for x in range(14):ui._draw_atlas_cell(atlas,int(ui.battle_pack.base.cobble[(x*3+y)%4]),ORIGIN+Vector2(x,y)*16)
	ui._draw_hub_surroundings("P00",ORIGIN)
	for x in [1,10]:ui.draw_texture(ui._tex("res://assets/battle_tiles/modules/barracks.png"),ORIGIN+Vector2(x,0)*16)
	# Reuse real winter ground at the square's edges: lingering snow over wet paving.
	var snow=ui._tex("res://assets/battlefield-0.3.0/terrain.png")
	for cell in [Vector2i(0,1),Vector2i(0,2),Vector2i(1,2),Vector2i(12,2),Vector2i(13,2),Vector2i(13,3),Vector2i(0,7),Vector2i(13,7)]:
		ui._draw_atlas_cell(snow,5+(cell.x+cell.y)%3,ORIGIN+Vector2(cell)*16,Color(1,1,1,0.6))
	ui.draw_texture(ui._tex("res://assets/battle_tiles/modules/grain_wagon.png"),Vector2(18,92))
	for y in [91,110,129]:_civilian(Vector2(22,y),0.72)
	var altar_tint=Color.WHITE
	if active and not reprise_mode and _kind()=="projection" and float(state.time)<1.0:
		var pulse=sin(float(state.time)*PI);altar_tint=Color(1+2*pulse,1+1.6*pulse,1+.4*pulse)
	ui.draw_texture(ui._tex("res://assets/battle_tiles/modules/sun_altar.png"),Vector2(144,8),altar_tint)

func draw_plaza(cinematic:bool) -> void:
	_floor()
	if cinematic:
		_draw_stage();return
	_herlan(Vector2(168,56));_pose("eileen",0,Vector2(88,72))
	for foot in [Vector2(72,72),Vector2(104,72),Vector2(88,104)]:_guard(foot)
	var hub=ui.hub_controller
	var direction="up" if hub.facing.y<0 else "left" if hub.facing.x<0 else "right" if hub.facing.x>0 else "down"
	var travel_frame=_hero("hunapu",hub.render_position+ORIGIN+Vector2(8,16),direction,hub.motion_left>0)
	for object in hub.objects:
		if ui.game.hub_position+hub.facing==Vector2i(object.position[0],object.position[1]):ui._draw_indicator("down",ORIGIN+Vector2(object.position[0],object.position[1])*16+Vector2(4,-8))
	audit={"kind":"prepared_plaza","captive":true,"guard_count":3,"refugees":3,"snow_edges":true,"korlan_flag_raised":false,"map_body_height":16,"guard_profile":str(guard_art.reviewed_profile),"hero_walking":hub.motion_left>0,"hero_travel_frame":travel_frame}

func _kind() -> String:
	return "held" if reprise_mode else str(spec.steps[int(state.step)].kind)

func _stage_mode() -> String:
	if reprise_mode:return "held"
	var shot:Dictionary=spec.steps[int(state.step)]
	return str(shot.get("stage",shot.kind))

func _frame_at(time:float,starts:Array,frames:Array) -> int:
	var result=int(frames[0])
	for n in range(starts.size()):
		if time<float(starts[n]):break
		result=int(frames[n])
	return result

func _draw_stage() -> void:
	var mode=_stage_mode();var t=float(state.get("time",0.0))
	var intercept=Vector2(143,66);var hp=Vector2(128,100);var ep=Vector2(88,72)
	var hframe=0;var eframe=0;var rframe=0;var hpose=0;var epose=0;var spread=0.0
	if mode=="cast_block":
		var release=smoothstep(.1,.65,t);ep=Vector2(88,72).lerp(Vector2(96,76),release)
		eframe=_frame_at(t,[0,.12,.3,.52,.72,.9,1.34,1.85],[0,1,2,3,4,5,6,7]);epose=1 if t<.65 else 2
		var step=smoothstep(.65,1.34,t);hp=Vector2(128,100).lerp(intercept,step)
		hframe=_frame_at(t,[0,.65,.88,1.18,1.58,1.82,2.12,2.45],[0,1,2,3,4,3,5,0]);hpose=1 if t>=1.18 and t<2.12 else 0
		rframe=_frame_at(t,[0,.25,.72,.95,1.3,1.58,1.85,2.12,2.4],[0,1,2,3,4,5,6,7,0])
		spread=release
	elif mode in ["after_block","projection","island_dialogue","reach","held","fade","flashback"]:
		hp=intercept;ep=Vector2(96,76);eframe=7;epose=3;spread=1
	if mode in ["reach","held","fade","flashback"]:
		var u=smoothstep(0.0,.65,t) if mode=="reach" else 1.0
		hp=intercept.lerp(Vector2(134,81),u)
		hframe=_frame_at(t,[0,.15,.32,.65,.8,1.0],[0,2,5,5,6,7]) if mode=="reach" else 7
		hpose=2 if u<.9 else 3
	# All three existing blue-purple enemy bastion guardians remain in the shot.
	_herlan(Vector2(168,56),rframe)
	_guard(Vector2(72,72).lerp(Vector2(61,77),spread),"left",spread>0 and spread<1)
	_guard(Vector2(104,72).lerp(Vector2(116,90),spread),"right",spread>0 and spread<1)
	_guard(Vector2(88,104))
	_pose("eileen",eframe,ep)
	var hero_walking=(mode=="cast_block" and t>=.65 and t<1.34) or (mode=="reach" and t<.65)
	var travel_frame=-1
	if hero_walking:travel_frame=_hero("hunapu",hp,"right" if mode=="cast_block" else "left",true,(t-.65 if mode=="cast_block" else t)*2.0)
	else:_pose("hunapu",hframe,hp)
	var impact=false;var projectile=false;var spell_at=Vector2.ZERO
	if mode=="cast_block" and t>=.9 and t<=1.85:
		var progress=clampf((t-.9)/.68,0,1)
		# A single cast follows the small body's hand to the raised blocking arms.
		var from_hand=Vector2(104,67);var blocking_hands=intercept+Vector2(-6,-9)
		spell_at=from_hand.lerp(blocking_hands,progress)
		var effect=ui.PartySprites.Reviewed.metadata().sprites["character-sync-781ff6f08108738a5178"]
		_sprite(effect,spell_at,0,.65 if t>1.58 else .45);projectile=true;impact=t>=1.58
		if impact:ui.draw_rect(Rect2(ui._visible_native_rect().position,Vector2(ui.get_viewport_rect().size.x,144)),Color(1,.84,.55,maxf(0,(1.85-t)*.35)))
	audit={"kind":_kind(),"stage":mode,"hero":hp,"eileen":ep,"herlan":Vector2(168,56),"hero_pose":hpose,"eileen_pose":epose,"hero_frame":hframe,"eileen_frame":eframe,"herlan_frame":rframe,"projectile":projectile,"spell_at":spell_at,"impact":impact,"spell_target":"herlan","interceptor":"hunapu","guards_released":spread>=1,"guard_count":3,"guard_profile":str(guard_art.reviewed_profile),"map_body_height":16,"reprise":reprise_mode,"hero_walking":hero_walking,"hero_travel_frame":travel_frame}

func _fit(path:String,area:Rect2,alpha:float=1.0) -> Rect2:
	var tex=ui._tex(path);var scale=minf(area.size.x/tex.get_width(),area.size.y/tex.get_height());var size=tex.get_size()*scale
	var rect=Rect2(area.get_center()-size/2.0,size);ui.draw_texture_rect(tex,rect,false,Color(1,1,1,alpha));return rect

func _islands(area:Rect2,clock:float) -> void:
	var rect=_fit(ART+"east-evacuation.webp",area)
	var scale=rect.size.x/256.0;var tint=Color(.72,.79,.9)
	var boat=ui._tex(ART+"rowboat.png");var cycle=fmod(clock,8.0)
	var a=Vector2(32+fmod(clock*5,93),105)
	var b=Vector2(239-maxf(0,cycle-4)*4,98)
	for p in [a,b]:ui.draw_texture_rect(boat,Rect2(rect.position+(p-Vector2(15,8))*scale,Vector2(30,16)*scale),false,tint)
	_civilian(rect.position+(a+Vector2(-3,-1))*scale,.33*scale,tint)
	_civilian(rect.position+Vector2(225,64)*scale,.46*scale,tint)
	var aboard=cycle>=3.2
	var walk=clampf((cycle-.4)/2.8,0,1)
	var person=Vector2(231,71).lerp(Vector2(250,85),walk*2) if walk<.5 else Vector2(250,85).lerp(Vector2(239,96),(walk-.5)*2)
	if aboard:person=b+Vector2(0,-2)
	_civilian(rect.position+person*scale,.4*scale,tint)
	if cycle>=1.8:_civilian(rect.position+(b+Vector2(8,-2))*scale,.33*scale,tint)
	islands_audit={"boat_a":a,"boat_b":b,"boarder":person,"aboard":aboard,"clock":clock,"live_scene":true}

func draw() -> void:
	islands_audit={}
	var kind=_kind();var bounds=ui._visible_native_rect();var t=float(state.get("time",0.0))
	draw_plaza(true)
	if kind=="knot":
		ui.draw_rect(bounds,Color(0,0,0,.82));_fit(ART+"wrist-knot.webp",Rect2(bounds.position.x+8,4,bounds.size.x-16,136),minf(1,t/.3))
	elif kind=="face":
		ui.draw_rect(bounds,Color(0,0,0,.75))
		var portrait=ui.Portraits.entry("eileen_present")
		ui.draw_texture_rect(ui._tex(portrait.path),Rect2(80,28,96,96),false)
	elif kind=="projection":
		# Same live evacuation clock before and after the sunlit square cutaway.
		if t<1.0:
			ui.draw_rect(Rect2(bounds.position.x,0,bounds.size.x,144),Color(1,.92,.67,sin(t*PI)*.22))
		elif t<4.0 or t>=5.1:
			ui.draw_rect(bounds,Color.BLACK)
			_islands(Rect2(bounds.position.x+4,2,bounds.size.x-8,140),float(state.clock))
		else:ui.draw_rect(Rect2(bounds.position.x,0,bounds.size.x,144),Color(1,.96,.79,.12))
	elif kind=="fade":ui.draw_rect(bounds,Color(0,0,0,clampf(t/float(spec.steps[int(state.step)].duration),0,1)))
	elif kind=="flashback":
		ui.draw_rect(bounds,Color.BLACK)
		ui._center_text(str(spec.transition_caption),Rect2(bounds.position.x+16,102,bounds.size.x-32,24),Color(1,1,1,minf(1,t/.5)))
		if t>=1.0:ui._center_text("确认继续",Rect2(bounds.position.x+16,210,bounds.size.x-32,16),Color("8f9299"))
	# Black letterbox below the action never becomes a speech or director panel.
	if ui.view!="plot" and kind!="flashback":ui.draw_rect(Rect2(bounds.position.x,152,bounds.size.x,bounds.end.y-152),Color.BLACK)
	audit.kind=kind;audit.dialogue_visible=ui.view=="plot";audit.time=t
	if not islands_audit.is_empty():audit.islands=islands_audit.duplicate(true)

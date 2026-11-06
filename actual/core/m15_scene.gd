extends RefCounted
## Small map-scale tableaux on the actual fort map. Every timed shot and page
## has a checkpoint; all troop movement during a tableau is presentation only.
const VERSION=1
const FALL={"path":"res://assets/m15-story-20261101/korlan-last-moments.png","frame_size":[128,96],"columns":6,"native_density":4,"anchor":[16,20]}
var _owner:WeakRef
var ui:
	get:return _owner.get_ref()
var active=false
var state:Dictionary={}
var steps:Array=[]
var advance_pending=false
var checkpoint_second=-1
var audit:Dictionary={}

func _init(owner) -> void:_owner=weakref(owner)

func can_resume() -> bool:
	return ui.game.stage_id==105 and ui.game.flags.get("m15_scene",{}) is Dictionary and not ui.game.flags.get("m15_scene",{}).is_empty()

func _steps(scene:String,pages:Array) -> Array:
	match scene:
		"opening":return [
			{"kind":"grain","duration":2.6,"focus":"grain"},
			{"kind":"dialogue","pages":pages.slice(0,4),"focus":"entry"},
			{"kind":"command","duration":0.8,"focus":"boss"},
			{"kind":"dialogue","pages":pages.slice(4,7),"focus":"boss"},
			{"kind":"dialogue","pages":pages.slice(7),"focus":"entry"}]
		"escape":
			var shots=[
				{"kind":"turn","duration":0.65,"focus":"boss"},
				{"kind":"dialogue","pages":pages.slice(0,1),"focus":"boss"},
				{"kind":"watch","duration":0.45,"focus":"boss"}]
			# Older in-progress scenes still have the separate interception line.
			if pages.size()>1:shots.append({"kind":"dialogue","pages":pages.slice(1),"focus":"boss"})
			return shots
		"death":return [
			{"kind":"kneel","duration":0.6,"focus":"boss"},
			{"kind":"dialogue","pages":pages.slice(0,5),"focus":"boss","pose":1},
			{"kind":"rise","duration":0.8,"focus":"boss"},
			{"kind":"dialogue","pages":pages.slice(5,pages.size()-1),"focus":"boss","pose":2},
			{"kind":"collapse","duration":1.55,"focus":"boss"},
			{"kind":"silence","duration":1.15,"focus":"boss"},
			{"kind":"dialogue","pages":pages.slice(-1),"focus":"boss","pose":5},
			{"kind":"silence","duration":0.65,"focus":"boss"}]
	return []

func start(event:Dictionary,return_view:String) -> void:
	state={"version":VERSION,"scene":str(event.m15_scene),"pages":event.pages.duplicate(true),"return":return_view,"step":0,"time":0.0,"clock":0.0}
	steps=_steps(str(state.scene),state.pages)
	active=true;advance_pending=false
	if str(state.scene)=="death":ui.audio.play_music("rm_story_memory")
	_enter(0)

func resume() -> void:
	state=ui.game.flags.m15_scene.duplicate(true)
	steps=_steps(str(state.get("scene","")),state.get("pages",[]))
	active=true;advance_pending=false
	if str(state.scene)=="death":ui.audio.play_music("rm_story_memory")
	_enter(clampi(int(state.get("step",0)),0,maxi(0,steps.size()-1)),true)

func _persist() -> void:
	ui.game.flags.m15_scene=state.duplicate(true)
	ui.game.save_game()

func _enter(index:int,restoring:bool=false) -> void:
	if index>=steps.size():_finish();return
	state.step=index
	if not restoring:state.time=0.0
	checkpoint_second=int(state.time)
	ui.busy=true;ui.held_direction=Vector2i.ZERO;ui._clear_menu();ui.view="m15_scene"
	_persist()
	var shot:Dictionary=steps[index]
	if str(shot.kind)=="dialogue":
		if restoring and str(ui.game.flags.get("active_plot",{}).get("callback",""))=="m15_next":ui._resume_plot()
		else:ui.play_pages(shot.pages,str(state["return"]),"m15_next")
	ui.queue_redraw()

func dialogue_finished() -> void:
	ui.view="m15_scene";advance_pending=true

func process(delta:float) -> void:
	if not active:return
	if advance_pending:advance_pending=false;_enter(int(state.step)+1);return
	state.clock=float(state.clock)+delta
	var shot:Dictionary=steps[int(state.step)]
	if str(shot.kind)!="dialogue":
		state.time=float(state.time)+(maxf(delta,0.5) if ui.instant_mode else delta)
		if int(state.time)>checkpoint_second:checkpoint_second=int(state.time);_persist()
		if float(state.time)>=float(shot.duration):_enter(int(state.step)+1)
	ui.queue_redraw()

func _finish() -> void:
	var return_view=str(state.get("return","battle"))
	if str(state.get("scene",""))=="death":ui.game.flags.korlan_dead=true
	active=false;advance_pending=false
	ui.game.flags.erase("m15_scene");ui.game.flags.erase("active_plot")
	ui.plot_finished=true;ui.view=return_view
	ui.game.save_game()

func _sprite(art:Dictionary,foot:Vector2,frame:int=0) -> void:
	if art.is_empty():return
	var size=Vector2(art.frame_size[0],art.frame_size[1]);var density=float(art.get("native_density",1))
	var columns=int(art.get("columns",maxi(1,frame+1)))
	var source=Rect2(Vector2(frame%columns,floori(float(frame)/columns))*size,size)
	var anchor=art.get("anchor",[12,20])
	ui.draw_texture_rect_region(ui._tex(str(art.path)),Rect2((foot-Vector2(anchor[0],anchor[1])).round(),size/density),source)

func _actor(unit:Dictionary,foot:Vector2,direction:String="",walking:bool=false) -> void:
	var actor=unit.duplicate(false);actor.acted=false
	var art=ui.PartySprites.sprite("map_move" if not direction.is_empty() else "map",actor,1)
	if art.is_empty():art=ui._map_unit_sprite(actor)
	var frame=0
	if not direction.is_empty():frame=ui.PartySprites.Reviewed.travel_frame(art,direction,float(state.clock),walking)
	elif art.has("native_cycle"):frame=int(art.native_cycle[int(float(state.clock)*3)%art.native_cycle.size()])
	_sprite(art,foot,frame)

func _boss_cell() -> Vector2:
	var boss=ui.game.find_unit("M15_boss")
	return Vector2(boss.position[0],boss.position[1]) if not boss.is_empty() else Vector2(20,10)

func hero_cell() -> Vector2i:
	var hero=ui.game.find_unit("hunapu");var boss=Vector2i(_boss_cell())
	# A farewell on the coastal escape path needs different staging from the
	# courtyard. Pick real walkable ground, never a cliff, roof or occupied cell.
	for delta in [Vector2i(-2,0),Vector2i(0,2),Vector2i(2,0),Vector2i(0,-2),Vector2i(-2,1),Vector2i(2,1),Vector2i(-1,2),Vector2i(1,2)]:
		var cell=boss+delta
		if ui.game.in_bounds(cell) and ui.game.movement_cost(hero,cell)<255 and ui.game.can_stop(hero,cell):return cell
	return ui.game.pos(hero)

func draw() -> void:
	if not active or steps.is_empty():return
	var shot:Dictionary=steps[int(state.step)];var kind=str(shot.kind);var scene=str(state.scene)
	var bounds=ui._visible_native_rect();var area=Rect2(bounds.position,Vector2(bounds.size.x,maxf(112,bounds.size.y-104)))
	var focus=_boss_cell()+Vector2(0.5,0.5)
	if str(shot.focus)=="grain":focus=Vector2(28,5)
	elif str(shot.focus)=="entry":focus=Vector2(19,22)
	if scene=="opening" and ui.view=="plot" and str(ui.plot_pages[ui.plot_index].speaker)=="劳工":
		var worker=ui.game.units.filter(func(u):return str(u.id).begins_with("M15_workers") and int(u.hp)>0)
		if not worker.is_empty():focus=Vector2(worker[0].position[0],worker[0].position[1])
	var origin=(area.get_center()-focus*16).round()
	ui._draw_map(ui.game.battle_data.map,ui._tex(str(ui.graphics.compat_atlas)),origin)
	for unit in ui.game.units:
		if int(unit.hp)<=0 or unit.get("hidden",false) or str(unit.side)=="evacuated":continue
		if scene=="death" and str(unit.id) in ["M15_boss","hunapu"]:continue
		var foot=origin+Vector2(unit.position[0],unit.position[1])*16+Vector2(8,16)
		if str(unit.id)=="M15_boss" and scene=="escape":_actor(unit,foot,"right" if kind=="turn" and float(state.time)<0.3 else "up")
		elif str(unit.id)=="M15_boss" and kind=="command":_actor(unit,foot,"right" if float(state.time)<0.35 else "down")
		else:_actor(unit,foot)
	if scene=="opening" and kind=="grain":
		var progress=clampf(float(state.time)/float(shot.duration),0,1)
		for offset in [0.0,2.0]:
			var at=origin+Vector2(28,7+offset-progress*5.5)*16
			ui.draw_texture(ui._tex("res://assets/battle_tiles/modules/grain_wagon.png"),at-Vector2(8,8))
	var pose=-1
	var staged_hero=Vector2i.ZERO
	if scene=="death":
		pose=int(shot.get("pose",5))
		if kind=="kneel":pose=0 if float(state.time)<0.3 else 1
		elif kind=="rise":pose=1 if float(state.time)<0.25 else 2
		elif kind=="collapse":pose=3 if float(state.time)<0.45 else 4 if float(state.time)<0.9 else 5
		var foot=origin+_boss_cell()*16+Vector2(8,16)
		_sprite(FALL,foot,pose)
		var hero=ui.game.find_unit("hunapu")
		if not hero.is_empty():
			staged_hero=hero_cell()
			var delta=Vector2i(_boss_cell())-staged_hero
			var direction=("right" if delta.x>0 else "left") if absi(delta.x)>=absi(delta.y) else ("down" if delta.y>0 else "up")
			_actor(hero,origin+Vector2(staged_hero)*16+Vector2(8,16),direction)
	audit={"scene":scene,"kind":kind,"step":int(state.step),"pose":pose,"visual_only":true,"boss_hp":int(ui.game.find_unit("M15_boss").hp),"grain_wagons":2 if kind=="grain" else 0,"corpse_still":pose==5,"map_body_height":16,"hero_cell":[staged_hero.x,staged_hero.y]}

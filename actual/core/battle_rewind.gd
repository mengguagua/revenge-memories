extends RefCounted
## Keep genuine player-phase boundaries, independently of the retry checkpoint.
## Uses are outside the restored state, so neither rewinding nor reloading refunds them.
const LIMIT := 2
const VERSION := 1

static func _capture(g) -> Dictionary:
	var s={"schema":3,"campaign_id":g.CAMPAIGN_ID,"hub_record":g.hub_record,"map_revision":str(g.battle_data.get("tactical_review_version","0.2.0"))}
	for key in g.SAVE_FIELDS:
		if key=="battle_start_snapshot":continue
		var v=g.get(key)
		s[key]=[v.x,v.y] if v is Vector2i else v.duplicate(true) if v is Array or v is Dictionary else v
	return s

static func _matches(g) -> bool:
	return int(g.battle_rewind.get("stage",0))==int(g.stage_id) and int(g.battle_rewind.get("chapter",0))==int(g.chapter) and str(g.battle_rewind.get("route",""))==str(g.route)

static func reset(g) -> void:
	g.battle_rewind={"version":VERSION,"stage":int(g.stage_id),"chapter":int(g.chapter),"route":str(g.route),"used":0,"starts":[]}
	record(g)
	# Opening dialogue is consumed before the first actionable player phase.
	# Returning to turn one must not replay the entire battle introduction.
	if int(g.turn)==1 and not g.battle_rewind.starts.is_empty():g.battle_rewind.starts[0].story_events=[]

static func record(g) -> void:
	if g.mode!="battle" or g.phase!="player" or not g.battle_outcome.is_empty():return
	if not _matches(g):reset(g);return
	# A second call in the same turn must never overwrite its untouched start.
	if g.battle_rewind.starts.any(func(s):return int(s.turn)==int(g.turn)):return
	g.battle_rewind.starts.append(_capture(g))
	while g.battle_rewind.starts.size()>3:g.battle_rewind.starts.pop_front()

static func load_legacy(g) -> void:
	if not g.battle_rewind.is_empty() or g.mode not in ["battle","victory","defeat"] or g.battle_start_snapshot.is_empty():return
	# An older save proves only turn one's start. Never invent a past boundary
	# from the current, possibly already acted, formation.
	var initial=_capture(g)
	for key in g.battle_start_snapshot:
		if key in g.SAVE_FIELDS and key!="battle_start_snapshot":initial[key]=g.battle_start_snapshot[key].duplicate(true) if g.battle_start_snapshot[key] is Array or g.battle_start_snapshot[key] is Dictionary else g.battle_start_snapshot[key]
	initial.mode="battle";initial.phase="player";initial.turn=1;initial.kills=0
	initial.battle_outcome="";initial.battle_settled=false;initial.selected_id="";initial.victory_rewards=[];initial.story_events=[]
	initial.flags.erase("active_plot")
	for unit in initial.units:
		if str(unit.id)==g.leader_id():initial.cursor=unit.position.duplicate();initial.move_origin=unit.position.duplicate()
	g.battle_rewind={"version":VERSION,"stage":int(g.stage_id),"chapter":int(g.chapter),"route":str(g.route),"used":0,"starts":[initial]}

static func remaining(g) -> int:
	return maxi(0,LIMIT-int(g.battle_rewind.get("used",0))) if _matches(g) else LIMIT

static func reason(g) -> String:
	if g.mode!="battle" or g.phase!="player" or not g.battle_outcome.is_empty():return "只能在我方行动阶段回溯"
	if remaining(g)<=0:return "本场2次回溯已用完"
	if int(g.turn)<=1:return "第1回合还没有上回合"
	if not _matches(g) or not g.battle_rewind.starts.any(func(s):return int(s.turn)==int(g.turn)-1):return "旧记录没有上回合起点；记录新的完整回合后可用"
	return ""

static func _restore(g, s: Dictionary) -> void:
	for key in g.SAVE_FIELDS:
		if key=="battle_start_snapshot":continue
		var v=s[key]
		if key in ["hub_position","cursor","move_origin"]:g.set(key,Vector2i(int(v[0]),int(v[1])))
		elif key=="cleared_stages":g.cleared_stages=v.map(func(id):return int(id))
		else:g.set(key,v.duplicate(true) if v is Array or v is Dictionary else v)
	for key in ["stage_id","chapter","world_node","previous_world_node","turn","kills","rng_state","frame_counter"]:g.set(key,int(g.get(key)))
	g.hub_record=str(s.hub_record)
	g.battle_data=g.SaveValidation.campaign_stage(g,int(g.stage_id),str(s.map_revision)).duplicate(true)
	g._restore_battle_geometry()
	g.Battlefield.restore(g);g.Cover.refresh(g)
	g._escort_hint_stamp.clear();g.log_lines.clear()

static func commit(g) -> bool:
	if not reason(g).is_empty():return false
	var target_turn=int(g.turn)-1
	var target:Dictionary=g.battle_rewind.starts.filter(func(s):return int(s.turn)==target_turn)[0]
	var before=_capture(g);var history=g.battle_rewind.duplicate(true)
	_restore(g,target)
	g.selected_id="";g.cursor=g.pos(g.find_unit(g.leader_id()));g.move_origin=g.cursor
	g.battle_rewind.used=int(history.used)+1
	g.battle_rewind.starts=history.starts.filter(func(s):return int(s.turn)<=target_turn)
	if g.save_game():return true
	# A failed write consumes neither progress nor a rewind use.
	_restore(g,before);g.battle_rewind=history
	return false

static func for_save(g) -> Dictionary:
	return g.battle_rewind if _matches(g) and g.mode in ["battle","victory","defeat"] else {}

static func valid(g, state:Dictionary) -> bool:
	var value=state.get("battle_rewind",{})
	if not value is Dictionary:return false
	if value.is_empty():return true
	if value.get("version")!=VERSION or not g.SaveValidation._integer(value.get("used"),0,LIMIT):return false
	if value.get("stage")!=state.stage_id or value.get("chapter")!=state.chapter or value.get("route")!=state.route:return false
	if state.mode not in ["battle","victory","defeat"] or not value.get("starts") is Array or value.starts.size()>3:return false
	var previous=0
	for raw in value.starts:
		if not raw is Dictionary or raw.has("battle_rewind") or raw.has("battle_start_snapshot"):return false
		if not g.SaveValidation._integer(raw.get("turn"),previous+1,int(state.turn)):return false
		if raw.get("stage_id")!=state.stage_id or raw.get("chapter")!=state.chapter or raw.get("route")!=state.route:return false
		if raw.get("mode")!="battle" or raw.get("phase")!="player" or raw.get("battle_outcome")!="" or raw.get("battle_settled")!=false:return false
		if not raw.get("flags") is Dictionary or raw.flags.has("active_plot"):return false
		var checked=raw.duplicate(true);checked.battle_start_snapshot=state.battle_start_snapshot
		# Run the same unit, quest, geometry, casualty and training checks as the
		# live save. The nested state contains no rewind history, so this is bounded.
		if not g.SaveValidation.campaign_valid(g,checked,g.SAVE_FIELDS):return false
		for unit in raw.units:
			if unit.side=="player" and int(unit.hp)>0 and unit.acted:return false
		previous=int(raw.turn)
	return true

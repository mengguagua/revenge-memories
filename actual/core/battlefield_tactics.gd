extends RefCounted
## Authored, telegraphed battle decisions. State lives in the ordinary quest save.
const Rules = preload("res://core/combat_rules.gd")
const Items = preload("res://core/item_rules.gd")
const VERSION = 1

static func _point(value) -> Vector2i:
	return value if value is Vector2i else Vector2i(int(value[0]), int(value[1]))

static func _distance(a: Vector2i, b: Vector2i) -> int:
	return absi(a.x-b.x)+absi(a.y-b.y)

static func _spec(g) -> Dictionary:
	return g.battle_data.get("battlefield_tactics", {})

static func _state(g) -> Dictionary:
	return g.flags.get("quest", {}).get("battlefield", {})

static func initialize(g, new_battle: bool=true) -> void:
	if _spec(g).is_empty() and g.battle_data.get("breakable_obstacles", []).is_empty():return
	if not g.flags.has("quest"):g.flags.quest={}
	if new_battle or not g.flags.quest.has("battlefield"):
		g.flags.quest.battlefield={"version":VERSION,"broken":{},"intents":{},"last_turn":{},"command_announced":false}
	if new_battle:
		var intro=str(_spec(g).get("intro", ""))
		if not intro.is_empty():g.queue_lines(intro, str(g.battle_data.code)+"-TACTICAL-INTRO")
		for obstacle in g.battle_data.get("breakable_obstacles", []):
			g.queue_lines("战场提示："+str(obstacle.name_zh)+"可在邻格消耗一次行动破坏。"+str(obstacle.effect_text), str(obstacle.id)+"-BREAKABLE-INTRO")
		after_phase(g)
	restore(g)

static func restore(g) -> void:
	if _spec(g).is_empty() and g.battle_data.get("breakable_obstacles", []).is_empty():return
	# Existing in-progress saves receive no retroactive attack or mid-turn warning.
	if _state(g).is_empty():
		if not g.flags.has("quest"):g.flags.quest={}
		g.flags.quest.battlefield={"version":VERSION,"broken":{},"intents":{},"last_turn":{},"command_announced":false}
	_discard_expired(g)
	for obstacle in g.battle_data.get("breakable_obstacles", []):
		if _state(g).broken.get(str(obstacle.id), false):_open_obstacle(g, obstacle)

static func _command_active(g) -> bool:
	var command:Dictionary=_spec(g).get("command", {})
	if command.is_empty() or g.turn<int(command.get("first_turn", 2)):return false
	var commander=g.find_unit(str(command.commander))
	return not commander.is_empty() and int(commander.hp)>0 and not commander.get("surrendered", false) and not g.flags.quest.get("objects", {}).get(str(command.disable_object), false)

static func after_phase(g) -> void:
	if g.phase!="player" or not g.battle_outcome.is_empty():return
	var state=_state(g)
	if state.is_empty():return
	_discard_expired(g)
	if _command_active(g) and not state.command_announced:
		state.command_announced=true
		g.queue_lines(str(_spec(g).command.warning), str(g.battle_data.code)+"-TACTICAL-COMMAND")
	for attack in _spec(g).get("attacks", []):
		var id=str(attack.actor);var actor=g.find_unit(id)
		if actor.is_empty() or int(actor.hp)<=0 or actor.get("surrendered", false):continue
		if g.turn<int(attack.get("first_turn", 2)) or g.turn<int(state.last_turn.get(id, -100))+int(attack.get("interval", 3)):continue
		if state.intents.has(id):continue
		var selected=_choose_cells(g, actor, attack)
		if selected.is_empty():continue
		var intent={"actor":id,"name":str(attack.name),"origin":actor.position.duplicate(),"cells":selected,
			"turn":g.turn,"damage_taken":0,"interrupted":false,"break_damage":int(attack.get("break_damage", 0)),
			"power":int(actor.strength)+int(attack.get("power_bonus", 0)),"kind":str(attack.get("kind", "physical")),
			"warning":str(attack.warning)}
		state.intents[id]=intent;state.last_turn[id]=g.turn
		g.queue_lines(str(actor.name_zh)+"："+str(attack.warning)+"／战场提示："+_intent_text(intent), str(g.battle_data.code)+"-INTENT-"+id+"-"+str(g.turn))

static func _discard_expired(g) -> void:
	var state=_state(g)
	if state.is_empty():return
	for id in state.intents.keys():
		var actor=g.find_unit(str(id));var intent:Dictionary=state.intents[id]
		# A skipped/dead source cannot release yesterday's attack after a reload.
		# Same-turn interrupted intentions remain until their ordinary spent action.
		if int(intent.turn)!=g.turn or actor.is_empty() or int(actor.get("hp",0))<=0:
			state.intents.erase(id)

static func _choose_cells(g, actor: Dictionary, attack: Dictionary) -> Array:
	var best:Array=[];var best_score=-1;var reach=int(attack.get("range", 3))
	for target in g.living("player"):
		if target.get("neutral", false) or target.get("event_object", false) or not target.get("controllable", true):continue
		var center=g.pos(target)
		if _distance(g.pos(actor), center)>reach:continue
		var cells:Array=[center]
		if str(attack.get("shape", "cross"))=="cross":
			for offset in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:cells.append(center+offset)
		else:
			var delta=center-g.pos(actor)
			var perpendicular=Vector2i.RIGHT if absi(delta.y)>=absi(delta.x) else Vector2i.DOWN
			cells.append(center+perpendicular);cells.append(center-perpendicular)
		cells=cells.filter(func(cell):return g.in_bounds(cell) and _distance(g.pos(actor),cell)<=reach)
		var score=0
		for unit in g.living("player"):
			if not unit.get("locked", false) and cells.has(g.pos(unit)):score+=1
		if score>best_score:
			best_score=score;best=cells.map(func(cell):return [cell.x,cell.y])
	return best

static func _intent_text(intent: Dictionary) -> String:
	var text=str(intent.name)+"将在本回合敌方阶段攻击标记格；撤离可避开，掩护可分担。推动蓄力者可打断"
	if int(intent.break_damage)>0:text+="，准备期间累计造成%d点实际伤害也可打断"%int(intent.break_damage)
	return text+"。标记格内必中；威力%d，按%s结算。"%[int(intent.power),"魔防" if str(intent.kind)=="magic" else "物防"]

static func record_damage(g, unit_id: String, amount: int) -> void:
	var state=_state(g)
	if state.is_empty() or amount<=0 or not state.intents.has(unit_id):return
	var intent:Dictionary=state.intents[unit_id]
	intent.damage_taken=int(intent.damage_taken)+amount
	if int(intent.break_damage)>0 and int(intent.damage_taken)>=int(intent.break_damage) and not intent.interrupted:
		intent.interrupted=true
		g.queue_lines("战场提示："+str(intent.name)+"被打断。敌方仍可正常反击，本次蓄力动作失效。")

static func _interrupted(g, actor: Dictionary, intent: Dictionary) -> bool:
	return bool(intent.get("interrupted", false)) or g.pos(actor)!=_point(intent.origin)

static func action(g, actor: Dictionary, gather: bool=false) -> Dictionary:
	if gather or actor.get("side", "")!="enemy" or int(actor.get("hp", 0))<=0 or actor.get("acted", false):return {}
	var state=_state(g)
	if state.is_empty():return {}
	var id=str(actor.id)
	if state.intents.has(id):
		return {"destination":g.pos(actor),"target":"","spell_id":-1,"support":false,"teleport":false,"special":"battlefield_release"}
	if not _command_active(g):return {}
	for follower in _spec(g).command.followers:
		if str(follower.id)!=id:continue
		actor.guard_alerted=true
		var response=g.CampaignTactics.action(g, actor)
		if not str(response.get("target", "")).is_empty():return response
		var goal=_point(follower.destination)
		if g.pos(actor)==goal:return response
		var advance=g._toward(actor, goal)
		if advance.destination!=g.pos(actor):return advance
		return response
	return {}

static func apply_special(g, actor: Dictionary, action_data: Dictionary) -> Dictionary:
	var state=_state(g);var id=str(actor.get("id", ""))
	if action_data.get("special", "")!="battlefield_release" or state.is_empty() or not state.intents.has(id):return {}
	if actor.get("side", "")!="enemy" or int(actor.get("hp", 0))<=0 or actor.get("acted", false) or g.phase!="enemy":return {}
	var intent:Dictionary=state.intents[id]
	state.intents.erase(id);actor.acted=true
	var result={"action":"battlefield_release","name":str(intent.name),"changed":[],"cells":intent.cells.duplicate(true),"interrupted":_interrupted(g,actor,intent)}
	if result.interrupted:
		g.queue_lines("战场提示："+str(intent.name)+"准备被打乱，本次攻击取消。")
		return result
	# Targets are the announced cells, never a newly selected substitute target.
	for target in g.living("player").duplicate():
		if target.get("locked",false) or target.get("event_object",false) or not intent.cells.any(func(p):return _point(p)==g.pos(target)):continue
		var defence=Items.magic_defence(target) if str(intent.kind)=="magic" else int(target.get("defence",0))+Items.physical_defence_bonus(target,actor)
		var damage=maxi(1,int(intent.power)-defence)
		var before=int(target.hp)
		var actual=g.apply_tactical_damage(actor,target,damage,str(intent.kind))
		_record_change(result.changed,str(target.id),before,int(target.hp),actual)
		var cover:Dictionary=actual.get("cover",{})
		if not cover.is_empty():
			var guard=g.find_unit(str(cover.unit))
			_record_change(result.changed,str(cover.unit),int(cover.hp_before),int(cover.hp_after),actual)
			g.queue_lines("战场提示："+str(guard.get("name_zh","同伴"))+"掩护分担"+str(int(cover.damage))+"伤害。")
	g.queue_lines("战场提示："+str(intent.name)+"已释放。仅标记格承受直接攻击，掩护分担另行结算。")
	g.check_outcome()
	return result

static func _record_change(changes:Array, id:String, before:int, after:int, damage:Dictionary) -> void:
	if before==after:return
	# An ally may both cover one hit and stand in the announced area. Preserve
	# the chronological health endpoints and each real event, but animate once.
	for change in changes:
		if str(change.id)!=id:continue
		change.after=after;change.events.append(damage.duplicate(true));return
	changes.append({"id":id,"before":before,"after":after,"damage":damage.duplicate(true),"events":[damage.duplicate(true)]})

static func warning_cells(g) -> Array:
	var result:Array=[];var state=_state(g)
	if state.is_empty():return result
	for intent in state.intents.values():
		var actor=g.find_unit(str(intent.actor))
		if actor.is_empty() or int(actor.hp)<=0 or _interrupted(g,actor,intent):continue
		for p in intent.cells:
			result.append({"position":p.duplicate(),"name":str(intent.name),"actor":str(intent.actor),"text":_intent_text(intent)})
	return result

static func status(g) -> Array[String]:
	var result:Array[String]=[];var state=_state(g)
	if state.is_empty():return result
	for intent in state.intents.values():
		var actor=g.find_unit(str(intent.actor))
		if actor.is_empty() or int(actor.hp)<=0:continue
		if _interrupted(g,actor,intent):result.append(str(intent.name)+"：已打断")
		else:result.append(_intent_text(intent))
	if _command_active(g):result.append("铁骑钳击命令生效：击败统领或切断投送站可解除；守骑随后仍会正常交战。")
	for obstacle in g.battle_data.get("breakable_obstacles", []):
		if not state.broken.get(str(obstacle.id),false):result.append(str(obstacle.name_zh)+"："+str(obstacle.effect_text))
	return result

static func can_break(actor: Dictionary) -> bool:
	if actor.is_empty() or actor.get("side", "")!="player" or int(actor.get("hp",0))<=0 or actor.get("acted",false) or actor.get("neutral",false) or not actor.get("controllable",true):return false
	# Existing physical melee professions; switching the selected spell does not
	# remove a sword user's ability to dismantle an adjacent light obstacle.
	return int(actor.get("class_id",0)) in [1,2,3,4,5,6,7,8,9,10,11,14,21,22]

static func interactions_for(g, actor: Dictionary) -> Array:
	var result:Array=[];var state=_state(g)
	if state.is_empty() or not can_break(actor):return result
	for obstacle in g.battle_data.get("breakable_obstacles", []):
		if state.broken.get(str(obstacle.id),false) or _distance(g.pos(actor),_point(obstacle.position))!=1:continue
		var choice:Dictionary=obstacle.duplicate(true)
		choice.kind="breakable";choice.label="破坏"+str(obstacle.name_zh);choice.optional=true
		choice.confirm_text="消耗本次行动破坏"+str(obstacle.name_zh)+"。"+str(obstacle.effect_text)+"破坏不可在本场撤销。"
		result.append(choice)
	return result

static func interact(g, id: String) -> bool:
	var actor=g.find_unit(g.selected_id)
	for obstacle in interactions_for(g,actor):
		if str(obstacle.id)!=id:continue
		_state(g).broken[id]=true;_open_obstacle(g,obstacle)
		g.queue_lines("战场提示："+str(obstacle.name_zh)+"已破坏。"+str(obstacle.effect_text))
		g.mark_wait(str(actor.id))
		return true
	return false

static func _open_obstacle(g, obstacle: Dictionary) -> void:
	var cell=_point(obstacle.position)
	if not g.in_bounds(cell):return
	g.battle_data.map.tiles[cell.y*int(g.battle_data.map.width)+cell.x]=int(obstacle.open_tile)
	for i in range(g.battle_data.get("art_layers",[]).size()):
		g.battle_data.art_layers[i][cell.y][cell.x]=int(obstacle.base_art_tile) if i==0 else null
	var pixel=[cell.x*16,cell.y*16]
	g.battle_data.art_props=g.battle_data.get("art_props",[]).filter(func(prop):return not (_point(prop.position)==_point(pixel) and str(prop.path)==str(obstacle.get("remove_prop", ""))))
	# Keep the geometry labels consistent after removing a whole one-cell crate.
	for module in g.battle_data.get("art_modules",[]):
		if module.get("name", "") in ["crates","palisade_v","palisade_h"]:
			module.cells=module.get("cells",[]).filter(func(p):return _point(p)!=cell)

static func hint(g, cell: Vector2i) -> Dictionary:
	var state=_state(g)
	if state.is_empty():return {}
	for obstacle in g.battle_data.get("breakable_obstacles", []):
		if _point(obstacle.position)!=cell:continue
		var broken=state.broken.get(str(obstacle.id),false)
		return {"object_id":str(obstacle.id),"text":("已破坏 · 敌我可通行" if broken else "可破坏 · 邻格行动"),"available":not broken,"description":str(obstacle.effect_text),"kind":"breakable"}
	for mark in warning_cells(g):
		if _point(mark.position)==cell:return {"text":str(mark.name)+" · 敌方阶段命中此格","available":false,"description":str(mark.text),"kind":"danger"}
	return {}

static func _whole(value, minimum:int=0, maximum:int=100000) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value)==floor(float(value)) and int(value)>=minimum and int(value)<=maximum

static func _valid_cell(value, stage:Dictionary) -> bool:
	return value is Array and value.size()==2 and _whole(value[0],0,int(stage.map.width)-1) and _whole(value[1],0,int(stage.map.height)-1)

static func validate(_g, flags:Dictionary, stage:Dictionary) -> bool:
	var quest=flags.get("quest",{})
	if not quest is Dictionary:return false
	if not quest.has("battlefield"):return true
	var state=quest.battlefield
	if not state is Dictionary:return false
	if not _whole(state.get("version",0),VERSION,VERSION) or not state.get("command_announced",null) is bool:return false
	for key in ["broken","intents","last_turn"]:
		if not state.get(key,null) is Dictionary:return false
	var obstacle_ids=stage.get("breakable_obstacles",[]).map(func(o):return str(o.id))
	for id in state.broken:
		if not id is String or not obstacle_ids.has(id) or not state.broken[id] is bool:return false
	var specs:Dictionary={}
	for attack in stage.get("battlefield_tactics",{}).get("attacks",[]):specs[str(attack.actor)]=attack
	for id in state.last_turn:
		if not id is String or not specs.has(id) or not _whole(state.last_turn[id],1):return false
	for id in state.intents:
		if not id is String or not specs.has(id):return false
		var intent=state.intents[id];var spec:Dictionary=specs[id]
		if not intent is Dictionary:return false
		# GDScript rejects some cross-type comparisons at runtime. A malformed
		# checkpoint must return false before comparing any untrusted identity.
		for field in ["actor","name","kind"]:
			if not intent.get(field,null) is String:return false
		if intent.actor!=id or intent.name!=spec.name or intent.kind!=spec.kind:return false
		if not intent.get("interrupted",null) is bool or not _whole(intent.get("damage_taken",null)):return false
		if not _whole(intent.get("turn",null),1) or int(state.last_turn.get(id,-1))!=int(intent.turn):return false
		if not _whole(intent.get("power",null),0,100) or not _whole(intent.get("break_damage",null),0,100):return false
		if int(intent.break_damage)!=int(spec.get("break_damage",0)) or not _valid_cell(intent.get("origin",null),stage):return false
		var cells=intent.get("cells",null)
		if not cells is Array or cells.is_empty() or cells.size()>(5 if spec.get("shape","")=="cross" else 3):return false
		var seen:Dictionary={}
		for p in cells:
			if not _valid_cell(p,stage):return false
			var cell=_point(p)
			if seen.has(cell) or _distance(cell,_point(intent.origin))>int(spec.range):return false
			seen[cell]=true
	return true

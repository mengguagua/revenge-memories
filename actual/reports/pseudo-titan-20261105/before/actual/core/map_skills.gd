extends RefCounted
## Hero and healer MAP actions. Confirmation commits a complete action atomically; the
## animation presents the frozen receipt and never reapplies HP or rewards.
const Rules=preload("res://core/combat_rules.gd")
const Items=preload("res://core/item_rules.gd")
const Professions=preload("res://core/hero_professions.gd")
const Experience=preload("res://core/campaign_experience.gd")
const Healing=preload("res://core/healing_map_skills.gd")
const StrongBody=preload("res://core/strong_body.gd")
const LIMIT=3

static func eligible(unit:Dictionary)->bool:
	return Healing.eligible(unit) or not Professions.definition(unit).is_empty()

static func used(unit:Dictionary)->int:
	return clampi(int(unit.get("map_uses",0)),0,LIMIT)

static func clear(unit:Dictionary)->void:
	unit.erase("map_uses");unit.erase("map_fatigue_until_turn");unit.erase("map_move_penalty_until_turn");StrongBody.clear(unit)

static func reset_battle(actors:Array)->void:
	for unit in actors:clear(unit)

static func expire_after_player_phase(g)->void:
	if g.phase!="player":return
	for unit in g.units:
		for field in ["map_fatigue_until_turn","map_move_penalty_until_turn"]:
			if int(unit.get(field,0))>0 and int(g.turn)>=int(unit[field]):unit.erase(field)

static func profile(unit:Dictionary)->Dictionary:
	if Healing.eligible(unit):return Healing.profile(unit)
	if not eligible(unit):return {}
	var advanced=Professions.advanced(unit)
	var male=str(unit.id)=="hunapu"
	var bow=male and advanced and Rules.weapon_index(unit) in [1,20,21,22]
	var tier=used(unit)
	return {"key":"hunapu_bow" if bow else ("hunapu_advanced" if advanced else "hunapu_base") if male else ("eileen_advanced" if advanced else "eileen_base"),
		"name":("破晓·破阵" if advanced else "破阵") if male else ("引光·焰环" if advanced else "焰环"),
		"advanced":advanced,"male":male,"bow":bow,"magic":not male,"tier":tier,
		"power":([0,3,6] if advanced else [0,2,4])[mini(2,tier)],
		"cost":ceili(float(unit.get("max_hp",1))*([0.0,.25,.4][mini(2,tier)])),
		"depth":4 if advanced else 2,"reach":4 if advanced else 3,"radius":2 if advanced else 1}

static func cells(g,unit:Dictionary,center:Vector2i,facing:Vector2i=Vector2i.RIGHT)->Array:
	var spec=profile(unit);var result=[]
	if spec.is_empty():return result
	if spec.get("support",false):return [center] if g.in_bounds(center) else []
	if spec.male:
		if facing not in [Vector2i.UP,Vector2i.DOWN,Vector2i.LEFT,Vector2i.RIGHT]:return result
		var side=Vector2i(-facing.y,facing.x)
		for depth in range(1,int(spec.depth)+1):
			for width in range(-1,2):
				var p=g.pos(unit)+facing*depth+side*width
				if g.in_bounds(p):result.append(p)
	else:
		for y in range(-int(spec.radius),int(spec.radius)+1):
			for x in range(-int(spec.radius),int(spec.radius)+1):
				var p=center+Vector2i(x,y)
				if absi(x)+absi(y)<=int(spec.radius) and g.in_bounds(p):result.append(p)
	return result

static func preview(g,id:String,center:Vector2i,facing:Vector2i=Vector2i.RIGHT)->Dictionary:
	if Healing.eligible(g.find_unit(id)):return Healing.preview(g,id,center)
	var actor=g.find_unit(id);var spec=profile(actor)
	if spec.is_empty():return {"valid":false,"reason":"该角色没有MAP技能"}
	var result=spec.duplicate(true)
	result.merge({"valid":false,"actor":id,"center":[center.x,center.y],"facing":[facing.x,facing.y],"targets":[],"cells":[]})
	if g.mode!="battle" or g.phase!="player" or not str(g.battle_outcome).is_empty():result.reason="当前不能释放MAP";return result
	if int(actor.get("hp",0))<=0 or actor.get("acted",false) or not actor.get("controllable",true):result.reason="本回合已经行动";return result
	if int(spec.tier)>=LIMIT:result.reason="本场MAP三次额度已用尽";return result
	if int(actor.hp)<=int(spec.cost):result.reason="支付后至少需要保留1HP";return result
	if not g.in_bounds(center) or (not spec.male and absi(center.x-g.pos(actor).x)+absi(center.y-g.pos(actor).y)>int(spec.reach)):
		result.reason="选点超出MAP范围";return result
	result.cells=cells(g,actor,center,facing)
	if result.cells.is_empty():result.reason="请选择攻击方向";return result
	result.hp_before=int(actor.hp);result.hp_after=int(actor.hp)-int(spec.cost)
	for target in g.units:
		if target.get("side","")!="enemy" or int(target.get("hp",0))<=0 or target.get("hidden",false) or target.get("event_object",false) or not result.cells.has(g.pos(target)):continue
		var defence=Items.magic_defence(target) if spec.magic else Rules._defence(target)+Items.physical_defence_bonus(target,actor)
		if spec.male and spec.advanced:defence-=floori(defence*.25)
		var bonus=4 if spec.magic and spec.advanced and g.pos(target)==center else 0
		var blocked=Rules.attack_blocked(actor,target)
		var damage=0 if blocked else clampi(int(actor.strength)+int(spec.power)+bonus-defence,1,60)
		var before=int(target.hp)
		result.targets.append({"id":str(target.id),"unit":target.duplicate(true),"position":target.position.duplicate(),
			"hp_before":before,"hp_after":maxi(0,before-damage),"damage":mini(before,damage),
			"raw_damage":damage,"center_bonus":bonus,"blocked":blocked})
	if result.targets.is_empty():result.reason="范围内没有可攻击的敌人";return result
	result.valid=true;result.reason="";return result

static func apply(g,id:String,center:Vector2i,facing:Vector2i=Vector2i.RIGHT)->Dictionary:
	if Healing.eligible(g.find_unit(id)):return Healing.apply(g,id,center)
	# Recompute at confirmation. A stale forecast cannot spend a second action.
	var receipt=preview(g,id,center,facing)
	if not receipt.valid:return receipt
	var actor=g.find_unit(id)
	receipt.actor_unit=actor.duplicate(true)
	actor.hp=int(receipt.hp_after);actor.map_uses=used(actor)+1;actor.acted=true
	var gain=0
	for hit in receipt.targets:
		var event={"attacker":id,"defender":str(hit.id),"hit":true,"critical":false,
			"damage":int(hit.damage),"hp_before":int(hit.hp_before),"hp_after":int(hit.hp_after),"kind":"hero_map"}
		g.commit_strike(event)
		if int(hit.damage)>0 and not hit.unit.get("no_experience",false):
			# One action receives one normal-combat reward, never one per cell.
			gain=maxi(gain,Rules.experience_gain(actor,hit.unit,int(hit.hp_before),int(hit.hp_after),int(hit.hp_after)==0))
	if int(actor.map_uses)==LIMIT:actor.map_fatigue_until_turn=int(g.turn)+1
	receipt.reward={}
	if gain>0 and not actor.get("no_experience",false) and not g.Training.active(g):
		receipt.reward=Experience.award(g,actor,gain)
		receipt.reward.victory_training=false;receipt.reward.map_skill=true
	actor.erase("weapon_index")
	g.mark_wait(id);g.selected_id="";g.Cover.refresh(g)
	g.log_lines.append(str(actor.name_zh)+"释放"+str(receipt.name)+"，命中"+str(receipt.targets.size())+"名敌人")
	return receipt

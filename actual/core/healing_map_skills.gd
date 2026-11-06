extends RefCounted
## One ally, one heal, one refreshed buff, one action. Presentation uses this receipt.
const Rules=preload("res://core/combat_rules.gd")
const StrongBody=preload("res://core/strong_body.gd")
const Experience=preload("res://core/campaign_experience.gd")

static func eligible(unit:Dictionary)->bool:
	return unit.get("side","")=="player" and int(unit.get("class_id",0)) in [17,18] and not unit.get("neutral",false) and not unit.get("event_object",false) and not unit.get("dead",false) and unit.get("controllable",true)

static func profile(unit:Dictionary)->Dictionary:
	if not eligible(unit):return {}
	var advanced=int(unit.class_id)==17
	var tier=clampi(int(unit.get("map_uses",0)),0,3)
	return {"key":"saint" if advanced else "healer","name":"济世·愈护之环" if advanced else "愈护之环",
		"support":true,"advanced":advanced,"male":false,"bow":false,"magic":false,"tier":tier,"power":0,
		"heal":int(unit.get("strength",0))+([2,6,10] if advanced else [0,3,6])[mini(tier,2)],
		"cost":ceili(float(unit.get("max_hp",1))*[0.0,.15,.25][mini(tier,2)]),"reach":10 if advanced else 8}

static func targetable(target:Dictionary,id:String)->bool:
	return not target.is_empty() and str(target.get("id",""))!=id and target.get("side","")=="player" and int(target.get("hp",0))>0 and not target.get("dead",false) and not target.get("neutral",false) and not target.get("event_object",false) and not target.get("hidden",false) and not target.get("escaped",false) and not target.get("retreated",false)

static func preview(g,id:String,center:Vector2i)->Dictionary:
	var actor=g.find_unit(id);var spec=profile(actor)
	if spec.is_empty():return {"valid":false,"reason":"该角色没有治疗MAP技能"}
	var result=spec.duplicate(true)
	result.merge({"valid":false,"actor":id,"center":[center.x,center.y],"facing":[1,0],"targets":[],"cells":[],"range_cells":[]})
	if g.mode!="battle" or g.phase!="player" or not str(g.battle_outcome).is_empty():result.reason="当前不能释放MAP";return result
	if int(actor.get("hp",0))<=0 or actor.get("acted",false):result.reason="本回合已经行动";return result
	if int(spec.tier)>=3:result.reason="本场MAP三次额度已用尽";return result
	if int(actor.hp)<=int(spec.cost):result.reason="支付后至少需要保留1HP";return result
	var origin=g.pos(actor)
	for y in range(-int(spec.reach),int(spec.reach)+1):
		for x in range(-int(spec.reach),int(spec.reach)+1):
			var p=origin+Vector2i(x,y)
			if absi(x)+absi(y)<=int(spec.reach) and g.in_bounds(p) and p!=origin:result.range_cells.append(p)
	if not g.in_bounds(center) or absi(center.x-origin.x)+absi(center.y-origin.y)>int(spec.reach):result.reason="选点超出治疗距离";return result
	result.cells=[center];result.hp_before=int(actor.hp);result.hp_after=int(actor.hp)-int(spec.cost)
	var target=g.unit_at(center)
	if not targetable(target,id):result.reason="请选择其他存活的战斗友军";return result
	var before=int(target.hp);var after=mini(int(target.max_hp),before+int(spec.heal))
	if after==before and StrongBody.remaining(target,int(g.turn))>=2:result.reason="目标生命已满且强身无需刷新";return result
	result.targets=[{"id":str(target.id),"unit":target.duplicate(true),"position":target.position.duplicate(),"hp_before":before,"hp_after":after,"heal":after-before,"strong_body_before":StrongBody.remaining(target,int(g.turn)),"strong_body_after":2}]
	result.valid=true;result.reason="";return result

static func apply(g,id:String,center:Vector2i)->Dictionary:
	var receipt=preview(g,id,center)
	if not receipt.valid:return receipt
	var actor=g.find_unit(id);var hit=receipt.targets[0];var target=g.find_unit(str(hit.id))
	receipt.actor_unit=actor.duplicate(true)
	actor.hp=int(receipt.hp_after);actor.map_uses=int(actor.get("map_uses",0))+1;actor.acted=true
	target.hp=int(hit.hp_after);StrongBody.apply(target,int(g.turn))
	if int(actor.map_uses)==3:actor.map_move_penalty_until_turn=int(g.turn)+1
	receipt.reward={}
	var gain=Rules.healing_experience_gain(actor,int(hit.heal))
	if gain>0 and not g.Training.active(g):
		receipt.reward=Experience.award(g,actor,gain);receipt.reward.victory_training=false;receipt.reward.map_skill=true
	actor.erase("weapon_index")
	g.mark_wait(id);g.selected_id="";g.Cover.refresh(g)
	g.log_lines.append(str(actor.name_zh)+"释放"+str(receipt.name)+"，为"+str(target.name_zh)+"恢复"+str(hit.heal)+"生命并施加强身")
	return receipt

extends RefCounted
const Progression=preload("res://core/unit_progression.gd")
const FIELDS=["max_hp","strength","skill","speed","luck","defence","resistance","move"]
const LABELS=["生命上限","力量","技巧","速度","幸运","物防","魔防","移动"]
static func choices(unit:Dictionary)->Array:
	var result=[];var cid=int(unit.class_id)
	if cid==14:
		for target in Progression.Items.data().villager_options:result.append({"class_id":int(target),"level_required":3})
	else:
		for p in Progression.Items.data().promotions:
			if int(p.from_class)==cid:result.append({"class_id":int(p.to_class),"level_required":int(p.level)})
	return result
static func preview(g,id:String,target:int)->Dictionary:
	if not g.party.has(id) or not g.roster.has(id):return {"valid":false,"reason":"该成员不在当前队伍中","rows":[]}
	var u:Dictionary=g.roster[id];var options=choices(u).filter(func(c):return int(c.class_id)==target)
	var reason="";var required=0
	if options.is_empty():
		reason="该职业已没有祭台进阶路线。"
		if id in ["hunapu","eileen"]:
			reason="已完成剧情进阶，没有后续祭台路线。" if g.HeroProfessions.advanced(u) else "需在第四章安全停用西塔，随剧情进阶。" if id=="hunapu" else "需在第四章完成祭所验证，随剧情进阶。"
	else:
		required=options[0].level_required
		if u.get("dead",false):reason="成员已阵亡，不能进阶。"
		elif not g.can_deploy(u):reason="成员处于濒死状态，请先救治再进阶。"
		elif int(u.level)<required:reason="需要等级%d，当前%d，还差%d级。"%[required,int(u.level),required-int(u.level)]
	var simulated=u.duplicate(true);simulated.level=maxi(int(u.level),required)
	var outcome=Progression.promote(simulated,target)
	var rows=[]
	if outcome.valid:
		for n in range(FIELDS.size()):
			var key=FIELDS[n];rows.append({"label":LABELS[n],"before":int(u.get(key,0)),"after":int(outcome.unit.get(key,0)),"delta":int(outcome.unit.get(key,0))-int(u.get(key,0))})
	return {"valid":reason.is_empty() and outcome.valid,"reason":reason if not reason.is_empty() else "需要等级%d · 条件已满足"%required,"required":required,"rows":rows,"before":u.duplicate(true),"after":outcome.get("unit",u),"id":id,"target":target}
static func commit(g,snapshot:Dictionary)->Dictionary:
	var now=preview(g,str(snapshot.get("id","")),int(snapshot.get("target",-1)))
	if not now.valid:return now
	if now.before!=snapshot.get("before",{}):return {"valid":false,"reason":"成员状态已变化，请重新查看预览。"}
	var old=g.roster[str(now.id)].duplicate(true);var result=g.promote_unit(str(now.id),int(now.target))
	if not result.get("valid",false):return {"valid":false,"reason":"进阶条件已变化，请重新选择。"}
	if not g.save_game():g.roster[str(now.id)]=old;return {"valid":false,"reason":"保存失败，尚未执行进阶。"}
	return {"valid":true,"reason":"进阶完成。"}

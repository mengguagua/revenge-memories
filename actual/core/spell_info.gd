extends RefCounted
## Read-only spell descriptions use combat's equipment, cost and reach.
const Items=preload("res://core/item_rules.gd")
const Rules=preload("res://core/combat_rules.gd")

static func actor(caster:Dictionary,id:int)->Dictionary:
	var preview=caster.duplicate(true);preview.weapon_index=id;return preview

static func describe(game,caster:Dictionary,id:int)->Dictionary:
	var spell=Items.spell(id);var cost=Items.cost_for(caster,id)
	var info={"id":id,"title":str(spell.get("name_zh","魔法"))+" · 消耗"+str(cost)+"HP","effect":"单体魔法伤害，按魔防计算","stats":"","range":"","availability":""}
	if Items.is_support(id):
		var strength=int(caster.get("strength",0));var action=str(spell.get("action",""))
		match action:
			"recover","physic":
				info.effect="恢复单名受伤友军"
				info.stats="最多恢复%d生命"%strength
				if action=="recover":
					info.effect="恢复单名友军，可能追加"
					info.stats="最多恢复%d生命，追加再耗血"%strength
			"fortify":
				info.effect="恢复全体存活友军"
				info.stats="每人最多恢复%d生命"%strength
			"warp":
				info.effect="传送邻接友军至可落脚空格"
				info.stats="先选友军，再选传送落点"
			"invoke":
				if game.get("campaign")!=null:
					var level=game.Phantoms.rank(game,caster);var uses=game.Phantoms.uses(game,caster)
					info.title="幻影%d级 · 消耗10HP"%level
					info.effect="召唤%d名不同职业优先的幻影"%(level*2)
					info.stats="全队每图1次 · "+("已满级" if level==3 else "熟练%d/6"%(uses%6))
				else:
					info.effect="在周围可落脚空格召唤援军";info.stats="数量由力量与随机结果决定"
			"conjure":
				info.effect="在周围可落脚空格召唤援军"
				info.stats="数量由力量与随机结果决定"
			"expel":
				info.effect="随机驱散指定种类的敌方魔物"
				info.stats="成功判定取决于施法者力量"
		info.range="施法范围1格，须相邻" if Items.support_range(id).y==1 else "施法范围全地图"
		if action in ["invoke","conjure"]:info.range="召唤范围为周围合法空格"
		info.availability="可选%d名友军"%game.support_targets(caster,id).size() if action in ["recover","physic","warp"] else "确认后施放"
		if action=="invoke" and game.get("campaign")!=null:
			var unavailable=game.Phantoms.reason(game,caster)
			info.availability=unavailable if not unavailable.is_empty() else "本次可生成%d名 · 当回合待机"%game.Phantoms.plan(game,caster,false).size()
	else:
		var preview=actor(caster,id);var profile=Items.weapon_profile(preview,id);var reach=Rules.attack_range(preview)
		if id==26:info.effect="对指定魔物特效，伤害按魔防"
		elif id==34:info.effect="命中后将目标生命降至1"
		elif id==42:info.effect="按实际造成的伤害吸取生命"
		info.stats="威力%d 基础命中%d 重量%d"%[int(profile.get("might",0)),int(profile.get("hit",0)),int(profile.get("weight",0))]
		info.range="攻击距离：%d～%d格"%[reach.x,reach.y]
		info.availability="范围内敌人：%d名"%game.targets(preview).size()
	if int(caster.get("hp",0))<=cost:info.availability="生命须高于%d才能施放"%cost
	return info

static func attack_cells(game,caster:Dictionary,id:int)->Array:
	if Items.is_support(id):return []
	var preview=actor(caster,id);var reach=Rules.attack_range(preview);var origin=game.pos(caster);var result=[]
	for dx in range(-reach.y,reach.y+1):
		for dy in range(-reach.y,reach.y+1):
			var cell=origin+Vector2i(dx,dy)
			if game.in_bounds(cell) and Rules.can_attack(preview,absi(dx)+absi(dy)):result.append(cell)
	return result

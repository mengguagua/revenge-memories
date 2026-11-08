extends RefCounted
## Battle facts are recorded at settlement, never inferred from cleared stages.
const Items=preload("res://core/item_rules.gd")

static func claimed(g,id:int) -> bool:
	return bool(g.flags.get("story_accessories_claimed",{}).get(str(id),false))

static func eligible(g,id:int) -> bool:
	var spec:Dictionary=Items.accessories().items.get(str(id),{})
	if spec.is_empty() or not g.stage_cleared(int(spec.stage)):return false
	var facts:Dictionary=g.flags.get("story_accessory_results",{}).get(str(id),{})
	return spec.facts.all(func(key):return facts.get(key,false)==true)

static func record_victory(g) -> void:
	if not g.battle_settled or g.battle_outcome!="victory" or not g.stage_cleared(g.stage_id):return
	var id=53 if g.stage_id==501 else 55 if g.stage_id==411 else 0
	if id==0:return
	var results:Dictionary=g.flags.get("story_accessory_results",{})
	if results.has(str(id)):return
	var q:Dictionary=g.flags.quest
	var boss:Dictionary=g.find_unit(str(g.battle_data.boss_id))
	var facts={"boss_defeated":not boss.is_empty() and (int(boss.get("hp",0))<=0 or boss.get("surrendered",false))}
	if id==53:
		for i in range(2):
			facts["ward_"+str(i+1)+"_open"]=bool(q.objects.get("ward_"+str(i+1),false))
			var unit:Dictionary=g.find_unit("royal_wounded"+str(i))
			facts["wounded_"+str(i)+"_alive"]=not unit.is_empty() and int(unit.get("hp",0))>0
			facts["wounded_"+str(i)+"_evacuated"]=q.evacuated.has("royal_wounded"+str(i))
	else:
		facts.register_protected=bool(q.objects.get("black_register",false))
		facts.register_intact=not bool(q.get("record_lost",false))
		facts.refuge_confirmed=bool(q.objects.get("refuge_court",false))
	results[str(id)]=facts
	g.flags.story_accessory_results=results

static func claim(g,id:int) -> bool:
	var spec:Dictionary=Items.accessories().items.get(str(id),{})
	if spec.is_empty() or claimed(g,id) or not eligible(g,id):return false
	if g.mode!="hub" or g.route!="alm" or g.hub_record!=spec.room or g.chapter!=int(spec.chapter):return false
	if g.flags.get("chapter5_merged",false) and id==53:return false
	# Automatic handover preserves the item above the manual convoy limit.
	g.convoy.alm.append(id)
	var taken:Dictionary=g.flags.get("story_accessories_claimed",{})
	taken[str(id)]=true;g.flags.story_accessories_claimed=taken
	return true

static func delivery_pages(id:int) -> Array:
	var spec:Dictionary=Items.accessories().items[str(id)]
	return [{"speaker":spec.speaker,"text":spec.handover},{"speaker":"旁白","text":str(spec.name_zh)+"已收入西队行囊，可在部队整备中分配。"}]

static func talk(h,id:int) -> void:
	var g=h.ui.game;var L=preload("res://core/late_dialogue.gd")
	var area="H51" if id==53 else "H49";var heading="护途盾" if id==53 else "续愿戒"
	var index=1 if claim(g,id) else 2 if claimed(g,id) else 0
	await L.say(h,L.lines(area,heading,index))

static func closing_reminder(g,id:int) -> String:
	if claimed(g,id):return ""
	var spec:Dictionary=Items.accessories().items[str(id)]
	if eligible(g,id):return str(spec.name_zh)+"尚未领取，可回"+("王都内廷伤兵照护处找军械官；合流后无法折返。" if id==53 else "黑钟村避难院找保管人；进入第五章后无法折返。")
	return str(spec.name_zh)+"尚未取得；领取需"+("M51两处病房开门、两组伤兵存活撤离并胜利。合流后无法补做。" if id==53 else "S41保住名册、确认避难院并胜利。进入第五章后无法补做。")+"不影响主线。"

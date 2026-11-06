extends RefCounted
static func entry(g)->Dictionary:
	var title="当前任务";var text="";var f=g.flags
	if f.get("campaign_complete",false):return {"title":"旅程已完成","text":"最后的战斗已经结束。可以回顾队伍与旅程记录。"}
	if g.chapter==1:
		if not f.get("prologue_done",false):text="走向海峡城广场的传光台，与艾琳或赫兰交谈。"
		elif not f.get("village_ready",false):text="回雪原村，到凯尔墓前与达恩交谈，再从村南出发。"
		elif not g.stage_cleared(101):text="沿村外林路前进，击退追兵，护送流民离开。"
		elif not g.stage_cleared(102):text="前往丘堡粮站，夺回被扣下的粮食。林路营地还可打听矿道和诊所的求助。"
		elif not f.get("grain_shared",false):text="回到丘堡粮站，调查粮车，把粮食送回雪原村。分粮后再向东去押送所。"
		elif not g.stage_cleared(103):text="向东前往南岗押送所，救出被扣押的劳工，寻找凯尔的军令。"
		elif not f.get("orders_collected",false):text="进入南岗押送所的战后据点，调查军令箱，取走押送名单和凯尔的军令。"
		elif not f.get("cooperation_done",false):text="从押送所东侧入口进入旧塔教堂，与赫兰确认合作。兰斯会带领队伍继续前进。"
		elif not g.stage_cleared(104):text="离开教堂，沿新开放的道路前往骑兵营，继续向北推进。祭台可查看同伴的职业进阶条件。"
		elif not g.stage_cleared(105):text="前往旧塔外营，截断敌人的退路。"
		elif not f.get("workers_treated",false):text="进入旧塔内院，先到伤者与医者旁安置获救的劳工。"
		elif not f.get("chapter1_complete",false):text="在旧塔内院与赫兰确认日返仪式。仪式会收束本章未完成的支线，可先完成矿道和送药求助。"
		else:text="第一章已经结束。返回当前地点，继续章节交接。"
	else:
		var route_ids={2:[201,202,203,204,205,206],3:[301,302,303] if g.route=="alm" else [304,305,306],4:[401,402,403,404] if g.route=="alm" else [405,406,407,408],5:[533,534] if f.get("chapter5_merged",false) else [501,502] if g.route=="alm" else [503,504]}
		var followups={201:["F21_confirmed","返回海岸据点，与获救者交谈，确认下一段航路。"],202:["F22_confirmed","返回战后据点，完成救援交接，再沿岸前进。"],203:["F23_confirmed","返回战后据点，与居民确认撤离安排。"],204:["islanders_settled","回到据点，安置获救的岛民。"],205:["east_departure_confirmed","回到港口，收集海图并确认出航安排。"],301:["D32_done","返回海峡城，与同伴商定两队的行动。"],302:["M32_confirmed","回到战后据点，与获救工匠交谈，确认军需线的消息。"],303:["M33_confirmed","回到战后据点，完成西队的交接，再前往营站。"],305:["F32_confirmed","回到战后据点，确认岛上的线索与下一步行动。"],306:["F33_confirmed","回到提炼院工房，完成交接后前往营站。"],401:["M41_confirmed","回到战后据点，确认水源与居民的情况。"],403:["west_tower_safe","返回西塔据点，完成塔内的调查和安排。"],405:["F41_confirmed","返回港口据点，完成撤离交接。"],406:["obs_steps_ready","进入观测据点，完成观测台的调查与准备。"],407:["F43_confirmed","回到古道据点，确认通行与交接。"],501:["M51_confirmed","回到西队据点，确认宫门前的安排。"],503:["east_network_ready","回到东队据点，确认联系网络已准备完毕。"]}
		for id in route_ids.get(g.chapter,[]):
			if not g.stage_cleared(id):
				var stage:Dictionary=g.stages[id];var name=str(stage.get("name_zh",stage.get("name",stage.code)))
				text="下一步：前往"+name+"。";break
			if followups.has(id) and not f.get(followups[id][0],false):text=followups[id][1];break
		if g.chapter==2 and not f.get("east_departure_ready",false):text="在东岸起点与同伴交谈，准备好后再沿海岸出发。"
		if text.is_empty():text="本队当前路段已完成。前往两队会合地点，完成据点中的交接；另一队尚未完成时，可在菜单切换队伍。"
	if g.chapter==2 and f.get("chapter2_complete",false):text="返回海峡城，继续与胡纳普会合后的故事。"
	if g.chapter==4 and g.route=="alm" and g.stage_cleared(403) and not f.get("west_tower_safe",false) and not f.get("obs_steps_ready",false):text="西塔控制室已守住，还缺东岸观测步骤。在菜单切换东队，完成盐原观测台，再回西塔确认安全停用。"
	if g.chapter==5 and not f.get("chapter5_merged",false):
		if g.route=="alm" and g.stage_cleared(502) and not f.get("west_palace_gate",false):text="回到西队宫门据点，与接应者确认通行，再前往两队会合地点。"
		if g.route=="celica" and g.stage_cleared(504) and not f.get("east_palace_gate",false):text="回到东队宫门据点，完成通路交接，再前往两队会合地点。"
	return {"title":title,"text":text,"chapter":g.chapter,"route":g.route}

extends RefCounted
# Destinations and motives are authored independently of battle titles.
static func route_task(stage_id:int)->String:
	var tasks=JSON.parse_string(FileAccess.get_file_as_string("res://data/current_tasks_20261103.json"))
	return str(tasks.get(str(stage_id),""))

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
		elif not g.stage_cleared(104):text="离开教堂，沿新开放的道路前往旧塔外营，拿下两处哨卡。祭台可查看同伴的职业进阶条件。"
		elif not g.stage_cleared(105):text="前往海峡城内的旧塔堡，救出劳工，截断科兰的退路。"
		elif not f.get("workers_treated",false):text="进入旧塔内院，先与女医者交谈，安置获救的劳工。"
		elif not f.get("chapter1_complete",false):text="在旧塔内院与赫兰确认日返仪式。仪式会收束本章未完成的支线，可先完成矿道和送药求助。"
		else:text="第一章已经结束。返回当前地点，继续章节交接。"
	else:
		var route_ids={2:[201,202,203,204,205,206],3:[301,302,303] if g.route=="alm" else [304,305,306],4:[401,402,403,404] if g.route=="alm" else [405,406,407,408],5:[533,534] if f.get("chapter5_merged",false) else [501,502] if g.route=="alm" else [503,504]}
		var followups={201:["F21_confirmed","回船团停泊栈桥，跟马丁确认押送舰的航路。"],202:["F22_confirmed","去救护栈桥安置伤者，向母亲船上的舵手问清当年的事。"],203:["F23_confirmed","回到礁岛渔村，向长者打听可以带伤者休息的岸边。"],204:["islanders_settled","回到海灯岛灯屋，与留守骑士确认岛民已经安全上船。"],205:["east_departure_confirmed","回军港取回母亲的航图，再跟马丁确认西渡。"],301:["D32_done","返回海峡城，与同伴商定两队的行动。"],302:["M32_confirmed","回到军需大道的营地，与获救工匠交谈，查清原料被送往哪里。"],303:["M33_confirmed","回沿海石堡与工匠核对投送记录，再去营站与东队互证。"],305:["F32_confirmed","回盐路据点，与向导核对研究院的线索。"],306:["F33_confirmed","回研究院工房，带走调节记录，再去营站与西队互证。"],401:["M41_confirmed","回雪峡村，与居民确认水源和撤离的情况。"],403:["west_tower_safe","返回西塔据点，完成塔内的调查和安排。"],405:["F41_confirmed","回沙城港口，与居民确认水井和撤离船的情况。"],406:["obs_steps_ready","进入观测据点，完成观测台的调查与准备。"],407:["F43_confirmed","回沼泽古道，确认获救的难民已经安置，再沿干地前进。"],501:["M51_confirmed","回到西队据点，确认宫门前的安排。"],503:["east_network_ready","回到东队据点，确认联系网络已准备完毕。"]}
		for id in route_ids.get(g.chapter,[]):
			if not g.stage_cleared(id):
				text=route_task(id);break
			if followups.has(id) and not f.get(followups[id][0],false):text=followups[id][1];break
		if g.chapter==2 and not f.get("east_departure_ready",false):
			text="母亲薇娅出海求医后失踪。卡洛刚回到风灯岛，说有那条船的消息。去船坞见他。"
			if f.get("east_martin_pending",false):text="到南边跳板旁和马丁谈谈，准备出海。"
		if text.is_empty():text="本队当前路段已完成。前往两队会合地点，与同伴核对带回的消息；另一队尚未完成时，可在菜单切换队伍。"
	if g.chapter==2 and f.get("chapter2_complete",false):text="返回海峡城，继续与胡纳普会合后的故事。"
	if g.chapter==4 and g.route=="alm" and g.stage_cleared(403) and not f.get("west_tower_safe",false) and not f.get("obs_steps_ready",false):text="西塔控制室已守住，还缺东岸观测步骤。在菜单切换东队，完成盐原观测台，再回西塔确认安全停用。"
	if g.chapter==5 and not f.get("chapter5_merged",false):
		if g.route=="alm" and g.stage_cleared(502) and not f.get("west_palace_gate",false):text="回到西队宫门据点，与接应者确认通行，再前往两队会合地点。"
		if g.route=="celica" and g.stage_cleared(504) and not f.get("east_palace_gate",false):text="回东队宫门据点，与接应者确认门阵已经接手，再前往两队会合地点。"
	return {"title":title,"text":text,"chapter":g.chapter,"route":g.route}

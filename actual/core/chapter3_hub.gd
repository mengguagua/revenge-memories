extends RefCounted
const L=preload("res://core/late_dialogue.gd")
## Third-chapter conversations share the existing room/input and plot controllers.
static func pages(h,lines: Array,callback: String="") -> void:
	var list=[]
	for line in lines:
		var parts=str(line).split("：",true,1);list.append({"speaker":parts[0],"text":parts[1]})
	await h.ui.play_pages(list,"hub",callback)

static func action(h,key: String) -> void:
	var ui=h.ui;var g=ui.game
	if key.begins_with("promote_"):
		await h._east_action(key);return
	if key.begins_with("third_transfer_"):
		var result=g.ChapterThree.transfer_supply(g,int(key.substr(15)))
		ui._notice("已交给本队行囊" if result.valid else str(result.reason));return
	match key:
		"third_prologue":await ui.prologue_scene.reprise()
		"third_altar":
			await L.say(h,L.lines("H30","仍在",0))

		"third_reunion":
			if not g.stage_cleared(301) or not g.stage_cleared(304):await L.say(h,L.lines("H31","D32",4));return
			if g.flags.get("D32_done",false):await L.say(h,L.lines("H31","D32",3));return
			var rows=L.lines("H31","D32")
			if g.speaker_alive("米蕾"):rows+=L.lines("H31","D32",1)
			elif g.parties.celica.has("mireille"):rows+=L.lines("H31","D32",2)
			await L.say(h,rows,"third_reunion")

		"third_people":
			await L.say(h,L.lines("H31","留守",0))

		"third_supply":
			await L.say(h,L.lines("H32","清点",1 if g.flags.get("M32_confirmed",false) else 0),"late:M32_confirmed")

		"third_s31":
			await L.say(h,L.lines("H32","山村",0),"late:S31_invited")

		"third_records_w":
			await L.say(h,L.lines("H33","确认",1 if g.flags.get("M33_confirmed",false) else 0),"late:M33_confirmed")

		"third_german":
			if g.party.has("german"):await L.say(h,L.lines("H33","格曼",1));return
			if not g.flags.chapter3_recruits.get("german",false):await L.say(h,L.lines("H33","格曼",2));return
			await L.say(h,L.lines("H33","格曼"),"late_invite:german")

		"third_route_e":
			await L.say(h,L.lines("H34","向导",1 if g.flags.get("salt_guide_survived",false) else 0)+L.lines("H34","井台"),"late:F32_confirmed")

		"third_s32":
			await L.say(h,L.lines("H34","盐原",0),"late:S32_invited")

		"third_records_e":
			await L.say(h,L.join_groups("H35","确认",[0,1]),"late:F33_confirmed")

		"third_families":
			var count=g.flags.get("S31_families",{}).values().filter(func(v):return v).size()
			var rows=L.lines("H36","获救",0 if count==2 else 2)
			if not g.speaker_alive("蕾娜"):rows=rows.slice(0,1)+L.lines("H36","获救",1).slice(1)
			await L.say(h,rows)

		"third_noya":
			if g.party.has("noya"):await L.say(h,L.lines("H37","诺娅：",1));return
			if not g.flags.chapter3_recruits.get("noya",false):await L.say(h,L.lines("H37","诺娅：",2));return
			await L.say(h,L.lines("H37","诺娅："),"late_invite:noya")

		"third_recruit_german","third_recruit_noya":
			var id=key.substr(14)
			if g.flags.chapter3_recruits.get(id,false) and not g.roster.get(id,{}).get("dead",false):g.recruit(id);h.enter_room(h.room,true)
		"third_brother":
			await L.say(h,L.lines("H37","诺娅弟弟",1 if g.flags.get("noya_brother_survived",false) else 0)+L.lines("H37","诺娅弟弟",2))

		"third_council":
			if int(g.route_positions.alm)!=9 or int(g.route_positions.celica)!=9:await L.say(h,L.lines("H10","D33",2));return
			if g.flags.get("D33_done",false):await L.say(h,L.lines("H10","D33",1))
			else:await L.say(h,L.lines("H10","D33"),"third_council")

		"third_messenger":
			if not g.flags.get("D33_done",false):await pages(h,["信使：先让两队到齐，确认下一步的计划。"]);return
			var missing=[]
			if not g.stage_cleared(311):missing.append("山村地牢")
			if not g.stage_cleared(312):missing.append("盐原营地")
			if not missing.is_empty():await pages(h,["信使：尚未完成的支路："+"、".join(missing)+"。确认分兵后本章救援收束，准备好了再来找我。"])
			ui._open_menu("third_end",["继续整备","确认第三章收束"],["close","hub:third_finish"],Vector2(36,88))
		"third_finish":
			if not g.flags.get("D33_done",false):return
			g.flags.chapter3_complete=true;g.flags.chapter4_pending=true;g.mode="chapter_end";ui.view="chapter_end"
		"third_training":
			if not g.flags.get("D33_done",false):ui._notice("先完成两队会谈");return
			ui._open_menu("camp_training",["职业进阶","接收另一队物资","离开"],["hub:third_promotions","hub:third_exchange","close"],Vector2(32,80))
		"third_promotions":await h._east_action("east_promotions")
		"third_exchange":
			if int(g.route_positions.alm)!=9 or int(g.route_positions.celica)!=9:ui._notice("两队都在营站才能当面交接");return
			var other="alm" if g.route=="celica" else "celica";var labels=[];var actions=[]
			for i in range(g.convoy[other].size()):
				labels.append(str(g.Items.item(int(g.convoy[other][i])).name_zh));actions.append("hub:third_transfer_"+str(i))
			if labels.is_empty():ui._notice("另一队行囊为空，可先切队存入装备");return
			ui._open_menu("camp_exchange",labels,actions,Vector2(40,64))
		"third_relations":await relations(h)

static func finish(h,key: String) -> void:
	var g=h.ui.game
	match key:
		"third_prologue":g.flags.D31_done=true;h.ui._continue_world()
		"third_reunion":g.flags.D32_done=true
		"third_council":g.flags.D33_done=true;g.ensure_treatment_sources();h.enter_room("H10",true)

static func relations(h) -> void:
	var g=h.ui.game;var rows=[];var seen=[]
	if not g.flags.get("D33_done",false):await L.say(h,L.lines("H10","R01",0));return
	var source=L.lines("H10","R01",2)
	for item in [["R01","达恩","米蕾",0,4],["R04","芙拉","赫维",4,6],["R08","格曼","奥托",6,8],["R07","莉莎","诺娅",8,10]]:
		if L.member(g,item[1]) and L.member(g,item[2]) and not g.flags.get("seen_"+item[0],false):
			rows+=source.slice(item[3],item[4]);seen.append("seen_"+item[0])
	if rows.is_empty():rows=L.lines("H10","R01",1)
	await L.say(h,rows,"late:"+",".join(seen) if not seen.is_empty() else "")

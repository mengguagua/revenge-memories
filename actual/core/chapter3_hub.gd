extends RefCounted
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
		"third_prologue":await ui.play_pages(g.campaign.scenes.D31,"hub","third_prologue")
		"third_altar":await pages(h,["旁白：传光台仍在向西岸投下明亮的日光。神幕另一端的船还没有获准靠岸。"])
		"third_reunion":
			if not g.stage_cleared(301) or not g.stage_cleared(304):
				await pages(h,["留守医者：这一队已经脱围。另一队还在海峡城，先去接应他们。", "提示：按S打开菜单，可以切换队伍。两队各自保留位置、成长和行囊。"]);return
			if g.flags.get("D32_done",false):await pages(h,["信使：西队走军需大道，东队沿盐路调查。两边的来信都由我们传递。"]);return
			var story=g.campaign.scenes.D32.duplicate(true)
			if g.speaker_alive("米蕾"):story.append({"speaker":"米蕾","text":"艾琳，伤者已经交给留守医者。我在船边等你。"})
			elif g.parties.celica.has("mireille"):story.append({"speaker":"艾琳","text":"动身前我要去照护处看看米蕾。她还在队伍里，不能让她再承担医疗。"})
			await ui.play_pages(story,"hub","third_reunion")
		"third_people":await pages(h,["留守医者：濒死同伴和撤下来的居民由我们照护。同伴仍随原队接受照护，能出阵的人会继续护送他们。"])
		"third_supply":
			g.flags.M32_confirmed=true
			await pages(h,["工匠：人、车辆和普通工具都已清点，物资会送往沿海营站。石堡还扣着另一批工匠。", "胡纳普：先让他们休息。我们去石堡查投送记录。"])
		"third_s31":
			g.flags.S31_invited=true
			await pages(h,["工匠：山村地牢又关进了两组家属。他们说蕾娜过去曾护送他们回家。", "工匠：支路从军需大道分开，可以先救人，也可以稍后回来。营站分兵前还来得及。"])
		"third_records_w":
			g.flags.M33_confirmed=true
			await pages(h,["工匠：这是石堡的投送记录，原料和人一直送往提炼院。", "胡纳普：等另一队取到调节记录，就能知道这些设施究竟怎样相连。", "信使：两边确认后会开放营站短渡。两队都到营站，再共同会谈。"])
		"third_german":
			if g.party.has("german"):
				await pages(h,["格曼：押送记录已交出去。我会留下作证，也会把工房欠下的物资逐项补齐。"]);return
			if not g.flags.chapter3_recruits.get("german",false):
				await pages(h,["工匠：石堡的投降者和伤亡都已登记。能回家的先回去，押送责任仍会追查。"]);return
			await pages(h,["格曼：我愿意跟你们走。但那些押送名单上也有我的名字。", "胡纳普：名单交给记录官。你可以参与护送，受害者也可以继续向你问责。"])
			ui._open_menu("recruit",["邀请格曼同行","留在安置处"],["hub:third_recruit_german","close"],Vector2(36,88))
		"third_route_e":
			g.flags.F32_confirmed=true
			await pages(h,["船民：向导已把提炼院后门的位置画好了。" if g.flags.get("salt_guide_survived",false) else "船民：向导没能回来。他留下的路线册标着提炼院后门，我们会把消息带回家。", "艾琳：记下他的名字。沿干道过去，先把被迫维持设施的人带出来。"])
		"third_s32":
			g.flags.S32_invited=true
			await pages(h,["船民：盐原营地囚着术士和居民。有个叫诺娅的人，请我们救她弟弟。", "艾琳：把支路标出来。营站分兵前，我们还可以回来。"])
		"third_records_e":
			g.flags.F33_confirmed=true
			await pages(h,["术士：调节记录已经复制。强拆阵台会伤到靠它维持土地的人，观测台还有完整的数据。", "艾琳：这份记录交给营站。我要先验证办法，再要求他停塔。", "信使：等石堡也确认记录，两队就能分别渡往营站。"])
		"third_families":
			var count=g.flags.get("S31_families",{}).values().filter(func(v):return v).size()
			var lines=["家属：这次回来的是"+str(count)+"组家庭。救援和伤亡都记在名单上，狱卒的责任不能就这样算了。"]
			if g.speaker_alive("蕾娜"):lines.append("蕾娜：我会回来听你们说，也会把那份旧誓和今天的事一起交代。")
			else:lines.append("家属：蕾娜以前护送我们走过这条路。请告诉她，我们还记得。")
			await pages(h,lines)
		"third_noya":
			if g.party.has("noya"):
				await pages(h,["诺娅：路线册和我泄露过的位置都已登记。我会帮助旧船团撤离，也会接受他们的责问。"]);return
			if not g.flags.chapter3_recruits.get("noya",false):
				await pages(h,["留守医者：诺娅没有活着离开营房。她弟弟的消息记在旁边的伤员名册上。"]);return
			await pages(h,["诺娅：他们用我弟弟逼我。我把船团藏在哪里告诉了他们。这件事是我做的。", "艾琳：救你出来，不代表这件事已经过去。把路线册交出来，帮助撤离的人，也接受他们的审查。", "诺娅：我愿意。我想把后面的船带出来。"])
			ui._open_menu("recruit",["接纳诺娅同行","留在安置处"],["hub:third_recruit_noya","close"],Vector2(36,88))
		"third_recruit_german","third_recruit_noya":
			var id=key.substr(14)
			if g.flags.chapter3_recruits.get(id,false) and not g.roster.get(id,{}).get("dead",false):g.recruit(id);h.enter_room(h.room,true)
		"third_brother":await pages(h,["留守医者：诺娅的弟弟已经交给照护处。" if g.flags.get("noya_brother_survived",false) else "留守医者：诺娅的弟弟遇难了。我们已经留下他的姓名和遗物。"])
		"third_council":
			if int(g.route_positions.alm)!=9 or int(g.route_positions.celica)!=9:
				await pages(h,["信使：另一队尚未到营站。可以按S切队，沿短渡把他们带来。会谈需要两队都在场。"]);return
			if g.flags.get("D33_done",false):
				await pages(h,["信使：观测台、日塔和村落的计划已登记。还可以整理行囊、训练、救治同伴，或返回本章未完成的支路。"])
			else:await ui.play_pages(g.campaign.scenes.D33,"hub","third_council")
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
	var g=h.ui.game;var lines=[]
	if not g.flags.get("D33_done",false):await pages(h,["旁白：营火旁空着两个位置，等两队回来。"]);return
	if g.speaker_alive("达恩") and g.speaker_alive("米蕾") and not g.flags.get("seen_R01",false):
		lines.append_array(["达恩：商队还剩这些干净的布。先记在我账上。", "米蕾：伤者会用得上。你带的货单，我也可以帮你看。", "达恩：那下次写信，你教我读剩下的几行。"]);g.flags.seen_R01=true
	if g.speaker_alive("芙拉") and g.speaker_alive("赫维") and g.stage_cleared(112) and not g.flags.get("seen_R04",false):
		lines.append_array(["芙拉：你为什么一定要离开诊所？村里还需要人。", "赫维：我想学会这些设备。回来以后，村里就不必一直等教团发药。"]);g.flags.seen_R04=true
	if g.speaker_alive("奥托") and g.speaker_alive("格曼") and not g.flags.get("seen_R08",false):
		lines.append_array(["格曼：投降以后，我还能离开吗？", "奥托：先把你参与过的押送记录交出来。我执行过的封路，也会登记。"]);g.flags.seen_R08=true
	if g.speaker_alive("莉莎") and g.speaker_alive("诺娅") and not g.flags.get("seen_R07",false):
		lines.append_array(["莉莎：你交出了路线，别人就替你付了代价。", "诺娅：这是我完整的路线册。我先去帮助旧船团撤离，你们可以继续查。"]);g.flags.seen_R07=true
	if lines.is_empty():lines.append("旁白：留守人员正准备照护与通信的物资。缺席的同伴仍记在各队名册上。")
	await pages(h,lines)

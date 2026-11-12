extends RefCounted
const L=preload("res://core/late_dialogue.gd")
## Small explorable story rooms. Facing interaction and visual objects share cells.
const FifthHub = preload("res://core/chapter5_hub.gd")
const FourthHub = preload("res://core/chapter4_hub.gd")
const ThirdHub = preload("res://core/chapter3_hub.gd")
var ui
var room := "P00"
var objects: Array=[]
var scenery: Array=[]
var title := ""
var hint := ""
var facing := Vector2i.UP
const ORIGIN := Vector2(16,8)
const STEP := 16.0 / 60.0988
var render_position := Vector2.ZERO
var motion_origin := Vector2.ZERO
var motion_target := Vector2.ZERO
var motion_left := 0.0
var clock := 0.0
var chapter2_rooms: Dictionary={}
var east_data: Dictionary={}
var east_materials: Dictionary={}
var east_shore_cache: Dictionary={}
var chapter1_climate: Dictionary={}
var climate_layout_cache: Dictionary={}
var chapter2_environment: Dictionary={}
var chapter3_environment: Dictionary={}
var chapter4_environment: Dictionary={}
var chapter5_environment: Dictionary={}

func _init(owner) -> void:
	ui=owner
	chapter1_climate=ui.GameState.read_json("res://data/chapter1_hub_climate.json")
	chapter2_environment=ui.GameState.read_json("res://data/chapter2_hub_environment.json")
	chapter3_environment=ui.GameState.read_json("res://data/chapter3_hub_environment.json")
	chapter4_environment=ui.GameState.read_json("res://data/chapter4_hub_environment.json")
	chapter5_environment=ui.GameState.read_json("res://data/chapter5_hub_environment.json")
	var data=ui.GameState.read_json("res://data/chapter2_hubs.json")
	chapter2_rooms=data.get("rooms",{});east_materials=data.get("materials",{})
	var third=ui.GameState.read_json("res://data/chapter3_hubs.json")
	chapter2_rooms.merge(third.rooms);east_materials.merge(third.materials)
	var fourth=ui.GameState.read_json("res://data/chapter4_hubs.json")
	chapter2_rooms.merge(fourth.rooms);east_materials.merge(fourth.materials)
	var fifth=ui.GameState.read_json("res://data/chapter5_hubs.json")
	chapter2_rooms.merge(fifth.rooms);east_materials.merge(fifth.materials)
func process(delta: float) -> void:
	clock+=delta
	if motion_left>0.0:
		motion_left=maxf(0.0,motion_left-delta)
		render_position=motion_origin.lerp(motion_target,1.0-motion_left/STEP)
	else:render_position=Vector2(ui.game.hub_position)*16
	# Source hub controller chains complete tiles, independent of OS key repeat.
	if motion_left<=0.0 and ui.view=="hub" and not ui.busy and ui.menu_items.is_empty() and ui.held_direction!=Vector2i.ZERO:
		direction(ui.held_direction)
func dispose() -> void:ui=null
func mouse_accept(point: Vector2) -> void:
	if motion_left>0.0:return
	if not ui.menu_items.is_empty():
		var index=ui._menu_pointer_index(point)
		if index>=0:ui.menu_selected=index;accept()
		return
	var cell=Vector2i(floori((point.x-ORIGIN.x)/16),floori((point.y-ORIGIN.y)/16))
	for o in objects:
		if not object_occupies(o,cell):continue
		var delta=cell-ui.game.hub_position
		if absi(delta.x)+absi(delta.y)==1:facing=delta;accept()
		else:ui._notice("先走到对象旁边，再面对确认")
 
func resume() -> void:enter_room(ui.game.hub_record,true,false)
func enter(_id: int,_at: Vector2i) -> void:enter_world()

func enter_world() -> void:
	if ui.game.chapter==5:
		enter_room(ui.game.ChapterFive.room_for(ui.game));return
	if ui.game.chapter==4:
		enter_room(ui.game.ChapterFour.room_for(ui.game));return
	if ui.game.chapter==3:
		enter_room(ui.game.ChapterThree.room_for(ui.game));return
	if ui.game.flags.get("chapter2_complete",false) and ui.game.route=="celica" and ui.game.world_node==6:
		enter_room("H27");return
	if ui.game.ChapterTwo.at_s21(ui.game):return
	var rooms={1:"H01",2:"H07",3:"H02",4:"H03",5:"H05",6:"H06",31:"H08",32:"H09",17:"H21",18:"H22",19:"H23",20:"H24",21:"H25",22:"H26",23:"H27",34:"H24"}
	enter_room(rooms.get(ui.game.world_node,"H07"))

func enter_room(id: String,resuming: bool=false,checkpoint: bool=true) -> void:
	ui.game.Equipment.reconcile(ui.game)
	ui.game.ensure_treatment_sources()
	room=id;ui.game.hub_record=id;ui.game.flags.hub_record=id;ui.view="hub";ui.game.mode="hub"
	ui.busy=false;ui.held_direction=Vector2i.ZERO;ui._clear_menu();facing=Vector2i.UP
	if not resuming:ui.game.hub_position=Vector2i(6,7)
	render_position=Vector2(ui.game.hub_position)*16;motion_left=0.0
	motion_origin=render_position;motion_target=render_position
	objects=[];east_data={}
	match room:
		"P00":
			title="序章 · 海峡城庆典";hint="走向传光台，面对人物确认"
			obj("guard",[4,5],"教团守卫","actor",0,"胡纳普，赫兰大人在传光台等你。")
			obj("prologue",[9,2],"赫兰","actor",4);obj("prologue",[4,3],"艾琳","actor",2)
			obj("altar",[8,1],"传光台","sun_altar")
			obj("guard",[3,3],"教团守卫","actor",0);obj("guard",[5,3],"教团守卫","actor",0)
		"H01":
			title="半年前 · 雪原村";hint="墓前交谈后，向南离村"
			obj("grave",[6,3],"凯尔的墓","grave");obj("otto",[3,4],"奥托","actor",5)
			obj("daan",[10,5],"达恩","actor",21)
		"H02":
			title="丘堡粮站 · 战后";hint="确认分粮，再与芙拉交谈"
			obj("grain",[6,3],"粮车","grain_wagon",0,"",Vector2i(2,1));obj("fula",[3,5],"芙拉","actor",14)
			obj("crown",[10,3],"救济牌","aid_plaque")
		"H03":
			title="南岗押送所 · 战后";hint="查看军令，再到东侧教堂"
			obj("orders",[6,3],"军令箱","orders_case");obj("lena",[3,5],"蕾娜","actor",9)
			obj("church",[11,2],"教堂入口","stairs_up")
		"H04":
			title="押送所旁 · 旧塔教堂";hint="与赫兰确认合作，兰斯同行"
			obj("cooperate",[6,3],"赫兰","actor",4);obj("lance",[10,5],"兰斯","actor",10)
			obj("shrine",[3,5],"教堂祭台","sun_altar")
			obj("treatment",[4,6],"救治泉 · 西队剩余"+str(ui.game.treatment_remaining())+"份","well")
		"H05":
			title="旧塔外营 · 战后";hint="两处道路已受控制，继续北行"
			obj("camp",[6,3],"投降兵","actor",5,"修城墙的人还在堡里。")
		"H06":
			title="海峡城 · 旧塔内院";hint="与女医者安置伤者，再到日塔确认仪式"
			obj("treat",[6,5],"女医者","actor")
			obj("ceremony",[7,2],"日返仪式","sun_altar")
		"H07":
			title="林路营地";hint="查看矿道和诊所的求助，再选道路"
			obj("invite",[6,3],"村民","actor",7)
			obj("camp",[10,5],"村中老妇","actor",0,"凯尔把军粮分给了我们。科兰说他通敌，就把他杀了……那时谁也不敢站出来。")
		"H08":
			title="旧矿道 · 战后"
			if not ui.game.party.has("beck") and ui.game.speaker_alive("贝克"):
				hint="与贝克交谈，邀请他同行";obj("beck",[6,3],"贝克","actor",20)
			else:
				hint="与获救矿工交谈，听听矿道里的遭遇";obj("mine_survivor",[6,3],"老矿工","actor",0)
			obj("mine_apprentice",[9,3],"年轻矿工","actor",0);obj("tools",[10,5],"矿工工具","crates")
		"H09":
			title="林村诊所 · 医疗交接"
			hint="药车尚未送达，请先护送药车" if not ui.game.stage_cleared(112) else "请与管理员核对药单，完成医疗交接" if not ui.game.flags.get("clinic_staffed",false) else "管理员已接手，可与赫维交谈邀请同行" if not ui.game.party.has("hervi") else "赫维已同行，管理员负责诊所照护"
			obj("staff",[4,3],"管理员","actor",7);obj("hervi",[9,5],"赫维","actor",27)
			if ui.game.stage_cleared(112):
				obj("transport",[5,4],"运药员","actor",3)
				obj("delivery",[7,3],"送达的药车","medicine_wagon")
	for o in objects.duplicate():
		if o.action=="hervi" and ui.game.flags.get("clinic_hervi_unavailable",false):objects.erase(o);continue
		if o.action in ui.game.characters:
			var u=ui.game.roster.get(o.action,{})
			if bool(u.get("dead",false)):objects.erase(o)
			elif ui.game.is_dying(u):o.name=str(u.name_zh)+" · 濒死"
	scenery=[]
	var plans={"P00":[["barracks",1,0],["barracks",10,0]],"H01":[["snow_cottage",1,0],["snow_cottage",10,0],["snow_pine_patch",0,6]],
	 "H02":[["grain_store",9,0],["grain_sacks",1,2],["crates",1,5]],"H03":[["barracks",1,0],["barracks",10,0]],
	 "H04":[["stone_gate",7,0],["north_wall",1,0]],"H05":[["barracks",9,0],["north_fence",1,0]],
	 "H06":[["tower_entry",10,0],["north_wall",1,0]],"H07":[["pine_patch",0,5],["grain_sacks",11,1]],
	 "H08":[["cave_entry",1,0],["rock_face",9,0]],"H09":[["clinic_door",1,1],["snow_cottage",10,0],["flowers",1,6]]}
	for entry in plans.get(room,[]):
		for module in ui.battle_pack.modules:
			if module.name==entry[0]:
				scenery.append({"name":entry[0],"rect":Rect2i(entry[1],entry[2],module.footprint[0],module.footprint[1])});break
	if room=="H06":scenery.append({"name":"medicine_wagon","rect":Rect2i(4,5,2,1)})
	if chapter2_rooms.has(room):_configure_east_room()
	if room=="H21":
		var martin=_martin_cell()
		if ui.game.hub_position==martin:
			ui.game.hub_position=martin+Vector2i.RIGHT
			render_position=Vector2(ui.game.hub_position)*16
			motion_origin=render_position;motion_target=render_position
		var to_martin=martin-ui.game.hub_position
		if ui.game.flags.get("east_martin_pending",false) and absi(to_martin.x)+absi(to_martin.y)==1:facing=to_martin
	if room=="H04":
		var positions={"cooperate":[8,3],"lance":[10,6],"shrine":[6,2],"treatment":[1,6]}
		for o in objects:
			if positions.has(o.action):o.position=positions[o.action]
		scenery=[]
		for rect in [Rect2i(1,0,12,3),Rect2i(3,4,3,1),Rect2i(3,5,3,1),Rect2i(8,4,3,1),Rect2i(8,5,3,1),Rect2i(1,7,5,1),Rect2i(8,7,5,1)]:
			scenery.append({"name":"chapel_structure","rect":rect})

	if room=="H04" and (scenery.any(func(d):return d.rect.has_point(ui.game.hub_position)) or objects.any(func(o):return object_occupies(o,ui.game.hub_position))):
		ui.game.hub_position=Vector2i(6,7);render_position=Vector2(ui.game.hub_position)*16;motion_origin=render_position;motion_target=render_position

	# A pre-fix journal may place the player inside the wagon's missing half.
	# Move to an adjacent free tile once; keep the handover and party intact.
	if room in ["H02","H06"] and (objects.any(func(o):return object_occupies(o,ui.game.hub_position)) or scenery.any(func(d):return d.rect.has_point(ui.game.hub_position))):
		for offset in [Vector2i.DOWN,Vector2i.RIGHT,Vector2i.UP,Vector2i.LEFT]:
			var next=ui.game.hub_position+offset
			if next.x<1 or next.x>12 or next.y<1 or next.y>7:continue
			if objects.any(func(o):return object_occupies(o,next)) or scenery.any(func(d):return d.rect.has_point(next)):continue
			ui.game.hub_position=next;render_position=Vector2(next)*16;motion_origin=render_position;motion_target=render_position;break
	ui.audio.play_music("village")
	if checkpoint:ui.game.save_game()
	ui.queue_redraw()

func obj(action: String,at: Array,name: String,sprite: String,source: int=0,text: String="",footprint: Vector2i=Vector2i.ONE) -> void:
	objects.append({"action":action,"position":at,"name":name,"sprite":sprite,"source":source,"text":text,"footprint":[footprint.x,footprint.y]})

func object_occupies(object: Dictionary,cell: Vector2i) -> bool:
	var size=object.get("footprint",[1,1])
	return Rect2i(Vector2i(object.position[0],object.position[1]),Vector2i(size[0],size[1])).has_point(cell)

func direction(d: Vector2i) -> void:
	if ui.busy or motion_left>0.0:return
	if not ui.menu_items.is_empty():
		ui._move_menu_selection(d.x if d.x!=0 else d.y);return
	facing=d;var at=ui.game.hub_position+d
	if at==Vector2i(6,8):
		if not east_data.is_empty() and not _east_exit_allowed():return
		if room=="P00":ui._notice("先到传光台，看看庆典发生了什么");return
		if room=="H01" and not ui.game.flags.get("village_ready",false):ui._notice("先到凯尔墓前与达恩谈谈");return
		if room=="H02" and not ui.game.flags.get("grain_shared",false):
			await ui.play_pages([{"speaker":"胡纳普","text":"粮食还没分给村民。先去看看粮车。"}],"hub");return
		if room=="H03" and not ui.game.flags.get("orders_collected",false):ui._notice("先查看军令箱");return
		if room=="H04":
			enter_room("H03",false,false)
			ui.game.hub_position=Vector2i(11,3);facing=Vector2i.DOWN
			render_position=Vector2(ui.game.hub_position)*16;motion_origin=render_position;motion_target=render_position
			ui.game.save_game();ui.queue_redraw();return
		ui._open_menu("hub_exit",["离开据点","留下"],["new:world","close"],Vector2(48,88));return
	if at.x<1 or at.x>12 or at.y<1 or at.y>7:return
	if not east_data.is_empty() and not east_walkable(at):return
	if objects.any(func(o):return object_occupies(o,at)):return
	if scenery.any(func(d):return bool(d.get("blocking",true)) and d.rect.has_point(at)):return
	_step_to(at)
	ui.game.save_game()

func _step_to(at: Vector2i) -> void:
	motion_origin=Vector2(ui.game.hub_position)*16;motion_target=Vector2(at)*16
	motion_left=0.0 if ui.instant_mode else STEP
	render_position=motion_target if ui.instant_mode else motion_origin
	ui.game.hub_position=at;ui.queue_redraw()

func accept() -> void:
	if ui.busy or motion_left>0.0:return
	if not ui.menu_items.is_empty():
		var a=str(ui.menu_actions[ui.menu_selected]);var context=ui.menu_context;ui._clear_menu();ui._menu_action(a,context);return
	var target=ui.game.hub_position+facing
	for o in objects:
		if object_occupies(o,target):action(str(o.action));return
	ui._notice("面对人物或物件，再按确认")

func action(key: String) -> void:
	var g=ui.game
	if key in ["shrine","east_promotions","third_promotions"] or key.begins_with("promote_"):
		ui.field_notes.open_promotions();return
	if key=="treatment":
		_open_treatment();return
	if key.begins_with("treat_choose_"):
		var id=key.substr(13)
		ui._open_menu("treatment_confirm",["救治"+str(g.roster[id].name_zh)+"（消耗1份）","返回"],["hub:treat_confirm_"+id,"hub:treatment"],Vector2(24,88));return
	if key.begins_with("treat_confirm_"):
		var result=g.treat_member(key.substr(14))
		if result.valid:
			enter_room(room,true);ui._notice("救治完成，可以重新出阵；剩余"+str(result.remaining)+"份",6)
		else:ui._notice(str(result.reason),6)
		return
	if g.party.has(key) and g.is_dying(g.roster.get(key,{})):
		if g.chapter>=2:
			await L.say(self,["医者："+str(g.roster[key].name_zh)+"还在养伤，我们会照看。","界面提示：这位同伴暂不能出阵，可在部队状态查看伤情。"]);return
		await ui.play_pages([{"speaker":"医者","text":str(g.roster[key].name_zh)+"仍在队伍中，由我们照护，暂时不能出阵。可在部队状态查看伤情。"}],"hub");return
	if g.chapter==5:
		await FifthHub.action(self,key);g.save_game();return
	if g.chapter==4:
		await FourthHub.action(self,key);g.save_game();return
	if g.chapter==3:
		await ThirdHub.action(self,key);g.save_game();return
	if not east_data.is_empty():
		await _east_action(key);g.save_game();return
	match key:
		"prologue":
			ui.prologue_scene.start();return
		"grave":
			if g.flags.get("village_ready",false):
				var line="我还会回来。" if g.flags.get("korlan_defeated",false) else "哥，我们过了林路。我再找找见过那件事的人。" if g.stage_cleared(101) else "我去找科兰。等我回来，再把你的名字刻完。"
				await ui.play_pages([{ "speaker":"胡纳普","text":line}],"hub");return
			await ui.play_pages(g.campaign.scenes.D11,"hub","grave")
		"otto":await ui.play_pages([{"speaker":"奥托","text":"凯尔打开门，放走了老人和孩子。科兰以通敌罪处死他。"}],"hub")
		"daan":
			var scene="H01_DAAN_REPEAT" if g.flags.get("daan_companionship_seen",false) else "H01_DAAN_FIRST"
			await ui.play_pages(g.campaign.scenes[scene],"hub","daan_companionship")
		"grain":
			if g.flags.get("grain_shared",false):
				await ui.play_pages([{"speaker":"管理员","text":"粮车走了，给赫兰大人的信也送出去了。"}],"hub");return
			g.flags.grain_shared=true
			await ui.play_pages([
				{"speaker":"胡纳普","text":"这车照原来的名单送回雪原村。让伤者先领。"},
				{"speaker":"管理员","text":"士兵运走了一些，剩下的都点过了。这是教团的救济牌。冠上的七根羽毛是太阳神的记号。"},
				{"speaker":"管理员","text":"粮是赫兰大人拨的。是这一带教团的首领。你叫什么？我给他捎个信。"},
				{"speaker":"胡纳普","text":"胡纳普。"}],"hub")
		"crown":await ui.play_pages([{"speaker":"管理员","text":"七羽日冠是乌库布·卡基的神印。"}],"hub")
		"orders":
			g.flags.orders_collected=true
			await ui.play_pages([
				{"speaker":"胡纳普","text":"押送名单……还有我哥的军令。"},
				{"speaker":"界面提示","text":"到南岗押送所东边的教堂找赫兰。"}],"hub")
		"church":enter_room("H04")
		"cooperate":
			if g.flags.get("cooperation_done",false):
				await ui.play_pages([{"speaker":"赫兰","text":"凯尔的事，我已经交给记录官处理了，教团会歌颂他的正义。"}],"hub")
			elif not g.flags.get("orders_collected",false):
				ui._notice("先查看南岗押送所里的军令箱，再去找赫兰。")
			else:
				await ui.play_pages(g.campaign.scenes.D12,"hub","cooperate")
		"fula","lena","beck","hervi":
			if g.party.has(key):
				var pages=g.campaign.scenes.H09_HERVI_JOINED if key=="hervi" else [{"speaker":g.characters[key].name_zh,"text":"与你们同行，是一个不错的选择。" if key=="fula" else "我会与你同行。"}]
				await ui.play_pages(pages,"hub");return
			if key=="fula" and not g.flags.get("grain_shared",false):
				await ui.play_pages([{"speaker":"芙拉","text":"请先到那边的粮车，帮忙送回村里。"}],"hub");return
			if key=="fula":
				var text="伤者有村里的医者照看。让我跟你们走吧。" if g.stage_cleared(103) else "粮车走了，伤者也有人照看。你们路上缺个医者吧？"
				await ui.play_pages([{"speaker":"芙拉","text":text}],"hub","fula_invite");return
			if key=="hervi":
				if not g.stage_cleared(112):ui._notice("先护送运药员，将药车送达诊所");return
				if not g.flags.get("clinic_staffed",false):
					await ui.play_pages(g.campaign.scenes.H09_HERVI_ON_DUTY,"hub");return
				if not g.can_invite_hervi():ui._notice("赫维目前无法同行");return
			if key in ["beck","hervi"]:
				if not _companion_invitable(key):return
				var prefix="H08_BECK_" if key=="beck" else "H09_HERVI_"
				var scene=prefix+("REPEAT" if g.flags.get(key+"_invitation_seen",false) else "FIRST")
				await ui.play_pages(g.campaign.scenes[scene],"hub","companion_invite:"+key);return
			ui._open_menu("recruit",["邀请同行","暂不邀请"],["hub:recruit_"+key,"close"],Vector2(48,88))
		"lance":
			var line="去海峡城要过旧塔外营。" if g.flags.get("cooperation_done",false) else "赫兰大人在里面。他在等押送所的消息。"
			await ui.play_pages([{"speaker":"兰斯","text":line}],"hub")
		"shrine":
			var labels=[];var actions=[]
			for id in g.party:
				if not g.can_deploy(g.roster[id]):continue
				for option in ui.Progression.promotion_options(g.roster[id]):
					labels.append(str(g.roster[id].name_zh)+"→"+str(g.catalog.classes[str(int(option.class_id))].name_zh))
					actions.append("hub:promote_"+str(id)+"_"+str(int(option.class_id)))
			if labels.is_empty():ui._notice("尚无成员达到转职等级");return
			ui._open_menu("promotion",labels,actions,Vector2(24,72))
		"invite":
			var mine_line="矿工们都回来了。多亏了你们！" if g.stage_cleared(111) else "旧矿道塌了，矿工还在里面。贝克进去救人，路又被匪徒堵上了。求你们去看看。"
			var clinic_line="药已经送到诊所。伤员们可算有救了。" if g.stage_cleared(112) else "送药去林村诊所的车被士兵拦在桥南了。赫维还等着药救人。"
			await ui.play_pages([{"speaker":"村民","text":mine_line},{"speaker":"村民","text":clinic_line}],"hub")
		"mine_survivor":
			var pages=[{"speaker":"老矿工","text":"军队要的矿石越来越多。矿道都快塌了，他们还不许我们停工。"}]
			pages.append({"speaker":"老矿工","text":"多亏你们和贝克，我们才活着出来。那小伙子，就拜托你们了。" if ui.game.party.has("beck") else "贝克没能回来……他是为了救我们啊。"})
			await ui.play_pages(pages,"hub")
		"mine_apprentice":await ui.play_pages([{"speaker":"年轻矿工","text":"多谢！我娘还在村里等我。我这就回去。"}],"hub")
		"tools":await ui.play_pages([{"speaker":"年轻矿工","text":"工具也找回来了！谢谢你们，这些可都是吃饭的家伙啊。" if g.flags.get("tools_reward",false) else "有些工具还落在洞里。等大家歇一歇，我们自己去搬吧。"}],"hub")
		"staff":
			if room!="H09" or not g.stage_cleared(112):ui._notice("药车尚未送达，先完成护送");return
			if g.flags.get("clinic_staffed",false):
				await ui.play_pages([{"speaker":"管理员","text":"伤员有我照顾，你们安心。"}],"hub");return
			var pages=[{"speaker":"运药员","text":"药车在门口。退热药在最上面。"},{"speaker":"管理员","text":"我去搬药。伤者也交给我吧。"}]
			if not g.flags.get("clinic_hervi_unavailable",false) and g.speaker_alive("赫维"):
				pages.append({"speaker":"赫维","text":"拜托你了。里屋有一位还没醒。"})
			await ui.play_pages(pages,"hub","clinic_handover")
		"transport":await ui.play_pages([{"speaker":"运药员","text":"那些士兵运药的车都拦。"}],"hub")
		"delivery":await ui.play_pages([{"speaker":"管理员","text":"药放在这。哪间屋用完了，再来拿。"}],"hub")
		"treat":g.flags.workers_treated=true;await ui.play_pages([{"speaker":"医者","text":"伤者安顿好了。伟大的日返仪式可以在堡里的塔上举行。"}],"hub")
		"ceremony":
			if g.flags.get("chapter1_complete",false):await ui.play_pages([{"speaker":"赫兰","text":"大家正为明日的庆典做准备。"}],"hub");return
			if not g.flags.get("workers_treated",false):ui._notice("先在内院安置获救的伤者");return
			if not g.flags.get("chapter1_complete",false) and (not g.stage_cleared(111) or not g.stage_cleared(112)):
				ui._open_menu("side_closure",["返回整备","举行日返"],["close","hub:ceremony_confirm"],Vector2(44,112));ui._notice("未完成支线将随仪式收束",6);return
			action("ceremony_confirm")
		"ceremony_confirm":
			var pages=[
				{"speaker":"赫兰","text":"可以举行日返仪式了。"},
				{"speaker":"乌库布·卡基","text":"我救下这片土地。日光将重返西大陆，愿你们记住庇护的恩情。"},
				{"speaker":"胡纳普","text":"把内院的人都带出来。"}]
			if g.speaker_alive("达恩"):
				pages.append({"speaker":"达恩","text":"明天庆典结束，一起回雪原村吧。凯尔的名字还没刻完。"})
				pages.append({"speaker":"胡纳普","text":"好。明天庆典结束就回去。"})
			else:
				pages.append({"speaker":"胡纳普","text":"等庆典结束，我就回雪原村把哥哥的名字刻完。"})
			await ui.play_pages(pages,"hub","ceremony")
		"camp","guard","altar":
			var line="仪式还没开始。你可以过去。"
			var speaker="村民" if key=="camp" else "教团守卫"
			for o in objects:
				if o.action==key and not str(o.text).is_empty():line=o.text;speaker=str(o.name)
			await ui.play_pages([{ "speaker":speaker,"text":line}],"hub")
		_:
			if key.begins_with("decline_"):
				var id=key.trim_prefix("decline_")
				if _companion_invitable(id):await ui.play_pages(g.campaign.scenes["H08_BECK_DECLINE" if id=="beck" else "H09_HERVI_DECLINE"],"hub")
				return
			if key.begins_with("promote_"):
				var parts=key.split("_");var result=g.promote_unit(parts[1],int(parts[2]))
				ui._notice("转职完成" if result.get("valid",false) else "未满足转职条件");g.save_game();return
			if key.begins_with("recruit_"):
				var id=key.substr(8)
				if id in ["beck","hervi"] and not _companion_invitable(id):return
				if id=="hervi" and (room!="H09" or not g.can_invite_hervi()):ui._notice("先完成送药与诊所交接");return
				g.recruit(id)
				if not g.party.has(id):return
				if id=="beck":enter_room("H08",true,false)
				var pages=g.campaign.scenes["H08_BECK_ACCEPT" if id=="beck" else "H09_HERVI_ACCEPT"] if id in ["beck","hervi"] else [{"speaker":g.characters[id].name_zh,"text":"谁受伤我来医治。" if id=="fula" else "走吧。这儿有人照看，我也能放心。"}]
				await ui.play_pages(pages,"hub")
				if id=="hervi":enter_room("H09")
	ui.game.save_game()

func _companion_invitable(id: String) -> bool:
	var g=ui.game
	if g.party.has(id) or not g.speaker_alive(str(g.characters.get(id,{}).get("name_zh",""))):return false
	return (room=="H08" and g.stage_cleared(111)) if id=="beck" else (room=="H09" and g.can_invite_hervi()) if id=="hervi" else false

func finish_story(callback: String) -> void:
	if callback=="prometheus_maintenance":
		preload("res://core/prometheus_story.gd").accept(ui.game);return
	if callback.begins_with("late_invite:"):
		var id=callback.trim_prefix("late_invite:")
		var prefix="fourth_recruit_" if id=="celine" else "third_recruit_"
		ui._open_menu("recruit",["邀请同行","留在安置处"],["hub:"+prefix+id,"close"],Vector2(36,88));return
	if callback.begins_with("late:"):
		L.finish(self,callback);return
	# The callback is saved with the dialogue, so resuming its final page still
	# records the first conversation and restores the invitation choice.
	if callback.begins_with("companion_invite:"):
		var id=callback.trim_prefix("companion_invite:")
		if _companion_invitable(id):
			ui.game.flags[id+"_invitation_seen"]=true
			ui._open_menu("recruit",["邀请同行","暂不邀请"],["hub:recruit_"+id,"hub:decline_"+id],Vector2(48,88))
		return
	if callback=="d00_next":ui.prologue_scene.dialogue_finished();return
	if callback=="third_prologue":ui.prologue_scene.end_reprise()
	if callback.begins_with("third_"):ThirdHub.finish(self,callback);return
	match callback:
		"daan_companionship":ui.game.flags.daan_companionship_seen=true
		"fula_invite":
			var member=ui.game.roster.get("fula",{});var npc=ui.game.find_unit("fula")
			if room=="H02" and ui.game.flags.get("grain_shared",false) and not ui.game.party.has("fula") and not bool(member.get("dead",false)) and not ui.game.is_dying(member) and (npc.is_empty() or int(npc.hp)>0):
				ui._open_menu("recruit",["邀请同行","暂不邀请"],["hub:recruit_fula","close"],Vector2(48,88))
		"clinic_handover":
			if room=="H09" and ui.game.stage_cleared(112):
				ui.game.flags.clinic_staffed=true;enter_room("H09")
		"prologue":ui.game.flags.prologue_done=true;ui.game.world_node=1;enter_room("H01")
		"grave":ui.game.flags.village_ready=true
		"cooperate":ui.game.flags.cooperation_done=true;ui.game.recruit("lance")
		"ceremony":ui.game.flags.chapter1_complete=true;ui.game.mode="chapter_end";ui.view="chapter_end"
		"east_carlo":ui.game.flags.east_martin_pending=true
		"east_departure":
			ui.game.flags.east_departure_ready=true
			ui.game.flags.erase("east_martin_pending")
		"east_chart":ui.game.flags.sea_chart_collected=true
		"east_finale":
			if ui.game.finish_chapter_two():ui.view="chapter_end"

func open_system_menu() -> void:
	if ui.busy:return
	if ui.game.can_switch_route():
		ui._open_menu("hub_system",["部队整备","切换队伍","保存进度","返回标题"],["new:camp","new:switch","new:save","title"],Vector2(48,64));return
	ui._open_menu("hub_system",["部队整备","保存进度","返回标题"],["new:camp","new:save","title"],Vector2(48,72))

func _open_treatment() -> void:
	var g=ui.game
	var source="church" if room=="H04" else "lighthouse" if room=="H25" else ""
	if not (g.chapter==5 and room in ["H51","H55"]) and not (room=="H10" and g.flags.get("D33_done",false)) and (source.is_empty() or g.Casualties.SOURCES[source]!=g.route or not g.flags.get("treatment_sources",{}).get(source,false)):
		ui._notice("先完成教堂合作或安置岛民，开放本队救治份额",6);return
	if g.treatment_remaining()<=0:ui._notice("本队救治份额已经用尽",6);return
	var labels=[];var actions=[]
	for id in g.party:
		var unit: Dictionary=g.roster[id]
		if id in ["hunapu","eileen"] or not g.is_dying(unit):continue
		if int(unit.get("treatment_count",0))>=1:continue
		labels.append(str(unit.name_zh)+" · 濒死");actions.append("hub:treat_choose_"+str(id))
	if labels.is_empty():ui._notice("没有可救治的濒死成员；份额可以保留",6);return
	labels.append("返回");actions.append("close")
	ui._open_menu("treatment",labels,actions,Vector2(48,72))
func cancel() -> void:
	ui._clear_menu()

func winter_visual(id: String) -> Dictionary:
	# Drawing-only season; room objects and rules are never mutated.
	if ui.game.chapter!=1 or ui.game.flags.get("chapter1_complete",false):return {}
	return chapter1_climate.get("rooms",{}).get(id,{})

func _winter_nature_props(props: Array) -> Array:
	var result=props.duplicate(true)
	var keys: Dictionary=chapter1_climate.get("nature_keys",{})
	for p in result:p.key=keys.get(str(p.key),p.key)
	return result

func climate_surroundings(id: String,base: Dictionary) -> Dictionary:
	if winter_visual(id).is_empty():return base
	if climate_layout_cache.has(id):return climate_layout_cache[id]
	var layout=base.duplicate(true)
	layout.biome="snow"
	layout.props=_winter_nature_props(layout.get("props",[]))
	for group in layout.get("groves",[]):group.props=_winter_nature_props(group.props)
	climate_layout_cache[id]=layout
	return layout

func _draw_winter_grove(name: String,rect: Rect2i) -> bool:
	if winter_visual(room).is_empty():return false
	var layout=climate_surroundings(room,ui.nature_layouts.get("hubs",{}).get(room,{}))
	for group in layout.get("groves",[]):
		if str(group.source_name)==name and Vector2(group.rect[0],group.rect[1])==Vector2(rect.position)*16:
			ui._draw_nature_props(group.props,ORIGIN);return true
	return false

func _draw_winter_floor(visual: Dictionary) -> void:
	var atlas=ui._tex(str(visual.atlas))
	for y in range(9):
		for x in range(14):
			ui._draw_atlas_cell(atlas,int(visual.tiles[y][x]),ORIGIN+Vector2(x,y)*16)

func draw() -> void:
	if room=="H04":_draw_chapel();return
	if room=="P00":
		ui.prologue_scene.draw_plaza(false)
		var caption=hint
		for o in objects:
			if ui.game.hub_position+facing==Vector2i(o.position[0],o.position[1]):caption="确认:"+str(o.name)
		ui._draw_hub_caption(title,caption);return
	var material="snow" if room=="H01" else "cave" if room=="H08" else "cobble" if room in ["P00","H04","H06"] else "grass"
	var atlas=ui._tex("res://assets/battle_tiles/battle-tiles.png")
	var winter=winter_visual(room)
	if not east_data.is_empty():_draw_east_floor(atlas)
	else:
		if not winter.is_empty():_draw_winter_floor(winter)
		else:
			for y in range(9):
				for x in range(14):
					var id=int(ui.battle_pack.base[material][(x*3+y)%4])
					ui.draw_texture_rect_region(atlas,Rect2(Vector2(x,y)*16+ORIGIN,Vector2(16,16)),Rect2(id%32*16,id/32*16,16,16))
		ui._draw_hub_surroundings(room,ORIGIN)
	# Paint entire objects; their interaction anchor is the bottom cell.
	for d in scenery:
		if _draw_winter_grove(str(d.name),d.rect):continue
		if ui._draw_natural_grove(room,str(d.name),ORIGIN,d.rect):continue
		var path=str(d.get("sprite_path","res://assets/battle_tiles/modules/"+str(d.name)+".png"))
		if not winter.is_empty():path=str(chapter1_climate.get("scenery_paths",{}).get(str(d.name),path))
		if ui.game.chapter==3:path=str(chapter3_environment.get("rooms",{}).get(room,{}).get("scenery_paths",{}).get(path,path))
		if ui.game.chapter==4:path=str(chapter4_environment.get("rooms",{}).get(room,{}).get("scenery_paths",{}).get(path,path))
		if ui.game.chapter==5:path=str(chapter5_environment.get("rooms",{}).get(room,{}).get("scenery_paths",{}).get(path,path))
		ui.draw_texture(ui._tex(path),ORIGIN+Vector2(d.rect.position)*16,_east_environment_tint())
	# Sort by feet/ground anchor. Tall signs cover someone behind them;
	# someone in front covers the sign. Collision remains on the ground.
	if motion_left<=0.0:render_position=Vector2(ui.game.hub_position)*16
	var layers=objects.duplicate()
	layers.append({"sprite":"hub_player","position":[render_position.x/16,render_position.y/16]})
	layers.sort_custom(func(a,b):return float(a.position[1])<float(b.position[1]))
	for o in layers:
		if o.sprite=="hub_player":_draw_player();continue
		var at=Vector2(o.position[0],o.position[1])*16+ORIGIN
		if o.sprite=="actor":
			var sp: Dictionary=ui.graphics.village_sprites.get(str(int(o.source)),ui.graphics.village_sprites["1"])
			if ui.has_method("_party_hub_sprite"):sp=ui.call("_party_hub_sprite",o,sp)
			ui._draw_frame(sp,int(sp.directions.down[0]),at-Vector2(sp.tile_origin[0],sp.tile_origin[1]))
		else:
			var tex=ui._tex(str(o.get("sprite_path","res://assets/battle_tiles/modules/"+str(o.sprite)+".png")));ui.draw_texture(tex,at-Vector2(0,tex.get_height()-16),Color.WHITE if o.sprite in ["sun_altar","lit_brazier","ritual_lamp","well"] else _east_environment_tint())
		if object_occupies(o,ui.game.hub_position+facing):ui._draw_map_indicator("down",at+Vector2(4,-8))
	ui._draw_map_indicator("down",ORIGIN+Vector2(6,8)*16+Vector2(4,-2))
	var text=hint
	for o in objects:
		if object_occupies(o,ui.game.hub_position+facing):text="确认:"+str(o.name)
	ui._draw_hub_caption(title,text)

func _draw_player() -> void:
	var source_id="2" if ui.game.route=="celica" else "1"
	var sp: Dictionary=ui.graphics.village_sprites[source_id]
	if ui.has_method("_personal_hub_sprite"):sp=ui.call("_personal_hub_sprite",sp)
	var direction="up" if facing.y<0 else "side" if facing.x!=0 else "down"
	if motion_left<=0.0:render_position=Vector2(ui.game.hub_position)*16
	var at=render_position+ORIGIN
	if facing.x!=0 and sp.directions.has("left"):direction="left" if facing.x<0 else "right"
	var travel=preload("res://core/reviewed_animations.gd")
	var frame=travel.travel_frame(sp,direction,clock,motion_left>0.0)
	ui._draw_frame(sp,frame,at-Vector2(sp.tile_origin[0],sp.tile_origin[1]),facing.x<0 and not sp.directions.has("left"))

func _configure_east_room() -> void:
	east_data=chapter2_rooms[room].duplicate(true)
	title=str(east_data.title);hint=str(east_data.hint);objects=[];scenery=[]
	var s21_rescued: bool = room == "H22" and ui.game.stage_cleared(211)
	if s21_rescued:hint = "向地方医者报告渔船救援"
	for raw in east_data.objects:
		var o: Dictionary=raw.duplicate(true)
		if s21_rescued and o.action == "invite_s21":continue
		if o.has("party") and not _east_alive(str(o.party)):continue
		if o.has("recruit"):
			var id=str(o.recruit)
			if not ui.game.flags.get("east_recruit_ready",{}).get(id,false) and not ui.game.party.has(id):continue
			if bool(ui.game.roster.get(id,{}).get("dead",false)):continue
		if o.action=="resistance_spring" and ui.game.flags.get("lighthouse_spring_used",false):o.name="抗性泉 · 已用尽"
		if o.action=="treatment":o.name=("共享救治 · 剩余" if ui.game.chapter>=3 else "救治泉 · 东队剩余")+str(ui.game.treatment_remaining())+"份"
		if ui.game.chapter==4 and o.action=="fourth_celine" and not ui.game.flags.get("celine_ready",false):o.name="安置记录";o.sprite="orders_case"
		if ui.game.chapter==3 and o.action in ["third_german","third_noya"]:
			var member="german" if o.action=="third_german" else "noya"
			if not ui.game.flags.get("chapter3_recruits",{}).get(member,false):o.name="安置记录";o.sprite="orders_case"
		if ui.game.chapter==3 and o.action in ["third_reunion","third_council"]:
			var present=(ui.game.stage_cleared(301) and ui.game.stage_cleared(304)) if o.action=="third_reunion" else (int(ui.game.route_positions.alm)==9 and int(ui.game.route_positions.celica)==9)
			o.name=("艾琳" if ui.game.route=="alm" else "胡纳普") if present else "信使"
			o.source=(2 if ui.game.route=="alm" else 1) if present else 5
		objects.append(o)
	for raw in east_data.scenery:
		var d: Dictionary=raw.duplicate(true)
		d.rect=Rect2i(int(d.position[0]),int(d.position[1]),int(d.footprint[0]),int(d.footprint[1]));scenery.append(d)

func _east_alive(id: String) -> bool:
	return ui.game.party.has(id) and ui.game.roster.has(id) and not bool(ui.game.roster[id].get("dead",false)) and int(ui.game.roster[id].get("hp",0))>0

func east_walkable(at: Vector2i) -> bool:
	if east_data.is_empty():return true
	if at.x<0 or at.x>=14 or at.y<0 or at.y>=9:return false
	if str(east_data.floor[at.y])[at.x]=="~":return false
	for o in objects:
		var p=Vector2i(int(o.position[0]),int(o.position[1]));var shape=Vector2i(1,1)
		if o.sprite!="actor":
			var fp=o.get("footprint",[1,1]);shape=Vector2i(int(fp[0]),int(fp[1]));p.y-=shape.y-1
		if Rect2i(p,shape).has_point(at):return false
	return not scenery.any(func(d):return bool(d.get("blocking",true)) and d.rect.has_point(at))

func _east_exit_allowed() -> bool:
	if ui.game.chapter==4:return true
	if ui.game.chapter==3:
		if room=="H30":ui._notice("先面对赫兰，接续庆典");return false
		return true
	if room=="H21" and ui.game.flags.get("east_martin_pending",false):
		ui._notice("先在南边跳板旁和马丁谈谈");return false
	var guards={"H21":["east_departure_ready","先与卡洛谈谈，确认出航"],"H22":["F21_confirmed","先向马丁确认押送舰的航路"],"H23":["F22_confirmed","先在安置处照顾全部伤者"],"H24":["F23_confirmed","先向渔村长者确认岸线"],"H25":["islanders_settled","先请留守骑士安置岛民"]}
	if room=="H27":ui._notice("先向广场前的守卫交涉");return false
	if guards.has(room) and not ui.game.flags.get(guards[room][0],false):ui._notice(guards[room][1]);return false
	return true

func _east_environment_tint() -> Color:
	if ui.game.chapter==5 and chapter5_environment.get("rooms",{}).has(room):
		var fifth_tint=chapter5_environment.rooms[room].get("tint",[1.0,1.0,1.0])
		return Color(fifth_tint[0],fifth_tint[1],fifth_tint[2])
	if ui.game.chapter==4 and chapter4_environment.get("rooms",{}).has(room):
		if room=="H48" and ui.game.flags.get("island_loop_safe",false):return Color.WHITE
		if room=="H47" and ui.game.flags.get("D42_done",false):return Color.WHITE
		var fourth_tint=chapter4_environment.rooms[room].get("tint",[1.0,1.0,1.0])
		return Color(fourth_tint[0],fourth_tint[1],fourth_tint[2])
	if ui.game.chapter==3 and chapter3_environment.get("rooms",{}).has(room):
		var third_tint=chapter3_environment.rooms[room].get("tint",[1.0,1.0,1.0])
		return Color(third_tint[0],third_tint[1],third_tint[2])
	if ui.game.chapter==2 and ui.game.flags.get("F22_confirmed",false) and room in ["H21","H22","H23"]:
		return Color(.82,.86,.94)
	var tint=east_data.get("environment_tint",[1.0,1.0,1.0])
	return Color(float(tint[0]),float(tint[1]),float(tint[2]))

func _draw_east_floor(atlas: Texture2D) -> void:
	var visible: Rect2=ui._visible_native_rect()
	var tint=_east_environment_tint()
	var environment: Dictionary=chapter2_environment.get("rooms",{}).get(room,{}) if ui.game.chapter==2 else {}
	if ui.game.chapter==3:environment=chapter3_environment.get("rooms",{}).get(room,{})
	if ui.game.chapter==4:environment=chapter4_environment.get("rooms",{}).get(room,{})
	if ui.game.chapter==5:environment=chapter5_environment.get("rooms",{}).get(room,{})
	var environment_atlas=chapter3_environment.get("atlas","") if ui.game.chapter==3 else chapter2_environment.get("atlas","")
	if ui.game.chapter==4:environment_atlas=environment.get("source_atlas",chapter4_environment.get("atlas",""))
	if ui.game.chapter==5:environment_atlas=chapter5_environment.get("atlas","")
	var background=str(environment.get("background",east_data.get("biome_override","sea")))
	for y in range(floori((visible.position.y-ORIGIN.y)/16),ceili((visible.end.y-ORIGIN.y)/16)):
		for x in range(floori((visible.position.x-ORIGIN.x)/16),ceili((visible.end.x-ORIGIN.x)/16)):
			var variant=posmod((x*73856093)^(y*19349663),4)
			var id=int(ui.battle_pack.base[background][variant])
			ui.draw_texture_rect_region(atlas,Rect2(Vector2(x,y)*16+ORIGIN,Vector2(16,16)),Rect2(id%32*16,id/32*16,16,16),tint*Color(float(environment.get("background_darkness",1.0)),float(environment.get("background_darkness",1.0)),float(environment.get("background_darkness",1.0))))
	for y in range(9):
		for x in range(14):
			var mark=str(east_data.floor[y])[x]
			if mark=="~":continue
			var material=str(east_materials.get(mark,"sand"))
			var variant=posmod((x*73856093)^(y*19349663)^((x+y*17)>>2),4)
			var id=int(ui.battle_pack.base[material][variant])
			if not environment.is_empty():
				ui._draw_atlas_cell(ui._tex(str(environment_atlas)),int(environment.tiles[y][x]),Vector2(x,y)*16+ORIGIN,tint)
			else:
				ui.draw_texture_rect_region(atlas,Rect2(Vector2(x,y)*16+ORIGIN,Vector2(16,16)),Rect2(id%32*16,id/32*16,16,16),tint)
			if background=="sea" and mark not in ["=","c"]:
				var mask=_east_land_mask(Vector2i(x,y))
				if mask!=255:ui.draw_texture(_east_shore_overlay(atlas,mask),Vector2(x,y)*16+ORIGIN,tint)
	for prop in environment.get("props",[]):
		ui.draw_texture(ui._tex(str(prop.path)),ORIGIN+Vector2(prop.position[0],prop.position[1]),tint)
	# The boundary is outside the original walkable room. The original south exit remains open.
	var frame=environment.get("wall_frame",{})
	if not frame.is_empty():
		var wall_atlas=ui._tex(str(environment_atlas))
		for x in range(-1,15):
			ui._draw_atlas_cell(wall_atlas,int(frame.north[posmod(x,frame.north.size())]),ORIGIN+Vector2(x,-1)*16,tint)
			if x!=6:ui._draw_atlas_cell(wall_atlas,int(frame.north[posmod(x,frame.north.size())]),ORIGIN+Vector2(x,9)*16,tint)
		for y in range(9):
			for x in [-1,14]:ui._draw_atlas_cell(wall_atlas,int(frame.west[y%frame.west.size()]),ORIGIN+Vector2(x,y)*16,tint)

	if background=="cobble":ui._draw_hub_surroundings("P00",ORIGIN)

func _east_land_mask(at: Vector2i) -> int:
	var mask=0
	var neighbors=[[0,-1,1],[1,0,2],[0,1,4],[-1,0,8],[1,-1,16],[1,1,32],[-1,1,64],[-1,-1,128]]
	for neighbor in neighbors:
		var p=at+Vector2i(neighbor[0],neighbor[1])
		if p.x>=0 and p.x<14 and p.y>=0 and p.y<9 and str(east_data.floor[p.y])[p.x]!="~":mask|=int(neighbor[2])
	for corner in [[16,1,2],[32,2,4],[64,4,8],[128,8,1]]:
		if not ((mask&corner[1]) and (mask&corner[2])):mask&=~int(corner[0])
	return mask

func _east_shore_overlay(atlas: Texture2D,mask: int) -> Texture2D:
	if east_shore_cache.has(mask):return east_shore_cache[mask]
	# Use the existing 47-tile coast's authored alpha; this only composes an
	# inverse water overlay, preserving the original sand and sea textures.
	var source=atlas.get_image();var id=int(ui.battle_pack.families.water[str(mask)])
	var alpha=source.get_region(Rect2i(id%32*16,id/32*16,16,16));id=int(ui.battle_pack.base.sea[0])
	var water=source.get_region(Rect2i(id%32*16,id/32*16,16,16));water.convert(Image.FORMAT_RGBA8)
	for y in range(16):
		for x in range(16):
			var pixel=water.get_pixel(x,y);pixel.a=1.0-alpha.get_pixel(x,y).a;water.set_pixel(x,y,pixel)
	var texture=ImageTexture.create_from_image(water);east_shore_cache[mask]=texture;return texture

func _east_pages(lines: Array,callback: String="") -> void:
	var result=[]
	for line in lines:
		var parts=str(line).split("：",true,1)
		result.append({"speaker":parts[0],"text":parts[1] if parts.size()>1 else ""})
	await ui.play_pages(result,"hub",callback)

func _martin_cell() -> Vector2i:
	for o in objects:
		if o.action=="east_martin":return Vector2i(int(o.position[0]),int(o.position[1]))
	return Vector2i(-1,-1)

func resume_east_departure() -> void:
	if room!="H21" or not ui.game.flags.get("east_martin_pending",false):return
	var martin=_martin_cell()
	var target=martin+Vector2i.RIGHT
	var grid=AStarGrid2D.new()
	grid.region=Rect2i(1,1,12,7)
	grid.diagonal_mode=AStarGrid2D.DIAGONAL_MODE_NEVER
	grid.update()
	for y in range(1,8):
		for x in range(1,13):
			var cell=Vector2i(x,y)
			grid.set_point_solid(cell,not east_walkable(cell))
	var start: Vector2i=ui.game.hub_position
	var path: Array[Vector2i]=[]
	if grid.region.has_point(start) and grid.region.has_point(target):path=grid.get_id_path(start,target)
	if path.is_empty():
		ui._notice("去南边跳板旁找马丁");return
	var was_busy=ui.busy
	ui.busy=true;ui.held_direction=Vector2i.ZERO
	for cell in path.slice(1):
		facing=cell-ui.game.hub_position
		_step_to(cell)
		while motion_left>0.0:await ui.get_tree().process_frame
	facing=martin-ui.game.hub_position
	await L.say(self,L.lines("H21","艾琳与马丁"),"east_departure")
	ui.busy=was_busy

func _east_action(key: String) -> void:
	if key=="east_promotions" or key.begins_with("promote_"):
		ui.field_notes.open_promotions();return
	var g=ui.game
	match key:
		"east_departure":
			if g.flags.get("east_departure_ready",false):await L.say(self,L.lines("H21","D21",1));return
			if not g.flags.get("east_martin_pending",false):await L.say(self,L.lines("H21","D21"),"east_carlo")
			await resume_east_departure()

		"east_martin":
			if g.flags.get("east_departure_ready",false):await L.say(self,L.lines("H21","艾琳与马丁",1));return
			if not g.flags.get("east_martin_pending",false):ui._notice("先和卡洛谈谈");return
			await L.say(self,L.lines("H21","艾琳与马丁"),"east_departure")

		"east_mireille":
			await L.say(self,L.lines("H21","米蕾"))

		"east_lisa":
			await L.say(self,L.lines("H21","莉莎"))

		"east_chart_start":
			await L.say(self,L.lines("H21","薇娅"))

		"sea_route":
			await L.say(self,L.lines("H22","确认"),"late:F21_confirmed")

		"invite_s21":
			await L.say(self,L.lines("H22","漂泊渔船求救",0 if _east_alive("mireille") else 1),"late:S21_invited")

		"s21_report":
			await L.say(self,L.lines("H22","漂泊渔船救援",0 if g.stage_cleared(211) else 1))

		"prisoners_treat":
			var treatment_branch=0 if _east_alive("mireille") else 1
			var survivors=g.stage_id==202 and g.stage_cleared(202) and not g.living("enemy").is_empty()
			if not g.flags.get("F22_soldiers_surrendered",survivors):treatment_branch+=2
			var lord_present=g.flags.get("east_recruit_ready",{}).get("lord",false) and g.speaker_alive("洛德")
			var rows=L.lines("H23","照护",treatment_branch)
			rows+=L.lines("H23","薇娅")+L.lines("H23","舰上的",0 if lord_present else 1)
			await L.say(self,rows,"late:F22_confirmed")

		"captives_route":
			await L.say(self,L.lines("H23","引航者"))

		"lord","roan","shia":
			if g.party.has(key):
				var group=1
				if key=="lord":group=2 if _east_alive(key) else 0
				await L.say(self,L.lines({"lord":"H23","roan":"H24","shia":"H25"}[key],{"lord":"洛德的","roan":"罗恩的","shia":"希雅的"}[key],group).filter(func(row):return not str(row).begins_with("界面提示：")));return
			if not g.flags.get("east_recruit_ready",{}).get(key,false) or bool(g.roster.get(key,{}).get("dead",false)):ui._notice("这位同伴未能获救");return
			if key=="lord" and not g.flags.get("F22_confirmed",false):ui._notice("先在安置处照顾获救伤者");return
			if key=="shia" and not g.flags.get("islanders_settled",false):ui._notice("先安置岛民，让留守骑士接手");return
			if key=="lord":
				var available=g.speaker_alive("洛德")
				await L.say(self,L.lines("H23","洛德的",1 if available else 0))
				if not available:return
			ui._open_menu("recruit",["邀请同行","暂不邀请"],["hub:east_recruit_"+key,"close"],Vector2(48,88))
		"reef_route":
			await L.say(self,L.join_groups("H24","渔村岸线",[0,1,2]),"late:F23_confirmed")

		"invite_s22":
			await L.say(self,L.lines("H24","海洞遗物",0 if g.stage_cleared(212) else (1 if _east_alive("carlo") else 2)),"late:S22_invited")

		"holy_sword":_east_claim_item("F23_holy_sword_taken",16,"圣剑")
		"holy_bow":_east_claim_item("F25_holy_bow_taken",21,"圣弓")
		"islanders_settle":
			if g.flags.get("islanders_settled",false):await L.say(self,L.lines("H25","安置",1));return
			var rows=L.lines("H25","安置",0 if g.flags.get("islanders_survived",true) else 2)+L.lines("H25","灯屋")
			await L.say(self,rows,"late:islanders_settled")

		"east_training":
			if not g.flags.get("islanders_settled",false):ui._notice("先让留守骑士安置岛民");return
			ui._open_menu("east_training",["职业进阶","法术与训练","离开"],["hub:east_promotions","hub:east_magic_info","close"],Vector2(40,80))
		"east_promotions":
			var labels=[];var actions=[]
			for id in g.party:
				if not _east_alive(id):continue
				for option in ui.Progression.promotion_options(g.roster[id]):
					labels.append(str(g.roster[id].name_zh)+"→"+str(g.catalog.classes[str(int(option.class_id))].name_zh));actions.append("hub:promote_"+str(id)+"_"+str(int(option.class_id)))
			if labels.is_empty():ui._notice("尚无成员达到转职等级");return
			ui._open_menu("promotion",labels,actions,Vector2(24,72))
		"east_magic_info":
			await L.say(self,L.lines("H25","学舍"))

		"resistance_spring":
			if g.flags.get("lighthouse_spring_used",false):ui._notice("抗性泉已经用尽，不会再次补充");return
			var labels=[];var actions=[]
			for id in g.party:
				if _east_alive(id):labels.append(str(g.roster[id].name_zh)+" 抗性+1");actions.append("hub:east_spring_"+str(id))
			ui._open_menu("east_spring",labels,actions,Vector2(40,72))
		"r05":await _east_relation()
		"chart_recover":
			await L.say(self,L.lines("H26","取回",1 if g.flags.get("sea_chart_collected",false) else 0),"east_chart")

		"harbor_patients":
			await L.say(self,L.lines("H26","军港撤离",0 if _east_alive("mireille") else 1),"late:harbor_patients_treated")

		"ancient_departure":
			if not g.flags.get("sea_chart_collected",false):ui._notice("先面对神教箱，取回母亲航图");return
			if not g.flags.get("harbor_patients_treated",false):ui._notice("先在安置处确认撤离者已经上船");return
			if g.flags.get("east_departure_confirmed",false):await L.say(self,L.lines("H26","古道西渡").slice(0,1));return
			var pending=[]
			if not g.stage_cleared(211):pending.append("漂泊渔船")
			if not g.stage_cleared(212):pending.append("碎石海洞")
			if not pending.is_empty():
				ui._notice("西渡后不能折返。未完成支线："+"、".join(pending),6)
			ui._open_menu("east_closure",["继续整备","确认西渡"],["close","hub:east_sail_confirm"],Vector2(44,112))
		"east_sail_confirm":
			await L.say(self,L.join_groups("H26","确认西渡",[0,1]),"late:east_departure_confirmed")

		"east_finale":
			if g.flags.get("chapter2_complete",false):g.mode="chapter_end";ui.view="chapter_end";return
			if not g.stage_cleared(206):ui._notice("先护送船团通过断航古道");return
			await L.say(self,L.join_groups("H27","D26",[0,1]),"east_finale")

		"arrival_captain":
			await L.say(self,L.lines("H27","广场"))

		"arrival_altar":
			await L.say(self,L.lines("H27","认出"))

		_:
			if key.begins_with("east_recruit_"):
				var id=key.substr(13)
				if not g.flags.get("east_recruit_ready",{}).get(id,false) or bool(g.roster.get(id,{}).get("dead",false)):return
				g.recruit(id)
				await L.say(self,L.lines({"lord":"H23","roan":"H24","shia":"H25"}[id],{"lord":"洛德接受","roan":"罗恩接受","shia":"希雅接受"}[id]))
			elif key.begins_with("promote_"):
				var parts=key.split("_");var result=g.promote_unit(parts[1],int(parts[2]));ui._notice("转职完成" if result.get("valid",false) else "未满足转职条件")
			elif key.begins_with("east_spring_"):
				var id=key.substr(12)
				if g.flags.get("lighthouse_spring_used",false) or not _east_alive(id):return
				var u: Dictionary=g.roster[id];var current=int(u.get("resistance",0));var bonus=15 if int(u.class_id)==10 else 0
				var personal=int(u.get("personal_resistance",current-bonus));u.personal_resistance=mini(40,personal+1);u.resistance=int(u.personal_resistance)+bonus
				g.flags.lighthouse_spring_used=true;g.flags.lighthouse_spring_recipient=id
				_configure_east_room();ui._notice(str(u.name_zh)+"抗性提升，泉水已用尽")

func _east_claim_item(flag: String,item_id: int,label: String) -> void:
	if ui.game.flags.get(flag,false):ui._notice("宝箱已经取空");return
	var receipt=ui.game.receive_equipment(item_id)
	if not receipt.valid:ui._notice("行囊已满，整理后可再次领取");return
	ui.game.flags[flag]=true
	if receipt.destination=="unit":ui._notice("获得"+label+"，已交给"+str(ui.game.roster[receipt.recipient].name_zh))
	else:ui._notice("获得"+label+"，已放入东队行囊")

func _east_relation() -> void:
	var g=ui.game;var index=2;var callback=""
	if _east_alive("carlo"):
		if not _east_alive("shia"):index=4
		elif g.flags.get("carlo_promise_completed",false) and not g.flags.get("R05_promise_seen",false):index=3;callback="late:R05_promise_seen,seen_R05"
		elif not g.flags.get("seen_R05",false):index=0;callback="late:seen_R05"
		else:index=1
	await L.say(self,L.lines("H25","R05",index),callback)

func _draw_chapel() -> void:
	ui.draw_rect(ui._visible_native_rect(),Color("15171d"))
	# The east opening of the healing alcove meets walkable tile (2, 6).
	ui.draw_texture_rect(ui._tex("res://assets/field-notes-20261030/chapel-open.webp"),Rect2(ORIGIN,Vector2(224,144)),false)
	if motion_left<=0:render_position=Vector2(ui.game.hub_position)*16
	var layers=objects.duplicate();layers.append({"sprite":"hub_player","position":[render_position.x/16,render_position.y/16]})
	layers.sort_custom(func(a,b):return float(a.position[1])<float(b.position[1]))
	for o in layers:
		if o.sprite=="hub_player":_draw_player();continue
		var at=ORIGIN+Vector2(o.position[0],o.position[1])*16
		if o.sprite=="actor":
			var sp=ui._party_hub_sprite(o,{})
			ui._draw_frame(sp,int(sp.directions.down[0]),at-Vector2(sp.tile_origin[0],sp.tile_origin[1]))
		elif o.action=="shrine":
			ui.draw_texture_rect(ui._tex("res://assets/old-chapel-20261030/altar.png"),Rect2(at,Vector2(32,16)),false)
		else:
			var tex=ui._tex("res://assets/battle_tiles/modules/"+str(o.sprite)+".png")
			ui.draw_texture(tex,at-Vector2(0,tex.get_height()-16))
		if object_occupies(o,ui.game.hub_position+facing):ui._draw_map_indicator("down",at+Vector2(4,-12))
	var caption="中央祭台：查看进阶条件；南门返回押送所"
	for o in objects:
		if object_occupies(o,ui.game.hub_position+facing):caption="确认："+str(o.name)
	ui._draw_hub_caption(title,caption)

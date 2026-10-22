extends RefCounted
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

func _init(owner) -> void:
	ui=owner
	chapter1_climate=ui.GameState.read_json("res://data/chapter1_hub_climate.json")
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
		if Vector2i(o.position[0],o.position[1])!=cell:continue
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
	var rooms={1:"H01",2:"H07",3:"H02",4:"H03",5:"H05",6:"H06",31:"H08",32:"H09",17:"H21",18:"H22",19:"H23",20:"H24",21:"H25",22:"H26",23:"H27",33:"H22",34:"H24"}
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
			obj("guard",[4,4],"教团守卫","actor",0,"这里刚恢复日光。请沿着广场走到传光台。")
			obj("prologue",[7,2],"赫兰","actor",4);obj("prologue",[10,3],"艾琳","actor",2)
			obj("altar",[6,1],"传光台","sun_altar")
		"H01":
			title="半年前 · 雪原村";hint="墓前交谈后，向南离村"
			obj("grave",[6,3],"凯尔的墓","grave");obj("otto",[3,4],"奥托","actor",5)
			obj("daan",[10,5],"达恩","actor",21)
		"H02":
			title="丘堡粮站 · 战后";hint="确认分粮，再与芙拉交谈"
			obj("grain",[6,3],"粮车","grain_wagon");obj("fula",[3,5],"芙拉","actor",14)
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
			obj("camp",[6,3],"投降兵","actor",5,"塔工还在内院。将军要带粮走，没有给他们留车。")
		"H06":
			title="海峡城 · 旧塔内院";hint="安置伤者后，在日塔确认仪式"
			obj("treat",[4,5],"伤者与医者","medicine_wagon")
			obj("ceremony",[7,2],"日返仪式","sun_altar")
		"H07":
			title="林路营地";hint="查看矿道和诊所的求助，再选道路"
			obj("invite",[6,3],"村民","actor",7)
			obj("camp",[10,5],"奥托","actor",5,"凯尔也是从这里护送流民。粮站在北面，那里还能找到军令的副本。")
		"H08":
			title="旧矿道 · 战后";hint="贝克存活时可交谈招募"
			obj("beck",[6,3],"贝克","actor",20);obj("tools",[10,5],"矿工工具","crates")
		"H09":
			title="林村诊所 · 战后";hint="请管理员接手医疗，再与赫维交谈"
			obj("staff",[4,3],"管理员","actor",7);obj("hervi",[9,5],"赫维","actor",27)
	for o in objects.duplicate():
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
	if chapter2_rooms.has(room):_configure_east_room()
	ui.audio.play_music("village")
	if checkpoint:ui.game.save_game()
	ui.queue_redraw()

func obj(action: String,at: Array,name: String,sprite: String,source: int=0,text: String="") -> void:
	objects.append({"action":action,"position":at,"name":name,"sprite":sprite,"source":source,"text":text})

func direction(d: Vector2i) -> void:
	if ui.busy or motion_left>0.0:return
	if not ui.menu_items.is_empty():
		ui.menu_selected=posmod(ui.menu_selected+(d.x if d.x!=0 else d.y),ui.menu_items.size());return
	facing=d;var at=ui.game.hub_position+d
	if at==Vector2i(6,8):
		if not east_data.is_empty() and not _east_exit_allowed():return
		if room=="P00":ui._notice("先到传光台，看看庆典发生了什么");return
		if room=="H01" and not ui.game.flags.get("village_ready",false):ui._notice("先到凯尔墓前与达恩谈谈");return
		if room=="H02" and not ui.game.flags.get("grain_shared",false):ui._notice("粮车还没确认分粮");return
		if room=="H03" and not ui.game.flags.get("orders_collected",false):ui._notice("先查看军令箱");return
		if room=="H04":enter_room("H03");return
		ui._open_menu("hub_exit",["离开据点","留下"],["new:world","close"],Vector2(48,88));return
	if at.x<1 or at.x>12 or at.y<1 or at.y>7:return
	if not east_data.is_empty() and not east_walkable(at):return
	if objects.any(func(o):return Vector2i(o.position[0],o.position[1])==at):return
	if scenery.any(func(d):return bool(d.get("blocking",true)) and d.rect.has_point(at)):return
	motion_origin=Vector2(ui.game.hub_position)*16;motion_target=Vector2(at)*16
	motion_left=0.0 if ui.instant_mode else STEP
	render_position=motion_target if ui.instant_mode else motion_origin
	ui.game.hub_position=at;ui.game.save_game();ui.queue_redraw()

func accept() -> void:
	if ui.busy or motion_left>0.0:return
	if not ui.menu_items.is_empty():
		var a=str(ui.menu_actions[ui.menu_selected]);var context=ui.menu_context;ui._clear_menu();ui._menu_action(a,context);return
	var target=ui.game.hub_position+facing
	for o in objects:
		if Vector2i(o.position[0],o.position[1])==target:action(str(o.action));return
	ui._notice("面对人物或物件，再按确认")

func action(key: String) -> void:
	var g=ui.game
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
			await ui.play_pages(g.campaign.scenes.D00+[{"speaker":"旁白","text":"胡纳普挡住法术。神幕显出倾斜的屋顶与撤离的船。她来自同一个世界的另一岸。"},{"speaker":"旁白","text":"半年前，西大陆。"}],"hub","prologue")
		"grave":
			if g.flags.get("village_ready",false):
				var line="科兰已败。我还会回来，把你的名字刻完。" if g.flags.get("korlan_defeated",false) else "林路已清，我会继续寻找军令的证人。" if g.stage_cleared(101) else "我们先把林路上的居民送出去。"
				await ui.play_pages([{ "speaker":"胡纳普","text":line}],"hub");return
			await ui.play_pages(g.campaign.scenes.D11,"hub","grave")
		"otto":await ui.play_pages([{ "speaker":"奥托","text":"凯尔打开关卡，放走了老人和孩子。科兰以通敌罪处死他。这份军令，我愿作证。"}],"hub")
		"daan":await ui.play_pages([{ "speaker":"达恩","text":"我带着弓。先把林路上的人送出去，再找科兰。"}],"hub")
		"grain":
			g.flags.grain_shared=true
			await ui.play_pages([{ "speaker":"胡纳普","text":"粮车按原名单送回雪原村。受伤的人先领。"},{"speaker":"管理员","text":"粮已经点清。这块救济牌刻着七羽日冠，和塔上的冠印一样。"}],"hub")
		"crown":await ui.play_pages([{ "speaker":"管理员","text":"七羽日冠是乌库布·卡基的神印。粮还得装车，牌也会送到村里。"}],"hub")
		"orders":
			g.flags.orders_collected=true
			await ui.play_pages([{ "speaker":"胡纳普","text":"押送名单和凯尔的军令都在。先带劳工回去，再去教堂找赫兰。"}],"hub")
		"church":enter_room("H04")
		"cooperate":
			if g.flags.get("cooperation_done",false):await ui.play_pages([{ "speaker":"赫兰","text":"军令已交给记录官。你救下的人都会记得凯尔。"}],"hub")
			else:
				var pages=g.campaign.scenes.D12.duplicate(true)
				pages.append({"speaker":"医者","text":"教堂留有一份泉液，可以救治一名濒死同伴。未用时会保留，每个人只能接受一次。"})
				pages.append({"speaker":"医者","text":"濒死者仍随队接受照护，暂时不能出阵。泉液只能修复活人的伤损，不能救回凯尔。"})
				await ui.play_pages(pages,"hub","cooperate")
		"fula","lena","beck","hervi":
			if g.party.has(key):await ui.play_pages([{ "speaker":g.characters[key].name_zh,"text":"我会与你同行。村里的人已经有人照顾。"}],"hub");return
			if key=="fula" and not g.flags.get("grain_shared",false):ui._notice("芙拉希望先把粮送回村庄");return
			if key=="hervi" and not g.flags.get("clinic_staffed",false):ui._notice("先请管理员接手诊所");return
			ui._open_menu("recruit",["邀请同行","暂不邀请"],["hub:recruit_"+key,"close"],Vector2(48,88))
		"lance":await ui.play_pages([{ "speaker":"兰斯","text":"赫兰让我带你们进城。右边是骑兵营，我们可以分路推进。"}],"hub")
		"shrine":
			var labels=[];var actions=[]
			for id in g.party:
				if not g.can_deploy(g.roster[id]):continue
				for option in ui.Progression.promotion_options(g.roster[id]):
					labels.append(str(g.roster[id].name_zh)+"→"+str(g.catalog.classes[str(int(option.class_id))].name_zh))
					actions.append("hub:promote_"+str(id)+"_"+str(int(option.class_id)))
			if labels.is_empty():ui._notice("尚无成员达到转职等级");return
			ui._open_menu("promotion",labels,actions,Vector2(24,72))
		"invite":await ui.play_pages([{ "speaker":"村民","text":"旧矿道里还有两队矿工。林村诊所的药车也被封路兵拦住了。两处支路都在这里分开。"},{"speaker":"村民","text":"它们可以先做，也可以之后回来；日返仪式举行前，请决定是否前往。"}],"hub")
		"tools":await ui.play_pages([{ "speaker":"矿工","text":"工具不是开路的钥匙。你即使没有找到工具，也能继续追查科兰。"}],"hub")
		"staff":g.flags.clinic_staffed=true;await ui.play_pages([{ "speaker":"管理员","text":"药车已经到诊所。我留下照顾病人，赫维可以与你们同行。"}],"hub")
		"treat":g.flags.workers_treated=true;await ui.play_pages([{ "speaker":"医者","text":"内院的伤者已经安置。粮与药交给我们，你去塔上确认仪式吧。"}],"hub")
		"ceremony":
			if g.flags.get("chapter1_complete",false):await ui.play_pages([{ "speaker":"赫兰","text":"日返已经完成。大家正为明日的庆典做准备。"}],"hub");return
			if not g.flags.get("workers_treated",false):ui._notice("先在内院安置获救的伤者");return
			if not g.flags.get("chapter1_complete",false) and (not g.stage_cleared(111) or not g.stage_cleared(112)):
				ui._open_menu("side_closure",["返回整备","举行日返"],["close","hub:ceremony_confirm"],Vector2(44,112));ui._notice("未完成支线将随仪式收束",6);return
			action("ceremony_confirm")
		"ceremony_confirm":
			var pages=[{"speaker":"赫兰","text":"凯尔的军令已交给记录官。我会公布他的事。日塔可以恢复仪式了。"},{"speaker":"乌库布·卡基","text":"我救下这片土地。日光将重返西大陆，愿你们记住庇护的恩情。"},{"speaker":"胡纳普","text":"先把内院的人都带出来。"}]
			if g.speaker_alive("达恩"):pages.append({"speaker":"达恩","text":"明日典礼后，一起回村里吧。凯尔的名字还没有刻完。"})
			pages.append({"speaker":"胡纳普","text":"好，明日之后。"});await ui.play_pages(pages,"hub","ceremony")
		"camp","guard","altar":
			var line="日塔正在准备仪式。"
			for o in objects:
				if o.action==key and not str(o.text).is_empty():line=o.text
			await ui.play_pages([{ "speaker":"村民" if key=="camp" else "教团守卫","text":line}],"hub")
		_:
			if key.begins_with("promote_"):
				var parts=key.split("_");var result=g.promote_unit(parts[1],int(parts[2]))
				ui._notice("转职完成" if result.get("valid",false) else "未满足转职条件");g.save_game();return
			if key.begins_with("recruit_"):
				var id=key.substr(8);g.recruit(id);await ui.play_pages([{ "speaker":g.characters[id].name_zh,"text":"我与你们同行。这里的居民仍由管理员照顾。"}],"hub")
	ui.game.save_game()

func finish_story(callback: String) -> void:
	if callback.begins_with("third_"):ThirdHub.finish(self,callback);return
	match callback:
		"prologue":ui.game.flags.prologue_done=true;ui.game.world_node=1;enter_room("H01")
		"grave":ui.game.flags.village_ready=true
		"cooperate":ui.game.flags.cooperation_done=true;ui.game.recruit("lance")
		"ceremony":ui.game.flags.chapter1_complete=true;ui.game.mode="chapter_end";ui.view="chapter_end"
		"east_departure":ui.game.flags.east_departure_ready=true
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
		ui.draw_texture(ui._tex(path),ORIGIN+Vector2(d.rect.position)*16,_east_environment_tint())
	for o in objects:
		var at=Vector2(o.position[0],o.position[1])*16+ORIGIN
		if o.sprite=="actor":
			var sp: Dictionary=ui.graphics.village_sprites.get(str(int(o.source)),ui.graphics.village_sprites["1"])
			if ui.has_method("_party_hub_sprite"):sp=ui.call("_party_hub_sprite",o,sp)
			ui._draw_frame(sp,int(sp.directions.down[0]),at-Vector2(sp.tile_origin[0],sp.tile_origin[1]))
		else:
			var tex=ui._tex(str(o.get("sprite_path","res://assets/battle_tiles/modules/"+str(o.sprite)+".png")));ui.draw_texture(tex,at-Vector2(0,tex.get_height()-16),Color.WHITE if o.sprite in ["sun_altar","lit_brazier","ritual_lamp","well"] else _east_environment_tint())
		if ui.game.hub_position+facing==Vector2i(o.position[0],o.position[1]):ui._draw_indicator("down",at+Vector2(4,-8))
	var source_id="2" if ui.game.route=="celica" else "1"
	var sp: Dictionary=ui.graphics.village_sprites[source_id]
	if ui.has_method("_personal_hub_sprite"):sp=ui.call("_personal_hub_sprite",sp)
	var direction="up" if facing.y<0 else "side" if facing.x!=0 else "down"
	if motion_left<=0.0:render_position=Vector2(ui.game.hub_position)*16
	var at=render_position+ORIGIN
	var step=(int(clock*60.0988)>>4)&1 if motion_left>0.0 else 0
	ui._draw_frame(sp,int(sp.directions[direction][step]),at-Vector2(sp.tile_origin[0],sp.tile_origin[1]),facing.x<0)
	ui._draw_indicator("down",ORIGIN+Vector2(6,8)*16+Vector2(4,-2))
	var text=hint
	for o in objects:
		if ui.game.hub_position+facing==Vector2i(o.position[0],o.position[1]):text="确认:"+str(o.name)
	ui._draw_hub_caption(title,text)

func _configure_east_room() -> void:
	east_data=chapter2_rooms[room].duplicate(true)
	title=str(east_data.title);hint=str(east_data.hint);objects=[];scenery=[]
	for raw in east_data.objects:
		var o: Dictionary=raw.duplicate(true)
		if o.action=="east_departure" and not _east_alive("carlo"):
			o.name="船长";o.source=5
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
	var guards={"H21":["east_departure_ready","先与卡洛确认船牌与出航"],"H22":["F21_confirmed","先向船长确认押送舰的灯线"],"H23":["F22_confirmed","先在安置处照顾全部伤者"],"H24":["F23_confirmed","先向渔村长者确认岸线"],"H25":["islanders_settled","先请留守骑士安置岛民"]}
	if room=="H27":ui._notice("先向广场前的守卫交涉");return false
	if guards.has(room) and not ui.game.flags.get(guards[room][0],false):ui._notice(guards[room][1]);return false
	return true

func _east_environment_tint() -> Color:
	var tint=east_data.get("environment_tint",[1.0,1.0,1.0])
	return Color(float(tint[0]),float(tint[1]),float(tint[2]))

func _draw_east_floor(atlas: Texture2D) -> void:
	var visible: Rect2=ui._visible_native_rect()
	var tint=_east_environment_tint()
	var background=str(east_data.get("biome_override","sea"))
	for y in range(floori((visible.position.y-ORIGIN.y)/16),ceili((visible.end.y-ORIGIN.y)/16)):
		for x in range(floori((visible.position.x-ORIGIN.x)/16),ceili((visible.end.x-ORIGIN.x)/16)):
			var variant=posmod((x*73856093)^(y*19349663),4)
			var id=int(ui.battle_pack.base[background][variant])
			ui.draw_texture_rect_region(atlas,Rect2(Vector2(x,y)*16+ORIGIN,Vector2(16,16)),Rect2(id%32*16,id/32*16,16,16),tint)
	for y in range(9):
		for x in range(14):
			var mark=str(east_data.floor[y])[x]
			if mark=="~":continue
			var material=str(east_materials.get(mark,"sand"))
			var variant=posmod((x*73856093)^(y*19349663)^((x+y*17)>>2),4)
			var id=int(ui.battle_pack.base[material][variant])
			ui.draw_texture_rect_region(atlas,Rect2(Vector2(x,y)*16+ORIGIN,Vector2(16,16)),Rect2(id%32*16,id/32*16,16,16),tint)
			if background=="sea" and mark not in ["=","c"]:
				var mask=_east_land_mask(Vector2i(x,y))
				if mask!=255:ui.draw_texture(_east_shore_overlay(atlas,mask),Vector2(x,y)*16+ORIGIN,tint)

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

func _east_action(key: String) -> void:
	var g=ui.game
	match key:
		"east_departure":
			if g.flags.get("east_departure_ready",false):
				await _east_pages(["卡洛：船已整备好了。从南面的跳板下去，我们去找押送舰。"] if _east_alive("carlo") else ["船长：航线已经记下。船团会沿着灯线继续走。"]);return
			await ui.play_pages(g.campaign.scenes.D21,"hub","east_departure")
		"east_mireille":await _east_pages(["米蕾：岸边还有失散的人。我们走了以后，学舍的医者会留下来。", "艾琳：药和干净的布留给他们。我们的船也要留出伤者的位置。"])
		"east_lisa":await _east_pages(["莉莎：残图只画到神幕外沿。完整那一张，母亲没有留在学舍。", "艾琳：先找那艘押送舰。也许还有认得她的船员。"])
		"east_chart_start":await _east_pages(["旁白：残图边缘写着薇娅的名字。两年前，她带着伤者出航，再也没有回来。", "艾琳：母亲教我读的灯线，现在还在海上。"])
		"sea_route":
			g.flags.F21_confirmed=true
			await _east_pages(["船长：押送舰必须经过前面的灯线。船体已经修补好，跳板也收妥了。", "艾琳：记下它的航向。先让伤者坐稳，再动身。"])
		"invite_s21":
			g.flags.S21_invited=true
			var who="米蕾" if _east_alive("mireille") else "艾琳"
			await _east_pages(["船员：西南方有条漂泊渔船。码头不准它靠岸，上面还有病人。",who+"：不能就这样走。让他们先到安全的停泊点。", "船长：这条支路可以现在去，也能之后返回。西渡古道前，请决定是否前往。"])
		"s21_report":
			if g.stage_cleared(211):await _east_pages(["地方医者：获救的人已经交给岸上的医者。备用停泊点和补给都登记好了，不必再冒险回去。"])
			else:await _east_pages(["地方医者：我留在这里照顾伤者。治疗要消耗施法者的生命，请让前排护住病人，不必让一个人承担全部救援。"])
		"prisoners_treat":
			var lines=[]
			lines.append("米蕾：放下武器的敌人也在流血。先把他们和船员一起抬进来。" if _east_alive("mireille") else "地方医者：囚舱的人已经接回来了。放下武器的敌人也需要包扎。")
			if _east_alive("lisa"):lines.append("莉莎：再耽搁下去，裴萨会把箱子送得更远。")
			lines.append("艾琳：先治伤。让船长记下去军港的路，我们不把伤者留在这艘船上。")
			g.flags.F22_confirmed=true
			await _east_pages(lines)
		"captives_route":await _east_pages(["引航者：裴萨留下了那只箱子，要送到潮狩军港。箱上的七羽日冠和港口的封条一样。", "艾琳：先到安全岸边。你愿意的时候，再把母亲那趟航行告诉我。"])
		"lord","roan","shia":
			if g.party.has(key):
				var lines={"lord":"洛德：船上的铰链还用得上。我会帮他们修好渡船。","roan":"罗恩：我认得军港外的岸线。村里的渔船得留一部分，不能全被我们带走。","shia":"希雅：留下的骑士够守航灯了。我与你同行，岛上也会继续有船。"}
				await _east_pages([lines[key]]);return
			if not g.flags.get("east_recruit_ready",{}).get(key,false) or bool(g.roster.get(key,{}).get("dead",false)):ui._notice("这位同伴未能获救");return
			if key=="lord" and not g.flags.get("F22_confirmed",false):ui._notice("先在安置处照顾获救伤者");return
			if key=="shia" and not g.flags.get("islanders_settled",false):ui._notice("先安置岛民，让留守骑士接手");return
			ui._open_menu("recruit",["邀请同行","暂不邀请"],["hub:east_recruit_"+key,"close"],Vector2(48,88))
		"reef_route":
			g.flags.F23_confirmed=true
			await _east_pages(["渔村长者：军港拿走了货船。经过海灯岛，就能看见军港外的岸线。", "渔村长者：黑昼已经持续太久，连岸上的魔物也不肯退。先让岛民留在营地。"])
		"invite_s22":
			g.flags.S22_invited=true
			if g.stage_cleared(212):
				await _east_pages(["渔村长者：海洞的遗物已经登记。送给家属的事情，我们会记住。"]);return
			var lines=["船员：东边碎石海洞里有人躲着。他带着失踪船员的遗物，一直不敢回来。"]
			lines.append("卡洛：他认得这块船牌。我去见他。" if _east_alive("carlo") else "艾琳：我会去看看。遗物该交回家属手里。")
			lines.append("船员：海洞可以之后再去。西渡古道后，船团就不能折返这里了。")
			await _east_pages(lines)
		"holy_sword":_east_claim_item("F23_holy_sword_taken",16,"圣剑")
		"holy_bow":_east_claim_item("F25_holy_bow_taken",21,"圣弓")
		"islanders_settle":
			var first=not g.flags.get("islanders_settled",false)
			g.flags.islanders_settled=true
			var report="留守骑士：伤者已经进屋，航灯和岛上的船都有人照看。军港的航线也已经确认。" if g.flags.get("islanders_survived",true) else "留守骑士：我们还在清点失踪者，会继续搜救。其他撤离的岛民已有安置处，航灯和留下的船由我们照看。"
			var lines=[report, "艾琳：留足撤离用的船。我们只带已经准备好的这一队。"]
			if first:
				lines.append("地方医者：灯屋还留有一份救治泉液，可以救治一名濒死同伴；每人只能接受一次，未用时会保留。")
				lines.append("地方医者：由我来主持救治。泉液只能修复活人的伤损，已经遇难的人无法救回。")
			await _east_pages(lines)
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
		"east_magic_info":await _east_pages(["学舍导师：个人法术随着训练学会。职业进阶保留已学法术和训练计数，不是从头学习。", "学舍导师：施法会消耗生命。请在部队整备查看法术与装备，先给施法者留出安全的位置。"])
		"resistance_spring":
			if g.flags.get("lighthouse_spring_used",false):ui._notice("抗性泉已经用尽，不会再次补充");return
			var labels=[];var actions=[]
			for id in g.party:
				if _east_alive(id):labels.append(str(g.roster[id].name_zh)+" 抗性+1");actions.append("hub:east_spring_"+str(id))
			ui._open_menu("east_spring",labels,actions,Vector2(40,72))
		"r05":await _east_relation()
		"chart_recover":
			if g.flags.get("sea_chart_collected",false):await _east_pages(["艾琳：航图和封航命令已经收好了。图上的旧石门，是通往西岸的路。"]);return
			await ui.play_pages(g.campaign.scenes.F25_MYTH,"hub","east_chart")
		"harbor_patients":
			g.flags.harbor_patients_treated=true
			await _east_pages([("米蕾" if _east_alive("mireille") else "地方医者")+"：撤离者都上船了。还有几个伤口要包扎，我们会在船上继续照顾。", "艾琳：母亲的航图拿回来了。剩下的路，我会把他们一起带出去。"])
		"ancient_departure":
			if not g.flags.get("sea_chart_collected",false):ui._notice("先面对神教箱，取回母亲航图");return
			if not g.flags.get("harbor_patients_treated",false):ui._notice("先在安置处确认撤离者已经上船");return
			if g.flags.get("east_departure_confirmed",false):await _east_pages(["船长：船团已准备沿古道西渡。你可以从南侧跳板返回地图。"]);return
			var pending=[]
			if not g.stage_cleared(211):pending.append("漂泊渔船")
			if not g.stage_cleared(212):pending.append("碎石海洞")
			if not pending.is_empty():
				await _east_pages(["船长：西渡后，我们暂时不能折返。尚未完成："+"、".join(pending)+"。可以先回去，准备好再来找我。"])
			ui._open_menu("east_closure",["继续整备","确认西渡"],["close","hub:east_sail_confirm"],Vector2(44,112))
		"east_sail_confirm":
			g.flags.east_departure_confirmed=true
			await _east_pages(["艾琳：航图、伤者和船都确认了。我们去西岸。", "船长：沿旧石门进入古道。海面的船由我们护航，你们走遗迹上的铺板。"])
		"east_finale":
			if g.flags.get("chapter2_complete",false):g.mode="chapter_end";ui.view="chapter_end";return
			if not g.stage_cleared(206):ui._notice("先护送船团通过断航古道");return
			await ui.play_pages(g.campaign.scenes.D26_ARRIVAL,"hub","east_finale")
		"arrival_captain":await _east_pages(["船长：至少这一队船抵达了西岸。伤者还在等靠岸的命令。", "艾琳：别把船开回去。我去广场见他们。"])
		"arrival_altar":await _east_pages(["旁白：传光台的七羽日冠，与军港神教箱的封印一模一样。"])
		_:
			if key.begins_with("east_recruit_"):
				var id=key.substr(13)
				if not g.flags.get("east_recruit_ready",{}).get(id,false) or bool(g.roster.get(id,{}).get("dead",false)):return
				g.recruit(id)
				var speech={"lord":"洛德：我能修船，也能挡住追兵。囚舱里的事，我会留下作证。","roan":"罗恩：军港拿走了我们的货船。我知道那里的岸线，让我带路。","shia":"希雅：留守的人够了。我与你去军港，但岛上的船不能全带走。"}
				await _east_pages([speech[id]])
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
	var g=ui.game
	if not _east_alive("carlo") or not _east_alive("shia"):
		await _east_pages(["卡洛：报酬到这里已经结清。船团还要西渡，我会先把这一程护送做完。"] if _east_alive("carlo") else ["旁白：船团正在清点下一程的物资。"]);return
	var promised=bool(g.flags.get("carlo_promise_completed",false))
	if promised and not g.flags.get("R05_promise_seen",false):
		g.flags.R05_promise_seen=true;g.flags.seen_R05=true
		await _east_pages(["希雅：军港的报酬已经结清。接下来的航路，你还会留下吗？","卡洛：海洞那个人和我一样，一直不敢回家属面前。我答应陪他把遗物送回去。","卡洛：这笔预支报酬先留给岛上修船。欠下的事，不能总让后面的人收拾。","希雅：那就先把岛民的船修好。我也不会把岛上的责任全交给别人。"])
	elif not g.flags.get("seen_R05",false):
		g.flags.seen_R05=true
		await _east_pages(["希雅：你收了钱，就能在下一个港口离开吗？","卡洛：以前我就是这么想的。那天有人来讨债，我提前下了薇娅的船。","希雅：我的岛民也在这些船上。我得知道护卫会不会走。","卡洛：先把这一路护送完。报酬到了，也不等于我没有别的事要做。"])
	else:await _east_pages(["希雅：岛上的船仍有人修。我会按约定去检查。","卡洛：我也会。船团还在等我们。"])

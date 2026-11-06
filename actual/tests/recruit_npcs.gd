extends SceneTree
const State=preload("res://core/game_state.gd")
const Npcs=preload("res://core/postbattle_npcs.gd")
const OUT="res://reports/recruit-npcs-20261025/"
const VICTORY="res://reports/full-playtest-20261023/ch1/cover-archer-20261025/cover-archer-20261025-S11-victory.json"
var checks=[]
var failures=[]
var shots=[]
var cache=""
var visual=false
var ui
var phone
var screen
var events=[]
var jingles=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func key(code:int):
	var event=InputEventKey.new();event.physical_keycode=code;event.pressed=true;ui._input(event)
	event=InputEventKey.new();event.physical_keycode=code;event.pressed=false;ui._input(event)
func choose(action:String):
	var at=ui.menu_actions.find(action);check(at>=0,"menu offers "+action)
	if at>=0:ui.menu_selected=at;key(KEY_Z)
func settle():
	for i in range(8):await process_frame
func finish_plot():
	for i in range(120):
		if ui.view=="plot":ui.dialogue_reveal=10000;key(KEY_Z)
		await process_frame
		if ui.view!="plot" and not ui.busy:return
	check(false,"dialogue finishes without blocking")
func frame(name:String,capture:bool=true):
	phone._sync_controls();ui.queue_redraw();phone.queue_redraw();await settle()
	if not visual:return
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),name+" text and buttons inside safe bounds: "+str(ui.layout_errors))
	if capture and not (OS.get_environment("DIALOGUE_REFRESH")=="1" and name=="01-battle-controls"):
		screen.get_texture().get_image().save_png(OUT+name+".png");shots.append(name+".png")
func object(action:String)->Dictionary:
	for item in ui.hub_controller.objects:
		if item.action==action:return item
	return {}
func inspect_dialogue(action:String,speaker:String,name:String):
	ui.hub_controller.action(action);await settle()
	check(ui.view=="plot" and str(ui.plot_pages[0].speaker)==speaker,action+" opens dialogue with its own speaker")
	ui.dialogue_reveal=10000;await frame(name)
	var face=ui._speaker_portrait(speaker)
	check(not face.is_empty() and str(face.path).contains("postbattle-npcs-20261025"),speaker+" uses its new civilian portrait")
	await finish_plot()
func domain():
	var g=State.new();g.new_game();g.save_path=cache+"domain.json"
	g.character_recruited.connect(func(id):events.append(id))
	g.recruit("hervi");g.recruit("no_such_character")
	check(events.is_empty(),"denied and unknown recruits emit no success signal")
	g.recruit("beck");g.recruit("beck");g.recruit("lance")
	check(events==["beck","lance"],"successful invitation and scripted join emit once per character")
	g.recruit("fula");g.roster.fula.dead=true;g.party.erase("fula");g.parties.alm=g.party.duplicate();events.clear();g.recruit("fula")
	check(events.is_empty(),"unavailable character emits no success signal")
	# Source art is only connected to peaceful hub identities; existing tactical art stays separate.
	g.mode="hub";g.hub_record="H08"
	var paths=[];var faces=[]
	for name in ["村民","村中老妇","老矿工","年轻矿工"]:
		var sprite=Npcs.hub(g,{"name":name});var face=Npcs.portrait(g,name)
		check(not sprite.is_empty() and ResourceLoader.exists(str(sprite.path)) and ResourceLoader.exists(str(face.path)),name+" resources load")
		check(int(sprite.frames)==1 and sprite.directions.down.size()==1 and int(sprite.directions.down[0])==0 and sprite.static_facing,"stationary "+name+" has only one front idle frame")
		paths.append(sprite.path);faces.append(face.path)
	check(paths.size()==4 and paths[0]!=paths[1] and paths[2]!=paths[3] and faces[0]!=faces[1] and faces[2]!=faces[3],"four civilian identities have distinct bodies and portraits")
	g.hub_record="H09"
	check(Npcs.profile(g,"运药员")=="village_man" and Npcs.profile(g,"管理员")=="village_elder_woman","peaceful clinic staff use civilian identities rather than military placeholders")
	g.mode="battle"
	check(Npcs.hub(g,{"name":"村民"}).is_empty() and Npcs.portrait(g,"矿工").is_empty(),"hub identities do not override battlefield units or dialogue")
	g.mode="hub";g.hub_record="H08"
	var old=[{"speaker":"矿工","text":"工具不是开路的钥匙。你即使没有找到工具，也能继续追查科兰。"}]
	var revised=Npcs.refresh_saved_dialogue(g,old)
	check(revised[0].speaker=="年轻矿工" and not revised[0].text.contains("钥匙") and old[0].speaker=="矿工","old paused mine dialogue refreshes without mutating unrelated source pages")
	g.mode="battle";check(Npcs.refresh_saved_dialogue(g,old)==old,"saved battlefield dialogue is untouched")
func load_victory():
	ui.audio.stop_all();ui.audio.set_music_enabled(false)
	DirAccess.copy_absolute(ProjectSettings.globalize_path(VICTORY),cache+"victory.json")
	ui.game.save_path=cache+"victory.json";check(ui.game.load_game(),"genuine 15-turn S11 victory checkpoint loads in isolated storage")
	ui.game.flags.erase("active_plot");ui.plot_finished=true;ui.busy=false;ui._clear_menu();ui.notice_time=0
	ui.hub_controller.enter_room("H08",false,false);await settle()
func presentation():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=cache+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=4;ui.audio.set_music_enabled(false);ui.audio.set_sfx_enabled(false)
	ui.game.new_game();ui.game.save_path=cache+"ui.json";ui.game.world_node=int(ui.game.stages[111].node);ui.game.start_battle(111);ui.game.story_events.clear()
	ui.view="battle";ui.ui_mode="action";ui.busy=false;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
	var actor=ui.game.find_unit("hunapu");actor.position=[10,16];ui.game.find_unit("daan").position=[11,16];ui.game.find_unit("daan").acted=true;ui.game.find_unit("S11_e1").position=[10,15];ui.game.selected_id="hunapu";ui.game.cursor=Vector2i(10,16);ui._focus_battle(ui.game.cursor,true);ui._unit_action_menu()
	check(ui.menu_actions.has("attack") and ui.menu_actions.find("cover:choose")==ui.menu_actions.find("attack")+1,"attack is immediately above cover when both are available")
	await frame("01-battle-controls")
	var order=[]
	for button in phone.buttons:
		if int(button.key) not in phone.DIRECTION_KEYS:order.append(int(button.key))
	check(order==[KEY_S,KEY_E,KEY_Z,KEY_X,KEY_TAB],"battle right rail is menu, switch ally, confirm, back, status")
	ui._clear_menu();await load_victory()
	check(not object("beck").is_empty() and object("mine_survivor").is_empty(),"before invitation Beck remains available in the cleared mine hub")
	ui.hub_controller.action("beck");choose("close");await settle()
	check(not ui.game.party.has("beck") and not object("beck").is_empty(),"declining invitation keeps Beck on hub map")
	ui.audio.set_music_enabled(true);ui.audio.play_music("village");await create_timer(.8).timeout
	ui.audio.jingle_started.connect(func(id):jingles.append(id))
	var music_before=ui.audio._music_key;var pos_before=ui.audio._music_player.get_playback_position()
	ui.hub_controller.action("beck");choose("hub:recruit_beck");await settle()
	check(ui.game.party.has("beck") and object("beck").is_empty() and not object("mine_survivor").is_empty(),"successful Beck invitation immediately replaces him with rescued foreman")
	check(jingles==["rm_jingle_recruit"] and ui.audio._jingle_active and ui.audio._music_player.stream_paused,"success plays the dedicated cue once and pauses hub BGM")
	check(absf(ui.audio._jingle_player.stream.get_length()-2.0)<.001 and not ui.audio._jingle_player.stream.loop,"recruitment cue is exactly two seconds and nonlooping")
	await create_timer(2.3).timeout
	check(not ui.audio._jingle_active and not ui.audio._music_player.stream_paused and ui.audio._music_key==music_before and ui.audio._music_player.get_playback_position()>=pos_before,"after cue ends, previous hub music resumes from saved playback position")
	await finish_plot();ui.audio.set_music_enabled(false)
	var before_jingles=jingles.size();ui.game.recruit("beck");await settle();check(jingles.size()==before_jingles,"repeated invitation cannot replay recruitment success cue")
	ui.game.recruit("fula");await settle();check(ui.game.party.has("fula") and jingles.size()==before_jingles and not ui.audio._jingle_active,"successful recruitment respects muted music setting")
	check(ui.game.save_game(),"joined party and rebuilt hub can be saved")
	check(ui.game.load_game(),"joined party checkpoint reloads")
	ui.hub_controller.enter_room("H08",true,false);await settle()
	check(ui.game.party.has("beck") and object("beck").is_empty() and not object("mine_apprentice").is_empty(),"reloading keeps Beck in party and both miners in postbattle scene")
	await inspect_dialogue("mine_survivor","老矿工","04-mine-foreman")
	await inspect_dialogue("mine_apprentice","年轻矿工","05-young-miner")
	ui.game.flags.tools_reward=true;ui.hub_controller.action("tools");await settle();check(ui.plot_pages[0].text.contains("找回来了"),"recovered tools use persistent reward flag on revisit");await finish_plot()
	ui.game.flags.tools_reward=false;ui.hub_controller.action("tools");await settle();check(ui.plot_pages[0].text.contains("落在洞里") and not ui.plot_pages[0].text.contains("继续追查"),"optional missing tools yield personal testimony without system language");await finish_plot()
	ui.hub_controller.enter_room("H07",false,false);await settle()
	await inspect_dialogue("invite","村民","02-village-man")
	await inspect_dialogue("camp","村中老妇","03-village-elder")
	ui.hub_controller.action("invite");await settle();check(ui.plot_pages[0].text.contains("回来了"),"village testimony acknowledges completed mine rescue");await finish_plot()
	ui.game.cleared_stages.erase(111);ui.game.cleared_stages.erase(112);ui.hub_controller.action("invite");await settle();check(ui.plot_pages[0].text.contains("困在里面"),"before rescue villager describes people still trapped");await finish_plot()
	ui.game.cleared_stages.append(112);ui.hub_controller.action("invite");await settle();check(ui.plot_pages.any(func(p):return p.text.contains("药已经送到诊所")),"village testimony acknowledges delivered medicine");await finish_plot()
	# Backward-compatible paused dialogue, not a new event or reward.
	ui.hub_controller.enter_room("H08",true,false);ui.game.flags.active_plot={"pages":[{"speaker":"矿工","text":"工具不是开路的钥匙。你即使没有找到工具，也能继续追查科兰。"}],"index":0,"return":"hub","callback":""};ui._resume_plot()
	check(ui.plot_pages[0].speaker=="年轻矿工" and not ui.plot_pages[0].text.contains("钥匙"),"resuming an old paused mine page shows the corrected civilian line");await finish_plot()
	await load_victory();ui.game.flags.unrecruitable_beck=true;ui.game.roster.beck=ui.game._initial_character("beck");ui.game.roster.beck.dead=true;ui.game.find_unit("beck").hp=0;ui.hub_controller.enter_room("H08",true,false)
	check(object("beck").is_empty() and not object("mine_survivor").is_empty(),"unavailable Beck still leaves a nonblocking miner scene")
	ui.hub_controller.action("mine_survivor");await settle();check(ui.plot_pages.any(func(p):return p.text.contains("没能回来")),"unavailable Beck variant does not falsely say he joined");await finish_plot()
	ui.audio.stop_all();await create_timer(.12).timeout;phone.queue_free();await process_frame;screen.queue_free();await process_frame
func run():
	cache="/private/tmp/recruit-npcs-"+str(Time.get_ticks_usec())+"/";DirAccess.make_dir_recursive_absolute(cache+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT));visual=DisplayServer.get_name()!="headless" and OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")=="1"
	domain();await presentation()
	var result_file="dialogue-checks.json" if OS.get_environment("DIALOGUE_REFRESH")=="1" else "visual-checks.json" if visual else "checks.json"
	var f=FileAccess.open(OUT+result_file,FileAccess.WRITE);f.store_string(JSON.stringify({"passed":failures.is_empty(),"checks":checks,"failures":failures,"screenshots":shots,"device_updated":false},"  "));f.close()
	print("RECRUIT_NPCS ",checks.size()," checks ",failures.size()," failures");quit(0 if failures.is_empty() else 1)

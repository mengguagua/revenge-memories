extends SceneTree
const State=preload("res://core/game_state.gd")
const OUT="res://reports/d00-prologue-20261026/"
const CACHE="/private/tmp/revenge-d00-prologue-20261026/"
var checks=[]
var errors=[]
var shots=[]
var checkpoints={}
var sounds=[]
var seen=[]
var screen
var phone
var ui
var rendered=false
var completed=false
var record_checkpoints=true
var checkpoint_name=""
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)
func key(code:int):
	for pressed in [true,false]:
		var event=InputEventKey.new();event.physical_keycode=code;event.pressed=pressed;ui._input(event)
func same(a,b):return JSON.parse_string(JSON.stringify(a))==JSON.parse_string(JSON.stringify(b))
func on_sound(cue:String):sounds.append(cue)
func checkpoint(label:String):
	if not record_checkpoints or checkpoints.has(label):return
	check(ui.game.save_game(),label+" has a valid ordinary hub checkpoint")
	var path=CACHE+label+".json";var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(FileAccess.get_file_as_string(ui.game.save_path));file.close();checkpoints[label]=path
	var loaded=State.new();loaded.save_path=path
	check(loaded.load_game() and loaded.mode=="hub" and loaded.hub_record=="P00",label+" checkpoint loads without a new save mode")
func frame(label:String,save:bool=true):
	if ui.view=="plot":ui.dialogue_reveal=999
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw()
	for n in range(2):await process_frame
	if not rendered:return
	await RenderingServer.frame_post_draw
	check(ui.layout_errors.is_empty() and phone.layout_errors.is_empty(),label+" runtime content and touch safety")
	if ui.view=="plot":
		var a=ui.plot_layout_audit;var safe:Rect2=a.panel.grow(-8)
		for t in ui.text_checks:check(safe.encloses(t.bounds),label+" actual glyphs clear of frame")
		if a.has_portrait:check(not a.portrait.intersects(a.text),label+" face and text separated")
	if save:screen.get_texture().get_image().save_png(OUT+label+".png");shots.append(label+".png")
func setup():
	screen=SubViewport.new();screen.size=Vector2i(2556,1179);screen.render_target_update_mode=SubViewport.UPDATE_ALWAYS if rendered else SubViewport.UPDATE_DISABLED;root.add_child(screen)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(177,0,2202,1116);phone.journal_directory_override=CACHE+"slots";screen.add_child(phone);await process_frame
	ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);ui.instant_mode=true;ui.elapsed=7;ui.audio.sfx_played.connect(on_sound)
func begin(entry:String):
	ui.game.new_game();ui.game.save_path=CACHE+"working.json";ui.prologue_scene.active=false;ui.prologue_scene.advance_pending=false;ui.plot_finished=true
	ui.hub_controller.enter_room("P00");ui.busy=false
	var object=ui.hub_controller.objects.filter(func(o):return o.name==entry)[0]
	ui.game.hub_position=Vector2i(object.position[0],object.position[1])+Vector2i.DOWN;ui.hub_controller.render_position=Vector2(ui.game.hub_position)*16;ui.hub_controller.facing=Vector2i.UP
	key(KEY_Z);check(ui.prologue_scene.active and ui.view=="prologue_scene" and int(ui.prologue_scene.state.step)==0,entry+" actual facing-confirm enters the same D00 sequence")
func drive(capture:bool=false):
	var guard=0;var photographed={}
	while ui.prologue_scene.active and not ui.prologue_scene.reprise_mode and guard<180:
		guard+=1
		var scene=ui.prologue_scene;var step=int(scene.state.step);var shot=scene.spec.steps[step];var id=str(shot.id)
		if ui.view=="plot":
			var page=ui.plot_pages[ui.plot_index]
			seen.append({"speaker":str(page.speaker),"text":str(page.text).replace("\n","")})
			check(str(page.speaker)!="旁白" and not str(page.text).contains("演出说明"),id+" contains only authored character dialogue")
			checkpoint(id+"-page-"+str(ui.plot_index))
			if capture:await frame(id+"-page-"+str(ui.plot_index))
			ui.dialogue_reveal=999;key(KEY_Z);await process_frame
			if scene.advance_pending:scene.process(0)
			continue
		if scene.advance_pending:scene.process(0);await process_frame;continue
		check(ui.menu_items.is_empty(),id+" has no gameplay menu during the shot")
		var pos=ui.game.hub_position;var before_time=float(scene.state.time)
		for code in [KEY_UP,KEY_DOWN,KEY_LEFT,KEY_RIGHT,KEY_S,KEY_TAB,KEY_X]:key(code)
		check(ui.game.hub_position==pos and ui.menu_items.is_empty() and int(scene.state.step)==step,id+" blocks movement/status/system/back input")
		key(KEY_Z)
		if str(shot.kind)!="flashback":check(int(scene.state.step)==step and scene.state.time==before_time,id+" confirm cannot skip its action")
		if not scene.active:break
		if str(shot.kind)=="cast_block":
			for sample in [0.4,1.1,1.65,2.1]:
				scene.process(maxf(0,sample-float(scene.state.time)));checkpoint("cast-"+str(sample))
				if capture:await frame("cast-"+str(sample))
				if rendered and capture and sample==1.65:check(scene.audit.impact and scene.audit.hero_pose==1 and scene.audit.spell_target=="herlan","Hunapu physically intercepts Eileen's single spell before Herlan")
		elif str(shot.kind)=="projection":
			for sample in [1.7,3.5,4.5,5.7]:
				scene.process(maxf(0,sample-float(scene.state.time)));checkpoint("projection-"+str(sample))
				if capture:await frame("projection-"+str(sample))
				if rendered and capture:check(not scene.audit.dialogue_visible,"projection cutaway hides the dialogue box")
		else:
			scene.process(minf(.9,float(shot.get("duration",1))*.6));checkpoint(id)
			if capture:await frame(id)
			if str(shot.kind)=="flashback":
				check(not ui.game.flags.has("active_plot"),"six-month subtitle is independent from narration/dialogue pages")
				if rendered:check(scene.audit.kind=="flashback" and not scene.audit.dialogue_visible,"flashback is a centered standalone black screen")
		if scene.active:scene.process(float(shot.get("duration",1))+0.1);await process_frame
	check(guard<180 and not ui.prologue_scene.active and ui.game.hub_record=="H01" and ui.game.flags.get("prologue_done",false),"D00 ends once in the half-year-earlier snow village")
	await process_frame
func authored_dialogue(section:String) -> Array:
	var pages=[]
	for line in section.split("\n"):
		if not line.begins_with("> "):continue
		var parts=line.trim_prefix("> ").split("：",true,1)
		pages.append({"speaker":parts[0],"text":parts[1]})
	return pages

func data_checks():
	var g=State.new();var expected=State.read_json("res://reports/dialogue-sync-20261026/expected-dialogue.json")
	var script_path=ProjectSettings.globalize_path("res://").path_join("../docs2/完整台词汇总.md")
	var script=FileAccess.get_file_as_string(script_path)
	var intro=script.get_slice('<a id="opening-narration"></a>',1).get_slice('<a id="prologue"></a>',0)
	var d00=script.get_slice('<a id="d00-prologue"></a>',1).get_slice('<a id="chapter-1"></a>',0)
	check(g.campaign.scenes.D00==authored_dialogue(d00),"all twelve D00 lines exactly match the approved script")
	check(g.campaign.scenes.D31[0].text==expected.D31_opening,"D31 narration returns to the exact hand/eye-line/evacuation stop")
	check(State.read_json("res://data/story_intro.json").scenes.map(func(entry):return entry.text)==authored_dialogue(intro).map(func(page):return page.text),"all four opening paragraphs exactly match the approved script")
	var safe={"version":1,"step":0,"time":.5,"clock":.5,"sounds":{}}
	var validation=preload("res://core/prologue_checkpoint.gd")
	check(validation.STEP_COUNT==State.read_json("res://data/prologue_scene.json").steps.size() and validation.valid(safe),"checkpoint contract matches the eleven authored shots")
	for pair in [["step",-1],["step",11],["step",1.5],["step",[]],["time","bad"],["time",-1],["time",INF],["clock",{}],["sounds",[]],["sounds",{"block":"yes"}],["sounds",{"unknown":true}],["version",{}]]:
		var damaged=safe.duplicate(true);damaged[pair[0]]=pair[1]
		check(not validation.valid(damaged),"reject malformed shot checkpoint "+str(pair))
	var manifest=State.read_json("res://assets/prologue-d00-20261026/manifest.json")
	for asset in manifest.assets:
		check(ResourceLoader.exists("res://"+str(asset.path).trim_prefix("actual/")),"runtime art loads "+str(asset.path))
		check(int(asset.bytes)<(200000 if str(asset.path).ends_with("webp") else 50000),"optimized production art reference size "+str(asset.path))
func run():
	rendered=DisplayServer.get_name()!="headless"
	DirAccess.make_dir_recursive_absolute(CACHE+"slots");DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	data_checks();await setup()
	ui.game.new_game();ui.game.save_path=CACHE+"working.json";ui.hub_controller.enter_room("P00");await frame("prepared-plaza")
	check(ui.hub_controller.objects.filter(func(o):return o.action=="prologue").size()==2,"two named interaction entrances and no second narrated arrest")
	var roster=ui.game.roster.duplicate(true);var party=ui.game.party.duplicate();begin("艾琳");seen=[];sounds=[];await drive(true)
	check(same(ui.game.roster,roster) and ui.game.party==party and ui.game.units.is_empty(),"story spell alters no HP, items, members or combat units")
	check(seen==ui.game.campaign.scenes.D00,"actual displayed dialogue follows all twelve revised lines once")
	check(sounds.count("rm_sfx_06")==1 and sounds.count("rm_sfx_03")==1,"one cast cue and one blocking impact cue")
	check(not ui.game.flags.has("prologue_scene") and not ui.game.flags.has("active_plot") and not ui.game.flags.get("village_ready",false),"D00 clears its checkpoint and does not complete the village's later grave event")
	record_checkpoints=false
	begin("赫兰");seen=[];await drive();check(seen==ui.game.campaign.scenes.D00,"Herlan entry has identical dialogue and action sequence")
	for label in ["recognition-page-1","cast-1.65","projection-3.5","six_months_earlier"]:
		var resumed=State.new();resumed.save_path=checkpoints[label];check(resumed.load_game(),label+" real checkpoint reload")
		ui.game=resumed;ui._resume_journey();await process_frame
		check(ui.prologue_scene.active,label+" actual UI resumes the scene")
		if label=="cast-1.65":
			sounds=[];ui.prologue_scene.process(.25);check(sounds.is_empty(),"resuming after impact cannot replay cast or block sound")
		await drive()
	# Retired linear D00 pages are migrated without granting progress or rewards.
	var legacy=State.new();legacy.new_game();legacy.save_path=CACHE+"legacy.json"
	legacy.flags.active_plot={"pages":[{"speaker":"赫兰","text":"带她上来。有人说，她拆了传光台的封印。"}],"index":0,"return":"hub","callback":"prologue"}
	check(legacy.save_game(),"legacy D00 checkpoint fixture is valid")
	ui.game=legacy;ui._resume_journey();check(ui.prologue_scene.active and int(ui.prologue_scene.state.step)==0 and not legacy.flags.has("active_plot"),"retired linear D00 restarts the new recognition shot safely")
	await drive()
	# Third chapter enters through the existing chapter transition, not fake membership.
	ui.game.new_game();ui.game.save_path=CACHE+"third.json";ui.game.chapter=2;ui.game.flags.chapter2_complete=true;ui.game.cleared_stages=[206]
	ui.game.party=["eileen"]
	ui.game.roster.eileen=ui.game._initial_character("eileen");ui.game.parties.celica=["eileen"]
	check(ui.game.begin_chapter_three(),"normal third-chapter transition prepares reunion")
	ui.hub_controller.enter_room("H30");ui.hub_controller.action("third_prologue");await process_frame;await frame("D31-same-instant")
	check(ui.prologue_scene.reprise_mode and ui.view=="plot" and ui.plot_pages[0].text.replace("\n","")==ui.game.campaign.scenes.D31[0].text,"D31 uses revised opening over the same held tableau")
	if rendered:check(ui.prologue_scene.audit.hero_pose==3 and ui.prologue_scene.audit.eileen_pose==3,"D31 restores the same open hand and glance beyond it")
	var guard=0
	while ui.view=="plot" and guard<40:ui.dialogue_reveal=999;key(KEY_Z);guard+=1;await process_frame
	check(ui.game.flags.get("D31_done",false) and not ui.prologue_scene.active and ui.view=="world","D31 ends in existing third-chapter world flow")
	# Shorter phone fixture checks the same production staging and subtitle geometry.
	if rendered:
		screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout()
		begin("艾琳");ui.prologue_scene.state.step=8;ui.prologue_scene.state.time=1;await frame("compact-held")
		ui.prologue_scene.state.step=10;ui.prologue_scene.state.time=1.4;await frame("compact-flashback")
		await drive()
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
	completed=true
	var report={"checks":checks.size(),"errors":errors,"labels":checks,"screenshots":shots,"rendered":rendered,"checkpoints":checkpoints,"complete":completed,"scope":"D00 data, two real interaction entries, complete directed story playback, interruption/resume, legacy D00 migration, D31 continuation and phone glyph/touch safety. Temporary journals only; no battles played or iPhone update."}
	var file=FileAccess.open(OUT+("visual.json" if rendered else "logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("D00_PROLOGUE checks=",checks.size()," errors=",errors);quit(0 if errors.is_empty() and completed else 1)

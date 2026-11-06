extends "res://tests/d00_prologue.gd"
## Focused follow-up: real map scale, extra poses, existing enemy guard identity.
func run():
	rendered=DisplayServer.get_name()!="headless";record_checkpoints=false
	DirAccess.make_dir_recursive_absolute(CACHE+"slots");await setup()
	ui.game.new_game();ui.game.save_path=CACHE+"small-cast.json";ui.hub_controller.enter_room("P00")
	var scene=ui.prologue_scene
	var manifest=State.read_json("res://assets/prologue-small-20261026/manifest.json")
	for asset in manifest.assets:
		var id=str(asset.actor);var art:Dictionary=scene.cast_art[id]
		var image=ui._tex(art.path).get_image();var poses={}
		check(int(art.native_density)==4 and int(art.frame_size[0])==128 and int(art.frame_size[1])==96 and int(art.anchor[0])==16 and int(art.anchor[1])==24,id+" keeps the fixed 4x map scale and foot anchor")
		check(int(asset.bytes)<20000,id+" complete eight-frame atlas under 20KB")
		for n in range(8):
			var cell=image.get_region(Rect2i(n%4*128,floori(n/4.0)*96,128,96));var bounds=cell.get_used_rect()
			check(bounds.size.y<=64 and bounds.size.y>=60 and bounds.end.y==96,id+" frame "+str(n)+" body stays 15–16px with aligned feet")
			check(bounds.position.x>0 and bounds.end.x<128 and bounds.position.y>=24,id+" frame "+str(n)+" full silhouette has clear cell padding")
			if id=="herlan":check(bounds.size.x<=37,"Herlan frame "+str(n)+" uses the regenerated narrow silhouette")
			poses[hash(cell.get_data())]=true
		check(poses.size()==8,id+" has eight distinct drawn frames")
	check(str(scene.guard_art.reviewed_profile)=="professions-class-22-enemy-maps-tactical-idle","all three guards reuse the existing blue-purple enemy bastion guardian")
	check(str(scene.guard_walk_art.reviewed_profile)=="professions-class-22-enemy-maps-tactical-walk","released guards use the same profession's existing walk art")
	await frame("prepared-plaza")
	if rendered:check(scene.audit.guard_count==3 and scene.audit.map_body_height==16,"free plaza keeps small cast and three guardians")
	begin("艾琳");scene.state.step=3;scene.state.time=0;ui.view="prologue_scene"
	var hero_frames={};var eileen_frames={};var herlan_frames={};var last_hero=Vector2(128,100)
	for n in range(34):
		scene.state.time=n*.08
		await frame("small-motion-%02d"%n,false)
		# Audit is produced by the real renderer even without visible windows.
		if not rendered:continue
		var a=scene.audit;hero_frames[a.hero_frame]=true;eileen_frames[a.eileen_frame]=true;herlan_frames[a.herlan_frame]=true
		check(a.guard_count==3 and a.map_body_height==16,"cast tick "+str(n)+" retains three guards and small bodies")
		check(a.hero.distance_to(last_hero)<7,"cast tick "+str(n)+" moves the blocker continuously")
		last_hero=a.hero
		if a.impact:check(a.spell_at.distance_to(a.hero+Vector2(-6,-9))<.1 and a.hero_frame in [3,4],"impact meets the small hero's raised hands")
	if rendered:
		check(hero_frames.size()>=6 and eileen_frames.size()==8 and herlan_frames.size()>=7,"cast plays multiple actual drawn inbetweens for all three characters")
		for sample in [.12,.32,.56,.78,1.1,1.4,1.65,1.9,2.2,2.55]:
			scene.state.time=sample;await frame("small-cast-"+str(sample))
		for sample in [.4,1.1,1.65,2.1]:
			scene.state.time=sample;await frame("cast-"+str(sample))
		for pair in [[7,"hand_and_look"],[8,"hold_same_instant"]]:
			scene.state.step=pair[0];scene.state.time=1.1;await frame(pair[1])
			check(scene.islands_audit.is_empty() and scene.audit.hero_frame==7,"reach/hold retains small body without the removed inset")
		scene.resume_reprise();ui.play_pages([ui.game.campaign.scenes.D31[0]],"hub");await frame("D31-same-instant")
		check(scene.audit.hero_frame==7 and scene.audit.eileen_frame==7 and scene.audit.guard_count==3,"D31 reprises the same small cast and three guardians")
		ui.plot_finished=true;ui.view="prologue_scene";scene.reprise_mode=false;scene.state.step=8;scene.state.time=1.1
		screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout();await frame("compact-held")
	ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
	var report={"checks":checks.size(),"errors":errors,"labels":checks,"screenshots":shots,"rendered":rendered,"scope":"Small cast in P00/D00/D31, 24 real drawn poses, actual image bounds and feet, original blue-purple class-22 enemy guard idle/walk, projectile meets hands, continuous interception movement and two phone layouts. No iPhone install/update."}
	var file=FileAccess.open(OUT+("small-cast.json" if rendered else "small-cast-logic.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("D00_SMALL_CAST checks=",checks.size()," errors=",errors);quit(0 if errors.is_empty() else 1)

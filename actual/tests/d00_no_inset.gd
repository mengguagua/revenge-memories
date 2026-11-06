extends "res://tests/d00_prologue.gd"
## Small visual follow-up: only the removed inset and retained full cutaway.
func dismiss():
	while ui.view=="plot":ui.dialogue_reveal=999;key(KEY_Z);await process_frame
func run():
	rendered=true;record_checkpoints=false
	DirAccess.make_dir_recursive_absolute(CACHE+"slots");await setup()
	ui.game.new_game();ui.game.save_path=CACHE+"no-inset.json";ui.hub_controller.enter_room("P00");ui.prologue_scene.start()
	var scene=ui.prologue_scene
	for pair in [[6,"where_and_stop"],[7,"hand_and_look"],[8,"hold_same_instant"],[9,"fade_out"]]:
		scene.state.step=pair[0];scene.state.time=.6;scene.state.clock=26.0;ui.view="prologue_scene"
		if int(pair[0])==6:
			ui.play_pages(ui.game.campaign.scenes.D00.slice(9,12),"hub")
			while ui.view=="plot":
				await frame(str(pair[1])+"-page-"+str(ui.plot_index))
				check(scene.islands_audit.is_empty(),"no island inset in later plaza dialogue "+str(ui.plot_index))
				ui.dialogue_reveal=999;key(KEY_Z);await process_frame
		else:
			await frame(str(pair[1]));check(scene.islands_audit.is_empty(),"no island inset in "+str(pair[1]))
	scene.resume_reprise();ui.play_pages([ui.game.campaign.scenes.D31[0]],"hub");await frame("D31-same-instant")
	check(scene.islands_audit.is_empty() and scene.audit.hero_pose==3 and scene.audit.eileen_pose==3,"D31 preserves the held gesture without a corner inset")
	await dismiss();scene.reprise_mode=false;scene.active=true
	for sample in [1.7,3.5]:
		scene.state={"version":1,"step":5,"time":sample,"clock":20+sample,"sounds":{}}
		ui.view="prologue_scene";await frame("projection-"+str(sample))
		check(not scene.islands_audit.is_empty(),"full island cutaway still shows animated evacuation "+str(sample))
	screen.size=Vector2i(1334,750);phone.safe_area_override=Rect2(0,0,1334,750);phone._layout()
	scene.state.step=8;scene.state.time=1;ui.view="prologue_scene";await frame("compact-held")
	check(scene.islands_audit.is_empty(),"compact phone held shot has no island inset")
	scene.active=false;ui.audio.stop_all();screen.queue_free();await process_frame;await process_frame
	var report={"checks":checks.size(),"errors":errors,"labels":checks,"screenshots":shots,"scope":"Small follow-up only: later plaza dialogue, reach, held/fade, D31, compact phone and retained full island cutaway. Background engine rendering, no iPhone capture/update."}
	var file=FileAccess.open(OUT+"no-inset.json",FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
	print("D00_NO_INSET checks=",checks.size()," errors=",errors);quit(0 if errors.is_empty() else 1)

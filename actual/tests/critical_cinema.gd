extends SceneTree
## Real native contact path and cinematic player. Fixtures use temporary journals only.
const Cinema=preload("res://core/critical_cinema.gd")
class ObservedGame extends "res://core/game_state.gd":
	var strike_commits=0
	func commit_strike(value:Dictionary)->void:
		strike_commits+=1
		super.commit_strike(value)
	func random_bounded(_upper:int)->int:return 0
var ui
var vp
var checks=[]
var errors=[]
var samples=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:errors.append(label);push_error(label)

func cutin_fits(spec:Dictionary)->bool:
	var packed := FileAccess.get_file_as_bytes(str(spec.program))
	var scene: Dictionary = JSON.parse_string(packed.decompress_dynamic(32*1024*1024,FileAccess.COMPRESSION_GZIP).get_string_from_utf8())
	var images: Array = Cinema.data().images
	var sampled := 0
	for tick in range(scene.frames.size()):
		var glyphs: Array = []
		var portrait_edge := Cinema.FIELD.end.x
		for op in scene.frames[tick]:
			if int(op[0])!=1:continue
			var image: Dictionary = images[int(op[1])]
			var source := str(image.source)
			if "portraits-" in source or "-cutins-" in source:
				portrait_edge = minf(portrait_edge,Cinema.FIELD.end.x-float(op[2])-float(op[4]))
			elif source.begins_with("Cinematic label:") and source!="Cinematic label: 必 杀" and float(op[3])>=Cinema.FIELD.position.y and float(op[3])<Cinema.FIELD.end.y:
				glyphs.append([float(op[3]),float(image.width),float(image.height)])
		for subframe in [.01,.5,.99]:
			var boxes: Array[Rect2] = []
			for glyph in glyphs:
				var pos := Cinema.cutin_text_layout(float(tick)+subframe,float(glyph[1]))
				if pos.y<=0.0:continue
				sampled += 1
				var box := Rect2(pos.x,glyph[0],glyph[1],glyph[2])
				if not Cinema.FIELD.grow(-24.0).encloses(box) or box.end.x>=portrait_edge:return false
				if pos.y>=.15 and portrait_edge-box.end.x<24.0:return false
				for previous in boxes:
					if previous.grow(4.0).intersects(box):return false
				boxes.append(box)
	return sampled>0

func fixture(hero:String,advanced:bool,weapon:int,dead:bool=false)->Dictionary:
	ui.battle_animation.reset();ui.game.new_game();ui.game.stage_id=101
	ui.game.battle_data=ui.game.stages[101].duplicate(true);ui.game.mode="battle"
	ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
	var actor=ui.game.characters[hero].duplicate(true);actor.side="player";actor.position=[4,4];actor.hp=100;actor.max_hp=100;actor.acted=false;actor.no_experience=true
	if advanced:ui.game.HeroProfessions.apply(actor)
	var target=ui.game.characters.otto.duplicate(true);target.id="critical_test_target";target.side="enemy";target.class_id=6;target.character_id=99;target.position=[5,4];target.name_zh="实际目标";target.hp=1 if dead else 30;target.max_hp=30;target.item_id=0;target.no_experience=true
	ui.game.units=[actor,target];ui.combat={"attacker":actor.id,"defender":target.id,"distance":1,"initiative_side":"player"};ui.view="combat";ui.busy=true
	ui.combat_hp={actor.id:actor.hp,target.id:target.hp};ui.combat_poses.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.combat_message=""
	var cost=2 if weapon>=23 else 0
	return {"attacker":actor.id,"defender":target.id,"weapon_index":weapon,"distance":1,"critical":true,"hit":true,"damage":1 if dead else 7,"hp_before":target.hp,"hp_after":0 if dead else 23,"source_hp_before":actor.hp,"source_hp_after":actor.hp-cost,"hp_cost":cost}
func run():
	vp=SubViewport.new();vp.size=Vector2i(426,240);root.add_child(vp)
	ui=load("res://scenes/main.tscn").instantiate();ui.game=ObservedGame.new();ui.game.slot_directory="/private/tmp/critical-cinema-test-slots";ui.game.save_path="/private/tmp/critical-cinema-test-save.json";vp.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.audio.stop_all();ui.instant_mode=true
	var definitions=Cinema.data().cases
	check(definitions.size()==14,"fourteen approved native programs")
	for key in definitions:
		var spec=definitions[key];var weapon=23 if spec.get("spell","")=="fire" else 26 if spec.get("spell","")=="holy" else 24 if spec.get("spell","")=="thunder" else 27 if spec.get("spell","")=="wind" else 1 if spec.weapon=="弓" else 0
		check(cutin_fits(spec),"unclipped cut-in text stays clear of portrait and neighboring text "+key)
		var e=fixture(str(spec.hero),bool(spec.advanced),weapon);var chosen=ui.battle_animation.selection(e)
		check(chosen.kind=="critical_cinema" and chosen.key==key,"resolved event selects "+key)
		var before=ui.game.strike_commits;var kills=ui.game.kills;var roster=ui.game.roster.duplicate(true)
		await ui.battle_animation.play(e)
		check(ui.game.strike_commits==before+1 and ui.battle_animation.contact_calls==1,"one real contact for "+key)
		check(ui.game.find_unit(e.defender).hp==23 and ui.game.find_unit(e.attacker).hp==int(e.source_hp_after),"exact final target and caster HP "+key)
		check(ui.game.kills==kills and ui.game.roster==roster,"no duplicate reward or persistent roster edits "+key)
		check(not ui.battle_animation.cinema.active and ui.battle_animation.effects.is_empty() and ui.combat_offsets[e.attacker]==Vector2.ZERO,"presentation cleaned up "+key)
		samples.append({"key":key,"contacts":ui.battle_animation.cinema.audit.contacts.duplicate(true),"target":ui.battle_animation.cinema.audit.target.duplicate(true)})
	var e=fixture("hunapu",true,0,true);var kills=ui.game.kills;var commits=ui.game.strike_commits
	check(ui.battle_animation.cinema.prepare(e),"defeated branch prepares actual target")
	check(is_equal_approx(ui.battle_animation.cinema.duration(),float(definitions["hunapu-sword-advanced"].hit)+1.05),"defeated enemy ends early before return")
	ui.battle_animation.cinema.reset();await ui.battle_animation.play(e)
	check(ui.game.kills==kills+1 and ui.game.strike_commits==commits+1 and ui.game.find_unit(e.defender).hp==0,"defeat/kill settlement exactly once")
	check(float(ui.combat_fades.get(e.defender,1.))==0.,"defeated target stays removed when popup closes")
	# Actual planner output includes initiative, counters and resolved costs.
	for hero in ["hunapu","eileen"]:
		fixture(hero,false,0);var actor=ui.game.units[0];var target=ui.game.units[1]
		actor.skill=80;actor.strength=1;actor.speed=4;target.hp=100;target.max_hp=100;target.defence=20;target.strength=1;target.skill=20;target.speed=4;target.item_id=0
		var exchange=ui.game.plan_combat(str(actor.id),str(target.id));ui.combat=exchange;commits=ui.game.strike_commits
		check(not exchange.is_empty() and not exchange.events.is_empty(),"actual combat planner creates exchange "+hero)
		var final_hp={actor.id:actor.hp,target.id:target.hp};var saw_critical=false
		for strike in exchange.get("events",[]):
			if str(strike.attacker)==hero and strike.critical:
				saw_critical=true;check(ui.battle_animation.selection(strike).kind=="critical_cinema","actual resolved planner critical enters cinema "+hero)
			final_hp[strike.defender]=int(strike.hp_after);final_hp[strike.attacker]=int(strike.source_hp_after)
			await ui.battle_animation.play(strike)
		check(saw_critical and ui.game.strike_commits==commits+exchange.events.size(),"planned critical and counter sequence each commit once "+hero)
		check(actor.hp==final_hp[actor.id] and target.hp==final_hp[target.id],"planner HP/counter outcomes preserved "+hero)
	for change in [{"critical":false},{"hit":false},{"visual_only":true},{"self_damage":3},{"blocked":true},{"weapon_index":25},{"weapon_index":40},{"weapon_index":15,"distance":2}]:
		e=fixture("eileen",false,0);e.merge(change,true)
		check(Cinema.case_for(ui.game.find_unit(e.attacker),e).is_empty(),"unsupported event preserves old animation "+str(change))
	e=fixture("hunapu",false,0);var impostor=ui.game.find_unit(e.attacker).duplicate(true);impostor.id="not_the_hero"
	check(Cinema.case_for(impostor,e).is_empty(),"shared class/character art does not grant hero cinema to NPC")
	for file in DirAccess.get_files_at("res://data/stages"):
		if not file.ends_with(".json"):continue
		var stage=JSON.parse_string(FileAccess.get_file_as_string("res://data/stages/"+file));var key=Cinema.background_for(stage)
		check(Cinema.data().backgrounds.has(key) and ResourceLoader.exists(Cinema.data().backgrounds[key]),"real stage scenery mapped "+file)
	check(Cinema.background_for({"code":"F31"},{"position":[2,4]})=="ship" and Cinema.background_for({"code":"F31"},{"position":[10,4]})=="coast","harbor fight follows ship/deck side of actual battlefield")
	for im in Cinema.data().images:check(not ("target-" in str(im.source) or "opponent" in str(im.source) or str(im.source).ends_with("battlefield.png")),"runtime pack excludes preview enemies/backdrop "+str(im.path.get_file()))
	# Timed real contact play: hold accelerates; no skipped or duplicate commit.
	var times=[]
	for fast in [false,true]:
		e=fixture("hunapu",false,0);ui.instant_mode=false;ui.animation_speed=1.;ui.set_touch_fast_forward(fast);commits=ui.game.strike_commits
		if fast:
			var guard=ui.game.units[1].duplicate(true);guard.id="cover_guard";guard.hp=30;guard.position=[6,4];ui.game.units.append(guard)
			e.cover={"unit":guard.id,"damage":5,"hp_after":25}
		var start=Time.get_ticks_usec();await ui.battle_animation.play(e);var seconds=float(Time.get_ticks_usec()-start)/1000000.;times.append(seconds)
		check(ui.game.strike_commits==commits+1 and ui.game.find_unit(e.defender).hp==23,"timed critical settles once "+str(fast))
		var hp_steps: Array = ui.battle_animation.cinema.audit.hp_steps
		check(hp_steps.map(func(row):return int(row[1]))==[29,28,27,26,25,24,23],"timed critical removes exactly one cell per point "+str(fast))
		check(hp_steps.is_empty() or float(hp_steps[0][0])>float(definitions["hunapu-sword"].hit)+.15,"critical takes its HP steps after the hit reaction")
		if fast:check(ui.game.find_unit("cover_guard").hp==25,"critical preserves actual guard damage without interrupting audiovisual clock")
		check(not ui.audio._critical_active,"exclusive music released after playback "+str(fast))
	check(times[0]>=7.1 and times[0]<8.3 and times[1]<times[0]*.48 and times[1]>times[0]*.22,"normal and held critical clocks preserve approximately 7.2 sec / 3x")
	ui.set_touch_fast_forward(false);ui.instant_mode=true
	var report={"passed":errors.is_empty(),"checks":checks,"errors":errors,"cases":samples,"timed_seconds":times,"player_saves_touched":false,"scope":"Production scene and actual commit_strike with temporary fixture events. Base-bow presentation input does not change equipment permission. No reward/playthrough completion shortcuts."}
	var f=FileAccess.open("res://reports/critical-cinema-20261104/logic.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("CRITICAL_CINEMA ",checks.size()," checks; timed ",times,"; errors ",errors)
	ui.audio.stop_all();ui.queue_free();vp.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

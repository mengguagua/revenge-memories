extends SceneTree
## Current production PC renderer, isolated deterministic presentation fixtures.
const OUT="/Users/gcc/gaocc/project/revenge-memories/officialWebsite/source/latest-20261113/"
const FRAMES="/private/tmp/website-latest-pc-frames/"
const State=preload("res://core/game_state.gd")
var ui
var vp
var errors=[]
var shots=[]
var movies=[]
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	call_deferred("run")
func fresh(code:String):
	ui.battle_animation.reset();ui.game=State.new();ui.game.new_game()
	ui.game.save_path="/private/tmp/website-latest-journal.json";ui.game.slot_directory="/private/tmp/website-latest-slots"
	for id in ui.game.stages:
		if str(ui.game.stages[id].get("code",""))==code:
			ui.game.stage_id=int(id);ui.game.battle_data=ui.game.stages[id].duplicate(true);break
	ui.game.chapter=int(ui.game.stage_id/100);ui.game.mode="battle"
	ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false}
	ui.game.units=[]
	for e in ui.game.battle_data.get("enemies",[]):
		var unit=e.duplicate(true);unit.side="enemy";ui.game.Mechanical.prepare(unit);ui.game.units.append(unit)
	ui.game.story_events.clear();ui.game.flags.erase("active_plot");ui.game.battle_outcome=""
	ui.view="battle";ui.ui_mode="inspect";ui.busy=false;ui.instant_mode=true;ui.notice_time=0;ui.phase_time=0;ui._clear_menu()
	ui.combat.clear();ui.combat_poses.clear();ui.combat_hp.clear();ui.combat_offsets.clear();ui.combat_fades.clear();ui.layout_errors.clear()
	ui.combat_hit_time=0;ui.combat_hit_id="";ui.combat_shake=0
func picture(path:String):
	ui.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	for e in ui.layout_errors:
		if not errors.has(str(e)):errors.append(str(e))
	vp.get_texture().get_image().save_png(path)
func still(key:String):
	await picture(OUT+key+".png");shots.append({"id":key,"pixels":[1278,720],"layout_errors":ui.layout_errors.duplicate()})
func setup_combat(hero:Dictionary,target:Dictionary,weapon:int,distance:int,enemy_attacks:bool=false)->Dictionary:
	hero.side="player";hero.position=[4,4];hero.hp=60;hero.max_hp=60;hero.no_experience=true
	target.side="enemy";target.position=[4+distance,4];target.hp=60;target.max_hp=60;target.no_experience=true
	ui.game.units=[hero,target]
	var actor=target if enemy_attacks else hero;var defender=hero if enemy_attacks else target
	if not enemy_attacks:actor.weapon_index=weapon
	ui.combat={"attacker":actor.id,"defender":defender.id,"distance":distance,"initiative_side":"enemy" if enemy_attacks else "player"}
	ui.view="combat";ui.busy=true;ui.combat_message=""
	for u in ui.game.units:
		ui.combat_hp[u.id]=60;ui.combat_poses[u.id]=int(ui.battle_animation.sprite(u).sequences.idle[0]);ui.combat_offsets[u.id]=Vector2.ZERO;ui.combat_fades[u.id]=1.0
	var context=ui.game.Rules.attack_context(actor,distance)
	var stats=ui.game.Rules.attack_stats(context,defender,ui.game.terrain_avoid(ui.game.pos(defender)))
	var damage=int(stats.damage);var cost=int(stats.hp_cost)
	ui.combat.stats={actor.id:stats};ui.combat_hp[actor.id]=60-cost
	return {"attacker":actor.id,"defender":defender.id,"weapon_index":weapon,"distance":distance,"hit":true,"critical":false,"damage":damage,"hp_before":60,"hp_after":60-damage,"source_hp_before":60,"source_hp_after":60-cost,"hp_cost":cost}
func record_attack(key:String,event:Dictionary,movie:String,offset:int)->int:
	var anim=ui.battle_animation;var chosen=anim.selection(event)
	if chosen.kind!="source":errors.append("Missing native sequence "+key);return 0
	var variant:Dictionary=chosen.variant;var fps=float(variant.get("native_fps",60.0988));var hit=float(variant.contact_tick)/fps
	var recipe=anim.ReviewFx.puppet_plan(str(chosen.puppet_fx),variant) if chosen.has("puppet_fx") else anim.ReviewFx.battle_plan(str(chosen.key),event)
	var actor=ui.game.find_unit(event.attacker);var target=ui.game.find_unit(event.defender)
	anim.review_fx.prepare(recipe,event,anim.origin(actor,ui.combat),anim.origin(target,ui.combat))
	var duration=maxf(float(variant.frames.size())/fps,hit+float(recipe.get("end",0)))+.15
	var count=ceili(duration*30);var folder=FRAMES+movie+"/";DirAccess.make_dir_recursive_absolute(folder)
	var contacted=false;var snap_done=false
	for frame in range(count):
		var time=frame/30.;ui.elapsed=time;ui.combat_hit_time=maxf(0,.5-(time-hit)) if contacted else 0
		var tick=mini(variant.frames.size()-1,floori(time*fps))
		anim.show_frame(event,tick)
		if not contacted and time>=hit:
			contacted=true;await anim._contact(event);anim.review_fx.contact();anim._review_contact(event)
		if time<hit:anim.review_fx.source_tick(tick,int(variant.contact_tick))
		else:
			anim.review_fx.seek(time-hit,false)
			var graphic=anim.sprite(target);var reaction={}
			if ui.game.Mechanical.is_puppet(target):reaction=anim.MechanicalArt.reaction(target,"hit",anim.origin(target,ui.combat),anim._left(target,ui.combat))
			else:
				var reaction_key=str(graphic.get("reviewed_reactions",{}).get("hit",""))
				if not reaction_key.is_empty():reaction=anim.Reviewed.variant(reaction_key)
			if not reaction.is_empty():
				var rt=floori((time-hit)*float(reaction.native_fps))
				anim._reaction_actor=str(target.id) if rt<reaction.frames.size() else ""
				anim._reaction_frame=reaction.frames[rt] if rt<reaction.frames.size() else {}
		await picture(folder+"frame-%04d.png"%(offset+frame))
		if not snap_done and time>=hit+.25:
			snap_done=true;await still(key+"-impact")
	var audio=[]
	for cue in recipe.get("audio",[]):
		audio.append({"path":anim.ReviewFx.data().audio.get(cue.key,""),"at":offset/30.+hit+float(cue.time),"gain":float(cue.gain),"duration":float(cue.duration)})
	movies.append({"id":key,"movie":movie,"frames":count,"offset":offset,"seconds":count/30.,"hit":hit,"contact_count":anim.contact_calls,"target_hp":target.hp,"expected_hp":event.hp_after,"damage":event.damage,"native_sequence":chosen.key,"audio":audio})
	print("LATEST_ATTACK ",key," frames=",count," contacts=",anim.contact_calls)
	return count
func run():
	DirAccess.make_dir_recursive_absolute(OUT);DirAccess.make_dir_recursive_absolute(FRAMES)
	vp=SubViewport.new();vp.size=Vector2i(1278,720);vp.size_2d_override=Vector2i(426,240);vp.size_2d_override_stretch=true;vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	ui=load("res://scenes/main.tscn").instantiate();vp.add_child(ui);await process_frame
	ui.set_process(false);ui.set_physics_process(false);ui.audio.stop_all()
	var environment_offset=0
	for job in [["snow","M11",Vector2i(10,9)],["shore","F23",Vector2i(16,12)],["cave","F51",Vector2i(12,10)]]:
		fresh(job[1]);ui.busy=true;ui.map_ambient.prepare(ui)
		var focus:Vector2i=job[2]
		if job[0]=="shore" and not ui.map_ambient.shores.is_empty():focus=ui.map_ambient.shores[int(ui.map_ambient.shores.size()/2)].cell
		if job[0]=="cave" and not ui.map_ambient.fires.is_empty():focus=Vector2i(ui.map_ambient.fires[0]/16)
		ui.game.cursor=focus;ui._focus_battle(focus,true)
		var folder=FRAMES+"environment/";DirAccess.make_dir_recursive_absolute(folder)
		for frame in range(120):
			ui.elapsed=2+frame/30.;await picture(folder+"frame-%04d.png"%(environment_offset+frame))
			if frame==60:await still("environment-"+job[0])
		movies.append({"id":job[0],"movie":"environment","offset":environment_offset,"frames":120,"seconds":4,"stage":job[1],"profile":ui.map_ambient.profile.duplicate(true),"water_cells":ui.map_ambient.water.size(),"shore_edges":ui.map_ambient.shores.size(),"fires":ui.map_ambient.fires.size(),"lamps":ui.map_ambient.lamps.size(),"audio":[]});environment_offset+=120
	var offset=0
	for job in [["sword","hunapu",0,1],["bow","hunapu",1,2],["fire","eileen",23,2],["thunder","eileen",24,2]]:
		fresh("M11")
		var hero=ui.game.characters[job[1]].duplicate(true)
		if job[0]=="bow":ui.game.HeroProfessions.apply(hero);hero.item_id=22
		var target={}
		for s in ui.game.stages.values():
			for e in s.get("enemies",[]):
				if int(e.class_id)==1:target=e.duplicate(true);break
			if not target.is_empty():break
		offset+=await record_attack("attack-"+job[0],setup_combat(hero,target,job[2],job[3]),"combat",offset)
	var puppet_offset=0
	for model in ["water_monkey","pseudo_titan","cyclops","owl","prometheus"]:
		fresh("F44")
		var puppet={}
		for s in ui.game.stages.values():
			for e in s.get("enemies",[]):
				if e.get("mechanical_model","")==model:puppet=e.duplicate(true);break
			if not puppet.is_empty():break
		if puppet.is_empty():errors.append("No current deployment "+model);continue
		ui.game.Mechanical.prepare(puppet)
		var hero=ui.game.characters.eileen.duplicate(true)
		var weapon={"water_monkey":1008,"pseudo_titan":1009,"cyclops":1010,"owl":1011,"prometheus":1013}[model]
		var distance=1 if model in ["pseudo_titan","owl"] else 2
		puppet.innate_attack_index=weapon
		var event=setup_combat(hero,puppet,weapon,distance,true)
		await still("puppet-"+model+"-intact")
		puppet_offset+=await record_attack("puppet-"+model,event,"puppets",puppet_offset)
		ui.battle_animation.reset()
		for key in ui.game.Mechanical.part_keys(puppet):puppet.parts[key].hp=0
		ui.combat_poses[puppet.id]=int(ui.battle_animation.sprite(puppet).sequences.idle[0]);ui.combat_offsets[puppet.id]=Vector2.ZERO
		ui.combat_poses[hero.id]=int(ui.battle_animation.sprite(hero).sequences.idle[0]);ui.combat_hp[hero.id]=48
		await still("puppet-"+model+"-broken")
	var report={"passed":errors.is_empty(),"errors":errors,"background_guard":true,"viewport":[1278,720],"shots":shots,"movies":movies,"scope":"Fresh current PC scene and native map/battle renderers. Staged placements, deterministic 30fps. One production contact per attack; no user save writes."}
	var f=FileAccess.open(OUT+"capture.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("LATEST_CAPTURE_ERRORS ",errors);ui.audio.stop_all();ui.queue_free();await process_frame;vp.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

extends "./capture_batch.gd"
var map_job={};var receipt={};var map_points=[];var map_contact=-1.
func base_fixture(stage:int=101):
	ui.hero_map_animation.reset();ui.map_effects.reset();ui.map_actor_alpha.clear();ui.game.new_game();ui.game.save_path="/private/tmp/pixelfx-map-only/never-published.json";ui.game.slot_directory="/private/tmp/pixelfx-map-only/slots"
	ui.game.world_node=int(ui.game.stages[stage].node);ui.game.stage_id=stage;ui.game.battle_data=ui.game.stages[stage].duplicate(true);ui.game.chapter=int(ui.game.battle_data.chapter);ui.game.route=str(ui.game.battle_data.route);ui.game.mode="battle";ui.game.battle_outcome=""
	ui.game.flags.quest={"objects":{},"evacuated":[],"freed":[],"burn_streak":0,"reinforced":false,"mid_done":false};ui.game.ChapterTwo.initialize(ui.game)
	if ui.game.chapter==4:ui.game.ChapterFour.initialize(ui.game)
	ui.game.story_events.clear();ui.game.phase="player";ui.game.turn=1;ui.game.units=[];ui.game.selected_id="";ui.game.cursor=Vector2i(6,13);ui.game.move_origin=ui.game.cursor
	ui.view="battle";ui.ui_mode="whole_capture";ui.busy=true;ui.notice_time=0;ui.phase_time=0;ui.elapsed=.4;ui.instant_mode=false;ui.animation_speed=1.;ui._clear_menu();ui.layout_errors.clear();phone.layout_errors.clear()

func unit(cid:int,side:String,id:String,at:Array)->Dictionary:
	var u=ui.game._initial_character("daan").duplicate(true);u.id=id;u.class_id=cid;u.character_id=0;u.name_id=0;u.side=side;u.position=at;u.acted=false;u.hp=30;u.max_hp=30;u.strength=10;u.defence=4;u.resistance=3;u.item_id=0;u.magic_flags=255;u.no_experience=true;u.name_zh=str(ui.game.catalog.classes[str(cid)].get("enemy_name_zh" if side=="enemy" else "name_zh","角色"));return u

func hero_fixture(job:Dictionary):
	base_fixture(int(job.stage));var hero=job.hero_data.duplicate(true);hero.side="player";hero.position=job.hero_at;hero.acted=false;hero.no_experience=true;ui.game.MapSkills.clear(hero)
	if job.advanced:ui.game.HeroProfessions.apply(hero);hero.hp=hero.max_hp
	if str(job.key)=="hunapu-bow":hero.item_id=22
	var friend=ui.game.characters.otto.duplicate(true);friend.id="map_preview_friend";friend.side="player";friend.position=job.friend;friend.acted=false
	ui.game.units=[hero,friend]
	for item in job.enemies_data:
		var enemy=item.unit.duplicate(true);enemy.acted=false;ui.game.units.append(enemy)
	ui.game.party=[hero.id,friend.id];ui.game.selected_id=hero.id;ui.game.cursor=Vector2i(job.hero_at[0],job.hero_at[1]);ui._focus_battle(Vector2i(job.center[0],job.center[1]),true)
	receipt=ui.game.MapSkills.apply(ui.game,str(hero.id),Vector2i(job.center[0],job.center[1]),Vector2i.RIGHT)
	return hero

func picture()->Image:
	ui.queue_redraw();phone._sync_controls();phone.queue_redraw();await process_frame;await RenderingServer.frame_post_draw
	var im=vp.get_texture().get_image();im.resize(W,H,Image.INTERPOLATE_NEAREST);im.convert(Image.FORMAT_RGBA8);return im

func point(cell:Array)->Array:
	var p=ui._battle_cell_screen(Vector2i(cell[0],cell[1]))+ui._canvas_offset()+ui.map_offset+Vector2(124,8);return [p.x,p.y]

func row(t:float,id:int)->Dictionary:
	var points=[]
	for u in ui.game.units:
		if str(u.id) in map_points:points.append({"id":u.id,"at":point(u.position),"hp":u.hp})
	return {"t":t,"image":id,"points":points,"map_active":ui.map_effects._active,"map_program_frame":ui.map_effects._frame,"map_cell":[ui.map_effects._cell.x,ui.map_effects._cell.y],"effect_point":point([ui.map_effects._cell.x,ui.map_effects._cell.y]) if ui.map_effects._active else [],"offset":[ui.map_offset.x,ui.map_offset.y],"modulate":[ui.self_modulate.r,ui.self_modulate.g,ui.self_modulate.b,ui.self_modulate.a],"hero_time":ui.hero_map_animation.elapsed,"contacts":ui.hero_map_animation.audit.get("contacts",[]).duplicate()}

func play_flow(caster:Dictionary,value:Dictionary):
	playing=true;await ui._map_spell_feedback(caster,value);playing=false

func capture_flow(kind:String):
	base_fixture();receipt={};var caster;var spell=37 if kind=="summon" else 45 if kind=="invoke" else 46
	var hero=ui.game._initial_character("hunapu").duplicate(true);hero.side="player";hero.position=[3,13];hero.acted=false
	var guard=unit(19,"enemy","flow_guard",[12,13]);guard.enemy_slot=0
	if kind=="summon":
		caster=unit(19,"enemy","flow_caster",[5,13]);caster.magic_flags=16;caster.strength=2;caster.enemy_slot=1;ui.game.units=[caster,hero,guard];ui.game.party=[hero.id]
	else:
		caster=ui.game._initial_character(ui.game.character_key(15)).duplicate(true);caster.side="player";caster.position=[5,13];caster.class_id=18;caster.hp=40;caster.max_hp=40;caster.strength=16 if kind=="expel" else 2;caster.magic_flags=255;caster.acted=false;caster.no_experience=true
		ui.game.units=[caster,hero,guard];ui.game.party=[hero.id,caster.id]
		if kind=="expel":
			var victim=unit(17,"enemy","flow_victim",[6,13]);victim.enemy_slot=2;ui.game.units.append(victim)
	ui.game.selected_id="";ui._focus_battle(Vector2i(5,13),true);map_points=[str(caster.id)]
	var before=await picture();var before_row=row(0,0);var hp_before=int(caster.hp);ui.game.rng_state=13
	receipt=ui.game.use_support(str(caster.id),spell)
	if receipt.is_empty() or (receipt.get("spawned",[]).is_empty() and receipt.get("changed",[]).is_empty()):errors.append("Empty full spell flow "+kind);return
	for id in receipt.get("spawned",[]):map_points.append(str(id));ui.map_actor_alpha[str(id)]=0.
	for change in receipt.get("changed",[]):map_points.append(str(change.id))
	var job={"id":"map-full-"+kind,"kind":"support-flow","family":"map","program":7 if kind=="summon" else 1 if kind=="invoke" else 8,"profile":"19_enemy" if kind=="summon" else "18_ally","side":"enemy" if kind=="summon" else "ally","label":str(caster.name_zh)+" · "+str(ui.Items.spell(spell).name_zh)+"完整流程","move":str(ui.Items.spell(spell).name_zh),"spell":spell,"caster":caster.id,"caster_hp_before":hp_before,"caster_hp_after":caster.hp,"suppress_flash":true}
	var images=[before];var frames=[before_row];var start=Time.get_ticks_usec();play_flow(caster,receipt)
	while playing:
		images.append(await picture());var t=float(Time.get_ticks_usec()-start)/1000000.+.3;ui.elapsed=t;frames.append(row(t,frames.size()))
		if t>18:errors.append("Full map flow timeout "+kind);break
	images.append(await picture());frames.append(row(float(Time.get_ticks_usec()-start)/1000000.+.3,frames.size()))
	await store_movie(job,images,frames,.3,float(frames[-1].t)+.65)

func store_movie(job:Dictionary,images:Array,frames:Array,contact:float,duration:float):
	var dir=ROOT+"map-captures/"+str(job.id)+"/";DirAccess.make_dir_recursive_absolute(dir)
	var unique=[];var seen={};var mapping=[]
	for im in images:
		var bytes=im.get_data();var key=bytes.hex_encode().sha256_text()
		if not seen.has(key):seen[key]=unique.size();unique.append(im)
		mapping.append(int(seen[key]))
	for i in range(frames.size()):frames[i].image=mapping[i]
	var atlases={"current":save_atlases(unique,dir,"current")};var layout=[]
	for e in ui.layout_errors+phone.layout_errors:
		if not layout.has(str(e)):layout.append(str(e))
	var report={"id":job.id,"job":job,"frames":frames,"duration":duration,"contact_time":contact,"receipt":receipt.duplicate(true),"atlases":atlases,"unique_frames":unique.size(),"atlas_frames":16,"atlas_cols":4,"layout_errors":layout,"guard":true,"engine":"Current Godot map renderer and source timing; isolated fixture."}
	var f=FileAccess.open(dir+"capture.json",FileAccess.WRITE);f.store_string(JSON.stringify(report));f.close();records.append({"id":job.id,"frames":frames.size(),"unique":unique.size(),"duration":duration,"layout_errors":layout});print("MAP_CAPTURE ",JSON.stringify(records[-1]))

func capture_hero(job:Dictionary,healer:int=0):
	var hero
	if healer==0:hero=hero_fixture(job)
	else:
		base_fixture();hero=unit(healer,"player","map_healer",[5,13]);var target=unit(6,"player","map_friend",[7,13]);target.hp=8;var enemy=unit(14,"enemy","map_enemy",[10,15]);ui.game.units=[hero,target,enemy];ui.game.party=[hero.id,target.id];ui.game.selected_id=hero.id;ui._focus_battle(Vector2i(6,13),true);receipt=ui.game.MapSkills.apply(ui.game,hero.id,Vector2i(7,13))
	if not receipt.get("valid",false):errors.append("MAP invalid "+str(job.id)+": "+str(receipt.get("reason","")));return
	ui.hero_map_animation.prepare(receipt);map_points=receipt.targets.map(func(t):return str(t.id));map_points.append(str(hero.id))
	var spec=ui.hero_map_animation.spec;var duration=float(spec.duration)+.85;var contact=.3+float(spec.impact);var images=[];var frames=[]
	job.family="map";job.label=str(hero.name_zh)+" · "+str(receipt.name);job.profile=str(hero.class_id)+"_ally";job.side="ally";job.move=str(receipt.name);job.kind="hero-map";job.support=bool(receipt.get("support",false));job.bow=receipt.bow;job.magic=receipt.magic;job.targets=[]
	for hit in receipt.targets:job.targets.append({"id":hit.id,"time":.3+ui.hero_map_animation.hit_time(hit),"damage":hit.get("damage",0),"heal":hit.get("heal",0),"hp_before":hit.hp_before,"hp_after":hit.hp_after})
	for n in range(ceili(duration*60)):
		var t=n/60.;ui.hero_map_animation._step(clampf(t-.3,0,float(spec.duration)));ui.elapsed=t
		images.append(await picture());frames.append(row(t,n))
	var expected=receipt.targets.size();var actual=ui.hero_map_animation.audit.contacts.size()
	if expected!=actual:errors.append("MAP target count "+str(job.id))
	job.contacts=actual;await store_movie(job,images,frames,contact,duration);ui.hero_map_animation.reset()

func play_map(job:Dictionary,target:Dictionary):
	playing=true
	if job.kind=="teleport":await ui.map_effects.teleport(target,Vector2i(8,13))
	elif job.kind=="quake":await ui.map_effects.flash("quake");await ui.map_effects.play_program(9,target)
	else:
		if job.get("disappear",false):target.hp=0
		await ui.map_effects.play_program(int(job.program),target)
		if job.get("spawn",false):ui.map_actor_alpha.erase(str(target.id))
	playing=false

func capture_program(job:Dictionary):
	base_fixture();receipt={};var target=unit(int(job.class_id),str(job.get("unit_side","enemy")),"map_target",[6,13]);var hero=ui.game._initial_character("hunapu").duplicate(true);hero.position=[4,13];hero.side="player";hero.acted=false;var enemy=unit(19,"enemy","map_caster",[9,13]);ui.game.units=[target,hero,enemy];ui.game.party=[hero.id];ui.game.selected_id="";ui._focus_battle(Vector2i(6,13),true)
	job.label=job.label+" · "+str(target.name_zh);job.profile=str(target.class_id)+"_"+("enemy" if target.side=="enemy" else "ally");job.side="enemy" if target.side=="enemy" else "ally";job.family="map";map_points=[str(target.id)]
	if job.get("spawn",false):ui.map_actor_alpha[str(target.id)]=0.
	var images=[];var frames=[];images.append(await picture());frames.append(row(0,0));var start=Time.get_ticks_usec();play_map(job,target)
	while playing:
		var im=await picture();var t=float(Time.get_ticks_usec()-start)/1000000.+.3;ui.elapsed=t;images.append(im);frames.append(row(t,frames.size()))
		if t>16:errors.append("MAP timeout "+str(job.id));break
	images.append(await picture());frames.append(row(float(Time.get_ticks_usec()-start)/1000000.+.3,frames.size()))
	await store_movie(job,images,frames,.3,float(frames[-1].t)+.65)

func run():
	Engine.max_fps=60;vp=SubViewport.new();vp.size=Vector2i(1184,480);vp.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(0,0,1184,480);phone.journal_directory_override="/private/tmp/pixelfx-map-only/slots";vp.add_child(phone);await process_frame;ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);phone.set_process(false);ui.audio.stop_all()
	if OS.get_environment("PIXELFX_MAP_FLOWS_ONLY")=="1":
		for kind in ["summon","invoke","expel"]:await capture_flow(kind)
		var f=FileAccess.open(ROOT+"map-flow-summary.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"records":records,"guard":true},"  "));f.close();ui.audio.stop_all();phone.queue_free();await process_frame;vp.queue_free();await process_frame;print("MAP_FLOW_ERRORS ",errors);quit(0 if errors.is_empty() else 1);return
	var fixtures=JSON.parse_string(FileAccess.get_file_as_string(ROOT+"map-fixtures.json"))
	for fixture in fixtures:
		fixture.id="map-"+str(fixture.key);await capture_hero(fixture)
	for cid in [18,17]:await capture_hero({"id":"map-heal-"+str(cid)},cid)
	var jobs=[
		{"id":"map-phantom","kind":"program","program":1,"class_id":8,"unit_side":"player","label":"幻影入场","move":"幻影","spawn":true},
		{"id":"map-warp","kind":"teleport","program":2,"class_id":6,"unit_side":"player","label":"传送离场与落点","move":"传送"},
		{"id":"map-summon-bone","kind":"program","program":3,"class_id":5,"label":"召唤入场","move":"召唤","spawn":true},
		{"id":"map-expel-bone","kind":"program","program":4,"class_id":5,"label":"驱邪退场","move":"驱邪","disappear":true},
		{"id":"map-summon-corpse","kind":"program","program":5,"class_id":11,"label":"召唤入场","move":"召唤","spawn":true},
		{"id":"map-expel-corpse","kind":"program","program":6,"class_id":11,"label":"驱邪退场","move":"驱邪","disappear":true},
		{"id":"map-summon-skeleton","kind":"program","program":7,"class_id":17,"label":"召唤入场","move":"召唤","spawn":true},
		{"id":"map-expel-skeleton","kind":"program","program":8,"class_id":17,"label":"驱邪退场","move":"驱邪","disappear":true},
		{"id":"map-stone-appearance","kind":"program","program":11,"class_id":3,"label":"石翼兽入场","move":"召唤","spawn":true},
		{"id":"map-stone-expel","kind":"program","program":11,"class_id":3,"label":"石翼兽驱邪","move":"驱邪","disappear":true},
		{"id":"map-restore","kind":"program","program":10,"class_id":15,"label":"地图恢复反馈","move":"恢复"},
		{"id":"map-damage","kind":"program","program":9,"class_id":6,"label":"地图伤害反馈","move":"地图伤害"},
		{"id":"map-quake","kind":"quake","program":9,"class_id":6,"label":"地震与伤害反馈","move":"地震"}
	]
	for job in jobs:await capture_program(job)
	var f=FileAccess.open(ROOT+"map-summary.json",FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"errors":errors,"records":records,"guard":true},"  "));f.close();ui.audio.stop_all();phone.queue_free();await process_frame;vp.queue_free();await process_frame;print("MAP_ERRORS ",errors);quit(0 if errors.is_empty() else 1)

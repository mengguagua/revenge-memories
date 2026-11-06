extends SceneTree
## Tests the real sprite/animation selectors against the frozen review import.
const Reviewed=preload("res://core/reviewed_animations.gd")
const Party=preload("res://core/party_sprites.gd")
const OUT="res://reports/character-art-sync-20261024/"
var ui
var checks=0
var errors:Array=[]
var selected=0
var references:Array=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks+=1
	if not ok:
		errors.append(label)
		if errors.size()<30:push_error(label)
func sha(bytes:PackedByteArray)->String:
	var ctx=HashingContext.new();ctx.start(HashingContext.HASH_SHA256);ctx.update(bytes)
	return ctx.finish().hex_encode()
func actor(key:String,id:String)->Dictionary:
	var a:Dictionary=ui.game.characters.hunapu.duplicate(true)
	var cid=11 if key=="eileen" else 24 if key=="eileen_promoted" else int(key.split("_")[0])
	a.merge({"id":"eileen" if key.begins_with("eileen") else id,"class_id":cid,"side":"enemy" if key.ends_with("enemy") else "player","hp":30,"max_hp":30,"acted":false,"promoted":key in ["23_ally","eileen_promoted"],"alm_promoted":false,"position":[4,4]},true)
	if key in ["21_ally","23_ally"]:a.id="hunapu"
	if key=="21_enemy":a.campaign_final_boss=true
	return a
func fixture(item:Dictionary,art:Dictionary)->Dictionary:
	var a=actor(item.key,"sync_actor")
	var b=actor("7_ally" if str(item.id).ends_with("_vs_heavy") else "6_ally","sync_target")
	b.side="player" if a.side=="enemy" else "enemy"
	ui.game.units=[a,b]
	var base=str(item.id).get_slice("--",1).split("_far_")[0].trim_suffix("_vs_heavy")
	var weapon=0
	if "_item_" in base:weapon=int(base.get_slice("_item_",1))
	elif "levin" in base:weapon=15
	elif "silver_bow" in base:weapon=22
	elif "bow" in base:weapon=1
	elif "javelin" in base:weapon=4
	elif base=="stone-claw":weapon=1001
	elif base in ["stone-spit","stone-spit-far"]:weapon=1002
	elif base=="innate-bone-bite":weapon=1003
	elif base=="innate-eroding-breath":weapon=1004
	elif base=="wing-beak":weapon=1005
	elif base in ["sun-crown","sun-crown-far"]:weapon=1006
	var far="_far_" in str(item.id) or base.ends_with("-far")
	ui.combat={"attacker":a.id,"defender":b.id,"distance":2 if far else 1,"initiative_side":"enemy" if "_far_enemy" in str(item.id) else "player"}
	var e={"attacker":a.id,"defender":b.id,"weapon_index":weapon,"critical":base.ends_with("_critical"),"hit":true,"hp_before":30,"hp_after":29}
	ui.battle_animation.active_event=e.duplicate(true)
	return e
func run():
	var expected:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OUT+"import.json"))
	var d=Reviewed.data()
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.game.new_game();ui.game.save_path="/private/tmp/character-art-sync-test-save.json";ui.instant_mode=true
	var roster=ui.game.roster.duplicate(true)
	var profile_art={}
	var texture_cache={}
	for item in expected.inventory:
		var art:Dictionary=d.battle[item.key] if item.context=="battle" else d.maps[item.key][item.context]
		profile_art[item.profile]=art
		check(art.art_revision==item.revision,"active revision "+item.profile)
		var tex:Texture2D=load(art.path)
		check(tex!=null,"texture "+item.profile)
		if tex==null:continue
		var im=tex.get_image();im.convert(Image.FORMAT_RGBA8)
		check(im.get_size()==Vector2i(item.size[0],item.size[1]),"atlas dimensions "+item.profile)
		for slot in item.frame_hashes:
			var i=int(slot);var w=int(art.frame_size[0]);var h=int(art.frame_size[1]);var cols=int(art.columns)
			var region=im.get_region(Rect2i(i%cols*w,floori(float(i)/cols)*h,w,h))
			check(sha(region.get_data())==item.frame_hashes[slot],"review pixels "+item.profile+"/"+slot)
		if item.context=="battle":continue
		var a=actor(item.key,"map_actor")
		var kind={"story":"hub","world":"world","tactical-idle":"map","tactical-walk":"map_move"}[item.context]
		var chosen=Party.sprite(kind,a,1)
		check(chosen.get("path","")==art.path,"map route "+item.profile)
		if item.context=="tactical-walk":
			ui.moving_id=a.id
			for direction in ["up","right","down","left"]:
				ui.moving_direction={"up":Vector2i.UP,"right":Vector2i.RIGHT,"down":Vector2i.DOWN,"left":Vector2i.LEFT}[direction]
				var sp:Dictionary=ui._map_unit_sprite(a)
				var cyc:Dictionary=art.direction_cycles[direction]
				check(sp.native_cycle==cyc.frames and sp.cycle_ticks==cyc.ticks,"walk direction "+item.profile+"/"+direction)
				var tick=0
				for n in range(cyc.frames.size()):
					for k in range(int(cyc.ticks[n])):
						ui.elapsed=(tick+0.1)/60.0988
						check(ui._native_map_pose(sp)==int(cyc.frames[n]),"walk phase "+item.profile+"/"+direction+"/"+str(tick));tick+=1
			ui.moving_id=""
	for effect in expected.effects:
		var meta:Dictionary=d.sprites[effect.id]
		var tex:Texture2D=load(meta.path);check(tex!=null,"effect "+effect.id)
		if tex!=null:
			var im=tex.get_image();im.convert(Image.FORMAT_RGBA8)
			check(sha(im.get_data())==effect.rgba_sha256,"effect pixels "+effect.id)
	var samples={}
	for item in expected.actions:
		var art:Dictionary=profile_art[item.profile]
		var v:Dictionary=d.variants[item.runtime_key]
		check(v.frames.size()==int(item.frames) and float(v.native_fps)==float(item.fps),"timeline "+item.id)
		for row in v.frames:
			check(int(row.frame)<int(art.frames),"pose range "+item.id)
			for e in row.get("effects",[]):check(d.sprites.has(e.sprite) and not str(e.sprite).ends_with("target-reference"),"effect binding "+item.id)
		if item.kind!="attack":continue
		# Native bone-dragon flight is a reference; real combat owns the existing
		# jaw/breath cards and uses their separately imported reviewed timelines.
		if item.key=="5_enemy" and str(item.id).ends_with("--original_class_5_enemy_normal"):
			references.append(item.id);continue
		if item.profile=="hunapu-battle" and str(item.id).ends_with("--original_class_21_promoted"):
			references.append(item.id);continue  # The dedicated dawn-warrior profile owns promotion now.
		var e=fixture(item,art)
		var chosen:Dictionary=ui.battle_animation.selection(e)
		check(chosen.get("key","")==item.runtime_key,"runtime action "+item.id+" selected="+str(chosen.get("key","")))
		if chosen.get("key","")!=item.runtime_key:continue
		selected+=1
		check(int(chosen.variant.contact_tick)==int(item.contact_tick),"one contact tick "+item.id)
		check(ui.battle_animation.sprite(ui.game.find_unit(e.attacker)).path==art.path,"battle body "+item.id)
		if not samples.has(item.profile):samples[item.profile]=item
	for pid in samples:
		var item:Dictionary=samples[pid];var art:Dictionary=profile_art[pid];var e=fixture(item,art)
		ui.battle_animation.reset();await ui.battle_animation.play(e)
		check(ui.battle_animation.contact_calls==1 and ui.game.find_unit(e.defender).hp==29,"single gameplay commit "+pid)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[e.attacker]==Vector2.ZERO,"cleanup "+pid)
		for kind in ["miss","hit","exit"]:
			check(await ui.battle_animation.reaction(e.attacker,kind),"reaction route "+pid+"/"+kind)
	check(Party.sprite("map",actor("23_ally","sync_actor"),1).reviewed_profile=="hunapu-promoted-maps-tactical-idle","dawn promotion route")
	check(Party.sprite("hub",actor("eileen_promoted","eileen"),1).reviewed_profile=="eileen-promoted-maps-story","personal promoted story route")
	# Exercise the deadline clock, visual tails and target reactions through
	# the actual controller as well as the instant single-contact path above.
	ui.instant_mode=false;ui.animation_speed=20.0
	for pid in ["hunapu-promoted-battle","professions-class-17-enemy-battle","professions-class-16-enemy-battle"]:
		var item:Dictionary=samples[pid];var art:Dictionary=profile_art[pid];var e=fixture(item,art)
		if pid=="professions-class-17-enemy-battle":e.hp_after=0
		ui.battle_animation.reset();await ui.battle_animation.play(e)
		check(ui.battle_animation.contact_calls==1 and ui.game.find_unit(e.defender).hp==e.hp_after,"timed single commit "+pid)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[e.attacker]==Vector2.ZERO,"timed return "+pid)
		if e.hp_after==0:check(float(ui.combat_fades[e.defender])==0.0,"reviewed death fade "+pid)
	check(ui.game.roster==roster,"saved roster untouched")
	var result={"passed":errors.is_empty(),"checks":checks,"selected_attacks":selected,"battle_profiles_played":samples.size(),"timed_playback_profiles":3,"reference_only_native_programs":references,"errors":errors,"headless":true,"device_updated":false}
	var f=FileAccess.open(OUT+"runtime-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
	print("CHARACTER_ART_SYNC ",JSON.stringify({"passed":errors.is_empty(),"checks":checks,"selected_attacks":selected,"error_count":errors.size()}))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

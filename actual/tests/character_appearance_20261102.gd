extends SceneTree
## Exercise the actual lazy runtime index, texture imports and battle selectors.
const Reviewed=preload("res://core/reviewed_animations.gd")
const Programs=preload("res://core/animation_programs.gd")
const OUT="res://reports/character-appearance-20261102/"
var ui
var checks:=0
var slots:=0
var attacks:=0
var errors:Array=[]
func _initialize():
	create_timer(60.0).timeout.connect(_timeout)
	call_deferred("run")
func _timeout():
	push_error("Character appearance test timed out");quit(1)
func check(ok:bool,label:String):
	checks+=1
	if not ok:errors.append(label);push_error(label)
func visible_hash(image:Image)->String:
	image.convert(Image.FORMAT_RGBA8)
	var bytes=image.get_data()
	for n in range(0,bytes.size(),4):
		if bytes[n+3]==0:bytes[n]=0;bytes[n+1]=0;bytes[n+2]=0
	var hash=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes)
	return hash.finish().hex_encode()
func actor(cid:int,id:String,side:String)->Dictionary:
	var a:Dictionary=ui.game.characters.hunapu.duplicate(true)
	a.merge({"id":id,"class_id":cid,"character_id":0,"name_id":0,"side":side,"hp":30,"max_hp":30,
		"acted":false,"promoted":false,"alm_promoted":false,"position":[4,4]},true)
	return a
func fixture(item:Dictionary)->Dictionary:
	var cid=int(item.class_id)
	var a=actor(cid,"appearance_actor","player")
	var heavy=str(item.source_key).ends_with("_vs_heavy")
	var b=actor(7 if heavy else 6,"appearance_target","enemy")
	b.position=[5,4]
	ui.game.units=[a,b]
	ui.combat={"attacker":a.id,"defender":b.id,"distance":2 if "_far_" in str(item.source_key) else 1,
		"initiative_side":"enemy" if "_far_enemy" in str(item.source_key) else "player"}
	var weapon=22 if "silver_bow" in str(item.source_key) else 1 if "bow" in str(item.source_key) else 4 if "javelin" in str(item.source_key) else 0
	var e={"attacker":a.id,"defender":b.id,"weapon_index":weapon,"hit":true,"critical":false,"hp_before":30,"hp_after":29}
	ui.battle_animation.active_event=e.duplicate(true)
	return e
func run():
	var expected:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OUT+"import.json"))
	var metadata=Reviewed.metadata()
	check(not Programs.groups.reviewed.has("fallback"),"uses regenerated lazy metadata index")
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.game.save_path="/private/tmp/character-appearance-test-unused.json";ui.game.new_game();ui.instant_mode=true
	for item in expected.inventory:
		var art:Dictionary=metadata.battle[item.key]
		check(art.path==item.path and art.art_revision==item.revision,"active new atlas "+item.key)
		check(ResourceLoader.exists(art.path),"resource imported "+item.key)
		var texture:Texture2D=load(art.path)
		check(texture!=null,"texture loaded "+item.key)
		if texture==null:continue
		var image=texture.get_image()
		check(image.get_size()==Vector2i(item.atlas_size[0],item.atlas_size[1]),"atlas dimensions "+item.key)
		var w=int(art.frame_size[0]);var h=int(art.frame_size[1]);var cols=int(art.columns)
		for slot in item.slots:
			var f=int(slot.slot)
			var region=image.get_region(Rect2i(f%cols*w,floori(float(f)/cols)*h,w,h))
			check(visible_hash(region)==slot.visible_rgba_sha256,"exact review pose "+item.key+"/"+str(f));slots+=1
	var samples={}
	for item in expected.actions:
		var v=Reviewed.variant(item.runtime_key)
		check(v.frames.size()==int(item.frames) and float(v.native_fps)==float(item.fps),"unchanged timing "+item.id)
		check(v.get("contact_tick")==item.contact_tick,"unchanged contact "+item.id)
		if item.kind!="attack":continue
		var e=fixture(item)
		var chosen:Dictionary=ui.battle_animation.selection(e)
		check(chosen.get("key","")==item.runtime_key,"actual action selection "+item.source_key)
		var art=ui.battle_animation.sprite(ui.game.find_unit(e.attacker))
		check(art.path==metadata.battle[item.key].path,"actual body selection "+item.source_key)
		if chosen.get("key","")==item.runtime_key:
			attacks+=1
			var pose=int(chosen.variant.frames[int(chosen.variant.contact_tick)].frame)
			check(ui.battle_animation.show_frame(e,int(chosen.variant.contact_tick)),"show actual contact "+item.source_key)
			check(int(ui.combat_poses[e.attacker])==pose,"contact pose "+item.source_key)
		if not samples.has(item.key):samples[item.key]=item
	for key in samples:
		var e=fixture(samples[key])
		ui.battle_animation.reset();await ui.battle_animation.play(e)
		check(ui.battle_animation.contact_calls==1,"one gameplay contact "+key)
		check(int(ui.game.find_unit(e.defender).hp)==29,"one HP change "+key)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[e.attacker]==Vector2.ZERO,"animation cleanup "+key)
	var result={"passed":errors.is_empty(),"checks":checks,"source_poses":slots,"selected_attacks":attacks,
		"played_profiles":samples.size(),"uses_runtime_metadata_index":true,"headless":true,"errors":errors,"device_updated":false}
	var f=FileAccess.open(OUT+"runtime-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(result,"  "));f.close()
	print("CHARACTER_APPEARANCE ",JSON.stringify(result))
	ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

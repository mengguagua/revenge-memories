extends SceneTree
## Also runs from outside the exported app against its embedded PCK.
const Reviewed=preload("res://core/reviewed_animations.gd")
var ui
var checks:=0
var errors:Array=[]
var slots:=0
var variants:=0
func _initialize():call_deferred("run")
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
func run():
	var expected:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("RECENT_ART_EXPECTED")))
	var data=Reviewed.data()
	check(str(ProjectSettings.get_setting("application/config/version"))=="0.10.1","embedded version")
	ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.set_process(false);ui.game.new_game();ui.game.save_path="/private/tmp/recent-art-unused.json";ui.instant_mode=true
	for item in expected.inventory:
		var art:Dictionary=data.battle[item.key] if item.context=="battle" else data.maps[item.key][item.context]
		check(art.art_revision==item.revision,"active revision "+item.profile)
		var texture:Texture2D=load(art.path);check(texture!=null,"loaded "+item.profile)
		if texture==null:continue
		var image=texture.get_image();check(image.get_size()==Vector2i(item.size[0],item.size[1]),"atlas size "+item.profile)
		for slot in item.frame_hashes:
			var n=int(slot);var w=int(art.frame_size[0]);var h=int(art.frame_size[1]);var columns=int(art.columns)
			var rect=Rect2i(n%columns*w,floori(float(n)/columns)*h,w,h)
			check(visible_hash(image.get_region(rect))==item.frame_hashes[slot],"exact review pixels "+item.profile+"/"+slot);slots+=1
		if item.context!="battle":
			var actor={"id":"revision_actor","class_id":int(item.key.split("_")[0]),"side":"enemy" if item.key.ends_with("enemy") else "player","acted":false}
			var moving=item.context=="tactical-walk";ui.moving_id="revision_actor" if moving else ""
			for direction in [Vector2i.UP,Vector2i.RIGHT,Vector2i.DOWN,Vector2i.LEFT]:
				ui.moving_direction=direction;var selected=ui._map_unit_sprite(actor)
				check(selected.path==art.path and selected.has("native_cycle"),"runtime cycle "+item.profile+str(direction))
				var sum_ticks=0
				for tick in selected.cycle_ticks:sum_ticks+=int(tick)
				var cycle=[]
				for n in range(selected.native_cycle.size()):
					for tick in range(int(selected.cycle_ticks[n])):cycle.append(int(selected.native_cycle[n]))
				for tick in range(sum_ticks):
					ui.elapsed=(tick+0.1)/60.0988;check(ui._native_map_pose(selected)==cycle[tick],"map tick "+item.profile+str(tick))
			ui.moving_id="";continue
		var actor=ui.game.characters.hunapu.duplicate(true);actor.id="revision_actor";actor.class_id=art.reviewed_class_id;actor.side="enemy" if art.reviewed_side=="enemy" else "player";actor.hp=30;actor.max_hp=30;actor.acted=false
		var target=actor.duplicate(true);target.id="revision_target";target.side="player" if actor.side=="enemy" else "enemy"
		ui.game.units=[actor,target];var sample={}
		for source_key in art.reviewed_variants:
			var original:Dictionary=ui.graphics.battle["class_"+item.key]
			var base=str(source_key).split("_far_")[0].trim_suffix("_vs_heavy");var weapon=0
			for table in [original.get("weapon_variants",{}),original.get("spell_variants",{})]:
				for candidate in table:
					if str(table[candidate]).trim_prefix("fe2_")==base:weapon=int(candidate)
			target.class_id=7 if source_key.ends_with("_vs_heavy") else 6
			ui.combat={"attacker":actor.id,"defender":target.id,"distance":2 if "_far_" in source_key else 1,"initiative_side":"enemy" if "_far_enemy" in source_key else "player"}
			var event={"attacker":actor.id,"defender":target.id,"weapon_index":weapon,"critical":source_key.ends_with("_critical"),"hit":true,"hp_before":30,"hp_after":29}
			ui.battle_animation.active_event=event
			var chosen=ui.battle_animation.selection(event);var key=art.reviewed_variants[source_key]
			check(chosen.get("key","")==key,"variant selection "+source_key);variants+=1
			var variant:Dictionary=data.variants[key]
			check(int(variant.contact_tick)<int(variant.source_frame_count),"original contact before visual tail "+source_key)
			for row in variant.frames:
				check(int(row.frame)<int(art.frames),"valid body slot "+source_key)
				for e in row.get("effects",[]):check(data.sprites.has(str(e.sprite)) and ResourceLoader.exists(data.sprites[str(e.sprite)].path) and not str(e.sprite).ends_with("-target-reference"),"real effect "+str(e.sprite))
			if sample.is_empty():sample=event.duplicate(true)
		ui.battle_animation.reset();await ui.battle_animation.play(sample)
		check(ui.battle_animation.contact_calls==1 and target.hp==29,"single HP contact "+item.key)
		check(ui.battle_animation.effects.is_empty() and ui.combat_offsets[actor.id]==Vector2.ZERO,"clean return "+item.key)
		if int(art.reviewed_class_id)==15:
			ui.battle_animation.active_event=sample
			for cid in [1,4,6,15]:
				target.class_id=cid;ui.combat_offsets[target.id]=Vector2(3,-2)
				check(ui.battle_animation.effect_position({"position":[0,0],"bind_target":true})==ui.battle_animation.origin(target,ui.combat)+Vector2(3,-2),"slime binds actual target "+item.key+str(cid))
	for effect in expected.effects:
		var meta:Dictionary=data.sprites[effect.id];var texture:Texture2D=load(meta.path)
		check(texture!=null and visible_hash(texture.get_image())==effect.visible_hash,"exact effect "+effect.id)
	check(variants==int(expected.attack_variants),"all requested variants")
	var report={"passed":errors.is_empty(),"checks":checks,"slots":slots,"variants":variants,"errors":errors,"version":"0.10.1","headless":true}
	var f=FileAccess.open(OS.get_environment("RECENT_ART_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("RECENT_ART ",JSON.stringify(report));ui.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

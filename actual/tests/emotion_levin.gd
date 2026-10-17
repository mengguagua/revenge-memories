extends SceneTree
const Art=preload("res://core/hunapu_sprites.gd")
const CombatAnimation=preload("res://core/battle_animation.gd")
const State=preload("res://core/game_state.gd")
const Portraits=preload("res://core/portrait_library.gd")
class FakeAudio extends RefCounted:
	func play_request(_id):pass
class FakeGame extends RefCounted:
	var units=[]
	func find_unit(id):
		for unit in units:
			if unit.id==id:return unit
		return {}
class FakeUI extends RefCounted:
	var game=FakeGame.new()
	var audio=FakeAudio.new()
	var graphics={}
	var combat={}
	var combat_poses={}
	var combat_offsets={}
	var combat_hp={}
	var combat_fades={}
	var combat_message=""
	var combat_hit_id=""
	var combat_hit_time=0.0
	var elapsed=0.0
	var instant_mode=false
	var contacts=[]
	var trace=[]
	func _personal_battle_sprite(unit,original):return Art.battle(unit,original)
	func queue_redraw():pass
	func _wait(seconds):trace.append({"poses":combat_poses.duplicate(),"offsets":combat_offsets.duplicate(),"duration":seconds})
	func _contact(event):contacts.append(event);combat_hp[event.defender]=event.hp_after
var checks=[]
var failures=[]
func _initialize():call_deferred("run")
func check(ok: bool,label: String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func run():
	var graphics=State.read_json("res://data/legacy/graphics.json");var contract=State.read_json("res://source/hunapu-0.5.1/contract.json")
	check(Art.data().max_opaque_colors==12 and Art.data().palette.size()==12,"One shared twelve-color palette")
	for kind in ["map","hub","battle"]:
		var sprite=Art.sprite(kind);check(not sprite.is_empty(),"Personal resource loads: "+kind)
		if sprite.is_empty():continue
		var tex=load(sprite.path);var image=tex.get_image();var colors={};var alpha_ok=true
		for y in range(image.get_height()):
			for x in range(image.get_width()):
				var color=image.get_pixel(x,y)
				if color.a>0:colors[color.to_html(false)]=true
				if color.a!=0 and color.a!=1:alpha_ok=false
		check(colors.size()<=12 and alpha_ok,"Opaque palette and clean transparency: "+kind)
		check(tex.get_size()==Vector2(sprite.frame_size[0]*sprite.frames,sprite.frame_size[1]),"Exact source canvas contract: "+kind)
	var g=State.new();g.new_game();var hero=g.roster.hunapu.duplicate(true);hero.side="player"
	check(Art.applies(hero),"Unpromoted Hunapu receives personal art")
	for other in [g.roster.otto,g.roster.daan,{"id":"illusion","side":"player","class_id":21},{"id":"hunapu","side":"enemy","class_id":21},{"id":"hunapu","side":"player","class_id":21,"promoted":true}]:check(not Art.applies(other),"No art/ability leakage to "+str(other.get("id",""))+":"+str(other.get("side",""))+":"+str(other.get("promoted",false)))
	var ui=FakeUI.new();ui.graphics=graphics
	var foe=g.stages[101].enemies[1].duplicate(true);foe.id="foe";foe.side="enemy"
	ui.game.units=[hero,foe];ui.combat={"attacker":"hunapu","defender":"foe","distance":1,"initiative_side":"player"}
	var animation=CombatAnimation.new(ui);var art=animation.sprite(hero);var original=graphics.battle.class_21_ally
	check(art.path!=original.path and art.attack_schedule.native_timeline==original.attack_schedule.native_timeline and art.weapon_variants==original.weapon_variants,"Native class metadata and weapon variants retained")
	check(art.frame_size==original.frame_size and art.anchor==original.anchor and art.sequences==original.sequences and art.oam_flip_origin_offset==original.oam_flip_origin_offset,"Frame IDs, feet, mirroring and idle contract unchanged")
	check(original.attack_schedule.native_timeline==contract.timeline,"Original generic authored table retained for other actors")
	var critical=State.read_json("res://source/clarity-0.5.2/critical-timeline.json")
	check(art.personal_source_programs.critical.source_program_address==critical.source_program,"Original independent critical program restored: L05B3A9")
	var executed=State.read_json("res://source/clarity-0.5.2/executed-melee.json")
	check(art.personal_source_programs==executed.programs,"Full source interpreter execution includes dispatch and wait ticks")
	var native=load("res://assets/original/graphics/battle/class_21_ally.png").get_image()
	var personal=load(Art.sprite("battle").path).get_image();var geometry_ok=true
	for y in range(native.get_height()):
		for x in range(native.get_width()):
			if x/80 not in range(120,125) and native.get_pixel(x,y).a!=personal.get_pixel(x,y).a:geometry_ok=false
	check(geometry_ok,"All 128 unchanged source alpha masks retain exact hand/leg gaps")
	for frame in range(120,125):
		var cumulative=Image.load_from_file("res://source/emotion-levin-0.5.3/levin-source-"+str(frame)+".png")
		var exact=true;var body_pixels=0
		for y in range(72):
			for x in range(80):
				var pixel=personal.get_pixel(frame*80+x,y)
				if pixel.a!=cumulative.get_pixel(x,y).a:exact=false
				if y>=40 and y<65 and pixel.a==1:body_pixels+=1
		check(exact and body_pixels>90,"Complete native cumulative body and feet: "+str(frame))
	var before_roster=g.roster.duplicate(true)
	var expressions=JSON.parse_string(FileAccess.get_file_as_string("res://reports/emotion-levin-0.5.3/portrait-manifest.json"))
	var face_hashes={}
	for row in expressions:
		var face=Portraits.entry(row.key);var image=load(face.path).get_image()
		check(image.get_size()==Vector2i(48,48),"Native expression loads: "+str(row.key))
		image.convert(Image.FORMAT_RGBA8)
		face_hashes[image.get_data().hex_encode().sha256_text()]={"key":row.key,"path":face.path,"bytes":image.get_data().size()}
	if face_hashes.size()!=6:print("EXPRESSION_DIGESTS ",face_hashes)
	check(face_hashes.size()==6,"Six expressions are visually distinct native images")
	for scene in ["D00","D11","D12","D13"]:
		g.hub_record="P00" if scene=="D00" else "H01";g.flags.erase("korlan_defeated")
		for page in g.campaign.scenes[scene]:
			if page.speaker!="胡纳普":continue
			var face=Portraits.speaker(g,page.speaker,Portraits.dialogue_emotion(page))
			check(face.key.ends_with("_"+str(page.emotion)),"Authored scene expression: "+scene+" / "+str(page.emotion))
			var old=page.duplicate();old.erase("emotion");old.text=str(old.text).replace("。","。\n")
			check(Portraits.dialogue_emotion(old)==page.emotion,"Old active dialogue emotion fallback: "+scene+" / "+str(page.emotion))
	check(g.roster==before_roster,"Expression lookups preserve growth EXP gear and roster")
	for frame in Art.data().active_battle_frames:check(ResourceLoader.exists("res://assets/hunapu-0.5.3/frames/battle-"+str(int(frame))+".png"),"All visible body/effect frames registered: "+str(int(frame)))
	var scenarios=[]
	for row in [[0,1,false,false],[15,1,false,false],[15,2,false,false],[0,1,true,false],[0,1,false,true]]:
		ui.contacts.clear();ui.trace.clear();animation.reset();ui.combat.distance=row[1]
		hero.item_id=15 if row[0]==15 else 59
		var event={"attacker":"hunapu","defender":"foe","weapon_index":row[0],"distance":row[1],"hit":not row[2],"critical":row[3],"damage":5 if not row[2] else 0,"hp_before":foe.hp,"hp_after":foe.hp-5 if not row[2] else foe.hp,"source_hp_before":hero.hp,"source_hp_after":hero.hp,"visual_only":true}
		var chosen=animation.selection(event)
		check(chosen.kind=="source","Executed original program selected: "+str(row))
		await animation.play(event)
		if row[0]==0:
			var expected=chosen.variant.frames;var same=ui.trace.size()==expected.size()+1
			for tick in range(mini(expected.size(),ui.trace.size())):
				if ui.trace[tick].poses.hunapu!=int(expected[tick].frame) or ui.trace[tick].offsets.hunapu!=Vector2(expected[tick].offset[0],expected[tick].offset[1]):same=false
			check(same,"Every approach/return pose and XY tick matches source: "+str(row))
		check(ui.contacts.size()==1 and animation.contact_calls==1,"Exactly one contact, including miss: "+str(row))
		check(animation.effects.is_empty() and ui.combat_offsets.hunapu==Vector2.ZERO and ui.combat_poses.hunapu==60,"Original recovery to idle: "+str(row))
		if row[0]==0:check(ui.trace.size()==(264 if row[3] else 204),"All original executed normal/critical ticks plus recovery wait executed")
		else:check(ui.trace.size()==299,"All original 298 Levin ticks plus recovery wait executed")
		scenarios.append({"weapon":row[0],"distance":row[1],"miss":row[2],"critical":row[3],"contacts":animation.contact_calls,"waits":ui.trace.size()})
	check(animation.sprite(foe).path==graphics.battle.class_6_enemy.path,"Enemy renderer retains original class sheet")
	var effect_source=State.read_json("res://data/legacy/full_animation_effects.json")
	for suffix in ["","_vs_heavy","_far_ally","_far_ally_vs_heavy","_far_enemy","_far_enemy_vs_heavy"]:
		var variant=effect_source.variants["class_21_ally_levin"+suffix];var held_ticks=0
		for frame in variant.frames:
			if int(frame.frame)==124:held_ticks+=1
		check(variant.frames.size()==298 and variant.contact_tick==226 and variant.contact_count==1 and held_ticks==208,"Levin body persists for all original near/far/heavy hold ticks: "+suffix)
	var report={"passed":failures.is_empty(),"checks":checks.size(),"labels":checks,"failures":failures,"scenarios":scenarios,"scope":"Explicit animation/palette/identity fixtures; same source timeline, offsets, frames, contact count and cleanup. Not natural battle victories."}
	var f=FileAccess.open("res://reports/emotion-levin-0.5.3/animation-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("HUNAPU_ANIMATION ",checks.size()," FAILURES ",failures);quit(0 if failures.is_empty() else 1)

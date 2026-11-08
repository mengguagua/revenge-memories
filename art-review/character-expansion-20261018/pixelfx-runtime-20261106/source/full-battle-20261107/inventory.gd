extends SceneTree
const State=preload("res://core/game_state.gd")
const Items=preload("res://core/item_rules.gd")
const ROOT="/Users/gcc/gaocc/project/revenge-memories/art-review/character-expansion-20261018/pixelfx-runtime-20261106/source/full-battle-20261107/"
var ui;var phone;var vp;var jobs=[];var skipped=[];var errors=[];var seen={}
func _initialize():call_deferred("run")
func unit_for(profile:String,cid:int,side:String)->Dictionary:
	var u=ui.game._initial_character("eileen" if profile.begins_with("eileen") else "hunapu" if profile in ["21_ally","23_ally"] else "daan").duplicate(true)
	if profile in ["eileen_promoted","23_ally"]:ui.game.HeroProfessions.apply(u)
	elif not profile.begins_with("eileen") and profile!="21_ally":
		u.id="preview_"+profile;u.class_id=cid;u.character_id=0;u.name_id=0;u.promoted=false
		u.name_zh=str(ui.game.catalog.classes.get(str(cid),{}).get("enemy_name_zh" if side=="enemy" else "name_zh","职业"+str(cid)))
	u.side="enemy" if side=="enemy" else "player";u.position=[5,5];u.hp=40;u.max_hp=40;u.strength=12;u.skill=30;u.speed=8;u.defence=4;u.resistance=4;u.luck=0;u.item_id=0;u.level=10;u.exp=0;u.acted=false;u.magic_flags=255;u.raw_magic_flags=255
	u.erase("weapon_index");u.erase("temporary");u.erase("neutral");u.erase("body_attack")
	if profile not in ["eileen_promoted","23_ally"]:u.erase("hero_profession")
	if side=="enemy" and cid==21:u.campaign_final_boss=true
	return u
func setup(c:Dictionary)->Dictionary:
	var actor=unit_for(str(c.profile),int(c.class_id),str(c.side));var support=int(c.weapon) in [40,41,43,44]
	var target_side=str(c.side) if support else "ally" if c.side=="enemy" else "enemy"
	var target=unit_for(("4" if c.heavy else "6")+"_"+target_side,4 if c.heavy else 6,target_side);target.id="preview_target";target.name_zh="骑士" if c.heavy else "士兵";target.position=[6,5]
	if int(c.weapon)>=1000:actor.innate_attack_index=int(c.weapon)
	else:actor.weapon_index=int(c.weapon)
	if int(c.weapon)==1002:actor.body_attack="stone_spit"
	if int(c.weapon)==1005:actor.innate_counter=true
	if support:target.hp=20
	if int(c.weapon)==42:actor.hp=24
	ui.game.units=[actor,target]
	var distance=2 if not str(c.far).is_empty() else 1
	if int(c.weapon)==1004:distance=2
	var initiative="player" if c.far=="ally" else "enemy" if c.far=="enemy" else str(actor.side)
	if int(c.weapon)==1005:initiative="player"
	ui.combat={"attacker":actor.id if actor.side==initiative else target.id,"defender":target.id if actor.side==initiative else actor.id,"distance":distance,"initiative_side":initiative,"support":support}
	var event={"attacker":actor.id,"defender":target.id,"weapon_index":int(c.weapon),"distance":distance,"critical":bool(c.critical),"hit":true,"damage":7,"hp_before":int(target.hp),"hp_after":int(target.hp)-7,"source_hp_before":int(actor.hp),"source_hp_after":int(actor.hp),"hp_cost":0,"feedback_only":true}
	if support:
		event.visual_only=true;event.damage=0;event.hp_before=20;event.hp_after=20 if int(c.weapon)==43 else 32;event.hp_cost=Items.cost_for(actor,int(c.weapon));event.source_hp_after=int(actor.hp)-int(event.hp_cost)
	else:
		var result=ui.game.Rules.strike_effect(actor,target,true,bool(c.critical),99,distance,0)
		event.merge(result,true);event.hp_after=int(target.hp)-int(result.damage);event.source_hp_after=int(actor.hp)-int(result.hp_cost)+int(result.heal)
	ui.battle_animation.reset();ui.battle_animation.active_event=event
	var chosen=ui.battle_animation.selection(event)
	return {"actor":actor,"target":target,"event":event,"exchange":ui.combat.duplicate(true),"selected":chosen}
func run():
	vp=SubViewport.new();vp.size=Vector2i(1184,480);root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(0,0,1184,480);phone.journal_directory_override="/private/tmp/pixelfx-full-inventory/slots";vp.add_child(phone)
	await process_frame;ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);phone.set_process(false);ui.audio.stop_all();ui.game.new_game()
	var source=JSON.parse_string(FileAccess.get_file_as_string(ROOT+"candidates.json"))
	for c in source.candidates:
		var s=setup(c);var selected=s.selected;var kind=str(selected.get("kind","missing"));var key=str(selected.get("key",""))
		if str(c.family)=="support" and not str(c.far).is_empty():
			skipped.append({"candidate":c,"actual_kind":"support_fixed_closeup","actual_program":"","reason":"Current support controller always uses its fixed distance-1 close-up."});continue
		if int(c.weapon) in [35,36,37,45,46]:
			skipped.append({"candidate":c,"actual_kind":"map_feedback","actual_program":"","reason":"Current support controller routes this spell to the tactical-map renderer."});continue
		if int(c.weapon)>=23 and int(c.weapon)<=46 and not Items.spells(s.actor).has(int(c.weapon)):
			skipped.append({"candidate":c,"actual_kind":"not_in_class_spell_table","actual_program":"","reason":"Not an available spell for this class in the current rules."});continue
		if kind=="source" and key==str(c.expected_program):
			var identity=str(c.profile)+"|"+key+"|"+str(c.far)+"|"+str(c.heavy)
			if seen.has(identity):continue
			seen[identity]=true
			var j=c.duplicate(true);j.kind=kind;j.program=key;j.source_frames=selected.variant.frames.size();j.fps=float(selected.variant.get("native_fps",60.0988));j.contact_tick=int(selected.variant.contact_tick);j.actor=s.actor.duplicate(true);j.target=s.target.duplicate(true);j.event=s.event.duplicate(true);j.exchange=s.exchange.duplicate(true);j.graphic=selected.sprite.duplicate(true)
			jobs.append(j)
		else:skipped.append({"candidate":c,"actual_kind":kind,"actual_program":key,"reason":"Current selection routes this alias elsewhere or to a fallback; not presented as a distinct reachable program."})
	var f=FileAccess.open(ROOT+"inventory.json",FileAccess.WRITE);f.store_string(JSON.stringify({"jobs":jobs,"skipped":skipped,"raw_programs":source.raw_programs,"profiles":source.profiles,"candidate_count":source.candidates.size(),"errors":errors},"  "));f.close()
	print("INVENTORY active=",jobs.size()," other_routes=",skipped.size())
	ui.audio.stop_all();phone.queue_free();await process_frame;vp.queue_free();await process_frame;quit()

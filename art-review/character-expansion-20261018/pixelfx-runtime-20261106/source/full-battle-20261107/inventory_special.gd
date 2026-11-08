extends "./inventory.gd"
var special=[]
func register(actor:Dictionary,target:Dictionary,weapon:int,critical:bool,family:String,label:String,id:String,extras:Dictionary={}):
	ui.battle_animation.reset();actor=actor.duplicate(true);target=target.duplicate(true)
	ui.game.units=[actor,target];var distance=int(extras.get("distance",1));var initiative=str(extras.get("initiative",actor.side))
	ui.combat={"attacker":actor.id if actor.side==initiative else target.id,"defender":target.id if actor.side==initiative else actor.id,"distance":distance,"initiative_side":initiative,"support":false}
	var hit=extras.get("reaction","")!="miss";var result=ui.game.Rules.strike_effect(actor,target,hit,critical,int(extras.get("roll",99)),distance,0)
	var event={"attacker":actor.id,"defender":target.id,"weapon_index":weapon,"distance":distance,"critical":critical,"hit":hit,"hp_before":int(target.hp),"hp_after":int(target.hp)-int(result.damage),"source_hp_before":int(actor.hp),"source_hp_after":int(actor.hp)-int(result.hp_cost)+int(result.heal),"feedback_only":true};event.merge(result,true)
	if int(result.self_damage)>0:event.source_hp_after=maxi(0,int(actor.hp)-int(result.hp_cost)-int(result.self_damage))
	ui.game.Mechanical.reflect(event,actor,target)
	ui.battle_animation.active_event=event.duplicate(true);var selected=ui.battle_animation.selection(event)
	if not bool(result.valid):errors.append("Invalid "+id)
	if selected.get("kind","") not in ["source","critical_cinema"]:errors.append("No selected program "+id);return
	var j={"id":id,"profile":extras.get("profile",str(actor.get("class_id",0))+"_"+("enemy" if actor.side=="enemy" else "ally")),"class_id":int(actor.class_id),"side":"enemy" if actor.side=="enemy" else "ally","family":family,"label":label,"weapon":weapon,"far":extras.get("far",""),"heavy":int(target.class_id) in [4,7],"critical":critical,"actor":actor.duplicate(true),"target":target.duplicate(true),"event":event.duplicate(true),"exchange":ui.combat.duplicate(true),"kind":selected.kind,"program":selected.key,"alias":id,"reaction":extras.get("reaction",""),"target_profile":extras.get("target_profile","")}
	if selected.kind=="source":j.source_frames=selected.variant.frames.size();j.contact_tick=selected.variant.contact_tick;j.fps=selected.variant.native_fps;j.graphic=selected.sprite.duplicate(true)
	else:j.source_frames=0;j.contact_tick=-1;j.fps=60
	j.target_graphic=ui.battle_animation.sprite(target).duplicate(true)
	special.append(j)

func run():
	vp=SubViewport.new();vp.size=Vector2i(1184,480);root.add_child(vp)
	phone=load("res://scenes/phone.tscn").instantiate();phone.safe_area_override=Rect2(0,0,1184,480);phone.journal_directory_override="/private/tmp/pixelfx-special-inventory/slots";vp.add_child(phone)
	await process_frame;ui=phone.game_ui;ui.set_process(false);ui.set_physics_process(false);phone.set_process(false);ui.audio.stop_all();ui.game.new_game()
	var art=JSON.parse_string(FileAccess.get_file_as_string("res://data/reviewed_animations.json"))
	for profile in art.battle:
		var g=art.battle[profile];var side=str(g.get("reviewed_side","ally"));var cid=int(g.reviewed_class_id)
		for kind in ["hit","miss","exit"]:
			var target=unit_for(profile,cid,side)
			# Eileen's reviewed body is keyed by her actual ID, not merely class 11.
			if profile not in ["eileen","eileen_promoted","21_ally","23_ally"]:target.id="preview_target"
			target.hp=8 if kind=="exit" else 40
			var actor=unit_for("8_ally" if side=="enemy" else "8_enemy",8,"ally" if side=="enemy" else "enemy");actor.weapon_index=0
			register(actor,target,0,false,"reaction",str(target.name_zh)+" · "+{"hit":"受击","miss":"闪避","exit":"退场"}[kind],"reaction-"+profile+"-"+kind,{"reaction":kind,"target_profile":profile,"profile":profile})
	var cinema=ui.battle_animation.CriticalCinema.data()
	var recoil_actor=unit_for("8_ally",8,"ally");recoil_actor.weapon_index=14
	var ordinary_target=unit_for("6_enemy",6,"enemy");ordinary_target.id="preview_target"
	register(recoil_actor,ordinary_target,14,false,"sword","佣兵 · 魔剑反噬","outcome-recoil",{"roll":0,"profile":"8_ally"})
	var crit_actor=unit_for("9_ally",9,"ally");crit_actor.weapon_index=0;crit_actor.strength=6
	register(crit_actor,ordinary_target,0,true,"sword","剑士 · 普通必杀","outcome-critical",{"profile":"9_ally"})
	for key in cinema.cases:
		var advanced=str(key).ends_with("-advanced");var eileen=str(key).begins_with("eileen");var profile=("eileen_promoted" if advanced else "eileen") if eileen else ("23_ally" if advanced else "21_ally")
		var actor=unit_for(profile,11 if eileen else 21,"ally");actor.strength=6
		var weapon=1 if "bow" in key else 23 if "fire" in key else 24 if "thunder" in key else 26 if "holy" in key else 27 if "wind" in key else 0;actor.weapon_index=weapon
		var target=unit_for("6_enemy",6,"enemy");target.id="preview_target"
		register(actor,target,weapon,true,"cinema",str(actor.name_zh)+(" · 进阶必杀" if advanced else " · 必杀"),"cinema-"+key,{"profile":profile,"distance":2 if weapon==1 else 1})
	for far in ["","ally","enemy"]:
		for heavy in [false,true]:
			var actor=unit_for("6_enemy",6,"enemy");actor.weapon_index=4;actor.guard_counter=true;actor.behavior="guard"
			var target=unit_for("4_ally" if heavy else "6_ally",4 if heavy else 6,"ally");target.id="preview_target"
			register(actor,target,4,false,"javelin","士兵 · 守备反击","counter-"+("near" if far.is_empty() else far)+("-heavy" if heavy else ""),{"far":far,"distance":1 if far.is_empty() else 2,"initiative":"enemy" if far=="enemy" else "player","profile":"6_enemy"})
	var states=[]
	for stage in [201,205]:
		ui.game.save_path="res://reports/full-assessment-20261025/campaign-final-r4/ch2/chain-F%d-deployment.json"%(21 if stage==201 else 25)
		if not ui.game.load_game() or not ui.game.start_battle(stage):errors.append("Mechanical fixture load");continue
		var monster=ui.game.find_unit("F21_water_monkey_1" if stage==201 else "F25_pseudo_titan_1").duplicate(true)
		var hero=ui.game.find_unit("eileen").duplicate(true);hero.item_id=0;hero.weapon_index=0;hero.hp=hero.max_hp
		for broken in [false,true]:
			var actor=monster.duplicate(true);var part=ui.game.Mechanical.part_key(actor)
			if broken:actor.parts[part].hp=0
			actor.innate_attack_index=1007 if stage==201 else 1009;actor.hp=actor.max_hp
			var key=("water-monkey" if stage==201 else "titan")+("-broken" if broken else "-intact")
			register(actor,hero,int(actor.innate_attack_index),false,"mechanical",str(actor.name_zh)+(" · 破损掌击" if broken and stage==201 else " · 破损锤击" if broken else " · 掌击" if stage==201 else " · 锤击"),"mechanical-"+key,{"profile":str(actor.class_id)+"_enemy"})
			for kind in ["hit","exit"]:
				var target=actor.duplicate(true);target.hp=1 if kind=="exit" else target.max_hp
				register(hero,target,0,false,"reaction",str(target.name_zh)+(" · 破损" if broken else " · 完好")+("受击" if kind=="hit" else "退场"),"reaction-"+key+"-"+kind,{"reaction":kind,"target_profile":str(actor.class_id)+"_enemy","profile":str(actor.class_id)+"_enemy"})
	var f=FileAccess.open(ROOT+"inventory-special.json",FileAccess.WRITE);f.store_string(JSON.stringify({"jobs":special,"errors":errors},"  "));f.close();print("SPECIAL ",special.size()," errors=",errors)
	ui.audio.stop_all();phone.queue_free();await process_frame;vp.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)

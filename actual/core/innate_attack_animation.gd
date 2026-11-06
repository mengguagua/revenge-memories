extends RefCounted
## One body action per resolved strike. Poses and bitmap effects never add damage.
const CampaignArt=preload("res://core/campaign_art.gd")
const Body=preload("res://core/innate_attacks.gd")
const Reviewed=preload("res://core/reviewed_animations.gd")
static var art:Dictionary={}

static func sprite(unit:Dictionary,original:Dictionary) -> Dictionary:
	if not Body.is_body(unit):return original
	if original.has("innate_variants") and CampaignArt.valid(original):
		var reviewed = original.duplicate(true)
		if int(unit.class_id)==21 and int(unit.get("hp",0))*2<=int(unit.get("max_hp",0)):
			reviewed.sequences.idle=[int(reviewed.get("empowered_idle",reviewed.sequences.idle[0]))]
		return reviewed
	if art.is_empty() and FileAccess.file_exists("res://data/innate_attack_art.json"):
		art=JSON.parse_string(FileAccess.get_file_as_string("res://data/innate_attack_art.json"))
	var result:Dictionary=art.get(str(int(unit.class_id)),original).duplicate(true)
	if not CampaignArt.valid(result):return CampaignArt.battle(unit)
	# The recovered bone-dragon sheet already contains an unarmed jaw/body.
	if int(unit.class_id)==5 and not art.has("5"):
		result.pose_map={"idle":41,"prepare":17,"release":19,"recover":18,"bite_prepare":17,"bite_contact":19,"hurt":41,"empowered":41}
	if int(unit.class_id)==21 and int(unit.get("hp",0))*2<=int(unit.get("max_hp",0)):
		result.sequences.idle=[int(result.get("pose_map",{}).get("empowered",7))]
	return result

static func horizontal_flip(graphic:Dictionary,left:bool,action_flip:bool=false) -> bool:
	return (left != (graphic.get("default_facing","left")=="right")) != action_flip

static func safe_origin(graphic:Dictionary,desired:Vector2) -> Vector2:
	var width=float(graphic.frame_size[0])/maxf(1.0,float(graphic.get("native_density",1)))
	var anchor=float(graphic.anchor[0])
	return Vector2(clampf(desired.x,anchor+8,256-(width-anchor)-8),desired.y)

static func effect_sprites() -> Dictionary:
	return {"innate_stone":{"path":"res://assets/nature/stone_low.png","frame_size":[32,16],"frames":1,"anchor":[8,4],"native_density":2.0},
		"innate_glow":{"path":"res://assets/reviewed-animation-20261018/effects/review-halo-ally-charge-8198b40abef726.png","frame_size":[288,192],"frames":1,"columns":1,"anchor":[12,8],"logical_frame_size":[24,16],"native_density":4.0},
		"innate_breath":{"path":"res://assets/reviewed-animation-20261018/effects/review-ghost-fire-enemy-flight-ca271c883ab5b7.png","frame_size":[192,64],"frames":1,"anchor":[24,8],"native_density":4.0}}

static func selection(graphic:Dictionary,event:Dictionary,actor_origin:Vector2,target_origin:Vector2,left:bool) -> Dictionary:
	var index=int(event.get("weapon_index",0))
	if not Body.PROFILES.has(index):return {}
	if graphic.has("innate_variants"):
		var key = str(index)
		if absf(target_origin.x-actor_origin.x)>128 and graphic.innate_variants.has(key+"_far"):key+="_far"
		var runtime_key = str(graphic.innate_variants.get(key,""))
		if runtime_key.is_empty():return {}
		var variant:Dictionary=Reviewed.variant(runtime_key).duplicate(true)
		var source_origin=Vector2(variant.review_origin[0],variant.review_origin[1])
		var source_target=source_origin+Vector2(176 if key.ends_with("_far") else 112,0)
		var source_span=source_target.x-source_origin.x
		var target_span=absf(target_origin.x-actor_origin.x)
		# Review enemies stand on the left. Translate/mirror their complete
		# timeline into the real exchange; keep its one existing contact.
		for row in variant.frames:
			row.offset[0]*=(1 if left else -1)*(target_span-42)/(source_span-42) if index in [Body.STONE_CLAW,Body.BONE_BITE,Body.WING_BEAK] else (1 if left else -1)
			for effect in row.get("effects",[]):
				var x=float(effect.position[0])-source_origin.x
				var emission=24.0 if index==Body.SUN_CROWN else 32.0
				var progress=clampf((x-emission)/(source_span-10-emission),0.0,1.0)
				effect.position[0]=actor_origin.x+(x+(target_span-source_span)*progress)*(1 if left else -1)
				effect.position[1]+=actor_origin.y-source_origin.y
				if not left:effect.flip=not bool(effect.get("flip",false))
		return {"kind":"source","key":runtime_key,"sprite":graphic,"variant":variant}
	var poses:Dictionary=graphic.get("pose_map",{"idle":0,"prepare":1,"release":2,"recover":3,"bite_prepare":4,"bite_contact":5})
	var melee=index in [Body.STONE_CLAW,Body.BONE_BITE,Body.WING_BEAK]
	# Stone dives quickly; bone jaws hold a longer, heavy preparation.
	var preparation=12 if index==Body.STONE_CLAW else 24 if index==Body.BONE_BITE else 20
	var contact=preparation+14
	var total=contact+20
	var frames=[]
	var direction=1.0 if left else -1.0
	var emission=Vector2(24,-71) if index==Body.SUN_CROWN else Vector2(32,-44)
	var mouth=actor_origin+Vector2(direction*emission.x,emission.y)
	var impact=target_origin+Vector2(-direction*10,-28)
	for tick in range(total):
		var pose=int(poses.get("idle",0));var offset=Vector2.ZERO;var effects=[]
		if tick<preparation:
			pose=int(poses.get("bite_prepare" if melee else "prepare",0))
			offset=Vector2(-direction*3.0*float(tick)/preparation,-2 if index==Body.STONE_CLAW else 0)
			if index==Body.SUN_CROWN and tick>=preparation-8:effects.append({"sprite":"innate_glow","position":[mouth.x,mouth.y],"flip":false})
		elif tick<=contact:
			pose=int(poses.get("bite_contact" if melee else "release",0))
			var progress=float(tick-preparation)/14.0
			if melee:
				offset=Vector2(direction*(absf(target_origin.x-actor_origin.x)-42)*progress,-sin(progress*PI)*12 if index==Body.STONE_CLAW else 0)
			else:
				var point=mouth.lerp(impact,progress)
				var kind="innate_stone" if index==Body.STONE_SPIT else "innate_breath" if index==Body.ERODING_BREATH else "innate_glow"
				effects.append({"sprite":kind,"position":[point.x,point.y],"flip":left,"tint":[0.65,0.9,0.65,1] if index==Body.ERODING_BREATH else [1,1,1,1]})
				# One pure golden-white light orb travels from crown to impact; no creature sprites.
		else:
			pose=int(poses.get("recover",0))
			if melee:offset=Vector2(direction*(absf(target_origin.x-actor_origin.x)-42)*(1.0-float(tick-contact)/20),0)
			if tick<contact+5 and index in [Body.STONE_CLAW,Body.STONE_SPIT]:
				effects.append({"sprite":"innate_stone","position":[impact.x+direction*(tick-contact),impact.y+(tick-contact)*2],"flip":left})
		frames.append({"frame":pose,"offset":[offset.x,offset.y],"flip":false,"effects":effects})
	return {"kind":"source","key":"innate_"+str(index),"sprite":graphic,"variant":{"native_fps":50,"contact_tick":contact,"frames":frames}}

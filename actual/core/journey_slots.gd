extends RefCounted
## Five independent journals. Legacy single-file saves appear in slot 1 until
## that slot is first written; the legacy source is never moved or overwritten.
const COUNT := 5
const LEGACY := "revenge-memories-ch1.json"

static func path_for(directory: String, slot: int) -> String:
	return directory.path_join("journey-slot-%d.json" % slot) if slot >= 1 and slot <= COUNT else ""

static func timestamp(unix: int) -> String:
	if unix <= 0:return "时间未记录"
	var local=unix+int(Time.get_time_zone_from_system().bias)*60
	return Time.get_datetime_string_from_unix_time(local).replace("T"," ").left(16)

static func duration(seconds: float) -> String:
	var minutes=maxi(0,int(seconds)/60)
	return "%02d:%02d" % [minutes/60,minutes%60]

static func info(game, slot: int) -> Dictionary:
	var path=path_for(game.slot_directory,slot)
	var legacy=false
	if slot==1 and not FileAccess.file_exists(path):
		var old=game.slot_directory.path_join(LEGACY)
		if FileAccess.file_exists(old):path=old;legacy=true
	var result={"slot":slot,"path":path,"exists":FileAccess.file_exists(path),"valid":false,"legacy":legacy,"time":"","location":"","chapter":"","seconds":0.0}
	if not result.exists:return result
	var state=game.read_json(path)
	result.valid=game.SaveValidation.campaign_valid(game,state,game.SAVE_FIELDS)
	if not result.valid:
		result.time=timestamp(FileAccess.get_modified_time(path));return result
	var meta=state.get("journal",{})
	if not meta is Dictionary:meta={}
	var recorded=meta.get("saved_unix",FileAccess.get_modified_time(path))
	if not (recorded is float or recorded is int):recorded=FileAccess.get_modified_time(path)
	result.time=timestamp(int(recorded))
	var seconds=meta.get("play_seconds",0.0)
	result.seconds=maxf(0.0,float(seconds)) if seconds is float or seconds is int else 0.0
	result.chapter="序章" if str(state.get("hub_record",""))=="P00" else ["","第一章","第二章","第三章","第四章"][clampi(int(state.chapter),1,4)]
	result.location="海峡城庆典" if result.chapter=="序章" else str(game.formal_world.nodes.get(str(int(state.world_node)),{}).get("name_zh","旅途中"))
	if str(state.mode) in ["battle","victory","defeat"]:result.location=str(game.stages[int(state.stage_id)].get("name_zh",result.location))
	result.route="东队" if str(state.route)=="celica" else "西队"
	result.mode=str(state.mode)
	return result

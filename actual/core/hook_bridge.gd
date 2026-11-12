extends RefCounted

const ATLAS="res://assets/ship-hulls-20261109/F22-hook-bridge-frames.png"
const FRAME_SIZE=Vector2(128,96)
const FRAME_TIMES=[0.0,0.0,0.10,0.18,0.24,0.30,0.36,0.50,0.62,0.71,0.80,0.89,0.98,1.12]
const DURATION=1.29

static func closed_at(g,cell:Vector2i)->bool:
	var target: Array=g.battle_data.get("hook_bridge",{}).get("target",[])
	return not target.is_empty() and cell==Vector2i(target[0],target[1]) and not g.flags.quest.objects.get("reserve_bridge",false)

static func frame_at(seconds:float)->int:
	for i in range(FRAME_TIMES.size()-1,0,-1):
		if seconds>=FRAME_TIMES[i]:return i
	return 0

static func region(frame:int)->Rect2:
	return Rect2(Vector2(frame%7,floori(float(frame)/7))*FRAME_SIZE,FRAME_SIZE)

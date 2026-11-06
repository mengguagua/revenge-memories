extends RefCounted
## Battle-only physical defence. The absolute expiry is safe across saves and rewind.
const BONUS=2
const ICON="res://assets/healer-map-20261104/strong-body.png"

static func bonus(unit:Dictionary)->int:
	return BONUS if int(unit.get("strong_body_until_turn",0))>0 else 0

static func remaining(unit:Dictionary,turn:int)->int:
	return clampi(int(unit.get("strong_body_until_turn",0))-turn,0,2)

static func apply(unit:Dictionary,turn:int)->void:
	unit.strong_body_until_turn=turn+2

static func clear(unit:Dictionary)->void:
	unit.erase("strong_body_until_turn")

static func expire_at_player_start(g)->void:
	if g.phase!="player":return
	for unit in g.units:
		if int(unit.get("strong_body_until_turn",0))<=int(g.turn):clear(unit)

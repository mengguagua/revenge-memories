extends RefCounted
## Shared by save validation and the visual controller; no UI dependencies.
const VERSION=1
const STEP_COUNT=11
static func number(value) -> bool:
	return typeof(value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(value)) and float(value)>=0
static func valid(value) -> bool:
	if not value is Dictionary:return false
	if not number(value.get("version")) or float(value.version)!=VERSION:return false
	if not number(value.get("step")) or float(value.step)!=floor(float(value.step)) or float(value.step)>=STEP_COUNT:return false
	if not number(value.get("time")) or not number(value.get("clock")):return false
	if not value.get("sounds") is Dictionary:return false
	for key in value.sounds:
		if key not in ["cast","block","curtain"] or not value.sounds[key] is bool:return false
	return true

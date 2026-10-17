extends "res://tests/art_play.gd"
func _initialize():
	if OS.get_environment("CHRONO_BACKGROUND_GUARD_ACTIVE")!="1":quit(1);return
	party_round=1;polish_round=1;polish_label="map-identity-0.7.2"
	polish_codes=["M11","F21"]
	review_out="res://reports/current-art/play/"
	call_deferred("run")
func write_review():
	super.write_review()
	var path=review_out+"play-checks.json";var data=State.read_json(path)
	data.version="0.7.2";data.scope="One targeted keyboard-play round through M11 and F21, actual actor-specific map appearances and unchanged combat bodies. No edits to growth, equipment, HP, positions or RNG; no forced victories."
	var file=FileAccess.open(path,FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "));file.close()

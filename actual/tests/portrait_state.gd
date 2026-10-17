extends SceneTree
const State=preload("res://core/game_state.gd")
const Portraits=preload("res://core/portrait_library.gd")
var checks=[]
var failures=[]
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func _initialize() -> void:call_deferred("run")
func run() -> void:
	var g=State.new();g.new_game();var records=[]
	check(Portraits.data().assets.size()>=g.characters.size(),"Portrait catalogue covers current formal companions")
	for key in Portraits.data().assets:
		var face=Portraits.entry(key)
		check(not face.is_empty(),"Portrait resource exists: "+key)
		if face.is_empty():continue
		var texture=load(face.path)
		check(texture.get_size()==Vector2(48,48),"Native 48x48 slot: "+key)
		records.append({"key":key,"path":face.path,"width":48,"height":48,"bytes":FileAccess.get_file_as_bytes(face.path).size()})
	for stage_id in g.stages:
		g.stage_id=stage_id;g.chapter=int(g.stages[stage_id].chapter)
		for actor in g.stages[stage_id].enemies+g.stages[stage_id].reinforcements+g.stages[stage_id].npc_units:
			check(not Portraits.unit(g,actor).is_empty(),"Live troop/NPC has new portrait: "+str(g.stages[stage_id].code)+":"+str(actor.id))
	for id in g.characters:
		check(not Portraits.unit(g,{"id":id}).is_empty(),"Formal companion portrait: "+id)
	g.hub_record="P00"
	check(Portraits.phase_key(g,"hunapu")=="hunapu_present" and Portraits.phase_key(g,"eileen")=="eileen_present","Present-time protagonist identities")
	g.hub_record="H01"
	check(Portraits.phase_key(g,"hunapu")=="hunapu_memory" and Portraits.phase_key(g,"eileen")=="eileen_departure","Memory-chapter protagonist identities")
	g.flags.korlan_defeated=true;g.flags.sea_chart_collected=true
	check(Portraits.phase_key(g,"hunapu")=="hunapu_victory" and Portraits.phase_key(g,"eileen")=="eileen_chart","Existing chapter events advance protagonist portraits")
	g.stage_id=101
	check(Portraits.unit(g,{"id":"gold_test","class_id":7,"side":"enemy"}).key=="west_cavalry","Golden knight uses cavalry uniform")
	g.stage_id=201
	check(Portraits.unit(g,{"id":"gargoyle_test","class_id":3,"class":"gargoyle","side":"enemy"}).key=="gargoyle","Monster identity overrides shared class ID")
	var report={"passed":failures.is_empty(),"checks":checks.size(),"failures":failures,"assets":records,"scope":"Resource, role, region, protagonist story flags and native-size fixtures; visual evidence is separate."}
	var f=FileAccess.open("res://reports/playtest-0.5.0/portrait-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close()
	print("PORTRAIT_STATE ",checks.size()," FAILURES ",failures);quit(0 if failures.is_empty() else 1)

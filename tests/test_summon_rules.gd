extends SceneTree
const Summons = preload("res://core/summon_rules.gd")
const Items = preload("res://core/item_rules.gd")
class Board:
	extends RefCounted
	var units: Array = []
var checks:=0
var failures: Array[String]=[]
func check(value:bool,message:String)->void:
	checks+=1
	if not value:failures.append(message)
func _initialize()->void:
	var player:Dictionary={"id":"silque","side":"player","character_id":14,"class_id":17,"route":"celica"}
	var phantom:=Summons.spawn_unit(player,10)
	check(phantom.character_id==35 and phantom.class_id==10 and phantom.source_template_index==7,"Silque uses source phantom DreadFighter template7")
	check(phantom.max_hp==36 and phantom.strength==15 and phantom.skill==16 and phantom.speed==18 and phantom.defence==11 and phantom.luck==0,"phantom uses native class base stats")
	check(phantom.resistance==15 and phantom.move==7,"phantom retains native DreadFighter RES15 and move7")
	check(phantom.no_experience and phantom.ai_flags==68 and not phantom.acted and not phantom.controllable,"phantom flag44 and initial action state")
	check(phantom.route=="celica" and not phantom.has("position") and not phantom.has("id"),"constructor preserves route and delegates placement/ID")
	player.character_id=15
	check(Summons.spawn_unit(player,6).max_hp==26,"Genny source soldier base26HP")
	player.character_id=30
	check(Summons.spawn_unit(player,3).resistance==7,"Tatiana pegasus phantom native RES7")
	var cantor:Dictionary={"id":"cantor","side":"enemy","character_id":191,"class_id":19,"magic_flags":128}
	for i in range(4):
		cantor.magic_flags=128>>i
		var cls:int=[5,3,11,17][i]
		var unit:=Summons.spawn_unit(cantor,cls)
		check(unit.source_template_index==i and unit.level==1 and unit.ai_flags==72,"Cantor high bits choose exact template")
		check(not unit.no_experience and unit.exp_value>0,"enemy summons award normal enemy experience")
	cantor.magic_flags=4
	var mogall:=Summons.spawn_unit(cantor,18)
	check(mogall.source_template_index==11 and mogall.level==5 and mogall.ai_flags==8,"Jedah low flags fallback template11 level5")
	check(mogall.strength==18 and mogall.skill==12 and mogall.speed==20 and mogall.defence==12 and mogall.luck==0,"level5 adds2 to four combat stats but leaves luck0")
	check(mogall.max_hp==38 and mogall.exp_value==84 and mogall.resistance==4,"level5 HP base32+6 EXP60+24 RES4")
	var duma:Dictionary={"id":"duma","side":"enemy","character_id":167,"class_id":21}
	check(Summons.spawn_unit(duma,18,{"divide":true}).level==5,"Duma eyes use level5 template11")
	var eye:Dictionary={"id":"eye","side":"enemy","character_id":194,"class_id":18}
	check(Summons.spawn_unit(eye,18,{"divide":true}).level==1,"Mogall offspring use level1 template10")
	var witch:Dictionary={"id":"nuibaba","side":"enemy","character_id":142,"class_id":16}
	var copy:=Summons.spawn_unit(witch,16)
	check(copy.magic_flags==1 and copy.resistance==14 and copy.ai_flags==200,"witch summons know their native attack spell and RES")
	check(Summons.spawn_unit(player,16).is_empty(),"unsupported player summon cannot invent profession")
	var board:=Board.new()
	for i in range(20):board.units.append({"id":str(i),"side":"player","character_id":1+i,"hp":28})
	board.units[5].hp=0
	check(Summons.available_slots(board,"player")==0,"dead permanent ally does not free original phantom slot")
	board.units[5].character_id=35
	check(Summons.available_slots(board,"player")==1,"dead phantom slot may be reused")
	for unit in board.units:unit.side="enemy"
	board.units[0].hp=0
	check(Summons.available_slots(board,"enemy")==1,"enemy commander slot0 reserved, other dead slot reusable")
	board.units=[]
	var caster_dead:Dictionary={"id":"genny","side":"player","character_id":15,"class_id":18,"hp":0}
	board.units=[{"id":"phantom_other_caster","side":"player","character_id":35,"class_id":6,"hp":26,"summoner_id":"other"},
		{"id":"formal_soldier","side":"player","character_id":5,"class_id":6,"hp":28},
		{"id":"phantom_pegasus","side":"player","character_id":35,"class_id":3,"hp":26}]
	check(Summons.cleanup(board,caster_dead)==["phantom_other_caster"],"Genny death clears all soldier phantoms, keeps formal soldiers and other phantom classes")
	check(board.units[0].no_drop and board.units[0].no_experience and board.units[0].vanished,"cleanup marks disappearance without death loot/experience")
	cantor.hp=0;cantor.magic_flags=32
	board.units=[{"id":"native_revenant","side":"enemy","character_id":187,"class_id":11,"hp":20},
		{"id":"other_cantor_revenant","side":"enemy","character_id":187,"class_id":11,"hp":20,"summoner_id":"other"},
		{"id":"gargoyle","side":"enemy","character_id":179,"class_id":3,"hp":26}]
	check(Summons.cleanup(board,cantor)==["native_revenant","other_cantor_revenant"],"Cantor death removes all same-class enemies including pre-existing/other caster units")
	eye.hp=0;witch.hp=0;duma.hp=0
	check(Summons.cleanup(board,eye).is_empty() and Summons.cleanup(board,witch).is_empty() and Summons.cleanup(board,duma).is_empty(),"non-Cantor summoners do not erase their descendants on death")
	var injured:Dictionary={"side":"enemy","character_id":182,"class_id":6,"hp":10,"max_hp":26,"item_id":0}
	check(Items.phase_effect(injured,0,0,true).heal==0,"enemy skeleton-class neighbor cannot grant Saint aura")
	injured.side="player";injured.character_id=5
	check(Items.phase_effect(injured,0,0,true).heal==5,"allied Saint restores player5HP")
	var output:=FileAccess.open("res://reports/summon-rules-verification.json",FileAccess.WRITE)
	output.store_string(JSON.stringify({"checks":checks,"failures":failures,"source":["L039267-L03965C","L0899FA-L089A54","L08A31B-L08A3CC","L039172"]},"  ")+"\n");output.close()
	print("FE_SUMMON_RULES_CHECK ",checks," checks; failures=",failures)
	quit(0 if failures.is_empty() else 1)

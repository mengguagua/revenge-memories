extends SceneTree
const State=preload("res://core/game_state.gd")
const Hub=preload("res://core/story_hub.gd")
const L=preload("res://core/late_dialogue.gd")
const Third=preload("res://core/chapter3_hub.gd")
const Fourth=preload("res://core/chapter4_hub.gd")
const Fifth=preload("res://core/chapter5_hub.gd")
class UIProbe extends RefCounted:
 const GameState=preload("res://core/game_state.gd")
 var game;var hub;var spoken=[];var menus=[];var view="hub"
 func play_pages(pages:Array,_return:String,callback:String=""):
  spoken+=pages
  if not callback.is_empty():hub.finish_story(callback)
 func _notice(_text:String,_seconds:float=0):pass
 func _open_menu(_context:String,_labels:Array,actions:Array,_position:Vector2):menus=actions
var checks=[];var errors=[];var probes=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
 checks.append(label)
 if not ok:errors.append(label);push_error(label)
func words(ui)->String:return "／".join(ui.spoken.map(func(p):return str(p.speaker)+"："+str(p.text)))
func probe(code:String,ch:int):
 var ui=UIProbe.new();ui.game=State.new();ui.game.save_path="res://reports/full-assessment-20261025/campaign-final-r4/ch%d/chain-%s-deployment.json"%[ch,code]
 if ch==5:ui.game.save_path=ui.game.save_path.replace("campaign-final-r4","campaign-final-r5")
 check(ui.game.load_game(),code+" fixture loads")
 ui.game.save_path="/private/tmp/revenge-dialogue-hubs.json";ui.hub=Hub.new(ui);probes.append(ui);return ui
func run():
 var ui=probe("F22",2);var h=ui.hub;var g=ui.game
 await h._east_action("prisoners_treat")
 check(words(ui).contains("海峡城。裴萨不放行") and words(ui).contains("清掉记忆"),"H23 mother motive and repair-book clue are mandatory")
 check(g.flags.get("F22_confirmed",false),"H23 completion callback unlocks route")
 ui.spoken.clear();await h._east_action("reef_route")
 check(words(ui).contains("刻了个号"),"H24 fixed villager supplies numbered clasp")
 ui.spoken.clear();await h._east_action("islanders_settle")
 check(words(ui).contains("普罗米修斯是谁") and words(ui).contains("不肯让我走"),"H25 rescue and confinement both introduced")
 # Named comrade missing never turns into a generic speaker telling their personal history.
 g.roster.mireille.hp=0;g.roster.lisa.hp=0;g.roster.carlo.hp=0;ui.spoken.clear()
 await h._east_action("prisoners_treat")
 check(not ui.spoken.any(func(p):return p.speaker in ["米蕾","莉莎","卡洛"]),"Unavailable comrades never speak in mandatory H23")
 check(words(ui).contains("获救船员"),"Missing comrades do not remove mother testimony")
 ui=probe("M33",3);h=ui.hub;g=ui.game
 if not g.stage_cleared(303):g.cleared_stages.append(303)
 g.flags.erase("M33_confirmed");g.flags.story_armaments_claimed={};g.convoy.alm.erase(18)
 await Third.action(h,"third_records_w")
 check(words(ui).contains("前一年") and words(ui).contains("凯尔"),"M33 mandatory worker testimony introduces earlier forced removal")
 check(g.flags.get("M33_confirmed",false) and g.Armaments.claimed(g,18),"Sword delivered after testimony callback")
 var count=g.convoy.alm.count(18);ui.spoken.clear();await Third.action(h,"third_records_w")
 check(g.convoy.alm.count(18)==count and not words(ui).contains("前一年"),"Repeat neither replays revelation nor duplicates sword")
 ui=probe("F33",3);h=ui.hub;g=ui.game
 await Third.action(h,"third_records_e")
 check(words(ui).contains("我先不走") and words(ui).contains("有一次它没撑住"),"H35 patient choices and failed rescue survive no sidequest")
 ui=probe("F42",4);h=ui.hub;g=ui.game
 g.flags.erase("obs_steps_ready")
 await Fourth.action(h,"fourth_obs_report")
 check(g.flags.get("obs_steps_ready",false) and words(ui).contains("有人冻死"),"H46 full history is delivered before stop-tower gate")
 g.flags.west_tower_safe=false;ui.spoken.clear()
 await Fourth.action(h,"fourth_tower_shutdown")
 check(words(ui).contains("今年") and words(ui).contains("留种") and words(ui).contains("教堂"),"H43 shows relocation, seed grain and church alternative")
 check(g.flags.get("west_tower_safe",false),"Tower callback commits after full cost discussion")
 for outcome in ["maintenance","destroyed"]:
  g.flags.prometheus_outcome=outcome;g.flags.island_loop_safe=true;g.flags.erase("D42_done");ui.spoken.clear()
  await Fourth.action(h,"fourth_d42")
  check(words(ui).contains("没有清掉" if outcome=="maintenance" else "再也醒不过来了"),"D42 letter branches: "+outcome)
  check(words(ui).contains("外头新来的船还是进不来"),"D42 concrete reason to seek god: "+outcome)
 ui=probe("M51",5);h=ui.hub;g=ui.game
 g.flags.prometheus_outcome="maintenance";ui.spoken.clear()
 await Fifth.action(h,"fifth_repair_report")
 check(words(ui).contains("还要修") and words(ui).contains("还在检修"),"F51 promises match surviving boss and incomplete repairs")
 check(g.flags.get("F51_handover_seen",false),"F51 handoff callback recorded")
 for outcome in ["maintenance","destroyed"]:
  g.flags.prometheus_outcome=outcome;g.flags.erase("H55_letters_seen");g.route_positions={"alm":15,"celica":15};ui.spoken.clear()
  await Fifth.action(h,"fifth_merge")
  check(g.flags.get("H55_letters_seen",false) and words(ui).contains("高处还不能住"),"H55 compulsory exchange before merge: "+outcome)
  check(words(ui).contains("以后" if outcome=="maintenance" else "再也醒不过来了"),"H55 correct boss choice: "+outcome)
 # Resolve every fresh main/side opening, victory and fallback with actual cast state.
 g=State.new();g.new_game()
 g.roster.eileen=g._initial_character("eileen");g.parties.celica=["eileen"]
 for stage in g.stages.values():
  if int(stage.get("chapter",0))<2 or stage.get("training",false):continue
  g.chapter=int(stage.chapter);g.route=stage.route;g.stage_id=int(stage.id);g.battle_data=stage;g.units=stage.enemies.duplicate(true)+stage.npc_units.duplicate(true)
  g.flags.quest={"transfer_cut_snapshot":false};g.story_events.clear()
  var opening=preload("res://core/late_battle_dialogue.gd").resolve(g,[],str(stage.code)+"-BEGIN")
  var ending=preload("res://core/late_battle_dialogue.gd").resolve(g,[],str(stage.code)+"-END")
  check(not opening.is_empty() and not ending.is_empty(),str(stage.code)+" opening and victory branch resolve")
  check(not opening.any(func(p):return str(p.text).contains("拟补") or str(p.text).contains("演出说明")),str(stage.code)+" no director notes in speech")
 var f=FileAccess.open("res://reports/dialogue-ch2-5-20261107/hub-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"errors":errors},"  "));f.close()
 for probe_ui in probes:
  probe_ui.hub.ui=null;probe_ui.hub=null;probe_ui.game=null
 probes.clear();ui=null;h=null;g=null
 print("DIALOGUE_HUB_CHECKS ",checks.size()," errors=",errors)
 quit(0 if errors.is_empty() else 1)

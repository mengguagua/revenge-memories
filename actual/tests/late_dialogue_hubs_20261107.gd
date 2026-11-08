extends SceneTree
const State=preload("res://core/game_state.gd")
const Hub=preload("res://core/story_hub.gd")
const L=preload("res://core/late_dialogue.gd")
const Portraits=preload("res://core/portrait_library.gd")
const Third=preload("res://core/chapter3_hub.gd")
const Fourth=preload("res://core/chapter4_hub.gd")
const Fifth=preload("res://core/chapter5_hub.gd")
class UIProbe extends RefCounted:
 const GameState=preload("res://core/game_state.gd")
 var game;var hub;var spoken=[];var menus=[];var view="hub"
 var busy=false;var instant_mode=true;var held_direction=Vector2i.ZERO
 func play_pages(pages:Array,_return:String,callback:String=""):
  spoken+=pages
  if not callback.is_empty():hub.finish_story(callback)
 func _notice(_text:String,_seconds:float=0):pass
 func queue_redraw():pass
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
 g.flags.erase("east_departure_ready")
 h.room="H21";h._configure_east_room();g.hub_position=Vector2i(8,6)
 await h._east_action("east_martin")
 check(ui.spoken.is_empty() and not g.flags.get("east_departure_ready",false),"H21 the captain cannot begin the pursuit before Carlo speaks")
 await h._east_action("east_departure")
 check(words(ui).contains("我喜欢玩骰子") and words(ui).contains("接了个长途护送的活") and words(ui).contains("你母亲船上的舵手"),"D21 uses the revised Carlo dialogue")
 var captain=ui.spoken.filter(func(p):return p.speaker=="马丁")
 check(g.flags.get("east_departure_ready",false) and captain.size()==3 and captain[0].text.contains("学舍") and captain[1].text.contains("她没回来我也很担心") and captain[2].text.contains("我和船员不擅长战斗"),"D21 plays the revised Martin dialogue before departure")
 check(g.hub_position+h.facing==h._martin_cell() and not g.flags.has("east_martin_pending"),"D21 ends facing the on-map captain and clears the departure checkpoint")
 check(Portraits.speaker(g,"马丁").get("key","")=="sailor","Martin uses the existing captain portrait")
 ui.spoken.clear()
 g.flags.erase("F21_confirmed")
 await h._east_action("sea_route")
 check(g.flags.get("F21_confirmed",false) and words(ui).contains("马丁：给学舍送药"),"H22 the same captain confirms the route")
 ui.spoken.clear()
 await h._east_action("prisoners_treat")
 check(words(ui).contains("卡洛在外岛看见你") and words(ui).contains("送他们去海峡城") and words(ui).contains("裴萨不放行") and words(ui).contains("清掉记忆"),"H23 the rescued helmsman gives mandatory testimony alongside the repair-book clue")
 check(g.flags.get("F22_confirmed",false),"H23 completion callback unlocks route")
 ui.spoken.clear();await h._east_action("reef_route")
 check(words(ui).contains("刻了个号"),"H24 fixed villager supplies numbered clasp")
 ui.spoken.clear();await h._east_action("islanders_settle")
 check(words(ui).contains("普罗米修斯是谁") and words(ui).contains("不肯让我走"),"H25 rescue and confinement both introduced")
 # Named comrade missing never turns into a generic speaker telling their personal history.
 g.roster.mireille.hp=0;g.roster.lisa.hp=0;g.roster.carlo.hp=0;ui.spoken.clear()
 await h._east_action("east_martin")
 check(ui.spoken.size()==1 and ui.spoken[0].speaker=="马丁" and ui.spoken[0].text=="船好了，出发。","H21 the captain still speaks from his own position when Carlo cannot participate")
 ui.spoken.clear()
 await h._east_action("prisoners_treat")
 check(not ui.spoken.any(func(p):return p.speaker in ["米蕾","莉莎","卡洛"]),"Unavailable comrades never speak in mandatory H23")
 check(words(ui).contains("薇娅的舵手") and words(ui).contains("他们把我关在外岛"),"Missing comrades do not remove the helmsman's testimony")
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
  check(words(ui).contains("马丁：外头新来的船还是进不来"),"D42 Martin reports the remaining blockade: "+outcome)
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
  if stage.code=="F22":
   var helmsman=g.find_unit("prisoners_0")
   check(helmsman.get("name_zh")=="薇娅的舵手" and opening[0].text.contains("从外岛押走的舵手") and opening.any(func(p):return p.text.contains("护卫去挡舰长")) and ending[0].text.contains("那位舵手"),"F22 identifies the same mandatory captive even without Carlo in the battle")
  if stage.code=="F33":
   check(opening.any(func(p):return p.speaker=="船团护卫" and p.text.contains("工房的门")) and not opening.any(func(p):return p.speaker=="马丁"),"F33 a guard covers Carlo's position while Martin stays with the boats")
  if stage.code=="J54":
   check(ending.any(func(p):return p.speaker=="船团信使" and p.text.contains("马丁船长")),"J54 the messenger refers to the same captain")
 var f=FileAccess.open("res://reports/dialogue-ch2-5-20261107/hub-checks.json",FileAccess.WRITE);f.store_string(JSON.stringify({"checks":checks,"errors":errors},"  "));f.close()
 for probe_ui in probes:
  probe_ui.hub.ui=null;probe_ui.hub=null;probe_ui.game=null
 probes.clear();ui=null;h=null;g=null
 print("DIALOGUE_HUB_CHECKS ",checks.size()," errors=",errors)
 quit(0 if errors.is_empty() else 1)

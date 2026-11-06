extends SceneTree
const State=preload("res://core/game_state.gd")
const Training=preload("res://core/training_rules.gd")
const OUT="res://reports/tactical-expansion-20261025/training/"
const CACHE="/private/tmp/revenge-training-tests/"
const FIXTURES={
	"1:alm":"campaign-final-r1/ch1/chain-M13-victory.json",
	"2:celica":"campaign-final-r4/ch2/chain-F24-victory.json",
	"3:alm":"campaign-final-r4/ch3/chain-M31-victory.json",
	"3:celica":"campaign-final-r4/ch3/chain-F31-victory.json",
	"4:alm":"campaign-final-r4/ch4/chain-M41-victory.json",
	"4:celica":"campaign-final-r4/ch4/chain-F41-victory.json",
	"5:alm":"campaign-final-r5/ch5/chain-M51-victory.json",
	"5:celica":"campaign-final-r5/ch5/chain-F51-victory.json"}
var checks=[]
var failures=[]
var layouts=[]
func _initialize():call_deferred("run")
func check(ok:bool,label:String):
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func same(a,b)->bool:return JSON.stringify(a)==JSON.stringify(b) or JSON.parse_string(JSON.stringify(a))==JSON.parse_string(JSON.stringify(b))
func fixture(pool:String):
	var g=State.new();g.save_path="res://reports/full-assessment-20261025/"+str(FIXTURES[pool])
	if not g.load_game():check(false,"historic source loads "+pool);return null
	# Use the recorded real post-victory roster as a peaceful unit-test fixture.
	# The integration driver separately exercises the UI departure/return flow.
	g.mode="world";g.story_events=[];g.flags.erase("active_plot")
	g.battle_start_snapshot={};g.units=[];g.selected_id="";g.battle_outcome="";g.battle_settled=false
	g.save_path=CACHE+pool.replace(":","-")+".json"
	return g
func run():
	DirAccess.make_dir_recursive_absolute(CACHE)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	var opening=State.new();opening.new_game()
	check(Training.choices(opening).is_empty(),"training unavailable before early story unlock")
	for region in Training.config().regions:
		var pool=Training._pool(int(region.chapter),str(region.route))
		for stage_id in region.ids:
			var g=fixture(pool)
			if g==null:continue
			var before_roster=g.roster.duplicate(true);var before_convoy=g.convoy.duplicate(true)
			var before_flags=g.flags.duplicate(true);var before_clear=g.cleared_stages.duplicate()
			check(g.save_game(),"peaceful fixture valid "+str(stage_id))
			check(Training.choices(g).size()==2,"two authored exercises available "+str(stage_id))
			check(Training.start(g,int(stage_id)),"enter exercise "+str(stage_id))
			var occupied={};var legal=true
			for u in g.units:
				var cell=g.pos(u)
				legal=legal and not occupied.has(cell) and g.in_bounds(cell) and g.movement_cost(u,cell)<255
				occupied[cell]=true
			check(legal,"all drill deployment positions legal and unique "+str(stage_id))
			check(g.battle_data.objects[0].sprite=="white_flag","exercise goal has actual bitmap "+str(stage_id))
			check(g.battle_data.enemies.size()==int(region.enemy_count),"bounded opponent count "+str(stage_id))
			check(g.units.all(func(u):return u.no_experience and u.no_drop),"no combat XP or loot during drill "+str(stage_id))
			layouts.append({"stage":stage_id,"code":g.battle_data.code,"map":g.battle_data.training_base,"goal":g.battle_data.training_target,"players":g.living("player").size(),"enemies":g.living("enemy").size()})
			check(g.save_game(),"active training save validates "+str(stage_id))
			var r=State.new();r.save_path=g.save_path
			check(r.load_game() and Training.active(r),"active training reload reconstructs map "+str(stage_id))
			if not Training.active(r):continue
			var snapshot=r.battle_start_snapshot.duplicate(true)
			r.find_unit(r.leader_id()).hp=1;r.turn=7;r.rng_state=123
			check(r.retry_battle() and r.turn==1 and same(r.units,snapshot.units),"retry restores opening exercise state "+str(stage_id))
			check(Training.leave(r),"exit exercise "+str(stage_id))
			check(same(r.roster,before_roster) and same(r.convoy,before_convoy) and same(r.flags,before_flags),"exit rolls back training only "+str(stage_id))
			check(same(r.cleared_stages,before_clear) and r.mode=="world" and not Training.active(r),"exit preserves story progress "+str(stage_id))
			check(r.save_game() and r.load_game(),"returned peaceful checkpoint reloads "+str(stage_id))
	completion_checks()
	equipment_exchange_checks()
	var report={"checks":checks.size(),"failures":failures,"layouts":layouts,"scope":"Headless state/serialization tests using copies of real historical rosters. Direct state injections test boundary conditions; these are not manual playthroughs."}
	var f=FileAccess.open(OUT+"checks.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"\t"));f.close()
	print(JSON.stringify({"checks":checks.size(),"failures":failures}));quit(0 if failures.is_empty() else 1)
func completion_checks():
	var g=fixture("1:alm")
	if g==null:return
	var original_clear=g.cleared_stages.duplicate();var original_roster=g.roster.duplicate(true)
	var original_items={}
	for id in g.roster:original_items[id]=int(g.roster[id].get("item_id",0))
	check(Training.start(g,191),"completion fixture enters")
	check(g.save_game(),"validation fixture saves before mutation")
	var valid_entry=State.read_json(g.save_path)
	for key in ["origin","participants","settled","stage_id","pool"]:
		for value in [null,"broken",[],17]:
			var broken=valid_entry.duplicate(true);broken.flags.training_active[key]=value
			check(not g.SaveValidation.campaign_valid(g,broken,g.SAVE_FIELDS),"reject malformed training active "+key+" "+str(value))
	for key in ["flags","battle_start_snapshot","roster","units","stage_id","mode"]:
		for value in [null,"broken",[],17]:
			if key=="units" and value is Array:continue
			var broken=valid_entry.duplicate(true);broken.flags.training_active.origin[key]=value
			check(not g.SaveValidation.campaign_valid(g,broken,g.SAVE_FIELDS),"reject malformed training origin "+key+" "+str(value))
	var recursive=valid_entry.duplicate(true)
	recursive.flags.training_active.origin.flags.training_active={"origin":valid_entry.duplicate(true)}
	check(not g.SaveValidation.campaign_valid(g,recursive,g.SAVE_FIELDS),"reject nested training origin before recursion")
	var participants=g.flags.training_active.participants.duplicate()
	var nonleader=participants.filter(func(id):return id!=g.leader_id())[0]
	var u=g.find_unit(nonleader)
	g.commit_strike({"attacker":g.living("enemy")[0].id,"defender":nonleader,"hp_before":int(u.hp),"hp_after":0,"damage":int(u.hp),"hit":true,"critical":false})
	check(not g.roster[nonleader].get("dying",false) and int(u.get("item_id",0))==original_items[nonleader],"training knockout neither wounds roster nor stores equipment")
	# Exercise victory is injected only to verify one-time settlement boundaries.
	g.battle_outcome="victory";g.mode="victory"
	check(g.complete_battle(),"first exercise completion settles")
	check(not g.complete_battle(),"settlement cannot award twice")
	check(int(g.flags.training_counts["1:alm"])==1,"one success consumed")
	for id in participants:
		var expected=int(original_roster[id].level)*100+int(original_roster[id].exp)+60
		var actual=int(g.roster[id].level)*100+int(g.roster[id].exp)
		check(actual==expected,"every participant including knockout receives training XP "+str(id))
		check(not g.roster[id].get("dying",false) and not g.roster[id].get("no_experience",false) and int(g.roster[id].hp)==int(g.roster[id].max_hp),"participant restored without temporary flags "+str(id))
	check(same(g.cleared_stages,original_clear),"training does not clear or replay story")
	check(g.save_game(),"settled training save valid")
	var r=State.new();r.save_path=g.save_path
	check(r.load_game() and r.battle_settled,"settled training resumes without awarding again")
	if not Training.active(r):return
	check(Training.leave(r) and int(r.flags.training_counts["1:alm"])==1,"victory return preserves count")
	check(r.save_game() and r.load_game(),"victory return remains loadable")
	check(Training.start(r,192),"second variant enters same finite pool")
	r.battle_outcome="victory";check(r.complete_battle(),"second permitted success")
	check(Training.leave(r),"second victory returns")
	check(Training.remaining(r)==0 and Training.choices(r).all(func(c):return not c.enabled),"two-success cap is exposed in choices")
	check(not Training.start(r,191),"third successful training cannot be started")
	check(r.save_game() and r.load_game() and Training.remaining(r)==0,"success cap persists across restart")
	var state=State.read_json(r.save_path)
	state.flags.training_counts["1:alm"]=-1
	check(not r.SaveValidation.campaign_valid(r,state,r.SAVE_FIELDS),"reject forged negative count")
	state.flags.training_counts["1:alm"]=3
	check(not r.SaveValidation.campaign_valid(r,state,r.SAVE_FIELDS),"reject count beyond cap")
func equipment_exchange_checks():
	var g=fixture("1:alm")
	if g==null:return
	var initial=g.roster.duplicate(true);var convoy=g.convoy.duplicate(true)
	check(Training.start(g,191),"equipment exchange drill enters")
	var pair=[]
	for a in g.living("player"):
		for b in g.living("player"):
			if g.Inventory.can_exchange(a,b):pair=[str(a.id),str(b.id)];break
		if not pair.is_empty():break
	check(pair.size()==2,"real roster has a legal adjacent equipment exchange")
	if pair.is_empty():return
	check(g.Inventory.exchange(g,pair[0],pair[1]),"ordinary training equipment exchange succeeds")
	check(Training.leave(g) and same(g.roster,initial) and same(g.convoy,convoy),"unsuccessful exit restores exchanged equipment exactly")
	check(Training.start(g,191),"equipment success drill enters")
	check(g.Inventory.exchange(g,pair[0],pair[1]),"second ordinary exchange succeeds")
	g.battle_outcome="victory";g.mode="victory"
	check(g.complete_battle() and Training.leave(g),"successful exchanged drill settles and returns")
	check(int(g.roster[pair[0]].item_id)==int(initial[pair[1]].item_id) and int(g.roster[pair[1]].item_id)==int(initial[pair[0]].item_id) and same(g.convoy,convoy),"successful training preserves legitimate exchange without duplication")
	check(g.save_game() and g.load_game(),"exchanged success survives reload")

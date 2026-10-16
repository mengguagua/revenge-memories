extends SceneTree
const State=preload("res://core/game_state.gd")
var checks: Array=[]
var failures: Array=[]
func _initialize() -> void:call_deferred("run")
func check(ok: bool,label: String) -> void:
	checks.append(label)
	if not ok:failures.append(label);push_error(label)
func army():
	var g=State.new();g.new_game();g.route="celica";g.party=["eileen","carlo","lord","roan","shia"];g.parties.celica=g.party.duplicate();g.convoy.celica=[]
	for id in g.party:
		g.roster[id]=g._initial_character(id)
		g.roster[id].item_id=0 # This fixture specifically exercises empty slots.
	return g
func run() -> void:
	var g=army()
	for id in ["eileen","carlo","lord","roan"]:g.roster[id].item_id=49
	var original=g.roster.duplicate(true);var west=g.convoy.alm.duplicate();var bow=g.receive_equipment(21)
	check(bow.valid and bow.destination=="convoy" and g.convoy.celica==[21],"occupied archer and empty flying knight sends holy bow to east convoy")
	check(g.roster==original and g.convoy.alm==west,"no carried equipment silently replaced and west convoy unchanged")
	g=army();bow=g.receive_equipment(21)
	check(bow.valid and bow.destination=="unit" and bow.recipient=="roan" and g.roster.shia.item_id==0,"empty compatible archer receives bow before incompatible empty members")
	for item in [16,49,4]:
		g=army();var result=g.receive_equipment(item)
		check(result.valid and result.destination=="unit" and g.Items.can_use(g.roster[result.recipient],item),"documented sword shield or javelin assigned only to compatible empty member: "+str(item))
		check(g.party.filter(func(id):return int(g.roster[id].item_id)==item).size()==1,"one claim creates exactly one carried copy: "+str(item))
	g=army();g.roster.roan.hp=0;g.roster.roan.dead=true;bow=g.receive_equipment(21)
	check(bow.destination=="convoy" and g.roster.roan.item_id==0,"dead archer cannot receive claimed bow")
	g=army()
	for id in g.party:g.roster[id].item_id=49
	for i in range(40):g.convoy.celica.append(49)
	var before=g.roster.duplicate(true);var full=g.convoy.duplicate(true);var blocked=g.receive_equipment(21)
	check(not blocked.valid and blocked.reason=="convoy_full" and g.roster==before and g.convoy==full,"full convoy leaves equipment and claim pending without mutation")
	# Exercise the exact UI claim path and its one-time flag/recipient notice.
	var ui=load("res://scenes/main.tscn").instantiate();root.add_child(ui);await process_frame
	ui.game=army();ui.game.save_path="res://reports/chapter2/equipment-claim-save.json"
	for id in ["eileen","carlo","lord","roan"]:ui.game.roster[id].item_id=49
	ui.hub_controller._east_claim_item("F25_holy_bow_taken",21,"圣弓")
	check(ui.game.flags.get("F25_holy_bow_taken",false) and ui.game.convoy.celica==[21],"actual holy-bow claim path stores incompatible unassigned reward")
	ui.hub_controller._east_claim_item("F25_holy_bow_taken",21,"圣弓")
	check(ui.game.convoy.celica==[21],"repeated chest interaction does not duplicate stored bow")
	var report={"scope":"Targeted equipment compatibility/empty-slot/convoy/chest idempotency checks","passed":failures.is_empty(),"checks":checks.size(),"failures":failures}
	var f=FileAccess.open("res://reports/chapter2/equipment-claim-check.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("EQUIPMENT_CLAIM ",JSON.stringify(report));ui.queue_free();await process_frame;quit(0 if failures.is_empty() else 1)

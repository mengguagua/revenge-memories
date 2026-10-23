extends "res://tests/ch2_environment_shore.gd"
# The chapter's acquired holy equipment is selected through the normal replacement preview.
func prepare_current()->void:
 await super.prepare_current()
 if not abort and ui.game.flags.get("F23_holy_sword_taken",false):await upgrade_from_convoy("eileen",16)
 if not abort and ui.game.flags.get("F25_holy_bow_taken",false):await upgrade_from_convoy("roan",21)

func upgrade_from_convoy(id:String,item:int) -> void:
 var member=ui.game.roster.get(id,{})
 if member.is_empty() or not ui.game.can_deploy(member) or int(member.get("item_id",0))==item:return
 var stored=ui.game.convoy[ui.game.route];var index=-1
 for i in range(stored.size()):
  if int(stored[i])==item:index=i;break
 if index<0:return
 key(KEY_S);choose("new:camp");choose("camp:convoy");choose("camp:withdraw");choose("camp:withdraw_item:"+str(index))
 if abort:return
 if ui.view!="equipment_members" or not ui.equipment_screen.members.has(id):record_failure("Current equipment member list absent");return
 for i in range(ui.equipment_screen.members.size()):
  if str(ui.equipment_screen.members[ui.equipment_screen.selected])==id:break
  key(KEY_DOWN)
 key(KEY_Z)
 if ui.view!="equipment_preview" or not ui.equipment_screen.preview().can_equip:record_failure("Equipment comparison rejected "+id);return
 key(KEY_Z);await settle()
 if int(ui.game.roster[id].item_id)!=item:record_failure("Equipment confirmation failed "+id);return
 operations.append({"kind":"actual convoy equipment comparison and confirmation","unit":id,"item":item,"node":ui.game.world_node})
 if not ui.menu_items.is_empty():key(KEY_X)

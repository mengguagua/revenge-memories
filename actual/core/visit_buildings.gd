extends RefCounted
const TENT="res://assets/visit-buildings-20261030/records-tent.png"
const DOOR="res://assets/visit-buildings-20261030/open-entrance.png"
static func module_for(stage:Dictionary,object:Dictionary)->Dictionary:
	for module in stage.get("art_modules",[]):
		if object.position in module.get("cells",[]):return module
	# The first map's cottage is a direct art prop, not an art_module.
	if stage.code=="M11" and object.get("building","")=="snow_cottage":return {"name":"snow_cottage","origin":[9,2],"cells":[[9,2],[10,2],[9,3],[10,3]]}
	return {}
static func visit_at(stage:Dictionary,cell:Vector2i)->Dictionary:
	for object in stage.get("objects",[]):
		if object.get("kind","")!="visit":continue
		var cells=module_for(stage,object).get("cells",[]).duplicate()
		cells.append(object.position);cells.append_array(object.get("entrance_cells",[]));cells.append_array(object.get("approaches",[]))
		if cells.any(func(p):return cell==Vector2i(p[0],p[1])):return object
	return {}
static func name_at(stage:Dictionary,cell:Vector2i)->String:
	var visit=visit_at(stage,cell)
	if not visit.is_empty():return str(visit.label).trim_prefix("访问")
	for module in stage.get("art_modules",[]):
		if not module.get("cells",[]).any(func(p):return cell==Vector2i(p[0],p[1])):continue
		return str({"command_pavilion":"封闭军帐","grain_store":"封闭粮料库","hill_granary":"封闭粮仓","barracks":"封闭兵营","coastal_keep":"堡垒墙体","captain_cabin":"封闭船舱","snow_cottage":"封闭村舍","village_clinic":"封闭房屋","quay_warehouse":"封闭港仓","ruined_watchtower":"废弃瞭望塔"}.get(str(module.name),""))
	return ""
static func props(stage:Dictionary)->Array:
	var result=stage.get("art_props",[]).duplicate(true)
	for object in stage.get("objects",[]):
		if object.get("kind","")!="visit":continue
		var module=module_for(stage,object)
		if module.get("name","")!="command_pavilion":continue
		for prop in result:
			if prop.position==[module.origin[0]*16,module.origin[1]*16]:
				prop.path=TENT;prop.position=[module.origin[0]*16,module.origin[1]*16-8];prop.size=[32,40]
	return result
static func entrances(stage:Dictionary)->Array:
	var result=[]
	for object in stage.get("objects",[]):
		if object.get("kind","")!="visit" or module_for(stage,object).get("name","")=="command_pavilion":continue
		result.append({"path":DOOR,"position":[object.position[0]*16,object.position[1]*16-4],"size":[16,20]})
	return result

extends SceneTree
func _initialize():call_deferred("run")
func run():
 var data=JSON.parse_string(FileAccess.get_file_as_string(OS.get_environment("CH5_PALETTE_EXPECTED")));var checks=[];var errors=[]
 for entry in data:
  var texture=load(entry.path) as Texture2D
  if texture==null:errors.append("missing "+str(entry.path));continue
  var image=texture.get_image();image.convert(Image.FORMAT_RGBA8)
  var bytes=image.get_data()
  # Import fixes transparent border RGB. Compare opaque RGB and every alpha value.
  for i in range(0,bytes.size(),4):
   if bytes[i+3]!=255:bytes[i]=0;bytes[i+1]=0;bytes[i+2]=0
  var hash=HashingContext.new();hash.start(HashingContext.HASH_SHA256);hash.update(bytes);var digest=hash.finish().hex_encode()
  var ok=image.get_width()==int(entry.width) and image.get_height()==int(entry.height) and digest==entry.sha256
  checks.append({"path":entry.path,"width":image.get_width(),"height":image.get_height(),"pixels_match":ok})
  if not ok:errors.append("pixel mismatch "+str(entry.path))
 var f=FileAccess.open(OS.get_environment("CH5_PALETTE_REPORT"),FileAccess.WRITE);f.store_string(JSON.stringify({"passed":errors.is_empty(),"revision":"muted-v2","checks":checks,"errors":errors,"scope":"art-only exported texture verification; gameplay tests were not rerun"},"  "));f.close()
 print("CH5_PALETTE_PACK ",checks.size()," ",errors);quit(0 if errors.is_empty() else 1)

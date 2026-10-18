from PIL import Image
from pathlib import Path
import json, math, shutil
root = Path(__file__).resolve().parents[1]
manifest_path = root / "frame_mapping.json"
m = json.loads(manifest_path.read_text())
new_ids = list(range(10,22))+list(range(31,41))+[125,126,127]
backup = root / "source/registered-before-foot-anchor"
backup.mkdir(exist_ok=True)
# These ROIs isolate visible boots, never sword tips, bows, shield or sweep alpha.
roi = {
10:(208,232,264,280),11:(208,232,264,280),12:(184,216,228,252),
13:(136,236,196,280),14:(136,236,196,280),15:(136,236,196,280),16:(136,236,196,280),
17:(160,232,244,280),18:(160,232,244,280),19:(160,232,248,280),20:(160,232,248,280),21:(160,232,252,280),
31:(144,232,244,280),32:(220,232,280,280),33:(176,232,248,280),34:(208,232,268,280),
35:(216,232,280,280),36:(216,232,280,280),37:(216,232,280,280),38:(216,232,280,280),
39:(136,232,280,280),40:(136,232,280,280),
125:(144,224,264,280),126:(144,224,272,280),127:(144,224,264,280)}
reference_roi = dict(roi)
for i in (17,18,19,20,21): reference_roi[i]=(176,236,232,256)
for i in (125,126,127): reference_roi[i]=(168,236,228,256)
base_roi={0:(144,232,244,280),1:roi[32],2:roi[33],3:roi[34]}
both_boots={17,18,19,20,21,31,39,40,125,126,127}
def visible_boot_point(im, box, split=None):
    if split is not None:
        left=visible_boot_point(im,(box[0],box[1],split,box[3]))
        right=visible_boot_point(im,(split,box[1],box[2],box[3]))
        bounds=[min(left['sole_band_bbox'][0],right['sole_band_bbox'][0]),min(left['sole_band_bbox'][1],right['sole_band_bbox'][1]),max(left['sole_band_bbox'][2],right['sole_band_bbox'][2]),max(left['bottom_y'],right['bottom_y'])]
        return {'center_x':(bounds[0]+bounds[2])/2,'bottom_y':bounds[3],'sole_band_bbox':bounds,'roi':list(box),'separate_visible_boots':[left,right]}
    alpha=im.getchannel("A")
    pts=[(x,y) for y in range(box[1],box[3]) for x in range(box[0],box[2]) if alpha.getpixel((x,y))>=128]
    if not pts: raise ValueError(("empty boot ROI",box))
    bottom=max(y for x,y in pts)+1
    sole=[(x,y) for x,y in pts if y>=bottom-3]
    bounds=[min(x for x,y in sole), min(y for x,y in sole),max(x for x,y in sole)+1,bottom]
    return {"center_x":(bounds[0]+bounds[2])/2,"bottom_y":bottom,"sole_band_bbox":bounds,"roi":list(box)}
def nearest(v):
    return math.floor(v+0.5) if v>=0 else math.ceil(v-0.5)
records=[]
for i in new_ids:
    path=root/f"frames/frame-{i:03}.png";pre=backup/path.name
    if not pre.exists():shutil.copy2(path,pre)
    im=Image.open(pre).convert("RGBA")
    current=visible_boot_point(im,roi[i],204 if i in both_boots else None)
    if 31<=i<=34:
        base=i-31;ref_path=root/f"frames/frame-{base:03}.png"
        ref=Image.open(ref_path).convert("RGBA");target=visible_boot_point(ref,base_roi[base],204 if base==0 else None)
        reason="Approved baseline counterpart; original source body/feet identical outside shield region. Avoid moving approved0–3 to another coordinate standard."
    else:
        ref_id=126 if i==125 else i
        ref_path=root/f"reference/original-{ref_id:03}.png"
        ref=Image.open(ref_path).convert("RGBA");target=visible_boot_point(ref,reference_roi[i],204 if i in both_boots else None)
        reason="Native visible boot correspondence; no whole-frame alpha extrema."
        if i==125:reason+=" Source126 shared foot ROI excludes source125's bow tip that overlaps the low-left alpha row."
    dx=nearest(target["center_x"]-current["center_x"]);dy=target["bottom_y"]-current["bottom_y"]
    if i in (39,40) and abs(target["center_x"]-current["center_x"])<=1:
        dx=0
        reason+=" Horizontal residual at most1px preserved because paired source pose centers are already aligned."
    out=Image.new("RGBA",(320,288));out.paste(im,(dx,dy))
    assert sum(out.getchannel("A").getdata())==sum(im.getchannel("A").getdata()),(i,"translation would clip content")
    out.save(path)
    rec={"source_frame":i,"before":current,"target":target,"target_reference":str(ref_path.relative_to(root)),"translation":[dx,dy],"reason":reason,"result":{"center_x":current["center_x"]+dx,"bottom_y":current["bottom_y"]+dy},"backup":str(pre.relative_to(root))}
    records.append(rec)
    for r in m["records"]:
        if r["source_frame"]==i:r["whole_frame_anchor_translation"]=[dx,dy];r["anchor_evidence"]="source/foot-anchor-registration.json"
shutil.copy2(root/"frames/frame-126.png",root/"frames/frame-138.png")
report={"method":"Manually selected visible-boot ROIs; alpha>=128 within ROI; lower3-pixel sole bands. Standing pairs measured separately then combined, so both boots remain represented even with unequal sole heights. Whole-image integer translations only.","cautions":["Source125 bow tip excluded by using proven matching126 boot geometry.","31–34 target accepted0–3 corresponding boots, not unapproved relocation of the baseline.","No whole-frame alpha extrema, weapon clamping, limb transforms, recoloring or rescaling."],"records":records}
(root/"source/foot-anchor-registration.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
m["foot_anchor_registration"]="source/foot-anchor-registration.json"
m["status"]="all_35_registered_final_visual_qa"
manifest_path.write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n")
for r in records:print(r["source_frame"],r["translation"],r["before"]["sole_band_bbox"],"->",r["target"]["sole_band_bbox"])


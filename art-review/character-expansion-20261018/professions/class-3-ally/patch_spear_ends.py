"""Composite ImageGen spear-end components only; preserve all pixels outside declared endpoint masks."""
from pathlib import Path
from PIL import Image
import json,shutil,hashlib,subprocess
import register_art as m
R=Path(__file__).resolve().parent;r=R/'maps';src=r/'source/spear-end-components-v1.png';work=r/'source/spear-end-patches';work.mkdir(exist_ok=True)
components={'upcap':[282,170,403,540],'downblade':[846,127,984,552],'diagcap':[125,694,547,1115],'diagblade':[785,699,1175,1112],'bladetip':[850,320,984,552]}
def component(name,width):
    roi=components[name];h=round((roi[3]-roi[1])*width/(roi[2]-roi[0]));p=work/f'{name}-{width}.png'
    m.run(src,'-crop',f'{roi[2]-roi[0]}x{roi[3]-roi[1]}+{roi[0]}+{roi[1]}','+repage','-filter','Lanczos','-resize',f'{width}x{h}!',p)
    return Image.open(p).convert('RGBA')
# Each patch: erase ROI, component name/width, paste XY, optional diagonal-sum mask, optional preserve old body alpha.
configs={
('tactical-native-frames',0):[([69,0,79,14],'upcap',5,[70,0],None,False),([72,49,77,56],'bladetip',3,[73,49],None,True)],
('tactical-native-frames',1):[([73,0,83,14],'upcap',5,[74,0],None,False),([76,50,81,57],'bladetip',3,[77,50],None,True)],
('tactical-native-frames',4):[([45,0,54,16],'upcap',5,[47,0],None,False),([46,63,54,79],'downblade',5,[47,63],None,False)],
('tactical-native-frames',5):[([49,0,58,16],'upcap',5,[51,1],None,False),([50,66,58,83],'downblade',5,[51,66],None,False)],
('tactical-native-frames',6):[([83,3,101,17],'diagcap',14,[83,3],None,False),([32,33,43,44],'diagblade',9,[32,33],78,False)],
('tactical-native-frames',7):[([83,3,103,18],'diagcap',14,[83,4],None,False),([32,32,43,43],'diagblade',9,[32,32],77,False)],
('idle-frames',0):[([58,18,71,30],'diagcap',11,[59,18],92,False),([15,49,25,60],'diagblade',9,[15,49],77,False)],
('idle-frames',1):[([61,19,74,32],'diagcap',11,[61,20],None,False),([23,50,33,61],'diagblade',9,[23,50],85,False)],
('idle-frames',2):[([61,19,74,32],'diagcap',11,[61,20],None,False),([23,50,33,61],'diagblade',9,[23,50],85,False)]}
report=[]
for (folder,i),patches in configs.items():
    p=r/f'{folder}/frame-{i:03}.png';backup=work/f'{folder}-{i:03}-before.png'
    if not backup.exists():shutil.copyfile(p,backup)
    old=Image.open(backup).convert('RGBA');new=old.copy();allowed=set();patchmeta=[]
    for roi,name,width,xy,diag,protect in patches:
        layer=Image.new('RGBA',old.size);part=component(name,width);layer.alpha_composite(part,tuple(xy));allowed_here=[]
        for y in range(roi[1],roi[3]):
            for x in range(roi[0],roi[2]):
                if diag is not None and x+y>diag:continue
                if folder=='idle-frames' and i in [1,2] and name=='diagcap' and x<=62 and y>=29:continue
                if protect and old.getpixel((x,y))[3]>=16:continue
                new.putpixel((x,y),layer.getpixel((x,y)));allowed.add((x,y));allowed_here.append((x,y))
        patchmeta.append({'roi':roi,'imagegen_component':name,'source_component_roi':components[name],'uniform_width':width,'resampled_size':list(part.size),'paste_xy':xy,'diagonal_sum_max':diag,'preserve_existing_body_alpha_ge16':protect})
    changed=[(x,y)for y in range(old.height)for x in range(old.width)if old.getpixel((x,y))!=new.getpixel((x,y))];assert all(pt in allowed for pt in changed)
    new.save(p,optimize=True);m.compress(p);report.append({'path':str(p.relative_to(r)),'before':str(backup.relative_to(r)),'before_sha256':m.sha(backup),'after_sha256':m.sha(p),'changed_pixels':len(changed),'outside_endpoint_masks_rgba_exact':True,'patches':patchmeta})
for folder,pairs in [('idle-frames',[(3,1),(4,0),(5,1)]),('tactical-native-frames',[(2,6),(3,7)])]:
    for i,j in pairs:
        base=Image.open(r/f'{folder}/frame-{j:03}.png').convert('RGBA');im=base.transpose(Image.Transpose.FLIP_LEFT_RIGHT)if folder=='tactical-native-frames'else base
        p=r/f'{folder}/frame-{i:03}.png';backup=work/f'{folder}-{i:03}-before.png'
        if not backup.exists():shutil.copyfile(p,backup)
        im.save(p,optimize=True);m.compress(p)
(r/'source/spear-end-patch-qa.json').write_text(json.dumps({'imagegen_source':'source/spear-end-components-v1.png','component_source_sha256':m.sha(src),'policy':'ImageGen art components; technical crop, uniform resampling and endpoint-mask compositing only. No recoloring/drawing; body/wing/projection outside masks remains exact.','records':report},ensure_ascii=False,indent=2)+'\n')
print('patched',len(report),'independent map frames; aliases/mirrors regenerated')

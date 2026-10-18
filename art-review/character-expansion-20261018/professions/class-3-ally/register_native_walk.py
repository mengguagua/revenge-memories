"""Register ImageGen walking bodies; preserve separately proven native projection pixels."""
from pathlib import Path
import json,shutil,hashlib
from PIL import Image,ImageDraw
import register_art as m
R=Path(__file__).resolve().parent;B=R.parents[1];r=R/'maps';outdir=r/'tactical-native-frames';outdir.mkdir(exist_ok=True)
native=B/'source-input/corrected-tactical-walk/class-3-ally.png';ni=Image.open(native).convert('RGBA')
configs=[(0,3,300,[390,1210,480,1305],[14,18,15,19],12),(1,1,300,[450,1180,590,1305],[16,17,17,20],12),(4,3,360,[450,1280,545,1370],[15,18,16,19],6),(5,3,282,[460,1170,575,1260],[16,16,17,18],8),(6,3,244,[320,850,405,930],[11,13,12,14],1),(7,1,244,[410,1005,505,1085],[13,15,14,16],1)]
records=[]
for i,v,head,roi,nroi,targethead in configs:
    source=r/f'source/native-walk-{i:03}-generated-v{v}.png';si=Image.open(source);nf=ni.crop((i*32,0,(i+1)*32,24));fb=m.foot_box(nf,nroi);target=[(fb[0]+fb[2])*2,fb[3]*4]
    original_measure=m.foot_box
    if i==1:m.foot_box=lambda im,roi,hoof=False:original_measure(im,roi,False)
    rec=m.register(source,(0,0,*si.size),head,roi,[128,96],targethead,target,i,outdir);m.foot_box=original_measure
    out=r/rec['path'];body=Image.open(out).convert('RGBA');body.save(r/f'source/native-walk-body-{i:03}.png',optimize=True)
    shadow_roi=[0,22,32,24];shadow=nf.crop(shadow_roi);shadow_path=r/f'source/native-shadow-{i:03}.png';shadow.save(shadow_path,optimize=True)
    assert all(a==0 or (red,green,blue)==(0,0,0)for red,green,blue,a in shadow.getdata());assert not nf.crop((0,21,32,22)).getchannel('A').getbbox(),'body-shadow gap must remain transparent'
    body.alpha_composite(shadow.resize((128,8),Image.Resampling.NEAREST),(0,88));body.save(out,optimize=True);m.compress(out)
    rec.update(source_index=i,output_index=i,output_path=rec['path'],native_hoof_roi=nroi,native_hoof_bounds=fb,body_visible_bounds=rec['visible_bounds'],visible_bounds=list(m.box(body)),bytes=out.stat().st_size,sha256=m.sha(out),native_projection={'source_roi':shadow_roi,'source_rgba_sha256':hashlib.sha256(shadow.tobytes()).hexdigest(),'source_file':str(shadow_path.relative_to(r)),'composite_at':[0,88],'scale':4,'filter':'nearest','separate_from_body_registration':True},direction='up' if i in [0,1] else 'down' if i in [4,5] else 'left',anchor_is_anatomical_foot=i!=1,anchor_kind='tail-end silhouette; tucked hind hooves overlap in source and are visually checked separately' if i==1 else 'selected visible hoof',registration_scope='Selected declared semantic anchor only; source frame/tile anchor remains [16,24]. Projection is not an anatomical anchor. Tail registration is explicitly not reported as foot precision.')
    records.append(rec)
for i,j in [(2,6),(3,7)]:
    src=ni.crop((j*32,0,(j+1)*32,24)).transpose(Image.Transpose.FLIP_LEFT_RIGHT);dst=ni.crop((i*32,0,(i+1)*32,24));assert src.size==dst.size and src.tobytes()==dst.tobytes();rep=next(x for x in records if x['source_index']==j);im=Image.open(r/rep['path']).convert('RGBA').transpose(Image.Transpose.FLIP_LEFT_RIGHT);out=outdir/f'frame-{i:03}.png';im.save(out,optimize=True);m.compress(out);records.append({'source_index':i,'source_frame':i,'output_index':i,'representative_frame':j,'kind':'native_proven_full_canvas_mirror','path':str(out.relative_to(r)),'output_path':str(out.relative_to(r)),'mirrored_from':rep['path'],'direction':'right','size':[128,96],'bytes':out.stat().st_size,'sha256':m.sha(out),'source_and_output_mirror_exact':True})
records.sort(key=lambda x:x['source_index']);(r/'source/native-walk-registration.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
for theme,bg,fg in [('dark','#1d2b35','#edf0e7'),('light','#e9e4d9','#26333a')]:
    board=Image.new('RGBA',(552,500),bg);dr=ImageDraw.Draw(board);dr.text((16,10),'天马真实战术左向 · 原CPU / 新图',font=m.FONT,fill=fg)
    for col,i in enumerate([6,7]):
        x=16+col*268;nf=ni.crop((i*32,0,(i+1)*32,24)).resize((256,192),Image.Resampling.NEAREST);new=Image.open(outdir/f'frame-{i:03}.png').convert('RGBA').resize((256,192),Image.Resampling.NEAREST);board.alpha_composite(nf,(x,42));board.alpha_composite(new,(x,264));dr.text((x+110,470),str(i),font=m.FONT,fill=fg)
    board.convert('RGB').save(r/f'reviews/tactical-native-side-{theme}.png',optimize=True)
print([(x['source_index'],x.get('registered_foot_anchor'),x['bytes'])for x in records])

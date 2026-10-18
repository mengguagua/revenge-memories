"""Technical packaging only: rectangular crops, isotropic scaling, whole-frame XY.
No painting, recoloring, warping or part stitching. Source art is ImageGen.
"""
from PIL import Image, ImageDraw
from pathlib import Path
import json

P=Path(__file__).parent
def mask(im): return im.getchannel('A').point(lambda x:255 if x>=128 else 0)
def bounds(im,roi):
    b=mask(im.crop(tuple(roi))).getbbox()
    if b is None: raise ValueError(roi)
    return [b[0]+roi[0],b[1]+roi[1],b[2]+roi[0],b[3]+roi[1]]

configs=[
 (0,'keyposes-generated-v1.png',[0,0,724,724],192/567,[200,312,324,320],0),
 (13,'keyposes-generated-v1.png',[724,0,1448,724],192/567,[200,312,292,320],0),
 (50,'keyposes-generated-v1.png',[1448,0,2172,724],192/567,[200,312,324,320],0),
 (1,'gallop-1-3-generated-v3.png',[0,0,724,724],None,[300,312,324,320],.65),
 (2,'gallop-1-3-generated-v2.png',[724,0,1416,724],None,[184,312,304,320],0),
 (3,'gallop-1-3-generated-v1.png',[1416,0,2172,724],None,[184,312,304,320],0),
 (4,'gallop-4-6-generated-v1.png',[0,0,724,724],None,[172,312,276,320],0),
 (5,'gallop-4-6-generated-v1.png',[724,0,1448,724],None,[172,312,276,320],0),
 (6,'gallop-4-6-generated-v1.png',[1448,0,2172,724],None,[172,312,276,320],0),
 (7,'gallop-7-9-generated-v2.png',[0,0,724,724],196/555,[232,312,252,320],0),
 (8,'gallop-7-9-generated-v3.png',[724,0,1448,724],196/555,[232,304,268,312],0),
 (9,'gallop-7-9-generated-v3.png',[1448,0,2172,724],196/555,[232,304,268,312],0),
 (10,'gallop-10-11-generated-v1.png',[0,0,887,887],None,[232,304,268,312],0),
 (11,'gallop-10-11-generated-v1.png',[887,0,1774,887],None,[232,304,268,312],0),
 (12,'turn-12-generated-v1.png',None,None,[240,312,268,320],0),
 (14,'turn-release-14-52-generated-v4.png',[0,0,916,858],None,[152,312,284,320],0),
 (52,'turn-release-14-52-generated-v1.png',[916,0,1832,858],None,[200,312,324,320],0),
 (15,'spin-015-generated-v6.png',None,'body-top:694',[148,312,292,320],0),
 (17,'spin-15-17-18-generated-v5.png',[603,0,1205,870],'body-top:407',[148,312,292,320],0),
 (18,'spin-15-17-18-generated-v5.png',[1205,0,1808,870],'body-top:407',[148,312,292,320],0),
 (16,'spin-16-19-20-selected-technical.png',[0,0,724,724],'body-top:313',[148,312,292,320],0),
 (19,'spin-16-19-20-selected-technical.png',[724,0,1448,724],'body-top:314',[148,312,292,320],0),
 (20,'spin-16-19-20-selected-technical.png',[1448,0,2172,724],'body-top:314',[148,312,292,320],0),
 (21,'spin-21-22-generated-v4.png',[0,0,887,887],'body-top:405',[148,312,292,320],0),
 (22,'spin-21-22-generated-v4.png',[887,0,1774,887],'body-top:405',[148,312,292,320],0),
]
records=[]
for n,fn,crop,scale,sroi,gxmin in configs:
    raw=Image.open(P/'source'/fn).convert('RGBA')
    if crop:raw=raw.crop(tuple(crop))
    sb=mask(raw).getbbox()
    orig=Image.open(P/'reference'/f'pose-{n:03}.png').convert('RGBA')
    ob=mask(orig).getbbox()
    scale_basis='source total visible height'
    if isinstance(scale,str):
        bodytop=int(scale.split(':')[1]);scale=184/(sb[3]-bodytop)
        scale_basis=f'manually inspected helmet crest y={bodytop} to visible hoof baseline; source helmet-to-hoof height184; raised lance excluded'
    if scale is None:scale=(ob[3]-ob[1])/(sb[3]-sb[1])
    art=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS)
    ab=mask(art).getbbox()
    # Only the lowest anatomically verified hooves; no lance or saddlecloth pixels.
    groi=[round(art.width*gxmin),ab[3]-6,art.width,ab[3]]
    gb=bounds(art,groi);tb=bounds(orig,sroi)
    gx=(gb[0]+gb[2])/2;tx=(tb[0]+tb[2])/2
    # ImageGen can contain alpha1 noise far from anatomy. Do not use that as feet.
    # Every selected pose has a verified hoof as its lowest visible object.
    # Preserve all alpha>4 edge pixels; only near-transparent encoding/interpolation
    # noise can lie outside the native canvas when the actual sole is registered.
    complete_hoof_bottom=art.getchannel('A').point(lambda v:255 if v>4 else 0).getbbox()[3]
    xy=[round(tx-gx),tb[3]-complete_hoof_bottom]
    out=Image.new('RGBA',(448,320));out.alpha_composite(art,tuple(xy))
    clipped=[v for i,v in enumerate(art.getchannel('A').getdata()) if v and not(0<=i%art.width+xy[0]<448 and 0<=i//art.width+xy[1]<320)]
    assert max(clipped,default=0)<=4, (n,'clipped visible alpha')
    pix=out.load()
    for y in range(out.height):
      for x in range(out.width):
        if pix[x,y][3]==0:pix[x,y]=(0,0,0,0)
    out.save(P/'frames'/f'frame-{n:03}.png',optimize=True)
    records.append({'frame':n,'raw_image':'source/'+fn,'raw_crop':crop,'isotropic_scale':scale,'scale_basis':scale_basis,'filter':'Lanczos','whole_frame_translation':xy,'source_hoof_roi':sroi,'source_hoof_bounds':tb,'generated_hoof_roi_after_scale':groi,'generated_hoof_bounds':gb,'source_hoof_anchor':[tx,tb[3]],'registered_hoof_anchor':[gx+xy[0],complete_hoof_bottom+xy[1]],'registered_opaque_sole_bottom':gb[3]+xy[1],'clipped_visible_alpha_gt4_pixels':0,'cropped_near_transparent_alpha_pixels':len(clipped),'maximum_cropped_alpha':max(clipped,default=0),'note':'Visible lowest hoof/hooves only; hidden joints not inferred. Alpha>=128 used for horizontal sole measurement, full visible alpha>4 sole edge for baseline. Faraway alpha1 encoding noise is not anatomy. Canvas cropping may omit alpha1..4 noise only, never a visible contour. No alpha threshold is applied to retained pixels; source alpha preserved inside canvas. RGB zeroed only where alpha==0.'})
(P/'source/selected-registration.json').write_text(json.dumps(records,indent=2))
for ids,name in [([0,13,50],'keyposes'),([1,2,3],'gallop-1-3'),([4,5,6],'gallop-4-6'),([7,8,9],'gallop-7-9'),([10,11],'gallop-10-11'),([12],'turn-12'),([14,52],'turn-release'),([15,17,18],'spin-15-17-18'),([16,19,20],'spin-16-19-20'),([21,22],'spin-21-22')]:
 board=Image.new('RGB',(448*len(ids),1316),(27,31,38));d=ImageDraw.Draw(board)
 for row in range(4):
  bg=(27,31,38) if row<2 else (232,230,222)
  d.rectangle((0,row*329,board.width,(row+1)*329),fill=bg)
  for col,n in enumerate(ids):
   im=Image.open(P/('reference' if row%2==0 else 'frames')/(f'pose-{n:03}.png' if row%2==0 else f'frame-{n:03}.png'))
   board.paste(im,(448*col,9+329*row),im)
   d.text((448*col+8,329*row),f'{n:03} '+('original' if row%2==0 else 'new'),fill=(240,240,240) if row<2 else (30,30,30))
 board.save(P/'reviews'/f'{name}-selected-dark-light.png',optimize=True)

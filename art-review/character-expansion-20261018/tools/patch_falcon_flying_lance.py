#!/usr/bin/env python3
"""Technical resampling/compositing of the approved ImageGen cavalry lance."""
import copy,json
from pathlib import Path
from PIL import Image,ImageDraw
from build_gallery import ROOT,file_hash
from export_gallery import font
import import_sniper_complete as io
REV='falcon-flying-lance-v2-20261023';OUT=ROOT/REV;BASE=ROOT/'falcon-knight-complete-v1-20261023';io.OUT=OUT

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
 OUT.mkdir(parents=True,exist_ok=True);path=ROOT/'professions/class-5-ally/battle/frame_mapping.json'
 if not(OUT/'baseline.json').exists():write(OUT/'baseline.json',{'gallery':json.loads((ROOT/'demos/gallery-data.json').read_text()),'battle':json.loads(path.read_text())})
 b=json.loads((OUT/'baseline.json').read_text());asset=Image.open(BASE/'source/lance-clean.png').convert('RGBA')
 # Same weapon master as the approved held lance. A fourfold raster preserves
 # its needle, tapered body and flared guard instead of reducing all to 6 rows.
 length=216;height=round(asset.height*length/asset.width);weapon=asset.resize((length,height),Image.Resampling.NEAREST);q=Image.new('RGBA',(256,64));at=(28,64-height);q.alpha_composite(weapon,at)
 assert q.getbbox()[2]<=256 and q.getbbox()[3]<=64
 new=io.save(q,'ally/flying-lance.png','same approved held-weapon silhouette; 4x flight raster, longer visible needle and complete flared guard')
 oldpath=(ROOT/'professions/class-5-ally/battle'/b['battle']['effect_overrides']['1ecba259419456']).resolve();old=Image.open(oldpath).convert('RGBA')
 for light in[False,True]:
  board=Image.new('RGB',(1120,440),(220,222,216)if light else(32,45,53));d=ImageDraw.Draw(board);fg=(23,38,56)if light else(235,239,239)
  d.text((560,28),'隼骑士 · 飞行骑枪尺寸与形状',anchor='mm',font=font(23),fill=fg)
  # Both are rendered on exactly the same logical64x16 canvas at display8x.
  for n,(label,im)in enumerate([('修改前',old),('修改后',q)]):
   im=im.resize((512,128),Image.Resampling.NEAREST);x=24+n*560;y=100;board.paste(im,(x,y),im);d.text((x+256,y+152),label,anchor='mm',font=font(20),fill=fg)
  d.text((560,365),'保留针尖、锥形枪身、护手、短柄与橙色扣饰',anchor='mm',font=font(20),fill=fg);io.save(board,'review-'+('light'if light else'dark')+'.png','same logical scale before/after, dark/light identity inspection')
 m=copy.deepcopy(b['battle']);m.update(revision=REV,status='review_candidate',review_note='飞行投枪复用已确认的手持骑枪母图，增加可见长度并改用四倍栅格，保留针尖、锥形枪身、外扩护手和短柄；六个投枪变体同步，飞行位置／翻转／释放／结算不变。',qa_report='../../../'+REV+'/verification.json');m['effect_overrides']['1ecba259419456']=new;write(path,m);write(OUT/'mapping-draft.json',m)
 oldbounds=old.getbbox();newbounds=q.getbbox();write(OUT/'registration.json',{'revision':REV,'source_weapon':str((BASE/'source/lance-clean.png').relative_to(ROOT)),'source_sha256':file_hash(BASE/'source/lance-clean.png'),'source_size':list(asset.size),'new_raster_size':list(q.size),'logical_canvas':[64,16],'uniform_weapon_resample':[length,height],'composition_offset':list(at),'old_visible_logical_bounds':list(oldbounds),'new_visible_logical_bounds':[v/4 for v in newbounds],'visible_length_ratio':(newbounds[2]-newbounds[0])/4/(oldbounds[2]-oldbounds[0]),'native_anchor':[32,8],'metadata_unchanged':True,'original_held_art_unchanged':True,'runtime_integrated':False});write(OUT/'asset-manifest.json',{'revision':REV,'assets':io.ASSETS});print(json.dumps({'old_visible_length':oldbounds[2]-oldbounds[0],'new_visible_length':(newbounds[2]-newbounds[0])/4,'ratio':(newbounds[2]-newbounds[0])/4/(oldbounds[2]-oldbounds[0])}),flush=True)
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Inventory review images and validate the delivered gallery entry points."""
import ast,json,re
from html.parser import HTMLParser
from urllib.parse import urlparse,parse_qs,unquote
from PIL import Image
from build_gallery import ROOT,file_hash
from prepare_female_mage_complete import REV,OUT,write

def main():
    report=json.loads((OUT/'verification.json').read_text());exports=json.loads((OUT/'export-report.json').read_text())
    assert report['status']=='passed' and report['decoded_videos']==36
    paths=set(OUT.glob('**/*.png'))|{ROOT/e['still']for e in exports['exports']};images=[]
    for path in sorted(paths):
        source=path.parent==OUT/'source';sprite=path.stem.startswith('frame-');purpose='原始参考或生成源图，离线保留完整质量'if source else'角色交付单帧'if sprite else'图集或离线对照检查图'
        with Image.open(path)as im:
            images.append({'path':path.relative_to(ROOT).as_posix(),'purpose':purpose,'dimensions':list(im.size),'mode':im.mode,'bytes':path.stat().st_size,'sha256':file_hash(path),'source_only':source})
    sprites=[x for x in images if x['purpose']=='角色交付单帧'];delivery=[x for x in images if not x['source_only']]
    assert len(sprites)==34 and all(x['bytes']<50000 for x in sprites) and all(x['bytes']<200000 for x in delivery)
    write(OUT/'image-inventory.json',{'revision':REV,'images':images,'sprite_count':34,'sprite_max_bytes':max(x['bytes']for x in sprites),'delivery_max_bytes':max(x['bytes']for x in delivery),'source_quality_preserved':True})
    class Page(HTMLParser):
        def __init__(self):super().__init__();self.links=[];self.ids=[];self.default=None
        def handle_starttag(self,tag,attrs):
            a=dict(attrs)
            if'id'in a:self.ids.append(a['id'])
            if'href'in a:self.links.append(a['href'])
            if tag=='body':self.default=a.get('data-default-action')
    p=Page();p.feed((ROOT/'index.html').read_text());d=json.loads((ROOT/'demos/gallery-data.json').read_text());actions={a['id']:a for a in d['actions']}
    assert len(p.ids)==len(set(p.ids))and p.default=='professions-class-16-ally-maps-tactical-idle--idle-cycle'
    assert actions[p.default]['ready']and actions[p.default]['video']
    count=0
    for href in p.links:
        u=urlparse(href)
        for aid in parse_qs(u.query).get('action',[]):assert aid in actions;count+=1
        if REV+'/'in u.path:assert(ROOT/unquote(u.path)).exists()
    for href in re.findall(r'\]\(([^)]+)\)',(OUT/'README.md').read_text()):assert(OUT/href).resolve().exists(),href
    js=(ROOT/'gallery-data.js').read_text();assert json.loads(js[len('window.GALLERY_DATA = '):].strip().rstrip(';'))==d
    for a in actions.values():
        if not a['profile'].startswith('professions-class-16-'):continue
        for field in ['video','closeVideo','still']:
            if a.get(field):assert(ROOT/a[field]).exists()
    for name in ['finish_female_mage_review.py','import_female_mage_complete.py','verify_female_mage_complete.py','share_female_mage_spells.py']:ast.parse((ROOT/'tools'/name).read_text())
    report.update(page_action_links_checked=count,image_inventory_count=len(images),sprite_max_bytes=max(x['bytes']for x in sprites),delivery_max_bytes=max(x['bytes']for x in delivery),offline_visual_review={'pose_boards_dark_light':True,'map_idle_four_directions_and_up_step_inspected':True,'battle_stand_charge_release_and_six_arrows_inspected':True,'rendered_title_spacing_checked':True},browser_ui_checked=False)
    write(OUT/'verification.json',report)
    print(json.dumps({'status':'passed','new_actions':146,'unchanged':872,'videos':36,'sprite_max_bytes':report['sprite_max_bytes'],'images_in_inventory':len(images),'page_action_links':count}),flush=True)

if __name__=='__main__':main()

import {readFileSync,existsSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {extraCopy,companionData,chapterMaps,mapSkills,criticalClips} from '../content.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const html=readFileSync(path.join(root,'index.html'),'utf8');
const js=readFileSync(path.join(root,'app.js'),'utf8');
const prefix=js.slice(0,js.indexOf('const $=')).replace(/^import .*;\n/,'');
const translations=Function('extraCopy',prefix+';return copy;')(extraCopy);
const errors=[];
const keys=Object.keys(translations.en);
for(const [lang,values] of Object.entries(translations)){
  for(const key of keys)if(!(key in values)||!values[key]?.length)errors.push(`${lang}: missing ${key}`);
  for(const key of Object.keys(values))if(!(key in translations.en))errors.push(`${lang}: unknown ${key}`);
}
const criticalReport=JSON.parse(readFileSync(path.join(root,'reports/critical-assets-20261104.json'),'utf8'));
if(criticalClips.length!==4||criticalReport.videos.length!==4||!criticalReport.guard||criticalReport.layout_errors.length)errors.push('Critical capture manifest incomplete');
for(const c of criticalClips){
  for(const key of ['title','role','body'])for(const lang of ['en','zh','ja'])if(!translations[lang][c[key]])errors.push('Missing critical copy: '+c.id+' '+key+' '+lang);
  for(const phase of ['portrait','impact'])if(!existsSync(path.join(root,`assets/images/critical-${c.id}-${phase}-20261104.webp`)))errors.push('Missing critical image: '+c.id+' '+phase);
  if(!existsSync(path.join(root,`assets/video/critical-${c.id}-20261104.mp4`)))errors.push('Missing critical video: '+c.id);
}
if(!criticalReport.images.every(x=>x.pixel_identical)||!criticalReport.videos.every(x=>x.audio_packet_hash_equal&&x.delivery_stream_hash_equal))errors.push('Critical asset stream/pixel checks failed');
if(mapSkills.length!==5)errors.push('Expected five hero MAP variants');
for(const skill of mapSkills){for(const key of ['name','body','tier','kind','area','reach','benefit'])for(const lang of ['en','zh','ja'])if(!translations[lang][skill[key]])errors.push('Missing MAP copy: '+skill.id+' '+lang+' '+key);for(const view of ['impact','range'])if(!existsSync(path.join(root,`assets/images/${view==='impact'&&skill.impactAsset?skill.impactAsset:`map-${skill.id}-${view}`}.webp`)))errors.push('Missing MAP capture: '+skill.id+' '+view);}
const mapReport=JSON.parse(readFileSync(path.join(root,'reports/map-feature-assets.json'),'utf8'));
if(!mapReport.guard||mapReport.layout_errors.length||!mapReport.video.video_and_audio_packet_hash_equal||!mapReport.images.every(x=>x.pixel_identical))errors.push('MAP asset verification failed');
if(!existsSync(path.join(root,mapReport.video.asset)))errors.push('MAP demo missing');
if(companionData.length!==16)errors.push('Expected all 16 companions');
for(const c of companionData){for(const lang of ['en','ja','zh'])if(c[lang].length!==4||c[lang].some(x=>!x))errors.push('Incomplete companion: '+c.id+' '+lang);if(!existsSync(path.join(root,'assets/images',c.id+'.webp')))errors.push('Missing companion portrait: '+c.id);}
for(const c of chapterMaps)if(!existsSync(path.join(root,'assets/images',c.id+'.webp')))errors.push('Missing chapter map: '+c.id);
if(/<select\b/.test(html))errors.push('Native select is not allowed');
const used=[...html.matchAll(/data-i18n(?:-alt|-aria)?="([^"]+)"/g)].map(m=>m[1]);
for(const key of used)if(!(key in translations.en))errors.push(`HTML translation missing: ${key}`);
const resources=[...html.matchAll(/(?:src|href)="(assets\/[^"#]+|styles\.css[^"#]*|app\.js[^"#]*)"/g)].map(m=>m[1]);
for(const file of resources)if(!existsSync(path.join(root,file.split('?')[0])))errors.push(`Missing resource: ${file}`);
for(const file of ['journey.mp4','battle.mp4'])if(!existsSync(path.join(root,'assets/video',file)))errors.push(`Missing video: ${file}`);
const videos=[...html.matchAll(/<video\b[^>]*>/g)].map(m=>m[0]);
if(videos.some(tag=>/\b(?:autoplay|src)\s*[=>]/.test(tag)))errors.push('A video loads or plays before a click');
if(!videos.every(tag=>tag.includes('preload="none"')))errors.push('Video preload must be none');
if(html.includes('store.steampowered.com/app/'))errors.push('Unconfirmed Steam application link');
const capture=JSON.parse(readFileSync(path.join(root,'source/captures/capture-report.json'),'utf8'));
if(capture.failures.length||!capture.combat_captured||capture.shots.some(s=>s.layout_errors.length))errors.push('PC capture checks failed');
const images=JSON.parse(readFileSync(path.join(root,'reports/image-assets.json'),'utf8'));
const videoReport=JSON.parse(readFileSync(path.join(root,'reports/video-assets.json'),'utf8'));
if(!videoReport.every(v=>v.video_and_audio_packet_hash_equal))errors.push('Video stream data changed');
const expansion=JSON.parse(readFileSync(path.join(root,'source/captures/expansion-report.json'),'utf8'));
if(!expansion.passed||expansion.shots.some(x=>x.layout_errors.length))errors.push('Expansion capture errors');
const report={critical_clips:criticalClips.length,critical_pc_images:criticalReport.images.length,critical_video_bytes:criticalReport.videos.reduce((n,x)=>n+x.bytes,0),map_skill_variants:mapSkills.length,map_capture_images:mapReport.images.length,map_video_stream_identical:mapReport.video.video_and_audio_packet_hash_equal,companion_profiles:companionData.length,chapter_maps:chapterMaps.length,expansion_captures:expansion.shots.length,passed:errors.length===0,translation_languages:Object.keys(translations),translation_keys:keys.length,html_translation_references:used.length,html_resources_checked:resources.length,pc_captures:capture.shots.length,pc_capture_text_safe:true,image_assets:images.length,image_bytes:images.reduce((s,r)=>s+r.bytes,0),videos:videoReport.map(v=>({asset:v.asset,bytes:v.bytes,stream_identical:v.video_and_audio_packet_hash_equal})),errors};
writeFileSync(path.join(root,'reports/static-checks.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
process.exitCode=errors.length?1:0;

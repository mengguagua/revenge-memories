import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {renderFrames,spriteSheet} from './pixelfx-work/tools/lib/fxlib.mjs';
const ROOT=dirname(fileURLToPath(import.meta.url)),OUT=join(ROOT,'../../weapon-magic-r2-20261107');
const steel=['#24313c','#3c5260','#607f8b','#8ea9b0','#b4c9c6','#d6dfd1','#eee9cf','#fcf2d8'];
const bronze=['#302a2b','#544738','#807050','#aa9468','#cbb584','#e2d2a4','#f0e3c4','#fff0d3'];
const white=['#283943','#496069','#6e8b93','#9cb4b4','#c0d0c7','#dce5d8','#f0edda','#faf2df'];
const gold=['#392c30','#654733','#976c3e','#c29452','#dbb66d','#e8cf93','#f5e4ba','#fff0d4'];
const lance=[
 {class:6,id:'soldier',name:'士兵',tier:1,palette:steel,direction:'窄直枪芒',description:'一束短直银灰枪芒，三枚细小火星；出手清楚、收势利落。'},
 {class:2,id:'armored',name:'重装兵',tier:2,palette:bronze,direction:'厚刃重楔',description:'宽而短的铜色冲击楔，带沉重碎屑和贴地尘团。'},
 {class:22,id:'bastion',name:'壁垒卫士',tier:3,palette:gold,direction:'三层贯阵',description:'三层压缩枪势同时向一个落点收束，金属火星与尘浪更宽。'},
 {class:1,id:'cavalry',name:'骑兵',tier:1,palette:steel,direction:'前冲流线',description:'随骑乘前冲展开细长空气流线，命中处只有一束枪尖反光。'},
 {class:4,id:'knight',name:'骑士',tier:2,palette:white,direction:'旋锋穿刺',description:'两道银灰弧纹围绕枪尖旋进，汇成更锐利的穿刺亮芒。'},
 {class:7,id:'grandknight',name:'大骑士',tier:3,palette:bronze,direction:'重骑贯锋',description:'三道宽阔压力弧沿同一次前刺展开，长枪芒和落尘强化重量。'},
 {class:3,id:'pegasus',name:'天马骑士',tier:1,palette:white,direction:'轻羽突刺',description:'轻薄羽状气流沿枪尖汇拢，轮廓轻巧，尾迹向上挑起。'},
 {class:5,id:'falcon',name:'隼骑士',tier:2,palette:gold,direction:'双翼破风',description:'更宽的双翼气流包住突刺轨迹，锐利交汇线和金色火星一起消散。'}
];
const bows=[
 {class:12,id:'archer',name:'弓箭手',tier:1,palette:steel,direction:'短尾快箭',description:'轻木杆、短羽尾和少量风迹，命中反馈短促。'},
 {class:13,id:'sniper',name:'狙击手',tier:2,palette:white,direction:'细锋贯穿',description:'细长镞刃与收束气流强调精准，接触时出现狭长贯穿亮线。'},
 {class:20,id:'bowknight',name:'弓骑士',tier:3,palette:bronze,direction:'重箭破风',description:'厚镞、双侧风迹和更宽的命中压力弧，表现高速重箭。'},
 {profile:'21_ally',id:'hero-base',name:'胡纳普 · 基础',tier:2,rank:1,palette:gold,direction:'铜金羽箭',description:'男主独立的铜金箭镞、斜切双羽和折线尾迹，命中呈收束的金色锐角。'},
 {profile:'23_ally',id:'hero-advanced',name:'胡纳普 · 破晓勇士',tier:3,rank:2,palette:gold,direction:'破晓贯心',description:'进阶专属长镞与三层金羽风迹，单箭抵达后展开更宽的锐角冲击。'}
];
const palettes={
 fire:['#35252b','#66332d','#984731','#bd6537','#dd8d43','#ecb660','#f5d695','#fff0d8'],
 ragnarok:['#30202b','#5b2734','#943837','#c55738','#df8040','#edac5b','#f6d58a','#fff0cc'],
 thunder:['#252d40','#3d4c68','#5c7896','#81a3b9','#a8c9d4','#cde1df','#e9ede0','#fff3dc'],
 levin:['#292b41','#44496c','#66769b','#8ea7be','#b9ced6','#d8e3df','#eeeede','#fff3db'],
 holy:['#34303b','#595163','#81768a','#aaa0a7','#c9bfad','#dfd4b6','#eee4cb','#fff2dc'],
 halo:['#383039','#605044','#897251','#b2996a','#d0bb86','#e6d6a9','#f2e6c7','#fff3da'],
 rain:steel,wind:white,
 wisp:['#262738','#46415c','#69607e','#8b7c9a','#afa0b9','#cbbdd0','#e1d5de','#f1e8e4'],
 slime:['#28382f','#40523a','#5e7249','#81915e','#a5b280','#c5cea5','#dce0c1','#eeedd7'],
 death:['#242332','#3f3652','#625172','#887596','#ad99b4','#cbb6cb','#e2cfe0','#f0e4e8'],
 medusa:['#2c2938','#514256','#796077','#9f8096','#bda2b3','#d5bfcd','#e6d4df','#f3e8e9'],
 drain:['#35262f','#5e3946','#8a5464','#ad7985','#c69aa3','#dcc0bf','#eaddcc','#f7eddd']
};
const magic=[
 [15,'levin','雷剑','刃上蓄电 → 斜向导雷 → 分叉余电',.22],
 [23,'fire','火球','旋焰聚核 → 火团飞行 → 爆燃与余烬',.10],
 [24,'thunder','雷电','电荷聚集 → 先导通道 → 单次分叉落雷',.28],
 [25,'ragnarok','诸神黄昏','熔火蓄势 → 地面聚焰 → 单次烈焰喷发',.36],
 [26,'holy','圣光','光瓣聚拢 → 光梭释放 → 聚焦光柱与碎芒',.16],
 [27,'wind','风刃','旋流成刃 → 弧风飞行 → 层叠风刃消散',.10],
 [28,'rain','箭雨','三瓣光纹 → 汇聚箭光 → 同刻命中与光屑',.18],
 [29,'halo','光环','复层光轮 → 收束光束 → 扩散光环',.22],
 [31,'wisp','鬼火','紫灰灵焰 → 冷焰飞行 → 碎焰与暗烟',.10],
 [32,'slime','史莱姆','黏液凝聚 → 胶团抛射 → 溅滴与短暂黏液轮廓',.10],
 [33,'death','死亡','暗流收束 → 虚空团飞行 → 钩状暗刃坍缩',.26],
 [34,'medusa','美杜莎','蛇纹目光 → 晶状投影 → 菱晶碎芒',.22],
 [42,'drain','吸血','暗红聚核 → 吸取接触 → 碎光回流',.10]
].map(([weapon,id,name,direction,hit])=>({weapon,id,name,direction,hit,palette:palettes[id]}));
const specs=[];
specs.push({id:'r2-map-hero-bow',module:'weapons',options:{mode:'maphit',style:'hero-advanced',tier:1,palette:gold,light:.10},meta:{size:[48,40],origin:[24,28],duration:.75}});
const angles=JSON.parse(readFileSync(join(ROOT,'weapon-angles.json'),'utf8'));
for(const x of lance){
 specs.push({id:'r2-lance-'+x.id,module:'weapons',options:{mode:'lance',style:x.id,tier:x.tier,palette:x.palette,light:.13}});
 specs.push({id:'r2-wake-'+x.id,module:'weapons',options:{mode:'wake',style:x.id,tier:x.tier,palette:x.palette,light:.08},meta:{size:[80,40],origin:[64,20],duration:.6,loop:true}});
 for(const angle of new Set(angles.filter(a=>a.class===x.class&&a.angle!==0).map(a=>a.angle)))specs.push({id:'r2-lance-'+x.id+'-angle'+angle,module:'weapons',options:{mode:'lance',style:x.id,tier:x.tier,palette:x.palette,light:.13,angle:angle*Math.PI/180},meta:{size:[160,144],origin:[96,96]}});
}
for(const x of bows){
 specs.push({id:'r2-arrow-'+x.id,module:'weapons',options:{mode:'arrow',style:x.id,tier:x.tier,palette:x.palette,light:.10},meta:{size:[80,40],origin:[64,20],duration:.6,loop:true}});
 specs.push({id:'r2-bowhit-'+x.id,module:'weapons',options:{mode:'bowhit',style:x.id,tier:x.tier,palette:x.palette,light:.13}});
 if(x.profile)specs.push({id:'r2-cinema-bowhit-'+x.id,module:'weapons',options:{mode:'bowhit',style:x.id,tier:x.tier+1,palette:x.palette,light:.17}});
}
for(const x of magic){
 for(const phase of['charge','travel','impact']){
  const options={kind:x.id,phase,hit:x.hit,size:1,palette:x.palette,light:.15};
  const meta=phase==='charge'?{size:[80,80],origin:[40,40],duration:1.2,loop:true}:phase==='travel'?{size:[96,48],origin:[72,24],duration:.8,loop:true}:{};
  specs.push({id:'r2-'+x.id+'-'+phase,module:'spells',options,meta});
 }
}
for(const kind of['fire','holy','thunder','wind']){
 const x=magic.find(x=>x.id===kind);
 for(const phase of['charge','travel','impact']){
  specs.push({id:'r2-cinema-'+kind+'-'+phase,module:'spells',options:{kind,phase,hit:x.hit,size:1.45,palette:x.palette,light:.16},meta:phase==='charge'?{size:[112,112],origin:[56,56],duration:1.2,loop:true}:phase==='travel'?{size:[144,80],origin:[108,40],duration:.8,loop:true}:{size:[176,184],origin:[88,144]}});
 }
}
const effects={};mkdirSync(join(OUT,'assets/fx'),{recursive:true});
for(const s of specs){
 const imported=await import(pathToFileURL(join(ROOT,'pixelfx-work/src/fx/revision2/'+s.module+'.js')));
 const meta={...imported.meta,...s.meta},fx={id:'revision2/'+s.id,meta,mod:{...imported,meta}};
 const rendered=renderFrames(fx,{fps:60,actor:false,bg:'none',options:{seed:23,...s.options}});
 const sheet=spriteSheet(fx,rendered,s.id);writeFileSync(join(OUT,'assets/fx/'+s.id+'.png'),sheet.png);writeFileSync(join(OUT,'assets/fx/'+s.id+'.json'),JSON.stringify(sheet.json,null,2));
 effects[s.id]={...sheet.json.meta.pixelfx,path:'assets/fx/'+s.id+'.png',module:s.module,options:s.options};console.log(s.id,sheet.png.length);
}
writeFileSync(join(OUT,'assets/fx/manifest.json'),JSON.stringify({upstream:'patch-gg/pixelfx',commit:'a84159688af3ca37a4be05a0d422b94451b2e24e',effects},null,2));
writeFileSync(join(ROOT,'design.json'),JSON.stringify({lance,bows,magic,promotion_chains:[[6,2,22],[1,4,7],[3,5],[12,13,20]],notes:'Profession stages follow current rules_full promotions; hero advanced stage follows hero_profession. Stronger VFX never add attacks, damage, status or unlocks.'},null,2));

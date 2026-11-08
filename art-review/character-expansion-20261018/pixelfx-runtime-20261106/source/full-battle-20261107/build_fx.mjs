import{readFileSync,writeFileSync,mkdirSync}from'node:fs';
import{dirname,join}from'node:path';import{fileURLToPath,pathToFileURL}from'node:url';
import{renderFrames,spriteSheet}from'./pixelfx-work/tools/lib/fxlib.mjs';
const root=dirname(fileURLToPath(import.meta.url)),lib=join(root,'pixelfx-work/src/fx'),dir=join(lib,'revenge'),out=join(root,'../../full-battle-20261107/assets/fx');mkdirSync(out,{recursive:true});
const changes=[];
function adapt(from,to,pairs){let s=readFileSync(join(lib,from),'utf8');for(const[a,b]of pairs){if(!s.includes(a))throw Error(to+' missing '+a);s=s.replaceAll(a,b);}writeFileSync(join(dir,to+'.js'),'// Native-size PixelFX adaptation for preview only.\n'+s);changes.push({from,to,pairs});}
adapt('melee/thrust.js','native-thrust',[
 ['size: [196, 76]','size: [112, 64]'],['origin: [34, 62]','origin: [38, 52]'],['actor: 2','actor: 0'],['reach: 66','reach: 23'],['ground: () => 0','ground: () => -4'],
 ['[-7, -4, -2, 0, 2, 4, 7]','[-3, 0, 3]'],['Rg.range(7, 17)','Rg.range(4, 8)'],['Rg.range(18, 42)','Rg.range(7, 14)'],['Rg.range(200, 340)','Rg.range(65, 110)'],
 ['i < 12','i < 4'],['i < 10','i < 4'],['i < 4; i++) ps.spawn(P.STAR','i < 1; i++) ps.spawn(P.STAR'],['Rg.range(150, 330)','Rg.range(55, 100)'],['Rg.range(40, 120)','Rg.range(15, 45)'],
 ['44, C[4], 0.45','20, C[4], 0.22'],['14, WHITE, 0.6','7, WHITE, 0.25'],['24 * g','9 * g'],['2 + 7 *','1 + 3 *'],['4 + 12 *','2 + 5 *']
]);
adapt('impacts/blunt-hit.js','native-blunt',[
 ['from "./_lib.js"','from "../impacts/_lib.js"'],['size: [128, 88]','size: [88, 72]'],['origin: [64, 72]','origin: [44, 62]'],['height: 22','height: 18'],['floor = () => 0','floor = () => -3'],
 ['length: 9','length: 6'],['i / 9','i / 6'],['length: 30','length: 12'],['i / 30','i / 12'],['R.range(13, 16)','R.range(5, 7)'],['R.range(6, 15)','R.range(3, 7)'],['R.range(3.2, 5)','R.range(1.5, 2.5)'],['R.range(40, 140)','R.range(16, 42)'],['R.range(2.4, 6.2)','R.range(1.4, 2.6)'],['R.range(70, 140)','R.range(25, 55)'],['R0 = f ? 13.5 : 11.5','R0 = f ? 6.5 : 5.5'],['48, WARM, 0.6','22, WARM, 0.22'],['16, WHITE, 0.6','8, WHITE, 0.3'],['36, WARM, 0.25','16, WARM, 0.12']
]);
adapt('holy/heal.js','native-heal',[
 ['from "./_lib.js"','from "../holy/_lib.js"'],['size: [80, 104]','size: [64, 76]'],['origin: [40, 92]','origin: [32, 66]'],['actor: 2','actor: 0'],['S = shapeOf(A)','S = {edge: []}'],['if (t < LIFT1 + 0.35) {','if (false) { // Keep the actual game actor; no stock-body recolor.'],
 ['NP = 8, PR = 16','NP = 6, PR = 11'],['TOPY = -43','TOPY = -31'],['R.range(4.2, 5.2)','R.range(2.5, 3.4)'],['k < 8; k++','k < 4; k++'],['k / 8','k / 4'],['R.range(12, 18)','R.range(8, 11)'],['R.range(46, 58)','R.range(28, 38)'],['lerp(PR, 12','lerp(PR, 8'],['rb = 6, rt = rb + 9','rb = 4, rt = rb + 6'],['26, C[5], 0.55','16, C[5], 0.22'],['else if (m.kind) heart(p, x, y - u * 6, C, k);','else if (m.kind) sparkle(p, x, y - u * 4, 1.6, C[6], C[4], .2*k);']
]);
adapt('revenge/rm-hit.js','cinema-hit',[
 ['size: [72, 56]','size: [112, 96]'],['origin: [28, 44]','origin: [48, 84]'],['height: 16','height: 34'],['R.range(15, 18)','R.range(27, 32)'],['w: 1.4','w: 2'],['R.range(7, 9)','R.range(13, 16)'],['R.range(3, 4), w: 1.5','R.range(9, 12), w: 1.5'],['diamond(p, X, Y, 2','diamond(p, X, Y, 3'],['i < 6','i < 10'],['18, C[4], 0.25','28, C[4], 0.25']
]);
adapt('shadow/dark-explosion.js','native-shadow',[
 ['from "./_lib.js"','from "../shadow/_lib.js"'],['size: [280, 248]','size: [80, 72]'],['origin: [140, 206]','origin: [40, 64]'],['duration: 3.8','duration: 1.25'],
 ['Y = -54, RS = 16, REL = 0.52, BURN = 1.62, POP = 1.84','Y = -20, RS = 6, REL = 0, BURN = 0.32, POP = 0.55'],['floor = () => 0','floor = () => -5'],
 ['r + 12 * heat + 2','r + 4 * heat + 2'],['1.5 + 12 * Math.max(0, T1) + 6 * Math.max(0, T2)','0.5 + 4 * Math.max(0, T1) + 2 * Math.max(0, T2)'],
 ['released = false, collapsing = false, popped = false','released = true, collapsing = false, popped = true'],['0 : 60 * (1 - ease.inQuad','0 : 18 * (1 - ease.inQuad'],
 ['100, C[4], 1.25','24, C[4], 0.35'],['86, mix(C[6], WHITE, 0.5), 1.3','18, mix(C[6], WHITE, 0.5), 0.35'],
 ['r1: 104','r1: 24'],['r1: 62','r1: 14'],['r1: 124','r1: 28'],['th: 3.6','th: 1.4'],
 ['i < 34','i < 6'],['i < 20','i < 4'],['i < 84','i < 7'],['i < 28','i < 4'],['i < 24','i < 3'],['i < 12','i < 3'],['i < 10','i < 2'],['i < 14','i < 3'],
 ['R.range(80, 170)','R.range(20, 45)'],['R.range(130, 220)','R.range(30, 60)'],['R.range(40, 110)','R.range(10, 25)'],['R.range(6, 11)','R.range(1.5, 2.5)'],['R.range(3, 4.5)','R.range(1, 1.5)'],['R.range(120, 235)','R.range(35, 70)'],['R.range(30, 130)','R.range(10, 35)'],['R.range(15, 70)','R.range(6, 20)'],['R.range(50, 120)','R.range(15, 32)'],['R.range(10, 40)','R.range(4, 12)'],['R.range(110, 200)','R.range(30, 60)'],['R.range(26, 48)','R.range(9, 15)'],
 ['R.range(1.6, 2.6)','R.range(.55, .9)'],['R.range(1.3, 2.5)','R.range(.45, .8)'],['R.range(2, 2.8)','R.range(.5, .85)'],['R.range(1.6, 2.4)','R.range(.5, .8)'],['R.range(1.2, 1.7)','R.range(.35, .65)'],['R.range(0.9, 1.6)','R.range(.3, .6)'],['R.range(0.6, 0.9)','R.range(.25, .4)'],['R.range(7, 12)','R.range(2, 3.5)'],['R.range(5, 9)','R.range(1.5, 3)'],
 ['ps.list.length = 0;','// Keep the one release spray.'],['dt * 34','dt * 12'],['b.y = -1;','b.y = -6;'],['const r = 36 *','const r = 9 *'],['? 36 *','? 9 *'],['if (pu >= 0 && pu < 1)','if (false && pu >= 0 && pu < 1)'],
 [', 0, R.chance(0.5));',', 0, false);'],[', 0, R.chance(0.2));',', 0, false);'],
 ['reach: 84','reach: 24'],['74, C[4], 0.24','22, C[4], 0.14'],['sr + 16','sr + 6'],['sr + 54','sr + 18'],['Y + Math.sin(g) * rr > 0.5','Y + Math.sin(g) * rr > -5'],['(x, y) => y < 0.5','(x, y) => y < -5'],
 ['  return {\n    update(dt) {','  release();\n  return {\n    update(dt) {']
]);
const steel=['#243840','#405663','#63818d','#91b2b9','#bdd0ce','#dce7df','#f1f0e2'],gold=['#302e35','#5a4d43','#8d7959','#b9a77d','#d7c9a4','#e5ddc3','#f1ecda','#f7f1df'],fire=['#2d2026','#65302c','#9f4230','#c76635','#df903f','#ecb65b','#f5d68b','#f5e5b7','#fff0d6'],holy=['#37303e','#605765','#8e8391','#b9aeba','#d4cbd0','#e4dcd5','#efeadb','#f6f0e1'],green=['#243c38','#405b50','#628571','#83a38b','#a8c1a3','#c6d8b7','#dce4ca','#eceddb'],voidC=['#252738','#403c54','#5e5877','#7f7595','#a095af','#bfb0c6','#d9cbdc','#e9dfea'];
const specs=[
 {id:'hit',module:'rm-hit',options:{palette:gold,light:.3}},{id:'cannon',module:'rm-hit',options:{palette:gold,light:.3}},
 {id:'core',module:'rm-core',options:{palette:holy,light:.3}},{id:'water',module:'rm-water',options:{palette:['#1f3642','#2e4d59','#466a76','#638b95','#88abb0','#b0cace','#d1dfdf','#e9eeee'],light:.12}},
 {id:'arrow',module:'rm-arrow',options:{palette:steel,wood:['#352f29','#65523c','#967f59','#c2ae83'],steel:['#32404a','#667b81','#a3b2b5','#d5dfda'],wind:'#7899a5',light:.15}},
 {id:'slash',module:'rm-slash',options:{palette:steel,sparks:gold,radius:22,light:.22}},
 {id:'thrust',module:'native-thrust',options:{palette:steel,sparks:gold,reach:23,light:.2}},
 {id:'blunt',module:'native-blunt',options:{palette:gold,warm:'#c3ac84',dust:'#8e8c86',clod:'#61594d',light:.2}},
 {id:'heal',module:'native-heal',options:{palette:green,light:.16}},
 {id:'lightning',module:'rm-core',options:{palette:steel,light:.23}},
 {id:'slime',module:'rm-water',options:{palette:['#263a35','#3e5743','#5c7551','#789369','#9cb187','#bfcead','#d9e1c8','#e8eadb'],light:.08}},
 {id:'map-warp',module:'native-feedback',options:{mode:'map-warp',palette:voidC,light:.1},meta:{size:[32,32],origin:[16,24],duration:.8}},
 {id:'void',module:'native-shadow',options:{palette:voidC,light:.12}},
 {id:'drain',module:'native-shadow',options:{palette:['#342631','#573747','#89546a','#ad7888','#c699aa','#d9bbc2','#e6d1d0','#f1e5d8'],light:.1}},
 {id:'cinema-hit',module:'cinema-hit',options:{palette:gold,light:.25}},
 ...[['fire',fire],['holy',holy],['wind',steel],['lightning',steel]].map(([mode,palette])=>({id:'cinema-'+mode,module:'cinema-impact',options:{mode,palette,light:.2}})),
 ...[['fire',fire],['holy',holy],['wind',steel],['stone',gold],['warp',voidC],['wake',steel],['dust',gold],['map-hit',gold],['map-heal',green]].map(([mode,palette])=>({id:mode,module:'native-feedback',options:{mode,palette,light:.15},...(mode.startsWith('map-')?{meta:{size:[32,32],origin:[16,24],duration:.8}}:mode==='wake'?{meta:{size:[48,24],origin:[36,12],duration:1,loop:true}}:{})}))
];
const manifest={upstream:'patch-gg/pixelfx',commit:'a84159688af3ca37a4be05a0d422b94451b2e24e',effects:{}};
for(const s of specs){const imported=await import(pathToFileURL(join(dir,s.module+'.js')));const meta={...imported.meta,...s.meta},mod={...imported,meta};const fx={id:'revenge/'+s.id,meta,mod};const rendered=renderFrames(fx,{fps:60,actor:false,bg:'none',options:{seed:13,...s.options}});const sheet=spriteSheet(fx,rendered,s.id);writeFileSync(join(out,s.id+'.png'),sheet.png);writeFileSync(join(out,s.id+'.json'),JSON.stringify(sheet.json,null,2));manifest.effects[s.id]={path:'assets/fx/'+s.id+'.png',...sheet.json.meta.pixelfx,module:s.module,options:s.options};console.log('Rendered',s.id,rendered.n,sheet.png.length);}
writeFileSync(join(out,'manifest.json'),JSON.stringify(manifest,null,2));writeFileSync(join(root,'fx-adaptations.json'),JSON.stringify(changes,null,2));

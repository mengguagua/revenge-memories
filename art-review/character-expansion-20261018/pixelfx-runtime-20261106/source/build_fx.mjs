import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {renderFrames,spriteSheet} from './pixelfx/tools/lib/fxlib.mjs';
const root=dirname(fileURLToPath(import.meta.url));
const target=join(root,'pixelfx/src/fx/preview');mkdirSync(target,{recursive:true});
const output=join(root,'../assets/fx');mkdirSync(output,{recursive:true});
const changes=[];
function adapt(path,name,pairs){
 let text=readFileSync(join(root,'pixelfx',path),'utf8');
 for(const [from,to] of pairs){if(!text.includes(from))throw Error(name+' missing replacement: '+from);text=text.replaceAll(from,to);}
 text='// Preview-only mobile-native adaptation. Source preserved in sibling categories.\n'+text;
 writeFileSync(join(target,name+'.js'),text);
 changes.push({name,upstream:path,changes:pairs});
}
adapt('src/fx/impacts/hit-spark.js','rm-hit',[
 ['size: [136, 80]','size: [72, 56]'],['origin: [44, 64]','origin: [28, 44]'],['height: 20','height: 16'],
 ['R.range(33, 37)','R.range(15, 18)'],['R.range(8, 10)','R.range(4, 6)'],['R.range(15, 18), w: 2.6','R.range(7, 9), w: 1.6'],['R.range(10, 12), w: 2.3','R.range(5, 7), w: 1.5'],['R.range(5, 7), w: 1','R.range(3, 4), w: 1'],['w: 2.2','w: 1.4'],
 ['38, C[4], 0.35','18, C[4], 0.25'],['22, C[5], 0.45','10, C[5], 0.25'],['26, C[3], 0.22','14, C[3], 0.12'],
 ['i < 9','i < 6'],['i < 6; i++) {\n    const a = A + R.range(-1.1','i < 3; i++) {\n    const a = A + R.range(-1.1'],
 ['R.range(170, 360)','R.range(65, 140)'],['R.range(70, 170)','R.range(35, 80)'],['R.range(30, 80)','R.range(15, 40)'],['v - 40','v - 20'],
 ['diamond(p, X, Y, 4','diamond(p, X, Y, 2'],['diamond(p, X, Y, 3','diamond(p, X, Y, 2'],
 ['22, C[4], 0.3','12, C[4], 0.2'],['Math.cos(A) * 26','Math.cos(A) * 14'],['Math.sin(A) * 26','Math.sin(A) * 14']
]);
adapt('src/fx/lightning/zap-hit.js','rm-core',[
 ['from "./_lib.js"','from "../lightning/_lib.js"'],['size: [144, 112]','size: [72, 64]'],['origin: [76, 56]','origin: [36, 32]'],
 ['for (let i = 0; i < 6; i++) grow','for (let i = 0; i < 4; i++) grow'],['R.range(18, 32)','R.range(6, 10)'],['depth < 2','depth < 1'],
 ['length: 16','length: 7'],['R.range(130, 250)','R.range(40, 85)'],['60, C[4], 0.7','18, C[4], 0.3'],['14, WHITE, 0.5','7, WHITE, 0.3'],
 ['if (t < 0.32) {','if (false) { // No incoming beam: this is a broken core, not another attack.'],
 ['R0 = 8 *','R0 = 4 *'],['Math.round(11 *','Math.round(5 *'],['20, C[4], 0.55','10, C[4], 0.22'],['40 * Math.max','18 * Math.max'],['0.45 * Math.exp','0.2 * Math.exp'],
 ['3 * (1 - a) + 1','1 * (1 - a) + 1'],['2 * (1 - a) + 0.5','1 * (1 - a) + 0.5']
]);
adapt('src/fx/water/splash.js','rm-water',[
 ['from "./_lib.js"','from "../water/_lib.js"'],['size: [176, 100]','size: [80, 64]'],['origin: [88, 78]','origin: [40, 58]'],['duration: 2.5','duration: 1.1'],['stone: true','stone: false'],
 ['HIT = 0.16','HIT = 0'],['FINGERS = 12','FINGERS = 6'],['JET = 0.3','JET = 100'],
 ['19 * ease.outCubic','11 * ease.outCubic'],['3 + 7.5 *','2 + 5 *'],['height(u) * 0.42','height(u) * 0.35'],
 ['52, C[5], 0.6','20, C[5], 0.22'],['16, WHITE, 0.5','8, WHITE, 0.18'],
 ['8, 56, 2.0','5, 22, 0.85'],['5, 38, 1.7','3, 16, 0.7'],['gap: 3.4','gap: 2'],
 ['i < 20','i < 8'],['R.range(50, 125)','R.range(20, 48)'],['R.range(160, 270)','R.range(75, 130)'],
 ['i < 9','i < 3'],['R.range(25, 70)','R.range(10, 24)'],['R.range(7, 11)','R.range(3, 5)'],['R.range(0.9, 1.5)','R.range(0.4, 0.65)'],
 ['R.range(25, 90)','R.range(10, 30)'],['R.range(30, 100)','R.range(18, 45)'],['R.range(0.7, 1.3)','R.range(0.3, 0.55)'],
 ['i < 5; i++) ps.spawn','i < 2; i++) ps.spawn'],['R.range(32, 88)','R.range(15, 35)'],['R.range(90, 190)','R.range(50, 95)'],
 ['i < 8; i++) {\n          const a','i < 4; i++) {\n          const a'],['R.range(15, 40)','R.range(10, 25)'],
 ['[[0, 0.95], [1, 1.2], [2, 1.5]]','[]'],['smooth(0.5, 2.0, u)','smooth(0.4, 0.9, u)'],['34, C[4], 0.2','16, C[4], 0.08'],['64, C[3], 0.16','26, C[3], 0.05']
]);
const specs=[
 {id:'hit',module:'rm-hit',fps:60,light:.35,palette:['#27303c','#575662','#857b78','#b4aa91','#ddcfaa','#ede3c8','#fff3dc']},
 {id:'cannon',module:'rm-hit',fps:60,light:.3,palette:['#34303b','#675750','#95836a','#bdab80','#dbcba4','#e8dfc3','#fff2d4']},
 {id:'core',module:'rm-core',fps:60,light:.4,palette:['#232b40','#3b4160','#5b5d7c','#7c7f97','#a5a6b5','#c3c9ce','#e0e2da','#f5f2e5']},
 {id:'water',module:'rm-water',fps:60,light:.12,palette:['#1f3642','#2e4d59','#466a76','#638b95','#88abb0','#b0cace','#d1dfdf','#e9eeee']}
];
const manifest={upstream:'patch-gg/pixelfx',commit:'a84159688af3ca37a4be05a0d422b94451b2e24e',effects:{}};
for(const s of specs){
 const mod=await import(pathToFileURL(join(target,s.module+'.js')));
 const fx={id:'preview/'+s.id,meta:mod.meta,mod};
 const r=renderFrames(fx,{fps:s.fps,actor:false,bg:'none',options:{palette:s.palette,light:s.light,seed:4}});
 const sheet=spriteSheet(fx,r,s.id);writeFileSync(join(output,s.id+'.png'),sheet.png);
 writeFileSync(join(output,s.id+'.json'),JSON.stringify(sheet.json,null,2));
 manifest.effects[s.id]={path:'assets/fx/'+s.id+'.png',...sheet.json.meta.pixelfx,options:s};
}
writeFileSync(join(root,'fx-adaptations.json'),JSON.stringify(changes,null,2));
writeFileSync(join(output,'manifest.json'),JSON.stringify(manifest,null,2));
console.log(JSON.stringify(manifest.effects,null,2));

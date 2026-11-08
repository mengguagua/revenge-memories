import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {dirname,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {renderFrames,spriteSheet} from '../pixelfx/tools/lib/fxlib.mjs';
const root=dirname(dirname(fileURLToPath(import.meta.url))),folder=join(root,'pixelfx/src/fx/preview'),out=join(root,'../assets/fx');
const adaptations=[];
function adapt(from,name,pairs){let s=readFileSync(join(root,'pixelfx/src/fx',from),'utf8');for(const [a,b] of pairs){if(!s.includes(a))throw Error('Missing '+name+' '+a);s=s.replaceAll(a,b);}writeFileSync(join(folder,name+'.js'),'// Native-size game preview adaptation; upstream source retained.\n'+s);adaptations.push({from,name,changes:pairs});}
adapt('projectiles/arrow.js','rm-arrow',[
 ['from "./_lib.js"','from "../projectiles/_lib.js"'],['size: [112, 32]','size: [72, 24]'],['origin: [92, 16]','origin: [60, 12]'],
 ['["..LL....", "..sLLL..", "bbsSSSSW", "..dDDD..", "..DD...."]','["..L..", "bbSSW", "..D.."]'],
 ['["AAa.........", ".aAAa.......", "..aaAAa.....", "nkkkkkkkkkkk", "..cCCc......", ".cCCc.......", "CCc........."]','["AAa.....", ".aAAa...", "nkkkkkkk", ".cCCc...", "CCc....."]'],
 ['[".AAa........", "..aAAa......", "..aaAAAa....", "nkkkkkkkkkkk", "..cCCCc.....", "..cCCc......", ".CCc........"]','[".AAa....", "..aAAa..", "nkkkkkkk", "..cCCc..", ".CCc...."]'],
 ['["AAAa........", "aAAa........", ".aaAAa......", "nkkkkkkkkkkk", "..ccCc......", "cCCc........", "CCc........."]','["AAAa....", "aAAa....", "nkkkkkkk", "cCCc....", "CCc....."]'],
 ['left = -meta.origin[0] + 2, LEN = 36','left = -Math.min(meta.origin[0]-2,24+t*100), LEN = 20'],
 ['beat(t, D, 9','beat(t, D, 5'],['r.range(160, 240)','r.range(65, 110)'],['r.range(8, 16)','r.range(5, 9)'],['r.range(3, 5)','r.range(2, 3)'],['beat(t, D, 6','beat(t, D, 3'],['r.range(100, 150)','r.range(55, 90)'],['rr = 1.2 + k * 1.5','rr = .7 + k * .6'],
 ['p.line(-LEN + 11, 0, -7, 0','p.line(-LEN + 7, 0, -3, 0'],['-LEN, -3);','-LEN, -2);'],['}, -7, -2);','}, -4, -1);'],['1 + Math.round(2 * Math.sin','1 + Math.round(1 * Math.sin']
]);
adapt('melee/sword-slash.js','rm-slash',[
 ['size: [136, 104]','size: [96, 84]'],['origin: [44, 92]','origin: [40, 70]'],['radius: 42','radius: 22'],['actor: 2','actor: 0'],
 ['W: 12, t0','W: 6, t0'],['ground: () => 0','ground: () => -4'],['i < 10','i < 5'],['i < 16','i < 7'],['Rg.range(150, 400)','Rg.range(65, 160)'],['Rg.range(30, 100)','Rg.range(18, 42)'],['9 * ease.outBack','4 * ease.outBack'],['p.glow(x, y, 40, C[3], 0.5','p.glow(x, y, 18, C[3], 0.22']
]);
const options={
 arrow:{palette:['#52656c','#809398','#c2d1c8','#e0e6da'],wood:['#352f29','#65523c','#967f59','#c2ae83'],steel:['#32404a','#667b81','#a3b2b5','#d5dfda'],wind:'#7899a5',light:.15},
 slash:{palette:['#243840','#405663','#63818d','#91b2b9','#bdd0ce','#dce7df','#f1f0e2'],sparks:['#e3dbb8','#c7b998','#8b8f8d','#526a74'],radius:22,light:.28}
};
const manifest={effects:{}};
for(const id of ['arrow','slash']){const mod=await import(pathToFileURL(join(folder,'rm-'+id+'.js')));const fx={id:'preview/'+id,meta:mod.meta,mod};const r=renderFrames(fx,{fps:60,actor:false,bg:'none',options:options[id]});const sheet=spriteSheet(fx,r,id);writeFileSync(join(out,id+'.png'),sheet.png);writeFileSync(join(out,id+'.json'),JSON.stringify(sheet.json,null,2));manifest.effects[id]={path:'assets/fx/'+id+'.png',...sheet.json.meta.pixelfx,options:options[id]};}
writeFileSync(join(root,'weapons-20261107/fx-manifest.json'),JSON.stringify(manifest,null,2));writeFileSync(join(root,'weapons-20261107/fx-adaptations.json'),JSON.stringify(adaptations,null,2));console.log(JSON.stringify(manifest));

const fs=require('fs'),path=require('path'),{execFileSync}=require('child_process');
const root=path.resolve(__dirname,'..'),repo=path.resolve(root,'../..');
const data=JSON.parse(fs.readFileSync(path.join(repo,'actual/data/reviewed_animations.json')));
const targets=[];
for(const [id,name,hp,damage] of [['4_enemy','重甲骑士',52,28],['15_enemy','咒术师',37,24],['21_enemy','羽冠神兽',96,46]]){
 const d=data.battle[id],n=d.sequences.idle[0],w=d.frame_size[0],h=d.frame_size[1],col=d.columns;
 const src=path.join(repo,'actual',d.path.replace('res://','')),dest=path.join(root,'assets','target-'+id+'.png');
 execFileSync('/opt/homebrew/bin/magick',[src,'-crop',`${w}x${h}+${n%col*w}+${Math.floor(n/col)*h}`,'+repage',...(d.idle_flip?['-flop']:[]),'-trim','+repage',dest]);
 targets.push({id,name,path:'assets/target-'+id+'.png',hp,maxHp:hp,damage,source:src,source_frame:n,static_only:true});
}
fs.writeFileSync(path.join(root,'targets.js'),'window.CinemaTargets='+JSON.stringify(targets)+';\n');
fs.writeFileSync(path.join(root,'source/target-snapshots.json'),JSON.stringify({note:'Dynamic target examples only, isolated current-game idle snapshots. No fixed enemy is part of the cinematic artwork. Each uses one static image, zero enemy pose animation.',targets},null,2));
console.log('3 static dynamic-target examples extracted.');

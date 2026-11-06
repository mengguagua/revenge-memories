# 原创配乐替换方案（2026-10-24）

状态：本页记录已采用的制作方案与映射。28首运行资源现已生成、接入；实际时长与客观检查见 `tracks.md`，实现与验证见 `integration.md`。全部按无歌词、无人声纯音乐要求使用本地模型生成；感知试听尚未确认。

## 现有资源与主要问题

- 根目录与 actual 均为 35 个唯一音乐文件：27 个循环曲、3 个长主题、5 个短提示；另 42 个音效保持独立。逐文件时长与匹配结果见 `source-inventory.json`。
- 世界地图按章节有 5 首；据点目前全播 `village`；战场按路线/回合/最后一敌选曲，交锋再切曲。原有播放器只保留jingle打断前的位置，交锋结束会从头播放地图曲。
- 新终战 J54 的 id 为 534，而旧音乐调用仍检查 62，因此必须改用本作实际关卡映射。
- 本作以 28 首原创资源替换：24 首循环主题/场景曲、4 首短提示。所有35个原音乐请求和10个别名有显式原创兜底，不以旧曲掩盖漏绑定。

## 曲目表

BPM 为原创目标值，非原作测量。时长为目标，模型未必精确遵守；必须按生成结果确认完整乐句。

| ID | 中文名 | 场景 | BPM | 目标秒 | 循环 |
|---|---|---|---:|---:|---|
| rm_title | 把名字留给明天 | 标题页与旅程选择 | 96 | 84 | 是 |
| rm_prologue | 庆典背后的黑昼 | P00序章；H27回到广场；H30接回现在 | 88 | 72 | 是 |
| rm_ending | 完整的天空 | J54胜利后的结局与十八人后日谈 | 82 | 96 | 是 |
| rm_world_ch1 | 雪下的道路 | 第一章世界地图 | 100 | 60 | 是 |
| rm_world_ch2 | 风灯与残图 | 第二章世界地图 | 108 | 64 | 是 |
| rm_world_ch3 | 两岸未寄的信 | 第三章世界地图 | 104 | 64 | 是 |
| rm_world_ch4 | 留住两岸的灯 | 第四章世界地图 | 112 | 64 | 是 |
| rm_world_ch5 | 登天路上的人 | 第五章世界地图 | 116 | 72 | 是 |
| rm_battle_snow | 先把他们送出去 | M11/M12/M13/S11/S12 | 124 | 64 | 是 |
| rm_battle_tide | 护船穿过暗潮 | F21/F22/F23/S21/S22 | 132 | 64 | 是 |
| rm_battle_revenge | 旧军旗下的答复 | M14/M15/F25 | 138 | 68 | 是 |
| rm_battle_refuge | 黑昼里的退路 | F24/F26/M31/F31/M41/F41 | 128 | 64 | 是 |
| rm_battle_two_fronts | 把道路接起来 | M32/M33/F32/F33/S31/S32 | 130 | 64 | 是 |
| rm_battle_sun_tower | 先保护，再停下 | M42/M43/M44 | 136 | 68 | 是 |
| rm_battle_circuit | 暗水下的微光 | F42/F43/F44/S41/S42 | 126 | 68 | 是 |
| rm_battle_ascent | 不再留下任何人 | M51/M52/F51/F52/J53/S51 | 142 | 72 | 是 |
| rm_battle_final | 天空不属于王座 | J54全阶段；攻击/法术/支援保持连续 | 146 | 96 | 是 |
| rm_hub_hearth | 雪屋里还有灯 | H02/H03/H05/H07/H08/H32/H33/H36/H41/H42/H49 | 84 | 56 | 是 |
| rm_hub_harbor | 等船的人 | H21/H22/H24/H26/H34/H37/H47 | 92 | 56 | 是 |
| rm_hub_care | 给后来的人留一盏灯 | H04/H09/H23/H25/H45/H50/H51；救治界面 | 72 | 56 | 是 |
| rm_story_memory | 名字不能被删去 | H01/D11/D13/D22/D41；死者与责任的对白 | 68 | 56 | 是 |
| rm_story_reunion | 重新认识你 | H31/H10/H55；D32/D33；关系对话 | 78 | 60 | 是 |
| rm_story_records | 灯仍然亮着 | H35/H43/H46/H48/H53/H56；D42 | 88 | 60 | 是 |
| rm_story_divine | 七羽冠的阴影 | H06/H44/H52/H54；D31/D52；神令与最后谈话 | 82 | 60 | 是 |
| rm_jingle_victory | 路已经打开 | 关卡胜利且结算首次完成；不用于每次击杀 | 120 | 6 | 否 |
| rm_jingle_growth | 向前一步 | 升级81；职业进阶可用奖赏cue | 120 | 4 | 否 |
| rm_jingle_award | 约定的交接 | 兵装/饰品交付、招募或进阶的通用确认；82/84/B6兼容 | 100 | 5 | 否 |
| rm_jingle_wounded | 请带他回去 | 正式同伴濒死90；战败提示；不用死亡葬礼语义 | 72 | 5 | 否 |

## 最小接入规则

1. 增加原创音乐清单，保留音效清单。音乐路径统一解为 canonical track_id，同曲请求不重启。
2. 从实际关卡 code/id、hub id、章节选择曲；J54使用终战曲；40关映射见下表。
3. 常规交锋、支援、敌我回合、最后一敌仍播放本关同一曲。新场景采用约0.6秒淡化过渡，菜单与状态页不换曲。
4. 升级、奖赏、濒死短提示使用独立jingle播放器，结束恢复原位置；战败停止后不恢复战场曲。胜利短句仅结算首次完成时播放。
5. 仅明确的主要剧情节点覆盖背景曲；普通对白延续所在地曲。现有callback可直接接，其他剧情可先靠据点曲覆盖，避免改动大量对白数据。
6. 生成后确认循环接头、无人声、响度与削波；音频证据和少量受控播放即可，不重跑40关、不增加重复截图。

## 40关映射

| 关卡 | 名称 | 曲目 |
|---|---|---|
| M11 (101) | 流民林路 | rm_battle_snow |
| M12 (102) | 丘堡粮站 | rm_battle_snow |
| M13 (103) | 南岗押送所 | rm_battle_snow |
| M14 (104) | 旧塔外营 | rm_battle_revenge |
| M15 (105) | 海峡旧塔堡 | rm_battle_revenge |
| S11 (111) | 旧矿道救援 | rm_battle_snow |
| S12 (112) | 林村诊所道路 | rm_battle_snow |
| F21 (201) | 海上拦截 | rm_battle_tide |
| F22 (202) | 押送舰救援 | rm_battle_tide |
| F23 (203) | 礁岛登岸 | rm_battle_tide |
| F24 (204) | 海灯岛防卫 | rm_battle_refuge |
| F25 (205) | 潮狩军港 | rm_battle_revenge |
| F26 (206) | 断航古道 | rm_battle_refuge |
| S21 (211) | 漂泊渔船 | rm_battle_tide |
| S22 (212) | 碎石海洞 | rm_battle_tide |
| M31 (301) | 西街撤离 | rm_battle_refuge |
| M32 (302) | 军需大道截运 | rm_battle_two_fronts |
| M33 (303) | 沿海石堡 | rm_battle_two_fronts |
| F31 (304) | 码头脱围 | rm_battle_refuge |
| F32 (305) | 盐路解围 | rm_battle_two_fronts |
| F33 (306) | 提炼院后庭 | rm_battle_two_fronts |
| S31 (311) | 山村地牢 | rm_battle_two_fronts |
| S32 (312) | 盐原营地 | rm_battle_two_fronts |
| M41 (401) | 雪峡撤离战 | rm_battle_refuge |
| M42 (402) | 铁骑封锁线 | rm_battle_sun_tower |
| M43 (403) | 北境日塔 | rm_battle_sun_tower |
| M44 (404) | 王都城门 | rm_battle_sun_tower |
| F41 (405) | 沙城守井战 | rm_battle_refuge |
| F42 (406) | 盐原观测台 | rm_battle_circuit |
| F43 (407) | 亡潮沼泽 | rm_battle_circuit |
| F44 (408) | 沉没祭所 | rm_battle_circuit |
| S41 (411) | 黑钟村名册 | rm_battle_circuit |
| S42 (412) | 沼泽孤岛 | rm_battle_circuit |
| M51 (501) | 王都内廷 | rm_battle_ascent |
| M52 (502) | 登天桥 | rm_battle_ascent |
| F51 (503) | 祭所底层 | rm_battle_ascent |
| F52 (504) | 日宫下层 | rm_battle_ascent |
| S51 (511) | 神宫旧书库 | rm_battle_ascent |
| J53 (533) | 神宫前庭 | rm_battle_ascent |
| J54 (534) | 太阳神乌库布·卡基 | rm_battle_final |

## 旧请求兜底表

上下文优先于此表：例如交锋80/86/A2在战场内仍保留本关曲，不能按兜底表切到村庄或早期战场。这里只保证旧调用未迁移处不会漏回原录音。

| 请求 | 原文件 | 新曲 |
|---|---|---|
| 70 | music_70.ogg | rm_battle_snow |
| 71 | title.ogg | rm_title |
| 72 | opening.ogg | rm_prologue |
| 73 | opening_alternate.ogg | rm_ending |
| 76 | music_76.ogg | rm_battle_revenge |
| 77 | music_77.ogg | rm_battle_tide |
| 80 | music_80.ogg | rm_battle_snow |
| 81 | levelup.ogg | rm_jingle_growth |
| 82 | music_82.ogg | rm_jingle_award |
| 83 | music_83.ogg | rm_world_ch5 |
| 84 | music_84.ogg | rm_jingle_award |
| 85 | music_85.ogg | rm_story_divine |
| 86 | combat.ogg | rm_battle_snow |
| 87 | music_87.ogg | rm_hub_care |
| 90 | unit_death.ogg | rm_jingle_wounded |
| 91 | music_91.ogg | rm_story_memory |
| 93 | music_93.ogg | rm_hub_hearth |
| 94 | music_94.ogg | rm_world_ch3 |
| 95 | music_95.ogg | rm_story_records |
| 96 | music_96.ogg | rm_world_ch4 |
| A0 | world_map.ogg | rm_world_ch1 |
| A1 | battle.ogg | rm_battle_snow |
| A2 | music_a2.ogg | rm_hub_care |
| A3 | music_a3.ogg | rm_battle_snow |
| A4 | enemy_phase.ogg | rm_battle_tide |
| A5 | music_a5.ogg | rm_battle_revenge |
| A6 | village.ogg | rm_hub_hearth |
| A7 | music_a7.ogg | rm_battle_tide |
| B0 | music_b0.ogg | rm_battle_final |
| B2 | music_b2.ogg | rm_story_reunion |
| B3 | music_b3.ogg | rm_story_records |
| B4 | music_b4.ogg | rm_battle_final |
| B5 | music_b5.ogg | rm_battle_final |
| B6 | music_b6.ogg | rm_jingle_award |
| B7 | music_b7.ogg | rm_world_ch2 |

## 制作与来源边界

源文件的时长、循环信息来自本地既有清单，并以ffprobe复核；所有actual副本与根目录音频SHA-256一致。未报告原作BPM实测或声称完成源音频听感验收。新曲采用原作所代表的复古音色、短句与清晰声部关系作为风格约束，旋律与录音从零生成。

完整英文prompt、40关/42个据点映射、10个别名映射、结构与音频验证要求见 `plan.json`。

# 蚀躯／断路匪对照页定向集成

范围仅为敌方职业11和14的美术对照；不修改actual游戏、共享页面默认角色或其他职业映射。制作源稿保存在`../enemy-revenant-brigand-v1-20261023/`。

## 输入接口

两类分别放在`professions/class-11-enemy/`与`professions/class-14-enemy/`，各提供：

- `maps/frame_mapping.json`：`class_id`、`actor_id: class-11-enemy/class-14-enemy`、`source_side: enemy`、明确的`revision`与`modified_by`。场景`scenarios`包含原生战棋行走和待机，各有源图集、原帧尺寸／锚点、四倍输出尺寸、完整逐帧路径、方向及节奏。战棋行走的`source_audit.status`为`verified_native_tactical`；来源证据须真实存在。
- `battle/frame_mapping.json`：`original_class_id`、`character_id: class-11-enemy/class-14-enemy`、`source_side: enemy`、`variant_keys`、`output_frame_size`及完整`frame_mapping`。11为`original_class_11_enemy_normal`（472ticks/contact274）；14为`original_class_14_enemy_normal`（181ticks/contact84）。原战斗图集／位移／节奏取冻结enemy-motion，不能把友方同编号动作混入。
- 角色`manifest.json`记录生成、切图、帧对应、来源及人工视觉审核边界。构建器本身通过frame_mapping发现角色，manifest不是唯一入口。

地图原生参考：待机3帧顺序`[0,1,2,1]`，时长`[14,8,14,8]`；行走8槽依次上01／右23／下45／左67，每姿势16ticks。四向不靠误用友方帧代替。

## 动作计数与来源边界

每类3个场景profile、14个页面条目：地图待机循环1、四向步行4、四向停止姿势4、原生普通攻击程序1、系统战斗待机／未命中停留／受击／退场4。两类共6个profile、28个可选条目；静止姿势和系统反应不能包装成28套独立新动作。未命中项只是沿用待机反馈，不是新闪避姿势。

11号仅使用`original_class_11_enemy_normal`，14号仅使用`original_class_14_enemy_normal`，不带入友方女魔剑士的术法、雷剑或乡勇的友方程序。蚀躯源frame49为完全透明潜伏区间；校验仅在baseline明确声明且冻结原图对应帧也全透明时允许此唯一空帧。83／98采用33的来源登记偏移，47含48身体与原生爪弧，不新增出牌或命中次数。

## 使用

从仓库根目录运行：

```sh
python3 art-review/character-expansion-20261018/tools/integrate_enemy_11_14_review.py --inspect
python3 art-review/character-expansion-20261018/tools/integrate_enemy_11_14_review.py
python3 art-review/character-expansion-20261018/tools/integrate_enemy_11_14_review.py --export all
python3 art-review/character-expansion-20261018/tools/integrate_enemy_11_14_review.py --merge
```

默认命令仅在此目录写局部数据和检查结果；导出仅写两类专属ID的`demos/stills`与`demos/videos`，深浅背景静帧另放此目录`previews/`，不覆盖全局export-report。每个视频核对解码帧数和时长。`--merge`须明确提供，读取最新共享数据后只替换本两类profiles/actions，更新必要统计，保留其他角色及未知字段；`index.html`及其默认角色不作写入。

不能直接运行共享`build_gallery.py`、`export_gallery.py`或`validate_gallery.py`主程序：它们会全量重建共享数据。此helper解析当前builder，在内存中只允许4个目标mapping，并移除三个全局写出点；若builder结构改变则拒绝继续，避免假装仍安全。

## 并行编辑边界

合并前检查当前JS与JSON一致，构造结果时保留所有非目标记录；写出前再次比对共享文件哈希，原子替换单文件，再核对写后内容和页面默认。其他任务不会自动遵守本helper锁，因此这不是跨进程全局事务：发现并行修改会报错，需重新读取最新数据，不自动恢复旧文件覆盖其他任务。尽量安排最后的短暂merge与其他共享构建错开；导出阶段可以并行制作。

最终通过现有页面查询参数打开，不改全局默认：

- [蚀躯普通攻击](../index.html?action=professions-class-11-enemy-battle--original_class_11_enemy_normal#motion-player)
- [断路匪普通攻击](../index.html?action=professions-class-14-enemy-battle--original_class_14_enemy_normal#motion-player)

上述动作链接须在目标映射齐备并merge后才可用。几何、完整性、视频检查不能代替实际深浅背景、逐动作及移动端尺寸的视觉验收；不会把本次对照页制作误写为游戏运行接入。

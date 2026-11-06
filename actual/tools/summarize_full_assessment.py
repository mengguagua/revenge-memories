#!/usr/bin/env python3
"""Follow real checkpoint ancestry; never combine unrelated deployment samples."""
import argparse
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/full-assessment-20261025"


def read(path):
    return json.loads(path.read_text())


def summarize(report_path):
    chain = []
    seen = set()
    path = report_path.resolve()
    while path not in seen:
        seen.add(path)
        report = read(path)
        chain.append((path, report))
        source = report.get("source", "")
        if not source.startswith("res://"):
            break
        source_path = ROOT / source.removeprefix("res://")
        expected = report.get("source_sha256")
        if expected and hashlib.sha256(source_path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Source checkpoint changed: {source_path}")
        path = source_path.parent / "report.json"
        if not path.exists():
            raise ValueError(f"Missing predecessor report: {path}")
    chain.reverse()
    victories = {}
    attempts = []
    actions = []
    for path, report in chain:
        actions.extend(report.get("operations", []))
        for battle in report.get("battles", []):
            item = {key: battle.get(key) for key in ("code", "stage", "outcome", "final_turn", "new_casualties")}
            item["report"] = str(path.relative_to(ROOT))
            item["entrant_count"] = len([u for u in battle.get("initial_players", []) if not u.get("neutral", False) and not u.get("temporary", False)])
            item["initial_players"] = battle.get("initial_players", [])
            item["initial_enemies"] = battle.get("initial_enemies", [])
            attempts.append(item)
            if item["outcome"] == "victory":
                victories[item["code"]] = item
    expected_codes = {p.stem for p in (ROOT / "data/stages").glob("*.json")}
    final = chain[-1][1]
    complete = (set(victories) == expected_codes and final.get("campaign_complete", False)
                and final.get("ending_done", False) and final.get("passed", False))
    verified_actions = []
    for action in actions:
        if action.get("kind") not in ("ordinary equipment upgrade", "ordinary earned promotion", "ordinary injury treatment"):
            continue
        item = dict(action)
        if item.get("kind") == "ordinary earned promotion" and not item.get("verified", False):
            item["kind"] = ("promotion menu selection blocked by chapter4 routing defect"
                            if int(item.get("stage", 0)) >= 400 else "promotion menu selection; inspect recorded class")
            item["verified"] = False
        verified_actions.append(item)
    result = {
        "complete": complete,
        "scope": "One new-game ancestry, ordinary input and recorded retries; no unrelated historical deployment checkpoints combined. Headless accelerated presentation, not human or iPhone testing.",
        "source_reports": [str(p.relative_to(ROOT)) for p, _ in chain],
        "root_source": chain[0][1].get("source"),
        "victories": list(victories.values()),
        "attempts": attempts,
        "missing_codes": sorted(expected_codes - set(victories)),
        "retry_actions": [a for a in actions if a.get("kind") == "ordinary retry after recorded defeat"],
        "equipment_and_growth_actions": verified_actions,
        "total_inputs": sum(report.get("inputs", 0) for _, report in chain),
        "harness_notes": ["Old driver promotion labels recorded clicks without checking state. Chapter4 repeated clicks had no effect due to the now-fixed production routing defect. Summary labels them as blocked attempts; original snapshots and class values are authoritative. Later driver asserts the actual class change."],
        "final_roster": final.get("final_roster", {}),
        "final_convoy": final.get("convoy", {}),
        "campaign_complete": final.get("campaign_complete", False),
        "ending_done": final.get("ending_done", False),
    }
    return result


def render_report(result):
    """A small local review page; source evidence stays linked and inspectable."""
    esc = html.escape
    characters = read(ROOT / "data/campaign.json")["characters"]
    names = {key: value.get("name_zh", key) for key, value in characters.items()}
    classes = read(ROOT / "data/legacy/campaign.json")["classes"]
    for key, value in read(ROOT / "data/class_names.json").items():
        classes[key].update(value)
    rows = []
    for entry in result["victories"]:
        stage = read(ROOT / f"data/stages/{entry['code']}.json")
        casualties = "、".join(names.get(key, key) for key in (entry["new_casualties"] or [])) or "无"
        href = Path(entry["report"]).relative_to("reports/full-assessment-20261025").as_posix()
        rows.append(f'<tr><td>{esc(entry["code"])}</td><td>{esc(stage["name_zh"])}</td><td>{entry["final_turn"]}</td><td>{esc(casualties)}</td><td><a href="{href}">连续记录</a></td></tr>')
    roster = []
    for key, unit in result["final_roster"].items():
        if key not in names:
            continue
        state = "濒死，接受照护" if unit.get("dying", False) else "可出阵"
        profession = {"dawn_warrior": "破晓勇士", "light_guide": "引光剑使"}.get(unit.get("hero_profession"), classes[str(int(unit["class_id"]))]["name_zh"])
        roster.append(f'<tr><td>{esc(names[key])}</td><td>{esc(profession)}</td><td>{int(unit["level"])}</td><td>{int(unit["max_hp"])}</td><td>{esc(state)}</td><td>{int(unit.get("treatment_count", 0))}</td></tr>')
    state = "已完成" if result["complete"] else "验证进行中"
    document = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>全流程评估与修复 · 2026-10-25</title><style>
body{{margin:0;background:#131b22;color:#e8e6de;font:16px/1.75 system-ui,sans-serif}}main{{max-width:1040px;margin:auto;padding:36px 24px}}h1,h2{{line-height:1.35;color:#f0d49b}}a{{color:#b5d3ed}}a:focus-visible{{outline:none;box-shadow:0 0 0 5px #35516a;border-radius:5px}}section{{margin:28px 0;padding:24px;background:#1d2832;border-radius:14px}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #34424e}}.scroll{{overflow:auto}}.muted{{color:#b6c0c8}}strong{{color:#f0d49b}}
</style><main><h1>全流程评估与修复</h1><p>2026-10-25 · {state} · 当前本地源码 · 未安装或更新 iPhone</p>
<section><h2>连续战役与难度</h2><p><strong>{len(result['victories'])}/40 关</strong>来自同一新档的存档链，保留成长、战损、装备、救治和正常重试，包含双队切换、四次跨章、合流及结局。没有把历史部署队伍拼成这条通关记录。</p>
<p>目标为需要较熟练战棋玩家决策的适中难度。保留敌军整体属性、经验与限时目标，修复实际影响成长的第四章转职入口，解决自动护送踏入可达攻击区及守卫被远程白打的问题；护途盾双防从13收紧至5，保留每阶段恢复5与唯一救援来源。</p>
<p>主链是带伤持续推进的压力样本。早期驾驶曾遗漏治疗、部分转职和装备操作，失败及原伤情全部保留；不能用这些遗漏论证角色应全面增强。另一个独立新档第一章对照7/7通关、0重试、71回合，仍有战损，两条队伍没有拼接。</p>
<p>护途盾同源对照在双防+5时，单前锋策略仍能19回合获胜，最低26/34生命，最大一次命中6；其他成员有被动反击和战损。结论是去除原先命中恒1伤的保障、保留强奖励，不能声称每种策略都必须治疗或已经证明真人难度。</p>
<p><a href="campaign-summary.json">完整存档链与成长数据</a> · <a href="balance/README.md">难度判断与独立对照</a> · <a href="ai/README.md">AI、固定单位与护途盾证据</a></p></section>
<section><h2>存档、剧情与成长修复</h2><p>重试清零本关击杀统计；保存前校验可恢复状态，主档与恢复副本原子替换，损坏原件保留并提供明确恢复入口。独立进程中断、旧档迁移、奖励及跨章状态分别验证。</p>
<p>修正M15、F31、F32、M33、S41的目标摘要；M33投降范围与实际对象一致；S32、S42战后文案按真实生死分支；手机提示使用菜单名称。第四章训练菜单的转职指令转发已修复，并独立验证实际职业、成长和存档变化。已完成的主线记录没有事后补改属性。</p>
<p><a href="save/README.md">存档专项</a> · <a href="save/index.html">恢复入口画面</a> · <a href="balance/promotion-route/README.md">第四章转职实际修复</a> · <a href="story/late-story-README.md">剧情专项</a> · <a href="story/late-story-review.html">目标与分支画面</a></p></section>
<section><h2>性能与视觉无损压缩</h2><p>相同本机后台场景，Godot静态内存<strong>764.54 → 168.49 MiB（−77.96%）</strong>，整屏RGBA相同；动画按需加载，2360个动作、502,873帧与原库相等。七个图集的旧纹理实际释放，静止手机外侧轨道90帧不再重复重绘。</p>
<p>3140张PNG检查、470张无损压缩，共减少<strong>6,175,926字节</strong>，没有改像素尺寸、RGBA或透明边缘。药车提示重复读取由约28ms降至0.060–0.082ms。PNG文件体积减少不等于同等比例减少GPU内存或发热。</p>
<p><a href="performance/README.md">环境、测量与局限</a> · <a href="performance/png-compression.json">逐图尺寸与字节清单</a> · <a href="performance/package-checks.json">独立PCK资源检查</a></p></section>
<section><h2>40关结果</h2><div class="scroll"><table><thead><tr><th>关卡</th><th>名称</th><th>完成回合</th><th>本关新增濒死</th><th>证据</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
<section><h2>最终成长与伤情</h2><p class="muted">职业采用友方实际名称，主角显示专属进阶身份；普通转职会重置显示等级，不能只比较等级高低。第四章转职入口修复没有事后修改这份历史队伍。</p><div class="scroll"><table><thead><tr><th>成员</th><th>职业</th><th>等级</th><th>生命上限</th><th>状态</th><th>救治次数</th></tr></thead><tbody>{''.join(roster)}</tbody></table></div></section>
<p class="muted">验证采用本机正常控制器输入与加速演出、独立规则夹具和不激活后台渲染。不是真人新手评测，也没有iPhone帧时间、温度或能耗采样；未自动更新设备。本页的“已完成”要求同一存档链40关胜利且结局标记已完成。</p></main></html>'''
    (OUT / "index.html").write_text(document)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    result = summarize(args.report)
    (OUT / "campaign-summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    if result["complete"]:
        render_report(result)
    print(json.dumps({"complete": result["complete"], "victories": len(result["victories"]),
                      "attempts": len(result["attempts"]), "missing": result["missing_codes"]}, ensure_ascii=False))

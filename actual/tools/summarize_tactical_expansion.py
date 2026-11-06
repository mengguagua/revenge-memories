#!/usr/bin/env python3
"""Summarize recorded checks and controller play; never reinterpret failures."""
import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/tactical-expansion-20261025"


def read(name):
    return json.loads((OUT / name).read_text())


def main():
    checks = []
    for title, file in [
        ("掩护规则与存档", "cover-checks.json"),
        ("击退与供给", "knockback-checks.json"),
        ("特殊AI、障碍与异常存档", "battlefield-checks.json"),
        ("16种补练布局与状态", "training/checks.json"),
        ("既有存档可靠性回归", "save-regression/checks.json"),
        ("取消、说明与读档边界", "final-review-probes.json"),
        ("后台手机布局", "visual/checks.json"),
    ]:
        data = read(file)
        count = data.get("checks", [])
        errors = data.get("errors", data.get("failures", data.get("driver_failures", [])))
        checks.append(dict(title=title, file=file, count=len(count) if isinstance(count, list) else count,
                           passed=data.get("passed", not errors), errors=errors))
    plays = []
    for round_no in (1, 2):
        path = f"knockback-play/round{round_no}/report.json"
        for record in read(path)["records"]:
            plays.append(dict(code=record["code"], round=round_no, outcome=record["outcome"],
                              turn=record["final_turn"], inputs=record["key_inputs"], file=path))
        for code in ("M42", "J54"):
            path = f"play/{code}-round{round_no}/report.json"
            data = read(path)
            record = data["battles"][-1]
            plays.append(dict(code=code, round=round_no, outcome=record["outcome"],
                              turn=record["final_turn"], inputs=data["inputs"], file=path))
        path = f"training/play-round{round_no}.json"
        for record in read(path)["battles"]:
            plays.append(dict(code=record["code"], round=round_no, outcome=record["outcome"],
                              turn=record["final_turn"], inputs=record["inputs"], file=path))
    attempts = read("rescue-play/attempt-summary.json")["attempts"]
    fingerprints = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in [*ROOT.joinpath("core").glob("*.gd"), ROOT / "data/knockback_equipment.json",
                              ROOT / "data/training_encounters.json", *[ROOT / f"data/stages/{c}.json" for c in ("F22", "M42", "J54")]]}
    summary = {"checks": checks, "plays": plays, "F22_attempts": attempts, "code_sha256": fingerprints,
               "scope": "Two rounds of sampled normal-input engine play from historical genuine checkpoints, with separate controlled rules and background graphics checks. Not a continuous new-game campaign, human play or iPhone device test.",
               "all_sampled_battles_won": False, "phone_updated": False}
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    e = html.escape
    table = "".join(f'<tr><td>{e(r["code"])}</td><td>{r["round"]}</td><td>{e(r["outcome"])}</td><td>{r["turn"]}</td><td>{r["inputs"]}</td><td><a href="{r["file"]}">原始记录</a></td></tr>' for r in plays)
    f22 = "".join(f'<tr><td>{e(r["attempt"])}</td><td>{e(r["outcome"])}</td><td>{r["turn"]}</td><td>{r["inputs"]}</td><td>{e("、".join(r["new_dying"]) or "无")}</td></tr>' for r in attempts)
    checked = "".join(f'<tr><td><a href="{r["file"]}">{e(r["title"])}</a></td><td>{r["count"]}</td><td>{"通过" if r["passed"] else "未通过"}</td></tr>' for r in checks)
    gallery = "".join(f'<figure><a href="visual/{e(p.name)}"><img loading="lazy" src="visual/{e(p.name)}" alt="{e(p.stem)}"></a><figcaption>{e(p.stem)}</figcaption></figure>' for p in sorted((OUT / "visual").glob("*.png")))
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>战术机制扩展 · 2026-10-25</title>
<style>body{margin:0;background:#101922;color:#e9edf1;font:16px/1.75 system-ui,sans-serif}main{max-width:1120px;margin:auto;padding:32px 24px}h1{font-size:30px}h2{margin-top:36px}a{color:#8cdbcb}table{width:100%;border-collapse:collapse;background:#18242f}td,th{text-align:left;padding:10px 14px;border-bottom:1px solid #354551}th{color:#9edfd2}.note{padding:18px 22px;background:#273524;border-radius:12px}.issue{background:#3b2b25}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}figure{margin:0;padding:12px;background:#18242f;border-radius:10px}img{width:100%;height:auto}figcaption{padding-top:8px}code{color:#badbd7}.scroll{overflow:auto}details{margin:24px 0}li{margin:8px 0}</style><main>
<h1>战术机制扩展</h1><p>2026-10-25 · 五项机制已接入本地源码 · 未安装或更新iPhone</p>
<div class="note">完成两轮涉及关卡抽查。六个主线抽查关和四种补练各有两轮胜利；F22第一轮重试后获胜，第二轮及重试战败，全部保留。以下回合数是自动操作记录，不代表真人平均耗时或难度已达标。</div>
<h2>已落地的规则</h2><ul>
<li><b>掩护：</b>近战物理职业消耗行动保护一名邻接同伴，持续至下次己方回合。首次命中分担一半伤害，奇数向上取整；分担量不超过掩护者剩余生命。离开邻接即失效，不增加反击、不循环转伤。</li>
<li><b>拒阵枪：</b>威力3、命中85、重量3、必杀附加0、射程1；士兵、重装兵、壁垒卫士可用。M13与F24战后各队获得一件。主动近战造成伤害、完整交战后双方存活则击退1格；实体障碍、占位、边界或不可通行时不推，反击不触发。M33/M52/J53各少数精英自带效果。</li>
<li><b>特殊AI：</b>F22预告封桥射击；M42统领指挥三骑钳击，击败统领或切断投送站解除；J54预告聚光区域，撤离、掩护、击退或准备期累计18伤害打断均可应对。预告不暗换目标。</li>
<li><b>有限补练：</b>整备菜单主动选择突破/护阵演习。每章每队最多成功两次，每名参训者成功获60经验，含本场倒地者；无战斗经验和掉落，不产生永久战损，也不复活原濒死者。失败/退出无收益，原状态还原。第一章M13后、第二章F24后，其余章节两队首场主线后开放，最终合流关闭。</li>
<li><b>可破坏障碍：</b>F22货箱与M42木栅，近战队员邻接消耗行动。确认前说明打开的通路、敌我均可通行及仍需操作的主线机关；破坏状态与位图一起保存，重试复原。</li></ul>
<p><a href="knockback-design.md">击退设计依据</a> · <a href="training/README.md">补练完整规则</a> · <a href="summary.json">汇总与源码指纹</a></p>
<h2>两轮正常输入抽查</h2><p>使用历史真实队伍检查点的副本，经正常整备、装备、重入和按键执行；没有修改属性、生命、位置、随机结果或强制胜利。J54第一轮奥托新增濒死，第二轮无新增濒死；M13/M33/M52/J53/M42两轮无新增濒死。</p>
<div class="scroll"><table><tr><th>关卡</th><th>轮次</th><th>结果</th><th>回合</th><th>按键</th><th>证据</th></tr>''' + table + '''</table></div>
<h2>F22：完整保留失败与重试</h2><div class="note issue">F22第二轮未通关，不能列入“全部通关”。首轮重试3在42回合胜利、莉莎濒死并真实破坏货箱。90回合上限是测试驾驶策略停滞，非游戏强制时长；记录中的特殊射击未对正式成员造成伤害，不能直接把战败归因为新AI强度。此关真人难度仍需实机反馈。</div>
<div class="scroll"><table><tr><th>尝试</th><th>结果</th><th>回合</th><th>按键</th><th>新增濒死ID</th></tr>''' + f22 + '''</table></div><p><a href="rescue-play/README.md">全部尝试说明</a> · <a href="rescue-play/attempt-summary.json">尝试记录</a> · <a href="cover-input/report.json">掩护正常输入实触发记录</a></p>
<h2>检查与已修复问题</h2><table><tr><th>检查</th><th>断言数</th><th>结果</th></tr>''' + checked + '''</table>
<ul><li>敌方回合反击取胜后升级页被普通奖励流程覆盖：已修复，第二轮训练重跑通过。</li><li>取消掩护/破坏确认可能卡在行动状态：已修复，返回行动菜单。</li><li>查看战术说明自动保存未提交移动、读档可能再次移动：说明改为临时页；打开系统菜单前撤回未确认移动，恢复原位后才保存。</li><li>飞行者可被推入实体货箱/木栅：击退增加实体障碍判定，开门与破坏后重新按当前地形判断。</li><li>掩护说明底部间距、长危险提示换行、特殊攻击掩护者受击反馈及异常存档类型检查均已修正。</li></ul>
<p>断言计数不是独立关卡数量。画面采用已验证的不激活窗口后台渲染，检查手机布局安全区域；不是iPhone触摸试玩。部分早期测试退出出现资源释放警告，未据此声称整机性能无问题。</p>
<details><summary>展开14张运行画面</summary><div class="grid">''' + gallery + '''</div></details><p>截图逐像素无损压缩，保留2556×1179分辨率：<a href="visual/image-sizes.json">尺寸与字节记录</a>。</p></main></html>'''
    (OUT / "index.html").write_text(page)
    print(json.dumps({"checks_passed": all(r["passed"] for r in checks), "assertions": sum(r["count"] for r in checks),
                      "successful_sample_runs": len(plays), "F22_attempts": len(attempts)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

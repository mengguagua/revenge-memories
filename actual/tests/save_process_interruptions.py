"""Kill only our own isolated headless writer during primary/backup writes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

PROJECT = Path(__file__).resolve().parents[1]
GODOT = "/Applications/Godot.app/Contents/MacOS/Godot"
OUT = PROJECT / "reports/full-assessment-20261025/save"
root = Path(tempfile.mkdtemp(prefix="revenge-save-process-", dir="/private/tmp"))
cases = []
for index, window in enumerate(["primary", "backup"] * 3):
    folder = root / f"{index:02d}-{window}"
    folder.mkdir()
    command = [GODOT, "--headless", "--path", str(PROJECT), "--log-file",
               str(folder / "godot.log"), "--script", "res://tests/save_process_worker.gd",
               "--", "write", str(folder)]
    with (folder / "stdout.log").open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        target = folder / ("journey-slot-1.json.tmp" if window == "primary" else "journey-slot-1.json.bak.tmp")
        deadline = time.monotonic() + 20
        observed = False
        while time.monotonic() < deadline and process.poll() is None:
            if (folder / "ready").exists() and target.exists():
                observed = True
                process.kill()  # Owned subprocess; this never targets the game/editor.
                break
            time.sleep(0.0001)
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
    record = {"case": folder.name, "observed_window": observed,
              "window": window, "exit_code": process.returncode, "files": {}}
    for suffix in ["", ".bak"]:
        path = folder / ("journey-slot-1.json" + suffix)
        body = path.read_bytes()
        state = json.loads(body)
        record["files"]["primary" if not suffix else "backup"] = {
            "serial": state["flags"]["process_serial"], "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(), "json_complete": True}
    cases.append(record)
verify = subprocess.run([GODOT, "--headless", "--path", str(PROJECT), "--log-file",
                         str(root / "verify.log"), "--script", "res://tests/save_process_worker.gd",
                         "--", "verify", str(root)], capture_output=True, text=True, timeout=30)
line = next(line for line in verify.stdout.splitlines() if line.startswith("PROCESS_VERIFICATION "))
runtime = json.loads(line.partition(" ")[2])
result = {"passed": all(c["observed_window"] and c["exit_code"] == -9 for c in cases)
          and verify.returncode == 0 and runtime["passed"], "cases": cases,
          "runtime_validation": runtime, "isolated_directory": str(root),
          "scope": "Six owned macOS headless subprocess SIGKILLs during enlarged checkpoint writes. Not device suspend, power-loss/fsync, or iOS thermal testing."}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "process-interruptions.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"passed": result["passed"], "cases": len(cases), "runtime_validation": runtime}, ensure_ascii=False))
raise SystemExit(0 if result["passed"] else 1)

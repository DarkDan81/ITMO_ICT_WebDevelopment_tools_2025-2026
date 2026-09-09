"""Последовательно запускает программы и сохраняет реальные результаты."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone


def main() -> None:
    root = Path(__file__).resolve().parent
    results = {"measured_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
               "platform": platform.platform(), "cpu_count": os.cpu_count(), "workers": 4, "runs": []}
    for task, mode, limit in [(1, "formula", 10**13), (1, "loop", 5_000_000), (2, "formula", 10**13)]:
        for method in ["threading", "multiprocessing", "async"]:
            name = f"task{task}_{method}.py"
            env = dict(os.environ, LAB2_WORKERS="4", LAB2_SUM_MODE=mode, LAB2_SUM_LIMIT=str(limit), PYTHONIOENCODING="utf-8")
            run = subprocess.run([sys.executable, name], cwd=root, env=env, capture_output=True,
                                 text=True, encoding="utf-8", timeout=120)
            print(name, mode, run.stdout, flush=True)
            results["runs"].append({"program": name, "mode": mode, "limit": limit, "returncode": run.returncode,
                                    "stdout": run.stdout, "stderr": run.stderr})
    (root / "benchmark_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

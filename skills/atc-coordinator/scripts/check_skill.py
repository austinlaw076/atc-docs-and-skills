#!/usr/bin/env python3
"""Isolated local checks. All results are fixtures, never real Agent dispatch."""
import hashlib
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RUNTIME = SKILL / "scripts/runtime"


def run(args, *, expected=0, cwd=None):
    result = subprocess.run([sys.executable, *map(str, args)], cwd=cwd,
                            text=True, capture_output=True, timeout=60)
    if result.returncode != expected:
        raise AssertionError(f"exit={result.returncode} expected={expected}\n{result.stdout}\n{result.stderr}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--advisory-only', action='store_true',
                        help='Explicitly omit restricted-process tests; no isolation claim')
    options = parser.parse_args()
    cli = SKILL / "scripts/atc.py"
    prompt = SKILL / "scripts/prepare_prompt.py"
    prd = SKILL / "assets/prd-template.json"
    with tempfile.TemporaryDirectory(prefix="atc-skill-check-") as tmp:
        work = Path(tmp)
        args = [cli, "--prd", prd, "--run", work / "run"]
        compiled = json.loads(run([*args, "compile"], cwd=work).stdout)
        assert compiled["levels"] == [["R1", "R2"], ["R3"]]
        request = json.loads(run([*args, "dispatch", "R1"], cwd=work).stdout)
        request_path = work / "request.json"
        request_path.write_text(json.dumps(request))
        rendered = run([prompt, request_path], cwd=work).stdout
        assert request["input_hash"] in rendered
        assert "RESPONSE SCHEMA" in rendered and "UNTRUSTED TASK DATA" in rendered
        assert request["sources"]["S1"]["sha256"] in rendered
        report = json.loads(run([*args, "report"], cwd=work).stdout)
        assert report["product_status"] == "incomplete"
        assert report["tasks"]["R1"]["status"] == "running"
        request["order"]["goal"] = "tampered input"
        request_path.write_text(json.dumps(request))
        assert "input_hash mismatch" in run([prompt, request_path], expected=2, cwd=work).stderr
        assert "explicit --prd" in run([cli, "compile"], expected=2, cwd=work).stderr
        missing_run = run([cli, "--prd", prd, "compile"], expected=2, cwd=work)
        assert "explicit --run" in missing_run.stderr
    version = json.loads((SKILL / "assets/version.json").read_text())
    for name, expected in version["runtime_sha256"].items():
        assert hashlib.sha256((RUNTIME / "atc10" / name).read_bytes()).hexdigest() == expected
    unit_args = ['-m', 'unittest', 'discover', '-s', 'tests', '-q']
    if options.advisory_only:
        unit_args.extend(['-p', 'test_atc10*.py'])
    unit = run(unit_args, cwd=RUNTIME)
    count = int(re.search(r"Ran (\d+) tests", unit.stderr).group(1))
    print(json.dumps({"status": "pass", "runtime_unit_tests": count,
        "checks": ["portable_cli", "prd_dag", "full_prompt", "tampered_request_rejected",
                   "explicit_inputs", "incomplete_not_success", "runtime_source_hashes"],
        'restricted_profile': 'not_tested' if options.advisory_only else 'verified_local_process_tests',
        'live_model_agents': False,
        "provenance": "local_fixtures_only_no_real_agent_execution"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

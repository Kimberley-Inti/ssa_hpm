#!/usr/bin/env python3
"""Recheck a finished native run, including semantic negatives, without simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--results', type=Path, required=True)
p.add_argument('--work', type=Path, required=True)
a = p.parse_args()
results, work = a.results.resolve(), a.work.resolve()
source = Path(__file__).resolve().parent
execution = json.loads((results / 'execution.json').read_text())
status = json.loads((results / 'runner-exit.json').read_text())
if status != dict(native_exit_code=0, auto_checker_exit_code=0, manual_checker_exit_code=0):
    p.error('original native run and both checkers must have completed successfully')
log = results / 'rocket-linux-transparent.txt'
sha = lambda f: hashlib.sha256(f.read_bytes()).hexdigest()
if execution['native_exit_code'] != 0 or sha(log) != execution['log_sha256']:
    p.error('native execution/log identity mismatch')
post = results / 'postcheck'
post.mkdir(exist_ok=True)
manual_log = results / 'manual-regression.txt'
manual_execution = dict(execution, log_sha256=sha(manual_log),
    original_native_log_sha256=execution['log_sha256'],
    coverage='normalized manual suffix of the same native run; not another simulation')
manual_receipt = post / 'manual-execution.json'
manual_receipt.write_text(json.dumps(manual_execution, indent=2) + '\n')
users = work / 'transparent-users.json'
cases = [
    ('automatic', source / 'grade.py', [log, '--exit-code', '0', '--users', users]),
    ('manual', source.parent / 'grade-classification.py', [manual_log, '--exit-code', '0']),
    ('capacity', source / 'check-capacity-elf.py', ['--native-log', log, '--work', work]),
    ('automatic-negatives', source / 'negative.py',
        ['--native-log', log, '--execution', results / 'execution.json', '--users', users]),
    ('manual-negative', source.parent / 'test_classification_native.py',
        ['--native-log', manual_log, '--execution', manual_receipt]),
]
checks = []
for name, script, args in cases:
    dest = post / (name + '.json')
    cmd = [sys.executable, str(script)] + list(map(str, args)) + ['--out', str(dest)]
    done = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (post / (name + '.txt')).write_text(done.stdout)
    if done.returncode:
        print(done.stdout)
        raise SystemExit(done.returncode)
    data = json.loads(dest.read_text())
    assert data['passed'], name
    checks.append(dict(name=name, command=cmd, exit_code=done.returncode,
                       checks=len(data['checks'])))
    print(name, 'PASS', flush=True)
for name, original in [('automatic', 'summary.json'), ('manual', 'manual-summary.json')]:
    assert json.loads((post / (name + '.json')).read_text()) == json.loads((results / original).read_text())
summary = dict(passed=True, coverage='host-only replay/mutations of one completed native run',
               original_native_log_sha256=execution['log_sha256'], checks=checks)
(post / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print('PASS: all postchecks; no new native execution')

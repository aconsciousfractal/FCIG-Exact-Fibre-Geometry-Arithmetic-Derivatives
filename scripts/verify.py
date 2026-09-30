"""Run the self-contained exact companions in isolated normal and optimized modes."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def main():
    jobs = [('prime_family', 'expected_prime_family.json', []),
            ('finite', 'expected_finite.json', []),
            ('k47', 'expected_output.json', ['--self-test'])]
    with tempfile.TemporaryDirectory(prefix='exact-fibre-replay-') as tmp:
        for name, expected_file, args in jobs:
            expected = json.loads((ROOT/'companion'/expected_file).read_text(encoding='utf-8'))
            outputs = []
            for optimized in (False, True):
                cmd = [sys.executable, '-I', '-B'] + (['-O'] if optimized else [])
                cmd += [str(ROOT/'companion'/('verify_'+name+'.py')), *args]
                run = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, encoding='utf-8')
                if run.returncode:
                    raise RuntimeError(f'{name}: exit {run.returncode}\n{run.stdout}\n{run.stderr}')
                result = json.loads(run.stdout)
                if result.get('status') != 'PASS':
                    raise RuntimeError(f'{name}: not PASS')
                if name == 'k47':
                    rejected = result.pop('rejected_corruptions', [])
                    if len(rejected) != 10 or len(set(rejected)) != 10:
                        raise RuntimeError('k47: missing semantic negative controls')
                if result != expected:
                    raise RuntimeError(f'{name}: deterministic expected output differs')
                outputs.append(run.stdout)
            if outputs[0] != outputs[1]:
                raise RuntimeError(f'{name}: normal/optimized semantics differ')
            print(f'{name}: PASS; normal/optimized identical')
    print('EXACT_FIBRE_REPLAY_PASS|companions=3|modes=2')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print('EXACT_FIBRE_REPLAY_FAIL: '+str(exc), file=sys.stderr)
        raise SystemExit(1)

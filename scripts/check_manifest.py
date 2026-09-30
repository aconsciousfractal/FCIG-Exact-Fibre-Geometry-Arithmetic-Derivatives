"""Verify the delivered reader-tree bytes; --write is an explicit authoring operation."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT/'MANIFEST_SHA256.txt'
EVIDENCE = ROOT/'EVIDENCE_SHA256.txt'

def files(evidence=False):
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if not p.is_file() or p == MANIFEST:
            continue
        if set(rel.parts) & {'.git', '__pycache__', '.pytest_cache'}:
            continue
        if rel.parts[:2] == ('paper', 'build') or p.suffix == '.pyc':
            continue
        if evidence:
            selected = (
                (rel.parts[0] == 'companion' and p.suffix in ('.py', '.json'))
                or (rel.parts[0] == 'tests' and p.suffix == '.py')
                or rel.as_posix() in ('scripts/verify.py', 'scripts/check_manifest.py',
                                      '.github/workflows/verify.yml', '.gitattributes', 'VERSION')
            )
            if not selected:
                continue
        yield p

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--evidence', action='store_true',
                        help='check computational evidence only, excluding paper and prose')
    args = parser.parse_args()
    manifest = EVIDENCE if args.evidence else MANIFEST
    marker = 'EVIDENCE_MANIFEST' if args.evidence else 'MANIFEST'
    actual = {p.relative_to(ROOT).as_posix(): digest(p) for p in files(args.evidence)}
    if args.write:
        manifest.write_text(''.join(f'{h}  {p}\n' for p,h in actual.items()), encoding='utf-8', newline='\n')
        print(f'{marker}_WRITTEN|files={len(actual)}')
        return 0
    expected = {}
    for line in manifest.read_text(encoding='utf-8').splitlines():
        h, sep, name = line.partition('  ')
        rel = PurePosixPath(name)
        if not sep or not re.fullmatch('[0-9a-f]{64}', h) or rel.is_absolute() or '..' in rel.parts or '\\' in name:
            raise ValueError('Invalid manifest entry')
        if name in expected:
            raise ValueError('Duplicate manifest entry: '+name)
        expected[name] = h
    if actual != expected:
        changed = sorted(n for n in actual.keys() | expected.keys() if actual.get(n) != expected.get(n))
        raise ValueError('Manifest mismatch: '+', '.join(changed))
    print(f'{marker}_PASS|files={len(actual)}')
    return 0

if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print('MANIFEST_FAIL: '+str(exc), file=sys.stderr)
        raise SystemExit(1)

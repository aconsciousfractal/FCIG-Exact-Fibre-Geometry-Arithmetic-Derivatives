# Reproduce the exact checks

Python 3.10+ and its standard library suffice. No pip installation, random seed,
symbolic algebra package, solver, network query or private input is required.
Run commands from the repository root; replace `python` by your interpreter name.

```text
python scripts/verify.py
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python scripts/check_manifest.py
python scripts/check_manifest.py --evidence
```

The replay compares all outputs in normal and `-O` modes against local expected
JSON. Each subprocess uses Python isolated mode and a temporary working directory.
The three independent entry points are:

```text
python companion/verify_prime_family.py
python companion/verify_finite.py
python companion/verify_k47.py --self-test
```

Expected results: 40 eligible exact prime-index minima below 200, 47 pivot lifts,
535 first-wrap controls; two original variable-base minimum pairs, 104 recursive
primality nodes, 453 literal cube controls and two mixed-frequency certificates;
k=47 minima 6493223 and 1358381707976, all 20 useful optimizers, and 10 rejected
mutations. The finite verifier rejects six further corruptions. These are finite
checks; density and universal statements are established by the manuscript proofs.
The 31 unit tests include semantic rejection checks for zero useful Wronskians,
missing or duplicate cases, extra or missing coordinates, and noninteger fields.
The k=47 tests check every numeric leaf and list dimension and reject the
reported floating-point basis through both CLI and aggregate replay.
Spectral certificates are matched to original inputs by unique case identifiers.
The displayed axis-ceiling calculation supports exactly two restrictive phases;
other dimensions are rejected.
Runtime is normally seconds to a few minutes, depending on the computer.

## Rebuild the PDF

With an existing pdflatex and the packages listed in the TeX preamble:

```text
python scripts/build_pdf.py
```

The builder uses three passes, disables MiKTeX automatic installation, and
writes auxiliaries only under `paper/build/`. Set `PDFLATEX` to an executable
path if necessary. It does not install TeX or packages. The supplied PDF was
built with pdfTeX 1.40.25 / TeX Live 2023 (Debian). PDF bytes may differ across TeX
versions; numerical companion outputs are deterministic.

`MANIFEST_SHA256.txt` identifies the delivered files, excluding Git metadata,
ignored caches and build auxiliaries. Intentional edits, including a PDF rebuild,
may change its hashes. After reviewing such changes, explicitly regenerate it
with `python scripts/check_manifest.py --write`; normal verification never
rewrites the manifest. This integrity check cannot certify mathematical truth.

## Evidence identity

Version 0.2.3 has computational manifest [EVIDENCE_SHA256.txt](EVIDENCE_SHA256.txt),
SHA-256 `9dba941d261ab87247323478b41bda18dd422b902f4f9f5ad1179d86ccdfe01c`, also printed in the paper and README.
First compare that digest with your independently obtained paper, then run
`python scripts/check_manifest.py --evidence`. For example, compute the digest
with Python's standard library:

```text
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('EVIDENCE_SHA256.txt').read_bytes()).hexdigest())"
```

This manifest covers companion Python/JSON files, public tests, replay and
manifest checkers, CI, checkout attributes and VERSION. It excludes the PDF,
TeX, prose and both manifests, avoiding a circular paper-dependent digest.
To prepare an intentional future revision, update the evidence with
`python scripts/check_manifest.py --evidence --write`, update its digest in
the paper/README/CITATION, rebuild the PDF, and only then regenerate the full
`MANIFEST_SHA256.txt`. Ordinary verification never rewrites either manifest.
An integrity digest identifies bytes; it does not certify mathematical truth.

# Reproduce the exact checks

Python 3.10+ and its standard library suffice. No pip installation, random seed,
symbolic algebra package, solver, network query or private input is required.
Run commands from the repository root; replace `python` by your interpreter name.

```text
python scripts/verify.py
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python scripts/check_manifest.py
```

The replay compares all outputs in normal and `-O` modes against local expected
JSON. Each subprocess uses Python isolated mode and a temporary working directory.
The three independent entry points are:

```text
python companion/verify_prime_family.py
python companion/verify_finite.py
python companion/verify_k47.py --self-test
```

Expected results:40 eligible exact prime-index minima below200,47 pivot lifts,
535 first-wrap controls; two original variable-base minimum pairs,104 recursive
primality nodes,453 literal cube controls and two mixed-frequency certificates;
k47 minima6493223 and1358381707976, all20 useful optimizers, and10 rejected
mutations. The finite verifier rejects six further corruptions. These are finite
checks; density and universal statements are established by the manuscript proofs.
The 22 unit tests include semantic rejection checks for zero useful Wronskians,
missing or duplicate cases, extra or missing coordinates, and noninteger fields.
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
built with pdfTeX1.40.25/TeX Live2023(Debian). PDF bytes may differ across TeX
versions; numerical companion outputs are deterministic.

`MANIFEST_SHA256.txt` identifies the delivered files, excluding Git metadata,
ignored caches and build auxiliaries. Intentional edits, including a PDF rebuild,
may change its hashes. After reviewing such changes, explicitly regenerate it
with `python scripts/check_manifest.py --write`; normal verification never
rewrites the manifest. This integrity check cannot certify mathematical truth.

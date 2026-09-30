# Exact bounded fibres and the cost of primitive Wronskians

**Oleksiy Babanskyy** · [ORCID 0009-0001-6176-6208](https://orcid.org/0009-0001-6176-6208)

Unpublished research manuscript and exact-arithmetic companion, version **0.2.3**.
The work has not undergone independent specialist review.

The paper compares two costs in Pasten's arithmetic-derivative lattice:
producing any nonzero Wronskian, and producing the positive generator of its
integer image. The norm always measures the original prime coordinates.

For every odd prime q such that q+2 has a simple prime divisor, the first cost
is one. The primitive cost is exactly (q-D)/2 for composite q+2 and (q+1)/2
for prime q+2, where D is the explicit image generator. The formula holds for
a relative-density-one set of prime indices and gives a linear penalty.

The manuscript also proves an exact bounded-fibre description, a uniform
simultaneous-return comparison on a positive-lower-density set of integer
bases yielding radical-small triples, and a precisely scoped limitation of sparse positive Fourier
certificates. It supplies exact finite minima for 2+3^47 and for variable bases
14 and 44, a full-domain fixed-power bound, and a weighted covering proposition.

Unbounded separation within 2+3^k and within rad(abc)<c remains open.
The selected-domain theorem uses an explicitly attributed analytic estimate.
Classical ingredients are identified; no priority or abc consequence is claimed.

- [Paper PDF](paper/Exact-Fibre-Geometry-Arithmetic-Derivatives.pdf)
- [Editable standalone TeX](paper/Exact-Fibre-Geometry-Arithmetic-Derivatives.tex)
- [Reviewer path](README_REVIEWER.md) and [reproduction](REPRODUCE.md)
- [Claim map](docs/CLAIM_MAP.md), [source comparison](docs/SOURCE_COMPARISON.md),
  [known limits](docs/KNOWN_LIMITS.md)

From the repository root, with Python 3.10 or newer:

```text
python scripts/verify.py
python -m unittest discover -s tests -v
python -O -m unittest discover -s tests -v
python scripts/check_manifest.py
```

These commands need no third-party Python packages or network. The PDF is
included; rebuilding it additionally requires an existing pdflatex installation.
See [licence scope](LICENSE_SCOPE.md), [AI use](AI_USE.md) and [citation](CITATION.cff).

## Companion identity

Canonical repository address: [https://github.com/aconsciousfractal/FCIG-Exact-Fibre-Geometry-Arithmetic-Derivatives](https://github.com/aconsciousfractal/FCIG-Exact-Fibre-Geometry-Arithmetic-Derivatives).
This is the prepared, unpublished version **0.2.3**; anonymous access at that
address must be confirmed on public release.

Computational evidence manifest: [EVIDENCE_SHA256.txt](EVIDENCE_SHA256.txt).
Its SHA-256 is `9dba941d261ab87247323478b41bda18dd422b902f4f9f5ad1179d86ccdfe01c`.
This identity covers the exact data, checkers, tests and replay configuration,
and excludes the manuscript and prose that cite it. The paper prints the same
digest. See [REPRODUCE.md](REPRODUCE.md) for verification.

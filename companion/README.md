# Exact-arithmetic companion

`verify_prime_family.py` checks literal lower cubes for eligible prime indices
below 200, all 47 simple-pivot lifts in that range, boundary cases, and 535 abstract
first-wrap controls. `verify_k47.py` verifies the full compact certificate and,
with `--self-test`, rejects ten corruptions. `verify_finite.py` certifies the
x14/x44 minima and two spectral benchmarks, including original equations,
recursive primality and six rejected corruptions.

The five files in `data/` contain self-contained exact integers and rational
pairs [numerator,denominator]. They were extracted from research deliveries,
checked against their source bytes, reformatted and assigned descriptive family
labels. No received program is imported. Acceptance reconstructs row gcds,
images, all relevant residues, lattice determinants, complete search rectangles
and original bounded carry equations; expected JSON is an additional regression
comparison, not the source of mathematical acceptance.

For k47, expected_output.json is the ordinary result; the top-level replay adds
the required ten-rejection self-test check before comparing it. Other expected
outputs are expected_finite.json and expected_prime_family.json.

Universal and density statements are not established by running these files.
See sections3–6 and the appendices for their proofs.

# Reviewer path

This unpublished manuscript and companion were developed with AI assistance.
The computational checks support review; they do not establish independent
scientific acceptance.

## Ten-minute reading path

1. Read Theorem 1.1 on PDF page 3: the exact prime/composite formula, its simple
   prime hypothesis, and the relative-prime-density quantifier.
2. Read Theorems 5.2 and 5.3 (pages 8–9): a uniform original-coordinate comparison
   and its common domain. Appendix A supplies the density proof and attribution.
3. Read Theorem 6.5 on page 12 and its final paragraph: the limitation concerns
   specified positive frequency certificates at feasible subquadratic budgets.
4. Read the two open questions on page 17 and the [claim map](docs/CLAIM_MAP.md).

## Thirty-minute replay path

Run `python scripts/verify.py` from the root. It runs all three companions in
normal and optimized isolated Python modes, compares deterministic expected
outputs, and requires rejection of ten k47 and six variable-base corruptions.
Expected terminal line: `EXACT_FIBRE_REPLAY_PASS|companions=3|modes=2`.
Then run the 22 unit tests in normal and optimized modes and the manifest check
in [REPRODUCE.md](REPRODUCE.md). The tests include altered certificates with a
zero Wronskian, missing cases, duplicate identifiers and inconsistent dimensions.
The checks read artifacts and use temporary working directories; they do not
rewrite certificate data or the paper. Python caches and TeX build files are ignored.

Inspect Theorem 7.1 and its supplied data for both lower and upper minima, then
the complete k47 proof in section 8. The x14 lower cube fails by a carry deficit
of two, although its reduced phase box still contains an index. This is a useful
test against confusing projected and original minima.

## Requested critical review

Check the bounded pivot lift in Theorem 1.1; all same-index residues in Theorem5.2;
the analytic-input and parameter-order deduction in Appendix A; the quantifiers
in Theorem6.5; and the exact lower-window exhaustion in section7. Assess originality
against the specific prior work in [SOURCE_COMPARISON](docs/SOURCE_COMPARISON.md).

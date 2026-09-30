"""Semantic regressions: invalid certificates must fail even under python -O."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("finite_validation", ROOT/"companion/verify_finite.py")
finite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finite)


class CertificateValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.minima = finite.inputs("exact_minima.json")
        cls.certs = finite.inputs("spectral_certificates.json")
        cls.originals = finite.inputs("spectral_inputs.json")
        cls.known = finite.certified_primes(finite.inputs("minima_primes.json"))
        cls.spectral_known = finite.certified_primes(finite.inputs("spectral_primes.json"))

    def test_zero_wronskian_is_not_a_useful_upper_witness(self):
        case = deepcopy(next(c for c in self.minima if c["input"]["x"] == 44))
        case["m"] = 11
        case["useful_upper"]["winner"].update(
            u=0, zx=[1,-11], zb=[0]*len(case["input"]["factors_b"]))
        with self.assertRaisesRegex(ValueError, "positive useful image index"):
            finite.minimum(case, self.known)

    def test_minimum_and_useful_index_require_positive_exact_integers(self):
        for field in ("m", "m_prim", "u"):
            for value in (0, -1, True, 1.0):
                with self.subTest(field=field, value=repr(value)):
                    case = deepcopy(self.minima[0])
                    obj = case["useful_upper"]["winner"] if field == "u" else case
                    obj[field] = value
                    with self.assertRaises(ValueError):
                        finite.minimum(case, self.known)

    def test_missing_or_extra_spectral_cases_fail(self):
        for certs, obs in (([],[]), (self.certs,[]), ([],self.originals),
                           (self.certs,self.originals[:1]), (self.certs[:1],self.originals)):
            with self.subTest(certificates=len(certs), inputs=len(obs)):
                with self.assertRaises(ValueError):
                    finite.spectral_pairs(certs,obs)

    def test_duplicate_or_mismatched_case_ids_fail(self):
        for side in ("certificates", "inputs"):
            for replacement in ("duplicate", "unknown", ""):
                with self.subTest(side=side, replacement=replacement):
                    certs,obs = deepcopy(self.certs),deepcopy(self.originals)
                    rows = certs if side == "certificates" else obs
                    rows[1]["id"] = rows[0]["id"] if replacement == "duplicate" else replacement
                    with self.assertRaises(ValueError):
                        finite.spectral_pairs(certs,obs)

    def test_case_pairing_uses_identity_not_position(self):
        pairs = finite.spectral_pairs(self.certs,list(reversed(self.originals)))
        self.assertEqual([(c["id"],ob["id"]) for c,ob in pairs],
                         [(c["id"],c["id"]) for c in self.certs])

    def test_extra_or_missing_frequency_coordinate_fails(self):
        for size in (1,3):
            case = deepcopy(self.certs[0])
            case["frequencies"][0]["vector"] = ([123456789]*size)
            with self.subTest(size=size), self.assertRaisesRegex(ValueError, "frequency dimension"):
                finite.spectrum(case)

    def test_every_zipped_spectral_array_has_exact_dimension(self):
        for field in ("lengths", "weights", "marginal_energy"):
            for size in (1,3):
                with self.subTest(field=field,size=size):
                    case = deepcopy(self.certs[0])
                    obj = case["native"] if field == "weights" else case
                    values = obj[field]
                    obj[field] = values[:1] if size == 1 else values+[values[0]]
                    with self.assertRaises(ValueError):
                        finite.spectrum(case)

    def test_axis_formula_rejects_other_phase_counts(self):
        for phases in ([], self.certs[0]["restrictive"][:1],
                       self.certs[0]["restrictive"]+[[101,1]]):
            case = deepcopy(self.certs[0])
            case["restrictive"] = phases
            with self.assertRaisesRegex(ValueError, "two restrictive phases"):
                finite.spectrum(case)

    def test_empty_frequency_list_fails(self):
        case = deepcopy(self.certs[0])
        case["frequencies"] = []
        with self.assertRaisesRegex(ValueError, "nonempty frequencies"):
            finite.spectrum(case)

    def test_frequency_booleans_and_floats_fail(self):
        for value in (True, 0.0):
            case = deepcopy(self.certs[0])
            case["frequencies"][0]["vector"][0] = value
            with self.assertRaises(ValueError):
                finite.spectrum(case)

    def test_witness_coordinates_cannot_be_truncated_or_overwritten(self):
        for i in range(len(self.certs)):
            for mutation in ("extra_prime", "extra_value", "duplicate_prime", "unknown_prime", "bool"):
                with self.subTest(case=i, mutation=mutation):
                    case = deepcopy(self.certs[i])
                    witness = case["witness"]
                    if mutation == "extra_prime":
                        witness["primes"].append(101)
                    elif mutation == "extra_value":
                        witness["z"].append(0)
                    elif mutation == "duplicate_prime":
                        witness["primes"][1] = witness["primes"][0]
                    elif mutation == "unknown_prime":
                        witness["primes"][0] = 101
                    else:
                        witness["z"][0] = True
                    with self.assertRaises(ValueError):
                        finite.spectral_original(case,self.originals[i],self.spectral_known)

    def test_spectral_index_requires_positive_integer(self):
        for i in range(len(self.certs)):
            for value in (0,-1,True,1.0):
                case = deepcopy(self.certs[i])
                case["witness"]["u"] = value
                with self.subTest(case=i,value=repr(value)), self.assertRaises(ValueError):
                    finite.spectral_original(case,self.originals[i],self.spectral_known)

    def test_unknown_spectral_input_kind_fails(self):
        ob = deepcopy(self.originals[1])
        ob["kind"] = "unrecognized"
        with self.assertRaisesRegex(ValueError, "spectral input kind"):
            finite.spectral_original(self.certs[1],ob,self.spectral_known)

    def test_exact_integer_fields_do_not_accept_equal_booleans(self):
        nodes = deepcopy(finite.inputs("minima_primes.json"))
        next(n for n in nodes if n["p"] == 3)["factors"][0][1] = True
        with self.assertRaises(ValueError):
            finite.certified_primes(nodes)
        for value in (True,1.0):
            with self.assertRaises(ValueError):
                finite.rat([value,1])

    def test_support_length_must_fit_claimed_budget(self):
        case = deepcopy(self.certs[0])
        case["lengths"][0] = case["B"]+2
        with self.assertRaisesRegex(ValueError, "spectral support within budget"):
            finite.spectrum(case)

    def test_aggregate_replay_fails_when_original_inputs_are_empty(self):
        # This previously passed with the exact expected aggregate output.
        with tempfile.TemporaryDirectory(prefix="fibre-negative-") as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT/"companion",root/"companion",
                            ignore=shutil.ignore_patterns("__pycache__"))
            shutil.copytree(ROOT/"scripts",root/"scripts",
                            ignore=shutil.ignore_patterns("__pycache__"))
            (root/"companion/data/spectral_inputs.json").write_text("[]\n",encoding="utf-8")
            cmd = [sys.executable,"-I","-B"] + (["-O"] if sys.flags.optimize else [])
            run = subprocess.run(cmd+[str(root/"scripts/verify.py")],cwd=root,
                                 capture_output=True,text=True,timeout=90)
            self.assertNotEqual(run.returncode,0)
            self.assertIn("nonempty spectral inputs",run.stderr)
            self.assertNotIn("EXACT_FIBRE_REPLAY_PASS",run.stdout)


if __name__ == "__main__":
    unittest.main()

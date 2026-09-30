"""Reject nonintegral k47 inputs before arithmetic, including aggregate replay."""
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
spec = importlib.util.spec_from_file_location("k47_validation", ROOT / "companion/verify_k47.py")
k47 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(k47)
FLOATING_BASIS = [-2144551.827586207, 739623.3103448276]


def descendants(value, path=()):
    yield path, value
    if type(value) is dict:
        for key, child in value.items():
            yield from descendants(child, (*path, key))
    elif type(value) is list:
        for index, child in enumerate(value):
            yield from descendants(child, (*path, index))


def replace(cert, path, value):
    for key in path[:-1]:
        cert = cert[key]
    cert[path[-1]] = value


class K47CertificateValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cert = json.loads((ROOT / "companion/k47_certificate.json").read_text(encoding="utf-8"))

    def test_original_exact_result_is_unchanged(self):
        expected = json.loads((ROOT / "companion/expected_output.json").read_text(encoding="utf-8"))
        self.assertEqual(k47.verify(deepcopy(self.cert)), expected)

    def test_reported_floating_basis_is_rejected(self):
        altered = deepcopy(self.cert)
        altered["projection_basis"][1] = FLOATING_BASIS[:]
        with self.assertRaisesRegex(k47.CertificateError, "projection_basis.*exact integer"):
            k47.verify(altered)

    def test_every_numeric_leaf_requires_an_exact_integer(self):
        for path, original in descendants(self.cert):
            if type(original) is not int:
                continue
            for value in (float(original), bool(original), str(original), None):
                with self.subTest(path=path, replacement=repr(value)):
                    altered = deepcopy(self.cert)
                    replace(altered, path, value)
                    with self.assertRaisesRegex(k47.CertificateError, "exact integer"):
                        k47.verify(altered)

    def test_every_list_has_exact_dimensions(self):
        for path, value in descendants(self.cert):
            if type(value) is not list:
                continue
            for replacement in (value[:-1], value + [deepcopy(value[-1])]):
                with self.subTest(path=path, size=len(replacement)):
                    altered = deepcopy(self.cert)
                    replace(altered, path, replacement)
                    with self.assertRaisesRegex(k47.CertificateError, "dimensions"):
                        k47.verify(altered)

    def test_sequence_substitutes_are_rejected(self):
        for path, value in descendants(self.cert):
            if type(value) is not list:
                continue
            with self.subTest(path=path):
                altered = deepcopy(self.cert)
                replace(altered, path, tuple(value))
                with self.assertRaisesRegex(k47.CertificateError, "dimensions"):
                    k47.verify(altered)

    def test_missing_or_extra_object_fields_are_rejected(self):
        for path, value in descendants(self.cert):
            if type(value) is not dict:
                continue
            for mutation in ("missing", "extra"):
                with self.subTest(path=path, mutation=mutation):
                    altered = deepcopy(self.cert)
                    target = altered
                    for key in path:
                        target = target[key]
                    if mutation == "missing":
                        del target[next(iter(target))]
                    else:
                        target["unrecognized"] = 0
                    with self.assertRaisesRegex(k47.CertificateError, "fields"):
                        k47.verify(altered)

    def test_certificate_requires_an_object(self):
        for value in (None, [], 47, "p68_k47_certificate_v1"):
            with self.subTest(value=value), self.assertRaises(k47.CertificateError):
                k47.verify(value)

    def test_cli_rejects_reported_basis_in_both_modes_with_or_without_self_test(self):
        with tempfile.TemporaryDirectory(prefix="k47-invalid-") as tmp:
            altered = deepcopy(self.cert)
            altered["projection_basis"][1] = FLOATING_BASIS[:]
            certificate = Path(tmp) / "invalid.json"
            certificate.write_text(json.dumps(altered), encoding="utf-8")
            for optimized in (False, True):
                for self_test in (False, True):
                    with self.subTest(optimized=optimized, self_test=self_test):
                        command = [sys.executable, "-I", "-B"]
                        command += ["-O"] if optimized else []
                        command += [str(ROOT / "companion/verify_k47.py"), "--certificate", str(certificate)]
                        command += ["--self-test"] if self_test else []
                        result = subprocess.run(command, cwd=tmp, capture_output=True, text=True, timeout=60)
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        output = json.loads(result.stdout)
                        self.assertEqual(output["status"], "FAIL")
                        self.assertIn("exact integer", output["error"])

    def test_aggregate_replay_rejects_reported_basis_in_both_modes(self):
        with tempfile.TemporaryDirectory(prefix="k47-aggregate-") as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / "companion", root / "companion",
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            (root / "scripts").mkdir()
            shutil.copyfile(ROOT / "scripts/verify.py", root / "scripts/verify.py")
            altered = deepcopy(self.cert)
            altered["projection_basis"][1] = FLOATING_BASIS[:]
            (root / "companion/k47_certificate.json").write_text(json.dumps(altered), encoding="utf-8")
            for optimized in (False, True):
                with self.subTest(optimized=optimized):
                    command = [sys.executable, "-I", "-B"]
                    command += ["-O"] if optimized else []
                    command += [str(root / "scripts/verify.py")]
                    result = subprocess.run(command, cwd=tmp, capture_output=True, text=True, timeout=60)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertNotIn("EXACT_FIBRE_REPLAY_PASS", result.stdout)
                    self.assertIn("projection_basis", result.stderr)
                    self.assertIn("exact integer", result.stderr)


if __name__ == "__main__":
    unittest.main()

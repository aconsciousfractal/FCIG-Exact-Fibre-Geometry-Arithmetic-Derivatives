"""Small independent mathematical boundaries against overbroad claims."""
from pathlib import Path
from itertools import product
from fractions import Fraction
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('finite', ROOT/'companion/verify_finite.py')
finite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finite)

class MathematicalBoundaries(unittest.TestCase):
    def test_gcd_and_real_interval_do_not_imply_a_bounded_lift(self):
        values = {5*x+3*y for x,y in product(range(-1,2), repeat=2)}
        self.assertNotIn(1, values)
        self.assertEqual(values, {-8,-5,-3,-2,0,2,3,5,8})

    def test_prime_target_requires_its_own_formula(self):
        feasible = [(a,b,a+b) for a,b in product(range(-2,3), repeat=2)
                    if 2*b-3*a == 1]
        optimum = min(max(map(abs,z)) for z in feasible)
        self.assertEqual(optimum, 2)
        self.assertEqual([z for z in feasible if max(map(abs,z)) == optimum], [(-1,-1,-2)])

    def test_powerful_target_cannot_use_simple_prime_formula(self):
        solutions = []
        for a in range(-27,28):
            for b in range(-27,28):
                if 2*b-47*a == 7 and (a+b)%14 == 0:
                    solutions.append((a,b,(a+b)//14))
        self.assertEqual(min(max(map(abs,z)) for z in solutions), 27)

    def test_a_large_modulus_does_not_force_an_improving_return(self):
        tau = min(max(u,abs(finite.center(4*u,97))) for u in range(1,98))
        self.assertEqual(tau,4)

    def test_strict_fractional_drift_window(self):
        actual = finite.admissible_indices([(11,2)], Fraction(7,2), 3, 1,
                 dict(pivot=0,basis=[[1,2],[0,11]]))
        self.assertEqual(actual,[1])

    def test_fermat_pseudoprime_is_not_a_prime_certificate(self):
        nodes=[{'p':2},{'p':3,'factors':[[2,1]],'a':2},
               {'p':5,'factors':[[2,2]],'a':2},
               {'p':7,'factors':[[2,1],[3,1]],'a':3},
               {'p':561,'factors':[[2,4],[5,1],[7,1]],'a':2}]
        with self.assertRaises(ValueError):
            finite.certified_primes(nodes)

if __name__ == '__main__':
    unittest.main()

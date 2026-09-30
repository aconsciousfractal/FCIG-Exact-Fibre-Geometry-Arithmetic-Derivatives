#!/usr/bin/env python3
"""Exact, standalone k=47 companion. Python standard library only.

Checks a finite certificate, including primality by exhaustive trial division,
coverage of all useful vectors below the candidate budget, the 20 minimizers,
and the primitive-value minimum and complete bounded affine parametrization.
No assertions are used for certificate acceptance; -O has identical semantics.
"""
from __future__ import annotations
import argparse
import copy
import json
from functools import lru_cache
from math import gcd, isqrt, prod
from pathlib import Path

class CertificateError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise CertificateError(message)


def integer_vector(value, size, name):
    require(type(value) is list and len(value) == size, name + " dimensions")
    for index, entry in enumerate(value):
        require(type(entry) is int, f"{name}[{index}] must be an exact integer")


def integer_matrix(value, rows, columns, name):
    require(type(value) is list and len(value) == rows, name + " dimensions")
    for index, row in enumerate(value):
        integer_vector(row, columns, f"{name}[{index}]")


def phase_shape(value, name):
    scalars = ("j", "v", "t", "H0", "x0", "beta", "C0")
    require(type(value) is dict and set(value) == {*scalars, "residues"},
            name + " fields")
    for key in scalars:
        require(type(value[key]) is int, name + "." + key + " must be an exact integer")
    integer_vector(value["residues"], 4, name + ".residues")


def validate_certificate_shape(cert):
    """Validate the fixed JSON schema before any certificate arithmetic."""
    scalars = ("k", "c", "image_generator", "useful_minimum", "primitive_minimum")
    vectors = {"ordered_primes": 7, "f_row": 7, "w_row": 7,
               "useful_projection": 2, "positive_primitive_witness": 7}
    matrices = {"factorization": (5, 2), "projection_basis": (2, 2),
                "all_useful_optimizers": (20, 7)}
    phases = ("useful_phase", "negative_primitive_phase")
    require(type(cert) is dict, "certificate must be a JSON object")
    require(set(cert) == {"format", *scalars, *vectors, *matrices, *phases},
            "certificate fields")
    require(cert["format"] == "p68_k47_certificate_v1", "certificate format")
    for key in scalars:
        require(type(cert[key]) is int, key + " must be an exact integer")
    for key, size in vectors.items():
        integer_vector(cert[key], size, key)
    for key, (rows, columns) in matrices.items():
        integer_matrix(cert[key], rows, columns, key)
    for key in phases:
        phase_shape(cert[key], key)


@lru_cache(maxsize=None)
def prime(n):
    if type(n) is not int or n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    return all(n % d for d in range(3, isqrt(n) + 1, 2))

def ceildiv(a, b):
    require(b > 0, "nonpositive denominator")
    return -((-a) // b)

def dot(a, b):
    require(len(a) == len(b), "row/vector length")
    return sum(x * y for x, y in zip(a, b))

def phase(k, h, d, P, ps, es, j, v):
    require((3 * d * v - j) % P == 0, "projected congruence")
    t = (3 * d * v - j) // P
    rs = [(-t * pow(3 * e * (d // p), -1, p)) % p
          for p, e in zip(ps, es)]
    numerator = t + sum(3 * e * (d // p) * r
                        for p, e, r in zip(ps, es, rs))
    require(numerator % d == 0, "phase divisibility")
    H = numerator // d
    x0 = (H * pow(k, -1, 3)) % 3
    require((k * x0 - H) % 3 == 0, "x3 residue")
    beta = (k * x0 - H) // 3
    require((h * j + 2 * k * x0) % 3 == 0, "x2 integrality")
    return dict(j=j, v=v, t=t, residues=rs, H0=H, x0=x0,
                beta=beta, C0=(h * j + 2 * k * x0) // 3)

def capacity(k, ps, es, ph, B):
    lo = [ceildiv(-B-r, p) for p, r in zip(ps, ph["residues"])]
    hi = [(B-r)//p for p, r in zip(ps, ph["residues"])]
    L, U = dot(es, lo), dot(es, hi)
    # Keep the x3 bound explicitly, even though it is redundant here.
    nlo = max(ceildiv(-B-ph["C0"], 2*k),
              ceildiv(-B-ph["x0"], 3), ceildiv(L-ph["beta"], k))
    nhi = min((B-ph["C0"])//(2*k),
              (B-ph["x0"])//3, (U-ph["beta"])//k)
    return dict(lo=lo, hi=hi, L=L, U=U, nlo=nlo, nhi=nhi,
                source_nmax=(B-ph["C0"])//(2*k))

def lift(k, ps, ph, n, ys):
    return [ph["C0"] + 2*k*n, ph["x0"] + 3*n,
            *[r+p*y for p,r,y in zip(ps,ph["residues"],ys)], ph["v"]]

def verify(cert):
    validate_certificate_shape(cert)
    k = cert["k"]
    require(type(k) is int and k == 47, "this verifier is for k=47")
    fac = cert["factorization"]
    require(fac == [[7,4],[11,1],[59,1],[4691,1],[3637447066471,1]],
            "declared factorization scope")
    require(all(prime(p) and type(e) is int and e > 0 for p,e in fac),
            "nonprime factor or invalid exponent")
    T, c = 3**(k-1), 3**k+2
    require(prod(p**e for p,e in fac) == c == cert["c"], "factorization product")
    ps, es = [p for p,e in fac[:-1]], [e for p,e in fac[:-1]]
    P, d = fac[-1][0], prod(ps)
    h = c // (d * P)
    primes = [2,3,*ps,P]
    f = [1,k*T,*[-c*e//p for p,e in fac]]
    w = [-3*T,2*k*T,*[0 for _ in fac]]
    require(primes == cert["ordered_primes"], "coordinate order")
    require(f == cert["f_row"] and w == cert["w_row"], "original rows")
    minor_gcd = 0
    for i in range(len(f)):
        for j in range(i):
            minor_gcd = gcd(minor_gcd, f[i]*w[j]-f[j]*w[i])
    fgcd = gcd(*f)
    require(fgcd == 1 and minor_gcd == T*h == cert["image_generator"],
            "image from exact minors")
    # Every bounded additive vector yields j=(3*x2-2*k*x3)/h in Z:
    # h divides c; reducing 3F mod h gives h | 3*x2-2*k*x3.
    require(c % h == 0 and (3*T+2) % h == 0, "integral j reduction")
    L = d + 2*sum(e*(d//p) for p,e in zip(ps,es))
    B = cert["useful_minimum"]
    require(type(B) is int and B > 0, "useful budget")
    u, vcol = cert["projection_basis"]
    require(len(u) == len(vcol) == 2, "basis dimensions")
    require(all((3*d*z[1]-z[0]) % P == 0 for z in [u,vcol]), "basis membership")
    require(u[0]*vcol[1]-vcol[0]*u[1] == P, "basis determinant/index")
    jmax = ((P*L+2*d)*B)//T
    require(0 < u[0] == jmax, "positive projection range")
    transverse_num = abs(u[0])*B + abs(u[1])*jmax
    require(transverse_num < P, "transverse integer must be zero")
    require(cert["useful_projection"] == u, "unique useful projected pair")
    ph = phase(k,h,d,P,ps,es,*u)
    require(ph == cert["useful_phase"], "useful affine phase")
    prev, curr = capacity(k,ps,es,ph,B-1), capacity(k,ps,es,ph,B)
    prev_target_max = ph["beta"] + k*prev["source_nmax"]
    require(prev_target_max < prev["L"], "previous-budget exclusion")
    require(curr["nlo"] == curr["nhi"], "unique affine n at first contact")
    n = curr["nlo"]
    deficit = ph["beta"] + k*n - curr["L"]
    require(deficit == 3 and es == [4,1,1,1], "small deficit equation")
    caps = [a-b for a,b in zip(curr["hi"],curr["lo"])]
    require(all(cap >= 3 for cap in caps), "deficit upper caps")
    negative = []
    # 4*d7+d11+d59+d4691=3 forces d7=0; these are all solutions.
    for a in range(4):
        for b in range(4-a):
            ds = [0,a,b,3-a-b]
            ys = [low+delta for low,delta in zip(curr["lo"],ds)]
            x = lift(k,ps,ph,n,ys)
            require(dot(f,x) == 0 and dot(w,x) == -T*h*u[0], "optimizer original rows")
            require(max(map(abs,x)) == B, "optimizer norm")
            negative.append(x)
    all_opts = sorted(negative + [[-z for z in x] for x in negative])
    require(len({tuple(x) for x in all_opts}) == 20, "optimizer denominator")
    require(all_opts == sorted(cert["all_useful_optimizers"]), "complete optimizer list")

    # For j=1 (W=-D), every pivot is in the same residue class.
    pivot = pow(3*d, -1, P)
    if 2*pivot > P:
        pivot -= P
    M = abs(pivot)
    require(2*M < P, "unique minimal primitive pivot")
    require(M == cert["primitive_minimum"], "primitive lower bound")
    pp = phase(k,h,d,P,ps,es,1,pivot)
    require(pp == cert["negative_primitive_phase"], "primitive affine phase")
    x = cert["positive_primitive_witness"]
    require(dot(f,x) == 0 and dot(w,x) == T*h, "positive primitive witness")
    require(max(map(abs,x)) == M, "primitive witness norm")
    # A complete parametrization is pp with es.y=beta+k*n and
    # every original coordinate between -M and M, followed by negation.
    # Verify a particular solution and the four free integer directions.
    ys = [0,pp["beta"],0,0]
    base = lift(k,ps,pp,0,ys)
    directions = [[2*k,3,0,ps[1]*k,0,0,0],
                  [0,0,ps[0],-ps[1]*es[0],0,0,0],
                  [0,0,0,-ps[1],ps[2],0,0],
                  [0,0,0,-ps[1],0,ps[3],0]]
    require(dot(f,base) == 0 and dot(w,base) == -T*h, "primitive affine origin")
    require(all(dot(f,z) == dot(w,z) == 0 for z in directions), "primitive affine directions")
    primitive_caps = capacity(k,ps,es,pp,M)
    return dict(status="PASS",scope="exact finite k=47 certificate, no infinite-family inference",
                k=k,c=c,ordered_primes=primes,f_row=f,w_row=w,image_generator=T*h,
                primality="exhaustive odd trial division through integer square root",
                useful_minimum=B,useful_projection_negative_W=u,
                previous_budget=B-1,previous_target_max=prev_target_max,
                previous_weighted_lower=prev["L"],first_contact_n=n,deficit=deficit,
                all_useful_optimizer_count=20,all_useful_optimizers=all_opts,
                primitive_minimum=M,positive_primitive_witness=x,
                negative_primitive_phase=pp,primitive_parameter_bounds=primitive_caps,
                primitive_optimizer_description="All negatives of phase lifts with 4*y7+y11+y59+y4691=29+47*n and every original coordinate bounded by primitive_minimum.",
                primitive_optimizer_count="not computed or claimed")

def self_test(cert):
    mutations = [
        ("wrong_k", lambda c: c.__setitem__("k",49)),
        ("wrong_factor", lambda c: c["factorization"][0].__setitem__(1,3)),
        ("wrong_original_row", lambda c: c["f_row"].__setitem__(0,2)),
        ("wrong_image", lambda c: c.__setitem__("image_generator",c["image_generator"]+1)),
        ("wrong_basis", lambda c: c["projection_basis"][0].__setitem__(1,c["projection_basis"][0][1]+1)),
        ("wrong_budget", lambda c: c.__setitem__("useful_minimum",c["useful_minimum"]-1)),
        ("wrong_affine_residue", lambda c: c["useful_phase"]["residues"].__setitem__(0,0)),
        ("missing_optimizer", lambda c: c["all_useful_optimizers"].pop()),
        ("wrong_primitive_budget", lambda c: c.__setitem__("primitive_minimum",c["primitive_minimum"]-1)),
        ("wrong_primitive_sign", lambda c: c.__setitem__("positive_primitive_witness",[-x for x in c["positive_primitive_witness"]])),
    ]
    rejected=[]
    for name,mutation in mutations:
        altered=copy.deepcopy(cert)
        mutation(altered)
        try:
            verify(altered)
        except CertificateError:
            rejected.append(name)
        else:
            raise CertificateError("tampered certificate accepted: "+name)
    return rejected

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--certificate",type=Path,default=Path(__file__).with_name("k47_certificate.json"))
    parser.add_argument("--self-test",action="store_true",help="also reject ten semantic corruptions")
    args=parser.parse_args()
    try:
        cert=json.loads(args.certificate.read_text(encoding="utf-8"))
        result=verify(cert)
        if args.self_test:
            result["rejected_corruptions"]=self_test(cert)
    except (OSError,ValueError,KeyError,TypeError,IndexError) as exc:
        print(json.dumps(dict(status="FAIL",error=str(exc)),sort_keys=True))
        return 1
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())


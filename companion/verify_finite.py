"""Exact original-coordinate minima and positive spectral certificates.

Python standard library only. No network or private research inputs.
Finite certificate checks do not prove infinite separation.
"""
from copy import deepcopy
from fractions import Fraction as Q
from itertools import combinations, product
from math import gcd, prod
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
COUNTS = {}
def need(ok, message):
    if not ok:
        raise ValueError(message)
def count(key, n=1):
    COUNTS[key] = COUNTS.get(key, 0) + n
def integer(a, name, minimum=None):
    need(type(a) is int and (minimum is None or a >= minimum), name)
    return a
def sequence(a, name, size=None, nonempty=False):
    need(type(a) is list and (size is None or len(a) == size)
         and (not nonempty or len(a) > 0), name)
    return a
def ints(a, name, size=None, minimum=None):
    sequence(a, name, size)
    for v in a:
        integer(v, name, minimum)
    return a
def exact_numbers(a):
    # JSON booleans compare equal to 0/1 in Python; floats can compare equal
    # to integers too. Neither is an exact integer certificate field.
    need(type(a) not in (bool, float), "certificate numbers must be integers")
    if isinstance(a, dict):
        for v in a.values():
            exact_numbers(v)
    elif isinstance(a, list):
        for v in a:
            exact_numbers(v)
def rat(a):
    ints(a, "rational pair", 2)
    need(a[1] > 0, "positive rational denominator")
    return Q(*a)
def ceil(a):
    a = Q(a)
    return -((-a.numerator)//a.denominator)
def center(a, p):
    r = a % p
    return r-p if 2*r > p else r
def pack(a):
    a = Q(a)
    return [a.numerator, a.denominator]

def inputs(name):
    return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))

def certified_primes(nodes):
    # Complete p-1 order certificate, checked bottom-up rather than recursively.
    sequence(nodes, "nonempty prime certificates", nonempty=True)
    exact_numbers(nodes)
    for n in nodes:
        integer(n["p"], "prime integer", 2)
    known = set()
    need(len(nodes) == len({n["p"] for n in nodes}), "duplicate prime")
    for n in sorted(nodes, key=lambda a:a["p"]):
        p = n["p"]
        if p == 2:
            need(n == {"p":2}, "prime base")
        else:
            fs = n["factors"]
            factor_pairs(fs)
            need(p > 2 and all(q in known and e > 0 for q,e in fs), "prime predecessor")
            need(len(fs) == len({q for q,e in fs}) and prod(q**e for q,e in fs) == p-1,
                 "prime predecessor product")
            a = n["a"]
            integer(a, "prime order witness", 2)
            need(1 < a < p and pow(a,p-1,p) == 1, "prime Fermat/order")
            need(all(gcd(pow(a,(p-1)//q,p)-1,p) == 1 for q,e in fs), "prime full order")
        known.add(p)
    return known

def factor_pairs(fs):
    sequence(fs, "nonempty factorization", nonempty=True)
    for pair in fs:
        ints(pair, "factor pair", 2, 1)
        need(pair[0] >= 2, "factor prime")

def row(n, fs, known):
    integer(n, "row integer", 2)
    factor_pairs(fs)
    need(fs == sorted(fs) and len(fs) == len({p for p,e in fs}), "factor order")
    need(all(p in known and e > 0 for p,e in fs) and prod(p**e for p,e in fs) == n,
         "factor product")
    a = [n*e//p for p,e in fs]
    g = gcd(*a)
    periods = [p//gcd(p,e) for p,e in fs]
    R = prod(periods)
    weights = []
    for ai, ell in zip(a,periods):
        need(ai % (g*(R//ell)) == 0, "row normalization")
        weights.append(ai//(g*(R//ell)))
    return dict(n=n,fs=fs,a=a,g=g,ell=periods,R=R,weights=weights,S=sum(a))

def phases(ro, T, anchor):
    integer(anchor, "anchor index", 0)
    need(anchor < len(ro["a"]), "anchor index")
    need(T % ro["g"] == 0 and ro["weights"][anchor] == 1, "unit anchor/image")
    return [(p, center((T//ro["g"])*pow(ai//ro["g"],-1,p),p))
            for i,((p,e),ai,ell) in enumerate(zip(ro["fs"],ro["a"],ro["ell"]))
            if i != anchor and ell > 1]

def model(c, known):
    exact_numbers({key:c[key] for key in ("input","Delta","mu","phases")})
    ob = c["input"]
    x,N = ob["x"],ob["N"]
    integer(x, "base", 2)
    integer(N, "exponent", 1)
    ints(ob["anchors"], "two anchor indices", 2, 0)
    rx = row(x,ob["factors_x"],known)
    rb = row(x**N-1,ob["factors_b"],known)
    C = N*x**(N-1)
    delta = rx["g"]*rb["g"]//gcd(rb["g"],C*rx["g"])
    # Recover W image directly from full original F,W row minors.
    f = [-C*a for a in rx["a"]]+rb["a"]
    w = [0]*len(rx["a"])+rb["a"]
    image = gcd(*(abs(f[i]*w[j]-f[j]*w[i]) for i,j in combinations(range(len(f)),2)))//gcd(*f)
    need(image == C*delta, "original image")
    mu = max(Q(delta,rx["S"]),Q(C*delta,rb["S"]))
    ph = phases(rx,delta,ob["anchors"][0])+phases(rb,C*delta,ob["anchors"][1])
    need(c["Delta"] == delta and rat(c["mu"]) == mu and c["phases"] == [list(v) for v in ph],
         "input phase reconstruction")
    return rx,rb,C,delta,mu,ph

def admissible_indices(ph, mu, B, H, box):
    # Cover the entire (u,z) lattice rectangle. No delivered point list is used.
    integer(B, "integer phase budget", 0)
    integer(H, "integer index horizon", 0)
    j = box["pivot"]
    integer(j, "pivot index", 0)
    need(j < len(ph), "pivot index")
    sequence(box["basis"], "two lattice basis vectors", 2)
    for v in box["basis"]:
        ints(v, "lattice basis dimension", 2)
    p,k = ph[j]
    (q,r),(s,t) = box["basis"]
    need(q > 0 and q*t-s*r == p and p > 2*B, "pivot lattice determinant/width")
    need((q*k-r) % p == 0 and (s*k-t) % p == 0, "pivot lattice congruence")
    # Invert (u,z) -> v=(q*z-r*u)/p over all rectangle corners.
    corners = [Q(q*z-r*u,p) for u in (1,H) for z in (-B,B)]
    vmin,vmax = ceil(min(corners)),max(corners).__floor__()
    need(vmax-vmin < 10000, "bounded enumeration contract")
    found = []
    candidates = []
    for v in range(vmin,vmax+1):
        lo,hi = ceil(Q(1-s*v,q)),(H-s*v)//q
        if r:
            ends = [Q(z-t*v,r) for z in (-B,B)]
            lo,hi = max(lo,ceil(min(ends))),min(hi,max(ends).__floor__())
        elif not -B <= t*v <= B:
            continue
        need(hi-lo < 10000, "bounded row contract")
        for a in range(lo,hi+1):
            u,z = q*a+s*v,r*a+t*v
            candidates.append(u)
            if all(abs(center(u*k,p)) <= B for p,k in ph):
                found.append(u)
    need(len(candidates) == len(set(candidates)), "unique lattice indices")
    count("independent_pivot_candidates",len(candidates))
    return sorted(found)

def bounded_row(ro, T, B):
    # Solve the original coordinate cube through all normalized periods.
    if T % ro["g"]:
        return False,None
    rr = [center((T//ro["g"])*pow(a//ro["g"],-1,m),m) if m>1 else 0
          for a,m in zip(ro["a"],ro["ell"])]
    intervals = [(ceil(Q(-B-r,m)),(B-r)//m) for r,m in zip(rr,ro["ell"])]
    if any(lo>hi for lo,hi in intervals):
        return False,None
    numerator = T//ro["g"]-sum((a//ro["g"])*r for a,r in zip(ro["a"],rr))
    need(numerator % ro["R"] == 0, "fibre carry integrality")
    target = numerator//ro["R"]
    need(set(ro["weights"]) <= {1,2}, "declared one/two weight domain")
    lower = sum(w*lo for w,(lo,hi) in zip(ro["weights"],intervals))
    upper = sum(w*hi for w,(lo,hi) in zip(ro["weights"],intervals))
    flexible_one = any(w==1 and hi>lo for w,(lo,hi) in zip(ro["weights"],intervals))
    feasible = lower<=target<=upper and (flexible_one or (target-lower)%2==0)
    return feasible,dict(target=target,lower=lower,upper=upper,
                         deficit=max(lower-target,target-upper,0))

def vector(ro, T, z, B):
    ints(z, "vector dimension", len(ro["a"]))
    integer(B, "integer norm budget", 0)
    need(sum(a*v for a,v in zip(ro["a"],z)) == T and max(map(abs,z))<=B,
         "original vector equation/budget")

def minimum(c, known):
    rx,rb,C,de,mu,ph = model(c,known)
    m,mp = c["m"],c["m_prim"]
    integer(m, "positive useful minimum", 1)
    integer(mp, "positive primitive minimum", 1)
    u = c["useful_upper"]["winner"]["u"]
    integer(u, "positive useful image index", 1)
    vector(rx,u*de,c["useful_upper"]["winner"]["zx"],m)
    vector(rb,u*C*de,c["useful_upper"]["winner"]["zb"],m)
    W = sum(a*z for a,z in zip(rb["a"],c["useful_upper"]["winner"]["zb"]))
    need(W == u*C*de and W != 0, "original useful nonzero W")
    need(max(map(abs,c["useful_upper"]["winner"]["zx"]+c["useful_upper"]["winner"]["zb"])) == m,
         "useful attained norm")
    lower = admissible_indices(ph,mu,m-1,(m-1)//mu,c["useful_lower"]["phase_box"])
    rejected = []
    for j in lower:
        goodx,detailx = bounded_row(rx,j*de,m-1)
        goodb,detailb = bounded_row(rb,j*C*de,m-1)
        need(not (goodx and goodb), "smaller original norm exists")
        rejected.append(dict(u=j,source=detailx,target=detailb))
    G = max([mu]+[abs(k) for p,k in ph])
    need(ceil(G) == mp, "primitive necessary lower")
    vector(rx,de,c["primitive_vector"]["zx"],mp)
    vector(rb,C*de,c["primitive_vector"]["zb"],mp)
    tau = rat(c["return"]["tau"])
    integer(c["return"]["u"], "positive return index", 1)
    h = max([mu*c["return"]["u"]]+[abs(center(c["return"]["u"]*k,p)) for p,k in ph])
    need(h == tau and rat(c["return"]["G"]) == G, "return attained")
    need(not admissible_indices(ph,mu,ceil(tau)-1,ceil(tau/mu)-1,c["return"]["lower"]),
         "smaller return exists")
    need(prod(p for p,e in rx["fs"])*prod(p for p,e in rb["fs"]) < rb["n"]+1,
         "radical-small triple")
    return dict(x=c["input"]["x"],N=c["input"]["N"],Delta=de,u=u,
                m=m,m_prim=mp,ratio=pack(Q(mp,m)),tau=pack(tau),
                source_zero_period=rx["R"]//rx["fs"][c["input"]["anchors"][0]][0],
                original_lower_survivors=lower,rejected_fibres=rejected)

def kernel(L,t):
    a = abs(t-Q((2*t.numerator+t.denominator)//(2*t.denominator)))
    if not a:
        return Q(1)
    d = abs(L*a-Q((2*(L*a).numerator+(L*a).denominator)//(2*(L*a).denominator)))
    y = d*d
    s = 1-Q(5,3)*y+Q(5,6)*y*y-Q(25,126)*y*y*y
    return max(Q(0),1-Q(10,3)*(L*L-1)*a*a,(d*s/(L*a))**2)

def exact_energy(ph,H,ls):
    # Literal time-domain sum, entirely separate from frequency certification.
    sequence(ls, "energy lengths", len(ph))
    integer(H, "energy horizon", 0)
    M = H+1
    acc = 0
    for u in range(1,M):
        acc += (M-u)*prod(max(0,L-abs(center(u*k,p))) for (p,k),L in zip(ph,ls))
    return 1+Q(2*acc,M*prod(ls))

def witness_coordinates(c, required):
    witness = c["witness"]
    primes = ints(witness["primes"], "witness prime coordinates", len(required), 2)
    zs = ints(witness["z"], "witness coordinate dimension", len(required))
    need(len(set(primes)) == len(primes) and set(primes) == set(required),
         "witness prime support")
    integer(witness["u"], "positive spectral index", 1)
    integer(witness["norm"], "positive spectral norm", 1)
    return dict(zip(primes,zs))

def spectral_original(c, ob, known):
    exact_numbers(c)
    exact_numbers(ob)
    need(ob["kind"] in ("variable_base", "fixed_power"), "spectral input kind")
    need(c["B"] == ob["budget"] and c["id"] == ob["id"], "spectral input budget")
    if ob["kind"] == "variable_base":
        x,N = ob["x"],ob["N"]
        integer(x, "base", 2)
        integer(N, "exponent", 1)
        ints(ob["anchors"], "two anchor indices", 2, 0)
        rx = row(x,ob["factors_x"],known)
        rb = row(x**N-1,ob["factors_b"],known)
        C = N*x**(N-1)
        delta = rx["g"]*rb["g"]//gcd(rb["g"],C*rx["g"])
        mu = max(Q(delta,rx["S"]),Q(C*delta,rb["S"]))
        ph = phases(rx,delta,ob["anchors"][0])+phases(rb,C*delta,ob["anchors"][1])
        image = C*delta
        zz = witness_coordinates(c, [p for p,e in rx["fs"]+rb["fs"]])
        u = c["witness"]["u"]
        vector(rx,u*delta,[zz[p] for p,e in rx["fs"]],c["witness"]["norm"])
        vector(rb,u*image,[zz[p] for p,e in rb["fs"]],c["witness"]["norm"])
        W = sum(a*zz[p] for a,(p,e) in zip(rb["a"],rb["fs"]))
    else:
        k,s = ob["k"],ob["s"]
        integer(k, "fixed-power exponent", 1)
        integer(s, "fixed-power pivot", 2)
        n = 3**k+2
        rb = row(n,ob["factors"],known)
        active = [(p,e) for p,e in rb["fs"] if p!=s and e%p]
        A = prod(p for p,e in active)
        d = n//(s*A)
        need(n == d*s*A, "fixed_power native cofactor")
        mu = Q(d)
        ph = [(p,center(pow(3*s*e*(A//p),-1,p),p)) for p,e in active]
        image = 3**(k-1)*d
        zz = witness_coordinates(c, [2,3]+[p for p,e in rb["fs"]])
        Da,Db = zz[2],k*3**(k-1)*zz[3]
        Dc = sum(a*zz[p] for a,(p,e) in zip(rb["a"],rb["fs"]))
        need(Da+Db == Dc, "fixed_power original F")
        W = 2*Db-3**k*Da
        need(W == -6*c["witness"]["u"]*image, "fixed_power nonzero image index")
    need(mu == rat(c["mu"]) and image == c["image"] and [list(z) for z in ph]==c["phases"],
         "spectral original image/phases")
    need([list(z) for z in ph if z[0]//2>c["B"]] == c["restrictive"], "all unpaid phases retained")
    need(c["H"] == c["B"]//mu and mu*c["H"]<=c["B"], "spectral drift paid")
    need(c["witness"]["u"]>0 and W==c["witness"]["W"] and W!=0, "original nonzero W")
    need(max(map(abs,c["witness"]["z"]))==c["witness"]["norm"]<=c["full_norm_bound"],
         "full original spectral witness")

def spectrum(c):
    exact_numbers(c)
    ph = c["restrictive"]
    # The displayed axis-ceiling formula is specifically for two phases.
    sequence(ph, "two restrictive phases", 2)
    for phase in ph:
        ints(phase, "phase pair", 2)
        need(phase[0] > 2, "phase modulus")
    need(len({p for p,k in ph}) == len(ph), "distinct phase moduli")
    H,M,ls = c["H"],c["H"]+1,c["lengths"]
    integer(H, "positive spectral horizon", 1)
    integer(c["B"], "positive spectral budget", 1)
    ints(ls, "spectral length dimension", len(ph), 1)
    need(all(L <= c["B"]+1 for L in ls), "spectral support within budget")
    need(all(p>2*L for (p,k),L in zip(ph,ls)), "nonwrapped interval energy domain")
    A = prod(p for p,k in ph)
    native = c["native"]
    need(native["A"] == A and gcd(native["V"],A)==1, "native dual unit")
    weights,V = native["weights"],native["V"]
    ints(weights, "native weight dimension", len(ph))
    sequence(c["marginal_energy"], "marginal energy dimension", len(ph))
    for value in c["marginal_energy"]:
        rat(value)
    sequence(c["frequencies"], "nonempty frequencies", nonempty=True)
    for f in c["frequencies"]:
        ints(f["vector"], "frequency dimension", len(ph))
    need(all((w*(A//p)*k-V)%p==0 for (p,k),w in zip(ph,weights)), "native conservation")
    base = M*prod(Q(L,p) for (p,k),L in zip(ph,ls))
    labels=set()
    score=Q(0)
    mixed=0
    for f in c["frequencies"]:
        ms=f["vector"]
        label=sum(m*k*(A//p) for m,(p,k) in zip(ms,ph))%A
        need(label not in labels and all((label*w*pow(V,-1,p)-m)%p==0
             for m,w,(p,k) in zip(ms,weights,ph)), "native dual distinct inverse")
        labels.add(label)
        term = kernel(M,sum((Q(m*k,p) for m,(p,k) in zip(ms,ph)),Q(0)))
        term *= prod(kernel(L,Q(m,p)) for m,(p,k),L in zip(ms,ph,ls))
        need(term==rat(f["mass"]), "frequency mass")
        score += base*term
        mixed += sum(m%p != 0 for m,(p,k) in zip(ms,ph))==2
    need(score==rat(c["score"]) and score>rat(c["strict_score_lower"])>1, "strict spectral mass")
    energies=[exact_energy([phase],H,[L]) for phase,L in zip(ph,ls)]
    full=exact_energy(ph,H,ls)
    axes=Q(ls[1],ph[1][0])*energies[0]+Q(ls[0],ph[0][0])*energies[1]-base
    need(full==rat(c["full_energy"]) and axes==rat(c["axis_ceiling"])<1, "direct energy/axis ceiling")
    need(all(e==rat(z) for e,z in zip(energies,c["marginal_energy"])), "direct marginal energies")
    # Per-budget necessary explicit term count, even using exact kernels.
    necessary_terms = (1/base).__floor__()+1
    return dict(id=c["id"],H=H,B=c["B"],frequencies=len(labels),mixed_frequencies=mixed,
                score=pack(score),score_lower=c["strict_score_lower"],
                direct_full_energy=pack(full),axis_ceiling=pack(axes),
                necessary_explicit_terms=necessary_terms)

def cube_controls():
    known=certified_primes([{"p":2},{"p":3,"factors":[[2,1]],"a":2},
        {"p":5,"factors":[[2,2]],"a":2},{"p":7,"factors":[[2,1],[3,1]],"a":3}])
    for n,fs in [(6,[[2,1],[3,1]]),(12,[[2,2],[3,1]]),(18,[[2,1],[3,2]]),
                 (49,[[7,2]]),(35,[[5,1],[7,1]])]:
        ro=row(n,fs,known)
        for B in range(3):
            actual={sum(a*z for a,z in zip(ro["a"],zs))
                    for zs in product(range(-B,B+1),repeat=len(fs))}
            for T in range(-B*ro["S"]-1,B*ro["S"]+2):
                need(bounded_row(ro,T,B)[0] == (T in actual), "literal cube cross-control")
                count("literal_original_cube_targets")

def case_index(cases, name):
    sequence(cases, "nonempty "+name, nonempty=True)
    ids = [c["id"] for c in cases]
    need(all(type(i) is str and i for i in ids) and len(set(ids)) == len(ids),
         "unique "+name+" ids")
    return dict(zip(ids,cases))

def spectral_pairs(cases, observations):
    indexed = case_index(cases, "spectral certificates")
    original = case_index(observations, "spectral inputs")
    need(len(cases) == len(observations) and indexed.keys() == original.keys(),
         "spectral case coverage")
    return [(c,original[c["id"]]) for c in cases]

def main():
    COUNTS.clear()
    known=certified_primes(inputs("minima_primes.json"))
    cases=inputs("exact_minima.json")
    sequence(cases, "nonempty exact minima", nonempty=True)
    case_index([c["input"] for c in cases], "exact minima")
    exact=[minimum(c,known) for c in cases]
    spectral_cases = inputs("spectral_certificates.json")
    spectral_inputs = inputs("spectral_inputs.json")
    spectral_primes = certified_primes(inputs("spectral_primes.json"))
    for c,ob in spectral_pairs(spectral_cases,spectral_inputs):
        spectral_original(c,ob,spectral_primes)
    spectral=[spectrum(c) for c in spectral_cases]
    cube_controls()
    rejected=[]
    for label,edit in [
        ("understated useful minimum",lambda c:c.update(m=c["m"]-1)),
        ("inflated primitive minimum",lambda c:c.update(m_prim=c["m_prim"]+1)),
        ("wrong original image",lambda c:c.update(Delta=c["Delta"]+1)),
        ("wrong original useful coordinate",lambda c:c["useful_upper"]["winner"]["zb"].__setitem__(0,0)),
        ("wrong phase congruence",lambda c:c["phases"][0].__setitem__(1,0)),
        ("invalid pivot lattice",lambda c:c["useful_lower"]["phase_box"]["basis"][0].__setitem__(0,1))]:
        c=deepcopy(cases[0]);edit(c)
        try:
            minimum(c,known)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("negative control accepted: "+label)
    # First-wrap filter is substantive: large initial phase with no useful return.
    p,k,mu=97,4,Q(1)
    tau=min(max(mu*u,abs(center(k*u,p))) for u in range(1,p+1))
    need(tau==k and min(Q(k),mu*p/(k+mu))==k, "first-wrap negative model")
    need(exact[0]["u"] % exact[0]["source_zero_period"] != 0,
         "new witness should escape old zero section")
    need(admissible_indices([(11,2)],Q(7,2),3,1,
         dict(pivot=0,basis=[[1,2],[0,11]])) == [1],
         "noninteger strict-return window must not round drift down to phase budget")
    count("recursive_prime_nodes",len(known))
    out=dict(status="PASS",scope="finite exact controls; no asymptotic or independent acceptance",
        counts=COUNTS,exact_minimum_pairs=exact,spectral_certificates=spectral,
        rejected_mutations=rejected,
        explicit_term_count_condition="Each positive explicit-frequency certificate requires T>1/(M product(L_i/p_i)); all phases retained or separately paid.")
    print(json.dumps(out,sort_keys=True,indent=2))
    return 0
if __name__=="__main__":
    raise SystemExit(main())


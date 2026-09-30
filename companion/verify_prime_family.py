"""Literal original-cube and boundary controls for the prime-family theorem."""
from fractions import Fraction as F
from itertools import combinations
from math import gcd, isqrt, prod
import json

def need(ok,msg):
    if not ok:raise ValueError(msg)
def factor(n):
    fs={};p=2
    while p*p<=n:
        while n%p==0:fs[p]=fs.get(p,0)+1;n//=p
        p+=1
    if n>1:fs[n]=1
    return fs
def center(a,p):
    a%=p
    return a-p if 2*a>p else a
def row(n,fs):return {p:n*e//p for p,e in fs.items()}
def rgcd(a):return gcd(*a.values())
def image(f,w):return gcd(*(abs(f[i]*w[j]-f[j]*w[i]) for i,j in combinations(range(len(f)),2)))//gcd(*f)
def values(coeff,B):
    out={0}
    for a in coeff:out={v+a*z for v in out for z in range(-B,B+1)}
    return out

def prime_gap():
    cases=[];pivots=0;exceptions=[]
    for q in range(3,200,2):
        if factor(q)!={q:1}:continue
        c=q+2;fs=factor(c);sim=[p for p,e in fs.items() if e==1]
        if not sim:exceptions.append(q);continue
        coeff=row(c,fs);D=image([1,1]+[-a for a in coeff.values()],[-q,2]+[0]*len(coeff))
        R=prod(p for p,e in fs.items() if e%p)
        need(D==c//R,'image formula')
        if fs=={c:1}:
            B=(q+1)//2;vs=[{c:-B}];kind='prime'
        else:
            B=(q-D)//2;vs=[];kind='composite_simple'
            for ell in sim:
                L=(1-R)//2;v={p:0 for p in fs}
                for p,e in fs.items():
                    if p!=ell and e%p:v[p]=center(L*pow(R*e//p,-1,p),p)
                num=ell*(L-sum((R*e//p)*v[p] for p,e in fs.items() if p!=ell and e%p))
                need(num%R==0,'pivot integer');v[ell]=num//R;vs.append(v);pivots+=1
        zq=-(q-1)//2 if kind=='prime' else -B
        for v in vs:
            need(-1+zq==sum(coeff[p]*v[p] for p in fs),'original F')
            need(2*zq+q==D,'original W')
            need(max(1,abs(zq),*(abs(z) for z in v.values()))==B,'original norm')
        # Full target-block attainability and all source pairs below the claimed minimum.
        lower=B-1;attainable=values(coeff.values(),lower)
        for z2 in range(-lower,lower+1):
            if (D+q*z2)%2:continue
            zq0=(D+q*z2)//2
            need(abs(zq0)>lower or z2+zq0 not in attainable,'smaller original cube feasible')
        need(F(B)>=F(q-1,3),'linear lower')
        cases.append(dict(q=q,c=c,kind=kind,m=1,mprim=B,D=D))
    # Old exact formula cannot be applied to prime c or to arbitrary powerful c.
    need(values([1],1)=={-1,0,1} and -2 not in values([1],1),'prime boundary q3')
    need(-21 not in values([14],20),'powerful boundary q47 target')
    return dict(exact_original_minima=len(cases),all_simple_pivots=pivots,excluded_powerful_q=exceptions,cases=cases)

def firstwrap():
    primes=(3,5,7,11,13);count=ties=0
    for p,q in combinations(primes,2):
        for a in range(1,p//2+1):
            for b in range(1,q//2+1):
                for mu in (F(1,7),F(1,2),F(1),F(2),F(4)):
                    G=max(mu,a,b);last=int(G/mu)
                    tau=min(max(mu*u,abs(center(a*u,p)),abs(center(b*u,q))) for u in range(1,last+1))
                    if G==mu:cap=F(1)
                    else:
                        mods=[m for m,k in [(p,a),(q,b)] if k==G];pm=max(mods)
                        cap=max(F(1),G*(G+mu)/(mu*pm));ties+=len(mods)>1
                    need(G/tau<=cap,'actual-ratio normalized cap');count+=1
    return dict(abstract_phase_cases=count,maximal_phase_ties=ties)

if __name__ == '__main__':
    print(json.dumps(dict(status='PASS', prime_gap=prime_gap(), first_wrap=firstwrap(), scope='Finite controls; universal statements are proved in the manuscript.'), indent=2, sort_keys=True))

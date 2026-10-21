"""checks.py -- RCWA 계산 후 판정 줄 (A 결과 경계 / B 요청 대 실사용 / C 수렴 줄 / D 미러 fixture).

각 함수는 한 줄 `PASS|WARN|FAIL <이름>: ...` 을 print 하고 같은 문자열을 반환한다.
호출 규칙 (agents/research-compute.md 작업 3·5): 계산 뒤 A·B·C 를 실행해 판정 줄을 보고에 붙인다. 새 형상이면 D 도.
새 판정 논리가 아니라 meent_convergence.md / grcwa_convergence.md 의 기존 규칙을 출력으로 강제하는 것이다.
"""
import numpy as np


def _out(verdict, name, msg):
    line = f"{verdict} {name}: {msg}"
    print(line)
    return line


# ---------------------------------------------------------------- A
def result_bounds(R, T, eps, tol=0.0):
    """A. 유한값 · R,T >= 0 · 0 <= eps <= 1.  tol 은 근거 없으면 0(정확 경계).
    주의(실측): 무손실 구조(eps_true=0)는 1-R-T 가 -1e-16~-7e-16 roundoff 로 tol=0 에서 FAIL 이 난다 -> 무손실 검증은 tol=1e-12 지정.
    R+T+A=1 은 eps=1-R-T 정의라 검사하지 않는다 (항등식)."""
    R, T, eps = (np.atleast_1d(np.asarray(x, dtype=float)) for x in (R, T, eps))
    bad = []
    nonfinite = int((~np.isfinite(R) | ~np.isfinite(T) | ~np.isfinite(eps)).sum())
    if nonfinite:
        bad.append(f"nonfinite={nonfinite}")
    with np.errstate(invalid="ignore"):
        for nm, a, lo, hi in (("R", R, 0.0, None), ("T", T, 0.0, None), ("eps", eps, 0.0, 1.0)):
            n_lo = int((a < lo - tol).sum())
            if n_lo:
                bad.append(f"{nm}<{lo}: n={n_lo} min={np.nanmin(a):.6g}")
            if hi is not None:
                n_hi = int((a > hi + tol).sum())
                if n_hi:
                    bad.append(f"{nm}>{hi}: n={n_hi} max={np.nanmax(a):.6g}")
    rng = "R[{:.6g},{:.6g}] T[{:.6g},{:.6g}] eps[{:.6g},{:.6g}]".format(
        np.nanmin(R), np.nanmax(R), np.nanmin(T), np.nanmax(T), np.nanmin(eps), np.nanmax(eps)) \
        if np.isfinite(R).any() and np.isfinite(T).any() and np.isfinite(eps).any() else "all-nonfinite"
    if bad:
        return _out("FAIL", "bounds", "; ".join(bad) + f" | {rng} tol={tol}")
    return _out("PASS", "bounds", f"N={eps.size} {rng} tol={tol}")


# ---------------------------------------------------------------- B
def read_meent(mee, n_extra_layers=0):
    """meent mee 객체에서 solver 가 실제로 읽는 속성을 되읽는다 (소스 확인: _base.py 속성 + setter).
    theta=0 은 setter 가 perturbation(1e-20) 으로 바꿔 저장한다 -> used 에 그대로 나타남.
    N_z = ucell 층 수 - n_extra_layers (예: 기판 층 1).  pol: 0=TE, 1=TM."""
    fto = mee.fto
    d = dict(fto=int(fto[0]), fto_y=int(fto[1]),
             theta_deg=float(np.degrees(np.real(mee.theta))),
             pol=float(mee.pol), wavelength=float(np.real(np.asarray(mee.wavelength)).ravel()[0]),
             period_x=float(np.asarray(mee.period).ravel()[0]))
    if getattr(mee, "ucell", None) is not None:
        d["N_z"] = int(mee.ucell.shape[0]) - n_extra_layers
    return d


def read_grcwa(obj):
    """grcwa obj 에서 되읽기. Init_Setup() 과 MakeExcitationPlanewave() 호출 뒤에 불러야 한다.
    nG: Init_Setup 이 Lattice_getG 결과로 obj.nG 를 실제 유지 개수로 덮어씀 (실측, 1D L=7.3 λ=3: 생성자 nG 5..59 전부 실사용 < 요청, 예 11->9, 35->31, 40->39 — 고정점 없음).
    -> 요청 dict 의 nG 에는 '생성자 목표치'가 아니라 보고·캐시 키로 쓸 값(= Init_Setup 뒤 obj.nG)을 넣는다. 목표치를 넣으면 FAIL 이 정상(실사용 값으로 기록하라는 신호).
    pol: a0[0]=-s*cos(theta)  a0[nG]=p (phi=0, forward, order 0 일 때) 에서 TM 비율 복원.
    N_z 는 grcwa 에 고유 개념이 없다(층 구성은 호출자 정의) -> Layer_N 과 thickness_list 를 돌려준다."""
    d = dict(nG=int(obj.nG), theta_deg=float(np.degrees(np.real(obj.theta))),
             wavelength=float(1.0 / np.real(obj.freq)), period_x=float(obj.L1[0]),
             n_layers=int(obj.Layer_N))
    if float(np.real(obj.phi)) == 0.0 and getattr(obj, "direction", "forward") == "forward" and hasattr(obj, "a0"):
        s = -obj.a0[0] / np.cos(obj.theta)
        p = obj.a0[obj.nG]
        d["pol"] = float(abs(p) ** 2 / (abs(p) ** 2 + abs(s) ** 2))
    return d


def read_torcwa(r):
    """torcwa rcwa 객체 되읽기 (소스 읽기 근거: torcwa 0.1.4.2 rcwa.py. 이 환경은 torch DLL 오류로 실행 미검증).
    order=[fto,0], inc_ang(rad), dtype(잘못된 dtype 은 warn 후 complex64 로 조용히 대체), layer_N, L."""
    d = dict(fto=int(r.order[0]), fto_y=int(r.order[1]), dtype=str(r._dtype), n_layers=int(r.layer_N),
             period_x=float(complex(r.L[0]).real))
    if hasattr(r, "inc_ang"):
        d["theta_deg"] = float(np.degrees(r.inc_ang.real.item()))
    return d


_INT_KEYS = {"fto", "fto_y", "nG", "N_z", "n_layers"}


def _norm_pol(v):
    if isinstance(v, str):
        return {"TE": 0.0, "S": 0.0, "TM": 1.0, "P": 1.0}[v.upper()]
    return float(v)


def requested_vs_used(requested, used, rtol=1e-12, atol=1e-12):
    """B. 요청 dict 의 키마다 used(read_* 반환) 값과 비교. 다르면 FAIL. 키가 used 에 없으면 FAIL(되읽기 불가 = 미검증).
    정수 키(fto, fto_y, nG, N_z, n_layers)는 정확 일치. 실수(theta_deg, wavelength, pol ...)는 |diff| <= atol + rtol*|req|
    (기본 1e-12 = 단위 변환 roundoff 수준, 물리 허용오차 아님; 인자로 조정).
    pol 은 'TE'/'TM'/0/1 (TM 비율)."""
    bad, ok = [], []
    for k, rv in requested.items():
        if k not in used:
            bad.append(f"{k}: used 에서 되읽기 불가")
            continue
        uv = used[k]
        if k == "pol":
            rv = _norm_pol(rv)
        if isinstance(rv, str) or isinstance(uv, str):
            same = str(rv) == str(uv)
        elif k in _INT_KEYS:
            same = int(rv) == int(uv)
        else:
            same = abs(float(uv) - float(rv)) <= atol + rtol * abs(float(rv))
        (ok if same else bad).append(f"{k}={uv}" if same else f"{k}: req={rv} used={uv}")
    if bad:
        return _out("FAIL", "used", "; ".join(bad))
    return _out("PASS", "used", ", ".join(ok))


# ---------------------------------------------------------------- C
def convergence_line(path, tol, cap=None, blas_spread=None):
    """C. path = 이미 계산된 step 목록, 각 step = dict(fto, N_z, eps, eps_fto_probe, eps_Nz_probe)
    (meent_convergence: probe = 해당 축 x1.5 한 점; s_fto = eps(fto*1.5,N_z)-eps(P), s_Nz 동일).
    grcwa 는 nG 를 fto 자리에 넣고 probe 배율만 다름 (|s| 정의 동일).
    축별 종료 (meent_convergence.md 종료 규칙):
      tol       |s| <= tol 이 마지막 2 step 연속
      saturated |s| 최소값이 최근 3 step 갱신 없음 (tol 미달 상태로 멈춤 = 노이즈바닥 > tol)
      cap       위 둘 다 아님 (발산 상한/미수렴).  cap=dict(fto=.., N_z=..) 를 주면 마지막 step 이 상한에 닿았는지도 표기.
    전체 stop = 두 축 중 나쁜 쪽 (cap > saturated > tol).  PASS=tol, WARN=saturated, FAIL=cap.
    ★ 같은 방법의 BLAS spread 일치만으로는 수렴이 아니다 -> 이 함수는 spread 로 PASS 를 만들지 않는다.
      blas_spread(grcwa gate)를 주면 > 0.01 일 때 FAIL 만 추가(grcwa_convergence §2)."""
    if len(path) < 1:
        return _out("FAIL", "converge", "path 없음")
    s_f = [p["eps_fto_probe"] - p["eps"] for p in path]
    s_z = [p["eps_Nz_probe"] - p["eps"] for p in path]

    def stop_of(s):
        a = np.abs(np.asarray(s, dtype=float))
        if not np.all(np.isfinite(a)):
            return "cap"
        if len(a) >= 2 and a[-1] <= tol and a[-2] <= tol:
            return "tol"
        if len(a) >= 4 and a[-3:].min() >= a[:-3].min():
            return "saturated"
        return "cap"

    rank = {"tol": 0, "saturated": 1, "cap": 2}
    stops = (stop_of(s_f), stop_of(s_z))
    stop = max(stops, key=rank.get)
    last = path[-1]
    extra = ""
    if cap:
        hit = [k for k in ("fto", "N_z") if k in cap and last[k] >= cap[k]]
        if hit:
            extra = f" at_cap={'+'.join(hit)}"
    line = (f"converge: s_fto={s_f[-1]:+.3g}, s_Nz={s_z[-1]:+.3g}, tol={tol:g}, stop={stop}"
            f" (axes fto={stops[0]} Nz={stops[1]}; steps={len(path)}; final fto={last['fto']} N_z={last['N_z']} eps={last['eps']:.6g}){extra}")
    verdict = {"tol": "PASS", "saturated": "WARN", "cap": "FAIL"}[stop]
    if blas_spread is not None and blas_spread > 0.01:
        verdict = "FAIL"
        line += f" blas_spread={blas_spread:.3g}>0.01 near-singular"
    line = f"{verdict} {line}"
    print(line)
    return line


# ---------------------------------------------------------------- D
def mirror_fixture(eps_plus, eps_minus, tol, theta_deg=None):
    """D. 새 형상 도입 시 필수 (첫 calibration, bare 구조).  대칭이어야 할 구조에서 eps(+theta) 와 eps(-theta) 비교.
    비대칭 구조(wedge 등)에는 쓰지 않는다 (±theta 가 물리적으로 다름).  차이가 tol 초과면 FAIL.
    tol 은 필수 인자 (그 형상·편광의 노이즈바닥 등 호출자 근거로 지정)."""
    ep, em = np.atleast_1d(np.asarray(eps_plus, dtype=float)), np.atleast_1d(np.asarray(eps_minus, dtype=float))
    d = np.abs(ep - em)
    th = "" if theta_deg is None else f" theta={np.atleast_1d(theta_deg).tolist()}"
    if not np.all(np.isfinite(d)):
        return _out("FAIL", "mirror", f"nonfinite eps{th}")
    verdict = "FAIL" if d.max() > tol else "PASS"
    return _out(verdict, "mirror", f"max|eps(+t)-eps(-t)|={d.max():.3g} tol={tol:g} N={d.size}{th}")


def mirror_fixture_run(solve, thetas_deg, tol):
    """D 편의: solve(theta_deg)->eps 를 ±theta 로 호출해 mirror_fixture 에 넘긴다."""
    thetas = list(thetas_deg)
    return mirror_fixture([solve(t) for t in thetas], [solve(-t) for t in thetas], tol, thetas)

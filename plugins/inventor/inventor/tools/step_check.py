"""Inventor 피처 단계 검증: 피처 하나마다 되읽은 체적·면 수 변화를 판정해 STEP 줄을 낸다.

근거(실측, 돌출은 references/inventor_ipt_modeling.md 「Extrude」):
- 방향이 틀린 HoleFeature 는 예외 없이 무동작(Volume·Faces 불변).
  MassProperties 는 캐시되므로 CacheResultsOnCompute=False 로 되읽어야 한다.
- 돌출: 체적만으로는 base extrude 방향 반전을 못 잡는다 -> RangeBox 대조.
- 평면·단일 원통 단계는 1e-4 mm3 로 일치, 곡면-곡면 단계는
  MassProperties 가 7e-5 mm3 (2598 mm3 중, 약 3e-8 상대) 어긋남 -> 상대 1e-4 면 곡면도 통과.

단위: 전부 Inventor 데이터베이스 단위. Volume = cm3, RangeBox = cm.
before/after = (volume_cm3, faces[, (minx, miny, minz, maxx, maxy, maxz)]).
dV = after - before (부호 있음: 절삭은 음수). exp_dV_cm3 도 같은 부호로 준다.
"""

TOL_REL = 1e-4       # 이론 dV 대비 상대 허용 오차
TOL_ABS_CM3 = 1e-7   # 상대 허용이 너무 작아질 때의 하한 = 1e-4 mm3 (평면 단계 일치 수준)
NOOP_CM3 = 1e-9      # 이 미만이면 체적 불변으로 본다 (무동작 사례는 byte-identical)
BBOX_TOL_CM = 1e-3   # 0.01 mm. 곡면 RangeBox 가 0.003 mm 느슨했던 사례 + 여유


class StepResult:
    def __init__(self, status, line, reasons):
        self.status, self.line, self.reasons = status, line, reasons

    def __str__(self):
        return self.line


def _split(state):
    vol, faces = state[0], state[1]
    bbox = state[2] if len(state) > 2 else None
    return float(vol), int(faces), bbox


def step_check(name, before, after, exp_dV_cm3=None, tol=TOL_REL, abs_tol=TOL_ABS_CM3,
               exp_bbox=None, bbox_tol=BBOX_TOL_CM, echo=True):
    """피처 1개 판정. exp_bbox 는 base extrude 방향 확인용(after 의 RangeBox 와 비교)."""
    v0, f0, _ = _split(before)
    v1, f1, bb1 = _split(after)
    dV, dF = v1 - v0, f1 - f0
    fails = []

    if abs(dV) < NOOP_CM3 and dF == 0:
        fails.append("no-op (dV=0, dF=0)")
    if exp_dV_cm3 is not None and abs(dV - exp_dV_cm3) > max(tol * abs(exp_dV_cm3), abs_tol):
        fails.append("dV mismatch (err=%.3e cm3)" % (dV - exp_dV_cm3))
    if exp_bbox is not None:
        if bb1 is None:
            raise ValueError("exp_bbox 를 주려면 after 에 RangeBox 가 있어야 한다")
        worst = max(abs(a - b) for a, b in zip(bb1, exp_bbox))
        if worst > bbox_tol:
            fails.append("bbox mismatch (max err=%.4f cm)" % worst)

    if fails:
        status = "FAIL"
    elif exp_dV_cm3 is None:
        status, fails = "WARN", ["no theoretical dV"]
    else:
        status = "PASS"

    exp = "none" if exp_dV_cm3 is None else "%+.6f" % exp_dV_cm3
    line = "[STEP %s] %s dV=%+.6f dF=%+d exp=%s" % (status, name, dV, dF, exp)
    if fails:
        line += " | " + "; ".join(fails)
    if echo:
        print(line, flush=True)
    return StepResult(status, line, fails)


def step_summary(results):
    """보고용 요약 한 줄. FAIL 0 이어야 모델링 완료로 보고한다."""
    n = {s: sum(r.status == s for r in results) for s in ("PASS", "WARN", "FAIL")}
    return "STEP 요약: FAIL %d / WARN %d / PASS %d" % (n["FAIL"], n["WARN"], n["PASS"])


# ---- Inventor 되읽기 헬퍼 (COM 필요) ----

def read_volume_cm3(part_doc):
    """체적(cm3). MassProperties 를 매번 새로 얻고 CacheResultsOnCompute=False 를 먼저 설정."""
    mp = part_doc.ComponentDefinition.MassProperties
    mp.CacheResultsOnCompute = False
    return mp.Volume


def read_state(part_doc):
    """(Volume cm3, 전체 Faces.Count, RangeBox (cm)) — step_check 의 before/after 입력."""
    comp = part_doc.ComponentDefinition
    vol = read_volume_cm3(part_doc)
    bodies = comp.SurfaceBodies
    faces = sum(bodies.Item(i).Faces.Count for i in range(1, bodies.Count + 1))
    rb = comp.RangeBox
    lo, hi = rb.MinPoint, rb.MaxPoint
    return vol, faces, (lo.X, lo.Y, lo.Z, hi.X, hi.Y, hi.Z)

# SpaceClaim IronPython 진단 — .NET reflection

reflection = 1차 도구. KB 보다 빠르고 정확.

## Pattern 1 — 후보 클래스명 systematic 시도

```python
import codecs
OUT = r"C:\...\introspect.txt"
candidates = ["Revolve", "RevolveEdges", "RevolveFaces", "Pull", "Sweep", "SketchSpline", "NurbsCurve", "DesignCurve", "DatumLine"]
lines = []
for n in candidates:
    try: lines.append("OK  %s -> %s" % (n, type(eval(n)).__name__))
    except NameError: lines.append("NA  %s" % n)
f = codecs.open(OUT, "w", "utf-8"); f.write(u"\n".join(lines)); f.close()
```

## Pattern 2 — 메서드 시그니처

```python
import clr, codecs
OUT = r"C:\...\introspect.txt"
lines = []
for cls_name in ["RevolveEdges", "RevolveFaces", "NurbsCurve"]:
    clr_type = clr.GetClrType(eval(cls_name))
    lines.append("=== %s === %s" % (cls_name, clr_type.FullName))
    for m in clr_type.GetMethods():
        if m.IsStatic and not m.Name.startswith(("get_", "set_", "op_")):
            sig = ", ".join(["%s %s" % (p.ParameterType.Name, p.Name) for p in m.GetParameters()])
            lines.append("  %s %s(%s)" % (m.ReturnType.Name, m.Name, sig))
f = codecs.open(OUT, "w", "utf-8")
for ln in lines: f.write(unicode(ln) + u"\n")
f.close()
```

## Pattern 3 — 인스턴스 property dump (default 포함)

```python
import clr, codecs
inst = SomeClass.Create()
clr_type = clr.GetClrType(type(inst))
lines = ["=== R/W properties ==="]
for p in clr_type.GetProperties():
    if p.CanRead and p.CanWrite:
        try: lines.append("%s : %s = %s" % (p.Name, p.PropertyType.Name, p.GetValue(inst, None)))
        except: lines.append("%s : %s = <read fail>" % (p.Name, p.PropertyType.Name))
lines.append("\n=== Read-only properties ===")
for p in clr_type.GetProperties():
    if p.CanRead and not p.CanWrite: lines.append("%s : %s" % (p.Name, p.PropertyType.Name))
lines.append("\n=== Public methods ===")
for m in clr_type.GetMethods():
    if not m.Name.startswith(("get_", "set_", "op_")) and m.Name not in ("Equals", "GetHashCode", "GetType", "ToString"):
        sig = ", ".join(["%s %s" % (p.ParameterType.Name, p.Name) for p in m.GetParameters()])
        lines.append("  %s %s(%s)" % (m.ReturnType.Name, m.Name, sig))
f = codecs.open(OUT, "w", "utf-8")
for ln in lines: f.write(unicode(ln) + u"\n")
f.close()
```

## Pattern 4 — 로드된 assembly 검색

```python
import codecs, System
out = []
for a in System.AppDomain.CurrentDomain.GetAssemblies():
    n = a.GetName().Name
    if 'speos' in n.lower() or 'optis' in n.lower():
        out.append("ASM: " + n)
        try:
            for t in a.GetTypes():
                if 'parabolic' in t.FullName.lower(): out.append("  T: " + t.FullName)
        except: pass
f = codecs.open(OUT, "w", "utf-8"); f.write(u"\n".join(out)); f.close()
```

## 단계별 file log (필수)

```python
import codecs
LOG = r"C:\...\sc_debug.log"
def log(msg):   # spaceclaim_pitfalls_ironpython.md 의 utf-8 log 함수
    ...
f = codecs.open(LOG, "w", "utf-8"); f.write(u"=== start ===\n"); f.close()
try:
    log("[A] step A"); ...
    log("[B] step B"); ...
    log("=== ALL OK ===")
except Exception as e:
    log("[FATAL] %s" % e)
    try:
        import traceback as _tb; log(_tb.format_exc())
    except: pass
```

- 헤드리스 stdout 캡처 불가 → file log
- `codecs.open utf-8` (non-ASCII exception 메시지)
- 단계 marker `[D1]`, `[D2]` → 정지 지점 특정
- 실행 전 다른 SpaceClaim 이 남아 있으면 kill 하지 않고 종료를 기다림(`sc_orchestrate.run` 이 처리), 종료는 자기 PID 만

## 진단 도구 우선순위

| 순서 | 도구 | 시간 |
|---|---|---|
| 1 | references/ 검증 패턴 | <1초 |
| 2 | `clr.GetClrType(cls).GetMethods()` | ~30초 (cold start + script) |
| 3 | 로컬 `SpaceClaim.Api.V261.xml` grep | <1초 |
| 4 | 로컬 `.chm` 3개 | 수 분 |
| 5 | WebSearch/WebFetch KB | 수 분 |
| 6 | 사용자 GUI macro record (Speos addin) | 수 분 |

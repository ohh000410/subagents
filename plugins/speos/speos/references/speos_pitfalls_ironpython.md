# SpaceClaim IronPython — 언어·인코딩·프로세스

## IronPython 2.7

- f-string 금지 → `"%s" % x` / `.format()`. type hints 금지
- `True/False/None` OK. list comprehension / generator OK. `unicode(...)` 사용 가능
- numpy/scipy/pandas 없음 → orchestrator(CPython) 에서 계산 후 hardcode 또는 file 전달

## log = `codecs.open(..., "utf-8")`

```python
import codecs
def log(msg):
    f = codecs.open(LOG_PATH, "a", "utf-8")
    try:
        if isinstance(msg, bytes): msg = msg.decode("utf-8", "replace")
        else:
            try: msg = unicode(msg)
            except: msg = repr(msg)
        f.write(msg + u"\n")
    except: pass
    f.close()
```
기본 `open()` → non-ASCII .NET exception 메시지에서 UnicodeEncodeError, 진짜 에러가 `('unknown', '\x00', 0, 1, '')` 로 잘림.

## open() 기본 인코딩 = cp949

config.json 등 non-ASCII 포함 파일 → `codecs.open(CONFIG, "r", "utf-8")`.

## Python 키워드 충돌 → getattr

```python
extrude = getattr(ExtrudeType, "None")   # ExtrudeType.None 은 SyntaxError
val = getattr(SomeEnum, "from")
```

## face.commit() 중복 금지

`face.commit()` 후 `body.commit()`/`root.commit()` → cascade read-back `vertices_data[-1]` IndexError (PySpeos v0.8.2). `root.commit()` 한 번만.

## globals()

`sorted(globals())` → 헤드리스에서 hang 또는 빈 결과. candidate list 로 systematic 시도.

## 잔여 프로세스

매 실행 전 이름으로 SpaceClaim·AnsysSpeosLauncher 를 종료하지 않는다 — 좌석을 spaceclaim 에이전트·다른 세션과 공유하며, 일괄 종료가 남의 SPEOS 작업을 끊은 사례가 있다. 좌석이 차 있으면 대기·보고, 종료는 자기가 띄운 PID 만(`tools/speos_run.py`, `speos_launch_modes.md`). 누적 시 cold start 지연·license 충돌 → 원인 프로세스를 보고.

## ExitAfterScript=True 정리

정상 종료 = 5~30초 cleanup. exception 종료 = hang 가능 → orchestrator watchdog (자기 PID 만 `Stop-Process -Id <pid> -Force`; headless 라 `CloseMainWindow` 무효).

## SpeosDes = SPEOS 모드만

일반 SpaceClaim 에서 `SpeosDes` → NameError. 모드 2 인자 필수 (`speos_launch_modes.md`).

## subprocess.run 인코딩

`capture_output=True, text=True` → PowerShell stdout 의 cp949 문자에서 `UnicodeDecodeError`. timeout 초과 시 `r.stdout` None → `.strip()` AttributeError.
```python
r = subprocess.run([...], capture_output=True, timeout=30, encoding="utf-8", errors="replace")
return (r.stdout or "").strip()
```

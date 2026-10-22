# SpaceClaim IronPython — 언어·인코딩·프로세스

## IronPython 2.7

- f-string 금지 → `"%s" % x` / `.format()`. type hints 금지
- `True/False/None` OK. list comprehension / generator OK. `unicode(...)` 사용 가능
- numpy/scipy/pandas 없음 → orchestrator(CPython) 에서 계산 후 hardcode 또는 file 전달

## 로그가 아예 안 생기는 무언 실패

- 스크립트 최상위(log()·try 밖)에서 `__file__` 를 읽으면 NameError 로 로그 파일을 열기 전에 죽는다(0바이트 파일조차 없다). 스크립트 안의 경로는 orchestrator(CPython)가 정해 넘기고, `__file__` 은 orchestrator 에서만 쓴다
- `/RunScript` 가 아무 일 없이 성공으로 끝나고 로그가 0바이트 = 컴파일 에러(예: 유니코드가 아닌 str 안의 한글). launch 전에 hosted IronPython 으로 컴파일 체크한다(`sc_orchestrate.run` 1단계)

## 스크립트는 파일 쓰기 도구로 쓴다

Claude Code 의 Bash 도구를 거친 heredoc 은 `\\` 를 `\` 로 줄인다 → `u"C:\Users.."` 의 `\U` 가 이스케이프 컴파일 에러(0바이트 로그, rc=0)가 된다(2회 재현). IronPython 스크립트는 파일 쓰기 도구(Write)로 만들고, ASCII 경로는 `r"..."` 로 쓴다.

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

이름으로 일괄 종료 금지 — 다른 세션의 SPEOS 작업을 끊은 사례. 남은 SpaceClaim 이 있으면 기다리고, 종료는 자기가 띄운 PID 만. `tools/sc_orchestrate.py` 가 좌석 대기·자기 PID 종료를 한다.

## ExitAfterScript=True 정리

정상 종료 = 마지막 로그 줄 뒤 ~2초에 PID 가 스스로 끝난다(v261 일반 모드, 2026-10-18 실측). 초기 기록(날짜 미상)은 5~30초 cleanup — orchestrator 는 30초까지 기다린다. exception 종료 = hang 가능 → orchestrator watchdog (자기 PID `Stop-Process -Force`, headless 는 `CloseMainWindow` 무효).

## SpeosDes = SPEOS 모드만

일반 SpaceClaim 에서 `SpeosDes` → NameError. 모드 2 인자 필수 (`spaceclaim_launch_modes.md`).

## subprocess.run 인코딩

`capture_output=True, text=True` → PowerShell stdout 의 cp949 문자에서 `UnicodeDecodeError`. timeout 초과 시 `r.stdout` None → `.strip()` AttributeError.
```python
r = subprocess.run([...], capture_output=True, timeout=30, encoding="utf-8", errors="replace")
return (r.stdout or "").strip()
```
